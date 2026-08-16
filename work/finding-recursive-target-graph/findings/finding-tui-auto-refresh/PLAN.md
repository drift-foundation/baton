# Plan

Queued with the other non-blocking findings from the first human trial. Do not
interrupt the trial or patch the published immutable release for this item.

1. Choose and document the explicit positive-seconds configuration surface;
   default to 2 seconds.
2. Add a bounded curses timeout that alone performs background canonical
   projection reads; ordinary keystrokes use cached state and do not poll the
   authority.
3. Preserve logical selection across inserted, removed, and reordered rows.
4. Prove that refresh performs no seen receipt, obligation consumption, audit
   act, or other mutation.
5. Exercise the installed TUI on a real PTY, then run focused and full v11
   gates before the next distribution.
