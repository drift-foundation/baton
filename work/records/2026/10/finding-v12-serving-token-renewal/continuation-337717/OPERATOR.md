# W333485 fresh authoring preparation — claim337717

Status: HELD BEFORE EXECUTION SELECTION. This immutable proposal supersedes execution333532 and withdrawn execution334650 for preparation review only. Independent preparation review and exact separate owner selection are required before launch. Neither this document nor disposable bootstrap/bind evidence grants execution. The old packet remains forbidden; do not edit or start it. No live provider, engine/container operation, credential-content read or pilot mutation occurs in these preparation checks.

Proposed run `serving-renewal-w333485-337717`, fresh root `/home/sl/baton-instances/serving-renewal-w333485-337717`, Job `job-serving-renewal-w333485-337717`, submission `serving-renewal-w333485-337717-submission`. Actual fresh authority UUID and Work ID are minted by bootstrap/bind; do not copy disposable rehearsal identities. Base `fb48797903160aa764229d58f3a5beaf29648bfc` contains accepted W333735 and W334910 bytes. PREPARATION-PINS.json binds118 committed host manager files including tools/authoring_enforcement.py, worker_manager/intake.py and attempts.py; three unchanged historical supervisor files remain pinned. SOURCE.json/source.tar.gz preserve306 committed source inputs. Runtime source is the exact Git base mounted read-only from `/home/sl/src/baton`; no ambient dirty source overlay; exactly three unaccepted partial files are explicitly restored into the private checkout. The archive is an audit copy, not a Git repository replacement.

The existing fresh git-line task/2 vehicle and worker `baton-v12-claude-worker:w239528-244216`, exact config `sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`, linux/amd64, are proposed unchanged. Historical bootstrap executable `/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro/baton-v12-stack` SHA256 `04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a`, build `1e576ff2186db69e8b44da9d38874ff7e99ebbe3`, remains separately pinned. Do not substitute the uncommitted task/3 work or rebuild the image. Image and authentication availability at eventual execution still need preflight; no credential contents were checked.

Proposed network bridge; credential slot claude, provider operator-file, reference w202663-development, registry `/home/sl/.baton/credential-sources.json`. Owner selection must explicitly include that credential delivery and the provider-backed authoring invocation. The disposable v12 authority's baton.impl/baton.review are its separate principals, not v11 impersonation. The production correction itself uses fake providers/engines for verification; no live test campaign is selected.

## Verify preparation inputs

```sh
PACKET_DIR=/home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal/continuation-337717
cd "$PACKET_DIR"
sha256sum --check SHA256SUMS
python3 -B "$PACKET_DIR/verify-inputs.py"
```

A mismatch refuses this proposal. Do not rewrite hashes to hide drift. The independent disposable check below uses public bootstrap/bind, no supervisor start and no provider/engine invocation:

```sh
python3 -B "$PACKET_DIR/check-preparation.py" /tmp/w333485-independent-preparation-337440
```

The evidence destination must be absent. The temporary instance is retained, never usable as the selected execution. Generated rehearsal start commands are inspectable proposals, not permission to run them. No actual v12 Job or attempt exists from preparation alone.

## Proposed owner sequence, only after review and selection

Run each command separately; stop on any failure, preserve partial state, and do not bypass refusal. Use a supervised foreground terminal. Stage refuses existing/aliased destinations and bind refuses changed inputs, staged bytes or existing packets.

```sh
RUN_ROOT=/home/sl/baton-instances/serving-renewal-w333485-337717
python3 -B "$PACKET_DIR/prepare.py" stage --root "$RUN_ROOT"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$RUN_ROOT/code/v12/python/src:$RUN_ROOT/code/v12/python:$RUN_ROOT/supervisor"
python3 -B -m tools.bootstrap --inputs "$RUN_ROOT/bootstrap-inputs.json" --destination "$RUN_ROOT/instance" --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
python3 -B "$PACKET_DIR/prepare.py" bind --root "$RUN_ROOT"
cat "$RUN_ROOT/PREPARED.json"
cat "$RUN_ROOT/packet/commands.json"
docker image inspect sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2 --format '{{.Id}} {{.Os}}/{{.Architecture}}'
```

Record actual authority/Work identity and generated PACKET.json digest before launch. Compare task, source pins, effective policy and submission limits against this proposal. Bootstrap/bind prepare authority Work but do not submit a Job. Start alone owns submission; never submit manually as well. The generated commands.json replaces the historical baseline start with this exact accepted entrypoint and includes the supervisor import directory:

```sh
export BATON_V12_STAGE_EXECUTION_CONFIG="$RUN_ROOT/packet/deployment.json"
/usr/bin/python3 -B -m tools.authoring_enforcement --packet "$RUN_ROOT/packet/PACKET.json"
```

Never run baseline.py directly. Its digest remains a required underlying supervisor pin, not the selected outer entrypoint. The controller validates its own pinned bytes and imported source. Ctrl-C/SIGINT or SIGTERM to the verified exact outer controller requests cancellation. Do not guess a PID or signal another process. Allow cleanup, preserve its JSON report and append-only log, and inspect exact cessation evidence. A sent stop or process exit is not container cessation.

