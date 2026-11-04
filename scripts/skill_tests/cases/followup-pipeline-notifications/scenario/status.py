"""Read a host-owned status endpoint; client success is not execution success."""

import argparse
import json
from pathlib import Path
import socket


def observe(after):
    endpoint = Path(__file__).with_name('feed.sock')
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(str(endpoint))
        client.sendall((json.dumps({'after': after}) + '\n').encode())
        result = json.loads(client.makefile('r', encoding='utf-8').readline())
    print(json.dumps(result), flush=True)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--after', type=int, required=True)
    args = parser.parse_args()
    raise SystemExit(observe(args.after))
