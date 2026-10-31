# Input-delivery Docker slice — W384944 / E384984

Partial fixture correction ready for independent review: final24 cases,23 pass,
zero failures/skips, one product cleanup error. No green-module/B4 claim.

## Exact candidate and contracts

Only `v12/python/tests/manager/test_input_delivery.py` changed; candidate SHA256 `4d7a7067b9a652a84c1e2234dc73849194e98168b6a2cafa5e7eb0f72899156c`,
accepted base `af6fa9da8cc47c25b6848fd22491318f2bd019e1924b39c570eb795c2a62854c`. Exact candidate/base/diff retained. Shared target matched
accepted base immediately before same-file transfer. Stable a8cbc974 source and all
1133 manifest paths verified with the three allocated test overlays; earlier accepted
integration-worker/initial-access/non-engine input changes retained. No K/shared edits.

Delivery.setUpClass accepts an explicit immutable local image through
BATON_V12_INPUT_DELIVERY_IMAGE, verifies daemon/image identity and absent declared
volumes, and uses it for both classes. Without explicit selection the existing
inherited behavior remains. No shared Lifecycle edit or hidden duplicate build.
Selected artifact lifecycle belongs to the supervising run.

Execution UID/GID checks now independently expect effective manager UID and configured
workspace GID, including actual --user and inspected Config.User. Image-default and
consent contracts were not changed. Owner-only output test renamed from
`test_an_owner_only_output_fails_closed_rather_than_widening` to
`test_an_owner_only_output_is_read_without_widening`: under HOST-5 shared ownership,
0600 must read successfully with unchanged mode. It also creates a genuinely unreadable
000 file, proves PermissionError and no implicit widening, then restores its own
fixture mode for disposal. This does not claim a foreign-UID negative under shared UID.
Nested runtime output now requires successful exact cleanup rather than expecting
foreign-owner failure. That positive assertion remains failing on the known product
bug; it is not waived or pre-thawed. Existing group/mode/isolation/restart assertions
remain. Added owner chmod attempts on actual input files/root requiring EROFS30,
so denial is proved at the mount even when ordinary read-only permission bits also
deny writes. Engine read-only mount inspection remains.

## Build and runs

One selected local offline build only: --pull=false --network=none, pinned installed
base, exact worker context hashes in context.json and build-plan.json. Build
0.163652s, exit0; immutable result `sha256:dacb6a0e11d5513a4fd774066141bb62d84e7bc0ad8be39df4ab7e96fb614ef0`. Both classes and
all iterations use this one ID; no provider, pull, installation or image substitution.
Build log and base identity retained. Prepared interpreter/focused just test-one,
actual uid1000 with gid1001 membership, unique disk roots and container evidence label.
The external Docker shim adds only that label, preserving runtime policy and mounts.

- Baseline after selected-image setup:24 cases9 pass/15 failures;5.055s body/5.270090s wall.
- Contract corrections:24 cases23 pass/1 error;5.504s body/5.719799s wall.
- Final with explicit EROFS chmod proof:24 cases23 pass/1 error;5.562s body/5.820718s wall.
Total focused command wall 16.810607s; no timeouts. Exact case IDs/outcomes in
ledgers.json; all24 started once each run. Before/after source hashes unchanged.

Exact created container IDs:29 baseline,31 corrected,31 final. Every ID absent after
its run and again at final cleanup, all historical container IDs preserved. Fresh
roots empty/removed. Unique task image tag removed; all pre-existing image IDs
preserved. The newly built image was removed with its final task tag; no pre-existing image
was deleted. See resource-cleanup.json plus each run's preflight/result/engine.jsonl.

## Remaining coordinated defect

DockerConfiguredGroup.test_manager_cleanup_of_worker_content_is_measured_not_assumed
now reaches the same K-assigned defect as the three non-engine cleanup cases:
workspaces.py:6904 `_removed_through_handles` calls rmdir on inputs through its still
frozen parent. Exact traceback in final/focused.log. Actual runtime-created nested
output is manager-owned/readable; the cleanup cannot complete because of product
permission ordering, not foreign ownership. Preserve this required positive case
for K's reviewed fix and the coordinator-selected stable overlay. No moving K source
was imported. One engine plus three non-engine cleanup errors remain outstanding;
other B4 inventory is unchanged from prior checkpoints. Joined-tree/full acceptance
and independent review remain due.
