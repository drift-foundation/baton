# Plan

1. Reproduce the full-module versus isolated-shard boundary-inventory verdict
   and enumerate every adopted attempt column lacking a probe.
2. Generalize the existing table-derived probe mechanism to
   `schema.ATTEMPT_COLUMNS`; add only evidence-backed exclusions for columns a
   corruption probe cannot drive.
3. Prove each generated probe reaches the `a persisted attempt` boundary
   rather than an earlier refusal.
4. Run the boundary-inventory module and the same isolated shards used by the
   parallel runner, then return for independent review.


## 2026-08-29 — implemented

1. [done] Reproduced and enumerated:
   `evidence/w35557-before-2026-08-29.txt`. The family is larger than the
   finding says -- the four omissions AND seven stale
   `output.py:_attempt_of` probes, from a hand-written list that had drifted
   the other way.
2. [done] `attempt_probes()` derives from `schema.ATTEMPT_COLUMNS` for all
   three sites that adopt an attempt row, each driven through its own module's
   public operation. Both hand-written lists are gone. The single exclusion --
   the lookup key -- is declared in `NO_PROBE`, which is the mechanism that
   already holds exemptions to being live and owned.
3. [done] `test_every_declared_probe_reaches_its_named_boundary` passes over
   the whole declared set.
4. [done] The sharded gate and the whole module, and they agree:
   `evidence/w35557-gate-2026-08-29.txt`.

## 2026-08-29 — independent review

5. [done] Recomputed the live attempt-family entries and declared probes on
   the current tree: 17 owned, 15 probeable, 15 declared, no missing or stale,
   with exactly two live `NO_PROBE` exemptions.
6. [done] Reran all 15 generated attempt probes independently; every probe
   reached the named persisted-attempt boundary. The correction is satisfying.
