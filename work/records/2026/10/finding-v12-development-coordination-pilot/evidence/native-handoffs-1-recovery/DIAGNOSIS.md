# native-handoffs-1 / `w385331-handoffs-1` — diagnosis and prepared recovery (2026-11-20)

K (`baton.prompt`), no claim held, under W321608 (owner claim, handler slaw). Read-only on the instance, the stores (never opened directly), the retained attempt and the human Git; one isolated candidate copy in `work/scratch/w383217/handoffs-recovery/` for deterministic checks. No fresh-attempt, host import, instance write, config change, live launch or Git mutation was performed. Disclosed: the retained native session log under `state/launch/logs/…/native/` was read once, read-only, to derive the tool-invocation timeline in `worker-timeline.txt`; no model prose or provider text was copied out.

## 1. What happened (facts, with sources)

| Instant (UTC) | Fact | Source |
|---|---|---|
| 15:05:47 | Workers composed (impl-a/review-a, image `sha256:f2b86df0…`, layout `1423c3aa…`) | `deployment.json` |
| 15:23:04.651 | Job `w385331-handoffs-1` created, incarnation `slaw-create-handoffs-1`, template `baton.v12.job-template.implementation-review/1`, control `documentation/1` (3600/4800/9960/900 s, 0 corrections), terminal policy `report-and-hold` | `status-17h15.json` |
| 15:23:13–18 | Offer issued and claimed by `baton.claude-native` on Work `daec1190-W1`; attempt `attempt-15d73943…`; runtime `e3559b37…` | `status-17h15.json` receipts |
| 15:23:26 | First provider activity in the container | `worker-timeline.txt` |
| 16:22:36 | Last observed activity (3 398 337 bytes) | `status-17h15.json` runtime.activity |
| 16:23:23 | Provider-turn bound (3600 s, `job-default`) reached; worker adapter committed the working tree as candidate `a743edeb` ("baton candidate: w385331-handoffs-1", author "Baton worker"), answered `unable` with `provider-failed/timeout`, verification not attempted | `proposal/result.json`, `worker-output.json`, `candidate-commit.txt` |
| 16:23:27 | Host sealed the output, retained the attempt (`cleanup: retained`, allocation released `cleanup-retained`), runtime `destroyed`, resource token returned | `status-17h15.json` |
| 16:43:13 | Implementation stage deadline (4800 s) reached; review stage `blocked` on the exceptional gate | `status-17h15.json` control.stages |
| 18:09:04 | Job deadline (9960 s). **Once the manager journals this expiry, `fresh-attempt` is refused** (`cancellation.refuse_fenced`: "expired at … admitted after the deadline") | `cancellation.py:208-224`, `fresh_attempt.py:251-257` |

Status surfaces say `cause unknown` / `operation unknown` although the retained result records the timeout; that is the separate finding in `FINDING-status-cause-unknown.md`.

The manager (pid 2236050) and publisher (pid 2236051) were still serving at 17:20Z; the snapshot is fresh; one Job observed, canonical. No second attempt exists; the review stage never reserved a worker.

## 2. Custody and provenance — verified

- Frozen artifact: `file:///home/sl/baton-instances/native-handoffs-1/state/workspaces/.baton-review-lines/line-3eb38e93…/custody/attempt-15d73943…/proposal` (dir `r-xr-xr-x`, files `r--r--r--`), tree digest `sha256:659338c3…`, 4 entries, 425 348 bytes — matches the status artifact entry and the completion manifest's `content_manifest`.
- Per-file sha256 (`proposal.sha256`): `change.patch 5ec3e85b…`, `objects.bundle 7e602da2…`, `result.json cf44d19a…`, `verification.txt 4825c3ea…` — equal to the manifest digests and to the copy in the review-line checkout.
- `git bundle verify` against the human checkout: bundle okay; contains `a743edeb` HEAD; requires `3d05430f` (`bundle-verify.txt`). The review-line checkout holds `a743edeb` on top of `3d05430f` with no other commits.
- Base agreement: `result.json.base = entry_head = 3d05430f` = task `declared_base` = deployment `line_declared_base` = `canonical_target_id` = installed `instance.json` build-stamp commit.
- Reconstruction: `git archive 3d05430f` + `patch -p1 < change.patch` in the isolated copy reproduces all 24 blobs of `a743edeb` exactly (`candidate-blobs.txt`; 0 mismatches), and `git diff --name-only 3d05430f a743edeb` lists exactly the 24 `changed_paths`. All 24 paths lie under the Job's work scope `v12/python`.
- Worker Git hygiene: every `git stash` in the session was paired with `git stash pop` in the same command (`worker-timeline.txt`); the adapter's commit captured the working tree at the bound. No `git add`/`git commit` by the model.
- Retained originals untouched: evidence copies were made with `cp`; nothing under the instance was modified.

