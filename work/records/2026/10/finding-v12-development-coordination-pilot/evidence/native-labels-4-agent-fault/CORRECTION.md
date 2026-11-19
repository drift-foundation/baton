# Correction candidate: compose-worker selects the verifier layout (K, 2026-11-19)

Answers T321608 seq 385234 under the owner-held W321608 manual assignment. Working-tree candidate, not committed; Git stays the owner's. No live operation, instance change, image build, engine run or store mutation.

## What changed (five paths, all K-owned or bounded by the outcome)

- `v12/python/tools/pool.py` — `compose-worker` now requires an explicit verifier-topology selection and writes the supported `/6` deployment for it:
  - `--verifier-layout MARKER` names the `worker/verifier-layout-marker.json` the selected image's recipe copied to `/opt/baton`, from the checkout the image was built from. `_layout_selection` holds it to the existing contract (`source_boundary.MARKER_MEMBERS`, `MARKER_SCHEMA`, `layout_digest()` and the composed topology members) and refuses a marker from another topology or shape by name, before anything is configured. The deployment becomes `baton.v12.single-worker-deployment/6` = the unchanged `/4` members plus `provider_context: null` and `verifier_layout: <marker>`.
  - `--legacy-verifier-layout` keeps the byte-identical `/4` document for an image built before the marker existed (explicit legacy compatibility).
  - Neither → `PoolRefusal` naming both operands and why ("a marker image started under a legacy deployment refuses inside the worker, before the provider, as an anonymous agent fault after the Work was admitted and claimed"), exit 2 from the command line, nothing written. Both → refused.
  - The compose summary prints a `layout` line (`trusted <layout_digest>` or `legacy (explicitly selected …)`); the API answer carries `layout: {selection, layout_digest}`.
  - No image inspection and no bespoke launcher: the marker is an operand read from the build's own recipe input by the operator who selected the image, exactly as `source_boundary.compose_verifier_layout` requires ("`marker` is an OPERAND and is not discovered here"). `image_layout_marker()` is not used as evidence about any image.
- `v12/python/tests/tools/test_pool.py` — `ComposingAWorkerForThisInstance` split into `ComposingCase` (helpers, explicitly legacy by default) + the unchanged legacy cases; new `ComposingAWorkerThatSelectsTheVerifierLayout` (9 cases, below); the CLI case passes `--legacy-verifier-layout`.
- `v12/python/tests/tools/test_bootstrap.py` — `composed_for` selects the marker, so the repeat clones and configures `/6` workers; `test_missing_worker_sources_are_cloned_from_the_target_and_proved` now also asserts both configured workers are `/6` with the marker intact.
- `v12/python/tests/tools/test_single_worker.py` — new `TheLayoutSelectionReachesTheRuntimeVector` (2 cases): the single-worker pipeline that the stage-execution pool launches through binds the materialized selection read-only at `/run/baton/verifier-layout.json`, composes `--user` from the same identity the document names, and mounts the four private verifier roots; a `/4` deployment binds none of that.
- `v12/python/tests/tools/test_connected_creation.py` — the two-Job connected-creation case selects the marker (the verb no longer writes without a selection).

Not touched: `tools/stage_execution.py`, `tests/tools/test_stage_execution.py`, `parallel_test.py`, `offers.py`, job_manager modules (codexpc, W385222/W385227). `tools/stack.py` and `tests/tools/test_stack.py` carry concurrent working-tree edits from 15:55Z (the W385227 status shape) that are not mine and are excluded from this candidate; they do not cause the group failures either (`isolate-stack-failing-ids.log`, 14 OK on a62bc9a3 with only that diff). No new test module, so no registry change; all five paths are already in the `tools-pure` group.

## Acceptance chain, deterministic and offline

