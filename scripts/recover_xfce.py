#!/usr/bin/python3
"""Manually inspect XFCE; --start starts missing components without replacing any.

Requires a surviving local XFCE X11 session. This does not change login startup,
saved sessions, or applications. --component includes its prerequisites.
"""

from __future__ import annotations

import argparse
import configparser
from dataclasses import dataclass
from pathlib import Path
import re
import shlex
import stat
import sys
import time

# Even a diagnostic invocation must not write a cache beside the shared launcher.
sys.dont_write_bytecode = True
import launch_xfwm4 as wm


ORDER = ("conf", "wm", "settings", "desktop", "panel")
DEPENDENCIES = {
    "conf": (), "wm": ("conf",), "settings": ("conf", "wm"),
    "desktop": ("conf", "wm", "settings"), "panel": ("conf", "wm", "settings"),
}


@dataclass(frozen=True)
class Component:
    name: str
    process_name: str
    executable: str
    bus_name: str
    arguments: tuple[str, ...] = ("--sm-client-disable",)
    environment: tuple[tuple[str, str], ...] = ()

    def unit(self, session: wm.Session) -> str:
        return f"xfce-recovery-{self.name}-{session.identifier}.service"


class RecoveryHost(wm.Host):
    def __init__(self, *, filesystem=Path("/"), **kwargs):
        super().__init__(**kwargs)
        self.filesystem = filesystem

    def file(self, path: str | Path) -> Path:
        """Filesystem boundary for executable/configuration fixtures, not a CLI option."""
        path = Path(path)
        if not path.is_absolute():
            raise wm.Refused(f"Expected an absolute installation path: {path}")
        return self.filesystem / str(path).lstrip("/")

    def components(self, session: wm.Session) -> dict[str, Component]:
        env = dict(session.environment)
        home = Path(env["HOME"])
        data_home = Path(env.get("XDG_DATA_HOME", str(home / ".local/share")))
        local_service = data_home / "dbus-1/services/org.xfce.Xfconf.service"
        service = self.file(local_service)
        if not service.exists() and not service.is_symlink():
            service = self.file("/usr/share/dbus-1/services/org.xfce.Xfconf.service")
        info = service.stat()
        if info.st_uid not in {0, self.uid} or info.st_mode & 0o022:
            raise wm.Refused("Unsafe xfconf activation file ownership or permissions")
        config = configparser.ConfigParser(interpolation=None)
        config.read_string(service.read_text())
        entry = config["D-BUS Service"]
        command = shlex.split(entry["Exec"])
        allowed_conf = {str(home / ".local/lib/xfce4/xfconf/xfconfd"),
                        "/usr/lib/x86_64-linux-gnu/xfce4/xfconf/xfconfd"}
        if (entry.get("Name") != "org.xfce.Xfconf" or len(command) != 1
                or command[0] not in allowed_conf or "SystemdService" in entry):
            raise wm.Refused("Unsupported xfconf activation command; preserve it and inspect manually")
        plugins = (str(home / ".local/lib/xfce4/panel/plugins")
                   + ":/usr/lib/x86_64-linux-gnu/xfce4/panel/plugins")
        return {
            "conf": Component("conf", "xfconfd", command[0], "org.xfce.Xfconf", ()),
            "wm": Component("wm", "xfwm4", "/usr/bin/xfwm4", ""),
            "settings": Component("settings", "xfsettingsd", "/usr/bin/xfsettingsd", "org.xfce.SettingsDaemon"),
            "desktop": Component("desktop", "xfdesktop", "/usr/bin/xfdesktop", "org.xfce.xfdesktop"),
            "panel": Component("panel", "xfce4-panel", str(home / ".local/bin/xfce4-panel"),
                               "org.xfce.Panel", environment=(("NO_AT_BRIDGE", "1"),
                                                              ("XFCE_PANEL_PLUGIN_PATH", plugins))),
        }

    def validate_binary(self, component: Component) -> None:
        info = self.file(component.executable).stat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid not in {0, self.uid}
                or info.st_mode & 0o022 or not info.st_mode & 0o111):
            raise wm.Refused(f"Unsafe or non-executable {component.name} binary")
        if component.name == "panel":
            for path in dict(component.environment)["XFCE_PANEL_PLUGIN_PATH"].split(":"):
                if not self.file(path).is_dir():
                    raise wm.Refused(f"Panel plugin directory is missing: {path}")

    def bus_call(self, session: wm.Session, destination: str, interface: str,
                 method: str, *arguments: str) -> str:
        env = dict(session.environment)
        path = "/org/freedesktop/DBus" if destination == "org.freedesktop.DBus" else "/"
        return self.command([
            "/usr/bin/busctl", f"--address={env['DBUS_SESSION_BUS_ADDRESS']}",
            "--auto-start=no", "--timeout=5", "call", destination, path,
            interface, method, *arguments,
        ], env).strip()

    def bus_owner(self, session: wm.Session, name: str) -> str:
        output = self.bus_call(session, "org.freedesktop.DBus", "org.freedesktop.DBus",
                               "GetNameOwner", "s", name)
        match = re.fullmatch(r's "(:[0-9]+\.[0-9]+)"', output)
        if not match:
            raise wm.Refused(f"Malformed bus owner for {name}")
        return match[1]

    def component_process(self, session: wm.Session, component: Component) -> wm.Process | None:
        output = self.bus_call(session, "org.freedesktop.DBus", "org.freedesktop.DBus",
                               "NameHasOwner", "s", component.bus_name)
        if output not in {"b true", "b false"}:
            raise wm.Refused(f"Unknown bus ownership for {component.name}")
        processes = self.named_processes(component.process_name)
        if output == "b false":
            if processes:
                raise wm.Refused(f"{component.name}: process exists without a verified bus owner")
            return None
        owner = self.bus_owner(session, component.bus_name)
        result = self.bus_call(session, "org.freedesktop.DBus", "org.freedesktop.DBus",
                               "GetConnectionUnixProcessID", "s", owner)
        pid_match = re.fullmatch(r"u ([1-9][0-9]*)", result)
        if not pid_match:
            raise wm.Refused(f"Malformed owner PID for {component.name}")
        process = self.process(int(pid_match[1]))
        if len(processes) != 1 or processes[0] != process:
            raise wm.Refused(f"{component.name}: ambiguous process/bus ownership")
        if process.executable != component.executable:
            raise wm.Refused(f"{component.name}: unexpected executable; leaving it untouched")
        env = dict(process.environment)
        expected = dict(session.environment)
        if env.get("HOME") != expected["HOME"]:
            raise wm.Refused(f"{component.name}: owner has a different HOME")
        if component.name != "conf" and wm.display_number(env.get("DISPLAY", "")) != wm.display_number(expected["DISPLAY"]):
            raise wm.Refused(f"{component.name}: owner has a different display")
        if component.name != "conf" and process.ticks < session.leader[1]:
            raise wm.Refused(f"{component.name}: owner predates the graphical session")
        response = self.bus_call(session, owner, "org.freedesktop.DBus.Peer", "Ping")
        if response:
            raise wm.Refused(f"Unexpected Ping reply for {component.name}")
        if (self.bus_owner(session, component.bus_name) != owner
                or self.process(process.pid) != process):
            raise wm.Refused(f"{component.name}: owner changed during inspection")
        return process

    def revalidate(self, session: wm.Session, components: dict[str, Component]) -> None:
        if self.discover() != session:
            raise wm.Refused("Graphical session changed; no further component will be started")
        if self.components(session) != components:
            raise wm.Refused("Component configuration changed; no further component will be started")

    def submit_component(self, session: wm.Session, component: Component) -> None:
        env = dict(session.environment)
        env.update(component.environment)
        self.command([
            "/usr/bin/systemd-run", "--user", "--no-ask-password", "--collect",
            "--service-type=exec", "--expand-environment=no", f"--unit={component.unit(session)}",
            "--property=Restart=no", "--", "/usr/bin/env", "-i",
            *(f"{key}={value}" for key, value in sorted(env.items())),
            component.executable, *component.arguments,
        ], dict(session.environment))


