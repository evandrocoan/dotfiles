---
name: plan-implementation
description: >-
  Turn an approved objective, bug diagnosis, or architecture record into a concrete, testable
  execution plan and keep implementation aligned with it. Use when the user asks for an
  implementation plan, asks to implement a non-trivial multi-file or multi-stage change, requests
  a plan for approval, or when an architecture record is moving into implementation. Also use for
  any requested implementation edit, regardless of the active model; read-only requests do not
  activate this edit-specific route. Also use for every high-risk change, including authorization,
  safety, risk, or mandatory-review policy; for a material continuation, replan, or follow-up under
  an existing formal plan; and before costly live validation, migrations, protocol changes, or fixes
  whose correctness depends on coordinated code, tests, replay, configuration, or documentation.
  Require a user-visible persistent Markdown plan when work may span phases, agents, interruptions,
  or context compaction.
---

# Plan implementation

Create the smallest plan that makes the requested delivery reliable. Keep durable design
authority in architecture records, as `architecture-records` classifies it; that skill excludes the
workflow rules of shared agent skills, which live in the skills themselves. Keep every formal plan
user-visible. When the persistence gate applies, keep detailed execution state in Markdown and
project its current steps into the task plan.

## Determine the planning mode

Classify the request before editing. The global model and reasoning-effort gate must identify the
acting agent's effective settings and satisfy any required role before task work begins; an unknown
setting cannot be replaced with a conservative plan. Read
[model-aware routing](references/model-routing.md) for every implementation edit to apply the
acting group's plan and review thresholds, and when recommending a model, reasoning effort, or
reviewer. The applicable user's explicit request and higher-priority question-only or read-only
rules come first. A model never waives the risk and persistence gates below.

- **Plan only:** When the user asks for a plan, asks to review or approve a plan, or explicitly
  says not to implement, inspect enough authoritative evidence to make the plan credible, offer its
  link in chat, and stop. Reviewing a plan-only deliverable does not authorize implementation.
- **Plan and execute:** When the user asks to change, fix, build, or implement, use a required or
  chosen formal plan when one applies. Offer its link for user review and wait for an explicit
  go-ahead before executing it. After that response, continue through the authorized in-scope
  steps without requesting approval for each step. Use the direct route when eligible.
- **No formal plan:** Use direct work only when the model route permits it, no mandatory risk or
  persistence gate applies, and the user has not requested a plan. Still identify the expected
  outcome and verify it.

Use a formal plan for every high-risk request and every persistence trigger below. For remaining
local reversible work, follow the model route and any explicit user preference. Touching several
files or performing several obvious edits under one owner does not by itself make otherwise
routine work non-trivial.

Before drafting or creating a formal plan or invoking a separate advisor, independent reviewer,
or domain reviewer, obtain the user's choice for each action. An explicit request for a plan or
review already answers that dimension for the current scope. Otherwise use minimal read-only
triage to state the recommendation, concrete reason, and whether the plan or review is mandatory
or optional; ask at the task boundary when foreseeable, before substantial dependent work or
reviewer effort. One clear answer may cover named pre-edit and final reviews. A declined or
unanswered mandatory action holds dependent work; silence never starts an optional plan or review.
Direct work may continue only when every other gate permits it. Ordinary author verification is
not a separate review invocation. Preserve the chronology of existing plans and reviews. Ask
before an uncovered material replan or reviewer invocation. This advance choice does not replace
the linked user review of a completed plan before implementation.

A bounded additive external action that meets every condition in
[external-action routes](references/external-actions.md) uses the compact persistent path. Read
that reference before classifying or performing an external write. Eligibility selects risk,
template, and closure; it never overrides an explicit plan-only request or supplies permission to
execute. When execution is authorized, use plan-and-execute mode. External mutation still activates
the persistence gate even
though externality alone does not make that narrowly defined action high risk. A routine external
editorial correction uses the direct path in that reference; its external location alone requires
neither a formal plan nor independent review. Apply any review required by the acting model's
group, another authority, or inherited risk. Neither path overrides authorization or plan-only
mode.

