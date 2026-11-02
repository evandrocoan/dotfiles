---
name: long-running-followup
description: >-
  Delegate waiting and operation-status checks to reusable workers. Use before known waits,
  at the first still-running result, or before any status check, polling or scheduled follow-up.
  Prefer completion events. Exclude short synchronous execution unless it remains running,
  and terminology-only explanations.
---

# Long-running follow-up

## Delegate waiting

Start required monitoring without a separate consent question. Honor explicit opt-outs and supplied
deadlines/check caps; otherwise follow until completion, failure, required intervention or
cancellation. Do not invent a cutoff; per-call wait limits do not end monitoring.

As coordinator, delegate operation-status checks, even a single short read. For a known wait,
have the assigned executor launch and follow the command. That executor owns its command's wait;
do not add a monitoring worker just because it takes time. If a parent launch unexpectedly remains
running and the parent is not the retained technical executor, hand off accessible observation
before another status/log read or execution wait.
The parent awaits delivery in a long event-driven blocking call, waking early on a result.
Use minute-scale supported timeouts unless a real deadline/tool limit requires less; do not loop
on short mailbox or worker-status checks.

Use workers as needed for independent work; there is no fixed worker-count limit. Fix the task scope
at assignment and reuse its worker across checks, commands, interim reports and continuations.
A command exit or native final alone does not complete that task. Start fresh when the task is
complete or the target, purpose or role changes, never for each command or check.
Honor a task-selected engineering model and effort; otherwise use `gpt-6.1-terra` / `high` in Codex
or Sonnet 5.5 / `high` in Claude Code. Work beyond Luna/Haiku's mechanical scope goes to that
engineering tier; preserve its executor through waits. If that tier is insufficient, including
selected Terra xhigh, the parent retains or takes over technical execution instead of spawning a
stronger engineering child. Do not require an unsuccessful trial first. The retained parent launches
and awaits its commands itself, including after a still-running return. Use the original command's
native result or completion event; do not delegate its wait or add a watcher or polling loop.
Separate status checks remain delegated.
For monitoring or mechanical execution without a selected executor, explicitly use
`gpt-6-luna` / `high` in Codex or Haiku 5.5 / `high` in Claude Code. Inherit tools and permissions.
An assigned worker does not delegate its own wait again.

Preserve already-started operations. Delegate an accessible status/result source; do not assume
another agent's execution session transfers. After worker completion evidence, the parent may
collect its terminal tool result once. If delegation or result access is unavailable, preserve
the operation and report the gap; do not substitute another model or resume parent polling.

## Choose how completion arrives

The worker records startup errors/prompts and operation identity.
Prefer native completion, then an existing deterministic watcher, then supported scheduling.
No routine polling alongside reliable completion delivery.
When following a log, include existing terminal output, avoid read/subscribe gaps, and make the
watcher terminate on the matched event or producer exit. An open-ended `tail` pipeline can remain
blocked after completion.

Verify lifetime/return support before yielding; proposed schedules are not active. Before choosing
a background-command route, load host details: [Codex](references/codex.md), [Claude](references/claude.md),
[other hosts](references/clients.md).

## Assign the observation directly

Pass the actual command or authoritative status source, operation identity, exact exit-code or
log-event condition, and return route. Have the worker load this skill; fresh context does not
include the parent's loaded skills. Include applicable access instructions and authorization.
Observation returns facts and evidence; diagnose or repair only when that is the assigned task.
For scheduled checks, include cadence, timezone and any supplied deadline/check cap. Do not add a
prompt-rewriting step or word budget before monitoring.

Do not create or require a checkpoint for a simple wait. Reference existing monitoring state only
when resumption or deduplication needs it. In observation-only assignments, read only observation,
access and return inputs; update needed monitoring state and report. Continuation plans, old
prompts and maintenance history are outside that assignment, even when referenced in its inputs.
Missing monitoring inputs need clarification. Do not restart operations.

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
