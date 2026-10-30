# Routine create while serving, and installer prerequisites — W371075

**Revision 2**, answering `review-2026-10-28T03-22-00Z.md` (R1–R4). The bytes
reviewed as revision 1 are preserved unchanged at
`evidence/claim-371264/as-delivered-371131/`.

**Planning only.** No product source, test or specification byte is changed,
nothing is installed, no instance is started and no engine, provider or
deployment is touched. Every contract below is a **proposal for owner
decision**, not a selected contract.

Prepared against `f36bcd75ed22430355efe1b274b8f236cb591f6b`, which **already
includes W370555** — revision 1 wrongly treated that correction's checkpoint
as a future gate, and R4 is right.

| anchor | sha256 |
| --- | --- |
| `v12/python/tools/job_manager.py` | `9f9008fd68a3f00ed41516c0127655cd24a5518df15294f22282c0f0dc66018f` |
| `v12/python/tools/bootstrap.py` | `3bc26bb0a71cf980ae9f37e813d52fd125a0dbed30d0a43e66e36dd0bcf0bc02` |
| `v12/python/tools/instance.py` | `ee59b95ca4f4a9753058ad48d4215f3a18be395290e8924b762311392dbad433` |
| `v12/python/tools/stack.py` | *read for `instance_settings`* |
| `v12/python/tools/fresh_attempt_ports.py` | `c8a41e078769eb105440ed8fb71e6d66bf484cf292cd344cabefa8dc2c75a2a5` |
| `v12/python/src/baton_v12/job_manager/creation.py` | `b707227ebb794158497b33228089df91db7b6aa69c22f71134fa62a2c96a42ee` |
| `v12/python/src/baton_v12/worker_manager/store.py` | *read for `ControlStore.open`* |
| `v12/python/src/baton_v12/worker_manager/workspaces.py` | `e769da4557d0405edee8e17d4333bebd18bc713c07781250d45f10d0e8587dc4` |
| `v12/DESIGN.md` **as read now** | `571738130e7cfedd33966c1e920488b629e6b877eef16b1a3c61ccb7ea7f2796` |
| `v12/DESIGN.md` at `f36bcd75`, which revision 1 recorded | `500fa602410be8fe125be56140685c696ebd653f68abbc87a4b0d4e512bc0751` |

**`DESIGN.md` changed during this claim.** Re-hashing it found +16 lines the
base does not have: a new owner clause, **Development role-contract admission
(owner 2026-10-28)**, which **selects sibling W371072's admission plan as
normative**. Revision 1's hash is not stale bookkeeping — the clause it
predates governs §2. §2.6 and §7 are written against the clause as selected,
not against a sibling proposal to be negotiated with.

---

## 1. The four observed failures, and which kind each is

Reached by me as the operator in W370268; refusal text retained in that
dossier's `evidence/claim-370272`.

| # | observed refusal | kind |
| --- | --- | --- |
| 1 | `create` before `start`: *"a read-only manager requires an existing regular store"* | code gap (OBS-0a, DB-6) |
| 2 | `start`: *"the configured workspace store … is not a directory this manager can see"* | code gap (OBS-0a) |
| 3 | `manager status --observe` without `BATON_V12_STAGE_EXECUTION_CONFIG` | code gap (OBS-0a) — and smaller than revision 1 implied; see §5 |
| 4 | `create` while serving: *"another manager is already active … stop the active one first"* | **design decision required** (HOST-8 vs DB-3/DB-5) |

`job_manager._create`/`_submit`/`_status` all use `ControlStore.open_readonly`;
the one writable `ControlStore.open` is in `_serve`. `instance.layout` has no
`workspaces`/`launch`/`credentials` member and `bootstrap` creates only
`stores`, `repository`, `logs`, `state`. OBS-0a already makes 1–3 defects:
*"The launcher MUST create and validate required output directories and other
launch prerequisites"*, and *"Further manual reprovisioning requirements are
product defects, not normal operator steps."*

(4) is not a defect. `HOST-8` mandates one active manager behind an exclusive
non-blocking file lock, and `creation.create_template_job` takes that guard
**deliberately** (`creation.py:225`) so the derivation cannot go stale — DB-3
and DB-5 satisfied. `workspaces.borrow_manager_instance` is a **counted**
in-process hold, so a separate `create` process must take the `flock` the
serving process holds. The question is **where the admission runs**.

