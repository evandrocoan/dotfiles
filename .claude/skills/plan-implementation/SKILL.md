---
name: plan-implementation
description: "Turn an approved objective, bug diagnosis, or architecture record into a concrete, testable execution plan and keep implementation aligned with it. Use when the user asks for an implementation plan, asks to implement a non-trivial multi-file or multi-stage change, requests a plan for approval, or when an architecture record is moving into implementation. Also use before costly live validation, migrations, protocol changes, or fixes whose correctness depends on coordinated code, tests, replay, configuration, or documentation. Require a user-visible persistent Markdown plan when work may span phases, agents, interruptions, or context compaction."
---

# Plan implementation

Create the smallest plan that makes the requested delivery reliable. Keep durable design
authority in architecture records. Keep every formal plan user-visible. When the persistence gate
applies, keep detailed execution state in Markdown and project its current steps into the task
plan.

## Determine the planning mode

Classify the request before editing:

- **Plan only:** When the user asks for a plan, asks to review or approve a plan, or explicitly
  says not to implement, inspect enough authoritative evidence to make the plan credible and stop
  after presenting it.
- **Plan and execute:** When the user asks to change, fix, build, or implement, create the plan and
  continue through it without requesting separate approval for routine in-scope steps.
- **No formal plan:** Skip a formal plan only for an obvious, low-risk, single-step change whose
  implementation and validation are both local. Still identify the expected outcome and verify it.

Use a formal plan whenever work crosses component boundaries, changes a protocol or state
transition, has several dependent stages, requires a migration or replay, consumes paid
validation, or has material uncertainty about scope.

## Materialize the plan visibly

Never keep a formal plan only in hidden reasoning or conversation memory. Materialize it in the
task's visible plan mechanism, or present it directly when no such mechanism exists, before editing
production code.

Use these two layers when the persistence gate applies:

- **Persistent execution plan:** Store the complete current execution contract in Markdown.
- **Task plan:** Project the current steps and statuses into the environment's visible plan
  mechanism for concise progress tracking.

The persistent plan is mandatory when any of these conditions applies:

- work is likely to cross context compaction, an interruption, a handoff, or more than one session;
- multiple agents or people may act on the plan;
- several dependent phases or cross-component consumers must remain coordinated;
- the task implements or materially audits an architecture record;
- migration, recorded replay, end-to-end validation, paid validation, or external mutation is
  required;
- losing a constraint, non-goal, authenticated fact, or validation obligation could produce an
  incorrect delivery.

When the repository defines a current implementation-plan convention, follow it. Otherwise, for
repository-backed work, create:

```text
implementation-plans/active/<task-slug>.md
```

Use `assets/implementation-plan-template.md` as the starting structure. Use a concise lowercase
hyphenated task slug. Keep one active file for one delivery objective; do not create a new file for
every retry or replanning event.

When no repository exists, use another durable user-visible Markdown artifact that every acting
agent can reopen. An issue or merge-request description may replace the local file only when it is
the established execution authority and all agents can read and update it. A chat message or hidden
model state never replaces the persistent plan.

Apply this authority order:

```text
approved architecture or product decision
        -> persistent implementation plan
        -> task-plan status projection
        -> conversational progress update
```

Resolve disagreement by correcting the lower layer. Never let the task-plan projection silently
override the persistent plan or let the persistent plan override approved architecture.

## Inspect before planning

Read the applicable repository instructions and inspect the authoritative code, configuration,
tests, and existing records before choosing implementation steps. Do not create a plan from
filenames, issue prose, or remembered architecture alone.

Inspect enough evidence to create a truthful initial plan, then materialize the plan before the
first production edit. Mark unresolved facts as assumptions or investigation steps instead of
inventing implementation details.

When a durable architecture record governs the change, use `architecture-records` together with
this skill. Treat the approved record as the design authority and derive the implementation plan
from it. Do not alter the record to legitimize incidental current code.

Load the task-specific skills required by the work before planning their stages. In particular,
use `test-quality` for executable validation, `documentation` for durable documentation,
`dependency-decisions` for dependency choices, and the relevant delivery or infrastructure skill
when those concerns are in scope.

## Establish the execution contract

Record these elements before implementation:

1. **Outcome:** State the externally observable result and the terminal condition for the task.
2. **Scope and non-goals:** Bound the authorized change and name nearby behavior that must remain
   unchanged.
3. **Authorities and invariants:** Identify the architecture record, schema, configuration,
   runtime owner, or other source that constrains the implementation.
4. **Current evidence:** Summarize the verified failure or current behavior. Mark assumptions that
   remain unverified.
