# Plan

1. [done] Inventory the current v12 fixture creators and cleanup lifetimes.
2. [done] Classify the exact residual W30 audit tree using ownership
   evidence without deleting it.
3. [done] Record the bounded correction, regression, and verification plan.
4. [done 2026-08-22] Pass the implementation-ready Work to `baton.impl`.
5. [done 2026-08-22] Implement the owned-root registry and the `node:test`
   `after` hooks. `v12/test/owned_roots.mjs` is the one registry; all nine
   test-owned families now come from it, and `mkdtempSync` is no longer
   imported by either test module.
6. [done 2026-08-22] Add the positive and deliberate-failure regressions with
   symlink preservation. `v12/test/fixture_cleanup.test.mjs` drives
   `v12/test/fixtures/fixture_cleanup_probe.mjs`, which lives outside the
   suite glob. Mutation-checked: with the probe's hook removed both cases fail
   with "survived the probe".
7. [done 2026-08-22] Run the complete v12 gate with a zero-residue bracket.
   141/141 pass; the bracket holds zero roots of any test-owned family. The
   same bracket without the correction holds 130.
   Evidence: `evidence/verification-2026-08-22.txt`.
8. [done 2026-08-22] Correct round-1 review: ownership is an identity rather
   than a pathname (remove-and-forget as one action, retirement for
   product-removed roots, dev/ino re-checked before removal, entries dropped
   only after success), and the probe reports through a parent-nominated file
   with every child failure mode diagnosed separately. Two new regressions,
   both mutation-checked. 155/155 from the documented gate with a zero-residue
   bracket. Evidence: `evidence/correction-2026-08-22.txt`.
9. [done 2026-08-22] Independent re-review signed off after the round-3
   absence/non-directory/error correction. Review:
   `review-2026-08-22T14-54-18Z.md`.
9a. [done 2026-08-22] Signed off by independent re-review
   (`review-2026-08-22T14-54-18Z.md`); revalidated at sign-off — 161 pass,
   0 fail with zero surviving roots in the bracket — and advanced to
   operations rather than closed.
10. [pending — separately authorized, NOT this Work] One-time host cleanup of
   the exact root `/tmp/w30-fixture-audit.Lmr3aa` (root-only, non-following)
   and any disposition of the ambient `v12poc-*` roots. Untouched here.

## For review

The audit's family count is superseded from eight to nine: W2928 added
`v12-authority-*` on 2026-08-22, after the audit. It was already using the
recommended shape with its own private registry, and is now folded into the
shared one. The dated supersession is in `FINDING.md`.
