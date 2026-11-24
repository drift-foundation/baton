#!/usr/bin/env bash
# setup-scenario.sh NAME [world-json]  -- one dry run of `option-a-setup.sh failures` against the scripted doubles.
set -u
H=/home/sl/src/baton/work/scratch/w385695-K-385929/qualify-harness
SCRIPT=${SETUP_SCRIPT:-/home/sl/src/baton/work/scratch/w385695-K-385897/option-a-setup.sh}
name=$1 extra=${2:-{\}}
R=$H/runs/setup-$name; rm -rf "$R"; mkdir -p "$R/world" "$R/dest/distro" "$R/dest/db" "$R/dest/state" "$R/evidence"
ln -s "$H/fake.py" "$R/dest/distro/baton-v12-stack"
cat > "$R/dest/stack.sh" <<STACK
#!/usr/bin/env bash
case "\$1" in
  start) touch "$R/world/started"; sleep 600 & echo "{\"pid\": \$!}" > "$R/dest/state/manager.json"; echo started;;
  stop) echo stopped >> "$R/world/stops"; kill "\$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["pid"])' "$R/dest/state/manager.json")" 2>/dev/null; rm -f "$R/dest/state/manager.json";;
esac
STACK
chmod +x "$R/dest/stack.sh"
printf 'start:\n\t@%s/dest/stack.sh start\nstop:\n\t@%s/dest/stack.sh stop\n' "$R" "$R" > "$R/dest/justfile"
python3 - "$R" "$extra" <<'PY'
import json, sys
R, extra = sys.argv[1:3]
world = {"scenario": "setup", "publisher": "p", "reviewer": "r", "storage": R, "images": {}}
world.update(json.loads(extra)); json.dump(world, open(R + "/world/world.json", "w"))
json.dump({"destination": R + "/dest", "deployment": R + "/dest/deployment.json", "job_store": R + "/dest/db/jobs.sqlite3",
           "control_store": R + "/dest/db/control.sqlite3", "authority_uuid": "u"}, open(R + "/instance.json", "w"))
open(R + "/evidence/run-id", "w").write("RUN\n")
for n in (1, 2): json.dump({"job_id": f"job-q-{n}", "template": {"version": "baton.v12.job-template.implementation-review/1"}}, open(R + f"/evidence/option-a.create-{n}.json", "w"))
PY
env EVIDENCE="$R/evidence" INSTANCE="$R/instance.json" OWNER=baton.owner PRODUCER_SECONDS=${PRODUCER_SECONDS:-60} bash "$SCRIPT" failures > "$R/out.txt" 2>&1
echo "== setup-$name: exit $?"
grep -E "^[0-9T:Z-]+ (FAIL|UNRESOLVED|cleanup|ok|failures|phase)" "$R/out.txt" | cut -c22-190
echo "   installed verbs: $(python3 -c 'import json,sys; print([json.loads(l)["argv"][1] for l in open(sys.argv[1]) if json.loads(l)["kind"]=="installed"])' "$R/world/calls.log" | tr -s ' ' | cut -c1-400)"
echo "   stack stops: $(grep -c stopped "$R/world/stops" 2>/dev/null || echo 0); record left: $([ -e "$R/dest/state/manager.json" ] && echo yes || echo no)"; cat "$R/evidence/option-a.env" 2>/dev/null | sed 's/^/   /'
pgrep -f "$R/" > /dev/null && { echo "   LEFTOVER PROCESSES"; pkill -f "$R/"; } || echo "   no process of this run is left"
