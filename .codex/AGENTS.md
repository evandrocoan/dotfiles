# Global agent instructions

Never redirect standard error to `/dev/null` (`2>/dev/null`). Hidden errors make
failures impossible to diagnose.

## Startup and workspace scope

At the start of work in each workspace root, before running project commands or
editing files, locate and read its root `AGENTS.md` if present. Use `CLAUDE.md`
only as a compatibility fallback when `AGENTS.md` is absent, and follow an
`@AGENTS.md` import by reading the target directly. Commands used only to locate
or read instruction files are permitted before this step. Read each file once
at startup. Reread it in full when it changes, when a new workspace root is
added, or when an applicable high-risk audit explicitly requires it. In later
turns, inspect only the relevant passage when exact wording matters or the file
may have changed; a turn boundary alone does not require another full reread.

Project instructions may refine global workflow assumptions, but must not relax
global safety, authorization, workspace-scope, or destructive-action boundaries.

When SSH works in the user's terminal but fails in the agent, inspect `ssh -G <host>`, the inherited
`SSH_AUTH_SOCK`, and active agent sockets (`ss -xl` on Linux) before reporting missing access.
A stale keyring socket can coexist with a working GNOME GCR agent. Check that the socket belongs
to the same user and use `ssh-add -l` to verify the expected public-key fingerprint, then select
the existing agent with a process-scoped socket override for the authorized connection. A
`BatchMode` rejection alone does not establish that credentials are unavailable.

When Kubernetes RBAC denies `exec`, port-forwarding, or proxy access in a service's namespace,
check the relevant permissions in application namespaces already within the task's scope before
reporting that authorized service diagnostics are unavailable. Where both pod access and the
target service operation are authorized, prefer an existing suitable client pod in an allowed
namespace and connect through the target Service's cluster DNS name, subject to NetworkPolicy
and service authentication. Keep diagnostic commands read-only whether using an existing or
temporary client pod. If a temporary client pod is needed and its creation is authorized, use
an image already declared or approved for the task and verify cleanup. Do not expand permissions
or use another workload's credentials to gain additional access. Network reachability does not
authorize the target operation. If no permitted route works or the diagnostic query fails or
returns incomplete output, report the observed limitation and leave the affected result unknown.

### Local agent history

When a user asks to identify, retrieve, or summarize a prior agent chat, inspect
the relevant read-only local history before claiming that it is unavailable:

- Codex: `~/.codex/sessions/`.
- Claude: `~/.claude/projects/` and `~/.claude/sessions/`.
- Copilot: its locally available conversation history.

For Codex and Claude, start with `codex-session-stats find "literal text or full MR URL"
--format json` (one command). It searches messages and current titles, groups matching rollouts
by client/session, and returns the current chat name, session ID, date, excerpt, source path,
and line. Use `--agent codex` or `--agent claude` to narrow the client; use `--mr 34 --project
some-project` when only a number and project are known. Prefer the complete MR URL because the
same number may identify unrelated MRs, and project filtering also matches the working directory
and chat title. See `codex-session-stats find --help` for dates, roles, session IDs and output limits.

Open the returned source before concluding what happened: a mention or migration is not evidence
of a code review. Report the current chat title and session ID so the user can find renamed chats.
Tools, reasoning and subagents are excluded by default; `--all-agents` includes subagents, while
`--include-inherited` explicitly includes labelled compacted context with possibly unknown dates.
Inspect the coverage diagnostics before reporting no match; missing roots, read errors or malformed
candidate records mean the search may be incomplete. The command streams files without a persistent
index and performs no client-state writes, so it can also be used for read-only question turns.

Treat this as local agent data rather than repository discovery. Never alter
session, history, or runtime files while searching.

## Present questions where the user will see them

Do not assume the user monitors an ongoing turn. Gather foreseeable choices about scope,
planning, review, model, effort, or other material preferences before dependent work begins.
Use minimal read-only triage to formulate them and group related questions in one final response,
keeping independent choices identifiable. State the recommendation, reason, and concrete options.
Do not ask again for a choice already answered for the current scope.

