# Plan

1. [done] Revalidate the portable case, offer decision boundary, and prior
   rulings.
2. [done] Present the two exact contracts and their authority/replay
   consequences for approver decision.
3. [done] Pin the 2026-08-28 approver ruling here and confirm the durable
   assignment, manifest and portable-case owners already express it.
4. [done; signed-off run2c checkpoint] Correct the Python
   offer boundary on the existing private W33937 development line, add
   positive/refusal/replay regressions, and deliberately revise any affected
   conformance evidence digests. The first review checkpoint was rejected by
   `review-2026-09-02T13-54-46Z.md`: it lets a foreign participant-bound port
   decline the offer and its concurrent exact-accept retry can collide when
   the observation instants differ. Run2c corrects both without altering the
   ruled portable contract.
5. [done; signed off 2026-09-02] Independently review the corrected immutable
   checkpoint from that same development line. The verdict in
   `review-2026-09-02T15-39-09Z.md` binds the run2c content digest and the exact
   six-path cumulative integration closure.
6. [ready for approver/integration provenance gate] Recheck the six base
   hashes in that review against the current target, import only their exact
   signed candidate bytes, and refuse the whole import on any drift or overlap.
   Do not import only run2c's immediate three-path patch or replace the whole
   candidate tree.

Scheduling: the run2c checkpoint is signed off and ready for the distinct
trusted integration gate described above.
