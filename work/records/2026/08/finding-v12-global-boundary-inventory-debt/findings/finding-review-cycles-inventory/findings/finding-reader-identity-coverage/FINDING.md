# Review reader identity coverage

Work W121031. Created 2026-09-08 by baton.tuner under W116975 claim120993. This is the
independently acceptable reader portion of the approved module inventory
scope; its Work is created immediately with this canonical binding.

## Confirmed source and bounded decision

`review_cycles.review_of` forwards attachment_id unchanged to `_attachment`,
which validates it as `a review attachment identity` before lookup.
`verdict_of` forwards verdict_id unchanged to `_verdict_row`, which validates
it as `a checkpoint verdict identity` before lookup. The accepted census has
both caller entries unowned. No runtime validator is missing.

Add exactly these DELEGATED entries in
`v12/python/tests/manager/test_boundary_inventory.py`:

- `(caller, review_cycles.py:review_of, attachment_id)` to
  `(review_cycles.py:_attachment, caller:attachment_id)`.
- `(caller, review_cycles.py:verdict_of, verdict_id)` to
  `(review_cycles.py:_verdict_row, caller:verdict_id)`.

Add one actual public-call probe per entry, passing existing SURROGATE to the
reader and preserving the exact corresponding label above. Add controls for
unchanged source forwarding, the exact catalog pairs, malformed identity
refusal before SQL, valid absent identities reaching the lookup/precondition,
and wrong-boundary guard rejection of absence. Reuse the genuine existing
ReviewCycles lifecycle fixture by named methods for a positive committed
attachment/verdict round, without inheriting and duplicating its tests.

Only additive catalog entries/probes/controls are authorized here. Preserve
every existing mapping, probe, assertion, shared scanner and runtime/schema
byte. Consumption ownership, helper residuals, nested JSON probes and joined
module acceptance remain separate results under W116975.

## Verification boundary

Bind accepted shared candidate918f8d9a and unchanged runtime/schema hashes.
One focused run of the new controls plus one before/after census and AST
preservation audit, combined process budget15s. Assert exactly two new owners
and probe pairs, with no removed pairs or changed old ownership, and retain
every other residual unchanged. No daemon or broad suite. Independent review
binds the candidate and evidence before releasing the shared file.

## New-control correction — 2026-09-08, claim121055

The initial run passed five controls, including both actual public malformed
probes and the genuine committed lifecycle. The new ownership control assumed
the label collection was a set; the unchanged delegated_labels API returns a
sorted list. Correct only that new assertion from `{label}` to `[label]`.
Preserve its exact single-owner requirement and the initial failure/candidate
in evidence/verification-121055.json and candidate-121055.py. The five other
controls are unchanged and reused; rerun only this corrected control before
the still-unrun census/audit.

## Candidate and accounting clarification — 2026-09-08

The bounded additive reader candidate is ready for independent review. Exact
candidate, source/preservation evidence, census and verification limitations
are recorded once in `evidence/execution.md`. The audit's original expectation
that all declaration-resolution links remain present is superseded: the
new verdict_of delegate directly claims `_verdict_row`'s lexical identity
occurrence, replacing its old declaration link. The unchanged accounting
requires this; all residuals and remaining links are preserved.

## Independent acceptance — 2026-09-08, claim121106

**Confirmed accepted.** review-2026-09-08T17-19-25Z.md supersedes pending
review. The independent corrected-control run and exact preservation audit
pass; retained five controls and census are accepted. The author's cumulative
timing limitation remains explicit. Close this reader result only; W121034
receives the next serial allocation and W116975 retains joined acceptance.
