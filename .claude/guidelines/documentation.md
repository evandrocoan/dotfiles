# Documentation guidelines

## General

Never write documentation that embeds data which becomes stale as the code
evolves. Specifically:

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

## README.md and CLAUDE.md roles

`README.md` is user-facing. It covers setup, operational usage, and runbooks,
answering "how do I run this?"

`CLAUDE.md` is AI-facing. It records architectural context, cross-file
invariants, non-obvious constraints, and decisions with their rationale,
answering "why is the code structured this way, and what breaks if I change
it?"

## Markdown tables of contents

Whenever editing a Markdown document that already has a table of contents,
keep it synchronized with the document's headings.

For long-form user-facing Markdown, create a table of contents when it would
materially improve human navigation. Include substantive sections and relevant
subsections.

Do not add a table of contents to AI-facing instruction files such as
`CLAUDE.md`, `AGENTS.md`, skill definitions, or command definitions. Clear
headings provide structure without duplicating tokens in every agent context.
Also omit tables of contents from short documents, templates, changelogs,
generated files, and other documents where they add little navigational value.

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

## What belongs in CLAUDE.md

Include information that cannot be derived by reading a single file:

- Data flow and why operation order matters.
- Load-bearing constraints with non-local consequences.
- Cross-file coupling and shared state.
- Gotchas that span multiple files.
- Architectural decisions with permanent consequences.

Keep specific values such as concurrency limits, batch sizes, and function
names in code comments. Describe the invariant in `CLAUDE.md` and point to the
authoritative file instead of duplicating the value.

## Historical changelog anchors

Version anchor paragraphs describe what was true at a historical moment. Do
not retroactively edit them, and do not apply current-state staleness rules to
them.
