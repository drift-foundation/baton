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
- Run exactly one active readiness path per participant — never two concurrent
  `wait`s for the same address. Two consumers need two participant addresses,
  not one shared identity. Process every claim immediately with `reply` or
  `close`.
- `wait` is read-only: it blocks until work is ready, reports the deterministic
  head message (healthy or damaged) or the presence of a notice, and creates no
  claim or seen receipt. An active agent keeps one `wait` armed, polls its
  terminal, then explicitly uses `claim --message-id` for directed work or
  `see` for notices. Re-arm `wait` after every result. Never leave a successful
  readiness result unattended; terminal completion may not itself schedule a
  new model turn.
- The SQLite instance is the only coordination authority. Never mutate it with raw SQL or manually reconstruct protocol state. Never read it directly either: if a question about the mailbox can only be answered by opening the store, that inability is the finding.

## Baton defects and workarounds

- Never work around a Baton defect without logging a finding for it first. Log the finding, then a short-term workaround is acceptable — but only as a stated stopgap, never as the fix, and the finding is what carries the real correction.
- This applies with particular force to agents working inside Baton's own source tree. Privileged access to the source and the store lets an agent reach past a gap that every other team hits head-on. Doing so hides the defect, produces a false report of success, and advances nothing: other teams have the CLI and nothing else, and cannot route around what this repository can.
- The finding states what was observed, separates what is genuinely Baton's defect from the agent's own misuse of the tool, and proposes a direction. Filing it is not optional because the workaround happened to be easy.
