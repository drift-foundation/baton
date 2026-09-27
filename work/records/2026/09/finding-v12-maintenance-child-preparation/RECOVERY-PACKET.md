# W285465 — provisional maintenance recovery and integrated evidence packet

Prepared by baton.tuner under W285806 claim285818, 2026-09-27. Advisory input only.
W285465 waits on W285464 by actual edge285468; predecessor acceptance and normal
claim/file transfer still apply. This packet is not another gate. No tests ran.

## First executable step and exact boundary

After accepted W285464 and successful child claim, compare its actual product/test
manifest and latest review with this packet and the accepted facility. Pin the
finite interruption hooks below to the **actual** maintenance preparation path,
not an invented second dispatcher. Record API/receipt changes and exact owned
paths before editing. Reuse G1 and both G2 predecessor proofs at their digest-bound
limits. The selected outcome is maintenance recovery and the ordinary task handoff,
not all REC-3 cuts in every subsystem.

Current owned surface from child FINDING: worker_manager/maintenance.py;
custody.py for maintenance recovery; tools/job_manager.py for maintenance discovery/
reclaim; tools/single_worker.py for maintenance resume; corresponding
`tests/manager/test_maintenance.py`, `tests/job_manager/test_tool.py`,
`tests/tools/test_single_worker.py`, affected boundary/dependency declarations.
Other paths stay read-only unless a concrete needed extension is pinned. Shared
files transfer serially; no edits under W285806 or another active sibling claim.

## Current recovery integration map

- `tools/single_worker.py::_SingleWorker.start/_prepared`: resumed claimed attempt
  traverses preparation again before `reconcile_runtime`. It needs the accepted
  persisted preparation/host settlement reader, not a cached MaintenanceAnswer.
  Re-entry must recognize performed/settled/uncertain work before any second effect.
- `worker_manager/maintenance.py::prepare`: candidate facility owns launch and
  validates worker output. At read time, `standing_maintenance`,
  `maintenance_settlement`, `maintenance_orphan`, `_admitted`, `_settled`,
  `_orphaned` were being added. These are **unaccepted observed symbols**, not a
  required interface or proof that R1–R3 are fixed. READ-MANIFEST records moving bytes.
- `tools/job_manager.py::_reclaiming`: existing G1 serving-side overdue and uncertain
  passes use bounded rotation and per-resource refusal isolation. Preserve the
  existing expiry owner, clock and token arbitration. Extend discovery only as
  needed to account for the selected maintenance execution identity.
- `_observing_unresolved`: currently observes and reports unresolved tokens; it
  explicitly does not attach/return/dispatch. Do not reinterpret an observation as
  durable result settlement, absence proof or permission to restart preparation.
- `_serve`: composes `serve(... reclaim=operations.reclaim or _reclaiming(...))`.
  The selected maintenance recovery must be reachable from actual serving/resume,
  not merely from a helper the test calls directly. Preserve read-only `_status`
  and `_ReadOnly`; status must not become the trigger for expiry enforcement.
- Existing `tokens` and custody/OCI exact-container correlation are owners of their
  facts. No second lease, replacement clock, weak name-only destroy or automatic
  clearing of unrelated holds. Lost replies/engine outage are not non-execution.

## Finite actual-cut matrix

C labels identify proposed evidence rows, not runnable selectors. For every row:
assert the hook ran; retain pre-cut token/operation/claim/resource facts; close old
manager/store handles; reopen fresh handles/incarnation over the same disposable
stores; drive the real composed recovery path with the persistent recording fake
engine. Count create, admitted activation, governed effect, host settlement,
maintenance token return, task create/start and provider invitation independently.
A fake crash must not be caught by a branch that then finishes the very operation
claimed interrupted. Record the exact exception boundary and the reached state.

| ID / actual interruption | Durable facts that must survive | Expected resumed behavior and counts |
| --- | --- | --- |
| C1: launch intent committed, before create reply; engine may finish create late | Same resource/token generation, launch operation, intended execution and uncertainty; no assumed container absence | Reconcile the exact pending launch. Do not issue another effect-capable launch while unresolved. For a late exact container, follow accepted correlate/cleanup or safe continuation; unrelated/missing correlation stays held. Effect count0 before admission; no task start. |
| C2: create returns exact inert ID after expiry, or binding/admission refuses | Refused token cannot acquire late binding; exact returned orphan ID/operation retained | Exercise accepted facility R2 through composed path. Exact stop/remove/positive cessation or durable unknown; zero activation/effect/task start. Never force stale bind to obtain cleanup authority. Fresh-handle orphan evidence must survive lost cleanup reply. |
| C3: bound container, before activation admission | Token, launch and exact inert runtime known; no permission to execute yet | Revalidate current token/claim/resource. Continue same correlated execution only if accepted contract allows; otherwise reconcile/hold. Never create a second writer. At most one eventual admitted effect; zero task start until full handoff. |
| C4: activation admitted, start reply lost | Durable admitted-but-unsettled activation, possible actual effect | No duplicate start/provider dispatch merely because reply is missing. Observe exact container; uncertain remains held, no task. Positive start observation still does not manufacture successful preparation receipt. |
| C5: preparation effect and worker report exist, before host validation/settlement | Exact operation/token/runtime, result bytes and object identity; worker report is untrusted | Re-read and validate actual evidence, confirm exact cessation, commit authoritative outcome through accepted API. One effect total; malformed/foreign/unsupported-version report cannot settle. No rerun to regenerate missing evidence. |
| C6: exact cessation confirmed, before durable host settlement or token return | Old execution cessation and unresolved effects remain distinct | Reconcile only exact correlated evidence; settlement/replay cannot repeat effect. If absence evidence cannot be durably re-established, hold. No task until required outcome and ownership transitions are complete. |
| C7: host settlement committed, before return; return committed, before task admission | Exact versioned outcome and resource/checkpoint identity; expected token generation | Fresh-handle read returns same outcome. Conditional token return once, then revalidation and one task admission. No second maintenance create/effect. If returned-without-outcome is observed, refuse/hold rather than infer success. Split these two cut placements into distinct invocations. |
| C8: task admission boundary after maintenance return, resource/checkpoint changed or competitor wins | Original preparation receipt stays immutable; changed/current ownership visible | Refuse stale task start without undoing predecessor evidence or admitting overlap. Unrelated resource progresses. Later generation cannot be cleared by old cessation/settlement. |
| C9: active/uncertain maintenance expires; engine unavailable then available | Revocation/held state and exact runtime retained under existing token deadline owner | Actual serving pass attempts bounded stop outside transactions, reports failure honestly, retries supported reconciliation. Positive cessation plus effects settlement precede new use. Unknown surviving writer or absent correlated identity remains held; no task/provider effect on failed branch. |
| C10: completed preparation replay from new handle with same and changed operands | Immutable host outcome, original token/operation/runtime/input/object versions | Exact replay returns recorded result without new effect or extension; changed operands/ref/result/schema refuse. One host outcome for exact act, no foreign outcome adoption or false success. |

