# Progress

Allocated for preparation; no implementation started.

## 2026-11-23 — baton.codxpc, claim E385885

Retained candidate reconstructed and verified byte-for-byte in work/scratch/w385695-385885. Custody/reconstruction and focused retained-probe evidence: evidence/continuation-385885/. Implementing deterministic crash-cut/reentrancy protection in the isolated candidate, with additive tests in tests/job_manager/test_publication_recovery_execution.py. Remaining checkpoint-2 runtime confinement, real admission receipts and prior-session authority still require correction/verification; no completion or acceptance claimed.

### E385885 preserved result

Incomplete, not ready for acceptance. Five-path safety delta and full25-path candidate preserved in evidence/continuation-385885/candidate-files/, candidate.patch and delta.patch; manifest531ddac1f6fd2203fe3574c5c31726b6ca3781e3bdbf7240c54d324696d53eef. Required modules307/307 in15.980s; exact compatibility12/12 in25.055s; detailed failed probes and remaining runtime/serving integration obligations in REPORT.md and test-accounting.json. No host import/live changes. Return for independent delta review and implementation continuation under accepted scope, not a new product decision.

## 2026-11-23 — baton.prompt (K), owner-selected interactive continuation (M385897), no claim

Sole continuation writer per M385897. Start: preserved manifest 531ddac1…53eef and evidence/continuation-385885/REPORT.md, unchanged.

### Checkpoint K-1 — candidate verified, baseline reproduced, integration seam chosen

- Verified: candidate-manifest.json 531ddac1…, candidate.patch 6e3935aa…, delta.patch 8312c7e6…; all 25 candidate-files hashes match the manifest.
- Reconstructed in my own isolated disposable repository `work/scratch/w385695-K-385897/repo` (git archive of 6079ad78, then the 22 product paths overlaid; no alternates). Its diff over base equals candidate.patch for every product path (0 differing). Codexpc's scratch `work/scratch/w385695-385885` is untouched.
- Baseline on that reconstruction: the four required modules pass 307/307 in 16.317 s (prepared interpreter via `just test-one`; disk scratch `work/scratch/w385695-K-385897/verification`). Log: scratch `logs/baseline-required.log` (to be promoted with the final evidence).
- Surveyed (read-only) the serving path and precedents. Confirmed in the candidate: `publication_execution._publish` calls `PublicationWriter.adopt` in-process on the manager; `advance_publication` and `publication_seam()` have no production caller; `stage_execution.ROLES` refuses a publication worker; `projection._RUNNING` has no publication key; the launch document carries durations only, no absolute instant; the default `publication_decision.owners` holds a read-only Authority and no sessions.
- Precedents to reuse rather than invent: `single_worker.worker_operations(..., stage=<owner>)` with a role-specific `mount` and `end` (`StageComposition`, `ManagedApplyRuntime`, `AnalysisExecution`); the deterministic `ManagedApplyAgent` run by the unchanged `baton_worker.main`; read-only delivery at `/input/source` through `source_boundary.compose_source_boundary`; `request_runtime_start` / `reconcile_runtime` for lost-launch reconciliation by exact labels; process-group supervision as in `worker/reconciliation_task.run_bounded`; raw participant sessions already minted by `stage_execution._minted`.

Design being implemented (within the selected contract; no new decision):
1. Worker: a deterministic publication agent run by `baton_worker.main`, whose `work` runs the copy as a supervised child process group bounded by the ABSOLUTE deadline delivered in a pinned input document, and answers the declared outputs; no provider, no credential.
2. Host: a publication stage owner composed over the publication worker's ordinary `single_worker` lifecycle — staged original delivered read-only at `/input/source`, intent committed before the runtime start, result recorded only from the stopped runtime's measured outputs, ordinary freeze/intake/cleanup, runtime and token facts read from their owners.
3. Serving: the publication pass wired into the sweep; the prior assignment ended through the producer's own already-held serving session.
4. Tests: the existing in-process cases moved onto the real lifecycle with a fake engine at its normal boundary; added hung-child, host-loss, restart, cancellation, missing/invalid deadline cases.

Not done yet: everything in 1–4. No acceptance claimed.

### Checkpoint K-2 — confined publication runs end to end through the ordinary worker lifecycle (isolated candidate, not complete)

State of `work/scratch/w385695-K-385897/repo` (disposable repository, commits "K: …" on top of the 531ddac1 overlay):

