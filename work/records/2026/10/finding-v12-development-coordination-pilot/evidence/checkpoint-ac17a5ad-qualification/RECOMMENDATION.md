# Checkpoint `ac17a5ad` — minimal qualification and native-validation recommendation (K, preparation only)

K (`baton.prompt`, no claim; M385493). Nothing below was executed except read-only captures recorded in this directory (bundle identity, stamp, runtime manifest, image inspection, source identity, live stamp capture). No build repeat, install, live run, instance change, helper framework or Git mutation.

## 1. What exists now (recorded, read-only)

| Component | Identity | Evidence here |
|---|---|---|
| Checkpoint | `ac17a5add7a58fcd845a8eee7485a633ef917de3`, committed 2026-11-21T16:26:51Z: the 20 accepted joined paths over `7ac02c7f` (+ dossier records); host `v12/` clean | `source-identity-ac17a5ad.json`: `head ac17a5ad`, `changed: []`, 41 consumed files of 20 declared inputs, content digest `0ed455c2…` |
| Host bundle | `v12/python/build/out/distro/baton-v12-stack` sha256 **`601ef8df…`**, `baton 12.0.0 (ac17a5ad, dirty)`; stamp `commit ac17a5ad, dirty: true, changed_entries 64, excused 0` — the 64 are dossier records under `work/` (`git status` shows no entry outside `work/`); built 16:27Z after the commit | `bundle-identity.json`, `build-stamp.json`, `distro-sha256.txt`, `version.txt`, `live-capture-now.json` (65 entries now: one more record since the build), `runtime-manifest-summary.txt` (`tools.instance.manifest`: 82 files, digest `54b8d9ea1af2393b0c031806e56ad2da5d31a97f40b8d3dab676af0caccc2533`) |
| Packaging gate | owner ran `just test-packaging`; the final summary was not retained → **not independently verified** | — |
| Worker image | `baton-v12-worker:ac17a5ad` = `sha256:19eb459b44478f60ee16a61fcc32c2c99dd0132d7d93675adf9fb7afbe5a92b4`, entrypoint `python3 /opt/baton/dogfood_entry.py`, user `65532:65532`, created 16:28:52Z, 637 MB | `IMAGE.json` (coordinator), `image-inspect.json` |
| Instance | `native-handoffs-2` (bundle `25330714…` from `7ac02c7f`, image `edb46778…`), serving, 1 cancelled Job retained — **preserved, not touched** | `native-attempt-be4fbac0-recovery/` (W385424 dossier) |

## 2. Precise remaining artifact checks (existing commands; none run)

**(a) The packaging gate without a rebuild** — the recipe is `just build` followed by the gate; the gate alone, bound to the existing bundle, is:
```sh
cd /home/sl/src/baton/v12/python
env PYTHONPATH=src:. BATON_V12_STACK_DISTRO="$PWD/build/out/distro" BATON_V12_STACK_PACKAGING_REQUIRED=1 TMPDIR=/var/tmp/baton-v12-ac17a5ad/tmp BATON_V12_STACK_TEST_ROOT=/var/tmp/baton-v12-ac17a5ad/root BATON_V12_DISK_ROOT=/var/tmp/baton-v12-ac17a5ad/root \
  "$(python3 -m tools.environment interpreter)" -m unittest -v tests.tools.test_packaging tests.tools.test_packaged_creation 2>&1 | tee /home/sl/src/baton/work/records/2026/10/finding-v12-development-coordination-pilot/evidence/checkpoint-ac17a5ad-qualification/packaging-gate.log
```
Acceptance: `Ran 24 tests … OK`, no skips (`BATON_V12_STACK_PACKAGING_REQUIRED=1` turns a skip into a failure). Before it: `sha256sum v12/python/build/out/distro/baton-v12-stack` must still read `601ef8df…` (the bundle the gate is about). This replaces the missing summary without rebuilding; it is the same 24 checks the recipe runs.

**(b) The image carries the checkpoint's worker bytes** — read the files out of the image without running its entrypoint (engine operations, owner's boundary):
```sh
cd /home/sl/src/baton && E=work/records/2026/10/finding-v12-development-coordination-pilot/evidence/checkpoint-ac17a5ad-qualification
docker create --name baton-ac17a5ad-probe baton-v12-worker:ac17a5ad >/dev/null
for f in claude_agent.py baton_worker.py dogfood_entry.py; do docker cp baton-ac17a5ad-probe:/opt/baton/$f - | tar -xO | sha256sum | sed "s| -|  image:/opt/baton/$f|"; git show ac17a5ad:v12/worker/$f | sha256sum | sed "s| -|  git:ac17a5ad:v12/worker/$f|"; done | tee $E/image-adapter-bytes.txt
docker rm baton-ac17a5ad-probe >/dev/null
```
Acceptance: each image digest equals its `git show ac17a5ad:` digest (the W385427 adapter with provider-process timing is what the image must carry; `claude_agent.py`/`baton_worker.py` are Dockerfile inputs).

