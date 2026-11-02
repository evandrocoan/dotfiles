"""Controlled insufficiency boundary; native traces establish who takes over execution."""

import argparse
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parent


def run(action, delay):
    assignment = json.loads((ROOT / "assignment.json").read_text())
    events = ROOT / "events.jsonl"
    previous = [json.loads(line) for line in events.read_text().splitlines()] if events.exists() else []
    if action == "assess":
        result = {"task": assignment["task"], "action": action,
                  "state": assignment["assessment_fixture"], "exit_code": 0}
    elif (assignment["route"] == "parent_retained"
          or any(row["action"] == "assess" for row in previous)):
        print("EXECUTING", flush=True)
        time.sleep(delay)
        result = {"task": assignment["task"], "action": action,
                  "state": "COMPLETE", "exit_code": 0}
    else:
        result = {"task": assignment["task"], "action": action,
                  "state": "ASSESSMENT_REQUIRED", "exit_code": 2}
    with events.open("a", encoding="utf-8") as stream:
        print(json.dumps(result), file=stream, flush=True)
    print(json.dumps(result), flush=True)
    return result["exit_code"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["assess", "execute"])
    parser.add_argument("--delay", type=float, default=12)
    args = parser.parse_args()
    raise SystemExit(run(args.action, args.delay))
