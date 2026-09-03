---
name: architecture-records
description: "Create, organize, review, implement, audit, or supersede durable cross-component architecture plans and decision records. Use when adding or moving architecture plans or ADRs, creating or updating architecture/README.md, changing a record lifecycle status, promoting a proposed plan to actual architecture, tracing architectural invariants through code and regression protection, investigating whether a recurring failure is architectural, or synchronizing current architectural invariants into CLAUDE.md or AGENTS.md and operational behavior into README.md. Do not use for a temporary issue or merge-request checklist alone."
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

Keep a task-specific checklist, rollout log, or merge sequence in the issue or merge
request. A proposed architecture record may retain delivery order and architectural
acceptance criteria. After implementation, convert temporary execution detail into a
faithful description of the resulting architecture.

Treat an approved proposed record as a prescription for implementation, not as prose
to retrofit around whatever the code currently does. If implementation diverges,
correct the code and its protection to match the approved record. Change the record
first only when a deliberate architecture decision changes the approved design; do
not silently rationalize a defect by rewriting the plan after the fact.

### 3. Establish the record structure

Reuse the existing architecture directory and index when present. When the repository
has no convention, create `architecture/README.md` from
`assets/architecture-readme-template.md` and keep it in English.
Create a new record from `assets/architecture-record-template.md`, removing all
placeholders and unused sections.

Keep the index concise. Describe each record's subject and purpose, but keep its
lifecycle status only in the record itself so status has one authoritative owner.

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
  link to its replacement. Do not maintain two records as concurrently authoritative.

Do not mark a record implemented merely because code work started or most tasks are
complete. Require the described behavior and its required validation to be complete.

### 5. Maintain the source-of-truth hierarchy

Use this ownership model unless repository instructions define a stricter one:

- `CLAUDE.md`, `AGENTS.md`, or equivalent: short, current, load-bearing invariants.
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

Keep the trace in the architecture record when it aids future maintenance. Point to
symbols or focused source locations instead of copying code, schemas, current values,
or maintained inventories. Mark an unavailable element explicitly; never imply that
documentation, a unit test, an artifact fixture, a provider-stage replay, and a full
end-to-end replay provide equivalent coverage.

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
the durable contract was incomplete. Create or supersede a record only when the
ownership model, authority boundary, stage order, failure meaning, or recovery policy
actually changes.

Do not append an incident section merely because another merge request exposed the
same implementation defect. When an existing invariant already covers the failure,
change code, tests, and replay only. When the incident exposes a genuine contract gap,
edit the normative decision, invariant, flow, or failure semantics where it belongs;
do not add a chronological patch note.

Do not turn one provider response, log phrase, technology, or incident into a
deterministic semantic exception. Deterministic logic may authenticate and normalize
objective representation; semantic relevance and equivalence remain with the
appropriate semantic decision boundary.

### 8. Synchronize current behavior

When implementation changes a cross-file ownership boundary, stage order, failure
meaning, recovery rule, or other invariant, update the repository instruction file
with a concise current statement and point to the architecture record for detail.
Never present proposed behavior as current instruction.

Update user documentation only when setup, operation, configuration, or user-visible
behavior changes. Follow the repository's instruction-file language and synchronization
rules; in this environment, write AI-facing instruction files in English.

### 9. Audit the implemented architecture

Before declaring implementation complete, reconstruct the actual runtime flow from
code, configuration, tests, and recorded artifacts rather than from the intended
plan. Check that:

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

If any required trace or audit item is unresolved, keep the record proposed or in
implementation using the repository's established lifecycle wording. Do not call the
architecture implemented based only on code presence or passing unit tests.

### 10. Keep records durable

Point to authoritative code and configuration instead of copying maintained
inventories, defaults, model names, versions, limits, or deployment-specific values.
Preserve historical anchors. Use relative links that remain correct after moving the
record into its architecture directory.

Architecture records are normative design artifacts, not project journals. Do not
duplicate timestamps, per-run costs or token counts, mutable commit SHAs, suite pass
counts, raw logs, rollout narration, or merge-request-by-merge-request progress.
Store exact execution facts in their authoritative issue, merge request, replay
manifest, quality expectation, or test artifact. Reference a stable behavior-oriented
artifact when useful, and retain a specific incident only when its concise rationale
is necessary to understand the architectural decision.

Before marking a record implemented, perform an editorial closure pass. Remove future
delivery sequences, completed checklists, progress reports, repeated implementation
summaries, and raw validation metrics. The resulting record should contain the
decision, responsibilities, invariants, flow, failure semantics, risks, rejected
alternatives, and a compact decision-to-code-to-test/replay trace.

### 11. Validate the result

Before handoff:

- Confirm that the record has one explicit lifecycle status.
- Confirm that the architecture index links to every current record.
- Confirm that proposed behavior is not described as implemented elsewhere.
- Confirm that each implemented invariant is traceable to its runtime owner,
  affected consumers, and proportional executable protection.
- Confirm that real cross-component incidents have a faithful recorded replay when
  the required raw data exists, and that partial replays are not labeled end to end.
- Confirm that obsolete paths cannot compete with the current source of authority.
- Confirm that every runtime terminal state remains observable and semantically
  consistent through rendering, persistence, retries, and reuse.
- Audit for diary residue: merge-request sequences, timestamps, changing SHAs,
  per-run costs or token counts, suite totals, and repeated delivery narratives. Keep
  an occurrence only when it is a necessary rationale anchor; otherwise remove it or
  move it to the artifact that owns the execution evidence.
- Confirm that an implemented record describes the approved resulting architecture,
  rather than reverse-engineering or legitimizing incidental current behavior.
- Verify relative links and moved-file paths.
- Keep an existing table of contents synchronized; add one only when the
  `documentation` skill calls for it.
- Run the repository's Markdown or whitespace checks when available and inspect
  untracked files as well as tracked diffs.
- Report changed files, lifecycle transitions, and validation performed. Do not commit
  unless the user explicitly requests it.

## Templates

- Use `assets/architecture-readme-template.md` only when no architecture index exists.
- Use `assets/architecture-record-template.md` as a starting structure, not as text to
  copy without adapting language, scope, headings, and sources.
