# Progress — the next release

Owner: `baton.implementer` only. The serial state of 1.1 work, so a reader who
arrives after a restart can tell what is done, what is running, and what is
deliberately not started.

Last updated 2026-08-12, reconciled against each finding's own journal rather
than from memory. Where this file and a finding folder disagree, the finding
folder is the record and this one is the bug.

## Source-approved

Each of these is signed off IN SOURCE. None of them has been built, deployed
or soaked: that is the RC gate below, and it is Slawomir's to open.

- **Scoped-notice authoring** — `work/finding-scoped-audiences/findings/
  finding-tui-notice-scope-picker/`, approved after three passes. `N` asks who
  a notice is for: `*` plus configured team scopes, typing filters, Tab
  completes, Enter submits typed text. The reviewer found both wrong-audience
  defects, and both were the same shape — a missing value whose default is
  "everyone".
- **Editor exit enters send confirmation** — `work/finding-human-console/
  findings/finding-editor-send-confirmation/`, signed off after six passes.
- **`m` boundary repair** — `work/finding-save-message/`, signed off. Anything
  viewable in full is saveable: answered messages, sent messages, seen
  notices. The preview boundary still refuses unreceived content.
- **Whole-message save (`M`)** — `work/finding-save-message/`,
  `review-2026-08-11T23-26-58Z.md`, **source signed off**. This is the
  finding's actual subject, and it is no longer "deliberately not started":
  that line in this file was ten hours stale.
- **TUI metadata search (`/`)** — `work/finding-tui-message-search/`,
  `review-2026-08-11T17-33-45Z.md`, signed off for MESSAGES and Sent.
  Author and subject only; no body read, no claim, no receipt. That sign-off
  named "Archived-view integration" as a remaining gate; the withdrawal below
  removes it, so search's only outstanding gate is Slawomir's trial.
- **Materialize boundary** — `tests/tui/test_tui_materialize_boundary.py`.
- **Config regeneration wording** — `work/finding-config-regen-wording/`,
  corrected in next-generation source and reviewed.
- **Deployment recipe, SOURCE ONLY** — `work/finding-deployment-recipe/`.
  `tools/deploy.py` and its `just deploy` / `just deploy-activate` /
  `just verify-deployment` targets are implemented, tested and reviewed.
  **Nothing has been deployed.**

## Withdrawn from 1.1

- **Bulk selection and archive** — `work/finding-tui-bulk-select-trash/`.
  Slawomir ruled that SQLite is Baton's metastore and must own
  participant-scoped archive metadata, so the participant-local JSON store and
  the 1.1 Archived UI must not ship; the feature is deferred to protocol 11.
  The implementation and its R1–R7 corrections were removed from the tree on
  2026-08-12 and the withdrawal is recorded in that finding's `PROGRESS.md`.
  Its two review journals are kept as future safety evidence, not as
  instructions to finish the JSON design.

## Deliberately not started

- **Reviewer polling reliability** — `work/finding-reviewer-polling-
  reliability/`, deferred from 1.1 by Slawomir. The contract review is done
  and recorded; no implementation is authorized.
- **Notice-wording cleanup** in the direct state method — non-blocking, queued
  by the reviewer as its own delta.

## Current state

Awaiting the reviewer's withdrawal and reconciliation clearance. After it:
Slawomir's human `just deploy DEST 1.1.0`, then soak and testing, then the RC
gate. No agent opens any of those.

## Finding-folder cleanup — 2026-08-12

Nine closed finding folders were removed from the filesystem after commit
`f20d5b2`: `finding-agent-wakeup`, `finding-attach-part-default-type`,
`finding-cli-read-authority`, `finding-effective-baton-guide`,
`finding-mailbox-conventions`, `finding-subject-normalization`,
`finding-project-layout`, `finding-release-version`, and
`finding-scoped-audiences` with its notice-scope-picker child. Each had its
resolution in `f20d5b2` or earlier, an approved or explicitly resolved
outcome, no open child, and no runtime dependency. Git holds every one of
them; nothing was staged, committed or otherwise touched in Git.

Two blockers stopped a wider sweep, both reported to the reviewer rather than
worked around:

- `finding-human-console` and its whole child tree STAY. `tests/packaging/
  test_docs_consistency.py` READS `work/finding-human-console/{FINDING,PLAN,
  TRIAL}.md` at runtime, so deleting the folder breaks the suite. That is the
  exact dependency `AGENTS.md` forbids — a permanent test resting on an
  ephemeral finding path — and clearing it needs a source/test change that
  this cleanup was not authorized to make.
- `finding-protocol-10-umbrella` STAYS. Its `BULK-TRASH.md` carries
  Slawomir's original bulk-selection rulings (`x`/`#`/`A`, the damaged glyph
  moving to `~`, Trash restorable until an explicit Empty Trash) which the
  retained protocol-11 bulk-archive owner does not restate, and its
  `POST-CUTOVER-AUDIT.md` is a live index of what remained after cutover.

One loose end I could not fix here: `tests/core/test_core_references.py` cites
`work/finding-mailbox-conventions` in prose. The test does not read the path
and passes, but the citation now dangles. The rule it quotes lives in
`docs/AGENTS-MAILBOX-PROTO.md` § "File references travel as their own part",
which is where the comment should point.

## Standing constraints

Frozen 1.0 binaries, manifests and the live authority/config remain untouched;
`bin/baton` is `8798de0c…` and `bin/baton-tui` is `24f08cb1…`, both unchanged
since the 1.0.0 gate. Verification uses candidate artifacts built to throwaway
roots.

Three tests are red on one cause, and have been since the first core change of
1.1: the source is ahead of the frozen artifacts, and the CLI manifest pins
`source_sha256`. They are `TestPackaging::test_distribution_root_contract`,
`TestPackaging::test_isolated_checkout_runs_full_reusable_suite` and
`test_rebuilding_reproduces_the_checked_in_artifacts_and_manifests`. They are
EXPECTED until the deliberate 1.1 build, which is a release act nobody has
authorized yet. Full suite after the withdrawal: 2501 passed, those 3 failed.
