# W333486 execution-selection packet, revision 4 — 2026-10-20

Author `baton.claude`, role `impl`, claim337453. Bound dossier
`work/records/2026/10/finding-v12-attempt-failure-diagnostics`.

**Declared base `fb48797903160aa764229d58f3a5beaf29648bfc`** — the human
checkpoint that integrated the accepted manager-guard correction (W334910,
owner close337414), which sits on the accepted authoring-enforcement
correction (W333735, `a9f4fa4d`). **Both prerequisites are closed.** Both
temporary direct-implementation exceptions have expired and neither ever
covered diagnostics.

**Supersedes `../execution-333504`, `../execution-333707` and
`../execution-334663`**, all preserved unchanged with their own seals
(`bca87e93…`, `a0414adb…`, `380ea20a…`). No hash was edited and no start flag
was flipped.

**State: `prepared-not-executed`; `start_selected: false`.** No Job submitted,
no engine or container invoked, no provider contacted, no credential read, no
host product or test edit, and **neither** the enforcement falsification
**nor** the manager-guard real-process proof was re-run — both are reused as
the reviewer directed.

## The thing a reader must know first

**This vehicle has already been run once, and it failed.**

`../execution-334663` was accepted (review334776) and the owner selected and
started it with its `AUTHORING-COMMAND.json`. It died **0.506 seconds** into
startup: the enforcement parent had composed a manager and taken the workspace
guard, and the child's own composition asked for the same guard and was
refused `policy/denied` by `workspaces.hold_manager_instance`. The refusal was
the product working — single-manager exclusion is an invariant and the
controller violated it.

`FAILURE.md` is the full account; `evidence/execution-334663-failure/` in the
dossier holds read-only copies of the retained log, the enforcement report and
the exact command used. W334910 corrected it, and this packet's base is that
correction.

**It does not follow that the next start succeeds.** One corrected startup
refusal is not a demonstration that a full provider-backed authoring
invocation completes here. No such run has ever completed for this Work.

## What changed since the accepted revision

| # | Change | Driver |
| --- | --- | --- |
| 1 | Rebased to `fb487979`; the pinned controller moves `2da6eb36…` → `bc8c0363…`, still 113 manager files | PLAN: the corrected checkpoint is the base |
| 2 | `FAILURE.md` and dossier evidence record the first actual execution and its startup failure | owner reroute334895 |
| 3 | TASK item (b) states the **quiescent-versus-absent** distinction as an explicit three-case table | review334776's correction of my prose |
| 4 | Gate re-measured; `tests.manager.test_authoring_manager_guard` excluded for a **measured ceiling** reason | 17.643s, see below |
| 5 | Decision snapshots refreshed: guard review, guard integration and its reusable result added; failed-run index added | PLAN: refreshed snapshots, reuse the guard proof |

### 3 — the correction to my own prose

`decisions/review-334776.md` caught a real overstatement. My revision-3
`PACKET.md` summary said a replay observing `absent`/`quiescent` issues "no
stop and no removal". The committed code does not say that, and my TASK's
detailed section did not either — but a summary that disagrees with the code
is a summary that can become implementation behaviour.

The two conditions are separate tests:

| observed `before` | stop issued | removal issued |
| --- | --- | --- |
| `absent` | no | **no** |
| `quiescent` | no | **yes**, if a removal capability exists |
| anything else | yes | yes |

**Only an exact absence skips both.** A quiescent container still exists and
still holds its mounts. `TASK.md` now carries this as a table, splits the
replay acceptance case into three, and adds "quiescent is not absent" to the
axes that must survive. Candidate review must check the stopped-but-present
removal separately.

### 4 — a gate decision made on a measured number

`tests.manager.test_authoring_manager_guard` costs **17.643 seconds for 7
tests** — it spawns real processes. The composer fixes
`verification_command_seconds` at **30**, and the ten gate modules already
cost **14.095s**. Including it would put the sealed gate at **31.7s before the
two new modules exist**.

So it is **excluded for the ceiling, not for coverage**, and its coverage is
carried by the reused accepted proof in
`decisions/guard-integration-result.json` — 79 tests, PASS, 15.278s, under
authority337376. This candidate does not edit `authoring_enforcement.py`; if a
turn ever does, `TASK.md` requires that module as a focused check **outside**
the sealed argv, reported as such.

## Selected identities

