# Implementation response 1 — active-view and persistence boundaries

Implementer: `baton.implementer`

Answers: `review-2026-08-12T00-02-57Z.md` (message `fb28bace69c5561bbba4fadfadaa7322`, claim `bab25b69f49c8f9ddeb79e34aa6f8994`)

Outcome: **all seven corrected; R6 took the review's second option and needs your ruling**

Every point was reproduced against the tree before it was changed, and every
correction is pinned by a test that fails when the correction is removed.
Twelve deliberate breaks were run at the end; each is caught by a named test.

`PROGRESS.md` § "Correction pass — review 1" carries the same material with
the reasoning; this is the handoff.

## R1 — the active view is what every action addresses

`selected` was the MESSAGES row and is now the row of whichever list view is
on screen; Sent keeps its separate read-only path through `selected_sent`.
That one property carries preview, Enter/open, the FIFO warning, `m`, `M` and
the follow-up, because all of them ask it. Two paths needed their own
correction, and both were wrong before Archived existed:

- `_revalidate_action_target` wrote an index within `_all_rows` into the
  MESSAGES cursor. That was the same number only while nothing was filtered
  and nothing was archived. `_point_at` now sets the cursor of the list that
  actually displays the row, and leaves every cursor alone when the row is
  filtered out of both.
- `refresh` restored one cursor. `_list_anchors` / `_restore_list_cursors`
  now capture and restore each list by its own identity, from one `_LISTS`
  table naming the three lists with their rows, cursor and top attributes.

Regressions, all of which deliberately put a DIFFERENT pending row under the
MESSAGES cursor first — with both cursors at zero every wrong-target path
passes by coincidence:

    test_entering_archived_opens_the_displayed_row_not_the_hidden_pending_one
    test_navigating_archived_moves_only_the_archived_cursor
    test_materialize_in_archived_writes_the_displayed_row
    test_whole_message_save_in_archived_captures_the_displayed_row
    test_a_follow_up_from_archived_answers_the_displayed_row
    test_a_filter_in_archived_never_reaches_the_hidden_pending_row
    test_a_poll_keeps_the_archived_cursor_on_its_own_row
    test_the_archived_view_creates_no_notice_receipt_for_a_hidden_notice

The entry test asserts full `dump()` equality across the transition; the
notice test rests the MESSAGES cursor on an UNSEEN broadcast and asserts the
receipt count is unchanged. The poll test archives three notices, puts the
cursor on the middle one and expires the newest underneath it: a clamped
index lands on the wrong row, a restored identity does not.

## R2 — a valid index cannot hide unresolved work

`is_archived` fails open: membership hides a row only if the row is also one
the human could have archived. An entry found ineligible is RELEASED for the
rest of the session, so resolving it later cannot make it disappear as a
delayed consequence of a file the human never saw. Releases leave the file on
the next successful human archive/restore write and by nothing else — never
by the poll, which was promised read-only.

    test_a_valid_index_cannot_hide_a_pending_message
    test_a_valid_index_cannot_hide_a_claimed_message
    test_a_valid_index_cannot_hide_a_damaged_pending_message
    test_a_valid_index_cannot_hide_an_unseen_notice
    test_the_control_an_index_entry_does_hide_a_terminal_message
    test_the_control_an_index_entry_does_hide_a_seen_notice
    test_a_released_entry_is_not_rewritten_by_the_poll
    test_a_released_entry_cannot_re_hide_the_row_when_the_lifecycle_changes
    test_a_released_entry_leaves_the_file_on_the_next_human_write

The damaged case is a real damaged row: an external part published and then
edited on disk, asserted `damaged is True` before the visibility assertion,
so the fixture cannot rot into a healthy row and still pass. The two controls
are there because without them every test above would pass on an index that
never hid anything at all.

**One wording question for you.** R2 ends "keep obligation counts unfiltered
in every view/header". The unresolved count is unfiltered and unaffected by
archiving, and that is pinned. The ARCHIVED header does not PRINT the owed
count, deliberately — nothing in that list can owe a reply, because owing one
is what makes a row ineligible to be there — and the Sent header has never
printed it either. If you meant "print it in the Archived header too", say so
and it is one clause.

## R3 — four keys, four gates

`select`, `select_all`, `select_none` and `archive` are separate affordances
sharing `_selectable` as one source of truth. `Space` asks about the row under
the cursor, `Ctrl+A` about every visible row, `U` about the set, `x` about
whichever it will act on.

    test_ctrl_a_selects_while_the_cursor_rests_on_an_ineligible_row
    test_U_clears_a_selection_after_the_cursor_becomes_ineligible
    test_x_archives_the_selection_while_the_cursor_is_ineligible
    test_select_all_refuses_only_when_nothing_visible_is_eligible

