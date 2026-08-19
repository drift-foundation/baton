# Progress — implementer

Work `b06383c8-W30`. State: **awaiting review**.

## Revalidation: the fix already landed, under W128

This record's Confirmed cause is exact — `links()`'s local `far()`
resolved every neighbour with `route_team` and `route_kind` and omitted
`route_selected`, so linked views fell back to the endpoint's default
while direct views honoured W230.

**That call is already corrected in the tree.** It was fixed on
2026-08-19 while implementing W128, because W128's own Required
behavior says a reroute must "project the new Route consistently
through direct and linked Work views" — its linked-projection test
failed on exactly this defect, and a reroute whose result the linked
view contradicts has not met that boundary. The comment at the site
names this record as the one that identified it first, and the W128
handoff reported the overlap rather than absorbing it.

So what this record still owned when I claimed it is its **acceptance
boundary**: the regressions that keep the correction true. W128's suite
covers one relationship (`blocked_by`) from one side, which is not what
this record asks for.

## What I verified before writing tests

- `far()` passes `_selected_route(other)`, and it is the ONLY resolution
  in `links()`.
- Every other resolution site was checked for the same omission:
  `_row_view` (direct rows) and `detail`'s authority matrix pass the
  selection; `participant_actions` and the due-trial `owed_by` were
  corrected under W39; the obligation `owed_by` sites resolve an
  obligation's own endpoint, which has no per-Work selection to carry.
  `_work_state` — used by `pokes`, `teams` and `runtime` — reports
  status, phase and handler and no route at all, so it cannot carry
  this defect.

That sweep is the reason these tests cover every relationship rather
than the one the incident exposed: one omitted argument broke all of
them at once, and a regression on a single call site would not have
noticed.

## Tests

`tests/work/test_w30_linked_route_parity.py` — 12 cases on a fixture
whose `lang.impl` offers an alternate resolving to a DIFFERENT member,
because with one route per endpoint the wrong resolution gives the right
answer and the defect is invisible:

- the incident itself, read from the other side of its dependency, with
  the edge created BEFORE the routing exactly as W17 → W25 predated
  W25's move to `impl2`;
- the same edge from the consumer side;
- containment in both directions, parent-on-alternate and
  child-on-alternate;
- both non-gating relationships — duplicate and follow-up — each read
  from both sides;
- a sweep asserting every relationship `far()` serves agrees with the
  neighbour's own direct projection;
- controls: a default-routed neighbour, an endpoint with no alternates
  configured at all, a terminal neighbour reporting no live route in
  either view;
- the withdrawn-alternate case, which is this defect wearing a different
  hat: after a regen removes the alternate, both views must report
  UNRESOLVED rather than substituting the default, because substituting
  would send the operator to an agent nobody chose;
- and the console's neighbour view, which renders `links` directly, so
  the operator-facing end is covered too.

Every parity assertion compares the linked row against the neighbour's
own `detail` route object in full — route, handlers, role and endpoint —
rather than spot-checking a field.

## Note for the reviewer

If the fix landing under W128 makes this record's disposition awkward, I
would rather that be your call than mine. The regressions here are worth
keeping wherever the record lives: they are what stops the next omitted
argument from reaching a release, and they cover relationships W128's
boundary never touched.

## Verification

- Focused: `tests/work/test_w30_linked_route_parity.py` — 12 passed.
- The complete v11 gate, `just test-v11`, exits 0 on this tree: **2076
  passed** (parallel), **40 passed** (serial), ACP acceptance green.
