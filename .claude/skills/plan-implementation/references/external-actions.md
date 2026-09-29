# External action routes

## Routine external editorial correction

Use this direct path for a bounded correction of prose or references in an identified existing
record only when all conditions hold:

- The user authorized the target record, fields, and correction. The outgoing diff is reviewable,
  and authoritative reads can verify the current and resulting record.
- Known effects are limited to the editorial update and ordinary notifications. The edit changes
  no requirements, acceptance criteria, decisions, policy, permissions, commitments, workflow
  state, executable content, or automation behavior, and erases no substantive history.
- No other high-risk trigger applies, and the correction is not part of an inherited high-risk
  plan. A selected pre-write AI review remains pending until completed or withdrawn.

Missing authorization, unknown effects, or unavailable authoritative read-back block writing;
plan or review choices cannot substitute for them. Ask about a recommended separate review at
the relevant task boundary, then:

1. Read the current record, verify changed claims under the domain skill, and inspect the exact
   outgoing diff. Preserve unrelated content and metadata. If the user chose a pre-write review,
   obtain it before writing. Recommend an autonomous-group reviewer for supervised work when
   available, and explain any higher stakes.
2. Immediately before writing, revalidate the target and compare against the read baseline. Use
   a version precondition when available. Preserve concurrent edits and re-review a revised diff
   within authorized scope; request direction for scope drift.
3. Update only authorized fields. Read back the record and verify the intended text and unrelated
   content and metadata, allowing expected server timestamps.
4. After an ambiguous result, reconcile through authoritative reads. Do not retry if it landed.
   Retry only after confirmed non-application and another pre-write check. Stop on unresolved or
   unexpected effects; never blindly retry or roll back.

These checks close the direct path without a formal plan or closure matrix. If the user chose a
compact plan due to another persistence trigger, record the same checks and author verdict there.
An unselected AI review adds no gate.

## Bounded additive external action

Use this bounded route only when every condition below is verified before the first write:

- The user authorized the exact destination, operation, finite items, payload or inputs, and
  target identifiers or preconditions. Establish this binding in a chosen compact plan or direct
  execution; do not request the same authorization again.
- Authoritative read-back can identify every created record and verify its target, exact request
  or content, multiplicity, and resulting state.
- Each intended effect creates a new, independently identifiable record and does not modify or
  delete an existing one.
- Downstream effects are known and limited to creation plus ordinary delivery or notification.
  The action does not change workflow state, approval state, or access, create a financial or legal
  commitment, deploy, or cause an operational or destructive effect.
- Mutable targets and preconditions are revalidated immediately before each write.
- No other high-risk trigger applies, and the action is not part of an inherited higher-risk plan.

The authorized destination and payload need no new approval. If the user chose a compact plan,
offer its link and wait for explicit go-ahead before the first write. If the user declined the
plan, execute directly with the same authorization, precondition, reconciliation, and read-back
checks. A separate review is an independent user choice.

Missing authorization, read-back authority, or knowledge of downstream effects blocks writing.
When those preconditions hold but another eligibility condition fails, classify the action as
high risk and strengthen the plan/review recommendation and author audit. A material change to
authorized destination, operation, item set, payload, target, or precondition requires renewed
user authorization before writing. Drift alone does not silently authorize a changed action.

Recommend a qualified pre-write AI reviewer according to model group, uncertainty,
coordination, and stakes. Obtain the user's choice before invoking one. A declined review does
not block an otherwise authorized write; a selected review holds the write until completed or
explicitly withdrawn. Post-action read-back verifies delivery, not substantive correctness.

Revalidate the current target and preconditions immediately before each write, including after
waiting for a selected plan or review, between items, and before any authorized retry. Perform
multiple items sequentially. After timeout, partial success, or inconclusive response,
stop later writes and retries, then reconcile through authoritative read-only evidence:

- Confirmed creation: record the external ID without retrying, then resume remaining items.
- Confirmed non-creation: retry only the same authorized item, then continue sequentially.
- Unresolved delivery: block completion and request direction when safe reconciliation cannot
  establish the result.
- Unexpected effects or target drift after an attempted write: stop, reconcile the prior attempt,
  obtain renewed authorization for changed scope, and reclassify remaining work as high risk.

Preserve confirmed results. Never blindly retry or perform an unapproved compensating mutation.
Conclusive reconciliation alone does not promote a chosen compact plan. An action within an
existing plan retains its highest risk classification and author closure rigor; separate review
choices remain revocable.
