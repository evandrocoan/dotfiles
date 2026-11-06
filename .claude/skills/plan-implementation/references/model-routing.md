# Model-aware planning route

Use this after applying the global client-specific model/effort rules and classifying the request,
risk, persistence, and inherited plan. Group labels express planning and review recommendations, not a
universal ranking of model quality or permission to skip safety checks.

The entrypoint's **Determine the planning mode** loads the canonical global rules for settings
and user choices. Apply them before this routing table; this reference owns the task-specific
recommendations, not another model-selection or approval procedure.

## Recommend a route and ask for the user's choices

An explicit plan-only request selects a plan and stops before implementation. Question-only and
read-only requests do not open an implementation choice. For an authorized edit, classify risk and
persistence first. They determine the recommendation and proportional verification, while the
user decides independently whether to have a formal plan and a review, including a formal audit.

| Acting group | Routine local reversible edit | Non-trivial local reversible edit |
| --- | --- | --- |
| Supervised: Terra, Sonnet, Luna, Haiku | Recommend direct work and an independent result review. Ask about review; offer a plan if the user wants one. | Recommend a compact plan and independent result review. Offer each independently. |
| Autonomous: Sol, Opus, Astra, Fable | Recommend direct work without a separate reviewer when owner and check are clear. Ask whether the user's sense of importance warrants review; offer a plan if requested. | Recommend direct work or a compact plan according to uncertainty, coordination, and the user's stakes. Recommend an independent result review and offer each independently. |

When settings remain unknown under the global fallback, base the recommendation on task risk and
persistence without assigning an unverified model group.

