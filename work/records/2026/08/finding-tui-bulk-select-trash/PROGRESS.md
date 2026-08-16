# Progress — bulk selection and archive

Owner: `baton.implementer` only.

State: **WITHDRAWN from the tree 2026-08-12 per Slawomir's ruling, and the
withdrawal is APPROVED — `review-2026-08-12T05-26-19Z.md`. Nothing outstanding
here; the feature is deferred to protocol 11 and SQLite.**

Two files in this folder are the SAME review. `review-2026-08-12T05-07-17Z.md`
is the reviewer's journal; `review-2026-08-12T05-07-48Z-ffa31780f37512da1bedc5cf1e2c2b8a.md`
is my materialization of the message that delivered it, named for the message's
publication time. Both are kept — a review journal is append-only and I do not
delete one — but there was one review, not two.

## Withdrawal — 2026-08-12

`review-2026-08-12T05-07-48Z-ffa31780f37512da1bedc5cf1e2c2b8a.md` records
Slawomir's ruling: SQLite is Baton's metastore and must own participant-scoped
archive metadata, so bulk archive is postponed to protocol 11 and neither the
participant-local JSON store nor the 1.1 Archived UI may ship.

Everything below this section is the SUPERSEDED work. It is kept, not deleted:
review 2 says the two defects it reproduced are future safety evidence, and
the R1–R7 record is how the next implementation knows which boundaries the
JSON design failed and why. None of it is an instruction to finish that
design.

### What was removed

Deleted outright:

- `src/baton_tui/archive.py`
- `tests/tui/test_tui_archive.py`
- `tests/tui/test_tui_archive_store.py`

Returned to their independently approved 1.1 content, which for every one of
them is exactly the staged index version — the archive work was never staged,
so the withdrawal is the whole of the unstaged delta and nothing else:

- `src/baton_tui/state.py` — Archived view, partitioning, `identity_of`,
  `is_archived`, the selection set, `archivable`, the four bulk commands,
  `load_archive`, the archive affordances and reasons, the three-list cursor
  table, `_point_at`, `_view_total`
- `src/baton_tui/keys.py` — `a`, `Space`, `Ctrl+A`, `U`, `x`, the Archive help
  section, `ARCHIVE_TOGGLE` in `EFFECTFUL`, the `RESERVED_ROW_KEYS` comment
- `src/baton_tui/driver.py` — dispatch, `_VIEW_FOR`, the affordance entries,
  the startup `load_archive`, the selection marks passed to the renderer
- `src/baton_tui/render.py` — `selection_mark`, the two marks and their ASCII
  fallbacks, the header counts, the view-generic list pane
- `src/baton_tui/drafts.py` — the `noun`/`purpose` parameters. They existed
  only so the archive could borrow the directory policy in its own words, and
  no included feature needs them.
- `README.md` — the archive paragraph
- `tests/tui/test_tui_driver.py` — the `EFFECTFUL` and legend registry members
- `tests/tui/test_tui_render.py` — the glyph registry members
- `tests/tui/test_tui_pty.py` — the candidate archive test AND the
  `_candidate_console` wait-for-screen capability. The capability was a real
  harness improvement (see below) but it was added for the archive test and
  has no other caller, so it goes with it rather than sitting unused.
- `tests/packaging/test_packaging_isolation.py` — `errno` in the stdlib
  allowlist, which only `O_NOFOLLOW`'s ELOOP report needed

### Verification of the withdrawal

`git status`/`git diff` over `src/`, `tests/` and `README.md`: no unstaged
changes and no untracked files remain. Every remaining modification is the
staged, independently approved 1.1 work — whole-message save, notice scope,
search, materialize boundary, deployment — and no shared file lost any of it.

`grep` for `archive`/`Archived`/`ARCHIVE`/`selection_mark`/`VIEW_ARCHIVED`
across `src/` and `tests/`: the only survivors are `zipfile`/zipapp locals in
the packaging and PTY tests and one sentence in a driver test docstring about
retention ("this is a view, not an archive"), all of which predate this work.

