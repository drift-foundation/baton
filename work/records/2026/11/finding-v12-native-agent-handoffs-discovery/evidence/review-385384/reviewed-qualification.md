# W385331 slice 1 — runtime-qualification packet (K, preparation only)

**Binding.** First cut bound to `331dd737` (the slice checkpoint). Refreshed 2026-11-20 after the composer correction candidate (`evidence/native-handoffs-composer/`, §2 below): the commands now bind to **the eventual accepted checkpoint that carries that correction**, read as `SHA=$(git rev-parse HEAD)` at step A after the owner commits it, and every placeholder is replaced by an executable form. The one input this packet deliberately leaves to the coordinator is the live Job's statement and identity (§3 F: `JOB`, `STMT`), which is a selection and not a command.

Prepared by `baton.prompt` under the owner-held W321608 arrangement after the owner's checkpoint `331dd7379b492ac0ad6c742ded032643ad17ce9c` ("v12: native handoffs — a question is not a candidate (W385331 slice 1)"), which carries the accepted 36-path candidate `f62bbaab…` (review-2026-11-20T21-32-47Z). Nothing was built, installed, started or probed live: the only engine call was a read-only `docker image inspect` of the existing image; the only reads of retained instances were `deployment.json` (read-only). K holds no claim. Captures: `source-state.txt`.

## 0. What a qualified native-handoff runtime consists of, and what exists today

| Component | Required for `/3` | Today | Status |
|---|---|---|---|
| Source checkpoint | `331dd737`, `v12/` clean | HEAD `331dd737`, `git status -- v12` empty | **bound** |
| Host bundle | `just build` output whose stamp is `331dd737`, `dirty: false`; packaged CLI carries `manager create --template … --control-profile …` and bootstrap `native_handoff_routing` | local `build/out/distro` stamp `3d05430f dirty:true changed_entries 65` (built from the pre-commit tree during integration) | **to build** (§3 step C) |
| Worker image | `Dockerfile.claude` from `331dd737`; the adapter inside is the accepted `claude_agent.py` (sha256 `368eae7a…`): declares `handoff`/`response` outputs, binds `handoff/request.json` and `response.json`, delivers the retained continuation | `baton-v12-worker:e670e624` = `sha256:f2b86df0…` (2026-11-19); `git diff --stat e670e624 331dd737` over the recipe's COPY set: **only `v12/worker/claude_agent.py` changed** (+614/−16) | **to rebuild** (§3 step D); the old image refuses a `/3` declaration by name (`declaration-name-unsupported`) rather than guessing |
| Worker capability declarations | each worker's input manifest declares the `/3` union `proposal, findings, logs, handoff, response` (none required for success beyond what the role owes) and `role_instructions_digest` bound to template `/3` | `pool compose-worker` hard-codes `TEMPLATE_VERSION = …/1` (`tools/pool.py:471`) and composes outputs `[proposal]` only (`tools/next_run_bindings.py:438`); the retained instances' workers declare exactly `[proposal]` | **GAP** (§2) |
| Role contract | `baton.v12.development-role-contract.native-handoff/1`, digest `sha256:66f2c37d501fdc66558aabec35430d1945e2671e76e341991fa263dab05fa38c` (baseline `/1` digest `21b78036…`); implementation produces `proposal, handoff`, owes `handoff`; review produces `findings, logs, response`, owes `findings, logs` | in the checkpoint (`role_contract.py`) | bound |
| Template | `baton.v12.job-template.implementation-review/3` (roles as above; `/1` stays the default) | in the checkpoint (`templates.py`); `manager create --template` selects it | bound |
| Continuation profile | `native-handoff/1`: 0 correction rounds, 4800 s stage, 9960 s Job, 3600 s provider turn, 900 s verification, **1 resolved continuation** | in the checkpoint (`job_control.py`); `manager create --control-profile native-handoff/1` | bound |
| Routing and grants | Authority policy `native_handoff_routing` = `{reviewer: baton.reviewer-native, decision_recipient: baton.slaw}`; `answer-handoff` granted to `baton.reviewer-native` in the bound Work's scope (deployment scope, which every `manager create` Work also carries) | bootstrap selection `native_handoff_routing` in the instance document (validated by `bootstrap.held` today: `source-state.txt`); grant made when a Job binds a Work (same repeat that brings the receipt grants) | **prepared** (`config/native-instance-handoffs-2.unbound.json`) |
| Instance | a NEW destination; `native-handoffs-1` and `native-labels-{1..5}` untouched | `/home/sl/baton-instances/native-handoffs-2` absent; 531 GB free | prepared |
| Authority store | schema 7, fresh (a store at 6 is refused, not migrated) | a new install creates one | by install |

