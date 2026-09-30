---
name: architecture-records
description: >-
  Create, organize, review, amend, implement, audit, or supersede durable cross-component
  architecture plans and decision records. Use when adding or moving architecture plans or ADRs,
  creating or updating architecture/README.md, changing a record lifecycle status, recording a
  deliberate user decision that changes an approved record, promoting a proposed plan to actual
  architecture, tracing architectural invariants through code and regression protection,
  investigating whether a recurring failure is architectural, or synchronizing current
  architectural invariants into the canonical AGENTS.md and operational behavior into README.md.
  Do not use for a temporary issue or merge-request checklist alone.
---

# Architecture records

Use this skill together with the `documentation` skill. Standardize durable
architecture context without turning temporary delivery tracking into permanent
documentation.

## Language

Write every architecture index, plan, ADR, decision record, and template-derived
architecture artifact in English, regardless of the repository's surrounding
documentation language. This rule applies to both new files and prose added to
existing architecture files.

When an affected architecture file is not in English or mixes languages, translate
the entire file and its coupled architecture index to English in the same change.
Never append English prose to a non-English architecture record and leave a mixed-
language artifact behind. Preserve literal strings that must remain exact, including
commands, paths, identifiers, API values, required UI labels, and quoted external
output. Continue to follow the `documentation` skill's language rules for coupled
files that are not architecture artifacts, such as user-facing README files.

## Normative force

Treat every imperative and every `must`, `require`, `never`, and `do not` in this
skill as a delivery gate, not as advice. Conditional language defines scope or an
explicitly permitted choice; it never makes an applicable requirement optional.
When this skill applies, do not mark a record implemented, approve the architecture,
or hand off the documentation while any applicable gate is violated. Correct the
artifact or move the misplaced information to its authoritative owner first. A
repository convention may make these gates stricter; it may not weaken them.
Plan, review, audit, model, and effort recommendations remain user choices under the global
instructions. These artifact requirements do not make an unselected process mandatory.

## Workflow

### 1. Inspect the repository convention

Read the repository instructions, existing architecture index, candidate records,
and the authoritative code, configuration, tests, and user documentation affected by
the decision. Follow an established repository convention when it is coherent; do not
create a competing structure.

### 2. Classify the artifact

Keep an artifact as a durable architecture record when it preserves one or more of
these concerns:

- Cross-component ownership or data flow.
- Non-local invariants, failure meanings, or recovery rules.
- A long-lived decision and its rationale or rejected alternatives.
- Risks, boundaries, migration constraints, or acceptance criteria needed to judge
  future changes.

The workflow rules of shared agent skills are not architecture records. A skill states
its own rules and gives the reason for each one in a sentence, because the skill is
what every agent loads where the rule applies, while a record kept in one repository is
out of reach from the others. Do not create an architecture record for them.

Keep a task-specific checklist, rollout log, or merge sequence in the issue or merge
request. A proposed architecture record may contain only the minimum prospective
implementation order needed to constrain the design and its architectural acceptance
criteria. It must never accumulate completed-step status, run-by-run evidence, or
chronological progress. After implementation, remove that temporary execution detail
and describe the resulting architecture.

An approved proposed record prescribes the implementation. Never retrofit it around
whatever the code currently does. If implementation diverges, correct the code and
its protection to match the approved record. Change the record first only when a
deliberate architecture decision changes the approved design, following section 7a;
never rationalize a defect by rewriting the plan after the fact.

### 2a. Hand off implementation planning

Use the `plan-implementation` skill before implementing a proposed or in-implementation
record, or before making a non-trivial correction governed by an implemented record.
The architecture record owns the durable design. A user-selected execution plan owns temporary
sequence and status; direct execution keeps its evidence in the task without a hidden plan.

Before production edits, identify the governing invariants, authoritative runtime owner,
affected consumers, ordered implementation slices, proportional test and replay coverage,
completion criteria, and replan conditions. Put them in a selected user-visible plan when one
exists, or establish them in direct task evidence. A persistence trigger strengthens the plan
recommendation but does not override the user's choice. Never keep execution status in the
architecture record.

When execution exposes a code defect under an adequate invariant, revise only the
execution route. When it exposes a missing or incorrect durable decision, amend or
supersede the architecture record first and then revise the affected execution
steps. Never let an implementation plan or direct route silently change ownership, authority, stage
order, terminal meaning, or recovery policy.

### 3. Establish the record structure

