# W385695 — complete source candidate under COMPLETION-PLAN-385909

**For independent review. Not accepted, not imported, not qualified.** All four plan outcomes are implemented and covered at source level; section 9 lists what is not proved.
Author: baton.prompt (K), owner-selected interactive continuation (M385915), no claim.
No host import, protected Git mutation, image build, engine or container operation, live call or credential read. One protected-tree file was edited on instruction: `v12/DESIGN.md` (section 2).

## 1. Identity

| | |
| --- | --- |
| Base | `6079ad78345aa87b7148db302d48fb9b1867f940` |
| This candidate | `candidate-manifest.json`; sha256 in `packet.sha256` and in the Baton message |
| Scratch repository | `work/scratch/w385695-K-385897/repo`, head `eccef18006a4c77175efa511f1d3c26fd24699e5` (disposable) |
| Paths | 42 over base; 19 changed since the last reviewed candidate; 11 since checkpoint 2 |
| Last reviewed candidate (preserved) | manifest `69b9328c…`, `evidence/continuation-K-385904/` |
| Checkpoint 1 (preserved) | manifest `485488c0…`, `evidence/checkpoint-K-385911-1/` |
| Checkpoint 2 (preserved) | manifest `5023ec31…`, `evidence/checkpoint-K-385913-2/` |

`candidate.patch` is over the base. `delta.patch` is over the last reviewed candidate `69b9328c`, so a reviewer has one delta to read. `delta-from-checkpoint-2.patch` is the work since M385915.
**Application proof:** the packet builder applied `candidate.patch` with `git apply` to a fresh archive of the base in an isolated directory, compared all 42 paths by sha256 with `candidate-files/`, and confirmed no other path differs.

The 11 paths changed since checkpoint 2: `worker_manager/review_cycles.py`, `worker_manager/provider_context.py`, `checkpoint_profiles.py`, `job_manager/publication_execution.py`, `tools/stage_execution.py`, `tools/publication_worker.py`, `tools/publication_decision.py`, `DEPLOYMENT.md`, `REVIEW-CYCLES.md`, `tests/job_manager/test_publication_recovery_execution.py`, `tests/manager/test_dependencies.py`. No worker image byte changed since checkpoint 2.

## 2. The R1 ruling, pinned and implemented

**DESIGN pin.** M385915 required the approved trust rule to be pinned in the appropriate DESIGN clause before dependent implementation. I added one paragraph and its decision-record line under REC-9 in the protected tree's `v12/DESIGN.md`, restating the ruling in FINDING without broadening it. This is a filesystem edit of a file that already carries other uncommitted owner edits; it is **not** part of the candidate path set. The exact text is in `DESIGN-pin.md` here. My standing instruction was not to edit DESIGN; I read M385915 as the explicit exception for this one clause. Say so if that reading is wrong and I will hand you the text instead.

**The owner operation.** `review_cycles.freeze_unreleased_recovered_checkpoint`. Required before anything changes:

- the writer is this attempt's own at this generation, still `active`, and was never released;
- the line is still `writing` at the checkpoint that writer was granted on;
- the attempt's runtime axis says destroyed with settled cleanup, **and** exactly one committed removal is read back through its own family reader (abandoned, ordinary or deadline) under the caller's retention policy;
- no later writer was granted on the line;
- the clean checkout's head equals the approved candidate's and the candidate's base equals the line's declared base. The head is read **before** the writer is revoked, through a new read-only `GitCheckpointProfile.head_of`.

One transaction then revokes the writer (reason `recovered`), writes the fenced `preparing` checkpoint row and moves the line to `freezing`, re-deciding every mutable fact under the lock. The profile freeze completes as an ordinary one does. A retry returns the same committed checkpoint with no new record; another candidate under the same writer collides; every hold leaves the writer active, the line `writing` and no record.

Nothing is asked of the Authority and nothing is recorded for the producer: its disposition stays `none`, nothing is frozen for it, and no release exists. All three are asserted in the connected case.

