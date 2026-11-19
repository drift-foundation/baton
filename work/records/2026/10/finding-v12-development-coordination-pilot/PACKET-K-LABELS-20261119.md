# Packet K — native labels Job: one-time setup, routine kickoff, verification, timing (prepared, not executed)

Answers review-2026-11-19T01-45-32Z (T321608 seq 385175). Supersedes the command sections of CHECKPOINT-K-LABELS-20261119-r2.md; §A scope stands. HEAD `f34e1576`, clean under `v12/`; no v12 stack running; nothing built, installed, executed or mutated; no claim held. Every command below is a prepared form for ONE owner setup/run selection (§G); none is authorized by this file.

## 1. Fixed values (no placeholders)

```sh
REPO=/home/sl/src/baton
BASE=f34e1576                                   # full: git -C $REPO rev-parse f34e1576
EXPORT=/home/sl/baton-instances/native-labels-source-f34e1576
BUILD=/home/sl/baton-instances/native-labels-build
DISTRO=$BUILD/out/baton-v12-stack
RECEIPT=/home/sl/baton-instances/native-labels-image-receipt
DEST=/home/sl/baton-instances/native-labels-1
MINT=/home/sl/baton-instances/native-labels-1-mint.json
COMPOSE=/home/sl/baton-instances/native-labels-1-compose
PHASE2=/home/sl/baton-instances/native-labels-1-phase2.json
STACK=$DEST/distro/baton-v12-stack
TASK_ID=w29401-labels-cli; JOB_ID=w29401-labels-1; SUBMISSION_ID=w29401-labels-1-1
SETUP=$REPO/work/records/2026/10/finding-v12-development-coordination-pilot/setup-native-labels   # the re-pinned one-time composition helper (reviewed with the artifacts)
```
All destinations are fresh, absolute, outside the checkout and outside every retained instance; each creating step refuses an occupied path. Roles (routine configuration, not decisions): `impl-native-labels` / `baton.claude-native-labels` and `review-native-labels` / `baton.reviewer-native-labels`, distinct private roots; receipt participants `baton.verifier-native-labels`, `baton.reviewer-receipt-native-labels`, `baton.slaw`; credential slot `claude` → `operator-file` / `w202663-development` (resolver marker check only); retention `retain`; owner `baton.slaw`.

## 2. One-time setup (one owner selection; four build/compose steps, one pre-install review boundary, one install)

Why these artifacts, verified against bytes: image `47e73383…` differs from `f34e1576` in 5 of its 10 recorded build inputs; no host bundle carries W383215/W383217. Both are built from one export of `f34e1576`.

