"""Filesystem transactions and disposable processes; never mutate the live desktop."""

import contextlib
import io
import json
import multiprocessing
import os
from pathlib import Path
import selectors
import shlex
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import xfce_panel_startup as fix
import diagnose_xfce_panel_boot as capture

EXPECTED = b'''<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-panel" version="1.0">
 <property name="configver" type="empty"/>
 <property name="panels" type="empty"><property name="panel-1" type="empty">
  <property name="position" type="string" value="p=6;x=20;y=30"/>
 </property></property>
</channel>
'''
ORIGINAL = EXPECTED.replace(b'type="empty"/>', b'type="int" value="2"/>', 1)


def contender(home, run, barrier, source):
    barrier.wait(timeout=5)
    capture.prepare_capture(Path(home), run, "next-boot", source)


class Fixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name) / "home with spaces"
        self.home.mkdir()
        self.environment = mock.patch.dict(os.environ)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        for key in ("XDG_CONFIG_HOME", "XDG_DATA_HOME"):
            os.environ.pop(key, None)
        self.service = self.home / fix.SERVICE
        self.autostart = self.home / fix.AUTOSTART
        self.panel = self.home / fix.PANEL
        self.daemon = self.home / fix.DAEMON
        for path in (self.service, self.autostart, self.panel, self.daemon):
            path.parent.mkdir(parents=True, exist_ok=True)
        self.service.write_text("[D-BUS Service]\nName=org.xfce.Xfconf\nExec="
                                + shlex.quote(str(self.daemon)) + "\n")
        desktop = b"[Desktop Entry]\nType=Application\nName=Fixture\nExec=unused\n"
        self.autostart.write_bytes(fix.desktop_shell(desktop, fix.OLD_PREFIX + fix.OLD_TAIL))
        self.autostart.chmod(0o664)
        self.panel.write_bytes(ORIGINAL)
        self.daemon.write_text("fixture; never execute\n")
        self.daemon.chmod(0o700)
        self.mint = self.home / "mint.xml"
        self.mint.write_bytes(EXPECTED)
        self.original_service = self.service.read_bytes()
        self.original_autostart = self.autostart.read_bytes()

    def apply(self):
        fix.apply(self.home, mint_xml=self.mint)

    def armed_capture(self, expected=EXPECTED):
        with mock.patch.object(capture, "current_boot", return_value="preparation-boot"):
            run = capture.prepare(self.home, expected)
            capture.activate(self.home, run)
        return run, capture.run_directory(self.home, run)

    def assert_edit_before_transaction_is_preserved(self, operation):
        real = fix.make_transaction
        for edited in (self.service, self.autostart):
            with self.subTest(edited=edited):
                self.service.write_bytes(self.original_service)
                self.autostart.write_bytes(self.original_autostart)

                def concurrent_edit(home, changes):
                    edited.write_bytes(b"user edit after candidate construction")
                    return real(home, changes)

                with mock.patch.object(fix, "make_transaction", side_effect=concurrent_edit):
                    with self.assertRaisesRegex(fix.Refused, "Concurrent file change before transaction"):
                        operation()
                self.assertEqual(edited.read_bytes(), b"user edit after candidate construction")
                untouched, expected = ((self.autostart, self.original_autostart)
                                       if edited == self.service else (self.service, self.original_service))
                self.assertEqual(untouched.read_bytes(), expected)
                self.assertEqual(self.panel.read_bytes(), ORIGINAL)
                self.assertFalse((fix.state_dir(self.home) / "repair.json").exists())
                self.assertFalse((fix.state_dir(self.home) / "captures").exists())


