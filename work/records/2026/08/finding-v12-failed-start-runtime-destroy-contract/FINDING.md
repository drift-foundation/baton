# Add the failed-start runtime destroy contract

## Discovery and ownership

W34998 is the bounded provider Work created by the approver ruling that unblocks
W32648. It owns the negotiated no-envelope destroy command and adapter crossing
for an exact runtime created by a failed start. W32648 owns composition of that
provider into the failed-start ending after this Work closes.

## Operational finding at intake — 2026-08-28

**Observed:** W34998 became ready with no repository binding, so there was no
exact dossier to read. The reviewer claimed it, recorded the missing binding
here, and created this canonical record before beginning technical research.

## Confirmed decision

Approver messages M34998/M34999 choose an explicit sibling no-envelope failed-
start destroy command. Preserve the existing intake-receipt-based destroy
command unchanged; a failure-record digest must never occupy an
`intake_receipt_digest` field.

The new negotiated command carries:

- the fixed assignment and runtime attempt;
- the exact runtime identity;
- the manager-owned failed-start record digest; and
- the retention-policy digest.

It removes the exact container, proves positive absence, and retains the
unique result directory as untrusted. It does not create or validate an intake
receipt, invent worker disposition, copy a second quarantine result, admit
material to the proposal pipeline, or delete that directory. W32648 resumes
only after this contract and adapter crossing land.

## Research status

## Current-tree revalidation — 2026-08-28

**Confirmed existing receipt-authorized path.** The frozen
`runtimeDestroyBody`, `documents.destroy_command`,
`intake.authorize_cleanup`/`_destroyed`, and `OciAdapter.destroy` all require
the same five body members: fixed assignment, attempt, runtime identity,
`intake_receipt_digest`, and `retention_policy_digest`. The intake path reads
the receipt before deriving its operation identity, refuses cleanup without
that receipt, delivers the complete body plus operation, removes the exact
runtime, observes it, and settles credential/launch roots only on positive
absence. Those semantics are accepted and remain unchanged.

**Confirmed provider boundary.** The failed-start command is trusted Manager
to runtime-adapter traffic, not worker traffic. No worker or remote peer needs
it, and sending it through worker-control 1.0 would require a new exact minor
schema because extensions may not alter lifecycle, digest or receipt meaning.
This bounded local provider Work therefore does not edit any frozen
worker-control 1.0 schema or envelope. The distinct adapter callable is the
capability boundary; the installed adapter's already-recorded exact build/
interface digest binds which provider implements it. A future remote transport
requires separately negotiated/versioned Work rather than silently adopting
this Python interface.

## Exact provider contract

Add one closed manager document, recommended public constructor
`failed_start_destroy_command`, with exactly:

```text
assignment_ref
runtime_attempt_id
runtime_id
failed_start_record_digest
retention_policy_digest
```

`runtime_id` is non-null: this command exists only for the exact runtime that
post-create reconciliation attached. `failed_start_record_digest` is the
canonical digest of the exact committed manager-owned `runtime.start-failed`
result, not a digest of free-form exception text, an operation signature, an
intake receipt, or an invented worker envelope. The caller may carry the fixed
manager operation metadata beside the body, following the accepted destroy
crossing, but that metadata does not change these five body operands.

Add a distinct adapter capability, recommended `destroy_failed_start(command)`.
Do not make `destroy` accept a union and do not fall back from the new method to
the receipt-authorized one. The new receiver owns its closed body before engine
activity, then uses the exact same private removal/observation/provider-ending
core as `destroy`. Factoring that core is allowed; duplicating provider logic or
changing either public method's accepted member set is not.

The provider interprets only the exact runtime identity it acts on. Assignment,
attempt and digests are manager authorization travelling with the command; the
W32648 caller owns their relationship to the durable attempt and journal before
crossing. The adapter returns the same closed destroy observation: exact
runtime, `running|quiescent|absent|uncertain`, reason, credential ending, and
launch ending. Only positive `absent` settles provider teardown.

## Custody and non-overlap

This provider removes a container and settles delivery roots. It does not read,
copy, validate, freeze, collect, admit, quarantine, retain-policy-delete, or
otherwise mutate the result directory. That unique directory was created
untrusted and stays in place untrusted. W32648 owns authority fencing,
failed-start journal validation/digesting, manager operation identity and
signature, retry/collision/restart composition, cleanup-axis settlement to
`retained`, and delivery-root settlement across the complete ending.

## Acceptance

- The existing receipt-authorized document and `destroy` method remain closed
  to their original five members and all existing tests remain green.
