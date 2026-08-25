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