- New `v12/worker/publication_entry.py`: `PublicationAgent` run by the unchanged `baton_worker.main`; the copy is a child in its own process group, supervised to the ABSOLUTE deadline read from the pinned `publication.json`; missing, zone-less or unparseable deadline refuses before a child exists; a bound that ends the run is a typed fault with no envelope. Probed with real processes: ordinary copy; symlink refused; existing destination refused; a hung child with a TERM-ignoring grandchild ended at the instant with the group observed empty (3.0 s for a 1 s bound); no stray process left.
- `job_manager/publication_execution.py`: the `writer`, `authority` and `adapter` seam members are gone; seam is control, host, exclusion, workspaces, runtime (a read of the exchange terminal). New `prepare_launch` (staging, then one durable intent before the runtime start; refuses a missing/unplaceable/reached deadline), `publication_request` (pinned document from committed records, absolute instant only), `record_adoption` (requires the Worker Manager's positive quiescent/settled observation, an answered completed terminal, the worker's envelope under the fresh assignment with zero provider and verifier counts, and this manager's own measurement against the approved digest). `publish` is now the pass's accounting of the one launch and never launches; a faulted/lost exchange or uncertain runtime is journalled UNCERTAIN. `take_custody` only reads the ordinary ending's freeze and intake. `hand_off` additionally requires positive cessation of the publishing runtime.
- `tools/publication_worker.py`: `PublicationWriter` removed. `PublicationStage` is the publication worker's mount and ending plugged into `single_worker.worker_operations(stage=…)`: mount calls `prepare_launch` and delivers the staged root read-only as the nominated source; ending stops and observes quiescence, records the measured adoption, then ordinary freeze, intake, retention, release of its own assignment, and cleanup (runtime destroyed, token returned).
- `tools/single_worker.py`: pinned `publication.json` hook (published, re-proved on restart, named in the preparation record); session `end` forwarded; a publication-role deployment declares no credential slot and composes no credential delivery (a publication worker WITH a slot is refused).
- `job_manager/projection.py`: `_RUNNING` gains the publication kind (was a latent `KeyError`).
- `tools/fresh_attempt_ports.py`: the publication worker's Job identity is the Job-scoped projection (`job_input_identity`), not the whole manifest digest — with the whole digest the worker lifecycle refuses every recovery Job as a legacy identity. This defect was invisible while publication never went through the lifecycle.
- New `tests/job_manager/test_publication_confined_execution.py` (harness plus one spike case so far): real Authority, real stores, real `manager.sweep`, real offer/claim/activation, real launch document and workspace token, fake ENGINE only, real worker entry served over the published exchange reading the directory the engine was told to bind read-only at `/input/source`. Observed in that run: mounts `/input` ro, `/output` rw, `/input/source` ro; conclude performed; runtime `destroyed`, cleanup `retained`; custody then hand-off performed by `advance_publication`; gate open; exactly one review offer owed.

Still owed before this is a candidate: wire the publication pass and the publication role into `manager.sweep` / `stage_execution`; the serving-held-session ending; convert the existing 2489-line execution suite from the removed writer to the real lifecycle; add hung-child, host-loss, restart/lost-launch, cancellation and deadline cases at the engine boundary; registries, operand registry, docstrings; required focused verifier. The four required modules are RED right now by construction (the old suite still names the removed writer). No acceptance claimed.

### Checkpoint K-3 — continuation candidate returned for independent review (not accepted)

Candidate manifest 623ac725b8d31368ea5a268b7c719ec979e1d63052737b2ff2bdeb6e46680698, packet.sha256 3a5027c4328fc0c8519c70ffc640f150c7d3eb02910d227f2052450d971bc29e, in `evidence/continuation-K-385897/` (REPORT.md, candidate-manifest.json, candidate.patch over base, delta.patch over 531ddac1, candidate-files/ for all 28 paths, test-accounting.json, logs/, probe_worker.py). Isolated repository `work/scratch/w385695-K-385897/repo` head 671ee3a3.

Since K-2: the publication pass and the serving manager's prior-assignment ending are wired into `manager.sweep`; `publication_recovery.end_prior_assignment` / `advance_endings` added and `_ended_prior` replays its own record; the pooled `stage_execution` accepts and composes an optional publication role in the publication lane (`ROLES` unchanged; `WORKER_ROLES` added) with a lookup over already-held producer sessions; the execution suite is converted from the removed writer to the real worker lifecycle (109 cases) with hung-child, host-loss, lost-start, cancellation, deadline, conformance, containment and ticks-only joined cases.

Final verification on 671ee3a3: four required modules 326/326 (28.0 s); whole test_stage_execution 514/514 (357.3 s); job_manager group 2228 collected, 2225 passed, 3 long-scratch-path message failures that pass under a short path; wider affected set 589 run, 568 passed, 21 errors all in test_managed_apply and identical on base 6079ad78 and on 531ddac1.

Not done or not proved (REPORT.md section 6): no worker image recipe and no engine or container run; the pooled `operations_from` publication branch is configuration-tested only and no installer produces a publication worker; per-Job binding of a pooled publication worker not examined; post-hold container removal, token return and owner-item delivery not exercised; installed resume/status commands and review binding untouched (checkpoint 3).

Shared files changed here that W385830 N1/N2 will build on: `tools/single_worker.py`, `tools/stage_execution.py`. No host import, protected Git mutation, build, engine operation or live call. Human Git checkpoint is due only after independent acceptance and import.

### Checkpoint K-4 — R1–R3 corrected after review 2026-11-23T18-55-03Z; refreshed candidate returned for delta review (not accepted)

Response to review-2026-11-23T18-55-03Z.md (M385902) under M385904. Previous candidate 623ac725… and its packet `evidence/continuation-K-385897/` are preserved unchanged (41 packet entries re-verified).

New candidate manifest 69b9328cfa8104dadb818af9d186818b6c70a9d5328e2a1bea06cc5650bebe75, packet.sha256 47e1a6d0cc30e999647a4c963b025e5c5b24361b513c24e26d87fde1a02845a0, in `evidence/continuation-K-385904/` (REPORT.md, candidate-manifest.json, candidate.patch over base, delta.patch over 623ac725, candidate-files/ for all 36 paths, test-delta.json, test-accounting.json, logs/). Isolated repository `work/scratch/w385695-K-385897/repo` head a0d57183. 36 paths over base, 16 changed since 623ac725.

- R2: one two-clock `Bound` per execution held to process exit; `supervised` compares the completion instant; `baton_worker` asks an agent that defines `may_complete` before the completion envelope and before the `answered` state; a watch thread ends the process at the instant while measuring; a restarted worker starts nothing.
- R3: `stage_execution._served_deployment` derives the installed publisher's document for each recovery's Work and original task; admission submits under that identity (`DeploymentBinding.publication_input`); `operations_from` composes one capacity with per-recovery operand sets; the task reader follows the recovery lineage. Installed configuration is not rewritten.
- R1: `pool compose-worker --role publication` and `add-worker`; bootstrap accepts one dedicated publication worker, registers it on the implementation route and prepares its staging root; validator holds one publisher with its own participant; recipe `v12/worker/Dockerfile.publication` (not built); `_bound` now compares the installed worker by worker id (the shipped binding could never satisfy the participant comparison).
- Joined pooled case: two failed Jobs on two Works served by one installer-composed publisher through `operations_from` — reservation, held-session ending, repeated admission, publication, custody, hand-off — with negatives.

Changed tests: 28 added, 0 removed, 2 modified (reasons in REPORT.md section 4): `test_the_recovery_input_is_the_approved_original_and_not_the_task` asserted the R3 defect and now asserts the derived identity while keeping what it protected; `test_the_two_recipes_without_an_adapter_import_the_worker_alone` gained the new recipe.

Verification: four required modules 342/342 (37.986 s) and installer/bootstrap/packaging set 248/248 on the final source; the reviewer's seven probes pass unmodified (were 3 pass, 3 fail, 1 error); whole test_stage_execution 517/517 (359.244 s), job_manager group 2244 collected / 2241 passed / 3 long-path failures (103/103 under a short path), focused tools+manager set 1338 run / 1302 passed / 1 failure / 35 errors on b143d92d — 21 test_managed_apply errors as before, and 15 failing identities in test_job_task_delivery and test_frozen identical on the unmodified base. b143d92d to final is comment, docstring and operator-text only. The `scans` group was ended at my 400 s limit: 74 of 75 shards finished, 30 failed; not complete and not clean.

Not done or not proved (REPORT.md sections 6 and 7): no image build or container run; the two failed executions in the pooled case are fixture-built because the accepted `retained_output_of` refuses the line workspace layout a pooled producer prepares (F1); the review lane there is configured to agree and production review binding is unresolved (F2); a worker admitted only with `add-worker` is dropped by the next repeat (F3, pre-existing); reclaim after an uncertain publication and owner-item delivery after failure or expiry not exercised; the failed-observation status qualifier unchanged.

Shared files W385830 N1/N2 will build on now also include `tools/pool.py`, `tools/bootstrap.py` and `v12/worker/baton_worker.py`. No host import, protected Git mutation, build, engine operation or live call.

### Checkpoint K-5 — internal checkpoint 1 under COMPLETION-PLAN-385909 (outcomes 1 and 3, owner side of outcome 2); one blocking decision raised

Recoverable progress checkpoint, not a candidate for acceptance. Manifest 485488c05e311c40bb058e308aa3a6059940c6d3e2effd2691792bbb8b404620 in `evidence/checkpoint-K-385911-1/` (CHECKPOINT.md, candidate-manifest.json, candidate.patch over base, delta.patch over 69b9328c, candidate-files/ for all 38 paths, logs/). Scratch repository head 26b6e6cf. Previous packet `evidence/continuation-K-385904/` preserved and re-verified.

- Outcome 1: `record_adoption` asks the store's fence and absolute bound inside the transaction that writes the result; a refused adoption is recorded as `publication.ended` (expired or cancelled); a committed result replays; the stage ending decides the adoption before recording the worker disposition.
- Outcome 3: `settle` act in the publication pass (fresh engine read, supported fourth ending, exact token return, one owner item to the deciding participant, no retry); `runtime-unknown` / `runtime-known` records; unknown observation reported while in flight; read-only `manager publication-status`.
- Outcome 2, owner side: `workspaces.retained_output_of` measures the declared output directory rather than the whole writable root, and locates a line-layout original through the attempt's writer grant and line record with writer-exclusion, later-writer, namespace and identity checks. A really pooled producer's failed output is now read by the default inspection.

Verification on 26b6e6cf: four required modules 358/358 (44.750 s); focused owner/custody/intake/installer/manager set 954/954 (35.042 s); 9 of 10 reviewer probes pass unmodified, the tenth asserts the layout hold that no longer exists. Whole test_stage_execution, the job_manager group and scans not rerun for this checkpoint.

Changed tests: 16 added, none removed, 3 cases and several fixture helpers modified (reasons in CHECKPOINT.md section 6).

BLOCKED: outcome 2's connected positive proof. The accepted `SourceCorrespondence` port reads the declared base only from the measured bundle, and the real adapter's bundle is a thin `base..HEAD` transport that does not carry it; with real git the read fails for every real producer. Options and a recommendation are in CHECKPOINT.md section 3; the choice is the owner's. Outcome 4 not started.

### Checkpoint K-6 — internal checkpoint 2 under COMPLETION-PLAN-385909; connected path to hand-off; one design decision raised

Recoverable progress checkpoint, not the complete candidate. Manifest 5023ec31ac9ec23170b44d7e8b4343e850075a53fe32fca9441d6d9303a515c1, packet.sha256 413a73f9661c7e26699b80fe6a81c00cfd5aef9764613f9cab4a3d88e95369cd, in `evidence/checkpoint-K-385913-2/` (CHECKPOINT.md, candidate-manifest.json, candidate.patch over base, delta.patch over 69b9328c, delta-from-checkpoint-1.patch, candidate-files/ for all 38 paths, logs/). Scratch repository head b5abcd8a. Earlier packets preserved and re-verified.

- Option A (M385913): the host owner answers the line's recorded source for a line-layout original; the Git-aware port imports the declared base from it by exact full object name after re-proving its identity, then the candidate from the bundle; no fallback; attempt layout unchanged.
- Connected path: installed `create`, real pooled producer overflow, supported fourth ending, installed `publication-inspect` (eligible), installed `publication-decide` (admitted), restarted manager, installed publisher, custody, hand-off, installed `publication-status`.
- Ordinary reviewer servability: the recovery Job is submitted under the original Job's input identity; the publication stage is held to its own identity through `publication_recovery.stage_job`, used by the scheduler's offer binding, the selector and the publication capacity.
- Also: pooled `cancel_attempt` / `fence_unstarted_attempt` routing for the publication capacity; `bootstrap.variant` answers multi-Job when a publisher is configured; owner item for a recovery that closes before launch.

Verification on b5abcd8a: four required modules 365/365 (51.957 s); job_manager group 2267/2267 with clean accounting (short scratch path); whole test_stage_execution 517/517 (357.602 s); focused owner/installer/creation set 861/861 (130.612 s); 9 of 10 reviewer probes, the tenth asserting the fixed line-layout refusal. Scans not rerun; still incomplete and unattributed.

Changed tests since checkpoint 1: connected class (3), base-origin class (2), pooled reviewer and cancel cases (2), before-launch case (1), bootstrap variant case (1) added; the pooled two-Work fixture's reviewers made ordinary and its Jobs admitted under the pool's own identity; the fixture-declaration negative class removed because ordinary reviewers now serve (its assertion is replaced by the two cross-lane negatives in the new reviewer case).

OPEN, raised for the owner: the reviewer is admitted and not run. An ordinary reviewer mounts a frozen line checkpoint, and the line owner freezes a recovered checkpoint only for a released writer; a producer whose publication failed was never released. Options R1–R3 in CHECKPOINT.md section 3. Routine remainder after that: hand the Work to the review route at the publication ending, deliver the publication hand-off document, run the reviewer and collect its verdict, restart/cancel cuts at review, acceptance matrix, qualification commands.

### Checkpoint K-7 — complete source candidate under COMPLETION-PLAN-385909, returned for independent review (M385915)

Author: baton.prompt (K), owner-selected interactive continuation, no claim. Manifest 6816e935776369ac3064b1c53ff71f3fd298cc38f31271d11b2a1596b8962838, packet.sha256 3923a303b529c7c169cda5ba99be6279332c2edf64f234d3e179312e332a516e, in `evidence/final-K-385915/` (REPORT.md, candidate-manifest.json, candidate.patch over base, delta.patch over 69b9328c, delta-from-checkpoint-2.patch, candidate-files/ for all 42 paths, DESIGN-pin.md, logs/). Scratch head eccef18006a4c77175efa511f1d3c26fd24699e5. Earlier packets re-verified unchanged. Not accepted, not imported, not qualified.

- R1 (owner, M385915): pinned under DESIGN REC-9 in the protected tree's `v12/DESIGN.md` (filesystem edit, on the message's instruction; text in DESIGN-pin.md; not in the candidate path set). Implemented as `review_cycles.freeze_unreleased_recovered_checkpoint` with a separately typed recovery fence, its own committed act, kind-explicit readers (`fence_kind`, `_committed_fence`, `_current_fence`, provider-context finalization) and a read-only `GitCheckpointProfile.head_of`.
- Reviewer delivery and execution: the publication ends by passing the Work to the review route; the hand-off is delivered to the ordinary reviewer as `recovery-review.json`; the line owner is asked before any line is created; the verdict is collected by the ordinary review ending.
- Review-phase owner item (`publication.review-item`) for a published recovery whose review is cancelled, expires or cannot start; `publication-status` reports the review, its reviewer and recorded verdict.
- DEPLOYMENT.md documents the supported decision-to-verdict sequence including the manager restart; REVIEW-CYCLES.md documents the two fence kinds.

