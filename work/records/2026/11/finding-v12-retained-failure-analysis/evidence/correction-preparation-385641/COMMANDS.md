# Retained-candidate correction — conditional operator commands

Preparation only, M385639 / E385641. **Same-Job retained correction is unsupported for this admission.** Installed manager exposes submit/fresh-attempt/create/status/serve; correction is internal `review_driver.open_correction` → `episodes.advance_correction`, subject to persisted job_control.refuse_round. Current allowance0/used0 refuses it. No supported CLI operand increases that allowance or selects a retained candidate for create. Fresh-attempt requires a failed stage; this completed changes-requested Job is not eligible, and that operation preserves old input anyway. Resolved clarification continuation is not a code-correction allowance. Do not call internal mutators or edit stores/config to bypass these rules.

Smallest supported alternative: a **separate ordinary native correction/review Job**, installed with the exact retained candidate as its source/base. This uses existing bootstrap `--repository-source`, compose-worker and create; it does not import the candidate into main, repeat implementation from72e1093, amend the old admission or claim native same-Job/session continuation. Link provenance in the new task and retained evidence; the CLI has no typed predecessor/correction link for this new Job, so that lineage is documentary, not an enforced recovery edge. If typed same-Job continuation is required, a bounded product admission capability is needed; no command in this packet can supply it.

Owner must select this new execution alternative before these mutating commands are run. M385634's separate-context Claude/Opus exception was for the original bounded Job: explicitly carry it to this separate correction Job or provide a supported alternate binding; do not infer general same-model fallback. No live selection is made here. Main checkout Git remains untouched. The source materialization commands below are **for Slawomir**, mutating only a named disposable clone, never run during preparation. They are necessary to make bundle objects reachable to the existing bootstrap, not a mainline import. No new launcher or product code is introduced.

## 1. Verify custody and materialize exact retained source

Run in one Bash session, stop on failure. Before execution, recheck original runtime settlement through supported status; retained/current publication during preparation showed both runtimes destroyed and allocations released. Human-readable status alone showed running unknown; it is not fresh cessation proof.

```bash
set -euo pipefail
REPO=/home/sl/src/baton
RECORD=work/records/2026/11/finding-v12-retained-failure-analysis
RETURN=$REPO/$RECORD/evidence/native-return-20261122
PACKET=$REPO/$RECORD/evidence/correction-preparation-385641
OLD=/home/sl/baton-instances/native-w385623-analysis-1
SRC=$REPO/work/scratch/w385623-retained-correction-source
RUN=$REPO/work/scratch/w385623-retained-correction-run
DEST=/home/sl/baton-instances/native-w385623-correction-1
BASE=f13e0b1255cfd43e145fe2ced565704e888e3e17
PRIOR=72e1093dccb3ded9763fd2c42f0f713a7ff2c88f
IMAGE=sha256:19eb459b44478f60ee16a61fcc32c2c99dd0132d7d93675adf9fb7afbe5a92b4
just --justfile "$OLD/justfile" status
python3 -I - "$RETURN" "$PACKET" <<'PY'
import hashlib, json, pathlib, subprocess, sys
ret, packet = map(pathlib.Path, sys.argv[1:])
for name, digest in json.loads((ret/'manifest.json').read_text()).items():
    assert hashlib.sha256((ret/name).read_bytes()).hexdigest() == digest, name
assert json.loads((ret/'findings/report.json').read_text())['verdict'] == 'changes-requested'
task = (packet/'TASK.txt').read_text().rstrip('\n')
assert 0 < len(task) <= 4096
argv = json.loads((packet/'verification-argv.json').read_text())
assert argv == json.loads((ret/'proposal/result.json').read_text())['verification']['argv']
subprocess.run(['bash','-n','-c',argv[2]], check=True)
PY
git -C "$REPO" bundle verify "$RETURN/proposal/objects.bundle"
test ! -e "$SRC" && test ! -L "$SRC"
test ! -e "$DEST" && test ! -L "$DEST"
mkdir "$RUN"
git clone --no-local "$REPO" "$SRC"
git -C "$SRC" fetch "$RETURN/proposal/objects.bundle" HEAD:refs/heads/w385623-retained
git -C "$SRC" checkout w385623-retained
test "$(git -C "$SRC" rev-parse HEAD)" = "$BASE"
test "$(git -C "$SRC" rev-parse HEAD^)" = "$PRIOR"
test -z "$(git -C "$SRC" status --porcelain)"
python3 -I - "$SRC" "$RETURN" <<'PY'
import json, pathlib, subprocess, sys
src, ret = map(pathlib.Path, sys.argv[1:])
p = json.loads((ret/'proposal/result.json').read_text())
actual = subprocess.check_output(['git','-C',str(src),'diff','--name-only',p['base'],p['head']], text=True).splitlines()
assert sorted(actual) == sorted(p['changed_paths'])
for name in ['AGENTS.md','v12/DESIGN.md','work/records/2026/11/finding-v12-retained-failure-analysis/FINDING.md','work/records/2026/11/finding-v12-retained-failure-analysis/PLAN.md','work/records/2026/11/finding-v12-retained-failure-analysis/evidence/native-kickoff-385631/TASK.txt']:
    assert (src/name).is_file(), name
PY
```

