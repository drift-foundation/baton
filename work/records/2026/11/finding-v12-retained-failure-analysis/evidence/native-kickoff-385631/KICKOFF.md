# W385623 native implementation/review kickoff — preparation only

M385630 / E385631. No host implementation, build, test, installation or launch performed. TASK.txt is the bounded Stage 1-A instruction; verification-argv.json is the exact submitted command. Existing `bootstrap`, `pool compose-worker`, manager `create`, `start` and `monitor` remain the execution tools. No bespoke launcher.

## Two concrete prerequisites

1. **Binding selection is blocked.** Current `pool.compose-worker` has no provider/model selection operand; `next_run_bindings.deployment_identities` selects `claude-fresh-implementation`, model `opus`, and `/opt/baton/dogfood_entry.py`, which imports ClaudeAgent. All three inspected installed instances have Claude-fresh implementation and review lanes (binding-observations.json). Different participant/context is supported; different family is not selectable through this composer. This is not a claim that another provider is unavailable generally. Needed: identify an already supported alternate-family native binding/tool, or record explicit owner selection of the available separate-context Claude/Opus pair for this bounded Job. No same-model fallback is selected by this packet. Supporting another adapter would be separate capability work, not hidden in 1-A. Commands below are conditional on explicit selection of the existing Claude pair; an alternate binding requires corrected composition operands and revalidation before launch.
2. **Owner checkpoint required.** Preparation source is `9f4fbb2e215f95e34241938cfbf27dc04e9ec9cd`, with REC-8 applied. New allocation FINDING/PLAN and this task are not in that commit. Required source paths/bytes are listed in required-inputs.json. Owner checkpoints those inputs; commands select HEAD once and validate committed bytes, then pin both source and task base to it. Evidence-only later changes do not require repinning/rebuilding; do not require HEAD equality after admission. Product drift from the prepared source requires bounded revalidation. Existing installations contain older source and `create --source installed` cannot import dirty records or choose arbitrary host HEAD. Use the fresh destination below, preserving existing instances.

No live execution is authorized here. After the prerequisites are resolved, the operator separately selects installation/creation/start. Do not execute the conditional blocks merely because they are provided.

## Read-only checkpoint and packet preflight

Run subsequent blocks in one Bash session, stopping on any failure. The required-input check must pass after owner checkpoint. No credential content is read or copied here.

```bash
set -euo pipefail
REPO=/home/sl/src/baton
RECORD=work/records/2026/11/finding-v12-retained-failure-analysis
PACKET=$REPO/$RECORD/evidence/native-kickoff-385631
DEST=/home/sl/baton-instances/native-w385623-analysis-1
BASE=$(git -C "$REPO" rev-parse HEAD)
IMAGE=sha256:19eb459b44478f60ee16a61fcc32c2c99dd0132d7d93675adf9fb7afbe5a92b4
cd "$REPO"
git diff --exit-code 9f4fbb2e215f95e34241938cfbf27dc04e9ec9cd "$BASE" -- v12
test -z "$(git status --porcelain -- v12)"
test ! -e "$DEST"
test ! -L "$DEST"
test "$(docker image inspect --format '{{.Id}}' baton-v12-worker:ac17a5ad)" = "$IMAGE"
python3 -I - "$REPO" "$PACKET" "$BASE" <<'PY'
import hashlib, json, pathlib, subprocess, sys
repo, packet, base = sys.argv[1:]
for path, expected in json.loads((pathlib.Path(packet)/'required-inputs.json').read_text()).items():
    committed = subprocess.check_output(['git', '-C', repo, 'show', base+':'+path])
    assert hashlib.sha256(committed).hexdigest() == expected, path
    assert hashlib.sha256((pathlib.Path(repo)/path).read_bytes()).hexdigest() == expected, path
argv = json.loads((pathlib.Path(packet)/'verification-argv.json').read_text())
assert argv[:2] == ['bash', '-c'] and len(argv) == 3
assert '\n' not in argv[2] and '\x00' not in argv[2]
subprocess.run(['bash', '-n', '-c', argv[2]], check=True)
print('Required committed input bytes and final verification shell syntax checked; tests not run.')
PY
df -T "$REPO/work/scratch" /home/sl/baton-instances
```

Both roots inspected during preparation are ext4, with about 528 GiB available; capacity must be rechecked at execution. Refuse tmpfs/ramfs or unwritable storage. Worker source and verifier candidate are private disk-backed workspace copies. Verification creates `work/scratch/w385623-verification` within that copy and sets BATON_V12_DISK_ROOT explicitly before loading fixtures; the normal verifier TMPDIR stays its bounded ephemeral root, not workspace storage. This prepares the disk selector, not a claim of runtime preflight success. Native admission must still validate actual workspace roots/access/capacity.

## Conditional installation — only after binding selection

The following uses the existing Claude/Opus pair and requires its explicit selection. It does not provide different-family review. Preserve the output under disk-backed scratch during installation; promote admission/result identities and evidence to the dossier afterward. Generating concrete installation operands from these templates does not change their required committed bytes.

