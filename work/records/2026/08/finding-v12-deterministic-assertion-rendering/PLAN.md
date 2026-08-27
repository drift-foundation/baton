# Plan — deterministic v12 assertion rendering

1. [done] Reproduce the reported variance with fixed hash seeds and
   separate unordered diagnostic bytes from `unittest` elapsed-time variance.
2. [done] Inventory all affected failing assertions and record exact source
   lines, operand shapes, and stable rendering transformations.
3. [done 2026-08-25] Obtain the required case-specific approval to edit the existing
   test assertions without changing their semantic verdicts. Slawomir approved
   the exact two-site boundary in T10265 message 10719.
4. [done 2026-08-25] Implement the bounded assertion-site normalization and focused
   regressions. Exactly the two ruled assertions changed; regressions added in
   `tests/manager/test_diagnostic_rendering.py`, registered atomically.
5. [done 2026-08-25] Added the test-local `self.maxDiff = None` authorized in
   T10265 message 11462, immediately before the approved comparison and
   nowhere else. The eight-entry difference renders complete again with no
   truncation notice. The focused regression grew from 3 cases to 10: the
   original three still pin the SHAPE of the two ruled sites through `ast`,
   and seven new ones prove the property itself over a synthetic failing
   assertion the module owns — determinism across six hash seeds,
   completeness, sorted order, unchanged verdict, a control requiring the
   replaced idiom to still reorder, and two cases holding the `maxDiff`
   correction test-local. Both ruled sites are byte-identical across seeds
   1, 2 and 3 with the verdict unchanged; the suite-wide failing-id set is
   unchanged except for two regressions W6633's reviewer added mid-correction.
   Evidence: `evidence/gate-after-maxdiff-correction-2026-08-25.txt`.
6. [done 2026-08-26] Independent review established deterministic complete
   diagnostics and unchanged verdicts within the exact approved boundary.
   Signed off in `review-2026-08-26T01-11-56Z.md`; close W10265 satisfying.
