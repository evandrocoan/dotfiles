# Isolated Claude CLI mode

Use this mode only after the user has authorized a task for Claude implementation.
The Codex coordinator recommends a plan, honors any user-selected plan, supervises, integrates
findings, verifies, and reports. By default,
Claude owns the assigned checkout implementation and applicable tests, including work it delegates
to authorized internal subagents. Claude also completes user-selected reviews before reporting
completion; a later coordinator review cannot supply missing Claude-side evidence. It does not
start a separate Codex–Claude collaboration loop. Apply the recommended complex-work profile
when relevant, preserving the user's separate plan and review choices.

## Establish one task and one implementation owner

1. Identify the authorized repository root, read its instructions, inspect the branch, status,
   staged index, unstaged changes, and untracked files, and establish the task's objective, scope,
   acceptance criteria, and any user-selected plan. Record a task ID, the
   canonical checkout root, pre-run Git state, and chosen Claude model and effort in the task's
   execution context, or record that this model has no configurable effort level. Do not put a
   machine-specific absolute path in a shared file. Tell Claude to preserve the baseline,
   including the index. Include requested Git or external delivery in Claude's assignment only
   when those exact actions are user-authorized; do not assume another agent will perform them.
2. Confirm that no previous owner, scheduled reactivation, lock, Claude process, or delegated
   checkout work can still act on this task. A missing process alone does not clear a scheduled
   action or an uncertain lock. Do not substitute another checkout or launch a second
   implementation owner to resolve uncertainty. Reconcile prior partial work before launch;
   recovery mutations require the user's direction.
3. Check `claude --version` and the installed CLI flags against the chosen model's minimum CLI
   version and supported effort levels. Inspect the active provider, account or organization
   restrictions, environment and settings, hooks, MCP servers, plugins, permission rules, and
   other startup behavior. Check available subagents and their effective tool rules when the task
   needs them, including access to a qualified reviewer when the user selected internal review.
   CLI help and public model docs do not prove account access. Verify known
   availability and, if needed, use only a task-authorized read-only probe after checkout
   trust and permissions are established; reconcile its result before implementation. `claude -p`
   skips the workspace trust dialog but still loads configured startup behavior. Run it only when
   the checkout and that behavior are trusted for this task. If a prerequisite fails, report the
   decision needed; do not update the CLI, switch models, enlarge permissions, or silently use
   `--bare`, which changes instruction discovery and authentication.
4. Recommend a fresh independent pre-edit review for high-risk work. If the user selected it,
   review the proposed scope and any chosen plan, resolve findings, then launch implementation.
   If the selected reviewer cannot run, hold affected implementation until review or explicit
   withdrawal. An unselected review does not hold launch.

## Isolate Claude's task context

- Give Claude an ordinary implementation assignment: objective, authorized scope, acceptance
  criteria, relevant repository instructions, a task-facing plan or brief, and existing work to
  preserve. Do not pass this coordinator skill, coordinator plans, reviewer
  identities, future review stages, or statements that another agent will complete the task.
  Inspect every referenced artifact before launch or resume. If a formal plan mixes implementation
  steps with coordination stages, provide the complete implementation contract in a separate
  task-facing brief; retain authorization and mandatory gates. Do not misrepresent the user's
  requirements or hide a prerequisite that Claude needs to finish safely.
- Keep Claude's applicable project instructions and skills enabled. For this CLI task, add a
  validated task-private `--settings` overlay whose `skillOverrides` sets only
  `codex-claude-loop` to `off`. Merge it with any other launch settings without replacing them,
  preserve normal setting sources, and verify that the override is effective. Confirm the
  coordinator skill is hidden and an unrelated applicable skill remains available through an
  effective-configuration check or a separate read-only probe. Reapply and verify the overlay on
  every resumed invocation. The installed Claude Code version and settings validation must support
  this route; a settings file's presence alone is not proof. If visibility cannot be verified,
  hold launch and report the configuration issue. Do not use `--bare`, `--safe-mode`, or a blanket
  skill disable to hide this skill, because those routes also suppress instructions or other skills
  Claude needs.
