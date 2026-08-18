# Progress

**Steps 1–4 implemented by `baton.claude` and returned to `baton.feat` for
independent review on 2026-08-18.** Schema 21. Step 5 is the live Gemini canary
and is operator-owned; step 2's configuration is recorded for the approver
rather than applied, for the reasons below.

## Revalidation

The routing model had no place to put this:

- a Work row stores the ENDPOINT (`route_team`, `route_kind`), and the route is
  re-resolved from the kind on every read;
- `kinds.route` is a single handle, so `baton.impl` always resolved through
  `impl`;
- therefore a Work handed to an alternate would have resolved back to the
  default at the very next read. The choice would have lasted one transaction.

That is why the selection is stored on the Work rather than inferred.

## What changed

**Configuration.** A kind may declare `alternates` beside its `route`. The
`route` stays the deterministic default — an omitted selection always resolves
to it — and alternates are selectable only by explicit request. Refusals at
acceptance: an undeclared route, a kind listing its own default, a repeat, and
an alternate whose role differs from the endpoint's. That last one matters most:
an alternate with another role would make one visible endpoint mean
implementation or review depending on a per-Work choice, which is what a visible
endpoint exists to prevent.

**Schema 21.** `work.route_selected` (NULL = the default) and a
`kind_alternates` table, rebuilt on every accepted generation like every other
configuration table.

**Handoff.** `pass … route=` selects one. It resolves inside the lock like every
other endpoint fact, so a regen removing the alternate between the operator's
choice and the commit refuses rather than routing elsewhere. The event records
`route_selected` and the resolution it produced.

**Projection.** A Work's `route` is its own — the selection when it has one, the
default otherwise — and nothing lists candidates on the row.

## Two things the work itself turned up

**The "already there" guard would have refused the whole feature.** `pass`
refuses when the destination endpoint equals the current one, so a reroute
within `baton.impl` — the exact operation this Work adds — read as a non-move.
The comparison now includes the route, in both the pre-read and the
authoritative in-lock copy.

**Authorization had to follow the selection, or the selection stranded the
Work.** `_handler_gate` resolved the endpoint's DEFAULT route, so after a
handoff to `impl2` the only eligible handlers were the default's — Gemini could
not claim, pass, or close the Work it was holding, and no one on `impl2` could
give it back. It now resolves through the Work's own route. This was a total
failure, not a rough edge, and it is pinned from both sides: the alternate's
handler can act, and the default's cannot while the Work sits elsewhere.

## Regressions

`tests/work/test_w230_selectable_routes.py` (22 tests): the configuration
rules and each refusal; birth on the default; an omitted handoff returning to
the default; nothing ever selecting an alternate on its own; the selection
surviving repeated reads and being the only route projected; the event record;
authorization from both sides; an unconfigured route refusing atomically with
no event written; the moved guard; claimed Work not moving underneath its
Handler while the claimant's own pass reroutes in one act; regeneration
rebuilding the selectable set; a Work on a withdrawn alternate projecting
explicitly unresolved rather than silently reverting; an endpoint without
alternates behaving exactly as before; and the recorded deployment block
validating as real configuration.

## Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| The selection is not stored | 9 red |
| Authorization resolves the default route | 4 red |
| The guard compares endpoints only | 13 red |
| The projection ignores the selection | 7 red |

## Not applied, deliberately

**Step 2's configuration** is in `DEPLOYMENT.md` beside this file, as the exact
`teams.baton` block plus the approver's steps. Accepting a configuration is the
approver's act and the deployed binary predates `alternates`, so editing the
live `baton.json` would refuse — and would take every launcher down with it. A
test parses that block and validates it as real configuration.

**Step 3's live bridge file.** `examples/acp-bridge-gemini.json` already ships
as the template; the instance file is deployment-owned and names real paths,
credentials and policy.

**Step 5's canary** needs a running Gemini process, its own authentication, and
a restart of the local infrastructure — the same operator territory as W20's
live smoke, and for the same reason: it cannot be driven from inside the
session it would restart.

## Gate

`just test-v11`: **1656 passed**, serial **38 passed**, ACP **41/41**.