---

## 2. R1 — the proposed durable admission contract

### 2.1 Owner, and why the Job store

DB-4: one owning store per fact. The Job's creation is already the Job store's
fact — `creation` owns `template_jobs` and `fresh_attempts` there and
`create_operation_id`/`job_signature` already live in its operation journal.
So the intent is a **Job-store relation**, and no second store is opened under
any transaction.

### 2.2 Proposed relation `creation_intents`

| column | meaning |
| --- | --- |
| `job_id` | primary key; one intent per Job identity |
| `operation_id` | `create_operation_id(job_id)` — **the same** id the direct path uses |
| `request_digest` | `job_signature(CREATE_KIND, operands)` — the existing signature |
| `operands` | the canonical operands blob, exactly as submitted |
| `received_at` | when the operator's command was received (see §4) |
| `state` | `pending` \| `performing` \| `completed` \| `refused` \| `retired` |
| `holder` | the incarnation that moved it to `performing`; null otherwise |
| `configuration_revision` | the revision the derivation was performed against |
| `outcome` | the recorded answer or the recorded refusal |
| `settled_at` | when it reached a terminal state |

### 2.3 Transitions, and who may make each

```
            create (direct, deployment stopped)
   ─────────────────────────────────────────────────────────┐
                                                            ▼
  create (queued) ──► pending ──► performing ──► completed / refused
                         │            │
                         │            └─(holder dies)─► pending  [flock released]
                         └──────────── retired  (explicit owner act only)
```

* **`pending`** is written by `create` **only after** `store.replay` finds no
  completed creation. The existing completed-request replay stays **before**
  derivation, exactly as `creation.py` already does it — a second identical
  request replays, a changed one collides as `_changed`.
* **`pending → performing`** is a **conditional** transition on
  `(job_id, state='pending', request_digest=…)`, and only the holder of the
  per-Job `invocation` flock may attempt it. A **retired** row cannot
  transition, which is the DB-7 retirement fence: a retired intent can never
  later execute.
* **`performing → completed/refused`** records the outcome in the same
  operation the journal already keys.
* **holder death** is handled by the kernel: `fresh_attempt_ports.invocation`
  drops its `flock` when the process dies, so the row is reclaimable. The
  reclaim is a conditional move back to `pending` by the next performer that
  acquires the flock — **not** a lease with a clock, which is the inferred
  cessation that module already refuses.

### 2.4 How the direct and queued paths arbitrate without duplicate effects

**The flock arbitrates, not the row.** Both paths call the same
`create_template_job` and therefore both take
`ownership.invocation(job_id)` — a per-Job `flock` that *"contends whether
they are in two processes or two threads of one"*. So:

1. both paths replay first; a completed creation returns its recorded answer;
2. both then contend for the per-Job flock; exactly one proceeds;
3. the loser is refused as a concurrent invocation, and its caller replays —
   reaching the winner's answer.

The intent row therefore never duplicates an effect; it only records that a
request exists so the serving manager can find it. **Revision 1 said "no
partial reservation survives", which was wrong** — DB-5 explicitly permits a
safe held/reconciling state, and §2.5 maps the ones that do survive.

### 2.5 Crash recovery, mapped onto the cuts that exist

`creation._owned` has three cuts, and the proposal does not move them:

| crash point | what survives | recovery |
| --- | --- | --- |
| before **CUT A** | nothing in any owner; intent `pending` or `performing` | re-enter under the same operation id; derivation repeats |
| after **CUT A** (identity, submission name, resolution digest reserved) | a reservation — a **safe held state** under DB-5 | the same operands re-enter; CUT A replays by operation id |
| after **CUT B** (Work authorization, then deployment binding — both already idempotent) | authorization and/or binding | re-enter; both idempotent by their own rule |
| after **CUT C** (`submission.submit`, then the completion that closes the intent) | a complete creation | `store.replay` returns it; the intent is moved to `completed` from the recorded outcome |
| after an effect but **before** the intent was updated | the effect, and a stale `performing` row | the row is reconciled **from the journal**, never from a second account — the operation id is the one fact |

The intent is a **pointer to an operation**, not a second record of it. That
is what keeps DB-4 satisfied.

