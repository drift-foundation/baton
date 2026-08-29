# Plan

Status: implementation-ready bounded v11 correction as Baton Work `W29146`.

1. [done 2026-08-28 UTC] Reproduce the mismatch: global Teams attention from
   `pc.slaw`/W12181, hidden by the default `baton.slaw` roster and the
   team-scoped Jobs search.
2. [done 2026-08-28 UTC] Revalidate against confirmed v11 pickup/search rulings
   and the v12 shared-principal roadmap. Existing rulings require a bounded v11
   correction now; v12 principal aggregation remains separate.
3. [done 2026-08-28 UTC] Pin the attention/findability contract: default Teams
   is own team plus every overdue cross-team exception, starred entry focuses a
   cause, Enter follows the canonical suggested-Work link, and search remains
   team-scoped while stating its scope in JSON/TUI.
4. [pending implementation] Add the focused cross-team, multiple-offender,
   own/all mode, focus, explicit-link, identity-style, pickup-transition,
   refresh, search-scope, projection-version and PTY regressions recorded in
   `FINDING.md`.
5. [pending implementation] Apply the bounded TUI/search-projection/docs patch;
   create implementer-owned `PROGRESS.md`; run focused and full gates; pass for
   independent review.

## 2026-08-28 — implementer round

- [done] 4. The recorded regression matrix, as
  `tests/work/test_w29146_cross_team_attention.py`: 29 cases over the star and
  roster, entry focus, multiple offenders, `t` browsing, pending, identity
  versus overdue styling, the explicit link and its Back, the pickup
  transitions, search scope, the projection minor, a narrow terminal and the
  one-snapshot guarantee.
- [done] 5. The bounded patch: attention-aware `team_rows`/`team_exceptions`/
  `_team_scope`, `_focus_attention`, the own-participant fallback, the
  suggested-Work `Enter` with an explicit restore frame, the team-qualified
  search heading and empty copy, additive `team` on the `search` result,
  projection 12.8 with its exact pins advanced, `BATON-WORK.md` and the CLI
  help. `PROGRESS.md` created; focused, full and mutation gates run; passed
  back for independent review.
- [done 2026-08-28] Independent review accepted the bounded v11 correction.
  Focused 29, Teams/search/navigation compatibility 124, and projection/
  ordering compatibility 240 are green; see
  `review-2026-08-28T13-49-33Z.md`.
