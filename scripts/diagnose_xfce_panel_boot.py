#!/usr/bin/python3
"""Opt-in, one-boot Xfconf capture with optional one-shot panel restoration.

prepare saves private evidence; activate installs temporary hooks. cleanup restores
the exact pre-capture launchers. Neither cleanup nor preparation changes panel XML.
Keep this file beside xfce_panel_startup.py until cleanup has completed.
"""

from __future__ import annotations

import argparse
import configparser
import ctypes
import datetime
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
import xfce_panel_startup as startup

SEARCH_ENV = ("HOME", "XDG_CONFIG_HOME", "XDG_CONFIG_DIRS", "XDG_DATA_DIRS",
              "XDG_CURRENT_DESKTOP", "LD_LIBRARY_PATH")


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def current_boot():
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def run_directory(home, run):
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}", run):
        raise startup.Refused("Invalid capture identifier")
    return startup.state_dir(home) / "captures" / run


def exclusive_write(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    startup.fsync_dir(path.parent)


def expected_from_git(home, revision):
    commit = subprocess.run(["git", "-C", str(home), "rev-parse", "--verify", "--end-of-options",
                             revision + "^{commit}"], check=True, capture_output=True, text=True).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise startup.Refused("Unexpected Git commit identity")
    data = subprocess.run(["git", "-C", str(home), "show", commit + ":" + str(startup.PANEL)],
                          check=True, capture_output=True).stdout
    return data, {"git_commit": commit, "git_path": str(startup.PANEL)}


def hook_entries(home, run, script):
    startup.regular_file(home / startup.SERVICE)
    startup.regular_file(home / startup.AUTOSTART)
    original = (home / startup.SERVICE).read_bytes()
    daemon, environment = startup.parse_activation(startup.service_entry(original), home)
    if daemon != str(home / startup.DAEMON):
        raise startup.Refused("Capture supports the existing local-build daemon only")
    prefix = ["/usr/bin/env", startup.ASSIGNMENT] if environment else []
    command = ["/usr/bin/python3", str(script), "launch", run, "dbus"]
    changes = {startup.SERVICE: (original, startup.replace_exec(original, shlex.join(prefix + command)))}
    desktop = (home / startup.AUTOSTART).read_bytes()
    arguments = startup.desktop_arguments(desktop)
    if arguments == ["/bin/sh", "-c", startup.OLD_PREFIX + startup.OLD_TAIL]:
        command[-1] = "autostart"
        shell = arguments[2].replace("~/.local/lib/xfce4/xfconf/xfconfd &",
                                    shlex.join(command) + " &")
        # Preserve command behavior, but expose errors instead of suppressing them.
        shell = shell.replace(" 2>/dev/null", "")
        changes[startup.AUTOSTART] = (desktop, startup.desktop_shell(desktop, shell))
    elif arguments != ["/bin/sh", "-c", startup.FIXED_TAIL]:
        raise startup.Refused("Unknown autostart command; refusing incomplete capture")
    return changes


def prepare(home, expected=None, provenance=None, *, script=None):
    startup.validate_home(home)
    script = script or Path(__file__).resolve()
    if expected is not None:
        xml = ET.fromstring(expected)
        if xml.tag != "channel" or xml.get("name") != "xfce4-panel":
            raise startup.Refused("Expected an xfce4-panel channel XML")
    with startup.operation_lock(home):
        if startup.capture_active(home):
            raise startup.Refused("Clean up the active capture before preparing another")
        run = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:12]
        changes = hook_entries(home, run, script)
        transaction = startup.make_transaction(home, changes)
        panel = home / startup.PANEL
        startup.regular_file(panel)
        previous = panel.read_bytes()
        root = run_directory(home, run)
        startup.private_directory(root.parent)
        root.mkdir(mode=0o700)
        startup.fsync_dir(root.parent)
        (root / "runs").mkdir(mode=0o700)
        startup.fsync_dir(root)
        exclusive_write(root / "prepared-panel.xml", previous)
        if expected is not None:
            exclusive_write(root / "expected-panel.xml", expected)
        startup.write_json(root / "transaction.json", transaction)
        startup.write_json(root / "manifest.json", {
            "schema": 1, "prepared_boot": current_boot(), "prepared_at": timestamp(),
            "panel_sha256": startup.sha(previous),
            "expected_sha256": startup.sha(expected) if expected is not None else None,
            "provenance": provenance or {}, "script": str(script)})
        return run


def activate(home, run):
    startup.validate_home(home)
    with startup.operation_lock(home):
        root = run_directory(home, run)
        manifest = startup.read_json(root / "manifest.json")
        if manifest["schema"] != 1 or manifest["prepared_boot"] != current_boot():
            raise startup.Refused("Capture must be activated in its preparation boot")
        if (root / "receipt.json").exists():
            raise startup.Refused("A capture was already attempted; do not rearm it")
        active = startup.capture_active(home)
        if active is not None and active != run:
            raise startup.Refused("Another capture is active")
        startup.transaction_entries(home, startup.read_json(root / "transaction.json"))
        startup.write_json(startup.state_dir(home) / "active-capture.json", {"run": run})
        startup.write_json(root / "arm.json", {"enabled": True})
        startup.switch_transaction(home, root / "transaction.json", True)


