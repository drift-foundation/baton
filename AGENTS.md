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
- Agents may always add tests without case-specific confirmation. This includes
  new test files/functions and additive cases or members in existing exhaustive
  test registries. Editing or weakening an existing test's assertions or
  expected behavior still requires clear, case-specific confirmation.

## Coordination identities

- Read `docs/AGENTS-MAILBOX-PROTO.md` in full before publishing or consuming Baton handoffs. The local deployment supplies the executable and explicit absolute config path; never infer or hard-code either in repository policy.
- This project's coordination identities are `baton.codex` for the reviewer
  (`rview`), `baton.claude` for the implementer (`impl`), `baton.slaw` for the
  approver (`approv`), and `baton.tuner` for final polish (`tuner`). Resolve
  role-only instructions to those identities; never substitute a participant
  from another domain. Every agent launch names both its participant and one
  explicit role it holds.
- Run exactly one active readiness path per participant — never two concurrent
  `wait`s for the same address. Two consumers need two participant addresses,
  not one shared identity. Act on every wake immediately: `claim` the Work
  before executing it, and `pass` or `close` it rather than leaving it held.
- `wait` is read-only: it blocks until actionable state or timeout and creates
  no claim. An active agent keeps one `wait` armed, polls its terminal, then
  acts explicitly — `claim work=` to take Work, `respond`/`accept`/`dispose`
  to answer a directed `@` obligation, `mark-seen` to acknowledge messages.
  Re-arm `wait` after every result. Never leave a successful readiness result
  unattended; terminal completion may not itself schedule a new model turn.
- The SQLite instance is the only coordination authority. Never mutate it with raw SQL or manually reconstruct protocol state. Never read it directly either: if a question about the coordination state can only be answered by opening the store, that inability is the finding.

## Confirmed decisions are pinned before implementation

- Baton discussion is coordination EVIDENCE, not the durable specification. A ruling that exists only in a message thread is one context loss away from being re-litigated or silently reversed.
- Before implementing a confirmed product, UX, protocol, or operational decision, write it into the owning record's `FINDING.md` under `work/records/YYYY/MM/finding-<slug>/`, and reflect its queued/in-progress/done state in the applicable `PLAN.md` or umbrella. If no owning record exists, create one before editing implementation.
- Findings preserve the CHRONOLOGICAL history of decisions; plans and umbrellas name the one that is currently actionable. The two answer different questions — "how did we get here" and "what is true now" — and collapsing them loses whichever the reader needed.
- At implementation start, REVALIDATE the recorded ruling against current code, protocol, and later decisions. If it has changed, append an explicit dated supersession or clarification with its rationale and update the plan. Never delete or rewrite an old decision as though it had never been made: the reasoning that was superseded is how the next reader knows why the current rule is not the obvious one.
- A superseding decision must explicitly mark the old text superseded. Two live rules that contradict each other are worse than either alone, because both look authoritative.
- Implementation and review handoffs reference the exact decision files.
- After a restart or context loss, resume from those repository records — never from memory, and never from a subject line.

This gate exists because a ruled decision was lost: the console's `Enter` behaviour was agreed, never written into its finding, and the implementation later contradicted it. `AGENTS.md` is this rule's one owner; it is agent policy and is not duplicated in the README.


## Review findings tracking (`work/records` dossiers)

**Superseded 2026-08-16 at the schema-14 cutover (checkpoint `6c3519e6`):**
finding dossiers are no longer ephemeral `work/finding-*` folders. A dossier
is a PERMANENT record created at its canonical path and never moved, archived,
or deleted by lifecycle:

```text
work/
  open/
    finding-friendly-name -> ../records/YYYY/MM/finding-stable-name
  records/
    YYYY/
      MM/
        finding-stable-name/
```

- The year/month is chosen at creation and the canonical `work/records/...`
  path does not change when Work changes phase or becomes terminal. The record
  holds the finding, plan, progress, append-only reviews, reproductions,
  scripts, fixtures, data, and other durable evidence.
- Baton Work bindings, messages, handoffs, reviews, and cross-references use
  only the configured repository identity plus the canonical repository-
  relative `work/records/...` path — never `work/open/...`, never an absolute
  checkout path, and never a Git commit as the primary locator.
- `work/open/` is a deliberately maintained human convenience index of
  relative symlinks for sweeping still-open records. Its links are not
  protocol state and carry no lifecycle semantics; unlinking a closed
  record's symlink is later housekeeping and never touches the record.
