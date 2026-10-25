"""Exercise the publisher/notifier file flow with only desktop delivery replaced."""
import argparse
import contextlib
import fcntl
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(os.environ.get("CORE_DUMP_ALERT_SCRIPT", Path(__file__).with_name("core_dump_alert.py")))
SPEC = importlib.util.spec_from_file_location("core_dump_alert", SCRIPT)
alert = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(alert)


class CoreDumpAlertTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cores = self.root / "cores"
        self.cores.mkdir()
        self.boot = self.root / "boot-id"
        self.boot.write_text("boot-one")
        self.snapshot = self.root / "public/status.json"
        self.state = self.root / "private/state.json"
        self.log = self.root / "notifications.jsonl"
        self.failure = self.root / "delivery-fails"
        self.notifier = self.root / "notify"
        self.notifier.write_text(
            f"#!{sys.executable}\nimport json,sys\nfrom pathlib import Path\n"
            f"with Path({str(self.log)!r}).open('a') as stream:\n"
            "    stream.write(json.dumps(sys.argv[1:])+'\\n')\n"
            f"if Path({str(self.failure)!r}).exists():\n"
            "    print('fixture delivery unavailable', file=sys.stderr)\n"
            "    raise SystemExit(1)\n")
        self.notifier.chmod(0o700)
        self.publisher_args = argparse.Namespace(directory=self.cores, snapshot=self.snapshot,
                                                 boot_id=self.boot)
        self.notifier_args = argparse.Namespace(snapshot=self.snapshot, state=self.state,
                                                boot_id=self.boot, notify_command=self.notifier)

    def tick(self, now, *, refresh=True):
        with mock.patch.object(alert, "elapsed_time", return_value=now):
            if refresh:
                alert.publish(self.publisher_args)
            return alert.notify(self.notifier_args)

    def attempts(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def core(self, name="core-first"):
        path = self.cores / name
        path.write_bytes(b"synthetic unreadable core payload")
        path.chmod(0o000)
        return path

    def test_empty_directory_is_quiet_and_state_is_private(self):
        self.assertEqual(self.tick(100), {"status": "empty", "count": 0})
        self.assertEqual(self.attempts(), [])
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.state.parent.stat().st_mode & 0o777, 0o700)

    def test_first_file_is_notified_and_duplicates_are_quiet(self):
        self.core()
        self.assertEqual(self.tick(100), {"status": "notified", "count": 1})
        saved = self.state.read_bytes()
        self.assertEqual(self.tick(101), {"status": "pending", "count": 1})
        self.assertEqual(self.state.read_bytes(), saved)
        self.assertEqual(len(self.attempts()), 1)
        self.assertIn("--expire-time=30000", self.attempts()[0])
        self.assertIn("1 arquivo(s) em /root/coredumps", self.attempts()[0][-1])

    def test_hourly_reminder_including_suspend_equivalent_elapsed_jump(self):
        self.core()
        self.tick(100)
        self.assertEqual(self.tick(3699), {"status": "pending", "count": 1})
        self.assertEqual(len(self.attempts()), 1)
        self.assertEqual(self.tick(3700), {"status": "notified", "count": 1})
        self.assertEqual(len(self.attempts()), 2)
        self.assertEqual(json.loads(self.state.read_text())["last_success"], 3700)

    def test_new_core_is_immediate_but_growth_is_not_new(self):
        first = self.core()
        self.tick(100)
        first.chmod(0o600)
        with first.open("ab") as stream:
            stream.write(b"more bytes")
        self.assertEqual(self.tick(101)["status"], "pending")
        self.core("core-second")
        self.assertEqual(self.tick(102), {"status": "notified", "count": 2})
        self.assertEqual(len(self.attempts()), 2)

    def test_removing_one_core_does_not_create_a_new_alert(self):
        first = self.core()
        self.core("core-second")
        self.tick(100)
        first.unlink()
        self.assertEqual(self.tick(101), {"status": "pending", "count": 1})
        self.assertEqual(len(self.attempts()), 1)
        self.assertEqual(self.tick(3700), {"status": "notified", "count": 1})

    def test_moving_last_core_stops_reminders_and_next_core_alerts(self):
        first = self.core()
        self.tick(100)
        first.rename(self.root / "archived-core")
        self.assertEqual(self.tick(101), {"status": "empty", "count": 0})
        self.assertEqual(self.tick(4000), {"status": "empty", "count": 0})
        self.assertEqual(len(self.attempts()), 1)
        self.core("core-next")
        self.assertEqual(self.tick(4001), {"status": "notified", "count": 1})
        self.assertEqual(len(self.attempts()), 2)

    def test_notification_failure_preserves_success_and_retries(self):
        self.core()
        self.tick(100)
        previous = self.state.read_bytes()
        self.core("core-second")
        self.failure.touch()
        with self.assertRaisesRegex(RuntimeError, "fixture delivery unavailable"):
            self.tick(101)
        self.assertEqual(self.state.read_bytes(), previous)
        self.failure.unlink()
        self.assertEqual(self.tick(102), {"status": "notified", "count": 2})
        self.assertEqual(len(self.attempts()), 3)

    def test_reboot_resets_success_timestamp(self):
        self.core()
        self.tick(10000)
        self.boot.write_text("boot-two")
        self.assertEqual(self.tick(20), {"status": "notified", "count": 1})
        self.assertEqual(len(self.attempts()), 2)

    def test_stale_snapshot_does_not_clear_pending_state(self):
        self.core()
        self.tick(100)
        previous = self.state.read_bytes()
        with self.assertRaisesRegex(ValueError, "stale"):
            self.tick(281, refresh=False)
        self.assertEqual(self.state.read_bytes(), previous)
        self.assertEqual(len(self.attempts()), 1)

    def test_invalid_timestamps_are_errors_and_preserve_state(self):
        self.core()
        self.tick(100)
        original = json.loads(self.snapshot.read_text())
        previous = self.state.read_bytes()
        for sampled in (float("nan"), float("inf"), -1, True, "100", 102):
            with self.subTest(sampled=sampled):
                self.snapshot.write_text(json.dumps({**original, "sample_time": sampled}))
                with self.assertRaisesRegex(ValueError, "invalid boot ID/timestamp"):
                    self.tick(101, refresh=False)
                self.assertEqual(self.state.read_bytes(), previous)
        self.assertEqual(len(self.attempts()), 1)

    def test_source_errors_do_not_report_empty_or_clear_state(self):
        self.core()
        self.tick(100)
        previous = self.state.read_bytes()
        self.snapshot.unlink()
        with self.assertRaises(FileNotFoundError):
            self.tick(101, refresh=False)
        self.snapshot.write_text("not JSON")
        with self.assertRaises(json.JSONDecodeError):
            self.tick(101, refresh=False)
        self.assertEqual(self.state.read_bytes(), previous)
        self.assertEqual(len(self.attempts()), 1)

    def test_missing_directory_is_not_published_as_empty(self):
        self.core()
        self.tick(100)
        previous = self.snapshot.read_bytes()
        self.cores.rename(self.root / "unavailable-cores")
        with self.assertRaises(FileNotFoundError):
            alert.publish(self.publisher_args)
        self.assertEqual(self.snapshot.read_bytes(), previous)

    def test_only_regular_core_files_contribute_and_payload_is_not_published(self):
        self.core("core-private-name")
        (self.cores / "core-link").symlink_to(self.root / "nonexistent-secret")
        (self.cores / "core-directory").mkdir()
        (self.cores / "unrelated-file").write_text("unrelated")
        with mock.patch.object(alert, "elapsed_time", return_value=100):
            self.assertEqual(alert.publish(self.publisher_args), {"status": "published", "count": 1})
        document = self.snapshot.read_text()
        self.assertNotIn("private-name", document)
        self.assertNotIn("payload", document)
        self.assertEqual(self.snapshot.stat().st_mode & 0o777, 0o644)
        self.assertEqual(len(json.loads(document)["files"][0]), 64)

    def test_locked_state_does_not_deliver_or_write_state(self):
        self.core()
        self.state.parent.mkdir(mode=0o700)
        with self.state.with_suffix(".lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.tick(100), {"status": "already-running"})
        self.assertFalse(self.state.exists())
        self.assertEqual(self.attempts(), [])

    def test_cli_publishes_and_notifies_using_real_files(self):
        self.core()
        # CLI uses the real host clock; only the external desktop endpoint is replaced.
        for command, options in [
            ("publish", ["--directory", str(self.cores)]),
            ("notify", ["--state", str(self.state), "--notify-command", str(self.notifier)]),
        ]:
            result = subprocess.run([sys.executable, "-I", str(SCRIPT), command,
                                     "--snapshot", str(self.snapshot), "--boot-id", str(self.boot),
                                     *options], text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["count"], 1)
        self.assertEqual(len(self.attempts()), 1)

    def test_cli_errors_are_visible_and_nonzero(self):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            result = alert.main(["notify", "--snapshot", str(self.snapshot),
                                 "--state", str(self.state), "--boot-id", str(self.boot)])
        self.assertEqual(result, 1)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("core-dump-alert:", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
