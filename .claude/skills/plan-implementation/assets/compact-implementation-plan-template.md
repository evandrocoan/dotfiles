# Implementation plan: <task>

**Status:** Planned
**Mode:** Plan only | Plan and execute
**Risk:** Non-trivial local and reversible | Bounded additive external action

Use this compact persistent template only when the work meets the skill's non-trivial local and
reversible criteria or every condition under **Bounded additive external action** in `SKILL.md`.
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

## Bounded additive external action

- Authorization binding: <approved destination, operation, finite item set, exact payload or inputs,
  and target identifiers or preconditions>.
- Intended effects: <finite ordered list of new records and their targets>.
- Governing review: Not required | <authority, reviewer, and verdict> | Required reviewer
  unavailable — execution blocked.
- Read-back authority: <source that returns external IDs, requests or content, targets,
  multiplicity, and state>.
- Reconciliation state: Not needed | Confirmed created | Confirmed not created | Unresolved.
- Prohibited effects: <existing-record, workflow, authority, commitment, deployment, operational,
  and destructive changes that must remain absent>.

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
- Delivery read-back: <target, exact request or content, multiplicity, state, and prohibited-effect
  verification for every external item, or `Not applicable`>.
- Focused author pass: Pending | Passed | Failed.
- Unresolved limitations: <limitations, or `None`>.
- Brief check: No brief on this subject | No `registro pendente`; open items reported and noted:
  <items, or `None`>.
- Verdict: Pending | Passed | Failed.

Set the verdict to `Passed` only when the outcome and affected consumers are verified, proportional
validation passed, the diff is scoped, statuses agree, the focused author pass completed, the brief
check found no `registro pendente`, and no required evidence remains unresolved. For a bounded
additive external action, also require every intended item's authoritative external ID, exact
delivery match, completed governing reviews, no prohibited effect, and no unresolved delivery
result.
