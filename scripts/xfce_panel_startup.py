#!/usr/bin/python3
"""Inspect or repair the known local-build Xfconf startup on Linux Mint.

No arguments inspects only. Apply/undo change launch files, never running clients or
the panel XML. Private transaction state also coordinates optional boot capture.
"""

from __future__ import annotations

import argparse
import base64
import configparser
import contextlib
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import sys
import tempfile

sys.dont_write_bytecode = True

MINT_DIRS = "/etc/xdg/xdg-xfce:/etc/xdg"
ASSIGNMENT = "XDG_CONFIG_DIRS=" + MINT_DIRS
PANEL = Path(".config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml")
DAEMON = Path(".local/lib/xfce4/xfconf/xfconfd")
SERVICE = Path(".local/share/dbus-1/services/org.xfce.Xfconf.service")
AUTOSTART = Path(".config/autostart/xfconfd-local.desktop")
MINT_XML = Path("/etc/xdg/xdg-xfce/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml")
OLD_PREFIX = "pkill xfconfd 2>/dev/null; sleep 0.3; ~/.local/lib/xfce4/xfconf/xfconfd & sleep 1; "
OLD_TAIL = ("pkill xfsettingsd 2>/dev/null; sleep 0.3; xfsettingsd --display :0.0 & sleep 0.5; "
            "pkill xfce4-panel 2>/dev/null; sleep 0.5; NO_AT_BRIDGE=1 "
            "XFCE_PANEL_PLUGIN_PATH=$HOME/.local/lib/xfce4/panel/plugins:"
            "/usr/lib/x86_64-linux-gnu/xfce4/panel/plugins ~/.local/bin/xfce4-panel")
FIXED_TAIL = OLD_TAIL.replace(" 2>/dev/null", "")


