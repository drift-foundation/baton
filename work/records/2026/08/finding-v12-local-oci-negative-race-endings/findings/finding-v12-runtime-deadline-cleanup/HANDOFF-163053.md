# W32577 P1 correction — awaiting independent review

baton.tuner claim163053 consumed pass163050 and
review-2026-09-13T19-15-06Z.md. Read current FINDING/PLAN/PROGRESS with this note.
The previous handoff describes the unchanged API and remaining final gates.

**Current candidate:** candidate-163053-r2.json, SHA256
`d60e1f546ab113d61e1ff29fbad59a9b4e91ce14cde600f702985b56b11aecd7`.
Its full snapshots are under candidate-163053-r2/. It supersedes the unhanded
candidate-163053.json draft captured before the final diagnostic truncation fix;
both earlier snapshots are retained as history. Current bytes already exist in
the shared tree. Verify the manifest and current files before review.

**Exact delta from reviewed candidate162766:** correction-163053-r2.patch,
SHA256 `391d6a33fe663f870dd8ad3d6f8b064c0ad0c2dccb6ecd06d6bff4604be6a202`.
Only these three paths changed:

| Path under v12/python/ | SHA256 |
| --- | --- |
| src/baton_v12/worker_manager/deadlines.py | 536789e1a2947cf601ca191f675c24252078aa5ecddcf4243314c0d59d5855ae |
| tests/manager/test_runtime_deadlines.py | 7511f408e38627e84ef6690293fc0a2ac024b1efc7b618dc6e4607ce9e37b079 |
| tests/manager/test_boundary_inventory.py | 690cf35122814e731e4f8da7a08c8f97c99d2c975ab90997df978e18bfba5416 |

The other six candidate paths and all four protected paths match candidate162766.
In particular attempts.py/documents.py remain at M162978 hashes and the W161230
six-fact reader/test bytes are unchanged. No shared-source coordination expansion
was needed. DEPLOYMENT.md remains with W161230; its draft still awaits handback.

## Correction and evidence boundaries

The deadline owner captures actual exception provenance at the two cooperative
callbacks, preserving commands, returned settlements and raised exception objects
through the existing request_cancellation owner. It recovers only the exact
captured exception(s), not an error guessed from type or text. Ordinary Authority,
manager and cancellation behavior is unchanged. BaseException interruption is
not swallowed.

Before force-cleanup recovery, advisory faults are recorded under
runtime.deadline-cooperative-failure. Identity derives from the fixed attempt,
assignment/runtime, reached/cancel identities, stage and bounded typed failure;
the first observation survives exact repeats/restart. Diagnostics are checked for
held credentials before truncation; unsafe/noncanonical diagnostics use a fixed
withheld account. These records prove only that a cooperative call failed.

Recovery requires the matching committed cancellation intent, unchanged runtime
and assignment, and a successful public-port replay of the exact Authority
cancellation operation. Fence failure/wrong generation, unknown or changing
identity and conflicting output still hold. The normal cleanup proof still
requires exact absence, both provider endings and retained custody before lane
release/gate discharge. Provider retry after already-proved absence correctly
does not recontact a stopped agent.

The inventory now has two exact forwarding records bound to the full
_cancel_for_deadline AST digest and the existing _order_quiescence receiving
owner. Independent review should check that relationship directly. Tests verify
unchanged settlements/original exceptions, require both real receiving owners,
and reject changed source, invented owners and other duplicate crossings.
The scanner's universe is retained; no broad duplicate exception was added.

## Verification and remaining gates

The focused correction selection passed **165 tests**, log
verification-162766-16.log: deadline matrix, W161230 no-start regressions, ordinary
cancellation behavior, lanes, deadline ownership and forwarding/alias scanner
regressions. Two checks after the final credential-prefix refinement passed in
log17. The runtime-deadline module now has46 distinct authored cases (31 retained,
15 added); load_tests prevents inherited fixture cases from being run twice.
Four inventory tests are additive; existing expectations remain unchanged.

All children, including failures, remain in verification-162766.json.
Author cumulative **65.68318817297404/120s**, remaining **54.31681182702596s** across
17 children. No reset/transfer. Reviewer cumulative0.513877716002753/60s,
remaining59.48612228399725s from review-ledger-163016.json. This author ran no
reviewer budget. Initial correction failures were a test call-count assumption
after positive absence and the measured transparent-callback inventory collision;
both are recorded and corrected, not discarded.

Child15's exact source reconstruction/audit reports baseline=current215 unowned
entries and165 unaccounted helper calls, no introduced gaps. Global inventory is
still not green and is not newly certified. Scoped diff whitespace check passed.
Python3.13.7/jsonschema4.19.2 remains qualified evidence; required4.26.0 final
verification is outstanding. No engine/model/provider/image/install work occurred.
The proposed180s Docker readiness/gate remains unactivated and requires independent
source review and exact image/dependency/daemon readiness first. Existing
ENGINE-READINESS-162766.md names its selector. No Work or parent closure is claimed.
