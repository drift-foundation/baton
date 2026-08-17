# Plan

**Status — 2026-08-17:** Confirmed during the live W2 ACP continuity trial.
Recovery of the surviving original session is approved for the current trial;
the product correction is queued before W2 can close.

1. Add a bridge-startup, pre-wait, pre-spawn refusal for `session.mode=new`
   whenever the session-state path already exists. Distinguish absent state
   from malformed or unreadable existing state; only absence permits first
   bootstrap.
2. Publish the first accepted selection create-only. A state-file collision
   after preflight must fail without replacing the winner.
3. Add focused regressions for first bootstrap, immediate repeated-bootstrap
   refusal with no Baton wait or ACP spawn, byte-identical surviving state,
   malformed/unreadable existing state, create-only collision, and subsequent
   load of the original session.
4. Keep session rotation out of this slice. Any future rotation operation
   needs its own contract and must not overload bootstrap.
5. Independently review the fail-closed boundary and repeat the live load
   continuity proof.

## Round-one review

Changes requested in `review-2026-08-17T14-45-24Z.md`: keep first publication
create-only, but replace the proposed in-run session rotation with a load of the
already selected session. The selection file remains unchanged across agent
process recovery.

Round two in `review-2026-08-17T14-51-21Z.md` accepts the corrected bootstrap
recovery and requests the symmetric configured-load correction: cache its
selected id once per run and reuse it across every agent-process rebuild.