### 2.6 Serialization inside the serving process, and the configuration fence

The review is right that the OS guard does not serialise multiple admissions
**inside** its owning process: `borrow_manager_instance` is counted, so N
in-process borrowers coexist by design. Two proposals, and they are separable:

* **Same Job** — already serialised by the per-Job `invocation` flock, which
  contends across threads of one process as well as across processes.
* **Different Jobs** — the serving manager performs queued admissions
  **serially, one per reconcile step**. That is the simplest correct answer
  and needs no new lock; it also bounds how much one tick can do.
* **Against serving/dispatch** — the derivation records a
  `configuration_revision` on the created Job, and dispatch compares it before
  offer/allocation and again before external launch. This is the
  **admitted configuration revision/fence** sibling W371072 asks for in terms:
  *"If startup ownership is changed by W371075, its admitted configuration
  revision/fence must replace the current OS-guard assumption explicitly; do
  not rely on rereading mutable files."* It does — the fence replaces the
  assumption that holding the guard means nothing can have changed.

### 2.6a Conformance with the selected admission clause

The owner clause of 2026-10-28 is **normative**, so these are conformance
obligations rather than proposals:

* *"Before fresh creation effects, the Job manager MUST validate that
  contract against trusted, versioned capabilities of the installed role
  adapters and the actual composed inputs."* Recording a `creation_intents`
  row **is** a Job-store effect. So the order is: replay → **contract
  validation on closed data** → record the intent → take the flock → CUT A.
  Revision 1 had no such step; §2.3 is read with this ordering.
* *"The selected contract and capabilities MUST be retained with the Job's
  resolved provenance and checked against the selected execution before
  dispatch."* The `configuration_revision` fence is the mechanism, and it
  must be compared **together with** the retained contract and capability
  digests — not instead of them.
* *"...without provider imports into the generic host or external callbacks
  inside database transactions."* So: no template- or deployment-supplied
  callback runs inside the intent transition or any cut, the validator reads
  **copied closed data** only, and the queued performer opens no second store
  under a transaction. The serial one-per-tick reconcile step satisfies this
  without a nested lock.
* *"Unsupported or changed contracts MUST refuse without silently
  reinterpreting admitted Jobs."* A queued intent whose contract no longer
  validates at performance time **refuses and records the refusal** — it does
  not re-derive against the new contract. This is why the intent stores the
  canonical operands rather than a reference to mutable configuration.
* *"Shared optional declarations MUST NOT waive role-required result
  validation."* Noted as the reason `SHARED_DECLARED`'s union of
  `required: False` members cannot be read as satisfying a role's required
  outputs — the exact fault W370268 observed.

### 2.7 Waiting, timeout and the operator's answer

* `create` **waits by default** and prints the answer it prints today, so no
  existing caller changes meaning.
* `--no-wait` prints the intent receipt — `job_id`, `operation_id`,
  `request_digest`, `state`.
* **Timeout while still pending** exits non-zero, names the intent, and
  **leaves the intent pending**. It is not retired, because a timed-out wait
  is a statement about the waiter and not about the request. Re-running the
  identical command replays or waits again; a changed command collides.
* **Manager absent with an intent pending**: the intent stays pending and the
  waiter says so. Starting the manager performs it.
* **Stopped deployment**: `create` takes the instance guard itself and
  performs directly, exactly as today.

### 2.8 Proposed API and specification deltas, kept apart from what exists

**Exists already** (no change proposed): `create_operation_id`,
`job_signature`, `store.replay`, `_changed`, the three cuts,
`ownership.held`, `ownership.invocation`, `borrow_manager_instance`,
`hold_manager_instance`, `ControlStore.open`/`open_readonly`,
`instance.settings`, `stack.instance_settings`.

**Proposed new** — each needs owner acceptance:

| delta | kind |
| --- | --- |
| `creation_intents` relation and its five states | new schema |
| a public owner API to record, claim, settle and retire an intent | new API |
| a reconcile step that performs at most one queued admission per tick | new behaviour |
| `configuration_revision` recorded at admission and compared before offer and before launch | new semantics — **coordinate with W371072** |
| `create --wait/--no-wait` | new operand, default preserves today's behaviour |
| `status --observe --instance` | new operand (§5) |
| installer prerequisite creation and an existing-instance **validate** verb (§5) | new behaviour |