**The fence is separately typed and readers validate the kind.** The fence's intent is a closed document naming `kind: review-line.recovery-fence`, journalled as its own act `review-line.recover-writer:<writer>`. `review_cycles.fence_kind` answers which proof a fence is, and:

- `_committed_fence` (every checkpoint read goes through it) validates a recovery fence against its own committed act and an assignment fence against the finalization, never one as the other;
- `_current_fence` refuses a recovery fence outright: it ends no assignment;
- `provider_context` finalization, which needs the writer's own assignment fence, refuses a recovery fence explicitly.

**One implementation choice for review.** The checkpoint row's `fence` column and its reader are pinned by the boundary inventory to the two-member envelope `{intent, fenced}`. I kept that envelope and put the kind in the intent, rather than changing the column contract and the inventory's reviewed fingerprints. The two intents are closed documents that each refuse the other's shape. If you would rather have a distinct column or envelope, that is a contained change plus an inventory update.

## 3. What else changed since checkpoint 2

- **The publication now ends by passing the Work to the review route** (`single_worker._passed`, the ordinary producer ending's act). A release left the Work on the route the publisher claimed it from, where the reviewer's claim was refused — the stop observed in checkpoint 2.
- **The reviewer is delivered the publication hand-off** as `recovery-review.json`, through the existing recovery-review channel. The reviewer must claim the hand-off digest in its report; the existing verdict reader holds a report that does not.
- **The line owner is asked before any line is created.** A publication recovery has no line of its own; its review prepares over the original producer's line or is refused, typed.
- **Review-phase owner item** (`publication.review-item`, act `review-item` in the publication pass). When a published recovery's review ends without a verdict — cancelled, expired, or unable to start — the owner who decided is told once, after the reviewer has positively stopped. It names the retained custody and candidate, carries no verdict, starts nothing, and states that a review-only continuation is not a command of this build (contract section 5).
- **Status.** `publication-status` now reports the review as its own statement (stage, reviewer, recorded verdict read through the review owner, whether the verdict's head is the approved original) and the review item.
- **Documentation.** `DEPLOYMENT.md` documents the supported sequence from decision to verdict, including the manager restart after admission (no hot reload), and replaces the checkpoint-1 sentence that an approval admits nothing. `REVIEW-CYCLES.md` documents the two fence kinds.

## 4. Acceptance matrix

Test ids are in `tests/job_manager/test_publication_recovery_execution.py` unless noted. "Connected" is `TheConnectedRecoveryFromARealPooledProducer` (13 cases): installed commands, real stores and owners, a real pooled producer run with real Git, engine and provider doubled at their normal boundaries.

| Plan outcome | Evidence |
| --- | --- |
| 1. Adoption fence, terminal race | `ARecoveryThatDoesNotPublishIsFencedSettledAndReported` (11); `TheBoundCoversMeasurementAndCompletion` (11); reviewer `probe-window` |
| 2. Real pooled original → inspect → decide → admit → publish | `APooledProducersFailedOutputIsReadThroughItsLine` (6); Connected `test_the_commands_carry_a_real_failed_producer_to_the_handoff`; `TheBaseIsReadFromTheRecordedSourceOrNotAtAll` (2) |
| 3. Settlement, unknown observation, owner item, read surface | settlement class above; reviewer `probe-failure` |
| 4. Ordinary reviewer via the typed publication edge | Connected `…carry_a_real_failed_producer_to_the_handoff` (serving `review-a`, Job under the original input identity); `test_the_review_stage_is_served_by_the_works_ordinary_reviewer` |
| 4. Reviewer delivered the candidate, runs its own verification, verdict collected | Connected `test_the_ordinary_reviewer_runs_and_its_verdict_is_collected` |
| 4. Zero implementation calls, zero producer-verifier repeats | same case: one implementation episode ever; publication result `provider 0, verifier 0, commands 0`; reviewer's verification child ran once, exit 0 |
| 4. Independence from producer and publisher | same case: three distinct participants; `scheduler._exclusions` for the recovery's review stage names `impl-a` and `publisher` |
| 4. No review before custody, hand-off and cessation; exactly one review | `TheReviewGateOpensOnTheHandoffAndOnNothingWeaker` (6); `IncompleteCustodyNeverOffersAReview` (3); `OneInstalledPublisherServesRecoveriesOnTwoWorks.test_the_review_stage_starts_nothing_before_the_handoff` |
| 4. Rejection stays the reviewer's outcome | Connected `test_a_rejection_is_the_reviewers_own_outcome` |
| 4. Verdict not bound to this hand-off is not collected | Connected `test_a_verdict_not_bound_to_this_handoff_is_not_collected` (missing and wrong digest; then expiry delivers one item) |
| 4. Cancellation and expiry during review | Connected `test_a_cancellation_during_review_stops_it_and_tells_the_owner`, `test_an_expiry_during_review_stops_it_and_tells_the_owner` |
| 4. Review that cannot start is reported | `OneInstalledPublisherServesRecoveriesOnTwoWorks.test_the_review_stage_starts_nothing_before_the_handoff` (line owner holds no writer; `review-failed` item) |
| R1 owner proof, negatives and replay | Connected `test_the_recovery_freeze_revokes_fences_and_replays`, `test_the_recovery_freeze_holds_on_unproved_or_conflicting_evidence`, `test_a_recovery_freeze_cut_after_the_revocation_finishes_once` |
| Original Job immutable and linked | asserted in the connected hand-off, verdict and restart cases |
| Installed commands and status | Connected: `create`, `publication-inspect`, `publication-decide`, `publication-status` through `tools.job_manager.main` |
| Manager recomposition documented | `DEPLOYMENT.md`, "The supported sequence, from decision to verdict" |

### Contract section 7 restart cuts

| Cut | Evidence |
| --- | --- |
| decision committed / lost reply | admission module: `test_the_same_command_twice_replays_the_decision_and_the_boundary`, `test_the_same_decision_key_with_changed_operands_collides` |
| admission reserved / owner effects incomplete | admission module: `test_a_restarted_manager_reconciles_rather_than_repeating`, `test_a_fault_between_the_decision_and_the_boundary_resumes`; `test_an_exact_repeat_replays_and_admits_nothing_twice` |
| old assignment release or new claim reply lost | `ThePriorAssignmentIsEndedThroughTheAuthority` (15), incl. `test_the_ending_is_journalled_once_and_replays` |
| staging interrupted | `test_interrupted_staging_bytes_are_preserved_on_retry`, `test_staging_replays_and_copies_once` |
| publication launch reply lost | `test_a_lost_start_reply_is_reconciled_and_never_started_twice`, `test_a_runtime_the_host_lost_is_journalled_uncertain_and_holds` |
| worker completed / freeze or intake reply lost | `test_the_adoption_replays_and_publishes_once`, `test_the_custody_record_replays_and_freezes_once`, `test_every_act_replays_across_a_restart_without_a_second_effect` |
| review gate / allocation reply lost | Connected `test_a_restart_between_handoff_and_review_starts_one_reviewer`; `test_the_handoff_replays_and_opens_one_gate`; freeze cut case above |
| review verdict reply lost | Connected `test_a_restart_after_the_review_turn_collects_one_verdict` |
| cancellation / expiry / revocation at any cut | `CancellationStopsNewEffectsAndRetainsEverything` (6); settlement class; the two review-phase cases |

## 5. Verification

Final head `eccef18006a4c77175efa511f1d3c26fd24699e5`. Logs, exit files and source identity are in `logs/`.

| Run | Head | Result |
| --- | --- | --- |
| Four required modules | final | 375 collected, 375 passed, 83.0 s |
| Affected owners, installer, creation, review line, provider context, retained recovery, review driver, dependencies (17 modules) | final | 1540 passed, 188.4 s |
| `job_manager` group (short scratch path) | final minus one documentation file | 2277 collected, 2277 passed, accounting clean |
| Whole `test_stage_execution` | final minus one documentation file | 517 passed, 360.1 s |
| Reviewer probes, unmodified | final minus one documentation file | 9 of 10 pass |
| `tests.manager.test_boundary_inventory` | see below | did not complete on candidate or base; stopped by me after about 30 minutes each |

"Final minus one documentation file": those runs were on `0d3beaab`; the only later change is `REVIEW-CYCLES.md`. The tenth probe asserts the line-layout refusal removed in checkpoint 1.

**Boundary inventory.** `review_cycles.py` is an inventoried file, so I ran this one `scans` module on the candidate and on a base tree side by side. Neither run completed: both were inside `test_no_entry_is_owned_twice` after about 30 minutes (128 of 380 test functions started) when I stopped them, so there are no totals. **The module is already failing at base** — at least 1096 failing sub-cases when stopped. The candidate had at least 1180. Comparing the failing sub-case ids (`logs/inventory-only-candidate.txt`, `logs/inventory-only-base.txt`):

- **41 are attributable to this candidate:** 40 name `review_cycles.py` entries (the new freeze operation's rows and replay, and the recovery fence's members as seen through `checkpoint_of` and `_verdict_row`) and 1 names `workspaces.py:_retained_line_home` (checkpoint 1). The owner registry does not name these new receiving entries.
- 47 name `documents.py` entries the candidate run reached and the base run had not; that is a difference in where each run was stopped, not in the code.
- 6 are base-only, in one probe test.

I did not update the registry: the module is not green at base and cannot be verified in bounded time, so an edit there would be unverifiable. **This is owed work**, and it is the reason I kept the checkpoint row's column contract and `checkpoint_of` byte-identical (section 2): their reviewed fingerprints still hold.

`scans` as a group was not rerun and stays incomplete and unattributed. `tests.manager.test_checkpoint_profiles` was not run, by standing instruction, and `checkpoint_profiles.py` gained one read-only method: that method is exercised only through the connected cases.

## 6. A failure the earlier checkpoints did not disclose

`tests.manager.test_dependencies.NoPublicOperationTakesInternalState` fails on checkpoints 1 and 2: `workspaces.retained_output_of` gained the public parameter `output` in checkpoint 1 and the declared-operand catalog did not name it. That module was outside the affected set I ran then, so both checkpoint reports claimed a clean affected run without it. It is corrected here by declaring `output` in the catalog with its reason (the caller-selected declared output path); the module is now in the affected set and passes.

## 7. Tests changed since checkpoint 2

- **Added:** 10 connected cases (review verdict, rejection, unbound verdict, cancel, expiry, two restart cuts, three R1 freeze cases) and the reviewer-turn fixture they share.
- **Modified, each because it asserted superseded behaviour:**
  - `test_the_commands_carry_a_real_failed_producer_to_the_handoff` ended by asserting that no reviewer container starts — the checkpoint-2 stop. It now asserts the reviewer is running under `baton.reviewer` with one more container.
  - `test_the_review_stage_starts_nothing_before_the_handoff` gains the fixture-written case's honest ending: the review start is refused by the line owner and one `review-failed` item is delivered.
  - `test_dependencies` operand catalog: `output` declared (section 6).
- The connected fixture's `restarted(same_engine=True)` keeps the engine double across a manager restart. A real daemon outlives the manager; a fresh double made a running reviewer look lost.
- No case was removed.

## 8. Prepared qualification (not run; each needs separate selection)

**Images whose worker bytes differ from the base** — every one carries `baton_worker.py`, which gained the completion gate in the last reviewed candidate:

| Image | Recipe | Changed bytes |
| --- | --- | --- |
| reference | `v12/worker/Dockerfile` | `baton_worker.py` |
| provider | `v12/worker/Dockerfile.claude` | `baton_worker.py` |
| integration | `v12/worker/Dockerfile.integration` | `baton_worker.py` |
| reconciliation | `v12/worker/Dockerfile.reconciliation` | `baton_worker.py` |
| publication (new) | `v12/worker/Dockerfile.publication` | `baton_worker.py`, `publication_entry.py` |

`claude_agent.py` is unchanged, so the reviewer's prompt and report contract are the accepted ones.

Commands, from `v12/python` of the imported tree with the prepared interpreter (`P=$(python3 -m tools.environment interpreter)`):

1. **Build the publisher candidate.** `PYTHONPATH=src $P -m tools.worker_image --tag baton-v12-publication:candidate --dockerfile ../worker/Dockerfile.publication --context ../worker` → record the printed digest as `$PUB`.
2. **Entrypoint and UID.** `docker image inspect $PUB --format '{{json .Config.Entrypoint}} {{.Config.User}} {{json .Config.Env}}'` → expect `["python3","/opt/baton/publication_entry.py"]`, `65532:65532`, no `ANTHROPIC_*` and no credential path.
3. **No provider runtime.** `docker run --rm --network none --entrypoint python3 $PUB -c "import os; print(sorted(os.listdir('/opt/baton')))"` → exactly `baton_worker.py`, `publication_entry.py`, `worker-control-1.0.schema.json`.
4. **Read-only input, separate writable output.** Compose with `pool compose-worker --role publication …` (DEPLOYMENT.md), run one recovery on a fake-provider instance, then `docker inspect <container> --format '{{json .Mounts}}'` → `/input/source` `RW:false`, the workspace mount `RW:true`, no other writable bind; and inside the container `touch /input/source/x` must fail with a read-only error.
5. **Whole-process deadline and cessation.** Start a recovery with the staged original replaced by a large tree so the copy outlasts a shortened bound; expect the container to exit with status 75, no completion envelope, `publication.ended` = `expired`, the settlement to remove the container (`docker ps -a --filter label=baton.v12.runtime_attempt_id=<attempt>` empty) and one owner item.
6. **Resource reconciliation.** After 4 and 5: `manager publication-status --decision-id …` shows `settled` or `published`; the workspace token is returned (no held token for the attempt in `manager status`).
7. **Installed command and reviewer delivery.** From a built bundle (`just build`): `manager publication-inspect` → `publication-decide --approve` → restart → publication → review with the scripted provider. Expect `/input/recovery-review.json` present and regular in the reviewer container, `/input/source` read-only at the approved head, and `publication-status` reporting the verdict.
8. **Rebuild the four existing images** with the same tool and their own recipes, and rerun their accepted engine gates (`just test-group manager-engine`) before selecting any digest.

No live provider is needed for any of these.

## 9. Not done, not proved, and items for the reviewer

- **Job versus publication-stage input identity** (checkpoint 2) is unchanged here and remains explicitly for independent review; M385915 did not accept it.
- **`settle-stopped` producers cannot be reviewed.** R1 requires the runtime positively absent. A producer that was only stopped keeps its container, so the freeze holds and the owner gets a `review-failed` item after publication. The connected cases use the abandonment ending. Inspection and decision do not warn about this in advance; that would be a small addition to the inspection's holds.
- **A held verdict stays open until expiry.** A report that does not claim the hand-off digest leaves the review stage open until the recovery's deadline; then one item is delivered. This is the existing recovery-review hold, unchanged.
- **Reviewer runtime after cancel or expiry is stopped, not removed.** It waits for the ordinary operator settlement, and the item says so. No automatic removal was added.
- **The 900-second per-command reviewer bound is not separately enforced.** The reviewer's verification runs inside the provider turn; what bounds it is the adapter's 3600-second turn and the 4800-second stage wall (observed: stage deadline 01:20:00 after a 00:00:00 admission). The contract's 900-second figure would need adapter support.
- **The reviewer's provider is scripted.** Its verification child is a real process over the delivered candidate; the model is a double at the provider boundary.
- **A running manager still serves only the bindings it started with.** Documented; the connected cases restart after admission.
- **Reviewer prompt wording.** The accepted adapter introduces the hand-off as "attributable verifier evidence". For a publication hand-off the document itself labels the producer's verification as producer evidence, not acceptance. I left the adapter untouched to avoid changing provider-image bytes for wording.
- No image build, container run or kernel confinement evidence. `scans` incomplete and unattributed.