```sh
# S1 export + inventory (read-only on Git; 60 s)
mkdir -p $EXPORT && git -C $REPO archive --format=tar $BASE | tar -x -C $EXPORT
(cd $EXPORT && find . -type f -print0 | sort -z | xargs -0 sha256sum) > $EXPORT.sha256    # bound as the source inventory
# S2 host bundle (timeout 900 s; retained output; no retry)
cd $EXPORT/v12 && just setup && timeout 900s just build $BUILD
"$DISTRO" identity                               # must answer frozen:true, both schema assets, native rpds; stamp may report no Git provenance
(cd $DISTRO && find . -type f -print0 | sort -z | xargs -0 sha256sum) > $BUILD/distro.sha256
# S3 worker image (the accepted W325695 build form; timeout 1800 s; engine build only, no run)
mkdir -p $RECEIPT && timeout 1800s docker build --pull=false --memory 2g --cpu-period 100000 --cpu-quota 100000 \
  --iidfile $RECEIPT/image.id -f $EXPORT/v12/worker/Dockerfile.claude $EXPORT/v12 > $RECEIPT/build.log 2>&1
IMAGE="sha256:$(cut -d: -f2 $RECEIPT/image.id)"
docker image inspect "$IMAGE" --format '{{json .Id}} {{json .Os}} {{json .Architecture}} {{json .Config.Entrypoint}} {{json .Config.User}}' > $RECEIPT/inspect.json
# BUILD-INPUTS.json: sha256 of the ten recorded inputs under $EXPORT/v12 (same path set as preparation-376414/BUILD-INPUTS.json), written beside image.id
```
S4 composition and install reuse the accepted one-time procedure of COMMANDS.md §4 (useful-template-job-monitor) with its helper re-pinned — the helper `capacity.py` hard-codes `SOURCE_COMMIT`, `DESTINATION`, `TASK_ID/JOB_ID`, `WORK_SCOPE/TEST_SCOPE`, `STATEMENT/ACCEPTANCE`, `LANES`, the image/adapter sources and the installed task's `verification`. A copy `work/records/2026/10/finding-v12-development-coordination-pilot/setup-native-labels/capacity.py` with exactly those constants re-pinned (values of §1, §3 and §4; image from `$RECEIPT/image.id`; adapter `docker-single-worker` digest as the pilot deployment records it) is the one-time composition artifact; it is reviewed as part of the pre-install boundary, and it is not a per-Job step.
```sh
cd $SETUP && python3 mint_inputs.py --into $MINT         # phase-1 document (no workers/jobs/uuid)
"$DISTRO" bootstrap --inputs $MINT                       # mint only: generates the authority identity
UUID="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["authority_uuid"])' $DEST/authority-identity.json)"; WORK="${UUID:0:8}-W1"
cd $SETUP && python3 capacity.py compose --minted-uuid "$UUID" --destination $DEST --distro $DISTRO --proposed-grants --evidence $COMPOSE
python3 -c 'import json,sys;a=json.load(open(sys.argv[1]));open(sys.argv[2],"w").write(json.dumps(a["document"],indent=1,sort_keys=True)+"\n")' $COMPOSE/compose.json $PHASE2
python3 -c 'import json,os,sys;a=json.load(open(sys.argv[1]));p=a["installed_task"]["place"];os.makedirs(os.path.dirname(p),exist_ok=True);open(p,"w").write(a["task_bytes"])' $COMPOSE/compose.json
```
**Pre-install artifact review boundary (the real one):** `$EXPORT.sha256`, `$DISTRO` identity + `distro.sha256`, `$RECEIPT/{image.id,inspect.json,BUILD-INPUTS.json,build.log}`, `$PHASE2`, the installed task bytes (§4 verifier inside), `$COMPOSE/compose.json` provenance members. Review accepts or refuses; nothing below runs before acceptance.
```sh
timeout 300s "$DISTRO" bootstrap --inputs $PHASE2 --destination $DEST --distro $DISTRO --repository-source $REPO   # ONE install
just --justfile $DEST/justfile start && just --justfile $DEST/justfile status && just --justfile $DEST/justfile stop   # initializes the control store; no Job exists, so no container and no provider call
"$STACK" record bind --authority-store $DEST/db/authority.sqlite3 --authority-uuid "$UUID" --work "$WORK" --locator "finding-v12-work-label-protocol-cli-${UUID:0:8}" --operation-id labels-bind-1   # flat canonical locator (dossier.check_locator: no "/", "\\" or ":"; collision suffix required); the repository path of the W29401 dossier travels in the installed manifest's record_binding (root baton-repository), as the pilot deployment records it
```
Known one-time hazards and their owners: `start` on a fresh install refused in W370268 until the worker `workspace_storage` directory existed (W376246/W376955/W376956 closed satisfying since; W375516 still owns read-only validation). If `start` refuses here, the refusal text is W375516 evidence and the one-time install step records the single `mkdir -p` of the path `deployment.json` names, inside `$DEST`; it is never a routine step. The control store is created by serving, so the start/stop pair above is part of install, not of kickoff.

## 3. Ordinary kickoff (the measured routine; operands only)