---

## 3. R2 — the actual OBS-0 interval, restored

**Revision 1 substituted install-to-first-start and dropped the bound. That
was wrong.** OBS-0 reads: *"Routine preparation and startup MUST take at most
**60 seconds** from receiving the task description and selected input files to
the assigned agent starting substantive task work"*, measuring *"the whole
routine path, including input handling, configuration, validation and
launch"*, and requiring endpoints and environment assumptions to be reported.
One-time installation is OBS-0a and is **separate**.

### Proposed instrumentation, which makes the interval measurable

W370268 established that nothing records when an operator's command was
received, and that `observed_at` is *query time*. So:

* **start endpoint** — `received_at` on the creation intent (§2.2). The
  operator's command receipt becomes a product fact instead of an operator
  stopwatch.
* **end endpoint** — the worker's existing `state-work.json`, whose
  `operation: work` state is published when the agent begins substantive work.
* **the interval** is the difference, measured across admission, serving,
  allocation, launch and worker start — the whole routine path.
* **assumptions to report**: one host, a warm image present locally, no pull,
  the deterministic provider, and the clock source for each endpoint.

### Deterministic composed proof, and its limit

A composed proof with a **simulated provider** can measure everything up to
the worker publishing `work`, because the provider turn is after that
endpoint. **The limit, stated:** a simulated provider does not establish real
image pull, real container start or real authentication latency. The existing
selected live evidence from W370268 may be reused for those; **no live run is
selected here**.

### OBS-1, corrected

Revision 1 asserted "mutates no durable byte". The owner clarification of
2026-10-18 supersedes that reading: status *"opens existing databases through
validated SQLite read-only connections and does not change application data or
schema, initialize or migrate stores, or fall back to writable access"*, and
*"SQLite's normal sidecar and locking behavior is acceptable."*
`ControlStore.open_readonly`'s own docstring says the same. So the acceptance
assertion becomes: **no application-data or schema mutation, no initialisation
or migration, no reconciliation, no writable fallback** — sidecars and locks
excepted.

That also explains the `*.sqlite3-shm/-wal` test failure I reported as
pre-existing in W370555: it asserts the superseded absolute.

---

## 4. R3 — installer, reopen and observation, concretely

### 4.1 No upgrade is invented

`bootstrap.install` refuses an occupied installed destination and upgrades
nothing. Revision 1's "create-and-validate-if-absent" implied a reinstall path
that does not exist. Corrected:

* **fresh install** creates every path the configuration it writes will
  require, and **validates** them, before reporting success;
* **existing instance** gets a separate **read-only validate** verb that
  reports which prerequisites are missing and **refuses** — it repairs
  nothing, creates nothing, and no `chmod` or recursive normalisation is
  proposed anywhere.

### 4.2 The control store, through its own opener

`ControlStore.open(path, *, incarnation, clock)` already initialises an empty
store, adopts a supported existing schema, requests WAL, takes an explicit
incarnation and an injected clock, and closes its handle on every failure. So:

* the installer calls **that same API** once, with the installer's own
  incarnation and its injected clock, and closes it;
* there is therefore **one creator and one migrator** — the proposal adds no
  second compatibility check and asserts no generic migrator;
* a store that exists but is not recognised refuses through the opener, and
  the install reports that rather than touching it;
* `_create`/`_status` keep `open_readonly`, so DB-6's prohibition on implicit
  reopening is untouched.

### 4.3 Directory identities and crash residue

Created exclusively at 0700, the way `_new_directory` already does it: an
existing name is not ours because it has the right spelling. A wrong type, a
symlink, or a foreign owner **refuses by name**. Residue from a failed install
belongs to that install and is **reported**, not repaired — a later install
still refuses the occupied destination, which is the existing rule.

### 4.4 No `instance.json` inventory is needed

Revision 1 proposed recording a prerequisite inventory. Withdrawn:
`instance.settings` already derives the four operands from the instance
document and `stack.instance_settings` already validates the installed
selector. A new versioned inventory would be a second account of a fact those
two already own (DB-4).

### 4.5 Observation, using the APIs that exist

`stack status`/`monitor` are already instance-addressed. The gap is only the
lower-level `manager status --observe`. Proposed:

