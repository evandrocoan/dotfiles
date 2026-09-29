# Model-aware planning route

Use this after the global model/effort gate and the entrypoint's request, risk, persistence, and
inherited-plan classification. Group labels express planning and review recommendations, not a
universal ranking of model quality or permission to skip safety checks.

## Apply the acting-role gate

Verify the acting model and effort, and assess fitness for this role under the global task-entry
gate. An unknown or inadequate setting holds the role. A plan or reviewer cannot make an
insufficient acting setting adequate. Reassess role fit for every new request; an earlier task's
adequacy decision does not carry to a different role. Verify model and effort availability in the
actual client before proposing a pair.

## Recommend a route and ask for the user's choices

An explicit plan-only request selects a plan and stops before implementation. Question-only and
read-only requests do not open an implementation choice. For an authorized edit, classify risk and
persistence first. They determine the strength of the recommendation and author closure, while
the user decides independently whether to have a formal plan and a separate AI review.

| Acting group | Routine local reversible edit | Non-trivial local reversible edit |
| --- | --- | --- |
| Supervised: Terra, Sonnet, Opus | Recommend direct work and an independent result review. Ask about review; offer a plan if the user wants one. | Recommend a compact plan and independent result review. Ask separately about each. |
| Autonomous: Sol, Astra, Fable | Recommend direct work without a separate reviewer when owner and check are clear. Ask whether the user's sense of importance warrants review; offer a plan if requested. | Recommend direct work or a compact plan according to uncertainty, coordination, and the user's stakes. Recommend an independent result review and ask separately. |
| Identity or effort unknown | Obtain the effective setting before task work. | Obtain the effective setting before task work. |

For high-risk architecture, protocol, security, authorization, migration, or costly validation,
strongly recommend a full persistent plan and qualified pre-edit and final independent reviews.
For lower-risk work likely to cross phases or sessions, recommend a compact persistent plan;
recommend review according to its actual risk and model route. Explain the concrete reason and
adequate planner, implementer, and reviewer model/effort when recommending a pair. A supervised
implementer often benefits from an autonomous reviewer even for routine work. These recommendations never turn
plan or separate AI review into a compulsory gate. Other authorization, model-fit, validation,
and author-conformance requirements still apply.

Ask at the relevant task boundary, before spending substantial dependent work or reviewer tokens.
Keep the plan and review questions separate. State the classification, recommendation, and why,
then invite the user's sense of importance: the agent may not know the user's stakes. An explicit
choice in the current request or an earlier choice still valid for this scope answers only its
dimension. “Without a plan” does not decline review; “with review” does not choose a plan.
When presenting options, make each answer's resulting route unambiguous, including whether a
plan and review will occur. Do not present accepting both as the only way to continue.

If the user declines either action, continue otherwise authorized work with the chosen route.
If a choice is unanswered, do not create a plan or invoke a separate advisor or reviewer. After
a reasonable opportunity, direct execution may proceed if all independent gates permit it.
Silence never supplies missing model/effort information, authorization, or approval of a linked
plan. A selected pre-edit, pre-write, or final review holds only its dependent phase until it
completes or the user explicitly withdraws it. A declined or unselected review never blocks.

If the user chooses a formal plan, create its linkable artifact, offer the current plan in chat,
and wait for the user's explicit go-ahead before implementation. A plan-only request stops after
the link. Ask again about a new plan or review action after a material change in scope,
uncertainty, handoff, or stakes only when the earlier choice did not cover it. Do not revive a
declined choice automatically during replanning. The user may withdraw a choice for remaining
work; preserve the chronology of actions already completed.

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
