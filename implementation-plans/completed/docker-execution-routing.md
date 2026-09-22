# Implementation plan: Docker execution routing

**Status:** Completed
**Mode:** Plan and execute
**Risk:** High risk: shared skill routing and host-execution authorization guidance.

## Outcome

Agents load the Docker skill before choosing dependency-installation, build, test, or service-start
commands when the repository establishes a Docker/Compose workflow. Mere code reading, source
editing, or test authoring does not activate this additional trigger. Host execution is an explicit
exception, with existing, specific user authorization preserved.

## Scope

- Update the description and execution guidance in `.claude/skills/docker/SKILL.md`.
- Synchronize only the Docker entry in the shared registry in `.codex/AGENTS.md`.
- Preserve `.agents/skills/docker` and `.claude/CLAUDE.md` as relative aliases of their owners.
- Do not change `dependency-decisions`, `test-quality`, runtime-owned skills, Docker resources,
  dependency installations, command allowlists, unrelated global rules, or ExcaliDash files.
- This plan is the temporary execution record; shared skill workflow policy stays in the skill.

## Governing decisions and invariants

- The user selected a narrow trigger in the Docker skill and its registry entry, then instructed
  correction of that skill. Earlier proposals to change two other skills were superseded.
- Global instructions require preserving user authorization, canonical shared sources, relative
  links, and unrelated working changes. No Git-state mutation is authorized.
- `skill-creator` and `documentation` require precise discovery and scoped, English instructions.
- `plan-implementation` requires independent plan and closure review for authorization-rule changes.
- Explicit authorization for host execution remains valid; generic approval to install dependencies
  or run tests does not itself choose host execution over a repository container workflow.

## Current evidence and assumptions

- The pre-change Docker description covers container work but does not explicitly route ordinary
  dependency installation or test commands through Docker environment selection first.
- The pre-change regression is authenticated by this session: ExcaliDash has Docker/Compose files,
  but missing frontend dependencies led to host `npm ci` before the Docker skill was loaded.
  Generic approval to install and validate did not explicitly select host execution. Do not repeat
  that installation as a negative control.
- Its original body prohibits host dependency installation to bypass a missing container entry point.
- The original registry repeats that trigger and is stored in `.codex/AGENTS.md`;
  `.claude/CLAUDE.md` points to it. `.agents/skills/docker` points to `.claude/skills/docker`.
- The target skill and registry had no pre-existing working changes. Two unrelated decision-flow
  documents under `implementation-plans/` were modified and must remain untouched.
- The repository has an existing implementation-plan lifecycle. Its briefs concern other subjects;
  the mention of Docker in the decision-flow brief only illustrates progressive disclosure.
- No advisor tool is available. An independent reviewer is available and pre-authorized by the
  governing review policy.
- No unresolved implementation assumption remains. Structural validation uses the existing skill
  validator; it must not install dependencies if that validator cannot run.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| completed | Independent plan review | Shared authorization guidance requires this review. | Fresh-context reviewer found two validation clarifications, both applied below. |
| completed | Edit skill and registry | Both are clean canonical owners with existing relative aliases. | Updated conditional discovery and explicit host exception in the two canonical owners. |
| completed | Validate discovery and behavior | A structural validator alone cannot prove routing. | Existing validator passed; relative aliases, reference targets, diff, and original/revised decision cases checked. |
| completed | Independent closure and lifecycle | All preceding evidence must be complete. | Author audit and fresh independent conformance/scenario review passed; moved this same plan to completed. |

## Guidance and validation scenarios

The new discovery text applies before choosing commands for project dependency installation, build,
test execution, or service startup when repository instructions or files establish a Docker/Compose
workflow, even if the user never mentions containers. It excludes ordinary code reading, source
editing, and test authoring alone from this additional trigger, while preserving existing triggers
for direct Docker work.

The body first checks the documented container workflow for the affected component and task. It
prefers that workflow unless the user already explicitly chose host execution. If it is unavailable
or unsuitable, the agent explains the concrete obstacle and proposed host commands and effects
before asking for an explicit host exception. Generic install/test approval does not substitute for
that choice; prior explicit host approval must not generate a repeated question.

Compare original and revised guidance on the same cases in read-only review; do not execute project
runtimes or create Docker resources. Use the authenticated incident above and the original Git
content as the baseline. Record which original gap the revised discovery and execution wording
detects; a validator pass alone is not regression evidence.

1. A React fix needs frontend tests, the repository provides Docker/Compose, and host `node_modules`
   is absent: consult Docker before choosing installation/test commands.
2. The same repository has no usable test container entry point: explain the exact gap before
   requesting a host exception; do not silently install on the host.
3. The user already explicitly authorized those tests on the host: preserve that authorization.
4. The task only reads source, edits a component, or writes a test without executing it: this
   additional routing trigger does not apply.
5. A repository has no Docker/Compose workflow: this trigger does not make every runtime task a
   Docker task. Direct Dockerfile/Compose work still activates the skill independently.
