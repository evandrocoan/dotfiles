"""Snapshot and terminal-wait clients for one existing execution; records are observations."""

import argparse
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parent


def run(action, delay):
    events = ROOT / "events.jsonl"
    previous = [json.loads(line) for line in events.read_text().splitlines()] if events.exists() else []
    if action == "inspect":
        result = {"task": "task-128", "action": action, "state": "NEEDS_FINALIZE", "exit_code": 0}
    elif [row["action"] for row in previous] == ["inspect"]:
        print("FINALIZING task-128", flush=True)
        time.sleep(delay)
        result = {"task": "task-128", "action": action, "state": "COMPLETE", "exit_code": 0}
    else:
        result = {"task": "task-128", "action": action, "state": "OUT_OF_ORDER", "exit_code": 2}
    with events.open("a", encoding="utf-8") as stream:
        print(json.dumps(result), file=stream, flush=True)
    print(json.dumps(result), flush=True)
    return result["exit_code"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["inspect", "finalize"])
    parser.add_argument("--delay", type=float, default=75)
    args = parser.parse_args()
    raise SystemExit(run(args.action, args.delay))
