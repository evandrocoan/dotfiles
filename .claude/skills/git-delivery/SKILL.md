---
name: git-delivery
description: >-
  Prepare or perform safe Git delivery and scoped tracking changes while preserving local work
  and explicit authorization boundaries. Use for commits, pushes, pull or merge requests, remote
  reviews and pipelines, repository issues, or requests to keep planning documents local.
---

# Git delivery

Keep file work in the authorized local working tree. A user-requested commit,
pull request, or merge request authorizes only its routine, in-scope Git steps.

## Establish scope and authorization

1. Read the repository instructions and inspect the current branch, status,
   staged changes, unstaged changes, untracked files, and configured remote.
2. Treat an explicitly requested commit, pull request, or merge request as
   authorization for its routine prerequisites. A commit-only request stays local.
   Opening a pull request or merge request includes the source branch, scoped
   commit, and push. It never includes merging, force-pushing, rewriting
   history, or unrelated changes. A review authorizes no mutations.
3. Creating, correcting, or amending a commit never authorizes a push by
   itself, even when the remote contains an earlier version of that commit.
   Leave the rewritten commit local unless the user requests a pull or merge
   request as the current outcome.
4. Never create another worktree, rewrite history, force-push, rebase, merge, or
   cherry-pick unless the user asks for that operation.
5. Preserve unrelated and pre-existing changes. Do not stage, unstage, discard,
   or include them merely to obtain a clean status.
6. If the requested delivery scope is ambiguous, identify the exact files or
   actions in question and ask before mutating Git state.

Execution plans and discussion briefs are working artifacts. Local persistence,
lifecycle moves, and prior tracking do not by themselves place them in a code or
documentation commit. Include them when the user's explicit commit scope covers
them (including requests to commit all changes or the staged set), or when a
concrete repository requirement makes them part of the requested delivery.
Possible future handoff or audit alone is not such a requirement. For a tracked
plan moved from `active/` to `completed/`, excluding it means excluding both the
old-path deletion and new-path addition. Preserve existing work and index state;
do not unstage, untrack, change ignore rules, or delete documents merely to
omit them from a commit.

## Apply an expressly chosen local-only policy

When the user requests a repository-wide local-only policy for specified plans
or briefs, inspect its existing plan-root convention, tracked files, and
references before changing anything. Add narrow `.gitignore` rules where
needed for the chosen working-document paths, and resolve links from tracked
documents to files that will leave Git. Explain in the plan-root
`README.md` which files remain local, their lifecycle, and that other clones
will not receive them. Do not ignore that README, architecture records,
templates, or other artifacts outside the chosen scope.

Ignore rules do not affect files already tracked. Remove their exact entries
from the index only when the user's request covers that tracking change. Check
for existing staged edits first; do not force a removal over them. Use a
cached-only removal so local files remain, verify each file still exists with
unchanged content and is ignored, and inspect the staged set. Preserve
unrelated staged work.

No current handoff, an uncommitted plan, or an ordinary code commit alone
authorizes this repository-wide transition. If a later commit request clearly
includes the local planning files, honor that scope within the repository's
ignore and authorization rules; ask when its relationship to the local-only
policy is ambiguous before changing Git state.

## Use local and remote tools correctly

- Read, edit, diff, and inspect files in the authorized local working tree.
- Infer GitLab from a GitLab remote URL. For GitLab merge requests, issues,
  reviews, or pipelines, use the available GitLab MCP tools before shell
  commands, HTTP calls, or local credential discovery.
- Use a shell or HTTP fallback only when the GitLab MCP capability is
  unavailable or returns an error, and state why the fallback was necessary.

## Prepare a commit

1. Read every file that will be committed and understand why it changed.
2. Inspect the exact intended diff and staged set. Confirm that it matches the
   requested scope before drafting the message.
3. Before writing, identify the problem or objective, the reason it matters,
   the important implementation or architectural decisions, the resulting
   behavior, and the validation performed. Derive these facts from the changed
   files and task evidence; do not infer intent from filenames alone.
4. Run validation proportionate to the change and report anything that could
   not be run.
5. Write the commit message in English with these rules:

   - Use no conventional-commit prefix.
   - Keep the title concise, descriptive, and at most 72 characters.
   - Separate the title from the body with a blank line.
   - Always include a nonempty body unless the user explicitly requests a
     title-only commit.
   - Wrap body lines at 80 columns.
   - Explain the problem or motivation first, then the consequential design or
     behavior. Include relevant validation when it materially supports the
     change.
   - Explain why the change matters instead of restating the title, listing
     filenames, or mechanically narrating the diff.
   - Do not start the body with "This commit".
   - Never add `Co-Authored-By` or another AI attribution trailer.

6. Treat installed commit-message generators as non-authoritative references.
   Do not run one unless the user asks. Independently derive and verify the
   message from the actual diff even when a generated draft is available.
7. After creating the commit and before any push, inspect the stored message.
   Confirm that its title and body satisfy the rules above and that every claim
   matches the committed diff and validation evidence. Correct the message
   before delivery if it fails this check; never rewrite a pushed commit merely
   to improve wording without explicit authorization.

When drafting a message for the user, present it as a plain-text code block. A
commit-only request stays local; a pull-request or merge-request request
continues through its routine delivery steps.

## Prepare a pull or merge request

1. Read every changed file included in the branch and analyze its architectural
   impact.
2. Write the title and body in Portuguese (Brazil), regardless of repository
   language, unless the user explicitly requests another language.
3. Use a concise, descriptive title with no emoji.
4. Explain the motivation, architectural context, important risks, and relevant
   validation. Describe why the change matters instead of merely listing files.
5. Present a drafted title and description as plain text. Create or update the
   remote request only when the user asks for that outcome.

## Prepare an issue

When creating an issue through a tool that writes a reviewable local draft,
follow the confirmation contract that tool itself states, such as kredmine's
proposal confirmation. It ships with the tool and stays current with its
behavior.

## Verify source evidence before publication

When drafting or updating an issue, pull request, merge request, or review that
cites source code or configuration as evidence, load `documentation` and apply
its [Use immutable source evidence](../documentation/SKILL.md#use-immutable-source-evidence)
section.

Immediately before an authorized remote write, inspect the exact outgoing text,
including descriptions and comments. Verify each source-evidence link's
revision, file, and any line anchors against the content read at that revision.
Apply the documentation skill's handling of moving or unverifiable references
before sending. Repeat this check when the outgoing text changes.

## Use GitLab push options only as a fallback

When GitLab CLI and MCP capabilities are unavailable, create the requested merge
request with GitLab push options. Set the target branch, title, and description
with `merge_request.create`.

Push-option values cannot contain literal newlines. Use the literal `\\n`
escape sequence for a multiline description; GitLab converts it to line breaks.
Never encode line breaks as `%0A`, because GitLab stores that text verbatim.

Later pushes may update an existing merge request through
`merge_request.title` and `merge_request.description`. Prefer an ordinary branch
update or the GitLab MCP/API for metadata changes. Never rewrite history only to
change merge-request metadata.

## Report delivery

Report the local branch, commit when one was created, validation performed, and
any remote action taken. State explicitly when changes remain local, uncommitted,
or unpushed.
