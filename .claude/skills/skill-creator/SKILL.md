---
name: skill-creator
description: Create or update a shared agent skill with appropriately scoped instructions and supporting resources.
metadata:
  short-description: Create or update a shared skill
---

# Shared skill creator

Read [UPSTREAM.md](UPSTREAM.md) in full before creating or updating a skill. It is the imported
Codex authoring guide. Apply the local adaptations below when its client-specific guidance differs
from this shared environment.

Use the `documentation` skill for skill instructions and references. Its writing conventions and
coupled-document consistency check govern the local authoring work, including the upstream guide's
optional contents-section suggestion. Apply that check to the changed rule's owner and consumers
before delivery; keep domain policy in its existing owning skill rather than reproducing it here.

## Shared-package adaptations

Use the shared-package location and exposure rules from the applicable global instructions.
For packages shared with Claude and Copilot, do not apply the upstream `$CODEX_HOME` scaffolding
or generate Codex-only `agents/openai.yaml` artifacts. The upstream initializer generates that
metadata automatically; create the shared package's required files directly instead. Preserve
existing imported metadata and resources in this package. Use the upstream UI-metadata guidance
only when the requested task actually targets Codex metadata.

## Imported and local ownership

Customize this entrypoint or the existing skill that owns the policy. Do not edit `UPSTREAM.md`
or other files listed in [upstream-manifest.json](upstream-manifest.json) as local adaptations.
The manifest maps each imported source file to its destination and records its snapshot hash.
`SKILL.md` from upstream is stored as `UPSTREAM.md` beside this entrypoint so its resource paths
remain valid without creating another discoverable skill.

Refresh imported files through the owning repository's maintenance procedure. Review upstream
changes against these adaptations and the coupled-document rules before replacing the imported
snapshot; do not overwrite this entrypoint with the system copy.