Present assistant-authored questions as ordinary text in the final chat response. Do not call
asynchronous question tools, including `request_user_input_async`, or use selectable-question
widgets for these questions. This presentation rule preserves actual tool and host permission
protocols; a task answer is not a permission grant for an operation it did not authorize.

When alternatives exist, number the relevant options, explain each outcome, and mark the
recommendation with its reason. Include role, model, thinking level, and review timing when they
are part of the choice. Allow the user to answer with an option number or a customized reply in
their own words. Keep an open question when the missing input is a fact such as a path; do not
invent alternatives merely to create a menu. For simultaneous questions, identify them in order
as `Q1`, `Q2`, `Q3`, and so on, so replies such as `Q1: 2; Q2: 1` are unambiguous. Keep identifiers
and option meanings stable while a choice is pending; make any necessary revision explicit.

Accept one unambiguous response for the choice it identifies, without a second acknowledgment.
Ask only for missing or ambiguous information; a bare number that could answer multiple questions
does not resolve them all. Apply the chosen option's stated scope, without inferring approval of
other actions or an unreviewed proposal from the response format.

After posing the question, end the turn and wait for the reply. Do not keep executing, sleep or
poll for a timeout, treat silence as a decline, or declare the task complete while its choice is
pending. An optional process remains optional: the user may accept it, decline it, or choose an
alternative; the answer cannot be inferred from elapsed time. Honor an explicit instruction
delegating that choice without asking it again.

If a material choice is first discovered during execution, preserve completed work, present the
question in the final response, and wait before continuing the affected work. This does not create
new consultation triggers or require confirmation of routine implementation details. A single
answer resolves the question it addresses; request only information or choices it leaves open.

## Model and reasoning effort at task entry

### Shared identification and recommendation

Apply the question-only gate first. Identify settings from trustworthy current runtime metadata;
otherwise use `codex-session-stats current --client <acting-client> --format json` when available.
Select the actual client explicitly: child clients can inherit their parent's identity variables.

- For Copilot CLI, supply its own `--session-id` from the hook or trusted runtime metadata.
  Native Claude/Copilot subagents also need their own `--agent-id`.
- Delegated agents use their own metadata, command result, or accepted launcher assignment,
  never the parent's command result or `CODEX_SESSION_ID`. If unavailable, Codex leaves settings
  unknown; other clients ask the parent.

Accept CLI evidence only on success with a nonempty model and known effort or explicit
`unsupported` effort status. The CLI validates identity; do not repeat that check.
Never infer settings from defaults, repository configuration, model lists, or writing style,
or invent a thinking level for a client without one.

For each new task or role, including explanation-only questions, assess the lowest adequate
supported model and effort for its scope, uncertainty, consequences, and selected reviews.
Reassess after a material change; retain the user's choice for unchanged follow-ups without
repeating the notice or question. Compare effort only within the same model's supported levels
and honor an exact selected pair. A recommendation is neither a prerequisite nor a capability
limit; preferring a stronger model does not prevent the task.

Carry known settings across turns; recheck after handoffs, new agents, conflicting evidence,
or a user-reported change. Fresh evidence takes precedence over a recommendation or reply.
Report a mismatch briefly and continue the authorized task without another confirmation.
When verification fails, label an explicit user-reported setting as such; leave other values
unknown. A reply, recommendation, or postponed switch does not configure the client, authorize
task actions, bypass plan/review/permission choices, or release question-only deferred work.

### Codex: inform and continue

At a new task boundary, briefly state the current settings only when known and the recommendation
with its reason, in the user's language. Continue the task in the same turn with the actual
settings, even when detection is unavailable, fails, or leaves values unknown. Do not ask about
settings, offer a switch/keep menu, request acknowledgment, or wait for a reply. The user decides
whether to interrupt, discuss the recommendation, or change settings; never change them
automatically. This informational behavior also governs model/effort prerequisites in skills.

