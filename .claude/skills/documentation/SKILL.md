---
name: documentation
description: "Create, edit, review, reorganize, or synchronize durable Markdown documentation. Use for README files, docs, runbooks, CLAUDE.md, AGENTS.md, Copilot instructions, skill and command instructions, changelogs, and any task that writes or changes documentation or exposes canonical AGENTS.md guidance to Claude, Codex, and Copilot without duplicating it."
---

# Documentation

Apply these rules when creating, editing, reviewing, or reorganizing
documentation. Inspect the target document and its authoritative sources before
changing content.

## Preserve the requested scope

- Treat examples named by the user as the edit targets, not as permission to
  rewrite adjacent content.
- Before removing content as duplication, verify that it has the same audience,
  execution boundary, inputs, outputs, and configuration semantics as its
  proposed replacement. If any of these differ, preserve it.
- Treat commands for host versus container, bridge versus host, interactive
  versus non-interactive use, and configuration that transforms canonical
  defaults for a supported mode as distinct operational workflows. They are
  not duplicates merely because they produce the same result or repeat some
  source values.
- When replacing copied facts with an authoritative pointer, preserve nearby
  procedures unless the user explicitly includes them, they directly
  contradict the requested change, or leaving them unchanged would make the
  edited instructions incorrect.
- When uncertain whether content is reference duplication or an operational
  recipe, preserve it and report the possible duplication instead of deleting
  or consolidating it.
- Report unrelated stale or improvable content separately instead of editing
  it opportunistically.

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
- Use the Markdown line width explicitly enforced by the repository. When the
  repository defines no width, wrap ordinary prose written or changed by the
  current task at 100 columns. Count list markers, blockquote prefixes, and
  indentation toward the target.
- Treat 100 columns as a soft limit. Tables, code blocks, HTML, URLs, paths,
  link destinations, and indivisible identifiers may exceed it. Never damage
  Markdown syntax or split an indivisible token solely to meet the limit.
- Preserve untouched prose and avoid whole-file line-width normalization unless
  the user explicitly requests it.
- Prefer the repository-approved Markdown formatter when one exists. Do not
  add a formatter or dependency without applying `dependency-decisions` and
  obtaining user approval.

## Keep content durable

Never embed information that will silently become stale as the code evolves:

- Do not hardcode counts such as tool, graph, or entity totals. Omit the number
  or link to the authoritative source instead.
- Do not put current version numbers in prose. Historical statements such as
  "removed in v2.1" are allowed.
- Do not copy reference inventories maintained in code, such as tool names,
  modules, CLI subcommands, environment variables, schema fields, model names,
  proxy aliases, or defaults, when an authoritative pointer gives the reader
  everything needed.
- Preserve complete, copy-ready operational configuration when it is required
  to transform canonical defaults for a documented mode or execution boundary.
  Link to the authoritative base, state why the overlay differs, and verify the
  repeated values against the current source instead of replacing the recipe
  with a pointer.
- Do not put deployment- or tenant-specific values in shared documentation,
  even as examples.

Use qualitative language for quantities so documentation remains accurate as
the code evolves. Never reproduce content merely to support another consumer.
Use an import, include, relative symlink, or authoritative pointer instead. If
the consumer supports none of these mechanisms, report the compatibility
limitation rather than creating another manually synchronized source.

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

## Keep one source of truth for agent instructions

Treat root `AGENTS.md` as the only source of project-wide AI guidance. Whenever
any of `AGENTS.md`, `CLAUDE.md`, or `.github/copilot-instructions.md` exists, or
a task creates or edits AI-facing project guidance, ensure all three paths exist
without copying the canonical content.

Expose `AGENTS.md` through compatibility files:

- keep `CLAUDE.md` as a regular file whose only content is the plain import
  `@AGENTS.md`, followed by a newline;
- keep `.github/copilot-instructions.md` as a relative symbolic link to
  `../AGENTS.md`.

Create `.github/` when needed. Never copy shared instructions into either
compatibility path, and never maintain byte-identical regular-file copies. Put
all project-wide rules in `AGENTS.md`. Use a supported scoped instruction file
only for genuinely consumer-specific rules; do not append them to these
repository-wide compatibility paths.

When existing files differ, inspect every one before changing them. Consolidate
unique, non-conflicting project-wide guidance into `AGENTS.md`, resolve material
conflicts with the user, then replace the compatibility files with the import
and relative symlink above. Never discard unique guidance merely to enforce the
layout.

After every canonical change, verify that `CLAUDE.md` contains exactly
`@AGENTS.md` plus its final newline and that
`.github/copilot-instructions.md` resolves through the relative symlink to the
root `AGENTS.md`. Revalidate all three paths before delivery.

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
| Configuring a mode that differs from `.env.example` | Keep the verified, copy-ready overlay and link to `.env.example` as its base |
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
