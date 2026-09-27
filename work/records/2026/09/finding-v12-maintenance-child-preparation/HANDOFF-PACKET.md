# W285464 — provisional connected preparation-to-task packet

Prepared by baton.tuner under W285806 claim285818, 2026-09-27. Advisory input,
not predecessor acceptance, another gate, or permission to edit before claiming
W285464. Own child FINDING/PLAN controls scope. W285464 waits on W285463 by
edge285466. The handler need not wait for this packet if eligible first.

## Contract and first executable step

Use current v12/DESIGN.md DB-1–DB-7, TOK-1–TOK-12, HOST-1, ART-2/3 and section17.
After canonical predecessor acceptance, successful child claim and serial file
release, compare the accepted W285463 manifest/review with READ-MANIFEST.json.
Read its actual preparation operation and durable settlement schema before binding
any caller. Pin the one ordinary no-context/no-review preparation path, all of its
governed writes, and the exact operation/result/identity operands in the child's
FINDING/PLAN before editing. This is routine execution preparation within the
existing child, not a new approval round. Product-policy change alone needs owner.

The minimal successful path must establish:

`canonical task claim -> eligible scoped maintenance ownership -> governed
preparation effect -> exact maintenance cessation -> durable host settlement and
safe token return -> prepared-object/checkpoint revalidation -> task token
admission -> inert task create/bind/admit/start`.

These are semantic obligations, not invented wire/API names. A maintenance answer,
worker JSON, token returned bit or directory existence alone is not a preparation
receipt. A returned generation must never authorize a second effect. Maintenance
uses its own execution identity, derived from the selected lifecycle act, with no
second Work claim. No task/preparation launch on expired offer or lost claim race.

## Current caller and writer map

Paths are under `v12/python/`. Symbols are exact observed names; use the line and
file digests in READ-MANIFEST.json rather than assuming offsets survive correction.
The source reading is a bounded map of this path, not a whole-program audit.

| Caller / boundary | Observed behavior | Selected handoff treatment |
| --- | --- | --- |
| `tools/single_worker.py::_SingleWorker.start` | `_matches`, `_claim`, record_attempt, activate_assignment, then `_prepared`; checkpoints claimed/attempt/activation | Preserve canonical authority before preparation. Drive this path through real disposable Authority/Job/Control stores; do not bypass it with direct helper calls. |
| `_SingleWorker._prepared -> _mounted` | Ordinary roots allocated before boundary composition; stage.mount may substitute persistent/review roots | Select ordinary path first. Persistent review/context/restoration are explicitly outside this child; do not claim their migration. |
| `worker_manager/workspaces.py::assignment_workspace` | `_admitted_allocation`; `_own_directory` for attempt home/HOME_ENTRIES/result; group adoption; completion | Split owner validation/admission from governed mkdir/normalization effects. Preserve ordinary root capability/identity and refusal semantics; do not call this host writer first merely to make maintenance inputs exist. |
| `worker_manager/source_boundary.py::_compose_boundary` / `source_mountpoint` | Checks overlap/disk/capacity, captures source/workspace objects, establishes input source mountpoint | Move selected mountpoint creation into scoped preparation; host read-only validation stays outside DB transactions. No nominated-source tree walk/copy/hash. |
| `_prepared -> pin_boundary_identity` | Persist source/workspace object identities before input work | Pin/check the actual prepared objects, not a new reading compared only with itself after restart. Pure DB facts are host control duties. |
| `_input -> _published_task` | Creates exclusive task document, writes/fsyncs/fchmods; refusal unwind unlinks it | These governed writes and failure cleanup belong to maintenance. Preserve held task bytes, exclusive publication, refusal of partial/foreign input and same-input replay. |
| `_input -> workspaces.compose_input_root` | Validates protocol pair; writes input/assignment JSON; freezes root and home permissions | Prepare exact pair and workload document under maintenance. Input digest remains the pre-claim one; assignment carries minted generation. Unknown/partial material is held/refused, never silently repaired. |
| `retain_manifest` | Records input-manifest control fact after composition | Remains host owner act; must consume actual validated prepared delivery. It is not permission to hide resource writes as metadata. |
| `_attempt_scratch` | Adopts scratch provisioned in HOME_ENTRIES; lstat/type checks, no creation here | Provision scratch under selected maintenance, then read-only revalidation outside transactions. Retain disk-backed and no-symlink contract. |
| `_launch_document` / `_credential` | Separate launch/exchange and exact credential delivery; `_unwound` has cleanup paths | Inventory their actual storage classification at implementation. Only genuinely separate control metadata stays host-side. No credentials/control DB in maintenance mount. If a governed writer outside allocated paths is required, pin that concrete path need before editing; do not expand into credential redesign or claim it exempt by its name. |
| `adopt_source_boundary(... pinned=boundary_identity_of(...))` | Final source/workspace identity check before adapter/start | Preserve after maintenance return, compare prepared receipt/checkpoint and durable pin. Replaced object/source refuses before task engine create. |
| `request_runtime_start(... govern=tokens.workspace_governance(control=..., mounted=...))` | Existing G1 task resource acquisition, inert create/bind/admit/start | Consume the same conflict domain or proved atomic mapping. Preserve mounted-root containment and G1 start/reconciliation rather than adding another token system. |
| nonfresh `_prepared -> reconcile_runtime` | Reconciles existing runtime rather than starting a second one | Preparation receipt replay must fit this re-entry. No replay may allocate or prepare anew merely because a Python object was lost. Child C owns the additional restart matrix. |

