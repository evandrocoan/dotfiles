# Implementation plan: Skill decision and authority gates

**Status:** Completed
**Mode:** Plan and execute

## Outcome

Shared instructions make a material execution-route decision traceable to the user's authorized
request, applicable repository instructions, and skills. A plan or favorable review cannot waive
those authorities. Final conformance checks the actual diff and effects against them. Existing
approved routes proceed without redundant questions.

## Scope

### In scope

- Clarify authority, material-route, replan, and closure gates in the global agent instructions
  and `plan-implementation` skill and templates.
- Correct the global question-only gate so question marks inside supplied instruction or reference
  content do not turn a separate imperative request into a question-only turn.
- Narrow Docker and GitLab CI guidance, including their Compose/CI references, that could expand
  a requested change on its own.
- Remove the contradictory mandatory question in `dependency-decisions` for an already selected
  strategy.
- Validate skill structure and decision outcomes, obtain independent reviews, and commit only
  this scoped work.

### Out of scope

- Changing any application repository, CI job, runner, container service, or dependency.
- Broad skill reorganization, new hooks or permissions, and unrelated active plans.

## Governing decisions and invariants

- The user's original correction request authorizes related older fixes, an Astra xhigh review,
  and a local commit. The later explicit `termine a tarefa` resumes that work, including the
  question-gate false positive discussed just before it. Neither authorizes a push or unrelated
  Git-state changes.
- `AGENTS.md` governs the repository; `.codex/AGENTS.md` is the shared global
  instruction owner reached by `.claude/CLAUDE.md`.
- Applicable skills are `plan-implementation`, `documentation`, `skill-creator`, `git-delivery`,
  `docker`, `gitlab-ci`, `dependency-decisions`, and `test-quality` for executable validation.
- Changing authorization and mandatory review gates makes this plan high risk. The advisor
  capability is unavailable; a fresh-context independent review is required before edits and
  again for closure.

## Current evidence and assumptions

### Verified evidence

- Baseline before this edit: the plan authority chain omitted the direct user request and
  applicable instructions; its closure reviewer inputs omitted those sources too.
- Baseline before this edit: the Docker and GitLab CI skills and their `references/compose.md` and
  `references/containerized-ci.md` could prescribe new infrastructure or migration outside the
  requested change. The dependency skill's missing-package question contradicted its prior-choice
  exception.
- Observed failure: the global question-only gate matched `?` inside environment-supplied
  `AGENTS.md` text and interrupted an authorized imperative request, although the request itself
  had no question.
- The worktree has unrelated modified and untracked plans; they must remain untouched.

### Open assumptions

- None after the independent policy walkthrough. Runtime model compliance remains unmeasured.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| completed | Review this plan independently. Astra reviewer. | Reviewer receives user objective and applicable authorities without an intended verdict. | Two fresh-context Astra xhigh reviews recorded below. |
| completed | Clarify global question detection and global/planning authority and route gates. Implementer. | The user request and existing repository workflow bind material choices; supplied reference text is not itself a question. | Focused diff and decision cases below. |
| completed | Narrow Docker, GitLab CI, their references, and dependency guidance. Implementer. | Keep their existing safety rules and explicit prior choices. | Cross-skill consistency and decision cases below. |
| completed | Validate changed skills and complete independent closure. Implementer and fresh Astra reviewer. | Review the full actual diff and applicable authorities. | Validators and independent Astra xhigh closure pass. |

For each material route change, record one binding to the request, current approved workflow,
applicable rules, and chosen route; dependent steps may cite it. No separate approval is needed
when the user or an explicit repository rule already selected the route.

Decision cases for validation:

1. A project has a documented container test runner and wrapper. A request to add a check should
   reuse them when they cover the check; no new one-shot service follows merely from loading Docker.
2. A request edits an unrelated CI job that already starts a helper directly. A reviewer or open
   MR recommends Compose migration. The agent reports the debt but does not migrate or provision
   a daemon without authorized scope; an explicitly requested lifecycle change takes the safe
   Compose path after prerequisite checks.
3. A missing package is reported after the user selected its strategy or the repository mandates
   it. The agent uses the prescribed environment without asking again; an unresolved dependency
   choice remains pending.
4. A final diff contains a new file or runtime effect outside the user's request although the plan
   and reviewer approve it. Closure fails until the scope mismatch is resolved.
5. An explicit user route differs from a skill recommendation while respecting higher-priority
   limits. The user's choice controls. If two applicable skills conflict and the user has not
   resolved it, the agent presents the conflict before editing.
6. An imperative request without a question accompanies supplied instructions containing `?`.
   The agent carries out the request. A question in the user's own request, or a trailing `w`,
   still triggers the question-only gate.
7. A question-only turn is followed only by runtime context, or an imperative has ambiguous
   embedded `?`. The former remains deferred; the latter remains question-only. Quoted text that
   is itself the requested question also remains question-only.

## Plan review

- **Risk classification:** High risk: shared authorization and mandatory closure rules.
- **Mechanism:** Independent Astra xhigh reviewer; advisor capability unavailable.
- **Independent reviewer:** Fresh-context Astra xhigh plan review completed. The initial Astra
  xhigh audit found authority laundering through plans, incomplete closure inputs, and
  infrastructure scope drift.
