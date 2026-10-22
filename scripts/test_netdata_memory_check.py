"""Exercise the notification entrypoint with disposable cgroup and desktop boundaries."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPT = Path(os.environ.get("NETDATA_CHECK_SCRIPT", Path(__file__).with_name("netdata_memory_check.py")))
spec = importlib.util.spec_from_file_location("netdata_check", SCRIPT)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class NetdataMemoryCheckTest(unittest.TestCase):
    def setUp(self):
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
        self.write_cgroup()

    def write_cgroup(self, anon=100, swap=0, high=1000, pswpin=0, cache=0, events=0):
        for name, value in {"memory.stat": f"anon {anon}\nfile {cache}\npswpin {pswpin}\n",
                            "memory.events": f"high {events}\n", "memory.swap.current": str(swap),
                            "memory.high": str(high), "memory.current": str(anon + cache)}.items():
            (self.cgroup / name).write_text(value)

    def run_check(self, expected=0, fail_notification=False):
        result = subprocess.run([sys.executable, str(SCRIPT), "--cgroup", str(self.cgroup),
                                 "--boot-id", str(self.boot), "--state", str(self.state),
                                 "--notify-command", str(self.notifier)],
                                env={**os.environ, "NOTIFY_LOG": str(self.log),
                                     "NOTIFY_FAIL": "1" if fail_notification else "0"},
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
        return json.loads(result.stdout) if result.stdout else result.stderr

    def notifications(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def age_sample(self, seconds=20):
        state = json.loads(self.state.read_text())
        state["sample"]["time"] = time.monotonic() - seconds
        self.state.write_text(json.dumps(state))

    def test_initial_baseline_and_private_state(self):
        result = self.run_check()
        self.assertEqual(result["status"], "baseline-reset")
        self.assertIsNone(result["swap_in_bytes_per_second"])
        self.assertEqual(self.notifications(), [])
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.state.parent.stat().st_mode & 0o777, 0o700)

    def test_swap_activity_notifies_with_real_page_size(self):
        self.run_check()
        self.age_sample()
        self.write_cgroup(pswpin=30 * 1048576 // os.sysconf("SC_PAGE_SIZE"))
        result = self.run_check()
        self.assertEqual(result["conditions"], ["swap-in"])
        self.assertEqual(result["sent"], ["swap-in"])
        self.assertIn("swap-in elevado", self.notifications()[0][-2])

    def test_demand_includes_cold_swap_without_claiming_thrashing(self):
        self.write_cgroup(anon=400, swap=500)
        result = self.run_check()
        self.assertEqual(result["conditions"], ["demand"])
        self.assertEqual(result["anonymous_plus_swap_bytes"], 900)
        self.assertIn("não comprova thrashing", self.notifications()[0][-1])

    def test_file_cache_alone_does_not_warn(self):
        self.write_cgroup(anon=100, cache=100000)
        self.run_check()
        self.age_sample()
        result = self.run_check()
        self.assertEqual(result["status"], "measured")
        self.assertEqual(result["conditions"], [])
        self.assertEqual(result["swap_in_bytes_per_second"], 0)
        self.assertEqual(self.notifications(), [])

    def test_suppression_survives_recovery_until_interval_expires(self):
        self.write_cgroup(anon=900)
        self.run_check()
        self.age_sample()
        self.assertEqual(self.run_check()["suppressed"], ["demand"])
        self.write_cgroup(anon=100)
        self.age_sample()
        self.assertEqual(self.run_check()["conditions"], [])
        self.write_cgroup(anon=900)
        self.age_sample()
        self.assertEqual(self.run_check()["suppressed"], ["demand"])
        state = json.loads(self.state.read_text())
        state["alerts"]["demand"] -= 21601
        self.state.write_text(json.dumps(state))
        self.assertEqual(self.run_check()["sent"], ["demand"])
        self.assertEqual(len(self.notifications()), 2)

    def test_notification_failure_retries_without_claiming_delivery(self):
        self.write_cgroup(anon=900)
        result = self.run_check(expected=2, fail_notification=True)
        self.assertEqual(result["notification_failures"], ["demand"])
        self.assertEqual(result["sent"], [])
        self.assertEqual(json.loads(self.state.read_text())["alerts"], {})
        self.assertEqual(self.run_check()["sent"], ["demand"])
        self.assertEqual(len(self.notifications()), 2)

    def test_reboot_resets_rate_baseline(self):
        self.run_check()
        self.age_sample()
        self.boot.write_text("boot-two")
        self.write_cgroup(pswpin=999999)
        result = self.run_check()
        self.assertEqual(result["status"], "baseline-reset")
        self.assertEqual(result["conditions"], [])

    def test_new_cgroup_resets_rate_baseline(self):
        self.run_check()
        self.age_sample()
        self.cgroup.rename(self.root / "old-cgroup")
        self.cgroup.mkdir()
        self.write_cgroup(pswpin=999999)
        self.assertEqual(self.run_check()["status"], "baseline-reset")

    def test_counter_reset_never_produces_negative_rate(self):
        self.write_cgroup(pswpin=100)
        self.run_check()
        self.age_sample()
        self.write_cgroup(pswpin=1)
        result = self.run_check()
        self.assertEqual(result["status"], "baseline-reset")
        self.assertIsNone(result["swap_in_bytes_per_second"])

    def test_counter_or_cgroup_reset_preserves_notification_cooldown(self):
        self.write_cgroup(anon=900, pswpin=100)
        self.run_check()
        self.age_sample()
        self.write_cgroup(anon=900, pswpin=1)
        self.assertEqual(self.run_check()["suppressed"], ["demand"])
        self.cgroup.rename(self.root / "old-cgroup")
        self.cgroup.mkdir()
        self.write_cgroup(anon=900)
        self.assertEqual(self.run_check()["suppressed"], ["demand"])
        self.assertEqual(len(self.notifications()), 1)

    def test_corrupt_state_reports_reset(self):
        self.run_check()
        self.state.write_text("{broken")
        result = self.run_check()
        self.assertTrue(result["state_reset"])
        self.assertEqual(result["status"], "baseline-reset")
        self.assertEqual(json.loads(self.state.read_text())["version"], 1)

    def test_unlimited_high_is_distinct_from_healthy_bounded_memory(self):
        self.write_cgroup(high="max", anon=99999)
        result = self.run_check()
        self.assertEqual(result["limit_status"], "unlimited")
        self.assertIsNone(result["demand_ratio"])
        self.assertEqual(self.notifications(), [])

    def test_missing_counter_is_unavailable_not_healthy(self):
        (self.cgroup / "memory.stat").write_text("anon 100\n")
        error = self.run_check(expected=2)
        self.assertIn("measurement unavailable", error)
        self.assertFalse(self.state.exists())
        self.assertEqual(self.notifications(), [])

    def test_missing_cgroup_is_unavailable(self):
        self.cgroup.rename(self.root / "missing")
        error = self.run_check(expected=2)
        self.assertIn("measurement unavailable", error)
        self.assertFalse(self.state.exists())

    def test_exact_thresholds_and_monotonic_time(self):
        current = {"boot": "a", "cgroup": ["/fixture", 1, 2], "time": 20,
                   "anon": 800, "swap": 50, "high": 1000, "pswpin": 1280, "high_events": 0}
        previous = {**current, "time": 10, "pswpin": 0}
        result = check.evaluate(current, previous, 8192, 1048576, .85)
        self.assertEqual(result["swap_in_bytes_per_second"], 1048576)
        self.assertEqual(result["conditions"], ["swap-in", "demand"])
        current.update(anon=799, pswpin=1279)
        self.assertEqual(check.evaluate(current, previous, 8192, 1048576, .85)["conditions"], [])
        previous["time"] = current["time"] + 1
        self.assertEqual(check.evaluate(current, previous, 8192, 1048576, .85)["status"], "baseline-reset")


if __name__ == "__main__":
    unittest.main()
