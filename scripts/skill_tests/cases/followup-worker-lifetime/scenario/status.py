"""Producer-owned observations for two separate native worker assignments."""

import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("operation", choices=["alpha", "beta"])
args = parser.parse_args()
result = ({"operation": "alpha", "target": "target-a", "state": "SUCCEEDED", "exit_code": 0}
          if args.operation == "alpha" else
          {"operation": "beta", "target": "target-b", "state": "FAILED", "exit_code": 7,
           "error": "fixture output directory is full"})
with Path(__file__).with_name("observations.jsonl").open("a", encoding="utf-8") as stream:
    print(json.dumps(result), file=stream, flush=True)
print(json.dumps(result), flush=True)
