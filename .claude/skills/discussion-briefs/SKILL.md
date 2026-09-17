---
name: discussion-briefs
description: >-
  Write and iteratively refine a Portuguese working document that explains several open points
  the user must understand, discuss, or decide, instead of listing them in chat. Use when a status
  report, plan, review, or investigation leaves several pending decisions or points that need
  explanation, when the user asks for such a document, or when refining an existing brief. Do not
  use for a single quick question, for the implementation plan itself, or for a durable
  architecture record.
---

# Discussion briefs

A long chat list of pending points forces the user to request clarification item by item, and the
refined understanding ends up scattered across the conversation. A discussion brief replaces that
list with one file that is rewritten until every point is understood and settled. The brief holds
the current state of the discussion, never its history.

## When to write a brief

Write or update a brief instead of a chat list when either condition applies:

- several points need the user's decision, authorization, or understanding; or
- a point cannot be explained in a sentence or two to someone who has not followed the work.

Answer a single quick question, a routine progress update, or a yes-or-no confirmation directly in
chat. Keep one brief per subject and keep updating it while the subject remains open. Add new
pending points on that subject to the existing brief rather than to chat or to a second file.

## What a brief is not

The brief is a working document written in Brazilian Portuguese. It is not an architecture index,
plan, ADR, or decision record, and it is not an implementation plan, so the English-only rule for
architecture artifacts does not apply to it. Never title or describe it as a "registro de decisão".

It stays outside the authority order of approved decision, persistent plan, task plan, and chat.
It never replaces a plan or record that the task's governing instructions require. When the brief
disagrees with its plan or record, correct the brief.

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

When the repository defines another implementation-plan location, use a `briefs/` directory beside
its plans. Reuse the slug of the plan that the brief feeds when there is one. When establishing
`briefs/`, add a sentence to that root's `README.md` defining it as Portuguese working documents
that hold no execution authority. When that README does not exist, first create it as
`plan-implementation` requires, so that skill's definitions are never left missing.

Follow the repository's tracking rules. Do not stage or commit the brief by default, and report
whether it is tracked, untracked, or ignored. Never use `/tmp` or another automatically cleaned
location. Use a remote document or artifact instead of the local file only when the user asks.

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

Reuse the identifiers of the governing plan or record, such as a stage or requirement ID, so the
brief maps back to it; otherwise number items sequentially, such as `D1`. Never renumber an item or
reuse an identifier. Give every identifier, acronym, component name, and merge-request or issue
number used in the brief a one-line plain-language definition in its glossary.

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
when the item must change, and say that the brief is pending that update. Apply pending updates at
the next instruction that permits edits. When you create a brief, tell the user once that an
instruction such as "explique melhor o D2 no documento", or a doubt written inside the file
followed by "refine o brief", updates the file in the same turn.

## Record decisions and promote them

Mark an item `decidido` only from the user's explicit statement, given in chat or in an edit to the
brief that the user asked you to process. Your recommendation, the user's silence, and a question
about an option are not decisions. Name each newly recorded decision in the chat reply so that a
misreading is caught at once.

Promote each decision to its authoritative owner, such as the implementation plan, architecture
record, issue, code, or configuration, under that owner's skill and language rules. Then reduce the
brief item to the decision in one or two sentences plus a link to where it was recorded, and move
it to the template's closing section so that open items stay on top. When no owner exists yet, say
so in the item; a later plan must absorb that decision before work depends on it.

## Keep chat a projection

After creating or updating a brief, the chat message gives the link to the file, how many items
remain open, what changed in this round, and the one decision that would unblock the most. Do not
paste the items into chat unless the user asks.

## Close the brief

When every item is decided or dropped and each decision is promoted, set the brief's state to
`concluído` and tell the user. Keep the file; remove it only when the user asks.
