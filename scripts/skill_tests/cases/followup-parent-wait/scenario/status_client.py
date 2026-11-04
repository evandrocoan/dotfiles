"""Simulate delayed status delivery, without starting an underlying execution."""

import argparse
import json
import time


def observe(delay):
    print('WAITING job-905', flush=True)
    time.sleep(delay)
    print(json.dumps({'operation': 'job-905', 'state': 'COMPLETE', 'exit_code': 0}), flush=True)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', type=float, default=75)
    args = parser.parse_args()
    raise SystemExit(observe(args.delay))
