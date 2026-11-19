# Checkpoint K r2 — labels run: one-time setup, ordinary kickoff, gaps, decisions (read-only)

Answers review-2026-11-19T01-39-09Z (T321608 seq 385173). Revises CHECKPOINT-K-LABELS-20261119.md §2–§5; §1's payload stands unless noted. HEAD `f34e1576`, clean under `v12/`; no v12 stack process is running on this host; nothing built, installed, executed or mutated; no claim held.

## A. Chosen labels scope (unchanged, one sentence per boundary)

Native v12 implements and independently reviews "W29401 CLI exposure, slice 1": a new bundled `work` subcommand (`label-work`, `unlabel-work`, `labels`, `list --label…/--without-label…`, AND + none-of, OR-like and `key=value` forms refused, dispatch by command never by spelling) over the existing Authority label API, plus `manager create --label` applied only when the Work is created (existing Work refuses by name). Not in scope: `bootstrap --label`, monitor/view columns, TUI (W29408), tags. The Job's `scope.work` and `scope.tests` are the files/tests named in the r1 checkpoint §1. K never implements labels interactively.

## B. True one-time setup (reusable; once per host, not per Job)

Technical basis for the artifact choice, verified against bytes rather than old hashes: the qualified worker image `sha256:47e73383…` was bound (W325695 `preparation-376414/BUILD-INPUTS.json`) to ten inputs; at `f34e1576` **five of the ten differ** (`worker/Dockerfile.claude`, `worker/baton_worker.py`, `worker/claude_agent.py`, `worker/dogfood_entry.py`, `python/src/baton_v12/verification_context.py`; the other five are byte-identical). The image used by W384870's suite (`sha256:9b8c9882…`) is the W32577 reference test image, not a build of these inputs. So a compatibility claim for `47e73383` has no technical evidence and is not proposed; **the shortest supported path is one worker image build from the same `f34e1576` export that the host is built from**, with its ten-input binding recorded (the `BUILD-INPUTS.json` form) for independent review. The host side needs `f34e1576` for installed cancellation and finite control, which no existing bundle has (installed stamps `614668e0`, `18e771f0`).

One bounded, reviewable setup selection (one owner decision, four retained steps, each refusing rather than repairing):

