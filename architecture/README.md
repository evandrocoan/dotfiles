# Architecture records

These records preserve cross-component decisions and invariants. Code and configuration own
executable behavior; tests own regression expectations. Temporary delivery state belongs in the
local implementation plans.

## Index

- [GitLab monitor work ownership](gitlab-monitor-work-ownership.md): superseded predecessor contract for native
  request provenance, ownership and recovery across MR chats.
- [GitLab monitor simple queue](gitlab-monitor-simple-queue.md): implemented monitor-owned FIFO, ordered
  Claude/Codex stages, direct native GitLab tools, passive self-activity observation, historical effect recovery and human holds.

## Lifecycle

Each record owns its lifecycle status. Proposed behavior is not current functionality. Mark a
record implemented only after its required behavior, validation and selected reviews complete.
Preserve superseded records with links to their replacements. Keep current instruction pointers
in the root AGENTS.md and operational commands in the root README.md.