## 3. Completed versus unfinished (against NATIVE-TASK.txt)

| Deliverable | State in `a743edeb` |
|---|---|
| Versioned handoff/response document contract (`src/baton_v12/native_handoff.py`, +398) | present |
| Authority Work/Job messages and schema (`authority/messages.py` +488, `schema.py`, `api.py`, `core.py`, `session.py`) | present |
| Host continuation module (`job_manager/native_handoffs.py`, +1021), role contract/capability/template changes, `review_driver.py` yield branch, `review_cycles.py` response ending, `projection.py`, `job_control.py` continuation profile, `tools/stage_execution.py` seam (+231) | present, unverified |
| `tests.authority.test_work_messages` (new, 757 lines) | present; **63 tests OK** in isolation |
| `tests.job_manager.test_native_handoffs` (new, 1136 lines) | present but **unloadable: `SyntaxError: unterminated string literal` at line 497** (a quadruple-quote left by the rewrite cut off at 16:23:22). The worker's last own run of it (16:22, before the rewrite) was 45 tests, 3 failures, 5 errors (`scratch/nh.txt`). |
| `tests.tools.test_native_handoffs` (new) | **absent** |
| Registration of the new modules in `tools/parallel_test.py` ("register once") | **absent** (`tools/parallel_test.py` unchanged) |
| `v12/STACK.md` documentation | unchanged |
| Six-module verification argv | **never run by the worker**; `verification.txt`: "no verification was attempted" |
| Retained proposal, path inventory, candidate/base identities, test counts, limitations (the report) | not produced (the ending was the timeout, not a submission) |

Estimated: the source side of the slice is drafted end to end; the test side is roughly two thirds drafted; nothing is verified or reviewed.

## 4. Verification assessment on the isolated copy (prepared interpreter 3.13.7, roots `/var/tmp/baton-v12-handoffs-1/recovery`, TMPDIR `work/scratch/w383217/handoffs-recovery/tmp`)

| Run | Result | Log |
|---|---|---|
| The Job's exact six-module argv | **exit 1 at load**: `SyntaxError` in `tests/job_manager/test_native_handoffs.py:497`; zero tests ran | `six-module-verification.log` |
| `tests.authority.test_work_messages` | Ran 63, OK, 0 skipped | `module-work-messages.log` |
| `tests.job_manager.test_role_contract tests.manager.test_output tests.job_manager.test_job_control` (existing required modules on the candidate source) | Ran 180, OK, 0 skipped | `modules-existing-required.log` |
| `tests.tools.test_native_handoffs` | errors=1: `ModuleNotFoundError` (module does not exist) | `module-tools-native-handoffs.log` |
| Existing modules the candidate edited: `test_boundary test_dossier test_session test_review_driver test_templates test_role_capability` | Ran 445, OK, 0 skipped | `modules-existing-touched.log` |
| Registry: `tests.tools.test_parallel_runner` | errors=2: the AST scan trips on the same SyntaxError, and `test_every_v12_test_module_is_registered_exactly_once` refuses — the two new modules belong to no registry | `registry-parallel-runner.log` |
| `tests.job_manager.test_store_readonly tests.job_manager.test_tool` (the worker saw 3 failures on base inside the container) | 3 failures on the candidate copy **and the same 3 on the untouched host tree 3d05430f**: the refusal text truncates a long store path with `…` so `'jobs.sqlite3' not in …` — environmental (path length), pre-existing, not a candidate regression | `modules-store-readonly-tool.log`, `modules-store-readonly-tool-HOST-BASE.log` |
| `tests.tools.test_stage_execution` (the candidate changes `tools/stage_execution.py`; the worker saw 477 ran / 68 failures with the candidate and 7 of 11 failing on base in the container) | see `module-stage-execution.log` and §4a | `module-stage-execution.log` |
| Syntax of all 24 changed paths | 23 parse; 1 fails (above) | `py-compile.txt` |

