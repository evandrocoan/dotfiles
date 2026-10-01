# Implementation plan: <task>

**Status:** Planned
**Mode:** Plan only | Plan and execute

Recommend this full template for high-risk or architecture-governed work; honor the user's chosen
detail, including a shorter plan. Use `compact-implementation-plan-template.md` for local work or
for a qualifying **Bounded additive external action**. A **Routine external editorial correction**
uses the compact template only when another persistence trigger applies, as defined in `SKILL.md`.

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
- Name the objective high-risk or architecture reason for recommending this full template.

## Current evidence and assumptions

### Verified evidence

- Record the authenticated current behavior or failure and point to its authoritative artifact.

### Open assumptions

- Mark every unverified fact that could change the execution route.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| pending | Obtain any selected pre-edit review. <review owner> | <user choice and review purpose> | <concise findings, or `Not selected`> |
| pending | Present the current plan link and explanatory summary in chat; in plan-and-execute mode, wait for an explicit go-ahead before implementation. <owner> | <complete current plan is accessible through the link> | <presentation and user response, or `Pending`> |
| pending | Reproduce or authenticate. <boundary> | <non-obvious premise and proof, or `None`> | <specific check> |
| pending | Change the authoritative owner and affected consumers. | <non-obvious premise and proof, or `None`> | <specific check> |
| pending | Integrate and remove competing behavior. <boundary> | <non-obvious premise and proof, or `None`> | <specific check> |
| pending | Run proportional checks and any selected review or audit. <complete flow> | <non-obvious premise and proof, or `None`> | <commands or concise final evidence> |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`.

Record a premise only when it is material and non-obvious. Write it before starting the dependent
step. An unverified material premise stays under **Open assumptions** and blocks that step. Keep
table cells concise; store decisive evidence and final results, not a chronological command diary.
For a material new or changed execution route, record one binding under **Governing decisions and
invariants** or **Current evidence and assumptions**: user authorization or explicit repository
mandate, existing workflow examined, applicable skills, chosen route, and any blocker. Dependent
steps may refer to that binding; do not repeat an approval check for every file.

## Plan review

Record a selected pre-execution review before its dependent implementation step. If none was
selected, record `Not selected`; do the author evidence check. Update this section if the user
selects a new review after a material replan.

- **Risk classification:** High risk. Give the objective reason.
- **Mechanism:** Not selected | Advisor | Independent reviewer | Both.
- **Independent reviewer:** Not selected | Opened | Selected but unavailable. State the reason,
  whether its model differs from the advisor, or the explicit user decision that pins the same
  model. Same-model review must disclose correlated blind-spot risk.
- **Applied:** List each finding that changed the plan and what changed.
- **Rejected:** List each finding that was not applied and the reason.

## User review before implementation

- **Advance choice to create the plan:** <explicit user request or affirmative response before
  creation>. A declined plan leads to the direct route after approval of the chat summary, with the
  same independent safeguards.
- **Advance choice for separate reviews:** <named advisor and reviewers, scope, and user response
  before each invocation, or `None selected`>. One answer may cover named phases;
  consent alone does not establish the active reviewer setting or a passing verdict.
- **Plan and summary offered in chat:** Pending | <current plan link, summary explaining the problem,
  intended changes, how they solve it, expected result and checks, plus plan line and word counts>.
- **User response:** Pending | <explicit go-ahead for this contract> | Plan only; implementation
  requires a later instruction. The initial task request and silence are not review.
- **Material revision:** None | <updated link and summary, and renewed approval before affected steps>.

## Replan conditions

- List discoveries that invalidate the current execution route or require an architecture decision.

## Completion evidence

- Record concise final evidence and unresolved limitations without adding a chronological run log.

## Closure audit

Include this section only when the user selected a full audit; choosing a plan alone does not
select it. Otherwise omit the matrix and report proportional completion evidence above.
For a selected audit, use its agreed scope and reviewer before completing these rows. Add rows until
every outcome, scope boundary, invariant, affected consumer, replan condition, and required
validation obligation is accounted for. A passing test supports only what it actually asserts.

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| pending | Advance user choices preceded new plan creation and separate review invocations; legacy actions retain their true chronology. | Plan and review steps | <request or response, timing, and any later uncovered action> |
| pending | The current plan and explanatory summary were presented in chat and the user explicitly released implementation. | User review and execution steps | <presentation, response, and material-revision check> |
| pending | <one requirement or safely grouped family> | <implementation owner and consumers> | <concise implementation plus validation evidence> |

Use only `verified`, `not applicable: <reason>`, and `unresolved: <reason>` for final row statuses.
Use `not applicable` only when approved scope or governing authority objectively excludes the
requirement; unavailable or skipped required evidence is `unresolved`. The plan cannot become
`Completed` while a row is `pending` or `unresolved`.

Record both closure directions:

- Architecture to implementation: every governing invariant reaches an implementation owner,
  every affected consumer, and proportional executable protection.
- Implementation to authority: every changed file and observed effect, including new files, traces
  through user authorization, applicable instructions and skills, this plan, and a governing
  invariant or explicit local objective.

Record any selected second pass; do not add an author second reading as a fallback,
and apply the skill's material-change rule when something changes after the verdict.

### Final conformance verdict

- **Verdict:** Pending | Passed | Failed
- **Second pass:** Not selected | Pending | Independent | Author pass explicitly selected
- **Auditor and evidence:** Identify the reviewer and link the original user request and decisions,
  applicable instructions and skills, final diff and effects, validation artifacts, and completed
  matrix used for the verdict.
- **Unresolved requirements:** List each unresolved row, or write `None` only after confirming the
  matrix contains no `pending` or `unresolved` status.
- **Brief check:** No brief on this subject | No `registro pendente`; open items reported and noted:
  <items, or `None`>.

For a selected full audit, set `Verdict` to `Passed` only when its chosen scope and both trace
directions are complete, required validation has run, the user reviewed the plan before execution,
any selected second pass is complete, and no applicable requirement is unresolved. A selected audit
holds its dependent phase until completed or explicitly withdrawn. An unselected audit or second
pass does not block plan completion; record only the verification and reviews actually performed.
