# W385695 continuation E385885 — incomplete checkpoint 2

Author: baton.codxpc, 2026-11-23. Disposition: safety corrections and exact preserved continuation, **not ready for checkpoint-2 acceptance, host import, live launch, or “resume supported.”** No owner product decision is requested; the remaining requirements are already selected. K may independently review this delta, but the remaining runtime implementation must still be completed before acceptance.

## Provenance and candidate identity

Base: `6079ad78345aa87b7148db302d48fb9b1867f940`. Retained native candidate: `4e8fbe1c3b596f2f5db9f03b6c63572c9b198df7`.

Original public host observation, artifact hash/size remeasurement, preserved bundle/patch/result/verification and handoff: `observed-status.json`, `custody-verification.json`, `original/`. Original proposal artifact: `sha256:1c5c4e90df8710ec424fbb6ae0027786c3884a609f129ca2cfbb8aef83f39614`, 689247 bytes. `reconstruction.json` proves the isolated retained tree's diff exactly equals retained change.patch, with no Git alternates. The native verifier was not run; preserved native verification.txt is not author verification.

Refreshed candidate identity is `candidate-manifest.json` SHA256 `531ddac1f6fd2203fe3574c5c31726b6ca3781e3bdbf7240c54d324696d53eef`. Complete patch over base: `candidate.patch`, SHA256 `6e3935aa01c36ced8e1f79649934173ff76039b56d8f9232384078ef6131a274`. Five-path correction over retained candidate: `delta.patch`, SHA256 `8312c7e639bb84081f9df2db00adbb5a2e6ed8e468dbab2063d5627ce3612559`. `candidate-files/` preserves all 25 changed paths with per-file SHA256, mode and base hashes in the manifest. Copied files and both patches were reread and hash-checked. The three native dossier paths are historical evidence, not an instruction to replace the current dossier or import older progress.

Scratch continuation: `work/scratch/w385695-385885`, a separate repository with retained candidate HEAD and five uncommitted filesystem corrections. No protected Git/index/history operation, host product import, live change, Docker or provider invocation occurred. Required recovery inputs are here in the dossier, not only scratch.

## Corrections

- `publication_execution.py`: per-recovery nonblocking host lock outside frozen input spans staging/adoption through durable result; callers recheck under lock before effects. Durable launch intent without result holds even if the process died before uncertainty was journalled. Readiness reports that cut as uncertain. Interrupted staging is preserved in an `interrupted-*` sibling instead of deleted. Lock files refuse symlink following and nonregular descriptors.
- `test_publication_recovery_execution.py`: five additive deterministic cases cover process death after intent, overlapping publication, overlapping staging, interrupted-input preservation, and refusal to mint a missing producer session. Existing fixture admission now uses actual `manager.sweep` adoption of the real owner receipt instead of raw receipt insertion. Existing assignment session is explicitly injected.
- `publication_ports.py` and `publication_decision.py`: absence of the producer's already-held session refuses with an actionable holder requirement; no default `Authority.session(participant)` impersonation. Default read-only owners composition remains unable to end a held assignment until the serving owner supplies the supported ending; this is explicitly unfinished production composition.
- `test_dependencies.py`: declare the real external `candidate` operand consumed by existing `freeze_recovered_checkpoint`; retain exhaustive unused/forbidden operand checks.

## Verification accounting

All command records/logs are alongside this report; `test-accounting.json` preserves every measured execution, exit status, timeout and log hash. Prepared interpreter `/home/sl/.local/state/baton-v12-venv/bin/python` via `just test-one`; final disposable storage is disk-backed `work/scratch/w385695-385885-verification`, outside the isolated checkout. Aggregate measured driver wall time is 61.82777210709173 seconds, including failed probes/repeated cases; this is not a count of unique passes.

- `checkpoint2-required-modules`: **307/307 pass**, no failures/errors/skips, unittest15.980s / wall16.276614s, exit0. All four required modules from the native verifier were run once together on the final source. Host equivalent uses prepared interpreter and disk-backed scratch instead of container `/scratch`; no adapter/native verifier or runtime-isolation acceptance is claimed.
- `compatibility-exact`: **12/12 pass**, no failures/errors/skips,25.055s / wall25.286771s, exit0. Includes every one of the eight failing native stage-execution methods. Those failures do not reproduce in the prepared host environment; their native-only cause has not been proved. No claims based on broad inventory completion.
- `corrected-publication-focused`: **93/93 pass**,7.716s / wall7.970798s, exit0; includes four exhaustive operand checks. This preceded the final interrupted-staging case and final source cleanup; the final required module run covers those changes.
- `execution-and-operands`:92 run,4 setup failures because the driver selected scratch inside the checkout; all four were explicit disk-root placement refusals. Driver fixed to sibling disk storage and rerun successfully; do not call them product failures.
- `retained-probes`:2 run,1 pass/1 failure,2.076s; native stage probe passed and undeclared candidate operand reproduced.
- `intent-crash-red`: real repeated writer call reached injected KeyboardInterrupt, test runner interrupted; no completed test count, wrapper exit1 with just signal2 retained in log. `intent-crash-green`:7/7 pass,0.539s.
- `real-admission-probe`:1 error,0.103s, fixture attempted nonexistent JobStore.snapshot; corrected fixture reads actual receipt through job_control with its existing store connection. `real-admission-probe2`:1/1 pass,0.104s.
- No timeout during this continuation, no broad inventory reruns. `git diff --check` passed.

## Exact remaining implementation and continuation

The retained implementation is substantially incomplete against selected checkpoint2, independently of compatibility passes:

1. `tools/publication_worker.py:PublicationWriter.adopt` is a direct in-process host copy. Contract section2 requires staged input mounted read-only in `/input` with separate output/scratch and normal containment. Integrate deterministic entrypoint with the existing worker/runtime launch, token and workspace owners; fake only engine/provider boundaries in focused tests. Do not add a new host-copy “success” path or treat permission bits as confinement.
2. `PublicationWriter._remaining` only polls clock between copies; it cannot stop a blocked copy, and missing/invalid deadline currently returns None. Contract section5 requires command-supervisor termination at the absolute remaining bound plus host/runtime enforcement and positively observed cessation. Carry durable origins unchanged; expiry is not cessation. Implement and test hung-child/host-loss/restart/rollback/cancellation at the normal boundary. Existing fixture `quiescent`/`settle_ending` writes runtime observations; its passing custody assertions do not prove real runtime enforcement.
3. `tools/publication_decision.owners` holds only a read-only Authority and no original participant session. Connect the already-owned serving-session ending path before fresh claim. The new missing-session refusal is safe but is not a delivered serving integration. Do not replace it with a factory minting arbitrary sessions. Retain exact assignment checks and no takeover.
4. Lost intent now safely holds, but there is still no observation of an actual launched runtime/token for reconciliation. Once the real runtime is integrated, reconcile exact launch/completion/custody without a second effect and retain uncertain state until cessation is proved.
5. Re-run required focused verifier on the completed candidate and obtain K's independent review. Checkpoint3 still owes substantive review delivery and joined installed commands; do not silently move the checkpoint2 gaps above into checkpoint3.

Canonical authorities remain FINDING.md consolidated owner selection and CONTRACT-PROPOSED-385720.md sections2,4,5,8, under DESIGN REC-9. Earlier native REPORT.md claims and passing fixture counts cannot supersede these requirements. No new decision or scope expansion is necessary to continue.
