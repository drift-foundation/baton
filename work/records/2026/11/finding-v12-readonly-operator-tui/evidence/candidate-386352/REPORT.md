# W386308 candidate — read-only TUI, first slice

Implemented by `baton.claude` under claim E386352 (this is the same interactive Claude session that prepared the contract as K, `baton.prompt`; it does not review its own candidate). Host workflow; no native Job, engine, provider or credential.

## Identity

- Base `7961f8bd4f5aae1209c72f796acb693d5ba65b76`. Patch `candidate.patch`, SHA-256 `92d60ea9b4db2d07ea6d3ba47a6b7bfd183c74aef462d7c86b0d392057738c4a`, plain unified diff, apply with `patch -p1`. Per-file digests in `candidate.json`.
- Eight paths: `v12/python/tools/job_tui.py` (new), `v12/python/tests/tools/test_job_tui.py` (new), `v12/python/tools/stack.py`, `v12/python/tools/stack_command.py`, `v12/python/tools/parallel_test.py`, `v12/python/tests/tools/test_work_command.py`, `v12/python/JOB-VIEWER.md`, `v12/DESIGN.md`.
- Applied to a clean archive of the base, the patch reproduces all eight digests. The working tree holds the same bytes for seven paths; `v12/DESIGN.md` there also carries unrelated uncommitted changes, so import the OBS-2 hunk from the patch.
- Main is `38ea1a07`, which differs from the base only in `packaging/stack.spec` and `tests/tools/test_packaging.py`; the patch touches neither.
- `tools/job_observation.py` and `tools/job_viewer.py` are not edited.

## What it is

`tools/job_tui.py`: `settle`, `step` and `frame` are pure functions over a state value, a key name and a snapshot; `Session` joins them to `job_viewer.JobViewer`; `run` is the only code that touches `curses`. Every word shown is a string `job_observation.job_view` returned. Reached as `baton-v12-stack tui --instance …` and `python3 -m tools.job_tui --status PATH`.

## Contract cases and their tests (`tests/tools/test_job_tui.py`)

| # | Test |
| --- | --- |
| 1 | `TheList.test_case_01_one_row_per_job_with_headline_reason_and_counts` |
| 2 | `TheList.test_case_02_the_retained_a1_case_carries_exactly_the_read_models_strings` |
| 3 | `TheList.test_case_03_a_selected_job_that_comes_to_need_a_decision_changes_in_place` |
| 4 | `TheList.test_case_04_the_selection_follows_its_job_through_insertion_and_reordering` |
| 5 | `TheList.test_case_05_a_vanished_job_is_one_line_and_never_stale_content` |
| 6 | `TheDetail.test_case_06_the_selected_phase_is_kept_and_a_vanished_one_is_one_line` |
| 7 | `Freshness.test_case_07_stale_at_fifteen_seconds_on_both_screens_and_fresh_again` |
| 8 | `Freshness.test_case_08_a_failed_read_says_why_and_keeps_the_last_good_content` |
| 9 | `Freshness.test_case_09_no_status_file_at_start_says_not_read_yet_and_stays_up` |
| 10 | `Keys.test_case_10_every_key_at_the_top_middle_and_bottom_and_unknown_keys` |
| 11 | `Keys.test_case_11_narrow_wide_long_and_resized_terminals_keep_the_selection` |
| 12 | `TheRealProgram.test_case_12_q_ctrl_c_and_sigterm_restore_the_terminal_and_leave_nothing` |
| 13 | `ItOnlyReads.test_case_13_a_whole_session_opens_only_the_status_file_read_only` |
| 14 | `TheRealProgram.test_case_14_without_a_terminal_it_refuses_with_exit_2_and_draws_nothing` |
| 15 | `WhatItIsBuiltOn.test_case_15_manual_jobs_show_the_read_models_labelled_headline_and_counts` |
| 16 | `WhatItIsBuiltOn.test_case_16_it_edits_nothing_it_is_built_on_and_is_reachable_beside_monitor`, plus the unchanged existing modules below |
| 17 | `WhatItIsBuiltOn.test_case_17_a_review_held_for_its_report_shows_the_read_models_sentence` |

## Verification

Run on the reconstruction (clean archive of the base plus the patch), prepared interpreter, empty environment, fixture roots outside the checkout. Log: `focused.log`.

- `tests.tools.test_job_tui`, `test_job_viewer`, `test_job_observation`, `test_stack`, `test_attempt_diagnostics`, `test_work_command` and the single registry test `tests.tools.test_parallel_runner.TheRealRegistryDescribesTheRealTree.test_every_v12_test_module_is_registered_exactly_once`: 447 tests, all pass, no skip, 49 s.
- Case 12 ran, under a pseudo-terminal the test allocated itself: `q` and `Ctrl-C` exit 0, `SIGTERM` exits 143, terminal attributes restored each time, no process left in the child's group. Case 14: exit 2 and the refusal line with standard output a pipe.
- The verification runner prepared for the native packet (`verify_w386308.py`) also exits 0 on this candidate: 398 collected, executed and passed; the TUI module carries 17 tests; registry and disk-dependent ids ran.
- Affected logical group: tools-pure. Not run: any whole group, `tests.manager.test_checkpoint_profiles`, any engine or packaged-bundle test.

## Test changes outside the new module

- `tools/parallel_test.py`: `tests.tools.test_job_tui` registered once, in the parallel registry beside the viewer tests.
- `tests/tools/test_work_command.py`: the test that pins the installed command table now also subtracts `tui`, the one verb this Work adds.

## Decisions I made that the contract left open, for the reviewer

- **DISCONNECTED line order.** The contract shows `!! DISCONNECTED <cause>`. I put the ages first (`!! DISCONNECTED last read 7s ago; observed <instant>; <cause>`) so that on a narrow terminal the long cause is what gets cut, not the ages.
- **Before the first good read.** After a failed first read the line is `not read yet: <cause>`, so the cause is visible without claiming a connection that never existed.
- **Vanished row position.** It stays where the identity last sat; moving from it selects the nearest row that exists.
- **`n`** wraps once to the first Job needing a decision and does nothing when there is none; on the detail screen it does nothing.
- **Extra keys** beyond the contract: `g`/`G` for Home/End, `l` to open, `h` to go back.
- **Ages** are formatted by this module (`41s`, `3m12s`, `2h05m`), because the read model's own formatter is private. No headline, reason, position or fact is formatted here.
- **The `tui` verb** does not refuse when no snapshot exists yet (unlike `monitor`); it starts at `not read yet`, as case 9 requires.

## Not shown

- The packaged bundle: I did not build one, so `baton-v12-stack tui` in a frozen build (that PyInstaller carries `curses` and `tools.job_tui`) is unverified.
- Behaviour on a real operator terminal beyond the pseudo-terminal cases: colours, very large Job counts, real resize events.
- Inside a worker container nothing was run; this was host implementation.
