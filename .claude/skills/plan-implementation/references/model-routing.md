# Model-aware planning route

Use this after the entrypoint's request, risk, persistence, and inherited-plan checks. Model
capability is a planning aid, never evidence that a safeguard can be skipped. These routes express
the user's preferred level of planning for this shared skill; they are not universal rankings of
model quality.

## Identify the actual session

1. Read model identity and reasoning effort from trustworthy runtime metadata when exposed by the
   client. Do not infer them from writing style, remembered chat claims, a model's self-description,
   or a command that merely lists installed models.
2. If identity or effort is unavailable and knowing it would change an optional plan, reviewer, or
   effort recommendation, ask the user once which model and thinking level this session uses.
   Work on independent read-only discovery while the answer is pending. If no answer arrives in a
   reasonable opportunity, use the conservative compact-plan route for discretionary edits.
   Never treat silence as permission for a consequential write.
3. Prefer runtime metadata over a conflicting user description. State the conflict and ask for
   clarification only if the decision depends on it. Reassess at a task boundary if the client
   reports a model or effort switch. Do not repeatedly ask after identity is established.

Only the user or a supported client control can change the active model or effort. Offer a switch
as a recommendation, not as an action already taken. Verify availability and supported thinking
levels in the actual client before naming one as selectable; otherwise describe the pairing as a
conditional example. Do not block authorized work solely because an optional switch is declined
or unanswered.

## Choose the smallest permitted plan

Apply an explicit plan-only request first. Follow the higher-priority question-only and read-only
rules; this skill does not turn an answer or inspection into implementation. For authorized edits,
first apply high-risk, persistence, external-action, and inherited-plan gates from the entrypoint.
Those gates override every row here. A user's explicit choice to proceed without a discretionary
plan controls when no stronger gate applies.

| Active model | Routine local reversible edit, no persistence trigger | Non-trivial local reversible edit, no persistence trigger |
| --- | --- | --- |
| Terra, Sonnet, Opus | Make a visible formal plan before editing, even if brief. Markdown is required only when the entrypoint's persistence gate applies. | Make a compact formal plan before editing and use its proportional review and closure. |
| Sol, Astra | Execute directly with a stated outcome and cheap check. | Offer one meaningful choice of direct execution or a compact plan. Recommend direct execution for bounded, well-understood work and a compact plan for material uncertainty, coordination, or a likely follow-up. If unanswered after a reasonable opportunity, proceed with the recommended route. |
| Identity unknown | Ask once when route-sensitive; use a compact plan if unanswered. | Ask once when route-sensitive; use a compact plan if unanswered. |

For Terra, Sonnet, and Opus, the default formal plan can be a short visible task plan for trivial
edits; do not create a Markdown file unless persistence applies. This preference covers edits and
implementation, not read-only inspection. A user can explicitly request a direct route for
low-risk, non-persistent work. Never use that choice to bypass mandatory high-risk or persistence
requirements.

When the route is discretionary and the answer would change work materially, ask at the first
planning boundary rather than waiting until after implementation. Give a recommendation and the
reason in one concise question. Ask again only after a material change in scope, uncertainty,
handoff, or model; do not ask for each file, retry, or routine step. When the request already says
to plan or to implement under an approved plan, follow it without a redundant preference prompt.
An optional question is not a new approval requirement for work the user already authorized.

Examples of useful recommendations:

- A well-scoped local fix in Sol or Astra: direct execution with focused validation; offer a
  compact plan when the change has a genuine discretionary coordination cost.
- A novel multi-component design, uncertain state transition, or shared agent-skill policy edit:
  use the mandatory full plan; recommend higher reasoning effort for planning and a fresh
  independent reviewer. Sol planning with Astra xhigh review is one option when available.
- An approved high-risk plan executed by Opus: keep its full gates and, when available, use Sol
  xhigh for independent review. Terra or Sonnet execution can use the same pattern. Different
  model families or providers may reduce correlated blind spots when both are capable.
- A routine bulk mechanical step: recommend a lower-cost model or effort only if the client offers
  it and the mandatory controls still run. Reassess before a newly discovered critical decision.

When proposing a pair, identify **planner or implementer**, **independent reviewer**, effort,
availability condition, and which risk gate the reviewer serves. Ask for a switch only where the
expected decision quality or cost difference matters. User-pinned model and effort choices take
precedence within the client's real capabilities and higher-priority requirements. An independent
review must use fresh context and the original authorities; a stronger model name alone does not
make a review independent.
