---
name: plan-implementation
description: >-
  Turn an approved objective, bug diagnosis, or architecture record into a concrete, testable
  execution plan and keep implementation aligned with it. Use when the user asks for an
  implementation plan, asks to implement a non-trivial multi-file or multi-stage change, requests
  a plan for approval, or when an architecture record is moving into implementation. Also use for
  every high-risk change, including authorization, safety, risk, or mandatory-review policy; for a
  material continuation, replan, or follow-up under an existing formal plan; and before costly live
  validation, migrations, protocol changes, or fixes whose correctness depends on coordinated code,
  tests, replay, configuration, or documentation. Require a user-visible persistent Markdown plan
  when work may span phases, agents, interruptions, or context compaction.
---

# Plan implementation

Create the smallest plan that makes the requested delivery reliable. Keep durable design
authority in architecture records, as `architecture-records` classifies it; that skill excludes the
workflow rules of shared agent skills, which live in the skills themselves. Keep every formal plan
user-visible. When the persistence gate applies, keep detailed execution state in Markdown and
project its current steps into the task plan.

## Determine the planning mode

Classify the request before editing:

- **Plan only:** When the user asks for a plan, asks to review or approve a plan, or explicitly
  says not to implement, inspect enough authoritative evidence to make the plan credible and stop
  after presenting it.
- **Plan and execute:** When the user asks to change, fix, build, or implement, create the plan and
  continue through it without requesting separate approval for routine in-scope steps.
- **No formal plan:** Skip a formal plan for routine local reversible work or a **Routine external
  editorial correction** below, unless another persistence condition applies. Still identify the
  expected outcome and verify it.

Use a formal plan for every high-risk request and for non-trivial work with dependent stages,
cross-component consumers, migration or replay, paid validation, or material scope uncertainty.
Touching several files or performing several obvious edits under one owner does not by itself make
otherwise routine work non-trivial.

A bounded additive external action that meets every condition under **Bounded additive external
action** uses the compact persistent path. Eligibility selects risk, template, and closure; it never
overrides an explicit plan-only request or supplies permission to execute. When execution is
authorized, use plan-and-execute mode. External mutation still activates the persistence gate even
though externality alone does not make that narrowly defined action high risk. A routine external
editorial correction uses the direct path below; its external location alone requires neither a
formal plan nor independent review. Neither path overrides authorization or plan-only mode.

## Materialize the plan visibly

Never keep a formal plan only in hidden reasoning or conversation memory. Materialize it in the
task's visible plan mechanism, or present it directly when no such mechanism exists, before editing
production code. User-visible means that the durable artifact is accessible through the
environment or a clickable path; it does not require pasting the full plan or its payloads into
progress messages. Give the user a concise summary and the artifact link unless they request the
complete text in chat.

Use these two layers when the persistence gate applies:

- **Persistent execution plan:** Store the complete current execution contract in Markdown.
- **Task plan:** Project the current steps and statuses into the environment's visible plan
  mechanism for concise progress tracking.

The persistent plan is mandatory when any of these conditions applies:

- work is high risk under **Review plans proportionally**;
- work is likely to cross context compaction, an interruption, a handoff, or more than one session;
- multiple agents or people may act on the plan;
- several dependent phases or cross-component consumers must remain coordinated;
- the task implements or materially audits an architecture record;
- migration, recorded replay, end-to-end validation, paid validation, or external mutation outside
  the **Routine external editorial correction** path is required;
- losing a constraint, non-goal, authenticated fact, or validation obligation could produce an
  incorrect delivery. The ordinary pre-write snapshot, payload, and read-back checks of a routine
  editorial correction do not alone activate this condition.

Persistence and risk are independent. Persistence determines where the execution contract
survives; it does not promote non-trivial local work or a bounded additive external action to high
risk. A persistent non-trivial local plan, a bounded additive external action, and a routine external
editorial correction with an independent persistence trigger use the compact template and their
proportional closure below. A high-risk or architecture-governed plan uses the full template,
closure matrix, bidirectional traces, full reread, and independent second pass.

If otherwise routine work later meets the persistence gate because of handoff, interruption,
multiple actors, or another listed condition, treat it as non-trivial for planning ceremony and use
the compact persistent path. That promotion does not make it high risk by itself.

