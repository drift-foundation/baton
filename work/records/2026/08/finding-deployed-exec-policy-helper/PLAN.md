# Plan

**Status — 2026-08-21:** round-2 independent review is clean in
`review-2026-08-21T04-36-20Z.md`; ready for approver Git and release
disposition. The `d46ab1e` rollout's source-helper stopgap remains the
recorded truth for that immutable release; this change is what removes the
need for it in the NEXT one.

1. [done] Reproduce the deployed/source mismatch and identify the packaging
   owner (`tools/deploy_work.py:SOURCE_SHARED_GATE`).
2. [done] Give the reviewed `exec_policy.mjs` a strict, stdout-only direct
   invocation which reuses `rulesFor()` and does not write policy files.
3. [done] Ship that exact module under
   `lib/codex-event-bridge/src/` without adding a third `bin/` product entry.
4. [done] Point the shipped dispatcher template at the installed interface
   and remove its checkout-only locator.
5. [done] Add deployed byte-parity, standalone invocation, strict-operand,
   no-import-side-effect, and exact/broad/extra artifact regressions.
6. [done] Round 2 P1: document provisioning for EVERY configured target
   identity — once per participant, appended into a staged file, then
   installed — and regress it against the deployed auditor for both of the
   template's identities.
7. [done] Round 2 P2: assert the existing policy file's BYTES survive a run.
8. [done] Round 2 P2: replace the same-artifact/beside-the-dispatcher claims
   with the confirmed byte-equal-immutable-copy statement.
9. [done] Run focused policy/deployment tests; the complete v11 gate and the
   ACP acceptance are green.
10. [done] Repeat independent review; round 2 is clean.
11. [pending] Approver owns Git and next-release disposition.