5. **Work sequence:** Divide the change into ordered, independently checkable slices.
6. **Validation:** Bind each material slice to focused protection and bind the completed flow to
   proportional integration, replay, end-to-end, or operational validation.
7. **Replanning conditions:** State the discoveries that would invalidate the current route.

Do not use vague steps such as “fix the logic,” “add tests,” or “verify everything.”
Name the behavior boundary, the affected owner or consumer, and the evidence that will prove the
step complete. Mention exact paths or symbols only after inspecting them; do not invent locations
to make a plan look concrete.

## Build an executable sequence

Order work by dependency and feedback speed:

1. Reproduce or authenticate the current failure when one exists.
2. Establish or update the smallest failing regression protection.
3. Change the authoritative owner of the behavior.
4. Update every affected consumer of that contract.
5. Remove competing or superseded behavior rather than leaving parallel authority.
6. Run focused checks after the smallest meaningful slice.
7. Run broader integration, replay, and suite-level checks after the flow is connected.
8. Perform operational or paid live validation only when it is useful and authorized under the
   applicable rules.
9. Perform the mandatory closure audit against the complete plan, governing architecture, actual
   runtime flow, repository diff, and validation evidence.

Combine steps when separating them would create meaningless bookkeeping. Split a step when it
contains more than one independently falsifiable outcome. Keep at most one step in progress, and
update statuses to reflect reality rather than intent.

For parallelizable work, group only tasks with no shared mutable files, state, generated artifacts,
expensive local resources, or causal dependency. Never parallelize merely to make a plan appear
faster.

When a persistent plan exists, reread it before starting each new phase and confirm that its
prerequisites are complete. After context compaction, interruption, session restart, or agent
handoff, reread the entire plan before acting. Give every delegated agent the plan path and the
exact step it owns.

## Keep planning state in the correct place

When the persistence gate applies, treat the persistent plan as the sole current authority for
execution detail. Keep it compact and current; do not append a chronological diary. Update it only
when status, scope, evidence, dependencies, validation obligations, blockers, or the chosen
execution route materially changes.

Mirror its executable steps into the task's plan mechanism. The task plan may be shorter, but it
must not omit a material pending phase or report a status that conflicts with the persistent file.
The user must be able to see the plan path and every status transition.

Do not commit the plan merely because it exists. Follow the user's requested Git outcome and the
repository convention. Report whether the plan is tracked or untracked. Keep it available through
handoff; remove or archive it only when the user requests that action or an established repository
lifecycle requires it.

Never store task status, completed-step narration, timestamps, run-by-run cost, mutable commit
identifiers, or raw logs in an architecture record. A proposed architecture record may contain only
the minimum implementation order needed to constrain the design and its architectural acceptance
criteria.

After implementation, close the execution plan. Preserve durable rationale and invariants in their
authoritative record, executable expectations in tests and fixtures, and operational evidence in
the issue, merge request, replay, or CI artifact that owns it.

Do not store chain-of-thought, speculative internal reasoning, raw prompts, secrets, or copied logs
in the plan. Store verified facts, explicit assumptions, decisions, dependencies, and observable
validation results.

## Replan without changing authority

Replan immediately when:

- an inspected fact contradicts a material assumption;
- an affected consumer or source of authority was omitted;
- the planned test cannot distinguish the defect from unrelated failure;
- an unexpected dependency, destructive action, external mutation, or scope expansion is required;
- user-owned concurrent changes overlap the planned edit;
- validation demonstrates that the chosen implementation violates an invariant;
- cost, quota, or operational state makes the remaining validation predictably wasteful.

Update the persistent plan before taking a materially different implementation route. Preserve the
current outcome and governing invariants, replace superseded steps instead of appending a narrative,
and synchronize the task-plan projection.

Change only the execution plan when the approved design remains valid. Amend or supersede the
architecture record first when ownership, authority, stage order, terminal meaning, recovery policy,
or another durable invariant must change. Stop and request direction when that design change
exceeds the user's authorization.

Do not preserve a failed approach as a second runtime path. Record the new current step, retain
useful authenticated evidence, and remove the superseded implementation before completion.

## Plan validation proportionally

Every plan that changes executable behavior must say how the change can fail and which check
detects that failure. Use the `test-quality` skill to design or modify tests.

Prefer this validation progression when applicable:

- a focused regression that fails for the observed reason before the fix;
- unit or property tests for local invariants and malformed boundaries;
- integration tests across changed producers and consumers;
- a faithful recorded replay for a real cross-component incident when sufficient raw interactions
  exist;
- an end-to-end or live run for behavior that hermetic evidence cannot prove;
- the repository's complete required suite before claiming full validation.

Include timeout, retry, duplicate-event, partial-progress, and terminal-failure cases when the
changed contract owns them. Do not replace a required integral replay with parser-only fixtures,
and do not label partial coverage as end to end.