When the repository defines a current implementation-plan convention, follow it. Otherwise use
this default root for repository-backed work:

```text
implementation-plans/
├── README.md
├── active/
└── completed/
```

A `briefs/` directory beside these holds `discussion-briefs` working documents when that skill
establishes it. Before planning, read a brief there on the same subject and absorb the items the
user decided into the plan's authorities and evidence, in English. A brief supplies user decisions
only; it holds no execution authority and is not evidence of current behavior.

Create `implementation-plans/README.md` when establishing this root. If the default root already
exists without that file, add it before the next plan is created, moved, or closed. Keep the README
concise and require it to define:

- `active/` as the location for planned, in-progress, blocked, or otherwise unresolved work;
- `completed/` as the location for plans whose risk-appropriate closure verdict passed;
- moving the same file between lifecycle directories without retaining a duplicate;
- the repository's plan naming and any additional lifecycle states; and
- the boundary between temporary execution authority and durable architecture records.

Do not maintain a manual inventory of individual plans in the README; the plan files present in the
lifecycle directories are the inventory and cannot drift from a copied list. Place an active
repository-backed plan at:

```text
implementation-plans/active/<task-slug>.md
```

Use `assets/compact-implementation-plan-template.md` for persistent non-trivial local work, bounded
additive external actions, and editorial corrections that independently require persistence.
Use `assets/implementation-plan-template.md` for high-risk or architecture-governed work. Use a
concise lowercase hyphenated task slug. Keep one active file for one delivery objective; do not
create a new file for every retry or replanning event.

When using the default lifecycle, close a successfully completed plan by moving the same file,
after its final conformance verdict passes, to:

```text
implementation-plans/completed/<task-slug>.md
```

Preserve the completed plan as the final execution contract; do not copy it or leave another copy
under `active/`. Update any task-plan, documentation, or brief link that pointed to the active
path. Keep a blocked or unresolved plan under `active/` with its real status unless the repository
defines a separate blocked state.

When no repository owns the task, use the same documented lifecycle under the global root:

```text
~/.claude/implementation-plans/active/<task-slug>.md
~/.claude/implementation-plans/completed/<task-slug>.md
```

Create `~/.claude/implementation-plans/README.md` when establishing that root. Never use `/tmp` or
another automatically cleaned location for a persistent plan. An issue or merge-request description
may replace the local file only when it is the established execution authority and all agents can
read and update it. A chat message or hidden model state never replaces the persistent plan.

Apply this authority order:

```text
approved architecture or product decision
        -> persistent implementation plan
        -> task-plan status projection
        -> conversational progress update
```

Resolve disagreement by correcting the lower layer. Never let the task-plan projection silently
override the persistent plan or let the persistent plan override approved architecture.

## Inspect before planning

Read the applicable repository instructions and inspect the authoritative code, configuration,
tests, and existing records before choosing implementation steps. Do not create a plan from
filenames, issue prose, or remembered architecture alone.

Inspect enough evidence to create a truthful initial plan, then materialize the plan before the
first production edit. Mark unresolved facts as assumptions or investigation steps instead of
inventing implementation details.

When a durable architecture record governs the change, use `architecture-records` together with
this skill. Treat the approved record as the design authority and derive the implementation plan
from it. Do not alter the record to legitimize incidental current code.

When the plan carries out a deliberate user decision that changes an approved record, follow
the deliberate-decision procedure in `architecture-records` section 7a. When it permits bounded
recording before review, the discussion/planning session amends the record first, then creates
or updates the plan from that amended record and submits both to the required review. When
mandatory maintenance puts the record edit outside those bounds, create or update the plan
with the maintenance and amendment steps first, keep the decision pending for the record with
the reason, and obtain the required plan review before performing that unit. Complete the
authorized recording before the implementing-session handoff; describe which owners were
actually updated without presenting pending recording or implementation as completed. The
fallback must not be overridden by an unconditional amendment-before-plan instruction.

Load the task-specific skills required by the work before planning their stages. In particular,
use `test-quality` for executable validation, `documentation` for durable documentation,
`dependency-decisions` for dependency choices, and the relevant delivery or infrastructure skill
when those concerns are in scope.

## Establish the execution contract

Record these elements before implementation:

