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
  `--session-id`, an explicit finite `--max-turns`, and the user's model and effort choices when
  specified. Supervise the process with a finite deadline. Set an overall finite limit for
  implementation/review iterations before the first launch. If using a cost cap, account for the
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
`--fork-session`. Keep the same checkout, permission boundary, and finite limits. Do not start a
new session merely because a response or tool call failed.

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
