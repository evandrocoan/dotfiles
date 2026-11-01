"""Disposable technical preparation with producer-owned evidence and no application step."""

import argparse
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parent


def record(**event):
    with (ROOT / "events.jsonl").open("a", encoding="utf-8") as stream:
        print(json.dumps(event), file=stream, flush=True)


def prepare(delay):
    original = (ROOT / "source.json").read_bytes()
    source = json.loads(original)
    if source != {"mode": "workspace-write", "network_enabled": True}:
        record(state="REFUSED", exit_code=2)
        print("REFUSED unsupported source", flush=True)
        return 2
    record(state="PREPARING", source_sha256=hashlib.sha256(original).hexdigest())
    print("PREPARING local preview", flush=True)
    time.sleep(delay)
    preview = {"permission_profile": "local-workspace", "network_enabled": True}
    output = (json.dumps(preview, sort_keys=True) + "\n").encode()
    with (ROOT / "preview.json").open("xb") as stream:
        stream.write(output)
    record(state="PREVIEW_READY", exit_code=0, preview_sha256=hashlib.sha256(output).hexdigest())
    print("PREVIEW_READY exit=0; not applied", flush=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=12)
    raise SystemExit(prepare(parser.parse_args().delay))
