# Plan: render TUI timestamps in host-local time

1. [done — reviewer research 2026-08-25] Inventory every human-facing TUI
   timestamp and the parsers feeding it. `FINDING.md` and
   `evidence/reviewer-inventory-2026-08-25.txt` name every current absolute
   timestamp site, the canonical naive-UTC hazard, and the elapsed-duration
   exclusions. Protocol/JSON serialization is outside the patch boundary.
2. [done 2026-08-25] Add one module-level local-instant formatter with full and
   compact modes. Treat Baton's naive storage spelling as UTC explicitly,
   convert at render time through the active host timezone, include `tzname()`
   with numeric-offset fallback, and do not cache a timezone object.
3. [done 2026-08-25] Route Message detail/index, Event detail/index and claim
   interval, Poke table/detail, and Teams pickup/runtime/answer absolute
   instants through the helper. Give compact Message/Event time columns enough
   dynamically measured width for the zone-bearing value and continue to drop
   the whole column under pressure. Leave elapsed Held/Since/age/duration cells
   unchanged.
4. [done 2026-08-25] Add pure formatter cases for Z, offset-bearing and naive UTC
   forms; Denver cross-calendar-day, winter/summer and repeated-hour behavior;
   in-process timezone change; UTC regression; all named virtual-screen
   surfaces; compact responsive column behavior; unchanged canonical JSON;
   and a non-UTC real-PTY case.
5. [done 2026-08-25] Run the focused Message/Event/Poke/Teams/Work TUI suites,
   responsive/parity and real-PTY suites, then complete `just test-v11` and
   return for independent review and visual acceptance.

## Implementation — 2026-08-25

`local_stamp(value, compact=False)` in `src/baton_work/tui/app.py`, beside
`duration_cell`/`held_cell` so a reader looking for "how does this console
render time" finds the clocks and the durations together.

- Explicit `Z`/offset instants parse aware; Baton's canonical naive UTC
  spelling gets `datetime.timezone.utc` attached BEFORE conversion. That
  attachment is the whole defect: `astimezone()` on the naive form assumes the
  fields are already local, keeps the wrong number and adds a zone label
  swearing to it.
- `astimezone()` with no argument, at render time, so the daylight rule in
  force at THAT instant decides and a `TZ` change under a live process is
  honoured. Nothing is cached.
- `tzname()`, falling back to numeric `%z` rather than dropping the context.
- Full `2026-08-24 18:36:19 MDT`; compact `18:36 MDT`.
- Absent renders `""` so each caller keeps its own absent spelling; an
  unparseable value is returned verbatim rather than crashing the console over
  the operator's screen.

Every site the reviewer inventoried now goes through it: `format_message`,
`_message_cells`, `_event_lines` (header and claim interval), `_event_row`,
`_poke_stamp` and its three callers, `_detail_pickup`, `_detail_runner` (four
fields) and `_detail_answer` (two). The elapsed cells are untouched.

The compact columns MEASURE the formatted value — `message_time_width` and
`event_time_width`, the idiom `message_cue_width` already established — and the
declared five is a floor. `event_index_width` raises the Events index PANE with
it, which the constant `EVENT_INDEX_WIDTH` could not: a measured `TIME` inside
a pane sized from the declared widths would have been dropped at every terminal
size, so the pane would never have offered it the cells.

Two defects the reviewer's boundary did not name but the work found:

- **The poke stamp's truncation is superseded, not extended.** It cut at the
  minute on the reasoning that a zone marker was spent on nothing a live reader
  needs. That was true only while the marker was `Z`. It is false for a local
  instant — the zone is what says the number is the operator's own clock — and
  the poke table already measures the cell and drops it whole, so the width is
  not bought by removing the field that makes the rest legible.
- **`_detail_answer`'s `Retry at` was raw UTC**, passed through with no
  formatting at all. It is in the inventory's site list and is now converted
  like the rest.

## Verification — 2026-08-25

- `tests/work/test_w8160_local_time.py`, 30 cases: the pure formatter over all
  three input forms, Denver cross-calendar-day, naive/`Z` equivalence,
  MST-versus-MDT, the repeated fall-back hour, an in-process `TZ` change across
  three zones, the nameless-zone numeric fallback, a UTC host, the elapsed
  helpers proved timezone-invariant, every inventoried surface, the responsive
  columns at every width from 20 to 70, byte-identical canonical pages across
  rendering, and two real-PTY cases.
- The second PTY case CHOOSES its zone from the instant (UTC-11 or UTC+14) so
  the cross-day rule is exercised whatever hour the suite runs at; a fixed zone
  would have proved it for part of the day and silently proved nothing for the
  rest. Both PTY cases assert the exact expected local rendering rather than
  the presence of a label, because a console that appended `MDT` to an
  unchanged UTC number would pass the weaker check.
- `tests/work/test_w49_message_index_columns.py` superseded IN PLACE: the
  `Time` cell is wider, so a full row needs 44 cells rather than 34 and `Time`
  drops at 34 rather than 30. Every rule W49 states is unchanged; `WIDEST` and
  `_time_cell` are the two places that now hold the arithmetic.
- `docs/BATON-WORK.md` states the rule concisely; the canonical command and
  JSON examples remain UTC.

## Independent review — 2026-08-25

Status: **signed off** in `review-2026-08-25T09-12-34Z.md`.

6. [done] Independent inspection confirmed the shared formatter, complete
   absolute-time site inventory, elapsed-duration exclusions, responsive
   whole-column behavior, unchanged canonical UTC boundary, and the required
   timezone/DST/PTY regression matrix.
7. [done] Independent focused, adjacent and full v11 gates are green. No
   review finding remains; W8160 may close satisfying.
