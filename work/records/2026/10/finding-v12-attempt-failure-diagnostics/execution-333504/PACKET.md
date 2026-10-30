# W333486 execution-selection packet — 2026-10-19

Author `baton.claude`, role `impl`, claim333504. Bound dossier
`work/records/2026/10/finding-v12-attempt-failure-diagnostics`.

**State: `prepared-not-executed`.** No Job was submitted, no engine or
container was invoked, no provider was contacted, no credential was read, and
no product or test file was edited on the host. Every identity below is a
**proposed generated identity**; the authority uuid, Work id, Job id,
submission id, attempt id and runtime id of an actual execution are derived by
the owner's own bootstrap and start and do not exist yet.

This packet is the deliverable the reviewer's return on sibling W333485
(`../finding-v12-serving-token-renewal/review-2026-10-19T16-20-30Z.md`)
identified as the authorized preparation milestone when the live
execution-selection gap is real: a fresh immutable execution-selection packet
with routine operands resolved from supported reference paths, actual bytes and
base pinned, the full task and outcome-based verification included, destination
reuse and drift refused, and exact preparation/start/status commands with the
limits the generated documents actually carry. It does not launch anything and
claims no authority to.

## Why the implementation is not on the host

PLAN.md requires this correction to be implemented through an isolated v12 Job
and states that an unavailable v12 operation is a blocker to resolve rather
than permission for direct host implementation. FINDING.md states "No direct
host implementation". `AGENTS.md` "V11 preparation and v12 execution — owner
2026-10-18" removes the general direct-execution fallback.

The gap is the same one the sibling recorded, and it is a selection gap rather
than a capability failure: this Work selects no authoring instance,
configuration, worker image, roots, run identity or provider delivery, and the
only concrete instance in scope is the failed native pilot, whose mutation and
retry are excluded. No launch refusal is claimed and no sandbox denial was
encountered. Docker is reachable read-only and the selected image is present
locally — `docker image inspect baton-v12-claude-worker:w239528-244216`
answers `sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`,
`amd64`, `linux`, unchanged and **not rebuilt**.

What remains for the owner is one decision: whether to select this exact
separate authoring run. Everything else it needs is resolved below.

## Selected identities

| element | selection |
| --- | --- |
| declared base | `bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c` — this tree's committed `HEAD`, matching PLAN.md, compared twice this claim |
| run identity | `attempt-diagnostics-w333486-333504` |
| selected root | `/home/sl/baton-instances/attempt-diagnostics-w333486-333504` — **does not exist**; `stage` refuses reuse |
| worker image | `baton-v12-claude-worker:w239528-244216`, config digest `sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2` — existing, revalidated, unchanged, **not rebuilt** |
| manager runtime | `/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro`, binary `sha256 04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a`, build commit `1e576ff2` |
| manager source | 112 files from `v12/python/{src/baton_v12,tools}` **at the declared base**, staged into the root's own `code/` |
| supervisor | `work/records/2026/09/finding-v12-single-implementation-proof/{baseline.py,baseline_bindings.py,prepare_instance.py}` at the declared base (`c1b0a10e…`, `09fbf3c5…`, `d08514cb…`) |
| launch envelope | `baton.dogfood-task/2`, `source_root` `source`, `source_profile` `git-line`, `context_mode` `fresh` |
| terminal policy | `report-and-hold`; one implementation invocation, no automatic retry |
| evidence digest | `sha256` of `../../finding-v12-native-pilot-instance-packet/OWNER-FAILURE-EVIDENCE-20261019.md` — the attributed incident this correction answers |

## Frozen input, and what is deliberately excluded

112 committed manager files and 3 committed supervisor files at the declared
base. **No overlay and no preserved candidate buffer**: unlike the 329953
reference this packet is modelled on, every byte this correction begins from is
committed, so there is no `restore.py` and nothing is written back into the
private checkout.

The working tree holds five changed files that belong to W321776's Stage-A
slice — `v12/.dockerignore`, `v12/worker/Dockerfile.claude`,
`v12/python/src/baton_v12/verification_context.py`,
`v12/python/tests/manager/test_verification_context.py`,
`v12/python/tests/manager/test_claude_agent.py`. They are **another Work's
inputs under another claim**, are not selected here, and are not staged,
overlaid or referenced by the composed submission. `PROVENANCE.json` names
them so review can see the exclusion was deliberate rather than overlooked.

The seven documents the turn must READ travel as the packet's own
`fixture.files` pins over the read-only nominated source, so the supervisor
refuses a drifted one **before any store opens** rather than inside a provider
turn. Two of them — this dossier's `FINDING.md` and `PLAN.md` — are the
reviewer's to own. If they are appended to before the owner starts,
`verify-inputs.py` refuses and the correct response is to **re-seal this packet
at the new bytes**, never to edit a pin to match.

## The task, in one paragraph

