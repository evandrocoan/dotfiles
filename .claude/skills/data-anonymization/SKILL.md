---
name: data-anonymization
description: >-
  Anonymize or pseudonymize data by replacing identifying names and values while preserving
  useful content, unless the user requests broader changes. Use for transcripts, records, and
  test datasets that need identity substitutions.
---

# Data anonymization

Replace identifying words and values with consistent fictional equivalents while preserving the
original data's useful meaning and structure. Follow the user's requested scope and explicit
instructions; do not infer permission to publish, commit, or send data elsewhere.

- Identify the people and identifying values in scope. Replace names, personal identifiers,
  contact details, and other details that actually identify them with fictional equivalents.
  Use the same substitute for the same person or value throughout the requested scope; distinguish
  different people where the source distinguishes them. Account for variants, fragments, and
  transcription errors when they refer to the same identifier.
- Preserve other content, words, and numbers. In particular, retain references to health conditions,
  drug use, imprisonment, finances, and other sensitive facts when they do not identify someone
  and the user has not requested their removal. A sensitive subject is not itself a reason to
  rewrite or omit a statement. Preserve negations, roles, events, amounts, and the evidence needed
  for the intended use.
- Preserve ordering, timestamps, segment boundaries, and other structure unless they identify
  someone or the user requests a change. Do not remove meaningful material merely because someone
  who already has the original could recognize it.
- When the user requests broader substitutions, apply that scope explicitly. For example, a request
  to change all spoken numbers includes digits and numbers written as words; a request may also
  include cities, addresses, and animal names. Do not treat an indefinite article as a number.
  Preserve repeated references, arithmetic, ordering, relative dates, and other relationships.
  Retain values the user has authorized keeping when changing them would distort the meaning.
- Prefer targeted substitutions over rewriting sentences. Preserve non-identifying facts,
  negations and conversational evidence, and keep previously substituted values consistent when
  revising an existing candidate. Do not change an already fictional value merely to change it
  again, unless the user requests that or it corrects a demonstrated inconsistency.
- Check substitutions in context for consistency, remaining identifying values, and accidental
  changes in meaning. Include relevant fields and metadata, not just visible narrative text.
  Report uncertainty honestly; do not describe pseudonymization as proven irreversible anonymity.
- Check unapplied or ambiguous suggestions and residual numeric forms against the requested scope;
  automated pattern checks and model responses alone do not prove contextual coverage. Keep
  unresolved cases visible instead of silently counting them as complete.
- Keep originals and any identity mapping out of outputs unless specifically required and
  authorized. Avoid disclosing original identifiers in logs, diagnostics, or examples. When an
  identifier cannot be replaced without changing meaning, surface the concrete limitation rather
  than silently deleting the surrounding facts.
