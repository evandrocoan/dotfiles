"""Manual coordinator tests: real orchestration/locks, synthetic OS boundaries.

Fixtures model D-Bus ownership, proc files and unit state, not GUI rendering or
live service startup. Every unexpected subprocess is forbidden.
"""

import concurrent.futures
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import launch_xfwm4 as wm
import recover_xfce as recovery
from test_launch_xfwm4 import Desktop


class RecoveryDesktop(Desktop):
    def __init__(self, root):
        super().__init__(root)
        self.disk = root / "filesystem"
        self.home = "/home/fixture"
        self.env["HOME"] = self.home
        self.write_process(101, "lightdm", self.scope)
        self.write_process(102, "xfce4-session", self.scope)
        self.owners = {}
        self.units = {}
        self.unresponsive = set()
        self.bus_replies = {}
        self.after_ping = None
        self.component_submit = self.make_component_ready
        self.host = recovery.RecoveryHost(proc=self.proc, runtime=self.runtime,
                                          filesystem=self.disk, runner=self.run)
        self.host.base_env["HOME"] = self.home
        self.service_path = self.disk / "home/fixture/.local/share/dbus-1/services/org.xfce.Xfconf.service"
        self.service_path.parent.mkdir(parents=True)
        self.service_path.write_text("[D-BUS Service]\nName=org.xfce.Xfconf\n"
                                     "Exec=/home/fixture/.local/lib/xfce4/xfconf/xfconfd\n")
        self.service_path.chmod(0o644)
        for name in ("/home/fixture/.local/lib/xfce4/xfconf/xfconfd",
                     "/usr/lib/x86_64-linux-gnu/xfce4/xfconf/xfconfd",
                     "/usr/bin/xfwm4", "/usr/bin/xfsettingsd", "/usr/bin/xfdesktop", "/home/fixture/.local/bin/xfce4-panel"):
            target = self.disk / name.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("fixture executable; never run\n")
            target.chmod(0o755)
        for name in ("home/fixture/.local/lib/xfce4/panel/plugins", "usr/lib/x86_64-linux-gnu/xfce4/panel/plugins"):
            (self.disk / name).mkdir(parents=True)
        self.specs = self.host.components(self.host.discover())
        self.calls.clear()

    def make_component_ready(self, name):
        spec = self.specs[name]
        pid = {"conf": 201, "settings": 202, "desktop": 203, "panel": 204}[name]
        unit = f"xfce-recovery-{name}-c7.service"
        group = "/user.slice/user-1000.slice/user@1000.service/app.slice/" + unit
        self.write_process(pid, spec.process_name, group, executable=spec.executable)
        self.owners[spec.bus_name] = (f":1.{pid}", pid)
        self.units[unit] = dict(LoadState="loaded", ActiveState="active", SubState="running",
                                MainPID=str(pid), ControlGroup=group, Transient="yes")

    def make_all_ready(self):
        self.make_ready()
        for name in ("conf", "settings", "desktop", "panel"):
            self.make_component_ready(name)

    def remove_component(self, name):
        owner, pid = self.owners.pop(self.specs[name].bus_name)
        del owner
        directory = self.proc / str(pid)
        for path in directory.iterdir():
            path.unlink()
        directory.rmdir()
        self.units.pop(f"xfce-recovery-{name}-c7.service", None)

    def run(self, argv, **kwargs):
        tool = Path(argv[0]).name
        custom = ((tool == "busctl" and argv[-1] != "org.xfce.SessionManager")
                  or (tool == "systemctl" and argv[4] != self.unit)
                  or (tool == "systemd-run" and f"--unit={self.unit}" not in argv))
        if not custom:
            return super().run(argv, **kwargs)
        self.calls.append((list(argv), dict(kwargs["env"])))
        if self.on_command:
            self.on_command(argv)
        if tool == "busctl":
            call = argv.index("call")
            destination, _, _, method = argv[call + 1:call + 5]
            argument = argv[-1]
            if (method, argument) in self.bus_replies:
                output = self.bus_replies[method, argument]
            elif method == "NameHasOwner":
                output = "b true" if argument in self.owners else "b false"
            elif method == "GetNameOwner":
                if argument not in self.owners:
                    return subprocess.CompletedProcess(argv, 1, "", "name has no owner")
                output = f's "{self.owners[argument][0]}"'
            elif method == "GetConnectionUnixProcessID":
                matches = [pid for owner, pid in self.owners.values() if owner == argument]
                if len(matches) != 1:
                    raise AssertionError(f"Unarranged owner PID lookup: {argv}")
                output = f"u {matches[0]}"
            elif method == "Ping":
                if destination in self.unresponsive:
                    raise subprocess.TimeoutExpired(argv, 5)
                self.assert_unique_destination(destination)
                if self.after_ping:
                    self.after_ping()
                output = ""
            else:
                raise AssertionError(f"Unexpected bus method: {argv}")
        elif tool == "systemctl":
            state = self.units.get(argv[4], dict(LoadState="not-found", ActiveState="inactive",
                                               MainPID="0", ControlGroup="", Transient="no"))
            output = "\n".join(f"{key}={value}" for key, value in state.items())
        elif tool == "systemd-run":
            self.submissions.append(list(argv))
            unit = next(arg.split("=", 1)[1] for arg in argv if arg.startswith("--unit="))
            name = unit.removeprefix("xfce-recovery-").removesuffix("-c7.service")
            self.component_submit(name)
            output = f"Running as unit: {unit}"
        else:
            raise AssertionError(argv)
        return subprocess.CompletedProcess(argv, 0, output + ("\n" if output else ""), "")

    def assert_unique_destination(self, destination):
        if destination not in [owner for owner, _ in self.owners.values()]:
            raise AssertionError(f"Ping must target an arranged unique owner: {destination}")