```bash
RUN=$REPO/work/scratch/w385623-kickoff-1
mkdir "$RUN"
python3 -I - "$PACKET" "$RUN" "$BASE" <<'PY'
import json, pathlib, sys
packet, run = map(pathlib.Path, sys.argv[1:3]); base = sys.argv[3]
for source, output in [('bootstrap-inputs.template.json','bootstrap-inputs.json'), ('installed-task.template.json','installed-task.json')]:
    d = json.loads((packet/source).read_text())
    for key in ('canonical_target_id','line_declared_base','declared_base'):
        if key in d: d[key] = base
    (run/output).write_text(json.dumps(d, indent=2)+'\n')
(run/'selected-base.txt').write_text(base+'\n')
PY
just --justfile "$REPO/v12/justfile" bootstrap "$RUN/bootstrap-inputs.json" "$DEST"
BIN=$DEST/distro/baton-v12-stack
mkdir -p "$DEST/state/task"
cp "$RUN/installed-task.json" "$DEST/state/task/installed-task.json"
for SPEC in 'impl-a implementation baton.claude-native' 'review-a review baton.reviewer-native'; do
    read -r WORKER ROLE PARTICIPANT <<< "$SPEC"
    "$BIN" pool compose-worker --deployment "$DEST/deployment.json" --worker-id "$WORKER" --role "$ROLE" --participant "$PARTICIPANT" \
        --template baton.v12.job-template.implementation-review/3 \
        --image-reference baton-v12-worker:ac17a5ad --image-digest "$IMAGE" --cli-build 2.1.247 --network bridge \
        --credential-sources /home/sl/.baton/credential-sources.json --credential claude=operator-file:w202663-development \
        --workspace-group 1001 --task-document "$DEST/state/task/installed-task.json" \
        --record "$RECORD" --checkout "$REPO" --verifier-layout "$REPO/v12/worker/verifier-layout-marker.json" \
        --into "$RUN/$WORKER.json"
done
python3 -I - "$RUN" "$DEST" <<'PY'
import json, pathlib, sys
run, dest = map(pathlib.Path, sys.argv[1:])
d = json.loads((run/'bootstrap-inputs.json').read_text())
dep = json.loads((dest/'deployment.json').read_text())
for key in ('integration_target','integration_workspace'): d[key] = dep[key]
d['workers'] = [json.loads((run/(w+'.json')).read_text()) for w in ('impl-a','review-a')]
(run/'workers.json').write_text(json.dumps(d, indent=2)+'\n')
PY
just --justfile "$REPO/v12/justfile" bootstrap "$RUN/workers.json"
just --justfile "$DEST/justfile" repository
just --justfile "$DEST/justfile" status
```

Require selected BASE, exactly two distinct role participants, zero Jobs and not serving. Existing credential registry handle is reused through the supported launch boundary; freshness/authentication was not tested. No new credential registry/profile is written. Image identity was read back exactly and all Dockerfile worker COPY source inputs are unchanged from ac17a5ad to preparation HEAD; no image rebuild selected. Build/install success is not claimed.

## Conditional Job creation and launch

This is the ordinary implementation Job building future analysis support; use existing native-handoff/1, not the future stage1-analysis/1 product profile. Existing limits: provider3600s, stage4800s, Job9960s including queue, verifier900s, automatic correction0. No automatic unlimited retries. New role availability is not required on the live runtime to implement it.

```bash
UUID=$(python3 -I - "$DEST/authority-identity.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))['authority_uuid'])
PY
)
mapfile -d '' VERIFY < <(python3 -I - "$PACKET/verification-argv.json" <<'PY'
import json, sys
for value in json.load(open(sys.argv[1])):
    sys.stdout.buffer.write(value.encode()+b'\0')
PY
)
VERIFY_ARGS=()
for ARG in "${VERIFY[@]}"; do VERIFY_ARGS+=("--verification=$ARG"); done
"$BIN" manager --store "$DEST/db/jobs.sqlite3" --incarnation slaw-w385623-analysis-1 --authority-uuid "$UUID" \
    create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
    --task w385623-native-analysis-1 --job-id w385623-native-analysis-1 --source installed \
    --template baton.v12.job-template.implementation-review/3 --control-profile native-handoff/1 \
    --statement "$(cat "$PACKET/TASK.txt")" \
    --acceptance 'Stage 1-A automatic retained-failure analysis and owner report; exact evidence, declared role authority, finite failure, duplicate/restart/cancel/expiry safety; focused deterministic evidence and independent substantive review.' \
    --work-scope 'Stage 1-A only: necessary v12 source and focused tests plus owning dossier evidence; no Stage 1-B/1-C behavior, broad refactor or live configuration.' \
    "${VERIFY_ARGS[@]}" > "$RUN/create.json" 2> "$RUN/create-report.log"
cat "$RUN/create-report.log"
just --justfile "$DEST/justfile" status
```

Before separately selecting start, inspect create result/report: intended task/argv/base, `/3`, native-handoff/1, exact impl/reviewer identities and scoped answer-handoff grant to baton.reviewer-native. Missing grant/readback or binding mismatch is a refusal to diagnose, not authority to patch a live instance or silently retry. The command submitted is exactly verification-argv.json, with no inline Python verification program or shell re-quoting of that string. The future acceptance module is deliberately absent now; the native candidate must add it and genuine behavior cases. It is not a preparatory pass.

```bash
just --justfile "$DEST/justfile" start
just --justfile "$DEST/justfile" monitor 10
```

Monitor exit does not stop execution. If operator selects stopping: `just --justfile "$DEST/justfile" stop`; supervisor stop alone is not runtime cessation proof. Preserve outputs/candidate/base/test accounting and exact review verdict in this Work. Native implementation → review handoff is automatic; unresolved decisions go to baton.slaw under /3. W385624 and W385625 remain blocked until canonical prerequisite acceptance. Reviewed native result returns to baton.decide for owner import/Git; no automatic host import is selected.
