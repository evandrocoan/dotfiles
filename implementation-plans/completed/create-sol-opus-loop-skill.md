# Implementation plan: Rename the shared Sol–Opus skill

**Status:** Complete
**Mode:** Plan and execute
**Risk:** High, inherited from the existing shared-skill and protocol plan.

## Outcome

The shared skill is invoked as `sol-opus-loop` from both Claude and Codex. Its canonical package,
Codex symlink, frontmatter, and shared registry agree on that name. The old skill name and link are
removed. Existing handoff files using `sol-fable-loop/2` remain readable without migration.

## Scope and boundaries

- Move the canonical package to `.claude/skills/sol-opus-loop/` and expose it through
  `.agents/skills/sol-opus-loop` with the required relative target.
- Replace the old shared registry entry in `.codex/AGENTS.md` and the skill frontmatter name.
- Keep `protocol: sol-fable-loop/2`, its ownership rules, and the explicit rejection of obsolete
  `owner: fable` files. The protocol identifier is separate from the skill package name.
- Remove the old skill path and old symlink. Do not keep a second discoverable alias.
- Reuse the already renamed active plan file; do not start a Kafka handoff, scheduler, Claude
  session, commit, push, MR, image publication, or deployment.

## Governing decisions and current evidence

- The user chose `sol-opus-loop` and asked for every necessary skill link. Claude skills are
  canonical under `.claude/skills/`; Codex discovers shared skills through `.agents/skills/`.
- The baseline canonical package was `.claude/skills/sol-fable-loop/`, and
  `.agents/skills/sol-fable-loop` pointed to it. `.claude/CLAUDE.md` points to the registry in
  `.codex/AGENTS.md`. Both new skill paths were absent before the rename.
- The repository's `.gitignore` allows both skill trees through wildcard rules. Tracked old-name
  references outside this plan are the skill frontmatter, legacy protocol fields, and registry.
- No `.agent-handoff` directory exists in this checkout, and the checked local scheduler paths are
  absent. The current tool catalog provides no inventory of recurring wakeups in other chats;
  their prompts cannot be silently migrated from this repository change.
- This material continuation inherits the previous plan's high-risk review and closure gates.

## Execution steps

| Status | Step | Evidence of completion |
| --- | --- | --- |
| completed | Review the rename plan under `plan-implementation`. | Fresh read-only findings applied below. |
| completed | Move canonical package and replace shared symlink. | New link resolves; old paths are absent. |
| completed | Update frontmatter, registry, and protocol-name explanation. | Package name and registry match; protocol remains unchanged. |
| completed | Validate both discovery paths and compatibility scenarios. | Both paths pass the validator; link, old-name, and handoff checks below. |
| completed | Complete inherited high-risk closure and move this plan to `completed/`. | Author audit, fresh independent pass, and staged-set reconciliation passed. |

## Plan review

- **Mechanism:** No dedicated advisor interface is available in the current tool catalog. A fresh
  read-only independent agent reviewed this rename plan.
- **Applied findings:** The plan file is already renamed; remove that pending action. Check for
  active handoffs or recurring prompts that still invoke the old skill name before removing its
  discoverable alias. The in-scope handoff directory and checked local scheduler paths are absent;
  wakeups in other chats are not exposed by this client.
- **Rejected findings:** None.

## Replan if

- A current handoff or recurring prompt in this checkout binds the old skill package name rather
  than just the protocol ID.
- The new package or link path appears or the observed symlink topology changes.
- Keeping the legacy protocol prevents the chosen new skill from reading an existing handoff.

## Completion evidence

- `quick_validate.py` accepted both `.claude/skills/sol-opus-loop` and its
  `.agents/skills/sol-opus-loop` symlink. The link target is
  `../../.claude/skills/sol-opus-loop`; the two old skill paths are absent.
- The skill frontmatter and shared registry now use `sol-opus-loop`. The handoff header and
  written file contract still require `sol-fable-loop/2`, and the version-2 Sol/Opus state mapping
  remains. The renamed skill instructs agents to accept the existing version-2 header;
  `quick_validate.py` validates package metadata, not handoff files.
- A read-only comparison with the pre-rename staged skill blob showed only the frontmatter name
  and added legacy-protocol explanation changed. Normal handoff, blocked resumption, cancellation,
  and optional periodic-check instructions were otherwise identical. There is no `.agent-handoff`
  directory in this checkout and no checked local scheduler path; current tools cannot inventory
  recurring prompts in other chats.
- The `.gitignore` wildcard rules admit the new paths. `git diff --check HEAD` passed for the
  registry. These checks do not constitute a live two-client run.

## Closure audit

| Status | Requirement | Evidence |
| --- | --- | --- |
| verified | New canonical package and shared symlink are the only discoverable skill paths. | Old-path absence, new link target, and registry. |
| verified | Frontmatter and registry use `sol-opus-loop`. | Exact content and both validators. |
| verified | Legacy version-2 handoffs retain their written protocol and ownership meaning. | Contract text, owner table, and pre-rename source comparison. |
| verified | Handoff safety and optional scheduler instructions remain unchanged. | Pre-rename source comparison and in-scope handoff check. |
| verified | Only scoped local files changed; staged content is current. | Four intended staged paths, empty working-tree diff, and staged whitespace check. |

- **Forward trace:** The chosen name maps to the canonical directory, shared symlink,
  frontmatter, and registry. Compatibility maps to the unchanged protocol and state table.
- **Reverse trace:** Moved paths and edited name fields implement the rename; the protocol-name
  explanation documents why its legacy value remains. No implementation or scheduler code changed.

### Final conformance verdict

- **Independent pass:** The fresh read-only review found the rename and links consistent. Two
  evidence wording gaps were corrected: package validation is distinct from the written handoff
  contract, and the unchanged behavior claim now cites a comparison with the prior staged skill.
- **Limit:** No live two-client handoff or scheduler was run. Recurring prompts in other chats are
  outside this client's visible inventory; any such prompt using the old skill name needs updating.
- **Verdict:** Pass for the renamed local skill, its shared discovery links, and the retained
  version-2 written handoff contract. No commit or remote delivery was performed.
