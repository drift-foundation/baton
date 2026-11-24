# W385695 checkpoint 2 — K corrections R1–R3 after review 2026-11-23T18-55-03Z

**Status: refreshed candidate returned for independent delta review. Not accepted, not imported, not "resume supported".**
Author: baton.prompt (K), owner-selected interactive continuation (M385897, M385904), no claim.
No host import, no protected Git mutation, no image build, no engine or container operation, no live call, no credential read.

## 1. Identity

| | |
| --- | --- |
| Base | `6079ad78345aa87b7148db302d48fb9b1867f940` |
| Previous candidate (preserved, unchanged) | manifest `623ac725b8d31368ea5a268b7c719ec979e1d63052737b2ff2bdeb6e46680698`, packet `evidence/continuation-K-385897/` — all 41 entries of its `packet.sha256` re-verified before this work was packaged |
| This candidate | manifest `candidate-manifest.json` in this directory; its sha256 is in `packet.sha256` and in the Baton message |
| Paths | 36 over base (28 before); 16 changed since `623ac725` |
| Patches | `candidate.patch` over base; `delta.patch` over the previous candidate |
| Scratch repository | `work/scratch/w385695-K-385897/repo`, head `a0d5718388b62e78fbbcf6635073bade5b7f7b1e` (disposable; not the only copy) |

The 16 delta paths: `v12/worker/baton_worker.py`, `v12/worker/publication_entry.py`, `v12/worker/Dockerfile.publication` (new), `tools/bootstrap.py`, `tools/pool.py`, `tools/stage_execution.py`, `tools/single_worker.py`, `tools/publication_worker.py`, `tools/fresh_attempt_ports.py`, `job_manager/publication_recovery.py`, `DEPLOYMENT.md`, and five test modules (`test_publication_recovery_execution`, `test_stage_execution`, `test_pool`, `test_bootstrap`, `test_worker_packaging`).

Eight of those were not in the previous path set: `baton_worker.py`, `Dockerfile.publication`, `bootstrap.py`, `pool.py`, `DEPLOYMENT.md`, `test_pool.py`, `test_bootstrap.py`, `test_worker_packaging.py`.

## 2. What was corrected

### R2 — the absolute deadline now governs the whole publication

The defect was as reviewed: the bound was compared only while the copy child ran, and the measurement and completion envelope ran after `work` returned, bounded by nothing.

- **One `Bound` per execution**, made before anything starts and held until the process exits. It is reached when either the wall clock reaches the delivered instant or the remainder first observed has elapsed on the monotonic clock. A clock set back cannot extend it; a clock set forward ends it early.
- **`supervised` compares the completion instant.** A copy observed finished at or after the instant is a timeout with no status.
- **Two commit-point gates in the ordinary worker.** `baton_worker` asks an agent that defines `may_complete` immediately before the completion envelope is written and again before the `answered` state. A refusal is the ordinary faulted ending with code `agent`. An agent that defines no `may_complete` is asked nothing.
- **A watch thread ends the process.** When the instant is reached while the main thread is measuring or writing, the worker exits with status 75 and publishes no terminal. During the copy the watch first leaves the supervisor its own window, because the supervisor's ending observes the process group and reports a typed fault. Once a fault is being reported the watch stands down so the typed fault is published.
- **Restart.** A second incarnation finds the receipt and starts nothing, with or without time left.

Host cessation enforcement and positive observation are unchanged.

What this does not close: between the second gate and the atomic publication of the answered terminal there are two small fsynced writes. The watch can end the process inside that window, but a terminal published inside it is not prevented by the worker. The host's own fence remains the other half, as before.

### R3 — one per-recovery derivation, used by admission, compatibility and delivery

- `stage_execution._served_deployment` now derives, for the publication role, the installed worker's document bound to **this recovery's Work** and **the original Job's task**. Nothing else moves: declared outputs, policy, profile, image and source declaration stay the installed publisher's.
- **Admission** asks the deployment for that document's Job-scoped identity (`DeploymentBinding.publication_input`) and submits the recovery Job under it, instead of under the installed worker's own identity.
- **Compatibility** is the unchanged selector over the same derivation. `_disagreements` is not weakened and still names a wrong Work.
- **Delivery**: `operations_from` composes one publication capacity with one held operand set per bound recovery (`publication_worker.PerRecoveryOperations`, the shape of the existing per-Job integration composition). A stage of a Job the deployment derived nothing for is refused.
- **The task lineage.** `single_worker.job_task_reader` reads a recovery Job's task from the original Job through the recovery owner's committed reservation/admission record, so the serving side and the admission resolve the same task.
- The installed configuration is never rewritten to make this true; the pooled case compares the installed worker entry before and after.

### R1 — supported installation and the real pooled path