class RepairTests(Fixture):
    def test_edit_before_transaction_does_not_become_repair_baseline(self):
        self.assert_edit_before_transaction_is_preserved(self.apply)

    def test_status_does_not_create_state(self):
        result = fix.status(self.home)
        self.assertEqual(result["activation"]["environment"], {})
        self.assertFalse(result["autostart_fixed"])
        self.assertFalse(fix.state_dir(self.home).exists())

    def test_apply_repeat_and_undo_preserve_xml_and_originals(self):
        self.apply()
        result = fix.status(self.home)
        self.assertEqual(result["activation"]["environment"], {"XDG_CONFIG_DIRS": fix.MINT_DIRS})
        self.assertTrue(result["autostart_fixed"])
        self.assertEqual(fix.desktop_arguments(self.autostart.read_bytes()), ["/bin/sh", "-c", fix.FIXED_TAIL])
        self.assertEqual(self.autostart.stat().st_mode & 0o777, 0o664)
        after = self.service.read_bytes(), self.autostart.read_bytes()
        self.apply()
        self.assertEqual((self.service.read_bytes(), self.autostart.read_bytes()), after)
        fix.undo(self.home)
        fix.undo(self.home)
        self.assertEqual(self.service.read_bytes(), self.original_service)
        self.assertEqual(self.autostart.read_bytes(), self.original_autostart)
        self.assertEqual(self.panel.read_bytes(), ORIGINAL)

    def test_unknown_command_and_missing_prerequisite_do_not_mutate_launchers(self):
        self.service.write_bytes(self.original_service + b"SystemdService=custom.service\n")
        before = self.service.read_bytes()
        with self.assertRaisesRegex(fix.Refused, "Unsupported xfconf"):
            self.apply()
        self.assertEqual(self.service.read_bytes(), before)
        self.assertEqual(self.autostart.read_bytes(), self.original_autostart)
        self.service.write_bytes(self.original_service)
        self.mint.unlink()
        with self.assertRaisesRegex(fix.Refused, "defaults or local"):
            self.apply()
        self.assertEqual(self.service.read_bytes(), self.original_service)

    def test_symlink_state_does_not_create_outside_files(self):
        outside = self.home / "outside"
        outside.mkdir()
        (self.home / ".local/state").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(fix.Refused, "symbolic-link state"):
            self.apply()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual(self.service.read_bytes(), self.original_service)

    def test_conflicting_edit_blocks_undo_without_other_launcher_write(self):
        self.apply()
        before = self.service.read_bytes()
        self.autostart.write_bytes(b"concurrent edit")
        with self.assertRaisesRegex(fix.Refused, "Concurrent file change"):
            fix.undo(self.home)
        self.assertEqual(self.autostart.read_bytes(), b"concurrent edit")
        self.assertEqual(self.service.read_bytes(), before)

    def test_edit_between_replacements_is_preserved_in_both_directions(self):
        real = fix.atomic_write
        for forward in (True, False):
            with self.subTest(forward=forward):
                self.service.write_bytes(self.original_service)
                self.autostart.write_bytes(self.original_autostart)
                if not forward:
                    self.apply()

                def injected(path, data, *args, **kwargs):
                    real(path, data, *args, **kwargs)
                    if path == self.service:
                        self.autostart.write_bytes(b"edit during first replacement")

                with mock.patch.object(fix, "atomic_write", side_effect=injected):
                    with self.assertRaisesRegex(fix.Refused, "Concurrent file change"):
                        self.apply() if forward else fix.undo(self.home)
                self.assertEqual(self.autostart.read_bytes(), b"edit during first replacement")
                phase = fix.read_json(fix.state_dir(self.home) / "repair.json")["phase"]
                self.assertEqual(phase, "applying" if forward else "undoing")