Reuse the existing architecture directory and index when present. When the repository
has no convention, create `architecture/README.md` from
`assets/architecture-readme-template.md` and keep it in English.
Replace or remove every sample index entry and placeholder link from that template;
never leave `record-file.md` or another template-only target in the resulting index.
Create a new record from `assets/architecture-record-template.md`, removing all
placeholders and unused sections.

Keep the index concise. Describe each record's subject and purpose, but keep its
lifecycle status only in the record itself so status has one authoritative owner.

### 3a. Keep record navigation canonical

Architecture records are AI-facing artifacts. Do not add a manual table of contents
to a plan, ADR, decision record, or architecture-record template. Use a clear heading
hierarchy inside each record and the concise `architecture/README.md` index for
cross-record navigation. The index is an authoritative catalog, not an internal table
of contents to duplicate inside each record.

When reviewing, editing, or closing a record that contains a manually maintained
table of contents, remove that section without removing the substantive headings it
referenced. This prevents a redundant heading inventory from becoming stale and
spending context tokens whenever an agent reads the record.

### 4. Apply the lifecycle

Use an explicit English semantic state:

- **Proposed:** Describe intended behavior, implementation order, risks, and
  acceptance criteria. State clearly that the record is not current functionality.
- **In implementation:** Separate delivered behavior from remaining gaps and do not
  present the record as fully available.
- **Implemented:** Rewrite speculative sections to describe actual behavior. Preserve
  durable rationale, boundaries, risks, and acceptance criteria. Remove temporary
  execution detail instead of preserving an implementation diary. Keep only compact
  traceability to authoritative executable evidence.
- **Superseded:** Preserve the record as a historical anchor, mark it superseded, and
  link to its replacement. Do not maintain two texts as concurrently authoritative for
  the same scope and phase. Section 7a defines the only split of authority: between
  a rule in force and an approved change that is still being implemented.

Do not mark a record implemented merely because code work started or most tasks are
complete. Require the described behavior and its required validation to be complete.

### 5. Maintain the source-of-truth hierarchy

Use this ownership model unless repository instructions define a stricter one:

- Root `AGENTS.md`: short, current, load-bearing project-wide invariants.
- `CLAUDE.md` and repository-wide Copilot instructions: compatibility paths that
  import or link to the root `AGENTS.md`; they never own a second copy.
- Architecture records: extended context, rationale, boundaries, risks, lifecycle,
  and architectural acceptance criteria.
- Code and configuration: executable behavior and current values.
- Tests and fixtures: executable expectations and regression protection.
- `README.md` or user docs: setup, operation, and user-visible behavior.

When sources disagree, determine which artifact represents the approved decision.
An approved current architecture record governs implementation until a deliberate
decision supersedes or amends it; current code is evidence of implementation, not
automatic authority to redefine the design. Update coupled artifacts in the same
change instead of correcting only prose.

### 6. Build implementation traceability

For every load-bearing invariant affected by implementation, maintain a compact
trace from the decision to its executable protection:

```text
invariant -> authoritative owner -> affected consumers -> tests -> recorded replay
```

Keep the trace in the architecture record unless the repository defines one canonical
traceability artifact linked directly from the record. Never omit the trace merely to
reduce document size. Point to symbols or focused source locations instead of copying
code, schemas, current values, or maintained inventories. Mark an unavailable element
explicitly; never imply that documentation, a unit test, an artifact fixture, a
provider-stage replay, and a full end-to-end replay provide equivalent coverage.

Require a recorded replay when a real incident exposed a cross-component protocol or
representation failure and sufficient raw inputs exist. The replay must consume the
recorded interaction completely, reject unexpected calls and silent network access,
and assert the architectural outcome rather than only a parser detail. When the
available capture is partial, build the narrowest faithful replay and state its
boundary; never fabricate the missing session.

Use the `test-quality` skill whenever implementation work adds or changes executable
regression protection. Follow its replay integrity, concurrency, property-testing,
skip, and flakiness rules as applicable.

### 7. Diagnose incidents before changing architecture

Classify the observed failure from evidence before deciding whether to amend an
existing record or create a new one:

- **Architecture:** ownership, authority, stage order, state transition, terminal
  meaning, or recovery policy is missing, conflicting, or intrinsically unsafe.
- **Implementation:** the approved invariant is sufficient, but code does not honor
  it consistently.
- **Model:** authenticated context and the protocol are sufficient, but a
  probabilistic judgment is wrong or malformed.
- **Operational:** transport, credentials, capacity, timeout, deployment, or external
  state prevented execution.

Record mixed causes when more than one applies. Correct an implementation defect
under the existing record when its invariant is unchanged. Amend that record when
the durable contract changes locally and most of its design still governs, including
when the revised rule also affects the flow, consequences, or traceability. Create or
supersede a record only for a substantial design replacement in which much of the
prior record will no longer govern the system.

