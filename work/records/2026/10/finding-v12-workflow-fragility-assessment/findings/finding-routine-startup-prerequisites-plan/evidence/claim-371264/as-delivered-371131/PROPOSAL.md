# Routine create while serving, and installer prerequisites — W371075

**Planning only.** No product source, test or specification byte is changed by
this document, nothing is installed, no instance is started and no engine,
provider or deployment is touched. Every proposed contract below is an
example for owner decision, not a selected contract.

Prepared against `f36bcd75ed22430355efe1b274b8f236cb591f6b`.

| anchor read for this plan | sha256 |
| --- | --- |
| `v12/python/tools/job_manager.py` | `9f9008fd68a3f00ed41516c0127655cd24a5518df15294f22282c0f0dc66018f` |
| `v12/python/tools/bootstrap.py` | `3bc26bb0a71cf980ae9f37e813d52fd125a0dbed30d0a43e66e36dd0bcf0bc02` |
| `v12/python/tools/instance.py` | `ee59b95ca4f4a9753058ad48d4215f3a18be395290e8924b762311392dbad433` |
| `v12/python/tools/fresh_attempt_ports.py` | `c8a41e078769eb105440ed8fb71e6d66bf484cf292cd344cabefa8dc2c75a2a5` |
| `v12/python/src/baton_v12/job_manager/creation.py` | `b707227ebb794158497b33228089df91db7b6aa69c22f71134fa62a2c96a42ee` |
| `v12/python/src/baton_v12/worker_manager/workspaces.py` | `e769da4557d0405edee8e17d4333bebd18bc713c07781250d45f10d0e8587dc4` |
| `v12/DESIGN.md` | `500fa602410be8fe125be56140685c696ebd653f68abbc87a4b0d4e512bc0751` |

---

## 1. The four observed failures, and which kind each one is

All four were reached by me as the operator in W370268 on a real fresh
installation. They are **observed**, with the refusal text retained in that
dossier's `evidence/claim-370272`. What follows separates them, which is the
distinction the FINDING asks for.

| # | observed refusal | kind |
| --- | --- | --- |
| 1 | `create` before `start`: *"a read-only manager requires an existing regular store"* | **code gap under existing DESIGN** (OBS-0a, DB-6) |
| 2 | `start` on a fresh install: *"the configured workspace store … is not a directory this manager can see"* | **code gap under existing DESIGN** (OBS-0a) |
| 3 | `manager status --observe` without `BATON_V12_STAGE_EXECUTION_CONFIG` | **code gap under existing DESIGN** (OBS-0a) |
| 4 | `create` while serving: *"another manager is already active for workspace … stop the active one first"* | **NOT a gap — a design decision is required** (HOST-8 vs DB-3/DB-5) |

The observed `start → stop → create → start` sequence is **evidence of the
gap and is not proposed as acceptance**, exactly as the parent assessment
says.

### Why 1–3 are code gaps rather than new semantics

OBS-0a is already normative and already says so, in its own words:

> The launcher MUST create and validate required output directories and other
> launch prerequisites before consuming a run selection. … Further manual
> reprovisioning requirements are product defects, not normal operator steps.

* **(2)** `tools/instance.py:layout` has **no** `workspaces`, `launch` or
  `credentials` member, and `bootstrap` creates only `stores`, `repository`,
  `logs` and `state`. The composed deployment nevertheless configures
  `workspace_storage`, `launch_home` and `credential_home` under
  `state/`, and `workspaces.check_workspace_storage` refuses a place it
  cannot see. So the installer does not create what the configuration it
  writes will require. The pilot packet published this as an operator step
  (*"Selection 2b — the workspace storage prerequisite"*), which is precisely
  what OBS-0a calls a product defect.
* **(1)** `job_manager._create` opens the control store with
  `ControlStore.open_readonly`; the only writable open in the module is
  `_serve` (one site, line ~1168). `_submit` and `_status` are read-only too.
  So on a fresh install the control store exists only once something has
  served, and nothing in the install path creates it. DB-6 forbids guessing
  or implicitly reopening a store to complete an operation, which is right —
  so the creation belongs to the installer, not to a fallback inside `create`.
* **(3)** `single_worker.observing_factory` reads
  `BATON_V12_STAGE_EXECUTION_CONFIG` from the environment and refuses when it
  is unset. A packaged `manager status --observe` therefore cannot be run
  without an operator-authored export, which OBS-0a also names.

### Why 4 is a decision and not a defect

`HOST-8` is explicit: only one Host Worker Manager may be active for a managed
workspace/DB, a second MUST refuse before dispatching work, MUST NOT stand by
and MUST NOT take over, and the guard MUST be an exclusive non-blocking OS
file lock.

And `creation.create_template_job` takes that same guard **deliberately**, at
`creation.py:225`:

```python
with ownership.held() as owner, ownership.invocation(operands["job_id"]):
```

with its own stated reason: the derivation reads the instance configuration
and *"the one writer that could change it is a manager whose guard this now
holds — so there is nothing composed outside the guard to go stale, and no
comparison between two readings for anybody to get wrong."* That is DB-3 and
DB-5 being satisfied, not sloppiness.

