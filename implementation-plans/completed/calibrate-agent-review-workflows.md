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
- For this follow-up, correct the compact template, the plan skill and lifecycle README wording,
  and this plan's historical classification without changing runtime model selection.

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
| completed | Review the current follow-up before implementation. Complete follow-up scope. | The material follow-up inherits the original high-risk classification, while the user explicitly rejected a new global model-selector rule. | Fresh-context review required separated execution and validation stages, explicit owner paths, and clear separation of prior-round evidence. The plan was corrected before content edits. |
| completed | Apply the four accepted corrections. Plan skill, compact template, lifecycle README, and this plan. | No runtime model-selection or unrelated workflow rule needs to change. | Added the authority field; synchronized lifecycle wording; simplified the high-risk second-pass gate; classified the restored Sonnet default as applied without attributing its cause to the review. |
| completed | Run focused semantic and package checks. Affected documentation and skill package. | Each check must distinguish the requested correction from unrelated text. | Exact positive and negative checks cover all four corrections; the skill validator and whitespace checks pass. |
| completed | Rebuild affected closure evidence and perform the author pass. Complete diff. | Prior-round validation remains historical evidence and does not close this follow-up. | The affected matrix rows, concise-plan requirement, reverse trace, diff, status, unchanged model configuration, index flags, and symlinks pass inspection. |
| completed | Perform the required independent second pass and close the same plan. Complete working-tree state. | All content changes and author checks must be complete first. | Fresh-context audit passed with no findings; the same plan was closed after recording the verdict. |

Keep at most one step `in_progress`. Use only `pending`, `in_progress`, and `completed`.

## Plan review

- **Risk classification:** High risk because the change calibrates global review and authorization
  boundaries used across repositories. Material follow-ups inherit this classification.
- **Mechanism:** The user's Fable second opinion supplies the current advisor findings. Independent
  fresh-context Codex review covers the pre-execution and final conformance passes because this
  client has no advisor mechanism.
- **Prior-round independent review:** Completed before the earlier workflow edits and repeated
  after those fixes. It established explicit risk precedence, proportional planning and closure,
  inherited high-risk follow-ups, objective absence controls, and a complete high-risk path.
- **Applied:** The persisted executor differed from the configured Sonnet default and was restored
  to Sonnet. The user confirmed separately that the model selector rewrites the persisted setting;
  this records the behavior without attributing the earlier drift to the review session.
- **Applied:** Add the missing authority field to the compact template, use risk-appropriate
  lifecycle wording for completed plans, and remove the redundant risk qualifier from the
  high-risk completion gate.
- **Rejected:** A new shared rule prescribing `@deep-reviewer` or prohibiting use of the model
  selector is unnecessary because no current instruction tells the executor to change models, and
  a Claude-specific invocation must not become a universal Codex rule. Architecture's stricter
  post-audit rule remains compatible with the general plan rule; the reviewer's `by default`
  wording is editorial rather than contradictory.
- **Current pre-execution review:** Required distinct review, implementation, focused-validation,
  author-closure, and independent-audit stages; explicit ownership by the compact template,
  `implementation-plans/README.md`, and the plan skill; and separation of retained prior-round
  evidence from checks invalidated by this follow-up. These findings were applied before content
  edits.

## Replan conditions

- A model alias or effort combination is unsupported by the locally installed Claude version.
- The active settings difference contains unrelated user preferences that cannot be preserved.
- A proposed relaxation weakens authorization or destructive-action safeguards rather than review
  ceremony.

## Completion evidence

- Prior-round evidence: focused consistency checks, skill validation, settings and alias checks,
  symlink checks, whitespace validation, and a repeated fresh-context audit passed before this
  follow-up.
- Current follow-up evidence: exact semantic controls verify the compact authority field, both
  lifecycle owners, unconditional high-risk second-pass wording, and neutral plan history. The
  skill validator, whitespace checks, final diff, status, model-setting, index-flag, and symlink
  checks pass. The independent conformance audit passed with no findings.

## Closure audit

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| verified | Risk classification is unambiguous, inherited by material follow-ups, and protects consequential shared-policy changes. | Plan skill, discovery metadata, full template, and implementing agents. | The high-risk gate now calls its second pass unconditionally required; exact semantic and package checks pass. |
| verified | Routine and non-trivial work avoid unnecessary plans, matrices, second passes, rereads, and absence controls. | Global instructions, plan skill, compact template, and lifecycle README; all agents. | The compact template records authority, and both lifecycle owners use risk-appropriate verdict wording. |
| verified | The user-pinned Fable advisor and reviewer configuration has an explicit independent-review rule. | Plan skill, Claude settings, and deep reviewer. | Same-model use requires fresh context, evidence baseline, withheld verdict, and residual-risk disclosure; settings checks passed. |
| verified | Plan evidence remains concise and current instead of accumulating a chronological review diary. | This plan and implementing agents. | The author pass retained current decisions and a single clearly labeled prior-round evidence summary. |
| verified | No unrelated configuration or remote state changes. | Complete working tree. | The candidate diff contains only the plan, skill, compact template, and lifecycle README; settings remain Sonnet/xhigh with Fable advisor, index flags are normal, and nothing is staged. |

- Architecture to implementation: No architecture record governs this local workflow calibration.
- Implementation to authority: `.codex/AGENTS.md`, the plan skill, both templates,
  `implementation-plans/README.md`, `.claude/settings.json`, `.claude/agents/deep-reviewer.md`, and
  this plan map directly to the requested workflow, evidence, and model-role corrections.

### Final conformance verdict

- **Verdict:** Passed.
- **Second pass:** Independent fresh-context Codex review.
- **Auditor and evidence:** Author checks passed; the independent reviewer verified the four
  corrections, scoped diff, unchanged model configuration, matrix, and traces with no findings.
- **Unresolved requirements:** None.
