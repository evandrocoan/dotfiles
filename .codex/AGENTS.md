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

- Answer only the question or questions.
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
perform that work.

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

## Review authorization

Reviews that a loaded shared skill requires, such as the plan review in
`plan-implementation` and the closure pass that it and `architecture-records`
require, are pre-authorized: open them without asking and report what they
found, including the findings you disagree with. The skill owns when a review
happens and how it runs on each client. A pre-authorized reviewer only reads
and reports; it never edits, commits, or performs a remote operation. Every
other delegation, including read-only exploration, still needs an explicit
request.

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
  policy. Also load it for a material continuation, replan, or follow-up under an
  existing formal plan. Use its persistent Markdown plan whenever its persistence
  gate applies, and complete its risk-appropriate closure before declaring success.
- `codex-claude-loop`: Coordinate Codex planning and review with Claude Code
  implementation in one checkout, through supervised local CLI turns or a
  shared handoff between two sessions with optional periodic checks.
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
