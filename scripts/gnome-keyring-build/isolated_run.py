#!/usr/bin/env python3
"""Run a built keyring test with host libraries and no session or home access."""

import argparse
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_root", type=Path)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--gcr-root", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.build_root.resolve(strict=True)
    owned = Path(__file__).resolve().parent
    if not root.is_relative_to(owned) or not args.command:
        parser.error("build_root must be an exported tree beside this runner; command is required")
    gcr_root = args.gcr_root.resolve(strict=True) if args.gcr_root else None
    if gcr_root and not gcr_root.is_relative_to(owned.parent / "gcr-build"):
        parser.error("gcr-root must be an exported tree under the sibling gcr-build directory")
    command = args.command
    if command[0] == "--":
        command = command[1:]
    with tempfile.TemporaryDirectory(prefix="keyring-isolated-") as scratch:
        work = Path(scratch)
        (work / "home").mkdir(mode=0o700)
        (work / "passwd").write_text("keyringtest:x:1000:1000:Test:/home/test:/bin/sh\n")
        (work / "group").write_text("keyringtest:x:1000:\n")
        (work / "nsswitch.conf").write_text("passwd: files\ngroup: files\nhosts: files\n")
        (work / "bus.conf").write_text('''<busconfig>
<type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth>
<policy context="default"><allow own="*"/><allow send_destination="*"/>
<allow receive_sender="*"/></policy>
</busconfig>\n''')
        (work / "probe.json").write_text(json.dumps({"real_home": str(Path.home()), "namespaces": {
            name: os.readlink(f"/proc/self/ns/{name}") for name in ("pid", "net", "mnt")
        }}))
        (work / "probe.py").write_text('''import json, os, pathlib, sys
before = json.loads(pathlib.Path("/sandbox/probe.json").read_text())
for name, identity in before["namespaces"].items():
    assert os.readlink(f"/proc/self/ns/{name}") != identity, name
assert os.getuid() == 1000 and os.getgid() == 1000
for path in (before["real_home"], "/run/user/1000/bus", "/root/coredumps"):
    assert not pathlib.Path(path).exists(), path
for name in ("SSH_AUTH_SOCK", "DISPLAY", "WAYLAND_DISPLAY", "DBUS_SYSTEM_BUS_ADDRESS"):
    assert name not in os.environ, name
address = os.environ["DBUS_SESSION_BUS_ADDRESS"]
assert address.startswith("unix:") and "/run/user" not in address
print("isolation verified: private PID/network/mount namespaces, synthetic home, private bus", flush=True)
os.execvpe(sys.argv[1], sys.argv[1:], os.environ)
''')
        argv = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session",
                "--uid", "1000", "--gid", "1000",
                "--clearenv", "--setenv", "PATH", "/usr/bin:/bin",
                "--setenv", "HOME", "/home/test", "--setenv", "USER", "keyringtest",
                "--setenv", "LOGNAME", "keyringtest", "--setenv", "LANG", "C.UTF-8",
                "--setenv", "XDG_RUNTIME_DIR", "/run/test",
                "--setenv", "XDG_DATA_HOME", "/home/test/.local/share",
                "--setenv", "XDG_CONFIG_HOME", "/home/test/.config",
                "--ro-bind", "/usr", "/usr", "--ro-bind", "/lib", "/lib",
                "--ro-bind", "/lib64", "/lib64", "--ro-bind", "/bin", "/bin",
                "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                "--tmpfs", "/run", "--dir", "/run/test", "--dir", "/etc",
                "--ro-bind", str(work / "passwd"), "/etc/passwd",
                "--ro-bind", str(work / "group"), "/etc/group",
                "--ro-bind", str(work / "nsswitch.conf"), "/etc/nsswitch.conf",
                "--ro-bind", "/etc/ld.so.cache", "/etc/ld.so.cache",
                "--bind", str(work / "home"), "/home/test",
                "--ro-bind", str(work), "/sandbox",
                "--ro-bind", str(root), "/build/gnome-keyring",
                "--chdir", "/build/gnome-keyring"]
        if gcr_root:
            argv += ["--ro-bind", str(gcr_root), "/build/gcr",
                     "--setenv", "LD_LIBRARY_PATH",
                     "/build/gcr/obj-x86_64-linux-gnu/gcr:/build/gcr/obj-x86_64-linux-gnu/gck"]
        argv += ["--", "dbus-run-session", "--config-file=/sandbox/bus.conf", "--",
                 "python3", "/sandbox/probe.py", *command]
        def disable_core_dumps():
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

        process = subprocess.Popen(argv, start_new_session=True, preexec_fn=disable_core_dumps)
        try:
            return process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise SystemExit("isolated test exceeded its explicit time bound")


if __name__ == "__main__":
    raise SystemExit(main())