Verification on the final head: four required modules 375/375 (83.0 s); 17 affected modules 1540/1540 (188.4 s). On the head one documentation file earlier: job_manager group 2277/2277 with clean accounting; whole test_stage_execution 517/517 (360.1 s); 9 of 10 reviewer probes. `tests.manager.test_boundary_inventory` did not complete on candidate or base; it is failing at base, and 41 failing sub-cases are attributable to this candidate's new receiving entries in `review_cycles.py` and `workspaces.py` — registry update owed, not done. `scans` group not rerun. `tests.manager.test_checkpoint_profiles` not run by standing instruction.

Corrected disclosure: `tests.manager.test_dependencies` failed on checkpoints K-5 and K-6 (undeclared public operand `output`); it was outside the affected set run then. Fixed here by declaring the operand.

Changed tests since K-6: 10 connected cases added; two cases modified because they asserted the checkpoint-2 stop or omitted the fixture-written recovery's ending; operand catalog entry added; none removed (REPORT.md section 7).

Open for the reviewer (REPORT.md section 9): the Job versus publication-stage input identity split; `settle-stopped` producers cannot be reviewed under R1; the fence envelope choice; the inventory registry; no 900-second per-command reviewer bound; no image, container or kernel evidence.

### Checkpoint K-8 — correction packet C1–C5 (review 2026-11-24T00-28-00Z, M385922), returned for independent review

