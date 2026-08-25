# Plan: use `d` for the dependency view

**Status — 2026-08-23:** confirmed, reviewer-revalidated, and implementation
ready as independent v11 usability Work. It is safe to execute beside v12-only
Worker Manager work because the implementation surfaces do not overlap.

1. Revalidate that lowercase `d` remains unbound in every live TUI mode.
2. Change the Work-table and Search dependency handlers from `b` to `d`.
3. Replace the Work-table footer and all three current operator-guide
   references from `[b] deps` to `[d] deps`; Search has no existing dependency
   legend, so do not add a new layout surface here.
4. Update the existing table/Search, PTY, parity, and breadcrumb key fixtures
   to `d`, including the shared real-terminal `OPEN_CENTER` script and truthful
   live comments/docstrings.
5. Add explicit negative `b` regressions in both table and Search modes, plus
   a real-terminal no-alias observation, without changing graph behavior or
   protocol surfaces.
6. Run the focused test surfaces enumerated in `FINDING.md`, then `just
   test-v11`, and return for independent review.

**Implemented — 2026-08-23 (`baton.claude`).** Items 1-6 are done and the
acceptance boundary is met item by item.

1. [done] `d` revalidated unbound across every live dispatch path, including
   the `key in (...)` forms and the three `chr(key)` text-entry paths where
   `d` is typed text rather than a binding.
2. [done] Both branches — `Console._search_mode_key` and the Work-table branch
   in `Console.handle` — moved to `ord("d")`; `b` removed with no alias.
3. [done] The Work-table footer and all three `docs/BATON-WORK.md` references
   read `[d] deps`. No Search legend was added.
4. [done] Table/Search, PTY, parity and breadcrumb fixtures moved to `d`,
   including the shared `OPEN_CENTER` script; live prose in the touched suites
   made truthful. `test_w17_deps_label.py`'s docstring deliberately RETAINS
   the W17 `[b] deps` history and names its supersession.
5. [done] `tests/work/test_w96_dependency_key_d.py` adds the explicit negative
   `b` regressions in table and Search modes plus the real-terminal no-alias
   observation. Graph behaviour and protocol surfaces are unchanged.
6. [done] Focused surfaces 167 passed; `just test-v11` equivalent green —
   2980 not-serial, 52 serial, ACP 55. Five mutations, all witnessed.
   Evidence: `evidence/implementation-2026-08-23.txt`. Returned for
   independent review at `baton.tune` per the T96 coordination message.
7. [signed off 2026-08-23] Independent review found no blocking issue. Both
   dispatch paths, the no-alias boundary, footer/docs and unchanged graph
   semantics are covered; the nine-file focused surface passed 167/167.
   Pass to `baton.tune` for the recorded post-review polish, including the
   non-blocking W17/W96 attribution note. Review:
   `review-2026-08-23T15-59-51Z.md`.
8. [done 2026-08-23, `baton.tuner`] Sharpened the W17/W96 attribution in
   `test_w17_deps_label.py`; its two focused PTY cases pass and whitespace is
   clean. No behavioral surface changed.