Nothing here is acceptance: these are focused deterministic observations on a disposable copy, per `v12/python/TESTING.md`, run by module rather than through `just test-group` because the copy is outside the host checkout.

### 4a. stage-execution result

Filled in below after the run completed (see the row appended at the end of this file).

## 5. The supported recovery mechanism, and what it does not do

`manager … fresh-attempt --prior-job w385331-handoffs-1 --control … --authority … --instance …` (DESIGN REC-7, `job_manager/fresh_attempt.py`, QUICKSTART §"fresh-attempt") is the only supported retry in the installed bundle. Confirmed from the source:

- It admits a **new Job** `w385331-handoffs-1-retry-2` carrying the prior Job's **submitted specification unchanged**: same input digest `cc1b6096…`, policy `d8583ad9…`, statement, acceptance, scopes, verification argv, template and `documentation/1` limits (3600 s provider turn). Work `daec1190-W1` is reused while open; the deployment binding is added "like" the prior Job (same `line_declared_base 3d05430f`, same `impl-a`).
- The fresh worker starts from the nominated source line at **`3d05430f`**. The retained candidate `a743edeb` is **not** delivered: it stays frozen in custody as evidence linked to the prior attempt. There is no operand and no code path that mounts a prior proposal, restores a checkout or reuses the provider session (`provider_context: null`). "Fresh" means from known inputs (REC-5), not from the partial edits.
- Prerequisites are met right now: every prior stage settled (`exceptional` + `blocked` on a gate that can never open), runtime `destroyed`, cleanup `retained`, token `returned`, no cancellation fence, timing `trusted`.
- It takes the instance guard (`hold_manager_instance`), so it must run while the manager is **not serving** (`just stop` first), exactly like `create`.
- It is **refused once the Job's deadline expiry is journalled** (18:09:04Z) — a hard window for option A below.
- One successor per failure (`fresh_attempts_one_successor`).

The capability that would carry `a743edeb` forward natively — delivering a retained checkpoint back to the same admitted task — is precisely what W385331's first slice implements (`retained-continuation delivery`, DESIGN change in 3d05430f). It does not exist in the runtime executing this Job, as NATIVE-TASK.txt itself states.

## 6. Options and recommendation

**A. `fresh-attempt` now (supported, zero configuration).** Repeats the identical specification from `3d05430f` with the identical 3600 s bound. The only sample we have used 3597 s to draft 5 467 lines and never reached verification; nothing in a repeat changes that budget or the task. This is the blind rerun the coordinator excluded, and it must be admitted before 18:09Z. Not recommended on its own.

**B. Bounded direct continuation preserving the candidate (recommended).** Under the standing temporary direct development workflow (AGENTS.md, owner 2026-10-22), an implementer (codexpc as `baton.codx`, or whoever the coordinator assigns) continues from the digest-bound candidate in an isolated copy, with one bounded milestone: (1) repair `tests/job_manager/test_native_handoffs.py` from line 497 (finish the interrupted "ending harness" rewrite) and resolve its 8 open cases; (2) write `tests/tools/test_native_handoffs.py`; (3) register the three modules once in `tools/parallel_test.py` in their groups; (4) document the contract in `v12/STACK.md`; (5) run the six-module argv plus `just test-group` for the touched groups (authority, job_manager, tools) and `tests.tools.test_stage_execution`; (6) emit a digest-bound packet (patch from `3d05430f`, manifest, test ledger) for independent review by `baton.rvpc`, then human integration. Reconstruction for the implementer:

```
mkdir -p work/scratch/<work>/candidate && git archive 3d05430f | tar -x -C work/scratch/<work>/candidate
patch -p1 -d work/scratch/<work>/candidate < work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-recovery/proposal/change.patch
# verify: git hash-object of each of the 24 paths equals candidate-blobs.txt
```

The native Job `w385331-handoffs-1` stays `FAILED / report-and-hold` as the pilot's evidence; no fresh-attempt is admitted. This preserves the candidate, the evidence and the review boundary, needs no runtime capability that does not exist, and costs no second 3600 s provider turn.

