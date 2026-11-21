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
JOB=invocation-ended-wording-1
STMT=$EV/native-task-invocation-ended-wording-1.txt
ACCEPTANCE='Ended invocation duration is labelled honestly while verification remains active; active and terminal timing, qualifications, freshness and causes remain correct across shared status/monitor views; focused deterministic and mandatory four-module verification pass.'
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