| element | selection |
| --- | --- |
| declared base | `fb48797903160aa764229d58f3a5beaf29648bfc` |
| run identity | `attempt-diagnostics-w333486-337453` — **fresh**; the failed run's identity is never reused |
| selected root | `/home/sl/baton-instances/attempt-diagnostics-w333486-337453` — **does not exist**; `stage` refuses reuse |
| authoring controller | `tools/authoring_enforcement.py`, `sha256 bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f` (previously `2da6eb36…`), pinned among the 113 manager files |
| worker image | `baton-v12-claude-worker:w239528-244216`, `sha256:c862c055…` — existing, **not rebuilt** |
| manager runtime | `/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro`, binary `sha256 04aa459a…` |
| supervisor | `baseline.py` `c1b0a10e…`, `baseline_bindings.py` `09fbf3c5…`, `prepare_instance.py` `d08514cb…` |
| launch envelope | `baton.dogfood-task/2`, `source_profile` `git-line`, `context_mode` `fresh` |
| terminal policy | `report-and-hold`; one implementation invocation, no automatic retry |
| **start** | **NOT SELECTED.** `start_authorized: false`, `start_selected: false` |

## The start command is still not the one the composer writes

`baseline_bindings.py` is unchanged at this base
(`sha256 09fbf3c5…`) and line 721 still composes `start` as
`[python, -B, <supervisor>/baseline.py, …]` — the unenforced path. Measured
again from this revision's composed documents, not inferred.

`decisions/review-334776.md` accepts **only** the enforced invocation and
records the discrepancy as tracked under this Work with no broad composer
rewrite selected. `prepare.py bind` writes `packet/AUTHORING-COMMAND.json`;
`PREPARED.json` carries `composer_start_is_unenforced: true`. Reported, not
patched — **every later authoring packet inherits the defect** until the
composer is corrected.

The operator-facing invocation did **not** change with the guard correction:
`python -m tools.authoring_enforcement --packet <PACKET.json>` from the staged
source. `--status-path` is internal — the watchdog passes it to the child.

## The lease, stated honestly

`tokens.LIFETIME_SECONDS` is still **900**; production renewal is still
W333485's unfinished work, separately allocated to `baton.codx`. Both
corrections make the initial lease **enforced**; neither extends it. Provider
3600s, verification 30s, total 4800s and cleanup 60s are **requested ceilings,
not a promise of a 3600-second run** — expect enforced expiry at 900 seconds
with cessation ordered, partial output retained and a held outcome.

Two earlier statements of mine remain withdrawn and are repeated in
`ENFORCEMENT.md` so nobody has to reconcile them from superseded packets: the
`execution-333504` claim that the native pilot's 903-second termination
transferred to this vehicle, and the `execution-333707` claim that the lease
was unenforced on it.

## Inputs

- **Fatal if drifted** — 113 committed manager files (including the corrected
  controller, cross-checked against both the manager source and the base), 3
  supervisor files, 2 preparation inputs, the bootstrap binary.
- **Immutable snapshots, fatal if damaged** — 11 decision documents under
  `decisions/`, pinned as `fixture.files` with `TASK.md`, `ENFORCEMENT.md` and
  `FAILURE.md` (15 in total). Added this revision: the guard review, its
  integration record and reusable result, and the failed-run index.
  `review-334776` is carried because it holds the quiescent correction. The
  first preparation review is dropped — its corrections are carried in later
  accepted text and it remains in `execution-333707`.
- **Reported, never fatal** — live decision-source drift, printed and exiting
  0, so an ordinary plan update cannot invalidate a sealed packet and cannot
  silently change what the turn was told.
- **Not pinned at all** — `v12/DESIGN.md`, `AGENTS.md`, the worker-visibility
  FINDING, and the supervisor's `baseline.py`; all committed at the base.

No overlay and no preserved candidate buffer. The five dirty W321776 Stage-A
files are a declared exclusion.

## Verification

Ten existing modules plus the two the turn must create, re-measured at **this**
base — **the preparing author's evidence, not independent product
acceptance**: **1124 tests, all passing, zero skips, 14.095s**.