- **Installer.** `pool compose-worker --role publication` composes the worker from this build's own documents: no credential, no CLI, network `none`, the two selected declarations read from `publication_recovery`, the instance's execution policy, its own runtime profile and adapter. Provider operands are refused, not dropped. `pool add-worker` and the worker wrapper accept the role.
- **Bootstrap.** The install document may name one publication worker, under a participant no other worker uses. Its participant is registered on the implementation route, where a recovery makes its fresh claim. Its private staging root is prepared with the worker's other roots; no repository is cloned for it.
- **Validator.** `stage_execution` holds at most one publication worker and a dedicated participant and principal, in the validator both install paths call.
- **Recipe.** `v12/worker/Dockerfile.publication`: the reference image's pinned Python base, the ordinary worker, `publication_entry.py`, the frozen control schema, UID/GID 65532, exec-form entry. Not built.
- **A defect the stand-in port hid.** `publication_recovery._bound` compared the installed worker's *participant* against the *worker ids* the real selector returns, so the shipped binding could never satisfy it. It now compares the worker id.
- **Operator text** in `v12/python/DEPLOYMENT.md`.

## 3. The joined pooled proof

`tests.job_manager.test_publication_recovery_execution.OneInstalledPublisherServesRecoveriesOnTwoWorks`.

Two failed Jobs on two Works, each held by its own producer. One publication worker, composed by `pool.composed`, named in the install document, staged by `bootstrap.prepare_prerequisites`, published by the bootstrap repeat. The serving object is `stage_execution.operations_from`'s. The owner ports are `publication_decision.owners`'.

Observed, per recovery:
1. The owner's admission reserves and is refused (`refused/capability`); nothing is ended.
2. The serving manager's next tick ends exactly that assignment through the producer session the deployment already holds.
3. The same admission, repeated, admits. The two recoveries carry different input identities, each equal to the derivation's.
4. After the serving object is recomposed, the one worker (`publisher`) is allocated both publication stages in turn.
5. Each container's `/input/input.json` names its own Work; each `task.json` is its original Job's task, byte for byte.
6. Each adopted proposal measures as its own original; custody and hand-off exist; the gate opens; each original tree is unchanged.

Negatives: a stage handed to the other recovery's operands is refused by the worker lifecycle; a Job nothing was derived for is refused; the shipped selector answers nobody for another recovery's input, the installed identity, another task, no task, or another policy; no review allocation exists before the hand-off.

**What is a double in that proof, stated plainly:**
- The engine, at its normal boundary.
- The Git consumer's process (checkpoint 1's own `GitEngine`).
- **The two failed executions.** Each failed Job is created by the product's creation operation over stand-in creation ports, as checkpoint 1's accepted fixture does. Its attempt row, retained output and workspace token are then written through the owners' operations by the fixture. No producer was run. The reason is finding F1 below.
- **The review lane's declarations.** Each Work's reviewer is configured with the publication declarations so the recovery's one input identity is servable by both stages. That is a fixture selection; see F2.

## 4. Rewritten and added tests

`test-delta.json` holds the AST comparison against the previous candidate. No case was removed.

| Module | Before | After | Added | Modified |
| --- | --- | --- | --- | --- |
| `test_publication_recovery_execution` | 109 | 125 | 16 | 1 |
| `test_stage_execution` | 514 collected | 517 collected | 3 | 0 |
| `test_pool` | 58 | 63 | 5 | 0 |
| `test_bootstrap` | 163 | 166 | 3 | 0 |
| `test_worker_packaging` | 9 | 10 | 1 | 1 |

The two modified cases and why:
- **`test_the_recovery_input_is_the_approved_original_and_not_the_task`** asserted that a recovery is submitted under the installed worker's own identity. That is the R3 defect. It now asserts the derived identity, that the derived document names the original Job's task and the recovery's Work, that outputs and policy did not move, and that the recorded installed-worker identity is unchanged. The rule it previously protected — not the whole runtime manifest digest, not the recovery-input digest, not the original Job's digest — is still asserted.
- **`test_the_two_recipes_without_an_adapter_import_the_worker_alone`** gained the new recipe in its loop. Nothing was relaxed.

Fixture changes in the execution suite, each of which makes the fixture follow the product rather than stand in for it:
- The fixture binding answers `publication_input` by calling the product derivation, and answers `serving` with worker ids, as the shipped port does.
- The single-worker composition is built over the derived document rather than the installed one.
- The worker's watch thread is off by default in-process (it ends the process it runs in); the cases about it either read its decision directly or run a real child process.

## 5. Verification

Prepared interpreter through `just`; disk-backed scratch. Numbers are from the retained logs.

| Run | Source | Result |
| --- | --- | --- |
| Four required modules | final `a0d57183` | 342 collected, 342 passed, 37.986 s |
| Installer, bootstrap, packaging and the publication stage class | final `a0d57183` | 248 passed, 20.431 s |
| The reviewer's seven probes, unmodified | final `a0d57183` | 7 passed (were 3 passed, 3 failed, 1 error) |
| Whole `test_stage_execution` | `b143d92d` | 517 passed, 359.244 s |
| `job_manager` group | `b143d92d` | 2244 collected, 2241 passed, 3 failed |
| Those three under a short path | `b143d92d` | 103 passed |
| Focused tools and manager modules | `b143d92d` | 1338 run, 1302 passed, 1 failed, 35 errors |
| `scans` group | final `a0d57183` | **not complete, not clean** — see below |

