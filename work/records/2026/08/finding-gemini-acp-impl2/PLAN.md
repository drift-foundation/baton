# Plan

**Status — steps 1-4 independently signed off 2026-08-18.** Schema 21 carries
selectable routes; `pass route=` selects one; the deployment configuration is
recorded in `DEPLOYMENT.md`. See `review-2026-08-18T19-51-54Z.md`. Step 5's
fresh-deployment live Gemini canary remains operator-owned.

**Prior status — approved and queued.** Gemini is the explicit `impl2` backup;
Claude's existing `impl` route remains the default.

1. [done] Extend configuration and authoritative handoff validation for one
   visible kind with a default route and explicitly selectable backup routes.
2. [recorded for the approver] Add `baton.gemini` with the existing `impl` role and sole
   membership in route `impl2`, without disrupting current `impl` Work.
3. [recorded for the approver] Add separate deployment-owned Gemini ACP bridge/session/policy
   configuration and enforce the deny policy.
4. [done] Cover default `impl`, explicit `impl2`, invalid override,
   claim/reroute safety, projection/Event truth, and config regeneration.
5. [operator-owned] Run the live Gemini canary acceptance and record certification or
   a concrete rejection.

## Phased deployment coordination — approved 2026-08-18

W6 joins W10's next immutable deployment rather than causing a separate
restart. Prepare the Gemini member, `impl2` alternate, bridge/session/policy,
and canary inputs in the new commit-named home while the current authority
continues running. The final freeze stops the old home first, then moves the
live symlink, starts the new complete set, and certifies all participants.
