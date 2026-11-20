# W385331 first native slice — operational kickoff packet (K, 2026-11-20)

Prepared by `baton.prompt` under the owner-held W321608 arrangement, for T321608 seq 385345 (coordinator) after the W385331 disposition at T385331 seq 385344. K holds no claim on W321608 or W385331. This packet references `2b077949-W385331` (`work/records/2026/11/finding-v12-native-agent-handoffs-discovery`) and consumes the corrected documents there, not K's earlier preparation (`evidence/native-handoffs-preparation-20261120/`, now superseded as the execution order and kept as history).

Nothing was executed beyond read-only inspection: no product edit, build, install, instance operation, engine or model run, Git mutation, live-provider probe or store access. The one engine call was a read-only `docker image inspect` of the already selected worker image. Every command below is written out in full for the step it belongs to, with its expected readback; each step names who runs it. Three of them are reserved to Slawomir (Git checkpoint, install, live start); the create step is an owner selection too because it binds the live run's inputs.

## 0. Inputs this packet is bound to

| input | identity |
|---|---|
| `FIRST-NATIVE-SLICE.md` | sha256 `617d97dc40f51f4e75f6df4d03fa3efd21c600a9ff11ee28956177acb053c29d` |
| `NATIVE-TASK.txt` (the Job statement, byte-exact) | sha256 `e0bc0440a8319b4b34b975d273452fbb98efdbb15f3e7d45f2d6ee648cb54a5a`, 3701 bytes |
| `KICKOFF-READINESS.md` | sha256 `eb7ac48094e47b6b2d60b5d3f0e3c218435537492cb273c71e36f2aa3b9754e5` |
| W385331 `FINDING.md` / `PLAN.md` | `9a7be38a…` / `e4832136…` (full values in `source-state.txt`) |
| review `review-2026-11-20T05-24-56Z.md` | `aa14098ef355432a480699d82045175bd0139031315e7b67a966815e26c55a48` |
| coordinator decisions | T385331 seq 385344, T321608 seq 385345; owner boundary T385331 seq 385334 / T321608 seq 385335 |
| DESIGN | SCH-2a present in the working tree, uncommitted (`git diff --stat -- v12/DESIGN.md` in `source-state.txt`) |

