"""Launcher orchestration with external-command/proc fixtures and real flock.

These tests never launch X clients. Opt-in lifecycle tests use disposable systemd units. Run the repository
gate inside the documented PID/socket isolation when working on desktop recovery.
"""

import concurrent.futures
import contextlib
import io
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from types import SimpleNamespace
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
        self.scope = f"/user.slice/user-{self.uid}.slice/session-c7.scope"
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
        self.unit_group = f"/user.slice/user-{self.uid}.slice/user@{self.uid}.service/app.slice/{self.unit}"
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
        self.submission_environments = []
        self.manager_environment = ["MANAGER_ONLY=stale", "LC_ALL=C", "SESSION_MANAGER=stale"]
        self.on_submit = self.make_ready
        self.on_command = None
        self.host = launcher.Host(proc=self.proc, runtime=self.runtime, runner=self.run, spawner=self.spawn)

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
        if pid == 102:
            self.write_process(106, "xfce4-terminal", group, ticks=ticks, env=environment)

    def spawn(self, argv, **kwargs):
        self.calls.append((list(argv), dict(kwargs["env"])))
        self.submissions.append(list(argv))
        self.submission_environments.append(dict(kwargs["env"]))
        self.unit = next(arg.split("=", 1)[1] for arg in argv if arg.startswith("--unit="))
        self.unit_group = f"/user.slice/user-{self.uid}.slice/user@{self.uid}.service/app.slice/{self.unit}"
        self.write_process(110, "systemd-run", "/caller.scope")
        self.on_submit()
        return SimpleNamespace(pid=110, poll=lambda: None)

    def make_ready(self):
        self.write_process(103, "xfwm4", self.unit_group)
        self.owner = 103
        self.state.update(LoadState="loaded", ActiveState="active", SubState="running",
                          MainPID="103", ControlGroup=self.unit_group, Transient="yes",
                          KillMode="process", Restart="no")

    def remove_process(self, pid):
        directory = self.proc / str(pid)
        for path in directory.iterdir():
            path.unlink()
        directory.rmdir()

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
            if "get-property" in argv:
                output = json.dumps({"type": "as", "data": self.manager_environment})
            else:
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
            state = self.state if argv[4] == self.unit else dict(LoadState="not-found", ActiveState="inactive", MainPID="0", ControlGroup="", Transient="no")
            output = "\n".join(f"{key}={value}" for key, value in state.items()) + "\n"
        else:
            raise AssertionError(f"Unexpected command: {argv}")
        return subprocess.CompletedProcess(argv, 0, output, "")

    def submitted_environment(self, command):
        index = next(index for index, submission in enumerate(self.submissions) if submission is command)
        return self.submission_environments[index]


class LauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.desktop = Desktop(Path(temporary.name))
        self.addCleanup(patch.stopall)
        patch.object(launcher.uuid, "uuid4", return_value=SimpleNamespace(hex="a" * 32)).start()
        patch("subprocess.Popen", side_effect=AssertionError("Real spawn forbidden in fixtures")).start()
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

    def test_absent_manager_starts_once_with_verified_unit_and_session_environment(self):
        self.assertEqual(self.run_launcher(start=True),
                         "Session c7: XFWM ready (PID 103, xfwm4-launch-c7-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.scope).")
        self.assertEqual(len(self.desktop.submissions), 1)
        command = self.desktop.submissions[0]
        self.assertEqual(command[:3], ["/usr/bin/systemd-cat",
                         "--identifier=xfwm4-launch-c7-" + "a" * 32 + ".scope", "/usr/bin/systemd-run"])
        self.assertIn("--scope", command)
        self.assertNotIn("--service-type=exec", command)
        end = command.index("/usr/bin/xfwm4")
        environment = self.desktop.submitted_environment(command)
        self.assertEqual(environment["DISPLAY"], ":0.0")
        self.assertEqual(environment["XAUTHORITY"], str(self.desktop.authority))
        self.assertEqual(environment["XDG_CONFIG_DIRS"], "/etc/xdg/xdg-xfce:/etc/xdg")
        self.assertNotIn("LD_PRELOAD", environment)
        self.assertNotIn("SESSION_MANAGER", environment)
        self.assertNotIn("MANAGER_ONLY", environment)
        self.assertEqual(command[end:], ["/usr/bin/xfwm4", "--sm-client-disable"])
        self.assertNotIn("--replace", command)
        lock = self.desktop.runtime / "xfwm4-launch-c7.lock"
        inode = lock.stat().st_ino
        self.assertIn("unchanged", self.run_launcher(start=True))
        self.assertEqual(len(self.desktop.submissions), 1)
        self.assertEqual(lock.stat().st_ino, inode)

    def test_graphical_launch_preserves_verified_session_locale(self):
        locale = {
            "LANG": "en_US.UTF-8", "LANGUAGE": "en_US:pt_BR", "LC_ALL": "en_US.UTF-8",
            "LC_CTYPE": "pt_BR.UTF-8", "LC_NUMERIC": "pt_BR.UTF-8", "LC_TIME": "pt_BR.UTF-8",
            "LC_COLLATE": "pt_BR.UTF-8", "LC_MONETARY": "pt_BR.UTF-8", "LC_MESSAGES": "pt_BR.UTF-8",
            "LC_PAPER": "pt_BR.UTF-8", "LC_NAME": "pt_BR.UTF-8", "LC_ADDRESS": "pt_BR.UTF-8",
            "LC_TELEPHONE": "pt_BR.UTF-8", "LC_MEASUREMENT": "pt_BR.UTF-8", "LC_IDENTIFICATION": "pt_BR.UTF-8",
        }
        self.desktop.env.update(locale)
        self.desktop.write_process(102, "xfce4-session", self.desktop.scope)
        self.assertIn("XFWM ready", self.run_launcher(start=True))
        self.assertEqual(len(self.desktop.submissions), 1)
        command = self.desktop.submissions[0]
        environment = self.desktop.submitted_environment(command)
        self.assertEqual({key: value for key, value in environment.items()
                          if key in {"LANG", "LANGUAGE"} or key.startswith("LC_")}, locale)
        self.assertNotIn("LD_PRELOAD", environment)
        for argv, env in self.desktop.calls:
            if Path(argv[0]).name != "systemd-cat":
                self.assertEqual(env["LC_ALL"], "C", argv)

    def test_graphical_launch_preserves_complete_session_environment(self):
        additions = {"SSH_AUTH_SOCK": "/run/session/keyring/ssh",
                     "PATH": "/home/fixture/bin:/usr/bin:/bin",
                     "SESSION_CUSTOM_VALUE": "spaces = equals\nand a newline",
                     "LD_LIBRARY_PATH": "/home/fixture/lib", "LC_CUSTOM": "session-value"}
        self.desktop.env.update(additions)
        self.desktop.write_process(102, "xfce4-session", self.desktop.scope)
        self.assertIn("XFWM ready", self.run_launcher(start=True))
        command = self.desktop.submissions[0]
        environment = self.desktop.submitted_environment(command)
        for key, value in additions.items():
            self.assertEqual(environment.get(key), value, key)
        self.assertNotIn("LD_PRELOAD", environment)

    def test_session_client_supplies_environment_added_after_session_start(self):
        environment = dict(self.desktop.env, SSH_AUTH_SOCK="/run/session/keyring/ssh",
                           SESSION_LATE_VALUE="from the desktop session",
                           SESSION_MANAGER="local/host:@/tmp/.ICE-unix/102")
        self.desktop.write_process(105, "xfsettingsd", self.desktop.scope, ticks=510, env=environment)
        self.assertIn("XFWM ready", self.run_launcher(start=True))
        command = self.desktop.submissions[0]
        submitted = self.desktop.submitted_environment(command)
        self.assertEqual(submitted["SSH_AUTH_SOCK"], "/run/session/keyring/ssh")
        self.assertEqual(submitted["SESSION_LATE_VALUE"], "from the desktop session")
        self.assertNotIn("SESSION_MANAGER", submitted)

    def test_unrelated_or_recovered_clients_do_not_supply_session_environment(self):
        cases = ((self.desktop.unit_group, "/usr/bin/xfsettingsd", ":0.0", 510),
                 (self.desktop.scope, "/tmp/xfsettingsd", ":0.0", 510),
                 (self.desktop.scope, "/usr/bin/xfsettingsd", ":1", 510),
                 (self.desktop.scope, "/usr/bin/xfsettingsd", ":0.0", 499))
        for group, executable, display, ticks in cases:
            with self.subTest(group=group, executable=executable, display=display, ticks=ticks):
                self.desktop.write_process(105, "xfsettingsd", group, executable=executable,
                                           ticks=ticks, env=dict(self.desktop.env, DISPLAY=display,
                                                                SESSION_LATE_VALUE="wrong source"))
                environment = dict(self.desktop.host.discover().environment)
                self.assertNotIn("SESSION_LATE_VALUE", environment)

    def test_environment_source_change_before_submission_is_rejected(self):
        self.desktop.write_process(105, "xfsettingsd", self.desktop.scope, ticks=510)
        calls = 0
        def change(argv):
            nonlocal calls
            if Path(argv[0]).name == "loginctl" and argv[1] == "list-sessions":
                calls += 1
                if calls == 3:
                    self.desktop.write_process(105, "xfsettingsd", self.desktop.scope, ticks=511)
        self.desktop.on_command = change
        self.assert_refused("session changed before launch")

    def test_environment_values_are_imported_without_command_line_exposure(self):
        self.desktop.env.update(SESSION_SECRET="secret value\nwith spaces = and $literal",
                                SESSION_MANAGER="local/host:@/tmp/.ICE-unix/102")
        self.desktop.write_process(102, "xfce4-session", self.desktop.scope)
        self.assertIn("XFWM ready", self.run_launcher(start=True))
        command = self.desktop.submissions[0]
        self.assertFalse(any(arg.startswith("--setenv=") for arg in command))
        self.assertEqual(self.desktop.submitted_environment(command)["SESSION_SECRET"],
                         "secret value\nwith spaces = and $literal")
        self.assertFalse(any("secret value" in argument for argument in command))
        self.assertNotIn("SESSION_MANAGER", self.desktop.submitted_environment(command))

    def test_manager_environment_does_not_affect_scope_inheritance(self):
        self.desktop.manager_environment = [7]
        self.assertIn("XFWM ready", self.run_launcher(start=True))
        self.assertFalse(any("get-property" in argv for argv, _ in self.desktop.calls))

    def test_initial_session_snapshot_is_not_used_as_post_login_environment(self):
        self.desktop.remove_process(106)
        self.assert_refused("cannot reconstruct the post-login environment")

    def test_saved_environment_survives_loss_of_original_clients(self):
        self.desktop.env["SSH_AUTH_SOCK"] = "/session/agent"
        self.desktop.env["SESSION_CUSTOM"] = "complete environment"
        self.desktop.write_process(106, "xfce4-terminal", self.desktop.scope)
        self.run_launcher(start=True)
        self.desktop.remove_process(106)
        session = self.desktop.host.discover()
        self.assertIsNone(session.environment_source)
        self.assertEqual(dict(session.environment)["SSH_AUTH_SOCK"], "/session/agent")
        self.assertEqual(dict(session.environment)["SESSION_CUSTOM"], "complete environment")
        self.assertEqual(self.desktop.host.environment_path(session.identifier, session.anchor).stat().st_mode & 0o777, 0o600)

    def test_environment_cache_is_bound_to_session_process_identity(self):
        session = self.desktop.host.discover()
        self.desktop.host.save_environment(session)
        self.desktop.write_process(102, "xfce4-session", self.desktop.scope, ticks=501)
        self.desktop.remove_process(106)
        self.assert_refused("cannot reconstruct")

    def test_environment_cache_symlink_is_refused(self):
        session = self.desktop.host.discover()
        self.desktop.host.environment_path(session.identifier, session.anchor).symlink_to(self.desktop.authority)
        self.desktop.remove_process(106)
        with self.assertRaises(OSError):
            self.run_launcher(start=True)
        self.assertEqual(self.desktop.authority.read_bytes(), b"fixture-cookie")
        self.assertEqual(self.desktop.submissions, [])

    def test_confirmed_exit_allows_new_scope_while_old_scope_remains_active(self):
        self.run_launcher(start=True)
        old_unit = self.desktop.unit
        self.desktop.remove_process(103)
        self.desktop.owner = None
        with patch.object(launcher.uuid, "uuid4", return_value=SimpleNamespace(hex="b" * 32)):
            self.assertIn("XFWM ready", self.run_launcher(start=True))
        self.assertNotEqual(old_unit, self.desktop.unit)
        self.assertEqual(len(self.desktop.submissions), 2)
        self.assertFalse(any("stop" in argv or "kill" in argv for argv, _ in self.desktop.calls))

    def test_late_ready_launch_is_reconciled_before_its_later_exit(self):
        self.desktop.on_submit = lambda: None
        with self.assertRaisesRegex(launcher.Refused, "Startup not confirmed"):
            self.run_launcher(start=True, timeout=0)
        self.desktop.make_ready()
        self.assertIn("unchanged", self.run_launcher(start=True))
        record = self.desktop.host.read_record(self.desktop.host.receipt_path("xfwm4-launch-c7.service"))
        self.assertIs(record["ready"], True)
        self.assertEqual(record["owner"], [103, 500])

    def test_interrupted_submission_before_pid_record_blocks_duplicate(self):
        host = self.desktop.host
        host.write_record(host.receipt_path("xfwm4-launch-c7.service"),
                          {"unit": "xfwm4-launch-c7-" + "a" * 32 + ".scope", "ready": False,
                           "launcher": None, "owner": None})
        self.assert_refused("Outstanding launch")

    def test_graphical_launch_preserves_unset_lc_all_and_ignores_caller_locale(self):
        locale = {"LANG": "pt_BR.UTF-8", "LANGUAGE": "pt_BR:en_US", "LC_NUMERIC": "en_US.UTF-8"}
        self.desktop.env.update(locale)
        self.desktop.write_process(102, "xfce4-session", self.desktop.scope)
        with patch.dict(os.environ, {"LANG": "de_DE.UTF-8", "LANGUAGE": "de_DE", "LC_ALL": "C"}):
            self.assertIn("XFWM ready", self.run_launcher(start=True))
        command = self.desktop.submissions[0]
        environment = self.desktop.submitted_environment(command)
        self.assertEqual({key: value for key, value in environment.items()
                          if key in {"LANG", "LANGUAGE"} or key.startswith("LC_")}, locale)
        for argv, env in self.desktop.calls:
            if Path(argv[0]).name != "systemd-cat":
                self.assertEqual(env["LC_ALL"], "C", argv)

    def test_graphical_launch_does_not_invent_locale_variables(self):
        self.assertIn("XFWM ready", self.run_launcher(start=True))
        command = self.desktop.submissions[0]
        environment = self.desktop.submitted_environment(command)
        self.assertEqual({key: value for key, value in environment.items()
                          if key in {"LANG", "LANGUAGE"} or key.startswith("LC_")}, {})
        for argv, env in self.desktop.calls:
            if Path(argv[0]).name != "systemd-cat":
                self.assertEqual(env["LC_ALL"], "C", argv)

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

    def test_pending_submission_blocks_another_invocation(self):
        self.desktop.on_submit = lambda: None
        with self.assertRaisesRegex(launcher.Refused, "Startup not confirmed.*No retry"):
            self.run_launcher(start=True, timeout=0)
        with self.assertRaisesRegex(launcher.Refused, "Outstanding launch"):
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

    def test_scope_readiness_uses_owner_membership_without_mainpid(self):
        def no_mainpid():
            self.desktop.make_ready()
            del self.desktop.state["MainPID"]
        self.desktop.on_submit = no_mainpid
        self.assertIn("XFWM ready", self.run_launcher(start=True))
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
        self.assertEqual(self.desktop.submitted_environment(command)["SESSION_MANAGER"], manager)
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



