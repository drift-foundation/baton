# Corrections to this directory — appended 2026-10-18, claim 325138

Review 2026-10-18T18-05-00Z found four faults in this harness and one false
claim in its prose. The observations here are preserved; the following
conclusions are withdrawn, and `../matrix-325138/` carries the corrected work.

1. **The harness did not check anything.** `Matrix.run` marked any returning
   body `observed` regardless of what the body found, its advertised
   `asserted` values were strings rather than checks, `main` exited 0 even
   when a scenario failed, and a cleanup failure did not fail a scenario. So
   "seven observed" meant seven bodies that returned, not seven passing
   checks. `matrix-325138/matrix2.py` replaces it with checks that raise, a
   non-zero exit, cleanup counted as failure, and a deliberately false
   self-check that must be reported as failed.

2. **The cancellation never happened.** `scenario-5-cancellation-and-non-
   satisfying.json` records `live_before_cancel: null` and carries no
   `cancelled` field: the assignment had already ended, so the act was
   skipped. `MATRIX.md`'s and `PROGRESS.md`'s claim that "cancelling the live
   assignment left the Work open and queued" was therefore unsupported by
   this directory's own JSON. The non-satisfying closure DID happen and
   stands. `matrix-325138/scenario-1-live-cancellation.json` drives a real
   cancellation while the assignment is live and asserts the act occurred.

3. **`exceptional` is a state, not a diagnostic owner.** Calling it the
   diagnostic owner renamed a scheduler state. The corrected answer is in
   `matrix-325138/scenario-3-diagnostic-owner.json`: every member the status
   projection gives an exceptional stage is enumerated, none of them names an
   owner, principal or eligible assignment, and the precise missing supported
   operation is documented as a bounded gap with its spec basis.

4. **Scope that was claimed as covered but was not driven**: no lost-reply
   injection existed in `2-restart-no-duplicate`; held-unknown runtime and
   disposable recovery were absent; and the correction check read the private
   `_prepared` inventory rather than resolving the predecessor candidate,
   review result and successor attempt through supported APIs. See
   `../PROGRESS.md` for which of these the corrected run now covers and which
   remain open.

Nothing in this directory was edited or deleted; this file is appended beside
it so the original evidence and its manifest stay exactly as reviewed.

## Appended 2026-10-18, claim 325259 — what this directory's observations became

The ten files here remain unedited. The outcomes this run OBSERVED without
checking are now asserted in `../matrix-325259/matrix3.py`, which is the
complete asserting matrix:

* the cancellation this directory's prose claimed but its JSON did not
  (`live_before_cancel: null`) — now driven live and asserted, with the
  runtime-quiescence gate surviving it, scenario 8;
* the stale-episode and wrong-principal refusals — now asserted together with
  the state being unchanged after each one, scenario 7;
* the empty provider turn — now asserted, scenario 6;
* the claim compare-and-swap and the read-only handle — now asserted inside
  scenario 8, with the accurate statement of what they enforce;
* the `exceptional` state I described as a diagnostic owner — corrected in
  `../matrix-325138/SUPERSESSION.md` and then resolved positively in scenario 5
  of the new run, which establishes the supported diagnostic-ownership path and
  withdraws the product-gap claim entirely.
