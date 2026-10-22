#!/usr/bin/env python3
"""Notify about Netdata swap activity or anonymous-memory demand, not file cache."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def read_pairs(path):
    return {key: int(value) for key, value in (line.split() for line in path.read_text().splitlines())}


def sample(cgroup, boot_file, now):
    stat = read_pairs(cgroup / "memory.stat")
    events = read_pairs(cgroup / "memory.events")
    high = (cgroup / "memory.high").read_text().strip()
    limit = None if high == "max" else int(high)
    values = {"anon": stat["anon"], "pswpin": stat["pswpin"], "high_events": events["high"],
              "swap": int((cgroup / "memory.swap.current").read_text()),
              "current": int((cgroup / "memory.current").read_text())}
    if any(value < 0 for value in values.values()) or (limit is not None and limit <= 0):
        raise ValueError("invalid cgroup counters or memory.high")
    identity = cgroup.stat()
    return {**values, "high": limit, "time": now, "boot": boot_file.read_text().strip(),
            "cgroup": [str(cgroup.resolve()), identity.st_dev, identity.st_ino]}


def evaluate(current, previous, page_size, swap_threshold, demand_threshold):
    comparable = (isinstance(previous, dict)
                  and previous.get("boot") == current["boot"]
                  and previous.get("cgroup") == current["cgroup"]
                  and isinstance(previous.get("time"), (int, float))
                  and math.isfinite(previous["time"])
                  and previous["time"] < current["time"]
                  and all(isinstance(previous.get(key), int) and 0 <= previous[key] <= current[key]
                          for key in ("pswpin", "high_events")))
    rate = ((current["pswpin"] - previous["pswpin"]) * page_size /
            (current["time"] - previous["time"])) if comparable else None
    demand = current["anon"] + current["swap"]
    ratio = demand / current["high"] if current["high"] is not None else None
    conditions = []
    if rate is not None and rate >= swap_threshold:
        conditions.append("swap-in")
    if ratio is not None and ratio >= demand_threshold:
        conditions.append("demand")
    return {"status": "measured" if comparable else "baseline-reset", "conditions": conditions,
            "swap_in_bytes_per_second": rate, "anonymous_plus_swap_bytes": demand,
            "demand_ratio": ratio, "limit_status": "unlimited" if ratio is None else "bounded"}


def save_state(path, data):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=".netdata-", delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), 0o600)
            json.dump(data, stream)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def check(args):
    if args.cgroup is None:
        result = subprocess.run(["systemctl", "show", "netdata.service", "--property=ControlGroup", "--value"],
                                check=True, capture_output=True, text=True, timeout=10)
        relative = result.stdout.strip()
        if not relative or not relative.startswith("/") or ".." in Path(relative).parts:
            raise ValueError("Netdata has no active cgroup; measurement unavailable")
        cgroup = Path("/sys/fs/cgroup") / relative.lstrip("/")
    else:
        cgroup = args.cgroup
    args.state.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    lock_fd = os.open(args.state.with_suffix(".lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock_fd, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "already-running"}, 0
        now = time.monotonic()
        current = sample(cgroup, args.boot_id, now)
        state = {}
        state_reset = False
        try:
            state = json.loads(args.state.read_text())
            if not isinstance(state, dict) or state.get("version") != 1:
                raise ValueError("invalid state version")
        except FileNotFoundError:
            pass
        except (ValueError, TypeError):
            state = {}
            state_reset = True
        result = evaluate(current, state.get("sample"), os.sysconf("SC_PAGE_SIZE"),
                          args.swap_in_threshold, args.demand_threshold)
        alerts = state.get("alerts", {})
        previous = state.get("sample")
        if (not isinstance(previous, dict) or previous.get("boot") != current["boot"]
                or not isinstance(previous.get("time"), (int, float))
                or not math.isfinite(previous["time"]) or previous["time"] > now
                or not isinstance(alerts, dict)
                or any(not isinstance(value, (int, float)) or not math.isfinite(value)
                       or value < 0 or value > now for value in alerts.values())):
            alerts = {}
        sent, suppressed, failures = [], [], []
        for condition in result["conditions"]:
            if condition in alerts and now - alerts[condition] < args.repeat_seconds:
                suppressed.append(condition)
                continue
            if condition == "swap-in":
                title = "Netdata: swap-in elevado"
                body = f"Entrada de swap: {result['swap_in_bytes_per_second'] / 1048576:.2f} MiB/s. Verifique a pressão de memória."
            else:
                title = "Netdata: demanda de memória elevada"
                body = (f"Memória anônima + swap: {result['demand_ratio']:.0%} do limite de pressão. "
                        "É um alerta de capacidade; não comprova thrashing ativo.")
            try:
                subprocess.run([args.notify_command, "-a", "netdata-memory-check", "-u", "normal", title, body],
                               check=True, capture_output=True, text=True, timeout=10)
            except (OSError, subprocess.SubprocessError):
                failures.append(condition)
            else:
                alerts[condition] = now
                sent.append(condition)
        save_state(args.state, {"version": 1, "sample": current, "alerts": alerts})
        return {**result, "state_reset": state_reset, "sent": sent,
                "suppressed": suppressed, "notification_failures": failures}, 2 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cgroup", type=Path, help="Inspect this cgroup instead of resolving netdata.service")
    parser.add_argument("--state", type=Path, default=Path.home() / ".local/state/netdata-memory-check/state.json")
    parser.add_argument("--boot-id", type=Path, default=Path("/proc/sys/kernel/random/boot_id"))
    parser.add_argument("--notify-command", default="notify-send")
    parser.add_argument("--swap-in-threshold", type=float, default=1048576,
                        help="Swap-in threshold in bytes per second")
    parser.add_argument("--demand-threshold", type=float, default=0.85,
                        help="Anonymous memory plus swap as a fraction of memory.high")
    parser.add_argument("--repeat-seconds", type=float, default=21600)
    args = parser.parse_args(argv)
    if (any(not math.isfinite(value) or value <= 0 for value in (
            args.swap_in_threshold, args.demand_threshold, args.repeat_seconds))
            or args.demand_threshold > 1):
        parser.error("thresholds and repeat interval must be positive; demand fraction must not exceed 1")
    try:
        result, status = check(args)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"Netdata measurement unavailable: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