`tests/tui/`: 1716 passed. Full repository suite: 2501 passed, 3 failed — the same three frozen-artifact
manifest checks that were failing before this finding began, stale against the
staged `src/baton_core/_impl.py` and out of scope by instruction.

Nothing was deployed, built or activated; frozen artifacts and manifests, the
live authority and config, Git state and the reviewer-owned finding, plan and
review journals are untouched.

---

## SUPERSEDED — the correction pass, kept as evidence

The material below describes the JSON archive implementation and its R1–R7
corrections. It is history as of the ruling above.

Review journal: `review-2026-08-12T00-02-57Z.md` — changes requested, R1–R7.
The correction pass below answered all seven; the response is
`implementation-response-2026-08-12T04-49-55Z-1e38ffc11eb1797e40802f16add52ced.md`.
R6 took the review's second option and would have needed a ruling pinned into
`FINDING.md`; the withdrawal makes that moot.

## Revalidation before editing

Read `FINDING.md`, `PLAN.md`, `work/records/2026/08/finding-next-release/PLAN.md` and
`AGENTS.md` in full, then checked the finding's implementation-start
revalidation against the tree rather than trusting it. Every claim held:

- `refresh()` still builds the complete authority-backed `_all_rows`, and
  `rows`/`sent_rows`/`_matching()`/`view_rows` still own the filtered
  projections. Archive partitioning went beside those, not into authority
  reads.
- `_CURSORS`/`_TOPS` were still a two-view table, and their comment already
  said a third view must not share the inbox cursor. Archived has its own.
- `Space`, `Ctrl+A`, `U`, `x` and `a` were all unbound in browse. Verified
  before taking each.
- `drafts.py` still supplies the required safety class.
- `row_matches()` still reads metadata only, so the same predicate governs
  Archived once the rows are partitioned.

`AGENTS.md` now carries Slawomir's repository policy directly (lines 18–21):
additive tests, including additive cases or members in existing exhaustive
registries, are always authorized. That also retroactively resolves the
whole-message-save gate.

## What shipped

**`src/baton_tui/archive.py`** — a separate versioned participant file under
`<projection_dir>/.baton-tui/<participant>.archive.json`. Ordered, deduplicated
`(row_type, id)` identities and nothing else: no subjects, no timestamps, no
content, no cursor state. It borrows the draft store's DIRECTORY policy by
calling into it rather than restating it, because it is literally the same
directory and two policies for one directory drift apart. Everything else is
its own: its own version (there is no readable predecessor — an unknown version
is refused, not guessed), its own participant check inside the document, its own
size and entry bounds applied before the content is trusted, and the same
scratch/fsync/replace/directory-fsync write.

**`state.py`** — `VIEW_ARCHIVED` with its own cursor and top; `identity_of()`
as the ONE spelling of a row identity; `rows`/`archived_rows` as partitions of
the same backing list; `archivable()`; the selection set by identity;
`toggle_selection`/`select_all_visible`/`clear_selection`/`archive_or_restore`;
`load_archive()`; and `select`/`archive` in the single affordance query with
their reasons in `unavailable_reason()`.

**`keys.py`** — `Space`, `Ctrl+A`, `U`, `x`, `a`, the help section, and
`ARCHIVE_TOGGLE` in `EFFECTFUL`.

**`driver.py`** — dispatch, the affordance entries, a `_VIEW_FOR` table so a
fourth view cannot silently fall through to MESSAGES, and `load_archive()` at
startup beside `load_drafts()`.

**`render.py`** — `selection_mark()` and the counts.

**`README.md`** — the keys, the eligibility rule, and the device-local nature.

## Decisions the ruling did not spell out

**The selection mark shares the cursor column.** One cell, four states:
`>` cursor, `•` selected, `»` both, blank otherwise, with `+`/`*` as the ASCII
fallbacks. A column of its own would have shifted the date, party and subject
of every row in both list panes the moment the feature shipped, and a column
that appears only while something is selected would make the whole list jump
sideways on the first `Space`. The ruling asks for a visible mark that does not
displace the lifecycle glyph; reusing the one column that is already variable is
how that stays true at every width. Pinned at 40, 50 and 60 columns.

