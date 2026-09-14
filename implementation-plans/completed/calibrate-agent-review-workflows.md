# Implementation plan: Calibrate agent review workflows

**Status:** Completed
**Mode:** Plan and execute

## Outcome

Shared agent workflows retain evidence-backed review for risky work without imposing full review,
reread, and audit ceremony on routine changes. Claude uses Sonnet for routine execution and Fable
for contextual supervision and independent review, and its tracked settings match the active file.

## Scope

### In scope

- Make plan review, independent review, closure rereads, and absence proof proportional to risk.
- Keep plan evidence concise instead of accumulating a chronological execution diary.
- Use Sonnet for routine Claude work and Fable for both contextual advice and fresh-context audit.
- Remove the hidden `assume-unchanged` state from `.claude/settings.json`.

### Out of scope

- Changing Codex's selected model or MCP configuration.
- Changing project-specific repository instructions.
- Committing or pushing these changes.

## Governing decisions and invariants

- `AGENTS.md` governs this repository.
- Shared safeguards stay centralized in `.codex/AGENTS.md`, exposed to Claude by the existing
  `.claude/CLAUDE.md` symlink.
- Classify review risk before execution:
  - routine, local, reversible work needs no formal plan, advisor, or independent reviewer;
  - non-trivial but local and reversible work uses a compact plan and advisor when available, but
    needs no independent reviewer by default;
  - high-risk work requires an advisor when available, independent review, and complete closure
    audit. Evaluate high-risk triggers first; any such trigger overrides locality or reversibility.
    High risk includes architecture, protocol or state transitions, security or authorization,
    migration or data loss, external or destructive actions, production-wide impact, and expensive
    or irreversible validation. Cross-file or cross-component scope alone is not high risk.
- Use one routine/no-plan definition: one obvious owner, no material uncertainty, local and
  reversible effects, and cheap local validation. File count or step count alone does not change
  that classification.
- Treat persistence and risk as independent dimensions. Non-trivial local work that meets the
  persistence gate uses a compact persistent template and lifecycle but no mandatory full closure
  matrix or bidirectional traces. High-risk work retains the full template, closure matrix, traces,
  complete reread, and independent second pass.
- A material follow-up or replan within an existing formal plan inherits the plan's highest risk
  classification. Formatting-only or evidence-only corrections keep their focused recheck.
- Changes to shared agent instructions, skills, or permission allowlists are high risk when they
  alter authorization, safety safeguards, risk classification, or mandatory review and closure
  gates; ordinary wording or narrowly scoped skill edits do not become high risk solely by location.
- Prefer model diversity for independent review, but an explicit user-pinned same-model advisor and
  reviewer is authoritative. Independence still requires fresh context, withholding the intended
  verdict, an authoritative baseline, and disclosure of the correlated-model residual risk.
- For a consequential absence claim, require a known-present control when a wrong root, matcher,
  pathspec, filter, exclusion, or inaccessible source could produce the empty result. Exact-target
  checks and deterministic universe queries that establish their own scope are exempt.

## Current evidence and assumptions

### Verified evidence

- Commit `c05c99f` made every formal plan use an advisor and added blanket later-turn rereads and
  same-turn negative-proof requirements.
- Before correction, the plan skill already forbade chronological diaries but its wide evidence
  table and mandatory review language encouraged them in practice. The affected surfaces were
  pre-execution review, per-phase rereads, closure rereads, second-pass criteria, the template
  matrix, and the global reread and negative-proof rules.
- Before correction, the committed Claude default was Opus/max while the active settings file was
  Fable/xhigh and marked `assume-unchanged`; advisor and independent reviewer both used Fable.
- Claude Code 2.1.268 documents `sonnet`, `opus`, and `fable` aliases and effort levels through
  `max`. The active file uses Sonnet/xhigh with Fable as advisor, and the reviewer also uses Fable;
  its index flags are normal, so the diff remains visible.

### Open assumptions

