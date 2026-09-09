#!/usr/bin/env python3
"""Bound historical atop storage without unlinking current or observed open logs."""

import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import sys


LOG_DIRECTORY = Path("/var/log/atop")
MAX_BYTES = 20 * 1024**3
MIN_FREE_BYTES = 10 * 1024**3
LOG_NAME = re.compile(r"atop_[0-9]{8}\Z")


def open_logs(directory):
    """Snapshot open descriptors, including readers and a writer awaiting rotation."""
    opened = set()
    prefix = str(directory) + "/"
    for process in Path("/proc").iterdir():
        if not process.name.isdecimal():
            continue
        try:
            descriptors = list((process / "fd").iterdir())
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        for descriptor in descriptors:
            try:
                target = os.readlink(descriptor)
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
            if target.startswith(prefix):
                opened.add(Path(target))
    return opened


def prune(directory, max_bytes, protected, today):
    candidates = sorted(
        path for path in directory.iterdir()
        if LOG_NAME.fullmatch(path.name) and not path.is_symlink() and path.is_file()
    )
    total = sum(path.stat().st_size for path in candidates)
    before = total
    removed = []
    for path in candidates:
        if total <= max_bytes:
            break
        if path in protected or path.name >= "atop_" + today:
            continue
        size = path.stat().st_size
        path.unlink()
        removed.append(path.name)
        total -= size
    return {
        "bytes_before": before,
        "bytes_after": total,
        "budget_bytes": max_bytes,
        "removed": removed,
        "protected_data_exceeds_budget": total > max_bytes,
    }


def main():
    with open("/run/performance-log-retention.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        total = sum(
            path.stat().st_size for path in LOG_DIRECTORY.iterdir()
            if LOG_NAME.fullmatch(path.name) and not path.is_symlink() and path.is_file()
        )
        free = shutil.disk_usage(LOG_DIRECTORY).free
        budget = min(MAX_BYTES, max(0, total + free - MIN_FREE_BYTES))
        result = prune(
            LOG_DIRECTORY, budget, open_logs(LOG_DIRECTORY),
            datetime.date.today().strftime("%Y%m%d"),
        )
        print(json.dumps(result, sort_keys=True))
        # An active/replayed file is kept even if it alone exceeds the budget.
        if result["protected_data_exceeds_budget"]:
            print("Storage budget exceeded by protected logs; inspect free disk space.",
                  file=sys.stderr)


if __name__ == "__main__":
    main()