These are finite variants of existing child PLAN cuts. C2/C10 consume facility
corrections; do not reimplement them under a second API. “At most one” must not be
used to hide zero progress in the positive control: where inputs/engine and
accepted recovery support completion, show one actual effect and one subsequent
task start. Where uncertainty is deliberately unresolved, prove precise held
state and its reason rather than claiming recovery succeeded.

## Fixtures and instrumentation

Use the existing `SingleWorkerCase` production composition and its
`crash_and_restart` pattern as a starting point. Existing checkpoints
claimed/attempt/activation/workspace/boundary/input/manifest/launch/credential/runtime
are coarse: interpose on the actual committed maintenance operation and engine
boundary for C1–C7. A generic workspace checkpoint alone cannot prove the late
create or effect-before-settlement cut. Preserve a recorder across fresh object
construction; resetting its counters on reopen makes duplicate-effect tests vacuous.

The maintenance test `Engine` records create/start/wait/logs/stop/rm/inspect and
runs real selected preparation at simulated admitted activation. Extend its state
for multiple exact container identities and delayed replies; do not merely report
that a directory was created. The fixture owns daemon responses only. Production
host code must author token/settlement records, validate actual bytes and decide
cessation from the controlled adapter observation. Never insert receipt-shaped
rows or reviewer/owner acceptance in test setup to make the chain pass.

`tests/job_manager/test_tool.py` has existing `_reclaiming` expiry cases and
`TheRecoveryPassVisitsTheUNCERTAINTokensToo`. Reuse their real stores, controlled
clock and injected adapter patterns for serving discovery, exact attribution,
engine failure isolation and read-only status checks. They do not by name prove
maintenance is visited; assert the selected maintenance identity and actual call.
Use existing G1 bounded rotation rather than adding a new scheduler exercise.

## Integrated G2 acceptance checklist

| Evidence | Reuse / new requirement and limit |
| --- | --- |
| G1 exact tokens, instance guard, renewal/expiry arbitration, uncertain launch observation | Inherit accepted reviews culminating in W275776 review-2026-09-27T12-37-13Z. Compare changed path digests; rerun affected evidence only when changes justify it. Not proof of maintenance resource effects. |
| Facility R1/R2/R3 | Require actual latest W285463 independent acceptance: reciprocal admission, safe late-create handling, versioned durable host outcome/fresh-handle replay. Old40 passing checks and current unreviewed helper names do not discharge these findings. |
| Facility R4 live-test incident | Preserve predecessor incident account and known/unknown resource disposition. Not accepted deterministic evidence; no rerun or cleanup in either packet. This preparation does not adjudicate or repair the incident. |
| Connected H1–H9 | Consume W285464 exact candidate and actual command/trace, maintenance effect through real task caller, no host governed writes, no external I/O under DB lock, cessation/settlement before task grant. |
| C1–C10 | Record each concrete selector, actual hook, prior/resumed durable facts, engine/effect counts and expected positive/held result. Distinguish two C7 placements. No whole REC-3 or unrelated consumer coverage claim. |
| Integrity and isolation | Token/operation/runtime/result/object/checkpoint versions match; narrow mount vectors exclude credentials/DB/sibling resources; stale generation and malformed evidence never release current owner. |
| Final candidate | Compare predecessor manifests and enumerate every changed source/test path, preserved negative assertion and affected evidence. Unknowns and unrelated inventory/fixture baseline failures remain separately reported. |
| Delivery | Independent child review; refresh parent G2 current checkpoint under assigned ownership, record remaining removal/retention/review/context migrations and human checkpoint suggestion. Parent closure/adoption is not implied by preparation or child self-report. |

## Planned commands, not execution evidence

Under the child's claim, map C rows to real selectors after implementation.
The following existing modules are focused starting points, not a new claim that
current tests cover the proposed matrix. Revalidate their imports and authorize an
explicit disk-backed disposable root before execution; use fresh fixture identities.

```sh
cd /home/sl/src/baton/v12/python
```

```sh
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 timeout --signal=TERM --kill-after=5s 120s /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning -m unittest tests.manager.test_maintenance tests.tools.test_single_worker.TheProductionCompositionIsRestartSafe tests.job_manager.test_tool
```

Prefer exact newly mapped selectors for iterations. No wildcard/engine suite,
live provider, deployed-store operation, residue cleanup or Git mutation. These
commands were not run by tuner. Record actual per-run time and scope; cumulative
historical unknowns remain accounting, not renewed approval gates.
