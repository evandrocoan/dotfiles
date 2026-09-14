# Implementation plan: <task>

**Status:** Planned
**Mode:** Plan only | Plan and execute
**Risk:** Non-trivial local and reversible

Use this compact persistent template only when the work meets the skill's non-trivial local and
reversible criteria. Reclassify to high risk and use `implementation-plan-template.md` when a
high-risk trigger applies.

## Outcome and scope

- Outcome: <observable result and terminal condition>.
- In scope: <authorized owner and consumers>.
- Out of scope: <adjacent behavior that remains unchanged>.
- Authority: <governing decision, configuration, schema, local objective, and relevant invariants>.

## Evidence and assumptions

- Verified: <current behavior or failure and authoritative artifact>.
- Open assumption: <material unverified premise, or `None`>.

## Execution

| Status | Step and owners | Validation or result |
| --- | --- | --- |
| pending | Obtain the risk-appropriate review. | <advisor or focused author findings> |
| pending | Change the authoritative owner and affected consumers. | <specific check> |
| pending | Integrate and remove competing behavior. | <specific check> |
| pending | Validate and close. | <proportional checks, diff, and status> |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`. Record a
material premise before its dependent step and keep evidence concise rather than chronological.

## Review and replan

- Review mechanism: Advisor | Focused author reread.
- Applied findings: <concise list, or `None`>.
- Rejected findings: <finding and reason, or `None`>.
- Replan if: <discovery that changes risk, scope, or execution route>.

## Completion

- Evidence: <outcome, consumers, validation, diff, and status>.
- Focused author pass: Pending | Passed | Failed.
- Unresolved limitations: <limitations, or `None`>.
- Verdict: Pending | Passed | Failed.

Set the verdict to `Passed` only when the outcome and affected consumers are verified, proportional
validation passed, the diff is scoped, statuses agree, the focused author pass completed, and no
required evidence remains unresolved.
