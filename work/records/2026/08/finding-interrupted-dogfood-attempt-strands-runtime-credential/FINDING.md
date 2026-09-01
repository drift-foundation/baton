# An interrupted dogfood attempt strands a runtime and a live credential

Work: W55758
Observed on: W51487 attempt `attempt-w51487-run7`
Related ACP claim settlement: W55705,
`work/records/2026/08/finding-acp-turn-teardown-strands-live-worker/`
Source attempt record:
`work/records/2026/08/finding-first-useful-task-second-attempt/`

## 2026-08-31 — initial observation

The managed ACP turn supervising run7 ended after the v12 worker had written
its workspace answer but before `dogfood_operator` could freeze output, take
intake custody, decide retention, or destroy the runtime. The v12 control arc
therefore stopped after `attempt.attach` while three external facts survived
the supervising process:

- the Docker runtime remained live until the operator stopped it;
- the volatile credential slot remained on the host until separately
  discarded; and
- the worker's complete-looking workspace proposal remained untrusted, with
  no manager freeze, intake receipt, retention decision, or terminal evidence.

The operator later stopped the exact container and invoked
`CredentialHome.discard_orphan` without reading the bearer. The credential
slot is now absent and `/tmp/w51487/run7/credential-home/credentials/` is
empty. The temporary run7 tree remains preserved for research.

## Evidence status

The Work's launch message says exact run7 paths and evidence already exist
under the W51487 dossier. **Observed:** no
`evidence/w51487-run7/` directory and no run7 entry currently exists there.
The durable source record ends with the run6 account. The available evidence
is still under `/tmp/w51487/run7/`, plus the Work's message and operational
recovery journal. Treat the missing cited durable copy as an operational
finding; do not infer its contents from the message.

Do not open, copy, hash, or publish any credential content. Do not inspect the
v12 authority or control SQLite files with raw SQL. Durable evidence for this
finding must be a redacted inventory or output obtained through the public
manager surfaces.

## Confirmed safety boundary

The workspace proposal is not a retained candidate. A worker-authored output
document and files existed, but the manager had not frozen or independently
accepted them. Recovery must not promote, accept, or pass that material merely
because it looks complete.

Runtime absence and credential absence are separate facts. Stopping the
container does not remove the host credential slot, and removing the slot does
not journal the attempt's runtime/authority/cleanup ending.

## Open research questions

- Which public operation can adopt or end an attempt interrupted after
  `attempt.attach` but before `output.freeze`, after the original operator
  process is gone?
- Does targeted `CredentialHome.discard_orphan` preserve, block, or falsify a
  later `abandon_attempt` ending?
- Which component owns prompt removal of credential material when supervision
  disappears, without releasing it while a runtime may still read the mount?
- What durable declaration and exact identities allow recovery to resume
  safely after process restart, including an already-absent runtime?
- How should the operator report and retry partial cleanup without replaying
  staging, provider work, output acceptance, or authority mutation twice?

## 2026-08-31 — reviewer reproduction and root cause

### Observed run7 state through public surfaces

The adjacent `evidence/inventory_run7.py` was run against offline copy
`/tmp/w55758-run7-copy.UdSqdZ`. It opens the copied control store only through
the public `ControlStore` API and never opens either SQLite file itself. Its
redacted answer is retained as `evidence/run7-inventory.json`:

- `attempt.attach` is committed for the exact run7 runtime;
- the attempt still holds its internal v12 runtime lane;
- `frozen_output_of` is absent;
- `intake_receipt_of` is absent;
- `retentions_of` is empty;
- worker-authored `workspace/output.json` is present; and
- manager `evidence.json` is absent.

The worker's document says provider status 0, verification status 1 and one
changed path. Its manifest was written at `2026-08-31T17:58:46Z`. These are
facts about untrusted workspace bytes, not a manager freeze or intake result.
No candidate content is copied into this record.

Read-only Docker inspection at `2026-08-31T18:45:42Z` shows the exact labelled
container still exists in `exited` state with PID 0 and exit code 137. It is
stopped, not manager-proved absent. Exact metadata is retained in
`evidence/run7-runtime-inspection.md`; this review did not remove it.

### Confirmed defect 1: no public recovery mode for this durable state

`v12/python/tools/dogfood_operator.py::run_dogfood_task` creates its evidence
document only after the runtime attaches and keeps it in memory until the
outer command returns or catches an ordinary fault. Process death loses that
document even though the manager stores, launch delivery, workspace, runtime
labels and credential lifecycle record survive.

