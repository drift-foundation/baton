#!/usr/bin/env bash
# W385331 runtime qualification of native-handoffs-2 -- the guarded steps.
#
# Review 2026-11-21T00-55-22Z C3.3: every step is one guarded block under
# `set -euo pipefail`, so a failed guard, a failed pipeline or a failed command
# ENDS the step with the status of that command and nothing after it runs; a
# log is written through `tee` without replacing the status. Every consuming
# step first re-verifies the ONE bound checkpoint: HEAD equals the bound SHA,
# the working tree is clean under v12/, the bound file still describes that
# SHA with the pinned accepted manifests (`native-handoffs-2-bind.py --check`),
# and every dirty path of the WHOLE repository is a named generated record of
# this qualification (`native-handoffs-2-tree.py`, M385402: the build stamp
# observes the whole repository, so `bind`'s own untracked records make a
# later bundle truthfully `dirty: true`; the stamp is held to that truth, never
# demanded clean and never falsified). Owner-reserved steps are marked (O) in PACKET.md; this helper
# runs whatever step it is given and selects nothing.
#
#   bash native-handoffs-2-qualify.sh bind                 # K
#   bash native-handoffs-2-qualify.sh bundle               # K, on selection
#   bash native-handoffs-2-qualify.sh image                # O (engine build)
#   bash native-handoffs-2-qualify.sh install              # O
#   bash native-handoffs-2-qualify.sh compose              # K
#   bash native-handoffs-2-qualify.sh repeat               # O
#   JOB=... STMT=... bash native-handoffs-2-qualify.sh create   # O
#   bash native-handoffs-2-qualify.sh start                # O (the live selection)
#
# Environment (defaults are the real deployment; the checks override them with
# disposable fixtures): QUALIFY_REPO (checkout), QUALIFY_DEST (instance
# destination), QUALIFY_PACKAGING_ROOT, QUALIFY_TMP, QUALIFY_PYTHON,
# QUALIFY_CREDENTIALS, QUALIFY_IMAGE_REF (the engine tag), QUALIFY_DECLARED
# (`--declared` by default: the source identity also binds the test runner's
# declared consumed inputs; the checks pass an empty value on fixtures that do
# not carry those inputs), JOB, STMT.
set -euo pipefail

REPO="${QUALIFY_REPO:-/home/sl/src/baton}"
DEST="${QUALIFY_DEST:-/home/sl/baton-instances/native-handoffs-2}"
PACKAGING_ROOT="${QUALIFY_PACKAGING_ROOT:-/var/tmp/baton-v12-handoffs-2/packaging}"
TMP="${QUALIFY_TMP:-/var/tmp/baton-v12-handoffs-2/tmp}"
PYTHON="${QUALIFY_PYTHON:-/home/sl/.local/state/baton-v12-venv/bin/python}"
CREDENTIALS="${QUALIFY_CREDENTIALS:-/home/sl/.baton/credential-sources.json}"
RECORD="work/records/2026/11/finding-v12-native-agent-handoffs-discovery"
PILOT="work/records/2026/10/finding-v12-development-coordination-pilot"
CFG="$REPO/$PILOT/config"
EV="$REPO/$PILOT/evidence"
BIND="$CFG/native-handoffs-2-bind.py"
TREE="$CFG/native-handoffs-2-tree.py"
BOUND="$CFG/native-bound-2.json"
DECLARED="${QUALIFY_DECLARED-"--declared"}"
MANIFESTS=("$EV/native-handoffs-composer/manifest.json" "$EV/native-handoffs-1-correction-2/manifest.json")
export GIT_OPTIONAL_LOCKS=0

step="${1:-}"
[ -n "$step" ] || { echo "refused: name one step (bind|check|bundle|image|install|compose|repeat|create|start)" >&2; exit 2; }
cd "$REPO"

clean_tree() {
    local lines
    lines="$(git status --porcelain -- v12 | wc -l)"
    [ "$lines" = 0 ] || { echo "refused: v12/ has $lines changed or untracked path(s); the qualification consumes a clean checkout only" >&2; exit 2; }
}

bound_sha() {
    [ -f "$BOUND" ] || { echo "refused: no binding at $BOUND; run the bind step first" >&2; exit 2; }
    python3 -I -c "import json,sys; print(json.load(open(sys.argv[1]))['sha'])" "$BOUND"
}

check() {
    # THE GUARD EVERY CONSUMING STEP RUNS FIRST. Each test fails the step with
    # its own status; nothing below a failed check executes.
    clean_tree
    SHA="$(bound_sha)"
    [ "$(git rev-parse HEAD)" = "$SHA" ] || { echo "refused: HEAD $(git rev-parse HEAD) is not the bound checkpoint $SHA" >&2; exit 2; }
    python3 -I "$BIND" --repo "$REPO" --sha "$SHA" --manifests "${MANIFESTS[@]}" --check "$BOUND"
    SHORT="${SHA:0:8}"
    tree_state
}

