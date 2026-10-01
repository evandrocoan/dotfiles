# Model-aware planning route

Use this after identifying the acting model/effort and classifying the request, risk, persistence,
and inherited plan. Group labels express planning and review recommendations, not a
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
| Supervised: Terra, Sonnet, Opus | Recommend direct work and an independent result review. Ask about review; offer a plan if the user wants one. | Recommend a compact plan and independent result review. Offer each independently. |
| Autonomous: Sol, Astra, Fable | Recommend direct work without a separate reviewer when owner and check are clear. Ask whether the user's sense of importance warrants review; offer a plan if requested. | Recommend direct work or a compact plan according to uncertainty, coordination, and the user's stakes. Recommend an independent result review and offer each independently. |
| Identity or effort unknown | Obtain the effective setting before task work. | Obtain the effective setting before task work. |

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
