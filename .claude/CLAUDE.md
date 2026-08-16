# Global Claude Instructions

Never redirect stderr to /dev/null (2>/dev/null) in any command, because it hides errors and makes failures impossible to diagnose.

## Reading CLAUDE.md before acting

Before running any command or making any file edit, read the CLAUDE.md of
every working directory in the session — both the primary directory and all
additional working directories listed in the session context. Each project
may have its own environment constraints, tool execution rules, and
architectural decisions that override default behavior. Skipping any of them
causes incorrect actions that cannot be undone safely.

## General

When browsing the web, if bot verification begins, wait for the user to complete
the verification and then continue the task. Do not try to bypass or automate
bot verifications, as that can lead to errors or account lockouts.

Do not change my code formatting style when fixing it.

AI-facing instruction files must always be written in English, regardless of
the surrounding codebase language. This covers any file whose primary purpose
is to instruct an AI agent — not just CLAUDE.md, but also skill and slash
command definitions (`.claude/commands/*.md`, `.claude/skills/**`), `AGENTS.md`,
`.github/copilot-instructions.md`, and equivalents. English gives the model a
small but real edge in instruction-following, and keeps these files consistent
with each other.

Two things inside an English instruction file stay in their original language:
- Literal strings the agent must emit verbatim — commit messages, menu/button
  labels, output templates, example values.
