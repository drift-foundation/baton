# Correct the inventory writer-key stimulus

Work W116032; parent W48697. Accepted B2 scope is pinned by the parent's
2026-09-08 owner ruling and the retained W115824 review.

The writer_id probe currently changes the stored primary key before querying
its old value, so adoption never sees the malformed row. In only
`v12/python/tests/manager/test_boundary_inventory.py`, change that specific
spoiling_review_row stimulus to returned-row corruption at the fixture row
factory, preserving the stored/query key and immediately restoring the factory.
Keep the real reader/validator, expected label/category/code and wrong-boundary
guard. Add positive, malformed-key, missing-row and restoration controls.
No runtime changes or validator mocks. Serial ownership follows the scanner.

## 2026-09-08 revalidated decision — claim116860

Accepted scanner candidate4cf7eae8 matches live bytes and is retained in
evidence/before.py. Read the final scanner acceptance and the B2 diagnosis.
Runtime review_cycles.writer_of at lines63–71 validates its query identity,
SELECTs line_writers by that unchanged key, refuses absent rows at precondition,
then applies real boundaries.row under a persisted line writer. Existing
spoiling_review_row updates writer_id to empty before querying writer-probe,
so no malformed row reaches adoption. The retained diagnostic demonstrates
integrity/schema at a persisted line writer's writer_id when the returned
identity is empty instead. No runtime correction is needed.

Only the exact writer_of/line_writers/writer_id stimulus will install a short
row-factory wrapper, delegate to the prior factory, recognize the writer row
by its exact schema columns, and replace returned writer_id with the existing
identity stimulus. Preserve stored/query identity, invoke real writer_of and
restore the original factory immediately in finally on success or refusal.
All other stored-row corruption and catalog entries remain unchanged.

Add valid-writer, malformed returned identity, valid returned identity, missing
row and wrong-boundary controls. The valid-stimulus control supplies the valid
key through the same fixture wrapper; the missing-row fixture removes its row
after world setup. Neither substitutes a reader or validator. Verify original
refusing label/category/code checks remain intact and the queryable stored
identity and original row factory survive the probe. This is one bounded B2
stimulus result; no further decomposition is needed before implementation.

## 2026-09-08 implementation and remaining check3 evidence — claim116860

Candidate3973301e09e27a4cb724969c158a0441a629037718d755dae1ada594a2a24b5c
changes only the authorized existing spoiling_review_row writer-key branch
and adds7 independent controls. The wrapper delegates to the original factory,
corrupts only an exact writer-row result, invokes real writer_of and restores
the original factory in finally. Valid and missing-row paths remain distinct.
The catalog still declares the exact writer_id pair with the unchanged
a persisted line writer label and successfully reaches its adoption refusal.
All41 top-level scanner functions and27 other baseline classes are unchanged.

Baseline new malformed-key regression fails at refused/precondition; final
7targeted controls pass. Original check3 ran once and still fails on four
other subcases. Full stack traces in evidence/verification.txt and exact rows,
fixture facts and next-scope boundaries in evidence/residual-probes.json:

- intake.py:_attempt_of / attempts.runtime_attempt_id: no runtime attempt.
- lanes.py:_occupy_lane / runtime_lanes.lane_id: lane-held refusal instead of adoption.
- output.py:_attempt_of / attempts.runtime_attempt_id: fixture None.keys error.
- review_cycles.py:_attachment_row / review_attachments.attachment_id: no attachment.

Read-only fixture inspection confirms each changes a stored lookup key before
its later query or collision path. These observations do not establish a
runtime defect or authorize broadening this writer-only stimulus correction.
Carry the exact rows to the inventory parent for bounded module work; output
is outside the previously enumerated B3 module extension and needs explicit
disposition before editing. No skipped probe or baseline subtraction is used.
Total measured5.405s within15s. Independent B2 review remains required; original
check3 and all larger inventory/suite gates remain unsatisfied.

## 2026-09-08 independent B2 acceptance — claim116899

Accepted exact candidate3973301e09e27a4cb724969c158a0441a629037718d755dae1ada594a2a24b5c;
review-2026-09-08T06-19-49Z.md and evidence/review-116899.json bind three
independent real-query/factory-restoration cases plus digest/AST audit. This
supersedes awaiting-review state only. The writer probe reaches real adoption,
preserves its stored key and restores the prior factory. All four original3
residuals remain for bounded parent/module disposition, including explicit
additional output-fixture scope. No global coverage or suite acceptance follows.
