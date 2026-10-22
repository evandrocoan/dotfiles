"""Exercise the notifier over HTTP, real SQLite history and desktop boundaries."""
import fcntl
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from urllib.parse import parse_qs, urlsplit

from process_swap_history import History

SCRIPT = Path(os.environ.get("NETDATA_CHECK_SCRIPT", Path(__file__).with_name("netdata_memory_check.py")))
spec = importlib.util.spec_from_file_location("netdata_check", SCRIPT)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class NetdataMemoryCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                suite = cls.active
                query = parse_qs(urlsplit(self.path).query)
                chart = query.get("chart", ["groups"])[0]
                suite.requests.append((self.path, query))
                if chart in suite.unavailable:
                    self.send_error(503)
                    return
                before = int(query["before"][0])
                if chart == "mem.swapio":
                    suite.seed_history(before)
                if chart == "mem.swapio":
                    labels, columns = ["in", "out"], [suite.incoming, suite.outgoing]
                elif chart == "system.memory_some_pressure":
                    labels, columns = ["some 60"], [suite.psi if isinstance(suite.psi, list) else [suite.psi] * 12]
                else:
                    self.send_error(404)
                    return
                rows = [[before - (11 - i) * 10] + [col[i] for col in columns] for i in range(12)]
                if suite.stale:
                    for row in rows:
                        row[0] -= 60
                if suite.missing and chart == "mem.swapio":
                    rows[5][1] = None
                doc = {"labels": ["time", *labels], "data": rows}
                body = json.dumps(doc).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        type(self).active = self
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cgroup = self.root / "cgroup"
        self.cgroup.mkdir()
        self.boot = self.root / "boot"
        self.boot.write_text("boot-one")
        self.state = self.root / "private/state.json"
        self.log = self.root / "notifications.jsonl"
        self.notifier = self.root / "notify"
        self.notifier.write_text(f"#!{sys.executable}\n" +
            "import json,os,sys\nfrom pathlib import Path\n"
            "with Path(os.environ['NOTIFY_LOG']).open('a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')\n"
            "raise SystemExit(int(os.environ.get('NOTIFY_FAIL','0')))\n")
        self.notifier.chmod(0o700)
        self.incoming, self.outgoing = [0] * 12, [0] * 12
        self.psi, self.stale, self.missing = 2, False, False
        self.unavailable, self.requests = set(), []
        self.history_path = self.root / "history.sqlite3"
        self.processes = [dict(pid=123, start=100, name="example-app", delay_ns=100000000,
                               rss=4096, swap=1024)]
        self.coverage = dict(scanned=1, measured=1, errors=0, truncated=0, baselines=0,
                             resets=0, gone=0, accounting_at_boot=True)
        self.history_missing, self.history_gap = False, False
        self.write_cgroup()

    def seed_history(self, before):
        if self.history_missing:
            return
        writer = History(self.history_path)
        try:
            writer.db.execute("DELETE FROM frames")
            writer.db.commit()
            for stamp in range(before - 110, before + 1, 10):
                if self.history_gap and stamp == before - 50:
                    continue
                writer.record(dict(boot=self.boot.read_text(), bucket=stamp, start=stamp-10,
                                   end=stamp, elapsed=10, coverage=self.coverage, activity=self.processes))
        finally:
            writer.close()

    def write_cgroup(self, anon=100, swap=0, high=1000, cache=0):
        for name, value in {"memory.stat": f"anon {anon}\nfile {cache}\n",
                            "memory.swap.current": str(swap), "memory.high": str(high)}.items():
            (self.cgroup / name).write_text(value)

    def run_check(self, expected=0, fail_notification=False):
        result = subprocess.run([sys.executable, str(SCRIPT), "--netdata-url",
                                 f"http://127.0.0.1:{self.server.server_port}",
                                 "--cgroup", str(self.cgroup), "--boot-id", str(self.boot),
                                 "--state", str(self.state), "--notify-command", str(self.notifier),
                                 "--process-history", str(self.history_path)],
                                env={**os.environ, "NOTIFY_LOG": str(self.log),
                                     "NOTIFY_FAIL": "1" if fail_notification else "0"},
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
        return json.loads(result.stdout) if result.stdout else result.stderr

    def notifications(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def test_quiet_history_and_private_state(self):
        result = self.run_check()
        self.assertEqual(result["status"], "measured")
        self.assertEqual(result["conditions"], [])
        self.assertEqual(self.notifications(), [])
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.state.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(len(self.requests), 2)  # No full cgroup query on a quiet sample.

    def test_sustained_swap_and_pressure_use_saved_measured_pid(self):
        self.incoming = [1024] * 12
        result = self.run_check()
        self.assertEqual(result["conditions"], ["memory-pressure"])
        self.assertEqual(result["sent"], ["memory-pressure"])
        self.assertEqual(result["host"]["swap_in_windows_bytes_per_second"], [1048576] * 2)
        self.assertEqual(result["host"]["attribution"]["processes"][0]["swap_in_wait_seconds"], 1.2)
        self.assertIn("example-app (PID 123): 1.200 s aguardando swap-in", self.notifications()[0][-1])
        self.assertNotIn("system.slice", self.notifications()[0][-1])
        self.assertTrue(all(q["points"] == ["12"] for _, q in self.requests))

    def test_negative_out_direction_is_measured_as_positive_activity(self):
        self.outgoing = [-2048] * 12
        self.psi = 2
        result = self.run_check()
        self.assertEqual(result["sent"], ["memory-pressure"])
        self.assertEqual(result["host"]["swap_out_windows_bytes_per_second"], [2097152] * 2)
        self.assertIn("Possível thrashing", self.notifications()[0][-1])

    def test_burst_and_psi_alone_do_not_warn(self):
        self.psi = 20
        for incoming, outgoing in (([4096] * 6 + [0] * 6, [0] * 12),
                                   ([0] * 12, [0] * 12),
                                   ([2048] * 6 + [0] * 6, [0] * 6 + [-2048] * 6)):
            self.incoming, self.outgoing = incoming, outgoing
            self.assertEqual(self.run_check()["conditions"], [])
        self.assertEqual(self.notifications(), [])

    def test_below_threshold_does_not_warn(self):
        self.incoming = [1023.99] * 12
        self.assertEqual(self.run_check()["conditions"], [])

    def test_demand_includes_cold_swap_without_claiming_thrashing(self):
        self.write_cgroup(anon=400, swap=500)
        result = self.run_check()
        self.assertEqual(result["conditions"], ["demand"])
        self.assertEqual(result["anonymous_plus_swap_bytes"], 900)
        self.assertIn("não comprova thrashing", self.notifications()[0][-1])

    def test_file_cache_alone_does_not_warn(self):
        self.write_cgroup(anon=100, cache=100000)
        self.assertEqual(self.run_check()["conditions"], [])
        self.assertEqual(self.notifications(), [])

    def test_suppression_survives_recovery_and_expires(self):
        self.incoming = [1024] * 12
        self.run_check()
        self.assertEqual(self.run_check()["suppressed"], ["memory-pressure"])
        self.incoming = [0] * 12
        self.assertEqual(self.run_check()["conditions"], [])
        self.incoming = [1024] * 12
        self.assertEqual(self.run_check()["suppressed"], ["memory-pressure"])
        state = json.loads(self.state.read_text())
        state["alerts"]["memory-pressure"] -= 901
        self.state.write_text(json.dumps(state))
        self.assertEqual(self.run_check()["sent"], ["memory-pressure"])
        self.assertEqual(len(self.notifications()), 2)

    def test_demand_keeps_separate_six_hour_cooldown(self):
        self.write_cgroup(anon=850)
        self.assertEqual(self.run_check()["sent"], ["demand"])
        self.incoming = [1024] * 12
        result = self.run_check()
        self.assertEqual(result["sent"], ["memory-pressure"])
        self.assertEqual(result["suppressed"], ["demand"])

    def test_notification_failure_retries_without_claiming_delivery(self):
        self.incoming = [1024] * 12
        result = self.run_check(expected=2, fail_notification=True)
        self.assertEqual(result["notification_failures"], ["memory-pressure"])
        self.assertEqual(result["sent"], [])
        self.assertEqual(json.loads(self.state.read_text())["alerts"], {})
        self.assertEqual(self.run_check()["sent"], ["memory-pressure"])

    def test_reboot_resets_suppression(self):
        self.incoming = [1024] * 12
        self.run_check()
        self.boot.write_text("boot-two")
        self.assertEqual(self.run_check()["sent"], ["memory-pressure"])

    def test_corrupt_state_reports_reset(self):
        self.run_check()
        self.state.write_text("{broken")
        self.assertTrue(self.run_check()["state_reset"])
        self.assertEqual(json.loads(self.state.read_text())["version"], 3)

    def test_old_state_migrates_demand_cooldown(self):
        self.run_check()
        self.state.write_text(json.dumps({"version": 1, "sample": {"boot": "boot-one"},
                                         "alerts": {"demand": time.monotonic()}}))
        self.write_cgroup(anon=900)
        self.assertEqual(self.run_check()["suppressed"], ["demand"])

    def test_unlimited_high_is_distinct_from_healthy_bounded_memory(self):
        self.write_cgroup(high="max", anon=99999)
        result = self.run_check()
        self.assertEqual(result["limit_status"], "unlimited")
        self.assertIsNone(result["demand_ratio"])
        self.assertEqual(self.notifications(), [])

    def test_missing_capacity_does_not_suppress_valid_host_warning(self):
        self.incoming = [1024] * 12
        (self.cgroup / "memory.stat").unlink()
        result = self.run_check(expected=2)
        self.assertEqual(result["sent"], ["memory-pressure"])
        self.assertIn("capacity", result["errors"])

    def test_missing_or_stale_history_is_not_healthy_or_a_warning(self):
        self.incoming = [1024] * 12
        for field in ("missing", "stale"):
            setattr(self, field, True)
            result = self.run_check(expected=2)
            self.assertEqual(result["host"]["status"], "unavailable")
            self.assertEqual(result["sent"], [])
            setattr(self, field, False)
        self.assertEqual(self.notifications(), [])

    def test_unavailable_api_preserves_capacity_warning(self):
        self.unavailable.add("mem.swapio")
        self.write_cgroup(anon=900)
        result = self.run_check(expected=2)
        self.assertEqual(result["sent"], ["demand"])
        self.assertEqual(result["status"], "unavailable")

    def test_low_pressure_swap_does_not_warn(self):
        self.incoming = [4096] * 12
        self.psi = 1.99
        self.assertEqual(self.run_check()["conditions"], [])
        self.assertEqual(self.notifications(), [])

    def test_isolated_pressure_spike_does_not_warn(self):
        self.incoming = [4096] * 12
        self.psi = [0] * 6 + [20] * 6
        self.assertEqual(self.run_check()["conditions"], [])
        self.assertEqual(self.notifications(), [])

    def test_missing_pressure_is_not_healthy_and_preserves_capacity(self):
        self.incoming = [4096] * 12
        self.unavailable.add("system.memory_some_pressure")
        self.write_cgroup(anon=900)
        result = self.run_check(expected=2)
        self.assertEqual(result["host"]["status"], "unavailable")
        self.assertEqual(result["sent"], ["demand"])

    def test_attribution_failure_is_explicit_without_suppressing_host(self):
        self.incoming = [1024] * 12
        self.history_missing = True
        result = self.run_check()
        self.assertEqual(result["sent"], ["memory-pressure"])
        self.assertEqual(result["host"]["attribution"]["status"], "unavailable")
        self.assertIn("Histórico por PID indisponível", self.notifications()[0][-1])

    def test_partial_coverage_and_gaps_are_visible(self):
        self.incoming = [1024] * 12
        self.coverage["truncated"] = 1
        self.history_gap = True
        result = self.run_check()
        self.assertEqual(result["host"]["attribution"]["status"], "partial")
        self.assertIn("example-app (PID 123)", self.notifications()[0][-1])
        self.assertIn("Cobertura por PID parcial", self.notifications()[0][-1])

    def test_measured_zero_is_distinct_from_partial_and_occupied_swap(self):
        self.incoming = [1024] * 12
        self.processes = []
        result = self.run_check()
        self.assertEqual(result["host"]["attribution"]["status"], "measured")
        self.assertEqual(result["host"]["attribution"]["processes"], [])
        self.assertIn("Nenhum PID com espera de swap-in", self.notifications()[0][-1])

    def test_top_three_ranks_by_wait_and_escapes_names(self):
        self.incoming = [1024] * 12
        self.processes = [dict(pid=i, start=100, name=name, delay_ns=delay,
                               rss=1000, swap=100000000 // i)
                          for i, name, delay in ((1, "slow", 100000000), (2, "<bad&>\n", 400000000),
                                                 (3, "third", 200000000), (4, "second", 300000000))]
        result = self.run_check()
        self.assertEqual([p["pid"] for p in result["host"]["attribution"]["processes"]], [2, 4, 3])
        body = self.notifications()[0][-1]
        self.assertIn("&lt;bad&amp;&gt; (PID 2)", body)
        self.assertNotIn("PID 1", body)

    def test_previous_low_pressure_notice_does_not_suppress_new_condition(self):
        self.run_check()
        self.state.write_text(json.dumps({"version": 2, "boot": "boot-one",
                                         "alerts": {"host-swap": time.monotonic()}}))
        self.incoming = [1024] * 12
        self.assertEqual(self.run_check()["sent"], ["memory-pressure"])
        self.assertNotIn("host-swap", json.loads(self.state.read_text())["alerts"])

    def test_locked_run_does_not_fetch_or_notify(self):
        self.state.parent.mkdir(mode=0o700)
        with self.state.with_suffix(".lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.run_check()["status"], "already-running")
        self.assertEqual(self.requests, [])

    def test_loopback_only_and_no_credentials(self):
        for base in ("https://127.0.0.1", "http://example.com", "http://u:p@localhost"):
            with self.assertRaises(ValueError):
                check.LocalAPI(base)


if __name__ == "__main__":
    unittest.main()
