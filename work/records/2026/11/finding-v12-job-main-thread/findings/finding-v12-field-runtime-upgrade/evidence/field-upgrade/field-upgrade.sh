#!/usr/bin/env bash
# W386447 field runtime upgrade for M386446 (gen-21b9296e). OWNER-RUN. Nothing here builds anything.
#   --check                                     read-only: the guards against the live field state; no stop, no start
#   --run M<seq> <candidate commit> <built distro>
#        stop the held gen-21b9296e stack after its guards, upgrade its runtime IN PLACE to the built distro (stores,
#        Jobs, Works, lines and configuration kept; the 35c7fe81 runtime retired beside it), start it, and watch for
#        the ONE continuation of job-worker-inbox-386446 that carries the recorded owner answer.
# The built distro must be a frozen bundle of <candidate commit>, the owner's checkpoint containing W386447.
# Corrected for review 2026-11-27 (M386454):
#  [1] the held-state guard is the upgrade's own `runtime_upgrade.unresolved` over a DURABLE read, not a member the
#      stage document never publishes;
#  [3] THE IMAGE GUARD measures the Baton files INSTALLED in each configured immutable image ID
#      (`tools.installed_worker`: inspect, create-never-start, cp, rm) and requires them byte-equal to the candidate,
#      adapter and entrypoint included; its report is kept as the run's qualification evidence. There is NO override:
#      a resume whose provider is not told the answer cannot satisfy this selection. No positive check is a
#      `| grep -q` pipeline. The watcher exits 0 only on CONFIRMED and non-zero on timeout or an unrelated transition.
# TODAY --run REFUSES at the image guard: both configured images predate the W386447 adapter, and replacing a
# configured worker's image on an activated instance is not yet a supported, rehearsed verb (W386447 PLAN).
set -Eeuo pipefail
umask 077
trap 'echo "FAILED at line $LINENO: $BASH_COMMAND" >&2' ERR
here=$(cd "$(dirname "$0")" && pwd)
repo=$(git -C "$here" rev-parse --show-toplevel)
py=/home/sl/.local/state/baton-v12-venv/bin/python
field=/var/tmp/baton-field-instance-1
generation=$field/gen-21b9296e
dest=$generation/instance; sel=$dest/instance.json
job=job-worker-inbox-386446
request=message-3194eab720781acbaa19adee
escalation=reply-bedcfea64f8a37b16446c3f4
answer=main.owner-answer:8803fd0dc3586409ec3e69df965ea0d672bc69704aa9849351c7540c71818c5e
old_runtime=45807d865274cd00f95428e246315f748b0f50c07ac25e9d2b04bc86a8f63695
marker="THE OWNER'S DECISION ON THAT ESCALATION"
live_seconds=7200
mode=${1:-}
[[ $(id -u):$(id -g) == 1000:1000 ]] || { echo "Run as the local 1000:1000 operator"; exit 2; }
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE PYTHONPATH
export PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
# shellcheck source=field-guards.sh
source "$here/field-guards.sh"

guards() {  # <source root for the readers> <dir for the reads>
    [[ -f $sel ]] || { echo "no field instance at $generation"; exit 1; }
    [[ $(jq -r .runtime.digest "$sel") == "$old_runtime" ]] || { echo "gen-21b9296e is not at runtime 35c7fe81 (already upgraded?)"; exit 1; }
    durable_status "$1" "$sel" > "$2/guard.status.json"
    held_for_owner "$2/guard.status.json" "$job" \
        || { echo "gen-21b9296e is not M386446 held for the owner; nothing was changed"; jq -c '[.jobs[] | [.job_id, [.stages[] | [.stage_id,.state,.episode]]]]' "$2/guard.status.json"; exit 1; }
    settled "$1" "$2/guard.status.json" || { echo "a phase of gen-21b9296e is, or may be, executing; nothing was changed"; exit 1; }
    thread_read "$1" "$sel" "$job" > "$2/guard.main-thread.json"
    thread_holds_answer "$2/guard.main-thread.json" "$request" "$escalation" "$answer" \
        || { echo "M386446's main thread does not hold exactly the escalated request and the recorded, undelivered owner answer; nothing was changed"; exit 1; }
    echo "GUARDS PASSED: gen-21b9296e at runtime 35c7fe81 holds only M386446, implementation awaiting-answer, review answered, nothing executing; owner answer ${answer:0:40}… recorded for $request"
}