identity() {
    # THE CONTENT-BOUND SOURCE IDENTITY of the bound checkout (tools/source_identity):
    # HEAD, every changed byte under v12/ (must be none) and the declared consumed
    # inputs. Written outside the tree; the inventory records its digest.
    mkdir -p "$TMP"
    env PYTHONPATH=v12/python/src:v12/python "$PYTHON" -m tools.source_identity --repo "$REPO" $DECLARED v12 > "$TMP/source-identity-$SHORT.json"
}

tree_state() {
    # EVERY DIRTY PATH OF THE WHOLE REPOSITORY, classified; only this
    # qualification's own generated records for $SHORT may be present.
    # $1 (optional): where to record the inventory; $2 (optional): a stamp to hold truthful.
    identity
    python3 -I "$TREE" --repo "$REPO" --sha "$SHA" --identity "$TMP/source-identity-$SHORT.json" ${1:+--out "$1"} ${2:+--stamp "$2"}
}

case "$step" in
bind)
    clean_tree
    SHA="$(git rev-parse HEAD)"
    python3 -I "$BIND" --repo "$REPO" --sha "$SHA" --manifests "${MANIFESTS[@]}" --out "$BOUND"
    python3 -I - "$SHA" "$CFG" <<'PY'
import json, sys
sha, cfg = sys.argv[1:3]
d = json.load(open(f"{cfg}/native-instance-handoffs-2.unbound.json")); d["line_declared_base"] = d["canonical_target_id"] = sha
json.dump(d, open(f"{cfg}/native-instance-2-{sha[:8]}.json", "x"), indent=2, sort_keys=True)
t = json.load(open(f"{cfg}/native-installed-task-handoffs-2.unbound.json")); t["declared_base"] = sha
json.dump(t, open(f"{cfg}/native-installed-task-2-{sha[:8]}.json", "x"), indent=2, sort_keys=True)
print("bound documents written for", sha)
PY
    ;;
check)
    check
    echo "ok: HEAD $SHA, v12/ clean, binding verified"
    ;;
bundle)
    check
    G="$EV/checkpoint-$SHORT-packaging"; mkdir -p "$PACKAGING_ROOT" "$TMP" "$G"
    tree_state "$G/tree-state.before.json"      # the evidence directory itself is now one generated record
    env TMPDIR="$TMP" BATON_V12_STACK_TEST_ROOT="$PACKAGING_ROOT" BATON_V12_DISK_ROOT="$PACKAGING_ROOT" \
        just --justfile v12/justfile test-packaging 2>&1 | tee "$G/build-and-gate.log"
    cp v12/python/packaging/build-stamp.json "$G/build-stamp.json"
    # THE STAMP IS HELD TO THE TRUTH, NOT TO "CLEAN": it must name $SHA and its
    # dirty/changed_entries must equal the inventory taken now, every entry a
    # generated record of this qualification. (v12/ clean is already proved.)
    tree_state "$G/tree-state.after.json" "$G/build-stamp.json"
    v12/python/build/out/distro/baton-v12-stack --version | tee "$G/version.txt"
    v12/python/build/out/distro/baton-v12-stack identity | tee "$G/bundle-identity.json"
    sha256sum v12/python/build/out/distro/baton-v12-stack | tee "$G/distro-sha256.txt"
    [ "$(v12/python/build/out/distro/baton-v12-stack pool compose-worker --help | grep -c -- --template)" -ge 1 ]
    ;;
image)
    check
    R="$EV/worker-image-$SHORT"; mkdir -p "$R"; mkdir -p "$TMP"
    timeout 1800s docker build --pull=false --memory 2g --cpu-period 100000 --cpu-quota 100000 \
        --iidfile "$R/image.id" -t "${QUALIFY_IMAGE_REF:-baton-v12-worker:$SHORT}" -f v12/worker/Dockerfile.claude v12 2>&1 | tee "$R/build.log"
    IMAGE="sha256:$(cut -d: -f2 "$R/image.id")"
    docker image inspect "$IMAGE" --format '{{json .Id}} {{json .Config.Entrypoint}} {{json .Config.User}} {{json .Created}}' | tee "$R/inspect.json"
    docker run --rm --network none --entrypoint sha256sum "$IMAGE" /opt/baton/claude_agent.py /opt/baton/baton_worker.py | tee "$R/adapter-in-image.sha256"
    for f in v12/worker/claude_agent.py v12/worker/baton_worker.py; do
        want="$(git show "$SHA:$f" | sha256sum | cut -d' ' -f1)"
        grep -q "^$want " "$R/adapter-in-image.sha256" || { echo "refused: $f in the image is not the bytes of the checkpoint ($want)" >&2; exit 2; }
    done
    (cd v12/python && env TMPDIR="$TMP" PYTHONPATH=src "$PYTHON" -m unittest -v tests.manager.test_dogfood_image 2>&1 | tee "$R/image-gate.log")
    ;;
