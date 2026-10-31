# Independent disposable operations

Run `python3 scenario/operation.py op-a` and `python3 scenario/operation.py op-b` from the workspace
root. Each command owns that operation's startup and terminal output. Use a separate monitoring
worker for each operation; their work is independent and both must be started before waiting.

The test controller already owns a local broker at `scenario/gate.sock`. It releases the two
operations only after both connect. It reports a barrier failure if only one arrives within its
configured fixture deadline. Do not start or restart the broker. Its `broker-events.jsonl` and
the client `operation-events.jsonl` are producer-owned execution receipts, not required monitoring
checkpoints. All resources are disposable, local and use Python's standard library.
