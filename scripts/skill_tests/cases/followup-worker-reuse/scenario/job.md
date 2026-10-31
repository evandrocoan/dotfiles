# Disposable status client

Follow job-91, attempt-3. The operation already exists. The local status API is represented by
`python3 scenario/status.py --once` for its first observation, then
`python3 scenario/status.py --wait` for a blocking terminal observation. Run from the workspace
root. These fixed external responses test native worker ownership, not a real remote service.

The client owns `scenario/queries.jsonl` as a receipt of requests. Preserve all source files.
No installation, plan, checkpoint, scheduler, operation restart or external contact is needed.
