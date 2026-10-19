# W321528 exact-file continuation — preparation326050

Preparation only under review20:07:01/E326047; no launch or retry selected.
Base 03b94fc80744671150cca1997712ee95a6537df5; four existing retained-input paths are identical to
prior372281f4, fifth absent. Retained0addd2af and patch3be10e04 unchanged.
PROVENANCE.json binds exact retained candidate, failed325711 diagnosis and prior
packet. Latest run spent1379.261536156s, provider1/api-error/native refusal after11
turns, no candidate/formal verification; exact runtime independently absent.
Preserve that refusal; this is a byte-delivery correction, no safeguard bypass,
model switch, timeout increase or inference that the provider refusal is resolved.

## Supported input delivery

Existing baseline_bindings compose -> single_worker nominated_source -> public
source_boundary.nominate_source/compose_source_boundary/boundary_mounts -> OCI
_source_mounts binds nominated repository read-only at /input/source. It is the
host directory mount, not only tracked files in the git-line candidate. Thus this
packet directory is readable there while source-profile checkout stays committed
base. No source-driver change, task /3 or new launch/input schema is introduced.
No unaccepted product bytes are imported into canonical product paths.

restore.py, retained.patch and candidate-input/ (five exact retained blobs) are
ordinary separately reviewable packet files.
Task carries only a short checksum loader: read mounted restore.py once, validate
SHA256, execute those same bytes. restore.py validates the provenance patch hash,
reads all5 candidate-input buffers, validates their hashes and all5 base states
before writing any file, copies only those buffers, then checks all5 result hashes.
Python alone performs restoration; the image recipe does not guarantee patch. No base64/zlib and no model recreation
of file contents. Model only invokes the short file loader. Stop on input/base
failure; no fallback or replay. Writes are confined to the private destination;
canonical/mounted source is explicitly refused. Partial command failure is failure,
not accepted restoration. It never mutates Git state.

Before starting, verify-inputs.py rechecks all selected packet inputs from the
actual nominated directory. Generated deployment pins nominated_source=/home/sl/src/baton
and task source_root=source. This directory is not a snapshot of arbitrary host
files; digest checks on the exact consumed buffers prevent silent drift. Container
read-only protection does not imply host immutability. Preserve these files through
the run; missing/drifted inputs fail closed rather than being retyped by the model.

DELIVERY-CHECK uses real public source-boundary/OCI composition on disjoint local
disk fixtures carrying identical inputs, then deterministic plain-filesystem
restoration at the current base. All5 hashes match; missing/corrupt/repeat/source
writes refuse. Fixture vector has readonly=true at /input/source. Production
configuration and original file hashes separately checked. No engine mount or
provider readability test was executed; this evidence does not claim a new live
runtime. Initial /tmp fixture was refused as tmpfs; corrected fixture uses this
dossier disk root and is cleaned, never weakens disk-backed workspace checks.

## Exact proposed commands after independent review and owner selection

Run from /home/sl/src/baton. Fresh destination must be absent. First commands
prepare and verify only; final start owns submission exactly once.

```sh
python3 -B work/records/2026/10/finding-v12-failed-run-candidate-reporting/preparation-326050/prepare.py stage --root /home/sl/baton-instances/failed-reporting-w321528-326050
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/failed-reporting-w321528-326050/code/v12/python/src:/home/sl/baton-instances/failed-reporting-w321528-326050/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/failed-reporting-w321528-326050/bootstrap-inputs.json --destination /home/sl/baton-instances/failed-reporting-w321528-326050/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
python3 -B work/records/2026/10/finding-v12-failed-run-candidate-reporting/preparation-326050/prepare.py bind --root /home/sl/baton-instances/failed-reporting-w321528-326050
python3 -B work/records/2026/10/finding-v12-failed-run-candidate-reporting/preparation-326050/verify-inputs.py
env BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/failed-reporting-w321528-326050/packet/deployment.json PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/failed-reporting-w321528-326050/code/v12/python/src:/home/sl/baton-instances/failed-reporting-w321528-326050/code/v12/python /usr/bin/python3 -B /home/sl/baton-instances/failed-reporting-w321528-326050/supervisor/baseline.py --packet /home/sl/baton-instances/failed-reporting-w321528-326050/packet/PACKET.json --incarnation failed-reporting-w321528-326050
```

3600s provider/4200s total/30s formal verification/60s cleanup, one invocation/no
retry. No manual second submission. Image baton-v12-claude-worker:w239528-244216,
sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2,
CLI2.1.247,bridge; registry /home/sl/.baton/credential-sources.json,
claude operator-file/w202663-development. No credential read/authentication claim.
Old image/supervisor remain old: manually retain all exact results at any ending.
Formal failure and independent verification/acceptance remain separate.
Fresh context: prior325711 fresh with no selected identity-bound finalized reuse
generation; no raw session/transcript import. Interrupted recovery deferred by
owner324905; successful-turn reuse remains target. Existing errno30 managed target
restriction is not presumed repaired; authorized operator or repaired access uses
these exact commands. /tmp preflight is not a substitute live root.

Only unreadable-ancestor reporting and real permission regression remain product
milestone. W325695 environment defect and W321776 /3 retain ownership; no reverse
gate or native-pilot dependency. Independent exact-byte review and human checkpoint
still required. Prior186-pass proof remains prior0add evidence, not new acceptance.
No product tests warranted on unchanged failed325711 output and none run here.

PREFLIGHT: stage/bootstrap/bind, held_packet/imported-source checks,8 generated
hashes/exact task pass. ARGV-CHECK:4546-byte prompt,4547 withNUL,126525 headroom;
inert exec passes/oversized controls E2BIG. No engine/provider/Job/attempt launched.
Disposable evidence /tmp/w321528-preflight-326050-final, all final input hashes in manifest.

Cumulative: latest served1379.261536156s added to preserved PROGRESS history, no
reset. This claim delivery first failure0.035495199 tool wall (tmpfs refusal), first
successful check0.167489804 measured, negative-fixture correction failure0.078802387
tool wall; final delivery0.168104417 measured. Preparation and argv in JSON. Product
verification0s. Prior author approximately98+2.195+73s, all prior preparation/reviewer
and served907.575625405/906.974666/1457.303273567s retained. Historical aggregate
unknown. Costs are evidence, not an execution grant or renewed approval gate.
