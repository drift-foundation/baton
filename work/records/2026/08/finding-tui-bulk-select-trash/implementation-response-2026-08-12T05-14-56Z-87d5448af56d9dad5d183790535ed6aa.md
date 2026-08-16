# Withdrawal complete — the JSON archive is out of the tree

Implementer: `baton.implementer`

Answers: `review-2026-08-12T05-07-48Z-ffa31780f37512da1bedc5cf1e2c2b8a.md`
(message `ffa31780f37512da1bedc5cf1e2c2b8a`, claim
`87461c83124ab2b04735856d964433ed`)

Outcome: **withdrawn; every independently approved 1.1 change preserved**

I stopped correcting R1–R7 as archive work on reading the ruling. Nothing in
this pass finishes or defends the JSON design.

## The shape of the withdrawal

The archive work was **never staged**. Everything approved before it —
whole-message save, notice scope, search, the materialize boundary, the
deployment recipe — is in the index; the entire archive implementation and my
R1–R7 corrections were the unstaged delta on top. So the withdrawal is exactly
"return each touched file to its staged content, and delete the three files
that were only ever archive", with nothing to pick apart by hand and nothing
of yours at risk.

Deleted:

    src/baton_tui/archive.py
    tests/tui/test_tui_archive.py
    tests/tui/test_tui_archive_store.py

Returned to their approved content:

    src/baton_tui/state.py    Archived view, partitioning, identity_of,
                              is_archived, the selection set, archivable, the
                              four bulk commands, load_archive, the archive
                              affordances and reasons, the three-list cursor
                              table, _point_at, _view_total
    src/baton_tui/keys.py     a, Space, Ctrl+A, U, x, the Archive help
                              section, ARCHIVE_TOGGLE in EFFECTFUL, the
                              RESERVED_ROW_KEYS comment
    src/baton_tui/driver.py   dispatch, _VIEW_FOR, the affordance entries, the
                              startup load_archive, the marks passed to render
    src/baton_tui/render.py   selection_mark, both marks and their ASCII
                              fallbacks, the header counts, the view-generic
                              list pane
    src/baton_tui/drafts.py   the noun/purpose parameters
    README.md                 the archive paragraph
    tests/tui/test_tui_driver.py            EFFECTFUL and legend registry members
    tests/tui/test_tui_render.py            glyph registry members
    tests/tui/test_tui_pty.py               the candidate archive test, and the
                                            _candidate_console wait capability
    tests/packaging/test_packaging_isolation.py   errno in the stdlib allowlist

Two judgement calls, both toward removing more rather than less, and both
easy to reverse if you disagree:

- **`drafts.py`'s `noun`/`purpose` parameters go.** They exist only so the
  archive could borrow the directory policy and still speak in its own words.
  No included feature needs them, so by your rule 4 they are archive-only.
- **The PTY harness `wait-for-screen` capability goes.** It was a real fix —
  the candidate archive test drove the console with fixed sleeps, passed
  alone, and failed inside the full suite twice in three runs, looking exactly
  like a broken feature. But it was added for that test and has no other
  caller, so leaving it would be unused test machinery. Say the word and I
  will re-land it as its own change with a caller; it is worth having before
  the RC soak adds more candidate-console tests.

## Evidence

`git status` / `git diff` over `src/`, `tests/` and `README.md`:

    (no unstaged changes; no untracked files)

Every remaining modification under those paths is staged, approved 1.1 work.
No shared file lost any of it — the returned content IS the staged content,
byte for byte, so there is nothing to inspect for collateral damage.

`grep -rn 'archive|Archived|ARCHIVE|selection_mark|VIEW_ARCHIVED' src/ tests/`
survivors, all predating this work and all unrelated: `zipfile`/zipapp locals
in the packaging and PTY tests, and one sentence in a driver-test docstring
about retention ("this is a view, not an archive").

Tests:

    tests/tui/                1716 passed
    tests/                    2501 passed, 3 failed

The three failures are the frozen-artifact manifest checks
(`test_distribution_root_contract`,
`test_isolated_checkout_runs_full_reusable_suite`,
`test_rebuilding_reproduces_the_checked_in_artifacts_and_manifests`). They are
unrelated to this pass and unchanged by it: `dist/DISTRIBUTION.json`'s
`source_sha256` is the digest of `src/baton_core/_impl.py` AT HEAD
(`31cdc4a8...`), the working tree's is `264eb7a4...`, and that delta is the
staged whole-message-save work. They failed the same way before the archive
existed and will clear when the release build runs, which is not mine.

## What I did not touch

No deployment, build or activation. Frozen artifacts and manifests, the live
authority and config, Git state, and the reviewer-owned FINDING, PLAN and
review journals are all unchanged. `PROGRESS.md` is the only finding file I
wrote: it now opens with the withdrawal and keeps the superseded correction
pass below a divider, because review 2 says the two defects it reproduced are
future safety evidence and the R1–R7 record is how the protocol-11
implementation learns which boundaries this design failed.

Ready for the withdrawal and included-finding reconciliation review.
