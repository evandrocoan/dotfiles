---
name: git-delivery
description: Prepare or perform safe Git delivery while preserving local work and explicit authorization boundaries. Use when drafting or creating commits, pushing branches, creating or updating pull requests or GitLab merge requests, reviewing remote changes, working with repository issues, or investigating remote pipelines.
---

# Git delivery

Keep file work in the authorized local working tree. Treat the requested
delivery outcome as authorization for its routine in-scope Git steps, but
nothing beyond it.

## Establish scope and authorization

1. Read the repository instructions and inspect the current branch, status,
   staged changes, unstaged changes, untracked files, and configured remote.
2. Treat the requested delivery outcome as authorization for its routine
   prerequisites. A commit-only request stays local. Opening a pull request or
   merge request includes the source branch, scoped commit, and push. It never
   includes merging, force-pushing, rewriting history, or unrelated changes. A
   review authorizes no mutations.
3. Creating, correcting, or amending a commit never authorizes a push by
   itself, even when the remote contains an earlier version of that commit.
   Leave the rewritten commit local until the user explicitly requests remote
   delivery or requests a pull or merge request as the current outcome.
4. Never create another worktree, rewrite history, force-push, rebase, merge, or
   cherry-pick unless the user asks for that operation.
5. Preserve unrelated and pre-existing changes. Do not stage, unstage, discard,
   or include them merely to obtain a clean status.
6. If the requested delivery scope is ambiguous, identify the exact files or
   actions in question and ask before mutating Git state.

## Use local and remote tools correctly

- Read, edit, stage, diff, and inspect files in the authorized local working
  tree. Never use a remote file or commit API to bypass missing local access.
- Infer GitLab from a GitLab remote URL. For GitLab merge requests, issues,
  reviews, or pipelines, use the available GitLab MCP tools before shell
  commands, HTTP calls, or local credential discovery.
- Use a shell or HTTP fallback only when the GitLab MCP capability is
  unavailable or returns an error, and state why the fallback was necessary.
- Treat remote tools as read-only unless the user requests the
  corresponding remote mutation. A remote URL alone grants no write authority.

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
