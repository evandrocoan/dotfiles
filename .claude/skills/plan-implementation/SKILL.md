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
  Recommend a user-visible persistent Markdown plan when work may span phases, agents,
  interruptions, or context compaction; create it only when the user chooses it.
---

# Plan implementation

Recommend the smallest plan that would make the requested delivery reliable. Keep durable design
authority in architecture records, as `architecture-records` classifies it; that skill excludes the
workflow rules of shared agent skills, which live in the skills themselves. Keep every formal plan
user-visible. When the user chooses a plan and a persistence trigger applies, keep detailed
execution state in Markdown and project its current steps into the task plan.

## Determine the planning mode

Classify the request before editing. Identify the acting agent's effective settings under the
global instructions and recommend settings for its role without overriding the user's choice.
An unknown setting cannot be replaced with a conservative plan. Read
[model-aware routing](references/model-routing.md) for every implementation edit to apply the
acting group's plan and review thresholds, and when recommending a model, reasoning effort, or
reviewer. The applicable user's explicit request and higher-priority question-only or read-only
rules come first. Risk and persistence shape validation and process recommendations; the user
decides whether to have a formal plan, review, or audit and which model and effort to use.

- **Plan only:** When the user asks for a plan, asks to review or approve a plan, or explicitly
  says not to implement, inspect enough authoritative evidence to make the plan credible, offer its
  link and explanatory summary in chat, and stop. Reviewing a plan-only deliverable does not
  authorize implementation.
- **Plan and execute:** When the user asks to change, fix, build, or implement and chooses a formal
  plan, offer its link and explanatory summary for user review and wait for an explicit go-ahead.
  After that response, continue through the authorized in-scope
  steps without requesting approval for each step. Use the direct route when eligible.
- **No formal plan:** When the user declines a plan or the model route does not call for offering
  one, present only the explanatory summary in chat and wait for explicit approval before direct
  work. Declining the document does not approve implementation. All independent gates still apply;
  an unanswered choice remains pending. Verify the expected outcome without creating a hidden plan.

Strongly recommend a formal plan for every high-risk request and persistence trigger below. The
recommendation does not make the plan compulsory. For other work, follow the model route and any
explicit user preference. Touching several files or performing several obvious edits under one
owner does not by itself make otherwise
routine work non-trivial.

Before drafting a formal plan or starting an advisor, independent review, domain review, or
structured author audit, obtain the user's choice. An explicit request for a plan or
review already answers that dimension for the current scope. Otherwise use minimal read-only
triage to state the recommendation and concrete reason; both choices are optional. Ask at the
relevant implementation task boundary when foreseeable, before substantial dependent work or
reviewer effort. Question-only requests do not open an implementation choice. One clear answer
may cover named pre-edit and final reviews. Follow the global visible-question rule: present
pending choices in the final response and wait. Direct work may continue after an explicit decline
only after the proposal approval below and when every independent gate permits it. Ordinary author
verification is not a separate review invocation.
Preserve the chronology of existing plans and reviews. Ask
before an uncovered material replan or reviewer invocation. This advance choice does not replace
the user's review and approval of the concrete proposal before implementation on either route.

A bounded additive external action that meets every condition in
[external-action routes](references/external-actions.md) uses the compact path when the user
chooses a plan. Read that reference before classifying or performing an external write.
Eligibility selects risk,
template, and closure; it never overrides an explicit plan-only request or supplies permission to
execute. When execution is authorized without a selected plan, use the direct route with the same
authorization, pre-write, reconciliation, and read-back checks. External mutation strongly favors
persistence even though externality alone does not make that narrowly defined action high risk.
A routine external editorial correction uses the direct path in that reference; its external
location alone requires
neither a formal plan nor independent review. Recommend review according to model, domain, and
inherited risk. Neither path overrides authorization or plan-only mode.

## Present the proposal and wait for approval

Before implementation on either route, present a concise, self-contained summary in the final chat
response. Explain the problem or objective, what will change, how those changes address it, the
expected result, and how it will be checked. A list of files or steps alone does not explain the
solution. Keep the summary proportional to the task and understandable without opening an artifact.

