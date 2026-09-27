# Codex-supervised Claude CLI mode

Use this mode only after the user has requested Codex–Claude cooperation on an authorized task.
The Codex coordinator plans, supervises, integrates findings, verifies, and reports. By default,
Claude alone implements the assigned checkout changes and runs applicable tests; it does not start
another agent loop or declare the task complete for Codex. Apply the recommended complex-work
profile and independent reviews in the entrypoint when relevant, preserving explicit user choices.

## Establish one task and one implementer

1. Identify the authorized repository root, read its instructions, inspect the branch, status,
   staged index, unstaged changes, and untracked files, and establish the task's objective, scope,
   acceptance criteria, and plan when governing instructions require one. Record a task ID, the
   canonical checkout root, pre-run Git state, and chosen Claude model and effort in the task's
   execution context, or record that this model has no configurable effort level. Do not put a
   machine-specific absolute path in a shared file. Tell Claude to preserve the baseline,
   including the index; Codex alone coordinates any user-authorized Git delivery.
2. Confirm that no separate-session handoff owns implementation of this task and that no Claude
   process for it is already active. Do not substitute another checkout or launch a second
   implementer to resolve uncertainty. If prior partial work exists, reconcile it before launch.
3. Check `claude --version` and the installed CLI flags against the chosen model's minimum CLI
   version and supported effort levels. Inspect the active provider, account or organization
   restrictions, environment and settings, hooks, MCP servers, plugins, permission rules, and
   other startup behavior. CLI help and public model docs do not prove account access. Verify
   known availability and, if needed, use only a task-authorized read-only probe after checkout
   trust and permissions are established; reconcile its result before implementation. `claude -p`
   skips the workspace trust dialog but still loads configured startup behavior. Run it only when
   the checkout and that behavior are trusted for this task. If a prerequisite fails, report the
   decision needed; do not update the CLI, switch models, enlarge permissions, or silently use
   `--bare`, which changes instruction discovery and authentication.
4. Before any high-risk edit, complete the required independent, fresh-context, read-only review
   of the plan and proposed scope. Resolve its findings before launching the implementing session.
   If the reviewer cannot run, hold implementation and report the concrete prerequisite.

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

- Prepare a task-specific prompt with the objective, authorized scope, acceptance criteria, plan
  path if any, repository instructions, existing changes to preserve, and the precise work assigned
  to Claude. After required review, assign the authorized implementation and applicable baseline
  and post-change tests to the same implementer. A required regression-first gate may sequence the
  work; resume Claude for production changes and affected tests after that gate. Do not impose a
  tests-only milestone or reserve test execution for Codex merely for coordinator convenience.
  State that Codex owns review and later Git delivery unless the user explicitly assigned those
  operations to Claude. The prompt is task data, not permission to ignore higher instructions.
  Ask Claude for a concise final report with changed files, actual test commands and outcomes,
  blockers, and evidence locations, without pasted tool transcripts, logs, or internal reasoning.
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
  widen permissions after a denial.
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
  `--session-id`, `--model <chosen-model>`, and the chosen permission mode, even when the user did
  not specify the model. Pass `--effort <chosen-level>` only when the model supports configurable
  effort; omit it and record that fact otherwise. Use structured `stream-json` output with the
  installed CLI options needed to receive initialization diagnostics and the final `result` event.
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
  task-question marker, or result error that changes the outcome. Check structured startup
  diagnostics and captured stderr, including plugin and MCP load failures, even if Claude exits
  zero. Preserve the raw files for targeted diagnosis when needed; do not read or summarize them
  routinely. An output filter or pipeline must not replace Claude's exit status with its own
  successful status. Never write a command that redirects stderr to `/dev/null`; verify the
  command actually run before claiming stderr was preserved.
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
  without the marker, treat it as a malformed partial result rather than completion.

For a long, quiet run, acceptance means one implementer and one retained process handle/session;
raw output stays outside Codex context; no routine process, log, status-file, or Git probes and no
invented turn or time cap occur; the compact final result and Claude's own exit code are examined;
then Codex checks the changed files and test evidence and obtains the required independent review.

