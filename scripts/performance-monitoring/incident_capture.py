#!/usr/bin/python3
"""Bounded local incident recorder. Runtime uses only the Python standard library."""

import argparse
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import selectors
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid


MIB = 1024 * 1024
CAPTURE_BYTES = 64 * MIB
STREAM_BYTES = 16 * MIB
SCHEMA = "performance-incident-v1"
CONFIG_PATH = Path("/etc/performance-monitoring/incident-capture.json")
LOG_DIR = Path("/var/log/performance-incidents")
STATE_DIR = Path("/var/lib/performance-incident")
LOCK_PATH = Path("/run/performance-incident/capture.lock")
LIMITS = {
    "io_some_avg10_percent": (.01, 100),
    "memory_some_avg10_percent": (.01, 100),
    "sustained_seconds": (1, 300),
    "cooldown_seconds": (60, 86400),
    "capture_seconds": (5, 60),
    "startup_timeout_seconds": (5, 60),
    "retention_days": (1, 90),
    "storage_budget_mib": (128, 4096),
    "minimum_free_mib": (1024, 1048576),
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def log(message):
    print(f"{utc()} {message}", flush=True)


def notify_ready():
    address = os.environ.get("NOTIFY_SOCKET")
    if address:
        if address.startswith("@"):
            address = "\0" + address[1:]
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as channel:
            channel.sendto(b"READY=1", address)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode()


def atomic_json(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(encoded(value))
    temporary.replace(path)


def load_config(path):
    config = json.loads(path.read_text())
    if set(config) != set(LIMITS):
        raise ValueError("configuration must contain exactly the documented configuration keys")
    for key, (low, high) in LIMITS.items():
        value = config[key]
        if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"configuration out of range: {key} ({low}..{high})")
    return config


def read_text(path, limit=128 * 1024):
    with Path(path).open() as stream:
        return stream.read(limit)


def pressure(root=Path("/proc/pressure")):
    result = {}
    for resource in ("cpu", "io", "memory"):
        result[resource] = {}
        for line in read_text(root / resource).splitlines():
            kind, *values = line.split()
            result[resource][kind] = {k: float(v) for k, v in (s.split("=") for s in values)}
    return result


def host_sample():
    # Keep raw kernel counters for interval calculations, with collection timestamps.
    sample = {"utc": utc(), "monotonic": time.monotonic(), "pressure": pressure()}
    for name in ("meminfo", "vmstat", "diskstats", "stat", "net/dev"):
        sample[name] = read_text(Path("/proc") / name, 32768)
    return sample


class Trigger:
    def __init__(self, config, last_attempt=0):
        self.config = config
        self.last_attempt = last_attempt
        self.since = {}

    def observe(self, sample, monotonic, wall):
        reasons = []
        for resource in ("io", "memory"):
            threshold = self.config[f"{resource}_some_avg10_percent"]
            if sample[resource]["some"]["avg10"] >= threshold:
                self.since.setdefault(resource, monotonic)
                if monotonic - self.since[resource] >= self.config["sustained_seconds"]:
                    reasons.append(resource)
            else:
                self.since.pop(resource, None)
        # Clamp a clock rollback to one cooldown instead of suppressing captures indefinitely.
        self.last_attempt = min(self.last_attempt, wall)
        if reasons and wall - self.last_attempt >= self.config["cooldown_seconds"]:
            return "pressure:" + "+".join(reasons)
        return None

    def attempted(self, wall):
        self.last_attempt = wall
        self.since.clear()


def parse_stat(text):
    close = text.rindex(")")
    fields = text[close + 2:].split()
    return {
        "comm": text[text.index("(") + 1:close], "state": fields[0],
        "start_ticks": int(fields[19]), "delay_ticks": int(fields[39]),
        "cpu_ticks": int(fields[11]) + int(fields[12]),
        "minor_faults": int(fields[7]), "major_faults": int(fields[9]),
        "rss_pages": int(fields[21]),
    }


def snapshot(proc=Path("/proc"), seconds=5):
    result = {"utc": utc(), "uptime": float(read_text(proc / "uptime").split()[0]),
              "hz": os.sysconf("SC_CLK_TCK"), "processes": [], "incomplete": False,
              "races_or_denied": 0}
    deadline = time.monotonic() + seconds
    size = 0
    for directory in proc.iterdir():
        if not directory.name.isdigit():
            continue
        if time.monotonic() >= deadline or size >= 7 * MIB:
            result["incomplete"] = True
            break
        try:
            process = parse_stat(read_text(directory / "stat"))
            process["pid"] = int(directory.name)
            process["cgroup"] = read_text(directory / "cgroup", 4096).splitlines()
            process["io"] = {k: int(v) for k, v in
                             (line.split(":") for line in read_text(directory / "io").splitlines())}
            process["memory_kib"] = {}
            for line in read_text(directory / "status").splitlines():
                key, _, value = line.partition(":")
                if key in ("VmRSS", "VmSwap", "RssAnon", "RssFile", "RssShmem"):
                    process["memory_kib"][key] = int(value.split()[0])
            process["threads"] = []
            for thread in (directory / "task").iterdir():
                if time.monotonic() >= deadline or len(process["threads"]) >= 8192:
                    result["incomplete"] = True
                    break
                try:
                    stat = parse_stat(read_text(thread / "stat"))
                    process["threads"].append({"tid": int(thread.name), **stat})
                except (OSError, ValueError, IndexError):
                    result["races_or_denied"] += 1
            # Do not join a recycled PID's cgroups/I/O with its previous identity.
            if parse_stat(read_text(directory / "stat"))["start_ticks"] != process["start_ticks"]:
                result["races_or_denied"] += 1
                continue
            size += len(encoded(process))
            result["processes"].append(process)
        except (OSError, ValueError, IndexError):
            result["races_or_denied"] += 1
    # Counters sampled during the scan are bounded against its END, not its start.
    result["uptime_end"] = float(read_text(proc / "uptime").split()[0])
    result["finished_utc"] = utc()
    return result


def delay_invalid(thread, sample):
    lifetime = sample["uptime_end"] * sample["hz"] - thread["start_ticks"]
    return thread["delay_ticks"] < 0 or thread["delay_ticks"] > lifetime + sample["hz"]


def summarize(before, after, excluded=()):
    previous = {(p["pid"], p["start_ticks"]): p for p in before["processes"]}
    current = {(p["pid"], p["start_ticks"]): p for p in after["processes"]}
    rows, anomalies = [], []
    invalid_exited = {}
    for identity, old in previous.items():
        present_threads = {(t["tid"], t["start_ticks"]) for t in current.get(identity, {}).get("threads", [])}
        for thread in old["threads"]:
            if (thread["tid"], thread["start_ticks"]) not in present_threads and delay_invalid(thread, before):
                anomalies.append({"pid": old["pid"], "tid": thread["tid"], "sample": "before",
                                  "reason": "delay_exceeds_thread_lifetime_or_negative",
                                  "raw_delay_ticks": thread["delay_ticks"]})
                invalid_exited[identity] = invalid_exited.get(identity, 0) + 1
    for process in after["processes"]:
        old = previous.get((process["pid"], process["start_ticks"]))
        threads = {(t["tid"], t["start_ticks"]): t for t in old["threads"]} if old else {}
        delay, valid, unmatched = 0, 0, 0
        invalid = invalid_exited.get((process["pid"], process["start_ticks"]), 0)
        for thread in process["threads"]:
            prior = threads.get((thread["tid"], thread["start_ticks"]))
            reason = None
            if delay_invalid(thread, after) or (prior and delay_invalid(prior, before)):
                reason = "delay_exceeds_thread_lifetime_or_negative"
            elif prior and thread["delay_ticks"] < prior["delay_ticks"]:
                reason = "delay_counter_decreased"
            if reason:
                invalid += 1
                anomalies.append({"pid": process["pid"], "tid": thread["tid"], "reason": reason,
                                  "raw_delay_ticks": thread["delay_ticks"]})
            elif prior:
                valid += 1
                delay += thread["delay_ticks"] - prior["delay_ticks"]
            else:
                unmatched += 1
        if old is None or process["pid"] in excluded:
            continue
        io = {}
        for key in ("read_bytes", "write_bytes", "cancelled_write_bytes"):
            delta = process["io"].get(key, 0) - old["io"].get(key, 0)
            io[key] = delta if delta >= 0 else None
        exited = len(set(threads) - {(t["tid"], t["start_ticks"]) for t in process["threads"]})
        rows.append({"pid": process["pid"], "comm": process["comm"], "cgroup": process["cgroup"],
                     "io_delta_bytes": io, "memory_kib": process["memory_kib"],
                     "cpu_delta_ticks": max(0, process["cpu_ticks"] - old["cpu_ticks"]),
                     "delay_seconds": delay / after["hz"] if valid and not invalid else None,
                     "valid_threads": valid, "invalid_threads": invalid,
                     "unmatched_threads": unmatched, "exited_threads": exited})
    return {"processes": rows, "invalid_delay_counters": anomalies,
            "snapshot_incomplete": before["incomplete"] or after["incomplete"],
            "exited_or_reused_processes": len(set(previous) -
                {(p["pid"], p["start_ticks"]) for p in after["processes"]})}


@contextmanager
def capture_lock(path):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def tree_bytes(directory):
    return sum(p.stat().st_size for p in directory.rglob("*") if p.is_file() and not p.is_symlink())


def open_incidents(directory):
    opened = set()
    prefix = str(directory.resolve()) + "/"
    for process in Path("/proc").iterdir():
        if not process.name.isdecimal():
            continue
        try:
            for descriptor in (process / "fd").iterdir():
                try:
                    target = os.readlink(descriptor)
                    if target.startswith(prefix):
                        opened.add(target[len(prefix):].split("/")[0])
                except OSError:
                    pass
        except OSError:
            pass
    return opened


def prune(directory, config, now=None, reserve=0):
    now = time.time() if now is None else now
    records = []
    for path in directory.glob("incident-*"):
        if path.is_symlink() or not path.is_dir():
            continue
        try:
            manifest = json.loads((path / "manifest.json").read_text())
            if manifest.get("schema") == SCHEMA and manifest.get("status") in (
                    "complete", "partial", "failed", "interrupted"):
                records.append((manifest["created_epoch"], path, tree_bytes(path)))
        except (OSError, ValueError, KeyError):
            continue
    total = tree_bytes(directory)
    removed = []
    opened = None
    for created, path, size in sorted(records):
        if (path / "KEEP").exists():
            continue
        old = now - created > config["retention_days"] * 86400
        over = total + reserve > config["storage_budget_mib"] * MIB
        low = shutil.disk_usage(directory).free < config["minimum_free_mib"] * MIB + reserve
        if old or over or low:
            if opened is None:
                opened = open_incidents(directory)
            if path.name in opened:
                continue
            tombstone = path.with_name(".deleting-" + path.name)
            path.rename(tombstone)
            shutil.rmtree(tombstone)
            total -= size
            removed.append(path.name)
    if removed:
        log(f"retention removed={len(removed)} bytes_remaining={total}")
    return total


def recover(directory):
    # Call only with the capture lock: a crash cannot turn a partial directory into success.
    for path in directory.glob(".deleting-incident-*"):
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
    for path in directory.glob("incident-*"):
        if path.is_symlink() or not path.is_dir():
            continue
        try:
            manifest = json.loads((path / "manifest.json").read_text())
            if manifest.get("schema") == SCHEMA and manifest.get("status") == "recording":
                manifest.update(status="interrupted", finished_utc=utc(),
                                error="recorder stopped before finalization")
                atomic_json(path / "manifest.json", manifest)
        except (OSError, ValueError):
            continue


class Budget:
    def __init__(self, directory, maximum=CAPTURE_BYTES - MIB):
        self.directory, self.maximum, self.used = directory, maximum, 0

    def write(self, name, data, append=False):
        if self.used + len(data) > self.maximum:
            raise RuntimeError("incident output budget exceeded")
        with (self.directory / name).open("ab" if append else "wb") as stream:
            stream.write(data)
        self.used += len(data)


def collectors():
    return {
        "biosnoop": ([sys.executable, str(Path(__file__).with_name("bcc_ready.py")), "biosnoop"],
                     b"PERFORMANCE_COLLECTOR_READY"),
        "biolatency": ([sys.executable, str(Path(__file__).with_name("bcc_ready.py")), "biolatency"],
                       b"PERFORMANCE_COLLECTOR_READY"),
    }


def source_fingerprints():
    paths = (Path(__file__), Path(__file__).with_name("bcc_ready.py"),
             Path("/usr/sbin/biosnoop-bpfcc"), Path("/usr/sbin/biolatency-bpfcc"))
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths if path.is_file()}


