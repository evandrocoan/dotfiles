"""Launcher orchestration with external-command/proc fixtures and real flock.

These tests never launch X clients or contact a service manager. Run the repository
gate inside the documented PID/socket isolation when working on desktop recovery.
"""

import concurrent.futures
import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

import launch_xfwm4 as launcher


class Desktop:
    def __init__(self, root):
        self.root = root
        self.proc = root / "proc"
        self.proc.mkdir()
        (self.proc / "self").mkdir()
        (self.proc / "self" / "cgroup").write_text("0::/user.slice/app.slice/terminal.scope\n")
        self.runtime = root / "run"
        self.runtime.mkdir(mode=0o700)
        self.authority = root / "Xauthority"
        self.authority.write_bytes(b"fixture-cookie")
        self.uid = os.getuid()
        self.scope = "/user.slice/user-1000.slice/session-c7.scope"
        self.env = {"DISPLAY": ":0.0", "XAUTHORITY": str(self.authority),
                    "XDG_CONFIG_DIRS": "/etc/xdg/xdg-xfce:/etc/xdg",
                    "XDG_DATA_DIRS": "/usr/share/xfce4:/usr/share", "XDG_CURRENT_DESKTOP": "XFCE"}
        self.write_process(101, "lightdm", self.scope)
        self.write_process(102, "xfce4-session", self.scope)
        self.session = dict(Id="c7", User=str(self.uid), Display=":0", Remote="no", Desktop="xfce",
                            Scope="session-c7.scope", Leader="101", Type="x11", Class="user",
                            Active="yes", State="active")
        self.sessions = f"c7 {self.uid} fixture seat0 - active no -\n"
        self.unit = "xfwm4-launch-c7.service"
        self.unit_group = f"/user.slice/user-1000.slice/user@1000.service/app.slice/{self.unit}"
        self.state = dict(LoadState="not-found", ActiveState="inactive", SubState="dead",
                          MainPID="0", ControlGroup="", Transient="no")
        self.bus_pid = 102
        self.screens = "number of screens:    1\n"
        self.owner = None
        self.root_override = None
        self.owner_override = None
        self.events = ("xwininfo: Window id: 0x123 (the root window)\n"
                       "  Someone wants these events:\n     PropertyChange\n"
                       "  Do not propagate these events:\n  Override redirection?: No\n")
        self.calls = []
        self.submissions = []
        self.on_submit = self.make_ready
        self.on_command = None
        self.host = launcher.Host(proc=self.proc, runtime=self.runtime, runner=self.run)

    def write_process(self, pid, name, group, *, ticks=500, env=None, executable=None):
        directory = self.proc / str(pid)
        directory.mkdir(exist_ok=True)
        values = ["S", "1"] + ["0"] * 17 + [str(ticks)] + ["0"] * 4
        (directory / "stat").write_text(f"{pid} ({name}) " + " ".join(values))
        (directory / "status").write_text(f"Uid:\t{self.uid}\t{self.uid}\t{self.uid}\t{self.uid}\n")
        (directory / "comm").write_text(name + "\n")
        (directory / "cgroup").write_text(f"0::{group}\n")
        environment = self.env if env is None else env
        (directory / "environ").write_bytes(b"\0".join(f"{k}={v}".encode() for k, v in environment.items()) + b"\0")
        target = directory / "exe"
        if target.is_symlink():
            target.unlink()
        target.symlink_to(executable or f"/usr/bin/{name}")

    def make_ready(self):
        self.write_process(103, "xfwm4", self.unit_group)
        self.owner = 103
        self.state.update(LoadState="loaded", ActiveState="active", SubState="running",
                          MainPID="103", ControlGroup=self.unit_group, Transient="yes")

    def run(self, argv, **kwargs):
        self.calls.append((list(argv), dict(kwargs["env"])))
        if self.on_command:
            self.on_command(argv)
        tool = Path(argv[0]).name
        if tool == "loginctl":
            if argv[1] == "list-sessions":
                output = self.sessions
            else:
                # loginctl accepts repeated properties, not a comma-separated list.
                keys = [arg.removeprefix("--property=") for arg in argv if arg.startswith("--property=")]
                output = "\n".join(f"{key}={self.session[key]}" for key in keys if key in self.session) + "\n"
        elif tool == "busctl":
            output = f"u {self.bus_pid}\n"
        elif tool == "xdpyinfo":
            output = self.screens
        elif tool == "xwininfo":
            output = self.events
        elif tool == "xprop":
            if argv[1] == "-root":
                output = self.root_override or ("_NET_SUPPORTING_WM_CHECK(WINDOW): window id # 0x123\n"
                                               if self.owner else "_NET_SUPPORTING_WM_CHECK:  not found.\n")
            else:
                output = self.owner_override or ("_NET_SUPPORTING_WM_CHECK(WINDOW): window id # 0x123\n"
                                                f"_NET_WM_PID(CARDINAL) = {self.owner}\n")
        elif tool == "systemctl":
            output = "\n".join(f"{key}={value}" for key, value in self.state.items()) + "\n"
        elif tool == "systemd-run":
            self.submissions.append(list(argv))
            self.on_submit()
            output = f"Running as unit: {self.unit}\n"
        else:
            raise AssertionError(f"Unexpected command: {argv}")
        return subprocess.CompletedProcess(argv, 0, output, "")


class LauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.desktop = Desktop(Path(temporary.name))
        self.addCleanup(patch.stopall)
        patch("subprocess.run", side_effect=AssertionError("Real subprocess forbidden in fixtures")).start()
        patch.dict(os.environ, {"DISPLAY": ":99", "SESSION_MANAGER": "untrusted", "LD_PRELOAD": "untrusted"}).start()

    def run_launcher(self, **kwargs):
        return launcher.launch(self.desktop.host, **kwargs)

    def assert_refused(self, text):
        with self.assertRaisesRegex(launcher.Refused, text):
            self.run_launcher(start=True, timeout=0)
        self.assertEqual(self.desktop.submissions, [])

    def test_default_check_creates_no_lock_or_unit(self):
        result = self.run_launcher()
        self.assertIn("no verified window manager", result)
        self.assertEqual(list(self.desktop.runtime.iterdir()), [])
        self.assertEqual(self.desktop.submissions, [])

    def test_existing_manager_is_preserved(self):
        self.desktop.write_process(103, "other-wm", self.desktop.scope)
        self.desktop.owner = 103
        self.assertEqual(self.run_launcher(start=True),
                         "Session c7: window manager present (PID 103); unchanged.")
        self.assertEqual(self.desktop.submissions, [])

    def test_absent_manager_starts_once_with_verified_unit_and_clean_environment(self):
        self.assertEqual(self.run_launcher(start=True),
                         "Session c7: XFWM ready (PID 103, xfwm4-launch-c7.service).")
        self.assertEqual(len(self.desktop.submissions), 1)
        command = self.desktop.submissions[0]
        self.assertEqual(command[:10], ["/usr/bin/systemd-run", "--user", "--no-ask-password",
                                       "--collect", "--service-type=exec", "--expand-environment=no",
                                       "--unit=xfwm4-launch-c7.service", "--property=Restart=no",
                                       "--", "/usr/bin/env"])
        start = command.index("-i") + 1
        end = command.index("/usr/bin/xfwm4")
        environment = dict(value.split("=", 1) for value in command[start:end])
        self.assertEqual(environment["DISPLAY"], ":0.0")
        self.assertEqual(environment["XAUTHORITY"], str(self.desktop.authority))
        self.assertEqual(environment["XDG_CONFIG_DIRS"], "/etc/xdg/xdg-xfce:/etc/xdg")
        self.assertNotIn("LD_PRELOAD", environment)
        self.assertNotIn("SESSION_MANAGER", environment)
        self.assertEqual(command[end:], ["/usr/bin/xfwm4", "--sm-client-disable"])
        self.assertNotIn("--replace", command)
        lock = self.desktop.runtime / "xfwm4-launch-c7.lock"
        inode = lock.stat().st_ino
        self.assertIn("unchanged", self.run_launcher(start=True))
        self.assertEqual(len(self.desktop.submissions), 1)
        self.assertEqual(lock.stat().st_ino, inode)

    def test_non_ewmh_manager_blocks_submission(self):
        self.desktop.events = self.desktop.events.replace("PropertyChange", "SubstructureRedirect")
        self.assert_refused("Root redirection is occupied")

    def test_unreadable_root_ownership_blocks_submission(self):
        self.desktop.events = "incomplete output"
        self.assert_refused("Cannot inspect root event ownership")

    def test_unrecognized_root_event_blocks_submission(self):
        self.desktop.events = self.desktop.events.replace("PropertyChange", "unrecognized-event")
        self.assert_refused("Unrecognized root event ownership")

    def test_root_probe_failure_blocks_submission(self):
        def fail(argv):
            if Path(argv[0]).name == "xwininfo":
                raise subprocess.TimeoutExpired(argv, 5)
        self.desktop.on_command = fail
        self.assert_refused("timed out")

    def test_zero_stale_and_unrecognized_root_properties_block(self):
        for value, message in (("_NET_SUPPORTING_WM_CHECK(WINDOW): window id # 0x0", "Stale zero"),
                               ("garbage", "Cannot establish absence")):
            with self.subTest(value=value):
                self.desktop.root_override = value
                self.assert_refused(message)

    def test_owner_self_check_blocks_stale_property(self):
        self.desktop.make_ready()
        self.desktop.owner_override = ("_NET_SUPPORTING_WM_CHECK(WINDOW): window id # 0x999\n"
                                       "_NET_WM_PID(CARDINAL) = 103\n")
        self.assert_refused("Unverifiable WM owner")

    def test_foreign_owner_credentials_are_rejected(self):
        self.desktop.make_ready()
        foreign = self.desktop.uid + 1
        (self.desktop.proc / "103" / "status").write_text(f"Uid:\t{foreign}\t{foreign}\t{foreign}\t{foreign}\n")
        self.assert_refused("incompatible credentials")

    def test_owner_on_another_display_is_rejected(self):
        self.desktop.make_ready()
        self.desktop.write_process(103, "xfwm4", self.desktop.unit_group, env={"DISPLAY": ":1"})
        self.assert_refused("different display")

    def test_xfwm_without_properties_blocks_duplicate(self):
        self.desktop.write_process(103, "xfwm4", self.desktop.scope)
        self.assert_refused("XFWM process exists")

    def test_invalid_session_gates(self):
        cases = {"Remote": "yes", "Desktop": "gnome", "Scope": "session-other.scope",
                 "Type": "wayland", "Class": "greeter", "Active": "no", "State": "closing",
                 "User": "2000"}
        for key, value in cases.items():
            with self.subTest(key=key):
                with patch.dict(self.desktop.session, {key: value}):
                    self.assert_refused("active local XFCE X11")

    def test_multiple_graphical_sessions_are_ambiguous(self):
        self.desktop.sessions += f"c8 {self.desktop.uid} fixture seat1 - active no -\n"
        self.assert_refused("exactly one graphical session")

    def test_missing_graphical_session_is_rejected(self):
        self.desktop.sessions = ""
        self.assert_refused("exactly one graphical session")

    def test_bus_owner_must_match_anchor(self):
        self.desktop.bus_pid = 777
        self.assert_refused("bus owner does not match")

    def test_screen_count_must_be_exactly_one(self):
        for value in ("number of screens:    2\n", "garbage", ""):
            with self.subTest(value=value):
                self.desktop.screens = value
                self.assert_refused("Exactly one X screen")

    def test_display_mismatch_is_rejected(self):
        self.desktop.session["Display"] = ":1"
        self.assert_refused("displays disagree")

    def test_remote_display_is_rejected(self):
        self.desktop.session["Display"] = "example:0"
        self.assert_refused("Only a local X display")

    def test_wrong_anchor_executable_is_rejected(self):
        self.desktop.write_process(102, "xfce4-session", self.desktop.scope, executable="/tmp/fake")
        self.assert_refused("Unexpected XFCE session executable")

    def test_ambiguous_anchor_is_rejected(self):
        self.desktop.write_process(104, "xfce4-session", self.desktop.scope)
        self.assert_refused("one live XFCE session process")

    def test_missing_authority_is_rejected(self):
        self.desktop.authority.unlink()
        with self.assertRaises(FileNotFoundError):
            self.run_launcher(start=True)
        self.assertEqual(self.desktop.submissions, [])

    def test_root_user_is_rejected_before_external_reads(self):
        self.desktop.host.uid = 0
        self.assert_refused("without sudo")
        self.assertEqual(self.desktop.calls, [])

    def test_unreadable_process_is_not_silently_ignored(self):
        original = Path.read_text
        def read(path, *args, **kwargs):
            if path == self.desktop.proc / "102" / "comm":
                raise PermissionError("fixture denied")
            return original(path, *args, **kwargs)
        with patch.object(Path, "read_text", read), self.assertRaisesRegex(PermissionError, "fixture denied"):
            self.run_launcher(start=True)
        self.assertEqual(self.desktop.submissions, [])

    def test_changed_anchor_identity_before_submission_is_rejected(self):
        count = 0
        def change(argv):
            nonlocal count
            if Path(argv[0]).name == "loginctl" and argv[1] == "list-sessions":
                count += 1
                if count == 3:
                    self.desktop.write_process(102, "xfce4-session", self.desktop.scope, ticks=501)
        self.desktop.on_command = change
        self.assert_refused("session changed before launch")

    def test_owner_appearing_before_submission_is_preserved(self):
        count = 0
        def appear(argv):
            nonlocal count
            if Path(argv[0]).name == "xprop" and argv[1] == "-root":
                count += 1
                if count == 2:
                    self.desktop.make_ready()
        self.desktop.on_command = appear
        self.assertIn("appeared; unchanged", self.run_launcher(start=True))
        self.assertEqual(self.desktop.submissions, [])

    def test_loaded_unit_blocks_resubmission(self):
        for state in ("activating", "failed", "inactive"):
            with self.subTest(state=state):
                self.desktop.state.update(LoadState="loaded", ActiveState=state)
                self.assert_refused("already exists")

    def test_submission_timeout_reconciles_ready_owner(self):
        def delayed_ack():
            self.desktop.make_ready()
            raise subprocess.TimeoutExpired("systemd-run", 5)
        self.desktop.on_submit = delayed_ack
        self.assertIn("XFWM ready", self.run_launcher(start=True))
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_no_ack_and_collected_unit_is_uncertain_without_retry(self):
        def lost_ack():
            raise subprocess.TimeoutExpired("systemd-run", 5)
        self.desktop.on_submit = lost_ack
        with self.assertRaisesRegex(launcher.Refused, "Startup not confirmed.*not-found/inactive.*No retry"):
            self.run_launcher(start=True, timeout=0)
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_failed_exec_is_reported_without_retry_or_rollback(self):
        def failed():
            self.desktop.state.update(LoadState="loaded", ActiveState="failed")
        self.desktop.on_submit = failed
        with self.assertRaisesRegex(launcher.Refused, "Startup failed"):
            self.run_launcher(start=True, timeout=0)
        self.assertEqual(len(self.desktop.submissions), 1)
        self.assertFalse(any("stop" in command or "reset-failed" in command for command, _ in self.desktop.calls))

    def test_mainpid_mismatch_is_never_reported_ready(self):
        def wrong_pid():
            self.desktop.make_ready()
            self.desktop.state["MainPID"] = "999"
        self.desktop.on_submit = wrong_pid
        with self.assertRaisesRegex(launcher.Refused, "Startup not confirmed.*owner=103"):
            self.run_launcher(start=True, timeout=0)
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_wrong_cgroup_is_never_reported_ready(self):
        def wrong_group():
            self.desktop.make_ready()
            self.desktop.write_process(103, "xfwm4", self.desktop.scope)
        self.desktop.on_submit = wrong_group
        with self.assertRaisesRegex(launcher.Refused, "Startup not confirmed"):
            self.run_launcher(start=True, timeout=0)
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_session_change_after_submission_is_reported_without_cleanup(self):
        def changed():
            self.desktop.make_ready()
            self.desktop.write_process(102, "xfce4-session", self.desktop.scope, ticks=501)
        self.desktop.on_submit = changed
        with self.assertRaisesRegex(launcher.Refused, "session changed after submission"):
            self.run_launcher(start=True, timeout=0)
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_slow_start_requires_readiness_not_ack(self):
        self.desktop.on_submit = lambda: self.desktop.state.update(LoadState="loaded", ActiveState="activating")
        waits = []
        def advance(delay):
            waits.append(delay)
            self.desktop.make_ready()
        with patch.object(launcher.time, "sleep", advance):
            self.assertIn("XFWM ready", self.run_launcher(start=True))
        self.assertEqual(waits, [0.1])
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_session_registration_requires_authenticated_caller(self):
        (self.desktop.proc / "self" / "cgroup").write_text(f"0::{self.desktop.scope}\n")
        manager = "local/host:@/tmp/.ICE-unix/102,unix/host:/tmp/.ICE-unix/102"
        with patch.dict(os.environ, {"SESSION_MANAGER": manager}):
            self.assertIn("XFWM ready", self.run_launcher(start=True, sm_client_id="saved-client"))
        command = self.desktop.submissions[0]
        self.assertIn(f"SESSION_MANAGER={manager}", command)
        self.assertEqual(command[-2:], ["/usr/bin/xfwm4", "--sm-client-id=saved-client"])

    def test_session_client_id_requires_matching_caller_scope(self):
        manager = "local/host:@/tmp/.ICE-unix/102,unix/host:/tmp/.ICE-unix/102"
        with patch.dict(os.environ, {"SESSION_MANAGER": manager}):
            with self.assertRaisesRegex(launcher.Refused, "authenticated XFCE session caller"):
                self.run_launcher(start=True, sm_client_id="stale", timeout=0)
        self.assertEqual(self.desktop.submissions, [])

    def test_session_client_id_requires_matching_endpoint(self):
        (self.desktop.proc / "self" / "cgroup").write_text(f"0::{self.desktop.scope}\n")
        for manager in ("local/host:@/tmp/.ICE-unix/999", ""):
            with self.subTest(manager=manager), patch.dict(os.environ, {"SESSION_MANAGER": manager}):
                with self.assertRaisesRegex(launcher.Refused, "authenticated XFCE session caller"):
                    self.run_launcher(start=True, sm_client_id="stale", timeout=0)
                self.assertEqual(self.desktop.submissions, [])

    def test_unsafe_lock_is_rejected(self):
        lock = self.desktop.runtime / "xfwm4-launch-c7.lock"
        lock.write_text("")
        lock.chmod(0o644)
        self.assert_refused("Unsafe session lock")

    def test_symlink_lock_is_not_followed(self):
        lock = self.desktop.runtime / "xfwm4-launch-c7.lock"
        lock.symlink_to(self.desktop.authority)
        with self.assertRaises(OSError):
            self.run_launcher(start=True)
        self.assertEqual(self.desktop.authority.read_bytes(), b"fixture-cookie")
        self.assertEqual(self.desktop.submissions, [])

    def test_lock_wait_expires_without_submission(self):
        session = self.desktop.host.discover()
        with launcher.session_lock(self.desktop.host, session, 0):
            self.assert_refused("lock wait expired")

    def test_two_real_lock_contenders_only_submit_once(self):
        entered = threading.Event()
        release = threading.Event()
        contended = threading.Event()
        real_flock = launcher.fcntl.flock
        def delayed_ready():
            entered.set()
            if not release.wait(5):
                raise AssertionError("test failed to release first submission")
            self.desktop.make_ready()
        def observed_flock(*args):
            try:
                return real_flock(*args)
            except BlockingIOError:
                contended.set()
                raise
        self.desktop.on_submit = delayed_ready
        with patch.object(launcher.fcntl, "flock", observed_flock), concurrent.futures.ThreadPoolExecutor(2) as pool:
            first = pool.submit(self.run_launcher, start=True)
            try:
                self.assertTrue(entered.wait(5), "first invocation did not reach submission")
                second = pool.submit(self.run_launcher, start=True)
                self.assertTrue(contended.wait(5), "second invocation did not contend on real flock")
                self.assertEqual(len(self.desktop.submissions), 1)
            finally:
                release.set()
            self.assertIn("XFWM ready", first.result(5))
            self.assertIn("unchanged", second.result(5))
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_cli_default_uses_read_only_flow(self):
        output = io.StringIO()
        with patch.object(launcher, "Host", return_value=self.desktop.host), contextlib.redirect_stdout(output):
            self.assertEqual(launcher.main([]), 0)
        self.assertIn("No action taken", output.getvalue())
        self.assertEqual(list(self.desktop.runtime.iterdir()), [])
        self.assertEqual(self.desktop.submissions, [])


if __name__ == "__main__":
    unittest.main()