With a formal plan, accompany the summary with the complete current plan's link and measured size
as specified below. Without a formal plan, present only the summary in chat; do not create a plan
artifact to satisfy this requirement. End the turn and wait for explicit user approval before the
first implementation step. The initial task request, declining a formal plan, silence, and an
advisor or reviewer verdict do not substitute for approval of the presented proposal. Read-only
scoping and separately selected reviews may make the proposal concrete before this gate.

An explicit instruction to implement an unchanged proposal already presented in chat satisfies
this gate. Continue the approved scope without requesting approval for each step. If the proposed
scope, approach, or expected effects change materially, present a revised summary and, when a plan
exists, its updated link; wait for renewed approval before affected steps. Evidence-only or
spelling corrections do not reopen approval. Plan-only mode still requires a later implementation
instruction; reviewing its deliverable does not itself authorize execution.

## Materialize the plan visibly

Never keep a formal plan only in hidden reasoning or conversation memory. Give every formal plan a
complete current artifact with a clickable link. Use a Markdown file under the task's plan
lifecycle by default; a task-plan mechanism may substitute only when its link opens the complete
current plan for the user. Chat prose alone does not supply the artifact. When first presenting a
formal plan or offering a materially revised version for user review, provide its link, a concise
explanatory summary under **Present the proposal and wait for approval**, and its measured size as
the line and word counts of the complete linked version. Keep ordinary progress updates concise
without repeating this presentation. Apply that approval gate before implementation and after a
material revision; the link alone does not satisfy the presentation requirement.

Use these two layers when the user chooses a plan and a persistence trigger applies:

- **Persistent execution plan:** Store the complete current execution contract in Markdown.
- **Task plan:** Project the current steps and statuses into the environment's visible plan
  mechanism for concise progress tracking.

Strongly recommend a persistent plan when any of these conditions applies:

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

Persistence and risk are independent. When a plan is chosen, persistence determines where its
execution contract survives; it does not promote non-trivial local work or an additive action to
high risk. A chosen persistent non-trivial local plan, a bounded additive external action, and a
routine external editorial correction with another persistence trigger use the compact template
and their proportional [closure](references/closure.md). For high-risk or architecture-governed
work, recommend the full template and a full conformance audit. Use the plan detail the user
chooses; choosing a short plan does not choose an audit, closure matrix, or second pass.

If otherwise routine work later meets a persistence trigger because of handoff, interruption,
multiple actors, or another listed condition, recommend the compact persistent path. That
trigger does not make the work high risk by itself or override a declined plan.

Before creating, resuming, moving, or closing a persistent plan, read
[persistent plan locations and lifecycle](references/persistent-plans.md). The trigger list above
stays here so a new task can discover the need for Markdown before taking the direct route.

## Inspect before planning

Read the applicable repository instructions and inspect the authoritative code, configuration,
tests, and existing records before choosing implementation steps. Do not create a plan from
filenames, issue prose, or remembered architecture alone.

When the user chose a plan, inspect enough evidence to make it truthful and materialize it before
the first production edit. Mark unresolved facts as assumptions or investigation steps instead of
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
this skill. Treat the approved record as design authority and derive the selected plan or direct
execution checks from it. Do not alter the record to legitimize incidental current code.

When carrying out a deliberate user decision that changes an approved record, follow
`architecture-records` section 7a. With a chosen plan, use its specified order for bounded
recording or required maintenance and offer the linked plan before dependent implementation.
Without a chosen plan, obtain any selected pre-edit review of the proposed record diff, record
the authorized decision in the architecture owner with the skill's author checks, then proceed
directly against the amended record. A chosen separate review follows its selected phase; a
declined review creates no recording deadlock. Complete
authorized recording before an implementing-session handoff, and describe which owners were
actually updated without presenting pending work as completed.

Load the task-specific skills required by the work before planning their stages. In particular,
use `test-quality` for executable validation, `documentation` for durable documentation,
`dependency-decisions` for dependency choices, and the relevant delivery or infrastructure skill
when those concerns are in scope.