```
<distro>/baton-v12-stack manager --store <jobs> --incarnation <name> \
    --authority-uuid <uuid> status --control <control> \
    --observe tools.single_worker:observing_factory --instance <dest>
```

* `--instance` derives `BATON_V12_STAGE_EXECUTION_CONFIG` through
  `instance.settings`, reusing that owner API rather than a new one;
* **precedence**: explicit `--instance` wins; the env var is retained for
  compatibility; and if **both** are present and disagree, it **refuses**
  rather than silently preferring one.

---

## 5. Finite slices and sequencing

| slice | scope | independent? |
| --- | --- | --- |
| **S1** | `instance.layout` gains the three members; fresh install creates and validates them; occupied/wrong-type refuses | yes |
| **S2** | install-time control-store initialisation through `ControlStore.open`; existing-instance read-only validate verb | yes |
| **S3** | `status --observe --instance` with mismatch refusal | yes |
| **S4** | `creation_intents`, its owner API, the serial reconcile step, the configuration fence, `--wait/--no-wait` | needs the §2 decision **and** W371072 coordination |

S1–S3 need no new semantics and should land first: together they reach a first
`start` with no operator-authored step, which is most of OBS-0a.

## 6. Proposed acceptance

Deterministic, with isolated temporary stores and fake owner boundaries — **no
live run, and the retained instance is never started.** Revision 1 claimed
reproduction would require starting it; R4 is right that this is unsupported,
and it is withdrawn.

| behaviour | assertion |
| --- | --- |
| fresh install | every configured path exists and validates before success is reported; first `start` needs no operator step |
| existing instance | validate reports missing prerequisites and refuses; repairs nothing |
| first create | on a never-started instance, `create` succeeds with no start/stop cycle |
| create on a running manager | admitted exactly once; one operation id in the journal |
| same request twice | replays to one admission (DB-7) |
| changed request | collides as `_changed`, naming the recorded digest |
| different Jobs | both admitted; derivations serialised; neither sees the other's configuration |
| direct vs queued race | exactly one performs; the loser replays to the same answer |
| crash after each cut | the table in §2.5, each row asserted; no duplicate effect |
| retired intent | never executes afterwards |
| timeout while pending | non-zero exit, intent still `pending`, later completion reaches the same answer |
| second `start` | still refuses under HOST-8 |
| store/directory failures | wrong type, symlink, foreign owner, unreadable: refuse by name; no chmod |
| read-only observation | no application-data or schema mutation, no initialisation, migration or reconciliation, no writable fallback; sidecars accepted |
| packaged commands | every assertion through the installed bundle's argv |
| OBS-0 | the ≤60s whole-path interval from `received_at` to the worker's `work` state, endpoints and clock sources named, simulated-provider limit stated |

## 7. Overlap

* **W371072 is no longer a peer proposal.** Its admission plan was selected as
  a `DESIGN.md` clause by the owner on 2026-10-28, during this claim. So
  pre-reservation validation and the retained-contract dispatch check are
  **settled requirements**, §2.6a states this plan's conformance with each,
  and S4 cannot be accepted in a form that contradicts them. `DESIGN.md` must
  be re-read at the next claim rather than carried from this base.
* **W325695** holds `claude_agent` and its adapter tests — the current
  working-tree modifications are that Work's, not this one's.
* **W370555** is **already in** `f36bcd75`; S3 touches `single_worker`'s
  `observing_factory` with no outstanding checkpoint to wait for.
* S1/S2 touch `bootstrap.py`, `instance.py` and the install path; S4 touches
  `job_manager`, `creation` and the reconcile loop.

## 8. Labelled

**Observed:** the four refusals and every source anchor, re-read at this base.
**Inferred:** that S1–S3 suffice to reach a first `start` with no operator
step; not built or run. **Proposed:** every contract in §2–§6. **Open:** the
§2 decision; whether `create` waits by default; whether the serial
one-per-tick reconcile is sufficient or a concurrency bound is wanted; and
whether `configuration_revision` is owned here or by W371072.

No probe was run. Revision 1 justified that by saying reproduction needed the
retained instance, which was wrong; the honest reason is that the four
refusals are already retained with their exact text, and isolated temporary
stores would re-derive facts the evidence already carries.
