# Review-attachment returned-key inventory stimulus

Work W120587, child of W116975. Created 2026-09-08 by baton.tuner under
parent claim120575, following the mandatory fixture split in independent
`../../../finding-module-scope-review/review-2026-09-08T06-42-22Z.md`.

## Confirmed defect and exact correction

`EveryProbeProvesItArrived.spoiling_review_row` currently executes
`UPDATE review_attachments SET attachment_id = ?` using `SPOILED["identity"]`
before calling `review_cycles.record_verdict(attachment_id="attachment-probe",
disposition="accepted", profile=profile, port=review_port("baton.review"))`.
The real `_attachment` validates that caller ID, then `_attachment_row` queries
`SELECT * FROM review_attachments WHERE attachment_id = ?`. The changed stored
key makes that query miss: retained parent inputs.json records
`refused/precondition: no review attachment attachment-probe`, not adoption.

Within the already approved existing key-stimulus scope, change only the exact
(`_attachment_row`, `review_attachments`, `attachment_id`) fixture branch:
leave attachment-probe in storage, install a scoped row factory wrapping the
original, and replace only the returned attachment_id with the same malformed
value when cursor.description exactly matches REVIEW_ATTACHMENT_COLUMNS.
Call the same public record_verdict path, restoring the original factory in
finally. The real `boundaries.row` owns the malformed returned member; do not
mock the validator or call it as a substitute for the public receiving path.

Preserve the exact catalog pair `(adopted, review_cycles.py:_attachment_row,
review_attachments.attachment_id)` / `a persisted review attachment`, existing
category/code and wrong-boundary guards, all other stimuli and every accepted
writer/lane/scanner/catalog/aggregate byte. Runtime review_cycles.py and schema
remain read-only. The source change lives only in
`v12/python/tests/manager/test_boundary_inventory.py`, with additive controls.

## Independent acceptance boundary

Prove the exact attachment SELECT returns a valid stored key to the original
factory before injection; malformed returned key reaches integrity/schema at
the persisted review attachment boundary; storage and original factory survive
refusal. A valid returned key must traverse the actual public path, and an
absent row must keep the earlier precondition refusal and restore the factory.
The existing guard must accept adoption refusal and reject earlier refusal.
Retain positive row/lookup evidence and run the focused controls, then a
bounded sweep of unchanged attachment-row probes. Preserve all broader module
ownership/pair residuals under W116975, which cannot finish with this fixture.

## Positive-path clarification — 2026-09-08, claim120598

The initial seven-control run passed six and exposed an incorrect expectation
in the new positive control: the unchanged world has already finalized the
review attempt with reason `probe review completed`, whereas record_verdict
requests `independent checkpoint review completed`. Actual row adoption and
retained review-result validation succeed before the real finalization journal
refuses `refused/operation-collision`. This supersedes the execution plan's
anticipated later active-current-review guard as the positive endpoint.
The control will assert the real finalization call and exact collision, while
retaining valid stored-row and restored-factory checks; the malformed-probe
guard still rejects this later refusal. No prior baseline assertion changes.
Initial output and candidate remain in evidence/ focused-120598.json and
initial-candidate-120598.py; no runtime change is warranted by a fixture reason.

## Candidate result — 2026-09-08, claim120598

Candidate SHA-256
`bf6160f596ad917fdb4296963d2c272adf3f328b2e78e279dc1f1eb4da7bf00c`
fixes the exact key stimulus. The query trace observes one complete attachment
row from the literal attachment-probe SELECT before corruption; the stored
row remains valid and the exact original factory is restored. The positive
key reaches the real finalization call, whose differing-reason journal guard
refuses; missing-row and later refusals cannot satisfy the adoption guard.
All nine actual catalog attachment-row closures pass on fresh fixture roots.

`evidence/verification-120598.json` and its runner prove only the exact new
fixture branch and additive class differ in AST from accepted lanes baseline;
runtime/schema hashes are unchanged. Six initial passing controls are preserved
(one name clarified) and the corrected seventh passes. Initial failure remains
in focused-120598.json and initial-candidate-120598.py. Base, exact final
candidate and patch remain in the same evidence directory. Independent fixture
acceptance is next; this result does not settle review_cycles module coverage.

## Independent acceptance — 2026-09-08, claim120734

**Confirmed accepted.** `review-2026-09-08T16-28-35Z.md` supersedes pending
fixture acceptance. The exact candidate and preserved scope are independently
verified in `evidence/review-120734-audit.json`; retained focused and attachment
closure results are accepted. W116975 retains module inventory coverage.
