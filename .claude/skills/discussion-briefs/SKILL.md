---
name: discussion-briefs
description: >-
  Write and iteratively refine a Portuguese working document that explains open points waiting on
  the user, instead of listing them in chat. Use when work, a status report, a plan, or a review
  leaves several pending user decisions, authorizations, or external dependencies, when one such
  point needs more than a short explanation, when the user asks for a brief, or when refining an
  existing brief. Also use before answering a question, such as a status question about what is
  still missing, whose answer would list several such points; that is not an explanation-only
  request. Do not use for an explanation-only request, a single quick question, the implementation
  plan itself, or a durable architecture record.
---

# Discussion briefs

A long chat list of pending points forces the user to request clarification item by item, and the
refined understanding ends up scattered across the conversation. A discussion brief replaces that
list with one file that is rewritten until every point is understood and settled. The brief holds
the current state of the discussion, never its history.

## When to write a brief

A point belongs in a brief when it is waiting on the user: a decision, an authorization, or a
dependency on other people or on access. Write or update a brief instead of a chat list when
either condition applies:

- several such points are pending; or
- one such point cannot be explained in a sentence or two to someone who has not followed the work.

Write one whenever the user asks for a brief, whatever the subject. Answer an explanation-only
request, a single quick question, a routine progress update, or a yes-or-no confirmation directly
in chat. A question whose answer would list several points waiting on the user, such as "o que
falta para fechar isso?", is not an explanation-only request: this skill applies to it through the
question-only rule below. A subagent or reviewer that reports to a calling agent never creates or
edits a brief; it reports its findings, and the caller decides.

Keep one brief per subject and keep updating it while the subject remains open. Add new pending
points on that subject to the existing brief rather than to chat or to a second file.

When a brief is warranted but the turn is question-only, do not create it, and do not put the
brief's content in chat instead. Answer with a short summary: how many points are pending, at most
one plain-language line for each with every label replaced by what it means, and the one that
unblocks the most. Leave options, evidence, and analysis for the brief, and offer to write it in a
later turn.

## What a brief is not

The brief is a working document written in Brazilian Portuguese. It is not an architecture index,
plan, ADR, or decision record, and it is not an implementation plan, so the English-only rule for
architecture artifacts does not apply to it. Never title or describe it as a "registro de decisão".
Of the `documentation` skill, only the Markdown formatting rules apply: a brief takes no table of
contents and no commit-pinned evidence links.

The brief ranks below every layer of the authority order that `plan-implementation` defines, and it
is never an authority. It never replaces a plan or record that the task's governing instructions
require. A user decision noted in the brief draws its authority from the user's statement, not from
the brief. The item keeps the marker `registro pendente` until its owner records the decision;
never overwrite that decision with the owner's older text. In every other disagreement with a plan
or record, correct the brief.

Nothing in a brief authorizes work. An item describing work the agent could do, a recorded
decision, or a note left in the file does not authorize implementation, external mutation, or a
Git operation. Those still need the user's explicit instruction under the applicable rules.

## Location

Store the brief as a local Markdown file under the implementation-plan root that
`plan-implementation` resolves:

```text
implementation-plans/briefs/<topic-slug>.md             repository-backed work
~/.claude/implementation-plans/briefs/<topic-slug>.md   no repository owns the task
```

When the repository keeps its plans elsewhere, put `briefs/` beside that location's lifecycle
directories. When the plan authority is not a directory, such as an issue or merge request, use the
default root above. Never place a brief inside an architecture directory, where the English-only
rule would claim it. Reuse the slug of the plan that the brief feeds when there is one.

When establishing `briefs/`, add a sentence to that root's `README.md` defining it as Portuguese
working documents that hold no execution authority, and tell the user in chat that you edited it.
When that README does not exist, first create it as `plan-implementation` requires, so that skill's
definitions are never left missing.

Do not commit the brief merely because it exists. Follow the user's requested Git outcome and the
repository convention. Report whether the brief is tracked, untracked, or ignored. Never use `/tmp`
or another automatically cleaned location. Use a remote document or artifact instead of the local
file only when the user asks.