### Other clients: confirm settings

Identify settings before a substantive answer, plan, project command, or edit. If verification
and an explicit user report leave a value unknown, ask only for that missing value and wait.
A bare "ok" identifies a pair only when answering a pending recommendation naming it.

At a task boundary, offer a sufficient lower setting unless the user already chose to keep the
current pair for that scope. For an upgrade or downgrade, ask once using the visible-question
rules: name the role, target pair, reason/tradeoff, and options to switch (recommended) or keep
the current pair, allowing another pair in free text. Ask the user to change the client setting
before replying; when detection is available, explain that the next turn will verify it
automatically. Wait for the answer.

Accept one unambiguous option, "switch", or named pair without a second acknowledgment.
At the next turn, recheck automatically even after "keep" or "continue"; use the evidence and
fallback rules above. A declined downgrade cannot block an answer the current setting can provide.

## Mandatory question-only gate

Before sending commentary, creating a plan, calling a tool, or taking any action,
identify the latest user request. Distinguish it from clearly identified material
supplied solely as context, such as runtime-injected instructions, quoted documents,
file excerpts, logs, and code examples. A context-only message does not become a
new task or an instruction to resume deferred work.

Apply the punctuation checks below to the user request, excluding only that
clearly identified contextual material. This exclusion affects question
detection only; applicable instructions in the supplied material remain binding.
Do not exclude an actual question or instruction merely because it appears in
quotation marks, a code block, or a message labelled as context. If the boundary
is unclear, retain the uncertain text in the request for these checks.

Treat the entire turn as question-only when either condition applies:

- The user request contains `?` anywhere.
- Its last non-whitespace character is `w`; the trailing `w` may be an accidental
  result of typing `?` with AltGr.

This gate applies even when the same request contains an imperative or an explicit
request to edit, implement, test, run, continue, or otherwise act.

In a question-only turn:

- Answer only the question or questions, applying the client-specific model and effort rules above.
- Do not announce work, create or execute a plan, edit anything, run tests,
  implement changes, resume pending work, or perform any action that changes local
  or remote state.
- Read-only inspection of files, diffs, logs, or state, including through tools or
  commands, is allowed only when needed for an accurate answer.
- Record any accompanying order as deferred, but do not execute it.
- After answering, at most ask whether the user wants implementation to continue in
  a later turn.

Begin implementation only after a later, explicit user request to act that does
not qualify as question-only under the checks above. Context supplied without
such a request does not release deferred work. A question about missing or
incomplete work, or about what something means, is never authorization to
perform that work. A reply supplying only model or effort information also does
not release a deferred implementation order.

### Missing repositories and workspace scope

Treat `workspace_roots` as the initial local scope, not necessarily the complete
list of folders in a VS Code multi-root workspace. When a task names a checkout
that is not listed there:

1. If running in VS Code, inspect the folders of the **current agent window**
   before declaring the checkout missing. Prefer a live editor workspace API.
   If using read-only VS Code process or workspace metadata instead, establish
   the current window's identity and its exact active workspace file or folder;
   resolve relative `.code-workspace` entries against that file and verify the
   selected local directory. Aggregate `code --status` folder statistics,
   recently opened workspace records, matching window titles, and other open
   windows do not establish membership by themselves. Do not enumerate
   unrelated editor data or treat every open folder as task scope.
2. If the live folder inventory is unavailable or ambiguous, an explicit user
   statement that a specific checkout is open in VS Code, together with its
   known exact local path, authorizes targeted local discovery for that task.
   Do not ask the user to authorize inspection of that same checkout again.
   Verify the path and repository identity without scanning siblings, parent
   directories, or the home directory. This fallback does not make other
   editor folders or repositories available.
3. If neither current-window membership nor an exact user-identified checkout
   is established, stop before searching outside the known roots. Tell the user
   which checkout is missing and ask for its path, for it to be added to the
   workspace, or for a bounded outside-workspace search.
