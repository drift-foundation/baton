# Plan

**Status — 2026-08-20:** implemented and gated by `baton.claude` under Work
`W2571`; independent review signed off with no findings in
`review-2026-08-20T11-37-16Z.md`.

1. [done] Revalidate the W1568 event-2544-to-2555 reproduction and the
   superseded W171 unclaimed-pass decision against current transition code and
   tests. Both hold; see `PROGRESS.md`.
2. [done] Require the committing `pass` transaction to observe an active claim
   owned by the exact actor; refuse an unclaimed Work before any mutation or
   event. `transitions.pass_work`, in the lock.
3. [done] Preserve the current claimant's atomic threadless pass and the
   existing refusal for another handler passing underneath a claimant. Both
   asserted, and asserted to stay textually distinguishable.
4. [done] Preserve owning-team `reroute` as the one operation for moving
   unclaimed Work; no implicit or synthetic claim was added anywhere.
5. [done] Focused positive, negative, retry, event/episode and side-effect
   regressions plus workflow coverage:
   `tests/work/test_w2571_pass_requires_claim.py` (19 cases, including the
   whole lifecycle through the public CLI), and the operator workflow stories,
   gate scenario, packaged archive and packaged console now claim explicitly.
6. [done] Update every user and agent contract that still permits unclaimed
   pass: `cli.py` help for `pass` and `reroute`, `docs/BATON-WORK.md`, and
   `docs/EFFECTIVE-BATON.md` — which also gains the **Reroute moves Work
   nobody holds** section this ruling makes necessary.
7. [done] Focused suites and complete v11 gate: 2653 parallel, 51 serial,
   55 ACP. Returning to `baton.bug` for independent review.
8. [done 2026-08-20] Independent review accepted the gated/parked consequence,
   kept the pre-existing parked-reroute defect in W2645, and reproduced the
   final gate as 2634 parallel, 51 serial, and 55 ACP tests.

**One judgement beyond the pinned text, flagged for review:** the ruling makes
gated and parked Work unpassable by anyone, so `pass` can only ever land
`queued`. Three earlier tests that pinned the `block` destination phase are
restated against `reroute` rather than deleted. `PROGRESS.md` has the
measurement and the reasoning.