def prepare_capture(home, run, boot, source):
    """Claim restoration durably before mutation, at most once in one later boot."""
    startup.validate_home(home)
    with startup.operation_lock(home):
        root = run_directory(home, run)
        manifest = startup.read_json(root / "manifest.json")
        if (manifest["schema"] != 1 or not startup.read_json(root / "arm.json")["enabled"]
                or boot == manifest["prepared_boot"]):
            return None
        receipt_path = root / "receipt.json"
        receipt = startup.read_json(receipt_path) if receipt_path.exists() else None
        if receipt and receipt["boot_id"] != boot:
            return None
        folder = root / "runs" / boot
        folder.mkdir(mode=0o700, exist_ok=True)
        startup.fsync_dir(folder.parent)
        panel = home / startup.PANEL
        if receipt is None:
            receipt = {"boot_id": boot, "phase": "claimed", "pid": os.getpid(),
                       "source": source, "claimed_at": timestamp()}
            startup.write_json(receipt_path, receipt)
            try:
                info = startup.regular_file(panel)
                previous = panel.read_bytes()
                exclusive_write(folder / "before-restore.xml", previous)
                if manifest["expected_sha256"] is not None:
                    expected = (root / "expected-panel.xml").read_bytes()
                    if startup.sha(expected) != manifest["expected_sha256"]:
                        raise startup.Refused("Pinned XML checksum mismatch")
                    startup.atomic_write(panel, expected, info.st_mode & 0o777, expected=(previous,))
                    if panel.read_bytes() != expected:
                        raise startup.Refused("Restoration read-back mismatch")
                    receipt["phase"] = "restored"
                    receipt["expected_sha256"] = startup.sha(expected)
                else:
                    receipt["phase"] = "observing"
                receipt.update(before_sha256=startup.sha(previous), completed_at=timestamp())
                startup.write_json(receipt_path, receipt)
            except Exception as error:
                receipt.update(phase="uncertain", error=f"{type(error).__name__}: {error}")
                startup.write_json(receipt_path, receipt)
                print("xfce-panel-capture: " + receipt["error"], file=sys.stderr, flush=True)
        stem = f"{time.time_ns()}-{os.getpid()}-{source}"
        record = {"boot_id": boot, "pid": os.getpid(), "ppid": os.getppid(), "source": source,
                  "time_utc": timestamp(), "monotonic_ns": time.monotonic_ns(),
                  "restore_phase": receipt["phase"],
                  "environment": {key: os.environ.get(key) for key in SEARCH_ENV}}
        data = panel.read_bytes()
        exclusive_write(folder / (stem + ".xml"), data)
        record["panel_sha256"] = startup.sha(data)
        startup.write_json(folder / (stem + ".json"), record)
        trace = folder / (stem + ".strace")
        exclusive_write(trace, b"")
        return trace


def traced_command(home, trace, pid):
    relative = "xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
    paths = {str(home / startup.PANEL), str(home / startup.PANEL) + ".new"}
    # libxfce's save directory ends with '/', and Xfconf adds another '/'.
    # strace's pathname filter also needs that spelling for actual persistence.
    for suffix in ("xfce4-panel.xml", "xfce4-panel.xml.new"):
        paths.add(str((home / startup.PANEL).parent) + "//" + suffix)
    directories = {"/etc/xdg", "/etc/xdg/xdg-xfce", str(home / ".local/etc/xdg")}
    directories.update(os.environ.get("XDG_CONFIG_DIRS", "").split(":"))
    for directory in directories:
        if directory and Path(directory).is_absolute():
            path = Path(directory) / relative
            paths.update((str(path), str(path.resolve())))
    command = ["/usr/bin/strace", "-f", "-I", "1", "-ttt", "-s", "1024",
               "-e", "trace=%file", "-o", str(trace)]
    for path in sorted(paths):
        command.extend(("-P", path))
    return command + ["-p", str(pid)]