case "$mode" in
  --check)
    [[ $# == 1 ]]; bash -n "$0"; bash -n "$here/field-guards.sh"
    reads=$(mktemp -d /var/tmp/w386447-check.XXXXXXXX)
    guards "$repo" "$reads"
    chmod -R u+rwx "${reads:?}" && rm -r -- "${reads:?}"
    echo "(the image guard needs the engine and runs only under --run)"
    exit 0 ;;
  --run)
    [[ $# == 4 && $2 =~ ^M[1-9][0-9]*$ && $3 =~ ^[0-9a-f]{40}$ ]] \
        || { echo "usage: --run M<owner selection seq> <candidate commit> <built distro>" >&2; exit 2; } ;;
  *) echo "Choose --check or --run M<seq> <candidate commit> <built distro>" >&2; exit 2 ;;
esac
selection=$2 candidate=$3 distro=$(realpath "$4")
run=$generation/runs/$selection-runtime-upgrade
[[ ! -e $run ]] || { echo "selection $selection already has a run at $run"; exit 1; }
git -C "$repo" cat-file -e "$candidate^{commit}"
# The candidate, read from a disposable archive rather than the checkout: readers, guard rules and the source the
# images are measured against.
reader_root=$(mktemp -d /var/tmp/w386447-reader.XXXXXXXX)
git -C "$repo" archive "$candidate" v12 | tar -x -C "$reader_root"
[[ -f $reader_root/v12/python/tools/runtime_upgrade.py && -f $reader_root/v12/python/tools/installed_worker.py ]] \
    && file_has "$reader_root/v12/worker/claude_agent.py" "$marker" \
    || { echo "$candidate does not contain W386447"; exit 1; }
identity=$("$distro/baton-v12-stack" identity)
jq -e --arg c "$candidate" '.frozen and .build_stamp.commit==$c' <<<"$identity" >/dev/null || { echo "$distro is not a frozen bundle of $candidate"; exit 1; }
export DOCKER_HOST=unix:///var/run/docker.sock; unset DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH
reads=$reader_root/reads; mkdir "$reads"
guards "$reader_root" "$reads"
echo "+ image guard: the installed Baton files of each configured image ID, against $candidate"
py_at "$reader_root" -m tools.installed_worker --deployment "$dest/deployment.json" --source "$reader_root/v12" \
        --report "$reads/installed-workers.json" \
    || { echo "Refused at the image guard: nothing was stopped or changed. Both configured workers must run images whose installed Baton files are $candidate's. Measurement kept at $reads/installed-workers.json."; exit 1; }
# Every guard passed: from here on the run is recorded.
mkdir -p "$run"; cp "$reads"/* "$run/"
exec > >(tee "$run/transcript.log") 2>&1
echo "Selection $selection: upgrade gen-21b9296e from runtime 35c7fe81 to $candidate ($distro); guards and image qualification in $run"
held_attempt=$(jq -r --arg j "$job" '.jobs[0].stages[] | select(.stage_id==($j+"/implementation")) | .attempt_id' "$run/guard.status.json")
held_episode=$(jq -r --arg j "$job" '.jobs[0].stages[] | select(.stage_id==($j+"/implementation")) | .episode' "$run/guard.status.json")
echo "+ stop the held stack (stores, M386446 and its evidence kept)"
"$dest/distro/baton-v12-stack" stop --instance "$sel" | tee "$run/stop.txt"; [[ ${PIPESTATUS[0]} == 0 ]] || { echo "the stack did not stop cleanly; nothing else was changed"; exit 1; }
echo "+ upgrade the runtime in place"
"$distro/baton-v12-stack" upgrade-runtime --instance "$sel" --distro "$distro" | tee "$run/upgrade.txt"; [[ ${PIPESTATUS[0]} == 0 ]] || { echo "the upgrade refused; the stack is stopped and the runtime unchanged unless the output says otherwise"; exit 1; }
cp "$dest/runtime-upgrades.jsonl" "$run/"
echo "+ start the upgraded stack"
"$dest/distro/baton-v12-stack" start --instance "$sel" | tee "$run/start.txt"
echo "WATCH (another terminal):  $dest/distro/baton-v12-stack tui --instance $sel"
deadline=$((SECONDS+live_seconds)) verdict=PENDING
while (( SECONDS < deadline )); do
    durable_status "$reader_root" "$sel" > "$run/after.status.json" && thread_read "$reader_root" "$sel" "$job" > "$run/after.main-thread.json" \
        && verdict=$(continuation_verdict "$run/after.status.json" "$run/after.main-thread.json" "$job" "$request" "$answer" "$held_attempt" "$held_episode")
    [[ $verdict == PENDING ]] || break
    sleep 10
done
jq -c --arg j "$job" '.jobs[0].stages[] | {stage_id, state, episode, attempt_id}' "$run/after.status.json" || true
"$dest/distro/baton-v12-stack" status --instance "$sel" | tee "$run/after.status.txt" || true
echo "The stack is LEFT RUNNING. Evidence: $run. Retired runtime: $(ls -d "$dest"/distro.retired-*)."
chmod -R u+rwx "${reader_root:?}" && rm -r -- "${reader_root:?}"
case $verdict in
  CONFIRMED) echo "CONFIRMED: one new implementation attempt of $job, with $request delivered carrying ${answer:0:40}…"; exit 0 ;;
  PENDING) echo "NOT CONFIRMED: no continuation carrying the owner answer within ${live_seconds}s"; exit 1 ;;
  *) echo "NOT CONFIRMED: $verdict"; exit 1 ;;
esac
