# Plan

**Status — independently signed off 2026-08-18.** The narrow W4/W101 test
conflict is corrected without weakening either boundary; see
`review-2026-08-18T15-27-54Z.md`. W4 may close satisfying and release W5, W6,
and W20.

1. [done] Inventory v10-only source, build inputs, compatibility code, tests,
   and Codex monitor paths; separate W102 deployment/data and W103/W104 prose.
2. [done] Prove the v11 package/deployer imports only `baton_work` plus the
   retained ACP and generic/v11 Codex bridge modules.
3. [done] Remove the approved v10-only runtime surface and obsolete tests.
   Reduce shared Codex configuration rather than deleting its retained generic
   transport. Keep `tests/conftest.py` with only v11-relevant setup.
4. [done] Make the Justfile honestly v11-only: no generic command may retain
   hidden v10 behavior, and no removed recipe may point at absent tooling.
5. [done] Run `just test-v11`, the retained Codex-event-bridge tests, focused
   v11 deployment/package checks, a scratch distribution inventory, and
   `git diff --check`; return for independent review.
6. [done] Replace the stale assertion forbidding the implementation token
   `assignedParticipants` with behavior coverage that rejects retired v10
   stack configuration while retaining W101's participant identity uniqueness
   guard; rerun the focused W4 and Codex bridge gates and return for review.