Direct work means implementation without a formal plan artifact, after the chat summary has been
presented and explicitly approved under
[proposal approval](../SKILL.md#present-the-proposal-and-wait-for-approval). Neither this table nor
a decision to dispense with the plan waives that gate.

For high-risk architecture, protocol, security, authorization, migration, or costly validation,
strongly recommend a full persistent plan and qualified pre-edit and final independent reviews.
For lower-risk work likely to cross phases or sessions, recommend a compact persistent plan;
recommend review according to its actual risk and model route. Explain the concrete reason and
adequate planner, implementer, and reviewer model/effort when recommending a pair. A supervised
implementer often benefits from an autonomous reviewer even for routine work. These recommendations never turn
plan, review, formal audit, or model recommendation into a compulsory gate. Authorization, actual
tool availability, and honest validation claims still apply.

Apply the global consultation procedure at every situation identified by the table and the
high-risk route, including a recommendation for direct work without extra review. Keep the
routine-local exception to offering a plan. Then use
[proposal approval](../SKILL.md#present-the-proposal-and-wait-for-approval) for the selected route.
A review before drafting assesses the approach; a review of the plan itself follows its creation.

## Recommend models and effort separately for each role

Keep detection of the acting agent's settings separate from recommendations for the work. When
the roles apply, recommend a concrete supported model and reasoning effort for each, with a short
reason tied to its scope, uncertainty, consequences, and available verification:

| Role | Assess independently |
| --- | --- |
| Planner | Investigation and decisions needed to produce an executable plan. |
| Plan reviewer | Assumptions, omitted consumers, sequencing, and validation gaps in that plan. |
| Implementer | Difficulty of carrying out the approved approach, remaining decisions, and checks available during execution. |
| Implementation reviewer | Defects, regressions, and unmet requirements in the actual result and its validation. |

Recommend review scope and timing separately for the plan and implementation. A plan review does
not review future code, select a result review, or determine the implementer's model. A result
review does not substitute for a selected plan review. Distinguish proposed assignments from
user-selected ones; omit unused roles rather than creating a plan or review to fill the table.
Use these recommendations on both formal-plan and direct routes, including plan-only requests
without implying implementation authority. Reassess the implementer when the plan reveals a
materially different execution scope.

Use these corresponding families as starting points for role recommendations:

| Families | Work to consider |
| --- | --- |
| Luna / Haiku | Small, repetitive implementations with complete requirements, an established pattern, and objective checks. |
| Terra / Sonnet | Bounded work that requires interpreting context and resolving local decisions. |
| Sol / Opus | Ambiguity, investigation, or coordination that requires broader judgment. |
| Astra / Fable | Demanding analysis or complex interactions that justify additional reasoning capability. |

These are local routing conventions, not claims of identical performance, capabilities, or effort
settings across models or providers. Other available models remain eligible when adequate for the
particular role; verify suitability rather than treating the table as a universal ranking.

Family names here are version-independent. For a new recommendation or authorized assignment,
resolve each family to its latest version actually available through the intended client, account,
and launch mechanism. Use current authoritative catalog or tool metadata, with provider
documentation when needed, and name the concrete model identifier and supported effort. Do not
infer release order or availability solely from version numbers, a default alias, or this skill's
examples. If the newest announced release is unavailable, use the latest verified available
version and disclose that limitation; if availability is unknown, say so. Honor an explicit
version pin. A catalog establishes available choices, not the acting agent's current settings;
this preference does not upgrade a running agent or authorize a new launch automatically.

For each role, choose the lowest adequate effort supported by that exact model and client.
`high` and `xhigh` are examples, not required levels or a minimum. Consider other supported levels
when appropriate, and do not translate an effort label between providers or invent one for a
client without effort support. A stronger reviewer does not make an inadequate author suitable;
consider the checks and review actually selected, without assuming a review will repair the work.

For example, Terra or Sol can author a plan reviewed by a fresh Sol or Astra agent, while Terra
implements and a separate Sol agent reviews the implementation. Sol can also author a plan
reviewed by another Sol agent when fresh context and the review scope provide independence. A
harder implementation may instead warrant Sol or Astra, independently of the planner or plan
reviewer. Apply the corresponding groups for Claude where available and select effort separately
for every assignment. These examples do not require one reviewer across phases, a stronger model
than every author, or automatic delegation; the existing user choices and execution permissions
still govern assigning agents and invoking reviews.

## Choose the smallest useful agent arrangement

Recommend the simplest arrangement that meets the task's needs. Justify each additional agent by
the work it removes from the principal agent or the focused execution it enables, considering
transferred context, communication, latency, validation, and rework. More agents can increase
total tokens even when their individual model rates are lower; do not promise unmeasured savings.

| Arrangement | When to consider |
| --- | --- |
| Current agent alone | A small task with straightforward execution and verification. |
| Principal with a direct implementer, such as Sol -> Terra or Luna | A bounded delivery that can be delegated without an intermediate coordinator. |
| Principal, coordinator, and implementer, such as Sol -> Terra -> Luna | A package of tasks where the coordinator meaningfully decomposes, checks, and consolidates work, reducing the principal's coordination burden. |

These are examples, not a required hierarchy of model families. Assign a coordinator only when
its responsibility is concrete; forwarding messages alone does not justify another layer. Bound
each implementer's writable scope and follow the entrypoint's rules for shared resources and
parallel work. The coordinator checks actual changes and validation evidence, consolidates the
result, and returns unresolved assumptions or decisions beyond its scope to the principal.
Its checks are part of execution and do not replace a user-selected independent plan or result
review. Nested delegation, like direct delegation, requires authorization covering that work.

Resume the implementer (`followup_task` in Codex) for the same authorized delivery, including
tests and fixes. Reassess the assignment if scope, ownership, or model suitability changes
materially. Start with fresh context when delegating a separate delivery. On handoff, preserve
existing work and transfer write ownership before a replacement edits the same files.

In a chosen plan, record only the selected arrangement and applicable roles: each agent's
responsibility, bounded scope, concrete model and effort, verification criteria, and conditions
for returning a decision to its coordinator. Distinguish proposed from authorized assignments
and keep plan review and implementation review separate. A single-agent plan needs only a brief
assignment; do not add unused roles or create agents to fill a template. On the direct route,
describe the applicable arrangement in the proposal summary without creating a plan artifact.

## Select a reviewer when chosen

Recommend an adequate autonomous-group reviewer for supervised-group work and a fresh reviewer
for complex autonomous-group work. Use [reviews and completion](closure.md) for qualifications,
timing, and evidence. Independent review uses fresh context and the original authorities; a
stronger model name alone does not make it independent. An advisor, author reread, and independent
review are different mechanisms. The author's own validation remains required on every route.

Examples of recommendations:

- A routine autonomous-group fix with one owner and cheap check: direct execution, ordinarily no
  extra reviewer; ask whether the user sees stakes that warrant review.
- A routine supervised-group fix: direct execution and an autonomous-group result review.
- A non-trivial local fix: a compact plan can preserve uncertainty and decisions; an independent
  result review can catch a missed consumer. Ask about both, with direct execution available.
- A shared skill policy or multi-component state transition: strongly recommend a full plan and
  fresh pre-edit and final reviews. Sol xhigh planning with Astra xhigh review is one option when
  available. Opus execution with Sol xhigh review is another when the roles fit.
- A routine mechanical step: propose a supported lower effort once if adequate and the user has
  not chosen to keep the current setting; reassess when the task becomes more critical.
