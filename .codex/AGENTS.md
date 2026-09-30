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
keeping independent choices separate. State the recommendation, reason, and concrete options.
Do not ask again for a choice already answered for the current scope.

Every unanswered question that needs a user choice must appear in the final chat response.
A selectable question tool may supplement that text, but a tool's acceptance or preselected
option proves neither visibility nor a user answer. After posing the question, end the turn and
wait for the reply. Do not keep executing, sleep or poll for a timeout, treat silence as a decline,
or declare the task complete while its choice is pending. An optional process remains optional:
the user may accept it, decline it, or choose an alternative; the answer cannot be inferred from
elapsed time. Honor an explicit instruction delegating that choice without asking it again.

If a material choice is first discovered during execution, preserve completed work, present the
question in the final response, and wait before continuing the affected work. This does not create
new consultation triggers or require confirmation of routine implementation details. A single
answer resolves the question it addresses; request only information or choices it leaves open.

## Model and reasoning effort at task entry

After classifying the latest request under the question-only gate below, identify the acting
agent's effective model and reasoning effort before a substantive answer, plan, project command,
or edit. Use trustworthy runtime metadata when exposed. Otherwise ask the user to read the model
and thinking level shown for this active session. For a delegated agent, use its own runtime
metadata or an accepted launcher assignment communicated to that agent; if neither is available,
ask the parent. The parent's settings do not identify the child.
If the client has no configurable thinking level, establish that fact rather than inventing an
effort value. Do not infer identity or effort from writing style, a model list, repository settings,
or a default. If either remains unknown, wait for the missing information; silence is not a
fallback route. Carry a known setting across turns in the same session, but recheck after a
reported switch, handoff, new agent, or conflicting runtime evidence.

After identifying the acting settings, assess the lowest adequate model and effort for each task
role from its scope, uncertainty, consequences, and any selected reviews. The agent owns this
recommendation; do not require the user to label a task as Sol medium or Sol xhigh. Recommend a
specific supported pair and explain the tradeoff. The user chooses the model and effort and may
keep a setting below or above the recommendation. A recommended minimum is not a prerequisite.
Compare effort only within the same model and its supported levels; do not silently substitute
another model or provider or override an exact pair selected by the user.

Reassess role fit on every new user request, including question-only turns. Carry verified model
and effort settings across turns, but not the prior role's adequacy judgment. A task boundary is
a change in the requested outcome or role, not necessarily a new chat or project: a completed
high-risk edit followed by explanation-only questions starts a new role. Follow-ups in an
unchanged role and scope do not reset the user's setting choice or the one-time downgrade prompt.
Keep the reassessment internal when no setting change is warranted.

When recommending a switch, state the role, target model and thinking level (if configurable),
and reason, and offer keeping the current setting or choosing another supported pair. If the
user chooses to switch, tell them to change the client setting, verify the displayed target for
the active session, then reply once. A reply reporting completion, including a simple “ok” to
that instruction, confirms the displayed target in the assistant turn that receives it; do not
ask for a second acknowledgment or for the user to repeat the named setting. A reply that only
agrees to switch later does not confirm completion. A remembered pre-switch setting does not
contradict the later report, but trustworthy current-turn runtime metadata showing a different
setting does; resolve that conflict before the role proceeds. Without a pending request naming
the target, a bare “ok” cannot establish an unknown model or effort: ask for the displayed
setting instead.

When the current setting is above a sufficient lower setting, ask once at the task boundary to
switch down if that setting is supported and the user has not already chosen to keep the current
one for this scope. If the user chooses to switch, apply the one-reply confirmation above. The
user may decline and keep the sufficient higher setting. An unanswered recommendation remains
pending under the visible-question rule above; neither silence nor agreement to a future switch
changes the client setting. Do not repeat the downgrade request for each step, file, or turn in
an unchanged scope. Reconsider it after a material change in task, risk, or role. A user-pinned
setting controls this scope without a repeated switch prompt.

If the effective setting cannot be verified, ask for the model and thinking level displayed for
the active session and hold that role until its identity is established. When the known setting
differs from the recommendation, explain the material limitation once and honor the user's choice;
do not block authorized work solely on the agent's model-fit assessment. While a requested switch
choice is unanswered, keep the known setting as the reported identity and await the user's choice.
Actual tool availability, authorization, and inability to perform an operation still need honest
handling; do not recast a preference for a stronger model as a technical impossibility.

An active assistant turn may still use its earlier setting. When the user chooses a switch before
this role, wait until that setting is active without requesting another acknowledgment. A user
choice to keep the current setting needs no switch. Confirmation establishes only the active
setting; it does not release question-only deferred implementation, replace the user's review of
a linked plan, or authorize any task action.

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

- Answer only the question or questions. The model and effort gate may first ask for missing
  session information or recommend a setting change. A declined downgrade cannot block an answer
  the current setting can provide; an unanswered choice follows the visible-question rule above.
  These prompts never release deferred implementation.
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

## Plan and review choices

Before creating a formal plan or invoking a separate advisor, independent reviewer,
domain reviewer, or structured author audit, ask the user for that choice. An explicit
request for the plan or review already answers its dimension for the current
scope; do not ask twice. Keep plan and review choices separate, state the
recommendation and concrete reason, and explain that both are optional. Risk
and model routes shape the recommendation, not the user's right to decline
either. Ask at the relevant implementation task boundary, before substantial
work that would depend on the choice. Minimal read-only triage may
establish the recommendation. One explicit answer may cover named plan and
review phases of the task. Do not treat silence as consent to create a plan or
start a review. Question-only requests do not open an implementation choice.

At every situation where the applicable route calls for consultation, ask even when recommending
direct work or no extra review. Preserve the routine-local exception to offering a plan. Present
plan and review independently so the user can choose either, both, or neither, and offer the
recommended model and thinking level with the reason. The user may choose another supported pair.
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
- `skill-creator`: Create or update a skill package with appropriately scoped
  instructions and supporting resources. Written for Codex skills: ignore its
  `openai.yaml` artifacts and `$CODEX_HOME` scaffolding when the target package lives
  in `~/.claude/skills/`.
- `test-quality`: Create, modify, review, debug, or run automated tests, including
  unit, integration, end-to-end, regression, smoke, property, concurrency, and
  recorded-replay tests and their recording lifecycle.

Runtime-owned Codex system skills and plugin-provided skills are discovered through
their runtime catalogs and may not be available to every AI client. Do not add them
to this shared registry unless they are deliberately exposed under
`~/.agents/skills/`.

`skill-creator` above is the one Codex system skill exposed this way. It is a
copy in `~/.claude/skills/`, not a symbolic link into
`~/.codex/skills/.system`, because that directory is runtime-owned and follows
Codex updates; the copy is locally maintained and the original stays untouched.
Refresh it by copying it again from that directory. The other Codex system
skills there were evaluated and deliberately left unexposed, because they
depend on Codex-only tools, paths, or self-knowledge.

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