def attach_tracer(home, trace):
    """Keep the original PID alive until strace proves it has attached."""
    command = traced_command(home, trace, os.getpid())
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                           ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int

    def allow_tracer(pid):
        # Per-process Yama exception for this child only; never PTRACER_ANY.
        if libc.prctl(0x59616d61, pid, 0, 0, 0) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))

    reader, writer = os.pipe()
    try:
        child = os.fork()
    except BaseException:
        os.close(reader)
        os.close(writer)
        raise
    if child == 0:
        try:
            os.close(writer)
            ready = os.read(reader, 1)
            os.close(reader)
            if ready == b'1':
                os.execv(command[0], command)
        except BaseException as error:
            print(f'xfce-panel-diagnostic: tracer child failed: {error}',
                  file=sys.stderr, flush=True)
        os._exit(127)

    os.close(reader)
    reaped = False
    try:
        allow_tracer(child)
        os.write(writer, b'1')
        os.close(writer)
        writer = None
        deadline = time.monotonic() + 3
        while True:
            exited, status = os.waitpid(child, os.WNOHANG)
            if exited:
                reaped = True
                raise RuntimeError(f'Tracer exited before attachment (wait status {status})')
            tracer = next(line.split(':', 1)[1].strip()
                          for line in Path('/proc/self/status').read_text().splitlines()
                          if line.startswith('TracerPid:'))
            if int(tracer) == child:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Tracer did not attach within three seconds')
            time.sleep(0.01)
        allow_tracer(0)
        return child
    except BaseException:
        if not reaped:
            # This unreaped child cannot have had its PID reused. No EXITKILL
            # option is used, so killing the tracer leaves this process alive.
            os.kill(child, signal.SIGKILL)
            os.waitpid(child, 0)
        allow_tracer(0)
        raise
    finally:
        if writer is not None:
            os.close(writer)


def launch(home, run, source, arguments):
    daemon = str(home / startup.DAEMON)
    try:
        trace = prepare_capture(home, run, current_boot(), source)
        if trace is not None:
            try:
                tracer = attach_tracer(home, trace)
            except Exception as error:
                startup.write_json(trace.with_suffix(".trace-status.json"), {
                    "status": "failed", "error": str(error), "time_utc": timestamp()})
                raise
            startup.write_json(trace.with_suffix(".trace-status.json"), {
                "status": "attached", "tracer_pid": tracer, "time_utc": timestamp()})
    except Exception as error:
        print(f"xfce-panel-capture: capture failed; starting original daemon: {error}",
              file=sys.stderr, flush=True)
    os.execv(daemon, [daemon, *arguments])


def owned_tracers(root):
    result = []
    for directory in Path("/proc").iterdir():
        if not directory.name.isdigit():
            continue
        try:
            if directory.stat().st_uid != os.getuid() or (directory / "exe").resolve() != Path("/usr/bin/strace"):
                continue
            args = (directory / "cmdline").read_bytes().decode().rstrip("\0").split("\0")
            if "-o" not in args:
                continue
            output = Path(args[args.index("-o") + 1])
            if output.parent.parent == root / "runs" and output.suffix == ".strace":
                result.append(int(directory.name))
        except (OSError, ValueError, IndexError, UnicodeError):
            continue
    return result


def cleanup(home, run):
    startup.validate_home(home)
    root = run_directory(home, run)
    with startup.operation_lock(home):
        active = startup.capture_active(home)
        if active is not None and active != run:
            raise startup.Refused("Another capture is active; do not clean up an unrelated run")
        startup.read_json(root / "manifest.json")
        startup.write_json(root / "arm.json", {"enabled": False})
        transaction = startup.read_json(root / "transaction.json")
        if transaction["phase"] != "undone":
            startup.switch_transaction(home, root / "transaction.json", False)
        if active == run:
            (startup.state_dir(home) / "active-capture.json").unlink()
            startup.fsync_dir(startup.state_dir(home))
    for pid in owned_tracers(root):
        try:
            descriptor = os.pidfd_open(pid)
        except ProcessLookupError:
            continue
        try:
            if pid in owned_tracers(root):
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        finally:
            os.close(descriptor)


def status(home, run):
    root = run_directory(home, run)
    result = {"run": run, "directory": str(root)}
    for name in ("manifest", "arm", "receipt", "transaction"):
        path = root / (name + ".json")
        data = startup.read_json(path) if path.exists() else None
        result[name] = {"phase": data["phase"]} if name == "transaction" and data else data
    result["tracers"] = owned_tracers(root)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    preparation = sub.add_parser("prepare", help="Save a new private capture; no live changes")
    restore = preparation.add_mutually_exclusive_group()
    restore.add_argument("--restore-from-git", metavar="REVISION")
    restore.add_argument("--expected-xml", type=Path)
    for command in ("activate", "cleanup", "status", "launch"):
        item = sub.add_parser(command)
        item.add_argument("run")
        if command == "launch":
            item.add_argument("source", choices=("dbus", "autostart"))
            item.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    home = Path.home()
    try:
        if args.command == "prepare":
            expected, provenance = None, None
            if args.restore_from_git:
                expected, provenance = expected_from_git(home, args.restore_from_git)
            elif args.expected_xml:
                expected = args.expected_xml.read_bytes()
                provenance = {"file": str(args.expected_xml.resolve())}
            print(prepare(home, expected, provenance))
        elif args.command == "launch":
            launch(home, args.run, args.source, args.arguments)
        else:
            if args.command == "activate":
                activate(home, args.run)
            elif args.command == "cleanup":
                cleanup(home, args.run)
            import json
            print(json.dumps(status(home, args.run), indent=2))
    except (startup.Refused, OSError, ValueError, KeyError, ET.ParseError, configparser.Error,
            subprocess.CalledProcessError) as error:
        print(f"xfce-panel-capture: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr,
                  file=sys.stderr, end="")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