1. Export `f34e1576` from Git objects to a fresh directory and record its file SHA256 inventory (the `check-377930.py` form; read-only on the checkout).
2. Host: `just --justfile <export>/v12/justfile build <export>/host-build` (900 s timeout, retained output); bind the one-folder distribution's identity/hash inventory.
3. Worker: `<prepared python> -m tools.worker_image --tag baton-v12-worker:f34e1576 --dockerfile <export>/v12/worker/Dockerfile.claude --context <export>/v12` (engine call; one-time), record the immutable image digest and the ten-input binding against the export.
4. Install once at a persistent destination `/home/sl/baton-instances/native-labels-1` with one `stack-bootstrap/1` inputs document (image digest from step 3, docker-single-worker adapter, fresh-context `/1` roles `impl-native-labels` / `review-native-labels` with distinct private roots, credential slot `claude`/`operator-file`/`w202663-development`, retention `retain`, receipt participants, and the deployment's installed task document whose `verification` argv is fixed once for coding Jobs — see E): `just --justfile <export>/v12/justfile bootstrap <inputs.json> /home/sl/baton-instances/native-labels-1 <host-build/out/baton-v12-stack>`; then `"$DEST/distro/baton-v12-stack" identity` and read `AUTHORITY_UUID` from `$DEST/authority-identity.json`. The installer hazard READINESS-377930 named (`bootstrap._remove_if_still_ours` + `rmtree`) is absent at HEAD; W376246/W376955/W376956 are closed satisfying and their correction entered with `84f66f43` (by inspection; the fresh-install acceptance evidence is theirs, not re-proven here).

Safety/operational boundaries inside that one selection: step 1–2 touch no engine; step 3 is the only engine call and builds only; step 4 writes only under the fresh destination and refuses an occupied path; no provider call, no Job, no credential value emitted (the resolver check prints a marker only). Review packet before install: export inventory, host identity, image digest + BUILD-INPUTS, inputs.json. This destination is then the persistent instance for the labels Job and for later Jobs; no per-Job bootstrap, provisioning or fresh install.

## C. Ordinary kickoff on the persistent instance (literal supported commands at `f34e1576`)

Inputs an operator supplies per Job are operands only: task id, statement, acceptance lines, work/test scope paths, profile. Everything else is the installed deployment's. With `DEST=/home/sl/baton-instances/native-labels-1`, `STACK=$DEST/distro/baton-v12-stack`, `AUTHORITY_UUID` from the install:

```sh
just --justfile $DEST/justfile stop            # only if a manager is serving; see the practical limit below
"$STACK" manager --store $DEST/db/jobs.sqlite3 --incarnation labels-create-1 --authority-uuid $AUTHORITY_UUID \
  create --instance $DEST --control $DEST/db/control.sqlite3 --authority $DEST/db/authority.sqlite3 \
  --task w29401-labels-cli-1 --statement "$(cat task-statement.txt)" \
  --acceptance "create accepts zero, one and repeated labels; normalized duplicates consume no cardinality" \
  --acceptance "label-work/unlabel-work: add, remove, terminal Work, unauthorized, exact retry, convergent changed:false, conflicting operation reuse, stable errors" \
  --acceptance "list: repeated --label is all-of, --without-label is none-of, they compose; OR-like and key=value forms refuse explicitly" \
  --acceptance "work verbs dispatch only Authority Work labels; Thread label/unlabel and OCI runtime labels are unreachable from them" \
  --acceptance "unfiltered list, existing verbs, help and output versions unchanged except additive fields" \
  --work-scope v12/python/tools/work_command.py --work-scope v12/python/tools/stack_command.py \
  --work-scope v12/python/src/baton_v12/job_manager/creation.py --work-scope v12/python/tools/job_manager.py \
  --test-scope v12/python/tests/tools/test_work_command.py --test-scope v12/python/tests/tools/test_stack.py \
  --test-scope v12/python/tests/tools/test_packaged_creation.py --test-scope v12/python/tests/tools/test_connected_creation.py \
  --test-scope v12/python/tools/parallel_test.py \
  --control-profile documentation/1 --job-id w29401-labels-1 --submission-id w29401-labels-1-1
just --justfile $DEST/justfile start
just --justfile $DEST/justfile status; just --justfile $DEST/justfile monitor 3
"$STACK" view --status $DEST/state/status.json --job w29401-labels-1
```

`task-statement.txt` is the §A slice in prose (the task's instructions; `tools/job_task.py` substitutes exactly `task_id` and `instructions` into the installed task document). Stop/observe: `"$STACK" manager cancel-job --instance $DEST/instance.json --job w29401-labels-1 --reason "<why>"`, `cancel-status`, `just stop` only after cessation is accounted; failed-attempt settlement through the installed `manager settlement-preview/settle-stopped/settlement-status` forms. Closure after human acceptance: `"$STACK" disposition close … --outcome satisfying --proposal … --expect-candidate-digest …`.

**Practical limit, stated plainly:** `manager create` takes `workspaces.hold_manager_instance`, the same file lock a serving manager holds, and a duplicate holder is refused (`tools/job_manager.py` 760–790; `workspaces.py` 1075). So on a serving instance the routine today is `stop → create → start`; a Job created while serving is the accepted outcome of W375518 (serving admission and instance-addressed commands; `block`, route baton.codx, behind W375517 ← W371295). That is the one existing correction outcome this payload touches; it is not a gate for the first run, and the stop/create/start interval is counted inside the measured startup (D).

## D. Focused verification and timing evidence plan

- Payload acceptance (inside the Job): the implementation attempt's focused tests over the named modules; the review attempt's independent verdict against the five acceptance lines. After human import: `just test-one tests.tools.test_work_command tests.tools.test_stack tests.tools.test_packaged_creation tests.tools.test_connected_creation tests.authority.test_work_label_exposure tests.authority.test_work_labels`, then `just test-group tools-pure` and `just test-group job_manager` (creation owner touched); no `test-all`.
- Deployment verification argv installed once for coding Jobs (the worker's `verification` runs inside the container under the 900 s ceiling): recommend `just test-group tools-pure` (measured 151–156 s on this host) followed by `just test-group job_manager` (16 s); both within 900 s, both the TESTING.md cadence, no per-Job scripting.
- Whole-path startup measurement (OBS-0/OBS-0a), pinned endpoints, operator wall clock: **T0** = the instant the operator issues the first routine command (`stop` if serving, else `create`) with the finished operands in hand, recorded with `date -u +%FT%T.%3NZ` immediately before it; **T1** = the first attributable substantive agent activity: the earliest provider-turn activity instant the snapshot/`view` reports for the implementation attempt (W61599 trusted activity source), cross-checked against the retained provider log's first byte timestamp through `logs … locators`. Report T1−T0 and every intermediate durable instant between them (`submissions.recorded_at`, admit `settled_at`, launch `recorded_at`, `admitted_at` in status, first activity). Dispatch/receipt timestamps alone are not the endpoint; if T1 cannot be read, the interval is reported unknown, never estimated. The 60 s bound is reported as met or missed; a miss is W371075/W375519 evidence, not a reason to hand-tune the run.
- Control/cancellation evidence: the Job's `control` report (profile, elapsed, deadlines, timing) and `cancel-status` are retained with the snapshot; the 120 s shutdown bound is only exercised if a stop is actually ordered.

## E. Concrete missing blockers for THIS payload (and what is not one)

1. **Artifacts** (B): no host bundle or worker image at `f34e1576` exists; one setup selection produces both. Blocker until built and reviewed; not a backlog gate.
2. **Create while serving** (C): practical limit, routine is stop/create/start; W375518 owns the correction; not a gate.
3. **Coding verification argv**: the installed task document's `verification` is per deployment, so the coding deployment installs its own (D recommendation). Decision at B step 4, no code.
4. Not blockers: W371296 `/2` qualification (run under `/1` with explicit roles, as the documentation plan did), W371295 (the `role_contract.py:510` import is not present at HEAD by inspection), W375516/W375517/W375519 (their outcomes are not required for one input-only create on a fresh persistent instance), W321776, W44342.

## F. Profile interpretation and provenance (decisions bundled, not implemented)

- `documentation/1` can be selected for this run without any code change: `--control-profile documentation/1` journals its numbers (0 rounds, 4800 s/stage, 9960 s/Job, 3600/900 s); nothing in `job_control`, `templates` or the worker reads the task kind. The name is the only mismatch. Options: (a) the owner records that `documentation/1` is the selected finite control for this coding run (interpretation, zero code; the r2 commands above assume it); (b) an additive alias/profile `coding/1` with identical numbers, as a later bounded change — never by the labels Job and not before this run. Recommend (a).
- Provenance versus execution identity: v11 `W29401` stays `parked` as the backlog/provenance record (no unpark, transfer or duplicate authority); the native Job runs under its own Work in the instance Authority (`<AUTHORITY_UUID>-W1`, created by `manager create`), which is the one execution authority for the run, bound to the repository dossier path `work/records/2026/08/finding-v12-work-tags/findings/finding-v12-work-label-protocol-cli` through `"$STACK" record bind …` as the pilot bound its Work. Evidence mapping afterwards: the native authority UUID, Work, Job, submission, attempt ids, candidate digest and the review verdict are recorded in W29401's PROGRESS/FINDING by the human/K under a v11 claim or manual assignment; human import, focused tests and Git checkpoint follow; then the owner disposes W29401 (close if the remaining parked exposure is accepted as out of scope, else keep parked with the delivered part recorded). A v12 Job is never bound to a v11 assignment as its execution authority.

## G. Remaining owner selections (only these)

1. The one setup/run selection of B (export → host build → worker image → install), with its review packet.
2. Profile interpretation F(a) or F(b).
3. The coding deployment's installed verification argv (D recommendation) and the two role identities/private roots.
4. After the run: human import/acceptance and the W29401 disposition.

No new Work, edge, claim or product change results from this checkpoint. Last positions read: T321608 through seq 385173; review-2026-11-19T01-39-09Z.md; W371075/W375516–W375519 details at snapshot 385173.
