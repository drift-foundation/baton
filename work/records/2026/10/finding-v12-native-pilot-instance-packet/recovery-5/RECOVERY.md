# W325959 recovery 5 — share the already committed workspace root

Prepared by baton.codxpc under claim329727 for independent review. This is a
configuration recovery proposal, not authority to apply it or restart the pilot.
Scope and decision: ../PLAN.md, ../FINDING.md (2026-10-19T04-30-14Z), and
../review-2026-10-19T04-30-14Z.md. Revision4 and all prior acceptance evidence
remain unchanged. Its startup-readiness claim was superseded by that review.

## Confirmed cause and correction

`stage_execution.operations_from` passes one control store to both
`single_worker.worker_preflight` calls. The latter commits one workspace storage
root and refuses a different root. Revision4 assigned a separate root per role.

Supported **read-only** `ControlStore.open_readonly` and
`configured_workspace_storage` now establish the actual committed root:

`/home/sl/baton-instances/native-coordination-pilot-w321608-1/workspaces/implementation`

This is a measured readback, not an inference from worker order. ROOT.json and
STATUS.json in evidence record the public reads at the selected source. The
current checkout has later provider-adapter edits; this proof imports the exact
owner-prepared source `/home/sl/baton-builds/native-pilot-14e52d80/v12/python`,
base `14e52d80679de5e844f72324df632da5e01cf393`.

Change only each review worker's `deployment.workspace_storage` to that root in
four files, preserving the author worker's existing setting:

- `deployment.json`
- `generated/configuration.json`
- `generated/configure-inputs.json`
- `inputs.json`

`CHANGE.json` binds exact before/after SHA-256 and modes; `before/` and `after/`
contain those actual bytes. All other JSON values compare equal. In particular,
launch and credential homes remain distinct, and nominated sources, input
manifest, policy and image identities remain unchanged. Workspace storage is the
manager's allocation root, not a shared writable attempt directory; private
per-attempt placement and exclusive ownership remain the product's responsibility.
No source staging, per-attempt allocation or live runtime is performed by this packet.

Twelve other installed files are pinned unchanged, including the selector,
authority identity, submission, task, manifest, dossier and historical preparation
readbacks. Those readbacks retain the original configuration observation rather
than being silently rewritten. This new packet and its application stdout are the
superseding configuration record. The submitted Job's input/policy identities and
3600/900 per-invocation limits do not change; no resubmission is needed or allowed.

## Retained episodes and recovery

Public canonical status reports native Work `1cdb8d19-W1` in authority
`1cdb8d19feda47c0a209bd0669b16871`, Job `quickstart-a`, submission
`sub-w321608-quickstart-1`. Implementation is queued and review blocked on it.
Both retain episode1, opened 2026-10-19T04:28:46.749Z by
`w325959-owner-submit-1`. Exact attempt/offer identities are in CHANGE.json.
Neither stage has a recorded runtime, allocation, receipt, exchange or artifact;
`outstanding_offers` returns an empty list. These are recorded-state observations,
not an engine-based cessation proof. Owner E329713 also reported manager/publisher
absent. Application takes the product's nonblocking manager guards for **both**
old roots and refuses a live holder before replacing configuration.

An open Job episode is not itself an issued worker offer. The public
`recover_on_restart` operation expires/abandons issued offers and preserves
accepted offers. For this exact empty-offer checkpoint, the expected result has
empty `abandoned` and `recoverable` lists. It neither opens a replacement episode
nor launches anything. The packet refuses if the complete canonical Job/episode
projection, any outstanding offer, committed root, immutable artifact, store inode
or candidate bytes changed. A new runtime/offer/receipt requires renewed diagnosis,
not an optimistic retry based on this old observation.

`recover_packet.py recover` performs that public boundary under the same manager
guards and verifies the retained state afterward. It does **not** call the manager
sweep/reconcile loop: that loop may admit and launch work. Later explicitly selected
`start` performs normal manager recovery and serving against the existing Job.
There is no deletion, replacement store, bootstrap replay, claim release, receipt
fabrication, resubmission, episode replacement or automatic retry in this packet.

## Deterministic evidence

`verify.py` exercises the real `worker_preflight` against one disposable control
store, with an injected credential-provider object and an engine callback that
fails if called. It reproduces the distinct-root refusal, proves both workers pass
with the recorded root, and preserves the same Job and episode records through
failure, fresh-handle recovery and configuration application. Public recovery is
invoked and its empty report verified. No provider/engine is contacted.

Final `evidence/VERIFICATION.json`: 22 checks passed in 0.049778792 seconds.
First run: 20 checks in 0.047956898 seconds, retained separately. Total measured
verification for this correction: 0.097735690 seconds. Reads/authoring/import time
are not included. Tests also prove candidate tamper, file drift and stale episode
refusal before configuration replacement, exact four-file application, mode/byte
checks, replay and preservation of the original two episodes. This is focused
preflight/recovery evidence, not full live startup or model-output acceptance.

## Exact proposed owner operations — not executed by preparer

After independent review and owner selection, run from any directory with the
following fixed environment and paths. No live state or product files were changed
by the preparer. The read-only `check` command was run successfully against the
actual instance; `apply`, `recover` and `start` below were not run.

```sh
export PYTHONPATH=/home/sl/baton-builds/native-pilot-14e52d80/v12/python/src:/home/sl/baton-builds/native-pilot-14e52d80/v12/python
PILOT_PY=/home/sl/.local/state/baton-v12-venv/bin/python
PILOT_PACKET=/home/sl/src/baton/work/records/2026/10/finding-v12-native-pilot-instance-packet/recovery-5
"$PILOT_PY" "$PILOT_PACKET/recover_packet.py" check
```

Verify this packet against its independently reviewed MANIFEST.json before applying.
The file-level operation checks every guard before writes, then repeats checks under
both product manager locks. Owner selects application separately:

```sh
"$PILOT_PY" "$PILOT_PACKET/recover_packet.py" apply --owner-selected
"$PILOT_PY" "$PILOT_PACKET/recover_packet.py" recover --owner-selected
```

Run those commands individually and retain their JSON stdout. Stop on any refusal.
The application atomically replaces each file and preserves its mode. There is no
cross-file filesystem transaction. If interrupted, retain staged files and inspect
the exact partial state. A mix of reviewed before/after bytes refuses by default;
only separately selected `apply --owner-selected --resume` may finish that exact
mix. Unknown bytes refuse even with --resume. A retained `.w325959-recovery-5.tmp`
file is never overwritten or removed by this script; report it for inspection.
An already complete application is an idempotent no-op. No rollback is automatic.

Review application/recovery readbacks, then, only if owner selects start:

```sh
TMPDIR=/tmp just -f /home/sl/baton-builds/native-pilot-14e52d80/v12/justfile start /home/sl/baton-instances/native-coordination-pilot-w321608-1
TMPDIR=/tmp just -f /home/sl/baton-builds/native-pilot-14e52d80/v12/justfile status /home/sl/baton-instances/native-coordination-pilot-w321608-1
```

TMPDIR avoids the reviewer's observed `/run/user/1000/just` temporary-file refusal;
it changes no configured instance or workspace path. Do not submit again. Capture
actual retained Job/episode/runtime evidence after start and stop on a new refusal.
Supervisor termination does not prove container cessation; unknown runtime keeps
its exclusion and must be handled through supported reconciliation. Native delivery,
independent semantic review and human acceptance/integration/closure remain owed.

No product source change or new bundle build is required for this configuration
correction. W321608 remains open through native delivery. Human Git checkpoint for
the accepted packet remains pending; suggested message after review:
`docs: correct native pilot shared workspace configuration`.