## Materialize the plan visibly

Never keep a formal plan only in hidden reasoning or conversation memory. Give every formal plan a
complete current artifact with a clickable link. Use a Markdown file under the task's plan
lifecycle by default; a task-plan mechanism may substitute only when its link opens the complete
current plan for the user. Chat prose alone does not supply the artifact. Before the first
implementation step under a formal plan, offer its link and a concise summary in chat. Wait for
an explicit user response to proceed. The initial implementation request, silence, and an agent
or advisor review cannot stand in for the user's review. A plan-only request stops after the link
is offered; it needs a later implementation instruction. An explicit request to execute an
unchanged plan already linked in chat satisfies this boundary without another question. If the
plan's execution contract changes materially, offer the updated link and wait again before affected
steps. Read-only scoping and reviews separately chosen by the user may make the plan reviewable
before this linked-plan gate.

Use these two layers when the persistence gate applies:

- **Persistent execution plan:** Store the complete current execution contract in Markdown.
- **Task plan:** Project the current steps and statuses into the environment's visible plan
  mechanism for concise progress tracking.

The persistent plan is mandatory when any of these conditions applies:

- work is high risk under **Review plans proportionally**;
- work is likely to cross context compaction, an interruption, a handoff, or more than one session;
- multiple implementation agents or people may act on the plan; a bounded read-only review alone
  does not count, but an actual implementation handoff or coordinated work still does;
- several dependent phases or cross-component consumers must remain coordinated;
- the task implements or materially audits an architecture record;
- migration, recorded replay, end-to-end validation, paid validation, or external mutation outside
  the **Routine external editorial correction** path is required;
- losing a constraint, non-goal, authenticated fact, or validation obligation could produce an
  incorrect delivery. The ordinary pre-write snapshot, payload, and read-back checks of a routine
  editorial correction do not alone activate this condition.

A formal plan still needs a linkable artifact when none of these persistence triggers applies.
Creating a Markdown file solely to provide that link does not trigger non-trivial classification,
high-risk review, or stronger closure. Keep its format and checks proportional to the underlying
work, including a minimal outcome, step, and check for a user-requested routine plan.

Persistence and risk are independent. Persistence determines where the execution contract
survives; it does not promote non-trivial local work or a bounded additive external action to high
risk. A persistent non-trivial local plan, a bounded additive external action, and a routine external
editorial correction with an independent persistence trigger use the compact template and their
proportional [closure](references/closure.md). A high-risk or architecture-governed plan uses the
full template, closure matrix, bidirectional traces, full reread, and independent second pass.

If otherwise routine work later meets the persistence gate because of handoff, interruption,
multiple actors, or another listed condition, treat it as non-trivial for planning ceremony and use
the compact persistent path. That promotion does not make it high risk by itself.

Before creating, resuming, moving, or closing a persistent plan, read
[persistent plan locations and lifecycle](references/persistent-plans.md). The trigger list above
stays here so a new task can discover the need for Markdown before taking the direct route.

## Inspect before planning

Read the applicable repository instructions and inspect the authoritative code, configuration,
tests, and existing records before choosing implementation steps. Do not create a plan from
filenames, issue prose, or remembered architecture alone.

Inspect enough evidence to create a truthful initial plan, then materialize the plan before the
first production edit. Mark unresolved facts as assumptions or investigation steps instead of
inventing implementation details.

Treat an item identifier carried from a `discussion-briefs` brief as a cross-document reference.
Within a plan and any brief that feeds it, the same identifier—`D1`, `T1`, `E2`, or any other item
label—must denote the same item and meaning, though the plan may summarize it. Never reuse a
brief identifier for an unrelated plan step, test, or decision; keep plan-only work descriptive
or give it a distinct, noncolliding label. When different briefs use the same identifier for
different items, qualify each reference by its brief or subject in the plan and in chat whenever
both could be meant. Check shared identifiers against their source briefs at handoff and closure.
Matching identifiers do not grant authority or bypass the brief's decision-recording gates.

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