class CaptureTests(Fixture):
    def test_edit_before_transaction_does_not_become_capture_baseline(self):
        self.assert_edit_before_transaction_is_preserved(lambda: capture.prepare(self.home, EXPECTED))

    def test_preparation_and_current_boot_do_not_restore(self):
        run = capture.prepare(self.home, EXPECTED)
        self.assertEqual(self.service.read_bytes(), self.original_service)
        capture.activate(self.home, run)
        self.assertIsNone(capture.prepare_capture(self.home, run, capture.current_boot(), "dbus"))
        self.assertEqual(self.panel.read_bytes(), ORIGINAL)
        self.assertFalse((capture.run_directory(self.home, run) / "receipt.json").exists())

    def test_cleanup_preserves_permanent_fix(self):
        self.apply()
        repaired = self.service.read_bytes()
        run, root = self.armed_capture()
        self.assertIn(fix.ASSIGNMENT, fix.service_entry(self.service.read_bytes())["Exec"])
        with self.assertRaisesRegex(fix.Refused, "Clean up the active capture"):
            fix.undo(self.home)
        with self.assertRaisesRegex(fix.Refused, "Clean up the active capture"):
            capture.prepare(self.home)
        capture.cleanup(self.home, run)
        capture.cleanup(self.home, run)
        self.assertEqual(self.service.read_bytes(), repaired)
        self.assertTrue(fix.status(self.home)["autostart_fixed"])
        self.assertIsNone(fix.capture_active(self.home))
        self.assertEqual(self.panel.read_bytes(), ORIGINAL)
        self.assertFalse(fix.read_json(root / "arm.json")["enabled"])

    def test_one_shot_preserves_later_evidence(self):
        run, root = self.armed_capture()
        trace = capture.prepare_capture(self.home, run, "next-boot", "dbus")
        self.assertTrue(trace.is_file())
        self.assertEqual(self.panel.read_bytes(), EXPECTED)
        self.assertEqual((root / "runs/next-boot/before-restore.xml").read_bytes(), ORIGINAL)
        self.panel.write_bytes(b"new daemon state")
        capture.prepare_capture(self.home, run, "next-boot", "autostart")
        self.assertEqual(self.panel.read_bytes(), b"new daemon state")
        self.assertIsNone(capture.prepare_capture(self.home, run, "another-boot", "dbus"))
        self.assertEqual(self.panel.read_bytes(), b"new daemon state")

    def test_observation_only_never_restores(self):
        run, root = self.armed_capture(None)
        capture.prepare_capture(self.home, run, "next-boot", "dbus")
        self.assertEqual(self.panel.read_bytes(), ORIGINAL)
        self.assertEqual(fix.read_json(root / "receipt.json")["phase"], "observing")

    def test_interrupted_claim_is_not_retried(self):
        run, root = self.armed_capture()
        fix.write_json(root / "receipt.json", {"boot_id": "next-boot", "phase": "claimed"})
        capture.prepare_capture(self.home, run, "next-boot", "dbus")
        self.assertEqual(self.panel.read_bytes(), ORIGINAL)
        self.assertEqual(fix.read_json(root / "receipt.json")["phase"], "claimed")

    def test_bad_checksum_is_reported_and_not_retried(self):
        run, root = self.armed_capture()
        (root / "expected-panel.xml").write_bytes(b"bad")
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            capture.prepare_capture(self.home, run, "next-boot", "dbus")
        self.assertIn("checksum mismatch", errors.getvalue())
        (root / "expected-panel.xml").write_bytes(EXPECTED)
        capture.prepare_capture(self.home, run, "next-boot", "autostart")
        self.assertEqual(self.panel.read_bytes(), ORIGINAL)
        self.assertEqual(fix.read_json(root / "receipt.json")["phase"], "uncertain")

    def test_cleanup_disarms_before_refusing_user_edit(self):
        run, root = self.armed_capture()
        self.service.write_bytes(b"user edit")
        with self.assertRaisesRegex(fix.Refused, "Concurrent file change"):
            capture.cleanup(self.home, run)
        self.assertFalse(fix.read_json(root / "arm.json")["enabled"])
        self.assertEqual(self.service.read_bytes(), b"user edit")
        self.assertEqual(fix.capture_active(self.home), run)

    def test_two_launches_restore_once_under_real_lock(self):
        run, root = self.armed_capture()
        context = multiprocessing.get_context("fork")
        barrier = context.Barrier(2)
        children = [context.Process(target=contender, args=(str(self.home), run, barrier, source))
                    for source in ("dbus", "autostart")]
        for child in children:
            child.start()
        for child in children:
            child.join(5)
            if child.is_alive():
                child.terminate()
                child.join(2)
                self.fail("Concurrent capture did not terminate")
            self.assertEqual(child.exitcode, 0)
        self.assertEqual(self.panel.read_bytes(), EXPECTED)
        records = list((root / "runs/next-boot").glob("*-dbus.json"))
        records += list((root / "runs/next-boot").glob("*-autostart.json"))
        self.assertEqual(len(records), 2)


