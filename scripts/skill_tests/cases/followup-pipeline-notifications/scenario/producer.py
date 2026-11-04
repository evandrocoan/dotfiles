"""Test controller owns an independent producer and its retained status feed."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import signal
import socket
import threading
import time


ROOT = Path(__file__).resolve().parent


def snapshots(task):
    if task['mode'] not in ('success', 'required_failure'):
        raise ValueError('Unsupported pipeline fixture mode')
    base = {
        'pipeline_id': task['pipeline_id'], 'status': 'running', 'pipeline_exit_code': None,
        'jobs': [
            {'name': 'build', 'status': 'success', 'required': True, 'exit_code': 0},
            {'name': 'lint', 'status': 'success', 'required': True, 'exit_code': 0},
            {'name': 'unit', 'status': 'running', 'required': True, 'exit_code': None},
            {'name': 'e2e', 'status': 'pending', 'required': True, 'exit_code': None},
        ],
    }
    rows = [deepcopy(base)]
    base['jobs'][2].update(status='success', exit_code=0)
    rows.append(deepcopy(base))
    base['jobs'][3]['status'] = 'running'
    rows.append(deepcopy(base))
    if task['mode'] == 'required_failure':
        base['jobs'][3].update(status='failed', exit_code=7)
    rows.append(deepcopy(base))
    if task['mode'] == 'required_failure':
        base.update(status='failed', pipeline_exit_code=7)
    else:
        base['jobs'][3].update(status='success', exit_code=0)
        base.update(status='success', pipeline_exit_code=0)
    rows.append(deepcopy(base))
    return [dict(row, sequence=index) for index, row in enumerate(rows)]


def record(kind, **values):
    with (ROOT / 'events.jsonl').open('a', encoding='utf-8') as stream:
        print(json.dumps({'kind': kind, 'monotonic': time.monotonic(), **values}),
              file=stream, flush=True)


def serve(interval):
    def stop(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    task = json.loads((ROOT / 'task.json').read_text())
    rows = snapshots(task)
    ready = threading.Condition()
    emitted = []

    def produce():
        for index, row in enumerate(rows):
            if index:
                time.sleep(interval)
            with ready:
                emitted.append(row)
                record('produced', snapshot=row)
                ready.notify_all()
        print('PRODUCER_TERMINAL', flush=True)

    worker = None
    endpoint = ROOT / 'feed.sock'
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(endpoint))
        server.listen()
        print('BROKER_READY', flush=True)
        try:
            while True:
                connection, _ = server.accept()
                with connection:
                    request = json.loads(connection.makefile('r', encoding='utf-8').readline())
                    after = request['after']
                    if type(after) is not int or not -1 <= after < len(rows) - 1:
                        raise ValueError('Invalid observation cursor')
                    if worker is None:
                        worker = threading.Thread(target=produce, daemon=True)
                        worker.start()
                    with ready:
                        ready.wait_for(lambda: len(emitted) > after + 1)
                        row = emitted[after + 1]
                        record('observed', after=after, sequence=row['sequence'])
                        connection.sendall((json.dumps(row) + '\n').encode())
        finally:
            endpoint.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=float, default=20)
    args = parser.parse_args()
    serve(args.interval)