The only restart command is `--retry-handoff`. Its documented and enforced
precondition is a completed, frozen, intaken, retained and independently
verified result. `retry_handoff` explicitly refuses missing trusted-result
members and says an attempt without them belongs to W44716 abandonment.
Run7 correctly cannot enter this path.

The ordinary command is not recovery. It materializes a fresh credential and
replays staging/claim/start; exact whole-attempt replay deliberately refuses
against the already-created roots and operations. No `--recover-abandoned`,
`--abandon` or equivalent public command constructs existing capabilities and
calls the exported `abandon_attempt` operation. The manager therefore has the
right receiptless ending and the dogfood deployment has no way to invoke it
after its original process dies.

### Confirmed defect 2: the dogfood deployment splits one credential lifecycle

The normal launcher materializes the credential with:

```text
CredentialHome(given["credential_home"])
```

For run7 that is `/tmp/w51487/run7/credential-home`. `OciAdapter`, however,
does not hold that home. `_credential_home()` derives another one from the
assignment workspace, `/tmp/w51487/run7/storage/attempt-w51487-run7`, and
uses it to publish, recover and remove the lifecycle record.

The live run7 record demonstrates the split rather than merely suggesting it:

- the volatile root named inside the record is below the granted home;
- the record itself is below the assignment-derived home; and
- the two `CredentialHome` objects each assume the volatile root and record
  are siblings below themselves.

This contradicts the component's own one-home contract and the prior W6634 /
W6636 recovery evidence, which requires `OciAdapter.recover_credentials` to
operate over the adapter's own credential home. It also defeats the dogfood
restart builder `_for_retry`: that builder reads state from the granted home,
sees none, and builds `OciAdapter(credential_delivery=None)` even though the
assignment home has a `live` record.

`evidence/reproduce_run7_recovery_gap.py` drives this against the offline copy
without any engine or authority act. The retained result in
`evidence/run7-recovery-gap.json` proves:

- adopting the assignment-home record refuses because its recorded root is
  not that home's proved root;
- `_for_retry` adopts the launch delivery but no credential delivery; and
- on positive runtime absence that adapter would answer credential
  `not-delivered`, not `torn-down`.

The current public retry acceptance test does not catch this integration
defect because its real durable-state case configures `credential_slots: []`
and its adapter reports both providers `not-delivered`.

### Confirmed emergency-cleanup outcome

The targeted emergency call removed the granted volatile root without reading
the bearer, which eliminated the live credential copy. It could not complete
the lifecycle because it acted through the granted home while the record is
under the assignment home. Current state is therefore:

- credential bytes: absent;
- granted-home lifecycle record: absent;
- assignment-home lifecycle record: present and `live`;
- runtime: exited but still present;
- internal v12 runtime lane: still held; and
- attempt cleanup: not terminal.

The original message's inference is corrected: `discard_orphan` did not make
`abandon_attempt` syntactically unreachable. It did remove the material needed
by ordinary `Delivery` adoption, while leaving the other home's live record;
the available restart builder then constructs no delivery and would misstate
the provider ending as `not-delivered`. That is a stronger and measured defect
than the original hypothesis.

## Required recovery contract

The prior W44716 ruling already decides that abandonment is explicit, not a
timer inference. Reuse that decision rather than inventing automatic cleanup:

1. A public dogfood recovery command takes the existing grants, an explicit
   operator reason and an output path for a new recovery record. It does not
   require the lost `evidence.json` or a credential source.
2. It holds the editable grants against the manager's durable attempt,
   assignment, runtime, profile, policy, roots and provider records before an
   external mutation. A newer attempt, authority, generation, runtime or home
   refuses.
3. It constructs only recovery capabilities. It performs no restage, offer,
   claim, provider turn, worker conversation, freeze, intake, retention
   decision, pass or partial-output acceptance.
4. It calls the exported `abandon_attempt`, preserving its durable declaration,
   exact authority fence, force-remove, positive-absence, directory-custody,
   terminal-retained and lane-release ordering. An exited-but-present
   container is still force-removed and observed absent.
5. Credential teardown is part of that one ending after positive runtime
   absence. Restart cleanup unlinks the exact bounded root without reading a
   bearer, removes the exact lifecycle record, and reports `torn-down`. It
   never reports a historically delivered credential as `not-delivered`.
6. Runtime uncertainty or credential root/record/mount disagreement leaves
   cleanup non-terminal and names the exact unresolved resources. It does not
   release the lane, forget a live bearer, or accept workspace output.
7. The explicit abandonment identity makes interruption retryable at every
   boundary. A retry with the same reason and policy resumes/replays; a
   conflicting declaration collides; a terminal retry returns the same
   composite result without another external act.
