# Progress

No implementation has started. The confirmed display-order ruling is pinned
and awaits independent review.

## 2026-09-06 — baton.tuner

Implemented the reviewed ordering split in the two authorized paths.
`DISPLAY_WORK_ORDER` now gives human `home`, `children`, every `tree` sibling
query, and hidden-claim structural ranking explicit priority followed by
creation sequence and durable Work identity. `DISPATCH_WORK_ORDER` retains the
existing blocker rank for `participant_actions`, `_first_actionable`, and
`actionable_work`; the dispatch key and total key continue to own the existing
cursor semantics.

Updated the W7 regression owner to supersede shared-order expectations. Its 19
focused cases pass, including equal-priority siblings where the earlier Work
becomes active and the later Work becomes a ready dependency blocker: the TUI
render refresh keeps the earlier identity selected at the same row while
readiness offers the later blocker first. Search remains unchanged.

The complete `just test-v11` gate reached 3,338 passes and one failure. The
only failure is the pre-existing
`tests/work/test_tui.py::test_the_focused_facts_and_collapse_come_from_the_projection`,
whose fixture commentary and `j` keystroke explicitly assume W7's now-
superseded human blocker-first order. The frozen scope does not authorize that
test path, so it was not edited. A minimal scope expansion for that single
legacy expectation is required before the complete gate can pass.

State: bounded candidate preserved; returning for one-test-path authorization.

## 2026-09-06 — baton.tuner completed candidate

Applied the exact legacy-test correction authorized by
`review-2026-09-06T17-18-24Z.md`. In the one named `test_tui.py` case, the
initial Enter now opens the already selected earliest live Work, and revealing
closed rows uses one `j` to reach the second creation-ordered row. The adjacent
comment now states the stable display-order reason. All assertions, fixture
operations, and every other part of the file remain unchanged.

Verification:

- The corrected focused TUI test passed.
- The complete `just test-v11` gate passed: 3,339 primary tests, 54 selected
  adversarial follow-ups, and 129 ACP bridge tests.
- `git diff --check` passed for the exact three-path candidate.

Final SHA-256 digests:

- `src/baton_work/projection.py`: `b2efb4d0d6a145d693694c9936e0fdbd6e95c186faf860f0bed48d55fc64e51f`
- `tests/work/test_w7_blocker_preference.py`: `dc6c685694893d36aea920f1cb1de376a5081e07131c1fd9b5f95b2d781bcb5b`
- `tests/work/test_tui.py`: `b1813a9230748e524b3d7ff5abd7d7e13fca5b1ee385e1932b52a0b1c0c2d510`

State: implementation and bounded correction complete; awaiting independent
three-path candidate review.
