# Plan

**Status — 2026-08-16 12:55Z:** changes requested in
`review-2026-08-16T12-55-05Z.md`. The initial implementation proves basic
verb/key/value assistance and read-only right-side rendering, but it does not
share quote-aware partial tokenization, interpret W13 conditional forms, expose
the ruled invalid states, or keep an over-width input's caret visible. W14
remains active with `baton.implementer`, returns to `baton.feat`, and stays out
of fresh-authority recreation pending sign-off.

**Signed off — 2026-08-16 13:10Z:** round two resolves the shared partial
analyzer, conditional/invalid assist states, visible-caret, horizontal-
viewport, resize, cancellation, and evidence gaps. See
`review-2026-08-16T13-10-12Z.md`. The focused 20-test target passes locally;
the complete 662 parallel plus 3 serial gate is reported green. W14 closes
satisfying and remains excluded from fresh-authority recreation.

1. Consume the declarative command specification established by
   `finding-key-value-command-grammar`; do not duplicate verb or parameter
   metadata in the renderer.
2. Define the command-prefix, exact-verb, supplied-key, missing-key, enum-value,
   invalid-token, quoted-input, and narrow-terminal assist states.
3. Render input and assistance without borders, preserving every typed cell and
   a visible caret. Use the right side at usable widths and return a compact
   narrow behavior for review before implementation is accepted.
4. Add pure-state and virtual/real-terminal regressions covering incremental
   typing, overlapping command prefixes, reordered keys, quoted spaces,
   embedded `=`, unknown/duplicate keys, narrow widths, resize, cancellation,
   and proof that assistance causes no authority or seen mutation.
5. Verify CLI/TUI command-spec parity, focused coverage, and `just test-v11`,
   then return for review before the next immutable distribution.