Commit identity cryptographically binds tree and parent; manifest pins bundle/result/review/patch. Full reconstructed-tree check above has not been executed during preparation (no import/materialization was authorized). The bundle verifies against the available prerequisite and advertises the exact candidate. Existing original task and accepted parent records travel in candidate source; new correction instructions are supplied explicitly by manager create, not assumed present in the old dossier. No new source checkpoint/repin is needed for this packet. Source changes beyond the retained candidate require revalidation.

## 2. Install separate instance with existing runtime and source selection

Use current supported bootstrap with the already installed distro; do not build candidate source or mutate the old instance. The candidate changes product library/tests/registry/evidence, not the worker image or bootstrap. Verify compatibility from the reconstructed source before installation. Existing image/credentials are references, not copied secrets.

```bash
git -C "$SRC" diff --exit-code "$PRIOR" "$BASE" -- v12/worker v12/python/tools/bootstrap.py v12/python/tools/pool.py v12/python/tools/next_run_bindings.py v12/python/src/baton_v12/verification_context.py v12/python/src/baton_v12/source_profiles v12/python/src/baton_v12/attempt_log_format.py
test "$(docker image inspect --format '{{.Id}}' baton-v12-worker:ac17a5ad)" = "$IMAGE"
just --justfile "$REPO/v12/justfile" bootstrap "$PACKET/bootstrap-inputs.json" "$DEST" "$OLD/distro" "--repository-source $SRC"
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
        --record "$RECORD" --checkout "$SRC" --verifier-layout "$SRC/v12/worker/verifier-layout-marker.json" --into "$RUN/$WORKER.json"
done
python3 -I - "$PACKET" "$RUN" "$DEST" <<'PY'
import json, pathlib, sys
packet, run, dest = map(pathlib.Path, sys.argv[1:])
d = json.loads((packet/'bootstrap-inputs.json').read_text())
dep = json.loads((dest/'deployment.json').read_text())
for key in ('integration_target','integration_workspace'): d[key] = dep[key]
d['workers'] = [json.loads((run/(w+'.json')).read_text()) for w in ('impl-a','review-a')]
(run/'workers.json').write_text(json.dumps(d,indent=2)+'\n')
PY
just --justfile "$REPO/v12/justfile" bootstrap "$RUN/workers.json" '' '' "--repository-source $SRC"
just --justfile "$DEST/justfile" repository
just --justfile "$DEST/justfile" status
```

Require candidate f13e0b12 as both source/line base, two independent identities and fresh contexts, zero Jobs and not serving. Refuse drift rather than repair live stores. Existing native-handoff/1 controls this correction Job: 9960s overall including queue,4800s stage,3600s provider,900s verification, zero automatic correction rounds. These new clocks belong only to the new admission; they do not reset the original. Future analysis profile remains unchanged.

## 3. Create bounded correction, inspect, then separately start

```bash
UUID=$(python3 -I - "$DEST/authority-identity.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))['authority_uuid'])
PY
)
mapfile -d '' VERIFY < <(python3 -I - "$PACKET/verification-argv.json" <<'PY'
import json, sys
for value in json.load(open(sys.argv[1])): sys.stdout.buffer.write(value.encode()+b'\0')
PY
)
VERIFY_ARGS=()
for ARG in "${VERIFY[@]}"; do VERIFY_ARGS+=("--verification=$ARG"); done
"$BIN" manager --store "$DEST/db/jobs.sqlite3" --incarnation slaw-w385623-correction-1 --authority-uuid "$UUID" \
    create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
    --task w385623-native-correction-1 --job-id w385623-native-correction-1 --source installed \
    --template baton.v12.job-template.implementation-review/3 --control-profile native-handoff/1 \
    --statement "$(cat "$PACKET/TASK.txt")" \
    --acceptance 'Correct f13e0b12: real automatic failure trigger/analysis dispatch/owner delivery and declared worker producer, preserve prior guarantees, correct group accounting, deterministic connected evidence and independent substantive review.' \
    --work-scope 'W385623 Stage1-A correction only from retained candidate; no Stage1-B/C, W385635, live instance changes or mainline import.' \
    "${VERIFY_ARGS[@]}" > "$RUN/create.json" 2> "$RUN/create-report.log"
cat "$RUN/create-report.log"
just --justfile "$DEST/justfile" status
```

Require installed candidate base, exact task/argv, /3 template and independent reviewer baton.reviewer-native, native-handoff/1 and scoped reply grant. Then, only on selected live execution:

```bash
just --justfile "$DEST/justfile" start
just --justfile "$DEST/justfile" monitor 10
```

The native reviewer automatically receives the corrected candidate and checks the missing production wiring, preservation of prior guarantees and actual seam tests. Full prior review is preserved in the return packet; operative correction text is self-contained in TASK.txt because that later review file is not in the candidate base. Keep original-base→retained and retained→corrected provenance together; a later import needs the full cumulative changed-path/digest review, not just the correction delta. Nothing is imported here. A further changes-requested verdict remains changes-requested despite COMPLETED status, with no automatic additional round. Retain results and pass them on canonical T385623. Stopping a monitor is not stopping execution; operator stop is `just --justfile "$DEST/justfile" stop`, never cessation proof by itself.