For a formal plan, record these elements before implementation. For a direct route, establish the
outcome, scope, authoritative evidence, intended change, and proportional check without creating
a formal plan solely to fill this list:

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

Before a material step or replan adds or replaces a CI job, runner, container service, test
runtime, dependency, owner, or other execution route, inspect the existing approved workflow for
that task. Bind the chosen route once to the user request or explicit repository mandate, the
applicable skills, and the reason the existing route does not suffice (or the user's explicit
choice to depart). Dependent steps may cite that binding; do not demand a separate decision per
file. If a required premise or authorization is missing, leave the dependent step pending and
resolve it before editing. Technical review cannot supply the missing authorization.

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

Review plans proportionally before implementation. Obtain the advance choice above before any
separate reviewer or advisor is invoked:

Evaluate high-risk triggers first; any match overrides locality, reversibility, or apparent
simplicity. Then distinguish the remaining levels:

- **High risk:** Requires advisor review when available and a fresh-context independent review.
  High risk includes architecture, protocol or state-transition changes, security or authorization
  boundaries, migration or data-loss risk, destructive actions, authorized and verifiable external
  mutations that qualify for neither eligible external route, production-wide impact, and
  expensive or irreversible validation. Changes to shared agent instructions, skills, or
  permission allowlists are also high risk when they alter authorization,
  safety safeguards, risk classification, or mandatory review and closure gates; ordinary wording
  and narrowly scoped skill edits do not become high risk solely because of their location.
- **Non-trivial local and reversible:** Follow the model route to choose a compact plan or direct
  execution when no persistence trigger applies. For a compact plan, call the advisor when
  available; otherwise perform a focused author reread. Both model groups require an independent
  review of the result before completion. Cross-file or cross-component scope belongs here when no
  high-risk trigger applies.
- **Routine, local, and reversible:** Follow the model route. The autonomous group needs no
  independent reviewer solely for routine work; the supervised group does, even when execution is
  direct. Routine means one obvious owner, no material uncertainty, and cheap local validation.
  File count and obvious mechanical steps do not change that classification alone.
- **Routine external editorial correction:** Uses the direct procedure in the external-action
  reference. Independent persistence triggers select a compact plan; other high-risk triggers and
  inherited risk prevail.

Here, local means effects remain confined to the working tree or an isolated development
environment, with no external or production mutation. Reversible means the intended operation has
no credible data-loss or recovery hazard.

Before reviewing a high-risk plan, read the reviewer selection and pre-edit rules in
[reviews and completion](references/closure.md). Use that reference for every group-required or
user-selected independent review, including direct work without a plan. Apply every domain-required
review regardless of the planning route. A formal plan already in progress retains its highest risk
classification and review and closure gates for material continuations.

## Build an executable sequence

Order work by dependency and feedback speed:

1. Obtain any risk-required plan review described above after the advance user choice, and record
   it in the plan's **Plan review** section before any implementation step starts. A routine formal
   plan needs no review section when no review is required.
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
    with the risk-appropriate [audit](references/closure.md).

For a formal plan, complete its linked user-review gate after any required pre-edit plan review and
before the first implementation step. Do not treat the planned sequence or initial request as
evidence that the user has reviewed the plan. On resuming an active plan, offer its current link and
wait if that review and go-ahead cannot be established for its current execution contract. If the
plan already has completed steps from before this rule applied, preserve their actual chronology
and require the review before the next implementation step.

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

When the persistence gate applies, treat the persistent plan as the current record of execution
detail, bounded by the authorization and instructions above. Keep it compact and current; do not
append a chronological diary. Update it only when status, scope, evidence, dependencies,
validation obligations, blockers, or the chosen execution route materially changes.