`workspaces.borrow_manager_instance` already supports *"ONE user, among any
number of them"* — but the count and cache (`_HELD_GUARDS`) are
**process-global**, so borrowing composes only **within one process**. A
separate `create` process must acquire the `flock` itself, and the serving
process holds it exclusively.

**So the conflict is structural, and neither side is wrong.** Admission needs
the exclusion for the length of its own work; serving holds it for its
lifetime; and cross-process borrowing of an exclusivity guard would be the
standby/takeover HOST-8 forbids. No lock can be relaxed without losing the
atomicity DB-3/DB-5 require. The decision is *where the admission runs*.

---

## 2. Proposed supported trace: install → create while serving → observe

```
  INSTALL (once, by the installer — OBS-0a)
    bootstrap --inputs <mint>                      mint identity, no workers
    bootstrap --inputs <phase2> --destination … --distro … --repository-source …
      ├── creates stores/, repository/, logs/, state/          (today)
      ├── creates and validates workspace_storage, launch_home,
      │   credential_home from the configuration it just wrote  (PROPOSED, gap 2)
      ├── initialises the control store at its current schema   (PROPOSED, gap 1)
      └── records the prerequisite inventory in instance.json   (PROPOSED)

  START
    <distro>/baton-v12-stack start --instance <dest>/instance.json
      └── the serving manager takes the instance guard for its lifetime (HOST-8)

  CREATE, on the running deployment, no supervisor cycling
    <distro>/baton-v12-stack manager … create --instance … (unchanged argv)
      └── records a durable creation INTENT, idempotent under the Job's
          operation id                                         (PROPOSED, gap 4)
      └── the SERVING manager performs the admission inside the guard it
          already holds, on its next reconcile                 (PROPOSED)

  OBSERVE, standalone and read-only
    <distro>/baton-v12-stack manager … status --observe … --instance <dest>
      └── the instance operand supplies what the env var supplies today
                                                               (PROPOSED, gap 3)
```

## 3. Owner responsibilities, as they stand and as proposed

| fact | owning API today | proposed change |
| --- | --- | --- |
| instance paths | `tools/instance.py:layout` | **add** `workspaces`, `launch`, `credentials` so one function answers every configured path |
| directory creation | `bootstrap` (`stores`, `repository`, `logs`, `state`) | **extend** to every layout member the configuration it writes will require, created and validated before the install reports success |
| control-store existence | implicit, first `ControlStore.open` in `_serve` | **explicit** idempotent initialisation at install; `_create`/`_status` stay `open_readonly` |
| store schema version | `ControlStore.open` / migrations | unchanged; install calls the same owner API, so there is **one** creator and one migrator |
| the active-manager guard | `workspaces.hold_manager_instance` (lifetime) | unchanged, and deliberately so |
| admission exclusion | `fresh_attempt_ports.held` → `borrow_manager_instance` | unchanged **in-process**; the admission moves to where the guard already is |
| per-admission exclusion | `fresh_attempt_ports.invocation` (per-Job `flock`) | unchanged |
| replay / idempotence | `store.replay` + `create_operation_id` (DB-7) | unchanged, and it is what makes the intent safe |
| observation configuration | `BATON_V12_STAGE_EXECUTION_CONFIG` | **add** an `--instance` operand; keep the env var as a fallback |

### Locking order, proposed and unchanged

1. the serving manager takes the **instance guard** at startup and keeps it;
2. an admission performed inside that manager **borrows** it — in-process,
   counted, released by the last borrower, never releasing a guard an
   external owner holds;
3. the admission then takes the **per-Job invocation** `flock`;
4. no DB transaction is held across either guard or across external I/O,
   which HOST-8 requires in terms;
5. on a **stopped** deployment `create` acquires the instance guard itself
   exactly as today — so the direct path is not removed, it is the fallback.

---

## 4. The one decision for the owner, with options

**How does an admission run while a manager is serving?**

### Option A — durable creation intent, performed by the serving manager *(recommended)*

`create` writes an intent row bound to the Job's existing operation id, then
the serving manager performs the *same* `create_template_job` on its next
reconcile, inside the guard it already holds. The operator command either
returns the intent receipt or waits for the admission to settle and prints
the same answer it prints today.

* **DESIGN fit:** DB-4 prescribes exactly this shape — *"compose them through
  durable intents, idempotent operations and explicit incomplete states"*.
  DB-7's operation identity already makes a repeated request replay and a
  changed request refuse. HOST-8 is untouched: one manager, no standby, no
  takeover. DB-3/DB-5 atomicity is preserved because the derivation still
  happens once, inside the guard.
* **Cost:** a new durable intent relation and one reconcile step; the
  operator command becomes asynchronous-with-wait, so its exit timing
  changes. The admission code itself does not move.
* **Open sub-decision for the owner:** whether `create` **waits** by default
  (same observable behaviour as today, slower) or returns the intent and a
  second command reads the outcome. I recommend waiting by default with an
  explicit non-waiting flag, so no existing caller changes meaning.

### Option B — separate "active manager" from "configuration writer"