## 1. The deterministic proof of request → reviewer answer → retained continuation, with no human/model courier

**Already in the checkpoint and run on the host tree after import** (`evidence/native-handoffs-1-integration/logs/host-six-module.log`, 342 OK): `tests.tools.test_native_handoffs` drives the REAL deployment composition (`stage_execution.operations_from`), real Authority/Job/Control/Integration stores, a real git line, the REAL worker adapter `claude_agent.py` entered through `baton_worker.serve_exchange`, and `review_driver`'s endings, with the provider replaced at its process seam by a script that writes the files a model would write. It proves, with zero human acts and no message relayed by anyone: yield retained and nothing published (`AClarificationResumesTheSameTaskWithNoHumanAct.test_the_yield_is_retained_and_publishes_nothing`); the reviewer is delivered the question and answers it in its own invocation, the SAME task resumes on the retained checkpoint with the reply AND the exact retained continuation delivered (file bytes, read-only, prompt text: `test_the_resumed_provider_is_given_the_exact_retained_continuation`); the resumed final submission reaches the ordinary review and the integration claim (`test_zero_human_acts_to_the_ordinary_final_review`); finding variant; one escalation held and reread; malformed request refused; restart and interior-fault cuts duplicate nothing; routing installed only through `bootstrap.held/_compose`; unsolicited response commits nothing; zero-edit yield. The adapter bytes under test are the bytes the image will carry (`claude_agent.py` sha256 `368eae7a…` at `331dd737`), and the host bytes are the bundle's.

**What the deterministic proof cannot reach inside a container.** The worker image deliberately carries no scripted provider (`Dockerfile.claude`, `test_dogfood_image.test_the_scripted_default_did_not_travel`) and the adapter composes its provider argv as `claude …` with a composed, never inherited, environment — there is no supported seam to inject a deterministic provider into the real image. So the in-image deterministic qualification is the existing image gate, which is identity, not behaviour: `tests.manager.test_dogfood_image` builds the image from `Dockerfile.claude` and proves the pinned CLI (2.1.247), that the worker and adapter in the image are byte-identical to the reviewed files, the non-root identity, no credential and no provider environment variable, nothing from the manager. Together: image bytes == proven adapter bytes, and the adapter bytes are proven end to end on the host with a scripted provider.

**Runtime qualification therefore decomposes into** (a) the host bundle gate (`just test-packaging`, 24 checks), (b) the image gate (`test_dogfood_image`, builds and probes), (c) the composed deterministic proof already in the suite, (d) a FRESH install + ordinary `/3` creation on a new instance proving the configured routing, grants and `/3` admission through the real installer and command (the connected-creation `TheNativeRoutingThroughTheRealInstaller` cases are that proof against a stand-in runtime; on the real instance it is `status` and the creation readback), and (e) the one live question in §4.

## 2. Prerequisite gap (HISTORICAL as of the composer candidate): no supported composition of `/3` worker declarations

*The text below records the gap as found on 2026-11-20 against `331dd737`. The composer candidate (`evidence/native-handoffs-composer/`) corrects it; after the C1 correction, an ordinary `/3` creation against lanes that do not declare the contract is refused before any creation effect, and the selector holds the same compatibility at dispatch.*

