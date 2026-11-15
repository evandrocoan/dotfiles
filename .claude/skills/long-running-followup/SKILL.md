---
name: long-running-followup
description: >-
  Delegate only waiting for long-running executions, such as CI pipelines, builds, tests or
  deployment rollouts. Use for known long waits, still-running executions or repeated checks of
  their progress. Not for database queries, investigation, coding, general execution, unrelated
  status questions or terminology-only explanations.
---

# Long-running follow-up

## Delegate waiting

This skill delegates waiting and execution-progress observation only. Use `gpt-6-luna` in Codex
or Haiku 5.5 in Claude Code for that role, with inherited tools and permissions and an explicitly
selected supported effort. It does not select engineering executors or delegate technical work.

The monitoring worker may run only wait/status commands for the assigned execution. It must not
connect to databases, write or execute SQL, investigate systems, modify code, prepare environments
or perform operational actions. Read-only access or a slow command does not make a task monitoring.
Do not ask it to launch, retry, cancel or change the underlying execution. That work stays with the
parent or the already-assigned executor.

Start required follow-up without a separate consent question. Honor explicit opt-outs and supplied
deadlines/check caps; otherwise follow until completion, failure, intervention or cancellation.
Do not invent a cutoff. A per-call wait limit does not end monitoring.

If an executor already owns a reliable completion route, keep that route rather than adding another
monitor for its command. Otherwise give the observer an accessible progress/completion source;
another agent's execution session does not automatically transfer. After completion evidence, the
original owner may collect its native terminal result once. Missing access stays a reported gap.

Fix the monitoring objective and completion condition at assignment. Reuse its worker across
checks, requested handbacks and related executions already included in that scope. A command exit
or intermediate report alone does not complete a multi-step monitoring assignment. Use fresh
context for a new assignment outside that scope or after the prior assignment is complete.

- Reuse: observe the build and deployment pipelines already included in one release-follow-up task.
- Fresh context: after one monitoring task finishes, a separately assigned pipeline gets a new worker.

Tell each fresh observer to load this skill. Keep its model and effort across continuations; it
does not delegate its own waiting again. Independent monitoring tasks may have independent workers.

When the parent is only awaiting a child, use a native event-driven wait with a 15-minute timeout
when permitted by current host instructions and the tool schema. Respect any stricter host limit
or earlier supplied deadline. Completion, messages or user input can wake the wait early. Renew
an expired wait without routine updates; do not loop on short mailbox checks or wake the parent
for cache warming. A shorter required wait does not create a reporting obligation.

## Choose how completion arrives

Keep the parent active while awaiting native observer completion. Use an available native route;
do not replace it with heartbeats that repeatedly resume the parent. If native delivery is
unavailable, use an existing deterministic wait tied to the execution. Use supported scheduling
only when these routes cannot meet the required lifetime or return, and state the concrete
limitation. Long duration alone is not such a limitation. Honor explicit scheduling requests.

Do not poll alongside reliable completion delivery. When following a log, include existing
terminal output, avoid read/subscribe gaps and terminate the wait on the matched event or producer
exit; an open-ended tail can remain blocked after completion.

Verify lifetime and return support before yielding. Read the relevant host details:
[Codex](references/codex.md), [Claude](references/claude.md) or [other hosts](references/clients.md).
Proposed schedules and queued messages do not prove active monitoring or parent wakeup.

## Assign the observation directly

Pass the execution identity, its existing log/status source or prescribed wait command, the actual
exit-code/log-event condition, return conditions and applicable access instructions. Explicitly
include the completion-only return contract below and the execution-wide stop condition in the
observer's assignment. Do not request routine snapshots or per-stage reports. Pass intermediate
updates or handbacks only when explicitly requested by the user for this assignment, preserving
their scope and cadence. The observer returns facts; diagnosis, repair and decisions about the
next action remain with the parent. For scheduled checks, include the cadence, timezone and any
supplied deadline/check cap.

Do not require a checkpoint for a simple wait or pass maintenance plans and old prompts. Use
existing monitoring state only when resumption or deduplication needs it.

## Check only when due

Observe the assigned execution once per due check, including visible failures or prompts. Use
native blocking waits or scheduling rather than short model-driven polling. Preserve the execution
identity and attempt. All normal progress stays silent, including changed job counts, jobs starting
or passing, and queue movement. These changes do not themselves require the parent to act.
Missing or failed observations mean uncertainty; report intervention when needed, without repair.

## Finish monitoring and return evidence

Do not call `send_message` to the parent for routine progress. Return once through native final
when the assigned execution completes, fails, or needs parent intervention. Return promptly on
those conditions, even within 15 minutes; the wait timeout is not a minimum delay for a terminal
return. If native return is unavailable, use the verified return route selected above.

A completed stage, new partial results, elapsed time or an expired tool wait does not by itself
authorize a message or final response. Keep observation cadence separate from parent notification
conditions, including when the host requires short waits. The parent does not monitor the same
progress in parallel.

An explicit user request for an update or intermediate handback is an exception. Send only that
requested update and keep observing without acknowledgment; use an interim native final only
when the request actually asks to hand control back. Never duplicate a native return with a
manual send.

If a final reports only normal progress and monitoring is still required, the parent resumes the
same observer at once with the original stop condition. If the observer cannot continue reliably,
use a replacement or the verified fallback. Do not take over routine polling.

Return identity, observed time/state, exit code or matched event and concise evidence. Uncertain
delivery requires read-back/deduplication or an uncertainty report, never a blind resend or restart.
On completion, failure, deadline, intervention or cancellation, deactivate only the owned schedule,
if any, and verify inactivity. Stopping monitoring does not cancel the execution. The parent checks
identity/freshness and decides its next authorized action; the observer does not continue the work.
