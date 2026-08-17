# Plan

**Status — 2026-08-16:** signed off in
`review-2026-08-16T19-58-11Z.md`. R1 now refuses a shared-route peer who does
not own the active claim, while preserving claimant and unclaimed transfers;
the focused W171 suite and complete v11 gate are green.

1. Revalidate every `pass` authority, projection, CLI, TUI command-mode and
   workflow-test path against the decision in `FINDING.md`.
2. Remove `thread=` from the pass grammar and stop creating a discussion
   Message as a side effect of transfer.
3. Preserve `comment=` in the authoritative pass event and expose it in the
   canonical Work history/JSON projection.
4. Prove the Work mutation remains atomic: claim release, Current, destination
   phase, planned return, event evidence and destination wake either commit
   together or do not occur.
5. Add negative and regression coverage for obsolete `thread=`, message/count
   immutability, retry replay, authorization and several-Thread Work.
6. Run the complete v11 gate and return for independent review before using
   the corrected operation to finish W148.
