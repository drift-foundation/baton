# W385624 Stage 1-B — native implementation/review packet

M385681 / E385683 preparation only. No implementation or launch performed. TASK.txt is the exact self-contained4028-character final statement (below4096); verification-argv.json is the literal submitted command, shell-parsed without executing tests. New acceptance module is an implementation deliverable, not a present passing test. Runtime/source pins and checks are in manifest.json/source-inputs.json. No bespoke launcher.

**One bounded Job is recommended.** Owner decision and successor admission share one exact binding/replay contract; keeping them together permits real command→admission acceptance now. No B1/B2 graph split needed. Stage1-C executes verification/review recovery; this Job must deliver its actual manager admission contract, with truthful unsupported-binding refusal/hold, not fake runnable stages. No repeated Stage1-A verification requested during preparation.

**Concrete selection still needed:** current compose-worker has no alternate provider/model selector; deployment_identities fixes Claude/Opus and dogfood_entry uses ClaudeAgent. Earlier same-family exceptions do not cover this Job. The commands below use distinct baton.claude-native and baton.reviewer-native principals/contexts only if owner explicitly selects that pair for W385624. Alternatively supply a supported alternate-family native binding and revalidate composition; no provider outage or silent fallback is inferred. Live installation/create/start are not selected by preparation.

**Limits:** the DEVELOPMENT Job uses qualified native-handoff-heavy/1, provider7200, stage9000, overall21600 including queue, ordinary verification900, zero corrections and one resolved clarification continuation; unchanged retry/shutdown. PRODUCT recovery admission must bind approved stage1-verification-review/1 digest5a6a420e… and9960/4800/3600/900 with zero automatic retry/correction, including review-only stage omission. Do not substitute development limits into recovery decisions.

Source is committed ce6e1b2bf12519a84a3792f06562b7727dfe3021; qualified runtime is v12/python/build/out/distro from that checkpoint. All82 runtime hashes match retained packaging-ce6e1b2b/runtime-files.json; accepted packaging result24/24 is reused, not rerun. Build stamp reports dirty=true/changed_entries5; retain that qualification exactly, despite v12 being clean as recorded by the packaging gate. No new rebuild is required by this packet. Worker image19eb459b… matches the installed image and copied worker/runtime input paths are unchanged from its ac17a5ad baseline. Runtime auth/access/readiness still checked at execution, not proved by source hashes.

The source checkout must remain pinned. The updated coordinator PLAN differs from its ce6e1b2b version. Use a separate exact ce6e1b2b source checkout, not the dirty coordinator record. The owner-only materialization below uses a disposable clone; a supplied SOURCE_CHECKOUT may reuse an already exact copy. Do not repin or rebuild merely for evidence changes. New TASK/JSON packet files are external operator inputs, copied/sealed by existing tools; the native worker does not need them committed at its source. Current PLAN assignment is carried self-contained in TASK.txt. Required source files are checked against their committed hashes, including the source version of FINDING/PLAN. Retain this packet through normal owner checkpoint/backup; no hidden scratch-only input.

## Conditional operator commands

Run blocks in one Bash session only after model binding and execution selection; stop on refusal. No main Git operations. Recheck disk space: preparation roots were writable ext4, about507GiB available. Runtime workspace/candidate disk is private; verifier explicitly creates work/scratch/w385624-verification and selects it as BATON_V12_DISK_ROOT. Existing TMPDIR remains bounded verifier ephemera, not workspace storage.

