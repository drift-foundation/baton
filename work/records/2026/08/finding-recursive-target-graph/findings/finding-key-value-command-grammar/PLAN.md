# Plan

1. Inventory every public v11 operation, its required, optional, repeatable,
   enum, and mutually exclusive inputs, including global launcher boundaries.
2. Define one declarative command specification consumed by both CLI and TUI
   parsing; no second hand-maintained command grammar.
3. Replace positional/operation-flag parsing with strict, order-independent
   `key=value` tokens. Refuse mixed old/new syntax and all ambiguous input
   before authority access or mutation.
4. Preserve normalized effectively-once fingerprints, ordered repeated values,
   identity injection, authorization, and JSON result/error contracts.
5. Add full command-matrix, quoting, embedded-equals, order, duplicate,
   unknown, missing, repeatable, mixed-dialect, CLI/TUI parity, retry, and
   refusal-without-residue regressions.
6. Run focused coverage and `just test-v11`, then return for review before the
   next immutable distribution.