class Refused(RuntimeError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def state_dir(home):
    return home / ".local/state/xfce-panel-startup"


def private_directory(path):
    if path.resolve() != path:
        raise Refused(f"Refusing symbolic-link state directory: {path}")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if path.resolve() != path or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise Refused(f"Unsafe private state directory: {path}")


def validate_home(home):
    if home != home.resolve() or home.stat().st_uid != os.getuid():
        raise Refused("Expected the current user's real home directory")
    for variable, relative in (("XDG_CONFIG_HOME", ".config"),
                               ("XDG_DATA_HOME", ".local/share")):
        value = os.environ.get(variable)
        if value and Path(value) != home / relative:
            raise Refused(f"Nonstandard {variable}; inspect the target paths manually")


@contextlib.contextmanager
def operation_lock(home):
    root = state_dir(home)
    private_directory(root)
    fd = os.open(root / "operation.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "r+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def regular_file(path):
    info = path.lstat()
    if path.resolve() != path or not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        raise Refused(f"Unexpected file type, path or owner: {path}")
    return info


def atomic_write(path, data, mode=0o600, expected=None):
    if path.is_symlink() or path.parent.resolve() != path.parent:
        raise Refused(f"Refusing symbolic-link destination: {path}")
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if expected is not None:
            regular_file(path)
            if path.read_bytes() not in expected:
                raise Refused(f"Concurrent file change; refusing overwrite: {path}")
        os.replace(temporary, path)
        fsync_dir(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    atomic_write(path, (json.dumps(value, indent=2) + "\n").encode())


def read_json(path):
    regular_file(path)
    return json.loads(path.read_text())


def parse_activation(entry, home):
    """Recognize only direct Xfconf or the exact Mint environment overlay."""
    command = shlex.split(entry["Exec"])
    env = ()
    if command[:2] == ["/usr/bin/env", ASSIGNMENT]:
        env = (("XDG_CONFIG_DIRS", MINT_DIRS),)
        command = command[2:]
    allowed = {str(home / DAEMON), "/usr/lib/x86_64-linux-gnu/xfce4/xfconf/xfconfd"}
    if (entry.get("Name") != "org.xfce.Xfconf" or "SystemdService" in entry
            or len(command) != 1 or command[0] not in allowed):
        raise Refused("Unsupported xfconf activation command; preserve it and inspect manually")
    return command[0], env


def service_entry(data):
    config = configparser.ConfigParser(interpolation=None, strict=True)
    config.read_string(data.decode())
    return config["D-BUS Service"]


def replace_exec(data, value):
    lines = data.decode().splitlines(keepends=True)
    indices = [i for i, line in enumerate(lines) if line.startswith("Exec=")]
    if len(indices) != 1:
        raise Refused("Expected exactly one Exec line")
    lines[indices[0]] = "Exec=" + value + "\n"
    return "".join(lines).encode()


def desktop_arguments(data):
    """Use the same key-file and command parsing as the desktop's GLib."""
    lib = ctypes.CDLL("libglib-2.0.so.0")
    ptr = ctypes.c_void_p
    lib.g_key_file_new.restype = ptr
    lib.g_key_file_load_from_data.argtypes = [ptr, ctypes.c_char_p, ctypes.c_size_t,
                                            ctypes.c_int, ctypes.POINTER(ptr)]
    lib.g_key_file_load_from_data.restype = ctypes.c_int
    lib.g_key_file_get_string.argtypes = [ptr, ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ptr)]
    lib.g_key_file_get_string.restype = ptr
    lib.g_shell_parse_argv.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int),
                                     ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p)), ctypes.POINTER(ptr)]
    lib.g_shell_parse_argv.restype = ctypes.c_int
    lib.g_strfreev.argtypes = [ctypes.POINTER(ctypes.c_char_p)]
    lib.g_free.argtypes = [ptr]
    lib.g_error_free.argtypes = [ptr]
    lib.g_key_file_free.argtypes = [ptr]
    key, error, value = lib.g_key_file_new(), ptr(), None
    argv = ctypes.POINTER(ctypes.c_char_p)()
    try:
        if not lib.g_key_file_load_from_data(key, data, len(data), 0, ctypes.byref(error)):
            raise Refused("Invalid desktop key file")
        value = lib.g_key_file_get_string(key, b"Desktop Entry", b"Exec", ctypes.byref(error))
        if not value:
            raise Refused("Missing desktop Exec")
        count = ctypes.c_int()
        if not lib.g_shell_parse_argv(ctypes.cast(value, ctypes.c_char_p), ctypes.byref(count),
                                      ctypes.byref(argv), ctypes.byref(error)):
            raise Refused("Invalid desktop command")
        return [argv[i].decode() for i in range(count.value)]
    finally:
        if argv:
            lib.g_strfreev(argv)
        if value:
            lib.g_free(value)
        if error:
            lib.g_error_free(error)
        lib.g_key_file_free(key)


def desktop_shell(data, body):
    # Shell argv quoting, followed by the desktop key-file escaping layer.
    escaped = body
    for character in ("\\", '"', "`", "$"):
        escaped = escaped.replace(character, "\\" + character)
    value = '/bin/sh -c "' + escaped + '"'
    proposed = replace_exec(data, value.replace("\\", "\\\\"))
    if desktop_arguments(proposed) != ["/bin/sh", "-c", body]:
        raise Refused("Desktop command did not round-trip")
    return proposed


def repaired_entries(home):
    regular_file(home / SERVICE)
    regular_file(home / AUTOSTART)
    service = (home / SERVICE).read_bytes()
    daemon, _ = parse_activation(service_entry(service), home)
    if daemon != str(home / DAEMON):
        raise Refused("This repair targets the existing local-build daemon only")
    desktop = (home / AUTOSTART).read_bytes()
    arguments = desktop_arguments(desktop)
    if arguments not in (["/bin/sh", "-c", OLD_PREFIX + OLD_TAIL],
                          ["/bin/sh", "-c", FIXED_TAIL]):
        raise Refused("Unrecognized autostart sequence; inspect it manually")
    return {SERVICE: (service, replace_exec(service, shlex.join(["/usr/bin/env", ASSIGNMENT, daemon]))),
            AUTOSTART: (desktop, desktop_shell(desktop, FIXED_TAIL))}


