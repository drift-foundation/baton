# TUI list refresh can appear stalled until restart

Status: **observed by Slawomir; diagnosis protocol pinned 2026-08-11; root
cause unconfirmed.**

## Report

Slawomir reported that new messages once stopped arriving/appearing in the TUI
list view and became visible only after quitting and restarting. There is not
yet enough retained evidence to distinguish an authority/publication problem,
an active filter/view issue, a refresh failure that deliberately kept the old
coherent rows, an event-loop/timer stall, or a refreshed model that was not
rendered.

Do not merge this with the agent-runner wakeup problem without evidence. The
TUI polls its list APIs every two seconds; Baton `wait` is a separate agent
readiness operation. The 2026-08-10 timing captured in
`work/finding-agent-wakeup/FINDING.md` was recovered by the waiter's safety
rescan and the TUI then refreshed, so that earlier event did not demonstrate
this defect.

## Confirmed current paths

- The TUI event loop calls `InboxState.refresh(store)` every two seconds.
- `Ctrl+r` invokes the same public refresh immediately.
- Refresh failures keep the prior coherent rows and put the failure in the
  status bar; stale-but-labelled is intentional.
- `/` search can hide nonmatching rows after the search box is accepted.
- `scan --participant ADDRESS` and `doctor` are read-only authority views.
  They do not claim a directed message or see a notice.
- There is currently no supported command that snapshots the live TUI's
  in-memory row/filter/cursor/timer state from another process. If that missing
  observability prevents diagnosis, that inability is part of this finding;
  do not read SQLite or attach an improvised state mutation workaround.

## Incident protocol — keep the TUI open

When this recurs, **do not quit first**. Preserve the stuck process until these
observations are captured:

1. Record the wall-clock time, participant, exact TUI executable/config, active
   view, selected row, header, status bar, and whether a filter banner/query is
   visible. Capture a screenshot or terminal transcript if practical.
2. In a separate terminal, using the deployment-supplied exact Baton executable
   and config, run:

   ```text
   BATON_BIN --config BATON_CONFIG scan --participant SAME_PARTICIPANT
   BATON_BIN --config BATON_CONFIG doctor
   ```

   Preserve both JSON results and the time. Do not run `claim`, `see`, raw SQL,
   or a second readiness waiter merely to diagnose the list.
3. If the missing message/notice is known, record its id, subject, author,
   publication time, and whether `scan` reports it. This separates “authority
   does not have/route it” from “authority has it but this TUI does not draw
   it.”
4. With the original TUI still open, press **Ctrl+r once**. Record the status
   text and whether the row appears. Do not press Enter on the row as part of
   diagnosis; that may claim/see it.
5. If the header showed an active filter and the row is still absent, record
   that fact, then use `/` followed by Esc once to clear the filter and record
   whether the row appears. Also confirm the intended MESSAGES/Sent/Archived
   view; do not silently treat a row hidden by the chosen view as a refresh
   failure.
6. Only after those captures, quit and restart if needed. Record whether the
   same executable/config immediately shows the row and whether its authority
   state changed. Restart is a recoverable stopgap after evidence capture, not
   the diagnosis or fix.

## Interpretation matrix

- `scan` lacks the item: investigate publication, participant/audience, or
  authority state rather than TUI refresh.
- `scan` has it; Ctrl+r shows it: automatic timer/event-loop refresh stalled.
- `scan` has it; clearing the visible filter shows it: search behaved as a
  filter, though discoverability/status may still be a UX finding.
- `scan` has it; Ctrl+r succeeds but the row remains absent until restart:
  investigate live model/view/filter/row reconstruction and rendering.
- Status reports a refresh failure: preserve the exact text and diagnose that
  underlying list/scan call; the old rows remaining are expected fail-safe
  behavior.
- `doctor` is not healthy: diagnose authority integrity first and do not infer
  a TUI-only defect.

## Evidence needed for implementation

Before code changes, revalidate the then-current event loop, timer scheduling,
refresh guards, filters/views, and render invalidation. A focused reproduction
must identify which branch above occurred. If live-state observability is the
blocker, propose a read-only diagnostic surface that exposes last refresh
attempt/success, row counts, active filter/view, and last failure without
content bytes or authority writes.

