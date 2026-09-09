# One exact test amendment requested

Superseded as a permission request,2026-09-09: the standing W71830 test-change
authority in AGENTS.md covers this exact amendment and future test changes
needed by accepted campaign scope. This file and its proposal are retained as
technical/decision history. No new per-test decision is required; current
PLAN.md governs execution. Source scope, budgets and acceptance remain.

Recommend authorizing only the conversion of
`RestoringOneCheckoutToItsRetainedCheckpoint.test_nothing_outside_the_nominated_checkout_is_named`
in `v12/python/tests/manager/test_checkpoint_profiles.py` to the exact proposed
method in evidence/review-129222/proposed_test.py. The runnable method passes
independently over a real disposable checkout. Full proposed file and patch:
evidence/review-129222/proposal/tests/manager/test_checkpoint_profiles.py and
evidence/review-129222/test-proposal.patch.

Current full-file SHA256:
dd65fa4e685f2745e974b64c4d25dcf2468e9d07d1d46ff95d2a0fa51271c86d.
Proposed full-file SHA256:
321ac78270ee842110cd289e32ee727f5bbde842ce154c089e228607c1b5860a.
Ordinary mode644. Only this method changes in the proposal.

The change replaces equality to the original pathname with equality to the
nominated directory's device/inode WHILE each command receives the still-open
descriptor reference. It preserves git/-C checks, exact reset and clean argv
checks, no sibling operand, and immutable sibling content. It follows the
object-binding behavior already approved; it does not authorize weaker custody
or a second target.

Owner129177's four conversions did not include this method and explicitly
preserved every other assertion/setup. AGENTS.md therefore requires this
additional case-specific authority. The implementer left the method unchanged
and reported its failure correctly.

No source path or budget extension is requested. Carry23.622/25s as derived
from all three listed author runs, leaving1.378s, and append that accounting
correction without rewriting earlier evidence. The remaining intent-signature
defect in review-2026-09-09T16-31-35Z.md is within existing source/additive-test
scope. After approval, pin the amendment and dispatch the existing correction
through baton.impl -> baton.bug. Use exact focused selectors and preserve all
other tests. C/W119114 remain gated until independent acceptance; approval of
this test scope does not approve the current source candidate.