8. The recovery evidence separately reports authority fence, runtime removal,
   credential ending, launch ending, directory custody and terminal manager
   state. It records no credential bytes or digest and does not call the
   worker-authored output trusted.

W55705 complements this contract at the supervisor boundary: an ACP turn that
leaves a v11 claim must raise an incident and retain later readiness. It does
not stop or settle this v12 runtime, credential or internal lane. W55758 owns
the explicit manager/deployment recovery once an operator acts on that
incident.

## Proposed patch boundary

**One owner is mandatory.** The same nominal credential-home capability must
govern materialization, lifecycle-state publication, restart adoption, orphan
cleanup and ordinary teardown. Do not repair this by trusting the
`credential_root` path from the record, deriving another raw path in the
deployment, or adding a third cleanup home.

The smallest coherent direction is to make the already-validated
`CredentialHome` capability used by `_launched` an owned `OciAdapter`
construction capability, and make `_for_retry` plus the new abandonment
builder recover through that same owner. An alternative is to move
materialization beneath the adapter's assignment-derived home and remove the
separate grant, but that changes the accepted grants contract and requires an
explicit supersession. The implementer must revalidate and record which one
is current before changing code.

Recovery also needs a no-read representation of a previously delivered
credential whose original process and in-memory `Delivery` are gone. Extend
the credential component with a typed, exact-record orphan teardown after
runtime absence; do not read the bearer merely to recreate a `Delivery` whose
only next act is deletion. The legacy run7 split must be handled explicitly by
holding both configured/proved homes and their record-root agreement, not by a
generic path exception.

Keep the implementation localized to the credential owner, `OciAdapter`
provider ending, and `dogfood_operator` recovery composition. `abandon_attempt`
already owns declaration, fence, runtime removal, terminal settlement and
idempotence; widening or duplicating those mechanics would create a second
ending rather than expose the existing one.

## Regression boundary

Add an end-to-end public-command fixture with at least one real non-secret
credential slot. It must create durable state through `attempt.attach`, omit
`evidence.json`, reconstruct in a fresh process and cross the new recovery
command. Also cover:

- interruption after materialization but before runtime creation/state;
- interruption after runtime creation but before lifecycle publication;
- interruption after attach and after worker workspace output but before
  freeze, matching run7;
- running, exited-present, absent, uncertain, wrong-label and duplicate
  runtimes;
- matching root+record, root absent with live record, record absent with root,
  mismatched root, damaged record and sibling-attempt material;
- restart before declaration, after declaration, after authority fence, after
  runtime removal, between credential and launch teardown, between directory
  receipts and before terminal commit;
- exact retry, conflicting reason/policy, and a newer generation/runtime;
- a canary credential whose cleanup proves unlink-without-read and whose bytes
  never reach recovery evidence, logs, exceptions or operation signatures;
- worker-authored complete-looking output remains `output=open`, has no freeze
  or intake receipt and is retained only as untrusted abandoned material; and
- normal completion and the existing trusted `--retry-handoff` path use the
  same credential owner and still settle both provider deliveries.

Baseline before implementation, from `v12/python` with `PYTHONPATH=src`:

- `tests.tools.test_dogfood_operator`: 159 tests passed;
- `tests.manager.test_credentials`: 92 tests passed; and
- `tests.manager.test_attempts`: 306 tests passed.

## 2026-09-01 — implementer revalidation: two decisions settled before code

### My own W55758 inference was wrong, and the truth is worse in a quieter way

Filing this Work I wrote, labelled as inference rather than measurement, that
`CredentialHome.discard_orphan` may FORECLOSE the `abandon_attempt`
ending — because `destroy_abandoned` settles the credential delivery that
discard has just removed — and that if so, run7 and run8 would be
**unendable** through the public surface. Measured against the current tree,
that is **refuted**.

A recovery process is exactly the shape in which the original in-memory
`Delivery` died with the interrupted process, so a reconstructed `OciAdapter`
holds `credential_delivery is None`. Driving the ending's own credential step
in that shape:

```text
credential_delivery in a recovery process: None
the ending's credential lifecycle_state: {'lifecycle_state': 'not-delivered'}
```

So the ending is **reachable**, and what it produces is a terminal record that
says `not-delivered` — a POSITIVE CLAIM THAT NO CREDENTIAL WAS EVER
DELIVERED —
about an attempt that demonstrably had one and left a 509-byte bearer on
disk for hours. `oci.py` is explicit that this word is not `absent` precisely
so a
reader cannot conclude a credential was torn down because a container was; here
it makes the opposite mistake, and a reader has no way to tell this record from
a genuine no-credential attempt.

