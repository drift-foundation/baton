# W266329 implementer progress

## Claim 266537 — the stale-precheck [P1] corrected, and this dossier bound

**THE DEFECT WAS REAL AND MY CONTENTION CASES DID NOT REACH IT.** Review
2026-09-25T14-12-41Z: caller A passes the preliminary `not-started` read, is
suspended, caller B on a second real handle reserves and completes the same
attempt's start, A resumes, REPLAYS the `runtime.start` identity and still calls
`adapter.start`. A second external crossing after a committed reservation. My two
contention cases only invoked the second request after the first had RETURNED, so
they exercised the early `already-terminal` check and never this ordering. The
reviewer's immutable `review_stage1_stale_start.py`
(sha256 `1ce6ddfe…`, verified against the tree before I ran it) reproduces it
deterministically with a bounded callback rather than threads or timing.

**THE CORRECTION, in `attempts.request_runtime_start` and nowhere else.**
`ControlStore.transact` runs its callback ONLY when it commits the act; a replay
answers from the journal without entering it. So the callback appends to a
`reserved` flag, and after the transaction a caller that did not reserve does not
launch — it calls `reconcile_runtime(store, adapter, attempt_id=…)`, deciding what
exists by identity and full labels instead of assuming its own intent was carried
out. Ownership is therefore decided INSIDE the write lock with no window, and NO
transaction is held across the adapter: the guard runs after the commit and before
the external call. The source's own comment already said the preliminary lane read
"proves only its own instant" and that the authoritative answer is inside `act`;
the mutable axis simply had no such counterpart, and now it does.

**NON-VACUITY, MEASURED.** With the guard removed in place, the reviewer's
regression fails `1 != 0` — the stale caller submits `runtime-first` after
`runtime-second` was attached — and my new loser case fails with a non-empty
submission list. The revert and restore happened in one act, verified by
re-hashing.

**TWO CASES ADDED, the distinct pair the review named.**
`test_a_contender_during_the_first_start_does_not_launch_again` places the
contender INSIDE caller A's `adapter.start`, after A's reservation committed: it is
refused `already-terminal` before the engine and its own adapter records nothing —
which the sequential cases could not show.
`test_the_stale_caller_reconciles_instead_of_submitting` asserts the other half of
the correction that the reviewer's regression leaves open: the loser does not
raise, it reconciles, it asks the engine what exists, and exactly one runtime was
ever created.

**AND ONE ASSERTION TIGHTENED.** My failure case asserted
`adapter.observed or adapter.listing is not None or adapter.started`, which
`started` alone satisfies by that point — it measured nothing. It now asserts
`adapter.observed`, which the fake appends on every `observe(runtime_id)`, so the
reconciliation query is measured directly.

**VERIFICATION.** One bounded command, reviewer regression plus my module:
10 cases OK in 0.094s. The revert probe ran 2 cases in 0.024s, deliberately red.
Stage author total: 0.193s (claim 266370) + 0.094s + 0.024s = 0.311s; with the
reviewer's 0.075s the measured stage total is 0.386s. No live provider, no daemon,
no deployed store, no residue or engine access, no cleanup, no broad suite.

**HASHES after this claim:**

- `v12/python/src/baton_v12/worker_manager/attempts.py`
  sha256 `85a7d1953425782ed76961ab24859ee6fb6171c47266415a6e28cf2a52fc978d`
  (was `1f7c1532…`; the ONLY product change, and the minimal one owner 266361
  authorized for the demonstrated path)
- `work/records/2026/09/finding-v12-failed-run-resource-hold/test_reserve_before_launch.py`
  sha256 `6c21edf5ffcdf1200d52ebb43c4f1db0c76199d35e71107eb50017dadb98e55f`
  (was `70a3e188…`)
- reviewer's `review_stage1_stale_start.py` `1ce6ddfe…` UNCHANGED, not edited
- `custody.py` `3e977dfb…` and `workspaces.py` `dafd9767…` UNCHANGED

**R2 DONE:** this dossier exists and is bound to W266329 at revision 1 through
`bind work=W266329 root=baton path=… expect=0`. Nothing was moved or deleted;
W257624 keeps its own binding and its files are cross-referenced from FINDING.md.
