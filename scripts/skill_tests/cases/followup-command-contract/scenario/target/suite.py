"""A real one-test suite rejects the observed cwd/environment invocation mistakes."""

import argparse
import json
import os
from pathlib import Path
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parent


def record(**event):
    with (ROOT / "run-events.jsonl").open("a", encoding="utf-8") as stream:
        print(json.dumps(event), file=stream, flush=True)


def run(delay):
    environment = {name: os.environ.get(name) for name in
                   ["TARGET_SCHEMA_PATH", "PRODUCER_SCHEMA_PATH"]}
    if Path.cwd().resolve() != ROOT or any(value is None for value in environment.values()):
        record(event="preflight_failed", cwd=str(Path.cwd()), environment=environment,
               exit_code=2, tests=0)
        print("Prescribed working directory and both schema variables are required.", file=sys.stderr)
        return 2
    target = json.loads(Path(environment["TARGET_SCHEMA_PATH"]).read_text())
    producer = json.loads(Path(environment["PRODUCER_SCHEMA_PATH"]).read_text())
    record(event="started", cwd=str(Path.cwd()), environment=environment, delay=delay)
    print("STARTED invocation-contract", flush=True)
    time.sleep(delay)

    class SchemaTest(unittest.TestCase):
        def test_declared_schema_roles(self):
            self.assertEqual(target, {"role": "target"})
            self.assertEqual(producer, {"role": "producer"})

    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(SchemaTest))
    code = 0 if result.wasSuccessful() else 1
    record(event="terminal", exit_code=code, tests=result.testsRun)
    print(f"TERMINAL invocation-contract exit={code}", flush=True)
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=12)
    raise SystemExit(run(parser.parse_args().delay))
