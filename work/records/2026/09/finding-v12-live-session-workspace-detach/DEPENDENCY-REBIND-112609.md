# W106673 diagnostic dependency rebind — claim112609

Owner111303 authorizes preparation after the provider gates settle. W110772 and
W112039 are closed satisfying; the OCI provider W110934 is also accepted.
Independent exact-binding review comes next, followed by a separate owner
execution decision. This document grants no live execution authority.

The separate evidence/live_controller_rebound_112609.py changes only the manifest
filename from the signed-off live_controller_result_diagnostics.py. It reuses
live_supervisor_result_diagnostics.py byte for byte. All diagnostics, acceptance,
credentials, source snapshot, restoration, custody and ending code are unchanged.
RESULT-DIAGNOSTICS.md describes the preserved closed field vocabulary and limits.

## Exact package and proposed invocation

Manifest: evidence/result-diagnostics-rebound-112609-manifest.json.
Offline package audit:

```sh
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_rebound_112609.py --audit
```

One proposed operator command, only after independent binding review and a
separate exact owner execution decision:

```sh
sudo -- /usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_rebound_112609.py --run
```

This supersedes the future manifest/controller/invocation selection in
RESULT-DIAGNOSTICS.md. Its old sources, manifest, instruction bytes and evidence
remain historical. No old invocation is repaired or reused as a new approval.

RESTORED-ONLY.md's limits remain: two containers and two user turns, 180 seconds
per turn, 420 seconds work plus 180 seconds ending within 600 seconds runtime.
The fixed image, Claude version/model, ordinary bridge, existing private credential
delivery, mount/receipt checks and teardown remain. Nominal USD2 is not a verified
hard billing cap. Initial successful work, confirmed stop and fixed-byte verification
precede replacement; the same actual session/workspace and remembered-token
correction after ordinary revocation are required. Closed export and exact ending
observations return for independent review. Accepted retained-session proof stays
separate; no matched comparison, automatic retry or production adoption is implied.

## Dependency account

Six existing runtime inputs changed; one Python module was added. Every changed
or added hash matches accepted W110772/W112029 joined or W110934 review evidence
in evidence/rebind-112609/accepted-dependencies.json. The manifest keeps every
prior input and adds the complete current Python file set, including oci_delivery.py;
it retains the two required schema assets and existing source-reader tool.
No dependency was deleted and no production file was edited. This is a current
binding observation, not proof of historical runtime drift or a whole-tree gate.

- v12/python/src/baton_v12/integration/driver.py
  Previous `d7a3e63e2b9ef8b6fffc6eb219790a3df7fd58c3be2ffeb59727bf9284dfd8b1`; current `d6b3be4f99e0776d6ec402db6bfb05b4db8fd376a36b8d1c4225eb17dec83bd6`.
- v12/python/src/baton_v12/integration/runtime.py
  Previous `742121cf0ae906160375e71bf0985b26091c5a2705bf2144236e12b6eb1b243c`; current `d76676e04d4917be39f723d670ce7ecb2fc5830ae9246e388a844e337806d2cb`.
- v12/python/src/baton_v12/job_manager/review_driver.py
  Previous `62db37ee8cd52bf99fc4e68b766841586f921324366e9e0191fc9618b33e6765`; current `0ba2b2bb7adb9c6181cb843a4b90ddf5da6bd8dadd43ed9e6e5a5952020c2262`.
- v12/python/src/baton_v12/worker_manager/custody.py
  Previous `86fbf3cd58e958b212e45efe569472b657428395a3e9a2169d73e3ddb324dbe0`; current `8a11cac9c2a3859392b619cd1bbaf7019c3fef57bd03c9b9cc651d7e8275dbd6`.
- v12/python/src/baton_v12/worker_manager/oci.py
  Previous `101a2c1754cfb2ea7fc6e08783a902c4e944b33ed7b0189130aaf8c6ff79f566`; current `68bb8831331ec1ac07b7b6bdb8a559573be348fe80ba796e50607d4b94af7b2f`.
- v12/python/src/baton_v12/worker_manager/review_cycles.py
  Previous `e085f0a0020b23a08650e8b60db78e27bb5ee9d273ae89474099481462f0d377`; current `774fae6bd09c9dfe9a1f47b6149c9cfbe375d22c6461a95a7aa7d251b7d02da6`.
- Added v12/python/src/baton_v12/integration/oci_delivery.py: `ccfa812ac3b6c4fa68d32bc4fcb25bf2c05c7220369af1b39dedc0aef8a08282`.

## Offline verification

The additive test_result_rebound_112609.py preserves every original test assertion
and changes only two controller import names, including the clean subprocess
snapshot import. Run it with no operand for eight diagnostics cases and --broad
for the 32 diagnostic/restoration/constructor/stream/snapshot checks. Actual
fresh-snapshot imports construct no source reader or runtime; they do not prove
live restoration. Exact source equality and all 191 protected historical dossier
files are checked against the claim baseline. Claim-specific logs and final audit
are retained under evidence/rebind-112609/. Earlier broad red evidence remains
unwaived; it is not rerun or relabeled by this packaging check.
