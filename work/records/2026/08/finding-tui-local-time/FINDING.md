# Finding: render TUI timestamps in host-local time

## Observed — 2026-08-24

The Message detail view rendered `2026-08-25 00:36:19` without a timezone
label while the synchronized host clock reported:

```text
Local time: Mon 2026-08-24 23:10:11 MDT
Universal time: Tue 2026-08-25 05:10:11 UTC
Time zone: America/Denver (MDT, -0600)
```

The displayed instant was UTC, but its missing `Z`/`UTC` marker made it look
like a future local timestamp. It also made comparison with terminal and
system-service activity unnecessarily difficult.

## Confirmed decision — 2026-08-24

Canonical storage and JSON/protocol timestamps remain UTC. Human-facing TUI
timestamps are converted at render time through the host's configured local
timezone. A full date/time includes the effective timezone abbreviation, for
example `2026-08-24 18:36:19 MDT`; compact time-only displays must have an
equally visible local-time context rather than silently presenting an
unlabelled UTC wall clock.

Conversion must honor the active system timezone and daylight-saving offset;
the TUI must not encode a fixed offset or reinterpret a naive timestamp as
local time.

## Acceptance

- Message, Event, Work and Teams timestamps use one shared local-time
  formatter.
- Full timestamps visibly include the effective timezone abbreviation.
- Canonical JSON and persisted values remain unchanged in UTC.
- Tests exercise a non-UTC timezone and a date where the local calendar day
  differs from UTC, and protect UTC hosts from behavioral regression.

## Reviewer inventory and implementation boundary — 2026-08-25

**Observed:** every absolute timestamp painted by the TUI is formatted ad hoc
inside `src/baton_work/tui/app.py`. The complete current set is:

- Message detail metadata at `format_message` and the compact Message index at
  `_message_cells`;
- Event detail metadata and claim-interval start at `_event_lines`, plus the
  compact Event index at `_event_row`;
- Poke table and detail timestamps through `_poke_stamp`;
- Teams member detail: pickup `Since`; runtime `Since`, `Last contact`, `Lease
  expires`, and refresh request; last-poke-answer `At` and `Retry at`.

The Jobs and Teams table `Held`/`Since` cells, operational-fact age, phase
duration, and pickup wait are elapsed durations. They are timezone-invariant
and stay on `held_cell`/`duration_cell`; converting those as wall clocks would
be a regression. Work-level absolute instants presently appear in its Message
and Event pages, including claim-interval metadata.

**Confirmed input forms:** canonical projections expose both explicit `Z`
instants such as `2026-08-25T05:17:35.151Z` and UTC storage strings without an
offset such as Message `ts = 2026-08-25 05:11:03`. The shared formatter must
normalize both as UTC instants before conversion. Calling `astimezone()` on a
naive parsed Message timestamp would reinterpret the UTC fields as already
local and silently preserve the defect.

**Proposed implementation boundary:** add one module-level presentation helper
with full and compact modes. Parse `Z`/offset-bearing ISO values as aware
instants; explicitly attach `datetime.timezone.utc` to Baton's canonical naive
UTC storage spelling; call `astimezone()` at render time so the active host
timezone and the historical DST rule for that instant decide the result. A
full value renders `YYYY-MM-DD HH:MM:SS ZONE`. A compact value renders
`HH:MM ZONE`. If `tzname()` is empty, use the numeric `%z` offset rather than
dropping timezone context.

Compact zone labels must not be clipped back to an ambiguous five-character
wall clock. Message and Event time-column widths should be derived from the
formatted values (as the Poke table already derives `Asked`) and the whole Time
column should continue to drop under width pressure. Full values wrap through
their existing detail layouts.

**Confirmed patch boundary:** this is TUI presentation only. Do not alter the
store, projection timestamp fields, JSON API, operation signatures, projection
version, elapsed-time helpers, or authority clock. Repository documentation
needs only a concise statement that displayed absolute instants are host-local;
canonical command/JSON examples remain UTC.

**Required regressions:**

- `TZ=America/Denver` converts `2026-08-25T00:36:19Z` to the prior local date
  with `MDT`, and the naive UTC Message spelling yields the identical instant;
- winter and summer instants prove `MST` versus `MDT`; the repeated 01:30 hour
  at fall-back remains distinguishable by its zone label;
- changing `TZ` plus `time.tzset()` during one process affects the next render,
  proving the timezone was not cached;
- Message, Event, Poke, Work claim metadata, and Teams member details all pass
  through the shared formatter; compact responsive tables retain or drop the
  entire zone-bearing Time cell, never only its suffix;
- `TZ=UTC` preserves the wall-clock value while adding `UTC`, and canonical
  JSON/projection values remain byte-for-byte unchanged;
- one real-PTY case runs with a non-UTC `TZ` and observes the cross-day local
  timestamp and zone on screen.

Evidence: `evidence/reviewer-inventory-2026-08-25.txt`.

## Independent review outcome — 2026-08-25

**Confirmed:** the implementation satisfies the recorded decision and patch
boundary. Every inventoried absolute TUI timestamp uses the one host-local
formatter with visible zone context; canonical naive UTC is attached before
conversion; elapsed durations remain unchanged; responsive compact columns
retain or drop the complete value; and storage/projection/JSON remain UTC.

Independent focused, adjacent, real-PTY and complete v11 gates are green. The
append-only review is `review-2026-08-25T09-12-34Z.md`. No review finding
remains.
