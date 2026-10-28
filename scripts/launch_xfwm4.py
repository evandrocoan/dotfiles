#!/usr/bin/python3
"""Check XFWM safely; --start launches it only for an authenticated, empty X session.

The lock coordinates this launcher and recover_xfce.py; other starters can bypass
it. Installing the file does not change XFCE startup or saved restart commands.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field


class Refused(RuntimeError):
    """Missing evidence: leave all desktop processes untouched."""


def properties(text: str) -> dict[str, str]:
    result = {}
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if not separator or key in result:
            raise Refused("Malformed or duplicate service properties")
        result[key] = value
    return result


def display_number(value: str) -> str:
    match = re.fullmatch(r"(?:unix)?:([0-9]+)(?:\.0)?", value)
    if not match:
        raise Refused("Only a local X display with screen zero is supported")
    return str(int(match[1]))


@dataclass(frozen=True)
class Process:
    pid: int
    ticks: int
    executable: str
    cgroup: str
    environment: tuple[tuple[str, str], ...]

    def matches_executable(self, expected: str) -> bool:
        # Package upgrades and custom rebuilds can replace a running binary.
        # proc retains its original path with this kernel-supplied suffix.
        return self.executable in {expected, expected + " (deleted)"}


@dataclass(frozen=True)
class Session:
    identifier: str
    leader: tuple[int, int, int, str]
    anchor: Process
    environment_source: Process | None = field(compare=False)
    environment_identity: tuple[int, int]
    environment: tuple[tuple[str, str], ...]
    authority_identity: tuple[int, int, int, int]

    @property
    def unit(self) -> str:
        return f"xfwm4-launch-{self.identifier}.service"


class Host:
    """OS boundaries are injectable for tests; CLI never accepts alternate roots."""

    def __init__(self, *, proc=Path("/proc"), runtime=None, uid=None, runner=None, spawner=None):
        self.uid = os.getuid() if uid is None else uid
        self.proc = proc
        account = pwd.getpwuid(self.uid)
        self.runtime = Path(f"/run/user/{self.uid}") if runtime is None else runtime
        self.base_env = {
            "HOME": account.pw_dir, "USER": account.pw_name,
            "LOGNAME": account.pw_name, "PATH": "/usr/bin:/bin",
            "XDG_RUNTIME_DIR": str(self.runtime),
            "DBUS_SESSION_BUS_ADDRESS": f"unix:path={self.runtime}/bus",
        }
        self.runner = subprocess.run if runner is None else runner
        self.spawner = subprocess.Popen if spawner is None else spawner
        self.children = []

    def command(self, argv, env=None, *, allowed=(0,), diagnostic_locale=True) -> str:
        command_env = dict(self.base_env if env is None else env)
        if diagnostic_locale:
            command_env["LC_ALL"] = "C"  # Only diagnostic output needs a fixed locale.
        try:
            result = self.runner(
                argv, env=command_env,
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                timeout=5, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Refused(f"Command unavailable or timed out: {argv[0]}: {error}") from error
        if result.returncode not in allowed:
            raise Refused(f"{argv[0]} failed ({result.returncode}): {result.stderr.strip()}")
        return result.stdout

    def process(self, pid: int) -> Process:
        directory = self.proc / str(pid)
        if directory.stat().st_uid != self.uid:
            raise Refused(f"PID {pid} belongs to another user")
        before = (directory / "stat").read_text().rsplit(")", 1)[1].split()
        if before[0] in {"Z", "X"}:
            raise Refused(f"PID {pid} is not a live process")
        uids = re.search(r"^Uid:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$",
                         (directory / "status").read_text(), re.MULTILINE)
        if not uids or any(int(value) != self.uid for value in uids.groups()):
            raise Refused(f"PID {pid} has incompatible credentials")
        environment = {}
        for entry in (directory / "environ").read_bytes().split(b"\0"):
            if entry:
                key, separator, value = os.fsdecode(entry).partition("=")
                if not separator or key in environment:
                    raise Refused(f"PID {pid} has ambiguous environment")
                environment[key] = value
        cgroup = (directory / "cgroup").read_text()
        executable = os.readlink(directory / "exe")
        after = (directory / "stat").read_text().rsplit(")", 1)[1].split()
        if before[19] != after[19] or after[0] in {"Z", "X"}:
            raise Refused(f"PID {pid} changed during inspection")
        return Process(pid, int(before[19]), executable, cgroup,
                       tuple(sorted(environment.items())))

    def named_processes(self, name: str) -> list[Process]:
        found = []
        for directory in self.proc.iterdir():
            if not directory.name.isdecimal():
                continue
            try:
                if directory.stat().st_uid != self.uid:
                    continue
                if (directory / "comm").read_text().strip() == name:
                    found.append(self.process(int(directory.name)))
            except FileNotFoundError:
                continue  # A process exited, not an unreadable process.
        return found

    def in_scope(self, process: Process, scope: str) -> bool:
        return any(scope in line.split(":", 2)[-1].split("/")
                   for line in process.cgroup.splitlines())

    def session_environment_source(self, anchor: Process, scope: str) -> Process | None:
        # /proc exposes the session manager's initial environment, before its
        # keyring/SSH setup. Original XFCE clients inherit those later additions.
        # Never use recovered clients in transient units or the invoking tool.
        original = dict(anchor.environment)
        home = self.base_env["HOME"]
        clients = (("xfsettingsd", {"/usr/bin/xfsettingsd"}),
                   ("xfdesktop", {"/usr/bin/xfdesktop"}),
                   ("xfce4-panel", {"/usr/bin/xfce4-panel", f"{home}/.local/bin/xfce4-panel"}),
                   ("xfwm4", {"/usr/bin/xfwm4"}),
                   ("xfce4-terminal", {"/usr/bin/xfce4-terminal"}))
        for name, executables in clients:
            candidates = []
            for process in self.named_processes(name):
                env = dict(process.environment)
                if (self.in_scope(process, scope) and any(process.matches_executable(path) for path in executables)
                        and process.ticks >= anchor.ticks
                        and env.get("HOME", home) == home
                        and env.get("XAUTHORITY") == original.get("XAUTHORITY")
                        and re.fullmatch(r"(?:unix)?:[0-9]+(?:\.0)?", env.get("DISPLAY", ""))
                        and display_number(env["DISPLAY"]) == display_number(original["DISPLAY"])):
                    candidates.append(process)
            if len(candidates) > 1:
                raise Refused(f"Ambiguous {name} session environment")
            if candidates:
                return candidates[0]
        return None

    def read_record(self, path: Path):
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return None
        with os.fdopen(descriptor) as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.uid
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
                    or info.st_size > 1024 * 1024):
                raise Refused(f"Unsafe recovery record: {path}")
            return json.load(stream)

    def write_record(self, path: Path, record) -> None:
        # The runtime directory is private; atomic replacement never follows a
        # symlink and leaves an interrupted launch conservatively pending.
        descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=self.runtime)
        try:
            with os.fdopen(descriptor, "w") as stream:
                json.dump(record, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def environment_path(self, identifier: str, anchor: Process) -> Path:
        return self.runtime / f"xfce-environment-{identifier}-{anchor.pid}-{anchor.ticks}.json"

    def save_environment(self, session: Session) -> None:
        self.write_record(self.environment_path(session.identifier, session.anchor),
                          {"source": list(session.environment_identity),
                           "environment": dict(session.environment)})

    def discover(self) -> Session:
        if self.uid == 0 or os.geteuid() != self.uid:
            raise Refused("Run as the desktop user, without sudo")
        runtime_stat = self.runtime.lstat()
        if (not stat.S_ISDIR(runtime_stat.st_mode) or runtime_stat.st_uid != self.uid
                or stat.S_IMODE(runtime_stat.st_mode) != 0o700):
            raise Refused("Unsafe user runtime directory")
        candidates = []
        rows = self.command(["/usr/bin/loginctl", "list-sessions", "--no-legend", "--no-pager"])
        for row in rows.splitlines():
            fields = row.split()
            if len(fields) < 3 or not fields[1].isdecimal():
                raise Refused("Malformed logind session list")
            if int(fields[1]) != self.uid:
                continue
            identifier = fields[0]
            if not re.fullmatch(r"[A-Za-z0-9]+", identifier):
                raise Refused("Unsupported logind session identifier")
            info = properties(self.command([
                "/usr/bin/loginctl", "show-session", identifier, "--no-pager",
                *(f"--property={key}" for key in
                  ("Id", "User", "Display", "Remote", "Desktop", "Scope", "Leader",
                   "Type", "Class", "Active", "State")),
            ]))
            if info.get("Type") in {"x11", "wayland"}:
                candidates.append(info)
        if len(candidates) != 1:
            raise Refused("Expected exactly one graphical session for this user")
        info = candidates[0]
        identifier = info.get("Id", "")
        if not re.fullmatch(r"[A-Za-z0-9]+", identifier):
            raise Refused("Invalid selected session ID")
        scope = f"session-{identifier}.scope"
        expected = {"User": str(self.uid), "Remote": "no", "Desktop": "xfce",
                    "Type": "x11", "Class": "user", "Active": "yes",
                    "State": "active", "Scope": scope}
        if any(info.get(key) != value for key, value in expected.items()):
            raise Refused("Session must be an active local XFCE X11 user session")
        # LightDM's logind leader is a root-owned wrapper; the XFCE anchor below
        # must still belong to the desktop user. Do not read the wrapper's env.
        leader_pid = int(info["Leader"])
        leader_path = self.proc / str(leader_pid)
        leader_stat = (leader_path / "stat").read_text().rsplit(")", 1)[1].split()
        leader_group = (leader_path / "cgroup").read_text()
        leader_uid = leader_path.stat().st_uid
        if leader_uid not in {0, self.uid} or leader_stat[0] in {"Z", "X"}:
            raise Refused("Incompatible logind leader")
        leader = (leader_pid, int(leader_stat[19]), leader_uid, leader_group)
        anchors = [process for process in self.named_processes("xfce4-session")
                   if self.in_scope(process, scope)]
        if len(anchors) != 1 or not any(scope in line.split(":", 2)[-1].split("/")
                                         for line in leader_group.splitlines()):
            raise Refused("Cannot identify one live XFCE session process in the logind scope")
        anchor = anchors[0]
        if not anchor.matches_executable("/usr/bin/xfce4-session"):
            raise Refused("Unexpected XFCE session executable")
        source = dict(anchor.environment)
        if display_number(source.get("DISPLAY", "")) != display_number(info.get("Display", "")):
            raise Refused("XFCE and logind displays disagree")
        authority = Path(source.get("XAUTHORITY", ""))
        if not authority.is_absolute():
            raise Refused("XFCE has no absolute XAUTHORITY path")
        auth_stat = authority.stat()
        if not stat.S_ISREG(auth_stat.st_mode) or auth_stat.st_uid != self.uid:
            raise Refused("X authority does not belong to the desktop user")
        with authority.open("rb") as stream:
            if not stream.read(1):
                raise Refused("Empty X authority file")
        # Once captured, one complete snapshot owns the environment for this
        # login. Switching to a surviving client's smaller/per-app environment
        # would silently lose keyring/custom variables on a later recovery.
        cached = self.read_record(self.environment_path(identifier, anchor))
        environment_source = self.session_environment_source(anchor, scope) if cached is None else None
        if environment_source is None and cached is None:
            raise Refused("No surviving session client or saved session environment; "
                          "cannot reconstruct the post-login environment")
        if cached is not None:
            if (not isinstance(cached, dict) or not isinstance(cached.get("environment"), dict)
                    or not cached["environment"] or not isinstance(cached.get("source"), list)
                    or len(cached["source"]) != 2
                    or any(type(value) is not int or value <= 0 for value in cached["source"])
                    or any(not isinstance(k, str) or not isinstance(v, str)
                           or not k or "=" in k or "\0" in k + v
                           for k, v in cached["environment"].items())):
                raise Refused("Malformed saved session environment")
            environment_identity = tuple(cached["source"])
        else:
            environment_identity = (environment_source.pid, environment_source.ticks)
        env = dict(self.base_env)
        env.update(environment_source.environment if environment_source else cached["environment"])
        if (env["HOME"] != self.base_env["HOME"]
                or env["XDG_RUNTIME_DIR"] != str(self.runtime)
                or env["DBUS_SESSION_BUS_ADDRESS"] != self.base_env["DBUS_SESSION_BUS_ADDRESS"]
                or env.get("XAUTHORITY") != str(authority)
                or display_number(env.get("DISPLAY", "")) != display_number(source["DISPLAY"])):
            raise Refused("Session environment disagrees with the authenticated user runtime")
        # Registration is controlled separately by start(); recovery disables it.
        env.pop("SESSION_MANAGER", None)
        bus_pid = self.command([
            "/usr/bin/busctl", f"--address={env['DBUS_SESSION_BUS_ADDRESS']}",
            "--auto-start=no", "--timeout=5", "call", "org.freedesktop.DBus",
            "/org/freedesktop/DBus", "org.freedesktop.DBus",
            "GetConnectionUnixProcessID", "s", "org.xfce.SessionManager",
        ], env).strip()
        if bus_pid != f"u {anchor.pid}":
            raise Refused("XFCE session-manager bus owner does not match the live session")
        screens = self.command(["/usr/bin/xdpyinfo"], env)
        if re.findall(r"^number of screens:\s+(\d+)\s*$", screens, re.MULTILINE) != ["1"]:
            raise Refused("Exactly one X screen is required")
        return Session(identifier, leader, anchor, environment_source, environment_identity, tuple(sorted(env.items())),
                       (auth_stat.st_dev, auth_stat.st_ino, auth_stat.st_size, auth_stat.st_mtime_ns))

    def manager(self, session: Session) -> Process | None:
        env = dict(session.environment)
        root = self.command(["/usr/bin/xprop", "-root", "_NET_SUPPORTING_WM_CHECK"], env).strip()
        owner = re.fullmatch(r"_NET_SUPPORTING_WM_CHECK\(WINDOW\): window id # (0x[0-9a-fA-F]+)", root)
        if owner:
            window = owner[1]
            if int(window, 16) == 0:
                raise Refused("Stale zero WM owner property")
            details = self.command(["/usr/bin/xprop", "-id", window,
                                    "_NET_SUPPORTING_WM_CHECK", "_NET_WM_PID"], env)
            expected = (r"_NET_SUPPORTING_WM_CHECK\(WINDOW\): window id # " + re.escape(window)
                        + r"\n_NET_WM_PID\(CARDINAL\) = ([1-9][0-9]*)\n?")
            match = re.fullmatch(expected, details)
            if not match:
                raise Refused("Unverifiable WM owner properties; leaving it untouched")
            process = self.process(int(match[1]))
            if display_number(dict(process.environment).get("DISPLAY", "")) != display_number(env["DISPLAY"]):
                raise Refused("WM owner process has a different display")
            return process
        if root not in {"_NET_SUPPORTING_WM_CHECK:  no such atom on any window.",
                        "_NET_SUPPORTING_WM_CHECK:  not found."}:
            raise Refused("Cannot establish absence of an EWMH window manager")
        events = self.command(["/usr/bin/xwininfo", "-root", "-events"], env)
        section = re.search(r"Someone wants these events:\n(.*?)\s*Do not propagate these events:",
                            events, re.DOTALL)
        if not section:
            raise Refused("Cannot inspect root event ownership")
        known_events = {"KeyPress", "KeyRelease", "ButtonPress", "ButtonRelease", "EnterWindow",
                        "LeaveWindow", "PointerMotion", "PointerMotionHint", "Button1Motion",
                        "Button2Motion", "Button3Motion", "Button4Motion", "Button5Motion",
                        "ButtonMotion", "KeymapState", "Exposure", "VisibilityChange",
                        "StructureNotify", "ResizeRedirect", "SubstructureNotify",
                        "SubstructureRedirect", "FocusChange", "PropertyChange", "ColormapChange",
                        "OwnerGrabButton"}
        if not set(section[1].split()) <= known_events:
            raise Refused("Unrecognized root event ownership output")
        if "SubstructureRedirect" in section[1].split():
            raise Refused("Root redirection is occupied by a window manager; leaving it untouched")
        for process in self.named_processes("xfwm4"):
            value = dict(process.environment).get("DISPLAY", "")
            if display_number(value) == display_number(env["DISPLAY"]):
                raise Refused("An XFWM process exists without verified X ownership; no duplicate start")
        return None

    def unit_state(self, session: Session, *, unit: str | None = None) -> dict[str, str]:
        state = properties(self.command([
            "/usr/bin/systemctl", "--user", "--no-pager", "show", unit or session.unit,
            "--property=LoadState,ActiveState,SubState,MainPID,ControlGroup,Transient,Restart,KillMode",
        ], dict(session.environment), allowed=(0, 4)))
        if not {"LoadState", "ActiveState", "ControlGroup", "Transient"} <= state.keys():
            raise Refused("Incomplete transient-unit state")
        return state

    def receipt_path(self, legacy_unit: str) -> Path:
        return self.runtime / (legacy_unit + ".launch.json")

    def same_process(self, identity) -> bool:
        if (not isinstance(identity, list) or len(identity) != 2
                or any(type(value) is not int or value <= 0 for value in identity)):
            raise Refused("Invalid launch process identity")
        try:
            directory = self.proc / str(identity[0])
            fields = (directory / "stat").read_text().rsplit(")", 1)[1].split()
            return (directory.stat().st_uid == self.uid and int(fields[19]) == identity[1]
                    and fields[0] not in {"Z", "X"})
        except FileNotFoundError:
            return False

    def available(self, session: Session, legacy_unit: str) -> None:
        state = self.unit_state(session, unit=legacy_unit)
        retired = (state["Transient"] == "yes" and state["ActiveState"] in {"inactive", "failed"}
                   and state.get("MainPID") == "0" and state.get("Restart") == "no")
        if state["LoadState"] != "not-found" and not retired:
            raise Refused(f"{legacy_unit} already exists ({state['ActiveState']}); no duplicate submission")
        record = self.read_record(self.receipt_path(legacy_unit))
        if record is None:
            return
        if (not isinstance(record, dict) or not isinstance(record.get("unit"), str)
                or not re.fullmatch(re.escape(legacy_unit.removesuffix('.service')) + r"-[0-9a-f]{32}\.scope",
                                    record["unit"]) or type(record.get("ready")) is not bool):
            raise Refused("Malformed launch receipt")
        identity = record.get("owner") if record["ready"] else record.get("launcher")
        if (identity is None and record.get("exited") is not True) or (identity is not None and self.same_process(identity)):
            raise Refused(f"Outstanding launch {record['unit']}; inspect it before retrying")
        if not record["ready"]:
            prior = self.unit_state(session, unit=record["unit"])
            if prior["LoadState"] != "not-found":
                raise Refused(f"Unconfirmed launch {record['unit']}; no duplicate submission")

    def submit_unit(self, legacy_unit: str, env: dict[str, str], arguments: list[str]) -> str:
        unit = legacy_unit.removesuffix(".service") + "-" + uuid.uuid4().hex + ".scope"
        record = {"unit": unit, "ready": False, "launcher": None, "owner": None}
        path = self.receipt_path(legacy_unit)
        self.write_record(path, record)
        # Scope lifetime follows all its processes, not the GUI parent's exit.
        # systemd-cat connects stdout AND stderr to the journal before exec.
        # Popen must not use communicate(timeout): that would kill a slow launch.
        command = ["/usr/bin/systemd-cat", f"--identifier={unit}",
                   "/usr/bin/systemd-run", "--user", "--no-ask-password", "--scope", "--collect",
                   "--quiet", "--expand-environment=no", f"--unit={unit}", "--slice=app.slice",
                   "--property=OOMPolicy=continue", "--", *arguments]
        try:
            child = self.spawner(command, env=dict(env), cwd=env["HOME"],
                                 stdin=subprocess.DEVNULL, start_new_session=True)
        except OSError as error:
            path.unlink()  # Popen guarantees that no child was successfully exec'd.
            raise Refused(f"Cannot launch {unit}: {error}") from error
        self.children.append(child)
        try:
            process = self.process(child.pid)
        except (FileNotFoundError, Refused):
            # A fast failure is still reported through readiness and the journal.
            if child.poll() is not None:
                record["exited"] = True
                self.write_record(path, record)
            return unit
        record["launcher"] = [process.pid, process.ticks]
        self.write_record(path, record)
        return unit

    def confirm_launch(self, legacy_unit: str, unit: str, process: Process) -> None:
        path = self.receipt_path(legacy_unit)
        record = self.read_record(path)
        if not isinstance(record, dict) or record.get("unit") != unit:
            raise Refused("Launch receipt changed during startup")
        record.update(ready=True, owner=[process.pid, process.ticks])
        self.write_record(path, record)

    def observe_launch(self, session: Session, legacy_unit: str, process: Process) -> None:
        record = self.read_record(self.receipt_path(legacy_unit))
        if isinstance(record, dict) and record.get("ready") is False:
            unit = record.get("unit", "")
            if isinstance(unit, str) and re.fullmatch(
                    re.escape(legacy_unit.removesuffix('.service')) + r"-[0-9a-f]{32}\.scope", unit):
                if self.scope_ready(self.unit_state(session, unit=unit), unit, process):
                    self.confirm_launch(legacy_unit, unit, process)

    def scope_ready(self, state: dict[str, str], unit: str, process: Process) -> bool:
        return (state["LoadState"] == "loaded" and state["Transient"] == "yes"
                and state["ActiveState"] == "active" and unit.endswith(".scope")
                and state["ControlGroup"].endswith("/" + unit)
                and any(line.split(":", 2)[-1] == state["ControlGroup"]
                        for line in process.cgroup.splitlines()))

    def protect_legacy_unit(self, session: Session, unit: str, process: Process) -> bool:
        """Retire old service supervision without stopping its GUI or applications."""
        if not self.in_scope(process, unit):
            return False
        state = self.unit_state(session, unit=unit)
        if (state["LoadState"] != "loaded" or state["Transient"] != "yes"
                or state["ActiveState"] != "active" or state.get("MainPID") != str(process.pid)
                or not state["ControlGroup"].endswith("/" + unit)
                or not any(line.split(":", 2)[-1] == state["ControlGroup"]
                           for line in process.cgroup.splitlines())):
            raise Refused(f"Cannot authenticate legacy service {unit}")
        if state.get("KillMode") == "process" and state.get("Restart") == "no":
            return False
        directory = self.runtime
        for name in ("systemd", "user", unit + ".d"):
            directory = directory / name
            directory.mkdir(mode=0o700, exist_ok=True)
            info = directory.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != self.uid or info.st_mode & 0o022:
                raise Refused(f"Unsafe runtime unit directory: {directory}")
        path = directory / "90-xfce-recovery-preserve-apps.conf"
        content = "[Service]\nKillMode=process\nRestart=no\n"
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            info = path.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.uid or info.st_mode & 0o022
                    or info.st_nlink != 1 or path.read_text() != content):
                raise Refused(f"Preserve conflicting runtime override: {path}")
        else:
            with os.fdopen(descriptor, "w") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        self.command(["/usr/bin/systemctl", "--user", "daemon-reload"], dict(session.environment))
        current = self.unit_state(session, unit=unit)
        if (current.get("KillMode") != "process" or current.get("Restart") != "no"
                or current.get("MainPID") != str(process.pid) or self.process(process.pid) != process):
            raise Refused(f"Legacy protection not confirmed for {unit}; no process was stopped")
        return True

    def start(self, session: Session, sm_client_id: str | None, *, register_session=True) -> str:
        env = dict(session.environment)
        scope = f"session-{session.identifier}.scope"
        caller_group = (self.proc / "self" / "cgroup").read_text()
        manager = os.environ.get("SESSION_MANAGER", "")
        trusted_sm = (register_session and any(scope in line.split(":", 2)[-1].split("/")
                          for line in caller_group.splitlines())
                      and re.search(r"/tmp/\.ICE-unix/" + str(session.anchor.pid) + r"(?:,|$)", manager))
        arguments = []
        if trusted_sm:
            env["SESSION_MANAGER"] = manager
            if sm_client_id:
                arguments.append(f"--sm-client-id={sm_client_id}")
        elif sm_client_id:
            raise Refused("A session-client ID requires an authenticated XFCE session caller")
        else:
            arguments.append("--sm-client-disable")
        return self.submit_unit(session.unit, env, ["/usr/bin/xfwm4", *arguments])


@contextlib.contextmanager
def session_lock(host: Host, session: Session, timeout: float):
    path = host.runtime / f"xfwm4-launch-{session.identifier}.lock"
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != host.uid
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise Refused("Unsafe session lock file")
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise Refused("Another launcher is still working; lock wait expired")
                time.sleep(0.05)
        yield
    finally:
        os.close(descriptor)  # Never unlink: another caller may already have this inode open.


def launch(host: Host, *, start=False, sm_client_id=None, timeout=10.0) -> str:
    session = host.discover()
    if not start:
        manager = host.manager(session)
        if manager:
            return f"Session {session.identifier}: window manager present (PID {manager.pid}); unchanged."
        state = host.unit_state(session)
        return (f"Session {session.identifier}: no verified window manager. "
                f"Unit {session.unit}: {state['LoadState']}/{state['ActiveState']}. No action taken.")
    with session_lock(host, session, timeout):
        return _launch_locked(host, session, sm_client_id=sm_client_id, timeout=timeout)


def _launch_locked(host: Host, session: Session, *, sm_client_id=None,
                   timeout=10.0, register_session=True) -> str:
    """Shared WM flow; callers must hold session_lock for the bound session."""
    if host.discover() != session:
        raise Refused("Graphical session changed while waiting; no startup submitted")
    manager = host.manager(session)
    if manager:
        host.observe_launch(session, session.unit, manager)
        host.save_environment(session)
        if manager.matches_executable("/usr/bin/xfwm4"):
            host.protect_legacy_unit(session, session.unit, manager)
        return f"Session {session.identifier}: window manager present (PID {manager.pid}); unchanged."
    host.available(session, session.unit)
    if host.discover() != session:
        raise Refused("Graphical session changed before launch; no startup submitted")
    if host.manager(session) is not None:
        return f"Session {session.identifier}: window manager appeared; unchanged."
    host.save_environment(session)
    attempted_unit = host.start(session, sm_client_id, register_session=register_session)
    deadline = time.monotonic() + timeout
    evidence = "no verified owner"
    while True:
        try:
            if host.discover() != session:
                raise Refused("Graphical session changed after submission")
            state = host.unit_state(session, unit=attempted_unit)
            manager = host.manager(session)
            if (manager is not None and manager.matches_executable("/usr/bin/xfwm4")
                    and host.scope_ready(state, attempted_unit, manager)
                    and host.process(manager.pid) == manager):
                host.confirm_launch(session.unit, attempted_unit, manager)
                return f"Session {session.identifier}: XFWM ready (PID {manager.pid}, {attempted_unit})."
            evidence = f"unit={state['LoadState']}/{state['ActiveState']}; owner={manager.pid if manager else 'absent'}"
            if state["ActiveState"] == "failed":
                raise Refused(f"Startup failed: {evidence}")
        except (Refused, OSError, ValueError) as error:
            evidence = str(error)
        if time.monotonic() >= deadline:
            raise Refused(f"Startup not confirmed for {attempted_unit}: {evidence}. "
                          "No retry or rollback performed.")
        time.sleep(0.1)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", action="store_true", help="start absent XFWM after checks (default: read-only)")
    parser.add_argument("--sm-client-id", help="XFCE session-client ID; requires --start and a trusted session caller")
    args = parser.parse_args(argv)
    if args.sm_client_id and not args.start:
        parser.error("--sm-client-id requires --start")
    try:
        print(launch(Host(), start=args.start, sm_client_id=args.sm_client_id))
        return 0
    except (Refused, OSError, ValueError, KeyError, IndexError, UnicodeError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
