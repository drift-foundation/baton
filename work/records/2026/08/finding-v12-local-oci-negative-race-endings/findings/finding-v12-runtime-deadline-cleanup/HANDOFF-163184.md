# W32577 lane assertion correction — awaiting independent review

baton.tuner claim163184 consumed pass163176 and review-2026-09-13T19-38-00Z.md.
Read current FINDING.md, PLAN.md and PROGRESS.md with this handoff. The independent
review resolved the earlier cooperative-failure P1 for the unchanged source bytes.
This correction addresses its P2 test finding only.

Current complete candidate: candidate-163184.json, SHA256
`e006a1e264463454be3aedb3355905dea7d5ceff09b139170f2d49f286c09a10`; full nine-file snapshots under
candidate-163184/. Predecessor candidate-163053-r2.json remains preserved, SHA256
`d60e1f546ab113d61e1ff29fbad59a9b4e91ce14cde600f702985b56b11aecd7`. Current candidate bytes are already in the shared tree.

Exact two-file delta: correction-163184.patch, SHA256
`245fc98da5c9743ee0d6adf12a62de90322ae61c8b513f9ebc839c2c71f6b7df`.

| Changed path under v12/python/tests/manager/ | SHA256 |
| --- | --- |
| test_runtime_deadlines.py | 0caf835093a0fd14663d99ca2a73e27767da259c2ac513c549005c6fe97389d1 |
| test_runtime_deadline_engine.py | 72247570d612c4e51941b0ef138d57efa21c5d715cbde74f01116ebe65fda782 |

The other seven candidate paths and all four protected paths match the reviewed
predecessor. This includes lanes.py and the shared attempts/documents/no-start
surfaces. No product change or W161230 overlap expansion. DEPLOYMENT.md remains
with W161230; DEPLOYMENT-DEADLINE-DRAFT-162766.md awaits serial file handback.

## Corrected assertions and focused coverage

All nine projection-existence hold assertions now require holder=attempt-1 and
held_by_this_attempt=True. Existing real manager/store fixtures additionally
assert exact release (holder=None, held_by_this_attempt=False) after successful
cleanup, provider/engine uncertainty retry, malformed-answer recovery, removal
interruption recovery, cooperative-failure restart and stop-fault recovery.
The ordinary success case verifies release after exact replay; the remote
receipt-commit interruption case verifies local release already persists.

The prepared engine test asserts the actual attempt holds its lane while running,
then asserts release of that same lane identity and an unchanged release projection
on replay. The incorrect whole-projection None assertion is removed. All other
acceptance assertions are preserved. Existing bounded test-change authority and
the explicit reviewer assignment authorize these two existing test-path changes.
No engine fixture was imported or launched; its changed source parses successfully.

## Verification and remaining gates

All46 deterministic deadline cases pass on final bytes in verification-162766-19.log.
Child18 also passed46 before removal of one redundant duplicate release assertion.
Both are charged in verification-162766.json; all19 children remain recorded.
Author cumulative **66.81117755598098/120s**, remaining **53.188822444019024s**, including every
prior failure/timeout. Reviewer remains **4.243902589994832/60s**, remaining
**55.75609741000517s**, in review-ledger-163135-r2.json. No budget reset/transfer.
The existing acceptance is qualified Python3.13.7/jsonschema4.19.2 deterministic
evidence. Unchanged product/inventory bytes retain the earlier reviewed evidence;
global inherited215/165 inventory gaps are not newly certified or waived.

Carry ENGINE-READINESS-162766.md forward unchanged: exact required Docker selector,
real-engine question, ownership/cleanup requirements and proposed180s bound still
apply. That allowance remains unactivated. Readable source provenance confirms
v12/python/pyproject.toml:30 requires jsonschema==4.26.0, while the recorded child
uses4.19.2. v12/worker/Dockerfile:14 pins base
python@sha256:8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3.
That is a base-image source pin, not evidence of a preloaded reference-worker
image. No exact worker image digest/provenance has been established by this claim.
The engine fixture requires BATON_W32577_IMAGE_DIGEST and validates that image ID
and reference-worker entrypoint in the later authorized execution. No engine,
image, install, live-provider/model or runtime work occurred here.

Return to baton.feat for independent review of this exact candidate. Required
4.26.0 verification, image/daemon readiness, separately bounded real Docker
execution and W161230 DEPLOYMENT handback remain due; W32577 and its parents
remain open. No pickup blocker occurred in claim163184.
