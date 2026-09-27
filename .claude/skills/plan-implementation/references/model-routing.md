# Model-aware planning route

Use this after the global model/effort gate and the entrypoint's request, risk, persistence, and
inherited-plan checks. Model capability is a planning aid, never evidence that a safeguard can be
skipped. These routes express the user's preferred level of planning for this shared skill; they
are not universal rankings of model quality.

## Apply the acting-role gate

Use the global task-entry gate's established acting pair, role-fit decision, and switch request
before choosing a plan route. A declined or unanswered downgrade leaves a sufficient higher
setting in use; an unmet minimum or fixed exact pair holds that role. For the pairings below,
verify selectable models and effort levels in the actual client, or label the example conditional.
A plan or reviewer cannot make an insufficient acting setting adequate.

## Choose the smallest permitted plan

Apply an explicit plan-only request first. Follow the higher-priority question-only and read-only
rules; this skill does not turn an answer or inspection into implementation. For authorized edits,
first apply high-risk, persistence, external-action, and inherited-plan gates from the entrypoint.
Those gates override every row here. A user's explicit choice to proceed without a discretionary
plan controls when no stronger gate applies.

| Acting group | Routine local reversible edit, no persistence trigger | Non-trivial local reversible edit, no persistence trigger |
| --- | --- | --- |
| Supervised group: Terra, Sonnet, Opus | Execute directly with a stated outcome and cheap check, unless the user requests a plan. | Make a compact formal plan before editing and use its proportional review and closure. |
| Autonomous group: Sol, Astra, Fable | Execute directly with a stated outcome and cheap check, unless the user requests a plan. | Ask once whether the user prefers direct execution or a compact plan before execution. Recommend a plan for material uncertainty, coordination, or likely follow-up; otherwise recommend direct execution. |
| Identity or effort unknown | Stop and obtain the effective setting before task work. | Stop and obtain the effective setting before task work. |

These are user-selected operational labels for this skill, not a universal ranking of model
quality. The plan threshold and independent-review threshold are separate. The supervised group
retains the pre-model plan route: routine local reversible work needs no formal plan; non-trivial
local reversible work needs a compact formal plan. A user may still request a plan for routine
work. An explicit direct preference can control any discretionary route, but cannot bypass a
mandatory high-risk, persistence, or inherited-plan requirement.

For the autonomous group, ask at the first planning boundary only for discretionary non-trivial
implementation work when no explicit plan/direct preference applies. Recommend direct execution
for bounded, well-understood work, or a compact plan for material uncertainty or coordination.
Mention that the user may prefer a plan because the task matters to them more than its technical
scope suggests. Offer direct execution or a compact plan **followed by execution**. If the user
asks for a plan only or for approval before execution, present the plan and stop. If the user
chooses plan and execute, continue after planning without a second approval request. Ask again
only after a material change in scope, uncertainty, handoff, or model; do not ask for each file,
retry, or routine step. Do not pose this implementation preference for question-only or read-only
requests, routine edits, or when an explicit or mandatory route already decides it. If an optional
preference is unanswered after a reasonable opportunity, proceed with the stated recommendation.
Silence never resolves missing model/effort information or an unmet role requirement.

## Apply the independent-review threshold

Review requirements do not depend on whether the user chooses a discretionary plan. The
autonomous group needs an independent reviewer from that group for non-trivial local work, whether
executed directly or from a compact plan. The supervised group needs an independent reviewer from
the autonomous group for every implementation edit, including routine local work. An ordinary
read-only reviewer alone does not create a multiple-implementer or handoff persistence trigger.
Qualifying external actions use the timing in [external-action routes](external-actions.md), and
high-risk work keeps its stronger pre-edit and final review gates. Read
[reviews and completion](closure.md) for reviewer qualifications, blocking behavior, and closure.
Do not replace a required independent review with an advisor or the author's reread.

Examples of useful recommendations:

- A well-scoped routine local fix in either group: execute directly with focused validation,
  unless the user requests a plan. The supervised group still needs a reviewer before completion.
- A non-trivial local fix in Sol, Astra, or Fable: ask whether the user wants direct execution or
  a compact plan followed by execution. Either choice still requires an independent final review.
- A novel multi-component design, uncertain state transition, or shared agent-skill policy edit:
  use the mandatory full plan; recommend higher reasoning effort for planning and a fresh
  independent reviewer. Sol planning with Astra xhigh review is one option when available.
- An approved high-risk plan executed by Opus: keep its full gates and, when available, use Sol
  xhigh for independent review. Terra or Sonnet execution can use the same pattern. Different
  model families or providers may reduce correlated blind spots when both are capable.
- A routine bulk mechanical step: ask once to use a sufficient lower effort if the client offers
  it and the user has not chosen to keep the current setting for this scope. Reassess before a
  newly discovered critical decision.

When proposing a pair, identify **planner or implementer**, **independent reviewer**, effort,
availability condition, and which risk gate the reviewer serves. Request a supported downgrade
once when a lower setting is adequate, or an upgrade when the current setting is insufficient.
Honor a sufficient user-pinned choice; resolve an unmet fixed pair or minimum before that role
proceeds. An independent review must use fresh context and the original authorities; a stronger
model name alone does not make a review independent.
