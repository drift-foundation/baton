# W333486 execution-selection packet, revision 3 — 2026-10-19

Author `baton.claude`, role `impl`, claim334663. Bound dossier
`work/records/2026/10/finding-v12-attempt-failure-diagnostics`.

**Declared base `a9f4fa4da2323a357ae15aefbc5d7d22d41487b6`** — the human
checkpoint that integrated the accepted authoring-enforcement correction.

**Supersedes `../execution-333504` and `../execution-333707`**, both preserved
unchanged with their own seals (`bca87e93…` and `a0414adb…`). No hash of
either was edited and neither `start_authorized` flag was flipped. Both pin the
old unenforced supervisor and remain unlaunchable regardless of
`execution-333707`'s preparation acceptance.

**State: `prepared-not-executed`; `start_selected: false`.** No Job submitted,
no engine or container invoked, no provider contacted, no credential read, no
product or test file edited on the host, and no falsification re-run — the
prerequisite that required one is closed.

## What changed since the accepted revision

`decisions/review-333812.md` accepted revision 2's task and preparation at
design level. Then the prerequisite closed and the base moved, so this revision
rebases and **revalidates the design against bytes that did not exist when it
was written**.

| # | Change | Driver |
| --- | --- | --- |
| 1 | Rebased to `a9f4fa4d`; **113** pinned manager files, up from 112 — the new one is `tools/authoring_enforcement.py` | PLAN: the accepted checkpoint is the new preparation base |
| 2 | Binds the accepted controller explicitly and **proves the binding both ways** | the controller's own `verify_controller` requires it |
| 3 | `bind` writes `packet/AUTHORING-COMMAND.json`, because the composer's generated `start` names the **unenforced** supervisor | measured; see below |
| 4 | TASK revalidated against the committed `intake.py`/`attempts.py`: token-bound identity, replay-with-no-effect, a new held outcome, and **cancellation as a second terminating component** | FINDING's fourth supersession |
| 5 | Gate adds `tests.manager.test_authoring_enforcement` | this candidate edits the files it covers |
| 6 | `HOLD.md` → `ENFORCEMENT.md`; the gate is now an **unselected start**, not a blocker | prerequisite closed by owner close334628 |
| 7 | Decision snapshots refreshed: enforcement review and integration added, closed-blocker evidence dropped | PLAN: refreshed immutable snapshots |

### 4 — the design had to change, not just the base

The accepted correction rewrote parts of the two files this candidate also
touches. Four consequences, each read from the committed diff:

- **The runtime identity now comes from the token, not the attempt row.**
  `reclaim_expired_resource` takes `runtime_id = overdue.get("container")`,
  refuses `identity-mismatch`, and derives its correlation id as
  `reclaim_operation_id(dict(attempt, runtime_id=runtime_id), generation)`.
  Revision 2's task proposed deriving a record identity from
  `attempt["runtime_id"]` — which can be `None` while a real writer exists,
  because the token binds a container **before** the attempt attaches it. That
  proposal is withdrawn in `TASK.md`.
- **A replayed reclaim issues no effect at all.** If the generation is revoked
  and the exact identity is already observed `absent`/`quiescent`, no stop and
  no removal are issued. So durable intent must be replay-honest: a pass that
  ordered nothing must not read as a pass that ordered a stop.
- **There is a new held outcome**: the token-bound runtime ceased while the
  attempt's own attachment or activation is unresolved. Two facts, not one.
- **Cancellation is a second terminating component.**
  `attempts._order_quiescence` now resolves the token-bound container after the
  Authority fence, refuses a conflicting identity, and otherwise answers
  *"the assignment is fenced but an unresolved launch is not proof of
  cessation"*. A composed cause that knew only about expiry reclaim would
  report `unknown` for an attempt cancellation actually ended.

`decisions/enforcement-integration.md` requires any overlapping candidate to be
**rebased onto** these bytes with independent review, never overwritten.
`TASK.md` carries that as a boundary: this candidate adds attribution and
preserves the accepted cessation semantics.

### 3 — the composer still advertises the unenforced start

This is the finding most worth a reviewer's attention.

`baseline_bindings.py` is **unchanged** at this base
(`sha256 09fbf3c59820231b7199e24aa1cf64eee93f6ea2e60f3477fed5ca909e5fc379`)
and its line 721 still composes `start` as
`[python, -B, <supervisor>/baseline.py, --packet, …, --incarnation, …]`.
Measured from the composed preflight documents rather than inferred:

```
commands.json  start : [python3, -B, <root>/supervisor/baseline.py, --packet, …, --incarnation, …]
AUTHORING-COMMAND.json start : [python3, -m, tools.authoring_enforcement, --packet, …]
```

So a packet composed by the accepted composer tells an operator to start
exactly the vehicle the prerequisite existed to replace. `prepare.py bind`
writes the enforced invocation beside it, `PREPARED.json` carries
`composer_start_is_unenforced: true`, and `ENFORCEMENT.md` and `OPERATOR.md`
both say plainly not to use `commands.json`'s `start`.