1. **Outcome:** State the externally observable result and the terminal condition for the task.
2. **Scope and non-goals:** Bound the authorized change and name nearby behavior that must remain
   unchanged.
3. **Authorities and invariants:** Identify the architecture record, schema, configuration,
   runtime owner, or other source that constrains the implementation.
4. **Current evidence:** Summarize the verified failure or current behavior. Mark assumptions that
   remain unverified.
5. **Work sequence:** Divide the change into ordered, independently checkable slices. For each
   material slice whose result depends on a non-obvious premise, record that premise and the
   artifact that proves it. A premise is what must already be true for the result to mean what the
   slice claims, such as what a passing test actually measures. Obvious local prerequisites need
   not become separate evidence fields. A slice with an unverified material premise does not
   start; record it as an open assumption and verify it first.
6. **Validation:** Bind each material slice to focused protection and bind the completed flow to
   proportional integration, replay, end-to-end, or operational validation.
7. **Replanning conditions:** State the discoveries that would invalidate the current route.

Do not use vague steps such as “fix the logic,” “add tests,” or “verify everything.”
Name the behavior boundary, the affected owner or consumer, and the evidence that will prove the
step complete. Mention exact paths or symbols only after inspecting them; do not invent locations
to make a plan look concrete.

When ownership or flow changes, carry each affected architectural guarantee into that sequence,
including unchanged behavior whose implementation path moves. Before a step removes an existing
responsibility or protection, require evidence that the replacement path preserves its
guarantees. Establish that path first, or use an explicitly atomic transition whose
prerequisites and validation rule out a protection or progress gap. If ownership is unknown,
make its investigation a prerequisite. An architectural assignment is not evidence that the
runtime path already exists. This applies the invariant-to-owner trace to the transition itself,
so a correct final design does not hide a gap in the steps that reach it.

Review plans proportionally before implementation:

Evaluate high-risk triggers first; any match overrides locality, reversibility, or apparent
simplicity. Then distinguish the remaining levels:

- **High risk:** Requires advisor review when available and a fresh-context independent review.
  High risk includes architecture, protocol or state-transition changes, security or authorization
  boundaries, migration or data-loss risk, destructive actions, authorized and verifiable external
  mutations that qualify for neither **Bounded additive external action** nor **Routine external
  editorial correction**, production-wide impact, and expensive or irreversible validation.
  Changes to shared agent
  instructions, skills, or permission allowlists are also high risk when they alter authorization,
  safety safeguards, risk classification, or mandatory review and closure gates; ordinary wording
  and narrowly scoped skill edits do not become high risk solely because of their location.
- **Non-trivial local and reversible:** Uses a compact plan. Call the advisor when available;
  otherwise perform a focused author reread. An independent reviewer is optional. Cross-file or
  cross-component scope belongs here when no high-risk trigger applies.
- **Routine, local, and reversible:** Uses no formal plan and needs no advisor or independent
  reviewer. Routine means one obvious owner, no material uncertainty, and cheap local validation.
  File count and the number of obvious mechanical steps do not change that classification alone.
- **Routine external editorial correction:** Uses the direct procedure below. Independent
  persistence triggers select a compact plan; other high-risk triggers and inherited risk prevail.

Here, local means effects remain confined to the working tree or an isolated development
environment, with no external or production mutation. Reversible means the intended operation has
no credible data-loss or recovery hazard.

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
  Every substantive review required by the user or another applicable authority still applies.

Missing authorization, unknown effects, or unavailable authoritative read-back block writing;
high-risk review cannot substitute for those prerequisites. When they are established but another
eligibility condition fails, use the normal risk classification above.

Perform only the verification needed for the correction; do not turn it into a new investigation:

1. Read the current record, verify changed claims and references under the applicable domain
   skill, and inspect the exact outgoing diff. Preserve unrelated content and metadata.
2. Immediately before writing, revalidate the target and compare against the read baseline. Use a
   version precondition when available. If concurrent edits appear, preserve them and re-review
   the revised diff within the authorized scope before writing; request direction for scope drift.
3. Update only authorized fields. Read back the record and verify the exact intended text and
   preservation of unrelated content and metadata, allowing expected server timestamps.