- The sibling method accepts only its five-member body plus the explicitly
  carried operation metadata; null runtime, missing/extra members, an intake
  receipt in place of the failed-start digest, or cross-calling either body on
  the other method refuses before engine activity.
- The exact runtime is force-removed and then observed. `absent` is positive
  evidence; `running`, `quiescent`, `uncertain`, malformed observation, engine
  failure and provider teardown failure remain distinguishable and do not
  overstate settlement.
- Credential and launch providers reuse their existing ordered teardown and
  retry behavior. No second implementation of those owners is introduced.
- A sentinel in the unique result directory survives successful removal,
  repeated removal, provider retry and process reconstruction.
- Boundary/contract inventories, declared-operand and secret/canary sweeps name
  the new digest and callable explicitly; no failure digest appears in an
  `intake_receipt_digest` field or frozen schema.

## Verification environment

**Observed:** the repository root `.venv` cannot collect the focused provider
suite because it lacks `jsonschema`; system Python has no `pytest`. This is the
already-recorded environment split for the self-contained v12 distribution,
not a product failure. Implementation verification must use the distribution's
prepared dependency environment and report any unavailable real-engine gate
without escalation or substitution.

## 2026-08-29 — implemented

**Confirmed against the current tree before acting**, rather than transcribed:
`destroy.command` still requires exactly its five members with
`intake_receipt_digest` among them; `OciAdapter.destroy` still owns that body
and then removes, observes and settles both deliveries on positive absence;
`runtime.start-failed` is the manager-owned record whose canonical digest this
new command carries.

**The sibling landed as pinned.** `destroy.failed-start-command` carries the
fixed assignment, the attempt, the exact runtime, the failed-start record
digest and the retention policy digest -- five members, no optional member at
all, and neither digest appears in the other document. `destroy_failed_start`
owns that body before any engine activity and shares `_removed` with `destroy`
rather than duplicating an ordered teardown.

**No frozen schema was edited**, and a case measures the files rather than
promising: no `*.schema.json` names `failed_start_record_digest` or the new
document, and the frozen destroy body still requires its receipt.

**A hole this round found in its own first coverage.** The document assertions
compared only the REQUIRED member tuple, so a mutation adding
`failed_start_record_digest` as an OPTIONAL member of the receipt-authorized
command measured zero -- exactly the conflation the ruling forbids, arriving
through the half nobody was looking at. Both documents are now asserted
required-and-optional, and both are proved closed to five with no optional
member.

**Custody, unchanged and proved so.** The provider names no result-directory
operand at all, its body contains no filesystem call, and a sentinel survives a
successful removal, a repeated removal, a provider retry and a rebuilt adapter
-- on the fake engine and again on a real daemon.

## 2026-08-29 — independent review

**Confirmed:** no blocking production finding was found in the closed sibling
document, separate adapter method, shared removal core, ordered provider
settlement, cross-call refusals, or untouched result-directory custody. The
focused provider, existing OCI, contract, dependency, secret and text sweeps
are green in the reviewer environment.

**Corrected review evidence:** two mutation-harness anchors no longer matched
the implementation even though the checked-in transcript reported six caught
mutations. The reviewer updated those evidence-script anchors and reran the
harness; all six current mutations are now caught. This changes no production
code.

**Operational finding — required real-engine proof is not independently
available.** The checked-in `w34998-gate-2026-08-29.txt` ends when the parallel
phase fails on known concurrent Work and explicitly says the serial registry
did not run. It therefore contains no execution of
`test_failed_start_destroy_engine`, despite PROGRESS claiming that suite among
83 serial tests. The reviewer invoked that exact module, but this managed
context cannot connect to `/var/run/docker.sock`; its required gate fails in
`setUpClass` with permission denied. Standing managed-turn policy forbids an
escalation workaround. Satisfying closure requires a durable successful
transcript from the already-authorized engine-capable runner (or a changed
product result if the gate fails), then one final review pass.

## 2026-08-29 — final independent review

**Confirmed:** the missing real-engine evidence is now durable at
`evidence/w34998-engine-gate-2026-08-29.txt`. It identifies the Docker client
and server, records Podman's narrow absence, names and passes all four cases in
`tests.manager.test_failed_start_destroy_engine`, and records the complete
engine-owning serial registry: 83 tests passed with the six expected Podman
skips. The evidence directly covers exact removal and daemon-observed absence,
idempotent repeat, retained untrusted result-directory custody, and cross-body
refusal before engine activity.

The reviewer reran the daemon-free 19-case focused provider suite and the
corrected six-mutation harness on the current tree; both are green. No
production change was made in the evidence round, and the prior review found
no blocking production defect. W34998 therefore satisfies its bounded provider
contract and may close, unblocking W32648's separate composition Work.
