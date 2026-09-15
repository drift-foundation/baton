# W32577 deterministic implementation candidate

Author: baton.tuner, standalone claim162766. Scope authority:
review-2026-09-13T18-26-19Z.md, REVALIDATION-162662.md and pinned M33822 in FINDING.md.
Current status: candidate awaiting independent baton.feat review. This does not
close W32577/W32382/W33755 or claim the separate Docker acceptance.

The manager now pins trusted runtime deadline configuration before start, records
expiry separately from action and advances only the stored policy. Cancellation
uses the existing Authority-first owner. Receiptless cleanup carries the exact
assignment/runtime/reached/cancel/fence/retention identities and preserves output
through the existing custody and lane owners. Positive cleanup proof and remote
gate discharge are separate journal records. Genuine receipts use ordinary
cleanup; unrelated cancellation intent, stale identity, unknown start and
concurrent output refuse or hold without fabricated terminal evidence.

## Candidate and path ownership

`candidate-162766.json` SHA256:
`b62194279e3f1c995ecfe11245edeefc427d3d40f7561e4c48c5efe1f70bc015`.
It enumerates SHA256, size and source mode for each path, with corresponding
full-byte snapshots under candidate-162766/. These bytes already exist in the
shared working tree. Verify the manifest and current paths before review; do not
blindly import the broader Git diff, which contains W161230 prerequisite changes.

All paths below are under `v12/python/`:

| Path | Change |
| --- | --- |
| src/baton_v12/worker_manager/deadlines.py | New pin/observation/advance/proof/gate owner |
| src/baton_v12/worker_manager/attempts.py | Start-policy selection/pin/expiry guard only |
| src/baton_v12/worker_manager/documents.py | Six closed manager-local deadline documents |
| src/baton_v12/worker_manager/intake.py | Private receiptless deadline authorization using existing settlement/custody core |
| src/baton_v12/worker_manager/oci.py | Typed destroy_deadline wrapper around exact existing removal |
| src/baton_v12/worker_manager/__init__.py | Five public exports |
| tests/manager/test_runtime_deadlines.py | 31 deterministic policy/boundary/race/retry/proof/receipt/sibling cases |
| tests/manager/test_runtime_deadline_engine.py | Prepared required Docker selector, unexecuted |
| tests/manager/test_boundary_inventory.py | Added exact deadline ownership, delegated probes, helper accounts and witnesses |

No existing test assertion or expectation was weakened. The boundary inventory's
existing exhaustive assertions remain; additions describe and exercise this
candidate's entries. test_contracts_inventory.py was run but not edited.
schema.py/store.py/lanes.py and W161230's test_reconciliation_worker.py retain
their pre-claim hashes, recorded in the manifest. No launch, interrogation, Job,
worker or runner source changed. DEPLOYMENT.md remains with W161230; the proposed
addition is DEPLOYMENT-DEADLINE-DRAFT-162766.md. PROGRESS was appended by the actual
change author under AGENTS.md; old history and reviews were preserved.

Released shared-source resulting hashes for W161230:

- attempts.py: `1f7c1532372bbf714d3c7d77ebb1a3d29e6d34a98afb0a718fa9f3a9ef4853f6`
- documents.py: `5f31654f699448a8e52d076f6ba517e9acfef201ada30dea0559051af474b014`

Subsequent edits to these shared paths require exact ownership coordination with
the candidate reviewer. No blanket W161230 completion dependency is introduced.

## Implemented public signatures

```python
request_runtime_start(store, adapter, *, attempt_id, inputs=None, deadline_policy=None)
deadline_of(store, *, attempt_id)
observe_deadline(store, port, *, attempt_id)
advance_deadline(store, port, agent, adapter, *, attempt_id, retention_policy_digest)
deadline_cleanup_of(store, *, attempt_id, retention_policy_digest)
discharge_deadline_quiescence_gate(store, port, *, attempt_id, retention_policy_digest)
```

Policy is closed policy_digest/policy_generation/duration_seconds/action, with
positive whole integer generation/duration and report-only/cancel. Digest agrees
with the attempt policy. Caller timestamps and replacement advance policies are
not accepted. None is an explicit immutable selection on new unconfigured starts;
legacy committed starts without a pin cannot acquire one. Before-deadline
observation remains retryable and only the first reached instant is committed.

The proof reader validates signed kind/operands, matching cancellation intent,
the separate cleanup authorization, fixed identities, positive absence, both
provider endings and retained directory custody. Destroyed axes alone supply no
proof. Missing underlying optional Authority discharge capability or an external
discharge failure can leave committed cleanup awaiting its exact retryable gate
receipt; the implementation uses only public port operations and does not inspect
the private session. Truly unstarted cancellation returns W161230's six-fact
proof and intentionally discharges no fabricated runtime gate.

## Verification and remaining acceptance

Final run: **802 selected deterministic tests passed**, log
verification-162766-12.log. This includes31 new deadline tests, full attempts and
fake-engine OCI suites, W161230 no-start tests, interrogation timeout semantics,
runtime lanes, ordinary/abandonment gate and provider regressions, contracts
inventory, deadline-specific boundary ownership/probes and all five witnesses.
The exact command/versions/guard are in verification-162766.json.

Author cumulative45.89975568297086/120s, remaining74.10024431702914s across12 children.
All failures are charged and retained; PROGRESS summarizes their corrections.
Independent reviewer allowance60s is separate and starts unspent by this author.
No runtime/engine/model/image/install allowance was consumed. Scoped git diff
--check passed; the new engine module and deadline module were AST-parsed.

The test interpreter was Python3.13.7 with jsonschema4.19.2. This is qualified
evidence; pyproject's required4.26.0 final verification is still pending. No
installation was run. The full boundary-inventory gate failed on inherited and
initially introduced gaps. inventory-audit-162766.json now compares verified
pre-change sources with current sources and finds baseline=current215 unowned
entries and165 unaccounted helper calls, with zero introduced gaps. It is a source
comparison, not a passing global gate. The global inherited failures remain
visible and are recorded in FINDING rather than silently exempted.

ENGINE-READINESS-162766.md names the exact required Docker selector and remaining
image/provenance/dependency/daemon readiness. The fixture never builds or pulls,
requires a preloaded digest and fails missing prerequisites instead of skipping.
Its proposed180s cumulative engine bound is not activated by this handoff.
Source review precedes that separate execution assignment. The deployment draft
also needs the existing serial file handback. These remaining gates are explicit;
the deterministic implementation assignment itself had no pickup blocker.
