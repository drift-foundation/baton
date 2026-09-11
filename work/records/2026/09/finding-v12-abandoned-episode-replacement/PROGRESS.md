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

## 2026-09-09 — baton.claude, claim 129529 (correction)

Claimed at seq129529 before reading the review and before any edit. All three
P1 findings accepted; the first found a relationship I had not bound at all.

**The Job's own committed correction is what selects the checkpoint.** I proved
the selected attempt and the Work's *current* prepared line, so a later custody
round recording changes-requested against another checkpoint — without ever
advancing this Job — let a recovery restored from that checkpoint end an
episode whose committed correction named a different one. `_job_correction`
now reads this store's own journal: the identity
`correction_operation_id(job_id, restored_checkpoint)` must be one this Job
committed, *and* the implementation episode that correction opened must be the
attempt this recovery is about. Either alone is a coincidence. The verdict it
resolved is re-read through `verdict_of` and bound to the same line, checkpoint,
Authority and Work.

**The commit boundary revalidates custody.** The Job write lock does not freeze
custody — they are two stores — so both providers' readers, the prepared line
and the Job correction are re-read inside the committing action, with ordinary
rather than durable refusals, leaving the episode and journal untouched when a
guard fires.

**Both exits own the receipt.** `JobStore.replay` verifies the operation kind
and the selector signature and hands back the stored result, so a row with a
foreign schema, a null assignment and somebody else's checkpoint replayed as a
success. `_adopted_restart` now owns the closed shape, schema, ending, every
identity and the nested assignment on both exits, and the replay additionally
re-reads the receipt's historical relationships — shape alone does not
establish whose checkpoint and assignment are being read. The replay still
precedes every live-state check.

**Concurrency criterion met.** A second manager with its own Job and control
connections, opened in its own thread, calls the replacement while the first is
inside its transaction; it blocks on the write lock and returns the identical
committed result without entering the action. One episode ends once.

**Withdrawn.** My "reported, not fixed" note about W128692's package export —
the reviewer is right that `worker_manager.review_cycles` is that provider's
public location exactly as its accepted CONTRACT states, so importing the
module is ordinary consumption and not a defect.

### Runs

11 OK (0.369s) → 17 with 1 error (0.697s) → 17 with 1 failure (0.705s) → 17 OK
(0.700s) → 242 OK across both declared selectors plus `test_review_driver`,
whose fixture this reuses (6.019s). **8.121s this pass, 15.191s of 20s, 4.809s
left, no reset.** The 222-test neighbour result the review audited was not
repeated. Detail: `evidence/provider-129529.json`.

## 2026-09-09 — baton.claude, claim 129579 (second correction)

Claimed at seq129579 before reading the review and before any edit. Taken under
the reviewer's continue-by-exception for this one outcome.

**One owner for every successful exit.** Two exits returned values nobody
owned: the early replay adopted only the provider half, and `store.transact`
itself returns a *competing caller's* committed result without entering the
action — so validation inside the action could never have covered it.
`_owned_restart` is now the single owner, and both store returns go through it.
It owns the closed receipt, the selected Job, stage, attempt, operation
identity, generation, Work and Authority, and — the part that was missing
entirely — the **historical episode row** the receipt names: it must exist for
this attempt and must record the exclusion ending. A receipt claiming episode
999, or one whose ending was cleared, describes a replacement this store cannot
show it made. Everything it reads is history, never today's live episode, the
current line state or a later writer, which is what a completed replay has to
survive.

**A row's own signature is never its expected signature.** `_job_correction`
handed `record["signature"]` back to `replay`, which compares that value with
itself — so a correction resigned under a foreign kind still authorized a fresh
replacement. The canonical `CORRECT_KIND` signature is now recomposed from the
adopted correction's own operands, with the verdict identity and its attachment
taken from `verdict_of` rather than from the row being checked, and the episode
that correction opened is correlated with this store's own row for it by
number, attempt and stored offer identity.

**The overlap control is corrected.** The hold sat in the `transact` wrapper,
before the first action started, so the event did not establish that the first
call held the write lock when the second arrived. The hold is now inside the
first action, the second caller's arrival is recorded on its own event and
asserted, and both of its connections are opened in its own thread.

### Test delta, recorded under the standing authority

`tests/job_manager/test_recovery.py`: four added controls — the foreign
`job_id` and episode 999 probes, the cleared historical ending, the
foreign-kind correction signature (proving the live episode is untouched), and
a valid replay still answering after a successor begins, which is the property
the ownership check must not cost. The overlap control's hold moved inside the
first action, for the reason above.

### Runs

17 OK (0.715s) → 21 OK (1.661s, first run) → 87 OK across both declared
selectors (1.772s). **4.148s this pass, 19.339s of 20s, 0.661s left, no reset.**
The cap is effectively reached; the 242-test and 222-test results the review
already audited were not repeated. Detail: `evidence/provider-129579.json`.