On the order dependence you found: the new tests place the cursor BY
PREDICATE, never by index. Three rows published in the same second are
ordered by id, so `cursor = 2` proves something different between runs —
which is exactly how the first pass's green evidence was produced. The
helpers `_put_cursor_on_the_last` and `_archived_beside_a_pending_row` say so
in their docstrings.

`driver._AFFORDANCE` gained the two new names, so
`test_nothing_advertised_refuses_for_want_of_state` covers them — its
`_LABELS` registry gained `Ctrl+a all` and `U clear` as additive members.

## R4 — filter restoration is view-generic

`_restore_after_filter` now takes anchors for all three lists rather than the
inbox and Sent, so narrowing Archived can no longer strand its cursor past the
end. The live search status counts the ACTIVE view: `_view_total()` answers
per view, because "1 of 40" in a list of three archived rows describes a
mailbox that is not on screen.

    test_filtering_archived_keeps_its_cursor_on_the_row_that_remains
    test_filtering_archived_clamps_its_cursor_when_the_row_stops_matching
    test_the_archived_cursor_stays_in_range_through_accept_and_clear
    test_the_search_status_counts_the_active_view

These assert on the RENDERED screen, not only the model: your report was
precise that reads clamped silently while the renderer marked no cursor row,
so a model-only assertion would have passed on the broken build.

## R5 — the read is checked on the descriptor

`load` opens with `O_NOFOLLOW`, `fstat`s THAT descriptor for regular type and
exact `0600`, and reads `size + 1` bytes taken from the same `fstat`, so
growth is detected rather than truncated to a prefix of a document nobody
wrote. `_checked_target` gained the same mode refusal, which is the check
`save` gets: it will not write through a name that is already world-readable.
`O_NONBLOCK` is set too — the same race can put a FIFO at that name, and a
blocking read-only open would wait forever for a writer.

The `str(error).replace("draft", "archive")` is gone. `drafts.directory` and
`drafts._checked_namespace` take the caller's `noun` and `purpose`, defaulting
to today's draft wording, so nothing about the drafts changed and the archive
speaks in its own words. Rewriting a word in a finished message also rewrites
any path inside it.

    test_a_world_readable_index_file_is_refused_on_read_and_on_write
    test_a_symlink_swapped_in_after_the_name_check_is_not_followed
    test_a_fifo_swapped_in_after_the_name_check_does_not_hang_the_console
    test_a_file_that_grows_after_its_size_is_checked_is_refused
    test_the_read_is_bounded_by_the_size_it_checked
    test_a_non_regular_file_is_refused_on_the_descriptor_too
    test_the_directory_policy_errors_name_the_archive_not_the_drafts
    test_a_path_containing_the_word_draft_is_reported_exactly

The swap tests interpose on `_checked_target` and replace the file between the
name check and the open, which is the race itself rather than a stand-in for
it. `test_the_read_is_bounded_by_the_size_it_checked` exists because the
growth check alone did NOT catch an unbounded `read()` — see the deliberate
breaks below.

## R6 — a distinct committed/uncertain outcome. YOUR RULING NEEDED

You offered two options. I took the second, because the first is not
truthfully available: past `os.replace` the target file already holds the new
document, and the only way to roll back is to write again — the operation
that has just failed.

**The commit point is `os.replace`**, and `save` now says so:

- anything failing BEFORE it raises `ArchiveError`. Previous file intact, no
  scratch file left behind, caller keeps the map it had. Unchanged.
- the replace itself is atomic: it happened or it did not.
- the directory fsync AFTER it can still fail, and by then the new document is
  what the target file contains. That raises `ArchiveNotDurable`.

`ArchiveNotDurable` subclasses `ArchiveError`, so a caller that has not been
taught the difference still fails safely on `except ArchiveError`. The
directory fsync moved OUT of the pre-commit `try`, which is what stopped the
scratch-cleanup handler deciding what a committed write means.

The model's half: `_persist_archive` returns one of `ARCHIVE_WRITTEN`,
`ARCHIVE_UNCERTAIN`, `ARCHIVE_FAILED` with a detail string.
`ARCHIVE_UNCERTAIN` ADOPTS the new in-memory map — because that is what the
file now contains — and reports `N rows archived — but the archive was
written to <path> but the directory entry could not be made durable: <reason>`
at warning severity. `ARCHIVE_FAILED` is unchanged: nothing adopted, "archive
failed, nothing changed".

    test_a_file_fsync_failure_leaves_everything_as_it_was
    test_a_failed_replace_is_an_ordinary_failure
    test_a_directory_fsync_failure_is_a_committed_write_and_says_so
    test_the_uncertain_outcome_is_an_archive_error_so_nothing_can_ignore_it
    test_a_post_commit_durability_failure_is_not_reported_as_a_failed_write
    test_a_pre_commit_failure_still_changes_nothing