def run_collectors(budget, config, stop, commands=None, sampler=host_sample):
    commands = collectors() if commands is None else commands
    result, children, files = {}, {}, {}
    selector = selectors.DefaultSelector()
    start, ready_start, next_sample = time.monotonic(), None, time.monotonic()
    deadline = start + config["startup_timeout_seconds"]
    reason = "startup_timeout"

    def consume(key):
        name, kind = key.data
        block = os.read(key.fd, 65536)
        if not block:
            selector.unregister(key.fileobj)
            return
        entry = files[name, kind]
        entry["bytes"] += len(block)
        maximum = STREAM_BYTES if kind == "stdout" else MIB
        if entry["bytes"] > maximum:
            raise RuntimeError(f"collector output limit: {name}/{kind}")
        budget.write(f"{name}.{kind}.log", block, append=True)
        combined = entry["tail"] + block
        if commands[name][1] in combined and not result[name]["ready"]:
            result[name].update(ready=True, ready_utc=utc())
        if b"PERFORMANCE_COLLECTOR_LOST" in combined:
            result[name]["lost_events"] = True
        entry["tail"] = combined[-256:]

    try:
        for name, (command, marker) in commands.items():
            child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     env={**os.environ, "PYTHONUNBUFFERED": "1", "LC_ALL": "C", "TZ": "UTC"},
                                     start_new_session=True)
            children[name] = child
            result[name] = {"pid": child.pid, "ready": False, "lost_events": False,
                            "started_utc": utc(), "command": command}
            for kind, stream in (("stdout", child.stdout), ("stderr", child.stderr)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, (name, kind))
                files[name, kind] = {"bytes": 0, "tail": b""}
        while True:
            now = time.monotonic()
            if stop():
                reason = "cancelled"
                break
            if any(child.poll() is not None for child in children.values()):
                reason = "collector_exited"
                break
            if ready_start is None and all(r["ready"] for r in result.values()):
                ready_start = now
                deadline = now + config["capture_seconds"]
                log(f"collectors ready; recording for {config['capture_seconds']} seconds")
            if now >= deadline:
                reason = "window_complete" if ready_start is not None else "startup_timeout"
                break
            if now >= next_sample:
                budget.write("host.jsonl", encoded(sampler()), append=True)
                next_sample = now + 1
            for key, _ in selector.select(min(.2, max(0, deadline - time.monotonic()))):
                consume(key)
    except Exception as error:
        reason = f"error: {type(error).__name__}: {error}"
    finally:
        capture_end = time.monotonic()
        # SIGTERM avoids SIGINT swallowed inside BCC's ctypes callback under heavy I/O.
        for child in children.values():
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        end = time.monotonic() + 3
        for name, child in children.items():
            try:
                child.wait(timeout=max(.01, end - time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=2)
            result[name]["returncode"] = child.returncode
            result[name]["finished_utc"] = utc()
            if reason == "window_complete" and child.returncode not in (0, -signal.SIGTERM):
                reason = "collector_shutdown_failed"
        try:
            # Drain finite pipe contents after termination, retaining final error/loss diagnostics.
            while selector.get_map():
                events = selector.select(0)
                if not events:
                    break
                for key, _ in events:
                    consume(key)
        except Exception as error:
            reason = f"error: {type(error).__name__}: {error}"
        for child in children.values():
            child.stdout.close()
            child.stderr.close()
        selector.close()
    return {"reason": reason, "collectors": result,
            "ready_window_seconds": 0 if ready_start is None else capture_end - ready_start,
            "output_bytes": {f"{name}.{kind}": entry["bytes"]
                             for (name, kind), entry in files.items()}}


def report_text(manifest, summary):
    lines = ["Performance incident", f"Started (UTC): {manifest['created_utc']}",
             f"Trigger: {manifest['trigger']}", f"Status: {manifest['status']}",
             "", "I/O byte deltas for surviving process identities (top 20):"]
    for row in sorted(summary["processes"],
                      key=lambda r: sum(r["io_delta_bytes"][k] or 0 for k in ("read_bytes", "write_bytes")),
                      reverse=True)[:20]:
        lines.append(json.dumps({k: row[k] for k in ("pid", "comm", "io_delta_bytes", "cgroup")}))
    lines += ["", "Delay deltas for matched threads; processes with invalid counters are excluded:"]
    for row in sorted((r for r in summary["processes"] if r["delay_seconds"] is not None),
                      key=lambda r: r["delay_seconds"], reverse=True)[:20]:
        lines.append(json.dumps({k: row[k] for k in ("pid", "comm", "delay_seconds", "valid_threads",
                                                   "unmatched_threads", "exited_threads")}))
    lines += ["", f"Invalid thread counters: {len(summary['invalid_delay_counters'])}",
              "Raw snapshots and summary.json preserve counter evidence and quality flags.",
              "biosnoop: TIME(s) is relative to its first event; LAT(ms) is device request latency;",
              "QUE(ms) is queue time. biolatency includes queueing (-Q), per disk, in milliseconds.",
              "Queue time -1 means unavailable. Collector stderr records map failures and unknown issuers.",
              "Block issuers can be kernel workers, especially with writeback/encrypted volumes.",
              "A waiter or high I/O issuer is a candidate, not proof of the cause of a slowdown.",
              "Snapshots miss exited/short-lived tasks; use atop history for that interval.",
              "Zero delay does not prove no waiting, especially for tasks predating runtime enable.",
              "Per-thread delays may be charged on wait completion; interval totals can exceed",
              "the observation window. Validation checks lifetime and identity, not interval size."]
    return ("\n".join(lines) + "\n").encode()


def capture(config, reason, history=(), stop=lambda: False, directory=LOG_DIR,
            lock_path=LOCK_PATH, commands=None, snapshotter=snapshot, sampler=host_sample):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with capture_lock(lock_path) as acquired:
        if not acquired:
            log("capture skipped: another capture owns the lock")
            return None
        recover(directory)
        total = prune(directory, config, reserve=CAPTURE_BYTES)
        if (total + CAPTURE_BYTES > config["storage_budget_mib"] * MIB or
                shutil.disk_usage(directory).free < config["minimum_free_mib"] * MIB + CAPTURE_BYTES):
            log("capture skipped: insufficient storage budget or free space")
            return None
        path = directory / ("incident-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") +
                            "-" + uuid.uuid4().hex[:8])
        path.mkdir(mode=0o700)
        manifest = {"schema": SCHEMA, "status": "recording", "trigger": reason,
                    "created_utc": utc(), "created_epoch": time.time(), "config": config,
                    "kernel": os.uname().release, "boot_id": read_text("/proc/sys/kernel/random/boot_id").strip(),
                    "delayacct_runtime": read_text("/proc/sys/kernel/task_delayacct").strip(),
                    "delayacct_boot": "delayacct" in read_text("/proc/cmdline").split(),
                    "recorder_pid": os.getpid(), "source_sha256": source_fingerprints()}
        atomic_json(path / "manifest.json", manifest)
        log(f"capture started trigger={reason} path={path}")
        budget = Budget(path)
        try:
            for sample in history:
                budget.write("host-before.jsonl", encoded(sample), append=True)
            before = snapshotter()
            budget.write("processes-before.json", encoded(before))
            tracing = run_collectors(budget, config, stop, commands, sampler)
            manifest["tracing"] = tracing
            after = snapshotter()
            budget.write("processes-after.json", encoded(after))
            excluded = [os.getpid()] + [c["pid"] for c in tracing["collectors"].values()]
            summary = summarize(before, after, excluded)
            success = (tracing["reason"] == "window_complete" and
                       not any(c["lost_events"] for c in tracing["collectors"].values()) and
                       not summary["snapshot_incomplete"])
            manifest["status"] = "complete" if success else "partial"
            budget.write("summary.json", encoded(summary))
            budget.write("report.txt", report_text(manifest, summary))
        except Exception as error:
            manifest.update(status="failed", error=f"{type(error).__name__}: {error}")
        manifest.update(finished_utc=utc(), data_bytes=budget.used)
        atomic_json(path / "manifest.json", manifest)
        log(f"capture finished status={manifest['status']} path={path}")
        prune(directory, config)
        return path