4. After an ambiguous result, reconcile through authoritative reads before another write. If the
   correction landed, do not retry. Retry only after confirming non-application and repeating the
   pre-write check. Stop on unresolved or unexpected results; never blindly retry or roll back.

These checks close the direct path without a closure matrix, extra review, or persistent evidence
bundle. When another persistence trigger applies, record the same checks in the compact plan and
close with its focused author pass. Existing higher-risk plans retain their closure requirements.

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

Fixed review comments, issue notes, messages, and unshared drafts are examples that may qualify;
their product names and fields do not define the category.

Treat authorization, authoritative read-back, and knowledge of downstream effects as blocking
preconditions, not high-risk fallbacks. If any is missing or uncertain, do not write. A material
change to the authorized destination, operation, item set, payload, target, or precondition
invalidates the binding until the user authorizes it; then classify again. Drift found before the
first write does not itself force high risk. Once these preconditions are established, a false or
unknown remaining condition routes the authorized action through the normal high-risk workflow.

Apply every substantive review required by the user, an applicable domain skill, or another
governing authority before writing. This planning skill neither adds nor removes a review based on
the payload's topic or vocabulary. If a required reviewer is unavailable, block execution and
report the limitation. The post-action read-back verifies delivery, not substantive correctness.

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

When an independent reviewer is required, prefer a different model from the advisor, ideally from
another family or provider. An explicit user decision that pins the same model for both roles is
authoritative; record that choice and the residual risk of correlated model blind spots. In every
case, preserve review independence with fresh context, an authoritative evidence baseline, and a
prompt that withholds the intended verdict. If the client cannot open a required reviewer, record
that it was unavailable. State which mechanism each applicable review used and record findings that
changed the plan plus findings rejected with a reason.

## Build an executable sequence

Order work by dependency and feedback speed:

1. Obtain the risk-appropriate plan review described above and record it in the plan's
   **Plan review** section before any implementation step starts.
2. Reproduce or authenticate the current failure when one exists.
3. Establish or update the smallest failing regression protection.
4. Change the authoritative owner of the behavior.
5. Update every affected consumer of that contract.
6. Remove competing or superseded behavior rather than leaving parallel authority.
7. Run focused checks after the smallest meaningful slice.
8. Run broader integration, replay, and suite-level checks after the flow is connected.
9. Perform operational or paid live validation only when it is useful and authorized under the
   applicable rules.
10. Close routine work with direct outcome, validation, diff, and status checks; close formal plans
    with the risk-appropriate audit below.

Step 1 has one exception. The record amendment that `architecture-records` allows for a deliberate
user decision precedes the plan, and therefore its review, so that the decision lives in its owner
at once and the reviewer reads the real wording. The exception covers only the labelled amendment
block, or the `Proposed` record with its notice line and index entry. No other record text, code,
configuration, or repository instruction file changes before the plan review. The review examines
the amended record together with the plan, and a finding against the amendment is corrected in that
block or record. When editing the record would require anything else, such as translating it or
removing a manual table of contents, the exception does not apply, because an edit of that size
could change a rule unseen before any review: say so, keep the decision pending for the record, and
turn those edits and the amendment into plan steps that run after the plan review.

Combine steps when separating them would create meaningless bookkeeping. Split a step when it
contains more than one independently falsifiable outcome. Keep at most one step in progress, and
update statuses to reflect reality rather than intent.

For parallelizable work, group only tasks with no shared mutable files, state, generated artifacts,
expensive local resources, or causal dependency. Never parallelize merely to make a plan appear
faster.

When a persistent plan exists, inspect its current step, prerequisites, and relevant scope before
starting each new phase; do not reread the entire file solely because the phase changed. When a
brief on the same subject exists under `briefs/`, also check it for decided items still marked
`registro pendente`. Report them to the user and hold each affected phase until the user instructs
recording and every owner named for the decision carries it, subject only to the recording paths
below. An owner is a document that records decisions: the plan, an architecture record, or an
issue. The code or skill text the plan will change is a work target, never such an owner.

With the user's instruction to record, the marker for that decision must not block the work that
resolves it. Distinguish these paths:

- When `architecture-records` section 7a permits recording before plan review, allow only its
  amendment block, or Proposed record with the notice and index entry, before deriving and
  recording the plan and reviewing both. This also applies when a persistent plan already exists.
  No other record text, code, configuration, or repository instruction changes before that review.