Admission takes a narrower *configuration* guard that the manager also takes
around its own configuration writes, leaving the instance guard purely for
HOST-8 exclusivity.

* **DESIGN fit:** needs **new semantics** — HOST-8 currently describes one
  guard for the instance, and a second cross-process guard with its own
  ordering is a new contract that must be specified before it is built.
* **Cost:** two guards to order correctly, and a lock-ordering mistake is a
  deadlock rather than a refusal. Higher risk than A for the same outcome.

### Option C — the serving manager yields the guard for admission windows

**Recommended against, explicitly.** A lifetime hold that can be yielded is
not a lifetime hold, and the window it opens is exactly the second-manager
window HOST-8 exists to refuse.

### Option D — keep the stop/create/start cycle

**Recommended against**, and the FINDING already rules it out as acceptance.
It also violates OBS-0a's prohibition on operator-authored routine
procedures.

---

## 5. Compatibility

* **Existing installs** keep working: the installer additions are
  create-and-validate-if-absent, and an already-provisioned instance presents
  them as present. No `chmod`, no recursive normalization, no repair of a
  path the installer did not create — an occupied path of the wrong type
  **refuses** with the name, as `_new_directory` already does elsewhere.
* **Existing argv** is unchanged for `create` under Option A. The
  `--instance` addition to `status --observe` is optional; the env var keeps
  working.
* **Stopped-deployment `create`** keeps the direct path, so packaged
  single-shot use is unaffected.
* **Store schema** is created by the same owner API that migrates it, so
  install-time creation cannot produce a version the runtime would not.

## 6. Finite implementation slices

| slice | scope | independently acceptable? |
| --- | --- | --- |
| **S1** | `instance.layout` gains the three missing members; `bootstrap` creates and validates every configured path; occupied/wrong-type refuses | yes — fixes gap 2 alone |
| **S2** | install-time idempotent control-store initialisation through the owning API; `_create` unchanged | yes — fixes gap 1 alone |
| **S3** | `status --observe --instance`, env var retained | yes — fixes gap 3 alone |
| **S4** | the Option A intent relation, the reconcile step and the waiting `create` | needs the owner's choice first |

S1–S3 are small, independently reviewable and need no new semantics. **They
should land before S4**, because together they make a fresh install reach its
first `start` with no operator-authored step — which is most of what OBS-0a
asks for — and they do not depend on the decision.

## 7. Proposed acceptance matrix

Deterministic boundaries, no engine, provider or live run.

| behaviour | proposed assertion |
| --- | --- |
| fresh install completes prerequisites | every configured path exists and validates **before** the install reports success; the first `start` needs no operator step |
| first create, no cycling | on a freshly installed, **never-started** instance, `create` succeeds without a start/stop |
| create on a running manager | with the manager serving, `create` succeeds and the Job is admitted exactly once |
| concurrent identical intent | two identical `create`s replay to one admission (DB-7) |
| concurrent different intent | the second refuses as a changed request, naming the recorded digest |
| conflicting ownership | a second `start` still refuses under HOST-8, unchanged |
| crash and reopen | an interrupted admission resumes or refuses honestly; no partial reservation survives |
| occupied prerequisite path | a wrong-type or foreign-owned path refuses by name; nothing is chmodded or normalised |
| standalone observation | `status --observe --instance` works with no env var and mutates no durable byte |
| packaged commands | every assertion above through the installed bundle's argv |
| OBS-0a interval | the install-to-first-start path measured **with its endpoints and clock source named**, and reported as unknown where no output records an endpoint |

**The OBS-0a interval needs its endpoints stated or it cannot be measured.**
W370268 established that the status projection's `observed_at` is *query
time*, that worker visibility distinguishes bytes observed from progress, and
that nothing records when an operator's command was received. So an interval
claim needs either an operator-side timestamp outside the product or a new
recorded endpoint — and that is an owner decision, not something to infer.

## 8. Overlap and sequencing

* **W325695** owns `claude_agent`/verifier-root source and is active; this
  plan touches none of it.
* **W370555**'s accepted correction touches `tools/single_worker.py`
  (`given_for_job`, `_Observation`). S3 would touch `observing_factory` in the
  same file — **coordinate**, and sequence after that candidate's accepted
  checkpoint.
* **W370688 / W333486** deliverables are reused, not re-derived.
* **S1/S2** touch `tools/bootstrap.py` and `tools/instance.py`, which no
  current claim holds.
* **S4** touches `job_manager`, `creation` and `stage_execution`'s reconcile —
  the largest overlap surface, and another reason to sequence it last.

## 9. What this plan does not establish

Observed facts are the four refusals and the source anchors above. **Inferred:**
that S1–S3 are sufficient to reach a first `start` with no operator step — I
did not build or run them. **Proposed:** every contract in §2–§6. **Open:**
the §4 decision and its waiting sub-decision, the OBS-0a endpoints, and
whether the intent relation belongs to the Job store or the control store
(DB-4 says one owner per fact; I recommend the Job store, because the Job's
creation is already its fact, but the owner should confirm).

No inert probe was needed: the four refusals are already retained with their
exact text in W370268's evidence, and re-reaching them would have required
starting the retained instance, which this planning claim forbids.
