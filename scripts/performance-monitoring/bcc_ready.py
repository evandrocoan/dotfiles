#!/usr/bin/python3
"""Gate packaged BCC collectors until attachment finishes; account for map failures."""

import ctypes
import json
from pathlib import Path
import re
import runpy
import signal
import sys
from datetime import datetime, timezone

UNKNOWN_QUEUE_NS = -1_000_000  # Packaged biosnoop formats this as -1.00 milliseconds.


def enable_capture(bpf, tool):
    names = ("start", "infobyreq") if tool == "biosnoop" else ("start",)
    sizes = {name: len(bpf[name]) for name in names}
    if any(sizes.values()):
        raise RuntimeError("collector maps populated before readiness")
    print("PERFORMANCE_COLLECTOR_INITIAL_MAPS " + json.dumps(sizes), file=sys.stderr, flush=True)
    bpf["perfmon_enabled"][ctypes.c_int(0)] = ctypes.c_uint(1)
    print("PERFORMANCE_COLLECTOR_READY", file=sys.stderr, flush=True)


def tracepoint_layout(text):
    fields = {}
    for line in text.splitlines():
        match = re.search(r"field:.*?\b(\w+)(?:\[.*?\])?;\s*offset:(\d+);\s*size:(\d+);", line)
        if match:
            fields[match[1]] = (int(match[2]), int(match[3]))
    common = {"dev": (8, 4), "sector": (16, 8), "nr_sector": (24, 4), "bytes": (28, 4)}
    modern = {**common, "ioprio": (32, 2), "rwbs": (34, 8)}
    legacy = {**common, "rwbs": (32, 8)}
    expected = modern if "ioprio" in fields else legacy
    if any(fields.get(key) != value for key, value in expected.items()):
        raise RuntimeError("unsupported block tracepoint field offsets; review biosnoop compatibility")
    return "ioprio" in fields


def adapt_text(text, formats):
    layouts = [tracepoint_layout(value) for value in formats]
    if len(layouts) != 2 or layouts[0] != layouts[1]:
        raise RuntimeError("block start/done tracepoint layouts differ")
    legacy = "    unsigned int bytes;\n    char rwbs[8];"
    modern = "    unsigned int bytes;\n    unsigned short ioprio;\n    char rwbs[8];"
    if layouts[0] and text.count(legacy) == 1:
        return text.replace(legacy, modern, 1)
    expected = modern if layouts[0] else legacy
    if text.count(expected) != 1:
        raise RuntimeError("distribution biosnoop struct changed; review compatibility runner")
    return text


def instrument(text, tool):
    header = "#include <linux/blk-mq.h>"
    declarations = """
BPF_ARRAY(perfmon_enabled, u32, 1);
BPF_ARRAY(perfmon_errors, u64, 1);
static int perfmon_active(void) {
    u32 key = 0;
    u32 *enabled = perfmon_enabled.lookup(&key);
    return enabled && *enabled;
}
"""
    if text.count(header) != 1:
        raise RuntimeError("BCC include changed; review collector instrumentation")
    text = text.replace(header, header + declarations)
    if tool == "biosnoop":
        functions = ("static int __trace_pid_start(struct hash_key key)",
                     "int trace_req_start(struct pt_regs *ctx, struct request *req)",
                     "static int __trace_req_completion(void *ctx, struct hash_key key)")
        updates = ("infobyreq.update(&key, &val)", "start.update(&key, &start_req)")
    else:
        functions = ("static int __trace_req_start(struct start_key key)",
                     "static int __trace_req_done(struct start_key key)")
        updates = ("start.update(&key, &ts)",)
    for function in functions:
        entry = function + "\n{"
        if text.count(entry) != 1:
            raise RuntimeError("BCC callback changed; review collector instrumentation")
        text = text.replace(entry, entry + "\n    if (!perfmon_active()) return 0;")
    for update in updates:
        if text.count(update + ";") != 1:
            raise RuntimeError("BCC map update changed; review collector instrumentation")
        text = text.replace(update + ";", "if (" + update + ") perfmon_errors.atomic_increment(0);")
    if tool == "biosnoop":
        # Disk/sector remain useful when issuer correlation is unavailable.
        text = text.replace("    u64 qdelta;", "    s64 qdelta;")
        text = text.replace("    data.qdelta = 0;", f"    data.qdelta = {UNKNOWN_QUEUE_NS};\n    data.dev = key.dev;\n    data.sector = key.sector;")
        text = text.replace("data.qdelta = startp->ts - valp->ts;",
                            f"data.qdelta = startp->ts >= valp->ts ? startp->ts - valp->ts : {UNKNOWN_QUEUE_NS};")
    return text


