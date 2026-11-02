# One task with an intermediate handback

Task `task-128` includes both phases below. Its goal remains incomplete after inspect.

1. From the workspace root, the mechanical worker runs `python3 scenario/operation.py inspect`
   once and returns its intermediate result through its native final. It must not finalize yet.
2. After that report, the coordinator requests finalize as a continuation of this same task.
   The worker runs `python3 scenario/operation.py finalize` once and returns the terminal result.

Finalize has controlled startup latency of 75 seconds to expose wait expiration. It owns
`scenario/events.jsonl`. Preserve source files; no installation or external service is needed.
During finalize, return only its terminal result, without intermediate notifications.

Native-tool arrangement: the coordinator's first mailbox wait after requesting finalize uses
`timeout_ms: 10000` to exercise an actual expiration. This one test-induced timeout is not an
operation deadline. After it expires, continue under the skill's ordinary wait policy. Record
actual expiration and delivery; latency alone is not proof that either event occurred.
