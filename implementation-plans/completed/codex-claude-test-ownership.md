# Implementation plan: Claude-owned implementation and test execution

**Status:** Completed
**Mode:** Plan and execute

## Outcome

For a Codex–Claude collaboration task, after its required plan and risk reviews, Claude receives
the authorized implementation and applicable repository-prescribed test execution. Codex plans,
supervises, inspects results, and independently verifies completion. A coordinator-selected
tests-only milestone or permission profile cannot silently replace Claude's end-to-end assignment.
Both collaboration modes and all authorization boundaries remain intact.

## Scope

### In scope

- Correct the canonical `codex-claude-loop` skill and affected mode references so the implementer
  owns applicable regression, implementation, and test runs after prerequisites pass.
- Clarify task-scoped CLI permissions for the repository's required test route, including a
  Docker/Compose route when that repository requires one.
- Preserve independent Codex review and optional independent test reruns without shifting the
  implementer's primary execution responsibility.
- Validate skill structure, changed instructions, and representative positive and negative paths.

### Out of scope

- Edit or run the `pr-agent` checkout or its D2.1/D5 task.
- Run Claude, a live provider, or project tests solely to validate this instruction edit.
- Change the handoff protocol, model profile, dependencies, Git index, or remote state.

## Governing decisions and invariants

- The user's correction follows the pasted D5 exchange: Claude was initially assigned only owner
  mapping and regression edits, with Bash and Docker tests forbidden; the user directed Claude to
  implement code and run Compose tests while Codex supervises and reviews.
- The existing skill makes Claude the sole checkout implementer but lets Codex run validation
  commands instead of granting shell access. That sentence permits the observed mismatch.
- Required high-risk plan review remains before high-risk edits. Once the plan is ready, assign
  the full authorized implementation and applicable tests to Claude unless the user explicitly
  chooses another split. A governing evidence gate may sequence Claude's work, but a
  coordinator-authored plan cannot itself change the agreed execution owner.
- Tests must follow the repository's authoritative environment and authorization rules. If Claude
  cannot run an applicable required test within an authorized permission profile, report the
  concrete decision needed; Codex running it cannot silently satisfy Claude's assigned role.
- Preserve one implementer, existing work and index, both modes, fresh independent review, and
  user control over Git, external services, and live actions.
- This is high risk because it changes shared agent execution, permission, and review guidance.
  The prior completed plan remains historical; this correction has its own plan and closure audit.

## Current evidence and assumptions

### Verified evidence

- The pasted exchange records the tests-only/no-Bash assignment and the user's correction.
- At baseline, the supervised CLI reference said Claude implements, but permitted Codex to run
  validation in place of shell access and later told the coordinator to run required validation.
- At baseline, the handoff reference said Opus runs relevant verification, while its task
  assignment language remained broad. The canonical entrypoint did not assign tests explicitly.
- At baseline, the target skill files were clean; unrelated plans and `.gitignore` had existing
  changes. Do not stage or include them.
- The corrected text uses the existing role and permission contract; the handoff state table and
  lock rules are unchanged, and no live Claude run was needed for the instruction edit.

### Open assumptions

- Actual Claude command scoping and future agent compliance are not established by static or
  textual validation; a future task must verify its own CLI, provider, trust, and permissions.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| completed | Obtain independent Astra xhigh plan review. | Reviewer sees the user correction, pasted exchange, current skill, and this plan. | Reviewer requested explicit behavioral cases and sensitivity control; revised plan passed recheck with no blockers. |
| completed | Update the canonical role rule and mode references. | Existing mode contracts support the clarified assignment. | Common role rule and both references now assign applicable tests to Claude, preserve Codex review, and make permission denial explicit. |
| completed | Validate syntax and exercise the cases below. | Written instructions are the system under test. | Canonical and shared-link validators, relative references, and whitespace passed. Fresh Astra xhigh textual evaluation covered all seven cases and rejected the old substitution sentence as unreliable. |
| completed | Complete high-risk closure audit and fresh Astra xhigh conformance. | Final diff and validation evidence exist. | Matrix and both traces complete; fresh Astra xhigh second pass found no blocking issue. |

## Plan review

- **Risk classification:** High risk; shared agent execution, permissions, and test ownership.
- **Mechanism:** Independent Astra xhigh reviewer; no separate advisor interface is available.
- **Independent reviewer:** Astra xhigh with fresh context and read-only scope;
  requested a concrete validation contract before skill edits, then passed the revised plan.
- **Applied:** Defined expected scenario decisions and a negative control; clarified that a
  coordinator-authored plan may sequence evidence but cannot change the agreed owner.
- **Rejected:** None.

## Replan conditions

- The corrected assignment requires a handoff owner/state change or conflicts with a governing
  review or test rule.
