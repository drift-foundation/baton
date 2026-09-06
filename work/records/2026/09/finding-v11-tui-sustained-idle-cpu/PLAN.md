# Plan

1. [done] Reproduce and attribute the sustained idle CPU consumption. The
   event loop blocks correctly; unconditional two-second cache invalidation
   runs the expensive 140-row tree projection on every top-level page. See
   `evidence/RESULTS.md`.
2. [done; approved by owner 2026-09-06] Pin the bounded correction rule in FINDING.md: the timer performs a
   cheap sequence observation, unchanged state retains cached canonical data
   while presentation repaints, changed state invalidates once, and failed
   observation/projection consumes no phase-cue cycle.
3. [done] Implement only that v11 TUI scheduling/invalidation correction in
   `src/baton_work/tui/app.py`, using `Authority.last_seq()` as the existing
   canonical freshness token. Preserve immediate refresh after local writes,
   wall-clock deadlines under continuous input, cached Held repainting, and
   exactly-three-successful-timer-render phase cue consumption. Do not optimize
   projection SQL in this Work.
4. [done] Update the now-superseded unconditional-read expectation and add
   deterministic regression cases in `tests/work/test_w5_auto_refresh.py`:
   unchanged timer deadlines perform no tree projection; one external commit
   causes exactly one projection at the next deadline; repeated unchanged
   ticks remain cached; local successful mutations still refresh immediately;
   and a failed freshness observation neither invalidates nor consumes a cue.
   Revalidate the existing timer/render and blink assertions in
   `tests/work/test_w336_blink_drain.py` and the scheduled-tick/failure cases in
   `tests/work/test_w33_claim_age.py`; bounded assertion or expectation edits
   in those three named test files are explicitly scheduled where the new
   freshness rule requires them. Retain the real-PTY external-update and
   continuous-input coverage; do not add host CPU percentage as a regression.
5. [done 2026-09-06 after re-review] The first independent review in
   `review-2026-09-06T15-13-51Z.md` accepted the sequence-gated invalidation
   and requested one bounded non-table phase-cue correction. The correction
   and its cross-view regression are signed off with no findings in
   `review-2026-09-06T15-29-15Z.md`.
