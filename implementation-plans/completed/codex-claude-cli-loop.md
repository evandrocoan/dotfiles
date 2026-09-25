# Implementation plan: Add a Codex-supervised Claude CLI mode

**Status:** Completed
**Mode:** Plan and execute

## Outcome

`codex-claude-loop` supports a Codex-supervised mode that invokes Claude Code through its local
CLI, reviews the result, and iterates without requiring a second active chat. The existing
two-session handoff remains available and retains its version-2 file contract. Both shared skill
discovery paths and the global registry describe the supported modes accurately.

## Scope

### In scope

- Route explicitly between a supervised CLI mode and the existing two-session mode.
- Define the supervised mode's invocation, bounded review cycle, state reconciliation, permission
  handling, and stopping conditions without silently broadening the user's work authorization.
- Preserve the existing handoff protocol and move its mode-specific detail to a reference if that
  makes the entrypoint clearer.
- Update the shared registry description and validate the skill package and affected links.

### Out of scope

- Starting an actual Claude implementation task, changing model settings, enabling unattended
  scheduling, committing, or changing an existing handoff file.
- Changing the two-session protocol or its state transitions.

## Governing decisions and invariants

- The user asked for this improvement and an independent Astra xhigh review.
- The canonical skill is `.claude/skills/codex-claude-loop/SKILL.md`; `.agents/skills/` exposes a
  relative symlink. `.codex/AGENTS.md` contains the shared registry description.
- The existing two-session contract uses `protocol: sol-fable-loop/2`; current handoffs must keep
  that meaning, including ownership, pause, cancellation, and recovery rules.
- A skill cannot grant permission for Claude to perform operations beyond the user's request or
  bypass repository instructions, approval prompts, review gates, or Git authorization.
- Codex owns planning, review, and the process handle. Claude owns only the assigned implementation
  turn. A task cannot have simultaneous CLI and two-session implementers. A resumed CLI turn uses
  the exact recorded session ID in the same verified checkout; neither `--continue` nor a name
  search may silently select a session.
- Before launch, Codex must establish that the checkout and Claude's startup customizations are
  trusted for this task. Headless mode skips the trust dialog but can run hooks and load MCP
  servers.
  `--bare` skips those customizations and repository CLAUDE guidance and requires separate API
  authentication; it cannot be silently substituted for the normal route. The launch must use a
  permission mode and tool scope consistent with user authorization, without permission bypass or
  automatic escalation after a denial.
- Every invocation has a finite turn limit and a supervised process deadline; the overall
  implementation/review cycle has a finite iteration limit. The CLI result, session ID, exit code,
  process termination, and working-tree changes must reconcile before another invocation.
- This is high risk because it changes an agent orchestration and authorization boundary.

## Current evidence and assumptions

### Verified evidence

- Before this edit, the skill described only two separate sessions and a shared handoff file;
  its `SKILL.md` had no supervised CLI route.
- The local `claude` CLI is installed. Its help exposes `--print`, `--output-format`, `--resume`,
  `--session-id`, `--model`, `--effort`, and permission controls. The installed binary contains
  `--max-turns`, though local help omits it; the current official CLI reference documents that
  flag and says it has no default bound. Official headless guidance says print mode skips the
  trust dialog and `--bare` omits discovered instructions.
- The repository has unrelated plan and brief changes; this task must preserve them.

### Open assumptions

- A live Claude run is outside the requested skill update. Static and scenario-based reviews can
  validate the skill's decision rules, while actual runtime supervision remains unverified.

## Execution steps

| Status | Step and owners | Material premise | Validation or result |
| --- | --- | --- | --- |
| completed | Resolve Astra xhigh plan findings and obtain its recheck. | Reviewer receives the user request, governing instructions, current skill, and revised plan. | Astra xhigh found no remaining blocking plan gaps after revision. |
| completed | Update the canonical skill and its mode-specific reference; update the registry description. | The existing handoff contract remains intact. | Original handoff body is byte-identical in its reference; new entrypoint and CLI reference are present. |
| completed | Validate metadata, references, symlink, CLI options, and scoped diff. | Installed CLI help, binary flags, and official CLI reference provide static interface evidence. | Validators and links passed; Astra xhigh scenario evaluation passed after its timeout finding was corrected. No live Claude run. |
| completed | Complete author audit and independent Astra xhigh conformance review. | Final diff and validation evidence are available. | Fresh Astra xhigh pass found no blocking omission or scope divergence. |

## Plan review

- **Risk classification:** High risk; the new route changes who launches and supervises the
  implementing agent and must preserve authorization safeguards.
- **Mechanism:** Independent Astra xhigh review; no separate advisor interface is available.
- **Independent reviewer:** Astra xhigh reviewed the initial plan and found the execution contract
  incomplete; its recheck found the revised plan adequate for implementation. Its model differs
  from this implementing Sol session.
- **Applied:** Specify headless startup and permission preflight, task/session/owner binding,
  interruption reconciliation, finite limits, and scenario-based forward evaluation.
- **Rejected:** None.

## Replan conditions

- The CLI cannot enforce a bounded, observable run without bypassing permission decisions.
- The chosen authentication route or inspected startup configuration makes the CLI invocation
  incompatible with the user's task or governing instructions.
