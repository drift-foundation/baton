# Immutable late identity after a failed start

**SUPERSEDED by owner2026-09-14T22:18:02Z / M172655.** Manual recovery with clear
operator reporting and human cleanup is sufficient for the initially unknown
runtime case. Preserve this design as history; it is not a current design-review
or implementation prerequisite. See current child FINDING/PLAN22:18:02Z.

W170382, baton.tuner claim172593, 2026-09-14. Design for independent review;
no implementation in this claim. Owner M172570 selected this direction and
M172588 assigned tuner. Read with FINDING entries22:08:03Z/22:09:53Z and
review-2026-09-14T21-50-56Z.md. This packet proposes the exact amendment to the
generic reuse-only boundary in parent SLICE2-SCOPE-165724.md:119–124. That boundary
continues until independent design review accepts the recorded amendment.

## Outcome and revalidation

A start fails after contacting the engine. Its immutable failure receipt records
an uncertain outcome and no runtime ID. A later exact observation must permit
the manager to end that same failed execution, retaining untrusted result bytes
and removing delivered credentials/launch material after positive exclusion.
Persistent uncertainty keeps the attempt and integration allocation held.

DESIGN-BASELINE-172593.json verifies all eight candidate/sibling paths against
review-candidate-172443.json, including bytes and modes. No drift was found.
The latest review's two probes are applicable evidence, not new runs by tuner:
one transiently empty listing stalls ordinary sweeps; explicit reconciliation
then attaches the runtime but the original cleanup rejects its disagreement
with the failure receipt. Known-at-failure cleanup and delivery recovery are
already implemented and independently verified in candidate172393.

Current owners explain both observations:

| Owner | Current behavior and proposed use |
| --- | --- |
| attempts._settled_and_recorded / _record_and_raise_start_failure | Ask outside the transaction, then atomically record the original failure and initial reconciliation. Preserve this history and operation identity. |
| attempts._identify / _reconciled / _attach | Separate observation from mutation; exact labels and immutable first attachment. Reuse this decision and compare-and-swap machinery under the new proof transaction. |
| intake._failed_start_record | Compares receipt attempt, assignment, start and runtime to the current attempt. Preserve its runtime comparison, including rejecting None versus an attached ID. |
| OciAdapter.list / observe | Listing checks the actual image against the resolved image, every runtime label, and resolved profile/policy/adapter identity; observation distinguishes running, quiescent, absent and uncertain. Reuse these checks. |
| ManagedPreparation._failed_start | Runs before the capacity refusal can prevent recovery; currently fences then calls only known-at-failure cleanup. Add explicit late-proof composition here. |
| PreparationRuntime.adapter | Recovers mounted roots, credential delivery/orphan teardown and adopted launch delivery. Reuse it for the new ending; never rematerialize a start. |

## Exact proposed implementation ownership

Paths are relative to repository baton. Tuner owns the following bounded edits
only after accepted design review, serially under a new W170382 claim. Existing
diffs belong to their authors; the baseline records their current bytes. Recheck
drift/ownership before touching them. This is not ownership of whole modules.

| Path | Scheduled change |
| --- | --- |
| v12/python/src/baton_v12/worker_manager/attempts.py | Add the immutable proof operation/reader described below; share existing original-receipt reading and identification/attachment logic. No change to original failure recording, generic retry policy or runtime state machine. |
| v12/python/src/baton_v12/worker_manager/intake.py | Add a separately named late-proof cleanup API and operation constructor, using existing custody/settlement owners. Preserve the original failed-start runtime guard and command. |
| v12/python/src/baton_v12/worker_manager/documents.py | Closed new late-identity receipt and late-failed-start destroy body; export their member sets and constructors in the package's established style. No optional proof fields on an old document. |
| v12/python/src/baton_v12/worker_manager/oci.py | Add one closed destroy_late_failed_start receiver delegating to existing _removed. No new engine algorithm, list semantics or provider delivery lifecycle. |
| v12/python/src/baton_v12/worker_manager/__init__.py | Export only the new public proof reader/operation and cleanup API/operation constructor. |
| v12/python/tools/integration_worker.py | Select known versus late failed-start ending from original owner facts; drive observation/proof before ending, enforce cleanup completion before capacity ending. |
| v12/python/tools/stage_execution.py | Only any necessary PreparationRuntime adapter/recovery composition for the new sibling capability. Preserve existing delivery adoption. No broad stage repair. |
| v12/python/tests/manager/test_attempts.py | Add proof/replay/race/restart and late cleanup tests beside original failure tests; preserve their mismatch assertions. |
| v12/python/tests/manager/test_failed_start_destroy.py | Add new closed sibling, cross-call refusal, exact removal/absence and delivery/custody tests through the deterministic engine boundary. Preserve existing five-member command assertions. |
| v12/python/tests/manager/test_boundary_inventory.py | Register and probe every new caller, injected and adopted crossing, outbound constructor and export. No allowlist exemption or removal of discovery. |
| v12/python/tests/tools/test_managed_preparation.py | Extend actual worker fixture with unknown-to-known, permanently unknown, partial delivery and restart cases; preserve known-failure success and all earlier recovery cases. |
| NEW v12/python/FAILED-START-RECOVERY.md | Durable API guide: distinct known/late receipt chains, recover/hold behavior, custody and replay; no transient Work IDs or deployment commands. Main DEPLOYMENT stays protected; group4 owns later integration of user documentation. |