Do not append an incident section merely because another merge request exposed the
same implementation defect. When an existing invariant already covers the failure,
change code, tests, and replay only. When the incident exposes a genuine contract gap,
edit the normative decision, invariant, flow, or failure semantics where it belongs;
do not add a chronological patch note.

Do not turn one provider response, log phrase, technology, or incident into a
deterministic semantic exception. Deterministic logic may authenticate and normalize
objective representation; semantic relevance and equivalence remain with the
appropriate semantic decision boundary.

### 7a. Record a deliberate decision that changes an approved record

Apply this section when the user deliberately decides to change the design that an
implemented record describes and instructs the recording of that decision. When
implementation is still pending, the record must show the approved change without
presenting it as current. When implementation has already closed, record the resulting
design without retaining a pending amendment. Follow this sequence.

#### 1. Identify the contract and choose the form

Read the whole current record, including guarantees expressed in its flow or prose,
not only its numbered invariants. Separate the changes the user approved from the
behavior the resulting architecture must preserve; this keeps an unchanged guarantee
from disappearing during a rewrite.

Choose the form by the extent of the architectural change and how much of the current
record will continue to govern after implementation. Map every passage that needs
synchronization, including rules, flow, consequences, diagrams, and traceability
tables; this map is a consistency check, not a threshold for a new file. Amend the
existing record when the change is localized to a rule or exception and the surrounding
design remains valid. Reserve a new record for a substantial replacement of the design,
when much of the prior record would cease to govern. Neither the number nor the type of
sections needing edits determines the form. Show the affected contract and chosen form
in chat, and ask before writing when the architectural reach is genuinely unclear.
The nature of the change sets recommended review depth and plan detail, not the
form of the text; `plan-implementation` treats an architecture change as high risk. A
selected plan reviewer may advise on the text before code.

For example, a scoped exception to one access rule takes an amendment even if its
description also appears in the flow, consequences, and traceability table. Replacing
a pipeline's decision owner and stage order so that much of its previous rules, flow,
and failure semantics no longer apply takes a new record.

#### 2. Check the recording boundary, then record

Record the authorized decision in its architecture owner before dependent code changes when
implementation is pending. With a selected plan and pre-edit reviewer, the bounded amendment
block or `Proposed` record, notice, and index entry may precede that review so it can examine
the real wording. If synchronization of affected passages, translation,
manual-table-of-contents removal, or other mandatory maintenance expands that edit, put the
expanded edit after the selected review; keep `registro pendente` for the record until then.
With a selected pre-edit reviewer but no plan, have it inspect the current record and proposed
diff before recording. Without a selected pre-edit reviewer, inspect the record and perform
authorized maintenance before recording; the absence of a reviewer creates no
staging deadlock.
Without a selected plan, no plan owner is invented. Section 8 synchronization waits for implemented
behavior, so proposed behavior is not presented as current.

If the approved change is already implemented, verify actual behavior and follow section 9
for result verification and any selected audit while reconciling the record. Use the same form
criterion without a temporary pending state: rewrite a localized rule and its affected passages
in the existing record, or make a substantial replacement `Implemented` and mark the
old record `Superseded` in the same change. Apply sections 10 and 11 for closure rather
than an implementation handoff. The paths below apply while implementation is pending.

Within that boundary, use the selected form:

- **Amendment block**, the default. Directly under the rule it changes, add a block
  that starts with the label `**Approved amendment, in implementation:**`, states the
  new rule, and says that the rule above stays in force until the amendment is
  implemented. Leave the current rule unmarked and unchanged, so that a reader sees
  what holds today and what is coming. Keep at most one pending block under a rule,
  and rewrite it when the user changes the decision. The block says which rule is in
  force, never the state of the code, and holds no date, plan link, or progress note,
  because a record carries no execution diary. Synchronize affected flow,
  consequences, diagrams, and traceability in the same record. While implementation
  is pending, preserve their current descriptions and identify the approved future
  effect as pending, with a concise reference to the block where useful. After
  implementation, rewrite the rule and affected passages as current and remove the
  block and pending qualifiers.
- **New record.** Create a record in `Proposed` that says which record it will
  supersede, add its entry to the index, and add one notice line to the status of the
  old record: a proposed replacement exists, with its link, and this record describes
  current behavior until that one is implemented. The new record replaces the old one
  whole: carry over every rule that the decision does not change, and leave no part of
  the old record governing after the replacement, because a superseded record keeps no
  authority and a rule left only there would be lost. The old record stays `Implemented`
  and in force. Mark it `Superseded` only when the new record becomes `Implemented`;
  superseding it earlier would leave no record describing what holds in the meantime.

