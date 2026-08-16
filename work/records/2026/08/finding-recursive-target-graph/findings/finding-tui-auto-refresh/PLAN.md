# Plan

Queued with the other non-blocking findings from the first human trial. Do not
interrupt the trial or patch the published immutable release for this item.

1. Choose and document the explicit positive-seconds configuration surface;
   default to 2 seconds.
2. Add one refresh scheduler and canonical refresh path. A monotonic wall-clock
   deadline schedules background refresh; a successful local storage mutation
   schedules on-demand refresh; pending requests may coalesce. Ordinary
   keystrokes, pure reads, and refused commands neither poll nor schedule,
   postpone, or accelerate refresh.
3. Preserve logical selection across inserted, removed, and reordered rows.
4. Prove that refresh performs no seen receipt, obligation consumption, audit
   act, or other mutation.
5. Exercise the installed TUI on a real PTY, then run focused and full v11
   gates before the next distribution.
