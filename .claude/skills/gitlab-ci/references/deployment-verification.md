# Deployment verification

## Verify observed state, not declared intent

Treat successful deployment orchestration, runtime identity, and behavioral health as separate claims. A job that
applied configuration proves only that the deployment command returned successfully. A desired image tag, branch,
Git history, or CI variable does not prove what every live replica is running.

Bind each verification to the exact environment, deployment pipeline, producer job, protected image tag, platform,
and release manifest. Reject an expected target selected only by a moving branch, mutable alias, or user-supplied ref.
Use `environment:action: verify` for a job that accesses an environment without creating a new deployment. Protect the
environment and verifier credentials independently from ordinary branch or merge request jobs.

## Authenticate the complete rollout

Use this order:

1. resolve the environment and intended workload through an authenticated, unambiguous selector;
2. confirm the deployment or rollout has reached its terminal stable state;
3. enumerate every active replica and relevant container, including mixed old and new revisions during rollout;
4. compare each observed protected image tag and CI-supplied OCI metadata with the release manifest;
5. run the smallest useful health or smoke check after identity succeeds;
6. retain bounded diagnostics and return a failing or incomplete status for any unresolved observation.

Never select the first item from an unordered workload list and treat it as the deployment. A missing target, multiple
unexpected workloads, mixed revisions, inaccessible metadata, failed read, or replica that cannot be inspected makes
verification incomplete or failed according to policy, never clean.

## Use content comparison as supplemental evidence

Directly comparing selected runtime files with the exact release source can expose stale or manually modified
containers. Keep the mapping explicit and compare bytes without shell interpolation. However, a few matching files do
not authenticate the complete image or prove runtime behavior. Prefer release-manifest identity, OCI labels, provenance,
and artifact-level tests as the primary contract; use targeted content comparison as a drift diagnostic.

Fail closed when the expected file, runtime file, container, or authenticated release source is absent. Store diffs
only when they cannot reveal secrets or sensitive implementation. Do not print the full environment or read arbitrary
paths from production containers.

## Minimize live-environment authority

- Use read-only metadata and health endpoints when they can prove the contract.
- Treat interactive container execution as elevated live access even when the command only reads a file. Grant it
  only to a protected verifier with narrowly scoped credentials and no deployment mutation permissions.
- Serialize verification with the deployment resource when concurrent rollout could change the observed target.
- Recheck deployment identity immediately before reporting success so a newer rollout cannot inherit a stale result.
- Make mandatory verification a real gate; do not hide drift or incomplete coverage with `allow_failure`.
- Keep scheduled drift checks bound to the environment's recorded desired release, not to the scheduler branch.

Authoritative references: [GitLab environments](https://docs.gitlab.com/ci/environments/), [protected
environments](https://docs.gitlab.com/ci/environments/protected_environments/), and [deployment
safety](https://docs.gitlab.com/ci/environments/deployment_safety/).
