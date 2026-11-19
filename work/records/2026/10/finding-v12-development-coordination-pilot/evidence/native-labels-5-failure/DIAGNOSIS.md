# native-labels-5 / w29401-labels-4: why the implementation stage is `exceptional` — read-only diagnosis (K, 2026-11-19)

Answers T321608 seq 385277 (`ASSIGNMENT-K.md`). No product edit, live provider call, test rerun, instance/store/config change, retry, cleanup or Git mutation. Evidence came from the owner's canonical snapshot, the instance's retained launch logs and custody under `/home/sl/baton-instances/native-labels-5/state`, the supported read-only `view`, and read-only Git queries (`GIT_OPTIONAL_LOCKS=0`) in the retained line checkout. No credential, raw SQLite or private provider transcript was read; the 2.1 MB session transcript under `launch/logs/<attempt>/native/` was only grepped for the one variable name named below.

Retained beside this file: `proposal/{change.patch,objects.bundle,result.json,verification.txt}` + `proposal.sha256` (byte copies of the sealed custody artifact), `custody-sealed.json`, `worker-output.json`, `provider-ending.json` (the provider's own result record), `provider.stderr.log`, the four `*.status.json`, `delivered-verifier-layout.json`, `task.json`, `verification-excerpt.txt`, `instance-listing.txt`, and the owner's `canonical-status*.json`.

## Verdict (confirmed)

**The execution succeeded and the candidate's own verification failed for an environment reason the task's argv did not provide for, not for a code reason.** The worker ran the provider turn to a clean end, committed and collected an 11-path candidate, ran the task's required verification argv inside the container, and that argv ended 1 because every `tests.tools.test_connected_creation` case refuses to start without a disk-backed test root outside the checkout. The worker reported this truthfully as disposition `unable` (recap `verification-failed: the task's own command ended 1`), the manager sealed that output, and the projection maps a frozen `unable` disposition to the stage state `exceptional`. Nothing in the manager ended this attempt; the worker ended itself.

The useful candidate is retained, intact and digest-bound (below). The failure boundary is **verification**, specifically the **test fixture's storage prerequisite inside the W325695 trusted verifier layout**; it is not execution, proposal collection, sealing or settlement.

## Timeline (host mtimes and store instants, UTC)

| when | what |
| --- | --- |
| 18:13:02.280 | Job `w29401-labels-4` created (`owner-create-labels-4`), both stages' episode 1 opened |
| 18:13:19.725 | implementation offer issued (`admit` performed); layout document materialized at `launch/verifier-layout/verifier-layout.json` (W325695 `/6` delivery, layout_digest `1423c3aa…`) |
| 18:13:24.800 | claim performed (`claimed`, policy generation 13) |
| 18:13:29.4 | inputs sealed (`task.json`, `input.json`, `assignment.json`); `.git/info/exclude` written in the line checkout (adapter `_reserve`) |
| 18:13:33.279 | provider started (`provider.stderr.log`: the CLI's "no stdin data received in 3s" notice only) |
| 18:35:41 | provider ran the candidate's own `tests.tools.test_connected_creation` with `BATON_V12_STACK_TEST_ROOT=/scratch` (fixture root `scratch/v12-w71917-j1m4t1kb` left on the attempt's disk-backed scratch) |
| 18:45:18.261 | last activity observed (2 184 534 bytes) |
| 18:45:49.5 | provider ended: `stop_reason end_turn`, `is_error false`, `num_turns 193`, 1 936 s, `terminal_reason completed` (`provider-ending.json`) |
| 18:45:49.9–51.1 | adapter ran the task's verification argv (`verification.stdout.log` 0 bytes; `verification.stderr.log` 89 679 bytes, `Ran 246 tests in 0.525s`, `FAILED (failures=30)`) |
| 18:45:51.0 | candidate committed on the line: `04648e1b` "baton candidate: w29401-labels-4" on base `d8f77700` |
| 18:45:51.3 | `output.json` written: `disposition: unable`, one `present` output `proposal` (4 entries, 160 442 bytes, tree `0a00bf5d…`) |
| 18:45:53.972 | manager sealed the result (`custody-sealed.json`, `output.freeze:01d7e589…`, `manager_observed_at`) into read-only custody under the line |
| 18:45:54.074 | attempt row: `execution_runtime: destroyed`, `cleanup: retained`; token returned (`completion: known true`, source `resource-token.returned`) |
| 18:45:54.098 | allocation `impl-a` released, `release_reason: cleanup-retained` |
| 18:50:36 | owner snapshot: implementation `exceptional`, review `blocked`, `attempt_diagnostics.cause: null` |

Container `9b5503a3…` is gone from the engine (runtime `destroyed`); no `docker ps -a` row exists for it, unlike native-labels-4's retained container. The exchange room (`launch/<attempt>/events/*`) was not retained either; the sealed custody record is the durable account of the ending.

## Confirmed chain (code, not inference)

1. **Worker ending.** `claude_agent._disposition` returns `verification-failed` when the provider is ok, a patch exists and `verification["status"] != 0` (`v12/worker/claude_agent.py:5363-5382`); the line profile commits regardless of disposition and publishes `unable` with the proposal present (`claude_agent.py:2255-2290` region, `result.json` `disposition: verification-failed`, `provider.status 0`, `verification.status 1`). `_verify` runs `task["verification"]` with `cwd=candidate` in the adapter-composed closed environment (`claude_agent.py:5140-5190`, `_closed_environment` 3357-3380): `HOME`, `PATH`, `TMPDIR`, `XDG_CACHE_HOME`, `PYTHONPYCACHEPREFIX` only; nothing else, and `os.environ` is never consulted.
2. **Where those roots are.** Under the selected trusted layout they are the four private tmpfs mounts `/run/baton-verifier/{home,tmp,cache,pycache}` (`source_boundary.VERIFIER_ROOTS`, `source_boundary.py:144-150`; `claude_agent.LAYOUT_ROOTS` 3426-3436; `delivered-verifier-layout.json` agrees). Under the legacy layout they are directories under `PRIVATE_ROOT = "/tmp"` (`claude_agent.py:207`), which is the 64 MiB tmpfs scratch (`source_boundary.SCRATCH_TARGET`, `:117-118`). **Either way the verifier's `TMPDIR` is memory-backed; the rootfs is read-only; `/var/tmp` is unwritable.** This is not new with W325695.
3. **What refused.** `tests/tools/test_stack._disk_root_outside_the_checkout` (`test_stack.py:2001-2062`), reached from `tests/tools/test_bootstrap.py:119` `setUp`, which every `test_connected_creation` case inherits: it tries `BATON_V12_STACK_TEST_ROOT` (unset), `/var/tmp` ("not a directory this process can write"), `~/.cache` = `/run/baton-verifier/home/.cache` (absent), `tempfile.gettempdir()` = `/run/baton-verifier/tmp` ("on a tmpfs filesystem, and the workspace boundary refuses a workspace on memory"), and by design **refuses rather than skips**, naming the variable to set. All 30 failures are this one sentence (`verification-excerpt.txt`); the other 216 cases (`test_work_command` 45, `test_creation` 92, `test_work_labels` 52, `test_work_label_exposure` 27) passed in the container.
4. **The product already provides the compliant place, and the task did not point at it.** W202663, owner 2026-09-21T05:53:07Z "I approve spare mount" (`work/records/2026/09/finding-v12-initial-claude-worker-pool/FINDING.md:2274-2278`): "Point `BATON_V12_STACK_TEST_ROOT` at the selected mount and verify the actual required tests against their path and filesystem checks." Implemented as the per-attempt disk-backed bind `oci._scratch_mount` → `/scratch` (`src/baton_v12/worker_manager/oci.py:257, 1084-1118`; "Job2 measured that this container offers no compliant place at all… This delivery is the correction"), allocated by `single_worker._attempt_scratch` on the workspace storage disk (`tools/single_worker.py:1879-1900`, delivered on the START path at `:2416`). This attempt had it: `state/workspaces/<attempt>/scratch` is on ext4 (`/dev/nvme0n1p2`) and the provider's own in-container run with `BATON_V12_STACK_TEST_ROOT=/scratch` created `scratch/v12-w71917-j1m4t1kb` there at 18:35:41 (the transcript names `STACK_TEST_ROOT=/scratch` 34 times). The Job's verification argv (`task.json`, from `manager create --verification …`) is `env PYTHONPATH=v12/python/src:v12/python python3 -m unittest -v …` with **no** `BATON_V12_STACK_TEST_ROOT`, so the adapter's run of it could not find real storage. The same argv was installed for native-labels-4's `w29401-labels-3`, which never reached verification.
5. **Manager side.** The sealed frozen output's `disposition: unable` is read by `projection._observed_state` → `_DISPOSITIONS["unable"] == "exceptional"` (`src/baton_v12/job_manager/projection.py:56-59, 183-192`). The review stage is `blocked` on that gate (`fresh_attempt._NEVER_OPENS`), so no native review of this candidate will happen inside this Job. `attempt_diagnostics.cause: null / unknown` is `failure_cause.attempt_failure_cause_of` saying exactly what it is built to say (`src/baton_v12/worker_manager/failure_cause.py:1197-1330`): no component of the manager ordered a cessation and no start/preparation failure exists, because none happened; the composition does not read the sealed result's disposition/recap, which is where the cause is. That is a reporting gap, not a defect in the ending (noted below, not K's path).
6. **Ruled out.** Not the layout pairing (the `/6` document was delivered and the adapter proved it: a provider turn ran for 32 minutes; the labels-4 refusal fires before any provider work). Not the route/claim (performed, generation 1). Not the credential (provider authenticated and completed 193 turns). Not the provider (`is_error false`, `end_turn`). Not a deadline (stage deadline 19:33:19Z, Job deadline 20:59:02Z, neither reached; `fence: null`). Not sealing/custody (freeze operation committed, custody read-only `0555/0444`, digests verified below). Not capacity/cleanup (token returned, allocation released, evidence retained).

## Retained candidate: status and integrity

- Custody: `state/workspaces/.baton-review-lines/line-f5caa59d…/custody/<attempt>/proposal/` (dir `0555`, files `0444`): `change.patch` 120 484 B `f614bf16…`, `objects.bundle` 37 090 B `490c75ef…`, `result.json` 2 103 B `bbef6d49…`, `verification.txt` 765 B `d5a11979…`; recomputed `contracts.manifest.digest(entries)` == recorded tree digest `sha256:0a00bf5d…` == `sealed.json` == owner snapshot `artifacts[0].content_digest`. Byte copies and `proposal.sha256` are beside this file.
- Line: checkout HEAD `04648e1b21b98aa0b3efad1b57fc3264c4a566ba` ("baton candidate: w29401-labels-4", author "Baton worker", 18:45:51Z) on `d8f77700` (the declared base and the instance's canonical target); worktree clean (`git status --porcelain --ignored` shows only the adapter's excluded `output.json`, `proposal/` and `__pycache__`). `git bundle verify` of `objects.bundle`: okay, carries `04648e1b HEAD`, requires `d8f77700`. `git diff d8f77700 04648e1b` sha256 == `change.patch` sha256 (`f614bf16…`): the patch is exactly the committed delta.
- Shape (`result.json`, `provider-ending.json`): 11 changed paths, 2 094 insertions / 21 deletions — new `tools/work_command.py` (365 lines) and `tests/tools/test_work_command.py` (45 cases); `stack_command.py` (`work` in `COMMANDS`), `job_manager.py` (`create --label`), `job_manager/creation.py` (labels normalized into the request digest; reused Work refuses relabelling), `fresh_attempt_ports.py` (`create_work(..., labels=())`), `parallel_test.py` (registers `tests.tools.test_work_command`), `v12/STACK.md` (`## work` + `create --label`), and added cases in `test_creation` (+14), `test_connected_creation` (+6, class `CreateTimeWorkLabelsThroughTheRealCommand`), `test_work_label_exposure` (+23). The provider's own report says 246 tests OK with `BATON_V12_STACK_TEST_ROOT=/scratch` and names two things for review: it widened the `test_no_broad_except_stands_between_a_fault_and_its_caller` allow-list to include `Refusal` (an existing-invariant change), and it put the documentation in `v12/STACK.md` because `v12/TEMPLATE-JOBS.md` (in scope) does not exist. **These are the provider's claims, not verified here**; the acceptance says the operator's own rerun from the collected tree, not the worker's record, is what is trusted. The `parallel_test.py` edit touches a codexpc-owned host path; that is an integration-time ownership question, not a candidate defect.

## Smallest correction and focused verification plan

**No product edit is required to make this Job's verification runnable.** The correction is in the Job's verification argv: name the delivered scratch root, exactly as the W202663 ruling says, with the `env` words the argv already uses:

```
env BATON_V12_STACK_TEST_ROOT=/scratch BATON_V12_DISK_ROOT=/scratch PYTHONPATH=v12/python/src:v12/python python3 -m unittest -v tests.tools.test_work_command tests.job_manager.test_creation tests.tools.test_connected_creation tests.authority.test_work_labels tests.authority.test_work_label_exposure
```

`BATON_V12_STACK_TEST_ROOT=/scratch` is the proven half (the provider's in-container run); `BATON_V12_DISK_ROOT=/scratch` is TESTING.md's companion so `tests.manager.disk_roots` does not fall back to the checkout for the manager suites — harmless here, optional. `/scratch` is a contract constant (`oci.SCRATCH_TARGET`), bind-mounted writable on the START path for every attempt; it is 552 GB of real storage shared per attempt directory, not the 16 MiB tmpfs `TMPDIR`.

Verification that the correction is sufficient, deterministic and offline, for whoever the owner assigns: on the host, from the retained bundle (`git -C <disposable clone of the instance target> fetch <objects.bundle> HEAD`, or `git apply --check change.patch` on a `d8f77700` export), run that exact argv with the two variables pointing at a disk-backed directory and confirm `Ran 246 … OK`; and run the same argv **without** the variables on a host whose `TMPDIR` is tmpfs to confirm the 30 refusals reproduce. That is the minimal reproduction; no container is needed because step 3 above is fixture logic, not container logic.

Two product-side items worth the owner's classification, **not required for recovery and not K's paths**:

- `attempt_diagnostics` reports `cause: null / unknown` for a worker that ended itself with a sealed `unable` result and a `verification-failed` recap; the sealed result is the cause and the composition never reads it. Status UX (W385227/W385263, codexpc). A one-line `unable: verification-failed …` beside `exceptional` would have made this snapshot self-explaining.
- Whether the adapter's closed verification environment should itself export the attempt scratch (e.g. carry `/scratch` into the verifier's environment under a product name) so operators need not know a container path. This is a layering decision (the product would be naming a test-suite variable, or the fixtures would be naming a product mount); the W202663 ruling chose "point the variable at the mount", which the argv correction above honours.

## Supported recovery (owner selection; nothing executed)

Facts that bound the choice:

- `fresh-attempt --prior-job w29401-labels-4` carries "its submitted specification, limits and scope … forward unchanged" (`tools/job_manager.py:1330-1333`), i.e. the same verification argv, so it would repeat this exact failure deterministically. **Not recommended.** It is also refused after the Job's fence.
- Deadlines: the implementation stage is *over* (runtime ceased), so its 19:33:19Z stage deadline no longer counts (`cancellation.over`, `job_control.closing(finished=…)`); the review stage never started (origin null). The **Job deadline 20:59:02Z** will be journalled as the fence by `_control` at the first tick after it, and the cancellation pass will then settle the Job as native-labels-4's did (implementation already ceased, review `retired-before-admission`, `shutdown: complete`). Nothing is running; the retained candidate, custody and logs are not touched by that. No `cancel-job` is needed; letting the deadline settle it is the supported path and the record stays "verification-failed, candidate retained".
- The installed bundle (`d8f77700`, runtime `59df90fa…`) is correct; the layout pairing worked. No rebuild, reinstall or new instance is needed.

**Recommended:** create a **new Job on the running native-labels-5 instance** with the corrected argv, same statement and scopes, a new `--task` name, and let it run end to end (implementation + native review), which is what the pilot is measuring. The provider will redo the slice from `d8f77700` (this one cost 32 min / $25.32); the retained `04648e1b` candidate stays as comparison evidence and can be host-reviewed in parallel if the owner wants to salvage it through the human-plus-agent integration default instead.

Exact owner commands (the instance stays up; `create` is a read-only-control creation that queues until the serving manager's next tick):

```sh
DEST=/home/sl/baton-instances/native-labels-5
STMT=/home/sl/src/baton/work/records/2026/10/finding-v12-development-coordination-pilot/config/labels-job.txt
"$DEST/distro/baton-v12-stack" manager create \
  --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
  --task w29401-labels-cli-5 --job-id w29401-labels-5 --statement "$(cat "$STMT")" \
  --acceptance "Work-label CLI and create-time labels satisfy the description and preserve existing authority semantics." \
  --acceptance "Focused tests prove authorization, replay, normalization, filtering and compatibility without required skips." \
  --acceptance "Independent review evaluates the retained candidate; human integration remains required." \
  --work-scope v12/python --work-scope v12/STACK.md --work-scope v12/TEMPLATE-JOBS.md \
  --test-scope v12/python/tests --test-scope v12/python/tools/parallel_test.py \
  --control-profile documentation/1 \
  --verification env --verification BATON_V12_STACK_TEST_ROOT=/scratch --verification BATON_V12_DISK_ROOT=/scratch \
  --verification PYTHONPATH=v12/python/src:v12/python --verification python3 --verification=-m --verification unittest --verification=-v \
  --verification tests.tools.test_work_command --verification tests.job_manager.test_creation --verification tests.tools.test_connected_creation \
  --verification tests.authority.test_work_labels --verification tests.authority.test_work_label_exposure
```

Prerequisites and expectations: the previous Job's create used the same three acceptance criteria and scopes (`task.json` here reproduces them; `--source` was omitted, so the installed source is used); `--task` must differ from `w29401-labels-4`'s so a new Job id is derived (the previous task name is in the dossier's create record, which K did not find verbatim — confirm against the owner's shell history before running). Expected: the answer names a new Job id, the derived Work `8148af5e-W1` reused (open), and the next `status` shows it `offered` then `claimed`/`running` within a tick. If the owner prefers to remove `v12/TEMPLATE-JOBS.md` from `--work-scope` (it does not exist in the tree), that is a statement change, not a verification change. Then observe with `just --justfile "$DEST/justfile" status` / `monitor`. Separate approval boundary: creating this Job is a live provider run (one model turn); it is the owner's selection, not K's.

## What this does not claim

- That the candidate is acceptable: its 246-OK claim is the provider's own in-container run, unverified by K; a host rerun from the bundle is the acceptance.
- That the layout correction is proved live end to end: it is proved to the point of a 32-minute provider turn and a verification run under the delivered layout, which is further than any prior native attempt reached; the kernel-mount half of `_layout_preflight` ran in the container (the provider turn could not have started otherwise) but no artifact here records its proof document.
- Why the exchange room was not retained for a completed attempt while native-labels-4 retained its faulted one; observed, not investigated (outside the assignment).

## Correction 2026-11-19T21:24Z — recovery command withdrawn; retained candidate verified on the host (K, answering T321608 seq 385287)

Append-only. The sections above are left as written; where this section disagrees with them, this section is current.

### 1. The "create on the running instance" recommendation was wrong and is withdrawn

The review (`review-2026-11-19T21-17-15Z.md`) is right. `tools/job_manager.py::_create` composes `creation_ports.InstanceOwnership` (re-exported from `tools/fresh_attempt_ports.py:100`), and `creation.create_template_job` enters `ownership.held()` at `src/baton_v12/job_manager/creation.py:225` before it derives or writes anything. `InstanceOwnership.held` (`fresh_attempt_ports.py:145-165`) is `workspaces.borrow_manager_instance`, which calls `workspaces.hold_manager_instance` (`worker_manager/workspaces.py:1074`): an exclusive non-blocking `flock` on the instance guard beside the workspace root. The serving manager (pid 2131939) holds that very guard for its lifetime, so a `create` against this instance while it serves is **denied** with "another manager is already active for workspace … stop the active one first" (`workspaces.py:1138`), not queued. Opening the control store read-only changes nothing about this: the guard is a file lock beside the workspace root, not a row in the store (the `fresh-attempt` docstring at `job_manager.py:770-774` says exactly this). The in-process borrow-count cache only serves a guard *this process* already holds. The product's own proof of two creations on one instance (`tests/tools/test_connected_creation.py:612-800`, `test_two_defined_jobs_run_on_one_product_configured_instance`) creates both Jobs on an instance nobody is serving; and native-labels-5 itself was created at 18:13:02Z and its manager started at 18:13:19Z (`ps lstart` of pid 2131939), i.e. create preceded start. **Do not run the command printed in "Supported recovery" above as written.** The supported order is unchanged: `stop` → `manager … create` → `start` (PROGRESS.md:9 records the same path at HEAD).

That command also omitted the manager's required global operands. The installed help (`host-verification/installed-manager-help.txt`) makes `--store`, `--incarnation` and `--authority-uuid` required on `manager` itself, ahead of the verb; `create`'s own required operands are `--instance --control --authority --task --statement --acceptance --work-scope`, with `--test-scope --job-id --submission-id --verification --control-profile --template --source --route --provider-turn-seconds --verification-command-seconds` optional (`installed-create-help.txt`). `creation_ports.agreeing` (`job_manager.py:847-849`) holds `--store`, `--control` and `--authority` to the paths the instance's own identity names, so they must be this instance's exact files. The Job id derives as `job-<task>` when `--job-id` is omitted (`test_connected_creation.py:527-532`: task `cli-first` → `job-cli-first`), so an explicit `--job-id` is needed to keep the `w29401-labels-N` naming.

### 2. State now: the Job deadline fenced and settled it, as predicted

`host-verification/status-after-fence.txt`, `view-after-fence.txt`, `canonical-status-after-fence.json` (read-only `status`/`view` and a byte copy of `state/status.json`, 21:20Z): `control.fence {trigger: job-deadline, requested_at 2026-11-19T20:59:02.280Z, operation_id job.expire:w29401-labels-4}`; `cancellation.shutdown: complete`; Job `w29401-labels-4: FAILED`, implementation `exceptional; cause unknown`, review `blocked`. Manager 2131939 and publisher 2131940 still serving, snapshot fresh. No cancel-job was needed and none was run. The implementation line is still clean (`git status --porcelain` empty under `GIT_OPTIONAL_LOCKS=0`); custody untouched.

### 3. Retained candidate verified on the host, offline (the reviewer's continuation)

Method (`host-verification/provenance.txt`, `run-header.txt`): the retained line checkout's HEAD is `04648e1b21b98aa0b3efad1b57fc3264c4a566ba`; `git archive` of that commit (read-only; no clone, fetch, apply or index operation) was extracted into the owned scratch `work/scratch/w383217/labels5-host-verification/export` (1.2 GB, tree listing digest `829c54e6…`). Every one of the 11 paths `git diff --name-only d8f77700 04648e1b` names has the same sha256 in the export as `git show 04648e1b:<path>` (11 `match`, 0 mismatch). Both storage variables name a real ext4 directory outside the tree (`…/labels5-host-verification/roots`, `/dev/nvme0n1p2`). The interpreter is the prepared one `tools.environment interpreter` resolves (`/home/sl/.local/state/baton-v12-venv/bin/python`, 3.13.7), run from the export root with the task's own `PYTHONPATH=v12/python/src:v12/python` and the task's own five modules, nothing else.

Result (`host-verification/unittest-04648e1b-host.log`, `per-module.txt`): **Ran 246 tests in 3.135s — OK**, exit 0, elapsed 4 s wall, **0 skipped, 0 errors, 0 failures** (an `OK` with skips prints `OK (skipped=N)`; none). Per module, run separately with the same environment: `test_work_command` 45 OK, `test_creation` 92 OK, `test_connected_creation` 30 OK, `test_work_labels` 52 OK, `test_work_label_exposure` 27 OK = 246. The 30 cases that refused in the container (`verification-excerpt.txt`) are exactly the 30 `test_connected_creation` cases that pass here with the root named. This matches the provider's in-container claim (246 OK with `BATON_V12_STACK_TEST_ROOT=/scratch`), now independently established rather than provider-reported.

What this is and is not: it is verification evidence that the retained candidate's own required argv passes under a compliant environment, which closes the "cause" half of the diagnosis. It is **not** independent code review of the 11 paths, not native reviewer acceptance, and not a packaged-CLI gate; the provider's other claims (widened `test_no_broad_except…` allow-list, `v12/STACK.md` as the documentation target, the `parallel_test.py` edit on a codexpc-owned path) are still unreviewed.

Negative reproduction, corrected: the plan above said "run the same argv without the variables on a host whose `TMPDIR` is tmpfs". That is not sufficient on this host: `_disk_root_outside_the_checkout` tries `/var/tmp` before `TMPDIR`, and `/var/tmp` is writable here, so the fixture would simply use it. The container condition (read-only rootfs ⇒ `/var/tmp` unwritable, `~/.cache` absent, tmpfs `TMPDIR`) was not reproduced on the host and is not claimed; the container's own 30 refusals (`verification-excerpt.txt`, `proposal/verification.txt`) remain the evidence for the negative half.

### 4. Supported recovery choices, validated and not executed

The choices are different in kind and the owner selects one:

**(A) Preserve and review this candidate; no new live run.** `04648e1b` is intact (digest-bound custody, host run 246 OK), and the human-plus-agent integration default applies. Review material is already on the host: `proposal/change.patch` (== `git diff d8f77700 04648e1b`), the export above, and this evidence. The native review stage cannot be driven for it on this instance (the Job is fenced and settled), so acceptance would be a host review recorded in the dossier, not a native reviewer result. Cost: review time only. This is what preserves the 32-minute / $25.32 implementation.

**(B) New Job with the corrected argv; redoes the implementation end to end.** This is a new provider turn from `d8f77700` plus a native review turn, which is what the pilot measures but not what salvages the existing candidate. Supported sequence, all three commands to be run by the owner in this order, nothing between them:

```sh
DEST=/home/sl/baton-instances/native-labels-5
STMT=/home/sl/src/baton/work/records/2026/10/finding-v12-development-coordination-pilot/config/labels-job.txt
BIN="$DEST/distro/baton-v12-stack"

# 1. release the instance guard: stops only the supervisor processes this deployment owns
"$BIN" stop --instance "$DEST/instance.json"
"$BIN" status --instance "$DEST/instance.json"      # expect: no manager/publisher process

# 2. create, with the manager's required global operands and the instance's exact stores
"$BIN" manager --store "$DEST/db/jobs.sqlite3" --incarnation slaw-create-labels-5 \
  --authority-uuid 8148af5e916148d091a9ac6ae0cc3f3c \
  create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
  --task w29401-labels-5 --job-id w29401-labels-5 \
  --statement "$(cat "$STMT")" \
  --acceptance "Work-label CLI and create-time labels satisfy the description and preserve existing authority semantics." \
  --acceptance "Focused tests prove authorization, replay, normalization, filtering and compatibility without required skips." \
  --acceptance "Independent review evaluates the retained candidate; human integration remains required." \
  --work-scope v12/python --work-scope v12/STACK.md --work-scope v12/TEMPLATE-JOBS.md \
  --test-scope v12/python/tests --test-scope v12/python/tools/parallel_test.py \
  --control-profile documentation/1 \
  --verification env --verification BATON_V12_STACK_TEST_ROOT=/scratch --verification BATON_V12_DISK_ROOT=/scratch \
  --verification PYTHONPATH=v12/python/src:v12/python --verification python3 --verification=-m --verification unittest --verification=-v \
  --verification tests.tools.test_work_command --verification tests.job_manager.test_creation --verification tests.tools.test_connected_creation \
  --verification tests.authority.test_work_labels --verification tests.authority.test_work_label_exposure

# 3. serve again (restart recovery; the fenced w29401-labels-4 stays settled)
"$BIN" start --instance "$DEST/instance.json"
"$BIN" status --instance "$DEST/instance.json"      # expect: 2 Jobs observed, w29401-labels-5 queued/offered
```

Operand provenance: `--store`/`--authority-uuid`/`--control`/`--authority` are the values `instance.json` records (`job_store`, `authority_uuid`, `control_store`, and `db/authority.sqlite3` under `destination`); the statement, three acceptance criteria, scopes and profile are the ones `task.json` carries for labels-4 (`config/labels-job.txt` is the statement source), so only the argv differs; `--verification=-m`/`=-v` follow the help's rule for dash-leading words; `--incarnation` is any operator-chosen name (the quickstart's `<yours>`). Expected outcome: `create` answers a bound, servable Job (replay-safe: the same request again answers the same Job; a changed request under the same `--job-id` refuses). The `v12/TEMPLATE-JOBS.md` work-scope path does not exist in the tree (the provider wrote its docs into `v12/STACK.md`); keeping it is harmless and keeps the request comparable to labels-4; dropping it is the owner's choice. Prerequisites: the owner's credential slot and image are unchanged; nothing else is running on the instance (`status` shows 2 open episodes with 1 recorded runtime, which is the settled labels-4 record, not a live container: `docker ps -a` showed none earlier). Boundaries: this is one live provider turn plus a native review turn (owner selection); it is not integration and does not touch `04648e1b`.

**(C) `fresh-attempt --prior-job w29401-labels-4`.** Not a choice: refused after the fence, and it would carry the unchanged argv anyway.

K's recommendation: **(A) first** — it costs no live run and the product question (does the candidate's argv pass under a compliant root?) is now answered on the host; run **(B)** only if the owner wants the end-to-end native pipeline measurement that the pilot exists for, in which case the stop/create/start sequence above is the supported path and the earlier one-command recommendation is void.

### 5. Reporting gap, recorded for classification only

Unchanged from above and not expanded here: `attempt_diagnostics.cause` and `status` print `cause unknown` for a worker that ended itself with a sealed `unable`/`verification-failed` result; the sealed disposition is the cause and no composition reads it. Codexpc owns W385227/W385263; nothing in those paths was touched.