class RecoveryCliTests(unittest.TestCase):
    def test_help_import_does_not_write_cache_beside_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("launch_xfwm4.py", "recover_xfce.py"):
                (root / name).write_text((Path(__file__).parent / name).read_text())
            result = subprocess.run([sys.executable, str(root / "recover_xfce.py"), "--help"],
                                    env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
                                    capture_output=True, text=True, timeout=5, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--component", result.stdout)
            self.assertEqual(sorted(path.name for path in root.iterdir()), ["launch_xfwm4.py", "recover_xfce.py"])


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.desktop = RecoveryDesktop(Path(temporary.name))
        self.addCleanup(patch.stopall)
        patch("subprocess.run", side_effect=AssertionError("Real subprocess forbidden in fixtures")).start()
        patch.dict(os.environ, {"DISPLAY": ":99", "SESSION_MANAGER": "stale", "LD_PRELOAD": "bad"}).start()

    def recover(self, **kwargs):
        return recovery.recover(self.desktop.host, **kwargs)

    def submission_units(self):
        return [next(arg.split("=", 1)[1] for arg in argv if arg.startswith("--unit="))
                for argv in self.desktop.submissions]

    def assert_refused_without_submission(self, message, **kwargs):
        with self.assertRaisesRegex(wm.Refused, message):
            self.recover(start=True, timeout=0, **kwargs)
        self.assertEqual(self.desktop.submissions, [])

    def test_default_diagnosis_has_no_effects(self):
        self.assertEqual(self.recover(), [f"{name}: absent; no action taken." for name in recovery.ORDER])
        self.assertEqual(list(self.desktop.runtime.iterdir()), [])
        self.assertEqual(self.desktop.submissions, [])
        for argv, _ in self.desktop.calls:
            if Path(argv[0]).name == "busctl":
                self.assertIn("--auto-start=no", argv)

    def test_diagnosis_reports_all_even_when_one_is_blocked(self):
        self.desktop.make_component_ready("conf")
        self.desktop.unresponsive.add(":1.201")
        with self.assertRaisesRegex(wm.Refused, "conf: blocked:.*timed out") as caught:
            self.recover()
        self.assertIn("panel: absent; no action taken.", str(caught.exception))
        self.assertEqual(list(self.desktop.runtime.iterdir()), [])
        self.assertEqual(self.desktop.submissions, [])

    def test_complete_recovery_order_and_repeat_are_idempotent(self):
        result = self.recover(start=True)
        self.assertEqual(self.submission_units(), ["xfce-recovery-conf-c7.service", "xfwm4-launch-c7.service",
                                                 "xfce-recovery-settings-c7.service", "xfce-recovery-desktop-c7.service",
                                                 "xfce-recovery-panel-c7.service"])
        self.assertEqual(len(result), 5)
        self.assertIn("started and responsive", result[-1])
        repeat = self.recover(start=True)
        self.assertEqual(len(self.desktop.submissions), 5)
        self.assertEqual(repeat, [f"{name}: running (PID {pid}); unchanged." for name, pid in
                                  (("conf", 201), ("wm", 103), ("settings", 202), ("desktop", 203), ("panel", 204))])

    def test_selective_panel_includes_prerequisites_but_not_desktop(self):
        self.recover(start=True, component="panel")
        self.assertEqual(self.submission_units(), ["xfce-recovery-conf-c7.service", "xfwm4-launch-c7.service",
                                                 "xfce-recovery-settings-c7.service", "xfce-recovery-panel-c7.service"])
        self.assertNotIn("org.xfce.xfdesktop", self.desktop.owners)

    def test_selective_conf_does_not_start_gui(self):
        self.recover(start=True, component="conf")
        self.assertEqual(self.submission_units(), ["xfce-recovery-conf-c7.service"])
        self.assertIsNone(self.desktop.owner)

    def test_existing_healthy_components_are_untouched(self):
        self.desktop.make_all_ready()
        self.assertEqual(len(self.recover(start=True)), 5)
        self.assertEqual(self.desktop.submissions, [])

    def test_custom_panel_and_conf_paths_and_environment_are_preserved(self):
        self.recover(start=True)
        conf = self.desktop.submissions[0]
        panel = self.desktop.submissions[-1]
        self.assertEqual(conf[-1], "/home/fixture/.local/lib/xfce4/xfconf/xfconfd")
        self.assertEqual(panel[-2:], ["/home/fixture/.local/bin/xfce4-panel", "--sm-client-disable"])
        self.assertIn("NO_AT_BRIDGE=1", panel)
        self.assertIn("XFCE_PANEL_PLUGIN_PATH=/home/fixture/.local/lib/xfce4/panel/plugins:/usr/lib/x86_64-linux-gnu/xfce4/panel/plugins", panel)
        for argv in self.desktop.submissions:
            self.assertIn("--property=Restart=no", argv)
            self.assertIn("-i", argv)
            self.assertIn("DISPLAY=:0.0", argv)
            self.assertIn(f"XAUTHORITY={self.desktop.authority}", argv)
            self.assertIn("XDG_CONFIG_DIRS=/etc/xdg/xdg-xfce:/etc/xdg", argv)
            self.assertFalse(any(arg.startswith("LD_PRELOAD=") for arg in argv))
            self.assertNotIn("--replace", argv)

    def test_recovery_disables_sm_even_for_trusted_caller(self):
        (self.desktop.proc / "self/cgroup").write_text(f"0::{self.desktop.scope}\n")
        with patch.dict(os.environ, {"SESSION_MANAGER": "local/host:@/tmp/.ICE-unix/102"}):
            self.recover(start=True)
        for argv in self.desktop.submissions:
            self.assertFalse(any(arg.startswith("SESSION_MANAGER=") for arg in argv), argv)
        for argv in self.desktop.submissions[1:]:
            self.assertEqual(argv[-1], "--sm-client-disable")

    def test_configured_vendor_conf_is_respected(self):
        self.desktop.service_path.write_text("[D-BUS Service]\nName=org.xfce.Xfconf\n"
                                             "Exec=/usr/lib/x86_64-linux-gnu/xfce4/xfconf/xfconfd\n")
        self.desktop.specs = self.desktop.host.components(self.desktop.host.discover())
        self.recover(start=True, component="conf")
        self.assertEqual(self.desktop.submissions[0][-1], "/usr/lib/x86_64-linux-gnu/xfce4/xfconf/xfconfd")

    def test_unsupported_activation_command_is_not_replaced(self):
        self.desktop.service_path.write_text("[D-BUS Service]\nName=org.xfce.Xfconf\nExec=/tmp/unknown\n")
        self.assert_refused_without_submission("Unsupported xfconf activation")

    def test_missing_binary_blocks_before_any_mutation(self):
        (self.desktop.disk / "home/fixture/.local/bin/xfce4-panel").unlink()
        self.assert_refused_without_submission("xfce4-panel")

    def test_missing_wm_binary_blocks_conf_start(self):
        (self.desktop.disk / "usr/bin/xfwm4").unlink()
        self.assert_refused_without_submission("xfwm4")

    def test_missing_plugin_directory_blocks_before_any_mutation(self):
        (self.desktop.disk / "home/fixture/.local/lib/xfce4/panel/plugins").rmdir()
        self.assert_refused_without_submission("Panel plugin directory is missing")

    def test_unsafe_binary_permissions_are_rejected(self):
        (self.desktop.disk / "usr/bin/xfsettingsd").chmod(0o777)
        self.assert_refused_without_submission("Unsafe or non-executable settings")

    def test_process_without_bus_owner_blocks_duplicate(self):
        spec = self.desktop.specs["panel"]
        self.desktop.write_process(204, spec.process_name, self.desktop.scope, executable=spec.executable)
        self.assert_refused_without_submission("process exists without a verified bus owner")

    def test_unresponsive_owner_is_not_replaced(self):
        self.desktop.make_component_ready("panel")
        self.desktop.unresponsive.add(":1.204")
        self.assert_refused_without_submission("timed out")

    def test_foreign_owner_credentials_are_rejected(self):
        self.desktop.make_component_ready("panel")
        foreign = self.desktop.uid + 1
        (self.desktop.proc / "204/status").write_text(f"Uid:\t{foreign}\t{foreign}\t{foreign}\t{foreign}\n")
        self.assert_refused_without_submission("incompatible credentials")

    def test_wrong_owner_executable_is_rejected(self):
        self.desktop.make_component_ready("panel")
        self.desktop.write_process(204, "xfce4-panel", self.desktop.scope, executable="/usr/bin/xfce4-panel")
        self.assert_refused_without_submission("unexpected executable")

    def test_wrong_owner_display_is_rejected(self):
        self.desktop.make_component_ready("panel")
        env = dict(self.desktop.env, DISPLAY=":9")
        self.desktop.write_process(204, "xfce4-panel", self.desktop.scope, env=env,
                                   executable=self.desktop.specs["panel"].executable)
        self.assert_refused_without_submission("different display")

    def test_wrong_owner_home_is_rejected(self):
        self.desktop.make_component_ready("conf")
        env = dict(self.desktop.env, HOME="/home/elsewhere")
        self.desktop.write_process(201, "xfconfd", self.desktop.scope, env=env,
                                   executable=self.desktop.specs["conf"].executable)
        self.assert_refused_without_submission("different HOME")

    def test_owner_from_an_older_session_is_rejected(self):
        self.desktop.make_component_ready("panel")
        self.desktop.write_process(204, "xfce4-panel", self.desktop.scope, ticks=499,
                                   executable=self.desktop.specs["panel"].executable)
        self.assert_refused_without_submission("owner predates the graphical session")

    def test_per_user_conf_without_display_or_graphical_scope_is_accepted(self):
        self.desktop.make_component_ready("conf")
        self.desktop.write_process(201, "xfconfd", "/user.slice/session.slice/dbus.service",
                                   env={"HOME": self.desktop.home}, executable=self.desktop.specs["conf"].executable)
        self.assertEqual(self.recover(start=True, component="conf"), ["conf: running (PID 201); unchanged."])
        self.assertEqual(self.desktop.submissions, [])

    def test_unknown_bus_reply_is_not_treated_as_absence(self):
        self.desktop.bus_replies["NameHasOwner", "org.xfce.Panel"] = "bad response"
        self.assert_refused_without_submission("Unknown bus ownership")

    def test_owner_changes_during_ping_blocks_submission(self):
        self.desktop.make_component_ready("panel")
        def change():
            self.desktop.owners["org.xfce.Panel"] = (":1.999", 204)
        self.desktop.after_ping = change
        self.assert_refused_without_submission("owner changed during inspection")

    def test_existing_unit_without_owner_blocks_submission(self):
        self.desktop.units["xfce-recovery-panel-c7.service"] = dict(LoadState="loaded", ActiveState="activating",
                                                                 MainPID="0", ControlGroup="", Transient="yes")
        self.assert_refused_without_submission("already exists")

    def test_changed_session_before_first_submit_is_rejected(self):
        calls = 0
        def change(argv):
            nonlocal calls
            if Path(argv[0]).name == "loginctl" and argv[1] == "list-sessions":
                calls += 1
                if calls == 3:
                    self.desktop.write_process(102, "xfce4-session", self.desktop.scope, ticks=600)
        self.desktop.on_command = change
        self.assert_refused_without_submission("Graphical session changed")

    def test_changed_activation_config_before_submit_is_rejected(self):
        def change(argv):
            if Path(argv[0]).name == "systemctl":
                self.desktop.service_path.write_text("[D-BUS Service]\nName=org.xfce.Xfconf\n"
                                                     "Exec=/usr/lib/x86_64-linux-gnu/xfce4/xfconf/xfconfd\n")
        self.desktop.on_command = change
        self.assert_refused_without_submission("Component configuration changed")

    def test_disappearing_prerequisite_stops_later_components(self):
        def submit(name):
            self.desktop.make_component_ready(name)
            if name == "settings":
                self.desktop.remove_component("conf")
        self.desktop.component_submit = submit
        with self.assertRaisesRegex(wm.Refused, "prerequisite conf disappeared") as caught:
            self.recover(start=True)
        self.assertIn("settings: started and responsive", str(caught.exception))
        self.assertEqual(self.submission_units(), ["xfce-recovery-conf-c7.service", "xfwm4-launch-c7.service",
                                                 "xfce-recovery-settings-c7.service"])

    def test_failed_component_leaves_prior_progress_without_rollback(self):
        def submit(name):
            if name == "desktop":
                self.desktop.units["xfce-recovery-desktop-c7.service"] = dict(
                    LoadState="loaded", ActiveState="failed", MainPID="0", ControlGroup="", Transient="yes")
            else:
                self.desktop.make_component_ready(name)
        self.desktop.component_submit = submit
        with self.assertRaisesRegex(wm.Refused, "desktop: startup not confirmed") as caught:
            self.recover(start=True, timeout=0)
        self.assertIn("settings: started and responsive", str(caught.exception))
        self.assertEqual(self.submission_units()[-1], "xfce-recovery-desktop-c7.service")
        self.assertEqual(len(self.desktop.submissions), 4)
        self.assertIn("org.xfce.SettingsDaemon", self.desktop.owners)
        self.assertFalse(any("stop" in argv or "kill" in argv or "reset-failed" in argv for argv, _ in self.desktop.calls))

    def test_lost_submission_ack_is_reconciled_without_second_submit(self):
        def submit(name):
            self.desktop.make_component_ready(name)
            raise subprocess.TimeoutExpired("systemd-run", 5)
        self.desktop.component_submit = submit
        result = self.recover(start=True, component="conf", timeout=0)
        self.assertIn("started and responsive", result[0])
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_malformed_config_after_partial_start_preserves_failure_context(self):
        def submit(name):
            self.desktop.make_component_ready(name)
            if name == "settings":
                self.desktop.service_path.write_text("invalid configuration\n")
        self.desktop.component_submit = submit
        with self.assertRaisesRegex(wm.Refused, "settings: startup not confirmed") as caught:
            self.recover(start=True, timeout=0)
        self.assertIn("conf: started and responsive", str(caught.exception))
        self.assertIn("xfce-recovery-settings-c7.service", str(caught.exception))
        self.assertEqual(len(self.desktop.submissions), 3)
        self.assertIn("org.xfce.SettingsDaemon", self.desktop.owners)

    def test_unresolved_submission_stops_without_retry(self):
        self.desktop.component_submit = lambda name: None
        with self.assertRaisesRegex(wm.Refused, "xfce-recovery-conf-c7.service.*No retry or rollback"):
            self.recover(start=True, timeout=0)
        self.assertEqual(self.submission_units(), ["xfce-recovery-conf-c7.service"])

    def test_slow_readiness_is_awaited_before_next_component(self):
        self.desktop.component_submit = lambda name: None
        waits = []
        def advance(delay):
            waits.append(delay)
            self.desktop.make_component_ready("conf")
        with patch.object(recovery.time, "sleep", advance):
            result = self.recover(start=True, component="conf")
        self.assertEqual(waits, [0.1])
        self.assertIn("started and responsive", result[0])
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_wrong_mainpid_cannot_be_reported_ready(self):
        def submit(name):
            self.desktop.make_component_ready(name)
            self.desktop.units[f"xfce-recovery-{name}-c7.service"]["MainPID"] = "999"
        self.desktop.component_submit = submit
        with self.assertRaisesRegex(wm.Refused, "startup not confirmed"):
            self.recover(start=True, component="conf", timeout=0)
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_wrong_unit_cgroup_cannot_be_reported_ready(self):
        def submit(name):
            self.desktop.make_component_ready(name)
            self.desktop.units[f"xfce-recovery-{name}-c7.service"]["ControlGroup"] = "/wrong/group"
        self.desktop.component_submit = submit
        with self.assertRaisesRegex(wm.Refused, "startup not confirmed"):
            self.recover(start=True, component="conf", timeout=0)
        self.assertEqual(len(self.desktop.submissions), 1)

    def test_session_change_after_submit_stops_the_chain(self):
        def submit(name):
            self.desktop.make_component_ready(name)
            self.desktop.write_process(102, "xfce4-session", self.desktop.scope, ticks=600)
        self.desktop.component_submit = submit
        with self.assertRaisesRegex(wm.Refused, "Graphical session changed"):
            self.recover(start=True, timeout=0)
        self.assertEqual(self.submission_units(), ["xfce-recovery-conf-c7.service"])

    def test_owner_appearing_before_submit_is_preserved(self):
        probes = 0
        def appear(argv):
            nonlocal probes
            if "NameHasOwner" in argv and argv[-1] == "org.xfce.Xfconf":
                probes += 1
                if probes == 3:
                    self.desktop.make_component_ready("conf")
        self.desktop.on_command = appear
        self.assertIn("appeared", self.recover(start=True, component="conf")[0])
        self.assertEqual(self.desktop.submissions, [])

    def exercise_contention(self, second):
        entered, release, contended = threading.Event(), threading.Event(), threading.Event()
        real_flock = wm.fcntl.flock
        def submit(name):
            if name == "conf":
                entered.set()
                if not release.wait(5):
                    raise AssertionError("first submission was not released")
            self.desktop.make_component_ready(name)
        def observed_flock(*args):
            try:
                return real_flock(*args)
            except BlockingIOError:
                contended.set()
                raise
        self.desktop.component_submit = submit
        with patch.object(wm.fcntl, "flock", observed_flock), concurrent.futures.ThreadPoolExecutor(2) as pool:
            first = pool.submit(self.recover, start=True)
            try:
                self.assertTrue(entered.wait(5))
                other = pool.submit(second)
                self.assertTrue(contended.wait(5), "second caller bypassed the real shared lock")
                self.assertEqual(self.submission_units(), ["xfce-recovery-conf-c7.service"])
            finally:
                release.set()
            self.assertEqual(len(first.result(5)), 5)
            result = other.result(5)
        self.assertEqual(len(self.desktop.submissions), 5)
        return result

    def test_concurrent_full_recoveries_share_one_lock(self):
        result = self.exercise_contention(lambda: self.recover(start=True))
        self.assertEqual(len(result), 5)
        self.assertTrue(all("unchanged" in item for item in result))

    def test_standalone_wm_waits_during_conf_recovery(self):
        result = self.exercise_contention(lambda: wm.launch(self.desktop.host, start=True))
        self.assertEqual(result, "Session c7: window manager present (PID 103); unchanged.")

    def test_default_cli_does_not_create_a_lock(self):
        output = io.StringIO()
        with patch.object(recovery, "RecoveryHost", return_value=self.desktop.host), contextlib.redirect_stdout(output):
            self.assertEqual(recovery.main([]), 0)
        self.assertIn("panel: absent; no action taken.", output.getvalue())
        self.assertEqual(list(self.desktop.runtime.iterdir()), [])
        self.assertEqual(self.desktop.submissions, [])


if __name__ == "__main__":
    unittest.main()
