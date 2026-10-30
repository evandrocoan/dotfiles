"""Opt-in installed-Xfconf integration through a disposable D-Bus activation bus.

Run with XFCE_PANEL_INTEGRATION_TESTS=1. These checks never start a real panel,
change the live XML, or signal a process outside their private bus and HOME.
"""

import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

import diagnose_xfce_panel_boot as capture
import xfce_panel_startup as fix
from test_xfce_panel_startup import Fixture, EXPECTED

INSTALLED_HOME = Path.home()


def private_probe(query):
    home = Path.home().resolve()
    address = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "")
    if (not (home / "isolated-xfce-test").is_file()
            or Path(os.environ["XDG_CONFIG_HOME"]).resolve() != home / ".config"
            or not address or "/run/user/" in address):
        raise RuntimeError("Refusing a non-disposable home or session bus")
    results = {}
    for prop in ("/configver", "/panels", "/plugins/plugin-1", "/panels/panel-1/position"):
        response = subprocess.run([query, "-c", "xfce4-panel", "-p", prop],
                                  capture_output=True, text=True, timeout=8)
        results[prop] = {"returncode": response.returncode,
                         "stdout": response.stdout, "stderr": response.stderr}
    reply = subprocess.run([
        "/usr/bin/gdbus", "call", "--session", "--dest", "org.freedesktop.DBus",
        "--object-path", "/org/freedesktop/DBus",
        "--method", "org.freedesktop.DBus.GetConnectionUnixProcessID", "org.xfce.Xfconf",
    ], check=True, capture_output=True, text=True, timeout=5).stdout
    match = re.fullmatch(r"\(uint32 ([0-9]+),\)\s*", reply)
    if not match:
        raise RuntimeError("Malformed private-bus daemon PID")
    pid = int(match[1])
    descriptor = os.pidfd_open(pid)
    try:
        proc = Path("/proc") / str(pid)
        environment = dict(item.split("=", 1) for item in
                           (proc / "environ").read_text().rstrip("\0").split("\0"))
        if (environment.get("HOME") != str(home)
                or environment.get("DBUS_SESSION_BUS_ADDRESS") != address
                or (proc / "exe").resolve() != (home / fix.DAEMON).resolve()):
            raise RuntimeError("Refusing to signal an unowned daemon")
        results["daemon_environment"] = {key: environment.get(key) for key in capture.SEARCH_ENV}
        subprocess.run([query, "-c", "xfce4-panel", "-p", "/capture-test",
                        "-n", "-t", "string", "-s", "probe-write"],
                       check=True, capture_output=True, text=True, timeout=5)
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        with selectors.DefaultSelector() as selector:
            selector.register(descriptor, selectors.EVENT_READ)
            if not selector.select(5):
                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
                raise RuntimeError("Disposable daemon did not terminate gracefully")
    finally:
        os.close(descriptor)
    xml = ET.parse(home / fix.PANEL).getroot()
    results["persisted_value"] = xml.find("./property[@name='capture-test']").get("value")
    print(json.dumps(results))


@unittest.skipUnless(os.environ.get("XFCE_PANEL_INTEGRATION_TESTS") == "1",
                     "set XFCE_PANEL_INTEGRATION_TESTS=1 on the Mint/local-Xfconf host")
class InstalledXfconfTests(Fixture):
    def run_activation(self, repaired):
        daemon = INSTALLED_HOME / fix.DAEMON
        query = INSTALLED_HOME / ".local/bin/xfconf-query"
        for required in (daemon, query, fix.MINT_XML, Path("/usr/bin/dbus-run-session"),
                         Path("/usr/bin/gdbus"), Path("/usr/bin/strace")):
            self.assertTrue(required.is_file(), f"Required integration prerequisite: {required}")
        self.daemon.unlink()
        self.daemon.symlink_to(daemon)
        (self.home / "isolated-xfce-test").touch()
        self.panel.write_bytes(EXPECTED)
        if repaired:
            self.apply()
        before_hook = self.service.read_bytes()
        run, root = self.armed_capture()
        env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / ".config"),
                   XDG_DATA_HOME=str(self.home / ".local/share"),
                   XDG_CACHE_HOME=str(self.home / ".cache"),
                   PYTHONDONTWRITEBYTECODE="1", LC_ALL="C")
        for key in ("XDG_CONFIG_DIRS", "DBUS_SESSION_BUS_ADDRESS"):
            env.pop(key, None)
        live = INSTALLED_HOME / fix.PANEL
        live_before = live.read_bytes()
        result = subprocess.run([
            "/usr/bin/dbus-run-session", "--", sys.executable, str(Path(__file__).resolve()),
            "--private-probe", str(query),
        ], env=env, capture_output=True, text=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(live.read_bytes(), live_before, "Live panel XML changed")
        observed = json.loads(result.stdout)
        self.assertEqual(observed["persisted_value"], "probe-write")
        self.assertEqual(observed["/panels/panel-1/position"]["returncode"], 0)
        self.assertEqual(observed["/panels/panel-1/position"]["stdout"].strip(), "p=6;x=20;y=30")
        folder = root / "runs" / capture.current_boot()
        records = list(folder.glob("*-dbus.json"))
        self.assertEqual(len(records), 1)
        self.assertEqual(fix.read_json(records[0])["panel_sha256"], fix.sha(EXPECTED))
        traces = list(folder.glob("*.strace"))
        self.assertEqual(len(traces), 1)
        trace = traces[0].read_text()
        self.assertIn("rename(", trace, "Must observe the installed daemon's actual persistence")
        self.assertIn("xfce4-panel.xml.new", trace)
        capture.cleanup(self.home, run)
        self.assertEqual(self.service.read_bytes(), before_hook)
        self.assertIsNone(fix.capture_active(self.home))
        return observed, trace

    def test_repaired_dbus_activation_loads_mint_and_traces_real_writes(self):
        observed, trace = self.run_activation(repaired=True)
        self.assertEqual(observed["daemon_environment"]["XDG_CONFIG_DIRS"], fix.MINT_DIRS)
        self.assertEqual(observed["/configver"]["returncode"], 0)
        self.assertEqual(observed["/configver"]["stdout"].strip(), "2")
        self.assertEqual(observed["/panels"]["returncode"], 0)
        self.assertEqual(observed["/panels"]["stdout"], "Value is an array with 1 items:\n\n1\n")
        self.assertEqual(observed["/plugins/plugin-1"]["returncode"], 0)
        self.assertEqual(observed["/plugins/plugin-1"]["stdout"].strip(), "whiskermenu")
        self.assertIn(str(fix.MINT_XML), trace)

    def test_unrepaired_activation_loses_mint_inheritance_negative_control(self):
        observed, trace = self.run_activation(repaired=False)
        self.assertIsNone(observed["daemon_environment"]["XDG_CONFIG_DIRS"])
        for prop in ("/configver", "/panels", "/plugins/plugin-1"):
            self.assertEqual(observed[prop]["returncode"], 1)
            self.assertIn("does not exist", observed[prop]["stderr"])
        self.assertNotIn(str(fix.MINT_XML), trace)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--private-probe":
        private_probe(sys.argv[2])
    else:
        unittest.main()
