---
name: long-running-followup
description: >-
  Follow authorized long-running operations without frequent model polling. Use before repeated
  status checks, scheduled follow-ups, or arranging a worker's return to a parent chat. Prefer
  completion events and minimal-context delegation. Exclude short commands, generic performance
  tuning, and explanations requiring no monitoring.
---

# Long-running follow-up

## Choose how completion arrives

Record startup errors/prompts, run/revision or process identity, source and terminal criteria.
Prefer native completion, then an existing deterministic watcher, then supported scheduling.
No routine polling alongside reliable completion delivery.

Verify lifetime/return support before yielding; proposed schedules are not active. Load host
details only if needed: [Codex](references/codex.md), [Claude](references/claude.md),
[other hosts](references/clients.md).

## Delegate once, with a compact handoff

Delegate once with fresh minimal context. Reuse one worker/monitor per operation; do not wake
the parent to delegate checks. Save in task state:

```text
Operation: identity, owner, source, terminal criteria.
Scope: continuation limits, instruction paths.
Return: parent, route, verifiable human authorization when required.
Monitor: worker/schedule ID, cadence, next due time/timezone, deadline or check cap.
State: last observation/cursor, operation status, delivery status.
```

Carry required instruction paths and authorization references, not summaries alone. Monitor
read-only; do not restart, expand or recursively delegate the work.

## Check only when due

Use scheduling or bounded native waits, not short sleep loops or cache warming. Choose cadence
(e.g. 15/30/60 minutes) and a deadline/check cap. Silent model activations still consume resources.

Observe new output once per due check, including prompts. Save the next check within bounds.
Stay silent on unchanged state unless updates were requested. Missing/failed observations mean
uncertainty, not completion; retry within bounds or report intervention.

## Finish monitoring and return evidence

On completion, failure, deadline, intervention or cancellation: if a schedule exists, deactivate
only the owned schedule and verify by read-back that it is inactive. A finished job does not
disable its schedule. Report failed cleanup.
Stopping monitoring does not cancel the operation; deadlines report the last known state.

Return once: identity, time/state, evidence and next action/blocker. Reuse native delivery.
Uncertain delivery needs supported read-back/deduplication or an uncertainty report, never blind
resend/restart.

The parent verifies identity/freshness, discards duplicate/stale results and resumes only authorized
work; pending approvals remain.
