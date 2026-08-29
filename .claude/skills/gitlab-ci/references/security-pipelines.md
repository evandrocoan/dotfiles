# Security pipelines

## Use a central pipeline without creating a confused deputy

A reusable central security flow can separate consumer scanning from privileged publication:

```text
consumer MR pipeline
  -> scanner produces a GitLab security report artifact
  -> narrow trigger sends non-secret snapshot metadata
  -> trusted downstream handler retrieves that exact artifact
  -> handler validates and publishes an idempotent MR result
```

This pattern keeps the publication credential out of consumer repositories, but the central handler becomes a
privileged deputy. Require all of the following:

- authenticate and allowlist caller projects or groups;
- verify the expected pipeline source and upstream project identity;
- pass only required metadata or typed inputs;
- disable broad variable inheritance and never forward the central credential;
- retrieve the exact upstream pipeline and job artifact, not the latest artifact for a branch;
- use a job token plus explicit cross-project allowlist when its permissions are sufficient;
- otherwise use a narrowly scoped central project or service token, protected from untrusted pipelines;
- mirror downstream status when the security result is a required upstream gate;
- make missing, ambiguous, stale, or inaccessible upstream data fail closed or report incomplete.

## Integrate GitLab security reports faithfully

- Start from the stable official GitLab security template unless the project explicitly accepts a preview template.
- Enable merge request scanning through the supported GitLab security configuration for the target instance. Inspect
  the merged result before replacing analyzer rules.
- Override a generated analyzer job only for a verified need such as stage, file types, exclusions, or version tag.
- Preserve `artifacts:reports`; a scanner exit, upload failure, malformed schema, or missing report is operational
  failure, not proof of no vulnerabilities.
- Keep scanner policy separate from transport and formatting: scanning observes, policy blocks, and publication renders.
- Scope exclusions narrowly. Excluding tests or generated files can hide executable or distributed code and requires
  repository-specific justification.
- Separate fast merge request checks from scheduled full or deep scans. A schedule complements, but does not replace,
  a required change gate.
- Preserve the scanner's exit status and machine-readable report; do not reconstruct verdicts from human-readable text.
- Pin scanner images and central templates to protected release tags under the project's tag-based policy.

Authoritative references: [GitLab SAST](https://docs.gitlab.com/user/application_security/sast/) and [security configuration](https://docs.gitlab.com/user/application_security/detect/security_configuration/).

## Distinguish diff scope from repository posture

Diff-scoped reporting is useful for incremental enforcement, but it cannot establish that the repository is clean.
Define the policy explicitly:

- whether only vulnerabilities intersecting added or modified lines block the MR;
- how renamed, deleted, generated, or truncated diffs are handled;
- whether findings outside the diff are shown separately;
- whether severity, confidence, baseline status, or dismissal affects blocking;
- what happens when the diff or report cannot be fetched completely.

Bind a finding to normalized path and line-range data from the report, then intersect it with authenticated new-side
diff coordinates. Treat unavailable locations and partially returned diffs as out-of-scope or incomplete according
to the explicit policy, never silently as clean.

## Publish merge request results idempotently

- Bind inline positions to the merge request's current base, start, and head identifiers.
- Recheck the head before publication. Do not attach a result for an older snapshot to a newer MR revision.
- Paginate notes, discussions, jobs, diffs, and other list endpoints.
- Use a stable private marker and finding identity to update an existing general note or thread. Do not identify a
  finding by list order.
- Preserve prior discussion when updating an inline finding; avoid adding an identical reply.
- Fall back to one bounded general note when GitLab cannot place an inline comment, while keeping the same finding
  identity and snapshot.
- Escape untrusted analyzer text before embedding it in HTML and keep public output within GitLab size limits.
- Separate publication failure from scan verdict. Retry only the idempotent external effect; do not reinterpret the
  report on retry.
- Separate parsing, diff intersection, identity, formatting, and policy from API I/O. Test valid, empty, malformed,
  stale, paginated, repeated, partially published, and unauthorized cases with representative fixtures.

## Prefer native CODEOWNERS enforcement

Prefer GitLab protected-branch Code Owner approval and merge request approval rules when the target tier and policy
support the requirement. They remain coupled to GitLab's own CODEOWNERS parser, eligibility model, branch protection,
and merge enforcement.

Use a custom CI approval check only for a requirement that native enforcement cannot express or for a verified tier
constraint. Then:

- read CODEOWNERS from the exact upstream commit being evaluated;
- implement GitLab's current path precedence, sections, optional sections, default owners, approval counts, duplicate
  sections, and eligible direct membership semantics rather than a generic glob approximation;
- paginate changed files, approvals, and membership APIs;
- decide explicitly whether every applicable section or any owner must approve;
- reject self-approval or committer approval when project policy forbids it;
- treat missing or malformed CODEOWNERS according to an explicit fail/skip policy;
- bind the decision to the current MR head and fail stale results;
- test parser and API behavior against representative GitLab fixtures.

A job that merely parses CODEOWNERS and exits successfully is not equivalent to enabling Code Owner approval on a
protected branch.

Authoritative references: [CODEOWNERS syntax](https://docs.gitlab.com/user/project/codeowners/reference/), [approval rules](https://docs.gitlab.com/user/project/merge_requests/approvals/rules/), and [protected
branches](https://docs.gitlab.com/user/project/repository/branches/protected/).
