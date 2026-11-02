"""A batch exposes phase changes without requiring coordinator intervention."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parent
PHASES = ('prepare', 'check', 'finish')
STATES = ('PREPARED', 'CHECKED', 'COMPLETE')


def run(action, delay):
    target = ROOT / 'events.jsonl'
    previous = [json.loads(line) for line in target.read_text().splitlines()] if target.exists() else []
    index = PHASES.index(action)
    if [row['action'] for row in previous] != list(PHASES[:index]):
        result = {'task': 'task-901', 'action': action, 'state': 'OUT_OF_ORDER', 'exit_code': 2}
        print(json.dumps(result), flush=True)
        return 2
    print(f'RUNNING task-901 {action}', flush=True)
    time.sleep(delay)
    result = {'task': 'task-901', 'action': action, 'state': STATES[index], 'exit_code': 0,
              'observed_at': datetime.now(timezone.utc).isoformat()}
    with target.open('a', encoding='utf-8') as stream:
        print(json.dumps(result), file=stream, flush=True)
    print(json.dumps(result), flush=True)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=PHASES)
    parser.add_argument('--delay', type=float, default=12)
    args = parser.parse_args()
    raise SystemExit(run(args.action, args.delay))
