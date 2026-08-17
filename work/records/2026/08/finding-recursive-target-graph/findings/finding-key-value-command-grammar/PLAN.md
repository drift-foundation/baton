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

## Follow-up plan — explicit transfer verb

**Status — 2026-08-16:** approved and queued as separate same-schema Work;
completed W13 remains closed.

**Superseded in part — 2026-08-17:** W73 removes caller-supplied `phase=` and
derives the handoff phase from the destination route. The explicit threadless
`pass` verb remains current; the historical implementation plan below is not
the actionable grammar.

1. Add the canonical `pass work= to= phase= thread= comment=` form to the one
   declarative grammar, including the existing optional planned-Next operand.
2. Route it through the existing atomic post-and-transfer transition; do not
   split evidence from workflow mutation or weaken retry fingerprints.
3. Retire `pass-to=` from `say` in the next immutable client instead of
   preserving two transfer dialects. Keep `say` discussion and directed
   request semantics intact.
4. Cover success, refusal atomicity, authorization, claim release,
   destination Phase/Current/Next, retry, CLI/TUI command assist, and packaged
   behavior.

**Signed off — 2026-08-16 16:17Z:** W80 satisfies the follow-up contract. The
39-test focused/public/package/workflow review target, complete 734-parallel
plus 3-serial v11 gate, and diff-check are clean. See
`review-2026-08-16T16-17-48Z.md`; W80 may close satisfying.