6. A task only needs a database sidecar in Compose: inspect applicability to the affected component
   rather than assuming an application test runner exists inside that database container. Loading
   Docker guidance does not authorize creating an application container. If only a native test
   workflow is documented, explain that limitation and the proposed host operation, then request
   the host exception unless the user already explicitly selected it. Documentation of a native
   command alone must not recreate the original generic-approval failure.

## Plan review

- **Mechanism:** Independent reviewer; advisor unavailable.
- **Independent reviewer:** `docker_plan_review`, fresh-context `deep-reviewer`, read-only. There
  was no advisor model to compare; review independence comes from a separate context and evidence.
- **Applied findings:** Specify the sidecar-only outcome and distinguish loading guidance from
  requiring a new container; compare original and revised decisions including generic approval.
  Reconcile existing one-shot/host-installation wording with the explicit host exception.
- **Rejected findings:** None.

## Replan conditions

- A source or alias is different from the verified canonical topology.
- Concurrent edits overlap either target, or another affected registry is discovered.
- The proposal activates Docker for unrelated reading/editing or invalidates explicit user choices.
- Validation needs dependency installation, project execution, or scope expansion.

## Completion evidence

- `python3 .claude/skills/skill-creator/scripts/quick_validate.py .claude/skills/docker` passed:
  the existing validator accepted the name, YAML frontmatter, description, and scaffold checks.
- Scoped `git diff --check` passed. The two instruction diffs contain only the Docker description,
  execution boundary guidance, and matching registry entry.
- Read-only path checks verified the exact relative targets of both existing aliases and every
  linked local Docker reference. No alias or reference file was changed.
- Full author reread covered this plan, the revised Docker skill, canonical global instructions,
  and the home repository's root instructions. No coupled architecture record applies.
- No project runtime, build, package installation, Docker operation, or Git-state mutation was
  performed for this skill change. The existing validator and path checks use maintenance tooling.
- The plan is untracked. The two pre-existing decision-flow document changes remain outside scope.

Read-only contract comparison, using original Git content and this session's incident as baseline:

| Case | Original guidance | Revised guidance |
| --- | --- | --- |
| Ordinary frontend test work in Docker repository | Discovery did not expressly cover choosing ordinary project commands; the observed host install preceded skill loading. | Both discovery surfaces require loading Docker before command selection. |
| Missing test entry point and generic install approval | Host bypass was prohibited after skill loading, but discovery and environment-specific approval were implicit. | Report the concrete gap and proposed host effects; generic approval is insufficient. |
| Prior explicit host choice | Global user authority applies, but the local one-shot rule was unconditional. | Explicit choice is honored without another question; one-shot guidance applies to the container route. |
| Read/edit/author only | No ordinary project-execution trigger existed. | Explicit exclusion preserves that result; direct Docker-file work still activates its original trigger. |
| No repository container workflow | Direct Docker tasks were covered. | No new trigger for ordinary non-container project tasks; direct Docker tasks remain covered. |
| Database sidecar only | Scope of the relevant runtime needed inference. | Inspect the affected task; do not infer an application runner or authorization to create infrastructure. Explain the gap before an unapproved host fallback. |

This comparison validates the instruction contract, not a statistical guarantee of future model
compliance. The fresh-context `docker_closure_review` independently assessed the six cases, both
trace directions, aliases, affected references, and scoped diff; it reported no findings or unresolved
implementation requirements. It also confirmed the scoped whitespace check. No review finding was
rejected. No live client or container replay was performed or required for this instruction change.

## Closure audit

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| verified | Conditional routing before command selection | Skill description and registry | Both descriptions name execution tasks and require repository Docker/Compose evidence. |
| verified | Narrow exclusions and existing Docker coverage | Skill description and body | Read/edit/author exclusion is limited to the new trigger; original Docker capabilities remain. |
| verified | Explicit host exception and existing user authority | Execution guidance | Concrete obstacle and host effects precede a host request; existing explicit choices remain valid. |
| verified | Single canonical source and relative aliases | Shared skill and global registry links | Exact relative targets and reference paths passed read-only checks. |
| verified | Scope and existing edits preserved | Final diff and repository status | Only the two authorized instruction owners changed; unrelated documents remain outside edits. |
| verified | Structural and author behavioral validation | Existing validator and comparison above | Structural validation, whitespace check, and six original/revised contract cases passed author review. |
| verified | Full reread and both trace directions | Implementer and independent closure review | Author reread and traces complete; `docker_closure_review` passed independently with no findings. |

Forward trace: the user's narrow discovery decision maps to the skill description and registry;
the host-exception decision maps to execution guidance; scenario review covers both.
Reverse trace: each changed instruction must map to one of those decisions. This plan only records
their execution and review. No architecture record applies to this shared skill workflow change.

### Final conformance verdict

- **Verdict:** Passed.
- **Second pass:** Independent; `docker_closure_review`, fresh-context `deep-reviewer`.
- **Auditor and evidence:** Author audit plus independent scoped Git diff, original/revised scenarios,
  aliases, references, and the validation evidence recorded above.
- **Unresolved requirements:** None.
- **Brief check:** No brief on this subject; unrelated decision-flow artifacts remain untouched.