`b143d92d` to the final source is 4 files, 49 insertions, 8 deletions: operator text and three comments or docstrings. No executable statement changed, and both touched test modules were rerun on the final source.

The failures, none of which is a clean result:
- **3 in the `job_manager` group** are the same long-scratch-path message cases as before; they pass under `/var/tmp/k695`.
- **21 errors in `test_managed_apply`** are the same as reported at the previous candidate.
- **14 errors in `test_job_task_delivery` and 1 failure in `test_frozen`** were new to my wider set this round. Their 15 failing identities are identical on the unmodified base commit (`logs/base-ids.txt`, `logs/cand-ids.txt`).
- **`scans`**: I ended the run at my own 400 s limit with 74 of 75 shards finished: 44 passed, 30 failed (29 in `test_boundary_inventory`, 1 in `test_text_sweep`). All five scan modules inventory `baton_v12.worker_manager`, in which this candidate changes no file. Two failing cases were sampled and fail identically on base. Identity with base was not established for the other failed shards.

## 6. Findings that need a decision or an owner

**F1 — a really pooled producer's failed output cannot be inspected.** I ran a real producer through the pooled composition and made it overflow its output ceiling (`logs/observation-pooled-producer-overflow.py`). The installed `publication-inspect` then held for two reasons:
- the failed attempt's cleanup was still pending (a supported stopped-settlement command exists; I did not drive it);
- `workspaces.retained_output_of` refuses a preparation whose workspace layout is `line`, and the pooled implementation role prepares exactly that layout.

The second is accepted checkpoint-1 code and is deliberate there. It means an approval can never be reached for a producer run through the pooled composition, independently of R1–R3. This is outside the three review items and I did not change it.

**F2 — the recovery's review stage is servable only by a reviewer that carries the recovery's Job-scoped declarations.** A recovery Job has one input identity and both stages are held to it. With an ordinarily configured reviewer the repeated admission stops at the review stage: reserved, incomplete, nothing submitted, nothing published (`AReviewerWithoutThePublicationDeclarationsHoldsTheAdmission`). That is fail-closed, and it is also an open design item: how a production reviewer comes to be servable is the review binding the contract places in checkpoint 3. I did not design it.

Related observation: in the pooled proof, after the hand-off the manager allocated and started the review stage on that Work's reviewer. What that reviewer is delivered was not examined.

**F3 — a worker admitted only with `pool add-worker` does not survive the next bootstrap repeat.** A recovery's Job binding is prepared from the install document, and the repeat composes the worker list from that document alone (`logs/observation-repeat-drops-admitted-worker.py`). This predates this work and applies to every role. The publisher must therefore be named in the install document; `DEPLOYMENT.md` says so. I did not change the behaviour.

**F4 — a running manager serves the bindings it started with.** After the repeated admission amends the configuration, the publication stage is served once the serving object is recomposed, as in the accepted retained-recovery joined case. The owner-visible sequence is: admit (reserved, refused) → manager tick ends the prior assignment → admit again → manager restart → publication.

**F5 — `baton_worker.py` changed.** It is copied into every worker image. The change is inert for every agent that defines no `may_complete`, and it changes the bytes the next build of each image carries.

## 7. Not done or not proved

- No worker image was built and no container ran. Read-only confinement is a mount vector handed to a fake engine.
- No producer was run to failure in the pooled proof (F1); the review lane's declarations there are a fixture selection (F2).
- M385904 also asked to finish owner-held and reclaim evidence through supported paths. Owner-held admission is now shown through the shipped ports. **Not done:** reclaim or return of the token after an uncertain publication, and delivery of an owner item after failure or expiry.
- The failed-observation qualifier the review asked to be retained in final status is unchanged: `publication_readiness` still answers `uncertain=False` while engine reads fail. Nothing regressed; nothing was added. It needs a durable record of the failed observation, which belongs with the status command.
- The manager's handling of a worker that ended itself at the bound is the existing lost-exchange path; it was not exercised end to end with a real exited container.
- The installed resume and status commands and the production review binding are checkpoint 3.
- The `scans` group is neither complete nor clean (section 5).

## 8. Handoff

- **Outcome:** R1, R2 and R3 corrected in the isolated candidate; the reviewer's seven probes pass unmodified.
- **Required for acceptance:** independent delta review of `delta.patch` against `623ac725`, reading the two modified cases against the rules they previously asserted.
- **Decisions the review or the owner may need to take:** whether F1 and F2 hold checkpoint 2 open or are assigned separately; whether the unfinished reclaim and owner-item evidence does.
- **Shared files** changed here that W385830 N1/N2 will build on: `tools/single_worker.py`, `tools/stage_execution.py`, and now `tools/pool.py`, `tools/bootstrap.py` and `v12/worker/baton_worker.py`.
- A human Git checkpoint is due only after independent acceptance and import.