This prerequisite adds five generic source paths and three existing test paths
to the inherited selection, plus the new API guide. The two composition files
and managed-preparation test already belong to that selection. No other source,
schema, migration, manifest, transport version, dependency or execution recipe
change is proposed. Existing store, lanes, scheduler, Authority, single_worker,
workspaces, launch, credentials, input/output, exchange, target and generic
state-transition owners remain reuse-only. Later group2 work still has its
original finite nine-source/eight-test selection and dossier draft obligation.
An additional required path is a concrete review amendment, not an implicit grant.

## Proof operation and immutable document

Proposed public API:

```python
reconcile_failed_start_runtime(store, adapter, *, attempt_id)
late_start_identity_of(store, attempt_id)
```

The first API obtains evidence itself through the configured adapter. It accepts
no caller runtime ID, label dictionary, failure document, proof digest or
absence boolean. The reader returns the committed closed receipt or None; it
does not authorize a mutation from a caller's reconstructed document.

New journal kind/document: `runtime.start-failed-late-identity`. Required fields:

```text
attempt_id, expect, start_operation_id, start_record_digest,
failed_start_operation_id, failed_start_record_digest, runtime_id, labels
```

`expect` is the complete fixed assignment. `labels` is the full existing
RUNTIME_LABELS document: runtime attempt, Authority, Work, participant,
generation, principal, effective scope, profile, policy and adapter. OCI's
existing listing receiver proves the resolved image before exposing a candidate;
an arbitrary ID or matching Work/generation alone is insufficient. The receipt
records identity, not a permanently current liveness assertion. No observation
timestamp or changing runtime state is part of its identity.

The original failure digest is the canonical digest of its decoded committed
result, exactly as the old cleanup uses. `start_record_digest` binds the original
start journal kind, signature and decoded committed result as one canonical
document; it excludes incidental database/time metadata. Readers require the
derived operation ID, expected kind, committed state and valid closed result,
and compare the signed operands to the attempt/assignment rather than trusting
that a row merely exists. Receipt reading uses the existing owner journal APIs.

The new operation ID derives ONLY from attempt ID, fixed assignment and original
start operation ID. Runtime ID, labels and both record digests are signature
operands, never key material. A changed runtime/receipt therefore reaches the
same key and collides; it cannot obtain a second authorization under a new key.
Missing/kind-invalid/changed journal evidence refuses without rewriting history.

For first issuance require a real committed start and start-failed receipt for
this exact attempt/assignment, with original runtime_id=None and original
execution_runtime=uncertain. A non-null original receipt always uses the old
API and its exact comparison. Preparation failure before a start, an ordinary
running attempt without a failure, or an abandonment declaration is ineligible.

Ask through the existing identification owner outside the write transaction.
Retain the exact validated candidate labels in its private identification plan
for this proof (not by fabricating labels at the receipt writer). First issuance
requires exactly one matching runtime and a conclusive running or quiescent
observation. Empty/malformed/unavailable listing, uncertain observation,
conflicting labels, mismatching current attachment or multiple candidates
creates no proof and invokes no destructive capability. A known ID supplied by
some other caller is not a substitute for that first complete listing evidence.
Foreign rows cannot supply a candidate; same-attempt contradictory labels refuse.