- An interrupted run's process or session state cannot be established well enough to avoid a
  duplicate implementer or repeated external effect.
- Moving the two-session contract changes its meaning or breaks existing handoffs.
- The new mode needs a dependency, scheduler, or mutation outside the authorized skill update.

## Completion evidence

- The original two-session body is byte-identical in
  `references/two-session-handoff.md` to the body of the committed skill before this change.
- The skill validator passed through both the canonical `.claude/skills/` path and the
  `.agents/skills/` symlink. The symlink still resolves to the canonical package, and both new
  reference links resolve.
- `git diff --check` passed. The new skill prose was checked against the repository's Markdown
  width convention. The two new references and plan are untracked but admitted by the ignore
  allowlist; unrelated working-tree changes were preserved.
- The installed CLI help confirms print mode, structured output, exact session IDs, model/effort,
  and permission flags. The binary contains `--max-turns`; the official CLI reference documents
  its semantics. No live Claude invocation was run, so actual CLI supervision remains unverified.
- Astra xhigh evaluated ten CLI and handoff scenarios, including false-completion and unsafe-retry
  negative controls. It found that deadline expiry lacked explicit process termination. The CLI
  reference now requires interruption and confirmed termination before partial-work inspection;
  the same reviewer found this resolved. A separate fresh-context Astra xhigh conformance pass
  independently rechecked these paths and found no blocking issue.
- The second reviewer reproduced both skill validators with the system `python3 -B`, confirmed
  symlink, references, allowlist, and diff whitespace. The `scripts/.venv` interpreter lacks
  PyYAML, but that environment was not used for this Markdown skill validation.

## Closure audit

| Status | Requirement | Owner and consumers | Evidence |
| --- | --- | --- | --- |
| verified | Two modes route one authorized task to one implementer. | `SKILL.md`; Codex and Claude. | Mode-selection and active-owner text; existing handoff scenario rejected simultaneous CLI launch. |
| verified | Headless startup and tools cannot silently expand authorization. | `references/supervised-cli.md`; Claude process. | Startup and permission preflight, no automatic `--bare` or bypass; denied-tool and hook scenarios passed. |
| verified | CLI identity, limits, failures, cancellation, and partial effects are reconciled. | CLI reference; Codex process supervisor. | Exact session/root, bounded turns/deadline/iterations, timeout termination, stop rules; failure scenarios and negative controls passed. |
| verified | Codex reviews actual changes before claiming completion. | CLI reference; Codex reviewer. | Independent diff/acceptance check; unsupported success claim rejected in forward evaluation. |
| verified | The two-session protocol retains its full contract and remains discoverable. | Handoff reference; both clients. | Original body byte-identical to committed skill; protocol-v2 resumption scenario passed. |
| verified | Shared discovery, instructions, and scope are consistent. | Canonical skill, symlink, registry, plan. | Both validators, link checks, scoped diff and status; unrelated work preserved. |
| not applicable: the change is AI instructions with no executable CLI wrapper | A live Claude implementation run proves runtime behavior. | No runtime owner added. | The user asked for the skill change and Astra review; static interface and scenario checks apply. Runtime effects remain unverified and are reported. |
| verified | Required fresh-context Astra xhigh conformance review. | Final diff, plan, instructions, validation evidence. | Independent second pass found no blocking defect and reproduced the scoped static checks. |

Scenario-based evaluation must test successful review, denied or missing permission, incorrect
session/root, competing owner, interrupted partial work, malformed or absent result, exhausted
limits, cancellation, repeated findings, unchanged version-2 handoff behavior, and rejection of a
false completion claim or unsafe retry. The evaluation must reason from the final skill text and
realistic task facts, not merely match wording.

- **Architecture to implementation:** The user-requested CLI and legacy modes reach the entrypoint
  and their references; authorization and startup rules reach CLI preflight, bounded invocation,
  and stop paths; protocol-v2 compatibility reaches the preserved reference. The registry and
  symlink expose the same package. Static validation and ten scenario checks cover those paths.
- **Implementation to authority:** The edited canonical `SKILL.md` and new CLI reference implement
  the requested mode. The copied handoff reference preserves its previous contract. The registry
  describes both modes. This plan records the required high-risk review and closure. All are
  authorized by the user's skill-improvement request and applicable shared-skill instructions;
  no Claude run, Git mutation, scheduler, or other external effect occurred.

### Final conformance verdict

- **Verdict:** Passed for the documented skill modes and their static invariants; live CLI behavior
  remains unverified because no Claude task was launched.
- **Second pass:** Independent Astra xhigh review found no blocking omission, contradiction,
  unauthorized path, or protocol regression.
- **Auditor and evidence:** Author pass: source and reference comparison, both skill validators,
  symlink and link checks, CLI interface inspection, scoped diff/status, and Astra xhigh forward
  evaluation. The fresh independent Astra xhigh reviewer read the original user request, global
  and project instructions, applicable skills, plan, complete scoped diff and untracked files,
  then reproduced the static checks and scenario reasoning.
- **Unresolved requirements:** None within the requested skill update.
- **Brief check:** No brief on this subject under `implementation-plans/briefs/`.
