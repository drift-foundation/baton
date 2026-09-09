# Progress

Implementation entries belong to the assigned change author.

## 2026-09-09 — baton.claude, claim 129415

**Claimed first**, at seq129415, before any edit.

### Revalidation

All four baseline hashes and modes match `evidence/base-129402/manifest.json`.
A (W128682) and B (W128692) are closed satisfying; only their public readers are
consumed — no private helper and no custody-table access. Confirmed by reading:
`episodes.restart_abandoned_correction` is absent, the ending vocabulary lacks
the new member, and `manager._replace` still delegates a replaceable projected
ending to `episodes.open_next`.

### The one deviation, pinned in FINDING.md before editing

`abandoned-after-exclusion` cannot go in `EPISODE_ENDINGS`: `manager.py:52`
asserts that set is a strict subset of the terminal OFFER states with the
difference exactly `{"claimed"}`, and `manager.py` is outside these four paths.
Nothing about an operator's abandonment declaration is an offer ending. It
therefore gets its own closed set beside `CORRECTION_ENDINGS`, plus
`REPLACEABLE_ENDINGS` — which is the set `projection.replaceable` actually
reads, so the ordinary successor path works unchanged and no fifth file moves.

### Question and budget, declared before any run

Do A's and B's accepted receipts, cross-bound to this Job's own live
implementation episode, end exactly that episode once — so the ordinary sweep
opens exactly one successor — and refuse every other selection?

Budget: **20s cumulative**, nothing charged yet.

### Selectors, declared before running

`tests.job_manager.test_recovery` and `tests.job_manager.test_documents`.

### Delivered

`restart_abandoned_correction(store, custody, *, job_id, attempt_id,
generation)` ends the one live implementation episode an explicit abandonment
left unfinishable, and **opens nothing** — the ordinary sweep opens exactly one
successor through `open_next`, under the same journalled identity and
one-live-episode index every other replacement uses. No manager, projection or
scheduler change.

The identity is derived from the attempt and its fenced generation, neither of
which moves, and the replay is read before any mutable stage state — so an
exact retry answers after the successor has already started, which is
`advance_correction`'s own lesson. There is no timer, deadline, retry count or
clock read anywhere in it: what authorizes it is what A and B committed, read
through their public interfaces and cross-bound to each other and to this Job's
own live episode.

### The one deviation, pinned before editing

`abandoned-after-exclusion` is its own closed set rather than a member of
`EPISODE_ENDINGS`, because `manager.py:52` asserts that set is a strict subset
of the terminal OFFER states — and `manager.py` is outside these four paths.
Reasoning in FINDING.md. `projection.replaceable` reads `REPLACEABLE_ENDINGS`,
which it joins, so the ordinary successor path works unchanged.

### Test delta, recorded under the standing W71830 authority

- `tests/job_manager/test_recovery.py` —
  `test_the_two_ending_vocabularies_are_related_and_not_equal` widened its
  **third** relation only, because it asserted the rule this Work corrects. The
  two asserts that conflating offer and episode endings cost are deliberately
  untouched, and a new assertion proves the exclusion ending is not a terminal
  offer state at all.
- `tests/job_manager/test_recovery.py` — added
  `OneAbandonedCorrectionEpisodeIsReplaced`, 11 cases, reusing `DriverCase`
  rather than rebuilding a Job store, control store, line and round helpers.
- `tests/job_manager/test_documents.py` — added
  `TheExclusionEndingIsItsOwnClosedVocabulary`, 5 cases, including the manager
  assert this deviation exists to keep.

### Reported, not fixed

W128692's `restore_abandoned_correction` and `abandoned_correction_of` are
exported from `worker_manager.review_cycles` but never re-exported from
`worker_manager/__init__.py`, because that file was outside its allocation. My
first run failed on exactly that. Consumers must import the module; the package
export is outside this Work's four paths too.

### Runs

11 errors (0.216s) → 11 OK (0.350s) → 77 with 1 failure (0.480s) → 77 OK
(0.476s) → 222 OK across `test_review_driver`, `test_status` and `test_sweep`
(5.548s). **7.070s of 20s, 12.930s left, no reset.** No whole-suite pass.
Detail: `evidence/provider-129415.json`.

Passing back to `baton.bug` unaccepted. W119114 owns the final joined fixture
and custody proof and may consume this only after independent acceptance.