Inside one existing ControlStore transaction, reread the original records and
fixed attempt facts against the captured signature, attach exactly the proved
runtime using _reconciled/_attach within that transaction, and seal the receipt.
Require the returned attachment to agree; a cancellation/refusal rolls back the
whole proof act. A crash or failed seal leaves neither new attachment nor proof.
If an earlier public reconciliation already attached the SAME runtime, fresh
complete adapter proof may still establish this receipt; a different attachment
refuses. Do not change the original failure receipt even in that recovery case.

Separate immutable replay from current observation. Exact proof replay returns
the same receipt and cannot refresh its historical fields. It first validates
the receipt chain/current fixed identity; fresh observations needed for a new
cleanup go through the existing reconciliation owner. A new conflicting listing
is a refusal, never a replacement receipt. No engine call occurs under a store
write lock. The first proof transaction rechecks database facts after observation,
so concurrent proofs for different runtimes cannot both commit.

## Separate cleanup crossing

Proposed public API and adapter capability:

```python
authorize_late_failed_start_cleanup(store, port, adapter, *, attempt_id,
                                    retention_policy_digest)
late_failed_start_destroy_operation(attempt, failed_start_record_digest,
                                    late_identity_digest, retention_policy_digest)
OciAdapter.destroy_late_failed_start(command)
```

The cleanup API reads the original failure AND committed late-identity receipt
from the same owner journal, verifies their complete chain and the current
attempt's exact runtime/assignment/start, then derives the removal. Supplying
the new receipt's digest as `failed_start_record_digest` to the old API is
forbidden. A shared original-record reader may be factored into attempts.py;
intake._failed_start_record keeps its existing strict runtime comparison.

New closed body `destroy.late-failed-start-command` has exactly:

```text
assignment_ref, runtime_attempt_id, runtime_id, failed_start_record_digest,
late_identity_digest, retention_policy_digest
```

The optional delivery envelope remains `operation`, as on existing adapter
commands. New kind/ID prefix is `runtime.destroy-late-failed-start`; ID and
signature bind both authorizing digests, exact fixed attempt/assignment and
retention policy, with runtime in the signature. Original command kinds/member
sets/signatures remain unchanged. Every cross-call among ordinary receipt,
known-failure and late-failure bodies refuses. The adapter owns the new body at
entry and delegates exact removal, positive absence and delivery teardown to
_removed; it has no ControlStore, proof-minting or result-intake capability.

For an already committed identical cleanup, replay its result without demanding
the removed runtime appear in a new listing. Validate the retained chain first;
changed proof/runtime/policy cannot replay that result. For a new or unfinished
cleanup, require the existing Authority exclusion check and nonterminal cleanup.
Refresh runtime evidence through the identification owner: conflicting/multiple
identities refuse, uncertainty remains held. After a proof exists, a missing
listing can be resolved only by positive observation of that receipt's exact
attached ID; it cannot establish first-time identity or license a new start.

Use the existing generic ending sequence and result validation: Authority fence,
exact runtime removal, positive absence, credential/orphan and launch teardown,
directory custody, retained cleanup, then preparation membership ending. Reuse
_not_an_ending, _normalized and _settle_recordless_cleanup, factoring only the
common observation parsing if needed inside intake.py. No second cleanup engine.
Uncertain removal or pending delivery teardown yields an unsettled outcome;
composition must not call end_integration_execution as though that succeeded.

Retain the existing untrusted per-attempt result directory without a fabricated
worker disposition, frozen manifest, intake receipt, proposal or adoption. Keep
the original failure, new proof and cleanup receipt available through the owner
journal after runtime and delivery roots are gone. No retention deletion is added.

## Composition and restart cuts

ManagedPreparation._failed_start continues to run before ordinary admission.
It first checks committed intent/assignment and member state. A member already
ended returns its existing failure outcome. For an original known runtime use
the old strict cleanup path; for an originally unknown failed start, establish
or read the late proof, refresh exact observation when cleanup is unfinished,
then use the new sibling. Existing fencing uses the same stable cancellation
operation. Fencing may occur while evidence is uncertain; it does not prove
exclusion and cannot by itself end membership or release capacity.

No branch returns to prepare/start or invents a new Work/offer/claim/attempt.
Keep parent queued/unclaimed, prepare held until ended as failed, root open and
recovery-required, and apply planned. No successful preparation adoption or
target change occurs. Final failed-root settlement remains the later group's
selected responsibility.

