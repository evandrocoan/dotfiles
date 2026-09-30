# Persistent implementation plans

When the repository defines a current implementation-plan convention, follow it. Otherwise use
this default root for repository-backed work:

```text
implementation-plans/
├── .gitignore
├── README.md
├── active/
└── completed/
```

Create a formal plan only after the user's advance choice or explicit request; record this basis
in the artifact. Risk, persistence, or handoff alone recommends a plan but never creates one.
Every chosen formal plan needs a complete
artifact that can be linked in chat for user review before execution. Use the current lifecycle's
Markdown file when the task-plan UI cannot link to its complete current plan. This also applies to
a user-requested routine plan or another formal plan without an independent persistence trigger.
Creating a file solely for the link does not change the task's risk classification, plan detail,
review recommendation, or author closure requirements. Record the user's separate response to the
linked plan before executing it; neither the original implementation request nor silence supplies
it.
For a plan created before the advance-choice rule, preserve its real chronology and ask before a
future material replan or uncovered reviewer invocation. A declined future review does not block
the plan's otherwise authorized steps. Status and lifecycle updates alone do not
retroactively create a plan or require inventing earlier consent.

A `briefs/` directory beside these holds `discussion-briefs` working documents when that skill
establishes it. Before planning, read a brief there on the same subject and absorb the items the
user decided into the plan's authorities and evidence, in English. A brief supplies user decisions
only; it holds no execution authority and is not evidence of current behavior.

An optional `evidence/<task-slug>.md` beside the lifecycle directories holds concise local
findings and source pointers when they would overfill a plan. Do not create the directory without
such a need. It is ignored by default and never owns current obligations, complete plan snapshots,
or raw logs. Keep the current contract in the active plan and executable evidence in its source.

When establishing a new default root, including when `discussion-briefs` establishes it first,
create `implementation-plans/.gitignore` with these rules:

```gitignore
/active/*.md
/completed/*.md
/briefs/*.md
/evidence/*.md
```

These rules keep default plans and briefs local while leaving the root `README.md`, `.gitignore`,
and files outside those Markdown paths visible. Architecture records and templates stay in their
own locations. Account for any parent allowlist so the README and `.gitignore` can be tracked when
Git delivery is requested.

Do not apply this default retroactively to an existing root as a side effect of planning; follow
its current convention unless the user explicitly requests a tracking change for that repository.
Ignore rules do not untrack existing files, and creating the root does not authorize index changes.

Create `implementation-plans/README.md` when establishing this root. If the default root already
exists without that file, add it before the next plan is created, moved, or closed. Keep the README
concise and require it to define:

- `active/` as the location for planned, in-progress, blocked, or otherwise unresolved work;
- `completed/` as the location for plans whose risk-appropriate closure verdict passed;
- moving the same file between lifecycle directories without retaining a duplicate;
- the repository's plan naming and any additional lifecycle states; and
- the boundary between temporary execution authority and durable architecture records.

When the optional evidence convention is used, explain its local, non-authoritative role in that
README. Do not present `history/` full-plan snapshots as a default lifecycle directory.

For a new default root, also explain that the ignored plans and briefs remain in the local
checkout across lifecycle moves but are not delivered to other clones. The README and ignore
rules remain shareable.

Do not maintain a manual inventory of individual plans in the README; the plan files present in the
lifecycle directories are the inventory and cannot drift from a copied list. Place an active
repository-backed plan at:

```text
implementation-plans/active/<task-slug>.md
```

Use [`../assets/compact-implementation-plan-template.md`](../assets/compact-implementation-plan-template.md)
for chosen persistent non-trivial local work, bounded additive external actions, and editorial
corrections that independently warrant persistence.
Recommend [`../assets/implementation-plan-template.md`](../assets/implementation-plan-template.md)
for high-risk or architecture-governed work; honor the user's choice of a shorter format. Use a
concise lowercase hyphenated task slug. Keep one
active file for one delivery objective; do not create a new file for every retry or replanning
event.

When using the default lifecycle, close a successfully completed plan by moving the same file,
after its final conformance verdict passes, to:

```text
implementation-plans/completed/<task-slug>.md
```

Preserve the completed plan as the final execution contract; do not copy it or leave another copy
under `active/`. Update any task-plan, documentation, or brief link that pointed to the active
path. Keep a blocked or unresolved plan under `active/` with its real status unless the repository
defines a separate blocked state.

When no repository owns the task, use the same documented lifecycle under the global root:

```text
~/.claude/implementation-plans/active/<task-slug>.md
~/.claude/implementation-plans/completed/<task-slug>.md
```

Create `~/.claude/implementation-plans/README.md` when establishing that root. Never use `/tmp` or
another automatically cleaned location for a persistent plan. An issue or merge-request description
may replace the local file only when it is the established execution authority and all agents can
read and update it. A chat message or hidden model state never replaces the persistent plan.

Apply this order among planning artifacts:

```text
approved architecture or product decision
        -> persistent implementation plan
        -> task-plan status projection
        -> conversational progress update
```

Resolve disagreement by correcting the lower layer. Never let the task-plan projection silently
override the persistent plan or let the persistent plan override approved architecture. This order
does not grant authorization. The user's authorized request, applicable global and repository
instructions, and task-specific skills constrain every layer. A plan, advisor,
reviewer, open change request, or prior implementation cannot expand scope or waive those
constraints. Honor a specific explicit user choice over skill guidance within higher-priority
limits; do not request the same decision again.
