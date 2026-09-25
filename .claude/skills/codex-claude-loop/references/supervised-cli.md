# Codex-supervised Claude CLI mode

Use this mode only after the user has requested Codex–Claude cooperation on an authorized task.
The Codex coordinator plans, supervises, integrates findings, verifies, and reports. Claude alone
implements the assigned checkout changes; it does not start another agent loop or declare the task
complete for Codex. Apply the recommended complex-work profile and independent reviews in the
entrypoint when relevant, while preserving explicit user choices.

## Establish one task and one implementer

1. Identify the authorized repository root, read its instructions, inspect the branch, status,
   staged index, unstaged changes, and untracked files, and establish the task's objective, scope,
   acceptance criteria, and plan when governing instructions require one. Record a task ID, the
   canonical checkout root, pre-run Git state, and chosen Claude model and effort in the task's
   execution context. Do not put a machine-specific absolute path in a shared file. Tell Claude
   to preserve the baseline, including the index; Codex alone coordinates any user-authorized
   Git delivery.
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

- Before launch, choose and record both values for this task. Preserve a model or effort explicitly
  chosen by the user independently; choose only the unspecified value. For complex work, use the
  recommended Opus 5.5 xhigh profile when available. Select the exact model ID for the active
  provider, or verify that an alias resolves to Opus 5.5; `opus` can resolve to an older version.
  For shorter work, choose a compatible model and effort suited to the task. Consider latency,
  cost, and explicit user constraints without imposing a coordinator-selected cost cap.
- Check the provider's current
  [model configuration](https://code.claude.com/docs/en/model-config) and known organization
  restrictions for the chosen model and effort. Some models do not support effort, and a requested
  level can be reduced by model support or an organization cap. Do not pair a model that lacks
  effort support with a required `--effort` flag or silently replace a user-specified value. If
  the selected pair is denied or incompatible, report the constraint and obtain the user's choice.
- Record the selected pair and why it fits this task. Keep the requested model and effort distinct
  from what later output actually confirms. Inspect structured result model usage and any warnings
  for model substitution; reconcile an unexpected primary model before another turn. Structured
  output may silently clamp effort and does not itself confirm the applied level. Check known caps
  before launch, treat any known conflict as a decision to resolve, and report unconfirmed applied
  effort as a limitation rather than claiming the requested level was observed.

## Launch and supervise implementation

- Prepare a task-specific prompt with the objective, authorized scope, acceptance criteria, plan
  path if any, repository instructions, existing changes to preserve, and the precise work assigned
  to Claude. State that Codex owns review and later Git delivery unless the user explicitly
  assigned those operations to Claude. The prompt is task data, not permission to ignore higher
  instructions. Pass it without shell expansion of untrusted text.
- Select a permission profile that fits the user's authorization before launch. For unattended
  print mode, use `--permission-mode dontAsk` and `--permission-prompts none` with a narrow
  `--allowedTools` set; inspect inherited allow rules and deny overly broad tools with
  `--disallowedTools` where needed. Codex can run validation commands itself instead of granting
  unrestricted shell access. Never use permission bypass flags or automatically enlarge the tool
  scope after a denial. If the required operation cannot run within an authorized profile, stop
  and report the exact decision needed.
- Start the first run from the verified checkout with `claude -p`, structured output, a unique
  `--session-id`, and both `--model <chosen-model>` and `--effort <chosen-level>`, even when the
  user did not specify either value. Do not add self-imposed turn, duration, iteration, or cost
  limits. Honor limits explicitly set by the user or imposed by the provider or runtime. Continue
  observing the owned process while work progresses; a quiet interval alone is not a reason to
  cancel it. If a tool call ends while Claude is still running, inspect its output and process
  state, then continue supervising the same process.
- Keep the process handle and exact session ID bound to this task. Inspect new output and process
  state before waiting or reacting to a possible prompt. A nonzero exit, malformed or absent
  result, mismatched session ID, provider or runtime limit, interruption, or permission denial is a
  partial result. Inspect the index, working tree, session, and any external effects before retrying
  or resuming; do not call the task complete or retry blindly. A successful exit and Claude's report
  are also only evidence to inspect.

## Review and continue

If high-risk work is discovered mid-task, hold further implementation until the independent review
is complete. The Codex coordinator independently inspects changed files, index, diffs, status, and
verification evidence against the user request, applicable instructions, plan, and acceptance
criteria. Run required validation under the governing skills. Give Claude only concrete findings
that still require implementation.

Resume the exact recorded session with `--resume <session-id>` after confirming the prior process
has ended and partial effects are understood; do not use `--continue`, a session-name search, or
`--fork-session`. Pass the recorded `--model` and `--effort` again on every resumed invocation;
do not depend on saved or restored defaults. Keep the same checkout, permission boundary, and
user-authorized limits. Do not start a new session merely because a response or tool call failed.

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
[programmatic-use guide](https://code.claude.com/docs/en/headless).