Required restart positions: before positive observation; after observation but
before proof transaction; within proof before sealing; after committed proof
before fencing; after fence before removal; after actual removal before cleanup
receipt; after delivery teardown before cleanup receipt; after retained cleanup
before capacity ending. Reopen composition/Authority/ControlStore/JobStore while
the external fixture runtime survives. First two positions may repeat reads;
none may repeat a start. Transaction rollback keeps proof/attachment atomic;
post-proof recovery uses the immutable chain; post-removal recovery observes
positive absence and resumes ordinary idempotent delivery/custody owners.

## Acceptance and focused verification

These are scheduled tests under standing authority, not additional approval
requests. Preserve original expectations; add cases beside their owners.

| Case | Required evidence |
| --- | --- |
| One inconclusive listing then exact identity | Real start-failed receipt stays None/byte-identical; one new proof binds exact labels/start; real worker exits, deliveries disappear before fixture teardown, result retained, preparation ends failed. |
| Persistent uncertainty | No proof, removal, end or release; no duplicate Work/claim/runtime/harness; actual owner state remains uncertain. |
| Wrong/multiple identity and changed proof inputs | No new proof or destructive effect; preserve original receipt and first proof, including null-versus-known old API refusal. Cover all labels, image mismatch via real OCI receiver, assignment/start/profile/policy and digest disagreement. |
| Replay and competing proofs | Same stable ID/result, changed runtime collides; two independent ControlStore handles cannot commit conflicting receipts. Crash before seal rolls back attachment and proof. |
| Already attached before late proof | Fresh full matching evidence authorizes; unrelated attachment refuses; original failure remains unchanged. |
| Cleanup provenance | Missing/wrong-kind/uncommitted/cross-attempt/altered proof refuses before adapter; live Authority assignment refuses; all closed command cross-calls refuse. |
| Current state changes | Same proof tolerates running-to-quiescent; uncertain observation is not absence. After removal, exact positive absence resumes cleanup without requiring a first-time listing. |
| Partial delivery and destructive retry | Credential orphan and launch adoption, including coordinator restart, remove only owned deliveries after positive exclusion. Pending teardown cannot become ended capacity. Actual process/root checks precede fixture teardown. |
| Retained custody and exclusions | Untrusted result sentinel bytes survive; no freeze/intake/adoption fabricated; original failure/proof receipts survive. Parent/root/apply/target and existing known-failure behavior unchanged. |

Run explicit relevant classes while iterating, then explicit modules
tests.manager.test_attempts, tests.manager.test_failed_start_destroy,
tests.manager.test_boundary_inventory and tests.tools.test_managed_preparation.
Use the existing deterministic supervisor with sensible per-run limits, process
group cleanup and measured ledger rows, including experiments. Do not invoke
discover or actual engine modules. Read-only source/export inventory and
tests.manager.test_dependencies may verify the added exports/dependency boundary
without editing that test. The first full inventory run needs its own sensible
timeout based on existing evidence; no cumulative stopwatch gate is added.

The prior13 stage errors remain bounded historical baseline evidence; this
design claims no clean broader regression run. New tests must discriminate the
late receipt from the old mismatch guard, proof-before-attachment atomicity,
wrong-runtime refusal and actual ending/delivery effects, not just count calls.

## Handoff and remaining scope

This claim changes only this design, its baseline/manifest and owning record
status. Tuner performed source/record review and static binding, zero tests or
engine/model executions. Reuse reviewer172443's measured evidence: cumulative
reviewer124.07460133001587s, author recorded30-row subset919.4569689099153s;
older unmeasured experiments remain unknown. Group1 and parent spending remain
separate. Search-path mistakes (runtime_adapters/oci.py, tests/manager/
test_boundaries.py, test_documents.py, v12/docs and v12/spec) were nonexistent
guesses, not unavailable required files; actual owners were located and read.

Pass to baton.feat with set-next=baton.tune for independent DESIGN review.
Reviewer should accept or correct this concrete12-path amendment, immutable
proof/replay/atomicity semantics and new closed cleanup crossing. No product
bytes are offered for implementation acceptance yet. After an accepted design,
tuner implements under a fresh claim and supplies a digest-bound complete
generic/composition candidate for independent review. The remaining group2
identity/custody/causal/limits/two-Job/exclusion/direct/legacy matrix and
DEPLOYMENT-SLICE2-DRAFT.md remain required. No group2 closure, import approval,
parent development or W170385/parent dependent release follows this packet.
