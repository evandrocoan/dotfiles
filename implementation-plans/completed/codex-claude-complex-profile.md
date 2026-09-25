# Implementation plan: Complex Codex–Claude collaboration profile

**Status:** Completed
**Mode:** Plan and execute

## Outcome

The shared `codex-claude-loop` skill recommends Codex Sol xhigh for coordination,
Claude Opus 5.5 xhigh as the sole checkout implementer, and fresh-context,
read-only Codex Astra xhigh reviews before high-risk edits and at closure. Both
existing collaboration modes remain usable. Explicit user model and effort choices
take precedence. The supervisor continues until completion or a concrete blocker,
without self-imposed turn, time, iteration, or cost limits.

## Scope

### In scope

- Update the canonical skill entrypoint and the supervised CLI and two-session
  references where the common profile or its mode-specific execution needs wording.
- Add preflight for CLI version, chosen model and effort availability, active
  configuration, checkout trust, permissions, and existing Git index and worktree.
- Define independent review, execution monitoring, partial-result reconciliation,
  interruption recovery, and concrete stopping conditions for both modes.
- Validate discoverability, symlink, Markdown, and scenario behavior.

### Out of scope for the original implementation request

- Running Claude on a project, updating the CLI or dependencies, changing saved
  configuration, changing the legacy handoff protocol, or touching `pr-agent`.
- Staging, committing, pushing, or any other Git-state mutation.

## Governing decisions and invariants

- The user's explicit request specifies the recommended Sol xhigh / Opus 5.5
  xhigh / Astra xhigh combination, read-only fresh reviews, no self-imposed
  execution limits, and preservation of both modes and user authorization.
- The canonical package is `.claude/skills/codex-claude-loop/`; the relative
  `.agents/skills/codex-claude-loop` link exposes it. The two-session contract
  keeps `protocol: sol-fable-loop/2` and its ownership transitions.
- Claude alone implements the assigned checkout changes. Sol owns plans,
  assignment, observation, integration assessment, validation, and user report;
  Astra reviews read-only with new context. Sol may write authorized planning
  and handoff artifacts under their own instructions. In the two-session mode,
  Astra advises within Sol's owned, locked turn: Sol retains the lock and alone
  publishes the next state, including `done`. No owner or protocol state changes.
- No model, permission, checkout, authentication route, dependency, Git authority,
  live action, or external service scope changes merely to keep the loop moving.
- An interrupted or partial invocation cannot be resumed or retried until the
  exact process, session, repository, index, and external effects are reconciled.
- This is high risk: the edit changes shared agent safety, supervision, and
  mandatory-review rules. The prior CLI-mode plan is completed and remains
  historical; this plan covers the new profile and removes a prior limit rule.

## Current evidence and assumptions

### Verified evidence

- At baseline, the supervised reference required finite `--max-turns`, a process
  deadline, an overall iteration limit, and stopping at that limit. It lacks
  a Codex Astra reviewer stage and an explicit Git index baseline.
- At baseline, the handoff reference had one owner at a time, lock and atomic-publish rules,
  pause and recovery paths, but names Opus high and lacks the proposed reviewer
  role and complex-work profile.
- The local Claude CLI reports version `2.1.282` and exposes `--model` and
  `--effort`. Current official Claude Code documentation says Opus 5.5 requires
  at least `2.1.280`, supports xhigh, and model aliases may resolve differently
  by provider. This proves local flag/version support, not account availability.
- The target skill files are clean at the starting Git status. The completed
  prior plan and other unrelated plans/briefs have existing changes; preserve them.

### Open assumptions

- Provider and account access to Opus 5.5 xhigh cannot be inferred from CLI
  version or documentation alone. At task time, check available capability and
  known configuration limits; stop on a concrete incompatibility, denial, or
  substitution. Structured output may not prove applied effort: report that
  limitation without turning absent telemetry into a failed prerequisite.
- No live Claude task is part of this skill update; runtime behavior will remain
  unverified unless a separately authorized task exercises the flow.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| completed | Obtain independent Astra xhigh plan review. | Reviewer reads the user request, instructions, current skill, and this plan before skill edits. | Reviewer found two contract clarifications and one existing handoff ambiguity; all are incorporated below. |
| completed | Update shared role and authorization rules in `SKILL.md`. | User choices override the recommended profile; only Claude implements. | Entrypoint routes both modes, preserves the index, and names reviewer gates without protocol drift. |
| completed | Update CLI and handoff references. | Both modes retain their own recovery and ownership contracts. | Former self-imposed caps removed; preflight, review, monitoring, and partial-result paths documented. |
| completed | Validate and run independent scenario evaluation. | The skill text, not a live Claude task, is the system under test. | Both skill validators, links, and whitespace passed; author-reported Astra xhigh textual traces covered healthy long work, concrete blockers, effort telemetry, review/permission/process/index denials, and both architecture-recording paths. The evaluator transcript is not preserved as a repository artifact. |
| completed | Perform author closure and fresh Astra xhigh conformance pass. | Final scoped diff and observed effects are available. | Matrix and bidirectional traces complete; fresh Astra xhigh conformance passed with no blocking findings. |

