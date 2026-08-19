# Finding: linked Work loses its selected alternate route

## Observation — 2026-08-18

The fresh projection-12 authority routed W25 through visible endpoint
`baton.impl` with explicit internal route `impl2`. Canonical `detail work=W25`
correctly projected:

    endpoint baton.impl
    route    impl2
    handlers gemini

W25 depends on W17. Reading the same relationship from `detail work=W17`
projected W25 beneath `links.blocks` as:

    endpoint baton.impl
    route    impl
    handlers claude

The authority row is not ambiguous and no configuration changed between the
reads. One projection of the same Work therefore sends an operator to Gemini
while the linked-Work summary sends the operator to Claude.

## Confirmed cause

`src/baton_work/projection.py:links()` builds every far-side summary through
its local `far()` helper. `far()` calls `_endpoint_struct()` with
`route_team` and `route_kind` but omits `route_selected`. Direct Work rows
already pass `_selected_route(row)`, so direct projections honor W230 while
linked projections silently fall back to the endpoint's default route.

This affects every relationship using `far()`: parent, containment children,
dependency `blocked_by`/`blocks`, duplicate, and follow-up navigation.

## Required behavior

- Every projection of one Work must resolve its route using that Work's
  durable `route_selected` value.
- A linked Work explicitly routed to an alternate must show only that selected
  route and its handlers, exactly as `detail`, `home`, and `tree` do.
- Default-routed and endpoint-without-alternates behavior must remain
  unchanged.
- A selected route withdrawn by a later accepted configuration must project
  unresolved everywhere; a relationship view must not silently substitute the
  new/default route.

## Acceptance boundary

Add focused regressions that route a Work to an alternate and inspect it from
both sides of a dependency, through parent/child containment, and through at
least one non-gating relationship. Assert exact route and handler parity with
the Work's direct projection. Include default-route and withdrawn-alternate
controls, then run the complete v11 gate.

