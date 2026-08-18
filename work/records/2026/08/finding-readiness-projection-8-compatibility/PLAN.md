# Plan

- [x] Reproduce the failure on both readiness paths.
- [x] Compare projection-8 `wait` output to the consumed typed contract.
- [x] Accept exactly projection majors 7 and 8 in the shared validator.
- [x] Extend positive and negative bridge regressions.
- [x] Add a release-current projection compatibility regression.
- [x] Run both bridge suites and the focused v11 projection tests.
- [x] Restart the source Codex bridge and K's source ACP bridge against the
  new authority. K's accepted review arrived through ACP, and W11 readiness
  arrived through the Codex bridge on projection 8.
- [x] Obtain independent review before the next commit/release. Claude's
  accepted review is recorded in
  `review-2026-08-18T02-15-00Z.md`.