**C. New native Job on a continuation line (owner decision, not recommended now).** Would require importing `a743edeb` (unverified, unreviewed, syntactically broken test) into the instance's source line (`repo/target.git` and `repo/source-impl-a`), a new Job binding whose `line_declared_base` differs from the one creation derives from existing bindings (`creation_ports._entry` carries the installed base; a different base means a bootstrap/config change), and a new task document. It is more mutation than the pilot has accepted for an unreviewed partial.

## 7. Exact operator commands

Option B needs no instance operation. If the owner nevertheless selects option A, run before 18:09Z:

```
cd /home/sl/baton-instances/native-handoffs-1
just --justfile /home/sl/baton-instances/native-handoffs-1/justfile stop
/home/sl/baton-instances/native-handoffs-1/distro/baton-v12-stack manager --store /home/sl/baton-instances/native-handoffs-1/db/jobs.sqlite3 --incarnation slaw-fresh-handoffs-1 --authority-uuid daec1190ac0c48329cf41937f7e2073d fresh-attempt --prior-job w385331-handoffs-1 --control /home/sl/baton-instances/native-handoffs-1/db/control.sqlite3 --authority /home/sl/baton-instances/native-handoffs-1/db/authority.sqlite3 --instance /home/sl/baton-instances/native-handoffs-1
just --justfile /home/sl/baton-instances/native-handoffs-1/justfile start
just --justfile /home/sl/baton-instances/native-handoffs-1/justfile monitor 10
```

Expected readback: fresh Job `w385331-handoffs-1-retry-2`, submission `sub-w385331-handoffs-1-retry-2`, same input/policy digests, Work `daec1190-W1` reused, a second `job_bindings` entry like the first; the prior Job unchanged. A refusal naming the expired deadline means the window closed.

To hold the instance without admitting anything (no action owed; `stop` only ends the two supervised processes, stores and evidence are retained):

```
just --justfile /home/sl/baton-instances/native-handoffs-1/justfile stop
```

## 8. Genuinely unresolved decision (owner)

Whether the first slice continues **natively** (A now, or C with an import of an unreviewed partial into the instance line) or **directly from the retained candidate** (B). The product cannot continue a retained partial natively today; B is the recommendation. A is time-boxed by the 18:09:04Z expiry fence. Everything else is routine coordination.

## 9. Separate finding

`FINDING-status-cause-unknown.md` — status/view/diagnostics print "cause unknown" although the sealed completion manifest and frozen result record a worker-declared `provider-failed/timeout`; prepared as independently assignable work for codexpc with code locations, evidence, direction and the exact `create` command.

## 10. Evidence index (this directory)

`proposal/` (byte copies of the four frozen files) and `proposal.sha256`; `bundle-verify.txt`; `candidate-commit.txt`; `candidate-blobs.txt`; `status-17h15.json`; `worker-output.json`; `provider.stdout.status.json`; `provider.stderr.status.json`; `native-retention.json`; `just-status.txt`; `view-job.txt`; `attempt-diagnostics.json`; `instance-listing.txt`; `worker-timeline.txt`; `py-compile.txt`; `six-module-verification.log`; `module-work-messages.log`; `modules-existing-required.log`; `module-tools-native-handoffs.log`; `modules-existing-touched.log`; `registry-parallel-runner.log`; `modules-store-readonly-tool.log`; `modules-store-readonly-tool-HOST-BASE.log`; `module-stage-execution.log`; `FINDING-status-cause-unknown.md`.

### 4a. stage-execution result (appended 2026-11-20T17:28Z)

`tests.tools.test_stage_execution` on the candidate copy: **Ran 477 tests in 305.075s, OK, 0 skipped, exit 0** (`module-stage-execution.log`). The worker's in-container run of the same module (`scratch/se.txt`: 477 ran, 68 failures, all in `TwoBoundJobsTraverseServingAndCorrection`) and its base comparison (`scratch/se_base.txt`: 7 of 11 `OrdinaryTerminalLifecycle` cases failing with the candidate stashed) show those failures were environmental inside the worker container, not a regression introduced by the candidate's `tools/stage_execution.py` change. Together with §4, every existing module touched or required by the Job passes on the host; the candidate's only verified defects are the unloadable `test_native_handoffs.py`, the absent `tests.tools.test_native_handoffs` and the missing registrations.