What the three W385331 documents fix for this packet and what this packet therefore does NOT re-decide: communication-first first slice; `NATIVE-TASK.txt` as the statement; template `baton.v12.job-template.implementation-review/1`; profile `documentation/1` for the development Job (it implements the future handoff feature on today's final-proposal runtime and does not demonstrate it); three acceptance criteria; work/test scopes; the six-module verification argv with three deliverable modules; no `--like`; no `--label`; no new verbs assumed; old installed instances untouched; live kickoff only after the exact inputs below exist and are read back.

## 1. Current state, read back today (evidence files beside this packet)

`source-state.txt`:

- HEAD `45141ac6` (labels checkpoint). Uncommitted: `v12/DESIGN.md` (SCH-2a), pilot `FINDING.md`/`PLAN.md`/`PROGRESS.md`; untracked: the W385331 dossier, `evidence/native-handoffs-preparation-20261120/`, and now this packet's files. No other v12 change.
- Destination `/home/sl/baton-instances/native-handoffs-1` does not exist. 549 GB free on that filesystem.

`cli-help.txt` (captured from the local bundle `v12/python/build/out/distro/baton-v12-stack`, exe sha256 `1265b1ff…`, stamp `86c1c22b dirty:true changed_entries:25`): the bundle is the one built for the labels import gate; it is NOT the artifact this packet selects (its stamp precedes the checkpoint). Its help is used only to confirm the operand set of the current source, which is unchanged by the pending checkpoint (DESIGN and records only):

- `pool compose-worker` takes `--deployment --worker-id --role --participant --image-reference --image-digest --cli-build --network --credential-sources --credential SLOT=PROVIDER:REFERENCE --workspace-group --task-document --record PATH [--checkout] [--work-id] --into [--verifier-layout MARKER | --legacy-verifier-layout] [--admit]`. There is no `--like`.
- `manager create` takes `--instance --control --authority --task --statement --acceptance… --work-scope… [--test-scope…] [--template] [--route] [--job-id] [--verification WORD…] [--label…] [--control-profile]`; dash-leading verification words are written `--verification=-m`.
- `start`/`stop`/`status` are driven through the installed instance's own justfile (`just --justfile <DEST>/justfile start|stop|status|monitor`), which passes `--instance <DEST>/instance.json`.
- `bootstrap` two-operand form installs (`--inputs --destination --distro [--repository-source]`); the one-operand repeat reconfigures an installed instance (`v12/STACK.md` "Reconfiguring an instance that is already installed").

`image-identity.txt` (the selected worker image, verified as identity, not by provider probing):

- `docker image inspect` (read-only): id `sha256:f2b86df0422a508bcf6603866fbf31b27828fd36b1dc3d88d9318f0225ffb380`, tag `baton-v12-worker:e670e624`, created 2026-11-19T05:16:19Z. This is the image every native-labels instance ran (`config/native-workers-d8f77700.json`, `README-native-instance.md`, `evidence/worker-image-e670e624/image.id`).
- Its recipe inputs are the `COPY` set of `v12/worker/Dockerfile.claude` (every `v12/worker/*` file it copies, `baton_v12/attempt_log_format.py`, `baton_v12/verification_context.py`, `baton_v12/source_profiles/`, the worker-control 1.0 schema, the verifier-layout marker) and `ARG CLAUDE_VERSION=2.1.247`. `git diff --stat e670e624 HEAD` over those paths is EMPTY: the image was built from exactly the bytes HEAD carries for them. **The image is reused without rebuild** (coordinator seq 385344/385345: reuse the already qualified image for ordinary source development). The bind step repeats this diff against the final checkpoint; a non-empty result would be a concrete reason to rebuild before composing, and none is expected because the checkpoint adds DESIGN and records only.
- Verifier layout: `v12/worker/verifier-layout-marker.json` sha256 `3355c11a…`, `layout_digest 1423c3aa9e41d7a8719297435798252133af88a55a6031491238ce0e412bc472`, identical to the `verifier_layout.layout_digest` the native-labels-5 deployment carries for both workers. Selecting it with `--verifier-layout` emits `single-worker-deployment/6`, the pairing the labels-5 run proved reaches the provider.
- Retained `native-labels-5`: Authority `8148af5e916148d091a9ac6ae0cc3f3c`, bundle `0f75ae9a…` (d8f77700, dirty), runtime digest `59df90fa…`. Not changed, not reused: the two-operand bootstrap refuses an occupied destination, and the Job must run on the checkpointed source.

Prepared non-secret inputs (`config/`, both byte-identical to the labels-5 inputs apart from root and base, proved in the preparation shell):

- `config/native-instance-handoffs-1.unbound.json` — instance-only `baton.v12.stack-bootstrap/1`, `state_root /home/sl/baton-instances/native-handoffs-1`, same integration profile, retention, generations, owner `baton.slaw`, receipt participants `baton.verifier-native` / `baton.reviewer-receipt-native` / `baton.slaw`; `line_declared_base` and `canonical_target_id` read `UNBOUND-CHECKPOINT` until step B writes the bound file.
- `config/native-installed-task-handoffs-1.unbound.json` — the reusable `baton.dogfood-task/2` delivery template (`native-development-default`, `git-line`, refusing verification unless the Job supplies its own); `declared_base` unbound likewise.

Credential and network inputs are the labels ones, by reference only: slot `claude` → `operator-file:w202663-development`, registry `/home/sl/.baton/credential-sources.json` (exists, mode 0600, not read), network `bridge`, workspace group `1001`, provider CLI build `2.1.247` (the recipe's pin). No secret value appears in this dossier.

## 2. Consolidated owner actions, in order

This is the whole list of acts reserved to Slawomir for this slice, so they are asked once:

1. **O1 — Git checkpoint** (step A). Commit DESIGN SCH-2a, the W385331 dossier, the pilot records and this packet. The dossier MUST be in the commit: the worker's source is cloned from the checkout's HEAD, and `pool compose-worker --record` digests the dossier's FINDING/PLAN into the worker manifest.
2. **O2 — install** (step D): the two-operand bootstrap into the new destination from the clean-stamp bundle.
3. **O3 — configure workers** (step F): the one-operand bootstrap repeat, which clones and proves the two worker sources.
4. **O4 — create the Job** (step G) while the instance is not serving, then **O5 — start** (step H). O5 is the one live-provider selection in this packet; it spends one implementation turn and one review turn on the selected useful development Job.

K runs the deterministic steps between them when the coordinator says so (B bind, C build and packaging gate, E task document and worker composition) and reads back every owner step. Nothing in this packet pre-authorizes O2–O5; the coordinator selects them after the readbacks exist.

## 3. Steps

All paths are absolute or repository-relative to `/home/sl/src/baton`. `DEST`, `SHA`, `BIN`, `CFG` are set at the top of each block so each block pastes on its own.

### A. Owner Git checkpoint (O1)

Paths to include: `v12/DESIGN.md`; `work/records/2026/11/finding-v12-native-agent-handoffs-discovery/` (all files); `work/records/2026/10/finding-v12-development-coordination-pilot/FINDING.md`, `PLAN.md`, `PROGRESS.md`, `config/native-instance-handoffs-1.unbound.json`, `config/native-installed-task-handoffs-1.unbound.json`, `evidence/native-handoffs-preparation-20261120/`, `evidence/native-handoffs-kickoff-20261120/`. Proposed message:

```
Pin W385331 native handoffs scope and first-slice kickoff packet

DESIGN SCH-2a (native handoffs and discovery, owner-interruption
boundary), the W385331 dossier with the reviewed communication-first
first slice, and the pilot kickoff packet for native-handoffs-1.
Records and design only; no product change.
```

Expected after commit: `git status --porcelain` lists none of the paths above; `git rev-parse HEAD` is the checkpoint `SHA`.

### B. Bind the inputs to the checkpoint (K, after A is read back)

```sh
cd /home/sl/src/baton && export GIT_OPTIONAL_LOCKS=0
SHA=$(git rev-parse HEAD); git cat-file -e "$SHA^{commit}" && echo "bound to $SHA"
git status --porcelain -- v12 work/records/2026/11/finding-v12-native-agent-handoffs-discovery   # expect: empty
git diff --stat e670e624 "$SHA" -- v12/worker v12/python/src/baton_v12/attempt_log_format.py v12/python/src/baton_v12/verification_context.py v12/python/src/baton_v12/source_profiles   # expect: empty (image inputs unchanged)
CFG=work/records/2026/10/finding-v12-development-coordination-pilot/config
python3 -I - "$SHA" "$CFG" <<'PY'
import json, sys
sha, cfg = sys.argv[1], sys.argv[2]
d = json.load(open(f"{cfg}/native-instance-handoffs-1.unbound.json"))
d["line_declared_base"] = d["canonical_target_id"] = sha
json.dump(d, open(f"{cfg}/native-instance-{sha[:8]}.json", "x"), indent=2); print("wrote", f"{cfg}/native-instance-{sha[:8]}.json")
t = json.load(open(f"{cfg}/native-installed-task-handoffs-1.unbound.json"))
t["declared_base"] = sha
json.dump(t, open(f"{cfg}/native-installed-task-{sha[:8]}.json", "x"), indent=2); print("wrote", f"{cfg}/native-installed-task-{sha[:8]}.json")
PY
```

Expected: two new bound files; nothing else changes. If the image-input diff is non-empty, stop and report: the image would need a rebuild from `SHA` before step E, which is a separate selection.

### C. Build the artifact and run the packaging gate (K, on coordinator selection)

Same gate as every checkpoint since 093e6bbc (`evidence/checkpoint-*-packaging/`): one build, hash-pinned build tools, the two packaged test modules, a test root outside the checkout.

```sh
cd /home/sl/src/baton && SHA=$(git rev-parse HEAD)
mkdir -p /var/tmp/baton-v12-handoffs-1/packaging work/scratch/w383217/tmp
env TMPDIR=/home/sl/src/baton/work/scratch/w383217/tmp BATON_V12_STACK_TEST_ROOT=/var/tmp/baton-v12-handoffs-1/packaging \
  just --justfile v12/justfile test-packaging 2>&1 | tee work/records/2026/10/finding-v12-development-coordination-pilot/evidence/checkpoint-${SHA:0:8}-packaging/build-and-gate.log
cat v12/python/packaging/build-stamp.json            # expect: "commit": "$SHA", "dirty": false
v12/python/build/out/distro/baton-v12-stack --version # expect: baton 12.0.0 (${SHA:0:8})
v12/python/build/out/distro/baton-v12-stack identity | tee work/records/2026/10/finding-v12-development-coordination-pilot/evidence/checkpoint-${SHA:0:8}-packaging/bundle-identity.json
sha256sum v12/python/build/out/distro/baton-v12-stack
```

Expected: `Ran 24 tests … OK`, no skips; stamp clean at `SHA`. (Create the evidence directory first; the labels gates ran 24/24 in about 14 s after the build.) A dirty stamp means something is uncommitted in the checkout and the build is not the selected artifact.

### D. Owner install (O2)

```sh
cd /home/sl/src/baton && SHA=$(git rev-parse HEAD)
just --justfile /home/sl/src/baton/v12/justfile bootstrap \
  /home/sl/src/baton/work/records/2026/10/finding-v12-development-coordination-pilot/config/native-instance-${SHA:0:8}.json \
  /home/sl/baton-instances/native-handoffs-1 \
  /home/sl/src/baton/v12/python/build/out/distro
```

Expected: a new Authority UUID printed and written to `/home/sl/baton-instances/native-handoffs-1/authority-identity.json`; `instance.json` whose `identity.build_stamp.commit` is `SHA` with `dirty: false`; `repo/target.git` holding `SHA`; zero workers, zero Jobs. The third operand names the bundle from step C explicitly so the recipe does not rebuild. The repository source defaults to this checkout. K readback after the owner reports:

```sh
DEST=/home/sl/baton-instances/native-handoffs-1
cat "$DEST/authority-identity.json"; python3 -I -c "import json;d=json.load(open('$DEST/instance.json'));print(d['authority_uuid'],d['identity']['build_stamp'],d['identity']['sha256'],d['runtime'])"
just --justfile "$DEST/justfile" status       # expect: not serving, 0 workers, 0 Jobs
just --justfile "$DEST/justfile" repository   # expect: target holds the declared base SHA
```

### E. Task document and worker composition (K, after D is read back)

The installed task document is delivered the way every native-labels instance received it (FINDING 2026-11-19 entries): copied into the instance's `state/task/`. Composition then uses the INSTALLED product so every derived member comes from that instance.

```sh
cd /home/sl/src/baton && SHA=$(git rev-parse HEAD); DEST=/home/sl/baton-instances/native-handoffs-1
CFG=/home/sl/src/baton/work/records/2026/10/finding-v12-development-coordination-pilot/config
mkdir -p "$DEST/state/task" && cp -n "$CFG/native-installed-task-${SHA:0:8}.json" "$DEST/state/task/installed-task.json"
BIN="$DEST/distro/baton-v12-stack"
for W in "impl-a implementation baton.claude-native" "review-a review baton.reviewer-native"; do set -- $W
"$BIN" pool compose-worker --deployment "$DEST/deployment.json" --worker-id "$1" --role "$2" --participant "$3" \
  --image-reference baton-v12-worker:e670e624 \
  --image-digest sha256:f2b86df0422a508bcf6603866fbf31b27828fd36b1dc3d88d9318f0225ffb380 \
  --cli-build 2.1.247 --network bridge \
  --credential-sources /home/sl/.baton/credential-sources.json --credential claude=operator-file:w202663-development \
  --workspace-group 1001 --task-document "$DEST/state/task/installed-task.json" \
  --record work/records/2026/11/finding-v12-native-agent-handoffs-discovery --checkout /home/sl/src/baton \
  --verifier-layout /home/sl/src/baton/v12/worker/verifier-layout-marker.json \
  --into "$CFG/$1-${SHA:0:8}.json" 2>&1 | tee "$CFG/$1-${SHA:0:8}-compose.log"
done
```

Expected per worker (as the d8f77700 logs read): `image sha256:f2b86df0…`, `layout trusted 1423c3aa…`, `profile claude-fresh-implementation …`, `task …/installed-task.json (native-development-default)`, a manifest digest, the written file, and the closing line "no Job was prepared, nothing was submitted, no Work was created or touched, and the instance's configuration was not changed". The record binding carries the W385331 dossier path and the FINDING/PLAN digests from the checkout, which equal the committed bytes after step A. Then assemble the repeat input (instance document + the two derived integration paths the repeat must name + both worker documents):

```sh
python3 -I - "$SHA" "$CFG" "$DEST" <<'PY'
import json, sys
sha, cfg, dest = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(f"{cfg}/native-instance-{sha[:8]}.json"))
dep = json.load(open(f"{dest}/deployment.json"))
for k in ("integration_target", "integration_workspace"): d[k] = dep[k]
d["workers"] = [json.load(open(f"{cfg}/{w}-{sha[:8]}.json")) for w in ("impl-a", "review-a")]
json.dump(d, open(f"{cfg}/native-workers-{sha[:8]}.json", "x"), indent=2, sort_keys=True); print("wrote", f"{cfg}/native-workers-{sha[:8]}.json")
PY
```

Verification before handing to the owner (K): both worker documents are `single-worker-deployment/6` with `verifier_layout.layout_digest 1423c3aa…`, `provider_context null`, `work_ref.authority_uuid` equal to the new instance's UUID, `record_binding.path` the W385331 dossier and its two digests equal to `sha256sum` of the committed FINDING/PLAN; the review worker's `review_route` is `integration` and the implementation worker's is `rview`, as in labels-5.

### F. Owner worker repeat (O3)

```sh
cd /home/sl/src/baton && SHA=$(git rev-parse HEAD)
just --justfile /home/sl/src/baton/v12/justfile bootstrap \
  /home/sl/src/baton/work/records/2026/10/finding-v12-development-coordination-pilot/config/native-workers-${SHA:0:8}.json
just --justfile /home/sl/baton-instances/native-handoffs-1/justfile status
```

Expected: the repeat preserves the identity and bindings, clones `repo/source-impl-a` and `repo/source-review-a` from the instance's own `target.git`, proves the declared base on every named source, and publishes the two-worker deployment; `status` shows workers `impl-a` and `review-a`, zero Jobs, not serving. (The labels flow then started and stopped the idle instance once as a health check; that is optional here because the create below requires the instance stopped anyway, and `status` already proves the runtime it verified.)

### G. Owner create (O4), with the instance NOT serving

Operand provenance: `--store`/`--authority-uuid`/`--control`/`--authority` are the new instance's `instance.json` values (`job_store`, `authority_uuid`, `control_store`, `db/authority.sqlite3` under `destination`), never copied from another instance; the statement is `NATIVE-TASK.txt` byte-exact; template, profile, acceptance, scopes and verification are `KICKOFF-READINESS.md`'s selected creation payload. No `--label`: the deployment's own Work already exists at creation, so a label would refuse by design; no `--route`/`--source`/`--submission-id`: the defaults are the deployment's.

```sh
DEST=/home/sl/baton-instances/native-handoffs-1; BIN="$DEST/distro/baton-v12-stack"
UUID=$(python3 -I -c "import json;print(json.load(open('$DEST/authority-identity.json'))['authority_uuid'])")
STMT=/home/sl/src/baton/work/records/2026/11/finding-v12-native-agent-handoffs-discovery/NATIVE-TASK.txt
just --justfile "$DEST/justfile" status          # expect: no manager/publisher process (create refuses while serving)
"$BIN" manager --store "$DEST/db/jobs.sqlite3" --incarnation slaw-create-handoffs-1 --authority-uuid "$UUID" \
  create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
  --task w385331-handoffs-1 --job-id w385331-handoffs-1 \
  --template baton.v12.job-template.implementation-review/1 --control-profile documentation/1 \
  --statement "$(cat "$STMT")" \
  --acceptance "A durable attributed clarification or in-scope-finding request and its reviewer response preserve the exact retained checkpoint and admitted task identity, with no human relay." \
  --acceptance "A yield is never task success or acceptance; continuation, restart, ownership, cancellation and finite bounds are honest and replay-safe." \
  --acceptance "Focused deterministic coverage and old/new-contract rejection prove the change; independent review and human Git/integration remain required." \
  --work-scope v12/python --work-scope v12/worker --work-scope v12/STACK.md \
  --test-scope v12/python/tests --test-scope v12/worker \
  --verification env --verification BATON_V12_STACK_TEST_ROOT=/scratch --verification BATON_V12_DISK_ROOT=/scratch \
  --verification PYTHONPATH=v12/python/src:v12/python --verification python3 --verification=-m --verification unittest --verification=-v \
  --verification tests.authority.test_work_messages --verification tests.job_manager.test_native_handoffs --verification tests.tools.test_native_handoffs \
  --verification tests.job_manager.test_role_contract --verification tests.manager.test_output --verification tests.job_manager.test_job_control
```

Expected: one bound, servable Job `w385331-handoffs-1` under the instance's own Work, the answer showing template origin and profile `documentation/1` (one implementation, one independent review, zero correction rounds, 4800/9960/3600/900 s ceilings). Running the identical command again answers the same Job (replay); a changed request under the same `--job-id` refuses. The three new test modules are the Job's deliverables; the implementer registers them in `tools/parallel_test.py` and, if it chooses other names, that is a reason to stop before creation and amend the argv, not to let the verification fail.

### H. Owner start (O5 — the live selection), observation, and after

```sh
DEST=/home/sl/baton-instances/native-handoffs-1
just --justfile "$DEST/justfile" start
just --justfile "$DEST/justfile" status          # expect: manager and publisher serving, 1 Job observed, w385331-handoffs-1 queued/offered then claimed
just --justfile "$DEST/justfile" monitor 10      # read-only; Ctrl-C leaves it without stopping scheduling
```

Progress stays observable without acknowledgments: the publisher snapshot (`$DEST/state/status.json`), `status`, `monitor`, and the retained attempt outputs under `$DEST/state/` are what K reads; K reads only, and reports through T321608. On an exceptional outcome the retained candidate and logs are diagnosed read-only as for labels-5; `fresh-attempt` and correction remain the supported selections, and a `changes-requested` review under `documentation/1` stays visible and opens nothing. After `completed`: the retained proposal is reviewed independently on the host, imported exactly and checkpointed as the labels slice was (`evidence/native-labels-5-import/`), then the second compatibility gate in `KICKOFF-READINESS.md` (new host bundle, worker declarations and image qualification for the versioned handoff contract) is its own selection before any native demonstration of the new protocol.

## 4. Operand provenance

| operand | value | source |
|---|---|---|
| `state_root` / destination | `/home/sl/baton-instances/native-handoffs-1` | absent today; sibling of the retained instances |
| `line_declared_base`, `canonical_target_id`, task `declared_base` | checkpoint `SHA` | bound in step B from `git rev-parse HEAD`, never typed |
| bundle | `v12/python/build/out/distro` built in step C, stamp `SHA` clean | `just test-packaging` |
| image | `baton-v12-worker:e670e624` = `sha256:f2b86df0…` | `docker image inspect`; recipe inputs unchanged since e670e624 |
| verifier layout | `v12/worker/verifier-layout-marker.json`, digest `1423c3aa…` | equals the labels-5 deployment's selection |
| provider CLI build | `2.1.247` | `Dockerfile.claude` `ARG CLAUDE_VERSION` |
| credential | slot `claude`, `operator-file:w202663-development`, registry `/home/sl/.baton/credential-sources.json` | labels-5 deployment, reference only |
| network / group | `bridge` / `1001` | labels-5 deployment |
| record | `work/records/2026/11/finding-v12-native-agent-handoffs-discovery` | W385331 binding (`detail`) |
| participants | `impl-a`=`baton.claude-native`, `review-a`=`baton.reviewer-native`; receipts `baton.verifier-native`, `baton.reviewer-receipt-native`, `baton.slaw`; owner `baton.slaw` | labels-5 inputs, unchanged |
| Job | `w385331-handoffs-1`, statement `NATIVE-TASK.txt`, template implementation-review/1, profile documentation/1 | `KICKOFF-READINESS.md` |
| verification | six modules, `/scratch` roots | `KICKOFF-READINESS.md` (three modules are deliverables) |

## 5. What this packet does not do

- It introduces no launcher, script or framework: the only helpers are two pasteable `python3 -I` JSON fills that write fresh files (`"x"` mode) from the prepared inputs and the instance's own documents.
- It does not assume the new handoff protocol exists in any runtime; the Job runs on today's final-proposal contract and produces an ordinary retained proposal.
- It does not select O2–O5; each is read back before the next. It does not update, cancel or touch `native-labels-{1..5}`.
- It does not claim the image is qualified for the FUTURE declared-output contract; that is the second gate in `KICKOFF-READINESS.md`, after source acceptance.
- Two owner-visible contingencies are named rather than hidden: a non-empty image-input diff at step B (rebuild before compose) and differently named deliverable test modules (amend the argv before step G).

## 6. Files

- `PACKET.md` (this), `cli-help.txt`, `source-state.txt`, `image-identity.txt` in `evidence/native-handoffs-kickoff-20261120/`.
- `config/native-instance-handoffs-1.unbound.json`, `config/native-installed-task-handoffs-1.unbound.json`; step B/E add `native-instance-<sha8>.json`, `native-installed-task-<sha8>.json`, `impl-a-<sha8>.json`, `review-a-<sha8>.json`, their compose logs and `native-workers-<sha8>.json`.

## 7. Bound — 2026-11-20 (after T321608 seq 385346)

Step A (O1) is fulfilled: owner checkpoint `3d05430f97ca9d4a516b51d15eb940840a6f0eff` ("v12: define native messaging and retained-continuation delivery") commits DESIGN SCH-2a, the W385331 dossier, the pilot FINDING/PLAN/PROGRESS and K's earlier preparation; it predates this packet, so this packet's own files (`PACKET.md`, the three captures, `bound-3d05430f.txt`, the config inputs) are evidence for a later records checkpoint and are not needed by the worker. Step B was executed (`bound-3d05430f.txt`):

- `git status --porcelain -- v12 <dossier>` empty; `git diff --stat HEAD -- v12` empty.
- `git diff --stat e670e624 3d05430f` over every `Dockerfile.claude` input: empty. The image `sha256:f2b86df0…` is reused; no rebuild.
- Committed dossier bytes equal the hashes in §0 (FINDING `9a7be38a…`, PLAN `e4832136…`, FIRST-NATIVE-SLICE `617d97dc…`, NATIVE-TASK `e0bc0440…`, KICKOFF-READINESS `eb7ac480…`), so `pool compose-worker --record … --checkout /home/sl/src/baton` will digest exactly what the worker's clone of `3d05430f` carries.
- Bound inputs written fresh: `config/native-instance-3d05430f.json` (sha256 `19b1e92c…`, bases `3d05430f…`) and `config/native-installed-task-3d05430f.json` (sha256 `01b881d9…`, `declared_base 3d05430f…`).

Everything in §3 now reads with `SHA=3d05430f97ca9d4a516b51d15eb940840a6f0eff` and file suffix `3d05430f`. Remaining order: C (K, on selection) → D (O2) → E (K) → F (O3) → G (O4) → H (O5). Nothing past B has been run.

## 8. Step C executed; packet corrections (append-only) — 2026-11-20, T321608 seq 385349

### Corrections to §3/§4 before anything depends on them

1. **`dirty: false` withdrawn as an expectation** (§3C, §4 "stamp SHA clean"). The stamp's boolean proves neither compatibility nor mismatch (KICKOFF-READINESS). While this packet, its evidence and the pilot records are uncommitted, a truthful stamp reads `dirty: true`. The check that matters is: build-consumed source equals the checkpoint (`git status --porcelain --untracked-files=normal -- v12` empty before and after the build) and every dirty path is captured and is outside the build inputs. No commit is requested to chase generated evidence.
2. **Unstarted-instance readbacks** (§3D, §3F). An instance that has never been started has no snapshot, so `status` cannot prove pool or runtime health; it can only report that no manager/publisher process exists. The supported views for an installed, unstarted instance are `just --justfile <DEST>/justfile repository` (target and sources, declared base), `<DEST>/instance.json` (identity, stores, runtime digest), `<DEST>/deployment.json` (workers and their `/6` documents after the repeat), `<DEST>/bootstrap.json` and `<DEST>/authority-identity.json`.
3. **`--label` omission** (§3G): omitted because labels are unnecessary for this run (KICKOFF-READINESS), not because every worker-only bootstrap necessarily mints a Work.
4. **Monitor operand** (§3H): the installed justfile defines `monitor INTERVAL="5"` and passes `--interval`, so `just --justfile <DEST>/justfile monitor 10` is valid; the bundle's `monitor` also accepts `--ticks N` for a bounded read.
5. **Source checkpoint stays `3d05430f`**: §3 blocks that set `SHA=$(git rev-parse HEAD)` are to be read with `SHA=3d05430f97ca9d4a516b51d15eb940840a6f0eff` literally; a later HEAD does not rebind the packet.

### Step C as run (one build, one gate)

```sh
cd /home/sl/src/baton && set -o pipefail
mkdir -p work/records/2026/10/finding-v12-development-coordination-pilot/evidence/checkpoint-3d05430f-packaging /var/tmp/baton-v12-handoffs-1/packaging work/scratch/w383217/tmp
env TMPDIR=/home/sl/src/baton/work/scratch/w383217/tmp BATON_V12_STACK_TEST_ROOT=/var/tmp/baton-v12-handoffs-1/packaging BATON_V12_DISK_ROOT=/var/tmp/baton-v12-handoffs-1/packaging \
  just --justfile v12/justfile test-packaging > <evidence>/build-and-gate.log 2>&1; echo exit=$?
```

Result: **exit 0, 22 s wall; `Ran 24 tests in 14.256s — OK`, 0 skipped** (`exit-status.txt`, `build-and-gate.log`). The recipe built once (pip `--require-hashes` from `requirements.build.lock`, PyInstaller 6.16.0, `--clean`) and ran `tests.tools.test_packaging` and `tests.tools.test_packaged_creation` against that build with `BATON_V12_STACK_PACKAGING_REQUIRED=1`. Fixture roots were on disk-backed `/var/tmp` outside the checkout; `TMPDIR` on `work/scratch`. Build inputs: `v12/python` at `3d05430f` (`source-before-build.txt`: v12 status empty; all nine dirty paths are pilot records/config/evidence under `work/records/2026/10/finding-v12-development-coordination-pilot/`, listed in `dirty-paths-at-capture.txt`). No build-input drift.

### Verified artifact identity (`evidence/checkpoint-3d05430f-packaging/`)

| item | value |
|---|---|
| distro | `/home/sl/src/baton/v12/python/build/out/distro` (one-folder, 82 files) |
| `--version` | `baton 12.0.0 (3d05430f, dirty)` |
| stamp | commit `3d05430f97ca9d4a516b51d15eb940840a6f0eff`, `dirty: true`, `changed_entries: 9`, `excused_build_output: 0` (`build-stamp.json`; `_internal/build-stamp.json` sha256 `63c08ccf99055e6222b3fc08d7bb029ba57a23418f5db18e3e266bb91757067c`) |
| launcher `baton-v12-stack` sha256 | `1265b1ff4c014cf9149bbdeeec8dc91163c0f41b5c3a35484e7dfbc135f9cb25` |
| runtime digest (installer's `tools.instance.manifest`, what `instance.json` will record) | `ea772e90867c32a8f1125201f3e2c7bbd699ebac17f6c6ce7a7fa1eaff7d3d7b` over 82 entries (`runtime-digest.json`) |
| per-file manifest | `distro-manifest.sha256` (82 lines; sha256 of the file `f1397aedbcbbfee69b69c142607645eac2349f349c500ee30bf138e7b421f631`) |
| identity | frozen, Python 3.13.7, `Linux-6.17.0-41-generic-x86_64-with-glibc2.42`; schema assets `agent-session-1.0` 48212, `input-manifest-template` 2990, `worker-control-1.0` 51419 (`bundle-identity.json`) |

The launcher hash equals the labels-gate bundle's (`evidence/native-labels-5-import/packaging/bundle-identity.json`, stamp 86c1c22b dirty). That is expected and not a reuse: `git diff --stat 45141ac6 3d05430f -- v12` is `v12/DESIGN.md` only, and DESIGN.md is not a packaged input, so the product bytes are identical; the bundles differ in `_internal/build-stamp.json`, which is why the whole-folder runtime digest above is the identity to bind, not the launcher hash alone. The distro folder was rebuilt in place by this run; the earlier bundle no longer exists separately.

### Exact installation command (O2, owner; not executed)

```sh
just --justfile /home/sl/src/baton/v12/justfile bootstrap /home/sl/src/baton/work/records/2026/10/finding-v12-development-coordination-pilot/config/native-instance-3d05430f.json /home/sl/baton-instances/native-handoffs-1 /home/sl/src/baton/v12/python/build/out/distro
```

Operands: the bound input (sha256 `19b1e92cb92694c993d25fac9074f58dabd8051f5c983a63557f79ccc214f345`, `state_root /home/sl/baton-instances/native-handoffs-1`, bases `3d05430f…`), the absent destination, and the verified distro above (naming it keeps the recipe from rebuilding). Repository source defaults to this checkout; the labels precedent (native-labels-5 installed with HEAD `bcb5e541` and declared base `d8f77700`; the worker line started at `d8f77700`) shows a later records-only HEAD does not change the declared base the instance proves. Immediately before running it, the owner or K re-reads `v12/python/build/out/distro/baton-v12-stack identity` and `sha256sum` of the launcher against the table above; any difference means the artifact was rebuilt since the gate and the gate must be re-run.

Expected readback after O2: `authority-identity.json` with a fresh UUID; `instance.json` with `identity.build_stamp.commit 3d05430f…`, `identity.sha256 1265b1ff…`, `runtime.digest ea772e90…`, `runtime.files 82`; `repository` showing the target holding `3d05430f`; `deployment.json` with no workers; `status` reporting no processes (health is not provable until a start). D through H stay unexecuted by this step.
