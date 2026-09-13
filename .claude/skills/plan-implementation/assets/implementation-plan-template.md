# Implementation plan: <task>

**Status:** Planned
**Mode:** Plan only | Plan and execute

## Outcome

State the observable result and terminal condition.

## Scope

### In scope

- Name the authorized behavior and affected boundary.

### Out of scope

- Name adjacent behavior that must remain unchanged.

## Governing decisions and invariants

- Link the approved architecture, product decision, schema, or runtime authority.
- State only the invariants needed to constrain this implementation.

## Current evidence and assumptions

### Verified evidence

- Record the authenticated current behavior or failure and point to its authoritative artifact.

### Open assumptions

- Mark every unverified fact that could change the execution route.

## Execution steps

| Status | Step | Affected owner and consumers | Premise and how it was verified | Validation |
| --- | --- | --- | --- | --- |
| pending | Obtain review of this plan before starting. | <the review mechanism the client offers, plus an independent reviewer when the skill requires one and the client can open it> | <the plan is complete and every premise is named> | <findings recorded under **Plan review**, each applied or rejected with a reason> |
| pending | Reproduce or authenticate the current behavior. | <boundary> | <premise and the artifact that proves it> | <specific check> |
| pending | Change the authoritative owner. | <owner and consumers> | <premise and the artifact that proves it> | <specific check> |
| pending | Integrate and remove competing behavior. | <boundary> | <premise and the artifact that proves it> | <specific check> |
| pending | Run proportional checks. | <test boundary> | <premise and the artifact that proves it> | <commands or artifacts> |
| pending | Audit and deliver. | <complete flow> | <premise and the artifact that proves it> | <completion evidence> |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`.

Every step states the premise it depends on and the artifact that proves it. A premise is what must
already be true for the step's result to mean what the step claims, such as what a passing test
actually measures. Write the premise before starting the step, not after. When it cannot be named or
has not been verified, the step does not start: record it under **Open assumptions** and verify it
first. A step built on an unverified premise produces work that must be discarded when the premise
turns out to be false.

## Plan review

Record the pre-execution review before the first step runs. Update this section if the plan is
reviewed again after a material replan.

- **Mechanism:** Name what reviewed the plan, such as the advisor in Claude Code, the closest review
  mechanism another client offers, or a self-reviewed full reread when the client offers none.
- **Independent reviewer:** Not required | Opened | Unavailable on this client. State the condition
  from the skill that required it.
- **Applied:** List each finding that changed the plan and what changed.
- **Rejected:** List each finding that was not applied and the reason.

## Replan conditions

- List discoveries that invalidate the current execution route or require an architecture decision.

## Completion evidence

- Record concise final evidence and unresolved limitations without adding a chronological run log.

## Closure audit

Reread this plan, every governing architecture record, coupled repository instructions, the final
implementation, and its validation artifacts in full before completing these rows. Add rows until
every outcome, scope boundary, non-goal, invariant, execution step, affected consumer, replan
condition, and required validation obligation is accounted for. A passing test may support only the
behavior it actually asserts.

| Status | Requirement source | Requirement | Implementation evidence | Validation evidence |
| --- | --- | --- | --- | --- |
| pending | <plan or architecture section> | <one requirement or one safely grouped family> | <owner and consumers> | <test, replay, CI, or operational artifact> |

Use only `verified`, `not applicable: <reason>`, and `unresolved: <reason>` for final row statuses.
Use `not applicable` only when approved scope or governing authority objectively excludes the
requirement; unavailable or skipped required evidence is `unresolved`. The plan cannot become
`Completed` while a row is `pending` or `unresolved`.

Record both closure directions:

- Architecture to implementation: every governing invariant reaches an implementation owner,
  every affected consumer, and proportional executable protection.
- Implementation to authority: every changed runtime, configuration, test, fixture, and durable
  document is authorized by this plan and a governing invariant or explicit local objective.

For persistent or architecture-governed work, record the second conformance pass and whether it was
independent or self-reviewed. Any change after this audit invalidates the closure verdict and
requires a complete final reread and renewed audit.

### Final conformance verdict

- **Verdict:** Pending | Passed | Failed
- **Second pass:** Pending | Independent | Self-reviewed
- **Auditor and evidence:** Identify the reviewer and link the final diff, validation artifacts,
  and completed matrix used for the verdict.
- **Unresolved requirements:** List each unresolved row, or write `None` only after confirming the
  matrix contains no `pending` or `unresolved` status.

Set `Verdict` to `Passed` only when both trace directions are complete, every required validation
has run, the second pass is complete, and unresolved requirements are `None`. Only then may the
plan status become `Completed`.