**Reported, not patched.** Correcting the composer is host product work this
Work does not own, and **every later authoring packet inherits the defect until
it is corrected** — which is why it is raised here for classification rather
than worked around quietly.

## Selected identities

| element | selection |
| --- | --- |
| declared base | `a9f4fa4da2323a357ae15aefbc5d7d22d41487b6` |
| run identity | `attempt-diagnostics-w333486-334663` |
| selected root | `/home/sl/baton-instances/attempt-diagnostics-w333486-334663` — **does not exist**; `stage` refuses reuse |
| authoring controller | `tools/authoring_enforcement.py`, `sha256 2da6eb36b398d730c8cc07a9df0b604de678a3fd994d5019097fa023addfb88f`, pinned among the 113 manager files |
| worker image | `baton-v12-claude-worker:w239528-244216`, `sha256:c862c055…` — existing, **not rebuilt** |
| manager runtime | `/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro`, binary `sha256 04aa459a…` |
| supervisor | `baseline.py` `c1b0a10e…`, `baseline_bindings.py` `09fbf3c5…`, `prepare_instance.py` `d08514cb…` at the declared base |
| launch envelope | `baton.dogfood-task/2`, `source_profile` `git-line`, `context_mode` `fresh` |
| terminal policy | `report-and-hold`; one implementation invocation, no automatic retry |
| **start** | **NOT SELECTED.** `PROVENANCE.json` `start_authorized: false`, `start_selected: false` |

## The lease, stated honestly

`tokens.LIFETIME_SECONDS` is still **900** and production renewal remains
W333485's unfinished work. The accepted controller makes that initial lease
**actually enforced** — it is no longer ignored — but it does not extend it.

So provider turn 3600s inside a 4800s total are **requested ceilings, not a
promise of a 3600-second authoring run.** Expect enforced expiry at 900
seconds with cessation ordered, partial output retained and a held outcome.
`TASK.md` requires the turn to preserve a partial candidate and report the
actual expiry, cleanup, retained-output and recovery behaviour it observes.

Two of my own earlier statements are **withdrawn** and recorded as such in
`ENFORCEMENT.md`, `PROVENANCE.json` and `LIMITS-CHECK.json`:
`execution-333504/OPERATOR.md` claimed the native pilot's 903-second
termination transferred to the authoring vehicle (it did not — that vehicle had
no reclaim at all), and `execution-333707/HOLD.md` said the lease was
unenforced (true of that vehicle, not of this base). Both documents are
preserved with their original wording.

## Inputs: pinned, snapshotted, and deliberately not pinned

- **Fatal if drifted** — 113 committed manager files (including the pinned
  controller, checked against both the manager source and the base), 3
  committed supervisor files, 2 preparation inputs, the bootstrap binary.
- **Immutable snapshots, fatal if damaged** — the 7 decision documents under
  `decisions/`, with source paths and digests in `decisions/INDEX.json`, pinned
  as `fixture.files` with `TASK.md` and `ENFORCEMENT.md` (10 in total).
  Refreshed this revision: the enforcement review and integration record are
  **added**; the sibling blocker review and its probe evidence are **dropped**,
  because carrying a resolved blocker forward would bind it as if it still
  stood. They remain in `execution-333707`.
- **Reported, never fatal** — whether each live decision source still matches
  its snapshot. `verify-inputs.py` prints `DECISION-SOURCE DRIFT` and exits 0,
  so an ordinary plan update cannot invalidate a sealed packet and cannot
  silently change what the turn was told either.
- **Not pinned at all** — `v12/DESIGN.md`, `AGENTS.md`, the worker-visibility
  FINDING, and `…/finding-v12-single-implementation-proof/baseline.py`. All are
  committed at the base, so the private checkout carries them. The last is
  listed because `tests.manager.test_authoring_enforcement` spawns a real
  supervisor and resolves that directory from the checkout root.

No overlay and no preserved candidate buffer. The five dirty W321776 Stage-A
files are named in `PROVENANCE.json` as a deliberate exclusion.

## Verification, and the ceiling that bounds it

Ten existing modules plus the two the turn must create. Measured against a
clean export of the declared base — **the preparing author's evidence, not
independent product acceptance**: **1124 tests, all passing, zero skips,
14.230s**.

| module | seconds | tests |
| --- | --- | --- |
| `tests.job_manager.test_status` | 0.459 | 65 |
| `tests.job_manager.test_delegation` | 0.059 | 44 |
| `tests.job_manager.test_documents` | 0.002 | 31 |
| `tests.job_manager.test_tool` | 0.587 | 72 |
| `tests.manager.test_intake` | 4.189 | 207 |
| `tests.manager.test_maintenance` | 2.390 | 148 |
| `tests.manager.test_attempts` | 4.061 | 431 |
| `tests.tools.test_worker_visibility` | 0.278 | 78 |
| `tests.manager.test_contracts_inventory` | 0.010 | 15 |
| `tests.manager.test_authoring_enforcement` | 2.194 | 33 |