Author: baton.prompt (K), owner-selected interactive continuation, no claim. Manifest 9475646dcbb06f8fc5f65a0a73150cdde2f16c98c51e7b75abb5c065f5d2f783, packet.sha256 e506609817beb95ba3952939694098194912e6f2223a3e1cd2a8aaa650985285, in `evidence/correction-K-385922/` (REPORT.md, candidate-manifest.json, candidate.patch over base, delta-from-reviewed.patch over 6816e935, delta.patch over 69b9328c, candidate-files/ for all 46 paths, qualify-w385695.sh, harness/, logs/). Scratch head 58d452ff0d174dc63a076e711c7633a8116d61c2. Earlier packets re-verified unchanged. No protected-tree file edited this round. Not accepted, not imported, not qualified.

- C1: `checkpoint_of` authenticates a recovery fence against the committed act of the row's own writer and binds it to the row's checkpoint, writer, line, the writer's own row and the frozen candidate; converse refusal for a recovered writer under an assignment fence. Reviewer probe passes unmodified.
- C2: the reviewer's worker (`claude_agent._reviewer_check`) runs the task's verification itself in its own process group under min(900, delivered verification bound, invocation bound), kills and observes the group, hands the provider only the remaining invocation, and withholds an acceptance unless the check passed; the manager holds an acceptance that lacks the worker's own passed, bounded claim. `claude_agent.py` and `review_driver.py` are new to the path set.
- C3: 30 candidate-added receiving entries versus 69b9328c, each with exactly one owner; every newly consumed fence member validated under its own literal label; 27 probes added and all arrive. Four relations naming the base's renamed `freeze_checkpoint` remain, identical at base.
- C4: installed `manager settlement-remove`; `publication-inspect` names it in a `continuation` for a held stopped original; connected case from stopped settlement through removal to the reviewer's verdict; the review item spells the command and both review-phase cases run it. The earlier report's claim that a stopped original is admitted and then refused was wrong and is corrected in DEPLOYMENT.md.
- C5: `qualify-w385695.sh`, parameterized, syntax-checked, not executed; deadline phase freezes the publisher with the engine and changes no approved byte or profile.

