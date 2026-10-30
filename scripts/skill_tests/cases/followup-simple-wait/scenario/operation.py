"""A disposable process whose initial output must not be mistaken for completion."""

import json
import sys
import time


operation, exit_code = sys.argv[1], int(sys.argv[2])
print(json.dumps({"operation": operation, "state": "RUNNING"}), flush=True)
time.sleep(12)
print(json.dumps({
    "operation": operation,
    "state": "TRANSFER_FINISHED" if exit_code == 0 else "FAILED",
}), flush=True)
raise SystemExit(exit_code)