def selected_components(component: str) -> tuple[str, ...]:
    if component == "all":
        return ORDER
    if component not in DEPENDENCIES:
        raise wm.Refused(f"Unknown component: {component}")
    wanted = {*DEPENDENCIES[component], component}
    return tuple(name for name in ORDER if name in wanted)


def inspect_component(host: RecoveryHost, session: wm.Session,
                      components: dict[str, Component], name: str) -> wm.Process | None:
    return host.manager(session) if name == "wm" else host.component_process(session, components[name])


def available_to_start(host: RecoveryHost, session: wm.Session,
                       components: dict[str, Component], name: str) -> wm.Process | None:
    host.validate_binary(components[name])
    process = inspect_component(host, session, components, name)
    if process is None:
        unit = session.unit if name == "wm" else components[name].unit(session)
        state = host.unit_state(session, unit=unit)
        if state["LoadState"] != "not-found":
            raise wm.Refused(f"{name}: {unit} already exists ({state['ActiveState']}); no duplicate submission")
    return process


def start_component(host: RecoveryHost, session: wm.Session, component: Component,
                    components: dict[str, Component], timeout: float) -> str:
    attempted_unit = component.unit(session)
    submission_error = ""
    try:
        host.submit_component(session, component)
    except wm.Refused as error:
        submission_error = str(error)
    deadline = time.monotonic() + timeout
    evidence = "no confirmed service owner"
    while True:
        terminal_failure = False
        try:
            host.revalidate(session, components)
            state = host.unit_state(session, unit=attempted_unit)
            terminal_failure = state["ActiveState"] == "failed"
            process = host.component_process(session, component)
            if (process is not None and state["LoadState"] == "loaded" and state["Transient"] == "yes"
                    and state["ActiveState"] == "active" and state["MainPID"] == str(process.pid)
                    and state["ControlGroup"].endswith("/" + attempted_unit)
                    and any(line.split(":", 2)[-1] == state["ControlGroup"]
                            for line in process.cgroup.splitlines())):
                return f"{component.name}: started and responsive (PID {process.pid}, {attempted_unit})."
            evidence = f"unit={state['LoadState']}/{state['ActiveState']}; owner={process.pid if process else 'absent'}"
        except (wm.Refused, OSError, ValueError, KeyError, IndexError, configparser.Error) as error:
            evidence = str(error)
        if terminal_failure or time.monotonic() >= deadline:
            raise wm.Refused(f"{component.name}: startup not confirmed for {attempted_unit}: {evidence}. "
                             f"No retry or rollback. {submission_error}".rstrip())
        time.sleep(0.1)


