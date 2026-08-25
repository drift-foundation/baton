# Progress — render TUI timestamps in host-local time

Implementer: `baton.claude`, claimed 2026-08-25.

## What was built

One module-level formatter, `local_stamp(value, compact=False)`, in
`src/baton_work/tui/app.py` beside `duration_cell` and `held_cell` — so a
reader looking for "how does this console render time" finds the clocks and
the durations in one place, which is the distinction the whole finding turns
on.

The conversion, in the order the defect requires it:

1. parse `Z` and offset-bearing ISO values as aware instants;
2. attach `datetime.timezone.utc` EXPLICITLY to Baton's canonical naive UTC
   spelling. This is the defect: `astimezone()` on the naive form assumes the
   fields are already local, keeps the wrong number, and adds a zone label
   swearing to it;
3. `astimezone()` with no argument at render time, so the daylight rule in
   force at that instant decides and a `TZ` change under a live process is
   honoured. Nothing is cached;
4. `tzname()`, falling back to the numeric `%z` rather than dropping the
   context — which would restore exactly the ambiguity being removed.

Full renders `2026-08-24 18:36:19 MDT`; compact renders `18:36 MDT`.

Every site the reviewer inventoried routes through it. The elapsed cells —
`Held`, Teams `Since`, the pickup wait, phase duration, operational-fact age —
are untouched, and a case proves they are identical across two zones.

The compact index columns MEASURE the formatted value (`message_time_width`,
`event_time_width` — the idiom `message_cue_width` already established) and the
declared five is a floor. `event_index_width` raises the Events index PANE with
it: a measured `TIME` inside a pane sized from the constant would have been
dropped at every terminal size, so the pane would never have offered it the
cells.

## Two things the boundary did not name and the work found

- **The poke stamp's truncation is superseded, not extended.** It cut at the
  minute on the reasoning that a zone marker was spent on nothing a live
  reader needs. True while the marker was `Z`; false for a local instant,
  where the zone is what says the number is the operator's own clock. The poke
  table already measures the cell and drops it whole, so the width is not
  bought by removing the field that makes the rest legible.
- **`_detail_answer`'s `Retry at` was raw UTC**, passed through with no
  formatting at all. It is in the inventory's site list and is converted now.

## Verification

`evidence/gate-after-2026-08-25.txt`. `just test-v11` is green — 3067 + 52
pytest cases and 55 ACP cases, exit 0 — and was green before this claim, so
there is no red baseline to diff against and none was created.
`tests/work/test_w8160_local_time.py` is 30 cases covering every item in the
finding's required-regressions list, including two real-PTY cases that assert
the exact expected local rendering rather than the presence of a zone label.

Two existing suites are superseded IN PLACE, each naming the ruling and
keeping the property it was written for; the arithmetic that moved is now in
one constant and one helper rather than spread across six slices.

## State

**Awaiting independent review and visual acceptance.** The claim is not
released and no Git operation was performed.
