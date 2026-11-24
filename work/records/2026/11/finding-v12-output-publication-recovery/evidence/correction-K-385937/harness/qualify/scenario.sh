#!/usr/bin/env bash
# scenario.sh NAME PHASE [key=value world overrides as JSON fragment]  -- one dry run of the qualification
# script against the scripted doubles. Prints the phase's exit status and what the engine was asked to do.
set -u
H=/home/sl/src/baton/work/scratch/w385695-K-385929/qualify-harness
SCRIPT=${SCRIPT:-/home/sl/src/baton/work/scratch/w385695-K-385897/qualify-w385695.sh}
name=$1 phase=$2 extra=${3:-{\}}
# THE INSTALLED LAYOUT IS THE REVIEWED TREE'S OWN (`tools.instance.layout`), not one this harness invents:
# stores under db/, the runtime under distro/, the stack's process records under state/. TREE is the real
# reviewed tree, so the script's layout check runs against the real `layout()`.
TREE_REAL=${TREE_REAL:-/home/sl/src/baton/work/scratch/w385695-K-385897/repo}
R=$H/runs/$name; rm -rf "$R"; mkdir -p "$R/world" "$R/dest/distro" "$R/dest/db" "$R/dest/state" "$R/storage" "$R/bin" "$R/evidence"
touch "$R/dest/db/authority.sqlite3" "$R/dest/db/jobs.sqlite3" "$R/dest/db/control.sqlite3"
ln -s "$H/fake.py" "$R/bin/docker"; ln -s "$H/fake.py" "$R/dest/distro/baton-v12-stack"
# THE STACK DOUBLE keeps the product's own process records: `start` records a live process under state/, `stop`
# ends it. START selects how a start goes: ok | fail-clean (fails, records nothing) | fail-partial (records a
# live process, then fails) | preexisting (a live record is already there before this run starts anything).
cat > "$R/dest/stack.sh" <<STACK
#!/usr/bin/env bash
case "\$1" in
  start) touch "$R/world/started"
         case "${START:-ok}" in
           fail-clean) echo "could not start"; exit 1;;
           *) sleep 600 & echo "{\"pid\": \$!}" > "$R/dest/state/manager.json"; echo started
              [ "${START:-ok}" = fail-partial ] && exit 1; exit 0;;
         esac;;
  stop) echo stopped >> "$R/world/stops"; kill "\$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["pid"])' "$R/dest/state/manager.json")" 2>/dev/null; rm -f "$R/dest/state/manager.json";;
  status) echo status;;
esac
STACK
chmod +x "$R/dest/stack.sh"
printf 'start:\n\t@%s/dest/stack.sh start\nstop:\n\t@%s/dest/stack.sh stop\nstatus:\n\t@%s/dest/stack.sh status\n' "$R" "$R" "$R" > "$R/dest/justfile"
if [ "${START:-ok}" = preexisting ]; then sleep 600 & echo "{\"pid\": $!}" > "$R/dest/state/manager.json"; echo $! > "$R/world/preexisting.pid"; fi
python3 - "$R" "$phase" "$extra" <<'PY'
import json, sys
R, phase, extra = sys.argv[1:4]
world = {"scenario": "recovery" if phase == "recovery" else "deadline", "publisher": "attempt-pub", "reviewer": "attempt-rev", "storage": R + "/storage",
         "images": {"publication": "sha256:pub", "provider": "sha256:fixture"},
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
PY
env FAKE_WORLD="$R/world" PATH="$R/bin:$PATH" TREE="$TREE_REAL" EVIDENCE="$R/evidence" ENGINE=docker INSTANCE="$R/instance.json" OWNER=baton.owner \
  JOB=job-1 STAGE=job-1/implementation EPISODE=1 DECISION=D1 JOB2=job-2 STAGE2=job-2/implementation EPISODE2=1 DECISION2=D2 \
  bash "$SCRIPT" "$phase" > "$R/out.txt" 2>&1 &
pid=$!
# TERM, not INT: a non-interactive shell starts background commands with INT ignored, which no trap can undo.
if [ -n "${INTERRUPT:-}" ]; then sleep "$INTERRUPT"; kill -TERM "$pid"; fi
wait $pid; code=$?
echo "== $name: exit $code"
grep -E "^[0-9T:Z-]+ (FAIL|UNRESOLVED|REFUSED|cleanup|phase)" "$R/out.txt" | cut -c22-200
python3 - "$R" <<'PY'
import json, sys
calls = [json.loads(l) for l in open(sys.argv[1] + "/world/calls.log")]
effects = [(c["argv"][0], c["argv"][1] if c["argv"][0] != "image" else " ".join(c["argv"][1:])) for c in calls if c["kind"] == "engine" and c["argv"][0] in ("pause", "unpause", "exec", "rm", "kill", "stop") or (c["kind"] == "engine" and c["argv"][:2] == ["image", "rm"])]
print("   engine effects:", effects)
listed_all = [c["argv"] for c in calls if c["kind"] == "engine" and c["argv"][0] == "ps" and not any(a.startswith("label=baton.v12.runtime_attempt_id=") for a in c["argv"])]
print("   unscoped container listings:", len(listed_all))
print("   stack stops:", open(sys.argv[1] + "/world/stops").read().count("stopped") if __import__("os").path.exists(sys.argv[1] + "/world/stops") else 0)
PY
if [ -e "$R/world/preexisting.pid" ]; then
  kill -0 "$(cat "$R/world/preexisting.pid")" 2>/dev/null && echo "   the pre-existing stack process is STILL RUNNING (untouched)" || echo "   THE PRE-EXISTING STACK PROCESS WAS STOPPED"
  kill "$(cat "$R/world/preexisting.pid")" 2>/dev/null
fi
[ -e "$R/dest/state/manager.json" ] && { echo "   A STACK PROCESS RECORD REMAINS"; kill "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["pid"])' "$R/dest/state/manager.json")" 2>/dev/null; }
pgrep -f "$R/" > /dev/null && { echo "   LEFTOVER PROCESSES:"; pgrep -af "$R/" | cut -c1-160; } || echo "   no process of this run is left"