def recover(host: RecoveryHost, *, start=False, component="all", timeout=10.0) -> list[str]:
    selected = selected_components(component)
    session = host.discover()
    components = host.components(session)
    results = []
    if not start:
        blocked = False
        for name in selected:
            try:
                process = available_to_start(host, session, components, name)
                result = f"running (PID {process.pid}); unchanged" if process else "absent; no action taken"
                results.append(f"{name}: {result}.")
            except (wm.Refused, OSError, ValueError, KeyError, IndexError, configparser.Error) as error:
                blocked = True
                results.append(f"{name}: blocked: {error}")
        if blocked:
            raise wm.Refused("\n".join(results))
        return results
    try:
        # The same lock also protects standalone launch_xfwm4 calls. No nested acquisition.
        with wm.session_lock(host, session, timeout):
            host.revalidate(session, components)
            for name in selected:
                available_to_start(host, session, components, name)
            for name in selected:
                host.revalidate(session, components)
                for dependency in DEPENDENCIES[name]:
                    if inspect_component(host, session, components, dependency) is None:
                        raise wm.Refused(f"{name}: prerequisite {dependency} disappeared; stopping recovery")
                process = available_to_start(host, session, components, name)
                if process is not None:
                    results.append(f"{name}: running (PID {process.pid}); unchanged.")
                    continue
                host.revalidate(session, components)
                if name == "wm":
                    results.append(wm._launch_locked(host, session, timeout=timeout, register_session=False))
                else:
                    # Probe again after session/configuration checks, just before submission.
                    process = available_to_start(host, session, components, name)
                    if process is not None:
                        results.append(f"{name}: appeared (PID {process.pid}); unchanged.")
                    else:
                        results.append(start_component(host, session, components[name], components, timeout))
        return results
    except (wm.Refused, OSError, ValueError, KeyError, IndexError, configparser.Error) as error:
        progress = "\n".join(results) if results else "No component was recovered."
        raise wm.Refused(f"{progress}\nRecovery stopped: {error}") from error


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", action="store_true", help="start missing components; default is read-only")
    parser.add_argument("--component", choices=("all", *ORDER), default="all",
                        help="select a component and its prerequisites (default: all)")
    args = parser.parse_args(argv)
    try:
        for line in recover(RecoveryHost(), start=args.start, component=args.component):
            print(line)
        return 0
    except (wm.Refused, OSError, ValueError, KeyError, IndexError, configparser.Error) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
