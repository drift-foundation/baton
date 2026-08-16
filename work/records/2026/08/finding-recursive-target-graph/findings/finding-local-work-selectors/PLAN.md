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
