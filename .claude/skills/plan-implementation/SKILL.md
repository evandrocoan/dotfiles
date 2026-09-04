---
name: plan-implementation
description: "Turn an approved objective, bug diagnosis, or architecture record into a concrete, testable execution plan and keep implementation aligned with it. Use when the user asks for an implementation plan, asks to implement a non-trivial multi-file or multi-stage change, requests a plan for approval, or when an architecture record is moving into implementation. Also use before costly live validation, migrations, protocol changes, or fixes whose correctness depends on coordinated code, tests, replay, configuration, or documentation."
---

# Plan implementation

Create the smallest plan that makes the requested delivery reliable. Keep durable design
authority in architecture records and keep temporary execution state in the task, issue, or merge
request.

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

## Inspect before planning

Read the applicable repository instructions and inspect the authoritative code, configuration,
tests, and existing records before choosing implementation steps. Do not create a plan from
filenames, issue prose, or remembered architecture alone.

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
9. Audit the final runtime flow and repository diff against the outcome and invariants.

Combine steps when separating them would create meaningless bookkeeping. Split a step when it
contains more than one independently falsifiable outcome. Keep at most one step in progress, and
update statuses to reflect reality rather than intent.

For parallelizable work, group only tasks with no shared mutable files, state, generated artifacts,
expensive local resources, or causal dependency. Never parallelize merely to make a plan appear
faster.

## Keep planning state in the correct place

Use the task's plan mechanism for transient execution tracking. Use an issue or merge request when
the plan must be shared across people or sessions. Write a repository plan file only when the user
explicitly requests one or the repository has an established non-architecture convention for it.

Never store task status, completed-step narration, timestamps, run-by-run cost, mutable commit
identifiers, or raw logs in an architecture record. A proposed architecture record may contain only
the minimum implementation order needed to constrain the design and its architectural acceptance
criteria.

After implementation, close the transient plan. Preserve durable rationale and invariants in their
authoritative record, executable expectations in tests and fixtures, and operational evidence in
the issue, merge request, replay, or CI artifact that owns it.

## Replan without changing authority

Replan immediately when:

- an inspected fact contradicts a material assumption;
- an affected consumer or source of authority was omitted;
- the planned test cannot distinguish the defect from unrelated failure;
- an unexpected dependency, destructive action, external mutation, or scope expansion is required;
- user-owned concurrent changes overlap the planned edit;
- validation demonstrates that the chosen implementation violates an invariant;
- cost, quota, or operational state makes the remaining validation predictably wasteful.

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

## Completion gates

Do not mark the plan complete until all applicable gates pass:

- The requested outcome exists in the authoritative runtime path.
- Every affected consumer uses the updated contract.
- No legacy or fallback path preserves the superseded meaning.
- Focused protection fails for the intended reason without the fix and passes with it.
- Required integration, replay, and broader checks have completed or are reported explicitly as
  unavailable.
- The final diff contains no unrelated user-owned changes.
- Documentation and architecture records are synchronized only where their owned behavior changed.
- Remaining limitations, skipped validation, live cost, and operational uncertainty are reported
  accurately.

If implementation is incomplete, leave the corresponding step pending or in progress and state the
concrete blocker. Never convert an unfinished plan into a successful handoff by weakening its
acceptance criteria.

## Compact plan format

Use a concise form unless the task needs more detail:

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
