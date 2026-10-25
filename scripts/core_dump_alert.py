#!/usr/bin/env python3
"""Publish native-core metadata as root; notify from the desktop user session."""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time


CORE_DIRECTORY = Path("/root/coredumps")
SNAPSHOT = Path("/run/core-dump-alert/status.json")
BOOT_ID = Path("/proc/sys/kernel/random/boot_id")
REMINDER_SECONDS = 3600
MAX_SNAPSHOT_AGE = 180


def elapsed_time():
    # Unlike CLOCK_MONOTONIC, this includes time spent suspended.
    return time.clock_gettime(time.CLOCK_BOOTTIME)


def atomic_json(path, document, mode):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent,
                                         prefix=".core-dump-", delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), mode)
            json.dump(document, stream, allow_nan=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_json(path):
    with path.open("rb") as stream:
        raw = stream.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError(f"JSON document too large: {path}")
    document = json.loads(raw)
    if (not isinstance(document, dict) or type(document.get("version")) is not int
            or document["version"] != 1):
        raise ValueError(f"invalid document version: {path}")
    return document


def validate_ids(values):
    if (not isinstance(values, list)
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                   for value in values)
            or values != sorted(set(values))):
        raise ValueError("invalid core identities")
    return values


def valid_time(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0)


def publish(args):
    identities = []
    # scandir must fail visibly if the protected directory is unavailable.
    with os.scandir(args.directory) as entries:
        for entry in entries:
            if not entry.name.startswith("core-"):
                continue
            try:
                metadata = entry.stat(follow_symlinks=False)
            except FileNotFoundError:
                continue  # A user moved the entry during enumeration.
            if not stat.S_ISREG(metadata.st_mode):
                continue
            # Do not hash size/mtime: a growing core is still the same pending file.
            identity = os.fsencode(entry.name) + f"\0{metadata.st_dev}:{metadata.st_ino}".encode()
            identities.append(hashlib.sha256(identity).hexdigest())
    document = {"version": 1, "boot_id": args.boot_id.read_text().strip(),
                "sample_time": elapsed_time(), "files": sorted(identities)}
    args.snapshot.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
    atomic_json(args.snapshot, document, 0o644)
    return {"status": "published", "count": len(identities)}


def load_state(path, boot):
    try:
        state = read_json(path)
    except FileNotFoundError:
        state = {"version": 1, "boot_id": boot, "seen": [], "last_success": None}
    if not isinstance(state.get("boot_id"), str) or not state["boot_id"]:
        raise ValueError("invalid state boot ID")
    validate_ids(state.get("seen"))
    if "last_success" not in state:
        raise ValueError("missing notification timestamp")
    last = state["last_success"]
    if last is not None and not valid_time(last):
        raise ValueError("invalid notification timestamp")
    if state["boot_id"] != boot:
        return {"version": 1, "boot_id": boot, "seen": [], "last_success": None}
    return state


def notify(args):
    args.state.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if stat.S_IMODE(args.state.parent.stat().st_mode) & 0o077:
        raise ValueError("notification state directory must be private (mode 0700)")
    descriptor = os.open(args.state.with_suffix(".lock"),
                         os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "already-running"}
        snapshot = read_json(args.snapshot)
        files = validate_ids(snapshot.get("files"))
        boot = args.boot_id.read_text().strip()
        sampled = snapshot.get("sample_time")
        now = elapsed_time()
        if (not boot or snapshot.get("boot_id") != boot or not valid_time(sampled)
                or sampled > now or now - sampled > MAX_SNAPSHOT_AGE):
            raise ValueError("publisher snapshot is stale or has an invalid boot ID/timestamp")
        state = load_state(args.state, boot)
        last = state["last_success"]
        if last is not None and last > now:
            raise ValueError("notification timestamp is in the future")
        new_files = set(files) - set(state["seen"])
        due = bool(files) and (new_files or last is None or now - last >= REMINDER_SECONDS)
        updated = {"version": 1, "boot_id": boot, "seen": files,
                   "last_success": last if files else None}
        if due:
            title = "Core dump pendente" if len(files) == 1 else "Core dumps pendentes"
            body = (f"{len(files)} arquivo(s) em {CORE_DIRECTORY}.\n"
                    "Os lembretes continuam de hora em hora enquanto houver arquivos nessa pasta.")
            result = subprocess.run(
                [str(args.notify_command), "--app-name=Core dumps", "--urgency=normal",
                 "--icon=dialog-warning", "--expire-time=30000", title, body],
                capture_output=True, text=True, timeout=10)
            if result.returncode:
                raise RuntimeError("notification failed: " + (result.stderr.strip()
                                   or f"exit status {result.returncode}"))
            updated["last_success"] = now
        if updated != state or not args.state.exists():
            atomic_json(args.state, updated, 0o600)
        return {"status": "notified" if due else ("pending" if files else "empty"),
                "count": len(files)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    publisher = commands.add_parser("publish", help="publish protected-directory metadata")
    publisher.add_argument("--directory", type=Path, default=CORE_DIRECTORY)
    publisher.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    publisher.add_argument("--boot-id", type=Path, default=BOOT_ID)
    notifier = commands.add_parser("notify", help="notify the logged-in desktop user")
    notifier.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    notifier.add_argument("--state", type=Path, default=state_home / "core-dump-alert/state.json")
    notifier.add_argument("--boot-id", type=Path, default=BOOT_ID)
    notifier.add_argument("--notify-command", type=Path, default=Path("/usr/bin/notify-send"))
    args = parser.parse_args(argv)
    try:
        result = publish(args) if args.command == "publish" else notify(args)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"core-dump-alert: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
