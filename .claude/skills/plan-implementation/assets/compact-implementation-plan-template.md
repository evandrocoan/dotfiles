# Implementation plan: <task>

**Status:** Planned
**Mode:** Plan only | Plan and execute
**Risk:** <classification from the skill; a compact format does not lower it>

Use this compact persistent template when the user chooses a plan for non-trivial local and
reversible criteria, **Bounded additive external action**, or **Routine external editorial
correction** with a persistence trigger in `SKILL.md`.
For high risk, recommend `implementation-plan-template.md`; use this shorter format if the user
prefers it. A chosen plan does not also select a full audit or second pass.
Delete the conditional external-action section for local work.

## Outcome and scope

- Outcome: <observable result and terminal condition>.
- In scope: <authorized owner and consumers>.
- Out of scope: <adjacent behavior that remains unchanged>.
- Authority: <governing decision, configuration, schema, local objective, and relevant invariants>.

## Evidence and assumptions

- Verified: <current behavior or failure and authoritative artifact>.
- Open assumption: <material unverified premise, or `None`>.

## User review before implementation

- Advance choice to create this plan: <explicit user request or affirmative response before
  creation>.
- Advance choice for separate reviews: <named advisor/reviewer, scope, and user response before
  invocation, or `None selected`>. A legacy plan preserves earlier chronology and
  asks before future uncovered material replanning or review.
- Plan and summary offered in chat: Pending | <current plan link, summary explaining the problem,
  intended changes, how they solve it, expected result and checks, plus plan line and word counts>.
- User response: Pending | <explicit go-ahead for this contract> | Plan only; implementation
  requires a later instruction. The initial task request and silence are not review.
- Material revision: None | <updated link and summary, and renewed approval before affected steps>.

## External action

- Authorization binding: <approved destination, operation, finite item set, exact payload or inputs,
  and target identifiers or preconditions>.
- Intended effects: <new records and targets, or existing record IDs, authorized fields, and
  editorial corrections>.
- Separate review: Not selected | <chosen reviewer, actual model/effort, and pre-write verdict> |
  Selected reviewer unavailable — write held until completed or withdrawn.
- Read-back authority: <source that verifies IDs, targets, exact content, and state; for creation,
  also multiplicity; for correction, the baseline and preserved unrelated content/metadata>.
- Reconciliation state: Not needed | Confirmed applied | Confirmed not applied | Unresolved.
- Prohibited effects: <changes outside the authorized creation or editorial fields, plus workflow,
  authority, commitment, deployment, operational, and destructive effects>.

## Execution

| Status | Step and owners | Validation or result |
| --- | --- | --- |
| pending | Perform author evidence check and obtain any selected pre-edit or pre-write review. | <author or reviewer findings; `No separate review selected` when applicable> |
| pending | Present the current plan link and explanatory summary in chat; in plan-and-execute mode, wait for an explicit go-ahead before implementation. | <presentation and user response, or `Pending`> |
| pending | Revalidate prerequisites and perform the scoped change or external action. | <specific check> |
| pending | Update affected consumers or create remaining authorized records. | <specific check or `Not applicable`> |
| pending | Validate and obtain any selected local result review; reconcile external delivery if needed, then close. | <proportional checks, final diff, selected review verdict or external read-back, and status> |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`. Record a
material premise before its dependent step and keep evidence concise rather than chronological.
For a material new or changed execution route, record one binding under **Evidence and
assumptions** or **Review and replan**: user authorization or explicit repository mandate,
existing workflow examined, applicable skills, chosen route, and any blocker. Dependent steps
may refer to that binding; do not repeat an approval check for every file.

## Review and replan

- Review mechanism: None selected | Selected advisor or independent reviewer | Focused author
  reread. Record each applicable mechanism; a selected independent reviewer cannot be replaced
  by an advisor or author reread without the user's withdrawal of that choice.
- Applied findings: <concise list, or `None`>.
- Rejected findings: <finding and reason, or `None`>.
- Replan if: <discovery that changes risk, scope, or execution route>.

## Completion

- Evidence: <outcome, consumers, validation, diff or authoritative external IDs, and status>.
- Delivery read-back: <target, exact request or content, state, and prohibited-effect verification;
  creation multiplicity or preservation of unrelated content/metadata, or `Not applicable`>.
- Focused author pass: Pending | Passed | Failed.
- Selected independent review: Not selected | Pending |
  <chosen reviewer, actual model/effort, local final-result or external pre-write timing,
  evidence scope, and verdict>.
- Unresolved limitations: <limitations, or `None`>.
- Brief check: No brief on this subject | No `registro pendente`; open items reported and noted:
  <items, or `None`>.
- Verdict: Pending | Passed | Failed.

Set the verdict to `Passed` only when the outcome and affected consumers are verified, proportional
validation passed, the diff is scoped, advance choices covered this plan and separate reviews, the
current plan had user review before implementation, statuses agree, the focused author pass
completed, the brief check found no `registro pendente`,
every selected independent review completed or was explicitly withdrawn, and no required evidence
remains unresolved. For
either external path, also require authoritative IDs, an exact delivery match, completed governing
reviews, no prohibited effect, and no unresolved delivery result. Editorial corrections additionally
verify that unrelated content and metadata were preserved.