install)
    check
    just --justfile v12/justfile bootstrap "$CFG/native-instance-2-$SHORT.json" "$DEST" v12/python/build/out/distro
    cat "$DEST/authority-identity.json"
    python3 -I - "$SHA" "$DEST" "$EV/checkpoint-$SHORT-packaging/build-stamp.json" <<'PY'
import json, sys
sha, dest, recorded = sys.argv[1:4]
d = json.load(open(f"{dest}/instance.json"))
stamp = d["identity"]["build_stamp"]; held = json.load(open(recorded))
# THE INSTALLED BUNDLE CARRIES THE STAMP THE BUNDLE STEP RECORDED AND HELD TRUTHFUL:
# same commit ($SHA), same dirty/changed_entries, the same document.
assert stamp["commit"] == sha, (stamp, sha)
assert stamp == held, ("the installed stamp is not the recorded bundle stamp", stamp, held)
print("instance", d["authority_uuid"], "bundle", d["identity"]["sha256"], "stamp", stamp["commit"][:8], "dirty", stamp["dirty"], "changed_entries", stamp.get("changed_entries"))
PY
    just --justfile "$DEST/justfile" status
    just --justfile "$DEST/justfile" repository
    ;;
compose)
    check
    R="$EV/worker-image-$SHORT"; IMAGE="sha256:$(cut -d: -f2 "$R/image.id")"
    mkdir -p "$DEST/state/task"; [ -e "$DEST/state/task/installed-task.json" ] || cp "$CFG/native-installed-task-2-$SHORT.json" "$DEST/state/task/installed-task.json"
    # THE CANONICAL DECLARATION ORDER, read from the bound checkout
    # product rather than typed (review C3.2).
    EXPECTED="$(env PYTHONPATH=v12/python/src "$PYTHON" -c 'import json; from baton_v12.job_manager import role_contract as r; print(json.dumps([o["name"] for o in r.contract_for(r.HANDOFF_TEMPLATE)["outputs"]]))')"
    for W in "impl-a implementation baton.claude-native" "review-a review baton.reviewer-native"; do set -- $W
        "$DEST/distro/baton-v12-stack" pool compose-worker --deployment "$DEST/deployment.json" --worker-id "$1" --role "$2" --participant "$3" \
            --template baton.v12.job-template.implementation-review/3 \
            --image-reference "${QUALIFY_IMAGE_REF:-baton-v12-worker:$SHORT}" --image-digest "$IMAGE" --cli-build 2.1.247 --network bridge \
            --credential-sources "$CREDENTIALS" --credential claude=operator-file:w202663-development \
            --workspace-group 1001 --task-document "$DEST/state/task/installed-task.json" \
            --record "$RECORD" --checkout "$REPO" \
            --verifier-layout "$REPO/v12/worker/verifier-layout-marker.json" --into "$CFG/$1-2-$SHORT.json" 2>&1 | tee "$CFG/$1-2-$SHORT-compose.log"
    done
    python3 -I - "$SHA" "$CFG" "$DEST" "$IMAGE" "$EXPECTED" <<'PY'
import json, sys
sha, cfg, dest, image, expected = sys.argv[1:6]
expected = json.loads(expected)
d = json.load(open(f"{cfg}/native-instance-2-{sha[:8]}.json"))
dep = json.load(open(f"{dest}/deployment.json"))
for k in ("integration_target", "integration_workspace"): d[k] = dep[k]
uuid = json.load(open(f"{dest}/authority-identity.json"))["authority_uuid"]
d["workers"] = []
for w in ("impl-a", "review-a"):
    held = json.load(open(f"{cfg}/{w}-2-{sha[:8]}.json")); m = held["deployment"]["input_manifest"]
    assert held["deployment"]["schema"] == "baton.v12.single-worker-deployment/6", held["deployment"]["schema"]
    assert [o["name"] for o in m["outputs"]] == expected, (m["outputs"], expected)
    assert all(o["required"] is False for o in m["outputs"])
    assert held["deployment"]["image_digest"] == image and m["work_ref"]["authority_uuid"] == uuid
    log = open(f"{cfg}/{w}-2-{sha[:8]}-compose.log").read()
    assert "declaring " + ", ".join(expected) in log, log
    d["workers"].append(held)