The adapter learns which outputs it may write from the manager's `/input/input.json`, i.e. the installed worker's input manifest (`tools/single_worker.py:1983`); the per-Job rebinding (`tools/job_task.manifest_for`) replaces only the task artifact. A `/3` Job delivers `handoff.json` to every attempt; an adapter whose declarations lack `handoff` refuses ("this attempt was delivered a native handoff context and declares no handoff output"), and a reviewer whose declarations lack `response` refuses likewise — fail-closed, as the slice requires. Both suites that prove the protocol therefore declare the `/3` union on the worker manifests (`tests/tools/test_native_handoffs.HANDOFF_OUTPUTS`; `test_connected_creation.TheNativeRoutingThroughTheRealInstaller.workers()` patches the stage fixture's manifests to add `handoff`/`response`).

The supported composer cannot produce that document: `pool compose-worker` pins `TEMPLATE_VERSION = "…/1"` (`tools/pool.py:471`) for `role_instructions_digest` and composes outputs as `[proposal]` only (`tools/next_run_bindings.py:433-440`); it has no template operand (`cli-help` of the installed `3d05430f` bundle: none). The retained instances' workers declare exactly `[proposal]` with `/1` role instructions (`source-state.txt`-adjacent read of `native-labels-5` and `native-handoffs-1` `deployment.json`).

**Corrected by the composer candidate** (`evidence/native-handoffs-composer/`, for codexpc review; owner checkpoint after acceptance): `pool compose-worker --template <version>` (default `/1`, byte-identical when omitted; `/1`/`/2` keep the legacy one-output declaration; a handoff-capable template declares its roles' union `proposal, handoff, findings, logs, response`, none required; `role_instructions_digest` from the selected version; an unsupported version refused by name before anything is written). Proofs: `tests.tools.test_pool.ComposingAWorkerForASelectedTemplate` and `tests.tools.test_connected_creation.TheReusableInstanceComposesHandoffCapableWorkers` (real install with the routing selection → real `pool compose-worker --template …/3` → repeat → real `manager create --template …/3 --control-profile native-handoff/1`, no manifest patched). Step E below assumes that checkpoint is HEAD.

## 3. Consolidated commands, in order (none executed here)

`SHA=331dd7379b492ac0ad6c742ded032643ad17ce9c`; `DEST=/home/sl/baton-instances/native-handoffs-2`; `CFG=work/records/2026/10/finding-v12-development-coordination-pilot/config`; `Q=…/evidence/native-handoffs-2-qualification`. Owner-reserved acts are marked **O**.

**A. Bind (K, read-only).** ONE owner-checkpoint identity, bound to the reviewed candidate BYTES and written down once; every later step reads it from the bound file and never re-derives it from `HEAD` (review 2026-11-20T23-15-20Z C3). The accepted composer candidate is identified by its packet (`evidence/native-handoffs-composer/manifest.json`, the one codexpc accepts); the check below proves that every path of that candidate AND every path of the accepted slice (`evidence/native-handoffs-1-correction-2/manifest.json`) is committed in `SHA` at exactly the accepted bytes, and that the working tree is clean at `SHA`.
```sh
cd /home/sl/src/baton && export GIT_OPTIONAL_LOCKS=0 && set -o pipefail
SHA=$(git rev-parse HEAD); CFG=work/records/2026/10/finding-v12-development-coordination-pilot/config; EV=work/records/2026/10/finding-v12-development-coordination-pilot/evidence
test "$(git status --porcelain -- v12 | wc -l)" = 0
python3 -I - "$SHA" "$CFG" "$EV" <<'PY'
import hashlib, json, subprocess, sys
sha, cfg, ev = sys.argv[1:4]
def committed(path):
    out = subprocess.run(["git", "show", f"{sha}:{path}"], capture_output=True, check=True).stdout
    return "sha256:" + hashlib.sha256(out).hexdigest()
bound = {"schema": "k.native-handoffs-2-binding/1", "sha": sha, "candidates": {}}
for name in ("native-handoffs-composer", "native-handoffs-1-correction-2"):
    m = json.load(open(f"{ev}/{name}/manifest.json"))
    bad = [one["path"] for one in m["paths"] if committed(one["path"]) != one["candidate"]]
    if bad:
        raise SystemExit(f"{name}: {sha} does not carry the accepted bytes of {bad}; stop, this is not the accepted checkpoint")
    bound["candidates"][name] = {"tree_digest": m["tree_digest"], "paths": len(m["paths"]),
                                 "manifest_sha256": hashlib.sha256(open(f"{ev}/{name}/manifest.json", "rb").read()).hexdigest()}
json.dump(bound, open(f"{cfg}/native-bound-2.json", "x"), indent=2, sort_keys=True)
d = json.load(open(f"{cfg}/native-instance-handoffs-2.unbound.json")); d["line_declared_base"] = d["canonical_target_id"] = sha
json.dump(d, open(f"{cfg}/native-instance-2-{sha[:8]}.json", "x"), indent=2, sort_keys=True)
t = json.load(open(f"{cfg}/native-installed-task-handoffs-2.unbound.json")); t["declared_base"] = sha
json.dump(t, open(f"{cfg}/native-installed-task-2-{sha[:8]}.json", "x"), indent=2, sort_keys=True)
print("bound", sha, json.dumps(bound["candidates"]))
PY
```
Expected: `bound <SHA> {...}` naming both accepted trees; three new files (`native-bound-2.json`, the bound instance and task documents). A mismatch stops here: nothing after A runs against a checkpoint that does not carry the accepted bytes. Every later block begins by reading `SHA` from the bound file:
```sh
cd /home/sl/src/baton && export GIT_OPTIONAL_LOCKS=0 && set -o pipefail
CFG=work/records/2026/10/finding-v12-development-coordination-pilot/config; EV=work/records/2026/10/finding-v12-development-coordination-pilot/evidence
SHA=$(python3 -I -c "import json;print(json.load(open('$CFG/native-bound-2.json'))['sha'])"); test "$(git rev-parse HEAD)" = "$SHA" && test "$(git status --porcelain -- v12 | wc -l)" = 0   # unchanged source before consuming it
```

**B. Prerequisite correction (§2):** the composer candidate's independent review (codexpc) and the owner's checkpoint; step A's byte check is what proves it is in `SHA`.

**C. Host bundle and packaging gate (K, on selection).** Roots outside the checkout (the integration run showed in-checkout `TMPDIR` refuses deployment-composing tests).
```sh
# (the A-prefix block: cd, pipefail, CFG/EV, SHA from native-bound-2.json, HEAD and clean checks)
G=$EV/checkpoint-${SHA:0:8}-packaging; mkdir -p /var/tmp/baton-v12-handoffs-2/packaging /var/tmp/baton-v12-handoffs-2/tmp "$G"
env TMPDIR=/var/tmp/baton-v12-handoffs-2/tmp BATON_V12_STACK_TEST_ROOT=/var/tmp/baton-v12-handoffs-2/packaging BATON_V12_DISK_ROOT=/var/tmp/baton-v12-handoffs-2/packaging \
  just --justfile v12/justfile test-packaging 2>&1 | tee "$G/build-and-gate.log"; echo "exit=$?" | tee -a "$G/build-and-gate.log"   # pipefail: the gate's own status, not tee's
cat v12/python/packaging/build-stamp.json | tee "$G/build-stamp.json"     # expect "commit": "$SHA", "dirty": false
v12/python/build/out/distro/baton-v12-stack --version | tee "$G/version.txt"   # expect: baton 12.0.0 (${SHA:0:8})
v12/python/build/out/distro/baton-v12-stack identity | tee "$G/bundle-identity.json"; sha256sum v12/python/build/out/distro/baton-v12-stack | tee "$G/distro-sha256.txt"
v12/python/build/out/distro/baton-v12-stack pool compose-worker --help | grep -c -- --template   # expect 1
```
Expected: `Ran 24 tests … OK`, no skips (the pre-commit integration gate ran 24 OK in 22 s on the same bytes).

**D. Worker image rebuild and image gate (O: engine build; K may run the gate on selection).** The accepted W325695 build form with the tag that names the checkpoint:
```sh
# (the A-prefix block)
R=/home/sl/src/baton/$EV/worker-image-${SHA:0:8}; mkdir -p "$R"    # ABSOLUTE evidence root, so a later `cd` cannot move the log
timeout 1800s docker build --pull=false --memory 2g --cpu-period 100000 --cpu-quota 100000 --iidfile "$R/image.id" -t baton-v12-worker:${SHA:0:8} -f v12/worker/Dockerfile.claude v12 > "$R/build.log" 2>&1; echo "exit=$?" | tee "$R/build-exit.txt"
IMAGE="sha256:$(cut -d: -f2 "$R/image.id")"; docker image inspect "$IMAGE" --format '{{json .Id}} {{json .Config.Entrypoint}} {{json .Config.User}} {{json .Created}}' | tee "$R/inspect.json"
docker run --rm --network none --entrypoint sha256sum "$IMAGE" /opt/baton/claude_agent.py /opt/baton/baton_worker.py | tee "$R/adapter-in-image.sha256"
git show "$SHA:v12/worker/claude_agent.py" | sha256sum; git show "$SHA:v12/worker/baton_worker.py" | sha256sum   # expect: equal to the two digests above, the checkpoint's own bytes
(cd v12/python && env TMPDIR=/var/tmp/baton-v12-handoffs-2/tmp PYTHONPATH=src /home/sl/.local/state/baton-v12-venv/bin/python -m unittest -v tests.manager.test_dogfood_image 2>&1 | tee "$R/image-gate.log"; echo "exit=$?" | tee -a "$R/image-gate.log")   # builds its own copy from the same recipe and probes it; needs network for the build
```
Expected: a new image id (not `f2b86df0…`), entrypoint `python3 /opt/baton/dogfood_entry.py`, non-root user, adapter bytes equal the checkpoint's, image gate OK. The `-t` tag is the operator's handle; the DIGEST is what the worker documents bind.

**E. Install, task, workers, repeat (O: install and repeat; K: task and composition).** The native-handoffs-1 flow (`evidence/native-handoffs-kickoff-20261120/PACKET.md` §3 D–F) with: destination `native-handoffs-2`; the instance document carrying `native_handoff_routing`; the new image reference/digest from D; `pool compose-worker --template baton.v12.job-template.implementation-review/3`; participants unchanged (`impl-a`=`baton.claude-native`, `review-a`=`baton.reviewer-native`), verifier layout `1423c3aa…`, credential `claude=operator-file:w202663-development` by reference, network `bridge`, group `1001`, record `work/records/2026/11/finding-v12-native-agent-handoffs-discovery`.
```sh
# (the A-prefix block)
DEST=/home/sl/baton-instances/native-handoffs-2; CFG=/home/sl/src/baton/$CFG
IMAGE="sha256:$(cut -d: -f2 $EV/worker-image-${SHA:0:8}/image.id)"
just --justfile v12/justfile bootstrap $CFG/native-instance-2-${SHA:0:8}.json $DEST v12/python/build/out/distro   # O
cat $DEST/authority-identity.json; python3 -I -c "import json;d=json.load(open('$DEST/instance.json'));print(d['authority_uuid'],d['identity']['build_stamp'],d['identity']['sha256'])"
just --justfile $DEST/justfile status; just --justfile $DEST/justfile repository   # expect: not serving, 0 workers, 0 Jobs; target holds $SHA; install output carried "routing  reviewer baton.reviewer-native, decisions to baton.slaw"
mkdir -p $DEST/state/task && cp -n $CFG/native-installed-task-2-${SHA:0:8}.json $DEST/state/task/installed-task.json
for W in "impl-a implementation baton.claude-native" "review-a review baton.reviewer-native"; do set -- $W
"$DEST/distro/baton-v12-stack" pool compose-worker --deployment $DEST/deployment.json --worker-id $1 --role $2 --participant $3 \
  --template baton.v12.job-template.implementation-review/3 \
  --image-reference baton-v12-worker:${SHA:0:8} --image-digest "$IMAGE" --cli-build 2.1.247 --network bridge \
  --credential-sources /home/sl/.baton/credential-sources.json --credential claude=operator-file:w202663-development \
  --workspace-group 1001 --task-document $DEST/state/task/installed-task.json \
  --record work/records/2026/11/finding-v12-native-agent-handoffs-discovery --checkout /home/sl/src/baton \
  --verifier-layout /home/sl/src/baton/v12/worker/verifier-layout-marker.json --into $CFG/$1-2-${SHA:0:8}.json | tee $CFG/$1-2-${SHA:0:8}-compose.log; done
# expect per worker a "template  baton.v12.job-template.implementation-review/3 declaring proposal, handoff, findings, logs, response" line
python3 -I - "$SHA" "$CFG" "$DEST" "$IMAGE" <<'PY'
import json, sys
sha, cfg, dest, image = sys.argv[1:5]
d = json.load(open(f"{cfg}/native-instance-2-{sha[:8]}.json"))
dep = json.load(open(f"{dest}/deployment.json"))
for k in ("integration_target", "integration_workspace"): d[k] = dep[k]
uuid = json.load(open(f"{dest}/authority-identity.json"))["authority_uuid"]
d["workers"] = []
for w in ("impl-a", "review-a"):
    held = json.load(open(f"{cfg}/{w}-2-{sha[:8]}.json")); m = held["deployment"]["input_manifest"]
    assert held["deployment"]["schema"] == "baton.v12.single-worker-deployment/6", held["deployment"]["schema"]
    assert [o["name"] for o in m["outputs"]] == ["proposal", "handoff", "findings", "logs", "response"], m["outputs"]
    assert all(o["required"] is False for o in m["outputs"])
    assert held["deployment"]["image_digest"] == image and m["work_ref"]["authority_uuid"] == uuid
    d["workers"].append(held)
assert "native_handoff_routing" in d
json.dump(d, open(f"{cfg}/native-workers-2-{sha[:8]}.json", "x"), indent=2, sort_keys=True); print("wrote", f"{cfg}/native-workers-2-{sha[:8]}.json")
PY
just --justfile v12/justfile bootstrap $CFG/native-workers-2-${SHA:0:8}.json   # O: the repeat; expect "routing  reviewer baton.reviewer-native, decisions to baton.slaw", two sources cloned and proved, "answer   answer-handoff to baton.reviewer-native" once a Job binds a Work
just --justfile $DEST/justfile status   # expect: 2 workers, 0 Jobs, not serving
```

**F. Ordinary `/3` creation (O).** Same operand provenance as the handoffs-1 packet §3 G, with the native template and profile. This packet SELECTS creation on the stopped instance (so the first start observes the Job from its first tick); ordinary creation while serving is DESIGN's contract and is not claimed impossible here. `JOB` and `STMT` are the two PENDING SELECTIONS — the Job identity (also the task name) and the statement file (a SMALL useful development task that can plausibly raise one in-scope clarification) — set by the coordinator before this block runs; they are not bound by this packet.
```sh
DEST=/home/sl/baton-instances/native-handoffs-2; BIN="$DEST/distro/baton-v12-stack"
UUID=$(python3 -I -c "import json;print(json.load(open('$DEST/authority-identity.json'))['authority_uuid'])")
JOB=PENDING-SELECTION             # the coordinator's selection; the block refuses to run until set
STMT=/PENDING/statement.txt       # the coordinator's selection, byte-exact statement
test "$JOB" != PENDING-SELECTION && test -f "$STMT"
just --justfile $DEST/justfile status          # expect: not serving (this packet's selection, not a requirement of creation)
"$BIN" manager --store $DEST/db/jobs.sqlite3 --incarnation slaw-create-handoffs-2 --authority-uuid "$UUID" \
  create --instance $DEST --control $DEST/db/control.sqlite3 --authority $DEST/db/authority.sqlite3 \
  --task "$JOB" --job-id "$JOB" --template baton.v12.job-template.implementation-review/3 --control-profile native-handoff/1 \
  --statement "$(cat "$STMT")" \
  --acceptance "The Job's own acceptance criterion as stated." \
  --work-scope v12/python --test-scope v12/python/tests \
  --verification env --verification BATON_V12_STACK_TEST_ROOT=/scratch --verification BATON_V12_DISK_ROOT=/scratch \
  --verification PYTHONPATH=v12/python/src:v12/python --verification python3 --verification=-m --verification unittest --verification=-v \
  --verification tests.job_manager.test_job_control
```
Expected readback (the create answer): `template.version` `…/3`, `control.profile` `native-handoff/1` (one continuation), `servable` `{implementation: [impl-a], review: [review-a]}`. Then, read-only: `"$BIN" manager --store $DEST/db/jobs.sqlite3 --incarnation slaw-view --authority-uuid "$UUID" view --job "$JOB"` shows the Job handoff-capable; the Authority holds `answer-handoff` for `baton.reviewer-native` in the Work's scope and NOT `review` for it (`"$BIN" work --authority $DEST/db/authority.sqlite3 …` grants listing, or the bootstrap repeat's own "answer" line). The acceptance, scopes and verification above are the executable minimum; the coordinator widens them with the selected statement.

**G. Live run (O: start; the live selection of §4).**
```sh
just --justfile $DEST/justfile start; just --justfile $DEST/justfile status; just --justfile $DEST/justfile monitor 10
```
Observation is read-only through `status`, `monitor`, `$DEST/state/status.json` and the retained outputs; K reports on T321608. Expected native evidence: the implementation stage reaching `awaiting-answer` (if the provider asks) with one `clarification-request` message in the Authority addressed to `baton.reviewer-native`, the review stage ending in `answered` with one reply, the resumed attempt's `handoff.json` carrying the continuation text, then an ordinary final submission and review — or a straight final submission if the provider never asks (which qualifies the runtime for the final-submission branch only; see §4).

## 4. The specific question that requires a live provider, stated separately

Everything protocol-side is proved deterministically (§1). What no fixture can answer is **model-dependent output**: given the handoff addendum in the implementation prompt (`_handoff_prompt`) and the response prompt in the review turn (`_response_prompt`), does the real `claude` CLI (2.1.247, as pinned) actually (a) stop and write exactly one `handoff/request.json` with the four members when it genuinely cannot finish within scope, rather than guessing or finishing; (b) as the reviewer, write `response.json` with a disposition, body, rationale and `escalation: null`, and NOT also a `review-report.json`; and (c) on the resumed turn, continue from the delivered note rather than restarting. These are prompt-adequacy questions about a provider, exactly the class the owner's deterministic-default ruling reserves a live run for. One live `/3` Job on a new instance answers them; a Job whose provider never asks still qualifies the final-submission branch and leaves (a)–(c) open. No live run is selected by this packet.

## 5. Preserved and not done

`native-handoffs-1` (its failed Job and retained candidate), `native-labels-{1..5}` and every other destination untouched; no image built, no bundle built, no install, no instance started, no store opened; no credential read (reference only); the status-timeout finding stands. Files: `PACKET.md`, `source-state.txt`, `config/native-instance-handoffs-2.unbound.json` (with `native_handoff_routing`, accepted by `bootstrap.held`), `config/native-installed-task-handoffs-2.unbound.json`.
