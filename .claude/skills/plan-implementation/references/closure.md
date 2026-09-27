# Reviews and completion

## Independent reviewer selection

When an independent reviewer is required, prefer a different model from the advisor, ideally from
another family or provider. An explicit user decision that pins the same model for both roles is
authoritative; record that choice and the residual risk of correlated model blind spots. In every
case, preserve review independence with fresh context, an authoritative evidence baseline, and a
prompt that withholds the intended verdict. Include the original user request and applicable
instructions in that baseline so the reviewer can detect a plan that exceeds them. If the client
cannot open a required reviewer, record that it was unavailable. State which mechanism each
applicable review used and record findings that changed the plan plus findings rejected with a
reason.

## Close work proportionally

Before moving any formal plan to `completed/`, open the brief on the same subject under `briefs/`
when one exists, because nothing else looks at a brief when the work ends. A decided item still
marked `registro pendente` blocks the move until every owner named for the decision has it. An
item that is merely open does not block through this check: report it to the user in the closing
message and note it in the plan. This check relaxes no other gate; an open item that stands for a
required validation, authorization, or access still blocks under the rules below.

Before any completion verdict, apply `test-quality`'s **Review test evidence before closure** to
every added or materially changed test and to existing tests cited as decisive evidence for the
requested outcome. For each, check the claimed behavior against the production boundary exercised,
an observation independent of configured mocks, and sensitivity evidence for a plausible defect.
Record the supported claim and any coverage gap in the proportional completion evidence; skipped
or quarantined tests provide no passing evidence.

Use the focused author check for routine tests and obtain a fresh-context independent test review
only when `test-quality` requires one, including for project-wide false-positive audits. The
absence of a second plan conformance pass in a routine or compact path does not waive that review.
Reuse an independent plan or closure review only if it examined the final tests against these
criteria. Leave required evidence or review unresolved until it is supplied.

Routine work without a formal plan closes after verifying the requested outcome, running its cheap
local validation, and checking the final diff and repository status. It needs no closure matrix or
second pass.

Routine local work with a brief formal plan under the model route uses the same direct checks and
marks that visible plan complete; the plan alone does not add an independent review or matrix.

For non-trivial local reversible work executed directly under the model route, reconstruct the
changed path and affected consumers, verify the requested outcome with proportional validation,
inspect the final diff and repository status, and report limitations accurately. Perform a
focused author pass against the governing instructions and original request. This direct route
needs no closure matrix or independent second pass unless another rule requires one.

A routine external editorial correction instead closes with its exact diff and authoritative
read-back checks in [external-action routes](external-actions.md); local repository checks apply
only if local files changed. When it independently requires a compact plan, also record its author
verdict and complete the same-subject brief check; no independent second pass is added solely for
the external edit.

For a non-trivial local and reversible formal plan, inspect the plan's outcome, scope, current
steps, completion evidence, verdict, and relevant governing instructions. After compaction,
handoff, or a material replan, reread the entire compact plan. Reconstruct the changed path from
the implementation and validation evidence, then verify the requested outcome, affected consumers,
required checks, final diff, and repository status. Record a concise completion verdict, unresolved
limitations, and a focused author pass. This level needs no closure matrix or bidirectional traces
unless it is reclassified as high risk.

For a bounded additive external action, reread the compact plan after compaction, handoff, material
replan, or an ambiguous tool result. Reconcile every intended item with one authoritative external
ID and verify the authorized target, exact request or content, multiplicity, and resulting state.
Confirm that every governing review completed and that no prohibited effect or unresolved delivery
outcome remains. Record the implementer's delivery read-back and concise verdict. Do not require a
second independent closure pass unless another governing rule requires it or the action inherits a
higher-risk formal plan.

For a high-risk formal plan, treat closure as a separate blocking phase, not as a summary written
from memory. After the candidate implementation and required validation are complete:

1. Reread the entire persistent plan, the user's original request and later explicit decisions,
   every governing architecture record, coupled global and repository instructions, and applicable
   skills. Do not rely only on task-plan labels or remembered intent.
2. Reconstruct the implemented runtime path from the full diff, including new files, code,
   configuration, tests, fixtures, observed effects, and actual validation artifacts. A report
   that a command passed is evidence only for what that command asserted.
3. Complete the plan's closure-audit matrix with concise evidence pointers rather than execution
   history. Account for every outcome, scope boundary, governing invariant, affected consumer,
   replan condition, and required validation obligation. Group entries when they share the same
   owner, failure mode, and evidence; keep distinct terminal or recovery paths separate.
