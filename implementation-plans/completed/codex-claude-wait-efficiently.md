# Implementation plan: Low-overhead Claude CLI supervision

**Status:** Completed
**Mode:** Plan and execute

## Outcome

The supervised CLI mode tells Codex to wait on the owned Claude process with the tool's session
handle, consume new output, and review the final result. It avoids frequent status or log polling
when the running state is already known, while detecting prompts, failures, interruptions, and
ambiguous process state. Waiting does not impose a task turn, time, or cost limit. The requested
local delivery is scoped to this skill's pending corrections and their completed plans.

## Scope

### In scope

- Clarify wait-first supervision in the canonical skill's supervised CLI reference.
- Preserve responsive handling of newly returned output and prompts, exact-session recovery,
  existing authorization and one-implementer rules, and both collaboration modes.
- Validate the skill, review realistic normal and failure paths, and prepare a scoped local commit
  after the high-risk closure pass.

### Out of scope

- Run Claude or project tests to exercise a real task, or touch the `pr-agent` checkout.
- Change the handoff protocol or enable recurring checks; change the model/effort profile.
- Include unrelated worktree changes, push, or modify dependencies or remote services.

## Governing decisions and invariants

- The user wants Sol to avoid spending tokens on frequent polling while Claude works and expects
  the normal path to wait for the process result, then inspect its output.
- The existing CLI reference says to observe the process, inspect output and state when a tool
  call ends early, and inspect new output before waiting again. It does not say to prefer waiting
  over repeated `ps` or log reads, so a coordinator can make unnecessary model calls.
- The coordinator must inspect newly returned output for prompts, including a prompt without a
  newline, and must not treat silence alone as an interactive prompt. When a tool response proves
  the same process remains active, that response is enough to continue waiting; inspect process
  state separately only when it is unknown or contradictory.
- Use a long supported per-call wait interval that fits prompt responsiveness and user updates.
  A short default wait repeated unchanged can create many model turns even without separate
  probes. A tool yield interval is not a task duration limit.
- An interrupted or partial result still requires exact process, session, index, worktree, and
  external-effect reconciliation before any resume or retry. User pause/cancellation still stops
  the owned process safely. No fixed implementation limit or unsafe wait is introduced.
- This is a high-risk follow-up because it changes shared supervision and prompt-handling rules.
  The earlier completed test-ownership plan remains historical; this plan owns the wait behavior.
- Git delivery is separately authorized by the current `commit` request. Commit only the final
  scoped skill diff and the completed plans for these local skill corrections, after closure.

## Current evidence and assumptions

### Verified evidence

- The user-provided transcript showed separate process and session-log checks while Claude was
  still running; the current CLI reference does not require those checks on every quiet interval.
- At baseline, the prior test-ownership correction was unstaged in the three canonical skill
  files, its completed plan was untracked, and the index was empty. Other files have unrelated
  changes and must remain outside the commit.
- Official OpenAI agent documentation distinguishes model generations from tool spans and counts
  model input, output, tool-result, and reasoning tokens per model call. Repeated result handling
  can add usage; wall time alone is not a token count for Sol.
- The available `exec_command` interface returns a session ID when a command remains running.
  `write_stdin` on that session returns new output and either a continuing session ID or an exit
  code. This provides a same-handle wait path without routine `ps` or log reads.

### Open assumptions

- None for the currently available command/session interface. Other clients must use their own
  documented equivalent rather than assume the same API shape.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| completed | Obtain independent Astra xhigh plan review. | Reviewer sees the user request, current skill, governing instructions, and this plan. | Added long supported waits and a short-default case; reviewer reread and found no pre-edit blocker. |
| completed | Correct the CLI supervision path. | Tool wait returns incremental output and a running/completed status, or exposes an explicit status path. | The CLI reference now prefers a long supported wait on the retained handle, inspecting new output and using process checks for ambiguity. |
| completed | Validate and forward-evaluate the changed instruction. | Written instruction is the system under test. | Both validators, references, symlink, and whitespace passed. Fresh Astra xhigh evaluator passed seven scenarios and rejected both negative controls. |
| completed | Complete high-risk closure. | Final diff and evidence exist. | Matrix and both traces passed; fresh Astra xhigh reviewer found no blocker; no same-subject brief exists. The authorized scoped commit follows closure and is verified separately. |

## Plan review

- **Risk classification:** High risk; shared agent process supervision and prompt safety.
- **Mechanism:** Independent Astra xhigh reviewer; no separate advisor interface is available.
- **Independent reviewer:** Fresh-context Astra xhigh read-only review; no pre-edit blocker
  remains after recheck.
- **Applied:** Require a long supported per-call wait suitable for prompt responsiveness and
  user updates; add a short-default validation case and two negative controls.
- **Rejected:** None.

## Replan conditions

