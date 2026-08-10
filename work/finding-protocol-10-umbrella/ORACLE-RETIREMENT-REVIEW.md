# Protocol-10 oracle retirement review

**Outcome:** sequence approved with one preservation correction.

## Accepted replacement sequence

The full protocol-9 corpus is the replacement, not a hand-picked subset. A
temporary import substitution from `baton_v6` to `baton_core._impl` runs all
432 tests unchanged. The reviewer independently started the same unchanged
corpus against the core and observed it progressing without an early failure;
the implementer's complete run reports 432/432 passing.

Apply the safety nets in this order:

1. copy/rename the corpus so it clearly names core protocol conformance and
   point it at `baton_core._impl`;
2. before any protocol-10 behavior change, require all 432 tests to pass with
   no skip, xfail, or expectation edit;
3. only after that replacement is active, remove differential parity from the
   gate and just recipe;
4. keep explicit conformance for every still-valid behavior; after the bump,
   change or remove an inherited expectation only beside a named superseding
   protocol-10 contract;
5. prove no active production/test import still reaches `baton_v6` except the
   historical-evidence hash guard.

This replacement-first order means there is no commit state where neither the
old bridge nor the ported corpus protects the core.

## Direct `_impl` access is approved for this corpus

This is white-box implementation/schema conformance, not solely a public API
test. It deliberately covers schema SQL, validators, canonical manifests,
doctor reconciliation, private delivery builders, and failure invariants that
`baton_core.__init__` should not export as product API. Importing
`baton_core._impl` directly is therefore correct. Public CLI/core surfaces
remain covered by their separate boundary tests; do not weaken those because
the conformance corpus can see internals.

## Correction — the frozen oracle itself remains byte-identical

Do **not** add the proposed retirement header inside `baton_v6.py`. That would
change the file and invalidate the exact hash Slawomir ruled should remain as
inactive protocol-9 evidence. Record retirement in the new corpus's module
docstring, this finding, README/test comments, or an adjacent marker. The
oracle file itself stays byte-for-byte unchanged and unimported by the active
implementation/conformance suite. Keep its hash guard as an evidence-integrity
check, not as active parity.

## Gate before `part_name`

- renamed/repointed corpus: 432/432 unchanged tests pass;
- frozen oracle digest unchanged;
- no parity allowlist remains active;
- no unintended import of `baton_v6` remains;
- standard test recipe includes the new core conformance corpus;
- only then may the first protocol-10 `_impl.py` change land.

## References

- `baton_v6.py`
- `test_baton_v6.py`
- `test_core_parity.py`
- `baton_core/_impl.py`
- `justfile`
- `work/finding-protocol-10-umbrella/FINDING.md`
