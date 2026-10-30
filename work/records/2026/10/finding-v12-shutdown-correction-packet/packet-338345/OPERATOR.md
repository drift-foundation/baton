# W338308 preparation proposal, packet338345

Prepared by baton.codxpc; not executed or accepted. This packet proposes one fresh
isolated W338305 correction Job. Independent preparation review and exact launch
selection remain required. No bootstrap, bind, fixture, provider or engine was run
while preparing it. `prepare.py` is a drafted future preparation program, not proof
that it has run. Do not execute the following sequence merely because it is written.

Run: `shutdown-deadline-w338305-prep338308`; proposed external root:
`/home/sl/baton-instances/shutdown-deadline-w338305-prep338308`.
Job: `job-shutdown-deadline-w338305-prep338308`; submission:
`shutdown-deadline-w338305-prep338308-submission`.
Actual authority UUID, Work, attempt, runtime and token identities must come from
supported bootstrap, claim and launch. None exists from this preparation.

Input is exactly committed fb48797903160aa764229d58f3a5beaf29648bfc, read-only
Git source at /home/sl/src/baton, no worktree overlay. HEAD was observed at
70760ef47a9bb2001c959a0dbdec72cdde61bfe6, the human diagnostic checkpoint.
That does not change this proposal's base. SOURCE.json/source.tar.gz are the exact
historical committed audit snapshot; the worker acquires the declared Git base.
Diagnostic scripts newly committed at HEAD are not delivered by that base.
TASK.md embeds the needed behavioral observations and requires candidate-native tests.
Task/2 instructions are delivered in the task payload; fixture pins on host files
do not mount those files into the candidate or provide task/3 inputs.

Host manager files and three historical supervisor files are pinned in
PREPARATION-PINS.json and staged from Git objects, never dirty working-tree bytes.
Controller SHA256 bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f;
baseline SHA256 c1b0a10e609503df0ba7ebdc7455cc8518c9175882edd185b65f20c342c4bd2f.
Candidate changes never replace these running host inputs.

Proposed worker baton-v12-claude-worker:w239528-244216, config digest
sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2,
linux/amd64, provider Claude model opus, CLI2.1.247. Historical image artifact is
pinned; image presence/authentication are unverified. Bootstrap build
1e576ff2186db69e8b44da9d38874ff7e99ebbe3 is separately pinned at
/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro/baton-v12-stack,
SHA25604aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a.
Network bridge; credential slot claude, operator-file/w202663-development through
/home/sl/.baton/credential-sources.json. No credential contents were read.

## Static checks permitted in this preparation

From this packet directory:

```sh
sha256sum --check SHA256SUMS
python3 -B check-static.py
```

The checker parses files and compares bytes/Git objects only. It imports no product
modules and runs no packet functions, bootstrap, fixtures, engines or providers.
STATIC-EVIDENCE.json records the preparation observation; later checks are observations
of their own time, not a replacement of that immutable evidence. No dynamic
composition or stage/bind claim follows from these checks.

## Future selected sequence

Exact execution selection must cover the fresh root, pinned image/bootstrap/source,
bridge credential delivery and one provider-backed authoring invocation with the
limits below, acknowledging the known finalization defect and partial-result risk.
The provider authors code; all product verification uses deterministic fake external
boundaries. Launch readiness must check available image, source pins, absent root,
disk/resources and credential delivery through the supported runtime.

Run commands separately, stop on any refusal and retain partial state. These are
proposals only. Rehearsing bootstrap/bind or a test is also execution requiring its
supported isolated selection; this packet grants no direct rehearsal exception.

```sh
PACKET_DIR=/home/sl/src/baton/work/records/2026/10/finding-v12-shutdown-correction-packet/packet-338345
RUN_ROOT=/home/sl/baton-instances/shutdown-deadline-w338305-prep338308
python3 -B "$PACKET_DIR/prepare.py" stage --root "$RUN_ROOT"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$RUN_ROOT/code/v12/python/src:$RUN_ROOT/code/v12/python:$RUN_ROOT/supervisor"
python3 -B -m tools.bootstrap --inputs "$RUN_ROOT/bootstrap-inputs.json" --destination "$RUN_ROOT/instance" --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
python3 -B "$PACKET_DIR/prepare.py" bind --root "$RUN_ROOT"
cat "$RUN_ROOT/PREPARED.json"
cat "$RUN_ROOT/packet/commands.json"
docker image inspect sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2 --format '{{.Id}} {{.Os}}/{{.Architecture}}'
export BATON_V12_STAGE_EXECUTION_CONFIG="$RUN_ROOT/packet/deployment.json"
/usr/bin/python3 -B -m tools.authoring_enforcement --packet "$RUN_ROOT/packet/PACKET.json"
```