Verification on the final head: four required modules 389/389 (104.2 s); 18 affected modules 1825/1825 (202.2 s); job_manager group 2291/2291 with clean accounting; whole test_stage_execution 517/517 (358.5 s); targeted inventory tests 13 of 14 (the failure is the inherited stale `freeze_checkpoint` stated owner); four `review-385919` probes pass unmodified. Whole boundary inventory, `scans` and `test_checkpoint_profiles` not run.

Changed tests since 6816e935: 5 connected cases and a 9-case adapter class added; 27 inventory probes added; reviewer fixture, document assertion, fence-kind references, review-phase cases and four inventory declarations modified with reasons (REPORT.md section 7); none removed.

Open for the reviewer: provider-chosen tool commands are bounded only by the remaining invocation, not per command (REPORT.md section 3); the four inherited registry relations; no image, container or kernel evidence.

### Checkpoint K-9 — correction packet C2–C5 (review 2026-11-24T01-52-00Z, M385927/M385929), returned for independent review

Author: baton.prompt (K), owner-selected interactive continuation, no claim. Manifest 0a9bc8a9ec662761166e1a050209f703b8742a186f914eec81250b4485660bc2, packet.sha256 8cecbd26b814107b4fb7547dd04a6a8a7a6cfe0e145b92c53822a082fbda37b1, in `evidence/correction-K-385929/` (REPORT.md, candidate-manifest.json, candidate.patch over base, delta-from-reviewed.patch over 9475646d, candidate-files/, qualify-w385695.sh, harness/, logs/). Scratch head 2d29513c; 50 paths over base, 11 changed since 9475646d. Not accepted, not imported, not qualified. No protected Git mutation, build, engine, container or live model operation; no protected-tree file edited.

