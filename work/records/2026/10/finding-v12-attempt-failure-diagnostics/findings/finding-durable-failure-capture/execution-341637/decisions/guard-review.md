# Independent acceptance — bounded manager ownership correction

Reviewer baton.rvpc claim335118; owner exception E335045, complete handoff335116 and thread T334910 read. Accept candidate-335047 only, MANIFEST.json SHA256 fd69976b517104355f6fc2bfd5136933964ce577f43c004b16c44279dad18eb7, base a9f4fa4da2323a357ae15aefbc5d7d22d41487b6. No canonical product import or live packet rerun occurred.

## Corrected ownership and review

The outer controller no longer calls operations_from or holds the workspace manager guard. It owns the separate authoring lock, launches one manager process, observes snapshots and enforces the process deadline. The manager acquires the unchanged workspace guard before historical preparation, then runs real enforcement and authoring compositions in separate threads/connections within that one owning process. Repeated process-local guard acquisition succeeds as designed; independent processes still refuse. No workspaces.py change, inherited workspace guard, relaxed exclusion or altered token constant is proposed.

Reviewed process loss and recovery paths: parent-death signal targets manager; outer watchdog retains owned process-group stop/reap; missing final enforcement snapshot produces held uncertainty. Recovery may start a cleanup manager but never re-enters the author invocation; original envelope and admission journals remain binding. Single live snapshot writer and final-write-after-thread-exit avoid overlapping writes. Signals request enforcement; acknowledgement/process death is not container cessation. Original expiry/cancellation rules and original Job limits remain intact.

## Independent evidence

Verified all26 manifest members, all470 reconstructed source members, both candidate file hashes and existing controller base hash from read-only Git history. Fresh private reconstruction /tmp/w334910-review-335118-19kj8lcy; real-disk fixture root evidence/review-335118/disk under this dossier. Reproduced the submitted focused command with55-second timeout:79 tests PASS in24.978061267 seconds measured subprocess wall time (unittest24.511s). Exact command/result and output are evidence/review-335118/RESULT.json and focused.log. No product source edits, real engine/provider operations, credential reads, live packet reruns or Git mutation. Author119.231799363 seconds across9 runs remains separately attributed in retained SPENDING.json, including failed fixture iterations.

The seven added process cases retain real Guard, child_main, child_compose, operations_from, worker_preflight, workspace guard, Authority/stores and performed public admission. They cover independent competitors before/during startup, duplicate outer controller, blocked workload/deadline, exception, operator cancellation, parent/manager loss, released process guard and recovery without another author action. This closes the earlier review gap where the Guard factory itself was replaced. Existing72 focused cancellation/expiry/unknown/restart tests are unchanged and pass.

Limits: these are deterministic local-process proofs, not live Docker/provider evidence or a complete installed workload run. Packet/image checks and baseline workload body are simulated in the new composition fixture; separate preparation tests and historical baseline blocked-sweep coverage remain their own evidence, not interchangeable proofs. Real guard/preflight/owner composition is not stubbed. An unavailable engine or lost manager still requires held recovery; no hard physical-container-cessation guarantee is asserted.

## Exact proposal and disposition

CANDIDATE.json binds two ordinary0644 paths:

- Modify v12/python/tools/authoring_enforcement.py: base2da6eb36b398d730c8cc07a9df0b604de678a3fd994d5019097fa023addfb88f; candidatebc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f.
- Add v12/python/tests/manager/test_authoring_manager_guard.py: candidate085852ceea66efc359c1c27a76e102755ca3c55e367c035cf809c32c4cfa49a0.

No existing test expectations changed. The new tests explicitly treat admitted-only fixture output as held rather than completed, which is consistent with accepted evidence requirements. Custody444 is not import mode. Current target/base/mode/overlap checks remain required before import.

E335045's new temporary direct isolated exception expires at this independent acceptance. W333735 stays closed with its separate old exception expired. Pass to baton.decide for human-plus-agent integration/disposition and human Git checkpoint; suggested message: fix(v12): keep authoring and enforcement under one manager guard. No agent staging or commit. Consumers W333485/W333486 remain gated until owner disposition, then need new exact-source preparation and separate execution selection. Do not rerun withdrawn packets or treat this acceptance as deployment/provider authority. W325959 remains joined acceptance consumer; no further split is warranted for this coupled correction.
