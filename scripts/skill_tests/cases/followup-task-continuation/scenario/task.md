# One monitoring task with an intermediate handback

The execution is already running. Monitoring task `task-128` includes both observations below;
its goal remains incomplete after inspect. The commands are disposable status clients, not
execution stages. In particular, `finalize` waits for terminal status; it does not finish the work.

1. From the workspace root, the observer invokes `python3 scenario/operation.py inspect`
   once and returns its intermediate result through its native final. It must not finalize yet.
2. After that report, the coordinator requests finalize as a continuation of this same task.
   The observer invokes `python3 scenario/operation.py finalize` once and returns the terminal result.

The final wait has controlled latency of 75 seconds to expose wait expiration. The clients own
`scenario/events.jsonl` as observation receipts. Preserve source files; no external service is needed.
During finalize, return only its terminal result, without intermediate notifications.

Native-tool arrangement: the coordinator's first mailbox wait after requesting finalize uses
`timeout_ms: 10000` to exercise an actual expiration. This one test-induced timeout is not an
operation deadline. After it expires, continue under the skill's ordinary wait policy. Record
actual expiration and delivery; latency alone is not proof that either event occurred.
