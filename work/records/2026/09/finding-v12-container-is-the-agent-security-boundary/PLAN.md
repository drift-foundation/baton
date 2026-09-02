# Plan

1. [done] Record the live `acceptEdits` approval refusals and supersede the old
   inner-policy decision.
2. [done, reviewer 2026-09-01] Revalidate the current Claude CLI flag and
   adapter/image boundary against the live tree. Host Claude Code 2.1.250
   confirms the activation flag; the exact pinned 2.1.247 image proof remains
   part of step 4 because the managed reviewer cannot reach Docker.
3. [done, integrated as `bbc5c09` 2026-09-02] Change only the provider argv and its
   focused golden/policy tests so arbitrary in-container tools run without
   approval. The exact two-file boundary and negative argv assertions are in
   `FINDING.md`.
4. [done, operator `baton.slaw` 2026-09-02] The rebuilt pinned image is selected
   by digest, its 2.1.247 CLI exposes the bypass activation flag, and the 167
   OCI/input-delivery cases pass. Fresh `attempt-w64268-run2` edited exactly one
   private-candidate path, ran its frozen Python verification inside the worker
   with status 0 and no approval interaction, and the outer operator reran the
   identical command with status 0. Runtime absence and a resolved ending are
   recorded under `evidence/w64268-run2/`.
5. [done, reviewer 2026-09-02] Independently reviewed retained run2 proposal
   `sha256:4e65e3316e02101953b3e06bc27e38350d7aae7cf382ea7ecab12206d1963014`
   and the unchanged external OCI boundary. Signed off for import in
   `review-2026-09-02T04-30-11Z.md`; rebuilt-image and live no-approval proofs
   remain step 4 gates before Work closure.

Scheduling: W61984 closed satisfying on 2026-09-02. This Work is now ready for
an isolated v12 attempt and must not be implemented through the v11 host
runner.