@unittest.skipUnless(Path("/usr/bin/strace").is_file(), "strace is required for tracer checks")
class TracerTests(Fixture):
    def start_probe(self, failure=None):
        run, root = self.armed_capture()
        self.daemon.write_text('''#!/usr/bin/python3
import json,os,pathlib,sys
p=pathlib.Path.home()/'.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml'
print(json.dumps({'pid':os.getpid(),'ppid':os.getppid(),'env':dict(os.environ),
 'argv':sys.argv[1:],'cwd':os.getcwd()}),flush=True)
if sys.stdin.readline().strip()=='rename':
 q=p.with_suffix('.xml.new');q.write_bytes(b'written by probe');q.replace(p)
sys.exit(7)
''')
        command = [sys.executable, str(Path(capture.__file__)), "launch", run, "dbus", "spaced argument"]
        if failure == "capture":
            (root / "arm.json").write_text("{bad")
        elif failure == "tracer":
            runner = '''import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import diagnose_xfce_panel_boot as d
original=d.traced_command
def broken(home,trace,pid):
 c=original(home,trace,pid);c[c.index('-o')+1]=str(trace.parent);return c
d.traced_command=broken
d.launch(Path.home(),sys.argv[2],'dbus',['spaced argument'])
'''
            command = [sys.executable, "-c", runner, str(Path(capture.__file__).parent), run]
        env = dict(os.environ, HOME=str(self.home), PRIVATE_SENTINEL="never-record-this",
                   PYTHONDONTWRITEBYTECODE="1", LC_ALL="C")
        child = subprocess.Popen(command, env=env, cwd=self.home, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(self.stop_child, child)
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            self.assertTrue(selector.select(5), "Probe did not start")
        line = child.stdout.readline()
        if not line:
            out, err = child.communicate(timeout=5)
            self.fail(f"Probe failed: {child.returncode}: {out} {err}")
        self.assertEqual(json.loads(line), {"pid": child.pid, "ppid": os.getpid(), "env": env,
                                           "argv": ["spaced argument"], "cwd": str(self.home)})
        return child, root, run

    @staticmethod
    def stop_child(child):
        if child.poll() is None:
            child.terminate()
            child.communicate(timeout=5)
        for stream in (child.stdin, child.stdout, child.stderr):
            stream.close()

    def test_trace_preserves_launch_and_captures_rename_without_secret(self):
        child, root, run = self.start_probe()
        out, err = child.communicate("rename\n", timeout=5)
        self.assertEqual(child.returncode, 7, err)
        self.assertEqual(self.panel.read_bytes(), b"written by probe")
        traces = list((root / "runs" / capture.current_boot()).glob("*.strace"))
        self.assertEqual(len(traces), 1)
        self.assertIn("rename(", traces[0].read_text())
        for path in traces[0].parent.iterdir():
            self.assertNotIn("never-record-this", path.read_text())

    def test_failures_still_start_original_daemon(self):
        for failure in ("capture", "tracer"):
            with self.subTest(failure=failure):
                child, root, run = self.start_probe(failure)
                out, err = child.communicate("finish\n", timeout=5)
                self.assertEqual(child.returncode, 7)
                self.assertIn("capture failed; starting original daemon", err)
                if failure == "tracer":
                    self.assertIn("Is a directory", err)
                capture.cleanup(self.home, run)

    def test_sigterm_reaches_same_pid(self):
        child, root, run = self.start_probe()
        child.terminate()
        out, err = child.communicate(timeout=5)
        self.assertEqual(child.returncode, -signal.SIGTERM, err)

    def test_cleanup_detaches_without_terminating_daemon(self):
        child, root, run = self.start_probe()
        tracers = capture.owned_tracers(root)
        self.assertEqual(len(tracers), 1)
        descriptor = os.pidfd_open(tracers[0])
        try:
            capture.cleanup(self.home, run)
            with selectors.DefaultSelector() as selector:
                selector.register(descriptor, selectors.EVENT_READ)
                self.assertTrue(selector.select(5), "Tracer did not detach")
        finally:
            os.close(descriptor)
        self.assertIsNone(child.poll())
        out, err = child.communicate("finish\n", timeout=5)
        self.assertEqual(child.returncode, 7, err)


if __name__ == "__main__":
    unittest.main()