## Establish the execution contract

For a formal plan, record these elements before implementation. For a direct route, establish the
outcome, scope, authoritative evidence, intended change, and proportional check without creating
a formal plan solely to fill this list; present the resulting summary for approval:

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

- **High risk:** Strongly recommend a full plan, advisor when useful, and a fresh-context
  independent pre-edit and final review. High risk includes architecture, protocol or state
  transitions, security or authorization boundaries, migration or data-loss risk, destructive
  actions, authorized and verifiable external
  mutations that qualify for neither eligible external route, production-wide impact, and
  expensive or irreversible validation. Changes to shared agent instructions, skills, or
  permission allowlists are also high risk when they alter authorization,
  safety safeguards, risk classification, or mandatory review and closure gates; ordinary wording
  and narrowly scoped skill edits do not become high risk solely because of their location.
- **Non-trivial local and reversible:** Follow the model route to recommend a compact plan or direct
  execution. Recommend an advisor when useful and an independent result review, especially for
  the supervised group. Verify the edited result proportionally on either route.
  Cross-file or cross-component scope belongs here when no high-risk trigger applies.
- **Routine, local, and reversible:** Follow the model route. Recommend a reviewer for the
  supervised group, even when execution is direct; ordinarily recommend none for the autonomous
  group. Routine means one obvious owner, no material uncertainty, and cheap local validation.
  File count and obvious mechanical steps do not change that classification alone.
- **Routine external editorial correction:** Uses the direct procedure in the external-action
  reference. Other persistence triggers strengthen a compact-plan recommendation; high-risk
  triggers and inherited risk prevail.

Here, local means effects remain confined to the working tree or an isolated development
environment, with no external or production mutation. Reversible means the intended operation has
no credible data-loss or recovery hazard.

Before a selected high-risk plan review, read the reviewer selection and pre-edit rules in
[reviews and completion](references/closure.md). Use that reference for every user-selected
independent review, including direct work without a plan. Domain reviews and formal author audits
remain user choices; substantive validation and authorization still apply. An existing plan retains
its highest risk classification for recommendations on material continuations; that classification
does not impose an audit or override the user's revocable review choice.

## Build an executable sequence

Order work by dependency and feedback speed:

1. Obtain a selected pre-edit review before dependent implementation and record its findings in
   the plan when one exists. Without a selected review, perform the author evidence check.
2. Reproduce or authenticate the current failure when one exists.
3. Establish or update the smallest failing regression protection.
4. Change the authoritative owner of the behavior.
5. Update every affected consumer of that contract.
6. Remove competing or superseded behavior rather than leaving parallel authority.
7. Run focused checks after the smallest meaningful slice.
8. Run broader integration, replay, and suite-level checks after the flow is connected.
9. Perform operational or paid live validation only when it is useful and authorized under the
   applicable rules.
10. Close work with outcome, validation, diff, and status checks and any selected
    [review or audit](references/closure.md).

On either route, complete proposal approval after any selected pre-edit review and before the first
implementation step. Do not treat the planned sequence or initial request as evidence of approval.
When resuming, establish approval for the current proposal; if it is missing, present the summary
and any chosen plan's current link, then wait. Preserve the actual chronology of steps completed
before this rule applied and require approval before the next implementation step.

For a deliberate architecture decision with a selected pre-edit plan review, use the bounded
recording order in `architecture-records` section 7a: its limited amendment may precede that
review so the reviewer sees the actual wording. When required maintenance exceeds that boundary,
put maintenance and amendment after the selected review. With no selected pre-edit review, the
author inspects the affected record and maintenance before recording; no review-only staging
exception is needed. A selected formal plan still needs its linked user go-ahead before
implementation.

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
recording and every actual document owner named for the decision carries it. An owner may be a
selected plan, an architecture record, or an issue. Do not invent a plan owner when the user
declined a plan. Code or skill text is a work target, never a decision-recording owner.

With the user's instruction to record, the marker for that decision must not block the work that
resolves it. Distinguish these paths:

