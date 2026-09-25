---
name: codex-claude-loop
description: >-
  Coordinate Codex planning and review with Claude Code implementation in the same local checkout,
  either through a Codex-supervised CLI run or a shared handoff between two sessions. Use when the
  user asks the two agents to cooperate on one task.
---

# Codex–Claude collaboration

Use this skill only for an authorized task that assigns work to both Codex and Claude. Loading it
does not launch Claude, create a handoff, schedule checks, or authorize new work. Model and
reasoning settings remain the user's choice.

Codex owns planning, assignment, review, and the final verdict. Claude implements the assigned
scope. Both use the same authorized local checkout and its applicable instructions. Preserve
existing changes and the user's Git and external-action boundaries. A task has one active
implementer; do not run the CLI mode alongside an owned two-session handoff for the same task.

## Choose the mode

- **Codex-supervised CLI:** Use when the user asks Codex to invoke Claude locally or asks for
  Codex–Claude collaboration without requiring a separate Claude chat. Read
  [supervised CLI mode](references/supervised-cli.md). Codex launches and observes each Claude
  turn, then independently reviews the resulting work. This mode has no recurring wakeups or
  two-session handoff file.
- **Two separate sessions:** Use when the user wants to converse with both agents separately or
  requests the existing shared-file or periodic-check workflow. Read
  [two-session handoff](references/two-session-handoff.md). Its `sol-fable-loop/2` file contract,
  ownership transitions, locks, pause rules, and recovery rules remain authoritative for that
  mode.

If the requested mode is unavailable, report the concrete prerequisite or decision needed. Do
not switch modes to bypass a failed assumption, permission decision, or active owner. A
user-directed mode change first reconciles the active process or handoff and all partial changes;
then starts the chosen mode under its own rules.