- C2 feasibility: no capability blocker. The pinned CLI 2.1.247 hands every shell-tool command, as one argument, to `CLAUDE_CODE_SHELL_PREFIX`; established on the host with the exact pinned binary against a local scripted endpoint (no model, no credential, no container).
- C2: new `v12/worker/bounded_command.py` (child subreaper; one command under min(bound, absolute deadline); every descendant ended and observed gone; start and finish records). The adapter runs its own check, the provider, and each provider-chosen shell-tool command under it; one invocation origin and deadline with an explicit 5 s ending grace; acceptance withheld on a failed check, an unfinished command or descendants not seen gone; the manager holds the same and no longer accepts `group_gone`. Same-user limit stated.
- C3: five recovery stated owners each have their own witness over a world where the freeze really runs; `EveryStatedOwnerHasAWitness` passes; one probe added for the new reader (28 arrive). The base's stale `freeze_checkpoint` stated owner still fails, unchanged.
- C4: installed removal gates a repeat on the attempt's committed abandonment declaration (new read-only `intake.abandonment_declared`), replays the declared reason, answers `replayed`; `single_worker.abandon_attempt` now releases the adoption window it opened on replay or fault. Lost reply, two crash cuts, preserved refusals and a second-process competing manager are covered.
- C5: `qualify-w385695.sh` rewritten: exact-attempt targeting proved against this instance's roots and this run's images before any effect; one-invocation recovery with trap cleanup of owned processes only; fresh recorded image identities; parsed JSON; structured probe results; installed bundle command. Dry-run against scripted doubles in nine scenarios. No engine phase executed.

Verification: four required modules 409/409 (135.9 s); 22 affected modules 1939/1939 (205.7 s); `test_stage_execution` 517/517 (350.9 s); seven recipe-reading modules 704/705 (the failure is inherited, identical at base); registry classes and witnesses 18/18; reviewer probes unmodified (385919 set passes; 385926 corrections: two pass, one errors on its own precondition because the escaped child is now ended). Whole boundary inventory, scans, the job_manager group and `test_checkpoint_profiles` not run.