At the end of a phase or before a material continuation, reconcile the active plan instead of
adding another account of the attempt. Replace obsolete "current" headings and steps with the
live outcome, next action, prerequisites, blockers, and closure state. Summarize a completed
attempt by its verdict, material limitations, and pointers to preserved evidence. Use the
authoritative CI, test, replay, issue, or review artifact for detailed protocols, transcripts, and
per-run reviews when retention is needed.

Before removing plan content, classify what still matters. Keep current decisions, prerequisites,
validation gates, and unresolved obligations in the active plan. Place durable product-design
decisions in their architecture owner, shared workflow rules in the governing skill, and executable
protection in its tests, fixtures, or replay, subject to the existing authorization and review
gates. If a required promotion is not authorized or complete, keep the obligation in the active
plan and mark that destination unresolved. Discard obsolete narration. Do not make a complete
plan snapshot or a supporting evidence file the sole owner of a current requirement.

When useful findings or source pointers would make the active plan unwieldy, an optional local
task evidence file may hold their concise conclusions. Follow an explicit repository convention;
otherwise use the ignored `implementation-plans/evidence/<task-slug>.md` convention in
[persistent plans](references/persistent-plans.md). Create it only when needed. It contains no
current instructions, full plan copy, raw transcript, or logs, and the active plan links to any
finding on which it still relies. Name the evidence owner and Git treatment when deviating from
the default. A reader should find the current execution contract without reading completed
attempts or local evidence first.

Keep conversational updates as a projection of that artifact: state the outcome or current status
and link the file. Do not reproduce the complete persistent plan or full external-action payloads in
chat unless the user asks for them.

Mirror its executable steps into the task's plan mechanism. The task plan may be shorter, but it
must not omit a material pending phase or report a status that conflicts with the persistent file.
The user must be able to see the plan path and every status transition.

Do not commit the plan merely because it exists. Follow the user's requested Git outcome and the
repository convention. Report whether the plan is tracked or untracked. Keep it available through
handoff. Follow the repository lifecycle when one exists; otherwise apply the default `active/` to
`completed/` transition in [persistent plans](references/persistent-plans.md). Remove a plan only
when the user requests removal.

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

Before a material replan, obtain the user's advance choice if the earlier plan choice did not cover
it; preserve completed work and hold dependent execution when that choice is missing.
Update the persistent plan before taking a materially different implementation route. Preserve the
current outcome and governing invariants, replace superseded steps instead of appending a narrative,
and synchronize the task-plan projection.
Offer the materially revised contract through its link and wait for renewed user review before
executing affected steps. Evidence-only or spelling corrections do not reopen this gate.
Updating the plan does not satisfy a missing user decision or bypass the global rule to stop when
a required assumption proves false. Recheck the material-route binding before executing the new
route and keep dependent steps pending until its prerequisites are resolved.

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

Before claiming completion, read [reviews and completion](references/closure.md). Its test-evidence
and group-required or user-selected review checks apply even when there is no formal plan. A
high-risk plan requires the full closure audit and a fresh independent second pass; compact and
direct work use their proportional gates. Do not mark any plan complete while a required check,
authorization, or review is unresolved.

## Compact plan format

Use `assets/compact-implementation-plan-template.md` for a persistent non-trivial local and
reversible plan, bounded additive external action, or routine external editorial correction with
an independent persistence trigger. Its conditional external-action section records the
authorization binding, items, governing-review status, read-back authority,
reconciliation state, and delivery evidence; omit that section for local work. Use the following
concise form for a task-plan projection or a linked non-trivial local and reversible formal plan
that does not meet the persistence gate. High-risk work always meets that gate and uses the full
persistent template. A routine edit that receives a formal plan because of the user's preference
needs just a linked outcome, step, and check, not this six-step form.

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
