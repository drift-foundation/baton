# Plan

1. [done] Remove the synthetic missing-log row while preserving published
   operational facts: `Console._detail_facts()` in
   `src/baton_work/tui/app.py`, plus the `Log` paragraph in
   `docs/BATON-WORK.md`.
2. [done] Supersede the old absent-log expectation in focused Teams tests and
   cover mixed participants and empty diagnostics:
   `tests/work/test_w1578_omit_unpublished_log.py`, and the retired case in
   `tests/work/test_w184_member_detail_table.py` replaced by its superseding
   statement.
3. [done] Run focused TUI tests and the complete v11 gate: 359 focused,
   then 2633 parallel / 51 serial / 55 ACP.
4. [done 2026-08-20] Independent review signed off with no findings in
   `review-2026-08-20T11-38-27Z.md`.