- The wait mechanism cannot expose prompt output or reliable process/session state.
- A proposed optimization would hide failures, ignore live prompts, start a second implementer,
  impose an arbitrary task cap, or change the handoff protocol.
- A target skill file or the index receives overlapping concurrent edits, or delivery would require
  changing the repository's unrelated `.gitignore` work.

## Validation contract

| Scenario | Expected decision |
| --- | --- |
| Claude runs quietly and the tool retains a running process handle. | Continue waiting on that handle without routine `ps` or session-log polling; do not cancel for silence. |
| The tool defaults to a short wait and permits a longer interval. | Choose a supported interval suited to prompt responsiveness and user updates; do not repeat the short default mechanically. |
| Tool yields early with new output and confirms Claude is still running. | Inspect only that new output for prompt/error, then wait again on the same handle. |
| Output requests input, including without a trailing newline. | Treat it as a prompt; answer only if authorized, otherwise seek the concrete user decision. |
| Tool result does not establish whether the process is alive. | Inspect process state read-only before waiting, retrying, or resuming. |
| Claude ends, fails, or the coordinator is interrupted. | Inspect structured result and partial effects; reconcile exact process/session before any resume. |
| User requests pause/cancellation. | Interrupt the owned process, verify termination, preserve partial work; do not keep waiting. |

An independent evaluator should apply these cases to the skill without receiving the expected
decisions. Negative controls are the older interpretation that performs `ps` and log tails on
every quiet wait despite an authoritative running process handle, and repeated short default waits
despite a longer supported interval. Include a prompt fragment without a newline while the process
remains active and a lost or contradictory handle that must not trigger relaunch.

## Completion evidence

- `quick_validate.py` returned `Skill is valid!` for both the canonical skill and its shared
  symlink. Both relative reference targets exist; the symlink resolves to the canonical package.
  `git diff --check` passed for the skill.
- A fresh Astra xhigh textual evaluation passed the quiet run, longer wait, live prompt fragment,
  ambiguous handle, malformed partial result, user pause, and concurrent handoff cases. It
  rejected routine `ps`/log probes and repeated short default waits while a longer wait is
  supported. This evaluates written instructions, not a live Claude run or measured token use.
- The current scoped diff includes the prior uncommitted test-ownership correction in the
  entrypoint and both references. The new wait edit affects only the CLI reference. No project
  test, provider call, dependency update, `pr-agent` action, or Git index change was made during
  validation.

## Closure audit

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| verified | Wait-first path and low-overhead observation. | CLI reference; Codex supervisor. | Launch section waits on retained handle with a long supported interval; yielded-output section rejects routine `ps`, log, session rereads, and status calls. Both negative controls failed textual evaluation. |
| verified | Prompt, failure, interruption, and ambiguous-state safety. | CLI reference and existing common rules. | Yielded-output section handles prompt fragments and uncertain state; partial-result and recovery paragraphs reconcile session, index, worktree, and effects. Seven scenarios passed textual evaluation. |
| verified | No task caps, mode drift, or authorization expansion. | Skill package and both modes. | The wait interval is distinguished from a task limit; only CLI supervision changes in this follow-up. Existing one-implementer, explicit-choice, permission, and handoff protocol text remains. |
| verified | Existing work and index preserved through instruction validation. | Repository and completed plans. | The index remained empty through instruction validation; unrelated concurrent work was outside the scoped diff. The authorized commit is a subsequent delivery action, not evidence of this conformance verdict. |
| verified | Validation and independent final conformance. | Plan and final diff. | Validators and seven textual scenarios with two negative controls passed; fresh Astra xhigh read-only reviewer found no blocker after checking both traces and the closure matrix. |

- **Architecture to implementation:** The intended supervised mode waits for Claude's final
  structured result through its retained handle. The CLI launch and yielded-output bullets now
  carry that rule, its prompt and ambiguity exceptions, and the distinction between a tool yield
  interval and a task cap. Structural validation and the textual cases exercise each branch. No
  architecture record governs this instruction change.
- **Implementation to authority:** The new CLI lines trace to the user's question about token
  use and subsequent explicit request to correct and commit. The earlier entrypoint, CLI test
  ownership, and handoff edits trace to the preceding D5 correction and its completed plan.
  Neither correction expands Git, permission, model, external, or live authorization.

### Final conformance verdict

- **Verdict:** Passed for instruction conformance; no blocking finding.
- **Second pass:** Fresh Astra xhigh read-only reviewer passed the complete package and scoped diff.
- **Auditor and evidence:** Author reread the complete skill package and governing instructions,
  inspected the scoped diff, and compared it with validator and forward-evaluation evidence.
- **Unresolved requirements:** None for the instruction edit. Actual runtime prompt delivery,
  permission confinement, and measured token savings await a future task using the workflow.
  The authorized scoped commit follows plan closure and is verified separately without recording
  it as already completed here.
- **Brief check:** No same-subject brief found under `implementation-plans/briefs/`.