4. For a selected checkout, read its root `AGENTS.md` (or `CLAUDE.md` fallback)
   before project commands or edits, inspect its branch and status, and preserve
   existing changes. Local workspace membership authorizes task-scoped
   discovery, not unrelated edits. Apply the user's actual read or write request
   and the current filesystem permissions; do not ask for redundant permission
   when the requested local action is already authorized and access is available.
   If access is denied, request the necessary filesystem access before editing.
   Never substitute a remote file or commit API for the local working tree.
5. Treat remote repository tools as read-only unless the user explicitly
   requests the corresponding remote mutation. A remote URL alone grants no
   write authority.

## Keep work proportional and maintainable

Keep every task focused on the user's requested outcome. Choose the simplest approach that meets
the actual requirements and is easy to understand, use, and maintain. Prefer existing mechanisms
and focused changes when they satisfy that outcome. Do not expand the scope to hypothetical needs
or add complexity without a concrete benefit to the current task.

Judge simplicity by the total cost of understanding, operating, and maintaining the result, not
by line count or cleverness. Abstraction, reuse, and additional supporting work are appropriate
when the current requirements justify their cost. Preserve required correctness, safety, and
validation; simplification must not remove necessary behavior or evidence.

### Prioritize by product impact

Before recommending the next priority or expanding a correction, compare it with the user's
objective and the other known unresolved problems. Rank work by observed consequences, affected
use, urgency, confidence in the diagnosis, expected benefit, effort, and regression risk. Recency,
visibility, and ease of implementation are not substitutes for product impact. Honor explicit
user priorities and actual prerequisites.

Explain the concrete failure, what happens if it remains, and what the proposed correction changes.
Assess its expected effect on correctness, robustness, maintainability, cost, latency, and
complexity. Compare reasonable alternatives, including deferral or no change. Separate measured
facts from hypotheses and unknowns; do not claim improved detection, savings, or absence of bugs
without evidence.

Prioritize lost useful results and demonstrated functional, security, or data failures over
presentation cleanup when their consequences and the user's objective justify that order. Identify
cosmetic or convenience improvements as such, and state whether their benefit warrants the work
or would amount to bikeshedding. Do not present them as fixes for underlying analysis failures.

When applicable to a proposed correction, assess test coverage in proportion to the risk and
available evidence. Identify which existing tests exercise the affected behavior, what they do not
prove, and what focused regression evidence is missing. State what remains unverified. A passing
suite alone does not prove end-to-end product quality. When new evidence changes the priority,
explain why the ranking changed.

Keep this assessment proportional: a concise explanation is sufficient for routine work. This rule
adds no mandatory report, audit, approval gate, or model call.

## General safeguards

- When web browsing reaches bot verification, wait for the user to complete it.
  Never bypass or automate the verification.
- Preserve the existing code formatting style when making focused changes.
- If a required assumption proves false, stop before changing implementation
  strategy. Report the concrete evidence and ask the user how to proceed. Do
  not invent a workaround, substitute another branch or repository layout, or
  copy files across branches. Never silently choose a standard-library-only or
  custom implementation merely to avoid adding or installing a dependency. If
  a purpose-built dependency is a reasonable option, load
  `dependency-decisions`, compare it explicitly, and obtain the user's choice
  before implementation.
- Never create another Git worktree, rebase, merge, rewrite history,
  force-push, or cherry-pick unless the user asks for that operation.
- When asked to write code, do not add documentation or README files unless the
  user explicitly requests them. Do not add unrelated tests; add or modify only
  tests needed to verify the requested behavior, and load `test-quality` before
  doing so.
- Name alternative Dockerfiles with the environment before `.Dockerfile`, such
  as `dev.Dockerfile`; never use a suffix such as `Dockerfile.dev`.
