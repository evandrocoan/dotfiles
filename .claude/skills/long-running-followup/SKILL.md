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

Separate waiting from continuation, even when inherited context contains a plan. Reuse one
authorized monitor, never one per check. For monitoring subagents use `gpt-6-luna` / `high`
explicitly, with fresh context and inherited tool permissions; report unavailability instead of
substituting another model. Fill this short handoff shape; never drop applicable fields to meet
a word target. Reference changing state instead of copying snapshots; do not restate this skill.

```text
Read: applicable instruction references; current monitoring state path.
Observe: identity/attempt, exact source and terminal condition; once when due, silent if unchanged.
Return: parent and supported route.
Bounds: cadence, timezone, deadline/check cap.
Stop: deactivate only owned schedule, read back inactivity; preserve operation.
Chat: retain any no-archive/no-new-chat constraint.
```

Include applicable instructions and required observation/access and return authorization.
Exclude maintenance plans, future-step checklists and continuation approvals from the assignment
and monitor reads, even at completion. Missing future-step references do not block observation;
missing monitoring inputs need clarification. Do not restart or recursively delegate.

## Check only when due

Use scheduling or bounded native waits, not short polling loops or cache warming.

Observe read-only once per due check, including prompts. Save only needed cursor/delivery/next-due
state; simple waits need no new checkpoint. Stay silent on unchanged state unless updates were
requested. Missing/failed observations mean uncertainty; retry within bounds or report intervention.

## Finish monitoring and return evidence

On completion, failure, deadline, intervention or cancellation, deactivate only the owned schedule,
if any; verify inactivity by read-back and report failed cleanup. Stopping monitoring does not
cancel the operation; deadlines report last known state.

Return identity, time/state, exit code or matched event, and concise evidence once through native delivery.
Completion proves neither downstream validation nor permission to continue.
Uncertain delivery requires read-back/deduplication or an uncertainty report, never blind resend/restart.

The parent checks identity/freshness, rejects duplicate/stale results and consults only prerequisites
for its next authorized action. Missing/stale prerequisites and pending approvals still block it.