This confirms the reviewer's research item 4 from the recovery direction rather
than the offline-copy direction, and it sharpens the requirement: **the recovery
command must carry the credential owner so the ending answers `torn-down` or
`unresolved`, never `not-delivered`.** "Unendable" was the wrong worry; "ends
with a false credential record" is the real one, and it is worse because it
looks settled.

### The credential-home contract: option (a) is current

The Proposed patch boundary offers two directions and requires the implementer
to revalidate and record which one is current before changing code. **Option (a)
is current**: make the already-validated `CredentialHome` capability that
`_launched` builds an owned `OciAdapter` construction capability, and have
`_for_retry` and the new abandonment builder recover through that same owner.

Recorded reasons rather than preference:

- it is localized to the credential owner, the `OciAdapter` provider ending and
  the `dogfood_operator` composition, which is where this record already scopes
  the change;
- it needs **no supersession**. Option (b) moves materialization beneath the
  adapter's assignment-derived home and removes the separate grant, which
  changes the accepted grants contract — and that contract is currently load
  bearing elsewhere: W51487's task-scoped authorization names
  `credential_home` as an operator-granted root, and every retained attempt's
  evidence records it;
- the measurement above says the defect is a MISSING OWNER at the ending, not a
  wrong root. Option (b) repairs the split by deleting one side; option (a)
  repairs it by giving both sides the same owner, which is what the record's own
  "one owner is mandatory" sentence asks for.

No supersession is therefore appended, and nothing in the grants contract moves.

### Baselines, re-verified on the current tree

`tests.tools.test_dogfood_operator`, `tests.manager.test_credentials` and
`tests.manager.test_attempts` together: **557 tests, OK** — the exact recorded
baseline, unchanged.

## 2026-09-01 — APPROVE-LAZY ruling closes the earliest credential window

The approver accepted the reviewer's exact recommendation in Baton response
M59057. Ordinary credential materialization moves into
`_launched.adapter_of`, after assignment activation and before runtime
creation. `run_dogfood_task` keeps its current parameter list.

This ruling **supersedes** the existing bundle-build expectation that
`_launched` already returns a `credentials.Delivery`. The authorized current
temporal contract is instead:

- constructing the launcher bundle leaves no credential root or lifecycle
  record;
- invoking the adapter factory after assignment activation materializes the
  credential exactly once; and
- the resulting adapter receives that exact `Delivery` and the same granted
  `CredentialHome`.

The purpose is to close, rather than recover through, the earliest crash
window: before activation there is no bearer; after materialization the
durable assignment identity and label context needed for bounded recovery
already exist. This does not authorize cleanup from raw grants, move the
accepted grants contract, or supersede option (a)'s one-owner decision.

## 2026-09-01 — open decision: bind recovery grants to the fixed assignment

**Observed:** the documented recovery command does not hold the grants'
`work_ref`, `participant`, and `generation` against the attempt's durable fixed
assignment before acting. A redacted public-command probe changed only the
grants generation from 1 to 2; `main --abandon` still fenced and ended the
generation-1 attempt, returned success, and wrote a recovery record naming
generation 2. The retained reproduction is
`/tmp/w55758-mismatched-grants-probe.py`.

**Confirmed:** `recover_abandoned` branches on `attempt_runtime_of`, whose
public answer currently includes only attempt/runtime/cleanup axes. The
manager has the exact four-part fixed assignment in the same attempt row, but
exposes it only through private `_fixed_assignment`. `abandon_attempt` uses
that row internally, so the ending can act on one assignment while the
deployment record repeats different identities from editable grants.

This violates Required recovery contract item 2. A recovery whose grants do
not exactly name the durable attempt assignment must refuse before authority,
engine, credential, launch, or custody mutation.

**Proposed — APPROVE-EXTEND:** extend the existing public
`attempt_runtime_of` recovery projection with one required `assignment`
member, composed by the manager as the complete four-part assignment document
or `None`. It already projects this same attempt row for this recovery command
and has no unrelated consumer. Returning assignment and runtime facts in one
closed answer avoids a second public reader and a split recovery snapshot.

The deployment then compares that assignment exactly with the held grants
identity `{work_ref, participant, generation}` before choosing either recovery
branch or performing any external act. An absent fixed assignment or any
authority UUID, Work, participant, or generation mismatch refuses closed. The
recovery record uses the manager-fixed identity after the match; it never
publishes editable grants as though they were the identity the ending used.

**Alternative — ADD-READ:** add a separate public
`attempt_assignment_of(store, attempt_id)` projection. This is coherent but
adds a second public surface and read where the existing recovery projection
already owns the same row. No implementation should choose between these
public contracts without approval.
