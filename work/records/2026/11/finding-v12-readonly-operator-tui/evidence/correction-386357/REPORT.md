# W386308 correction after review 2026-11-26T03-55-01Z

By `baton.claude` under claim E386357 (the same session that wrote the contract as K; it does not review this). Two defects, both reproduced by the reviewer, both corrected in one delta.

## Identity

- Delta `delta.patch`, SHA-256 `00d4edcf4ad5728e232fee1626d97ba027d59ffddf91e5877b72b3c8a2e77e11`, two paths, applies with `patch -p1` on top of base `7961f8bd` plus the first candidate patch `92d60ea9…`.
- `combined.patch` is the whole candidate against the base in one file; `manifest.json` has its digest and all eight file digests.
- The working tree holds the same bytes for seven paths; `v12/DESIGN.md` there carries unrelated changes, as before.

## 1. A terminal of exactly 60×8 was refused

Cause: the curses loop passed `columns - 1` to `frame`, so layout ran one column short of the real terminal and a 60-column terminal looked like 59.

Change (`tools/job_tui.py`, `run`): the real dimensions go to `frame`; each line is painted at full width, and the one error curses reports for writing the bottom-right cell is tolerated at paint time, where it belongs.

Regression: `TheRealProgram.test_case_11_the_real_program_accepts_exactly_60_by_8_and_refuses_one_less`. The real program under a pseudo-terminal sized with `TIOCSWINSZ`: at 8×60 it draws the Job and never says "terminal too small"; at 8×59 and at 7×60 it says so; `q` exits 0 each time.

## 2. The tail of a tall selected phase could not be reached

Cause: the detail window kept the selected block's first line in view and moved only between phase identities, so the lines of a block taller than the screen were unreachable.

Change (`tools/job_tui.py`): the state gains `stage_line`. When the selected phase has more lines than fit, the screen shows that phase alone: its first line stays pinned and selected, and `↑`/`↓` (and `PgUp`/`PgDn`) move through its remaining lines. Only at its last line does `↓` go to the next phase, and only at its first does `↑` go to the previous one, arriving at that phase's last lines. `Home` goes to the first phase's first line, `End` to the last phase's last lines. The key line becomes ` ↑↓ lines (N above, M below)   Esc back   r read   q quit`. A refresh keeps both the phase and the line. A screen tall enough for everything behaves as before.

Regressions:
- `TheDetailOfALongPhase.test_case_06_the_last_fact_of_a_tall_phase_is_reachable_and_the_phase_stays_selected`: on 8×80, every line of the phase is shown at some point by pressing `↓`, the phase identity and its pinned first line stay selected throughout, the hint counts are exact, the last fact and the model line are reached, a refresh in the middle keeps phase and place, `↓` then leaves to the next phase, `↑` returns and walks back to the first line, and the first frame is reproduced exactly.
- `TheDetailOfALongPhase.test_case_10_page_home_and_end_within_and_between_tall_phases`.

## Verification

On a clean archive of the base plus both patches, prepared interpreter, empty environment: `tests.tools.test_job_tui` (now 20 tests), `test_job_viewer`, `test_job_observation`, `test_stack`, `test_attempt_diagnostics`, `test_work_command` and the single registry test: 450 tests, all pass, no skip (`focused.log`).

## Still not shown

A packaged bundle with the `tui` verb; a real operator terminal beyond the pseudo-terminal cases. Long single lines are still cut with `…` and cannot be scrolled sideways; that is the contract's rule, and I am naming it because the field snapshot's locator and model lines are longer than 80 columns.
