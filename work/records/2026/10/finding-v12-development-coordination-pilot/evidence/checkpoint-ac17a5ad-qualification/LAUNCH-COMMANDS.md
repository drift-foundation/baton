# Prepared instance-3 launch commands — M385496

Preparation only, baton.codxpc, 2026-11-21. No commands below were executed. The owner must select the proposed task and authorize installation/launch before execution. Preserve native-handoffs-2 unchanged. Run blocks in order in one Bash session; stop on any failure. These are direct product commands, not a qualification helper. No old binding helper is used.

This supersedes the unexecuted commands and missing-packaging qualification in RECOMMENDATION.md for this preparation: packaging owner summary is 24 tests / 14.501s / OK (full log unconfirmed); image-byte-verification.json establishes all three exact committed worker files. Neither is rerun. Deterministic in-image fixtures need engine execution, not a live model. The proposed useful native Job exercises real implementation/review workflow; clarification coverage is conditional on a natural question, never induced. Source acceptance is not native Job acceptance.

## 1. Identity checks and absolute paths

```bash
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
JOB=invocation-ended-wording-1
STMT=$EV/native-task-invocation-ended-wording-1.txt
ACCEPTANCE='Ended invocation duration is labelled honestly while verification remains active; active and terminal timing, qualifications, freshness and causes remain correct across shared status/monitor views; focused deterministic and mandatory four-module verification pass.'
cd "$REPO"
test "$(git rev-parse HEAD)" = "$SHA"
test -z "$(git status --porcelain -- v12)"
printf '%s  %s\n' 601ef8dff39522765a52a3dafaa8e23a94547735f1c3ef910627e89da8b85b12 "$REPO/v12/python/build/out/distro/baton-v12-stack" | sha256sum -c -
test "$(docker image inspect --format '{{.Id}}' baton-v12-worker:ac17a5ad)" = "$IMAGE"
test ! -e "$DEST"
test ! -L "$DEST"
python3 -I -c 'import pathlib,sys; s=pathlib.Path(sys.argv[1]).read_text(); assert 0 < len(s) < 4096; print("statement characters",len(s))' "$STMT"
```

## 2. Bootstrap fresh instance (owner action)

This creates the new instance and its disposable Git repositories using the existing product bootstrap. It is not executed by this preparation.

```bash
just --justfile "$REPO/v12/justfile" bootstrap "$CFG/native-instance-3-ac17a5ad.json" "$DEST" "$REPO/v12/python/build/out/distro" 2>&1 | tee "$EV/instance-3-bootstrap.log"
python3 -I - "$DEST/instance.json" <<'PYCODE'
import json,sys
d=json.load(open(sys.argv[1]))
assert d['identity']['sha256']=='601ef8dff39522765a52a3dafaa8e23a94547735f1c3ef910627e89da8b85b12'
assert d['identity']['build_stamp']['commit']=='ac17a5add7a58fcd845a8eee7485a633ef917de3'
assert d['runtime']['digest']=='54b8d9ea1af2393b0c031806e56ad2da5d31a97f40b8d3dab676af0caccc2533'
print('installed',d['authority_uuid'],d['runtime']['digest'])
PYCODE
just --justfile "$DEST/justfile" status
just --justfile "$DEST/justfile" repository
```

## 3. Compose workers and install their configuration (owner action)

The installed task is a reusable template; the statement below is supplied by manager create. Worker manifests and UUIDs are derived from the actual new deployment, never invented in advance. CLI version 2.1.247 is pinned in the image recipe. Existing credential selection is referenced, never copied into evidence.

```bash
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
```

Confirm the supported status reports two workers, zero Jobs, not serving; bootstrap reports reviewer baton.reviewer-native and decisions to baton.slaw. Stop on disagreement.

## 4. Create the selected Job (owner action)

```bash
BIN=$DEST/distro/baton-v12-stack
UUID="$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["authority_uuid"])' "$DEST/authority-identity.json")"
    "$BIN" manager --store "$DEST/db/jobs.sqlite3" --incarnation slaw-create-handoffs-3 --authority-uuid "$UUID" \
        create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
        --task "$JOB" --job-id "$JOB" --template baton.v12.job-template.implementation-review/3 --control-profile native-handoff/1 \
        --statement "$(cat "$STMT")" \
        --acceptance "${ACCEPTANCE:-The acceptance criterion of the Job as stated.}" \
        --work-scope v12/python --test-scope v12/python/tests \
        --verification env --verification BATON_V12_STACK_TEST_ROOT=/scratch --verification BATON_V12_DISK_ROOT=/scratch \
        --verification TMPDIR=/scratch --verification PYTHONPATH=v12/python/src:v12/python --verification python3 --verification=-m --verification unittest --verification=-v \
        --verification tests.manager.test_attempt_failure_cause --verification tests.tools.test_attempt_diagnostics --verification tests.tools.test_job_observation --verification tests.tools.test_job_viewer > "$EV/create-$JOB.json" 2> "$EV/create-$JOB.report.log"
    cat "$EV/create-$JOB.report.log"
    # THE READBACK IS THE COMMAND'S OWN SUPPORTED OUTPUT: the create answer on
    # stdout and the installer report on stderr (`bootstrap.prepare` through
    # the creation binding), which states the routing selection and the
    # answering grant it made in the new Work's own scope. No store is opened
    # here (review 2026-11-21T01-49-15Z); the routing expected is read from the
    # BOUND INSTANCE DOCUMENT, an input of this qualification.
    python3 -I - "$SHA" "$CFG" "$EV/create-$JOB.json" "$EV/create-$JOB.report.log" <<'PY'
import json, sys
sha, cfg, answer, report = sys.argv[1:5]
held = json.loads(open(answer).read())
assert held["template"]["version"] == "baton.v12.job-template.implementation-review/3", held["template"]
assert held["control"]["profile"] == "native-handoff/1", held["control"]
routing = json.loads(open(f"{cfg}/native-instance-3-{sha[:8]}.json").read())["native_handoff_routing"]
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

```

## 5. Start (owner action)

Only after the create readback above passes:

```bash
just --justfile "$DEST/justfile" start
just --justfile "$DEST/justfile" status
```

Observe through the supported instance status/monitor and retained result files. Preserve logs, candidate identity, provider timing/cause, mandatory verification outcome and native review result. No automatic host import or acceptance. A timeout is evidence about cause reporting, not successful completion. This preparation does not resolve historical Git-dependent verification exceptions or authorize their host rerun.

## Prepared identity and evidence

Checkpoint ac17a5add7a58fcd845a8eee7485a633ef917de3; bundle 601ef8dff39522765a52a3dafaa8e23a94547735f1c3ef910627e89da8b85b12; runtime 54b8d9ea1af2393b0c031806e56ad2da5d31a97f40b8d3dab676af0caccc2533 (82 files); image sha256:19eb459b44478f60ee16a61fcc32c2c99dd0132d7d93675adf9fb7afbe5a92b4. Bundle's dirty stamp records dossier changes, not product changes. Reuse source-identity-ac17a5ad.json, bundle-identity.json, build-stamp.json, image-byte-verification.json and packaging-owner-result.txt here. Exact proposed statement is native-task-invocation-ended-wording-1.txt; prepared input hashes and syntax checks are in launch-preparation-validation.json. Future execution logs named above do not exist yet.