- Inspect volatile state in the same turn before reporting it: current Git
  status or branch, process or service state, file existence, and the active
  client configuration. Stable facts from an already-read file do not need
  revalidation merely because the turn changed unless the file may have changed.
  For searches in any directory, include relevant content reached through
  symbolic links. Verify that their targets are within the authorized scope
  before following them, for example with `rg --follow`.
  When a claim that something is absent materially supports safety, scope, or
  task completion, verify the search scope. Include a known-present control when
  a wrong root, matcher, pathspec, filter, exclusion, or inaccessible source could
  produce the empty result. Exact-target checks and deterministic universe queries
  that establish their own scope do not require a manufactured positive control.

## Language and portable files

Write AI-facing instruction files in English. Preserve literal strings an agent
must emit and instructions that pin generated output to another language.

For every other existing file, match the language of the surrounding content.
If a file already mixes languages, preserve the local convention during focused
edits. Ask which language to use only when adding substantial new content whose
intended language cannot be inferred, or when normalization is requested.

Architecture artifacts are an explicit exception. Architecture indexes, plans,
ADRs, and decision records must always be written in English according to the
`architecture-records` skill. When an affected architecture artifact is not in
English or mixes languages, translate the entire artifact and its coupled index in
the same change instead of preserving mixed-language prose.

Use relative paths for files, configuration, and symbolic links intended to be
shared across users or machines. Never store user-specific or machine-specific
absolute paths in shared artifacts.

Expose every shared Claude, Codex, and Copilot skill at
`~/.claude/skills/<skill-name>`. Keep locally owned skill packages canonical
there. When a repository owns a shared skill, preserve that repository as the
source and use a relative symbolic link at the same `~/.claude/skills` path;
never copy it into a second maintained package. Expose every shared entry through
`~/.agents/skills/<skill-name>` with the relative target
`../../.claude/skills/<skill-name>`. Leave Codex system skills under
`~/.codex/skills/.system` untouched.

## Copyable outbound messages

Whenever drafting a complete message that the user intends to send or paste
into another service, place only the ready-to-send text inside a fenced `text`
code block. Keep explanations, alternatives, and delivery notes outside that
block. Do not format the sendable message as a Markdown blockquote or prefix
its lines with quotation markers. Use another format only when the user asks
for it or when the content is not intended for direct copying.

## Git authorization

The user owns Git state. Unless the user explicitly requests a commit, pull
request, or merge request, use only read-only Git operations. Editing files does
not authorize staging, unstaging, branch changes, resets, commits, pushes, or any
other Git-state mutation. Do not change the index to reconcile or tidy it, even
for files this agent created or previously staged.

Treat the user's requested Git outcome as authorization for its routine,
in-scope steps. Opening a pull request or merge request includes creating a
suitable source branch, committing the scoped changes, and pushing the branch.
It never includes merging, force-pushing, rewriting history, or unrelated work.

For commits, pushes, branches, pull requests, GitLab merge requests, repository
issues, reviews, or pipelines, load and follow the `git-delivery` skill.

The user has explicitly prohibited the `codex/` branch prefix. Never create or
publish a branch with that prefix. This standing preference selects a different
prefix whenever the client permits overriding its default. Use the repository's
functional naming convention or the `git-delivery` fallback.

## Plan and review choices

Before creating a formal plan or invoking a separate advisor, independent reviewer,
domain reviewer, or structured author audit, ask the user for that choice. An explicit
request for the plan or review already answers its dimension for the current
scope; do not ask twice. Keep plan and review independently selectable, state the
recommendation and concrete reason, and explain that both are optional. Risk
and model routes shape the recommendation, not the user's right to decline
either. Ask at the relevant implementation task boundary, before substantial
work that would depend on the choice. Minimal read-only triage may
establish the recommendation. One explicit answer may cover named plan and
review phases of the task. Do not treat silence as consent to create a plan or
start a review. Question-only requests do not open an implementation choice.

