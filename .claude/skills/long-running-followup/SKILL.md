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

Inspect startup for errors/prompts. Record the exact run/revision or process start identity,
observation source, and success/failure criteria.

Prefer native completion, then an existing deterministic watcher, then a supported scheduler.
Read only the applicable [client route](references/clients.md). Verify handles, destination,
process lifetime and wakeup support before yielding; report gaps instead of inventing a fallback.
Suggested schedules are not active. Do not add polling to reliable completion delivery.

## Delegate once, with a compact handoff

Delegate once when authorized and useful, with fresh minimal context and mandatory instructions.
Do not wake the parent to delegate each check or spawn a worker each tick. Keep this handoff in
existing task/scheduler state:

```text
Operation: identity, owner, source, terminal criteria.
Scope: continuation limits, instruction paths.
Return: parent, route, verifiable human authorization when required.
Monitor: worker/schedule ID, cadence, next due time/timezone, deadline or check cap.
State: last observation/cursor, operation status, delivery status.
```

Monitor read-only; do not restart work, expand scope, or recursively delegate.

## Check only when due

Choose cadence by duration and urgency (e.g. 15, 30, 60 minutes). Reconcile/reuse one monitor per
operation. Use scheduling or bounded native waits, never repeated short sleeps or cache-warming
turns. Silent model activations still consume resources.

Each due check makes one bounded observation of new output, including prompts. Record the next
check within the bound; remain silent on unchanged state unless updates were requested.
Missing/failed observations mean uncertainty, not completion; retry within the bound or report
required intervention.

## Finish monitoring and return evidence

On success, failure, deadline, intervention, or user cancellation, deactivate only the owned
schedule and verify cleanup; report failures. Stopping monitoring does not cancel the operation.
A deadline reports the last known state, not an invented result.

Return once through the established route: run identity, observation time/state, decisive
evidence/artifact, and next action/blocker. Use the native result if it already reaches the parent.
Keep execution and delivery separate: uncertain delivery requires supported read-back/deduplication
or reporting uncertainty, never blind resend or rerunning work.

The parent checks identity/freshness, ignores stale/duplicate results, and resumes only
still-authorized work. Pending questions/approvals remain.
