# Plan

**Status — 2026-08-17:** Confirmed during the live W2/W27 ACP continuity trial.
The current trial may restart Claude's bridge as an explicit workaround after
this defect is represented in Baton. W2 cannot establish fallback-free v11
messaging while return handoffs can be suppressed.

1. Add a dedicated Work actionable-episode sequence to the fresh authority
   schema. Mint it on creation, pass/return, explicit claim release, false-to-
   true readiness, condition wake, and parked-to-queued resume; do not mint it
   on claim, heartbeat, ordinary phase, priority, classification, or metadata.
2. Project Work action identity from authority UUID, participant, Work episode,
   and accepted configuration generation. Move the projection major; retain
   the Work id as a separate structured field.
3. Add focused authority regressions for pass-away/pass-back between reads,
   release, dependency/child unblock, waiting wake, parked resume, route
   remove/restore, and every named non-minting mutation.
4. Make both external bridge validators and delivery memories consume the
   canonical episode key. Add an immediate `timeout=0` participant projection
   revalidation before each queued agent turn and discard an absent exact key
   without mutating Work.
5. Preserve one delivery for a stable episode, retry after delivery failure,
   participant/authority isolation, and one active readiness path per identity.
6. Independently review the fresh schema, protocol projection, and both bridge
   consumers. No in-place authority migration or compatibility alias.
7. Repeat the live pass-away/pass-back cycle without restarting the bridge,
   then resume the W2 fallback-free interval.
