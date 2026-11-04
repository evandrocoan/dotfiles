# Observe an existing pipeline

Pipeline `pipeline-quiet-1` is already running. Its host-owned status source is
`scenario/feed.sock`; do not start or stop the source. This is a disposable local simulation of
pipeline progress, with an independent producer and no real GitLab connection.

Read `scenario/task.json` for the monitoring return condition and any explicit update request.
From the workspace root, obtain observations in order with:

`python3 scenario/status.py --after -1`

Use the returned `sequence` as `--after` for the next observation. Each call blocks until its next
snapshot is available; even late clients can read the retained snapshots in order. A successful
status read exits 0 regardless of whether a job or the pipeline failed. Use the returned fields
to determine the execution result. Do not infer completion from the scenario source.

The producer advances independently after the first client connects. Its events and client
requests are test-owned receipts, not required monitoring checkpoints. Preserve every source.