- None.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| completed | Review the plan and follow-up findings. Complete workflow. | This global workflow change remains high risk through material follow-ups. | Initial reviews plus the user's fresh-context Fable second opinion identified the correction set below. |
| completed | Verify the current model roles. Claude settings and reviewer. | The model selector can rewrite the active default. | Current state is Sonnet/xhigh execution with Fable advisor and Fable reviewer; index flags are normal. |
| completed | Implement the governing workflow invariants. Global instructions, plan skill, compact and full templates. | The accepted findings concern coupled policy surfaces. | Routine work has one definition; persistent non-trivial work has a separate compact template; the full high-risk path remains intact. |
| completed | Validate and independently audit the corrected workflow. Complete change set. | The material follow-up inherits the original high-risk classification. | Focused routing checks, skill and settings validation, diff and status checks, and the repeated fresh-context audit passed. |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`.

## Plan review

- **Risk classification:** High risk because the change calibrates global review and authorization
  boundaries used across repositories. Material follow-ups inherit this classification.
- **Mechanism:** Independent fresh-context Codex reviews plus the user's Fable second opinion; this
  client has no advisor.
- **Independent reviewer:** Completed before workflow edits and repeated after the final fixes. The
  closing reviewer used a fresh Codex context outside the user-pinned Fable advisor path.
- **Applied:** Define three risk levels; enumerate all six workflow surfaces; remove
  `assume-unchanged` before editing and preserve non-model fields; verify model aliases before
  writing them; describe deep-reviewer read-only behavior as procedural unless a technical
  per-agent allowlist is available. The first final audit then required explicit risk precedence,
  a light closure path for work without a formal plan, advisor-unavailable reporting, and the new
  compact closure schema in this plan; all four findings were accepted.
- **Applied:** The follow-up review requires inherited risk; explicit user authority for a
  same-model advisor and reviewer; one routine-work definition; an actual compact persistent-plan
  path; objective positive-control rules; explicit high-risk shared-policy changes; proportional
  closure wording; and removal of the unreachable no-second-pass option.
- **Rejected:** The reported executor mismatch was real during the Fable session but is not current;
  architecture's stricter post-audit rule is compatible with the general plan rule; the reviewer's
  `by default` wording is editorial rather than contradictory.
- **Pre-execution follow-up review:** Required the compact persistent schema and full high-risk path
  to be explicit, made the positive-control predicate falsifiable, promoted four safety rules from
  review history to governing invariants, and bound validation to each accepted correction. All
  findings were applied before policy edits began.
- **First closure follow-up review:** Found that discovery metadata omitted single-file high-risk
  and inherited-plan triggers, a non-persistent high-risk task could reach the compact form, and the
  plan used an absolute repository path. Discovery now covers those triggers, every high-risk plan
  is persistent and full, and the plan path is relative.
- **Repeated closure review:** Passed the corrected working-tree state with no findings across all
  six routing scenarios and confirmed that unrelated safeguards remain intact.

## Replan conditions

- A model alias or effort combination is unsupported by the locally installed Claude version.
- The active settings difference contains unrelated user preferences that cannot be preserved.
- A proposed relaxation weakens authorization or destructive-action safeguards rather than review
  ceremony.

## Completion evidence

- Focused consistency checks cover every accepted Fable, pre-execution, and first closure-review
  finding.
- The skill validator, settings and alias checks, symlink checks, and `git diff --check` pass.
- The repeated fresh-context audit passed all six routing scenarios with no findings.
- Current Git inspection shows only the scoped workflow/configuration changes, normal settings
  index flags, and no staged changes.

## Closure audit

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| verified | Risk classification is unambiguous, inherited by material follow-ups, and protects consequential shared-policy changes. | Plan skill, discovery metadata, full template, and implementing agents. | High-risk discovery and persistence are explicit; the repeated scenario audit passed. |
| verified | Routine and non-trivial work avoid unnecessary plans, matrices, second passes, rereads, and absence controls. | Global instructions, plan skill, and compact template; all agents. | One routine definition, a separate compact persistent path, and objective absence controls passed focused and independent checks. |
| verified | The user-pinned Fable advisor and reviewer configuration has an explicit independent-review rule. | Plan skill, Claude settings, and deep reviewer. | Same-model use requires fresh context, evidence baseline, withheld verdict, and residual-risk disclosure; settings checks passed. |
| verified | No unrelated configuration or remote state changes. | Complete working tree. | Final diff and status contain only scoped local changes; settings flags are normal and nothing is staged. |

- Architecture to implementation: No architecture record governs this local workflow calibration.
- Implementation to authority: `.codex/AGENTS.md`, the plan skill and both templates,
  `.claude/settings.json`, `.claude/agents/deep-reviewer.md`, and this plan map directly to the
  requested workflow, evidence, and model-role corrections.

### Final conformance verdict

- **Verdict:** Passed after the repeated closure review.
- **Second pass:** Independent fresh-context review.
- **Auditor and evidence:** Focused routing and configuration checks plus a clean independent audit
  of the complete working-tree state.
- **Unresolved requirements:** None.