Inspect generated policy/task/submission/commands and retain digests and actual
authority/Work identities before start. Bootstrap/bind do not submit a Job;
the controller's baseline owns submission. Never submit twice, launch bare baseline,
reuse an old instance or replace the controller with candidate bytes. The disposable
v12 baton.impl/baton.review are distinct principals in that authority, not v11
identity substitutions. Generated status uses tools/job_manager.py status through
the pinned environment; before a store exists, a status refusal is not a failed Job.

## Limits, evidence and non-success handling

Provider3600s; formal verifier30s; total4800s including cleanup60s; one invocation;
automatic retry false; report-and-hold. Token900s/four-renewal policy unchanged;
no production renewal caller. Outer envelope stop_at is original total minus cleanup,
but token expiry/cancellation may stop work much earlier. Poll0.25s, engine call2s;
these do not guarantee physical cessation on unavailable Docker. Host finalization
can still lose reports. A smaller task is not proof it finishes before expiry.

The30s fast gate is fully spelled in prepare.py and TASK.md. Required supplemental
Composition and existing controller/manager tests run inside the author invocation
with120s command plus5s termination/reap bound. Candidate-native tests must exercise
the real baseline composition; existing tests alone are insufficient. Timing and
behavior are unproved until that execution. Timeout/failure/skip or absent supplemental
evidence is non-acceptance; never weaken acceptance to fit the gate. Independent
candidate review needs a separately selected isolated v12 verification execution,
using the same candidate-native suite and explicit import roots.

TASK-PREVIEW.json is the exact proposed task/2 payload (bind compares it against
the real composer's result before writing the packet). SUPPLEMENTAL-ARGV.json
spells the proposed supplemental argv from candidate root; it is a review artifact,
not an extra mounted input. The author can reconstruct that command from TASK.md's
module names and cwd/import instructions. Its120s limit belongs to the authoring
tool call/process supervision; it does not change the formal verifier's30s policy.

Retain workload packet/outcome.json, append-only outcome.json.authoring.log,
outcome.json.enforcement-<pid>-<ns>.json and outcome.json.manager-<pid>-<ns>.json,
original generated packet/commands/envelope, read-only Job/control views, actual
Job/attempt/runtime/token identities, measured durations and private candidate/proposal
locators. Safe status command is the generated commands.json status argv with its
environment, not raw store access. Report missing files and unknown states explicitly.
Producer success never supplies independent acceptance; partial files are not a
candidate verdict. Inspect outputs only after exact cessation is established.

If expiry or host finalization fails, retain all evidence and return exact remaining
scope to v11. Do not infer cessation from process exit, signal, report or token expiry.
Unknown execution/launch keeps the hold. Confirmed exact cessation and recorded status
must not gain a report-quality gate. No cleanup deletion, normalization, forced release
or automatic recovery/retry is selected. Supported same-packet recovery, if separately
selected after prior-controller cessation, is cancellation-only under original envelope
and authoring.lock; it cannot launch another author invocation. Never unlink that lock.
Any fresh continuation needs a separately selected attempt after safe prior-runtime
accounting and explicit adoption of retained candidate inputs.

This packet can offer a best-effort authoring attempt with honest partial retention;
it cannot guarantee final report delivery under the known host bug. If guaranteed
delivery is required before trying this route, the exact missing capability is bounded
cooperative finalization in the current host. A bounded alternative for owner selection
is a W338305-only direct correction/verification exception followed by isolated proof;
no such exception is requested implicitly or exercised here. Correction scope itself
is already selected and requires no routine reapproval.

Human diagnostic checkpoint70760ef is observed. After independent packet acceptance,
packet checkpoint remains due: `Prepare isolated v12 authoring shutdown correction packet`.
Correction candidate acceptance/integration and its human checkpoint remain separate.