- Start a fresh Claude session for an isolated task. Before resuming, check that the recorded
  session has not received task-specific coordination or future-review details through prompts,
  plans, tool results, or earlier skill invocation. Existing context cannot be erased. If a prior
  session is contaminated, reconcile its termination, descendants, index, files, tests, and
  external effects before starting a new clean session with the same authorized task and explicit
  checkpoint. Do not claim a resumed session forgot earlier information. Global shared guidance
  may still mention the skill generically; this is task-context isolation, not filesystem secrecy.

## Choose Claude's model and effort

- Before launch, choose and record the model and its supported effort level for this task; if the
  chosen model has no configurable effort, record that fact instead of inventing a level. Preserve
  a model or effort explicitly chosen by the user independently; choose only the unspecified value.
  For complex work, use the recommended Opus 5.5 xhigh profile when available. Select the exact
  model ID for the active provider, or verify that an alias resolves to Opus 5.5; `opus` can resolve
  to an older version.
  For shorter work, choose a compatible model and, when supported, effort suited to the task.
  Consider latency, cost, and explicit user constraints without imposing a coordinator-selected
  cost cap.
- Check the provider's current
  [model configuration](https://code.claude.com/docs/en/model-config) and known organization
  restrictions for the chosen model and effort. Some models do not support effort, and a requested
  level can be reduced by model support or an organization cap. Do not pair a model that lacks
  effort support with a required `--effort` flag or silently replace a user-specified value. If
  the selected setting is denied or incompatible, report the constraint and obtain the user's
  choice.
- Record the selected model and supported effort, or the absence of configurable effort, and why
  that setting fits this task. Keep the requested setting distinct from what later output actually
  confirms. Inspect structured result model usage and any warnings for model substitution;
  reconcile an unexpected primary model before another turn. Structured output may silently clamp
  effort and does not itself confirm the applied level. Check known caps
  before launch, treat any known conflict as a decision to resolve, and report unconfirmed applied
  effort as a limitation rather than claiming the requested level was observed.

## Launch and supervise implementation

- Prepare a task-specific prompt with the objective, authorized scope, acceptance criteria,
  task-facing plan or brief if any, repository instructions, existing changes to preserve, and the
  precise work assigned to Claude. After any selected pre-edit review, assign the authorized
  implementation,
  baseline tests, and post-change tests to the same implementer. A required regression-first gate
  may sequence the work; resume Claude for production changes and affected tests after that gate.
  Do not impose a tests-only milestone or reserve test execution for Codex merely for coordinator
  convenience. The prompt is task data, not permission to ignore higher instructions. Do not tell
  Claude that Codex or another agent will review, test, finish, or deliver the task afterward.
  Tell Claude to follow its applicable instructions and skills, use internal subagents only when
  authorized, and finish the assigned work, tests, and user-selected reviews before reporting
  completion. Pass the user's review choice explicitly; assignment to Claude alone does not
  authorize an internal review agent. Assign requested Git or external
  delivery only when the user authorized those exact actions; otherwise exclude them from Claude's
  scope without promising someone else will perform them. Delegate the relevant plan, scope,
  baseline, task authorization, and skill-loading instructions: a non-fork subagent does not
  inherit Claude's conversation or previously invoked skills. Claude integrates delegated work,
  addresses review findings, and repeats affected checks. When the user selected Claude-side
  review, Claude obtains a qualified fresh-context reviewer within its execution. Record the
  reviewer, effective model and effort, evidence examined, and findings. If that selected review
  is unavailable, report the blocker rather than counting a later review as Claude's own.
  Ask for a concise final report with changed files, actual test commands and outcomes, required
  review evidence and resolutions, blockers, evidence locations, and any unfinished delegated or
  background work, without pasted tool transcripts, logs, or internal reasoning. A test started in
  the background needs a retained identity and terminal result before Claude claims it passed.
  In no-host print mode, tell Claude not to call `AskUserQuestion`: when an essential task decision
  is missing, stop at a safe boundary and begin its final answer with `NEEDS_USER:`, followed by
  the exact question, brief decision context, partial changes, and test status. Do not guess an
  answer or keep implementing past that boundary. Pass the prompt without shell expansion of
  untrusted text.
- Choose and record a permission profile for the task's authorized implementation and tests
  before launch. Check inherited allow, ask, and deny rules, managed settings, and the installed
  CLI's actual permission-rule syntax. Use `--allowedTools` or `--disallowedTools` only for a
  concrete task or instruction reason and verify their patterns. `--allowedTools` preapproves
  matching calls in modes that consult allow rules; it does not confine the available tools or
  override inherited denials. A deny pattern covers only what it actually matches. Do not silently
  widen permissions after a denial. Do not deny Claude's subagent tool or impose a narrow tool
  list merely to enforce one implementation owner; internal delegates remain under Claude's
  responsibility. If a tool or suitable agent needed for the task is unavailable or denied,
  report the exact prerequisite rather than silently claiming the delegated work was done.
- For supervised permission requests in print mode, verify an Agent SDK permission host or a
  working `--permission-prompt-tool` before launch. Have that host surface each request to Codex,
  preserve the same process handle, and return a decision only when it is unambiguous and already
  authorized; otherwise ask the user. A plain `claude -p` call without a permission host denies
  requests that would prompt. `dontAsk` and `--permission-prompts none` intentionally deny such
  requests, so do not use them while claiming that an operator can answer prompts. If no working
  host is available, report the prerequisite before launch or use a different, user-authorized
  no-prompt profile; do not invent a prompt path or switch modes silently. A host that handles
  permission requests does not thereby prove it can deliver `AskUserQuestion`; verify task-question
  support separately before promising an in-process question.
- A no-prompt profile may use a supported permission mode suited to the task. `dontAsk` with
  preapproved tools remains an option for deliberately fixed, unattended work, not the default
  for complex implementation. `bypassPermissions` is a valid option when the user has chosen
  broad autonomy for this task, including an applicable earlier choice, and the environment is
  suitably isolated and provider or managed policy permits it. It skips ordinary permission
  prompts; `--allowedTools` does not restrict it, and it does not negate inherited deny or ask
  rules, other provider safeguards, or the user's scope. Check the installed CLI and effective
  rules before relying on that mode. If the profile cannot run an assigned test, including a
  repository-prescribed Docker Compose test, report the exact blocked action and decision needed;
  Claude retains test ownership. A named user-requested test carries only the authorization in
  `test-quality`, including its documented test effects. No profile authorizes staging, commits,
  live writes, publication, or external actions beyond the user's request.
- Before launch, verify that the available tool can consume CLI events and keep raw output out of
  Codex's model context while retaining the original Claude exit status and, when chosen, a
  working permission host. Use one `claude -p` run from the verified checkout with a unique
  `--session-id`, `--model <chosen-model>`, the verified task-private `--settings` overlay, and the
  chosen permission mode, even when the user did not specify the model. Pass
  `--effort <chosen-level>` only when the model supports configurable effort; omit it and record
  that fact otherwise. Use structured `stream-json` output with the installed CLI options needed
  to receive initialization diagnostics and the final `result` event.
  Do not enable partial-message or subagent-text forwarding merely for progress.
  Do not add self-imposed turn, duration, iteration, or cost limits. User limits and provider or
  runtime quotas, context windows, and safety controls still apply. If the tool cannot filter the
  stream safely or the chosen prompt route cannot deliver requests, report the limitation before
  launch instead of claiming a low-token or interactive supervised run.
- In the tool boundary, capture raw stdout and stderr separately in task-private diagnostic files
  outside the tracked checkout. Consume the event stream and stderr as they arrive without
  forwarding progress, tool calls, thinking, partial messages, logs, or raw event JSON into Codex's
  context. Surface only an actionable prompt or error during execution. At exit, expose a compact
  envelope: Claude's final answer, its actual process exit code, exact session ID, observed model
  and relevant warnings, and any initialization, permission denial, safety-classifier interruption,
  task-question marker, known unfinished delegated work, or result error that changes the outcome.
  Check structured startup diagnostics and captured stderr, including plugin and MCP load failures,
  even if Claude exits zero. Preserve the raw files for targeted diagnosis when needed; do not read
  or summarize them routinely. An output filter or pipeline must preserve Claude's exit status.
  Never write a command that redirects stderr to `/dev/null`; verify the command actually run before
  claiming stderr was preserved.
- Keep one process handle and the exact session ID bound to this task. Normally wait on that same
  handle until Claude exits. If the tool yields early, consume only the new events inside the tool
  boundary and surface an actionable prompt or error, including a prompt fragment without a
  trailing newline; otherwise continue waiting on the same handle for the longest suitable
  supported interval. Do not establish a fixed 30- or 55-second cadence, repeatedly use a short
  default, or run a background polling wrapper while the handle is available. Silence and an
  ordinary yield do not justify `ps`, log or status-file reads, Git checks, or cancellation. When
  process state or identity is missing or contradictory, inspect it read-only and reconcile the
  exact session before waiting, resuming, or relaunching. Answer a prompt only when the response
  is unambiguous and authorized; otherwise report the decision needed to the user.
- Treat user-facing updates separately from CLI observation. Send an update when higher-priority
  instructions require one without inspecting the process, files, or Git just to produce it. Do
  not add periodic progress updates by skill preference when the user has dispensed with them and
  higher-priority instructions permit that choice. Describe only the last observed state unless
  a current-state claim is independently required and checked. A tool wait interval is not a task
  deadline.
- A nonzero exit, malformed or absent result, mismatched session ID, provider or runtime limit,
  interruption, permission denial, or safety-classifier block is a partial result. Inspect
  `permission_denied` events, final `permission_denials`, and the actual diagnostic before naming
  a cause. An empty denial array alone does not identify a classifier block; when the diagnostic
  names the classifier, do not attribute it to `dontAsk` or recommend `bypassPermissions` as a
  workaround. Inspect the index, working tree, session, and any external effects before retrying
  or resuming; do not call the task complete or retry blindly. A successful exit and Claude's
  report are also only evidence to inspect. A final answer beginning `NEEDS_USER:` is a paused,
  partial result even when the process exits zero. If Claude instead asks for a blocking decision
  without the marker, treat it as a malformed partial result rather than completion. A root CLI exit
  while a delegated agent or required test is still running is likewise partial, even with exit
  code zero. Identify and reconcile descendants and their effects before Codex reviews, resumes,
  or starts another checkout owner; unknown termination does not release ownership.

For a long, quiet run, acceptance means one implementation owner and one retained root process
handle/session, with any internal subagents and background tests accounted for. Raw output stays
outside Codex context; no routine process, log, status-file, or Git probes or invented turn or time
cap occur. Examine the compact result and Claude's own exit code, including completed test and
review evidence, before Codex independently checks the changed files. Codex does not supply
missing Claude work.

## Host-owned supervisor for a Codex CLI session

For a long Claude run coordinated through `codex exec`, use
[`../scripts/follow_claude.py`](../scripts/follow_claude.py) when a host process can remain active
outside Codex turns. This route requires an existing exact **Codex CLI session ID**. It does not
resume this Codex app or API chat, and a session ID from another client is not interchangeable.
The Python supervisor owns the worker that launches Claude; a Codex tool command must not detach
Claude and assume it will survive the command's sandbox. The direct-handle route above remains
appropriate when the current interface can wait on its process handle or an interactive permission
host is needed.

Complete the checkout, model, effort, trust, permission, settings-overlay, and authorization
checks above before starting this route. It supports a verified **no-prompt** Claude profile;
it does not implement an interactive permission host. If the task requires permission decisions
while Claude runs, use a verified interactive host through the direct route or report the missing
prerequisite. The selected permission mode still cannot expand the user's task authorization.
Do not let a model-generated command or decision replace the coordinator's verified CLI options.

Create a task-private JSON config outside the checkout with these fields: `checkout` is the
absolute runtime checkout path; `codex.bin` and `claude.bin` are the verified executables;
`codex.args` and `claude.args` are arrays of verified CLI arguments. In `claude.args`, specify
the exact `--model`, the supported `--effort` when applicable, the verified task-private
`--settings` overlay, and the chosen `--permission-mode`. The supervisor owns `-p`,
`--output-format stream-json`, `--verbose`, and the exact Claude session or resume flag; do not
repeat those in the config. `codex.args` must preserve the selected Codex model, effort, and
approval configuration across resumes. Verify the installed CLI syntax; do not infer account
model access from the flag alone. Keep the config and start prompt stable for recovery.

Start a Codex CLI session with the authorized task context. From the canonical skill directory,
give the supervisor its exact ID, a task-private start prompt for Codex's first decision, and a
private state directory outside the checkout:

```text
python3 scripts/follow_claude.py follow \
  --config <private-config.json> --state-dir <private-state-dir> \
  --codex-session <exact-codex-cli-session-id> --start-prompt <private-start-prompt.txt>
```

Codex returns a structured decision to run Claude, finish, or request a user decision. For a
Claude run, Codex supplies a self-contained task prompt without coordinator or future-review
details; the host launches exactly one Claude worker with the configured options and waits for its
terminal status without another Codex turn. The worker keeps raw stdout and stderr in private
files, extracts the final result, result-error details, and diagnostic stderr lines, and preserves
Claude's exit code and session ID. It runs Claude in a private process group and waits for live
members of that group, including background tests, after the root CLI process exits. An escaped
or detached process outside that group still requires explicit reconciliation when indicated by
Claude's result or other evidence. Only the compact terminal result is sent to `codex exec resume`
for checkout verification and the next decision. A `done` decision ends the CLI loop; it does not replace any
separately selected final review or other delivery gate.

A `needs_user` decision stops the script and prints the exact question. After the user supplies an
answer that actually releases the paused task under applicable instructions, invoke the same
command with `--answer-file <private-user-answer.txt>`. The answer is passed to the same Codex CLI
session before another Claude run. Do not fabricate an answer, treat a question-shaped reply as
implementation authorization, or modify the state file to skip the pause.

The state directory binds the config, start prompt, Codex session, and one Claude session. Keep
it intact. If the outer supervisor is interrupted while the worker runs, invoke it again with the
same arguments: it waits for that identified worker and does not launch another implementer. If
the worker exits without a terminal record, its identity is uncertain, or a Codex turn or worker
launch was interrupted at an ambiguous point, the script stops instead of retrying. Reconcile
the exact process, recorded process group, CLI session, index, checkout changes, background descendants, tests, and any
external effects before continuing. Do not delete a state marker, switch session or model, or
launch a fresh worker merely to make the loop advance. No coordinator-imposed turn, time,
iteration, or cost limit is added; provider limits and user limits still apply.

## Handle a task question without an in-process host

When the final answer begins `NEEDS_USER:`, confirm that the process ended, the recorded session
ID matches, and any delegated agents or background commands are reconciled. Read the exact
question from the compact result and relay it with the decision context and known partial effects;
do not infer an answer from prior task wording. Keep
implementation paused. Reconcile the index, working tree, tests already run, and any external
effects before another Claude turn. An absent or unclear question, mismatched session, or
unreconciled effect is a partial-result diagnostic, not permission to start a fresh session or
claim completion. If the question is missing but the session is sound, ask the same Claude session
to state the exact question before seeking a user decision.

Treat the user's reply as a new turn under the applicable instructions. Confirm that it resolves
the question unambiguously and permits continued implementation; a question-shaped reply or a
reply that does not satisfy a required explicit-action gate does not release paused work. Update
any selected plan and ask about any uncovered review before resuming if the answer changes the
agreed approach. A declined new review does not block otherwise authorized continuation.
Then pass the actual user answer to the same recorded session only if its context is isolated. Use
`--resume <session-id>`, the recorded model, supported effort, verified task-private `--settings`
overlay, and permission boundary under **Review and continue**. Do not silently change the
implementer, session, model, effort, or permissions. Claude remains responsible for
finishing its assigned implementation and applicable tests; Codex verifies the result and obtains
any selected independent closure review.

This final-result route handles a task clarification, not a tool permission request. A permission
denial requires its own diagnostic and authorization decision; neither `NEEDS_USER:` nor the user's
task answer grants a denied tool, expands the scope, or overrides a safety-classifier block.

## Review and continue

If high-risk work is discovered mid-task, reassess authorization and recommend suitable settings,
plan detail, and review scope. Honor the user's process, model, and effort choices. Hold affected
work for a newly selected pre-edit review until completion or withdrawal, not merely because risk
increased. The Codex coordinator
inspects changed files, index, diffs, status, and verification evidence against the user request,
applicable instructions, any selected plan, and acceptance
criteria. Confirm that Claude ran the applicable baseline and post-change tests through the
repository-prescribed environment and inspect their actual results. Codex may independently rerun
authorized checks when useful or required by governing skills; that rerun does not replace Claude's
assigned test execution. Inspect the outcome of any selected Claude-side review; it does not
replace a separately selected Codex-side review or the coordinator's author checks.
Give Claude only concrete task findings that still require implementation, without identifying a
later reviewer or promising another review. When findings expose a recurring defect class, assign
the relevant invariant and adjacent cases for Claude to inspect and correct under its own skills,
rather than passing one variant at a time without context.

Resume the exact recorded session with `--resume <session-id>` only after confirming the prior
process has ended, partial effects are understood, and its context remains isolated. Do not use
`--continue`, a session-name search, or `--fork-session`. Pass the recorded `--model` and verified
task-private `--settings` overlay again on every resumed invocation. Repeat the recorded `--effort`
only if the model supports it; otherwise omit the flag as before. Do not depend on saved or
restored defaults. Keep the same checkout, permission boundary, and user-authorized limits unless
the user explicitly changes a choice; record that decision before resuming. A response or tool
failure alone does not justify a new session. Prior exposure of task-specific coordination does:
reconcile the old session and effects under **Isolate Claude's task context** before a clean launch.

After the coordinator verifies the result, obtain any selected independent closure review
before declaring its dependent phase complete. Do not add a substitute author audit or second
reading when no review was selected.
Send actionable findings to the same Claude session, then repeat invalidated checks and any
selected closure review after material corrections. Continue supervising until Codex verifies
completion or a concrete blocker appears: a missing user decision or prerequisite, denied
permission, unavailable selected reviewer, unreconciled process or effects, a required check that
cannot be completed or corrected within the authorized scope, or repeated findings with no viable
next action. Report the evidence and remaining work; do not stop for a count chosen by the
coordinator or repeat the same failed action blindly.

If the Codex process is interrupted, first establish whether Claude or delegated work is still
running. Do not resume or relaunch while another owner or descendant may be active. After confirmed
termination, inspect the exact session, repository state including the index, and any partial
external effects before continuing.
If process, session, or effects cannot be reconciled, stop and ask the user how to proceed. On an
explicit user pause or cancellation, interrupt the running process and reconcile any delegated
agents or background commands before releasing the checkout; verify termination, preserve and
report partial changes, and do not resume until a later explicit user instruction. A cancelled
task needs a new request.

Any user-selected persistent implementation plan still applies. CLI
options and headless startup behavior are documented in the
[Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference) and
[programmatic-use guide](https://code.claude.com/docs/en/headless). Check the current
[permission modes](https://code.claude.com/docs/en/permission-modes) and
[rule syntax](https://code.claude.com/docs/en/permissions) before choosing a profile.
