#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
packet=$(cd "$(dirname "$0")" && pwd)
repo=$(git -C "$packet" rev-parse --show-toplevel)
pin=76b2f2b2359a1211139625f8f5062d980c5f68bf
parent=sha256:1105e4639a109741f952dc364a497cd3fa5155a1dcc5064ddd6fc1a96c0fc60d
record=work/records/2026/11/finding-v12-owner-paced-manual-jobs
# The first field run (/var/tmp/baton-manual-field.WcXnE4DY, preserved) failed at the packaged
# `pool compose-worker`: the bundle did not carry provider_policy/worker_instructions.md.
# This packet builds the pin plus that one packaging correction, committed only in its own clone.
patch_sha256=9ff28a6788fd50cbda1d7ed91a59fcc49e6219dcc98b18eca0a7b9f5b1091d15
spec_sha256=05b11b252ed32a5bdddbc4c05500863e8b3db13fe3a80133cba14c58465c5843
instructions_sha256=369ccb173d0bec1b4ba109127677d611d36e327e17f11b82c3bf13bf2f28627b
py=/home/sl/.local/state/baton-v12-venv/bin/python
(cd "$packet" && sha256sum -c SHA256SUMS)
[[ $(git -C "$repo" rev-parse "$pin^{commit}") == "$pin" ]]
case "${1:-}" in
  --check) [[ $# == 1 ]]; bash -n "$0"; "$py" -B "$packet/check.py" "$repo"; exit ;;
  --run) [[ $# == 1 ]] ;;
  *) echo "Choose --check or --run" >&2; exit 2 ;;
esac
[[ -t 0 && $(id -u):$(id -g) == 1000:1000 ]] || { echo "Run interactively as the local 1000:1000 operator"; exit 2; }
for tool in git docker jq timeout; do command -v "$tool" >/dev/null; done
[[ -x ${py%/*}/pyinstaller ]]
# Name a fresh private root each time; never operate on an installed instance.
root=$(mktemp -d /var/tmp/baton-manual-field.XXXXXXXX)
exec > >(tee "$root/transcript.log") 2>&1
echo "Field evidence and retained instance: $root"
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES PYTHONPATH
export PYTHONDONTWRITEBYTECODE=1
src=$root/source; dest=$root/instance; sel=$dest/instance.json
stack=$dest/distro/baton-v12-stack; status=$dest/state/status.json
suffix=${root##*.}; suffix=${suffix,,}
net=manual-field-$suffix
job=field-survey; image=; owns_net=0; started=0
call() { echo "+ $*" >&2; timeout --kill-after=10 120 "$@"; }
cleanup() {
    code=$?; trap - EXIT; set +e
    if (( started )); then call "$stack" stop --instance "$sel" || code=1; fi
    if [[ -n $image ]]; then
        remaining=$(docker ps -aq --filter "ancestor=$image") || code=1
        if [[ -n $remaining ]]; then echo "Retained runtime(s): $remaining; inspect $root before recovery"; code=1
        else docker image rm --no-prune "$image" || code=1; fi
    fi
    if (( owns_net )); then docker network rm "$net" || code=1; fi
    echo "Exit $code; retained log, instance, status and findings under $root"
    exit "$code"
}
trap cleanup EXIT
trap 'exit 130' INT TERM
export DOCKER_BUILDKIT=0 DOCKER_HOST=unix:///var/run/docker.sock DOCKER_CONFIG=$root/docker-config
unset DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH
mkdir "$DOCKER_CONFIG"
[[ $(docker image inspect -f '{{.Id}}' "$parent") == "$parent" ]]
git init -q "$src"
git -C "$src" fetch -q --depth=1 --no-tags "$repo" "$pin"
git -C "$src" checkout -q -b field-source FETCH_HEAD
[[ $(git -C "$src" rev-parse HEAD) == "$pin" ]]
# The packaging correction, hash-pinned, as one commit in this disposable clone only.
[[ $(sha256sum < "$packet/packaging-fix.patch" | cut -d' ' -f1) == "$patch_sha256" ]]
git -C "$src" apply --index "$packet/packaging-fix.patch"
git -C "$src" -c user.name='W386295 field packaging' -c user.email='field@invalid' commit -q -m 'Carry worker_instructions.md in the packaged stack (field packet; disposable)'
built=$(git -C "$src" rev-parse HEAD)
[[ $(git -C "$src" diff --name-only "$pin" "$built") == v12/python/packaging/stack.spec && -z $(git -C "$src" status --porcelain) ]]
[[ $(sha256sum < "$src/v12/python/packaging/stack.spec" | cut -d' ' -f1) == "$spec_sha256" ]]
echo "Packaged source: $pin plus packaging-fix.patch $patch_sha256 = $built"
# Only the frozen source clone is packaged. No dependency install or registry pull.
(cd "$src/v12/python" && timeout --kill-after=10 900 "${py%/*}/pyinstaller" --noconfirm --clean --distpath "$root/bundle" --workpath "$root/build" packaging/stack.spec)
mkdir -p "$root/records/$record"
cp "$packet"/{FINDING,PLAN}.md "$root/records/$record/"
jq --arg root "$dest" --arg pin "$pin" '.state_root=$root | .line_declared_base=$pin | .canonical_target_id="manual-field" | .owner_participant="baton.slaw"' "$src/v12/instance-inputs.json" > "$root/install.json"
bootstrap() { (cd "$src/v12/python" && PYTHONPATH=src:. call "$py" -B -m tools.bootstrap "$@" --repository-source "$src"); }
bootstrap --inputs "$root/install.json" --destination "$dest" --distro "$root/bundle/distro"
call "$stack" identity > "$root/identity.json"
jq -e --arg built "$built" '.frozen and .build_stamp.commit==$built and .build_stamp.dirty==false' "$root/identity.json" >/dev/null
echo 'synthetic-field-token' > "$root/fixture-token"
jq -n --arg path "$root/fixture-token" '{schema:"baton.user-credential-sources/1",sources:[{provider:"operator-file",reference:"fixture",path:$path}]}' > "$root/registry.json"
jq -n --arg pin "$pin" '{task_id:"manual-field",base_commit:$pin}' > "$root/task.json"
compose() { call "$stack" pool compose-worker --deployment "$dest/deployment.json" --worker-id field-research --role research --participant field.research --image-reference "$1" --image-digest "$1" --cli-build 2.1.247 --provider claude --requested-model field-fixture --reported-identity field-fixture --network "$net" --credential-sources "$root/registry.json" --credential claude=operator-file:fixture --workspace-group 1000 --task-document "$root/task.json" --record "$record" --checkout "$root/records" --verifier-layout "$src/v12/worker/verifier-layout-marker.json" --into "$2"; }
# PACKAGED PREFLIGHT, before any Docker build or network: the regression check for the first run's failure.
# 1. The bundle carries the instructions at their package-relative path, byte-equal to the source.
carried=$dest/distro/_internal/baton_v12/provider_policy/worker_instructions.md
[[ -f $carried && ! -L $carried ]] || { echo "PREFLIGHT FAILED: the packaged stack does not carry $carried"; exit 1; }
[[ $(sha256sum < "$carried" | cut -d' ' -f1) == "$instructions_sha256" && $(sha256sum < "$src/v12/python/src/baton_v12/provider_policy/worker_instructions.md" | cut -d' ' -f1) == "$instructions_sha256" ]]
# 2. The packaged executable composes the research worker. The image identity here is a labelled
#    placeholder; nothing is installed from this document and no engine is asked anything.
placeholder=sha256:$(printf 'w386295 preflight placeholder, not an image' | sha256sum | cut -d' ' -f1)
compose "$placeholder" "$root/preflight-worker.json" || { echo "PREFLIGHT FAILED: packaged pool compose-worker refused the research worker"; exit 1; }
jq -e --arg d "sha256:$instructions_sha256" -f "$packet/preflight.jq" "$root/preflight-worker.json" >/dev/null
jq -e '(.workers|length)==0' "$dest/deployment.json" >/dev/null
echo "PREFLIGHT PASSED: packaged compose-worker composed the research worker; no Docker object exists yet"
ctx=$root/image-context; mkdir "$ctx"
cp "$src/v12/worker/claude_agent.py" "$ctx/"
cp -r "$src/v12/python/src/baton_v12/provider_policy" "$ctx/"
cp "$packet/fixture-claude" "$ctx/"
chmod 0644 "$ctx/claude_agent.py"
chmod -R a+rX "$ctx/provider_policy"
cat > "$ctx/Dockerfile" <<EOF
FROM ${parent#sha256:}
USER 0:0
RUN rm -f /usr/local/bin/claude
COPY fixture-claude /usr/local/bin/claude
RUN chmod 0755 /usr/local/bin/claude
COPY claude_agent.py /opt/baton/claude_agent.py
COPY provider_policy /opt/baton/provider_policy
LABEL org.opencontainers.image.revision="$pin" baton.field="$suffix"
USER 65532:65532
EOF
timeout --kill-after=10 300 docker build --pull=false --force-rm --network=none --iidfile "$root/image.id" "$ctx"
image=$(cat "$root/image.id")
[[ $(docker image inspect -f '{{.Id}}' "$image") == "$image" ]]
docker network create --internal "$net"; owns_net=1
[[ $(docker network inspect -f '{{.Internal}}' "$net") == true ]]
compose "$image" "$root/worker.json"
jq --slurpfile worker "$root/worker.json" '.workers=$worker' "$dest/install-inputs.json" > "$root/configured.json"
bootstrap --inputs "$root/configured.json"
jq -e '(.workers|length)==1 and .workers[0].role=="research"' "$dest/deployment.json" >/dev/null
# The condition the second run met, stated: this deployment declares no base of its own.
jq -e '.line_declared_base==null' "$dest/deployment.json" >/dev/null
# A pool with only research workers has no deployment-wide declared base, so every assignment names its
# source commit itself (second field run, /var/tmp/baton-manual-field.Enw7qwzp: add-phase refused without it).
phase_doc() { jq -n --arg p "$1" --arg pin "$pin" '{kind:"research",statement:("Measure "+$p),scope:[$p],depends_on:[],source_commit:$pin}'; }
phase_doc v12/QUICKSTART.md > "$root/guide.json"; phase_doc v12/README.md > "$root/overview.json"
jq -e --arg pin "$pin" '.source_commit==$pin' "$root/guide.json" "$root/overview.json" >/dev/null
jq -n --arg job "$job" '{job_id:$job,scope:["v12/QUICKSTART.md","v12/README.md"],wall_seconds:360}' > "$root/job.json"
manager() { local verb=$1; shift; call "$stack" manager "$verb" --instance "$sel" "$@"; }
todo() { call "$stack" monitor --instance "$sel" --todo --ticks 1; }
detail() { call "$stack" view --status "$status" --job "$job"; }
wait_status() {
    local label=$1 expr=$2 deadline=$((SECONDS+180))
    while (( SECONDS < deadline )); do
        if jq -e --arg job "$job" ".jobs[] | select(.job_id==\$job) | ($expr)" "$status" >/dev/null 2>&1; then
            cp "$status" "$root/$label.status.json"; return
        fi
        sleep 2
    done
    detail || true; echo "Timed out at $label; retained instance $dest"; return 1
}
report() {
    local phase=$1 file=$2 result path expected
    result=$(jq -cer --arg id "$job/$phase" '.jobs[].stages[] | select(.stage_id==$id) | .result' "$status")
    path=$(jq -er '.locator | select(startswith("file:///")) | ltrimstr("file://")' <<<"$result")/report.txt
    [[ $(realpath -e "$path") == "$dest/"* && $(realpath -e "$path") == "$path" ]]
    expected="Deterministic research: $file, $(git -C "$src" cat-file -s "$pin:$file") bytes, sha256 $(git -C "$src" show "$pin:$file" | sha256sum | cut -d' ' -f1)"
    echo "+ cat $path"; cat "$path"; echo
    printf %s "$expected" | cmp - "$path"
    jq -Sc . <<<"$result"
}
choose() { local reply; read -r -p "Type [$1] to continue, or Ctrl-C to stop: " reply; [[ $reply == "$1" ]]; }
started=1; call "$stack" start --instance "$sel"
manager create --mode manual --document "$root/job.json"
manager add-phase --job "$job" --phase guide --document "$root/guide.json"
wait_status initial '.mode=="MANUAL" and .lifecycle=="open" and (.stages|length)==1 and .stages[0].selected_at==null'
todo; detail
choose "start guide"
manager start-phase --job "$job" --phase guide
wait_status guide '.stages[0].state=="completed" and .lifecycle=="open"'
report guide v12/QUICKSTART.md | tee "$root/guide.before"
todo; detail
choose "restart manager"
call "$stack" stop --instance "$sel"; started=0
sleep 3
started=1; call "$stack" start --instance "$sel"
wait_status restarted '.lifecycle=="open" and (.stages|length)==1 and .stages[0].state=="completed"'
for f in guide restarted; do
    jq -Sc --arg job "$job" '.jobs[]|select(.job_id==$job)|[.budget.charged_milliseconds,.stages[0].attempt_id,.stages[0].result,.stages[0].selected_at]' "$root/$f.status.json" > "$root/$f.binding"
done
cmp "$root/guide.binding" "$root/restarted.binding"
report guide v12/QUICKSTART.md | tee "$root/guide.after"; cmp "$root/guide.before" "$root/guide.after"
todo; detail
choose "add overview"
manager add-phase --job "$job" --phase overview --document "$root/overview.json"
wait_status added 'any(.stages[]; (.stage_id|endswith("/overview")) and .selected_at==null and .attempt_id==null)'
detail; choose "start overview"
manager start-phase --job "$job" --phase overview
wait_status both '.lifecycle=="open" and (.stages|length)==2 and all(.stages[]; .state=="completed") and ([.stages[].attempt_id]|unique|length)==2'
report overview v12/README.md; todo | tee "$root/open.todo"; grep -F "$job" "$root/open.todo"; detail
choose "close field-survey"
manager close-job --job "$job"
wait_status closed '.lifecycle=="closed" and all(.stages[]; .state=="completed")'
todo | tee "$root/closed.todo"
if grep -F "$job" "$root/closed.todo"; then exit 1; fi
detail | tee "$root/closed.detail"
grep -F '2 finished · 0 failed · 0 never selected' "$root/closed.detail"
report guide v12/QUICKSTART.md; report overview v12/README.md
