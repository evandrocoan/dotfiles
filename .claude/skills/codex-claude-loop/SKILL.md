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
reasoning settings specified by the user take precedence over this skill's recommendations.

Codex owns planning, assignment, supervision, integration assessment, verification, and the final
verdict. Claude's session owns the assigned checkout implementation and may coordinate internal
subagents for investigation, implementation, tests, supervision, and review. Claude integrates
their work, coordinates checkout edits to avoid conflicts, and remains accountable for the result;
Codex may write authorized plans and handoff artifacts.
Both use the same authorized local checkout and its applicable instructions.
Before work, record staged, unstaged, and untracked changes. Preserve the Git index and existing
work; do not stage, unstage, reset, commit, or perform external or live actions without the user's
authorization. A task has one active implementation owner; Claude's internal subagents do not
become a separate CLI or handoff owner. Do not run the CLI mode alongside an owned two-session
handoff for the same task.

After required planning and review gates, assign Claude the authorized implementation, regression
work, and applicable test execution in the repository-prescribed environment through completion of
the plan and acceptance criteria. An evidence gate may sequence that work, but does not transfer
its owner. Claude follows its applicable instructions and skills, gives internal subagents the
scope and context they need, and resolves their findings before handing work to Codex. Reconcile
delegated work and background tests before ownership changes; an uncertain active descendant is a
partial result. Codex supervises and reviews the integrated diff and test evidence; internal Claude
reviews do not replace required independent Codex reviews, and an authorized independent rerun by
Codex does not substitute for tests assigned to Claude. Honor an explicit user choice of a
different division of work. Do not impose coordinator-selected limits on Claude's tools,
subagents, turns, duration, iterations, or cost; user limits and provider controls still apply.

## Recommended profile for complex work

Use Codex Sol xhigh to plan, supervise, integrate findings, and verify; Claude Opus 5.5 xhigh as
the checkout implementation owner, including its internal subagents; and Codex Astra xhigh for
independent, read-only reviews with fresh context before high-risk edits and at closure. This is a
recommendation, not a model override:
honor each explicit user choice of model and effort. Check that the selected roles and settings are
available before assigning work. If a required reviewer cannot run, hold the dependent high-risk
work or closure and report the decision needed; do not silently substitute another reviewer.

For each task, assess the lowest adequate model and effort separately for coordination,
implementation, and any required review. Do not apply the complex-work profile mechanically to
smaller tasks: Sol medium may suffice for coordination and Sol high for an independent review when
the task's difficulty and risk support those choices. Keep an explicitly selected model or effort,
and verify the acting setting for each role rather than inferring it from another agent's setting.

The coordinator gives the independent reviewer the user request, applicable instructions, plan,
repository baseline, and relevant diff without an intended verdict. The reviewer reports findings
without editing or publishing a handoff. The coordinator evaluates and reports all findings,
including disagreements; Claude implements any accepted correction. After a material correction,
repeat the affected validation and closure review before claiming completion. Keep these reviews
within the ownership rules of the selected mode.

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
not switch collaboration modes to bypass a failed assumption, permission decision, or active
owner. Before a user-directed mode change, reconcile the active process or handoff and all partial
changes; then start the chosen mode under its own rules.
