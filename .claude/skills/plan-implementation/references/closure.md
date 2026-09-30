# Reviews and completion

## Review or formal audit when the user selects it

Ask before invoking an advisor, independent or domain reviewer, or structured author audit unless
the user already selected it for this scope. State the proposed depth, timing, model, and effort;
the user may change or decline each recommendation. A choice may cover named pre-edit and final
phases. Identify the reviewer's actual settings. Recommend a different capable
model from the advisor, with fresh task context, the original user request and decisions,
applicable instructions, governing records, current plan if chosen, final diff or proposed scope,
and actual validation evidence. Withhold the intended verdict. Record applied and rejected
findings with reasons. A reviewer reads and reports; it never edits or delivers.

Use the selected timing:

- Pre-edit review examines a proposed high-risk approach before affected implementation.
- Pre-write review examines an external payload and its authority before the write.
- Final review examines the completed result, consumers, checks, and scope. Recheck a material
  correction within the selected scope; ask before an additional review outside that choice.

If a selected reviewer is unavailable, hold only the phase that depends on it: affected
implementation, external write, or completion. The user may explicitly withdraw the review for
remaining work. An unselected or declined review never blocks. An advisor or author reread does
not count as an independent review, but author verification is always required. An ordinary
read-only reviewer does not itself trigger a multiple-implementer plan recommendation.

## Checks shared by all routes

Before completion, confirm that every new formal plan, review, or structured author audit had an
explicit advance choice, or that the user requested it directly. Preserve the true chronology of
older actions; ask before any later uncovered action. An unanswered process choice remains pending;
do not close the task by treating silence as a refusal. A chosen plan must have been offered in
chat with a link to its complete current version, a concise summary, and its line and word counts,
followed by explicit user release before its first implementation step. A material contract
revision needs a new presentation and release before its affected steps. A direct route has no
linked-plan gate. A plan-only request never authorizes execution.

Apply `test-quality`'s **Review test evidence before closure** to added or materially changed
tests and existing tests cited as decisive evidence. Check what the production boundary actually
observes, an observation independent of configured mocks, and sensitivity to a plausible defect.
A selected independent test review can be reused when it examined those criteria. Skipped or
quarantined tests provide no passing evidence. Do not claim full validation from a partial check.

Check the requested outcome, affected consumers, governing instructions, actual validation,
final diff, repository status when applicable, and limitations. Missing required evidence,
authorization or external approval remains unresolved; a preferred model or an unselected audit
is not such a prerequisite. Do not create a substitute plan or closure-matrix artifact to bypass
the user's choice. Report unverified results as unverified.

Before closing either a formal-plan or direct route, inspect a same-subject brief under `briefs/`
when one exists. A decided item still marked `registro pendente` holds affected closure while an
actual decision-recording owner named for it is missing. A declined plan does not become an
invented owner. Report open items and note them in a chosen plan; an open item blocks only if it
represents a separate required validation, authorization, or access condition.

## Proportional author closure

For routine local work, verify the outcome, cheap local check, final diff and status. A selected
result review adds its verdict but does not force a plan or matrix.

For non-trivial local work, trace the changed path and affected consumers, perform proportional
validation and a focused author pass against the original request and authorities, then inspect
the diff and status. A chosen compact plan records its current steps, evidence, limitations,
selected review status, and verdict. Direct work needs no matrix.

For a routine external editorial correction, perform the exact-diff, precondition,
reconciliation, and read-back checks in [external-action routes](external-actions.md). For a
bounded additive external action, verify each intended item against one authoritative external
ID, exact target, request or content, multiplicity, expected state, and prohibited effects.
Selected pre-write reviews finish before writing. With a chosen compact plan, record the author
verdict and delivery evidence there. Without one, report the same evidence directly. Neither
route requires a second independent closure pass solely because the action is external.

## Selected full conformance audit

Strongly recommend this audit for high-risk or architecture-governed work. Perform it only when
the user selects it, with the selected auditor; an independent audit does not also require a full
author audit. Without this choice, use proportional result verification above, with no mandatory
matrix, systematic reread, or second pass. After candidate implementation and applicable validation:

1. Reread the original request and later explicit decisions, governing architecture records,
   coupled global and repository instructions, and applicable skills. If a plan was chosen,
   reread its complete current version as well.
2. Reconstruct the implemented path from the full diff, including new files, code,
   configuration, tests, fixtures, observed effects, and validation artifacts. A passed command
   supports only what it actually asserted.
3. Account for every outcome, scope boundary, governing invariant, affected consumer, failure
   path, replan condition, and required validation obligation. With a full formal plan, put
   concise evidence pointers and `verified`, `not applicable: <reason>`, or
   `unresolved: <reason>` in its closure matrix. Without a plan, perform the same evidence
   accounting in the selected audit and report the verdict; do not create a hidden plan or matrix.
4. Trace both directions, with the plan step included only if one exists:

   ```text
   architecture invariant -> [chosen plan step] -> code/config owner -> consumers -> test/replay
   changed file/effect -> user authorization and instructions -> [chosen plan scope]
                       -> governing invariant or explicit local objective
   ```

5. Resolve every unsupported, skipped, or unavailable required check as `unresolved`, not as
   satisfied by another passing row. Correct mismatches at the lowest incorrect authority,
   rerun invalidated validation, and recheck conclusions affected by the correction within the
   selected audit scope. Ask before an additional audit not covered by that choice.
6. Perform a second conformance pass only if selected. Use fresh context for an independent pass;
   do not add an author second reading when no second pass was chosen. An unavailable selected
   reviewer holds only its dependent phase until it runs or the user withdraws it.

When both are chosen, store the audit's matrix and verdict in the plan. Choosing a full plan alone
does not choose this audit. Keep raw logs, costs, and replay events in their operational owners.
A material change to an in-scope or coupled artifact invalidates the affected conclusions. Rerun
invalidated result checks and recommend the needed review scope; repeat a review or full audit
only within the user's selected scope or after a new choice. A formatting-only or evidence-wording
fix needs only the affected evidence and diff rechecked.

## Completion gates

Complete only when the requested outcome and consumers are verified, required validation and
author checks have passed, the final diff is scoped, and limitations are accurately reported.
The same-subject brief check applies to direct work too. For a chosen plan, its linked user review,
lifecycle status, and task-plan projection must agree. A selected review or audit holds its
dependent phase until completed or explicitly withdrawn. A declined audit, matrix, or second pass
does not block completion; do not claim it occurred. For executable high-risk changes that
require focused regression protection, demonstrate that the protection fails for the intended
reason without the fix and passes with it. If the negative control cannot safely or practically
run, report that limit and leave the high-risk gate unresolved unless governing authority
explicitly accepts alternative evidence; do not call unmeasured sensitivity measured. For external
actions, authoritative read-back, exact delivery, and absence of prohibited effects are additional
gates. If any independent prerequisite is unresolved, leave the work pending and state the concrete
blocker rather than weakening it.