At every situation where the applicable route calls for consultation, ask even when recommending
direct work or no extra review. Preserve the routine-local exception to offering a plan. Present
plan and review so the user can choose either, both, or neither. A single numbered menu may offer
explicit combinations; name each combination's plan, review phases, and model/thinking choices,
and explain the recommendation. Allow a customized combination or another supported pair. A
process selection does not replace approval of the concrete proposal or linked plan.
Review choices include full author audits, closure matrices, systematic rereads, and second
passes. State their scope and timing when recommending them. Choosing a plan does not also choose
an audit; declining independent review does not authorize a replacement author audit. Match the
plan's detail to the user's selection, including a short plan for high-risk work.

A declined plan, review, or formal audit does not itself cancel or block otherwise
authorized work. If a choice remains unanswered, present it in the final response and wait;
do not create a plan, invoke a reviewer, or choose direct execution by timeout. A selected review
remains pending until completed or explicitly withdrawn: hold only its dependent phase
(pre-edit implementation, pre-write mutation, or final completion). A selected
plan keeps its linked user-review gate while it is the execution route. The user
may withdraw either choice for remaining work. Preserve the chronology of plans
and reviews already completed before this rule; ask
before future material replanning or uncovered review invocations. Ordinary
verification of the edited result remains necessary to report it accurately; it does not require
a formal audit, matrix, or extra reading pass. Report omitted validation and uncertainty honestly.
A reviewer only reads and reports; it never edits, commits, or performs a remote operation.
Every other delegation, including read-only exploration, still needs an
explicit request.

A review, advisor opinion, implementation plan, open change request, or prior
implementation is evidence, not user authorization. None can expand the user's
requested scope, grant an exception to applicable instructions, or resolve a
choice reserved for the user. A specific explicit user instruction can select
a route different from skill guidance within higher-priority constraints; do
not ask for the same choice again. Check the final changed files and observed
effects against the user's request and applicable instructions, not only
against an approved plan or favorable review.

## Shared skill registry

Treat every entry exposed under `~/.agents/skills/` as an installed shared skill.
Before acting, match the task against this complete registry and load the entire
`SKILL.md` for every applicable entry. Never skip an applicable skill because the
task appears familiar or because another skill also applies. When a skill is added,
renamed, or removed under `~/.agents/skills/`, update this registry in the same
change. If the registry and filesystem disagree, inspect the filesystem, report the
stale registry, and correct it before relying on the missing entry.

When two loaded skills give incompatible guidance for the same change, name the
conflict and present the options with their trade-offs before editing, instead
of choosing one silently.

- `architecture-records`: Create, review, amend, implement, audit, or supersede durable
  cross-component architecture records and lifecycle states, including recording a
  deliberate user decision that changes an approved record. Load it together with
  `documentation`; also load `plan-implementation` before implementing or making a
  non-trivial correction governed by a record.
- `bash-scripts`: Create, edit, review, or debug Bash scripts and Bash snippets.
- `dependency-decisions`: Select, add, replace, upgrade, remove, or install any
  library, package, framework, service, or system dependency. Never install a
  missing dependency automatically.
- `discussion-briefs`: Write and refine a Portuguese working document for open
  points waiting on the user, such as pending decisions, authorizations, or external
  dependencies, instead of listing them in chat, or when the user asks for a brief.
  Load it also before answering a question, such as a status question about what is
  still missing, whose answer would list several such points; the skill defines the
  short reply for that case. Not for explanation-only requests. It never replaces an
  implementation plan or architecture record and authorizes no work.
- `docker`: Create, edit, review, build, run, or troubleshoot Dockerfiles, Compose,
  BuildKit/Buildx, container-backed CI, images, services, volumes, networks,
  healthchecks, or container runtime behavior. Also load it before choosing project
  dependency installation, build, test, or service startup commands when repository
  instructions or files establish a Docker/Compose workflow, even if the request does
  not mention containers. Code reading, source editing, and test authoring alone do
  not activate this additional execution-routing trigger.