## Plan review

- **Risk classification:** High risk; shared safety and mandatory-review behavior changes.
- **Mechanism:** Independent Astra xhigh reviewer; no separate advisor interface is available.
- **Independent reviewer:** Astra xhigh with fresh context and read-only scope;
  found the plan executable after the recorded clarifications.
- **Applied:** Distinguish capability checks from unobservable applied effort;
  keep Astra inside Sol's locked handoff turn without new states; clarify the
  conditional architecture-recording path. Add healthy-long-run and concrete
  blocker cases, reviewer/permission/index/process denials, and negative controls.
- **Rejected:** None.

## Replan conditions

- A required model or effort is concretely unsupported, denied, or substituted,
  or its use needs a different route, dependency update, or unapproved charge.
- Preserving the handoff protocol requires a state transition change.
- The user-owned index or working tree overlaps a planned edit.
- A necessary safeguard is found to depend on self-imposed turn, time, or cost
  limits rather than concrete failure, authorization, or reconciliation rules.
- The selected implementation would alter `pr-agent` or require Git/live effects.

## Completion evidence

- Both skill validators returned `Skill is valid!` on canonical and shared-symlink paths;
  `git diff --check` passed. The relative symlink and both local references resolve.
- The CLI reports `2.1.282`; official Claude Code documentation lists Opus 5.5
  support from `2.1.280` and xhigh effort. Account availability and effective
  effort were not tested; the skill requires task-time checks and truthful reporting.
- Author-reported Astra xhigh forward evaluation passed textual traces of the requested
  paths and rejected old finite-limit guidance, reviewer edits, a second implementer,
  and false completion. Its full transcript is not retained in this repository;
  the fresh closure reviewer must inspect the skill and diff independently.
- A live Claude implementation was outside the original request. Before the later
  commit request, no `pr-agent`, index, commit, or remote operation was performed.
  Unrelated concurrent changes in `.gitignore`, the plan index, other plans, and
  briefs were preserved.

## Closure audit

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| verified | Complex profile and user-choice precedence. | Entrypoint; both modes. | `SKILL.md` recommends Sol/Opus/Astra xhigh and preserves explicit model and effort choices; both references route through it. |
| verified | CLI version, model/effort, configuration, trust, and permission preflight. | CLI reference and handoff; both clients. | CLI steps 3–4 and model section; handoff preflight paragraph. CLI `2.1.282` supports current flags; account access remains task-time verification. |
| verified | Git, external, and live authorization boundaries. | Entrypoint and both modes. | Common index/Git rule; CLI permission profile and partial-effects rule; handoff authorization paragraph. No Git-state or external write occurred during the original implementation. |
| verified | Sole implementer and independent high-risk and closure reviews. | Both modes; Claude, Sol, and Astra. | Common role/review section; CLI gates and closure; handoff reviewer under Sol's lock without a new owner or state. |
| verified | Ongoing supervision, concrete blockers, and interruption recovery. | CLI reference and handoff. | CLI launch/review/continue sections removed former finite caps; handoff owns turns, reconciles partial work, and blocks only with evidence. Author-reported textual traces covered long and interrupted work; the final reviewer independently examines these paths. |
| verified | Existing work, index, protocol, mode routing, and discovery preserved. | Skill package and repository. | Final diff touches the three canonical skill files; `sol-fable-loop/2` state table and lock remain; shared symlink resolves; baseline and concurrent changes remain outside this diff; index was empty at implementation closure. |
| verified | Proportional validation. | Skill package and plan. | Both skill validators, relative links, and `git diff --check` passed. Author-reported Astra xhigh textual evaluation found no blockers; no live Claude invocation was in scope. |
| verified | Fresh independent final conformance. | Plan and final diff. | Separate Astra xhigh reviewer with fresh context inspected the full skill, scoped diff, plan, and governing instructions; no blocking findings. |

- **Architecture to implementation:** The shared single-implementer, review, authorization, and
  recovery invariants above map to the entrypoint and both mode references. Static validation and
  scenario evaluation cover the changed guidance; the existing handoff contract remains in its
  reference. No architecture record governs this shared skill workflow.
- **Implementation to authority:** Each changed entrypoint and reference paragraph maps to the
  user's profile, preflight, index, review, monitoring, recovery, no-arbitrary-cap, or authorization
  request and the corresponding plan step. The new plan is required by the high-risk planning
  skill. No `pr-agent`, Git index, external service, or live Claude task changed during
  the original implementation.

### Final conformance verdict

- **Verdict:** Complete for the written skill workflow; no blocking findings.
- **Second pass:** Fresh Astra xhigh read-only conformance review passed. It independently
  inspected continuation, denials, partial results, cancellation, handoff, scope, and both traces.
- **Auditor and evidence:** Author pass compared the full skill diff, plan, and observed checks
  with every requested outcome and boundary. The second pass checked the final text and diff;
  validator output was supplied to the reviewer rather than rerun by it.
- **Unresolved requirements:** None. Runtime access, effective effort, live permission behavior,
  process supervision, and actual recovery remain untested until a task uses the flow.
- **Brief check:** No same-subject brief found under `implementation-plans/briefs/`.
