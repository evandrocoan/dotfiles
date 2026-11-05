#!/usr/bin/python3
"""Filter kernel core-dump streams by exact %e name; keep other dumps private."""

import argparse
import errno
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import syslog
from typing import NamedTuple


ROOT = Path("/")
OWNER = (0, 0)
RULE_DIRECTORY = ("etc", "core-dump-filter")
CORE_DIRECTORY = ("root", "coredumps")
RULE_FILE = "ignore.conf"
MAX_RULE_BYTES = 65536
CHUNK_SIZE = 65536


class Event(NamedTuple):
    signal: int
    uid: int
    gid: int
    pid: int
    timestamp: int
    limit: int
    comm: str


class CaptureError(RuntimeError):
    """Capture failed; the message identifies any retained data."""


def log(priority, message):
    # The kernel helper's stderr may be closed; logging must never lose a core.
    try:
        syslog.openlog("core-dump-filter", syslog.LOG_PID, syslog.LOG_DAEMON)
        syslog.syslog(priority, message)
    except (OSError, ValueError):
        pass
    try:
        print(f"core-dump-filter: {message}", file=sys.stderr)
    except (OSError, ValueError):
        pass


def parse_event(arguments):
    if len(arguments) != 7:
        raise ValueError("expected SIGNAL UID GID GLOBAL_PID TIME CORE_LIMIT COMM")
    bounds = ((1, 128), (0, 2**32 - 1), (0, 2**32 - 1),
              (1, 2**31 - 1), (0, 2**63 - 1), (0, 2**64 - 1))
    numbers = []
    for value, (lower, upper) in zip(arguments[:6], bounds):
        if not re.fullmatch(r"[0-9]{1,20}", value) or not lower <= int(value) <= upper:
            raise ValueError("invalid numeric kernel metadata")
        numbers.append(int(value))
    comm = arguments[6]
    if len(os.fsencode(comm)) > 15 or "\0" in comm:
        raise ValueError("COMM must contain at most 15 bytes and no NUL")
    return Event(*numbers, comm)


def safe_name(comm):
    permitted = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    return "".join(chr(byte) if byte in permitted else f"%{byte:02X}"
                   for byte in os.fsencode(comm)) or "unnamed"


def _validate_directory(descriptor, owner, *, output=False):
    metadata = os.fstat(descriptor)
    mode = stat.S_IMODE(metadata.st_mode)
    if not stat.S_ISDIR(metadata.st_mode) or (metadata.st_uid, metadata.st_gid) != owner:
        raise ValueError("directory must belong to the trusted uid and gid")
    if mode & 0o022 and not (output and mode & stat.S_ISVTX):
        raise ValueError("directory must not be writable by group or others")
    if output and mode & 0o044:
        raise ValueError("core directory must not be readable by group or others")


def open_directory(parts, *, root=ROOT, owner=OWNER, output=False):
    """Walk fixed paths without following symlinks, anchored at a trusted root.

    root/owner are internal fixture boundaries, never kernel CLI or environment options.
    """
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor = os.open(root, flags)
    try:
        _validate_directory(descriptor, owner)
        for index, part in enumerate(parts):
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
            _validate_directory(descriptor, owner,
                                output=output and index == len(parts) - 1)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def load_rules(*, root=ROOT, owner=OWNER):
    directory = open_directory(RULE_DIRECTORY, root=root, owner=owner)
    try:
        descriptor = os.open(RULE_FILE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                             | os.O_CLOEXEC, dir_fd=directory)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (not stat.S_ISREG(metadata.st_mode)
                    or (metadata.st_uid, metadata.st_gid) != owner
                    or stat.S_IMODE(metadata.st_mode) & 0o022):
                raise ValueError("ignore.conf must be a trusted regular file, not writable by others")
            raw = stream.read(MAX_RULE_BYTES + 1)
    finally:
        os.close(directory)
    if len(raw) > MAX_RULE_BYTES:
        raise ValueError("ignore.conf exceeds 64 KiB")
    ignored = set()
    for line in raw.decode("utf-8").splitlines():
        name = line.strip()
        if not name or name.startswith("#"):
            continue
        if len(os.fsencode(name)) > 15 or any(ord(char) < 32 or ord(char) == 127 for char in name):
            raise ValueError("ignore.conf entries must be comm names of at most 15 bytes")
        ignored.add(name)
    return ignored


