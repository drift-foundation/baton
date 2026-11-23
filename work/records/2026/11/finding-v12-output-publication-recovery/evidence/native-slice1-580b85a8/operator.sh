#!/usr/bin/env bash
set -euo pipefail
REPO=/home/sl/src/baton
PACKET=$REPO/work/records/2026/11/finding-v12-output-publication-recovery/evidence/native-slice1-580b85a8
BASE=580b85a85930672aa3bbb1e702f05e4926c276e3
SRC=$REPO/work/scratch/w385695-source-580b85a8
RUN=$REPO/work/scratch/w385695-kickoff-1
DEST=/home/sl/baton-instances/native-w385695-publication-1
DISTRO=$REPO/v12/python/build/out/distro
IMAGE=sha256:82c0a2c7e735fe5344cc9e9f4942a928120363c0a1532d25bf326e3510bebb76
TEMPLATE=baton.v12.job-template.implementation-review/4
RECORD=work/records/2026/11/finding-v12-output-publication-recovery
STEP=${1:-check}
case "$STEP" in check|prepare|create|start) ;; *) echo 'Use check|prepare|create|start' >&2; exit 2;; esac
cmp "$0" "$PACKET/operator.sh"
# Read-only checks. No test/build/instance/provider operation.
python3 -I - "$REPO" "$PACKET" "$BASE" "$DISTRO" "$IMAGE" <<'PY'
import hashlib,json,pathlib,subprocess,sys,os
repo,p,base,distro,image=sys.argv[1:];repo=pathlib.Path(repo);p=pathlib.Path(p);distro=pathlib.Path(distro)
for name,want in json.loads((p/'inputs-manifest.json').read_text()).items():
    assert hashlib.sha256((p/name).read_bytes()).hexdigest()==want,name
for name,want in json.loads((p/'source-inputs.json').read_text()).items():
    raw=subprocess.check_output(['git','-C',str(repo),'show',base+':'+name])
    assert hashlib.sha256(raw).hexdigest()==want,name
assert not distro.is_symlink()
entries={}
for f in sorted(distro.rglob('*')):
    if f.is_symlink():
        assert f.resolve().is_relative_to(distro.resolve()) and f.exists(),str(f)
        entries[str(f.relative_to(distro))]='link:'+os.readlink(f)
    elif f.is_file(): entries[str(f.relative_to(distro))]=hashlib.sha256(f.read_bytes()).hexdigest()
    else: assert f.is_dir(),str(f)
assert entries==json.loads((p/'runtime-manifest.json').read_text())['entries'],'runtime drift'
identity=json.loads(subprocess.check_output([str(distro/'baton-v12-stack'),'identity']))
assert identity==json.loads((p/'bundle-identity.json').read_text()),'bundle identity'
assert subprocess.check_output(['docker','image','inspect','baton-v12-worker:580b85a8','--format','{{.Id}}'],text=True).strip()==image
assert 0<len((p/'TASK.txt').read_text().rstrip('\n'))<=4096
argv=json.loads((p/'verification-argv.json').read_text());assert argv[:2]==['env','BATON_V12_DISK_ROOT=/scratch'] and all(isinstance(a,str) and a for a in argv)
print('Pinned inputs/runtime/image verified. Provider selection and live execution authority remain separate.')
PY
if [[ "$STEP" == check ]]; then exit 0; fi
# Set only after owner selects this Job's separate Claude/Opus role contexts and execution.
: "${W385695_OWNER_SELECTION:?Set to claude-opus-separate-roles only after explicit owner selection for W385695}"
[[ "$W385695_OWNER_SELECTION" == claude-opus-separate-roles ]]
if [[ "$STEP" == prepare ]]; then
    [[ ! -e "$DEST" && ! -L "$DEST" && ! -e "$SRC" && ! -L "$SRC" && ! -e "$RUN" && ! -L "$RUN" ]]
    git clone --no-local "$REPO" "$SRC"
    git -C "$SRC" checkout --detach "$BASE"
    mkdir "$RUN"
    just --justfile "$SRC/v12/justfile" bootstrap "$PACKET/bootstrap-inputs.json" "$DEST" "$DISTRO" "--repository-source $SRC"
    mkdir -p "$DEST/state/task"
    cp "$PACKET/installed-task.json" "$DEST/state/task/installed-task.json"
    for SPEC in 'impl-a implementation baton.claude-native' 'review-a review baton.reviewer-native'; do
        read -r WORKER ROLE PARTICIPANT <<< "$SPEC"
        "$DEST/distro/baton-v12-stack" pool compose-worker --deployment "$DEST/deployment.json" --worker-id "$WORKER" --role "$ROLE" --participant "$PARTICIPANT" \
            --template "$TEMPLATE" --image-reference baton-v12-worker:580b85a8 --image-digest "$IMAGE" --cli-build 2.1.247 --network bridge \
            --credential-sources /home/sl/.baton/credential-sources.json --credential claude=operator-file:w202663-development --workspace-group 1001 \
            --task-document "$DEST/state/task/installed-task.json" --record "$RECORD" --checkout "$SRC" --verifier-layout "$SRC/v12/worker/verifier-layout-marker.json" --into "$RUN/$WORKER.json"
    done
    python3 -I - "$PACKET" "$RUN" "$DEST" <<'PY'