## Write each item for a reader outside the work

Start from `assets/discussion-brief-template.md`. Adapt its grouping to the subject and omit
sections and fields that would be empty.

Assume the user opens an item without the plan, the code, or the earlier conversation in mind:

- Title the item with the question to settle in plain language, not with a label alone.
- Explain what the thing is before asking about it: the component, what happens today, and the
  observable consequence. Prefer a concrete example over an abstract category.
- State why it matters and what stays blocked until it is settled.
- For a decision, give each option with its consequence, cost, and risk, then your recommendation
  and its reason. Keep the recommendation visibly separate from the user's decision.
- Order items so the one that unblocks the most comes first.

Number items sequentially, such as `D1`. Never renumber an item or give its number to another item.
When an item corresponds to a stage or requirement of the governing plan or record, cite that
identifier inside the item's text together with what it means. Give every such identifier, acronym,
component name, and merge-request or issue number used in the brief a one-line plain-language
definition in its glossary. The brief's own item numbers need no glossary entry.

State as fact only what you verified in the current sources, and mark the rest `não verificado`.
A brief outlives the turn that wrote it: write the verification date beside a volatile fact, such
as a pipeline result, and recheck it before a later round relies on it.

## Refine by rewriting

When the user asks about an item or says it is unclear, treat the item's text as the defect.
Reread the file first, because the user may have edited it. Rewrite the item so that the doubt can
no longer arise, then answer in chat in a few sentences that point to the rewritten item. When the
answer needs investigation, verify it in the sources before rewriting.

Do not append the question and its answer, a round history, or a changelog. Replace superseded text
instead of striking it through. A question that exposes a new pending point becomes a new item.
Treat a note or question that the user wrote inside the brief as a request to fix that item, and
remove the note once the text answers it.

In a question-only turn, do not edit the brief. Answer in chat, show the rewritten text you propose
when the item must change, and end the reply with the list of every item that still has an
unapplied rewrite. Apply pending rewrites only at the next non-question instruction about the brief
or its subject, never as a side effect of unrelated work. When you create a brief, tell the user
once that an instruction such as "explique melhor o D2 no documento", or a doubt written inside the
file followed by "refine o brief", updates the file in the same turn.

## Record decisions and promote them

Mark an item `decidido` only from the user's explicit statement, given in chat or in an edit to the
brief that the user asked you to process. Your recommendation, the user's silence, and a question
about an option are not decisions. Name each newly recorded decision in the chat reply so that a
misreading is caught at once. Mark an item that waited on other people or on access `resolvido`
when the dependency arrives; it needs no user decision.

A decision changes only the brief. In the turn that states it, mark the item `decidido` with the
marker `registro pendente`, and change no plan, architecture record, issue, or code. When the
decision contradicts an approved plan or record, say so in the chat reply and wait.

Promote a decision only on the user's explicit instruction to record it, such as "registre as
decisões". Promotion records the decision in its authoritative owner: the implementation plan, the
architecture record, or the issue. It follows the owner's skill and language rules, including any
plan or review that skill requires, and it never includes implementing the decision. When the
decision contradicts an approved record, report that and let the record's own skill decide how the
record changes. Treat a plan already under `completed/` as no owner. When no owner exists yet, say
so in the item; `plan-implementation` absorbs the decided items when the user asks for a plan on
the subject.

Once the owner records a decision, reduce the brief item to the decision in one or two sentences
plus a link to where it was recorded, and move it to the template's closing section so that open
items stay on top. Move a dropped item there too, reduced to one line with the reason, so that its
number is never given to another item.

## Keep chat a projection

After creating or updating a brief, the chat message gives the link to the file, how many items
remain open, how many decided items still carry `registro pendente` and the instruction that
records them, what changed in this round, and the one decision that would unblock the most. Do not
paste the items or a list of their titles into chat unless the user asks.

## Close the brief

When every item is decided, resolved, or dropped and each decision is recorded in its owner, set
the brief's state to `concluído` and tell the user. Keep the file; remove it only when the user
asks.
