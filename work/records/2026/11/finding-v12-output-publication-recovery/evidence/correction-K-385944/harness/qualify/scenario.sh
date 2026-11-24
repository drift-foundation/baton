#!/usr/bin/env bash
# scenario.sh NAME SCRIPT PHASE [world-json]  -- one dry run of `qualify-w385695.sh PHASE` or `option-a-setup.sh
# failures` (SCRIPT: qualify | setup) against scripted doubles. No engine, no container, no manager, no model.
#   START=<start-mode>   STOP=refuses   see stack-double.py
#   INTERRUPT=<seconds>  or  INTERRUPT_WHEN=<file under the run, appearing>  [INTERRUPT_DELAY=<seconds>]
#   GROUP=1              the signal goes to the script's whole process group, as a terminal's would
#   KILL_WATCHER_WHEN=<file>  SIGKILL the script's watcher when that file appears (qualify only)
# The engine double is `fake.py`; the stack double keeps the PRODUCT'S records and answers with the product's own
# `status` and `stop` (stack-double.py). Every process of a run carries HARNESS_RUN=<run dir>, so what is
# reported as left, and ended afterwards, is that run's and no other's.
set -u
H="$(dirname "$(realpath "$0")")"; P="$(dirname "$H")"
PY=/home/sl/.local/state/baton-v12-venv/bin/python
export HARNESS_TREE="${HARNESS_TREE:-/home/sl/src/baton/work/scratch/w385695-K-385897/repo}"
RUNS="${RUNS:-$P/runs}"
name=$1 which=$2 phase=$3 extra=${4:-{\}}
R="$RUNS/$name"; rm -rf "$R"; mkdir -p "$R/world" "$R/dest/distro" "$R/dest/db" "$R/dest/state" "$R/storage" "$R/bin" "$R/evidence"
export HARNESS_RUN="$R"
touch "$R/dest/db/authority.sqlite3" "$R/dest/db/jobs.sqlite3" "$R/dest/db/control.sqlite3"
ln -s "$H/fake.py" "$R/bin/docker"; ln -s "$H/fake.py" "$R/dest/distro/baton-v12-stack"
for verb in start stop status; do printf '%s:\n\t@%s %s/stack-double.py %s/dest/state %s/world %s\n' "$verb" "$PY" "$H" "$R" "$R" "$verb"; done > "$R/dest/justfile"
[ -z "${STOP:-}" ] || echo "$STOP" > "$R/world/stop-mode"
if [ "${START:-ok}" = preexisting ]; then
  # SOMEBODY ELSE'S STACK, live and recorded before this run starts anything; it carries no token of this run.
  just --justfile "$R/dest/justfile" start > "$R/world/preexisting.log" 2>&1; rm -f "$R/world/started" "$R/world/effect"
  "$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["pid"])' "$R/dest/state/manager.json" > "$R/world/preexisting.pid"
else echo "${START:-ok}" > "$R/world/start-mode"; fi
python3 - "$R" "$which" "$phase" "$extra" <<'PY'
import json, sys
R, which, phase, extra = sys.argv[1:5]
world = {"scenario": "setup" if which == "setup" else "recovery" if phase == "recovery" else "deadline", "publisher": "attempt-pub", "reviewer": "attempt-rev",
         "storage": R + "/storage", "images": {"publication": "sha256:pub", "provider": "sha256:fixture"},
         # ANOTHER INSTANCE'S CONTAINERS ON THE SAME DAEMON: a publisher and a source-mounted reviewer.
         "foreign": {"c-foreign-pub": ["attempt-other-pub", "sha256:pub", ["/srv/other-instance/storage/x/out"]],
                     "c-foreign-rev": ["attempt-other-rev", "sha256:prov", ["/srv/other-instance/storage/y/in"]]},
         "tags": {"baton-v12-publication:w385695-RUN": "sha256:pub", "baton-v12-provider:w385695-RUN": "sha256:someone-elses"}}
world.update(json.loads(extra))
json.dump(world, open(R + "/world/world.json", "w"))
json.dump({"destination": R + "/dest", "deployment": R + "/dest/deployment.json", "job_store": R + "/dest/db/jobs.sqlite3",
           "control_store": R + "/dest/db/control.sqlite3", "authority_uuid": "u"}, open(R + "/instance.json", "w"))
workers = json.loads(extra).get("workers") or [
    {"worker_id": "qualify-impl", "role": "implementation", "deployment": {"image_digest": "sha256:fixture"}},
    {"worker_id": "qualify-review", "role": "review", "deployment": {"image_digest": "sha256:fixture"}},
    {"worker_id": "qualify-publisher", "role": "publication", "deployment": {"image_digest": "sha256:pub"}}]