def main():
    from bcc import BPF
    from bcc.table import PerfEventArray

    if len(sys.argv) != 2 or sys.argv[1] not in ("biosnoop", "biolatency"):
        raise SystemExit("usage: bcc_ready.py biosnoop|biolatency")
    tool = sys.argv[1]
    original_init = BPF.__init__
    original_poll = BPF.perf_buffer_poll
    original_attach_tp = BPF.attach_tracepoint
    original_attach_kprobe = BPF.attach_kprobe
    state = {"bpf": None, "ready": False, "stop": False, "events": 0, "unknown_issuers": 0}
    formats = [Path(f"/sys/kernel/tracing/events/block/block_io_{event}/format").read_text()
               for event in ("start", "done")]

    def compatible_init(self, *args, **kwargs):
        if "text" not in kwargs or not isinstance(kwargs["text"], str):
            raise RuntimeError("distribution biosnoop compile interface changed")
        kwargs["text"] = instrument(adapt_text(kwargs["text"], formats), tool)
        result = original_init(self, *args, **kwargs)
        state["bpf"] = self
        return result

    def enable():
        enable_capture(state["bpf"], tool)
        state["ready"] = True

    def attach(original, self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        if tool == "biolatency" and kwargs.get("fn_name") in ("trace_req_done", "trace_req_done_tp"):
            enable()
        return result

    def poll(self, *args, **kwargs):
        if state["stop"]:
            raise SystemExit(0)
        return original_poll(self, timeout=100)

    def stop(*_):
        state["stop"] = True
        if tool == "biolatency":
            # This tool has no ctypes event callback, so it can exit directly and run finally.
            raise SystemExit(0)

    BPF.__init__ = compatible_init
    BPF.perf_buffer_poll = poll
    BPF.attach_tracepoint = lambda self, *a, **kw: attach(original_attach_tp, self, *a, **kw)
    BPF.attach_kprobe = lambda self, *a, **kw: attach(original_attach_kprobe, self, *a, **kw)
    original = PerfEventArray.open_perf_buffer

    def open_ready(self, callback, page_cnt=8, lost_cb=None):
        first = True

        def event(cpu, data, size):
            nonlocal first
            if first:
                print("PERFORMANCE_FIRST_EVENT_RECEIVED_UTC " +
                      datetime.now(timezone.utc).isoformat(), file=sys.stderr, flush=True)
                first = False
            state["events"] += 1
            if self.event(data).pid == 0:
                state["unknown_issuers"] += 1
            callback(cpu, data, size)

        def lost(count):
            print(f"PERFORMANCE_COLLECTOR_LOST count={count}",
                  file=sys.stderr, flush=True)
            if lost_cb is not None:
                lost_cb(count)

        result = original(self, event, page_cnt=page_cnt, lost_cb=lost)
        enable()
        return result

    PerfEventArray.open_perf_buffer = open_ready
    sys.stdout.reconfigure(line_buffering=True)
    signal.signal(signal.SIGTERM, stop)
    sys.argv = [f"/usr/sbin/{tool}-bpfcc"] + (["-Q"] if tool == "biosnoop" else ["-D", "-Q", "-m", "-T", "1"])
    try:
        runpy.run_path(sys.argv[0], run_name="__main__")
    finally:
        if state["bpf"] is not None:
            bpf = state["bpf"]
            bpf["perfmon_enabled"][ctypes.c_int(0)] = ctypes.c_uint(0)
            failures = bpf["perfmon_errors"][ctypes.c_int(0)].value
            stats = {"map_update_failures": failures}
            if tool == "biosnoop":
                stats.update(events=state["events"], unknown_issuers=state["unknown_issuers"])
            print("PERFORMANCE_COLLECTOR_STATS " + json.dumps(stats),
                file=sys.stderr, flush=True)
            if failures:
                print(f"PERFORMANCE_COLLECTOR_LOST map_update_failures={failures}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
