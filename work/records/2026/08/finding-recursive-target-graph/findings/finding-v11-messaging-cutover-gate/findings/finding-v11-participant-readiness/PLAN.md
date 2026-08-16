# Plan

**Status — 2026-08-16:** closed satisfying as v11 Work `W136` after independent
round-two sign-off. Projection 4.3 now supplies the permanent participant-action
contract; the parent gate auto-woke for its next stage.

1. Add one pure participant-action projection over ready Current Work,
   eligible pending obligations and eligible due rounds, with stable typed
   action keys and deterministic ordering.
2. Make `wait` pass the configured member as well as team and return that exact
   projection after its existing read-only timeout loop.
3. Derive the TUI's personal obligation/due header counts from the same
   participant facts while preserving the separately labelled team summary.
4. Cover eligibility, competing handlers, claim continuity, reroute, plain/+
   exclusions, @ completion, due generations, restart, timeout and races.
5. Run focused and full v11 gates and return for independent review. Do not
   modify the Codex monitor in this slice; its adapter depends on this contract.