### Concrete facility limitation to resolve at the serial handoff

The reviewed facility candidate's only verb was `establish-result-root`. Its
`prepare` derives an **existing** workspace via custody._derived_root and governs
a child result directory. That is useful facility proof, not complete ordinary
attempt allocation/input staging. The child must either consume an accepted
operation that now covers those effects or extend the scoped preparation operation
within its owned maintenance/workspaces/source-boundary paths. Define the stable
pre-allocation conflict identity before the task workspace exists and prove its
mapping to the task's eventual object identity. Never bootstrap with an untracked
host mkdir or a global token that serializes unrelated Jobs. Narrow registered
storage mounts must exclude siblings, credentials and authority/control databases.
No new product policy is chosen by this packet.

## Minimal serial path ownership

The existing child author owns `tools/single_worker.py`,
`worker_manager/workspaces.py`, `worker_manager/maintenance.py`, custody.py only
selected integration, and source_boundary.py only selected host staging migration.
Focused test paths: `tests/tools/test_single_worker.py`,
`tests/manager/test_maintenance.py`, affected boundary_inventory/dependencies
registries. Do not rewrite tokens.py, attempts.py, launch.py, context or stage
composition merely because referenced here; report and pin a concrete extra-path
need before editing. G1 is inherited, G2 facility files transfer only at safe
predecessor release. Reviewer owns reviews/FINDING/PLAN; author owns PROGRESS.

## Acceptance cases to implement, not claimed selectors

H labels are packet case IDs. They are not existing Python test names or passes.
Use `SingleWorkerCase` and `TheProductionCompositionIsRestartSafe` in
`tests/tools/test_single_worker.py`: real disposable stores, normal submit/claim/
start flow, injected engine. Extend the engine fixture to distinguish maintenance
and task containers and perform real preparation bytes only when maintenance
activation is admitted. Reuse `MaintenanceCase`/recording `Engine` in
`tests/manager/test_maintenance.py` where suitable; fixture identity/report shape
must follow the accepted facility. Do not mint host settlement or quiescence rows
in the fixture. Record actual production boundaries and assert each hook fired.

| ID | Reached schedule | Required observations |
| --- | --- | --- |
| H1 | Ordinary claimed task through real preparation and task activation | Trace claim, maintenance reserve/create/bind/admit/effect, exact stop/confirmation, host receipt/return, prepared revalidation, task acquisition/create/bind/admit/start. Exactly one effect and one task start; distinct runtime identities, correct input/task bytes and frozen modes. |
| H2 | Expired offer, lost claim race, stale assignment before maintenance | No governed mutation, maintenance create, task create or provider dispatch. A legitimate negative must reach the authority gate, not fail earlier on malformed fixture. |
| H3 | Maintenance paused while competing task/custody/removal admission attempts; reverse order too | One shared conflicting resource owner wins, loser has no effect. Use real second store connection and actual owner APIs; unrelated resource can progress. Reuse accepted R1 facility proof but prove caller uses it. |
| H4 | Swap prepared workspace/source or change checkpoint after maintenance settlement, before task acquisition | Compare durable expected identity; no task create/start, original prepared evidence retained, no new self-consistent repin accepting the replacement. |
| H5 | Exact same preparation from fresh store handle, then changed operation/input identity | Same committed host receipt and no second maintenance effect/launch; changed operands refuse. Token cessation alone cannot stand in for settled preparation. |
| H6 | Expiry/unknown maintenance ending or outstanding activation while task path continues | No task admission or conflicting token; exact unresolved runtime/operation remains visible. Stop request, done JSON and string truthiness are insufficient. |
| H7 | Real creation/publication/freeze and refusal-cleanup paths under host mutation traps | All selected governed mkdir/write/chmod/unlink effects occur only in simulated maintenance executor; trap covers home/inputs/workspace/result/scratch. Assert positive trap instrumentation so an unused trap cannot pass. Control-store metadata explicitly separated. |
| H8 | Each affected external engine/filesystem boundary, including refusal/replay/unwind | No DB transaction active; while external effect is paused, a second connection completes unrelated DB work. No cross-store callback inside retained transaction. |
| H9 | Actual created maintenance/task mount vectors | Maintenance exact scope, no credential/DB/sibling mounts; task input/source RO, output/scratch exact; unchanged source nomination and containment. Compare vectors, not fixture declarations alone. |

## Planned focused commands and proof limits

NOT RUN here. After adding H cases under the child's own claim, map each H label
to actual test selectors in its PLAN. Existing baseline module/class names below
are real; running them before adding connected cases is not H1–H9 acceptance.
Select authorized disk-backed disposable scratch explicitly before running; never
reuse a live instance or the facility incident's roots.

```sh
cd /home/sl/src/baton/v12/python
```

```sh
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 timeout --signal=TERM --kill-after=5s 120s /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning -m unittest tests.tools.test_single_worker.TheProductionCompositionIsRestartSafe tests.manager.test_maintenance
```

Revalidate command/module imports and timeout against accepted candidate. No
`test_custody_engine`, wildcard discovery, live Docker/provider or deployment test.
Record actual command, elapsed time, candidate hashes, evidence trace and simulation
limits. Stop with independently reviewable connected handoff evidence and exact
residuals; Child C supplies additional restart/integrated G2 proof. This child does
not certify retained-review/context/removal consumers or parallel adoption.