```bash
set -euo pipefail
REPO=/home/sl/src/baton
SRC=${SOURCE_CHECKOUT:-$REPO/work/scratch/w385624-source}
BASE=ce6e1b2bf12519a84a3792f06562b7727dfe3021
RECORD=work/records/2026/11/finding-v12-retained-recovery-admission
PACKET=$REPO/$RECORD/evidence/native-kickoff-385683
QUALIFIED=$REPO/work/records/2026/11/finding-v12-retained-failure-analysis/evidence/packaging-ce6e1b2b
DISTRO=$REPO/v12/python/build/out/distro
DEST=/home/sl/baton-instances/native-w385624-admission-1
RUN=$REPO/work/scratch/w385624-kickoff-1
IMAGE=sha256:19eb459b44478f60ee16a61fcc32c2c99dd0132d7d93675adf9fb7afbe5a92b4
# Owner-only disposable source materialization; no main index/history change.
if [[ -z "${SOURCE_CHECKOUT:-}" ]]; then
    test ! -e "$SRC" && test ! -L "$SRC"
    git clone --no-local "$REPO" "$SRC"
    git -C "$SRC" checkout --detach "$BASE"
fi
test "$(git -C "$SRC" rev-parse HEAD)" = "$BASE"
test -z "$(git -C "$SRC" status --porcelain -- v12)"
test ! -e "$DEST" && test ! -L "$DEST"
test "$(docker image inspect --format '{{.Id}}' baton-v12-worker:ac17a5ad)" = "$IMAGE"
python3 -I - "$SRC" "$PACKET" "$QUALIFIED" "$DISTRO" <<'PY'
import hashlib, json, pathlib, subprocess, sys
src, packet, qualified, distro = map(pathlib.Path, sys.argv[1:])
for name, digest in json.loads((packet/'source-inputs.json').read_text()).items():
    assert hashlib.sha256((src/name).read_bytes()).hexdigest() == digest, name
for name, digest in json.loads((qualified/'runtime-files.json').read_text()).items():
    assert hashlib.sha256((distro/name).read_bytes()).hexdigest() == digest, name
statement = (packet/'TASK.txt').read_text().rstrip('\n')
assert 0 < len(statement) <= 4096
argv = json.loads((packet/'verification-argv.json').read_text())
assert argv[:2] == ['bash','-c'] and len(argv) == 3 and '\n' not in argv[2]
subprocess.run(['bash','-n','-c',argv[2]],check=True)
PY
mkdir "$RUN"
just --justfile "$REPO/v12/justfile" bootstrap "$PACKET/bootstrap-inputs.json" "$DEST" "$DISTRO" "--repository-source $SRC"
BIN=$DEST/distro/baton-v12-stack
mkdir -p "$DEST/state/task"
cp "$PACKET/installed-task.json" "$DEST/state/task/installed-task.json"
for SPEC in 'impl-a implementation baton.claude-native' 'review-a review baton.reviewer-native'; do
    read -r WORKER ROLE PARTICIPANT <<< "$SPEC"
    "$BIN" pool compose-worker --deployment "$DEST/deployment.json" --worker-id "$WORKER" --role "$ROLE" --participant "$PARTICIPANT" \
        --template baton.v12.job-template.implementation-review/3 \
        --image-reference baton-v12-worker:ac17a5ad --image-digest "$IMAGE" --cli-build 2.1.247 --network bridge \
        --credential-sources /home/sl/.baton/credential-sources.json --credential claude=operator-file:w202663-development \
        --workspace-group 1001 --task-document "$DEST/state/task/installed-task.json" \
        --record "$RECORD" --checkout "$SRC" --verifier-layout "$SRC/v12/worker/verifier-layout-marker.json" --into "$RUN/$WORKER.json"
done
python3 -I - "$PACKET" "$RUN" "$DEST" <<'PY'
import json, pathlib, sys
packet, run, dest = map(pathlib.Path, sys.argv[1:])
d = json.loads((packet/'bootstrap-inputs.json').read_text())
dep = json.loads((dest/'deployment.json').read_text())
for key in ('integration_target','integration_workspace'): d[key] = dep[key]
d['workers'] = [json.loads((run/(w+'.json')).read_text()) for w in ('impl-a','review-a')]
(run/'workers.json').write_text(json.dumps(d,indent=2)+'\n')
PY
just --justfile "$REPO/v12/justfile" bootstrap "$RUN/workers.json" '' '' "--repository-source $SRC"
just --justfile "$DEST/justfile" repository
just --justfile "$DEST/justfile" status
```

Require pinned source/line base, two distinct role identities, zero Jobs and not serving. Credentials are referenced only; no credential bytes read/copied or registry changed by preparation. Refuse mismatched bindings, no live patch-up.

```bash
UUID=$(python3 -I - "$DEST/authority-identity.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))['authority_uuid'])
PY
)
mapfile -d '' VERIFY < <(python3 -I - "$PACKET/verification-argv.json" <<'PY'
import json, sys
for value in json.load(open(sys.argv[1])): sys.stdout.buffer.write(value.encode()+b'\0')
PY
)
VERIFY_ARGS=()
for ARG in "${VERIFY[@]}"; do VERIFY_ARGS+=("--verification=$ARG"); done
"$BIN" manager --store "$DEST/db/jobs.sqlite3" --incarnation slaw-w385624-admission-1 --authority-uuid "$UUID" \
    create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
    --task w385624-native-admission-1 --job-id w385624-native-admission-1 --source installed \
    --template baton.v12.job-template.implementation-review/3 --control-profile native-handoff-heavy/1 --provider-turn-seconds 7200 \
    --statement "$(cat "$PACKET/TASK.txt")" \
    --acceptance 'Stage1-B real owner read/decision command through authorized manager admission/readback, exact retained inputs/profile/stages, replay/cancel/cessation and review-only safety; no implementation redispatch; deterministic connected evidence and independent review.' \
    --work-scope 'W385624 Stage1-B only: necessary v12 command/admission/schema/tests and owning dossier evidence; no Stage1-C execution, broader pools or unrelated changes.' \
    "${VERIFY_ARGS[@]}" > "$RUN/create.json" 2> "$RUN/create-report.log"
cat "$RUN/create-report.log"
just --justfile "$DEST/justfile" status
```

Before selected start, require exact final statement/argv/source, heavy resolved limits, /3 template, reviewer identity, and scoped answer-handoff grant. The created DEVELOPMENT Job has implementation/review stages; the PRODUCT successor implemented by it must never include implementation. They are distinct objects. Required new test module must contain real owner command and production admission cases, not a placeholder; missing module is failure, not a reason to substitute a weaker verifier.

```bash
just --justfile "$DEST/justfile" start
just --justfile "$DEST/justfile" monitor 10
```

No start executed here. Monitor exit does not stop work. Operator stop, if selected: `just --justfile "$DEST/justfile" stop`; it does not prove runtime cessation. Retain exact candidate/base/digests, per-ID counts/failures/skips/duration and independent native verdict. Changes-requested is never acceptance merely because executions completed. Native review is automatic; unresolved product/authority questions use existing /3 handoffs to baton.slaw. Canonical result returns on W385624/T385624 for independent review/owner Git. No main import or W385625 execution selected.