| step | proof |
| --- | --- |
| product compose | `test_pool.ComposingAWorkerThatSelectsTheVerifierLayout.test_the_marker_selects_the_supported_layout_deployment`, `…legacy_selection_is_the_unchanged_legacy_document`, `…command_line_selects_either_topology` |
| missing / mismatched pairing refused before anything | `…no_selection_is_refused_before_anything_is_written`, `…both_selections_refuse`, `…a_marker_from_another_topology_or_shape_refuses` |
| bootstrap / repeat | `test_bootstrap.ARepeatProvisionsTheWorkerSourcesItNames.test_missing_worker_sources_are_cloned_from_the_target_and_proved` (both roles configured as `/6`); `test_connected_creation` two-Job case |
| admission + manager validator | `…the_selecting_worker_is_admitted_and_the_manager_accepts_it` (`stage_execution.held_configuration`) |
| stage composition → actual layout delivery | `…the_serving_preflight_delivers_the_selection_before_any_runtime` (`single_worker.worker_preflight`, the call `stage_execution.operations_from` makes per configured worker at `tools/stage_execution.py:6696`, materializes the document under the launch home, bound to the image digest and the minted uid/gid, with no engine start) |
| actual mount in the runtime vector | `test_single_worker.TheLayoutSelectionReachesTheRuntimeVector` (both directions) |
| worker preflight reaches the provider boundary / refuses without it | `…the_worker_reads_the_delivered_selection_and_refuses_without_it` (`claude_agent.ClaudeAgent._selected_layout` on the materialized document beside the shipped marker; absent document → "no trusted layout selection was delivered … refuses before the provider"); the mount-table half of `_layout_preflight` remains the separately selected kernel proof, as `tests/manager/test_verifier_topology` states |
| both roles | bootstrap repeat (implementation + review); `_held` review-role case already in `test_single_worker.TheLayoutSelectionIsIndependentOfTheContextMode` |

Verification (prepared interpreter, `v12/python`, `TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp`):

- `just test-one tests.tools.test_pool tests.tools.test_bootstrap tests.tools.test_single_worker tests.manager.test_verifier_topology` → 524 tests OK, 42.4 s (`focused-layout-correction.log`).
- `just test-one tests.tools.test_connected_creation` → 24 OK, 2.1 s.
- `just test-group tools-pure` (accounted, `group-tools-pure.log`): collected 3420, executed 3420, passed 3410, failed 7, errors 3, skipped 0 → FAILED. **None of the ten is this candidate's**, and every one of my five modules passed inside the group:
  - `tests.tools.test_parallel_runner.TheDeclaredInputsCoverWhatTheTestsRead.test_every_record_path_in_the_tree_is_declared_or_synthetic` fails on a clean export of a62bc9a3 too (`baseline-a62bc9a3-failing-ids.log`): the labels record path read by `test_pool`/`test_bootstrap`/`test_connected_creation` since before this work is not declared in `parallel_test.CONSUMED_INPUTS` (codexpc-owned file; pre-existing, reported).
  - the other nine (`test_dogfood_operator` arc ordering; `test_job_task_delivery` and `test_retry_task_lineage` stage `exceptional` instead of `offered`; `test_next_run_flow` and both `test_operator_verification_view` gates, which nest the dogfood case; three `test_stage_execution` cases with `KeyError: (1, 'implementation-worker')` in `scheduler._worker`) PASS on a clean export of a62bc9a3 with this candidate's diff applied (`isolate-mine-failing-ids.log`, 14 OK) and FAIL on a clean export of the new owner checkpoint **85e646ba** "Settle accepted offers and complete fenced Job cancellation" (committed 15:48Z during this assignment; `baseline-85e646ba-failing-ids.log`), and still fail in a copy of this working tree with this candidate reverted (`wtcopy-without-mine.log`, `wtcopy-clean-tree.log`). The dogfood case's refusal, read in that disposable copy, is "attempt 'attempt-1' has no committed claim; a live assignment elsewhere in the authority is not evidence that this attempt's offer claimed it". They belong to the W385222 slice (delegation/manager/scheduler/offers/stage_execution), not to this candidate; reported, not touched.
  - `working-tree-serial-failing-ids.log`: the same ids fail serially in this checkout, so the group failures are deterministic, not shard interference.
- Candidate base: HEAD moved from a62bc9a3 to 85e646ba during the assignment; 85e646ba does not touch any of the five candidate paths, so the diff and per-path digests are unchanged (`candidate-layout-selection.sha256`).

## What this does not claim

- That any image carries the marker. A marker image selected as legacy still refuses inside the worker before the provider, exactly as today; what changed is that the pairing is an explicit, recorded operator decision validated against the contract instead of a silent default, and a wrong marker refuses at composition rather than at preflight or in a container.
- The installed native-labels-4 bundle (a62bc9a3) does not carry this; its Job stays as diagnosed. A next labels attempt needs a reviewed checkpoint, the clean-source packaging gate, and a fresh instance whose workers are composed with `--verifier-layout <build-checkout>/v12/worker/verifier-layout-marker.json` (the e670e624 recipe input; `verifier-layout-marker.e670e624.json` here is that file, unchanged through a62bc9a3).

## Digest binding

`candidate-layout-selection.sha256`: the diff over the five paths and each path's bytes at this handoff.
