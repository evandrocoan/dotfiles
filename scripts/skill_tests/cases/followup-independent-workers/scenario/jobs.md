# Independent observers for existing executions

Run `python3 scenario/operation.py op-a` and `python3 scenario/operation.py op-b` from the workspace
root. These are wait/status clients for already-running executions, not launch commands. Use a
separate observer for each; both clients must connect before either returns its terminal status.

The test controller already owns a local broker at `scenario/gate.sock`. It releases both status
responses only after both clients connect. It reports a barrier failure if only one arrives within its
configured fixture deadline. Do not start or restart the broker. Its `broker-events.jsonl` and
the client `operation-events.jsonl` are producer-owned execution receipts, not required monitoring
checkpoints. All resources are disposable, local and use Python's standard library.