- When section 7a requires recording after plan review, allow the read-only inspection to scope it,
  the preparation and recording of the plan, and its required review while the architecture
  record still lacks the decision. Keep the marker and its reason; change no architecture file
  during this preparation or review. Do not move the maintenance or amendment ahead of review.
- After the required review, allow the unit that records the decision in its missing document
  owner, together with only the maintenance that owner's skill makes mandatory for that edit.
  For that fallback this is the maintenance and amendment of the architecture record.

Each path waives only the pending marker for the decision it resolves, not recording authority,
other pending decisions, or any other prerequisite. Keep the marker until every named owner
carries the decision. Dependent implementation remains held until recording and all required
reviews are complete. The discussion/planning session performs the architecture recording before
handing the plan and record to an implementing session, as section 7a requires.

After context compaction, interruption, session restart, material replan, or agent handoff, reread
the entire plan before acting. Give every delegated agent the plan path and the exact step it owns.

## Keep planning state in the correct place

When the persistence gate applies, treat the persistent plan as the sole current authority for
execution detail. Keep it compact and current; do not append a chronological diary. Update it only
when status, scope, evidence, dependencies, validation obligations, blockers, or the chosen
execution route materially changes.

Keep conversational updates as a projection of that artifact: state the outcome or current status
and link the file. Do not reproduce the complete persistent plan or full external-action payloads in
chat unless the user asks for them.

Mirror its executable steps into the task's plan mechanism. The task plan may be shorter, but it
must not omit a material pending phase or report a status that conflicts with the persistent file.
The user must be able to see the plan path and every status transition.

Do not commit the plan merely because it exists. Follow the user's requested Git outcome and the
repository convention. Report whether the plan is tracked or untracked. Keep it available through
handoff. Follow the repository lifecycle when one exists; otherwise apply the default `active/` to
`completed/` transition above. Remove a plan only when the user requests removal.

Never store task status, completed-step narration, timestamps, run-by-run cost, mutable commit
identifiers, or raw logs in an architecture record. A proposed architecture record may contain only
the minimum implementation order needed to constrain the design and its architectural acceptance
criteria.

After implementation, close the execution plan. Preserve durable rationale and invariants in their
authoritative record, executable expectations in tests and fixtures, and operational evidence in
the issue, merge request, replay, or CI artifact that owns it.

Do not store chain-of-thought, speculative internal reasoning, raw prompts, secrets, or copied logs
in the plan. Store verified facts, explicit assumptions, decisions, dependencies, and observable
validation results.

## Replan without changing authority

Replan immediately when:

- an inspected fact contradicts a material assumption;
- an affected consumer or source of authority was omitted;
- the planned test cannot distinguish the defect from unrelated failure;
- an unexpected dependency, destructive action, external mutation, or scope expansion is required;
- user-owned concurrent changes overlap the planned edit;
- validation demonstrates that the chosen implementation violates an invariant;
- cost, quota, or operational state makes the remaining validation predictably wasteful.

Update the persistent plan before taking a materially different implementation route. Preserve the
current outcome and governing invariants, replace superseded steps instead of appending a narrative,
and synchronize the task-plan projection.

Change only the execution plan when the approved design remains valid. Amend or supersede the
architecture record first when ownership, authority, stage order, terminal meaning, recovery policy,
or another durable invariant must change. Stop and request direction when that design change
exceeds the user's authorization.

Do not preserve a failed approach as a second runtime path. Record the new current step, retain
useful authenticated evidence, and remove the superseded implementation before completion.

## Plan validation proportionally

Every plan that changes executable behavior must say how the change can fail and which check
detects that failure. Use the `test-quality` skill to design or modify tests.

Prefer this validation progression when applicable:

- a focused regression that fails for the observed reason before the fix;
- unit or property tests for local invariants and malformed boundaries;
- integration tests across changed producers and consumers;
- a faithful recorded replay for a real cross-component incident when sufficient raw interactions
  exist;
- an end-to-end or live run for behavior that hermetic evidence cannot prove;
- the repository's complete required suite before claiming full validation.

Include timeout, retry, duplicate-event, partial-progress, and terminal-failure cases when the
changed contract owns them. Do not replace a required integral replay with parser-only fixtures,
and do not label partial coverage as end to end.

