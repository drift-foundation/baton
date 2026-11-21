#!/usr/bin/env bash
set -euo pipefail
export GIT_OPTIONAL_LOCKS=0
REPO=/home/sl/src/baton
CFG=$REPO/work/records/2026/10/finding-v12-development-coordination-pilot/config
EV=$REPO/work/records/2026/10/finding-v12-development-coordination-pilot/evidence/checkpoint-ac17a5ad-qualification
DEST=/home/sl/baton-instances/native-handoffs-3
SHA=ac17a5add7a58fcd845a8eee7485a633ef917de3
SHORT=ac17a5ad
IMAGE=sha256:19eb459b44478f60ee16a61fcc32c2c99dd0132d7d93675adf9fb7afbe5a92b4
CREDENTIALS=/home/sl/.baton/credential-sources.json
RECORD=work/records/2026/11/finding-v12-native-agent-handoffs-discovery
cd "$REPO"
test "$(git rev-parse HEAD)" = "$SHA"
test -z "$(git status --porcelain -- v12)"
test "$(docker image inspect --format '{{.Id}}' baton-v12-worker:ac17a5ad)" = "$IMAGE"
mkdir -p "$DEST/state/task"
test ! -e "$DEST/state/task/installed-task.json"
cp "$CFG/native-installed-task-3-ac17a5ad.json" "$DEST/state/task/installed-task.json"
    # THE CANONICAL DECLARATION ORDER, read from the bound checkout
    # product rather than typed (review C3.2).
    EXPECTED="$(env PYTHONPATH="$REPO/v12/python/src" python3 -c 'import json; from baton_v12.job_manager import role_contract as r; print(json.dumps([o["name"] for o in r.contract_for(r.HANDOFF_TEMPLATE)["outputs"]]))')"
    for W in "impl-a implementation baton.claude-native" "review-a review baton.reviewer-native"; do set -- $W
        "$DEST/distro/baton-v12-stack" pool compose-worker --deployment "$DEST/deployment.json" --worker-id "$1" --role "$2" --participant "$3" \
            --template baton.v12.job-template.implementation-review/3 \
            --image-reference "baton-v12-worker:$SHORT" --image-digest "$IMAGE" --cli-build 2.1.247 --network bridge \
            --credential-sources "$CREDENTIALS" --credential claude=operator-file:w202663-development \
            --workspace-group 1001 --task-document "$DEST/state/task/installed-task.json" \
            --record "$RECORD" --checkout "$REPO" \
            --verifier-layout "$REPO/v12/worker/verifier-layout-marker.json" --into "$CFG/$1-3-$SHORT.json" 2>&1 | tee "$CFG/$1-3-$SHORT-compose.log"
    done
    python3 -I - "$SHA" "$CFG" "$DEST" "$IMAGE" "$EXPECTED" <<'PY'
import json, sys
sha, cfg, dest, image, expected = sys.argv[1:6]
expected = json.loads(expected)
d = json.load(open(f"{cfg}/native-instance-3-{sha[:8]}.json"))
dep = json.load(open(f"{dest}/deployment.json"))
for k in ("integration_target", "integration_workspace"): d[k] = dep[k]
uuid = json.load(open(f"{dest}/authority-identity.json"))["authority_uuid"]
d["workers"] = []
for w in ("impl-a", "review-a"):
    held = json.load(open(f"{cfg}/{w}-3-{sha[:8]}.json")); m = held["deployment"]["input_manifest"]
    assert held["deployment"]["schema"] == "baton.v12.single-worker-deployment/6", held["deployment"]["schema"]
    assert [o["name"] for o in m["outputs"]] == expected, (m["outputs"], expected)
    assert all(o["required"] is False for o in m["outputs"])
    assert held["deployment"]["image_digest"] == image and m["work_ref"]["authority_uuid"] == uuid
    log = open(f"{cfg}/{w}-3-{sha[:8]}-compose.log").read()
    assert "declaring " + ", ".join(expected) in log, log
    d["workers"].append(held)
assert "native_handoff_routing" in d
json.dump(d, open(f"{cfg}/native-workers-3-{sha[:8]}.json", "x"), indent=2, sort_keys=True)
print("wrote", f"{cfg}/native-workers-3-{sha[:8]}.json", "declaring", expected)
PY

just --justfile "$REPO/v12/justfile" bootstrap "$CFG/native-workers-3-ac17a5ad.json" 2>&1 | tee "$EV/instance-3-workers-bootstrap.log"
just --justfile "$DEST/justfile" status
