# External action routes

### Routine external editorial correction

Use this path for a bounded correction of prose or references in an identified existing record,
such as fixing a source permalink or distinguishing a verified fact from an unmeasured inference.
All of these conditions must hold:

- The user authorized the target record, fields, and intended correction. The exact outgoing diff
  is directly reviewable, and authoritative reads can verify the current and resulting record.
- Known effects are limited to the editorial update and ordinary notifications. The edit changes
  no requirements, acceptance criteria, decisions, policy, permissions, commitments, workflow state,
  executable content, or automation behavior, and does not erase substantive historical evidence.
- No other high-risk trigger applies, and the correction is not part of an existing high-risk plan.
  Every substantive review required by the user, the model-group route, or another applicable
  authority still applies.

Missing authorization, unknown effects, or unavailable authoritative read-back block writing;
high-risk review cannot substitute for those prerequisites. When they are established but another
eligibility condition fails, use the risk classification in the [skill entrypoint](../SKILL.md).

Ask about a foreseeable required review at the task boundary before substantive work, then
perform only the verification needed for the correction; do not turn it into a new investigation:

1. Read the current record, verify changed claims and references under the applicable domain
   skill, and inspect the exact outgoing diff. Preserve unrelated content and metadata. When the
   acting agent belongs to the supervised group, obtain the previously chosen independent
   autonomous-group review of the authorized correction before writing. The autonomous group
   needs that review when another rule makes the work non-trivial or higher risk; obtain the same
   advance choice before invoking it.
2. Immediately before writing, revalidate the target and compare against the read baseline. Use a
   version precondition when available. If concurrent edits appear, preserve them and re-review
   the revised diff within the authorized scope before writing; request direction for scope drift.
3. Update only authorized fields. Read back the record and verify the exact intended text and
   preservation of unrelated content and metadata, allowing expected server timestamps.
4. After an ambiguous result, reconcile through authoritative reads before another write. If the
   correction landed, do not retry. Retry only after confirming non-application and repeating the
   pre-write check. Stop on unresolved or unexpected results; never blindly retry or roll back.

These checks close the direct path without a closure matrix or persistent evidence bundle. They do
not waive a group-required pre-write review. When another persistence trigger applies, record the
same checks and review in the compact plan and close with its focused author pass. Existing
higher-risk plans retain their closure requirements.

### Bounded additive external action

Use the compact path only when every condition below is verified before the first write:

- The user authorized the exact destination, operation, finite set of items, payload or inputs, and
  relevant target identifiers or preconditions. Record that binding in the compact plan; do not
  request the same approval again.
- Authoritative read-back can identify every created record and verify its target, exact request or
  content, multiplicity, and resulting state.
- Each intended effect creates a new, independently identifiable record. It does not modify or
  delete an existing record.
- Downstream effects are known and limited to record creation plus ordinary delivery or
  notification. The action does not change workflow or approval state, grant access, create a
  financial or legal commitment, deploy, or cause an operational or destructive effect.
- Revalidate mutable targets and preconditions immediately before acting.
- No other high-risk trigger or applicable skill requires the full workflow, and the action is not
  part of a formal plan that already inherited a higher risk classification.

The recorded destination and payload authorization need not be requested again. It does not
satisfy the separate user review of the newly linked compact plan: offer that plan in chat and
wait for an explicit go-ahead before the first write.

Fixed review comments, issue notes, messages, and unshared drafts are examples that may qualify;
their product names and fields do not define the category.

Treat authorization, authoritative read-back, and knowledge of downstream effects as blocking
preconditions, not high-risk fallbacks. If any is missing or uncertain, do not write. A material
change to the authorized destination, operation, item set, payload, target, or precondition
invalidates the binding until the user authorizes it; then classify again. Drift found before the
first write does not itself force high risk. Once these preconditions are established, a false or
unknown remaining condition routes the authorized action through the normal high-risk workflow.

Apply every substantive review required by the user, the model-group route, an applicable domain
skill, or another governing authority before writing. Obtain the user's choice before invoking a
separate reviewer, as the skill entrypoint requires; a declined required review blocks the write.
The supervised group always needs an independent autonomous-group reviewer. The autonomous group
needs one when the action is non-trivial due to material uncertainty, coordination, or multiple
affected consumers. A separate persistence trigger or inherited higher-risk plan also keeps its
required review. This planning skill adds no review based on the payload's topic or vocabulary.
If a required reviewer is unavailable, block execution and report the limitation. The post-action
read-back verifies delivery, not substantive correctness.

Perform multiple items sequentially. After a timeout, partial success, or inconclusive response,
stop later writes and retries, then reconcile through authoritative read-only evidence:

- Confirmed creation: record the external ID without retrying, then resume remaining items.
- Confirmed non-creation: retry only the same authorized item, then continue sequentially.
- Unresolved delivery: block completion and request direction when safe reconciliation cannot
  establish the result.
- Unexpected effects or target drift after an attempted write: stop, reconcile the prior attempt,
  obtain renewed authorization for changed scope, and replan remaining work as high risk.

Preserve confirmed results. Never blindly retry or perform an unapproved compensating mutation.
Conclusive reconciliation alone does not promote the compact plan. An action within an existing
formal plan retains that plan's highest risk classification and closure requirements.
