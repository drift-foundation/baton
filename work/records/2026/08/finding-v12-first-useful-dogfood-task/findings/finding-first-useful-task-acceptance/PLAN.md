# Plan

1. [blocked on W39358] Revalidate the accepted operator command and parent
   frozen-task evidence.
2. Obtain the exact credential-source and network-posture grants from the
   operator; record values without recording credential content.
3. Run one fresh attempt from clean operator-owned roots and retain its bounded
   correlated transcript and proposal.
4. Independently inspect the candidate tree/change, rerun the focused harness
   outside the worker and verify canonical input immutability and cleanup.
5. Record an explicit accept or reject in append-only review evidence and
   close W39364 with the matching outcome.

## 2026-08-30 — revalidated pre-run gate

1. [done] Revalidated W39358 and independently reproduced the parent task's
   frozen subset.
2. [done: approved] Correct the frozen delivery by adding only
   `v12/spike/ping-pong/trial.mjs`. The earlier three-file subset is
   superseded; the unchanged command passes 26 baseline cases with the fourth
   file present.
3. [done: approved and verified] Use credential source
   `/run/baton/credentials/claude` and explicit Docker network `bridge` for
   this supervised private-box attempt. Record no credential content and
   infer no default from these values. Correct the source's external metadata
   to mode `0400`, owner `sl:sl`, so the uid-1000 operator can materialize the
   attempt-scoped slot without exposing or rewriting its bytes.
4. [done: candidate rejected] One fresh supervised attempt resolved the real
   platform arc. The worker answered `unable` and changed nothing. Hard-coded
   discard removed the candidate before direct reviewer inspection; W51473
   owns that P0 and W51476 owns the independently observed preflight P1.
5. [done] Independent review matched every sealed candidate-source digest to
   the unchanged canonical four-file input, reran the exact reconstruction
   (26 baseline cases, OK), proved the custody locator and execution/provider
   roots absent, and recorded explicit rejection. Close W39364
   `non-satisfying`; do not spend a second provider turn under this Work.