def copy_sparse(stream, descriptor, limit):
    size = 0
    while size < limit:
        data = stream.read(min(CHUNK_SIZE, limit - size))
        if not data:
            os.ftruncate(descriptor, size)
            return size, False
        if not isinstance(data, bytes) or len(data) > min(CHUNK_SIZE, limit - size):
            raise ValueError("invalid core input stream")
        if data.count(0) == len(data):
            os.lseek(descriptor, len(data), os.SEEK_CUR)
        else:
            remaining = memoryview(data)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise OSError(errno.EIO, "core write made no progress")
                remaining = remaining[written:]
        size += len(data)
    # Exactly limit bytes may be a complete core. Probe before marking it partial.
    truncated = bool(stream.read(1))
    os.ftruncate(descriptor, size)
    return size, truncated


def publish(directory, temporary, basename):
    stem = basename[:-8] if basename.endswith(".partial") else basename
    suffix = ".partial" if basename.endswith(".partial") else ""
    for attempt in range(16):
        name = basename if attempt == 0 else f"{stem}-{secrets.token_hex(8)}{suffix}"
        try:
            os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory,
                    follow_symlinks=False)
            return name
        except FileExistsError:
            continue
    raise FileExistsError("could not allocate a unique core filename")


def save_core(event, stream, *, root=ROOT, owner=OWNER):
    directory = open_directory(CORE_DIRECTORY, root=root, owner=owner, output=True)
    temporary = f".core-dump-filter-{secrets.token_hex(16)}"
    basename = (f"core-{safe_name(event.comm)}-{event.signal}-{event.uid}-{event.gid}"
                f"-{event.pid}-{event.timestamp}")
    descriptor = None
    published = None
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                             | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
        os.fchmod(descriptor, 0o600)
        metadata = os.fstat(descriptor)
        if (metadata.st_uid, metadata.st_gid) != owner:
            raise ValueError("new core file has an unexpected owner or group")
        size, truncated = copy_sparse(stream, descriptor, event.limit)
        os.fsync(descriptor)
        published = publish(directory, temporary, basename + (".partial" if truncated else ""))
        os.unlink(temporary, dir_fd=directory)
        temporary = None
        os.fsync(directory)
        return {"status": "partial" if truncated else "saved", "name": published, "size": size}
    except (OSError, ValueError) as error:
        retained = published
        if descriptor is not None and temporary is not None:
            # Preserve a successfully written prefix, including a trailing sparse hole.
            try:
                os.ftruncate(descriptor, os.lseek(descriptor, 0, os.SEEK_CUR))
                os.fsync(descriptor)
            except OSError:
                pass
            if published is None:
                try:
                    retained = publish(directory, temporary, basename + ".partial")
                except OSError:
                    retained = temporary
            if retained != temporary:
                try:
                    os.unlink(temporary, dir_fd=directory)
                except OSError:
                    pass
        suffix = f"; retained {retained}" if retained else "; no output file was created"
        raise CaptureError(f"{error!r}{suffix}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(directory)


def collect(event, stream, *, root=ROOT, owner=OWNER):
    if event.limit == 0:
        return {"status": "disabled", "name": None, "size": 0}
    try:
        ignored = load_rules(root=root, owner=owner)
    except (OSError, ValueError) as error:
        # A broken exclusion file must not silently discard otherwise useful cores.
        log(syslog.LOG_ERR, f"ignore configuration unavailable ({error!r}); capturing without exclusions")
        ignored = set()
    if event.comm in ignored:
        return {"status": "ignored", "name": None, "size": 0}
    return save_core(event, stream, root=root, owner=owner)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate installed paths and ignore list")
    parser.add_argument("metadata", nargs="*", metavar="KERNEL_ARGUMENT")
    args = parser.parse_args(argv)
    try:
        if os.geteuid() != 0:
            raise ValueError("run the installed collector as root")
        if args.check:
            if args.metadata:
                raise ValueError("--check does not accept kernel arguments")
            ignored = load_rules(root=ROOT, owner=OWNER)
            directory = open_directory(CORE_DIRECTORY, root=ROOT, owner=OWNER, output=True)
            os.close(directory)
            print("Configuration OK; ignored comm names: " + ", ".join(sorted(ignored)))
            return 0
        event = parse_event(args.metadata)
        # Preserve the kernel helper's inherited RLIMIT_CORE=(1,1): its recursion guard.
        result = collect(event, sys.stdin.buffer, root=ROOT, owner=OWNER)
        priority = syslog.LOG_WARNING if result["status"] == "partial" else syslog.LOG_INFO
        log(priority, f"{result['status']}: {result['name'] or safe_name(event.comm)}"
                      f" ({result['size']} bytes)")
        return 0
    except (OSError, ValueError, CaptureError) as error:
        log(syslog.LOG_ERR, f"capture failed: {error!r}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
