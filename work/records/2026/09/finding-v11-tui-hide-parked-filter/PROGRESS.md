# Progress

Not started.

## 2026-09-06 — baton.tuner

Implemented the approved two-file TUI change. On a Jobs table, `f` now opens
one client-local chooser whose first option is `[p] Parked`; `p` toggles parked
row visibility and closes the chooser, while Esc cancels without changing the
view. The ordered option definition is the extension point for later approved
toggles, but this Work implements only parked visibility.

The filter is never sent to projection, readiness, JSON, or SQLite. Its active
state is disclosed as `Hide:parked` in the Jobs header and on a dedicated
`hide: parked (f changes)` line. The existing projection filter remains a
separate disclosure. Row reduction composes after closed-row visibility, so
`z` and the parked toggle coexist, and restoring parked Work uses the stable
structural order from W103313. If the selected parked row disappears, the
existing cursor position deterministically selects the next visible row (or
the preceding last row at the end); an empty result clears both cursor and
identity.

Added real-terminal and in-process regressions covering the chooser text,
activation, reversal, cancellation, refresh retention, selected-row repair,
stable restoration, coexistence with closed Work, and an unchanged authority
sequence.

Verification:

- The two new focused cases passed.
- Complete `tests/work/test_tui.py`: 33 tests passed.
- Complete `just test-v11`: 3,341 primary tests, 54 adversarial follow-ups,
  and 129 ACP bridge tests passed.
- `python3 -m py_compile` and `git diff --check` passed for both authorized
  paths.

Candidate SHA-256 digests:

- `src/baton_work/tui/app.py`: `c3b917ec467f01dc3bc1dc8566274f405d5c3b993b407effd1c133907b387872`
- `tests/work/test_tui.py`: `acc328ad0bd341b9214ca107f697c396885ab273c77308115e2629c4bbd4faf3`

State: implementation complete; awaiting independent two-path review.