4. Trace both directions:

   ```text
   architecture invariant -> implementation-plan step -> code/config owner -> consumers -> test/replay
   changed file/effect -> user authorization and applicable instructions -> authorized plan scope
                       -> governing invariant or explicit local objective
   ```

   The forward trace detects omitted implementation. The reverse trace detects unauthorized work,
   accidental new architecture, and tests that validate behavior outside the approved objective.
5. Mark each matrix row `verified`, `not applicable` with a concrete reason, or `unresolved`.
   Use `not applicable` only when the approved scope and governing authority objectively exclude
   the requirement. Missing evidence, unavailable or skipped required validation, an unexamined
   consumer, cost, time, or an unexplained scope addition is `unresolved`; it is never implicitly
   satisfied by another passing row.
6. Perform a second conformance pass after the implementer's pass. Use a separate agent with fresh
   task context and give it the original user request and decisions, applicable instructions and
   skills, plan, governing records, final diff, observed effects, and validation artifacts without
   the intended verdict. Apply the independent-review model rule above. When a required
   independent pass is unavailable, report that limitation instead of calling it independent.
7. If either pass finds a mismatch, reopen the affected execution steps, correct the lowest
   incorrect authority, rerun invalidated validation, and repeat the complete closure audit. Do not
   append an exception that permits completion.

For high-risk persistent plans, store the concise matrix and final conformance verdict in the plan.
For compact persistent plans, store only the proportional completion evidence and verdict described
above. Store detailed command output, costs, raw logs, and replay events in their executable or
operational artifacts and link them; do not copy them into either plan type or an architecture
record.

A material change after the closure audit to an in-scope or coupled artifact—including code,
configuration, tests, fixtures, plans, architecture, authorization rules, or behavior
documentation—invalidates the closure verdict. A material follow-up or replan within the same
formal plan inherits that plan's highest risk classification; it cannot be relabeled as a lower-risk
slice to avoid required review. Repeat the inherited-risk reread and review, recheck every affected
requirement, rerun checks invalidated by the change, and issue a new verdict. A formatting-only or
evidence-wording correction requires rechecking the affected evidence and final diff, not replaying
unrelated validation.

## Completion gates

For routine work without a formal plan, require the requested outcome, proportional local
validation, a scoped final diff, and an accurate report of limitations. For routine external
editorial corrections, use their direct verification and closure procedure in
[external-action routes](external-actions.md), including when an independent persistence trigger
requires a compact plan.

For non-trivial local reversible work completed without a formal plan under the model route,
require the requested outcome, every affected consumer, proportional validation, a scoped final
diff and status, a focused author pass, and an accurate limitation report. Apply any separate
test-evidence or domain review requirement above.

For a non-trivial local and reversible formal plan, require the requested outcome, every affected
consumer, proportional validation, a scoped final diff and status, a focused author pass, an
accurate limitation report, the same-subject brief check above, and agreement between the
persistent plan and task-plan statuses. Do not require a closure matrix, bidirectional traces, or
an independent second pass at this level.

For a bounded additive external action, require one authoritative external ID for every intended
item; an exact match for its authorized target, request or content, multiplicity, and expected
state; all governing reviews; no prohibited effect; no unresolved delivery result; the
same-subject brief check above; and agreement between plan statuses. The implementer's
authoritative read-back closes this path; do not require an independent second closure pass unless
a stronger or inherited rule does.

For a high-risk formal plan, do not mark the plan complete until all applicable gates pass:

- The requested outcome exists in the authoritative runtime path.
- Every affected consumer uses the updated contract.
- No legacy or fallback path preserves the superseded meaning.
- Focused protection fails for the intended reason without the fix and passes with it.
- Required integration, replay, and broader checks have completed. An unavailable required check
  remains unresolved and blocks completion unless the governing authority changes its requirement.
- The final diff contains no unrelated user-owned changes.
- Documentation and architecture records are synchronized only where their owned behavior changed.
- Remaining limitations, skipped validation, live cost, and operational uncertainty are reported
  accurately.
- The persistent plan and task-plan projection agree on every material terminal status.
- The same-subject brief check under **Close work proportionally** found no decided item still
  marked `registro pendente`, and every item that is merely open was reported and noted in the plan.
- The closure-audit matrix contains no `pending` or `unresolved` row and cites current evidence for
  every applicable requirement.
- The architecture-to-implementation and implementation-to-authority traces are both complete.
- The required second conformance pass found no unresolved
  omission, contradiction, unauthorized behavior, or unprotected failure path.

If implementation is incomplete, leave the corresponding step pending or in progress and state the
concrete blocker. Never convert an unfinished plan into a successful handoff by weakening its
acceptance criteria.