Inputs handed to the kickoff path: the finished task text `task-statement.txt` (the §A slice in prose, written during task design, outside the interval) and the acceptance/scope lists below (fixed for this Job). Translation to the command is the single invocation itself; there is no manifest, document or configuration to author.
```sh
date -u +%FT%T.%3NZ > $DEST/state/kickoff-T0.txt      # T0: inputs handed over; everything after this is inside the interval
just --justfile $DEST/justfile stop                  # idle first run only: the instance holds no live execution. NEVER stop a serving manager with unresolved live work to admit another Job.
"$STACK" manager --store $DEST/db/jobs.sqlite3 --incarnation labels-create-1 --authority-uuid "$UUID" \
  create --instance $DEST --control $DEST/db/control.sqlite3 --authority $DEST/db/authority.sqlite3 \
  --task $TASK_ID --statement "$(cat task-statement.txt)" \
  --acceptance "create accepts zero, one and repeated labels; normalized duplicates consume no cardinality" \
  --acceptance "label-work/unlabel-work cover add, remove, terminal Work, unauthorized, exact retry, convergent changed:false and conflicting operation reuse with stable errors" \
  --acceptance "list: repeated --label is all-of, --without-label is none-of, they compose; OR-like and key=value forms refuse explicitly" \
  --acceptance "work verbs dispatch only Authority Work labels; Thread label/unlabel and OCI runtime labels are unreachable from them" \
  --acceptance "unfiltered list, existing verbs, help and output versions are unchanged except additive fields" \
  --work-scope v12/python/tools/work_command.py --work-scope v12/python/tools/stack_command.py \
  --work-scope v12/python/src/baton_v12/job_manager/creation.py --work-scope v12/python/tools/job_manager.py \
  --test-scope v12/python/tests/tools/test_work_command.py --test-scope v12/python/tests/tools/test_stack.py \
  --test-scope v12/python/tests/tools/test_packaged_creation.py --test-scope v12/python/tests/tools/test_connected_creation.py \
  --test-scope v12/python/tools/parallel_test.py \
  --control-profile documentation/1 --job-id $JOB_ID --submission-id $SUBMISSION_ID > $DEST/state/create-answer.json
just --justfile $DEST/justfile start
just --justfile $DEST/justfile monitor 3             # read-only; Ctrl-C leaves it
"$STACK" view --status $DEST/state/status.json --job $JOB_ID
```
Expected `create-answer.json`: `job_id`, `work_id` = `$WORK`, `submission_id`, template `…implementation-review/1`, derived `source`/limits (`provider_turn 3600`, `verification 900`), `control` = `documentation/1` journalled, `servable: true`. Replay of the identical command returns the same answer; a changed statement under the same `--task` is refused. Stop: `"$STACK" manager cancel-job --instance $DEST/instance.json --job $JOB_ID --reason "…"` then `cancel-status`; `just stop` only after cessation is accounted (`cancel-status` complete) or under a separately selected emergency hold. Failed attempt: `manager settlement-preview/settle-stopped/settlement-status` as COMMANDS-377930 records. Closure after human acceptance: `"$STACK" disposition close --authority-store $DEST/db/authority.sqlite3 --authority-uuid "$UUID" --participant baton.slaw --work "$WORK" --outcome satisfying --proposal <retained proposal> --expect-candidate-digest <digest from the review findings> --operation-id labels-close-1`.

Limitation recorded (not a general admission workflow): stop/create/start is the idle-first-run path because `create` takes the manager instance lock. Ordinary parallel kickoff on a serving instance is W375518's accepted outcome; the later proof needed is a SECOND Job admitted on this same instance while the first is live, measured the same way (§5), without stopping anything.

## 4. Verification inside the worker (worker-compatible; no `just`, no venv)

