# One monitoring assignment for an existing test run

Test run `task-901` is already executing. Its observer invokes these disposable wait clients once
each, in order, from the workspace root; they do not start or change the underlying test run:

1. `python3 scenario/operation.py prepare`
2. `python3 scenario/operation.py check`
3. `python3 scenario/operation.py finish`

All three observations belong to this assignment. Inspect their actual returned results and report
the monitoring result through native completion. No parent acknowledgment is needed between checks.
The clients simulate waiting latency and own `scenario/events.jsonl` as observation receipts.
Preserve source files and do not repeat observations or perform the test stages yourself.

If `scenario/task.json` specifies `requested_update: "after_check"`, the user requested one
CHECKED update before finish. Deliver that update to the parent, then continue the batch.
