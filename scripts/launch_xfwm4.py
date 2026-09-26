#!/usr/bin/python3
"""Check XFWM safely; --start launches it only for an authenticated, empty X session.

The lock coordinates this launcher and recover_xfce.py; other starters can bypass
it. Installing the file does not change XFCE startup or saved restart commands.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import sys
import time
from dataclasses import dataclass


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


@dataclass(frozen=True)
class Session:
    identifier: str
    leader: tuple[int, int, int, str]
    anchor: Process
    environment: tuple[tuple[str, str], ...]
    authority_identity: tuple[int, int, int, int]

    @property
    def unit(self) -> str:
        return f"xfwm4-launch-{self.identifier}.service"


class Host:
    """OS boundaries are injectable for tests; CLI never accepts alternate roots."""

    def __init__(self, *, proc=Path("/proc"), runtime=None, uid=None, runner=None):
        self.uid = os.getuid() if uid is None else uid
        self.proc = proc
        account = pwd.getpwuid(self.uid)
        self.runtime = Path(f"/run/user/{self.uid}") if runtime is None else runtime
        self.base_env = {
            "HOME": account.pw_dir, "USER": account.pw_name,
            "LOGNAME": account.pw_name, "PATH": "/usr/bin:/bin", "LC_ALL": "C",
            "XDG_RUNTIME_DIR": str(self.runtime),
            "DBUS_SESSION_BUS_ADDRESS": f"unix:path={self.runtime}/bus",
        }
        self.runner = subprocess.run if runner is None else runner

    def command(self, argv, env=None, *, allowed=(0,)) -> str:
        try:
            result = self.runner(
                argv, env=self.base_env if env is None else env,
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
                key, separator, value = entry.decode().partition("=")
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
        if anchor.executable != "/usr/bin/xfce4-session":
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
        env = dict(self.base_env)
        for key in ("DISPLAY", "XAUTHORITY", "XDG_CONFIG_HOME", "XDG_CONFIG_DIRS",
                    "XDG_DATA_HOME", "XDG_DATA_DIRS", "XDG_CURRENT_DESKTOP", "LANG"):
            if key in source:
                env[key] = source[key]
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
        return Session(identifier, leader, anchor, tuple(sorted(env.items())),
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
            "--property=LoadState,ActiveState,SubState,MainPID,ControlGroup,Transient",
        ], dict(session.environment), allowed=(0, 4)))
        if not {"LoadState", "ActiveState", "MainPID", "ControlGroup", "Transient"} <= state.keys():
            raise Refused("Incomplete transient-unit state")
        return state

    def start(self, session: Session, sm_client_id: str | None, *, register_session=True) -> None:
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
        self.command([
            "/usr/bin/systemd-run", "--user", "--no-ask-password", "--collect",
            "--service-type=exec", "--expand-environment=no", f"--unit={session.unit}",
            "--property=Restart=no", "--", "/usr/bin/env", "-i",
            *(f"{key}={value}" for key, value in sorted(env.items())),
            "/usr/bin/xfwm4", *arguments,
        ], dict(session.environment))


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
        return f"Session {session.identifier}: window manager present (PID {manager.pid}); unchanged."
    state = host.unit_state(session)
    if state["LoadState"] != "not-found":
        raise Refused(f"{session.unit} already exists ({state['ActiveState']}); inspect it before retrying")
    if host.discover() != session:
        raise Refused("Graphical session changed before launch; no startup submitted")
    if host.manager(session) is not None:
        return f"Session {session.identifier}: window manager appeared; unchanged."
    attempted_unit = session.unit
    submission_error = ""
    try:
        host.start(session, sm_client_id, register_session=register_session)
    except Refused as error:
        submission_error = str(error)
    deadline = time.monotonic() + timeout
    evidence = "no verified owner"
    while True:
        try:
            if host.discover() != session:
                raise Refused("Graphical session changed after submission")
            state = host.unit_state(session)
            manager = host.manager(session)
            if (manager is not None and manager.executable == "/usr/bin/xfwm4"
                    and state["LoadState"] == "loaded" and state["Transient"] == "yes"
                    and state["ActiveState"] == "active" and state["MainPID"] == str(manager.pid)
                    and state["ControlGroup"].endswith("/" + attempted_unit)
                    and any(line.split(":", 2)[-1] == state["ControlGroup"]
                            for line in manager.cgroup.splitlines())
                    and host.process(manager.pid) == manager):
                return f"Session {session.identifier}: XFWM ready (PID {manager.pid}, {attempted_unit})."
            evidence = f"unit={state['LoadState']}/{state['ActiveState']}; owner={manager.pid if manager else 'absent'}"
            if state["ActiveState"] == "failed":
                raise Refused(f"Startup failed: {evidence}")
        except (Refused, OSError, ValueError) as error:
            evidence = str(error)
        if time.monotonic() >= deadline:
            raise Refused(f"Startup not confirmed for {attempted_unit}: {evidence}. "
                          f"No retry or rollback performed. {submission_error}".rstrip())
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