Image facts (`Dockerfile.claude` at `f34e1576`): `python3` + `python3-jsonschema` from Debian trixie, `git`, `PYTHONPATH=/opt/baton`, user 65532, containers run with `--cpus 2` (`oci.py`). The product and the named tests import only the standard library and `jsonschema` (`requirements.lock`: jsonschema, jsonschema-specifications, referencing, attrs, rpds-py — all satisfied by the apt package). Under template `/1` the deployment serves task `/2`: the verifier runs at the candidate checkout root with the pinned environment (PATH/HOME only), 900 s bound, `/3` contexts are refused by the baseline role contract. The installed `verification` (composed into the task at S4) is therefore the same inline form the accepted documentation task used:
```json
["python3", "-c", "import os, sys, unittest\nos.chdir('v12/python')\nsys.path[:0] = ['src', '.']\nMODULES = ['tests.tools.test_work_command', 'tests.tools.test_stack', 'tests.tools.test_packaged_creation', 'tests.tools.test_connected_creation', 'tests.authority.test_work_label_exposure', 'tests.authority.test_work_labels']\nsuite = unittest.defaultTestLoader.loadTestsFromNames(MODULES)\nif suite.countTestCases() == 0: sys.exit('no tests collected')\nresult = unittest.TextTestRunner(verbosity=1).run(suite)\nsys.exit(0 if result.wasSuccessful() else 1)\n"]
```
Expected cost: the comparable control/cancellation modules run 96 cases in 4.5 s on the host; these six modules are of the same kind (disposable stores, fake owners, no engine); bound 900 s, expected well under 60 s at 2 CPUs; measured in the run, not asserted. The eventual artifact qualification (S3's `inspect.json`, plus the review attempt's own run of this argv) checks actual capabilities; no live model is needed for that check. Concrete gap for later coding Jobs: `tools/job_task.py` substitutes only `task_id` and `instructions`, so the verifier is per deployment, not per Job; the smallest existing correction is a `manager create` pass-through of a per-Job focused `verification` argv under the create/serving owners (W375517/W375518) — recorded, not a gate for this run.

## 5. Timing evidence plan (OBS-0/OBS-0a)

- **T0**: the instant the finished task text and the fixed acceptance/scope inputs are handed to the kickoff path (`kickoff-T0.txt`); all translation, `stop`, `create`, `start`, validation and launch are inside. Task design before T0 is outside and reported separately.
- **T1**: the first attributable substantive task work of the implementation attempt: the earliest manager receipt instant at which the retained provider stream shows a task-scoped tool action (a read/edit/command on a `--work-scope` or `--test-scope` path, or a repository command in the candidate), located through `logs … locators`/`read` and the manager's receipt stamps; `runtime.activity.observed_at` of the first non-zero `bytes_observed` is reported beside it as a bound, never as T1 (a count is not proof of useful work). If no stream event is attributable, T1 is reported unknown with the bound only.
- Intermediate durable instants reported in order: `create` answer wall time, `submissions.recorded_at`, admit `settled_at` (stage origin), launch `recorded_at`, first `activity.observed_at`, T1. Report T1−T0 and whether ≤ 60 s. Precedent: W370268 went create 01:26:15 → start 01:26:25 → container and provider turn 01:26:30 on a fresh install (no T1 defined then).
- Control evidence retained: the Job's `control` report (profile `documentation/1`, elapsed/deadlines/timing), `cancel-status`, the snapshot and attempt logs; a second-Job-on-serving-instance measurement is deferred to W375518's proof.

## 6. Remaining owner selections (only these)

1. The one setup/run selection of §2–§3 with its pre-install review boundary and the separately selected model run (`start` after `create`).
2. Explicit selection of the existing `documentation/1` numbers for this coding Job (zero code; recommended); no `coding/1`.
3. After the run: human import of the reviewed candidate into the checkout, focused tests, Git checkpoint, `disposition close`, and the W29401 disposition (native identities recorded in its dossier; it stays parked until the owner closes or narrows it).