- Instructions that pin the language of generated output (e.g. "write the note
  in Portuguese", "generate the Mattermost message in Portuguese"). The
  instruction prose is English; the output language it specifies is unchanged.

When editing or adding content to any other existing file (code, docs, issue
files, anything that is not an AI-facing instruction file), match the language
already used in that file. If the file is in English, write in English. If the
file is in Portuguese, write in Portuguese.

If a non-instruction file already mixes languages, ask the user before
proceeding:
- Continue adding content in the dominant language?
- Pick one language and apply it to the new content only?
- Correct the entire file to a single language?

When a package or import is missing, do not install it automatically. Ask the
user whether to install the missing package or look for an alternative that is
already available.

## Dependency choices

Before choosing dependencies for new code, ask the user which libraries or
dependency strategy they prefer. Present the reasonable options, including
appropriate third-party libraries and a standard-library-only approach when it
is genuinely viable. Explain the relevant tradeoffs — such as ergonomics,
maintenance, performance, portability, and installation cost — and recommend
the option that best fits the task before asking the user to choose.

Do not default to the standard library, avoiding dependencies, or any specific
library without this discussion. Do not announce a dependency decision before
the user has chosen. A separate question is unnecessary only when the user has
already selected the dependency strategy or the repository contains an
explicit, applicable requirement that leaves no meaningful choice; state that
constraint before proceeding.

When asked to write code, do not create documentation, readmes, or tests
unless explicitly asked to.

The development machine has an extremely slow mechanical disk. All terminal
commands take much longer than normal. Never cancel a command early — always
wait for it to fully complete before running the next one. Never run multiple
commands back-to-back without waiting for each one to finish first.

## Markdown

When writing markdown, do not use CamelCase for section titles. Use normal
sentence case instead.

When writing markdown tables, always use spaces around the dashes in the
separator row: `| --- | --- | --- |` instead of `|---|---|---|`.

## Commits

Never create a git commit unless the user explicitly asks for it.

When the user requests a commit:

1. Read each changed file to understand what was modified and why
2. Analyze the architectural impact of the changes
3. Write a professional commit message as a plain text code block

Commit message rules:
- Always written in **English**
- No conventional commit prefixes (no `feat:`, `fix:`, `chore:`, etc.)
- Title line must be concise and descriptive, max 72 characters
- Body lines must wrap at 80 columns
- Explain *why* the change matters, not just what changed
- Separate title from body with a blank line
- Never add `Co-Authored-By` trailers

## Pull Requests

Never create a pull request unless the user explicitly asks for it.

When the user requests a pull request:

1. Read each changed file to understand what was modified and why
2. Analyze the architectural impact of the changes
3. Write a professional pull request description as a plain text code block

Pull request rules:
- Always written in **Portuguese (Brazil)**
- No emojis anywhere in the title or body
- Title must be concise and descriptive
- Body must explain *why* the change matters, not just what changed
- Describe the architectural context and motivation behind the changes

### GitLab merge requests through Git push options

When GitLab CLI or an MCP server is unavailable, create a merge request by
pushing the branch with GitLab push options. Set the target branch, title, and
description explicitly along with `merge_request.create`.

Push option values cannot contain literal newlines. For a multiline merge
request description, use the literal `\\n` escape sequence; GitLab converts it
to line breaks. Never URL-encode line breaks as `%0A`, because GitLab stores
that text verbatim.

`merge_request.title` and `merge_request.description` can also update an
existing merge request when supplied with a later push. Prefer an ordinary
branch update or the GitLab API/MCP for such edits; do not rewrite history
solely to alter metadata unless explicitly necessary and safe.

## CLAUDE.md and .github/copilot-instructions.md sync

When working in a project, keep CLAUDE.md and .github/copilot-instructions.md
in sync using the following logic:

- If `.github/copilot-instructions.md` **already exists**: add
  `@.github/copilot-instructions.md` at the top of `CLAUDE.md` so Claude
  also reads those instructions.
- If `.github/copilot-instructions.md` **does not exist**: create a symlink
  pointing it to `CLAUDE.md` so Copilot reads the same instructions:
  `ln -s CLAUDE.md .github/copilot-instructions.md`

## Documentation

Never write documentation that embeds data which becomes stale as the
code evolves. Specifically:

- No hardcoded counts ("28 tools", "3 graphs", "11 entity types") —
  omit the number or link to the authoritative source (code, CLAUDE.md
  changelog anchor) instead.
- No specific version numbers in prose unless they describe a historical
  event ("removed in v2.1") rather than current state.
- No snapshots of lists that are maintained in code (tool names, module
  names, CLI subcommands, env var names) unless the list is reproduced
  directly from the source and the file makes clear it must be kept in sync.

When describing quantities, use qualitative language ("typed, tenant-scoped
tools", "several cross-call rollup passes") so the description stays true
even as the codebase grows.

## Writing README.md and CLAUDE.md

### Role split

**README.md** is user-facing: setup, operational usage, runbooks. It
answers "how do I run this?"

**CLAUDE.md** is AI-facing: architectural context, cross-file
invariants, non-obvious constraints, decisions and their rationale. It
answers "why is the code structured this way, and what breaks if I
change it?"

### Markdown tables of contents

Whenever editing a Markdown document that already has a table of contents,
keep it synchronized with the document's headings.

If a long-form Markdown document does not have a table of contents, create one
when it would materially improve navigation. Include substantive sections and
relevant subsections. Do not add a table of contents to short documents,
templates, changelogs, generated files, or other documents where it adds
little navigational value.

### Staleness traps — never write these in either file

**Lists maintained in code.** Every item you name will silently diverge
as the code evolves. Never duplicate:

- Module inventories ("the package contains loader.py, classifier.py…")
- Entity/node-type or relationship tables copied from prompts or schemas
- Config-constant tables copied from config.py
- Env-var tables copied from .env.example
- Specific model names, proxy aliases, or default values from config
  files or code constants
- Schema field names maintained in Pydantic models or YAML manifests
- Tenant-specific data (IVR patterns, department tags, sub-bin names)

**Hardcoded counts** — already covered in the Documentation section
above. This rule applies to counts embedded inside narrative prose too,
not only standalone numbers ("Five rollup passes", "three signal
extractors").

**Deployment-specific values** that differ per environment or tenant
should never appear in shared docs, even as examples.

### The pointer pattern

Instead of duplicating, point to the authoritative source:

| Instead of… | Write… |
|---|---|
| Listing entity types or relationships | "defined in `prompts.py` and `call_center_ontology.owl`" |
| Listing config constants with defaults | "see `config.py` — each constant has an inline comment" |
| Listing env vars with values | "see `.env.example` — annotated list" |
| Listing module files | "source under `call_pipeline/`; see CLAUDE.md for per-module descriptions" |
| "Five rollup passes: A, B, C…" | "multiple idempotent Cypher passes — see `rollup.py`" |
| Hardcoded model names | "configurable via `litellm-config.yaml`" |
| Specific concurrency defaults | "code-level cap in `signals.py` — tune together with `.env`" |

### What belongs in CLAUDE.md (and not in code comments)

CLAUDE.md should contain what Claude cannot derive by reading any single
file — cross-file invariants and non-obvious "why":

- **Data flow narrative**: what calls what, in what order, why the order
  matters (e.g. "don't move env setup below `import cognee`")
- **Load-bearing constraints**: things that would surprise a reader and
  have non-local consequences (e.g. "EMBEDDING_MODEL must start with
  `hosted_vllm/` — see KNOWN_ISSUES.md for why")
- **Cross-file coupling**: shared state, shared constants, ordering
  dependencies between modules
- **Gotchas that span multiple files**: e.g. "throughput is capped in
  three separate places; bumping only `.env` does not raise throughput"
- **Architectural decisions with permanent consequences**: e.g. "URI
  scheme is frozen — renaming the MCP server breaks every stored
  citation"

Specific values (concurrency numbers, default batch sizes, function
names) belong in code comments, not in CLAUDE.md. CLAUDE.md should
describe the invariant and point to the file — not replicate the value.

### Changelog anchors are exempt

Version anchor paragraphs (e.g. "v2.1.0 anchor — tagged…") describe
what was true at a historical moment and are not subject to the
staleness rules above. They must not be edited retroactively.

## Memory policy

Do not use the private memory system (`~/.claude/projects/`) to store
decisions, preferences, or context learned during sessions. Instead, persist
all relevant information directly in the project's `CLAUDE.md` or this global
`~/.claude/CLAUDE.md` so that every user, machine, and AI session has access
to the same up-to-date context via version control.

## Dockerfile naming

Alternative Dockerfiles must be named with the environment as a **prefix**
before `.Dockerfile`, not as a suffix after `Dockerfile`:

- Correct: `dev.Dockerfile`, `test.Dockerfile`
- Wrong: `Dockerfile.dev`, `Dockerfile.test`

## Shell scripts

Ao escrever ou editar scripts bash, consulte primeiro
`~/.claude/guidelines/bash-scripts.md` para as convenções de estilo.

## ExcaliDash / Excalidraw MCP workflow

When asked to create, draw, or generate a diagram, follow this workflow using
the registered MCP tools:

1. `read_me` (excalidraw) — load the element format reference
2. `create_view` (excalidraw) — author and render the elements JSON
3. `read_checkpoint` (excalidraw) — extract elements using the returned checkpointId
4. `save_to_excalidash` (excalidash) — persist the drawing; return the URL to the user

Full tool reference: @/myfiles/Programs/ExcaliDash/mcp/README.md

## Commit message example

```
Allow git read-only commands without permission prompts

Adds status, log, and diff to the allow list so routine inspection
commands do not interrupt the workflow with permission dialogs. Write
operations such as commit and push remain unaffected and will still
require explicit approval.
```
