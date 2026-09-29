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

Codex owns plan recommendations and any user-selected plan, assignment, supervision,
integration assessment, verification, and the final verdict. Claude's session owns the assigned
checkout implementation and may coordinate explicitly
authorized internal subagents for investigation, implementation, tests, supervision, and review.
Claude integrates their work, coordinates checkout edits to avoid conflicts, and remains
accountable for the result;
Codex may write a user-selected coordination plan outside Claude's task-facing context.
Both use the same authorized local checkout and its applicable instructions.
Before work, record staged, unstaged, and untracked changes. Preserve the Git index and existing
work; do not stage, unstage, reset, commit, or perform external or live actions without the user's
authorization. A task has one active implementation owner; Claude's internal subagents do not
become a separate task owner. Do not start an isolated CLI run while another owner, process, or
scheduled action may still act on the task, or an existing lock has not been reconciled.

After the user's separate plan and review choices and all independent gates, assign Claude the
authorized implementation, regression work, and applicable test execution in the
repository-prescribed environment through completion of the acceptance criteria and any selected
plan. An evidence gate may sequence that work, but does not transfer its owner. Claude follows
its applicable instructions and skills, gives authorized internal
subagents the scope and context they need, completes selected reviews, and resolves findings before
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

Use Codex Sol xhigh to coordinate, supervise, integrate findings, and verify; Claude Opus 5.5
xhigh as the checkout implementation owner, with any authorized internal subagents; and Codex
Astra xhigh for
independent, read-only reviews with fresh context before high-risk edits and at closure. This is a
recommendation, not a model override:
honor each explicit user choice of model and effort. Check that the selected roles and settings are
available before assigning work. If a selected reviewer cannot run, hold its dependent phase
until review or explicit withdrawal; do not silently substitute another reviewer.

For each task, assess the lowest adequate model and effort separately for coordination,
implementation, and any user-selected review. Do not apply the complex-work profile mechanically to
smaller tasks: Sol medium may suffice for coordination and Sol high for an independent review when
the task's difficulty and risk support those choices. Keep an explicitly selected model or effort,
and verify the acting setting for each role rather than inferring it from another agent's setting.

When selected, the coordinator gives the independent reviewer the user request, applicable
instructions, any plan, repository baseline, and relevant diff without an intended verdict. The
reviewer reports findings without editing the checkout. The coordinator evaluates and reports all
findings,
including disagreements; Claude implements any accepted correction. After a material correction,
repeat affected validation and any selected closure review before claiming completion. Keep these reviews
within the ownership rules of this workflow.

## Execute the isolated CLI workflow

Read [supervised CLI workflow](references/supervised-cli.md). Codex launches and observes Claude's
isolated task session, then independently assesses the completed result. Keep coordinator plans,
reviews, and coordination metadata out of Claude's task-facing prompt, references, and session
context. Before launch, reconcile prior owners, active agents and commands, scheduled reactivations,
locks, the index, working tree, and partial effects. Do not break a lock, alter a prior task's
recovery state, or claim an old session has forgotten its context without the user's direction.
If isolation cannot be established, report the concrete prerequisite.