`GATE-CHECK.json`: this packet's composed argv run verbatim from
`packet/task.json` against that base with a deliberately useless ambient
`PYTHONPATH` — **status 1, 1126 tests in 13.792s, failing on exactly the two
owed modules.**

A **measured requirement**: `tests.manager.test_authoring_enforcement` needs
`work/records/2026/09/finding-v12-single-implementation-proof` at the checkout
root. Measured both ways — **1 error without it** (the spawned child cannot
import `baseline`, so the partial-output file is never written), **33 passing
with it**. The private checkout carries it; it is pinned in
`read_from_checkout_at_base` and stated in `ENFORCEMENT.md` so nobody
rediscovers it inside a provider turn.

`LIMITS-CHECK.json` reads the **generated** documents: `policy.json` and
`submission.json jobs[0].execution_limits` agree — provider 3600s,
verification 30s, one invocation, `report-and-hold`; bounds 4800s total, 60s
cleanup, 1110s residual. The 30-second ceiling is fixed by the composer, so the
ten existing modules' 14.230s leaves **≈15.8s** for the two new ones — tighter
than revision 2's ≈18.17s. The trade was deliberate: this candidate edits the
files `test_authoring_enforcement` covers.

### Two excluded modules, both explicitly unverified baseline reports

Recorded by review as the author's unverified baseline observations with no
cleanup selected; neither attributable to this candidate, neither worked
around: `tests.manager.test_boundary_inventory` does not pass at base (328
tests, 28 failures, 1 error, 49.469s measured alone on the previous base's
bytes, which alone exceeds the ceiling), and `tests.tools.test_packaging`'s
subcommand case holds the source command table against the **installed
bundle**, built at `1e576ff2` before `record` and `disposition` joined it.
**Source command-table proof is not proof that an eventual rebuilt bundle
carries the new verb**, and `TASK.md` keeps that deployment obligation
explicit.

## Preparation evidence

`PREFLIGHT.json` holds the whole run; no selected root exists.

- `stage --acknowledge-unselected-start` 0.126s,
  `bootstrap --no-repositories` 0.594s, `bind` 0.361s — **1.209s**, all status
  0, first attempt, ending `prepared-not-executed`, `start_selected: false`,
  `composer_start_is_unenforced: true`, after `held_packet` re-pinned every
  artifact including all 10 `fixture.files` and `verify_imported_sources`
  passed.
- **The vehicle binding proved both ways**, read-only, starting nothing and
  opening no store: the accepted controller's own `verify_controller`
  **ACCEPTED** this packet's composed documents when imported from the staged
  source (0.295s), and **REFUSED** — *"authoring controller is outside the
  pinned manager source"* — when imported from the host checkout instead.
- **Eight probes, all refusing as intended, 0.494s**: no acknowledgement; a
  drifted staged controller; an unpinned controller; a damaged enforcement
  snapshot; a provenance claiming a selected start; an absent enforcement
  document; an existing root; a root already holding a packet. Each
  root-creating probe also asserts the root was **not** created.
- `verify-inputs.py` on the current tree: 113 manager files, 3 supervisor
  files, 2 preparation inputs, 10 task inputs, 7 decision snapshots, 4 checkout
  documents, 1 pinned authoring controller, 2 gate modules still owed, no
  decision-source drift.
- The composed packet digest and authority uuid are **per-instance preflight
  facts**, not proposed production identities.

### One defect this revision's own probes found

`prepare.py` checked `start_authorized` but not `start_selected`, so a
provenance asserting a selected start would have staged. The two are different
claims — *may anyone start* versus *has anyone chosen to* — and both are now
refused, with a probe asserting it and the absent root. Carried forward from
revision 2: the `stage` ordering that proves every base byte before creating
the root.

## Overlap declaration

**Sibling W333485** is separately allocated to `baton.codx` for its own fresh
preparation (at334644), with no diagnostics dependency on its completion.
Intersection with its declared surfaces (`tools/job_manager.py`,
`job_manager/manager.py`) is **empty**: the new observation member is composed
inside `delegation.ManagerOperations.observe`, which both the serving loop and
the read-only `status` surface already reach, and `TASK.md` forbids touching
those two files.

**Intersection with the accepted enforcement bytes is real and declared**:
`worker_manager/intake.py` and `worker_manager/attempts.py`.
`decisions/enforcement-integration.md` requires rebasing onto the integrated
bytes with independent review and forbids overwriting or silent conflict
resolution. `TASK.md` carries that: attribution is added, cessation semantics
are preserved, and integration is serial.

## What is still owed

The entire correction in `decisions/FINDING.md`. This packet contains no
implementation. Owed: independent review of this preparation; an exact separate
execution selection; the run; the retained immutable candidate; independent
review of that; parent W325959's joined acceptance with W333485; and the human
Git checkpoint the parent PLAN carries. A retained proposal is not an accepted
candidate and nothing here is self-acceptance.
