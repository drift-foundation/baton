# Plan: render TUI timestamps in host-local time

1. [pending] Inventory every human-facing TUI timestamp and the parsers feeding
   it; keep protocol/JSON serialization outside the patch boundary.
2. [pending] Add one timezone-aware local formatter and use it consistently in
   Message, Event, Work and Teams views.
3. [pending] Add non-UTC, cross-calendar-day and UTC regression coverage.
4. [pending] Run focused TUI, real-PTY and complete v11 gates, then return for
   independent review and visual acceptance.

