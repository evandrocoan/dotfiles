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
| Autonomous group: Sol, Astra, Fable | Ask once about the user's sense of importance and whether they want an optional independent review. Recommend direct execution without a formal plan and state whether extra review is warranted; do not offer a plan solely for this classification. | Ask once about the user's sense of importance and whether they prefer direct execution or a compact plan. An independent result review is required either way. Recommend and explain the planning route. |
| Identity or effort unknown | Stop and obtain the effective setting before task work. | Stop and obtain the effective setting before task work. |

These are user-selected operational labels for this skill, not a universal ranking of model
quality. The plan threshold and independent-review threshold are separate. The supervised group
retains the pre-model plan route: routine local reversible work needs no formal plan; non-trivial
local reversible work needs a compact formal plan. A user may still request a plan for routine
work. An explicit direct preference can control any discretionary route, but cannot bypass a
mandatory high-risk, persistence, or inherited-plan requirement.

For the autonomous group, ask once at the first eligible boundary for the user's own sense of
importance and any still-open planning or review preference. State the agent's classification,
recommended route, and concrete reason in the same concise question. The agent still owns risk
classification: use new facts from the user to reassess it, and honor the user's desire for more
planning or review even when no risk gate demands it. A preference never waives a mandatory plan,
review, authorization, or acting-role requirement.

For routine local reversible work, explain that a clear owner and cheap local check make a formal
plan unnecessary; ask only whether the user wants an optional independent review. State whether
you recommend that review and why; for a well-understood low-stakes fix, ordinarily recommend no
extra reviewer, while inviting the user to identify importance the agent cannot see. Honor an
explicit user request for a plan, but do not offer one solely for this routine classification. For
discretionary non-trivial work, offer direct execution or a compact plan for user review before
execution; explain why a plan helps when uncertainty, coordination, or later follow-up could lose a
constraint, and why direct execution suffices when those concerns are absent. State that the
independent result review is required on either route. Apply mandatory status to each dimension
separately: name its trigger and never offer to omit it, but still ask an unanswered discretionary
choice in the other dimension. In particular, mandatory review for non-trivial local work leaves
the direct-versus-compact-plan question open. When both plan and review are mandatory, ask only
about additional detail or review and any importance the user sees. Apply the same user-input
principle to eligible external actions without turning the preference question into write
authorization.

Treat planning and review as separate choices. An explicit preference in the current request or
an earlier choice still valid for this scope resolves only the dimension it addresses: “without a
plan” does not decline review, and “with review” does not decide a discretionary plan. Ask only
about unanswered dimensions. When presenting selectable answers, make each label state the full
resulting route, including the plan and review outcome, even if one dimension was already settled.
For optional review on a direct route, use short labels such as “No plan; independent review” and
“No plan; no review”, adapted to the user's language and the client's label limits. Never make the
user infer the combination from the question alone. If review is mandatory, include it in every
eligible plan option rather than offering its removal. A plan-only request already chooses a plan;
ask about optional review when applicable, offer the linked plan, and stop without seeking
implementation permission. Do not ask an implementation preference for question-only or unrelated
read-only requests. If the user chooses a formal plan, offer its link and wait for the user's review
and explicit go-ahead before executing it; after that response, do not ask again for each file or
step. Ask about planning or review preferences again only after a material change in scope,
uncertainty, handoff, model, or the user's stated stakes; do not ask for each retry or routine step.
If an optional preference is unanswered after a reasonable opportunity, proceed with the stated
recommendation.
If that recommendation creates a formal plan, offer its link and wait for user review before
execution. Silence never resolves missing model/effort information, authorization, user plan
review, or an unmet required review.

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

- A well-scoped routine local fix in the autonomous group: recommend direct execution without a
  plan or extra review because the owner and check are clear; ask whether the user wants an
  independent review due to stakes the agent may not see. The supervised group executes directly
  but still needs a reviewer before completion.
- A non-trivial local fix in Sol, Astra, or Fable: ask whether the user wants direct execution or
  a compact plan offered for user review before execution, explain which route you recommend, and
  include the user's sense of importance. Either choice still requires an independent final review.
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
