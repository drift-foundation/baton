# Selected cleanup overlay: joined input-delivery verification

W384944 / E385001; M384998 and review-2026-10-31T03-06-27Z.md.
All56 required cases passed:32 non-engine then24 Docker, zero failures/errors/skips,
no duplicate/unaccounted cases. No test edits or shared product edits in this slice.

## Exact selected source

Verified original isolated workspaces.py SHA256
ef9bc97a2c38b536ad725ee2f113d77b686bd5d56425874b839f9e20cad0197f, then copied only
reviewed evidence/cleanup-only-overlay-20261031/candidate.py (SHA256
6cd8850ba08562565656aa1dc50eb32868843cbb80a17d8db36ede07640e82ce) into the same
isolated snapshot path, preserving mode 0o644. No shared
workspaces.py copy or broader Stage C import. All four accepted test overlays and
all1133 selected source hashes verified before/after. Explicit composed manifest:
selected-source.json; per-run before/after hash files retained. Snapshot remains
historical a8cbc974 plus only the selected overlays, not current-tree acceptance.

## Required cleanup cases now pass

- tests.manager.test_input_delivery.TheInputRootIsFrozenAndNotOnlyItsFiles.test_cleanup_removes_a_frozen_root_and_thaws_nothing_else
- tests.manager.test_input_delivery.TheRootsOwnENTRYIsFrozenToo.test_cleanup_reaches_exactly_one_frozen_home
- tests.manager.test_input_delivery.TheRuledTrustModel.test_cleanup_reaches_one_attempt_and_retries_cleanly
- tests.manager.test_input_delivery.DockerConfiguredGroup.test_manager_cleanup_of_worker_content_is_measured_not_assumed

These assertions ran unchanged, without fixture pre-thaw or acceptance waiver.
The accepted parent-descriptor thaw ordering clears all four prior errors.

## Execution and provenance

Six previously selected non-engine classes:32/32,0.506s body/0.764361s
wall. Same two Docker classes:24/24,5.552s body/5.820888s wall.
Total focused command wall 6.585249s. Engine IDs match
the previous24-case set exactly; complete56 ledger in ledger.json. Prepared interpreter
and just test-one; deterministic scripted providers only. Actual group membership,
selected environment and fresh external disk roots recorded. Both roots empty/removed.

One explicitly selected offline reference-worker build, 0.113625s,
exit0. Installed pinned base verified; --pull=false --network=none. Exact command,
base ID, full worker context hashes and build log retained. Resolved image
sha256:db9e357ca91ec376a20af1d341ef9ea6916ff8177d5bfee3451ce1c67d014840 reused by both Docker classes through the accepted explicit-image
setup; no additional build/pull. Source stable throughout both serial runs.

31 exact task container IDs recorded and all confirmed absent after
run and at final cleanup. Prior container IDs preserved. Unique task tag removed;
all pre-existing image IDs preserved. resource-cleanup.json records exact image
removal and pre-existence; no prune or unrelated cleanup. No timeout or emergency
cleanup. Build cap1800s, focused engine cap600s with cleanup reserve120s.

## Refreshed remaining B4 inventory

The retained preflight list had38 outstanding engine IDs. This and prior accepted
slices account for all22 input-delivery IDs (including the documented owner-only
case rename), four required initial-access skips, and one worker-entry ID.
11 historical IDs remain unverified here, explicitly enumerated in
remaining-historical-engine-ids.tsv: custody4, credentials namespace cleanup1,
ended-runtime adoption2, lifecycle composition2, negative endings2. These are prior
observations, not newly run failures. Pure worker/integration-image fixture contracts
and integration-driver retained-root cases remain from preflight; they are outside
this engine-ID list. Integration-worker83, initial-access4, worker-entry5 remain
previous accepted slice evidence; not rerun here. B4 still needs remaining work and
joined current-source/full acceptance after K review. No claim of overall completion.
