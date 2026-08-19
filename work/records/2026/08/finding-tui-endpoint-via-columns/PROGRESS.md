# Progress — implementer

Work `b06383c8-W35`. State: **awaiting review**.

## Revalidation (PLAN step 1)

The defect is exactly as recorded and still live in the tree: `COLUMNS`
carried one `ROUTE` entry and `_row_cells` filled it from
`row["route"]["endpoint"]`, so the label promised the route and the cell
showed the address.

Two things changed under this record while it was blocked, and both had
to be re-checked:

- **W25 landed** and rebuilt the table shell around three top-level
  tabs. The Work table itself — `COLUMNS`, `DROP_ORDER`,
  `visible_columns`, `_row_cells` — is unchanged by it, so this record's
  plan applies as written.
- **W39 landed** and made `participant_actions` honour `route_selected`.
  That matters here: the route object the table now renders is the same
  resolved one authorization uses, so Endpoint and Via cannot advertise
  a route the claim would refuse. A test asserts that pairing directly
  by rendering an alternate-routed row and then watching the default
  route's handler get refused.

## What was implemented

`COLUMNS` replaces `ROUTE` with `ENDPOINT` (13 cells — `team.kind` is at
most 6+1+6 by the handle rule) and adds `VIA` (6 cells — a route handle
is at most 6). `_row_cells` fills them from the one resolved route
object: `route.endpoint` and `route.route`.

`DROP_ORDER` puts `VIA` before `ENDPOINT`, both after `NEXT` and both
before `HANDLER` — the FINDING's rule, with one judgement inside it: a
bare route handle without its address is the more ambiguous of the two
halves, so Via is the one that goes first.

Nothing in JSON changed. The projection already carries the structured
route object with `endpoint` and `route` as separate fields; this Work
is the console finally reading both of them.

## A width consequence the reviewer should see

The extra column costs seven cells, and the Title is the one column the
layout may truncate. At 110 columns with terminal rows revealed the
title now sits at `MIN_TITLE`, where it previously had about seventeen
cells. That is the ruled behaviour — identities are drawn whole or the
column is dropped, and the title absorbs the remainder — but it is a
real cost and I did not want it to arrive silently. If the reviewer
prefers, `VIA` could drop earlier in the order, or the title floor could
rise; both are presentation rulings rather than implementer calls.

Two existing tests moved because of it, and both were presence checks
rather than statements about width. `test_tui.py`'s revealed-outcome
case asserted the full title AND the compact outcome on one line; it now
asserts the outcome cell and the disappearance of the collapse note,
which is the property it was about. `test_w84_hot_cue.py`'s cold-table
case looked for a 14-character title to locate its row; it now matches
the prefix that fits, and its blink assertion — the thing that test
exists for — is untouched.

That two tests needed it is the honest measure of the cost, which is why
it is written down here rather than absorbed quietly.

## Existing tests changed

- `test_tui.py` — the narrow-width column set (`ROUTE` → `ENDPOINT`) and
  the revealed-outcome assertion above.
- `test_parity.py` — the drawn-row mapping reads the `ENDPOINT` cell for
  the JSON `route.endpoint` it compares against.
- `test_w84_hot_cue.py` — the row-presence prefix described above.

None is weakened; each asks its original question of the renamed cell
or the property it was actually about.

## Tests added

`tests/work/test_w35_endpoint_via_columns.py` — 10 cases on a fixture
whose `impl` kind offers a genuine alternate route, because the defect
only exists where one endpoint has two: the header naming both columns
in order with `Route` gone; a default-routed row showing address and
route; two Works on ONE endpoint distinguished only by Via; a claimed
alternate showing `lang.impl` / `alt` / `lang.grace` — the acceptance
boundary's exact assertion; Via agreeing with the route that authorizes,
proved by the default handler's claim being refused on the same row; an
unresolved route reading `-` in Via while the address survives; a
terminal row reporting no eligibility in either cell; whole-column
omission with Via going before Endpoint and Handler outliving both; no
identity truncated at any width; and JSON keeping the distinction
structurally rather than by label.

One thing the new tests taught me: the fake screen used elsewhere in
this suite REPLACES a row's tail on each write, and the Work table
paints its bold Title after the full row at a smaller column (W23). A
replacing fake therefore loses every cell to the right of the title —
which is precisely the half this Work is about. The fake here overlays
instead, which is what a terminal does.

## Verification

- Focused: `tests/work/test_w35_endpoint_via_columns.py` — 10 passed.
- The complete v11 gate, `just test-v11`, exits 0 on this tree: **2032
  passed** (parallel), **40 passed** (serial), ACP acceptance green.
