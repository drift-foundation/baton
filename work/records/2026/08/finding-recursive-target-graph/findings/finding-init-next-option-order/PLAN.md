# Plan

1. Add a regression requiring `init`'s `next` command to be exactly compatible
   with the current public grammar: global options precede `activate`, and the
   target is `directory=.` rather than a positional operand.
2. Correct the generated hint in `src/baton_work/project.py`.
3. Verify focused onboarding/deployment tests and `just test-v11`.
4. Return for review before the next v11 distribution.

**Status — 2026-08-16:** queued as fresh-authority W2 and ready for
`baton.claude`; return to `baton.codex` for independent review.

**Signed off — 2026-08-16 14:09Z:** implementation is clean; see
`review-2026-08-16T14-09-46Z.md`. W2 may close satisfying.
