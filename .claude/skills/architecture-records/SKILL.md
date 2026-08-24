---
name: architecture-records
description: "Create, organize, review, implement, or supersede durable cross-component architecture plans and decision records. Use when adding or moving architecture plans or ADRs, creating or updating architecture/README.md, changing a record lifecycle status, promoting a proposed plan to actual architecture, or synchronizing current architectural invariants into CLAUDE.md or AGENTS.md and operational behavior into README.md. Do not use for a temporary issue or merge-request checklist alone."
---

# Architecture records

Use this skill together with the `documentation` skill. Standardize durable
architecture context without turning temporary delivery tracking into permanent
documentation.

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

### 3. Establish the record structure

Reuse the existing architecture directory and index when present. When the repository
has no convention, create `architecture/README.md` from
`assets/architecture-readme-template.md` and adapt it to the repository language.
Create a new record from `assets/architecture-record-template.md`, removing all
placeholders and unused sections.

Keep the index concise. Describe each record's subject and purpose, but keep its
lifecycle status only in the record itself so status has one authoritative owner.

### 4. Apply the lifecycle

Use an explicit semantic state and adapt its literal wording to the repository
language:

- **Proposed:** Describe intended behavior, implementation order, risks, and
  acceptance criteria. State clearly that the record is not current functionality.
- **Implemented:** Rewrite speculative sections to describe actual behavior. Preserve
  durable rationale, boundaries, risks, and acceptance criteria. Remove or summarize
  temporary execution detail.
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
Update coupled artifacts in the same change instead of correcting only prose.

### 6. Synchronize current behavior

When implementation changes a cross-file ownership boundary, stage order, failure
meaning, recovery rule, or other invariant, update the repository instruction file
with a concise current statement and point to the architecture record for detail.
Never present proposed behavior as current instruction.

Update user documentation only when setup, operation, configuration, or user-visible
behavior changes. Follow the repository's instruction-file language and synchronization
rules; in this environment, write AI-facing instruction files in English.

### 7. Keep records durable

Point to authoritative code and configuration instead of copying maintained
inventories, defaults, model names, versions, limits, or deployment-specific values.
Preserve historical anchors. Use relative links that remain correct after moving the
record into its architecture directory.

### 8. Validate the result

Before handoff:

- Confirm that the record has one explicit lifecycle status.
- Confirm that the architecture index links to every current record.
- Confirm that proposed behavior is not described as implemented elsewhere.
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