@unittest.skipUnless(os.environ.get("XFCE_RECOVERY_SYSTEMD_TESTS") == "1",
                     "opt-in tests need the user's systemd manager; only disposable processes are started")
class ScopeLifecycleTests(unittest.TestCase):
    """Real production scope transport and process lifetime, without X or desktop clients."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="xfce-scope-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(mode=0o700)
        real_runtime = f"/run/user/{os.getuid()}"
        self.env = {"HOME": str(self.root), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
                    "XDG_RUNTIME_DIR": real_runtime,
                    "DBUS_SESSION_BUS_ADDRESS": f"unix:path={real_runtime}/bus",
                    "SSH_AUTH_SOCK": str(self.root / "fixture-agent"),
                    "FIXTURE_CUSTOM": "spaces = and $literal\nsecond line"}
        self.host = launcher.Host(runtime=self.runtime)
        self.host.base_env.update(self.env)
        self.session = SimpleNamespace(environment=tuple(self.env.items()))
        self.units = []
        self.addCleanup(self.cleanup_units)
        self.payload = self.root / "payload.py"
        self.payload.write_text("""
import json, os, subprocess, sys, time
from pathlib import Path
root = Path(sys.argv[1])
def publish(name, value):
    path = root / name
    temporary = root / (name + ".tmp")
    temporary.write_text(json.dumps(value))
    temporary.replace(path)