assert "native_handoff_routing" in d
json.dump(d, open(f"{cfg}/native-workers-2-{sha[:8]}.json", "x"), indent=2, sort_keys=True)
print("wrote", f"{cfg}/native-workers-2-{sha[:8]}.json", "declaring", expected)
PY
    ;;
repeat)
    check
    just --justfile v12/justfile bootstrap "$CFG/native-workers-2-$SHORT.json"
    just --justfile "$DEST/justfile" status
    ;;
create)
    check
    JOB="${JOB:-}"; STMT="${STMT:-}"
    [ -n "$JOB" ] && [ "$JOB" != PENDING-SELECTION ] || { echo "refused: JOB is a pending selection; the coordinator names the Job before this step runs" >&2; exit 2; }
    [ -n "$STMT" ] && [ -f "$STMT" ] || { echo "refused: STMT is a pending selection; name the byte-exact statement file" >&2; exit 2; }
    BIN="$DEST/distro/baton-v12-stack"
    UUID="$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["authority_uuid"])' "$DEST/authority-identity.json")"
    just --justfile "$DEST/justfile" status
    mkdir -p "$EV/native-handoffs-2-qualification"
    "$BIN" manager --store "$DEST/db/jobs.sqlite3" --incarnation slaw-create-handoffs-2 --authority-uuid "$UUID" \
        create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
        --task "$JOB" --job-id "$JOB" --template baton.v12.job-template.implementation-review/3 --control-profile native-handoff/1 \
        --statement "$(cat "$STMT")" \
        --acceptance "${ACCEPTANCE:-The acceptance criterion of the Job as stated.}" \
        --work-scope v12/python --test-scope v12/python/tests \
        --verification env --verification BATON_V12_STACK_TEST_ROOT=/scratch --verification BATON_V12_DISK_ROOT=/scratch \
        --verification PYTHONPATH=v12/python/src:v12/python --verification python3 --verification=-m --verification unittest --verification=-v \
        --verification tests.job_manager.test_job_control > "$EV/native-handoffs-2-qualification/create-$JOB.json" 2> "$EV/native-handoffs-2-qualification/create-$JOB.report.log"
    cat "$EV/native-handoffs-2-qualification/create-$JOB.report.log"
    # THE READBACK IS THE COMMAND'S OWN SUPPORTED OUTPUT: the create answer on
    # stdout and the installer report on stderr (`bootstrap.prepare` through
    # the creation binding), which states the routing selection and the
    # answering grant it made in the new Work's own scope. No store is opened
    # here (review 2026-11-21T01-49-15Z); the routing expected is read from the
    # BOUND INSTANCE DOCUMENT, an input of this qualification.
    python3 -I - "$SHA" "$CFG" "$EV/native-handoffs-2-qualification/create-$JOB.json" "$EV/native-handoffs-2-qualification/create-$JOB.report.log" <<'PY'
import json, sys
sha, cfg, answer, report = sys.argv[1:5]
held = json.loads(open(answer).read())
assert held["template"]["version"] == "baton.v12.job-template.implementation-review/3", held["template"]
assert held["control"]["profile"] == "native-handoff/1", held["control"]
routing = json.loads(open(f"{cfg}/native-instance-2-{sha[:8]}.json").read())["native_handoff_routing"]
lines = open(report).read().splitlines()
# the report's own formats (`bootstrap._compose`): "routing%-14s reviewer %s, decisions to %s" % ("", …),
# "work  %-14s already exists; left alone" (the command reserved the Work before its installer
# preparation ran, so the installer finds it) and "answer%-14s %s to %s in its own scope; no review grant".
for wanted in ("routing%-14s reviewer %s, decisions to %s" % ("", routing["reviewer"], routing["decision_recipient"]),
               "work  %-14s already exists; left alone" % held["work_id"],
               "grant %-14s approve/review/verify/integrate in its own scope" % held["work_id"],
               "answer%-14s answer-handoff to %s in its own scope; no review grant" % ("", routing["reviewer"])):
    assert wanted in lines, "the create report lacks the line %r; it said:\n%s" % (wanted, "\n".join(lines))
print("created", held["work_id"], "template", held["template"]["version"], "profile", held["control"]["profile"])
print("reported by the command: routing", json.dumps(routing), "and answer-handoff to", routing["reviewer"], "in the Work scope")
PY
    ;;
start)
    check
    just --justfile "$DEST/justfile" start
    just --justfile "$DEST/justfile" status
    ;;
*)
    echo "refused: unknown step $step" >&2; exit 2 ;;
esac
