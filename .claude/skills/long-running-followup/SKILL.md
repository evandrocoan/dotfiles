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

Record startup errors/prompts and operation identity.
Prefer native completion, then an existing deterministic watcher, then supported scheduling.
No routine polling alongside reliable completion delivery.

Verify lifetime/return support before yielding; proposed schedules are not active. Load host
details only if needed: [Codex](references/codex.md), [Claude](references/claude.md),
[other hosts](references/clients.md).

## Delegate once, with a compact handoff

Reuse one authorized worker/monitor; delegate with fresh context, never per check. Keep procedure
in its authoritative source and live state in a checkpoint. Handoffs and scheduled prompts carry:

```text
Operation: identity/attempt, owner, observation source, terminal criteria.
References: instruction paths, checkpoint, verifiable authorization, continuation limits.
Return: parent and supported route.
Monitor: worker/schedule ID, cadence, timezone, deadline/check cap.
```

Keep identity, destination and bounds explicit; reference procedures and changing state. Verify
reference coverage; keep uncovered constraints concise. Aim for 100–200 words, longer only for
essential uncovered requirements. Omit historical IDs/snapshots. Require applicable instructions,
but do not make unchanged checks reread procedures or history. Load procedural detail for the next
authorized action; missing, stale or conflicting references block it. Monitor read-only; continuation
needs separate authority. Do not restart or recursively delegate.

## Check only when due

Use scheduling or bounded native waits, not short sleep loops or cache warming. Silent activations
still consume resources.

Observe new output once per due check, including prompts. Save observation/cursor, delivery status
and next due time in the checkpoint, within bounds. Stay silent on unchanged state unless updates
were requested. Missing/failed observations mean uncertainty; retry within bounds or report intervention.

## Finish monitoring and return evidence

On completion, failure, deadline, intervention or cancellation, deactivate only the owned schedule
if present; verify inactivity by read-back and report failed cleanup. Job completion does not disable
its schedule. Stopping monitoring does not cancel the operation; deadlines report last known state.

Return identity, time/state, evidence and next action/blocker once through native delivery.
Uncertain delivery requires read-back/deduplication or an uncertainty report, never blind resend/restart.

The parent verifies identity/freshness, rejects duplicate/stale results and resumes only authorized
work; pending approvals remain.
