# Plan

1. Revalidate Work-id construction, authority scoping, parser inputs, every
   public Work selector, recursive/link views, responsive layout, JSON/TUI
   parity, and durable-reference boundaries.
2. Define one strict resolver accepting canonical ids and exact authority-local
   `W<positive-sequence>` selectors. Refuse malformed, missing, foreign, or
   ambiguous input without title/cursor/order fallback.
3. Expose `local_id` beside canonical `id` in JSON and details; add an exact,
   non-truncating `Id` column to Work lists. Route every CLI/TUI Work-valued
   parameter through the same resolver.
4. Add positive/full-vs-short parity, typo, malformed, foreign-authority,
   ambiguity/future-proofing, duplicate-title, long-sequence, narrow-screen,
   command-bar, restart/rebuild, and refusal-without-residue regressions.
5. Run focused coverage and `just test-v11`, then return for review before the
   next immutable release.

**Scheduling — 2026-08-16:** confirmed by Slawomir as the next serial Work
after active W14. Keep W4 queued until W14 reaches a terminal disposition;
then pass it to `baton.impl` and return it to `baton.feat` for review.

**Review gate — 2026-08-16:** changes requested in
`review-2026-08-16T14-59-06Z.md`. The strict selector and identity surfaces are
present, but hidden closed rows currently widen the visible Id column and an
overwide visible Id bypasses the explicit narrow-terminal refusal. Correct R1
and R2, run the focused file and full v11 gate, then return W4 for review.

**Signed off — 2026-08-16:** round two is accepted in
`review-2026-08-16T15-04-00Z.md`. Visible-row Id sizing and Id-aware whole-table
refusal correct R1/R2; 10 focused tests plus projection/TUI parity and an
installed-product onboarding path pass independently. W4 may close satisfying
and unblock its dependent Work.