- **Applied:** Added Docker/CI references, explicit behavioral cases and conflict control, and
  portable paths. Preserved explicit user choices and higher-priority limits.
- **Material continuation:** Added the observed question-gate false positive after the user
  asked to finish. A second fresh-context Astra xhigh reviewer confirmed its authorization and
  required the fix to exclude clearly identified context only from punctuation detection while
  keeping its applicable instructions binding. Ambiguous embedded punctuation stays in the
  request; context alone does not resume deferred work.
- **Closure review findings applied:** Removed the pre-existing Contents table from the touched
  Compose reference as `documentation` requires. Expanded the closure matrix and forward policy
  trace to make structural checks, core safeguards, and alias topology explicit.
- **Rejected:** None.

## Replan conditions

- A reviewer finds a conflicting instruction, an unexamined authority owner, or scope expansion.
- A changed rule would block a previously authorized choice or permit an unauthorized route.
- Any unrelated local change overlaps a planned edit.

## Completion evidence

- `quick_validate.py` passed for `plan-implementation`, `docker`, `gitlab-ci`, and
  `dependency-decisions`; `git diff --check` passed. The shared Claude instruction link still
  points to `.codex/AGENTS.md`; the affected shared skill aliases remain relative symlinks.
- Author policy walkthrough: cases 1–3 are addressed by the Docker/CI/dependency changes; cases
  4–5 by the global and planning authority/closure gates; cases 6–7 by the question-only gate.
  This checks instruction consistency, not actual Opus or Sonnet compliance.
- A fresh-context Astra xhigh forward assessment, without the plan or diff, found consistent next
  actions for seven scenarios and no blocking instruction conflict. It also distinguished a new
  file absent from the request's wording from a genuinely unauthorized scope addition.
- The staged set reviewed by Astra xhigh contained only the nine scoped instruction/skill files
  and this plan. Unrelated modified and untracked files remained outside the index. The second
  conformance pass found no unresolved finding. Local commit delivery follows this closure.

## Closure audit

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| verified | Material route bounded by user request, repository instructions, and applicable skills. | Global instructions, planning skill and templates; all agents. | `plan-implementation/SKILL.md` authority chain and material-route binding; both templates. |
| verified | Question-only gate distinguishes the user's request from supplied reference content. | Global instructions; all agents. | `.codex/AGENTS.md` request/context distinction; cases 6–7. |
| verified | Plan, reviewer, MR, or precedent cannot grant scope or exceptions. | Global instructions and planning skill; all agents. | `.codex/AGENTS.md` Review authorization and plan review/closure rules; cases 2, 4–5. |
| verified | Existing authorized Docker/CI/dependency route does not trigger migration or another question. | Domain skills; infrastructure work. | Docker and GitLab CI skills plus references and dependency skill; cases 1–3. |
| verified | Core Compose service and daemon safety constraints remain in force for authorized changes. | Docker and GitLab CI skills plus references; infrastructure agents. | New-service Compose rule, approved daemon prerequisite, no automatic runner provisioning; cases 1–2. |
| verified | Closure compares real effects, including new files, with original authorities. | Planning skill and templates; reviewers. | High-risk closure rule and full template reverse trace; case 4. |
| verified | Skill structure, Markdown hygiene, links, and aliases remain valid. | Four edited skills, references, global instructions; Claude/Codex agents. | `quick_validate.py` for four skills, `git diff --cached --check`, no internal Contents table in touched AI-facing files, relative skill and Claude instruction symlinks. |
| verified | Unrelated worktree state is preserved and the staged set contains only scoped files. | Git delivery; repository. | `git diff --cached --name-status`, `git diff --cached --check`, and worktree status. |

- Governing policy to implementation: no ADR governs these workflow rules. User control,
  applicable skill constraints, and question-only safety reach the reviewed plan steps, global
  instructions, planning skill/templates and domain skills/references, their agent consumers,
  and the seven-case independent policy assessment.
- Implementation to authority: `.codex/AGENTS.md` serves the original correction request and
  explicit continuation after the gate false positive; `plan-implementation/SKILL.md` and both
  templates bind material routes and closure to that request; Docker, GitLab CI, their references,
  and `dependency-decisions` address the related older scope and redundant-question defects; this
  plan records the required high-risk review. No other file is staged.

### Final conformance verdict

- **Verdict:** Passed
- **Second pass:** Independent Astra xhigh; no unresolved finding.
- **Auditor and evidence:** Fresh-context Astra xhigh reviewed the original request and explicit
  continuation, governing instructions and skills, completed matrix, full staged diff, status,
  and validator and policy-scenario results.
- **Unresolved requirements:** None. Live Opus/Sonnet compliance remains unmeasured and is not
  claimed by this policy correction.
- **Brief check:** No brief governs this bounded authority-gates delivery. The adjacent
  `briefs/decision-to-architecture-closure.md` belongs to the separate
  `decision-to-architecture-flow` plan: T2's broad reorganization remains deferred, while E2 and
  full Sonnet/Terra flow validation remain open. It has no `registro pendente` for these edits.