if len(sys.argv) == 2:
    subprocess.Popen([sys.executable, __file__, str(root), "child"], stdin=subprocess.DEVNULL)
    publish("parent.json", {"pid": os.getpid()})
else:
    publish("child.json", {"pid": os.getpid(),
        "env": {k: os.environ.get(k) for k in ("SSH_AUTH_SOCK", "FIXTURE_CUSTOM", "LANG", "LC_ALL")}})
while True:
    time.sleep(3600)
""")

    def wait_for(self, predicate, message):
        deadline = time.monotonic() + 8
        while True:
            result = predicate()
            if result:
                return result
            if time.monotonic() >= deadline:
                self.fail(message)
            time.sleep(0.02)  # Poll an explicit process/file condition, not an ordering assumption.

    def cleanup_units(self):
        for unit in self.units:
            result = subprocess.run(["/usr/bin/systemctl", "--user", "stop", unit],
                                    env=self.env, capture_output=True, text=True, timeout=10)
            if result.returncode and "not loaded" not in result.stderr:
                self.fail(result.stderr)
        for child in self.host.children:
            child.wait(timeout=5)

    def payload_processes(self, directory):
        self.wait_for(lambda: all((directory / name).exists() for name in ("parent.json", "child.json")),
                      "fixture processes did not publish their identities")
        parent = json.loads((directory / "parent.json").read_text())
        child = json.loads((directory / "child.json").read_text())
        return self.host.process(parent["pid"]), self.host.process(child["pid"]), child["env"]

    def exercise_exit(self, termination_signal):
        legacy = f"xfce-recovery-test-{uuid.uuid4().hex}.service"
        first = self.root / "first"
        first.mkdir()
        unit = self.host.submit_unit(legacy, self.env, [sys.executable, str(self.payload), str(first)])
        self.units.append(unit)
        parent, child, environment = self.payload_processes(first)
        self.assertEqual(environment, {"SSH_AUTH_SOCK": self.env["SSH_AUTH_SOCK"],
                                       "FIXTURE_CUSTOM": self.env["FIXTURE_CUSTOM"],
                                       "LANG": "C.UTF-8", "LC_ALL": None})
        state = self.host.unit_state(self.session, unit=unit)
        self.assertTrue(self.host.scope_ready(state, unit, parent))
        self.host.confirm_launch(legacy, unit, parent)
        os.kill(parent.pid, termination_signal)
        self.wait_for(lambda: not self.host.same_process([parent.pid, parent.ticks]), "parent did not exit")
        self.assertTrue(self.host.same_process([child.pid, child.ticks]), "parent exit killed its child")
        self.assertEqual(self.host.unit_state(self.session, unit=unit)["ActiveState"], "active")
        self.host.available(self.session, legacy)
        second = self.root / "second"
        second.mkdir()
        new_unit = self.host.submit_unit(legacy, self.env, [sys.executable, str(self.payload), str(second)])
        self.units.append(new_unit)
        new_parent, _, _ = self.payload_processes(second)
        self.assertNotEqual(new_unit, unit)
        self.assertTrue(self.host.scope_ready(self.host.unit_state(self.session, unit=new_unit), new_unit, new_parent))
        self.assertTrue(self.host.same_process([child.pid, child.ticks]), "new launch killed the old application")

    def test_parent_termination_preserves_child_and_allows_another_launch(self):
        self.exercise_exit(signal.SIGTERM)

    def test_parent_crash_preserves_child_and_allows_another_launch(self):
        self.exercise_exit(signal.SIGKILL)

    def test_old_service_lifecycle_reproduces_child_loss(self):
        unit = f"xfce-recovery-test-control-{uuid.uuid4().hex}.service"
        self.units.append(unit)
        command = ["/usr/bin/systemd-run", "--user", "--no-ask-password", "--collect",
                   "--service-type=exec", f"--unit={unit}", "--", sys.executable,
                   str(self.payload), str(self.root)]
        result = subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=8)
        self.assertEqual(result.returncode, 0, result.stderr)
        parent, child, _ = self.payload_processes(self.root)
        os.kill(parent.pid, signal.SIGTERM)
        self.wait_for(lambda: not self.host.same_process([child.pid, child.ticks]),
                      "negative control did not reproduce the old service killing its child")

    def test_legacy_protection_preserves_child_without_restarting_parent(self):
        unit = f"xfce-recovery-test-migration-{uuid.uuid4().hex}.service"
        self.units.append(unit)
        result = subprocess.run(["/usr/bin/systemd-run", "--user", "--no-ask-password", "--collect",
                                 "--service-type=exec", f"--unit={unit}", "--", sys.executable,
                                 str(self.payload), str(self.root)],
                                env=self.env, capture_output=True, text=True, timeout=8)
        self.assertEqual(result.returncode, 0, result.stderr)
        parent, child, _ = self.payload_processes(self.root)
        actual_host = launcher.Host()
        dropin = actual_host.runtime / "systemd/user" / (unit + ".d") / "90-xfce-recovery-preserve-apps.conf"
        def cleanup_dropin():
            if dropin.exists():
                dropin.unlink()
                dropin.parent.rmdir()
                result = subprocess.run(["/usr/bin/systemctl", "--user", "daemon-reload"],
                                        env=self.env, capture_output=True, text=True, timeout=8)
                self.assertEqual(result.returncode, 0, result.stderr)
        self.addCleanup(cleanup_dropin)
        self.assertTrue(actual_host.protect_legacy_unit(self.session, unit, parent))
        self.assertEqual(actual_host.process(parent.pid), parent)
        self.assertEqual(actual_host.unit_state(self.session, unit=unit)["KillMode"], "process")
        os.kill(parent.pid, signal.SIGTERM)
        self.wait_for(lambda: actual_host.unit_state(self.session, unit=unit)["ActiveState"] == "inactive",
                      "legacy unit did not retire after main process exit")
        self.assertTrue(actual_host.same_process([child.pid, child.ticks]))
        self.host.available(self.session, unit)
        # Cleanup must still terminate the disposable leftover child: after the
        # migration, stopping the service deliberately no longer does so.
        os.kill(child.pid, signal.SIGTERM)
        self.wait_for(lambda: not actual_host.same_process([child.pid, child.ticks]), "fixture child did not exit")


if __name__ == "__main__":
    unittest.main()
