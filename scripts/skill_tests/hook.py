"""Private Claude observer. Never returns captured content to the model."""

import hashlib
import json
import os
from pathlib import Path
import sys


def main():
    event = json.load(sys.stdin)
    workspace = Path(os.environ["SKILL_TEST_WORKSPACE"]).resolve()
    if event.get("hook_event_name") == "InstructionsLoaded":
        path = Path(event["file_path"]).resolve()
        if path.is_relative_to(workspace) and path.is_file():
            event["observed_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            event["outside_workspace"] = True
    # Hooks are private evidence. Exporting this raw object is deliberately unsupported.
    fd = os.open(os.environ["SKILL_TEST_HOOK_LOG"], os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a") as stream:
        stream.write(json.dumps(event) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


if __name__ == "__main__":
    main()
