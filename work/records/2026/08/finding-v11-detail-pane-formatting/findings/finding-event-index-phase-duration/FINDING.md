# Finding: Event rows drift and omit scheduler-phase duration

## Observed

`WorkTUI._paint_event_index()` currently concatenates `E<seq>`, an unbounded
event kind, `HH:MM`, and actor into one string. Later fields therefore start at
different cells. `work-events` projects claim intervals, but it does not expose
the queued, active, waiting, and parked episodes that make up the Work's
scheduler history.

## Confirmed decision — 2026-08-18

Render the Event index as a compact fixed-column table. Its responsive column
sets preserve, in priority order, the stable Event id, typed kind, actor,
event time, scheduler phase, and phase duration. Each chosen set has one header
and fixed field starts; if width is insufficient, an entire lower-priority
column disappears rather than truncation moving another column.

The canonical `work-events` projection exposes a typed `phase_interval` for
every scheduler-phase episode:

- the phase (`queued`, `active`, `waiting`, or `parked`);
- start event sequence and timestamp;
- optional end event sequence, kind, and timestamp;
- elapsed whole seconds; and
- whether the interval is still open at the projection snapshot.

The phase-entry event owns the table's phase and duration cells. A later
boundary may expose the same interval in its complete reader details, as claim
intervals already do, but the index must not show one episode twice. Creation
starts the initial phase; claim, pass, release, gate, explicit phase change,
and close boundaries end or start episodes according to the authoritative
transition. Heartbeats never split or reset an episode.

The TUI renders elapsed whole seconds as `00:00` through `99:59`, then `∞` at
100 minutes and beyond, reusing the already confirmed Held scale. An open
episode advances from the projection read instant; a completed episode never
changes. A row without a phase interval renders `-`. JSON carries structured
seconds and timestamps, never the glyph or formatted timer as authority.

This is derived from the append-only event ledger and needs no persisted
schema change. The projection, not terminal clock arithmetic, owns the interval
facts so TUI and non-TUI clients agree.
