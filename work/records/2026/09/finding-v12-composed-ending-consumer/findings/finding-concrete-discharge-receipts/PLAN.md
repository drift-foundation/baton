# Plan

Current review125006: **accepted** in review-2026-09-09T04-30-45Z.md. Close
satisfying and release this provider gate. W122060 reuses exact accepted bytes
under the narrowed committed-handoff proof; no further provider edit is queued.

Approved owner124767; High baton.tune ownership returning baton.bug.

Current: baton.tuner claim124831 completed steps1–3; the two-path candidate is
ready for independent acceptance. Exact bytes and scoped verification are in
`evidence/implementation-124831/final.json` and `EXECUTION.md`. Ownership remains
reserved through independent acceptance; the parent consumer is not accepted.

1. Claim first; read FINDING, parent approved proposal/item1 and newest review.
   Revalidate the two owned paths and concrete Authority response contract.
2. Correct receipt compatibility and bounded wrong-kind test fixtures. Add
   real-session commit/replay and negative controls described in FINDING.
3. Declare commands and cumulative20s budget before verification; new controls,
   then one affected module if needed. Preserve commands, timing, hashes/modes
   and limitations in author-owned PROGRESS/evidence.
4. Pass baton.bug for independent acceptance. Do not edit W124784's paths or
   the parent consumer tests; W122060 owns the approved later conversions.
5. Acceptance releases this provider gate only; W122060/W119114 stay unaccepted.
