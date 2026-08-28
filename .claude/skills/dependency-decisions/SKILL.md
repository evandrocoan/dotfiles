---
name: dependency-decisions
description: Evaluate and select dependency strategies with explicit user approval. Use when new code may require a library, package, framework, service, or system dependency; when an import or package is missing; or when replacing, upgrading, installing, or removing a dependency requires a choice.
---

# Dependency decisions

Choose dependencies deliberately. Do not install, add, replace, upgrade, or
remove one until the applicable repository constraint or the user's choice is
clear.

## Inspect existing constraints

1. Read the repository instructions, manifests, lockfiles, build configuration,
   and existing imports relevant to the task.
2. Determine whether the repository already mandates a dependency or strategy.
   When that leaves no meaningful choice, state the constraint and proceed
   without asking a redundant question.
3. Check whether an already approved dependency can satisfy the requirement
   before proposing another package.
4. Confirm that the requested behavior genuinely needs a dependency rather than
   assuming one from a familiar implementation pattern.

## Compare viable strategies

Present the reasonable options, including:

- suitable maintained third-party libraries;
- reuse of an already approved project dependency;
- a standard-library-only approach when it is genuinely viable;
- a service or system dependency when that is the actual architectural choice.

Compare only factors material to the task, such as ergonomics, maintenance,
performance, portability, compatibility, security posture, licensing, package
size, runtime cost, and installation or operational burden. Verify unstable
facts against authoritative current sources when they affect the decision.

Recommend the option that best fits the repository and explain the tradeoff.
Do not present the recommendation as an approved choice.

## Obtain the decision

Ask the user to choose before changing manifests, lockfiles, imports, images, or
the environment. A separate question is unnecessary only when the user already
selected the strategy or an explicit repository rule leaves no meaningful
alternative; state that basis before proceeding.

When an import or package is missing, report the exact evidence. Ask whether to
install the dependency or use an alternative already available. Never install
the missing package automatically.

## Apply the approved choice

After approval:

1. Use the repository's package manager and prescribed environment.
2. Make only the dependency changes required by the selected strategy.
3. Avoid unrelated upgrades or lockfile churn.
4. Preserve the repository's formatting and dependency declaration style.
5. Validate compatibility through the repository's relevant build or test
   workflow, loading the applicable testing skill before test work.
6. Report the selected strategy, changed dependency files, and validation.

Do not create unrelated documentation or tests unless the user requested them.
