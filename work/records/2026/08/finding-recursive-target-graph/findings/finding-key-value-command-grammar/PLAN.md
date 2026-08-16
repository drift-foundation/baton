# Plan

**Status — 2026-08-16 12:25Z:** changes requested in
`review-2026-08-16T12-25-26Z.md`. The first implementation establishes the
shared strict tokenizer, but its declarative command specification lacks the
required/closed-value/alternative-form and help metadata needed to be the one
public grammar and to support dependent W14. W13 remains active with
`baton.implementer`; no authority/schema revision is required, and it must not
be recreated as unfinished Work in the fresh authority.

**Re-review — 2026-08-16 12:38Z:** round two resolves the core parser,
generated discovery, launcher, and regression gaps. Two bounded corrections
remain in `review-2026-08-16T12-38-20Z.md`: render universal operands and the
remaining phase/say/close form conditions from the authoritative spec, and
finish the retired flag/product wording sweep through live public errors and
comments. W13 remains active with `baton.implementer` and excluded from fresh
authority recreation.

**Signed off — 2026-08-16 12:44Z:** round three resolves the remaining
universal-discovery, static-form, stale-wording, and anti-drift gaps. See
`review-2026-08-16T12-44-53Z.md`. The focused 13-test target passes locally;
the complete 655 parallel plus 3 serial gate is reported green. W13 closes
satisfying and remains excluded from fresh-authority recreation.

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
7. Remove W13 from the fresh-authority recreation inventory and update its
   counts/proof after verification.