#### 3. Derive the execution route

With a selected plan, derive it from the amended record after bounded recording. For mandatory
maintenance with a selected plan and pre-edit reviewer, put the maintenance and amendment in the
plan, obtain that review, then reconcile the plan with the amended record before handoff. Without
a selected plan, use a direct route with the same invariant-to-owner and validation checks;
if a pre-edit reviewer was selected, have it inspect the proposed record diff before recording.
In either path, for every guarantee affected by an ownership or flow change, connect the resulting
rule to the responsible path, an execution step and its validation. A guarantee
can need a new implementation path even when its behavior is unchanged; preserving its
wording alone does not establish that path. Keep unverified ownership as an
investigation prerequisite, not an assumed implementation fact.

#### 4. Cross-check before handoff

Read the resulting record and any selected plan together before reporting the recording complete.
For a whole replacement, check that every unchanged guarantee is present and that no
section leaves the old record governing after supersession. Excluding a behavior change
from the decision's goals does not exclude that behavior's rules from a whole replacement.
Check that the execution route carries affected guarantees through prerequisites and validation
of the changed path. This checks the handoff, not completed code; selected independent review
and author implementation closure follow their own gates.

The session that conducted the discussion makes authorized recording before handing the record
and any selected plan to an implementing session, because it holds the decision's reasons.
Section 11 says which checks apply. Tell the implementer which records were amended.

While both texts coexist, the current rule stays in force for every consumer, and the
amendment or the `Proposed` record prescribes only the authorized future work. Partial progress
lives in a selected plan or direct task evidence, never in the record. When the
implementation closes, rewrite the rule and its affected flow, consequences, and
traceability and remove the block and pending qualifiers, or remove the notice line
and supersede the old record, whether or not the lifecycle state of the amended
record changes.

### 8. Synchronize current behavior

When implementation changes a cross-file ownership boundary, stage order, failure
meaning, recovery rule, or other invariant, update the repository instruction file
with a concise current statement and point to the architecture record for detail.
Never present proposed behavior as current instruction.

Update user documentation only when setup, operation, configuration, or user-visible
behavior changes. Follow the repository's instruction-file language and synchronization
rules; in this environment, write AI-facing instruction files in English.

### 9. Verify conformance and offer a full audit

Before declaring implementation complete or moving a record to `Implemented`, verify the record's
claims against the actual implementation and validation evidence. Strongly recommend a full
conformance audit and explain its scope through `plan-implementation`; perform it only if selected.
Otherwise verify the affected claims proportionally and report limits, without a substitute audit.

For a selected full audit, reread the entire governing architecture record, every coupled current
record, any selected implementation plan, and the coupled repository instructions. Then reconstruct
the actual runtime flow from code, configuration, tests, and recorded artifacts rather
than from the intended plan or a prior summary.

Account for every architectural invariant, affected consumer, failure path, and required
validation boundary. With a selected full implementation plan, record a completed closure-audit
matrix and row statuses there; keep only durable invariant traceability in the architecture
record. Without a plan, perform the same author evidence accounting without creating a hidden
matrix artifact.

Audit both directions:

```text
architecture invariant -> [chosen plan step] -> code/config owner -> consumers -> test/replay
changed artifact -> user authorization and instructions -> [chosen plan scope] -> governing rule
```

Check that:

- every invariant has one authoritative runtime owner and all consumers use it;
- no legacy, fallback, cache, renderer, or compatibility path reconstructs a second
  authority or preserves the superseded meaning;
- deterministic gates decide only objective facts and semantic gates receive the
  authenticated context needed for probabilistic decisions;
- every terminal path is explicit, observable, and preserves already authenticated
  independent outcomes;
- retries, timeouts, malformed provider output, partial progress, duplicate events,
  and stale state have bounded and documented meanings;
- incident-derived replays fail before the fix and protect the cross-component
  outcome after it.

Recommend an independent second pass for a lifecycle transition or non-trivial correction; perform
it only when selected. Give that reviewer fresh context, the records, any chosen plan, final diff,
and validation artifacts without the intended conclusion. Do not substitute an author second
reading for a declined review. A pre-edit review alone does not select a final review or full audit.

Any change after the audit to an in-scope or coupled artifact—including code,
configuration, tests, fixtures, implementation plans, architecture records, repository
instructions, or user documentation—invalidates affected audit conclusions. Reopen the
affected work and rerun invalidated checks. Recheck the review within the user's selected scope;
ask before an additional full audit or second pass that the earlier choice did not cover.