**(c) Image recipe gate (optional, labelled honestly)** — `tests.manager.test_dogfood_image` builds ITS OWN image from `Dockerfile.claude` in `setUpClass` and probes that; it verifies the recipe at `ac17a5ad`, not the tag `baton-v12-worker:ac17a5ad`. Run only if the recipe proof is wanted; it is not a substitute for (b).

**(d) What is already established and need not be repeated**: joined source review (M385484), the 541-case joined focused selection, the two deep cases under 002/022/077, the W385424 probes — all at the joined bytes now in `ac17a5ad`.

## 3. The qualification helper at `ac17a5ad` — one honest limit

`config/native-handoffs-2-bind.py` pins the composer and slice manifests (43 paths at `7ac02c7f` bytes). Four of the 20 joined paths are among them (`job_manager/documents.py`, `job_manager/projection.py`, `tests/manager/test_boundary_inventory.py`, `v12/worker/claude_agent.py`), so at `ac17a5ad` its `bind` step refuses them — correctly: those bytes are now the joined ones. The guarded helper path therefore needs a bounded helper-only correction first (add the accepted joined manifest `8fd5f3d2…` as the newest precedence layer with its enumerated overlap; review), OR the native validation proceeds with the product commands directly, identities pinned in this evidence. **Recommended: the direct path below**, minimal and using only existing commands; the helper correction can follow if the owner wants the guarded sequence retained for later checkpoints.

## 4. Native validation: the minimal sequence (owner-reserved acts marked O; none run)

Destination: a NEW instance `native-handoffs-3`; `native-handoffs-2` stays as it is (its retained attempt is evidence).

```sh
cd /home/sl/src/baton && export GIT_OPTIONAL_LOCKS=0
SHA=ac17a5add7a58fcd845a8eee7485a633ef917de3; CFG=work/records/2026/10/finding-v12-development-coordination-pilot/config; DEST=/home/sl/baton-instances/native-handoffs-3
IMAGE=sha256:19eb459b44478f60ee16a61fcc32c2c99dd0132d7d93675adf9fb7afbe5a92b4
test "$(git rev-parse HEAD)" = "$SHA" && test -z "$(git status --porcelain -- v12)" && test "$(sha256sum v12/python/build/out/distro/baton-v12-stack | cut -c1-64)" = 601ef8dff39522765a52a3dafaa8e23a94547735f1c3ef910627e89da8b85b12 && test "$(docker image inspect --format '{{.Id}}' baton-v12-worker:ac17a5ad)" = "$IMAGE"
# 1. documents for handoffs-3, derived from the reviewed unbound documents (K may prepare)
python3 -I - "$SHA" "$CFG" <<'PY'
import json, sys
sha, cfg = sys.argv[1:3]
d = json.load(open(f"{cfg}/native-instance-handoffs-2.unbound.json")); d["state_root"] = "/home/sl/baton-instances/native-handoffs-3"; d["line_declared_base"] = d["canonical_target_id"] = sha
json.dump(d, open(f"{cfg}/native-instance-3-{sha[:8]}.json", "x"), indent=2, sort_keys=True)
t = json.load(open(f"{cfg}/native-installed-task-handoffs-2.unbound.json")); t["declared_base"] = sha
json.dump(t, open(f"{cfg}/native-installed-task-3-{sha[:8]}.json", "x"), indent=2, sort_keys=True)
PY
# 2. install (O)
just --justfile v12/justfile bootstrap $CFG/native-instance-3-${SHA:0:8}.json $DEST v12/python/build/out/distro
python3 -I -c "import json;d=json.load(open('$DEST/instance.json'));assert d['identity']['sha256']=='601ef8dff39522765a52a3dafaa8e23a94547735f1c3ef910627e89da8b85b12' and d['identity']['build_stamp']['commit']=='$SHA' and d['runtime']['digest']=='54b8d9ea1af2393b0c031806e56ad2da5d31a97f40b8d3dab676af0caccc2533';print('installed',d['authority_uuid'],d['runtime'])"   # the installed runtime is the recorded manifest of this bundle (82 files)
just --justfile $DEST/justfile status; just --justfile $DEST/justfile repository
# 3. task + workers (K), with the /3 template and THIS image
mkdir -p $DEST/state/task && cp -n $CFG/native-installed-task-3-${SHA:0:8}.json $DEST/state/task/installed-task.json
for W in "impl-a implementation baton.claude-native" "review-a review baton.reviewer-native"; do set -- $W
$DEST/distro/baton-v12-stack pool compose-worker --deployment $DEST/deployment.json --worker-id $1 --role $2 --participant $3 --template baton.v12.job-template.implementation-review/3 --image-reference baton-v12-worker:${SHA:0:8} --image-digest $IMAGE --network bridge --credential-sources /home/sl/.baton/credential-sources.json --credential claude=operator-file:w202663-development --workspace-group 1001 --task-document $DEST/state/task/installed-task.json --record work/records/2026/11/finding-v12-native-agent-handoffs-discovery --checkout /home/sl/src/baton --verifier-layout /home/sl/src/baton/v12/worker/verifier-layout-marker.json --into $CFG/$1-3-${SHA:0:8}.json | tee $CFG/$1-3-${SHA:0:8}-compose.log; done
#    expect per worker: "template  …/3 declaring proposal, findings, logs, handoff, response" and "image  $IMAGE"; then the workers document exactly as the handoffs-2 one was assembled (native-workers-2-7ac02c7f.json), with native_handoff_routing kept
# 4. repeat (O): just --justfile v12/justfile bootstrap $CFG/native-workers-3-${SHA:0:8}.json ; then status: 2 workers, 0 Jobs, not serving; routing line "reviewer baton.reviewer-native, decisions to baton.slaw"
# 5. create (O): ONE useful /3 Job (statement = owner's selection; keep the W385424 statement shape), profile native-handoff/1, with the four-module mandatory verification:
#    --verification env --verification BATON_V12_STACK_TEST_ROOT=/scratch --verification BATON_V12_DISK_ROOT=/scratch --verification TMPDIR=/scratch --verification PYTHONPATH=v12/python/src:v12/python --verification python3 --verification=-m --verification unittest --verification=-v --verification tests.manager.test_attempt_failure_cause --verification tests.tools.test_attempt_diagnostics --verification tests.tools.test_job_observation --verification tests.tools.test_job_viewer
#    readback: the command's own stderr report must say "routing  reviewer baton.reviewer-native, decisions to baton.slaw" and "answer  answer-handoff to baton.reviewer-native in its own scope; no review grant"; the answer JSON template.version …/3, control.profile native-handoff/1
# 6. start (O): just --justfile $DEST/justfile start; observe read-only with status / monitor / state/status.json
```
The instance-3 document derivation and the worker composition are K's preparation steps once the owner selects the run; the Job statement is the owner's selection and is not written here.