- The permission guidance would require a silent bypass, broad shell grant, or test substitution.
- An affected skill file has concurrent changes or the scope expands to `pr-agent`, dependencies,
  Git state, or a live service.

## Validation contract

| Scenario | Expected decision |
| --- | --- |
| Required reviews complete; code and repository-prescribed tests remain. | Assign both implementation and applicable test execution to Claude; Codex supervises and reviews. |
| Regression-first evidence gate applies. | Claude writes and runs the baseline regression, then completes production changes and affected tests after the gate; no arbitrary tests-only handoff. |
| Claude lacks permission for a required test command. | Report the precise missing permission and decision; neither enlarge it nor silently move the test to Codex. |
| User explicitly selects a different implementation/test split. | Honor that choice within governing authorization and test rules. |
| Claude reports test results; Codex needs independent verification. | Codex may rerun an authorized check, but its run does not replace Claude's assigned execution. |
| Two-session handoff owns implementation. | Opus runs applicable tests under its lock and hands results to Sol; reviewer, index, and protocol ownership remain unchanged. |
| User requests a named test with documented live or disposable effects. | Follow `test-quality` authorization and prescribed environment for that test; exclude unrelated external effects. |

Ask an independent evaluator to apply realistic requests to the skill without supplying the
expected decisions. As a sensitivity control, it must reject a candidate that retains the
existing CLI permission sentence allowing Codex to take over Claude's test execution, or an
equivalent substitution, even if the entrypoint says Claude owns tests.

## Completion evidence

- The canonical and shared-symlink `quick_validate.py` runs returned `Skill is valid!`;
  `git diff --check` passed. Both reference files and the relative shared symlink resolve.
- Independent Astra xhigh textual forward evaluation found the intended decisions in all seven
  cases. It found the former Codex-validation substitution sentence would not reliably preserve
  Claude's test ownership. This was a read-only instruction trace, not a live Claude trial.
- No `pr-agent`, Git index, provider, or project test state was changed. Existing unrelated
  worktree changes remain outside the scoped skill diff.

## Closure audit

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| verified | Claude owns applicable implementation and tests after required reviews. | Entrypoint and both modes. | Common role paragraph; CLI launch/review sections; handoff owner turn. Textual scenarios covered approved high-risk work and regression-first sequencing. |
| verified | Safe permission profile and concrete denial path. | CLI mode and Claude. | CLI permissions paragraph requires scoped test access, including Compose where prescribed, and a decision on denial; textual denial scenario found no silent transfer. |
| verified | Codex supervision and independent verification without role substitution. | Both modes and reviewer. | Common role paragraph, CLI review section, and handoff Sol turn distinguish reruns from Claude's assigned tests; explicit user split is preserved. |
| verified | Existing protocol, index, authorization, and scope preserved. | Skill package and repository. | Scoped diff touches only three canonical skill files; handoff states/lock and model profile remain; no Git-state, `pr-agent`, dependency, or live action by this task. |
| verified | Proportional validation and sensitivity. | Skill package and plan. | Both `quick_validate.py` paths, references, relative symlink, and `git diff --check` passed; independent textual cases passed and the old substitution sentence was rejected as unreliable. Runtime behavior was not tested. |
| verified | Fresh independent final conformance. | Plan and final diff. | Separate Astra xhigh reviewer read the governing instructions, attachment, skill, plan, full diff, validator source, and current Git state; no blocking finding. |

- **Architecture to implementation:** The shared collaboration contract assigns Claude the code
  and applicable tests after required gates, and Codex the review. The plan's owner edit reaches
  `SKILL.md` and both mode references; the CLI permission path and handoff owner turn preserve the
  assignment. Static checks and independent textual scenarios cover the changed instructions. No
  architecture record governs this shared skill workflow.
- **Implementation to authority:** The entrypoint role paragraph and both reference edits trace
  to the user's correction of the D5 handoff, the pre-edit plan review, and this plan's scoped
  objective. The new active plan is required by `plan-implementation` for the safety/permission
  change. No affected file or observed effect requires wider user authorization.

### Final conformance verdict

- **Verdict:** Passed for the written collaboration workflow; no blocking finding.
- **Second pass:** Fresh Astra xhigh read-only final conformance review passed.
- **Auditor and evidence:** Author compared the full scoped diff, complete skill, plan, and
  validator/forward-evaluation results with the user correction and governing instructions.
  The second pass independently checked the text, diff, references, symlink, and Git state;
  validator outputs were supplied to it rather than rerun by it.
- **Unresolved requirements:** None for this instruction edit. Actual Claude behavior, CLI
  permission confinement, and Docker execution remain untested until a future task uses the flow.
- **Brief check:** No same-subject brief found under `implementation-plans/briefs/`.
