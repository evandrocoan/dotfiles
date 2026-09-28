# Implementation plans

`active/` contains planned, in-progress, blocked, or otherwise unresolved work. `completed/`
contains plans whose risk-appropriate closure verdict passed.

Move the same plan file from `active/` to `completed/` when it is complete; do not retain a
duplicate. Use concise lowercase hyphenated filenames. These plans are temporary execution
authority, while durable cross-component decisions belong in architecture records. The workflow
rules of the shared agent skills are the exception: they live in the skills themselves.

`briefs/` contains Portuguese working documents written under the `discussion-briefs` skill. They
explain open points to the user and hold no execution authority.

`evidence/<task-slug>.md` is optional local support for concise findings and source pointers
that would overfill a plan. It holds no current instructions, raw logs, or complete plan copies;
the active plan remains the execution authority.

Direct Markdown files in `active/`, `completed/`, `briefs/`, and `evidence/` are local working documents.
They are ignored by Git and do not accompany another clone. This README and the local
`.gitignore` remain shareable so each clone uses the same convention.
