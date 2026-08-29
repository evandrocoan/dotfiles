---
name: documentation
description: "Create, edit, review, reorganize, or synchronize durable Markdown documentation. Use for README files, docs, runbooks, CLAUDE.md, AGENTS.md, Copilot instructions, skill and command instructions, changelogs, and any task that writes or changes documentation or synchronizes AGENTS.md-first project guidance across Claude, Codex, and Copilot."
---

# Documentation

Apply these rules when creating, editing, reviewing, or reorganizing
documentation. Inspect the target document and its authoritative sources before
changing content.

## Match document language

Write AI-facing instruction files in English. This includes `CLAUDE.md`,
`AGENTS.md`, skills, slash commands, `.github/copilot-instructions.md`, and
equivalent agent guidance. Keep literal strings that an agent must emit and
instructions that prescribe an output language in their required language.

For every other existing document, match its language. If it already mixes
languages, ask whether to continue in the dominant language, select a language
for new content only, or normalize the entire document before editing it.

## Format Markdown consistently

- Use normal sentence case for headings; do not use CamelCase titles.
- In Markdown table separator rows, use spaces around the dashes, such as
  `| --- | --- |`.
- Preserve the surrounding document's formatting style and avoid unrelated
  reformatting.

## Keep content durable

Never embed information that will silently become stale as the code evolves:

- Do not hardcode counts such as tool, graph, or entity totals. Omit the number
  or link to the authoritative source instead.
- Do not put current version numbers in prose. Historical statements such as
  "removed in v2.1" are allowed.
- Do not copy lists maintained in code, such as tool names, modules, CLI
  subcommands, environment variables, schema fields, model names, proxy
  aliases, or defaults. Point to the authoritative source instead.
- Do not put deployment- or tenant-specific values in shared documentation,
  even as examples.

Use qualitative language for quantities so documentation remains accurate as
the code evolves. A list reproduced directly from its authoritative source is
allowed only when the document states that the copies must remain synchronized.

## Use immutable source evidence

Distinguish navigation links from evidence links. Use relative repository paths
for ordinary navigation to content that should follow the current branch. When a
document cites source code, configuration, or a specific line range as evidence
for a claim, use the provider's permalink bound to the full commit SHA. Never
anchor durable evidence to a moving branch, tag, or default-branch URL.

Resolve the exact revision through the repository provider connector or API and
read the cited content at that revision before writing the link. Verify that the
referenced lines support the surrounding claim, then use the provider-generated
permalink and its stable line anchors. Do not guess a SHA, combine line numbers
from one revision with another revision, or silently move an existing permalink
to a newer commit.

Preserve an existing immutable link when it still supports the claim. If the
exact revision or cited range cannot be verified, mark the reference as
unverified or omit the claim instead of replacing it with a moving link.

## Verify claims and lifecycle

Treat behavior as current only after checking its authoritative code,
configuration, test, or generated source. Label intended behavior as planned
and link to its proposed architecture record; do not describe it as available.
Preserve explicitly historical statements as history. When a claim cannot be
verified, say so or remove it instead of presenting an inference as fact.

## Distinguish README.md from agent instructions

Keep `README.md` user-facing. Cover setup, operational usage, and runbooks,
answering "how do I run this?"

Keep `CLAUDE.md`, `AGENTS.md`, skills, and equivalent agent instructions
AI-facing. Record architectural context, cross-file invariants, non-obvious
constraints, and decisions with their rationale, answering "why is the code
structured this way, and what breaks if I change it?"

## Synchronize agent instructions

Treat root `AGENTS.md` as the canonical shared project guidance. Whenever any of
`AGENTS.md`, `CLAUDE.md`, or `.github/copilot-instructions.md` exists, or a task
creates or edits AI-facing project guidance, ensure all three paths exist and
expose the shared instructions.

Keep the compatibility files regular so every supported consumer can load
them:

- make `CLAUDE.md` begin with the plain import line `@AGENTS.md`, outside code
  spans and fences, so Claude Code expands the canonical guidance;
- keep `.github/copilot-instructions.md` byte-identical to `AGENTS.md` for
  Copilot surfaces that do not load agent instructions directly.

Create `.github/` when needed. Do not replace either compatibility file with a
symlink. Add Claude-specific guidance below the import only when it cannot be
shared safely; keep shared rules in `AGENTS.md`. Do not add Copilot-specific
material to the synchronized repository-wide copy; use a supported scoped
instruction mechanism when such guidance is required.

When existing files differ, inspect every one before changing them. Consolidate
unique, non-conflicting shared guidance into `AGENTS.md`, preserve justified
Claude-specific guidance below its import, and resolve material conflicts with
the user. Never overwrite or discard unique guidance merely to enforce
synchronization.

After every canonical change, refresh the Copilot copy and verify
synchronization with `cmp -s AGENTS.md .github/copilot-instructions.md`. Verify
that the first non-empty line of `CLAUDE.md` is exactly `@AGENTS.md`. Revalidate
all three paths before delivery.

## Maintain tables of contents

When editing a Markdown document that already has a table of contents, keep it
synchronized with the document's headings.

For long-form user-facing Markdown, create a table of contents when it would
materially improve human navigation. Include substantive sections and relevant
subsections.

Do not add a table of contents to AI-facing instruction files. Clear headings
provide structure without duplicating tokens in every agent context. Also omit
tables of contents from short documents, templates, changelogs, generated
files, and other documents where they add little navigational value.

## Prefer authoritative pointers

Instead of duplicating evolving information, point to its authoritative source:

| Instead of… | Write… |
| --- | --- |
| Listing entity types or relationships | "defined in `prompts.py` and `call_center_ontology.owl`" |
| Listing configuration constants with defaults | "see `config.py`; each constant has an inline comment" |
| Listing environment variables with values | "see `.env.example`; annotated list" |
| Listing module files | "source under `call_pipeline/`; see CLAUDE.md for architectural context" |
| Enumerating rollup passes | "multiple idempotent Cypher passes; see `rollup.py`" |
| Hardcoding model names | "configurable via `litellm-config.yaml`" |
| Stating concurrency defaults | "code-level cap in `signals.py`; tune together with `.env`" |

## Keep agent instructions concise

Include information that cannot be derived by reading a single file:

- Data flow and why operation order matters.
- Load-bearing constraints with non-local consequences.
- Cross-file coupling and shared state.
- Gotchas that span multiple files.
- Architectural decisions with permanent consequences.

Keep specific values such as concurrency limits, batch sizes, and function
names in code comments. Describe the invariant in agent instructions and point
to the authoritative file instead of duplicating the value. Move procedures or
task-specific reference material to skills so they load only when relevant.

Use the `architecture-records` skill when documentation changes a durable
cross-component invariant, ownership boundary, stage order, failure meaning, or
recovery rule. Keep the extended rationale in the architecture record and only
the current load-bearing rule in agent instructions.

## Validate coupled documentation

Search for duplicate or contradictory descriptions in affected documentation,
agent instructions, architecture records, and configuration examples. Update or
replace stale copies with authoritative pointers rather than synchronizing prose
manually.

Before handoff, validate affected links, anchors, paths, and symlinks. Exercise
changed commands or executable examples in the repository-approved environment
when practical; otherwise report them as unverified. Run available Markdown and
whitespace checks, inspect untracked files as well as the diff, and report the
validation performed.

## Preserve historical anchors

Treat version anchor paragraphs as records of what was true at a historical
moment. Do not retroactively edit them or apply current-state staleness rules to
them.
