"""Controlled external status boundary for native worker-ownership tests."""

import argparse
import json
from pathlib import Path
import time


parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument("--once", action="store_true")
mode.add_argument("--wait", action="store_true")
args = parser.parse_args()
with Path(__file__).with_name("queries.jsonl").open("a", encoding="utf-8") as stream:
    print(json.dumps({"operation": "job-91", "attempt": 3, "wait": args.wait}), file=stream)
print(json.dumps({"operation": "job-91", "attempt": 3, "state": "RUNNING"}), flush=True)
if args.wait:
    time.sleep(12)
    print(json.dumps({"operation": "job-91", "attempt": 3, "state": "SUCCEEDED",
                      "exit_code": 0}), flush=True)