def make_transaction(home, changes):
    entries = []
    for relative, (before, after) in changes.items():
        if relative.is_absolute() or ".." in relative.parts:
            raise Refused("Invalid transaction path")
        info = regular_file(home / relative)
        if (home / relative).read_bytes() != before:
            raise Refused(f"Concurrent file change before transaction: {home / relative}")
        entries.append({"path": str(relative), "mode": stat.S_IMODE(info.st_mode),
                        "before": base64.b64encode(before).decode(),
                        "after": base64.b64encode(after).decode(),
                        "before_sha": sha(before), "after_sha": sha(after)})
    return {"schema": 1, "phase": "prepared", "entries": entries}


def transaction_entries(home, transaction):
    if transaction["schema"] != 1:
        raise Refused("Unknown transaction schema")
    result = []
    for entry in transaction["entries"]:
        relative = Path(entry["path"])
        if relative not in (SERVICE, AUTOSTART):
            raise Refused("Unexpected transaction target")
        before = base64.b64decode(entry["before"], validate=True)
        after = base64.b64decode(entry["after"], validate=True)
        if sha(before) != entry["before_sha"] or sha(after) != entry["after_sha"]:
            raise Refused("Transaction checksum mismatch")
        path = home / relative
        regular_file(path)
        if path.read_bytes() not in (before, after):
            raise Refused(f"Concurrent file change; refusing overwrite: {path}")
        result.append((path, before, after, entry["mode"]))
    if len(result) != len({item[0] for item in result}):
        raise Refused("Duplicate transaction target")
    return result


def switch_transaction(home, path, forward):
    transaction = read_json(path)
    entries = transaction_entries(home, transaction)
    transaction["phase"] = "applying" if forward else "undoing"
    write_json(path, transaction)
    for target, before, after, mode in entries:
        data = after if forward else before
        atomic_write(target, data, mode, expected=(before, after))
        if target.read_bytes() != data:
            raise Refused(f"Read-back mismatch: {target}")
    transaction["phase"] = "applied" if forward else "undone"
    write_json(path, transaction)


def capture_active(home):
    path = state_dir(home) / "active-capture.json"
    return read_json(path)["run"] if path.exists() else None


def apply(home, *, mint_xml=MINT_XML):
    validate_home(home)
    with operation_lock(home):
        if capture_active(home):
            raise Refused("Clean up the active capture before changing the permanent repair")
        if not mint_xml.is_file() or not os.access(home / DAEMON, os.X_OK):
            raise Refused("Required Mint defaults or local Xfconf executable is missing")
        changes = repaired_entries(home)
        path = state_dir(home) / "repair.json"
        if not path.exists():
            write_json(path, make_transaction(home, changes))
        else:
            transaction = read_json(path)
            transaction_entries(home, transaction)
            saved = {Path(e["path"]): base64.b64decode(e["after"]) for e in transaction["entries"]}
            if saved != {relative: after for relative, (_, after) in changes.items()}:
                raise Refused("Saved repair differs; reconcile before updating it")
        switch_transaction(home, path, True)


def undo(home):
    validate_home(home)
    with operation_lock(home):
        if capture_active(home):
            raise Refused("Clean up the active capture before undoing the permanent repair")
        switch_transaction(home, state_dir(home) / "repair.json", False)


def status(home):
    entry = service_entry((home / SERVICE).read_bytes())
    try:
        daemon, environment = parse_activation(entry, home)
        activation = {"daemon": daemon, "environment": dict(environment)}
    except Refused as error:
        activation = {"unrecognized": str(error)}
    return {"activation": activation,
            "autostart_fixed": desktop_arguments((home / AUTOSTART).read_bytes()) ==
                               ["/bin/sh", "-c", FIXED_TAIL],
            "active_capture": capture_active(home),
            "panel_sha256": sha((home / PANEL).read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "apply", "undo"), nargs="?", default="status")
    args = parser.parse_args()
    home = Path.home()
    try:
        if args.command == "apply":
            apply(home)
        elif args.command == "undo":
            undo(home)
        print(json.dumps(status(home), indent=2))
    except (Refused, OSError, ValueError, KeyError, configparser.Error) as error:
        print(f"xfce-panel-startup: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
