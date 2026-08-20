# Plan

1. [done] Reproduce the command-submit/Jobs-Enter crossover through a real
   terminal or PTY and identify the exact input-state transition.
   `repro_pty.py`; cause and correction pinned in `FINDING.md` under
   "Confirmed cause" and "Confirmed decision" (2026-08-19).
2. [done] Make one-line command submission consume its Enter without a
   timing-based suppression of later intentional input: `curses.nonl()` plus
   the `CR`+`LF` coalescing peek in `_read_key`/`_absorb_paired_linefeed`.
3. [done] Add success, refusal/read-only, refresh, and deliberate-follow-up
   Enter regressions: `tests/work/test_w1568_command_submit_enter.py`.
4. [done] Run focused TUI/PTY coverage and the complete v11 gate.
5. [done 2026-08-20] Independent review signed off with no findings in
   `review-2026-08-20T11-21-18Z.md`; the focused and complete gates pass.