**An archived row is always restorable, even if it became ineligible.** A row
archived while eligible could later acquire an obligation. If restore asked the
archive rule again, hiding a row could make it permanently unhideable-and-
unrestorable — the one way this feature could actually lose something. In
Archived, eligibility is "has an identity"; the archive rule applies only in
MESSAGES.

**The whole selection is used, including members the filter currently hides.**
They were selected while visible, and silently dropping them would make `x` act
on fewer rows than the count on screen says. Changing the query clears the
selection, so this can only ever be rows the human chose. An UNCHANGED accepted
query does not clear it — the ruling explicitly allows filtering, looking, and
acting on the matches.

**The console does not duplicate the retention rule for `x`.** It has no
retention concept to duplicate: archiving writes nothing to the authority, so
there is nothing for retention to protect against here.

## A mistake worth recording

I split the `_AFFORDANCE` table while inserting into it and left half its
entries — part navigation and horizontal scroll — inside the new `_VIEW_FOR`
dict. The suite caught it immediately (`h`/`l` scrolled a list-focused pane,
and `a` raised `KeyError`), but the lesson is the same one the scripted edits
taught during whole-message save: inserting into the middle of a literal by
text match is how a block ends up in the wrong container. The fix was to
rewrite both dicts as units.

## Evidence

`tests/tui/test_tui_archive_store.py`, 29 tests: round trip and order; the
file's version, privacy and participant; identities and nothing else; a
separate file from the drafts; no/relative/missing projection directory;
malformed JSON, future version, another participant's file, oversize, too many
entries, and seven shapes of damaged identity list; symlinked and non-regular
files; a world-readable namespace; a bad participant address; a failed write
leaving the previous file intact with no scratch behind; an invalid identity
refused before anything is written; and the directory fsync.

`tests/tui/test_tui_archive.py`, 46 tests, every interaction driven through the
real key: the full eligibility matrix (pending, claimed, damaged, closed,
outbound, unseen notice, seen notice, authored notice, draft);
Space/Ctrl+A/U/x; select-all as a snapshot; current-row action; bulk archive
and restore; restore of a row that became ineligible; identity survival across
reorder, arrival, vanished rows and a message/notice id collision; a thread
parent archived with its child left visible and rendering; filter change,
filter clear, unchanged filter, filtered select-all; view change; Archived
search; Sent unaffected; the pre-write eligibility recheck; a failed write
changing nothing; no projection directory; a damaged index blocking mutation;
restart round trip; full `dump()` equality across the whole flow with the table
list DISCOVERED rather than hard-coded; unchanged obligation counts; no claim
or receipt; the mark sharing the cursor column; narrow terminals at 40/50/60;
both header counts; the selected count; per-view cursors; and Help.

`tests/tui/test_tui_pty.py::test_bulk_archive_and_restore_on_a_candidate_console`
— a real PTY, a real zipapp, a real index file on disk.

Deliberate breaks, each failing named tests: pending/claimed made eligible;
unseen notices made eligible; the pre-write eligibility recheck removed;
in-memory state updated before the write succeeds; the selection kept across a
filter change; the poll pruning the stored index; identity reduced to the bare
id; a damaged index no longer blocking mutation; the mark given a column of its
own; and Archived reusing the inbox cursor.

## Additive registry updates, under the new policy

Three existing exhaustive registries gained members, none weakened:
`test_the_effectful_events_are_exactly_these` (`ARCHIVE_TOGGLE`),
`test_nothing_advertised_refuses_for_want_of_state` (`select`, `archive`), and
`test_every_optional_glyph_falls_back_together` (the two selection marks in
both spellings, plus a one-cell width assertion for every mark that shares the
cursor column).

## Correction pass — review 1 (`review-2026-08-12T00-02-57Z.md`)

Every point was reproduced against the tree before it was changed, and every
correction is pinned by a test that fails when the correction is removed. The
twelve deliberate breaks are listed at the end.

**R1 — the active view is what every action addresses.** `selected` was the
MESSAGES row; it is now the row of whichever list view is on screen, and Sent
keeps its separate read-only path through `selected_sent`. That one property
carries preview, Enter/open, the FIFO warning, `m`, `M` and the follow-up,
because all of them ask it. Two paths needed their own correction:

