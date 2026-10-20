# GitLab monitor work ownership

**Status:** Superseded by the implemented [simple queue](gitlab-monitor-simple-queue.md).
Retained as the historical contract of the predecessor. Its state/chats are not migrated into the
fresh consumer; the latest explicit user decision selected new chats and a separate queue.

## Context and decision

A completed automatic review releases its MR owner. A later explicit human request needs a new
round, with its own provenance and scope, rather than borrowing a completed automatic event.
The standalone [monitor](../.local/bin/codex-session-stats) owns this transition, its private state
and the shared instruction source for old and new chats.

## Trust and semantic boundary

Authenticate the exact native user text and active turn in the mapped MR chat. Trusted local
clients may use the native user channel; all automation admitted by the monitor must register
its provenance. Native history does not distinguish an unregistered local textual injection from
a physical human. clientId, Boolean payload fields and verb matching are not human-origin proofs.
The agent decides whether authenticated text is an explicit executable request and identifies its
bounded scope. The control requires that decision and its exact native basis; questions,
explanations, preferences, registered automation and mixed monitor/user input grant no new owner.
Preserve the question-mark and trailing-w gate.

## Ownership and queue flow

Automatic claim requires its exact registered automatic delivery. A human start uses an explicit
resume mode and creates an immutable request identity, source digest, scope and link to the prior
round. Its queue ticket shares transactional capacity and FIFO with automatic work. Keep separate
requests separate; code-event coalescing must not cancel or absorb a human ticket.

**Approved amendment, in implementation:** Ownership, observations and effects are scoped by
GitLab repository identity and MR number. Repository namespaces share one global queue and
capacity authority. Exact native human source identity survives storage-schema migration; old
callbacks retain only their authenticated original repository mapping. The rule above stays in
force until this amendment is implemented. Current single-repository storage remains available
until explicit verified migration. Removing a repository blocks new admission after current
configuration validation; previously admitted bounded operations retain their settlement path.

The pending amendment also applies to effect routing and shared instruction delivery below.
Migration must preserve stored source envelopes, receipts, holds and historical bootstrap bytes;
it cannot create new human authorization or advance an unrelated code checkpoint.

Immediate execution creates a new generation and owner in the same transaction as reservation.
When capacity is busy, persist authorization and end the human turn. Deferred execution proves
the original human source and an exact registered human-continuation delivery in the same chat.
A real delivery attempt is distinct from an automatic code-review event. Repetition preserves
identity and cannot broaden scope or reacquire a completed request.

A pause keeps the interrupted human request and scope. Only the existing later sufficient-answer
route releases it. New-round registration cannot clear a pause, recovery requirement, conflicting
owner or uncertain effect. Workspace adoption and project selection cannot transfer pending human
work to another native source.

## Effects, completion and failure semantics

Human effects must fit the recorded effect kinds and discussion targets. Keep the common native
identity, generation, head/discussion snapshot, authenticated actor, intent, receipt, deduplication
and complete concern-assessment gates. Closed or merged MRs permit no new effects. A human
request to resolve does not replace the verified-fix or verified-bot-false-positive criteria.

Event-free human completion records its own outcomes and settled receipts, releases its owner and
marks the reservation disposition. It preserves the automatic reviewed-head checkpoint,
automatic concerns and completed history. Native terminal observation frees capacity; an
unfinished terminal round remains recovery-required. Lost acknowledgements remain uncertain
until exact native evidence reconciles them. Operator recovery requeues the same authorization
only after the former execution is terminal and public effects are settled; it never fabricates
an automatic event or blindly republishes an uncertain operation.

## Instruction delivery and publication

One canonical instruction producer feeds new bootstraps and read-only status for mapped existing
chats. Preserve stored bootstrap text and native history, so exact older provenance remains valid.
An ownerless effect diagnostic points to status and never acquires ownership implicitly.
Stage a new executable outside the live path through checks and selected review. The operator
lock blocks scheduled dispatch, not existing callbacks. Publish only tested complete bytes
atomically, preserving executable ownership/mode and protected configuration.

## Acceptance and traceability

The authoritative [monitor tests](../scripts/tests/test_codex_gitlab_monitor.py) exercise production
controls and state schema with external native/provider boundaries substituted. Required evidence
covers post-complete start, scoped intent/receipt, FIFO contention, exact continuation, existing
hold resumption, terminal recovery, repetition, question/automation/mixed denials and changed
context. The incident capture supports a partial artifact replay, not a full native session or
real provider-write claim. Deterministic validation must reject unexpected external interactions.

| Invariant | Runtime owner and consumers | Executable protection |
| --- | --- | --- |
| Native source and bounded intent | Human validation, resume, shared instructions | Human request registration and denial cases; partial incident replay |
| One generation and FIFO reservation | State transaction, enqueue/reserve, dispatch and native reconciliation | Immediate, busy, contention and tail/restart cases |
| Immutable request and preserved holds | Pause/resume, adoption/selection and recovery | Human pause/answer, scope and context cases |
| Scoped and reconciled effects | Common effect intent/receipt and resolution assessment | Scope, snapshot, deduplication, resolution and closure denials |
| Independent human completion | Complete, queue disposition and operator recovery | Empty-event checkpoint/history and repeat/recovery cases |
| Repository identity (pending amendment) | Project resolver, scoped state and global queue admission | Required equal-number isolation, migration and stale-configuration cases |
| Shared current protocol | Canonical producer, bootstrap, status and diagnostics | Old/new chat CLI discovery and preservation cases |

## Alternatives and risks

Reusing a completed automatic event would forge provenance and advance unrelated code work.
Implicit ownership in effect-intent would bypass explicit scope and FIFO. A separate queue would
split capacity authority. Requiring another chat or repeated sufficient authorization would lose
continuity. Positive physical-human ingress would need an additional trusted runtime capability;
it is outside the retained local-client boundary. Semantic classification and concern completeness
remain agent judgments; deterministic controls authenticate their inputs and constrain their effects.
