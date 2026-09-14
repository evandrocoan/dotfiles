# Implementation plan: <task>

**Status:** Planned
**Mode:** Plan only | Plan and execute

Use this full template for high-risk or architecture-governed work. Use
`compact-implementation-plan-template.md` for persistent non-trivial local and reversible work.

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
- Name the objective high-risk or architecture trigger that requires this full template.

## Current evidence and assumptions

### Verified evidence

- Record the authenticated current behavior or failure and point to its authoritative artifact.

### Open assumptions

- Mark every unverified fact that could change the execution route.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| pending | Obtain any risk-required review. <review owner> | <why this review level applies> | <concise findings under **Plan review**> |
| pending | Reproduce or authenticate. <boundary> | <non-obvious premise and proof, or `None`> | <specific check> |
| pending | Change the authoritative owner and affected consumers. | <non-obvious premise and proof, or `None`> | <specific check> |
| pending | Integrate and remove competing behavior. <boundary> | <non-obvious premise and proof, or `None`> | <specific check> |
| pending | Run proportional checks and audit. <complete flow> | <non-obvious premise and proof, or `None`> | <commands or concise final evidence> |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`.

Record a premise only when it is material and non-obvious. Write it before starting the dependent
step. An unverified material premise stays under **Open assumptions** and blocks that step. Keep
table cells concise; store decisive evidence and final results, not a chronological command diary.

## Plan review

Record the risk-appropriate pre-execution review before the first implementation step runs. Update
this section if the plan is reviewed again after a material replan.

- **Risk classification:** High risk. Give the objective reason.
- **Mechanism:** Advisor and independent reviewer | Independent reviewer with advisor unavailable.
- **Independent reviewer:** Opened | Unavailable on this client. State the high-risk condition,
  whether its model differs from the advisor, or the explicit user decision that pins the same
  model. Same-model review must disclose correlated blind-spot risk.
- **Applied:** List each finding that changed the plan and what changed.
- **Rejected:** List each finding that was not applied and the reason.

## Replan conditions

- List discoveries that invalidate the current execution route or require an architecture decision.

## Completion evidence

- Record concise final evidence and unresolved limitations without adding a chronological run log.

## Closure audit

Perform the skill's risk-appropriate reread before completing these rows. Add concise rows until
every outcome, scope boundary, invariant, affected consumer, replan condition, and required
validation obligation is accounted for. A passing test supports only what it actually asserts.

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| pending | <one requirement or safely grouped family> | <implementation owner and consumers> | <concise implementation plus validation evidence> |

Use only `verified`, `not applicable: <reason>`, and `unresolved: <reason>` for final row statuses.
Use `not applicable` only when approved scope or governing authority objectively excludes the
requirement; unavailable or skipped required evidence is `unresolved`. The plan cannot become
`Completed` while a row is `pending` or `unresolved`.

Record both closure directions:

- Architecture to implementation: every governing invariant reaches an implementation owner,
  every affected consumer, and proportional executable protection.
- Implementation to authority: every changed runtime, configuration, test, fixture, and durable
  document is authorized by this plan and a governing invariant or explicit local objective.

Record the required independent second pass and apply the skill's material-change rule when
something changes after the verdict.

### Final conformance verdict

- **Verdict:** Pending | Passed | Failed
- **Second pass:** Pending | Independent
- **Auditor and evidence:** Identify the reviewer and link the final diff, validation artifacts,
  and completed matrix used for the verdict.
- **Unresolved requirements:** List each unresolved row, or write `None` only after confirming the
  matrix contains no `pending` or `unresolved` status.

Set `Verdict` to `Passed` only when both trace directions are complete, every required validation
has run, the second pass is complete, and unresolved requirements are `None`. Only then may the
plan status become `Completed`.