## 5. The bounded native question (what one live Job answers, and what it does not)

With `ac17a5ad` installed and this exact image, one useful `/3` Job answers three things that no deterministic run can:
1. **W385454 in the worker**: the mandatory four-module argv (which includes the two real-reader cases) passes INSIDE the worker image (umask 022/077), i.e. the Job's `verification` reports `status 0` and the retained `result.json` disposition is not `verification-failed` for that reason. Deterministic proof so far is the confined host harness under 022/077; the worker's own run is the remaining fact.
2. **W385424 + W385427 on a real ending and a real turn**: `just status` / `monitor` / the viewer show `Job age`, `running <duration>` and `<cause> timeout in …` while the implementation runs (the installed `ac17a5ad` bundle now carries the shared interpretation), and on any non-success ending the worker-declared cause (`worker declared unable: … (provider timed out)` / `verification … status N`) instead of `cause unknown` — the exact surface the retained `native-handoffs-2` ending demonstrates was missing.
3. **The handoff prompt question (unchanged from the qualification packet §4)**: only if the provider naturally asks — one `clarification-request` to `baton.reviewer-native`, the reviewer's `response.json`, the resumed attempt with `handoff/continuation.txt`. A Job that never asks qualifies the final-submission branch only; no question may be induced.

Acceptance boundaries: (1) and (2) are observed through supported views and retained files only (`status`, `monitor`, `view`, `logs locators`, the custody tree) — no store opened; a Job that ends by provider timeout still answers (2) if the cause is reported. Nothing here accepts the Job's proposal; independent review and human integration remain. Not answered by this run: image-recipe equivalence (that is (c)), packaging (that is (a)), and anything about `native-handoffs-2`.

## 6. Preserved and reused

`native-handoffs-2` untouched (serving; its retained attempt stays the W385424 evidence); no build repeat (the existing bundle `601ef8df…` is the artifact, its gate is run in place); the image `19eb459b…` is the artifact; joined-review, focused and confined evidence reused by reference; the qualification helper and its binding at `7ac02c7f` left as they are, with the limit in §3 stated rather than worked around.
