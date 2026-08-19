# Progress

## 2026-08-18 — `baton.claude` (implementer)

W12, PLAN steps 1–3. Presentation only: no schema, no projection, no version
bump. The projection already carried gate duration and Handler duration as two
separate facts, which is precisely why the cell could be wrong while the data
was right.

### Revalidation — step 1

Against the current tree, not the finding's description of it:

- `held_field()` had exactly the two branches W78 gave it: `claimed_at` when
  present, then the displayed gate's `started_at` for any open row carrying a
  gate. The second is the one this Work removes.
- **The `Held=-` rule and the `handler is null` rule are already the same
  rule.** `_row_view` sets `claim_fact = (None, None)` when `row["handler_team"]
  is None`, so `claimed_at` is null exactly when `handler` is. The old branch
  order was therefore already handler-equivalent by accident.
- Nothing else reads gate time as a duration: `blocker_cue` reads `row["gate"]`
  for the `Wait` selector only, and the gate's typed identity and episode start
  are projected independently.

### The change

`held_field` now states the ruling in the ruling's own terms — no Handler, no
Held — and formats `claimed_at` only after that test passes:

```python
if row.get("handler") is None:
    return "-"
return held_cell(row.get("claimed_at"), now)
```

Testing `handler` rather than the `claimed_at` proxy is deliberate and is
*not* dead weight, which the sweeps below demonstrate rather than assert.

### Superseded assertions — every one, for audit

The finding supersedes the blocked-Held half of an earlier ruling, so tests
that encoded it had to move. They are listed individually because changing an
existing assertion is the thing that most easily hides a regression, and this
Work changed seven of them across three files. **No assertion was weakened to
make the new code pass; each states the new rule where it stated the old one.**

`tests/work/test_w78_typed_timed_gates.py` (my own file, W78):

1. `test_a_first_dependency_blocks_releases_and_starts_the_clock` → renamed
   `…_blocks_and_releases_without_a_clock`; `"00:45"` → `"-"`, with the episode
   start still asserted present.
2. `test_two_unclaimed_rows_no_longer_run_unexplained_clocks` — the tail
   asserted a blocked row DOES run a clock. It now asserts the row has no
   Handler, runs no clock, and still names its gate in `Wait`.
3. `test_every_row_with_a_clock_names_its_cause` — `explained` was
   `handler is not None or blocker_cue(row)`; now `handler is not None`. This
   is the invariant the whole Work turns on, so it is narrowed rather than
   deleted.
4. `test_a_child_gated_parent_names_the_child` — `"00:20"` → `"-"`; the gate
   SELECTION this test exists for is untouched.

`tests/work/test_w226_held_pickup.py`:

5. `test_the_held_field_walks_the_ruled_states` — the `block` clause `"00:45"`
   → `"-"`, plus the docstring's two-clock rule.
6. `test_the_overflow_value_composes_like_any_other_base` — a blocked row old
   enough to overflow rendered `"∞"`; it now renders `"-"`, because there is no
   value to overflow.

`tests/work/test_w47_heartbeat.py`:

7. Not an assertion — its `field()` helper built `{"claimed_at", "heartbeat_at"}`
   with no `handler`, and every assertion in that file went to `"-"`. The helper
   now names a Handler whenever the row carries a claim. Same for two synthetic
   rows in W226. **This is worth the reviewer's attention:** those rows were not
   states the authority can produce, and the old cell accepted them only because
   it read `claimed_at` alone. Every assertion in both files is unchanged.

### Regressions — `tests/work/test_w12_blocked_held.py`, 10 tests

The reported shape (blocked on another Work); the Message gate as well as the
Work gate, since a fix covering only `work` would leave the identical row
running a clock through a directed obligation; the active claim still timing
from `claimed_at` including the cap; the gate episode and its start surviving;
the rule as an invariant over every scheduler state including `released` and
terminal; a counted version of the same fact so the invariant cannot hold
vacuously; a cleared gate timing from the CLAIM rather than backdating to the
block; and the projection coupling pinned directly.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| Restore W78's gate branch | 9 red |
| No clock at all (remove the active branch) | 6 red |
| Projection keeps `claimed_at` on unclaimed rows | 2 red |

The third sweep is the interesting one and it is why the `handler` test is
written the way it is. With the projection coupling broken, every blocked row
**stayed `-`** — the Handler guard held the line on its own — while
`test_claimed_at_is_null_exactly_when_handler_is` went red and named the drift.
That is the claim the code comment makes, demonstrated rather than asserted.

### Gate

`just test-v11`: **1752 passed**, serial **40 passed**, ACP **41/41**.
`tools/codex-event-bridge`: **44 passed**.

### Step 4

`Independently review and verify JSON/TUI parity` is the reviewer's, and the
parity claim to check is narrow: this Work touches no projected field. The
two durations had separate origins before it and have the same separate origins
after; only which one the Handler column reads has changed.
