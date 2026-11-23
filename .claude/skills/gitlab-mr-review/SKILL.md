---
name: gitlab-mr-review
description: Review GitLab merge requests and decide which findings warrant publication or must be addressed before merge.
---

# GitLab merge request review

## Load applicable skills

- Read `~/.claude/skills/git-delivery/SKILL.md` for every GitLab MR review.
- Read `~/.claude/skills/test-quality/SKILL.md` before evaluating, creating or running tests.
- Read `~/.claude/skills/gitlab-ci/SKILL.md` when investigating GitLab pipelines, jobs or CI configuration.
- Read `~/.claude/skills/docker/SKILL.md` before choosing or running container-based checks.

Open the actual files before the corresponding work so their instructions are available in context.

## Decide what deserves a comment

Publish findings that help the author decide or act. State what fails or can improve, under which
conditions it matters, what evidence supports it, and the smallest useful correction or next step.
Prioritize observed consequences, affected users or workflows, regression risk and confidence in
the diagnosis. Keep cosmetic preferences and speculation without actionable evidence out of the MR.

Read the current discussions, including the other reviewer's findings. Use the existing discussion
for the same defect. Reply when you can add useful evidence, correct a conclusion or explain a
verified fix. Separate defects may warrant separate discussions even when they share a code change.

When verified on the MR base, say in the opening sentence that the problem already existed before this MR
and cite the evidence. Explain any new exposure or impact caused by the changes. State when the
origin is uncertain. Classify a pre-existing problem as requiring action before merge only when
the MR introduces or materially worsens its impact, or when it prevents meeting an identified,
applicable requirement of this MR. Name that impact or requirement in the comment. Use
`git-delivery` for claims about whether GitLab itself prevents the merge.

## Label automated review comments

Start each published automatic-review finding and substantive reply with exactly one of these
Markdown prefixes. Keep both brackets inside the bold formatting, as shown.

**[Corrigir antes do merge]** A demonstrated problem or unmet requirement needs action in this MR.

**[Corrigir em outra entrega]** A demonstrated problem warrants follow-up. Explain why this MR can proceed.

**[Sugestão opcional]** An improvement has a concrete benefit and remains the author's choice.

**[Preciso de uma resposta para avaliar]** Ask for the specific missing information and say which
review decision depends on it. Report other unverified concerns as gaps in the final summary.

Support findings with evidence from code, a test, or a reproduction. If new evidence changes the
priority, use the new label in the same discussion and explain what changed the assessment.
