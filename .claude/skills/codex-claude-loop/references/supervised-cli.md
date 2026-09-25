# Codex-supervised Claude CLI mode

Use this mode only after the user has requested Codex–Claude cooperation on an authorized task.
Codex remains the planner, process supervisor, reviewer, and final reporter. Claude implements only
the assigned work; it does not start another agent loop or declare the task complete for Codex.

## Establish one task and one implementer

1. Identify the authorized repository root, read its instructions, inspect the branch, status, and
   existing changes, and establish the task's objective, scope, acceptance criteria, and plan when
   the governing instructions require one. Record a task ID, the canonical checkout root, the
   pre-run state, and the chosen Claude model, effort, and execution limits in the task's execution
   context. Do not put a machine-specific absolute path in a shared file.
2. Confirm that no separate-session handoff owns implementation of this task and that no Claude
   process for it is already active. Do not substitute another checkout or launch a second
   implementer to resolve uncertainty. If prior partial work exists, reconcile it before launch.
3. Confirm the local `claude` CLI and required flags are available. Inspect the active Claude
   configuration and the checkout's hooks, MCP servers, plugins, permissions, and other startup
   customizations before a headless launch. `claude -p` skips the workspace trust dialog but still
   loads configured startup behavior. Run it only when the checkout and that behavior are trusted
   for this task. If they cannot be established, stop and obtain the user's choice of execution
   profile. Do not silently switch to `--bare`: it skips discovered instructions and
   customizations and has different authentication requirements.

## Choose Claude's model and effort

- Before launch, choose and record both values for this task. Preserve a model or effort explicitly
  chosen by the user independently; choose only the unspecified value. For short, mechanical work,
  prefer `sonnet` at low or medium effort; for ordinary implementation, prefer `sonnet` at high
  effort; for complex debugging, broad changes, or consequential decisions, consider `opus` at
  high or xhigh effort. Reserve more capable models and deeper effort for work
  that warrants their latency and cost. Consider `fable` for unusually hard or long tasks only
  after confirming access and any usage-credit cost. These are starting points, not fixed defaults.
- Check the installed CLI, provider, current
  [model configuration](https://code.claude.com/docs/en/model-config), and known organization
  restrictions for the chosen model and effort. Some models do not support effort, and a requested
  level can be reduced by model support or an organization cap. Do not pair a model that lacks
  effort support with a required `--effort` flag or silently replace a user-specified value. If
  the requested pair cannot run as intended, report the constraint and obtain the user's choice.
- Record the selected pair and why it fits this task. Keep the requested model and effort distinct
  from what later output actually confirms. Inspect structured result model usage and any warnings
  for model substitution; reconcile an unexpected primary model before another turn. Structured
  output may silently clamp effort and does not itself confirm the applied level. Check known caps
  before launch, treat any known conflict as a decision to resolve, and report unconfirmed applied
  effort as a limitation rather than claiming the requested level was observed.

## Launch a bounded implementation turn

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
  `--session-id`, an explicit finite `--max-turns`, and both `--model <chosen-model>` and
  `--effort <chosen-level>`, even when the user did not specify either value. Supervise the
  process with a finite deadline. Set an overall finite limit for implementation/review iterations
  before the first launch. If using a cost cap, account for the
  fact that `--max-budget-usd` applies per invocation, including a resumed invocation. On deadline
  expiry, interrupt the owned process and confirm termination before inspecting partial effects.
  If termination cannot be confirmed, stop further work and report the active-process uncertainty.
- Keep the process handle and exact session ID bound to this task. Inspect new output and process
  state before waiting or reacting to a possible prompt. A nonzero exit, malformed or absent
  result, mismatched session ID, turn or deadline exhaustion, or permission denial is a partial
  result. Inspect the working tree and reconcile it; do not call the task complete or retry blindly.
  A successful exit and Claude's report are also only evidence to inspect.

## Review and continue

Codex independently inspects the changed files, diffs, status, and verification evidence against
the user request, applicable instructions, plan, and acceptance criteria. Run required validation
under the governing skills. Give Claude only concrete findings that still require implementation.
Resume the exact recorded session with `--resume <session-id>` after confirming the prior process
has ended and partial effects are understood; do not use `--continue`, a session-name search, or
`--fork-session`. Pass the recorded `--model` and `--effort` again on every resumed invocation;
do not depend on saved or restored defaults. Keep the same checkout, permission boundary, and
finite limits. Do not start a new session merely because a response or tool call failed.

Stop the loop when Codex verifies completion, a user decision or prerequisite is missing, a
permission is denied, a required check cannot be completed, the iteration limit is reached, or
findings recur without progress. Report the observed state and remaining work. Do not turn a
repeated finding into another automatic implementation turn.

If the Codex process is interrupted, first establish whether the Claude process is still running.
Do not resume or relaunch while another owner may be active. After confirmed termination, inspect
the exact session, repository state, and any partial external effects before continuing.
If process, session, or effects cannot be reconciled, stop and ask the user how to proceed. On an
explicit user pause or cancellation, interrupt the running process, verify its termination, preserve
and report partial changes, and do not resume until a later explicit user instruction. A cancelled
task needs a new request.

This mode does not require a shared handoff file or periodic checks. A persistent implementation
plan required by the task's own instructions still applies. The CLI option details and headless
startup behavior are documented in the
[Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference) and
[programmatic-use guide](https://code.claude.com/docs/en/headless).
