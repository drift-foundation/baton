# Corrected-base continuation proposal — not selected for execution

W333485 claim339444. This packet proposes one new isolated authoring invocation,
including explicit restoration of three UNACCEPTED partial buffers from
review-337905. Neither old restoration permission nor old execution selection
transfers. Independent preparation review and exact owner selection must precede
any selected-root creation, restoration into a candidate, or launch. Preparation
checks use disposable fixtures only. Preserve both prior instances unchanged.

Base: bc925cf5c62d69426ed5862af4d41f4d2a967b0f. Accepted shutdown correction is
bound by ACCEPTED-PREREQUISITE.json, with exact controller, shutdown helper,
baseline and all staged host source pins. PARTIAL-INPUT.json binds proposed
buffers, original provenance and new-base target bytes. Existing manager.py and
tools/job_manager.py base bytes are unchanged; renewal.py is absent in both bases.
No host product patch or candidate restoration was performed for preparation.

Proposed run: serving-renewal-w333485-339444; root below must be absent.
Image baton-v12-claude-worker:w239528-244216, config
sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2,
linux/amd64, task/2, Claude CLI2.1.247, bridge network. Credentials are only the
logical claude/operator-file reference w202663-development through
/home/sl/.baton/credential-sources.json; no credential contents read here.
Historical bootstrap binary is pinned to04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a,
build1e576ff2186db69e8b44da9d38874ff7e99ebbe3. No rebuild or implicit upgrade.

## Preparation review

Run commands separately; stop on refusal. Evidence destinations must be fresh.

```sh
PACKET_DIR=/home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal/continuation-339444
python3 -B "$PACKET_DIR/verify-inputs.py"
python3 -B "$PACKET_DIR/check-preparation.py" /tmp/w333485-review-preparation-339444
python3 -B "$PACKET_DIR/check-overlay.py"
```

The overlay checker copies only three base-file fixtures to /tmp, not a runnable
candidate. It proves exact copy and all-before-write refusals. The preparation
checker stages committed source and bootstraps disposable authority Work without
repositories; it never submits a Job, calls the engine/provider or starts the
controller. Its generated commands are evidence, not runnable selection.

## Owner sequence, only after exact separate selection

```sh
RUN_ROOT=/home/sl/baton-instances/serving-renewal-w333485-339444
python3 -B "$PACKET_DIR/prepare.py" stage --root "$RUN_ROOT"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$RUN_ROOT/code/v12/python/src:$RUN_ROOT/code/v12/python:$RUN_ROOT/supervisor"
python3 -B -m tools.bootstrap --inputs "$RUN_ROOT/bootstrap-inputs.json" --destination "$RUN_ROOT/instance" --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
python3 -B "$PACKET_DIR/prepare.py" bind --root "$RUN_ROOT"
cat "$RUN_ROOT/PREPARED.json"
cat "$RUN_ROOT/packet/commands.json"
docker image inspect sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2 --format '{{.Id}} {{.Os}}/{{.Architecture}}'
```

Compare actual authority/Work identity, generated PACKET digest, task/fixture
pins, limits and image availability before start. Never substitute rehearsal
UUIDs. Credential availability preflight is part of selected execution only.
Start alone submits the Job; no duplicate manual submission. Use a supervised
foreground terminal and the exact generated start/environment:

```sh
export BATON_V12_STAGE_EXECUTION_CONFIG="$RUN_ROOT/packet/deployment.json"
python3 -B -m tools.authoring_enforcement --packet "$RUN_ROOT/packet/PACKET.json"
```

Never invoke baseline.py directly. TASK carries the hash-verified loader command
for the selected private checkout; source is read-only mounted at /input/source.
The loader validates every input and target before any write. It never modifies
the original instance or canonical source.

Read-only status after stores exist:

```sh
python3 -B -c 'import json,os,subprocess,sys; c=json.load(open(sys.argv[1])); sys.exit(subprocess.run(c["status"],env=dict(os.environ,**c["environment"])).returncode)' "$RUN_ROOT/packet/commands.json"
```

An absent Job store before start is expected; do not initialize it. Ctrl-C or
SIGINT/SIGTERM to the verified exact outer PID requests cancellation. Do not guess
PIDs. Allow the existing cleanup envelope and inspect exact-runtime cessation;
a stop acknowledgement or manager exit is not cessation. Unknown engine state
retains the hold. No forced settlement, repeated invocation or automatic recovery.

## Finite milestone, limits and collection

TASK first requires timely renewal through blocked reconcile/sweep/custom reclaim
and authoritative ending/cancellation serialization, proven with controlled-clock
3600 and cancellation/end races before extending the full matrix. Finite remaining
steps are the negative/replay/restart/expiry/exhaustion/clock/fairness matrix and
independent acceptance. This is sequencing, not a narrowed delivery claim. The
partial Job read/write window is unresolved; prose or accounting is not proof.
120-second lead/30-second cadence remain proposals requiring latency evidence.

900-second initial permission begins at acquisition, before useful provider work.
Four renewals and30-second stop grace remain unchanged, but this host has no
production renewal caller and cannot hot-load the candidate. Provider3600/verifier30,
outer4800/cleanup60, one invocation/no retry are ceilings. No guaranteed900-second
fit is asserted after two truncated attempts. If cut short, retain the exact next
step and partial bytes; a subsequent invocation needs separate selection. A formal
verifier timeout is non-acceptance; no gate weakening or hidden limit extension.
Diagnostics W333486 is preferred for the next useful run; no dependency or shared
preparation queue is introduced.

Reuse W338305 review-2026-10-20T12-29-38Z.md:44 deterministic tests,11 real-process
composition cases with fake external boundaries. Current preparation establishes
exact staging and generated composition, not new live cessation or product proof.
The corrected manager shares the outer cutoff with baseline cleanup, accounting,
publication and guard stop; the outer retains kill/reap reserve. The main-thread
alarm is cooperative and is not a guarantee against arbitrary kernel stalls.
Controller publication can still fail; missing output remains incomplete.

Retain workload outcome.json, authoring.log, enforcement-*.json, manager-*.json
and their shutdown request/progress sidecars, supported status and exact
Job/attempt/runtime/token identities, controller/manager exit and cessation
observations, candidate/proposal paths, changed hashes and measured verification.
Record absent reports explicitly. Resource return and pending output are separate;
no report presence implies acceptance, no missing report alone implies live writer.
Do not read authority stores directly. Do not delete or rewrite old stores/evidence.
Cleanup-only recovery requires explicit separate selection after prior controller
cessation, with the same envelope/admission fences and no author invocation.

Diagnostics keeps its separate candidate. Its declared intake/attempts/delegation
and document paths may overlap necessary owner-boundary edits; declare actual
intersections and integrate serially after independent review. W325959 retains
joined acceptance. Only Slawomir owns Git changes. All direct exceptions expired.