If the described behavior or required acceptance evidence is missing, keep the record proposed or
in implementation. A selected audit holds its dependent phase until completed or withdrawn;
declining an audit alone does not prevent the lifecycle transition. Do not call the architecture
implemented based only on code presence or passing unit tests.

### 10. Keep records durable

Point to authoritative code and configuration instead of copying maintained
inventories, defaults, model names, versions, limits, or deployment-specific values.
Preserve historical anchors. Use relative links that remain correct after moving the
record into its architecture directory.

Architecture records are normative design artifacts, not project journals. They must
not contain timestamps, per-run costs or token counts, mutable commit SHAs, suite pass
counts, raw logs, rollout narration, or merge-request-by-merge-request progress.
Store those execution facts only in their authoritative issue, merge request, replay
manifest, quality expectation, or test artifact. Reference only the stable
behavior-oriented artifact identifiers required for traceability. Retain a specific
incident in the record only when a concise statement of its cause is indispensable to
the rationale; omit its chronological execution details and mutable metrics.

Before marking a record implemented, remove future
delivery sequences, completed checklists, progress reports, repeated implementation
summaries, and raw validation metrics. The resulting record must contain the
decision, responsibilities, invariants, flow, failure semantics, risks, rejected
alternatives, and a compact decision-to-code-to-test/replay trace.

Apply the same content cleanup when the implementation of an amendment recorded under section 7a
closes, even though the amended record was already `Implemented`: rewrite the amended
rule and affected flow, consequences, and traceability, then remove the amendment
block and pending qualifiers. For a replacement, remove the notice from the old record.

### 11. Validate the result

Apply this list at two moments, because a record is handed over both before and after
its implementation exists: at closure, apply the artifact checks and any selected audit checks; at
the implementation handoff, when the session that recorded a decision passes the record and
any selected plan to an implementing session, apply every check except the ones that presuppose
a finished implementation, which are runtime traceability with its executable
protection, recorded replay, competing obsolete paths, terminal states, the description
of the resulting architecture, any selected plan reread with its closure-audit matrix, the two
traces, the second conformance pass, and the removal of closed amendment blocks and
replacement notices.

Before handoff:

- Confirm that the record has one explicit lifecycle status.
- Confirm that the architecture index links to every current record.
- Confirm that proposed behavior is not described as implemented elsewhere.
- Confirm that each implemented invariant is traceable to its runtime owner,
  affected consumers, and proportional executable protection.
- Confirm that real cross-component incidents have a faithful recorded replay when
  the required raw data exists, and that partial replays are not labeled end to end.
- Confirm that obsolete paths cannot compete with the current source of authority.
- Confirm that every amendment block sits directly under its rule, carries its label,
  says that the rule above stays in force, and holds no diary content; that no rule
  has more than one; and that no block or replacement notice remains for an
  implementation that closed.
- Confirm that affected flow, consequences, diagrams, and traceability distinguish
  current behavior from an approved pending amendment, and describe only the resulting
  behavior after implementation closes.
- Confirm that every runtime terminal state remains observable and semantically
  consistent through rendering, persistence, retries, and reuse.
- Fail the validation when diary residue exists: merge-request sequences, timestamps,
  changing SHAs, per-run costs or token counts, suite totals, or repeated delivery
  narratives. Keep an occurrence only when its concise cause is indispensable to the
  architectural rationale; otherwise remove it or move it to the artifact that owns
  the execution evidence before handoff.
- Confirm that an implemented record describes the approved resulting architecture,
  rather than reverse-engineering or legitimizing incidental current behavior.
- If a full audit was selected, confirm its forward and reverse traces and any chosen matrix
  support its verdict. Choosing a plan alone does not select this audit.
- Confirm completion of selected reviews and second passes, or record their explicit withdrawal.
  Do not require a substitute author audit or second reading when none was selected.
- Verify relative links and moved-file paths.
- Confirm that architecture records and their templates contain no manual table of
  contents. Keep the heading hierarchy clear and verify that the architecture index
  links to each current record instead.
- Run the repository's Markdown or whitespace checks when available and inspect
  untracked files as well as tracked diffs.
- Report changed files, lifecycle transitions, and validation performed. Do not commit a
  record merely because it is complete. Follow the user's requested Git outcome and the
  repository convention.

## Templates

- Use `assets/architecture-readme-template.md` only when no architecture index exists.
- Use `assets/architecture-record-template.md` as a starting structure, not as text to
  copy without adapting language, scope, headings, and sources.
