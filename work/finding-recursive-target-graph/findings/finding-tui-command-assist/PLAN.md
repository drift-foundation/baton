# Plan

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
