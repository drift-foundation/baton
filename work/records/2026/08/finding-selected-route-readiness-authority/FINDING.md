# Finding: readiness and authority projections drop selected routes

## Discovery — 2026-08-18

Claude received a readiness wake for W30 even though W30's visible endpoint
`baton.impl` explicitly selected alternate route `impl2`, whose sole handler
is Gemini. Claude did not work around the wake: the atomic claim correctly
refused that Claude is not a resolved handler of route `impl2`.

The same canonical `detail work=W30` response contradicted itself:

- `route` correctly reported `endpoint=baton.impl`, `route=impl2`, and
  `handlers=[gemini]`;
- `available_transitions` nevertheless advertised route-owned mutations to
  Claude.

The write authority remains safe because every mutation rechecks eligibility
inside its transaction. The read/action projections are still operationally
wrong: readiness wakes the wrong agent, and detail says an agent may perform
operations that the authority will refuse.

## Confirmed cause

`_endpoint_struct()` accepts the Work's durable selected route and direct Work
rows pass it. Three route-sensitive read paths resolve only `(team, kind)` and
therefore fall back to the endpoint default:

- `participant_actions()` memoizes endpoint resolution by `(team, kind)`, a
  key that structurally cannot represent per-Work route selection. Both Work
  readiness and due-trial readiness use that result.
- `detail()` computes `available_transitions` against the default endpoint
  rather than the Work's selected route.
- due-trial `obligations()` projects `owed_by` through the default route.

The separate W30 contract owns relationship summaries in `links().far()`.
W39 does not absorb or duplicate that correction; it owns readiness,
transition authority, and due-trial obligation surfaces.

## Required behavior

- Work readiness uses each Work's selected route. Only Gemini is offered a
  Work routed through `impl2`; Claude receives no action for it.
- Claimed-Work recovery and recurring assignment episodes retain the same
  selected-route eligibility.
- `detail.available_transitions` is computed from the same selected route the
  result displays and the write authority enforces.
- Due-trial readiness and `obligations.owed_by` use the labelled Work's
  selected route where Work route eligibility is the governing fact.
- Endpoint-only obligations with no selected Work route keep ordinary endpoint
  resolution.
- Default routes, endpoints without alternates, withdrawn alternates, and
  configuration-generation changes remain fail-closed and deterministic.

## Acceptance boundary

Add focused two-participant alternate-route tests proving the default handler
receives no readiness, no route-owned available transition, and no selected-
route trial obligation, while the alternate handler receives the exact
canonical action. Cover both unclaimed and already-claimed assignment
episodes, default-route controls, and withdrawn alternate configuration. Run
the complete v11 and bridge gates.

