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

- Read `docs/AGENTS-MAILBOX-PROTO.md` in full before publishing or consuming Baton handoffs. The local deployment supplies the executable and explicit absolute config path; never infer or hard-code either in repository policy.
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

## Confirmed decisions are pinned before implementation

- Baton discussion is coordination EVIDENCE, not the durable specification. A ruling that exists only in a message thread is one context loss away from being re-litigated or silently reversed.
- Before implementing a confirmed product, UX, protocol, or operational decision, write it into the owning `work/finding-*/FINDING.md`, and reflect its queued/in-progress/done state in the applicable `PLAN.md` or umbrella. If no owning finding exists, create one before editing implementation.
- Findings preserve the CHRONOLOGICAL history of decisions; plans and umbrellas name the one that is currently actionable. The two answer different questions — "how did we get here" and "what is true now" — and collapsing them loses whichever the reader needed.
- At implementation start, REVALIDATE the recorded ruling against current code, protocol, and later decisions. If it has changed, append an explicit dated supersession or clarification with its rationale and update the plan. Never delete or rewrite an old decision as though it had never been made: the reasoning that was superseded is how the next reader knows why the current rule is not the obvious one.
- A superseding decision must explicitly mark the old text superseded. Two live rules that contradict each other are worse than either alone, because both look authoritative.
- Implementation and review handoffs reference the exact decision files.
- After a restart or context loss, resume from those repository records — never from memory, and never from a subject line.

This gate exists because a ruled decision was lost: the console's `Enter` behaviour was agreed, never written into its finding, and the implementation later contradicted it. `AGENTS.md` is this rule's one owner; it is agent policy and is not duplicated in the README.


## Review findings tracking (`work/finding-*` folders)

Findings are dedicated folders under `work/`, one per independently
schedulable item: `work/finding-<slug>/`. The goals are that no observation or
decision is lost and that human/reviewer research can prepare queued work
without interrupting the implementer.

- Slawomir and the reviewer normally create, research, prioritize, and queue
  findings. The implementer stays on the current serial item rather than
  spending implementation cycles reconstructing queued decisions.
- A top-level finding owns `FINDING.md`, `PLAN.md`, and implementer-owned
  `PROGRESS.md`. The finding records observed behavior, evidence, decisions,
  and acceptance boundaries; the plan orders current work; progress is the
  implementer's claim of current state.
- Reviewer research should make the next item implementation-ready: include a
  minimal repro/baseline, exact code paths and symbols, confirmed facts versus
  hypotheses, recommended patch boundary, interactions, positive/negative/
  race/retry regressions, focused verification, and unresolved decisions.
  Label uncertain material **Observed**, **Confirmed**, **Inferred**,
  **Proposed**, or **Open**. Reviewer proposals are decision support, not
  authority; the implementer must revalidate them against the current tree.
- Findings are worked serially to completion. Reviewer work may continue on
  queued findings, but the implementer does not switch merely because a queued
  folder changed.
- When starting an item, read its whole folder fresh and re-check every
  captured claim. Earlier work may have resolved or invalidated it. Record an
  explicit resolved/superseded outcome rather than silently deleting stale
  work or reimplementing it.
- Discovery is recursive and role-neutral. Either role may immediately file a
  new defect; filing does not interrupt the serial queue. Human/reviewer still
  own formal enrichment and priority by default.
- A causally tied child lives at
  `work/finding-<parent>/findings/finding-<child>/`, with its own `FINDING.md`,
  `PLAN.md`, and `PROGRESS.md`. The child names its parent/discovery context;
  the parent plan/progress indexes the child and status. Use a top-level
  finding instead when it is independent, separately scheduled, or may outlive
  the parent.
- Do not encode hierarchy/order with dotted names or numeric prefixes. Keep at
  most two child levels. Promote a deeper or independently scheduled child to
  top level and update live references without leaving an alias/stub. A parent
  cannot close while it contains an open child.
- `PROGRESS.md` has one writer: `baton.implementer`. Reviewer input goes into
  FINDING/PLAN, evidence files, or append-only review journals, never progress.
- Each review pass is append-only
  `review-YYYY-MM-DDTHH-MM-SSZ.md` in that finding root (UTC). Never edit or
  delete an earlier review. The implementer records its response and current
  awaiting-review/changes-requested/signed-off state in `PROGRESS.md`.
- Before parallel edits, establish file ownership explicitly. Implementation
  handoffs reference the exact finding, plan, progress, and newest review
  paths discussed.
- Finding folders are ephemeral branch work. After the resolution is committed
  and closed, remove them in the deliberate cleanup pass. Anything that must
  outlive the folder (tests, user docs, durable repository policy) must already
  stand alone elsewhere; no permanent source/test reference may depend on an
  ephemeral finding path.

## Baton defects and workarounds

- Never work around a Baton defect without logging a finding for it first. Log the finding, then a short-term workaround is acceptable — but only as a stated stopgap, never as the fix, and the finding is what carries the real correction.
- This applies with particular force to agents working inside Baton's own source tree. Privileged access to the source and the store lets an agent reach past a gap that every other team hits head-on. Doing so hides the defect, produces a false report of success, and advances nothing: other teams have the CLI and nothing else, and cannot route around what this repository can.
- The finding states what was observed, separates what is genuinely Baton's defect from the agent's own misuse of the tool, and proposes a direction. Filing it is not optional because the workaround happened to be easy.