Keep paid or externally mutating scenarios sequential unless the applicable policy explicitly
requires otherwise. Measure the complete scenario rather than hiding retries or nested commands.

## Close work proportionally

Before moving any formal plan to `completed/`, open the brief on the same subject under `briefs/`
when one exists, because nothing else looks at a brief when the work ends. A decided item still
marked `registro pendente` blocks the move until every owner named for the decision has it. An
item that is merely open does not block through this check: report it to the user in the closing
message and note it in the plan. This check relaxes no other gate; an open item that stands for a
required validation, authorization, or access still blocks under the rules below.

Routine work without a formal plan closes after verifying the requested outcome, running its cheap
local validation, and checking the final diff and repository status. It needs no closure matrix or
second pass. A routine external editorial correction instead closes with its exact diff and
authoritative read-back checks above; local repository checks apply only if local files changed.
When it independently requires a compact plan, also record its author verdict and complete the
same-subject brief check; no independent second pass is added solely for the external edit.

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

1. Reread the entire persistent plan, every governing architecture record, and coupled repository
   instruction file. Do not rely only on task-plan labels or remembered intent.
2. Reconstruct the implemented runtime path from code, configuration, tests, fixtures, and actual
   validation artifacts. A report that a command passed is evidence only for what that command
   asserted.
3. Complete the plan's closure-audit matrix with concise evidence pointers rather than execution
   history. Account for every outcome, scope boundary, governing invariant, affected consumer,
   replan condition, and required validation obligation. Group entries when they share the same
   owner, failure mode, and evidence; keep distinct terminal or recovery paths separate.
4. Trace both directions:

   ```text
   architecture invariant -> implementation-plan step -> code/config owner -> consumers -> test/replay
   changed code/config/test -> authorized plan scope -> governing invariant or explicit local objective
   ```

   The forward trace detects omitted implementation. The reverse trace detects unauthorized work,
   accidental new architecture, and tests that validate behavior outside the approved objective.
5. Mark each matrix row `verified`, `not applicable` with a concrete reason, or `unresolved`.
   Use `not applicable` only when the approved scope and governing authority objectively exclude
   the requirement. Missing evidence, unavailable or skipped required validation, an unexamined
   consumer, cost, time, or an unexplained scope addition is `unresolved`; it is never implicitly
   satisfied by another passing row.
6. Perform a second conformance pass after the implementer's pass. Use a separate agent with fresh
   task context and give it the plan, governing records, final diff, and validation artifacts
   without the intended verdict. Apply the independent-review model rule above. When a required
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
editorial corrections, use their direct verification and closure procedure above, including when
an independent persistence trigger requires a compact plan.

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

## Compact plan format

Use `assets/compact-implementation-plan-template.md` for a persistent non-trivial local and
reversible plan, bounded additive external action, or routine external editorial correction with
an independent persistence trigger. Its conditional external-action section records the
authorization binding, items, governing-review status, read-back authority,
reconciliation state, and delivery evidence; omit that section for local work. Use the following
concise form for a task-plan projection or for a non-trivial local and reversible formal plan that
does not meet the persistence gate. High-risk work always meets that gate and uses the full
persistent template.

```text
Outcome: <observable result>
Constraints: <invariants, non-goals, and authorization boundaries>
Evidence: <verified current behavior and open assumptions>

1. <obtain any risk-required plan review> — mechanism: <advisor, independent plan or domain-required reviewer, or focused author reread> — findings: <concise applied or rejected findings>
2. <reproduce or authenticate> — premise: <what must already be true, and its proof> — validation: <specific check>
3. <change authoritative owner> — premise: <what must already be true, and its proof> — validation: <specific check>
4. <update affected consumers> — premise: <what must already be true, and its proof> — validation: <specific check>
5. <integrate and replay> — premise: <what must already be true, and its proof> — validation: <specific check>
6. <audit and deliver> — premise: <what must already be true, and its proof> — validation: <specific check>

Replan if: <material invalidating conditions>
```

Expand the plan only when additional detail changes how the implementation will be performed or
validated. Record premises only when they are material and non-obvious. An unverified material
premise stays in `Evidence` as an open assumption until it is verified; its dependent step does not
run.