import json,pathlib,sys
p,run,dest=map(pathlib.Path,sys.argv[1:]);d=json.loads((p/'bootstrap-inputs.json').read_text());dep=json.loads((dest/'deployment.json').read_text())
for key in ('integration_target','integration_workspace'): d[key]=dep[key]
d['workers']=[json.loads((run/(w+'.json')).read_text()) for w in ('impl-a','review-a')]
contract=json.loads((p/'role-contract.json').read_text())
for worker in d['workers']: assert worker['deployment']['input_manifest']['outputs']==contract['outputs']
assert len({w['participant'] for w in d['workers']})==2
(run/'workers.json').write_text(json.dumps(d,indent=2)+'\n')
PY
    just --justfile "$SRC/v12/justfile" bootstrap "$RUN/workers.json" '' '' "--repository-source $SRC"
    just --justfile "$DEST/justfile" repository
    just --justfile "$DEST/justfile" status
    exit 0
fi
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$BASE" ]]
[[ -z "$(git -C "$SRC" status --porcelain -- v12)" ]]
if [[ "$STEP" == create ]]; then
    UUID=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["authority_uuid"])' "$DEST/authority-identity.json")
    mapfile -d '' VERIFY < <(python3 -I - "$PACKET/verification-argv.json" <<'PY'
import json,sys
for arg in json.load(open(sys.argv[1])): sys.stdout.buffer.write(arg.encode()+b'\0')
PY
)
    VERIFY_ARGS=(); for ARG in "${VERIFY[@]}"; do VERIFY_ARGS+=("--verification=$ARG"); done
    "$DEST/distro/baton-v12-stack" manager --store "$DEST/db/jobs.sqlite3" --incarnation slaw-w385695-publication-1 --authority-uuid "$UUID" \
        create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
        --task w385695-native-publication-1 --job-id w385695-native-publication-1 --source installed --template "$TEMPLATE" \
        --control-profile native-handoff-heavy/1 --provider-turn-seconds 7200 --statement "$(cat "$PACKET/TASK.txt")" \
        --acceptance 'REC-9 checkpoint1: real owner inspection/decision/admission, exact original output and verifier attribution, immutable history, restart/replay and zero execution from partial closed gates; independent review of actual candidate.' \
        --work-scope 'W385695 checkpoint1 only: v12 inspection, decision and closed admission with focused tests/docs and owning dossier evidence; no publication execution or unrelated changes.' \
        "${VERIFY_ARGS[@]}" > "$RUN/create.json" 2> "$RUN/create-report.log"
    cat "$RUN/create-report.log"
fi
python3 -I - "$RUN/create.json" "$PACKET" <<'PY'
import json,pathlib,sys
held=json.load(open(sys.argv[1]));p=pathlib.Path(sys.argv[2])
assert held['job_id']=='w385695-native-publication-1'
assert held['template']['version']=='baton.v12.job-template.implementation-review/4'
assert held['control']['resolved']==json.loads((p/'development-profile.json').read_text())
assert held['execution_limits']['boundaries']['provider_turn']['seconds']==7200
assert held['execution_limits']['boundaries']['ordinary_verification']['seconds']==900
assert held['servable']=={'implementation':['impl-a'],'review':['review-a']}
print('Exact /4 heavy development admission and both lanes verified.')
PY
if [[ "$STEP" == start ]]; then
    just --justfile "$DEST/justfile" start
    just --justfile "$DEST/justfile" monitor 10
else
    just --justfile "$DEST/justfile" status
fi
