# Plan

1. [done] Reproduce the contract gap from the live trial and locate the input
   boundary that bypassed the synthetic-key tests.
2. [done] Enable real-terminal cursor decoding at the curses runner boundary.
3. [done] Add packaged-PTY cursor, bare-Esc, and refresh-independence
   regressions, including the raw-cursor refresh-deadline case requested by
   the first independent review.
4. [done] Run focused tests and the full v11 gate, then receive independent
   sign-off in `review-2026-08-18T04-44-39Z.md`.

**Note — 2026-08-18:** step 2's premise ("enable real-terminal cursor
decoding") was based on a diagnosis the implementation disproved; keypad
translation was already enabled by `curses.wrapper`. The step was
delivered as the correction the measurement actually called for. See
`PROGRESS.md` and the amendment in `FINDING.md`.