json.dump({"workspace_storage": R + "/storage", "workers": workers}, open(R + "/dest/deployment.json", "w"))
open(R + "/evidence/run-id", "w").write("RUN\n")
open(R + "/evidence/images.owned", "w").write("publication baton-v12-publication:w385695-RUN sha256:pub\nprovider baton-v12-provider:w385695-RUN sha256:prov\nfixture baton-v12-qualification-fixture:w385695-RUN sha256:fixture\n")
for n in (1, 2):
    json.dump({"job_id": f"job-q-{n}", "template": {"version": "baton.v12.job-template.implementation-review/1"}}, open(R + f"/evidence/option-a.create-{n}.json", "w"))
PY
if [ "$which" = setup ]; then script="$P/option-a-setup.sh"; stem="$R/evidence/option-a"; else script="$P/qualify-w385695.sh"; stem="$R/evidence/$phase"; fi
launch=(env FAKE_WORLD="$R/world" PATH="$R/bin:$PATH" TREE="$HARNESS_TREE" EVIDENCE="$R/evidence" ENGINE=docker ENGINE_SECONDS="${ENGINE_SECONDS:-60}" INSTANCE="$R/instance.json" OWNER=baton.owner
  PRODUCER_SECONDS="${PRODUCER_SECONDS:-60}" OBSERVE_SECONDS="${OBSERVE_SECONDS:-20}" JOB=job-1 STAGE=job-1/implementation EPISODE=1 DECISION=D1 JOB2=job-2 STAGE2=job-2/implementation EPISODE2=1 DECISION2=D2 bash "$script" "$phase")
if [ -n "${GROUP:-}" ]; then setsid "${launch[@]}" > "$R/out.txt" 2>&1 & else "${launch[@]}" > "$R/out.txt" 2>&1 & fi
pid=$!
appears() { local end=$(( $(date +%s) + 60 )); until [ -e "$R/$1" ]; do [ "$(date +%s)" -lt "$end" ] || { echo "   HARNESS: $1 never appeared"; return 1; }; sleep 0.05; done; }
if [ -n "${KILL_WATCHER_WHEN:-}" ] && appears "$KILL_WATCHER_WHEN"; then
  kill -KILL "$(awk '$2 == "watch" { print $1 }' "$stem.owned-pids")"; echo "   harness: SIGKILL to the watcher when $KILL_WATCHER_WHEN appeared"
fi
if [ -n "${INTERRUPT_WHEN:-}" ] && appears "$INTERRUPT_WHEN"; then INTERRUPT="${INTERRUPT_DELAY:-0}"; fi
# TERM, not INT: a non-interactive shell starts background commands with INT ignored, which no trap can undo.
if [ -n "${INTERRUPT:-}" ]; then
  sleep "$INTERRUPT"
  if [ -n "${GROUP:-}" ]; then kill -TERM -- "-$pid"; echo "   harness: TERM to the whole process group"; else kill -TERM "$pid"; echo "   harness: TERM to the script"; fi
fi
wait $pid; code=$?
echo "== $name: exit $code"
grep -E "^[0-9T:Z-]+ (FAIL|UNRESOLVED|REFUSED|cleanup|phase|failures|ok   producer)" "$R/out.txt" | cut -c22-330
python3 - "$R" <<'PY'
import json, os, sys
R = sys.argv[1]
calls = [json.loads(l) for l in open(R + "/world/calls.log")] if os.path.exists(R + "/world/calls.log") else []
eng = [c["argv"] for c in calls if c["kind"] == "engine"]
effects = [(a[0], " ".join(a[1:]) if a[0] == "image" else a[1]) for a in eng if a[0] in ("pause", "unpause", "exec", "rm", "kill", "stop") or a[:2] == ["image", "rm"]]
print("   engine effects:", effects)
# A listing is SCOPED when it names one exact attempt label or one exact container id.
print("   unscoped container listings:", len([a for a in eng if a[0] == "ps" and not any(x.startswith(("label=baton.v12.runtime_attempt_id=", "id=")) for x in a)]))
print("   stack starts asked: %d; stops asked: %d" % (os.path.exists(R + "/world/started"), open(R + "/world/stops").read().count("stopped") if os.path.exists(R + "/world/stops") else 0))
PY
echo "   product status now: $(rm -f "$R/world/status-down"; just --justfile "$R/dest/justfile" status 2>&1 | grep -E '^(manager|publisher) ' | tr -s ' ' | paste -sd';')"
echo "   start intent: $(ls "$R/evidence" | grep -E 'stack-start-(intent|reconciled)$' | paste -sd' ' || true)"
if [ -e "$R/world/preexisting.pid" ]; then
  kill -0 "$(cat "$R/world/preexisting.pid")" 2>/dev/null && echo "   the pre-existing stack process is STILL RUNNING (untouched)" || echo "   THE PRE-EXISTING STACK PROCESS WAS STOPPED"
fi
left="$(python3 "$H/owned.py" list "HARNESS_RUN=$R")"
if [ -n "$left" ]; then echo "   processes of this run still alive:"; echo "$left" | sed 's/^/      /'; python3 "$H/owned.py" kill "HARNESS_RUN=$R"; else echo "   no process of this run is left"; fi
