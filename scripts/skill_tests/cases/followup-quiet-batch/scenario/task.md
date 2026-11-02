# One authorized execution batch

The mechanical worker runs these commands once each, in order, from the workspace root:

1. `python3 scenario/operation.py prepare`
2. `python3 scenario/operation.py check`
3. `python3 scenario/operation.py finish`

All three phases are already authorized. Inspect their actual returned results and report the
batch result through native completion. No new parent acknowledgment is needed between phases.
Each phase has controlled startup latency; use its original execution result when waiting.
The producer owns `scenario/events.jsonl`. Preserve all source files and do not rerun phases.

If `scenario/task.json` specifies `requested_update: "after_check"`, the user requested one
CHECKED update before finish. Deliver that update to the parent, then continue the batch.