- With a selected pre-edit review, follow the bounded-before-review or maintenance-after-review
  order in `architecture-records` section 7a. Keep the marker until actual owners are updated.
- Without a selected separate review, perform the author inspection and authorized recording in
  the real owner. A declined plan or reviewer alone does not keep `registro pendente` alive.

Each path waives only the pending marker for the decision it resolves, not recording authority,
other pending decisions, or any other prerequisite. Keep the marker until every actual named owner
carries the decision. Dependent implementation remains held until recording and any selected
pre-edit review are complete. The discussion or planning session performs authorized architecture
recording before handing it to an implementing session, as section 7a requires.

When a formal plan exists, reread it entirely after context compaction, interruption, session
restart, material replan, or agent handoff. Give an authorized delegated agent the plan path and
exact step it owns. For direct work, reconstruct the request, decisions, and evidence instead.

## Keep planning state in the correct place

When a chosen plan has a persistence trigger, treat it as the current record of execution detail,
bounded by the authorization and instructions above. Keep it compact and current; do not
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

After implementation, close any chosen execution plan. Preserve durable rationale and invariants in their
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

Before a material replan of a selected plan, ask about any new plan or review action the earlier
choice did not cover. A declined new action does not revive it as a mandatory gate. Preserve
completed work and hold affected execution for revised proposal approval on either route or another
independent prerequisite. If a formal plan remains selected, update
it before taking a materially different route. Preserve
the outcome and invariants, replace superseded steps, synchronize the task-plan projection, offer
the revised link and summary, and wait for renewed user review before affected steps. Without a
formal plan, present the revised summary and wait before materially changed steps. Withdrawing the
plan does not approve a changed proposal; direct work may resume against the unchanged approved
summary after independent prerequisites are resolved, without a substitute plan.
Evidence-only or spelling corrections do not reopen proposal approval. A replan does not
satisfy a missing user decision or bypass the global rule to stop when a required assumption
proves false. Recheck the material-route binding before the new route.

Change only the execution route when the approved design remains valid. Amend or supersede the
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
and user-selected review checks apply even when there is no formal plan. For high-risk work,
strongly recommend a full conformance audit with both trace directions; run it only if selected.
Do not replace a declined review with a mandatory author audit or second reread.
Do not mark a selected plan complete while its linked user review, a required check, authorization,
or a selected review is unresolved.

## Compact plan format

Use `assets/compact-implementation-plan-template.md` for a chosen persistent non-trivial local and
reversible plan, bounded additive external action, or routine external editorial correction with
an independent persistence trigger. Its conditional external-action section records the
authorization binding, items, governing-review status, read-back authority,
reconciliation state, and delivery evidence; omit that section for local work. Use the following
concise form for a task-plan projection or a linked non-trivial local and reversible formal plan
that has no persistence trigger. Recommend the full template for high-risk work, while honoring
the user's choice of a shorter plan. A routine edit that receives a formal plan needs just a linked
outcome, step, and check, not this six-step form.

```text
Outcome: <observable result>
Constraints: <invariants, non-goals, and authorization boundaries>
Evidence: <verified current behavior and open assumptions>

1. <author check and any selected pre-edit review> — mechanism: <author, advisor, or reviewer>
   — findings: <concise applied or rejected findings>
2. <reproduce or authenticate> — premise: <what must already be true, and its proof> — validation: <specific check>
3. <change authoritative owner> — premise: <what must already be true, and its proof> — validation: <specific check>
4. <update affected consumers> — premise: <what must already be true, and its proof> — validation: <specific check>
5. <integrate and replay> — premise: <what must already be true, and its proof> — validation: <specific check>
6. <verify result, finish any selected review or audit, and deliver>
   — premise: <what must already be true, and its proof> — validation: <specific check>

Replan if: <material invalidating conditions>
```

Expand the plan only when additional detail changes how the implementation will be performed or
validated. Record premises only when they are material and non-obvious. An unverified material
premise stays in `Evidence` as an open assumption until it is verified; its dependent step does not
run.
