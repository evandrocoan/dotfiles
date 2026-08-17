---
name: documentation
description: "Create, edit, review, or reorganize durable Markdown documentation. Use for README files, docs, runbooks, CLAUDE.md, AGENTS.md, skill and command instructions, changelogs, and any task that writes or changes documentation."
---

# Documentation

Apply these rules when creating, editing, reviewing, or reorganizing
documentation. Inspect the target document and its authoritative sources before
changing content.

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

## Distinguish README.md from agent instructions

Keep `README.md` user-facing. Cover setup, operational usage, and runbooks,
answering "how do I run this?"

Keep `CLAUDE.md`, `AGENTS.md`, skills, and equivalent agent instructions
AI-facing. Record architectural context, cross-file invariants, non-obvious
constraints, and decisions with their rationale, answering "why is the code
structured this way, and what breaks if I change it?"

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

## Preserve historical anchors

Treat version anchor paragraphs as records of what was true at a historical
moment. Do not retroactively edit them or apply current-state staleness rules to
them.
