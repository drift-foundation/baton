# Plan

1. [done] Revalidate the portable case, offer decision boundary, and prior
   rulings.
2. [done] Present the two exact contracts and their authority/replay
   consequences for approver decision.
3. [done] Pin the 2026-08-28 approver ruling here and confirm the durable
   assignment, manifest and portable-case owners already express it.
4. [changes requested; resume the isolated v12 Work line] Correct the Python
   offer boundary on the existing private W33937 development line, add
   positive/refusal/replay regressions, and deliberately revise any affected
   conformance evidence digests. The first review checkpoint was rejected by
   `review-2026-09-02T13-54-46Z.md`: it lets a foreign participant-bound port
   decline the offer and its concurrent exact-accept retry can collide when
   the observation instants differ. Do not alter the ruled portable contract
   merely to make the stale implementation pass. Do not restage from the host
   baseline or require a canonical commit between correction turns.
5. [blocked on corrected review checkpoint] Independently review the next
   immutable checkpoint from that same development line. Only a signed-off
   checkpoint becomes the proposal sent to integration.

Scheduling: W33937 is ready for a bounded isolated v12 correction turn against
its retained private development line. It must not be implemented through the
v11 host runner.