| module | seconds | tests |
| --- | --- | --- |
| `tests.job_manager.test_status` | 0.452 | 65 |
| `tests.job_manager.test_delegation` | 0.059 | 44 |
| `tests.job_manager.test_documents` | 0.003 | 31 |
| `tests.job_manager.test_tool` | 0.586 | 72 |
| `tests.manager.test_intake` | 4.133 | 207 |
| `tests.manager.test_maintenance` | 2.382 | 148 |
| `tests.manager.test_attempts` | 4.003 | 431 |
| `tests.tools.test_worker_visibility` | 0.274 | 78 |
| `tests.manager.test_contracts_inventory` | 0.010 | 15 |
| `tests.manager.test_authoring_enforcement` | 2.193 | 33 |

`GATE-CHECK.json`: the composed argv run verbatim from `packet/task.json`
against a clean export of the base with a deliberately useless ambient
`PYTHONPATH` — **status 1, failing on exactly the two owed modules**, 14.099s.

`LIMITS-CHECK.json` reads the generated documents: `policy.json` and
`submission.json jobs[0].execution_limits` agree — provider 3600s,
verification 30s, one invocation, `report-and-hold`; 4800s total, 60s cleanup,
1110s residual. ≈**15.9s** of the ceiling remains for the two new modules, and
`decisions/review-334776.md` is explicit that this fit **remains unproved** and
that no coverage may be removed to force a pass.

`tests.manager.test_authoring_enforcement` needs
`work/records/2026/09/finding-v12-single-implementation-proof` at the checkout
root — it spawns a real supervisor. Measured: **1 error without it, 33 passing
with it.** Pinned in `read_from_checkout_at_base`.

Two modules remain excluded as **explicitly unverified baseline reports** with
no cleanup selected: `tests.manager.test_boundary_inventory`, and
`tests.tools.test_packaging`'s subcommand case, which holds the source command
table against the installed bundle. **Source proof is not rebuilt-bundle
proof**, and `TASK.md` keeps that obligation explicit.

## Preparation evidence

`PREFLIGHT.json` holds the run; no selected root exists.

- `stage --acknowledge-unselected-start` 0.123s, `bootstrap` 0.591s, `bind`
  0.354s — **1.195s**, all status 0, first attempt, ending
  `prepared-not-executed`, `start_selected false`,
  `composer_start_is_unenforced true`.
- **The corrected controller's binding proved both ways**, read-only: its own
  `verify_controller` **ACCEPTED** this packet's composed documents from the
  staged source, and **REFUSED** — *"authoring controller is outside the
  pinned manager source"* — from the host checkout.
- **Nine probes, all refusing as intended, 0.927s**, each root-creating one
  also asserting the root was not created: no acknowledgement; a drifted
  staged controller; **the superseded controller digest**; a damaged
  guard-review snapshot; a provenance claiming a selected start; an existing
  root; a root already holding a packet; plus the two binding checks above.
- `verify-inputs.py`: 113 manager files, 3 supervisor files, 2 preparation
  inputs, 15 task inputs, 11 decision snapshots, 4 checkout documents, 1 pinned
  authoring controller, 2 gate modules still owed, no decision-source drift.

### A probe expectation I had wrong

The superseded-controller probe initially asserted the wrong refusal message.
The packet **did** refuse — earlier and better than I predicted, at the
cross-check between `authoring_controller.sha256` and the pinned manager
source — so the probe's expectation was corrected to the message the code
actually produces, not the other way round.

Carried forward: the `stage` ordering that proves every base byte before
creating the root, and the `start_authorized`/`start_selected` pair both being
refused.

## Overlap declaration

**W333485** is separately allocated to `baton.codx`; no dependency on its
completion. Intersection with its declared surfaces (`tools/job_manager.py`,
`job_manager/manager.py`) is **empty** — the new observation member is
composed in `delegation.ManagerOperations.observe`, and `TASK.md` forbids
touching those two files.

**Intersection with the accepted corrections is real and declared**:
`worker_manager/intake.py` and `worker_manager/attempts.py`.
`decisions/enforcement-integration.md` requires rebasing onto the integrated
bytes with independent review and forbids overwriting or silent conflict
resolution. `tools/authoring_enforcement.py` is **not** in this candidate's
surfaces: the guard correction is a prerequisite this packet binds, not a file
it edits.

## What is still owed

The entire correction in `decisions/FINDING.md`. This packet contains no
implementation. Owed: independent review of this preparation; an exact
separate execution selection; a run that actually completes; the retained
candidate; independent review of that; parent W325959's joined acceptance with
W333485; and the human Git checkpoint the parent PLAN carries.
