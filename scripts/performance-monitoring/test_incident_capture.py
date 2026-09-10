"""Deterministic artifact/trigger replay and real disposable subprocess/storage checks."""

import copy
from contextlib import redirect_stderr
from functools import partial
import json
import io
import os
import re
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import incident_capture as recorder
import bcc_ready


ROOT = Path(__file__).parent


def config():
    return recorder.load_config(ROOT / "incident-capture.json")


def sample(io=0, memory=0):
    return {"pressure": {"io": {"some": {"avg10": io}},
                         "memory": {"some": {"avg10": memory}}}, "utc": "fixture"}


def process(delay=10):
    return {"pid": 42, "start_ticks": 100, "comm": "fixture-app", "cgroup": ["0::/test.slice"],
            "cpu_ticks": 1, "memory_kib": {"VmRSS": 64, "VmSwap": 0},
            "io": {"read_bytes": 10, "write_bytes": 20, "cancelled_write_bytes": 0},
            "threads": [{"tid": 42, "start_ticks": 100, "delay_ticks": delay}]}


def snapshot():
    return {"processes": [process()], "hz": 100, "uptime_end": 10, "incomplete": False}


def command(program):
    return [sys.executable, "-u", "-c", program], b"READY"


class IncidentTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = config()

    def test_rejects_invalid_config_and_unknown_keys(self):
        for delta in ({"capture_seconds": 0}, {"storage_budget_mib": float("nan")},
                      {"cooldown_seconds": True}, {"extra": 1}):
            with self.subTest(delta=delta):
                path = self.root / "config.json"
                path.write_text(json.dumps({**self.config, **delta}))
                with self.assertRaises(ValueError):
                    recorder.load_config(path)

    def test_kernel_tracepoint_layout_adapts_ioprio_and_rejects_unknown_offsets(self):
        # Relevant field offsets from this host's block_io_start/block_io_done format.
        common = "\n".join(f"field:{name}; offset:{offset}; size:{size}; signed:0;" for name, offset, size in
                           (("dev",8,4), ("sector",16,8), ("nr_sector",24,4), ("bytes",28,4)))
        modern = common + "\nfield:ioprio; offset:32; size:2;\nfield:rwbs[8]; offset:34; size:8;"
        legacy = common + "\nfield:rwbs[8]; offset:32; size:8;"
        source = "struct tp_args {\n    unsigned int bytes;\n    char rwbs[8];\n};"
        expected = "struct tp_args {\n    unsigned int bytes;\n    unsigned short ioprio;\n    char rwbs[8];\n};"
        self.assertEqual(bcc_ready.adapt_text(source, [modern, modern]), expected)
        self.assertEqual(bcc_ready.adapt_text(expected, [modern, modern]), expected)
        self.assertEqual(bcc_ready.adapt_text(source, [legacy, legacy]), source)
        for formats in ([modern, legacy], [modern.replace("offset:34", "offset:36")] * 2):
            with self.subTest(formats=formats), self.assertRaises(RuntimeError):
                bcc_ready.adapt_text(source, formats)

    def test_collector_adapter_gates_every_callback_and_checks_map_writes(self):
        # Relevant callback shapes from native BCC; this tests the source adapter boundary.
        # Compilation, actual kernel effects and native output are covered by the live proof.
        biosnoop = """
#include <linux/blk-mq.h>
static int __trace_pid_start(struct hash_key key)
{
    infobyreq.update(&key, &val);
}
int trace_req_start(struct pt_regs *ctx, struct request *req)
{
    start.update(&key, &start_req);
}
static int __trace_req_completion(void *ctx, struct hash_key key)
{
    u64 qdelta;
    data.qdelta = 0;
    data.qdelta = startp->ts - valp->ts;
}
"""
        biolatency = """
#include <linux/blk-mq.h>
static int __trace_req_start(struct start_key key)
{
    start.update(&key, &ts);
}
static int __trace_req_done(struct start_key key)
{
    return 0;
}
"""
        for tool, source, expected_callbacks, expected_updates in (
                ("biosnoop", biosnoop, 3, 2), ("biolatency", biolatency, 2, 1)):
            with self.subTest(tool=tool):
                output = bcc_ready.instrument(source, tool)
                bodies = re.findall(r"int (?:__)?trace_\w+\([^)]*\)\n\{([^}]+)", output)
                self.assertEqual(len(bodies), expected_callbacks)
                self.assertTrue(all(body.lstrip().startswith("if (!perfmon_active()) return 0;") for body in bodies))
                checked = re.findall(r"if \((?:start|infobyreq)\.update\([^;]+\)\) perfmon_errors.atomic_increment\(0\);", output)
                self.assertEqual(len(checked), expected_updates)
        output = bcc_ready.instrument(biosnoop, "biosnoop")
        sentinel = int(re.search(r"data\.qdelta = (-\d+);", output).group(1))
        self.assertEqual("%7.2f" % (float(sentinel) / 1000000), "  -1.00")
        self.assertIn("data.dev = key.dev;", output)
        with self.assertRaises(RuntimeError):
            bcc_ready.instrument(biosnoop.replace("start.update", "start.insert"), "biosnoop")

    def test_collector_enable_checks_empty_maps_before_enabling_and_notifying(self):
        class EnabledArray:
            value = 0

            def __setitem__(self, key, value):
                self.value = value.value
                if "PERFORMANCE_COLLECTOR_READY" in output.getvalue():
                    raise AssertionError("ready was sent before enabling collection")

        for tool, stale_map in (("biosnoop", "infobyreq"), ("biosnoop", "start"), ("biolatency", "start")):
            with self.subTest(tool=tool, stale_map=stale_map):
                output = io.StringIO()
                enabled = EnabledArray()
                maps = {"start": {}, "infobyreq": {}, "perfmon_enabled": enabled}
                maps[stale_map][123] = "unfinished request"
                with redirect_stderr(output), self.assertRaises(RuntimeError):
                    bcc_ready.enable_capture(maps, tool)
                self.assertEqual(enabled.value, 0)
                self.assertNotIn("PERFORMANCE_COLLECTOR_READY", output.getvalue())
                maps[stale_map].clear()
                with redirect_stderr(output):
                    bcc_ready.enable_capture(maps, tool)
                self.assertEqual(enabled.value, 1)
                self.assertEqual(output.getvalue().count("PERFORMANCE_COLLECTOR_READY"), 1)

    def test_sustained_trigger_recovery_and_cooldown(self):
        trigger = recorder.Trigger(self.config)
        self.assertIsNone(trigger.observe(sample(6)["pressure"], 0, 1000))
        self.assertIsNone(trigger.observe(sample(6)["pressure"], 9, 1009))
        self.assertIsNone(trigger.observe(sample()["pressure"], 10, 1010))
        self.assertIsNone(trigger.observe(sample(memory=3)["pressure"], 11, 1011))
        self.assertEqual(trigger.observe(sample(memory=3)["pressure"], 21, 1021), "pressure:memory")
        trigger.attempted(1021)
        self.assertIsNone(trigger.observe(sample(6)["pressure"], 22, 1022))
        self.assertIsNone(trigger.observe(sample(6)["pressure"], 40, 1040))
        self.assertEqual(trigger.observe(sample(6)["pressure"], 921, 1921), "pressure:io")

    def test_artifact_replay_excludes_impossible_delay_preserving_raw(self):
        fixture = json.loads((ROOT / "delay-anomaly-fixture.json").read_text())
        self.assertEqual(recorder.delay_invalid(fixture["thread"], fixture["sample"]),
                         fixture["expected_invalid"])
        before, after = snapshot(), snapshot()
        after["processes"][0]["threads"][0]["delay_ticks"] = fixture["thread"]["delay_ticks"]
        original = copy.deepcopy(after)
        result = recorder.summarize(before, after)
        self.assertIsNone(result["processes"][0]["delay_seconds"])
        self.assertEqual(result["invalid_delay_counters"], [{"pid": 42, "tid": 42,
            "reason": "delay_exceeds_thread_lifetime_or_negative", "raw_delay_ticks": 738541183}])
        self.assertEqual(after, original)

    def test_multithread_delays_are_valid_beyond_capture_interval(self):
        before, after = snapshot(), snapshot()
        before["processes"][0]["threads"].append({"tid": 43, "start_ticks": 100, "delay_ticks": 0})
        after["processes"][0]["threads"].append({"tid": 43, "start_ticks": 100, "delay_ticks": 500})
        after["processes"][0]["threads"][0]["delay_ticks"] = 510
        result = recorder.summarize(before, after)
        self.assertEqual(result["processes"][0]["delay_seconds"], 10)
        self.assertEqual(result["invalid_delay_counters"], [])

    def test_invalid_exited_threads_remain_flagged(self):
        before, after = snapshot(), snapshot()
        before["processes"][0]["threads"].append({"tid": 43, "start_ticks": 100, "delay_ticks": 738541183})
        result = recorder.summarize(before, after)
        self.assertIsNone(result["processes"][0]["delay_seconds"])
        self.assertEqual(result["processes"][0]["invalid_threads"], 1)
        self.assertEqual(result["invalid_delay_counters"][0]["tid"], 43)
        self.assertEqual(result["invalid_delay_counters"][0]["sample"], "before")
        after["processes"] = []
        self.assertEqual(recorder.summarize(before, after)["invalid_delay_counters"][0]["tid"], 43)

    def test_decreased_delays_and_reused_identity_are_not_ranked(self):
        before, after = snapshot(), snapshot()
        after["processes"][0]["threads"][0]["delay_ticks"] = 1
        result = recorder.summarize(before, after)
        self.assertIsNone(result["processes"][0]["delay_seconds"])
        self.assertEqual(result["invalid_delay_counters"][0]["reason"], "delay_counter_decreased")
        after["processes"][0]["start_ticks"] = 200
        result = recorder.summarize(before, after)
        self.assertEqual(result["processes"], [])
        self.assertEqual(result["exited_or_reused_processes"], 1)

    def test_stat_parser_handles_spaces_and_closing_parentheses(self):
        fields = ["0"] * 50
        fields[0], fields[19], fields[39] = "S", "123", "738541183"
        parsed = recorder.parse_stat("42 (some ) tricky name) " + " ".join(fields))
        self.assertEqual(parsed["comm"], "some ) tricky name")
        self.assertEqual(parsed["delay_ticks"], 738541183)
        self.assertEqual(parsed["start_ticks"], 123)

    def test_lock_rejects_a_second_real_owner(self):
        lock = self.root / "capture.lock"
        with recorder.capture_lock(lock) as first:
            self.assertTrue(first)
            with recorder.capture_lock(lock) as second:
                self.assertFalse(second)
        with recorder.capture_lock(lock) as third:
            self.assertTrue(third)

    def fake_collectors(self, **changes):
        settings = {**self.config, "capture_seconds": .05, "startup_timeout_seconds": .4, **changes}
        return settings, {"probe": command("import time; print('READY', flush=True); time.sleep(30)")}

    def test_trigger_replay_reaches_a_real_terminal_capture_and_persists_cooldown(self):
        settings, commands = self.fake_collectors()
        capture = partial(recorder.capture, directory=self.root / "reports", lock_path=self.root / "lock",
                          commands=commands, snapshotter=snapshot, sampler=sample)
        monitor = recorder.Monitor(settings, self.root / "state", capture)
        results = [monitor.step(sample(6), tick, 2000 + tick) for tick in range(11)]
        self.assertEqual(results[:10], [None] * 10)
        path = results[10]
        manifest = json.loads((path / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "complete")
        self.assertEqual(manifest["trigger"], "pressure:io")
        self.assertEqual(manifest["tracing"]["reason"], "window_complete")
        self.assertEqual(len((path / "host-before.jsonl").read_text().splitlines()), 11)
        self.assertEqual(json.loads((path / "summary.json").read_text())["processes"][0]["pid"], 42)
        restored = recorder.Monitor(settings, self.root / "state", capture)
        for tick in range(20, 41):
            self.assertIsNone(restored.step(sample(6), tick, 2000 + tick))
        self.assertEqual(len(list((self.root / "reports").glob("incident-*"))), 1)
        self.assertEqual(json.loads((self.root / "state/state.json").read_text())["last_attempt_epoch"], 2010)

    def test_manual_request_and_duplicate_during_capture(self):
        reasons = []

        def capture(config, reason, history, stop):
            reasons.append(reason)
            monitor.request()
            return "captured"

        monitor = recorder.Monitor(self.config, self.root / "state", capture)
        monitor.request()
        self.assertEqual(monitor.step(sample(), 0, 1000), "captured")
        self.assertIsNone(monitor.step(sample(), 1, 1001))
        self.assertEqual(reasons, ["manual"])

    def test_ready_notification_allows_immediate_manual_signal(self):
        address = str(self.root / "notify.sock")
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as receiver:
            receiver.bind(address)
            receiver.settimeout(3)
            program = """
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import incident_capture as r
root = Path(sys.argv[2])
r.LOG_DIR = root / 'logs'
r.LOG_DIR.mkdir()
r.LOCK_PATH = root / 'capture.lock'
r.host_sample = lambda: {'pressure': {'io': {'some': {'avg10': 0}}, 'memory': {'some': {'avg10': 0}}}}
def capture(config, reason, history, stop):
    (root / 'manual-proof.json').write_text(json.dumps({'reason': reason}))
    monitor.stop = True
monitor = r.Monitor(r.load_config(Path(sys.argv[1]) / 'incident-capture.json'), root / 'state', capture)
monitor.watch()
"""
            child = subprocess.Popen([sys.executable, "-c", program, str(ROOT.resolve()), str(self.root)],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     env={**os.environ, "NOTIFY_SOCKET": address})
            try:
                self.assertEqual(receiver.recv(128), b"READY=1")
                os.kill(child.pid, signal.SIGUSR1)
                _, errors = child.communicate(timeout=4)
                self.assertEqual(child.returncode, 0, errors.decode())
                self.assertEqual(json.loads((self.root / "manual-proof.json").read_text()), {"reason": "manual"})
            finally:
                if child.poll() is None:
                    child.kill()
                    child.communicate(timeout=2)

    def test_cancelled_writes_do_not_inflate_io_ranking(self):
        first, second = process(), process()
        first.update(pid=43, comm="cancel-only")
        first["io"] = {"read_bytes": 0, "write_bytes": 0, "cancelled_write_bytes": 10000}
        second.update(pid=44, comm="reader")
        second["io"] = {"read_bytes": 100, "write_bytes": 0, "cancelled_write_bytes": 0}
        before = {**snapshot(), "processes": [copy.deepcopy(first), copy.deepcopy(second)]}
        for row in before["processes"]:
            row["io"] = {k: 0 for k in row["io"]}
        after = {**snapshot(), "processes": [first, second]}
        report = recorder.report_text({"created_utc": "fixture", "trigger": "test", "status": "complete"},
                                      recorder.summarize(before, after)).decode()
        self.assertLess(report.index('"comm": "reader"'), report.index('"comm": "cancel-only"'))

    def test_collector_timeout_kills_subprocess_and_marks_partial(self):
        settings, _ = self.fake_collectors(startup_timeout_seconds=.1)
        path = recorder.capture(settings, "test", directory=self.root, lock_path=self.root / "lock",
            commands={"probe": command("import time; time.sleep(30)")}, snapshotter=snapshot, sampler=sample)
        manifest = json.loads((path / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "partial")
        self.assertEqual(manifest["tracing"]["reason"], "startup_timeout")
        pid = manifest["tracing"]["collectors"]["probe"]["pid"]
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_loss_is_partial_even_with_complete_window(self):
        settings, _ = self.fake_collectors()
        commands = {"probe": command("import sys,time; print('READY'); "
            "print('PERFORMANCE_COLLECTOR_LOST count=3', file=sys.stderr); time.sleep(30)")}
        path = recorder.capture(settings, "test", directory=self.root, lock_path=self.root / "lock",
                                commands=commands, snapshotter=snapshot, sampler=sample)
        manifest = json.loads((path / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "partial")
        self.assertTrue(manifest["tracing"]["collectors"]["probe"]["lost_events"])

    def test_output_budget_failure_and_cancellation_cleanup(self):
        settings, commands = self.fake_collectors()
        result = recorder.run_collectors(recorder.Budget(self.root, maximum=5), settings,
                                          lambda: False, commands, sample)
        self.assertIn("incident output budget exceeded", result["reason"])
        for child in result["collectors"].values():
            with self.assertRaises(ProcessLookupError):
                os.kill(child["pid"], 0)
        result = recorder.run_collectors(recorder.Budget(self.root), settings,
                                          lambda: True, commands, sample)
        self.assertEqual(result["reason"], "cancelled")

    def test_early_exit_preserves_failure_diagnostics(self):
        settings, _ = self.fake_collectors()
        result = recorder.run_collectors(recorder.Budget(self.root), settings, lambda: False,
            {"probe": command("import sys; print('attach failed',file=sys.stderr); sys.exit(7)")}, sample)
        self.assertEqual(result["reason"], "collector_exited")
        self.assertEqual(result["collectors"]["probe"]["returncode"], 7)
        self.assertIn("attach failed", (self.root / "probe.stderr.log").read_text())

    def test_failure_during_shutdown_cannot_be_complete(self):
        settings, _ = self.fake_collectors()
        commands = {"probe": command("import signal,sys,time; "
            "signal.signal(signal.SIGTERM, lambda *a: sys.exit(7)); print('READY',flush=True); time.sleep(30)")}
        path = recorder.capture(settings, "test", directory=self.root, lock_path=self.root / "lock",
                                commands=commands, snapshotter=snapshot, sampler=sample)
        manifest = json.loads((path / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "partial")
        self.assertEqual(manifest["tracing"]["reason"], "collector_shutdown_failed")

    def test_map_update_failures_are_partial_even_without_perf_loss(self):
        settings, _ = self.fake_collectors()
        commands = {"probe": command("import sys,time; print('READY'); "
            "print('PERFORMANCE_COLLECTOR_LOST map_update_failures=1',file=sys.stderr); time.sleep(30)")}
        path = recorder.capture(settings, "test", directory=self.root, lock_path=self.root / "lock",
                                commands=commands, snapshotter=snapshot, sampler=sample)
        manifest = json.loads((path / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "partial")
        self.assertTrue(manifest["tracing"]["collectors"]["probe"]["lost_events"])

    def test_stream_limit_stops_flooding_child(self):
        settings, _ = self.fake_collectors()
        with patch.object(recorder, "STREAM_BYTES", 32):
            result = recorder.run_collectors(recorder.Budget(self.root), settings, lambda: False,
                {"probe": command("import time; print('x'*256,flush=True); time.sleep(30)")}, sample)
        self.assertIn("collector output limit: probe/stdout", result["reason"])
        with self.assertRaises(ProcessLookupError):
            os.kill(result["collectors"]["probe"]["pid"], 0)

    def record(self, name, created, status="complete"):
        directory = self.root / ("incident-" + name)
        directory.mkdir()
        (directory / "manifest.json").write_text(json.dumps({"schema": recorder.SCHEMA,
            "created_epoch": created, "status": status}))
        (directory / "data").write_bytes(b"x" * 100)
        return directory

    def test_retention_preserves_active_pinned_open_and_unrelated(self):
        old = self.record("old", 1)
        active = self.record("active", 2, "recording")
        pinned = self.record("pinned", 3)
        (pinned / "KEEP").touch()
        opened = self.record("open", 4)
        (self.root / "incident-unrelated").mkdir()
        (self.root / "incident-alias").symlink_to(old, target_is_directory=True)
        with (opened / "data").open():
            recorder.prune(self.root, self.config, now=40*86400)
        self.assertFalse(old.exists())
        self.assertTrue(active.exists())
        self.assertTrue(pinned.exists())
        self.assertTrue(opened.exists())
        self.assertTrue((self.root / "incident-unrelated").exists())
        self.assertTrue((self.root / "incident-alias").is_symlink())
        self.assertEqual(list(self.root.glob(".deleting-*")), [])

    def test_quota_removes_oldest_whole_record_first(self):
        first = self.record("first", 10)
        second = self.record("second", 20)
        settings = {**self.config, "storage_budget_mib": recorder.tree_bytes(second) / recorder.MIB}
        recorder.prune(self.root, settings, now=21)
        self.assertFalse(first.exists())
        self.assertTrue(second.exists())

    def test_recovery_finishes_interrupted_rotation_and_marks_abandoned(self):
        active = self.record("active", 1, "recording")
        tombstone = self.root / ".deleting-incident-old"
        tombstone.mkdir()
        (tombstone / "data").write_text("remaining")
        recorder.recover(self.root)
        self.assertFalse(tombstone.exists())
        self.assertEqual(json.loads((active / "manifest.json").read_text())["status"], "interrupted")

    def test_low_space_skips_before_starting_collectors(self):
        usage = type("Usage", (), {"free": 1})()
        with patch.object(recorder.shutil, "disk_usage", return_value=usage):
            self.assertIsNone(recorder.capture(self.config, "test", directory=self.root,
                              lock_path=self.root / "lock"))
        self.assertEqual(list(self.root.glob("incident-*")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