- `_revalidate_action_target` wrote an index within `_all_rows` into the
  MESSAGES cursor. That was the same number only while nothing was filtered
  and nothing was archived; `_point_at` now sets the cursor of the list that
  actually displays the row, and leaves every cursor alone when the row is
  filtered out of both.
- `refresh` restored one cursor. `_list_anchors`/`_restore_list_cursors` now
  capture and restore each list by its own identity, from one table naming
  the three lists and their cursor/top attributes.

The regressions all put a DIFFERENT pending row under the MESSAGES cursor
first, because with both cursors at zero every wrong-target path passes by
coincidence.

**R2 — a valid index cannot hide unresolved work.** `is_archived` fails open:
membership hides a row only if the row is also one the human could have
archived. An entry found ineligible is RELEASED for the rest of the session,
so resolving the row later cannot make it disappear as a delayed consequence
of a file the human never saw. Releases are pruned from the file by the next
successful human archive/restore write and by nothing else — never by the
poll, which was promised read-only. Seeded-index restart tests cover pending,
claimed, damaged pending and unseen notice, with terminal-message and
seen-notice controls so the fail-open test cannot pass on an index that never
hid anything.

**R3 — four keys, four gates.** `select`, `select_all`, `select_none` and
`archive` are separate affordances sharing `_selectable` as their source of
truth: `Space` asks about the row under the cursor, `Ctrl+A` about every
visible row, `U` about the set, `x` about whichever it will act on. The
covering tests now place the cursor BY PREDICATE rather than by index —
three rows published in the same second are ordered by id, so `cursor = 2`
proves something different between runs, which is exactly how the first
pass's green evidence was order-dependent.

**R4 — filter restoration is view-generic.** `_restore_after_filter` takes
anchors for all three lists rather than the inbox and Sent, so narrowing
Archived can no longer strand its cursor past the end (reads clamped silently
while the renderer marked no row at all). The live search status now counts
the ACTIVE view: "1 of 40" in a list of three archived rows describes a
mailbox that is not on screen.

**R5 — the read is checked on the descriptor.** `load` opens with
`O_NOFOLLOW`, `fstat`s that descriptor for regular type and exact `0600`, and
reads a bound taken from the same `fstat` — one byte more than the file was
said to hold, so growth is detected instead of silently truncated to a prefix
of a document nobody wrote. `_checked_target` gained the same mode refusal, so
`save` will not write through a name that is already world-readable. The
`str(error).replace("draft", "archive")` is gone: `drafts._checked_namespace`
takes the caller's noun and purpose, because rewriting a word in a finished
message also rewrites any path inside it.

**R6 — a distinct committed/uncertain outcome. NEEDS A RULING.** The review
offered either meeting the prior-file/visible-state contract or returning a
distinct outcome. I took the second, because the first is not truthfully
available: past `os.replace` the target file already holds the new document,
and the only way to roll back is to write again — the operation that just
failed.

So `save` raises `ArchiveNotDurable` (an `ArchiveError` subclass, so nothing
that catches the base type can ignore it) only when the post-replace directory
fsync fails. The model ADOPTS the new state, because that is what the file
contains, and says `N rows archived — but ... could not be made durable` at
warning severity. Everything before the replace is unchanged: previous file
intact, no scratch file, visible state untouched. File-fsync, replace and
directory-fsync failures are each tested at their exact boundary, and the
committed case is proved by restarting and finding the disk agreeing.

**This changes a confirmed contract sentence.** `FINDING.md` § Local
persistence says a failed write leaves both the prior file and visible memory
intact. That stays true of every failure; what is new is that one outcome is
no longer classified as a failure. The finding is reviewer-owned, so the
supersession is not mine to write — it is stated here and in the
implementation response for its owner to pin or overrule.