Disclosures: an earlier round of mine left `test_parallel_runner`'s record-path sweep failing (fixtures' disposable record locator undeclared); fixed here, present in 9475646d. Rerunning the reviewer's `probe-registry.py` unmodified rewrote `evidence/review-385926/registry-owners.json` with identical bytes; that packet's hashes still verify.

Changed tests since 9475646d: adapter class 9 → 23 cases (two rewritten for the grace and the deadline form); connected class +6 cases; five `StatedRules` witnesses and one probe added; manager-hold case extended to six altered claims; `group_gone` assertions renamed to `descendants_gone`; one synthetic record path declared; none removed.

Open for the owner (REPORT.md section 7): how image qualification gets a deterministic provider (labelled scripted fixture image prepared as option A; a supported endpoint selection is option B). Open for the reviewer: the inherited registry and authority-isolation failures; no image, container or kernel evidence.

### Checkpoint K-10 — correction packet C2/C5 (review 2026-11-24T03-03-48Z, M385935/M385937), returned for independent review

Author: baton.prompt (K), owner-selected interactive continuation, no claim. Manifest 162152b462b8ab0907a43b5dd41f85e8c7c2a6218053b6a93bbf9edc1762a8dd, packet.sha256 b57f29ae6a242de6a500dfcaf8bdc2359ae1856f8f666a41e768671329c0756b, in `evidence/correction-K-385937/` (REPORT.md, candidate-manifest.json, candidate.patch over base, delta-from-reviewed.patch over 0a9bc8a9, candidate-files/, qualify-w385695.sh revision 3, option-a-setup.sh, cli-in-image-driver.py, harness/, logs/). Scratch head 6d6a4fc8; 50 paths over base, 4 changed since 0a9bc8a9. Not accepted, not imported, not qualified. No protected Git mutation, build, engine, container or live model operation; no protected-tree file edited. C1, C3 and C4 unchanged.

- C2: the supervisor reads the clock after it sees the child ended and before it believes that ending, so a command still running at its bound is `timed-out` with no status whatever it then exits with; the allowance is read again at the launch; the adapter applies its own clock to the check's and the provider's supervisor. Five deterministic cases added. Documentation no longer suggests ledger tampering is detected.
- C5: installed layout corrected to `db/` and checked against `tools.instance.layout`; pause intent and acknowledgment records reconciled after the watcher is joined; stack stopped only on proved ownership from the stack's own process records; fixture recipe installs as root and restores the provider image's user; output ceiling pinned to `role_contract.MAX_OUTPUT_BYTES`; `preflight` refuses any provider-role worker not on the labelled fixture image.
- New `option-a-setup.sh` (compose three workers, repeat, create two Jobs, serve to two stopped producers, settle and remove). Its six composing and creating argv were executed against the real `pool`, `bootstrap` and `manager create` commands in the accepted connected fixture; one operand error found and fixed. Its serving phase is proved against doubles only.
- New `cli-in-image` phase and driver for the real pinned CLI inside the provider image with no network. Driver run on the host with the pinned binary and final supervisor bytes: pass. In-container run not executed.

Verification at the final head: four required modules 414/414 (135.2 s); eight worker-affected modules 1083/1083 (51.7 s); reviewer `probe-late-exit.py` and `probe-delta.py` pass unmodified; adapted qualification probe 4/4; 14 qualification and 3 setup dry-run scenarios behave as intended. Registry classes, the 22-module set, `test_stage_execution`, whole inventory, scans, the job_manager group and `test_checkpoint_profiles` not rerun.

Disclosure: one shell edit of mine was cut short by a nested here-document and its remaining lines ran as shell; they failed at once, no engine command ran and nothing was written.

Changed tests since 0a9bc8a9: adapter class 23 → 28 cases; none modified or removed.

Open: installing the qualification instance and the host facts the setup takes are the operator's (REPORT.md section 3.4); every engine phase, including the in-image CLI check, is unexecuted; the two inherited failures are unchanged.

### Checkpoint K-11 — C5 preparation-only corrections (review 2026-11-24T04-42-16Z, M385942/M385944), returned for independent review

Author: baton.prompt (K), owner-selected interactive continuation, no claim. Packet `evidence/correction-K-385944/` (34 entries; `packet.sha256` sha256 `298b604847499d6b867f02685b258c806231ad52e437f38c9c0f29d141aff727`). **No source change**: the accepted candidate stays manifest `162152b4…` in `evidence/correction-K-385937/`; `source-unchanged.json` records the 50-path check (scratch head `6d6a4fc8`, clean). No source test rerun.

