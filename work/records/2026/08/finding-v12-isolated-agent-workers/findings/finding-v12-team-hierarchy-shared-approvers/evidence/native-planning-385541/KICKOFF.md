# W9901 native planning kickoff

Prepared under E385541/M385539. **Not launched.** Run only as the selected operator execution. The task is TASK.txt; preparation does not implement or decide the substantive plan.

## Concrete prerequisite

Existing native-handoffs-3 is serving, with one completed Job and fresh canonical snapshot. Its repository/task base is ac17a5ad; native-handoffs-2 is at 7ac02c7f. Neither is the required current accepted source 9fa0ec37. `creation.py:412` supports only `--source installed`; it cannot select an arbitrary newer commit or copy this host's dirty records. Do not edit those live instances or pretend they contain current source. Smallest supported remedy: use existing bootstrap and pool compose-worker to prepare the fresh destination below at the pinned current source. No new launcher or capability implementation is needed. Build/install/creation/start are operator actions withheld by M385539, not an unresolved product decision.

The statement explicitly carries the latest owner ruling because that ruling is presently uncommitted in the dossier. Other required source/record inputs are in 9fa0ec37. Input FINDING/PLAN snapshots and their hashes are retained here. W9901 remains canonical in v11; the new native Work is a bounded planning execution, not a migrated backlog or competing authority for owner decisions.

## Preparation using existing tools

Run blocks in one Bash session; stop on any failure. The image is reused because `git diff ac17a5ad 9fa0ec37 -- v12/worker` is empty; the command checks the exact previously qualified image identity. Credential reference only, no credential bytes in this packet. Build/bootstrap creates the runtime and isolated repos; no mainline Git operation is included.

```bash
set -euo pipefail
REPO=/home/sl/src/baton
RECORD=work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-team-hierarchy-shared-approvers
PACKET=$REPO/$RECORD/evidence/native-planning-385541
DEST=/home/sl/baton-instances/native-w9901-planning-1
BASE=9fa0ec37a244a388a55be108fd73cb854846245c
IMAGE=sha256:19eb459b44478f60ee16a61fcc32c2c99dd0132d7d93675adf9fb7afbe5a92b4
cd "$REPO"
test "$(git rev-parse HEAD)" = "$BASE"
test -z "$(git status --porcelain -- v12)"
test ! -e "$DEST"
test ! -L "$DEST"
test "$(docker image inspect --format '{{.Id}}' baton-v12-worker:ac17a5ad)" = "$IMAGE"
just --justfile "$REPO/v12/justfile" bootstrap "$PACKET/bootstrap-inputs.json" "$DEST"
BIN=$DEST/distro/baton-v12-stack
mkdir -p "$DEST/state/task"
cp "$PACKET/installed-task.json" "$DEST/state/task/installed-task.json"
for SPEC in 'impl-a implementation baton.claude-native' 'review-a review baton.reviewer-native'; do
    read -r WORKER ROLE PARTICIPANT <<< "$SPEC"
    "$BIN" pool compose-worker --deployment "$DEST/deployment.json" --worker-id "$WORKER" --role "$ROLE" --participant "$PARTICIPANT" \
        --template baton.v12.job-template.implementation-review/3 \
        --image-reference baton-v12-worker:ac17a5ad --image-digest "$IMAGE" --cli-build 2.1.247 --network bridge \
        --credential-sources /home/sl/.baton/credential-sources.json --credential claude=operator-file:w202663-development \
        --workspace-group 1001 --task-document "$DEST/state/task/installed-task.json" \
        --record "$RECORD" --checkout "$REPO" --verifier-layout "$REPO/v12/worker/verifier-layout-marker.json" \
        --into "$PACKET/$WORKER.json"
done
python3 -I - "$PACKET" "$DEST" <<'PY'
import json, pathlib, sys
p, dest = map(pathlib.Path, sys.argv[1:])
d = json.loads((p/'bootstrap-inputs.json').read_text())
dep = json.loads((dest/'deployment.json').read_text())
for key in ('integration_target', 'integration_workspace'): d[key] = dep[key]
d['workers'] = [json.loads((p/(w+'.json')).read_text()) for w in ('impl-a', 'review-a')]
with (p/'workers.json').open('x') as f: json.dump(d, f, indent=2)
PY
just --justfile "$REPO/v12/justfile" bootstrap "$PACKET/workers.json"
just --justfile "$DEST/justfile" repository
just --justfile "$DEST/justfile" status
```

Require repository base 9fa0ec37, two installed lanes, zero Jobs, not serving. Bootstrap must report reviewer baton.reviewer-native and decision recipient baton.slaw. A refusal is a blocker to diagnose, not permission to substitute paths. Runtime/image readiness after installation is not claimed by this preparation.

## Minimal Job kickoff after that prerequisite

```bash
UUID=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["authority_uuid"])' "$DEST/authority-identity.json")
"$BIN" manager --store "$DEST/db/jobs.sqlite3" --incarnation slaw-w9901-planning-1 --authority-uuid "$UUID" \
    create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
    --task w9901-native-planning-1 --job-id w9901-native-planning-1 --source installed \
    --template baton.v12.job-template.implementation-review/3 --control-profile native-handoff/1 \
    --statement "$(cat "$PACKET/TASK.txt")" \
    --acceptance 'Evidence-backed workflows, capability/gap map, migration inventory, unresolved decision options and bounded two-project plan; complete automatic native handoffs are the final acceptance target; no invented semantics or product/spec changes.' \
    --work-scope "$RECORD/NATIVE-PLANNING.md" \
    --verification python3 --verification=-c \
    --verification "from pathlib import Path; p=Path('$RECORD/NATIVE-PLANNING.md'); t=p.read_text(); assert all(h in t for h in ['Operator workflows','Capability and gap map','Migration inventory','Decision questions','Two-project proof plan']), 'missing planning section'" \
    > "$PACKET/create.json" 2> "$PACKET/create-report.log"
cat "$PACKET/create-report.log"
just --justfile "$DEST/justfile" start
just --justfile "$DEST/justfile" monitor 10
```

Before start, require create.json template `/3`, profile `native-handoff/1`, and create report's scoped answer-handoff grant to baton.reviewer-native. The command's report is supported creation-time evidence; independent installed CLI grant readback remains unavailable (known earlier qualification limitation). Monitor exit does not stop the Job. Operator stop, if selected: `just --justfile "$DEST/justfile" stop`; stopping supervisors alone is not runtime cessation evidence.

## Routing, verification and result consumer

Implementation baton.claude-native → automatic independent review baton.reviewer-native; routine clarification/reply/retained continuation uses the native `/3` protocol. Actual unresolved decisions route to baton.slaw. Existing native-handoff/1 limits: provider turn3600s, stage4800s, Job9960s, verification900s, correction allowance0. Do not imply automatic correction rounds beyond that allowance. Escalations and finite-limit exhaustion remain held and honestly reported; no blind retry.

Verification command checks structural completeness only; independent native review must assess the substantive scenarios, evidence, gaps and owner decision boundaries. No tests or full suite are needed to author the planning document. No product edits or broad implementation is selected. The expected candidate changes one dossier document; mainline import/commit remains human-owned.

Retain create outputs and status/attempt/result identities. The native reviewer is the first consumer of the candidate; baton.decide consumes the retained reviewed planning packet and unresolved decisions through canonical W9901/T9901. This one bridge checkpoint is not a manual courier for native stage transitions. Do not call the future complete cross-project workflow accepted merely because this planning Job finishes. That later proof must traverse automatic questions/answers/findings/review/dependency satisfaction and retained continuation without a human/model courier.
