# Baton repository agent rules

## Git usage (strict)

- Use `git` only for reviewing history, status, and diffs (for example,
  `git status`, `git diff`, `git log`, `git show`, and `git blame`).
- Slawomir alone owns the Git index, commits, branches, tags, and history.
  Agents never stage or unstage changes (`git add`, `git restore --staged`,
  and equivalents).
- Agents never perform mutating Git operations, including `git commit`,
  `merge`, `rebase`, `cherry-pick`, `reset`, `checkout`/`switch`, `stash`,
  branch/tag operations, or pushes.
- A request to make the repository “ready,” “clean,” or “committable” means
  prepare and verify filesystem changes, then report the remaining diff to
  Slawomir. It does not authorize an agent to mutate Git state.
- Do not wrap long calls or expressions merely for readability; avoid
  indentation churn, especially in deeply nested code.
- Do not edit existing tests without clear, case-specific confirmation.

## Coordination identities

- Read `AGENTS-MAILBOX-PROTO.md` in full before publishing or consuming Baton handoffs. The local deployment supplies the executable and explicit absolute config path; never infer or hard-code either in repository policy.
- This project's coordination identities are `baton.reviewer` for the reviewer and `baton.implementer` for the implementer. Resolve role-only instructions to those identities; never substitute a participant from another domain.
- Use one stable 32-hex seed and one active consumer path per actor instance. Process every claim immediately with `reply` or `close`.
- The SQLite instance is the only coordination authority. Never mutate it with raw SQL or manually reconstruct protocol state.