The first three assert `failure.type is ArchiveError` where the outcome must
NOT be the subtype, so a change that promoted an ordinary failure to
"committed" fails here. The console-level pair drives the real key with fsync
failing on directories only, and then restarts and finds the disk agreeing —
which is the whole reason the outcome is distinct.

**What this supersedes.** `FINDING.md` § Local persistence says a failed write
leaves both the prior file and visible in-memory archive state intact. That
stays true of every failure; what is new is that one outcome is no longer
classified as a failure. The finding is yours, so the supersession is not mine
to write. If you would rather have the alternative — report it as a failure
and accept that memory and disk disagree until the next restart — say so and
I will change it back, but I do not recommend it.

## R7 — stable order, and the stale comment

A batch is taken in displayed order (from the backing rows) rather than off
the selection set, so the same actions produce the same file instead of a
hash-seed ordering. A selected identity the backing rows no longer carry is
kept rather than dropped: `x` must act on the whole set the human is looking
at, and `_selection_dropped_by_refresh` is what removes genuinely gone rows,
on the poll, where it can be seen.

`RESERVED_ROW_KEYS`'s comment said `x` marks a row, `#` trashes the marked set
and neither is bound. All three halves were superseded when the archive
shipped; it now says that `x` archives and restores, that marking is `Space`
(not a letter, so it cannot collide with a status glyph at all), and that `#`
stays reserved and unbound because the ruled feature is recoverable archiving
and nothing here deletes.

    test_a_batch_is_written_in_the_order_it_is_displayed

## A harness defect found on the way, and fixed

`test_bulk_archive_and_restore_on_a_candidate_console` drove the packaged
console with FIXED SLEEPS. It passed alone and failed inside the full
repository suite — twice in three runs — and the failure looked exactly like a
broken feature: the console had archived both rows and the frame was captured
before it had drawn them.

Your copy of that failure was almost certainly R3 (the console claims the
seeded pending row at startup, so the cursor rests on an ineligible row and
`Ctrl+A` refused), and that is fixed. But the harness would have gone on
producing the same symptom for unrelated reasons, and a flaky test that
reports "the feature is broken" is worse than either problem alone, because
nobody can tell them apart from the failure text.

`_candidate_console` now accepts an optional third element per script step:
the text to wait for. It waits for that text to be on the REPLAYED SCREEN and
for the console to have stopped writing for 200ms, up to a generous ceiling.
Steps that omit it behave exactly as before, so no other PTY test changed. A
first attempt without the quiet rule captured an Archived header above a
MESSAGES row — half of one frame over half of another — which is what the
rule is for. Under six competing CPU loads the test now passes four out of
four, in 2.4s rather than 4.8s.

## Deliberate breaks

Each was applied to the tree, the suite run, and the tree restored:

1. `selected` reading MESSAGES again
2. index membership hiding a row with no eligibility recheck
3. `select_all` following the cursor
4. `select_none` following the cursor
5. refresh clamping the Archived cursor instead of restoring it
6. filter restoration skipping Archived
7. the search status counting the whole mailbox
8. a loose file mode accepted
9. the open following symlinks
10. the read unbounded
11. a committed write reported as an ordinary failure
12. the batch taken from the selection set

Eleven failed a named test immediately. Number 10 did NOT — the growth check
still fired, because an unbounded read reaches it with the whole file already
in memory, which is the failure the bound exists to prevent. A spy on the read
request now pins the bound itself, and the break is caught.

## Verification

    env PYTHONPATH=src ./.venv/bin/python3 -m pytest -q tests/

    3 failed, 2617 passed in 214.07s

Focused sets: `tests/tui/test_tui_archive_store.py` 41 passed,
`tests/tui/test_tui_archive.py` 74 passed, `tests/tui/test_tui_pty.py` 26
passed — including `test_bulk_archive_and_restore_on_a_candidate_console`,
which your pass found failing. `tests/tui/` as a whole: 1832 passed.

The three failures are the frozen-artifact manifest checks:
`test_distribution_root_contract`,
`test_isolated_checkout_runs_full_reusable_suite`, and
`test_rebuilding_reproduces_the_checked_in_artifacts_and_manifests`. They are
stale against the working tree's `src/baton_core/_impl.py`, which is the
whole-message-save work rather than this finding's. Verified rather than
assumed: `dist/DISTRIBUTION.json`'s `source_sha256` equals the digest of
`_impl.py` AT HEAD (`31cdc4a8…`) and differs from the working tree's
(`264eb7a4…`), so the staleness predates this pass and rebuilding the frozen
1.0 artifacts is out of scope by instruction.

## Out of scope, untouched

No deployment, build, or activation. `bin/baton`, `bin/baton-tui`, their
manifests, the live authority and config, the reviewer-owned FINDING / PLAN /
review journals, and Git state are all unchanged. `PROGRESS.md` is the only
finding file I wrote.
