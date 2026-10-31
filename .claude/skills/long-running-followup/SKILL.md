---
name: long-running-followup
description: >-
  Delegate authorized polling and operations that remain running to a reusable worker. Use before
  launching known waits, at the first still-running result, or before any status polling or
  scheduled follow-up. Prefer completion events. Exclude short synchronous commands unless they
  return still running, and explanations requiring no monitoring.
---

# Long-running follow-up

## Delegate waiting

Start required monitoring without a separate consent question. Honor explicit opt-outs and supplied
deadlines/check caps; otherwise follow until completion, failure, required intervention or
cancellation. Do not invent a cutoff; per-call wait limits do not end monitoring.

Delegate polling, follow-up checks and any command that returns still running to one worker.
Delegate known waits before launch; on an unexpected running result, hand off observation before
another status check, log read or execution wait. The parent awaits the worker's completion event
instead of checking operation or worker progress.

Reuse the assigned worker for an operation, never one per check. Independent operations may use
different workers; there is no global one-worker limit. Select `gpt-6-luna` / `high` in Codex or
`haiku` in Claude Code explicitly. Start with fresh context and inherit tools and permissions.
An assigned observation worker keeps its operation; it does not delegate again.

Preserve already-started operations. Delegate an accessible status/result source; do not assume
another agent's execution session transfers. After worker completion evidence, the parent may
collect its terminal tool result once. If delegation or result access is unavailable, preserve
the operation and report the gap; do not substitute another model or resume parent polling.

## Choose how completion arrives

The worker records startup errors/prompts and operation identity.
Prefer native completion, then an existing deterministic watcher, then supported scheduling.
No routine polling alongside reliable completion delivery.
When following a log, include existing terminal output and avoid gaps between reading and subscribing.

Verify lifetime/return support before yielding; proposed schedules are not active. Load host
details only if needed: [Codex](references/codex.md), [Claude](references/claude.md),
[other hosts](references/clients.md).

## Assign the observation directly

Pass the operation/status source, exact exit-code or log-event condition, and parent/return route
directly. Have the worker load this skill before observing; fresh context does not include the
parent's loaded skills. Include applicable observation/access instructions, authorization and
chat restrictions.
For scheduled checks, include cadence, timezone and any supplied deadline/check cap. Do not add a
prompt-rewriting step or word budget before monitoring.

Do not create or require a checkpoint for a simple wait. Reference existing monitoring state only
when resumption or deduplication needs it. The monitor reads observation/access/return inputs,
updates needed monitoring state and reports. Do not follow continuation references or search for
later maintenance context. Missing monitoring inputs need clarification. Do not restart
or recursively delegate.

## Check only when due

The worker uses scheduling or bounded native waits, not short polling loops or cache warming.

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