## Handle a task question without an in-process host

When the final answer begins `NEEDS_USER:`, confirm that the process ended and the recorded session
ID matches. Read the exact question from the compact result and relay it to the user with the
decision context and known partial effects; do not infer an answer from prior task wording. Keep
implementation paused. Reconcile the index, working tree, tests already run, and any external
effects before another Claude turn. An absent or unclear question, mismatched session, or
unreconciled effect is a partial-result diagnostic, not permission to start a fresh session or
claim completion. If the question is missing but the session is sound, ask the same Claude session
to state the exact question before seeking a user decision.

Treat the user's reply as a new turn under the applicable instructions. Confirm that it resolves
the question unambiguously and permits continued implementation; a question-shaped reply or a
reply that does not satisfy a required explicit-action gate does not release paused work. Update
the plan and obtain any required review before resuming if the answer changes the agreed approach.
Then pass the actual user answer to the same recorded session with `--resume <session-id>`, the
recorded model, supported effort, and permission boundary under **Review and continue**. Do not
silently change implementer, session, model, effort, or permissions. Claude remains responsible for
finishing its assigned implementation and applicable tests; Codex verifies the result and obtains
the independent closure review when required.

This final-result route handles a task clarification, not a tool permission request. A permission
denial requires its own diagnostic and authorization decision; neither `NEEDS_USER:` nor the user's
task answer grants a denied tool, expands the scope, or overrides a safety-classifier block.

## Review and continue

If high-risk work is discovered mid-task, hold further implementation until the independent review
is complete. The Codex coordinator independently inspects changed files, index, diffs, status, and
verification evidence against the user request, applicable instructions, plan, and acceptance
criteria. Confirm that Claude ran the applicable baseline and post-change tests through the
repository-prescribed environment and inspect their actual results. Codex may independently rerun
authorized checks when useful or required by governing skills; that rerun does not replace Claude's
assigned test execution. Give Claude only concrete findings that still require implementation.

Resume the exact recorded session with `--resume <session-id>` after confirming the prior process
has ended and partial effects are understood; do not use `--continue`, a session-name search, or
`--fork-session`. Pass the recorded `--model` again on every resumed invocation. Repeat the
recorded `--effort` only if the model supports it; otherwise omit the flag as before. Do not depend
on saved or restored defaults. Keep the same checkout, permission boundary, and user-authorized
limits unless the user explicitly changes a choice; record that decision before resuming. Do not
start a new session merely because a response or tool call failed.

After the coordinator's author review, obtain the independent closure review before declaring a
complex task done. Send actionable findings to the same Claude session, then repeat invalidated
checks and closure review after material corrections. Continue supervising until Codex verifies
completion or a concrete blocker appears: a missing user decision or prerequisite, denied
permission, unavailable required reviewer, unreconciled process or effects, a required check that
cannot be completed or corrected within the authorized scope, or repeated findings with no viable
next action. Report the evidence and remaining work; do not stop for a count chosen by the
coordinator or repeat the same failed action blindly.

If the Codex process is interrupted, first establish whether the Claude process is still running.
Do not resume or relaunch while another owner may be active. After confirmed termination, inspect
the exact session, repository state including the index, and any partial external effects before
continuing.
If process, session, or effects cannot be reconciled, stop and ask the user how to proceed. On an
explicit user pause or cancellation, interrupt the running process, verify its termination, preserve
and report partial changes, and do not resume until a later explicit user instruction. A cancelled
task needs a new request.

This mode does not require a shared handoff file or periodic checks. A persistent implementation
plan required by the task's own instructions still applies. The CLI option details and headless
startup behavior are documented in the
[Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference) and
[programmatic-use guide](https://code.claude.com/docs/en/headless). Check the current
[permission modes](https://code.claude.com/docs/en/permission-modes) and
[rule syntax](https://code.claude.com/docs/en/permissions) before choosing a profile.