**R7 — stable order, and the stale comment.** A batch is taken in displayed
order (the backing rows) rather than off the selection set, so the same
actions produce the same file rather than a hash-seed ordering; a member the
backing rows no longer carry is kept rather than dropped, so `x` still acts on
the whole set the human is looking at. `RESERVED_ROW_KEYS`'s comment said `x`
marks a row, `#` trashes the marked set and neither is bound — all three
halves were superseded when the archive shipped, and it now says what is true:
`x` archives and restores, marking is `Space` (not a letter, so it cannot
collide with a glyph), `#` stays reserved and unbound.

### Where the reviewer's wording and mine may differ

R2 ends "keep obligation counts unfiltered in every view/header". The
unresolved count is unfiltered and unaffected by archiving, which is pinned.
The ARCHIVED header does not PRINT that count, deliberately — nothing in that
list can owe a reply, since owing one is what makes a row ineligible to be
there — and the Sent header has never printed it either. If the sentence meant
"print it in the Archived header too", say so and it is one clause.

### Additive registry members, under the repository policy

`test_nothing_advertised_refuses_for_want_of_state` and its `_LABELS` table
gained `select_all` and `select_none`; the packaging allowlist gained `errno`,
which `O_NOFOLLOW`'s ELOOP report needs so the console can say "symlink" in
its own words instead of comparing a bare number. No existing expectation was
weakened.

### Deliberate breaks, each caught by a named test

`selected` reading MESSAGES again; membership hiding a row without the
eligibility recheck; `select_all` and `select_none` following the cursor;
refresh clamping the Archived cursor instead of restoring it; filter
restoration skipping Archived; the search status counting the whole mailbox;
a loose file mode accepted; the open following symlinks; the read unbounded;
a committed write reported as an ordinary failure; the batch taken from the
selection set. Eleven of the twelve failed a named test immediately; the
unbounded read initially did not — the growth check still fired — so a spy on
the read request now pins the bound itself.

### A harness defect found on the way, and fixed

`test_bulk_archive_and_restore_on_a_candidate_console` drove the packaged
console with FIXED SLEEPS. It passed alone and failed inside the full
repository suite -- twice in three runs -- and the failure looked exactly like
a broken feature: the console had archived both rows and the frame was
captured before it had drawn them.

The review's own copy of this failure was almost certainly R3 (the cursor
rests on the seeded pending row at startup, so `Ctrl+A` refused), and that is
fixed. But the harness would have gone on producing the same symptom for
unrelated reasons, and a flaky test that reports "the feature is broken" is
worse than either problem alone, because nobody can tell them apart from the
failure text.

`_candidate_console` now takes an optional third element per script step: the
text to wait for. It waits for that text to be ON THE REPLAYED SCREEN and for
the console to have stopped writing for 200ms, up to a generous ceiling, so a
loaded machine costs time rather than a false failure. Steps that omit it
behave exactly as before. A first attempt without the quiet rule captured an
Archived HEADER above a MESSAGES row -- half of one frame over half of
another -- which is what the rule is for. Under six competing CPU loads the
test now passes four times out of four, in 2.4s rather than 4.8s.

### Verification

`tests/tui/`: 1832 passed. Focused: `test_tui_archive_store.py` 41,
`test_tui_archive.py` 74, `test_tui_pty.py` 26 (including
`test_bulk_archive_and_restore_on_a_candidate_console`, which the review found
failing). Full repository suite: 2617 passed, 3 failed — all three are the
frozen-artifact manifest checks (`test_distribution_root_contract`,
`test_isolated_checkout_runs_full_reusable_suite`,
`test_rebuilding_reproduces_the_checked_in_artifacts_and_manifests`), which are
stale against the working tree's `src/baton_core/_impl.py`. That file is the
whole-message-save work, not this finding's, and rebuilding the frozen 1.0
artifacts is out of scope by instruction. Verified: `dist/DISTRIBUTION.json`'s
`source_sha256` equals the digest of `_impl.py` AT HEAD, so the staleness
predates this pass and is not caused by it.

## Not done, by instruction

Nothing deployed or activated. `bin/baton`, `bin/baton-tui`, their manifests,
the live authority and config, reviewer-owned FINDING/PLAN/review files, and
Git state are untouched. Verification used candidate artifacts built to
throwaway roots.