`TASK.md` is the whole of it. The confirmed gap is that
`intake.reclaim_expired_resource` — the only act that stops a container because
its governed generation went overdue — journals no account of having done so:
its outcome is an in-memory dict handed to `tools/job_manager.py:_reclaiming`,
reported in one tick's sweep report, of which `manager.serve` keeps only the
last. That is why the owner's public `attempt_start_failure_of` and
`attempt_preparation_failure_of` both answered `null` for an attempt whose
runtime was in fact destroyed. The turn therefore (1) captures a typed,
journalled, manager-owned termination record **at that boundary**, with the
stable facts on the signature and the facts-as-they-stood in the document, written
after positive confirmation and before the return; (2) adds one public reader
for it, held to `attempt_start_failure_of`'s discipline; (3) composes one typed
cause with an **explicit unknown that names which records are absent**, the
whole token axis, the execution axis and safe locators only; (4) carries it to
ordinary status through an **optional** eighth observation member, moving
`STATUS_SCHEMA` to `/7`, deciding nothing on it; and (5) adds one read-only
report following `tools/worker_visibility.py`'s accepted discipline, reached
through `tools/stack_command.py` `COMMANDS` so it is the **deployed** command
rather than a source-only script.

## Verification, and the ceiling that bounds it

The sealed argv runs nine existing modules plus the two the turn must create.
Measured against a clean export of the declared base (`git archive` into
`/tmp/w333486-base-probe`, no working-tree bytes):

| module | seconds | tests |
| --- | --- | --- |
| `tests.job_manager.test_status` | 0.343 | 65 |
| `tests.job_manager.test_delegation` | 0.059 | 44 |
| `tests.job_manager.test_documents` | 0.002 | 31 |
| `tests.job_manager.test_tool` | 0.575 | 72 |
| `tests.manager.test_intake` | 4.121 | 207 |
| `tests.manager.test_maintenance` | 2.396 | 148 |
| `tests.manager.test_attempts` | 4.048 | 431 |
| `tests.tools.test_worker_visibility` | 0.277 | 78 |
| `tests.manager.test_contracts_inventory` | 0.010 | 15 |
| **total** | **11.830** | **1091**, all passing, zero skips |

`GATE-CHECK.json` records the composed argv run verbatim from
`packet/task.json` against that same base with a deliberately useless ambient
`PYTHONPATH`: **status 1, 1093 tests in 11.668s, failing on exactly the two
owed modules and nothing else.** That is the designed state — a sealed argv
cannot name classes that do not exist yet, so the two module names are part of
the contract and the gate fails until the turn writes them.

`LIMITS-CHECK.json` reads the **generated** documents rather than this prose.
`policy.json` and `submission.json jobs[0].execution_limits` agree: provider
turn 3600s, verification command 30s, one implementer invocation,
`report-and-hold`; supervisor bounds 4800s total with 60s reserved cleanup;
residual total margin 1110s.

**The 30-second verification ceiling is not this packet's to set.** The
composer fixes it in both places it appears — `baseline_bindings.py:345`, the
execution policy whose digest the submission carries, and `:522`, the
submission's own `execution_limits` — with no compose parameter and no bounds
member. A different ceiling would mean editing accepted supervisor product this
packet does not own. The nine existing modules already spend 11.83s of it, so
the two new modules have **≈18.17s** between them. `TASK.md` states that as a
real design constraint and requires an honest measured report if the gate
cannot be made to fit, rather than deleted coverage bought with time.

### Two modules are deliberately excluded, and both are pre-existing

Recorded here so review cannot attribute either to this candidate:

- **`tests.manager.test_boundary_inventory` does not pass at this base.**
  Measured alone against the clean base export: **328 tests, 28 failures, 1
  error, zero skips, 49.469s** — stale declared owners for `review_cycles.py`,
  entries owned twice for `intake.py:discharge_quiescence_gate`,
  `intake.py:discharge_abandoned_quiescence_gate` and
  `interrogation.py:probe`, plus lane-coverage and probe-arrival failures. Not
  an artefact of the dirty working tree: measured on base bytes alone. Its
  49.5s would also exceed the 30s ceiling by itself. `TASK.md` excludes it,
  forbids "fixing" it here, and still requires the turn to register the
  receiving entries and probes its **own** new boundary introduces — a
  pre-existing failure is not a licence to add an unregistered boundary.
- **`tests.tools.test_packaging` fails on this host for an unrelated reason.**
  `WhatTheBundleSaysItIs.test_every_subcommand_this_command_serves_is_offered`
  holds the source `stack_command.COMMANDS` table against the **installed
  bundle's** help, and the bundle at
  `/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro` was
  built at `1e576ff2`, before `record` and `disposition` joined that table.
  Observed failure: `'disposition' not found in` the bundle's help. Inside a
  private checkout the module instead SKIPs, because there is no
  `v12/build/out/distro`, and the gate program refuses a skip. So the
  packaged-table obligation moves to a source-level case in the new
  `tests.tools.test_attempt_diagnostics` module, and `TASK.md` forbids both
  rebuilding the bundle and editing that module to make it pass.

  This is worth the reviewer's attention beyond this packet: any Work that adds
  a packaged subcommand will fail that case on this host until the bundle is
  rebuilt, and the test cannot distinguish "the source grew a verb" from "the
  bundle is stale". Reported rather than worked around.

