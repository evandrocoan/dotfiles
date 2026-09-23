# Implementation plan: <task>

**Status:** Planned
**Mode:** Plan only | Plan and execute
**Risk:** Non-trivial local and reversible | Bounded additive external action |
Routine external editorial correction

Use this compact persistent template only when the work meets the skill's non-trivial local and
reversible criteria, **Bounded additive external action**, or **Routine external editorial
correction** with an independent persistence trigger in `SKILL.md`.
Reclassify to high risk and use `implementation-plan-template.md` when a high-risk trigger applies.
Delete the conditional external-action section for local work.

## Outcome and scope

- Outcome: <observable result and terminal condition>.
- In scope: <authorized owner and consumers>.
- Out of scope: <adjacent behavior that remains unchanged>.
- Authority: <governing decision, configuration, schema, local objective, and relevant invariants>.

## Evidence and assumptions

- Verified: <current behavior or failure and authoritative artifact>.
- Open assumption: <material unverified premise, or `None`>.

## External action

- Authorization binding: <approved destination, operation, finite item set, exact payload or inputs,
  and target identifiers or preconditions>.
- Intended effects: <new records and targets, or existing record IDs, authorized fields, and
  editorial corrections>.
- Governing review: Not required | <authority, reviewer, and verdict> | Required reviewer
  unavailable — execution blocked.
- Read-back authority: <source that verifies IDs, targets, exact content, and state; for creation,
  also multiplicity; for correction, the baseline and preserved unrelated content/metadata>.
- Reconciliation state: Not needed | Confirmed applied | Confirmed not applied | Unresolved.
- Prohibited effects: <changes outside the authorized creation or editorial fields, plus workflow,
  authority, commitment, deployment, operational, and destructive effects>.

## Execution

| Status | Step and owners | Validation or result |
| --- | --- | --- |
| pending | Obtain the risk-appropriate and governing reviews. | <advisor, domain-required reviewer, or focused author findings> |
| pending | Revalidate prerequisites and perform the scoped change or external action. | <specific check> |
| pending | Update affected consumers or create remaining authorized records. | <specific check or `Not applicable`> |
| pending | Validate, reconcile if needed, and close. | <proportional checks, diff or delivery evidence, and status> |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`. Record a
material premise before its dependent step and keep evidence concise rather than chronological.

## Review and replan

- Review mechanism: Advisor | Domain-required reviewer | Focused author reread.
- Applied findings: <concise list, or `None`>.
- Rejected findings: <finding and reason, or `None`>.
- Replan if: <discovery that changes risk, scope, or execution route>.

## Completion

- Evidence: <outcome, consumers, validation, diff or authoritative external IDs, and status>.
- Delivery read-back: <target, exact request or content, state, and prohibited-effect verification;
  creation multiplicity or preservation of unrelated content/metadata, or `Not applicable`>.
- Focused author pass: Pending | Passed | Failed.
- Unresolved limitations: <limitations, or `None`>.
- Brief check: No brief on this subject | No `registro pendente`; open items reported and noted:
  <items, or `None`>.
- Verdict: Pending | Passed | Failed.

Set the verdict to `Passed` only when the outcome and affected consumers are verified, proportional
validation passed, the diff is scoped, statuses agree, the focused author pass completed, the brief
check found no `registro pendente`, and no required evidence remains unresolved. For either external
path, also require authoritative IDs, an exact delivery match, completed governing reviews, no
prohibited effect, and no unresolved delivery result. Editorial corrections additionally verify
that unrelated content and metadata were preserved.
