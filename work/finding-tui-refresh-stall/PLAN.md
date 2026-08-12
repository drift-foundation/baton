# Plan — diagnose TUI refresh stall

1. **Use the incident protocol first** — keep the stuck TUI open; capture
   screen/status/view/filter, read-only `scan` and `doctor`, one Ctrl+r result,
   filter-clear result if applicable, and restart comparison.
2. Classify the incident as authority/routing, refresh call failure,
   timer/event-loop stall, active filter/view, model reconstruction, or render
   invalidation. Do not implement from the historical restart-only report.
3. Build the smallest deterministic reproduction for the classified branch,
   including a new arrival while the TUI remains open and a manual-refresh
   comparison.
4. If the live process cannot expose enough state, rule and implement a
   read-only diagnostic surface before attempting a speculative refresh fix.
5. Add focused state/driver/PTY regressions, independent review, and a human
   soak recurrence check. Preserve the frozen 1.0 artifacts and live authority.

