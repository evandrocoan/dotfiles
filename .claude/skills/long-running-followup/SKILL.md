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

## Assign the observation directly

Reuse one authorized monitor, never one per check. For monitoring subagents use `gpt-6-luna` /
`high` explicitly, with fresh context and inherited tool permissions; report unavailability
instead of substituting another model.

Pass the operation/status source, exact exit-code or log-event condition, and parent/return route
directly. Include applicable observation/access instructions, authorization and chat restrictions.
For scheduled checks, include cadence, timezone and deadline/check cap. Do not add a prompt-rewriting
step or word budget before monitoring.

Do not create or require a checkpoint for a simple wait. Reference existing monitoring state only
when resumption or deduplication needs it. The monitor reads observation/access/return inputs,
updates needed monitoring state and reports. Do not follow continuation references or search for
later maintenance context. Missing monitoring inputs need clarification. Do not restart
or recursively delegate.

## Check only when due

Use scheduling or bounded native waits, not short polling loops or cache warming.

Observe read-only once per due check, including prompts. Persist monitoring state only when needed
to resume or deduplicate; preserve operation identity/attempt. Stay silent on unchanged state unless
updates were requested.
Missing/failed observations mean uncertainty; retry within bounds or report intervention.

## Finish monitoring and return evidence

On completion, failure, deadline, intervention or cancellation, deactivate only the owned schedule,
if any; verify inactivity by read-back and report failed cleanup. Stopping monitoring does not
cancel the operation; deadlines report last known state.

Return identity, time/state, exit code or matched event, and concise evidence once through the agreed,
supported route, preferring native delivery when available.
Completion proves neither downstream validation nor permission to continue.
Uncertain delivery requires read-back/deduplication or an uncertainty report, never blind resend/restart.

The monitoring activation ends with its report, without inspecting continuation prerequisites.
After receiving it, the originating parent checks identity/freshness, rejects duplicate/stale
results and consults only prerequisites for its next authorized action. Missing/stale prerequisites
and pending approvals still block that action.
