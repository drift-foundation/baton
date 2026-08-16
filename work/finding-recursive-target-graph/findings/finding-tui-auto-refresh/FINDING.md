# Finding: v11 TUI needs configurable automatic refresh

## Observed

The first real v11 trial showed that the console re-reads the canonical
projection only after a terminal input event. Its curses loop blocks in
`getch()` with no timeout. A Work created by another participant therefore
appears after a key or resize event, not because the console watches the
authority.

## Confirmed feature

The TUI refreshes its canonical projection automatically on a seconds-based
interval. The default interval is **2 seconds** and the interval is
configurable. Configuration accepts a positive seconds delay; the exact
operator surface is selected in the implementation plan and must be explicit
in current-facing documentation.

This remains polling, not inotify. No authority file or WAL path becomes a
public interface, and the console does not infer state from filesystem events.
Each refresh performs ordinary canonical reads through the already-open bound
authority.

An automatic refresh is read-only. It must not mark discussions seen, consume
obligations, move the cursor to a different Work merely because rows changed,
or perform any workflow transition. Tests cover an externally created Work
appearing without input within the configured bound, plus selection stability
and the absence of seen/audit mutations.

The immutable `6d1b944` trial remains unchanged. This is non-blocking feedback
for the next v11 distribution.

## Clarification: keystrokes do not poll the authority

**Confirmed by Slawomir during the same trial.** The configured timer is the
only background trigger for reading a fresh SQLite projection. Ordinary
terminal keystrokes operate on the cached projection and may repaint local
navigation, but receiving input does not itself query the authority. An
explicit workflow mutation may refresh from its committed result as needed;
that is not a background poll.

The complete clarified contract is also promoted as revision 1 of v11 Work
`26de18dd-W7` from discussion message sequence 10.

## Clarification: the interval is wall-clock based

**Confirmed by Slawomir on 2026-08-15.** Keyboard activity neither postpones
nor accelerates automatic refresh. Repeated keystrokes across a refresh
deadline continue to operate on cached state until the wall-clock deadline,
then the timer refresh occurs on schedule; the key itself is not the trigger.

A dedicated explicit refresh key may be considered later, but W5 does not
require one and ordinary keys never acquire refresh semantics implicitly.

## Clarification: one refresh scheduler

**Confirmed by Slawomir on 2026-08-15.** Timer expiry and a successful local
storage mutation are two producers of the same refresh request. The console
has one canonical refresh path: producers schedule refresh, the event loop
consumes it, and concurrent/pending requests may coalesce because refreshing
the same projection twice carries no additional meaning.

A successful local mutation schedules an on-demand refresh so its committed
result becomes visible without waiting for the timer. A refused command, a
pure read, and ordinary navigation do not schedule one. Mutations made by
other processes remain discoverable through the scheduled timer refresh.
This is a scheduler contract; an implementation may use a due flag rather
than a literal FIFO, but it must not grow separate refresh behaviors for the
timer and local actions.
