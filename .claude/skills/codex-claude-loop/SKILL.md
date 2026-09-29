---
name: codex-claude-loop
description: >-
  Coordinate an isolated Claude Code implementation in one local checkout through a
  Codex-supervised CLI run. Use when the user asks Codex to assign implementation to Claude.
---

# Isolated Claude implementation

Use this coordinator skill only for an authorized task that assigns implementation to Claude.
Loading it does not launch Claude or authorize new work. Do not invoke or pass this skill to Claude;
the Claude assignment must be self-contained and must not disclose later Codex review or promise
delivery by another agent.
Model and reasoning settings specified by the user take precedence over recommendations here.

Codex owns planning, assignment, supervision, integration assessment, verification, and the final
verdict. Claude's session owns the assigned checkout implementation and may coordinate internal
subagents for investigation, implementation, tests, supervision, and review. Claude integrates
their work, coordinates checkout edits to avoid conflicts, and remains accountable for the result;
Codex may write authorized coordination plans outside Claude's task-facing context.
Both use the same authorized local checkout and its applicable instructions.
Before work, record staged, unstaged, and untracked changes. Preserve the Git index and existing
work; do not stage, unstage, reset, commit, or perform external or live actions without the user's
authorization. A task has one active implementation owner; Claude's internal subagents do not
become a separate task owner. Do not start an isolated CLI run while a legacy two-session handoff
or another process owns the same task.

After required planning and review gates, assign Claude the authorized implementation, regression
work, and applicable test execution in the repository-prescribed environment through completion of
the plan and acceptance criteria. An evidence gate may sequence that work, but does not transfer
its owner. Claude follows its applicable instructions and skills, gives internal subagents the
scope and context they need, completes its own required reviews, and resolves their findings before
reporting completion. Reconcile delegated work and background tests before ownership changes; an
uncertain active descendant is a partial result. Do not tell Claude that another agent will finish
its assigned work, tests, review, or authorized delivery afterward. Assign user-authorized Git or
external delivery to Claude when it is part of the task; absent that authorization, exclude the
action rather than reserving it for Codex. Codex independently assesses the completed diff and
evidence without supplying missing Claude review, test, or delivery work. Honor an explicit user
choice of a different division of work. Do not impose coordinator-selected limits on Claude's
tools, subagents, turns, duration, iterations, or cost; user limits and provider controls still
apply.

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

## Execute the isolated mode

Read [supervised CLI mode](references/supervised-cli.md). Codex launches and observes Claude's
isolated task session, then independently assesses the completed result. Keep coordinator plans,
reviews, and handoff metadata out of Claude's task-facing prompt, references, and session context.
The task uses no recurring wakeup or two-session handoff file.

Do not create a new two-session handoff: its shared state reveals the coordinator's later role.
The [legacy handoff reference](references/two-session-handoff.md) remains for read-only diagnosis
and user-directed recovery of existing handoffs. Before starting isolated CLI work on a task with
an existing handoff, reconcile its owner, active agents and commands, wakeups, lock, index, working
tree, and partial effects. Do not silently switch modes, break a lock, or claim an old session has
forgotten its prior context. If isolation cannot be established, report the concrete prerequisite.
