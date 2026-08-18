# Plan

**Status — 2026-08-18:** reviewer inventory complete; implementation blocked
by W102. The ordering is now ENFORCED rather than described: `block work=W101
on=W102` (seq 249) makes W101 unready, so it no longer wakes a handler who
cannot act. Re-audited 2026-08-18 — 11 live processes still import
`baton_source.mjs`/`main.mjs` from the working tree against the deployed v10
CLI and v10 mailbox config, so the refusal condition still holds. See
PROGRESS.md for the concrete "every v10 consumer is gone" predicate and for a
recommended safe/unsafe split awaiting the reviewer's ruling.

1. [done] Inventory v10-only source, build inputs, compatibility code, tests,
   and Codex monitor paths; separate W102 deployment/data and W103/W104 prose.
2. [done] Prove the v11 package/deployer imports only `baton_work` plus the
   retained ACP and generic/v11 Codex bridge modules.
3. [blocked on W102] Remove the approved v10-only runtime surface and obsolete tests.
   Reduce shared Codex configuration rather than deleting its retained generic
   transport. Keep `tests/conftest.py` with only v11-relevant setup.
4. [blocked on W102] Make the Justfile honestly v11-only: no generic command may retain
   hidden v10 behavior, and no removed recipe may point at absent tooling.
5. [blocked on W102] Run `just test-v11`, the retained Codex-event-bridge tests, focused
   v11 deployment/package checks, a scratch distribution inventory, and
   `git diff --check`; return for independent review.
