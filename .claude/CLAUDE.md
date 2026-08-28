# Global Claude instructions

Never redirect standard error to `/dev/null` (`2>/dev/null`). Hidden errors make
failures impossible to diagnose.

## Startup and workspace scope

Before running a command or editing a file, read the `CLAUDE.md` of the primary
working directory and every additional working directory listed in the session.
Project instructions may override global workflow assumptions.

### Missing repositories and workspace scope

Treat `workspace_roots` as the complete authorized repository discovery scope
unless the user explicitly says otherwise. When a task refers to a repository
that is not listed there:

1. Stop before searching sibling directories, parent directories, the home
   directory, editor metadata, or any other location outside the workspace.
2. Tell the user exactly which repository or checkout is missing.
3. Ask the user either to add the checkout to the workspace or to explicitly
   authorize a search outside it.
4. Search outside only after receiving that authorization, and limit the search
   to the smallest plausible location.
5. If an authorized checkout is outside the writable roots, request filesystem
   access before editing it. Never bypass missing local access through a remote
   file or commit API.
6. Prefer the authorized local working tree for file work. Read its
   `CLAUDE.md`, inspect its current branch and status, and preserve all existing
   changes.
7. Treat remote repository tools as read-only unless the user explicitly
   requests the corresponding remote mutation.

## General safeguards

- When web browsing reaches bot verification, wait for the user to complete it.
  Never bypass or automate the verification.
- Preserve the existing code formatting style when making focused changes.
- If a required assumption proves false, stop before changing strategy. Report
  the concrete evidence and ask the user how to proceed. Do not invent a
  workaround, substitute another branch or repository layout, or copy files
  across branches.
- Never create another Git worktree, switch branches, rebase, merge, or
  cherry-pick without explicit authorization for that specific action.
- When asked to write code, do not add documentation, README files, or tests
  unless the user explicitly requests them.
- Name alternative Dockerfiles with the environment before `.Dockerfile`, such
  as `dev.Dockerfile`; never use a suffix such as `Dockerfile.dev`.

## Language and portable files

Write AI-facing instruction files in English. Preserve literal strings an agent
must emit and instructions that pin generated output to another language.

For every other existing file, match its language. If a file already mixes
languages, ask whether to continue in the dominant language, choose a language
for new content only, or normalize the entire file.

Use relative paths for files, configuration, and symbolic links intended to be
shared across users or machines. Never store user-specific or machine-specific
absolute paths in shared artifacts.

Keep shared Claude, Codex, and Copilot skills canonical at
`~/.claude/skills/<skill-name>` and expose them through
`~/.agents/skills/<skill-name>` with the relative target
`../../.claude/skills/<skill-name>`. Leave Codex system skills under
`~/.codex/skills/.system` untouched.

## Git authorization

Never create a commit, push, branch, pull request, or merge request unless the
user explicitly requests that action. Interpret each authorization separately:
a commit does not authorize a push, and a push does not authorize a merge
request.

For commits, pushes, branches, pull requests, GitLab merge requests, repository
issues, reviews, or pipelines, load and follow the `git-delivery` skill.

## Task-specific skills

- Before selecting, adding, replacing, upgrading, removing, or installing a
  dependency, load `dependency-decisions`. Never install a missing package
  automatically.
- Before creating, modifying, reviewing, debugging, or running automated tests,
  load `test-quality`.
- Before writing or editing documentation or AI-facing Markdown instructions,
  load `documentation`.
- For durable cross-component architecture plans or decision records, load
  `architecture-records` together with `documentation`.
- Before creating, editing, reviewing, or debugging Bash, load `bash-scripts`.
- Before creating or editing a structured diagram, load
  `excalidash-diagrams`. If that skill is unavailable, report that it is not
  installed instead of improvising another workflow.

## Machine constraints

The development machine has an extremely slow mechanical disk. Never cancel a
command early. Wait for it to complete before running the next command, and do
not start terminal commands back-to-back without observing each result.

## Memory policy

Do not store project decisions, preferences, or session context in the private
memory system under `~/.claude/projects/`. Persist durable shared context in the
project's version-controlled instruction or architecture files. Use this global
file only for behavior that truly applies across projects.