## Preparation evidence

`PREFLIGHT.json` holds the whole run. The three preparation steps were
exercised once into the **throwaway** root `/tmp/w333486-preflight-333504`;
the selected root is untouched.

- `stage` 0.122s, `bootstrap --no-repositories` 0.592s, `bind` 0.353s —
  **1.189s**, all status 0, first attempt.
- `bind` ended at `PREPARED.json: state prepared-not-executed` over eight
  composed artifacts, after `baseline.held_packet` re-pinned every artifact the
  packet binds — including each of the seven `fixture.files` — and
  `baseline.verify_imported_sources` proved the process was running the staged
  code rather than some other checkout.
- **The composed packet digest is per-instance and is deliberately not quoted
  here as an expected value.** The preflight recorded authority
  `f72d08c14e7e4ab8967f2c512979fd9d` and packet
  `sha256 737083160d858babc09b1f085c78e505502de1c6c8717a8ee351b9cf13d9442d`,
  and the owner's own run will produce different ones: `bootstrap` generates
  this instance's own authority uuid, and `prepare.py bind` derives the Work id
  from it (`uuid[:8] + "-W1"`), which travels into the submission. Both values
  are therefore **actual-execution facts of the preflight**, not proposed
  production identities. What is stable and pinned is the input side — base,
  112 manager files, 3 supervisor files, 3 preparation inputs, 7 task inputs
  and the bootstrap binary — which is what `verify-inputs.py` and
  `held_packet` hold.
- **Ten refusal probes, all refusing as intended, 0.783s**: an existing root;
  a root that already holds a composed packet; drifted staged manager source
  (exercised on its own staged-but-unbound root, because the
  packet-existence check would otherwise answer first and mask it); a packet
  naming another base; a packet naming another run; a drifted preparation
  input; a wrong supervisor digest; a gate module that already exists on the
  host, refused by both `prepare.py` and `verify-inputs.py`; and
  `verify-inputs.py` passing on an undrifted tree.
- `verify-inputs.py` on the current tree: 112 manager files, 3 supervisor
  files, 3 preparation inputs, 7 task inputs, 2 gate modules still owed,
  0.108s.

### One defect this packet's own probes found, and fixed

The 329953 reference's `stage` creates the root and writes its 112 manager
files **before** validating the three supervisor digests, so a supervisor drift
left a half-staged root behind — which the "refuse reuse" rule in the very next
line then blocks forever, making the repair for a refused stage "delete the
directory the packet just made". Measured here rather than assumed: the probe
root survived the refusal. `prepare.py` now resolves and proves **every** base
byte in memory first and creates the root only once nothing left can refuse, so
a refused stage leaves the filesystem exactly as it found it. The probe
`a wrong supervisor digest refuses and leaves no root` asserts both halves.

## Overlap declaration to sibling W333485

Required by FINDING.md before a combined candidate.

This candidate's surfaces: `worker_manager/documents.py`,
`worker_manager/attempts.py`, `worker_manager/intake.py` (the reclaim path
only), a new `worker_manager/diagnostics.py`, `job_manager/delegation.py`,
`job_manager/documents.py`, `job_manager/projection.py`, a new
`tools/attempt_diagnostics.py`, `tools/stack_command.py`, and the two new test
modules.

W333485's PACKET.md expects to share `tools/job_manager.py` and
`job_manager/manager.py`. **This candidate touches neither**, and that is a
design choice rather than an accident: the new observation member is composed
inside `delegation.ManagerOperations.observe`, which both the serving loop and
the read-only `status` surface already reach, so the sibling's two files need
no edit here. `TASK.md` forbids touching them.

**Intersection: empty.** The one residual file-level risk is
`worker_manager/intake.py` if the sibling's renewal integration reaches the
reclaim path; it is declared here, and must be integrated serially rather than
overwritten.

**No behavioural dependency in either direction.** Existing failed records and
the explicit-unknown fallback are independent inputs, so this correction does
not wait on renewal. And once renewal is integrated, an attempt that is never
reclaimed simply holds no termination record — which this correction must
report as `unknown` naming the absent evidence, not as a failure. That is the
same branch a historical attempt reaches, and it is covered by the gate.

## What is still owed

The entire correction in FINDING.md. This packet contains no implementation.
Owed: the owner's selection of this exact separate authoring run; the run
itself; the retained immutable candidate; independent review of it; the
parent's joined acceptance with W333485; and the human Git checkpoint the
parent PLAN carries. A retained proposal is not an accepted candidate and
nothing here is self-acceptance.