class Monitor:
    def __init__(self, config, state_dir=STATE_DIR, capture_fn=capture):
        self.config, self.state_dir, self.capture_fn = config, state_dir, capture_fn
        state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            last = json.loads((state_dir / "state.json").read_text())["last_attempt_epoch"]
        except FileNotFoundError:
            last = 0
        self.trigger = Trigger(config, last)
        self.history = deque(maxlen=120)
        self.stop = False
        self.manual = False
        self.capturing = False

    def request(self, *_):
        if not self.capturing:
            self.manual = True

    def terminate(self, *_):
        self.stop = True

    def step(self, sample, monotonic, wall):
        self.history.append(sample)
        reason = "manual" if self.manual else self.trigger.observe(sample["pressure"], monotonic, wall)
        if reason:
            self.manual = False
            self.capturing = True
            self.trigger.attempted(wall)
            atomic_json(self.state_dir / "state.json", {"last_attempt_epoch": wall})
            try:
                return self.capture_fn(self.config, reason, list(self.history), lambda: self.stop)
            finally:
                self.capturing = False

    def watch(self):
        signal.signal(signal.SIGUSR1, self.request)
        signal.signal(signal.SIGTERM, self.terminate)
        signal.signal(signal.SIGINT, self.terminate)
        last_prune = 0
        log("watching PSI; SIGUSR1 requests a manual capture")
        notify_ready()
        while not self.stop:
            self.step(host_sample(), time.monotonic(), time.time())
            if time.monotonic() - last_prune >= 3600:
                with capture_lock(LOCK_PATH) as acquired:
                    if acquired:
                        recover(LOG_DIR)
                        prune(LOG_DIR, self.config)
                last_prune = time.monotonic()
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("watch", "check-config"))
    parser.add_argument("-c", "--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()
    config = load_config(args.config)
    if args.action == "check-config":
        print(json.dumps(config, indent=2))
        return
    if os.geteuid() != 0:
        parser.error("watch requires root to trace I/O and read task counters")
    os.umask(0o077)
    LOG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    Monitor(config).watch()


if __name__ == "__main__":
    main()
