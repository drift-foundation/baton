# Plan

**Status:** signed off in `review-2026-08-16T15-43-58Z.md`; same authority
schema.

1. Revalidate the claim/release/pass/close journal shape and project the
   timestamp belonging to the currently active claimant as `claimed_at`.
2. Keep JSON canonical: expose timestamp/null and derive the changing display
   value only in the TUI.
3. Add the final `Age` column and pure formatter for `MM:SS`, `HH:MM`, `99h+`,
   `-`, and negative-clock clamp behavior.
4. Compose with active/review hot styling, responsive column omission,
   selection, containment rows, refresh, claim transfer, release, and close.
   Remove indefinite hot-state `A_BLINK` styling atomically with the timer;
   retain only the approved three-scheduled-tick Phase-change blink. Bold Title
   and claim Age are the final steady hot cues.
5. Prove JSON/TUI parity for the claim fact, no extra authority reads between
   normal refreshes, baseline/restart cold state, timer-tick versus
   keystroke/redraw/immediate-refresh countdown behavior, and correct packaged
   behavior.
6. Run focused tests and `just test-v11`, then return for independent review.
7. Consume a phase-change blink cycle only after the scheduled canonical
   refresh succeeds; timer expiry followed by a failed read must retain the
   countdown for the next successful refresh.

## Follow-up — 2026-08-17

W33 is closed and remains historical. The confirmed `Held`/`HH:MM`
supersession is queued as new Work and specified in
`../finding-tui-held-duration/{FINDING,PLAN}.md`; it must not reopen or rewrite
W33.
