"""A real local barrier distinguishes concurrent native workers from serialized launches."""

import argparse
import json
import os
from pathlib import Path
import socket


ROOT = Path(__file__).parent
SOCKET = ROOT / "gate.sock"


def record(filename, **values):
    with (ROOT / filename).open("a", encoding="utf-8") as stream:
        print(json.dumps(values), file=stream, flush=True)


def serve(timeout):
    clients = {}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(SOCKET))
        server.listen(2)
        print("BROKER_READY", flush=True)
        try:
            while len(clients) < 2:
                server.settimeout(None if not clients else timeout)
                connection, _ = server.accept()
                connection.settimeout(timeout)
                identity = connection.recv(128).decode().strip()
                if identity not in {"op-a", "op-b"} or identity in clients:
                    connection.close()
                    raise ValueError("Unexpected or duplicate operation identity")
                clients[identity] = connection
                record("broker-events.jsonl", event="connected", operation=identity)
            record("broker-events.jsonl", event="released", operations=sorted(clients))
            for identity, connection in clients.items():
                result = {"operation": identity, "state": "SUCCEEDED", "exit_code": 0}
                connection.sendall((json.dumps(result) + "\n").encode())
            return 0
        except (OSError, ValueError) as error:
            record("broker-events.jsonl", event="failed", error=str(error))
            return 7
        finally:
            for connection in clients.values():
                connection.close()
            SOCKET.unlink()


def run(identity):
    record("operation-events.jsonl", event="started", operation=identity, pid=os.getpid())
    print(json.dumps({"operation": identity, "state": "RUNNING"}), flush=True)
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(SOCKET))
            client.sendall((identity + "\n").encode())
            response = client.makefile("r", encoding="utf-8").readline()
        result = json.loads(response)
        if result != {"operation": identity, "state": "SUCCEEDED", "exit_code": 0}:
            raise ValueError("Invalid broker result")
    except (OSError, ValueError) as error:
        result = {"operation": identity, "state": "FAILED", "exit_code": 7, "error": str(error)}
    record("operation-events.jsonl", event="terminal", **result)
    print(json.dumps(result), flush=True)
    return result["exit_code"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", nargs="?", choices=["op-a", "op-b"])
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--timeout", type=float, default=90)
    args = parser.parse_args()
    if not args.serve and args.operation is None:
        parser.error("operation is required without --serve")
    raise SystemExit(serve(args.timeout) if args.serve else run(args.operation))
