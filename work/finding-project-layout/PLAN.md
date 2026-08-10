# Plan — repository layout

1. **Finding and baseline inventory** — completed.
2. **Root discovery exceptions** — completed: Slawomir approved root
   `AGENTS.md` and `justfile` beside `README.md` and `LICENSE`.
3. **Revalidate remaining placement choices** — completed: CLI adapter stays
   under core, frozen evidence moves to `compat/`, and test discovery uses
   `tests/conftest.py` without a new root file.
4. **Capture pre-move source, oracle, artifact, and zip-member hashes** —
   completed: the corrected full-length baseline covers all 44 tracked
   non-`work`/non-`assets` paths with no mismatch; artifact, oracle, and ZIP
   member evidence independently matches. Root `.gitignore` is allowed and
   does not move.
5. **Move source, tests, tooling, and compatibility evidence mechanically** —
   completed; all 44 baseline paths were moved before path edits, with the
   recorded byte identities preserved.
6. **Update build/test discovery and documentation paths** — completed;
   policy, builders, README, manifests, and recursive discovery agree on the
   new layout and self-contained distribution-root contract.
7. **Prove standalone isolation, deterministic rebuilds, and artifact parity**
   — completed on the final candidate: 2,279 tests, sequential builds, exact
   baseline hashes, deterministic coverage, outside-repository execution,
   oracle isolation, and clean live doctor.
8. **Frozen handoff and independent review** — completed and approved in
   `review-2026-08-10T21-29-29Z.md`.
9. **Slawomir stages and commits the approved layout** — pending; agents do
   not touch the index or create the commit.
10. **Post-commit cross-team onboarding gate** — pending; `baton.reviewer`
    verifies the committed tree and explicitly clears onboarding before any
    other team is invited to rely on this release.