Keep paid or externally mutating scenarios sequential unless the applicable policy explicitly
requires otherwise. Measure the complete scenario rather than hiding retries or nested commands.

## Perform the mandatory closure audit

Treat closure as a separate blocking phase, not as a summary written from memory. After the
candidate implementation and required validation are complete:

1. Reread the entire persistent implementation plan from its first line through its final
   conformance-verdict section. Reread every governing architecture record and coupled repository
   instruction file in full. Do not rely on a prior summary, the changed sections, task-plan labels,
   or remembered intent.
2. Reconstruct the implemented runtime path from code, configuration, tests, fixtures, and actual
   validation artifacts. A report that a command passed is evidence only for what that command
   asserted.
3. Expand and complete the plan's closure-audit matrix. Account individually for every outcome,
   in-scope boundary, non-goal, governing invariant, execution step, affected consumer, replan
   condition, and required validation obligation. Group entries only when they share the same owner,
   failure mode, and evidence; never group distinct terminal or recovery paths merely to shorten the
   table.
4. Trace both directions:

   ```text
   architecture invariant -> implementation-plan step -> code/config owner -> consumers -> test/replay
   changed code/config/test -> authorized plan scope -> governing invariant or explicit local objective
   ```

   The forward trace detects omitted implementation. The reverse trace detects unauthorized work,
   accidental new architecture, and tests that validate behavior outside the approved objective.
5. Mark each matrix row `verified`, `not applicable` with a concrete reason, or `unresolved`.
   Use `not applicable` only when the approved scope and governing authority objectively exclude
   the requirement. Missing evidence, unavailable or skipped required validation, an unexamined
   consumer, cost, time, or an unexplained scope addition is `unresolved`; it is never implicitly
   satisfied by another passing row.
6. For persistent, architecture-governed, protocol, migration, replay, or cross-component work,
   perform a second conformance pass after the implementer's pass. Use a separate agent with fresh
   task context when one is available, giving it the plan, governing records, final diff, and
   validation artifacts without the intended verdict. Otherwise perform a separate full reread and
   report that the second pass was self-reviewed rather than independent.
7. If either pass finds a mismatch, reopen the affected execution steps, correct the lowest
   incorrect authority, rerun invalidated validation, and repeat the complete closure audit. Do not
   append an exception that permits completion.

Store the concise matrix and final conformance verdict in the persistent implementation plan.
Store detailed command output, costs, raw logs, and replay events in their executable or operational
artifacts and link them; do not copy them into the plan or architecture record.

Any change after the closure audit to an in-scope or coupled artifact—including code,
configuration, tests, fixtures, plans, architecture records, repository instructions, or user
documentation—invalidates the closure verdict. Reread the complete final plan and governing
records, recheck every row, rerun all checks invalidated by the change, and issue a new closure
verdict before completion.

## Completion gates

Do not mark the plan complete until all applicable gates pass:

- The requested outcome exists in the authoritative runtime path.
- Every affected consumer uses the updated contract.
- No legacy or fallback path preserves the superseded meaning.
- Focused protection fails for the intended reason without the fix and passes with it.
- Required integration, replay, and broader checks have completed. An unavailable required check
  remains unresolved and blocks completion unless the governing authority changes its requirement.
- The final diff contains no unrelated user-owned changes.
- Documentation and architecture records are synchronized only where their owned behavior changed.
- Remaining limitations, skipped validation, live cost, and operational uncertainty are reported
  accurately.
- The persistent plan and task-plan projection agree on every material terminal status.
- The closure-audit matrix contains no `pending` or `unresolved` row and cites current evidence for
  every applicable requirement.
- The architecture-to-implementation and implementation-to-authority traces are both complete.
- The required second conformance pass found no unresolved omission, contradiction, unauthorized
  behavior, or unprotected failure path.

If implementation is incomplete, leave the corresponding step pending or in progress and state the
concrete blocker. Never convert an unfinished plan into a successful handoff by weakening its
acceptance criteria.

## Compact plan format

Use the bundled template for a persistent file. For a formal task-plan projection or a plan that
does not meet the persistence gate, use this concise form:

```text
Outcome: <observable result>
Constraints: <invariants, non-goals, and authorization boundaries>
Evidence: <verified current behavior and open assumptions>

1. <reproduce or authenticate> — validation: <specific check>
2. <change authoritative owner> — validation: <specific check>
3. <update affected consumers> — validation: <specific check>
4. <integrate and replay> — validation: <specific check>
5. <audit and deliver> — validation: <specific check>

Replan if: <material invalidating conditions>
```

Expand the plan only when additional detail changes how the implementation will be performed or
validated.