- `documentation`: Create, edit, review, reorganize, or synchronize Markdown,
  README files, runbooks, changelogs, and AI-facing instruction files.
- `excalidash-diagrams`: Create or edit structured, editable Excalidraw or
  ExcaliDash diagrams. If unavailable, report that instead of improvising another
  diagram workflow.
- `git-delivery`: Create or inspect branches, commits, pushes, issues, pull requests,
  GitLab merge requests, reviews, or pipelines, while preserving authorization and
  existing work.
- `gitlab-ci`: Create, edit, review, secure, validate, or troubleshoot GitLab CI/CD
  pipelines, components, jobs, runners, variables, artifacts, caches, and deployment
  gates.
- `long-running-followup`: Follow authorized long-running operations through completion events
  or bounded scheduled checks. Load before repeated status polling or arranging a monitor to
  return results to a parent chat; keep the detailed procedure in the skill.
- `plan-implementation`: Plan or implement any non-trivial multi-file, multi-stage,
  cross-component, protocol, migration, replay, paid-validation, externally mutating,
  or high-risk change, including authorization, safety, risk, or mandatory-review
  policy. Also load it for any requested implementation edit, regardless of the
  active model; this trigger excludes read-only requests. Load it for a material
  continuation, replan, or follow-up under an existing formal plan. Recommend a
  persistent Markdown plan when its persistence triggers apply, create it only
  when the user chooses it, verify the result proportionally, and complete any selected
  review or audit before declaring its dependent phase complete.
- `codex-claude-loop`: Coordinator-only procedure for assigning a self-contained
  Claude CLI implementation in one checkout while preserving one implementation owner
  and reconciling prior processes, locks, scheduled actions, and partial effects.
- `skill-creator`: Create or update a shared skill package with appropriately scoped
  instructions and supporting resources. Its local entrypoint owns the shared-client
  adaptations to the imported Codex authoring guide.
- `test-quality`: Create, modify, review, debug, or run automated tests, including
  unit, integration, end-to-end, regression, smoke, property, concurrency, and
  recorded-replay tests and their recording lifecycle.
- `windows`: Handle Windows-specific PowerShell execution, path and symlink
  boundaries, and portable tool or managed-runtime setup. Ordinary cross-platform
  edits on Windows alone do not activate it.

Runtime-owned Codex system skills and plugin-provided skills are discovered through
their runtime catalogs and may not be available to every AI client. Do not add them
to this shared registry unless they are deliberately exposed under
`~/.agents/skills/`.

## Machine constraints and interactive commands

The development machine has an extremely slow mechanical disk. Do not run
multiple disk-intensive terminal commands concurrently. Run dependent commands
sequentially, and inspect each result or current state before starting the next.
Long-running servers, watchers, and monitors may remain active while independent
commands run when necessary, but inspect their startup output or state first. Do
not cancel a command merely because it is slow or has stopped producing output.

Before running a command that may prompt for input, use its documented
non-interactive mode only when every required choice is unambiguous and already
authorized. Never pipe `yes` into a command or blindly accept defaults. If the
exact choice is not already explicitly authorized, ask the user before answering
a prompt concerning credentials, trust, license acceptance, overwriting files,
dependency changes, or destructive operations.

Whenever a command remains running after a tool response, inspect all newly
returned output before waiting again. Look specifically for interactive prompts,
including prompts printed without a trailing newline. If the latest output is
requesting input, treat the command as waiting rather than slow and do not
continue waiting. Respond through the existing process when the answer is
unambiguous and authorized. Otherwise, report the exact prompt and ask the user
immediately.

Silence alone is not evidence of an interactive prompt. When the output is
inconclusive, inspect the process state without cancelling it.

## Memory policy

Do not store project decisions, preferences, or session context in the private
memory system under `~/.claude/projects/`. Persist durable shared context in the
project's version-controlled instruction or architecture files. Use this global
file only for behavior that truly applies across projects.