- Not every lightweight Baton Work needs a dossier or an open symlink. Once a
  dossier exists its canonical record path is the stable binding; later
  corrections to terminal evidence are explicit follow-up history, never a
  silent rewrite or a rename.
- Every finding dossier MUST have exactly one corresponding Work on the
  authoritative Baton ledger, bound to its canonical `work/records/...` path.
  Create the Work and dossier together when possible. If research creates the
  dossier first, create its ledger Work immediately before any further work or
  handoff. A deferred or roadmap finding is parked on the ledger; it is never
  left as an off-ledger folder. The reverse is intentionally not required:
  lightweight Work may still exist without a dossier.
- Remaining `work/finding-*` folders are LEGACY items pending the deliberate
  cleanup audit owned by `work/records/2026/08/finding-next-release/`; no new
  folder is ever created there.

The working process is unchanged by the layout:

- Slawomir and the reviewer normally create, research, prioritize, and queue
  findings. The implementer stays on the current serial item rather than
  spending implementation cycles reconstructing queued decisions.
- A top-level record owns `FINDING.md`, `PLAN.md`, and implementer-owned
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
  record changed.
- When starting an item, read its whole record fresh and re-check every
  captured claim. Earlier work may have resolved or invalidated it. Record an
  explicit resolved/superseded outcome rather than silently deleting stale
  work or reimplementing it.
- Discovery is recursive and role-neutral. Either role may immediately file a
  new defect; filing does not interrupt the serial queue. Human/reviewer still
  own formal enrichment and priority by default.
- A causally tied child lives at
  `work/records/YYYY/MM/finding-<parent>/findings/finding-<child>/`, with its
  own `FINDING.md`, `PLAN.md`, and `PROGRESS.md`. The child names its
  parent/discovery context; the parent plan/progress indexes the child and
  status. Use a top-level record instead when it is independent, separately
  scheduled, or may outlive the parent.
- Do not encode hierarchy/order with dotted names or numeric prefixes. Keep at
  most two child levels. Promote a deeper or independently scheduled child to
  top level as a NEW record with an explicit forwarding note in the old one —
  the old canonical path stays valid history and is never rewritten.
  A parent cannot close while it contains an open child.
- `PROGRESS.md` has one writer: the implementer (`baton.claude`). Reviewer
  input goes into FINDING/PLAN, evidence files, or append-only review
  journals, never progress.
- Each review pass is append-only
  `review-YYYY-MM-DDTHH-MM-SSZ.md` in that record root (UTC). Never edit or
  delete an earlier review. The implementer records its response and current
  awaiting-review/changes-requested/signed-off state in `PROGRESS.md`.
- Before parallel edits, establish file ownership explicitly. Implementation
  handoffs reference the exact finding, plan, progress, and newest review
  paths discussed.
- Anything that must stand alone regardless of the record (tests, user docs,
  durable repository policy) still lives outside it; a record is evidence and
  decision history, not a hiding place for product artifacts.

## The active-work claim (finding-active-work-claim, 2026-08-16)

- No participant starts implementation, review, or other execution owned by
  the Work's Route endpoint before the atomic `claim` operation SUCCEEDS,
  and a competing claim fails closed.
- Route, Handler and Next are three different questions: which endpoint MAY
  claim, which member IS executing, and which endpoint is planned next. The
  claim records the Handler.
- Phase is not orthogonal to the claim. It is a closed scheduler axis —
  `queued`, `active`, `block`, `parked`, and nothing at all once terminal —
  and `active` means exactly "a Handler holds it". Only `claim` reaches
  `active`; a `block` row names the one gate holding it.
- Discussion and planning while unclaimed are fine. A pass releases the
  claim and derives the destination phase from the destination Route
  atomically; the recipient claims explicitly once the Work is ready.

## Baton defects and workarounds

- Never work around a Baton defect without logging a finding for it first. Log the finding, then a short-term workaround is acceptable — but only as a stated stopgap, never as the fix, and the finding is what carries the real correction.
- This applies with particular force to agents working inside Baton's own source tree. Privileged access to the source and the store lets an agent reach past a gap that every other team hits head-on. Doing so hides the defect, produces a false report of success, and advances nothing: other teams have the CLI and nothing else, and cannot route around what this repository can.
- The finding states what was observed, separates what is genuinely Baton's defect from the agent's own misuse of the tool, and proposes a direction. Filing it is not optional because the workaround happened to be easy.
