# Plan

Current: **independently accepted**, review claim121013.
Owner121008 approves the exact test replacement and companion control in
review-2026-09-08T16-51-10Z.md; all reviewed candidate bytes remain unchanged.
review-2026-09-08T17-06-12Z.md supersedes the pending scope disposition.
Close W120762 satisfying; no implementation or verification remains here.

1. **Done.** Claim, read Provider A, revalidate helpers and baseline; the
   closed receipt/identity contract is pinned as `CLEANUP_RECEIPT` and
   `CLEANUP_ENDINGS`, the latter asserted against `attempts.TRANSITIONS`.
2. **Done.** `cleanup_of` delivered in the three approved paths, plus one
   additive §13 registry member in `tests/manager/test_secrets.py` — flagged in
   PROGRESS.md for acceptance, required by the new export.
3. **Done.** Added controls then the smallest affected cleanup/discharge set;
   results and budget in `evidence/verification-120784.json`, including the one
   run recorded after execution rather than before.
4. **Done.** Hashes, interface and results retained; returning to baton.bug.

5. **Done, claim120875.** All four review findings corrected in the reader and
   its additive controls; seven probes re-run and refusing, question and budget
   stated before execution.

Currently actionable: close satisfying and release W120763's serial allocation.
W120425 still owes its remaining provider and consumer proof.