## Status, result and recovery

After stores exist, use the generated read-only status command/environment:

```sh
python3 -B -c 'import json,os,subprocess,sys; c=json.load(open(sys.argv[1])); sys.exit(subprocess.run(c["status"], env=dict(os.environ, **c["environment"])).returncode)' "$RUN_ROOT/packet/commands.json"
```

Before start an absent Job store can refuse status; do not initialize it to fabricate a result. The workload result is `$RUN_ROOT/packet/outcome.json`; the controller appends `$RUN_ROOT/packet/outcome.json.authoring.log` and writes a distinct `outcome.json.enforcement-<pid>-<ns>.json`. Missing workload outcome is incomplete evidence. Read control/Job status and those reports together, record actual Job/attempt/runtime identities, original envelope, token state, measurements and retained workspace/proposal paths. No self-acceptance or automatic integration. Retain private workspace, partial output, stores, logs and original packets without deleting, resetting, normalizing or copying over them. Independent consumer review may use partial output only after exact-runtime cessation and with its actual provenance.

On controller failure or engine outage, unknown runtime/activation stays held. Do not release a resource from expired time or a successful stop acknowledgement. Recovery uses the SAME packet and entrypoint, after confirming the prior controller has ended and under explicit recovery selection; the existing envelope/halt/child-admission records make it cancellation-only, with60s cleanup and no author launch or new invocation. Recovery can start a cleanup manager; child_started is not author_invocation_started. The inherited flock prevents simultaneous controllers; never unlink its inode. Repeat recovery is not selected automatically. Failed engine control needs exact operation/runtime reconciliation; this packet grants no force cleanup or new attempt. A future authoring continuation requires separately selected fresh inputs/attempt after prior cessation, preserving old limits and evidence.

## Effective limits and acceptance boundary

Policy/submission provider3600s, verifier30s; envelope4800s with60s cleanup; one invocation, no automatic retry, report-and-hold. The committed host has NO production renewal caller. The initial token expires900s from acquisition, potentially before900s of provider work. Admission closes at the earliest observed expiry, cancellation, enforcement failure, clock regression or original envelope stop at4740s. The guard polls0.25s independently of blocked authoring sweep; each engine call is bounded at2s, but calls and OS scheduling add latency. At halt the manager enforcement requests cancellation and the outer controller bounds manager shutdown; up to12s of the60s is reserved for group kill/reap and enforcer join. These are local scheduling bounds, NOT a guarantee that unavailable Docker stops a writer at900s. Unavailable/unknown control retains the hold and reports failure. No lease increase, implicit renewal, deadline reset or host candidate hot-patch is permitted.

Reuse accepted W334910 review-2026-10-19T20-01-02Z.md and INTEGRATION-337376.md (79 deterministic tests, including seven real-process guard cases) for enforcement behavior; W333735 review-2026-10-19T17-25-12Z.md remains prior evidence. These tests simulate packet/image validation and workload boundaries; they are not live engine/provider or installed-workload proof. This packet's preparation checks establish pins, commands, staging/refusal/bootstrap/bind and coherent limits, not new physical shutdown or live-provider proof. Full production-renewal3600s acceptance,120s lead/30s cadence justification, eligibility/races/restart/exhaustion and slow-engine fairness remain TASK.md obligations inside the later v12 Job. The30s verification gate fit for new tests remains unproved; timeout is non-acceptance, never grounds to weaken tests.

Diagnostics W333486 remains separately allocated. It does not plan tools/job_manager.py or job_manager/manager.py edits. Potential intake.py/attempts.py overlap must be declared in actual output and integrated serially into a newly reviewed combined candidate; no overwrite. W325959 retains joined acceptance. The prerequisite human Git checkpoint is fulfilled; accepted production delivery needs its own checkpoint, owned only by Slawomir.

## Corrected manager ownership

The outer controller holds only authoring.lock, validates the packet and watches the manager. One manager process acquires the unchanged workspace manager guard before preparation, then runs authoring and enforcement in separate threads/connections. Independent managers remain excluded. The manager publishes outcome.json.manager-<pid>-<ns>.json snapshots; missing final state stays held. Manager death or parent-death shutdown never proves container cessation. The separate authoring lock is inherited; the workspace guard is not inherited. The accepted controller SHA256 is bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f. Both old packets remain sealed and forbidden. Owner close337414 binds this human checkpoint; its earlier integration record predates the commit.

## Continuation binding

PARTIAL-INPUT.json binds exact interrupted bytes from review337693 at the same committed base. TASK carries LOAD-COMMAND.txt, which hashes restore.py before execution; restore.py validates all three input hashes and target base bytes before writes. PREPARATION-PINS and the generated fixture bind these buffers and loader. The supported git-line task/2 vehicle mounts nominated source read-only at /input/source; only the new private candidate receives the copy. This is not accepted product or an automatic source-profile overlay. Preserve old instance337440 unchanged and held; no recovery or old selection applies. Full corrected timing/fencing and acceptance remain owed. Initial900s permission may again end authoring early; no guaranteed completion is claimed.