- C5.1: both scripts write a start intent with a per-start token before the start, run the start as a self-recorded process, and reconcile from those records on every exit. The stack is stopped through the instance's own `stop` only when every live process is positively this run's (the product's pid-and-start-time answer plus the token in the process's own environment), with a positive read-back; anything else is `UNRESOLVED` with the intent retained.
- C5.2: `pause_state` separates paused, not paused and positively absent from an engine that did not answer; an unknown state is never unpaused blind; every release is read back; a pause request in flight is settled before reconciliation; the leftover listing and the tag cleanup had the same fault and are corrected. A phase with unresolved cleanup does not exit 0.
- C5.3: the CLI driver selects and ends only processes carrying its own turn's random token.

Evidence (doubles only): reviewer `probe-cleanup-cuts.py` 3/3 and `probe-driver-ownership.py` 1/1 with the packet path changed only; reviewer's `probe-qualification-r3.py` 4/4; new `probe-cleanup-r4.py` 10/10; 40/40 dry-run scenarios as required; setup argv through the real commands 1/1; revised driver on the host with the pinned CLI: pass.

Disclosure: two earlier matrix runs were discarded (one stalled and was edited while running; one had two wrong expectations of mine); the retained log is the third, and the second is kept in the packet.

Open: token ownership is not proved against an installed bundle (it fails to "not established", never to a wrong stop); the rerun-after-SIGKILL path is not exercised; every engine phase, the fixture build and the in-image CLI check remain unexecuted; operator install and host facts as before.

### Checkpoint K-12 — C5 script cleanup R1/R2 (review 2026-11-24T05-49-33Z, M385949/M385951), returned for independent review

Author: baton.prompt (K), owner-selected interactive continuation, no claim. Packet `evidence/correction-K-385951/` (30 entries; `packet.sha256` sha256 `8ef13de9db43b69ec7c4f14cf978913a67e569a1a47957f82671655166195af7`). **No source change and no source test rerun**; `source-unchanged.json` records the 50-path check against manifest `162152b4…`. The driver is unchanged.

- R1: a retained start or pause intent is reconciled only on positive evidence about its command (completion record; readable own record and that process positively ended; or, for a start, the same invocation knowing it never forked). A missing or unreadable record is `UNRESOLVED`, the intent is retained, and no new start or freeze is made over it. A positively settled pause is filed.
- R2: a failed image removal sets the unresolved flag, so `cleanup` exits nonzero; `images.owned` is kept and nothing is forced.

Evidence (doubles only): reviewer `probe-restart.py` 3/3 with the packet path changed only; new `probe-cleanup-r5.py` 17/17; reviewer cleanup-cuts 3/3, driver-ownership 1/1, qualification-r3 4/4; `probe-cleanup-r4.py` 10/10 after its fixtures were given the completion record they implied; nine affected dry-run scenarios 9/9. The 40-scenario matrix was not repeated.

Open: unchanged from K-11; every engine phase, the fixture build and the in-image CLI check remain unexecuted.

## 2026-11-24T08:08:06.397363+00:00 — coordinator direct reviewer correction

Implemented per-attempt disk verification copy, honest missing-supervisor-result classification, and recovery failure observation/owner-item delivery over frozen unable. Evidence: evidence/qualification-review8-correction/REPORT.md. 437 affected tests passed before final status-order adjustment; 28 connected tests passed on final bytes (overlapping coverage). Engine-only old/corrected storage probes retained. Candidate source copies and 56-path identity retained. No live Job, protected Git mutation, or instance update. Next: owner refresh command in PLAN, then fresh scripted gate; deadline gate and checkpoint still pending.

## 2026-11-24T08:18:50.003629+00:00 — coordinator completion reader correction

Corrected recovery review status to use composed ending settlement plus frozen result and positive cleanup, instead of episode retirement alone. Retained recovery-9 reads completed/accepted without mutation. 28 connected tests passed; final null-attempt guard passed the ordinary-review case separately. Evidence and source: evidence/qualification-review9-status/. Prepared owner-finish.py and /tmp/baton-w385695-finish-recovery.py for packaging plus retained readback only; no rerun. Deadline gate and checkpoint remain pending.

## 2026-11-24T08:37:57.326081+00:00 — owner-approved combined deadline qualification passed

Owner answered yes to the explicit combined-proof selection. Host-clock coverage: 30 passed, 11.326s. Exact publication image real-container probe: 3s absolute deadline, blocked child ended and group positively gone in 5.013s including termination grace, same-deadline replay started no child, container removed. Evidence: evidence/qualification-short-deadline/QUALIFICATION.md and engine-fy4g2v0h/. Production profile stays at 900s. This supersedes the earlier continuous installed-stack deadline qualification requirement for this delivery, without claiming that run passed. Positive installed recovery-9 and packaged readback already passed. No Git mutation, live model or new Job.
