# W385695 — correction packet for C1–C5 (review 2026-11-24T00-28-00Z, M385922)

**For independent review. Not accepted, not imported, not qualified.** All five corrections are in this one packet. Section 8 lists what is still not proved.
Author: baton.prompt (K), owner-selected interactive continuation, no claim.
No host import, protected Git mutation, image build, engine or container operation, live call or credential read. No protected-tree file was edited in this round.

## 1. Identity

| | |
| --- | --- |
| Base | `6079ad78345aa87b7148db302d48fb9b1867f940` |
| This candidate | `candidate-manifest.json`; sha256 in `packet.sha256` and in the Baton message |
| Scratch repository | `work/scratch/w385695-K-385897/repo`, head `58d452ff0d174dc63a076e711c7633a8116d61c2` (disposable) |
| Paths | 46 over base; 14 changed since the reviewed candidate `6816e935`; 23 since `69b9328c` |
| Reviewed candidate (preserved) | manifest `6816e935…`, `evidence/final-K-385915/` |
| Earlier packets (preserved) | `checkpoint-K-385913-2/`, `checkpoint-K-385911-1/`, `continuation-K-385904/` |

`candidate.patch` is over the base. **`delta-from-reviewed.patch` is over `6816e935`** and is the one delta this round needs read. `delta.patch` is over `69b9328c`.
Application proof: `candidate.patch` applied with `git apply` to a fresh archive of the base in an isolated directory; all 46 paths compared by sha256 with `candidate-files/`; no other path differs.

Four paths are new to the set: `v12/worker/claude_agent.py`, `job_manager/review_driver.py`, `tools/stopped_settlement.py`, `tests/manager/test_boundary_inventory.py`.
**`claude_agent.py` changed, so the provider and integration images now carry changed worker bytes beyond `baton_worker.py`** (section 6).

## 2. C1 — the recovery fence is bound to the row that consumes it

`checkpoint_of` now dispatches on the fence's kind and authenticates a recovery fence with `_bound_recovery_fence`:

- the fence is the closed recovery document, every member under its own rule;
- it must be exactly the committed result of the recovery act **of the row's own writer** — the act's identity is derived from the row, never from what the fence says about itself, so a valid proof transplanted from another writer names an act that is not this row's;
- the proof's checkpoint, writer and line must be the row's; the writer's own row must be the recovered attempt's at that generation, granted on the same checkpoint and revoked as `recovered`; once frozen, the sealed base and head must be the approved candidate's.

The converse also holds: a writer revoked as recovered is refused under an assignment fence. `_committed_fence` is assignment-only again, so a review fence can never reach the recovery reader, and `_current_fence` refuses a recovery fence through the closed finalization document. `provider_context` now refuses on the writer's `recovered` revocation, which the two-way binding makes equivalent to the fence kind.

The reviewer's `probe-fence-binding.py` passes unmodified. New case `test_a_recovery_fence_is_bound_to_the_row_that_carries_it` covers: altered row identity; another line; another writer; a frozen candidate the proof did not approve; a writer row that no longer agrees; an uncommitted well-formed proof; an unknown kind; a malformed proof; and, after each, that the untouched row still reads and the exact replay returns the same committed checkpoint. The existing crash-cut and replay cases pass unchanged.

One simplification made on the way: the recovery fence's `fenced` record no longer carries a `gate` member (it was always null).

## 3. C2 — the 900-second reviewer command bound is enforced by the reviewer's worker

**Where it is enforced.** `claude_agent.ClaudeAgent._reviewer_check`, called by the real `_review` turn. The provider cannot be the enforcer of its own tools, so the adapter runs the read-only task's verification command itself:

- the bound is fixed before the child exists and is the smallest of: the owner-selected per-command bound delivered in the recovery input (900), this worker's delivered verification bound, and the invocation bound it runs inside;
- it runs in a private copy of the reviewed tree, as the leader of its own session;
- at the bound, and also after an ordinary exit, the whole process group is killed, the leader reaped, and the group observed empty; `group_gone` reports that observation;
- the provider is then handed only what is left of the 3600-second invocation (`_provider(spent=…)`), and none if nothing is left;
- the prompt tells the reviewer the outcome and states that producer verification is producer evidence, not independent acceptance (the wording point from the review).

**No accepted success from a check that did not pass.** If the report says `accepted` and the check's outcome is not `passed`, the adapter publishes no verdict: the turn answers `unable` and the review log records why. Any other verdict is the reviewer's own and is published with the check record beside it.

**The manager does not take the worker's word for it by omission.** `review_verdict_from_result` now holds an acceptance of a publication recovery unless the frozen findings carry the worker's own claim `baton.reviewer-verification/1`: the approved command (the argv the owner's decision bound), outcome `passed`, exit 0, group gone, and a bound no larger than 900. A worker image that does not supervise the command publishes no such claim and its acceptance is held.

**How the requirement travels.** `recovery-review.json` gains `reviewer_verification: {required: true, command_seconds: 900}` for publication recoveries only. Retained-verification recoveries are unchanged: there the task's verifier is the thing that was wrong.

Evidence, all with real child processes unless labelled:

| Required by the review | Case |
| --- | --- |
| command termination and child cleanup | `TheReviewersRequiredVerificationIsSupervisedAndBounded.test_the_bound_ends_the_command_and_every_descendant` (a descendant that would outlive the command is ended); `…test_a_descendant_left_by_a_passing_command_is_ended_too` |
| timeout attribution | same case: outcome `timed-out`, no status, `seconds_bound` 1 |
| successful shorter commands | `…test_a_shorter_command_passes_under_the_selected_bound`; connected verdict case (real adapter, bound 900, passed, group gone) |
| remaining-invocation truncation | `…test_the_remaining_invocation_truncates_the_command_bound`, `…test_no_remaining_invocation_runs_nothing`, `…test_the_provider_is_handed_what_the_check_left_of_the_invocation` |
| no accepted success from a timed-out required check | connected `test_an_acceptance_over_a_timed_out_required_check_is_not_collected` (the adapter's observation is forced there and labelled; the real timeout is the unit case above) |
| manager holds an unsupervised acceptance | connected `test_an_acceptance_without_the_workers_own_passed_check_is_held` (no claim; bound over 900; another command; processes left behind) |
| closed requirement | `…test_the_requirement_is_closed_and_never_exceeds_the_selected_bound` |
| unchanged clocks on restart | the bound is a member of the delivered launch input and is not recomputed; connected `test_a_restart_after_the_review_turn_collects_one_verdict` keeps the same reviewer container across two manager restarts and collects one verdict with one check |

**Limit, stated plainly.** This bounds the one command the contract requires the reviewer to run, by the adapter. Commands the provider chooses to run through its own tools during its turn are still bounded only by the remaining invocation time; the adapter does not see them individually. If the contract's "each reviewer verification/test command" is meant to cover those too, that needs the provider runtime's own per-tool limit and is a provider-configuration question I have not answered here.

## 4. C3 — candidate-added boundary entries are owned, validated and probed

I built a bounded harness over the inventory's own functions (seconds, not a scan run) and worked the finite set to zero. Logs: `logs/registry-owners.log`, `logs/registry-probe-accounting.log`, `logs/registry-probes-arrive.log`.

- **The projection now completes.** Every boundary label in the changed helpers is a literal. That includes the older `freeze_recovered_checkpoint` label the review found failing in the prior candidate.
- **New receiving entries versus `69b9328c`: 30** (the review counted 52; restructuring removed the rest rather than registering them — the freeze reads no member of its replayed fence, review fences no longer reach the recovery reader, and the public `fence_kind` is now private). **Each of the 30 has exactly one owner.** 24 are owned by a boundary rule at their own site; 5 are stated with a reason (three existence-only reads, the pass-through replay and the profile aggregate); 1 is the injected store, owned at its constructor.
- **Every newly consumed member is validated under its own label**, not covered by a fingerprint: the recovery fence's intent, record, kinds, operation, four identities, generation, based checkpoint, exclusion digest, revocation instant, candidate, base and head.
- **27 probes added (`w385695_probes`), each spoiling exactly one member, and all 27 arrive at their named boundary.**
- `checkpoint_of`'s reviewed fingerprint is updated, with the reason, because C1 changed that reader; the row call, the `_fence` repeat and the nullable guard it witnesses are unchanged and still pinned. One shadow entry that C1 made stale is retired, and its witness updated.

Targeted inventory tests on the final head: `DuplicateColumnChecksRequireOwnedWitnesses` and the shadow, exemption and staleness checks — result in section 7.

**Retained, not mine, not waived:** four registry relations still name `review_cycles.py:freeze_checkpoint` for code the base renamed `_freeze_checkpoint` (two unprobed pairs, one probed-never-owned, one stale stated owner). They are identical at base and are the only remaining accounting differences in the three changed owners. The whole module and the `scans` group were not rerun.

## 5. C4 — the stopped-original path is honest and executable

**My report was wrong and is corrected.** A `settle-stopped` original is not admitted and then refused: inspection holds it before approval, as the reviewer's probe showed. DEPLOYMENT.md now says so.

- **New installed command:** `manager settlement-remove --instance <instance.json> --job … --stage … --episode … --reason …`. It runs the serving composition's own abandonment ending for that exact attempt, with the manager stopped. It refuses any attempt whose runtime is not recorded `quiescent`, and exits non-zero unless the runtime is then destroyed with settled cleanup. It adds no trust rule.
- **Honest preflight:** when an original is held only because its stopped runtime is present, `publication-inspect` adds a `continuation` member spelling that command. No hold or eligibility changes.
- **Connected coverage, end to end:** `test_a_stopped_original_is_held_then_removed_recovered_and_reviewed` — real producer overflow → installed `settlement-preview` and `settle-stopped` → inspection held with the continuation → no admission → `settlement-remove` → inspection eligible → decide → publication → ordinary reviewer → collected verdict. `test_a_running_or_unstarted_attempt_is_not_removed` covers the refusal.
- **The reviewer item is actionable:** `publication.review-item.remaining` now spells the same command for the stopped review attempt, and both review-phase cases run it and observe the reviewer's runtime destroyed with the item unchanged.

The reviewer's `probe-stopped-preflight.py` and `probe-stopped-continuation.py` pass unmodified.
I found no other original shape that can be admitted and must then fail R1: admission requires an eligible inspection, and eligibility already requires the positive absence R1 needs.

## 6. C5 — executable qualification preparation

`qualify-w385695.sh` in this packet. **Prepared and syntax-checked (`bash -n`); not executed** — running it builds images and starts containers, which is separately selected. Its header states parameters and preconditions. Phases:

| Phase | What it does | Assertions |
| --- | --- | --- |
| `images` | builds all five changed images with `tools.worker_image` | each image's `/opt/baton` worker files equal the reviewed source by sha256; publisher entrypoint, UID/GID 65532, exactly three files, no provider or credential variable |
| `publisher` | inspect → decide → serve, on a prepared instance | container observed while it exists: user, network `none`, `/input/source` read-only, no writable input mount; status published and handed off; container gone; original byte-identical after approval |
| `reviewer` | continues the same recovery | delivered `recovery-review.json` is a regular file carrying the 900-second requirement; a write into `/input/source` is refused; verdict recorded for the approved original |
| `deadline` | a second prepared recovery | **the approved bytes and the 900-second profile are unchanged**: the engine freezes the publisher (`pause`) when it appears and releases it only after the manager's own clock reports the bound reached; then expired, settled, removed, one owner item, review blocked, original byte-identical |
| `cleanup` | removes only the tags it built | reports, never deletes, leftover containers |

Short-lived containers are observed by a watcher that inspects each container as it appears, plus an engine event log. Every phase writes its observations and an `evidence.sha256` into a new directory outside the tree.

Changed images and their consumers:

| Image | Recipe | Changed worker bytes | Qualification consumer |
| --- | --- | --- | --- |
| reference | `Dockerfile` | `baton_worker.py` | accepted engine gates (`manager-engine`), reference digest |
| provider | `Dockerfile.claude` | `baton_worker.py`, **`claude_agent.py`** | accepted engine gates; `reviewer` phase |
| integration | `Dockerfile.integration` | `baton_worker.py`, **`claude_agent.py`** | accepted integration engine gates |
| reconciliation | `Dockerfile.reconciliation` | `baton_worker.py` | accepted reconciliation engine gates |
| publication (new) | `Dockerfile.publication` | `baton_worker.py`, `publication_entry.py` | `publisher` and `deadline` phases |

What I could not verify without an engine, and say so in the script: how the manager's stop behaves on a paused container (the script accepts the publisher's own exit 75 or the manager's stop, and records which); and that the watcher always catches a reviewer container in time to read its input. Treat the first run as a qualification of the script too.

## 7. Verification

Final head `58d452ff0d174dc63a076e711c7633a8116d61c2`. Logs, exit files and source identity are in `logs/`.

| Run | Result |
| --- | --- |
| Four required modules | 389 collected, 389 passed, 104.2 s |
| Affected set, 18 modules (now includes `test_claude_agent`) | 1825 passed, 202.2 s |
| `job_manager` group | 2291 collected, 2291 passed, accounting clean |
| Whole `test_stage_execution` | 517 passed, 358.5 s |
| Targeted inventory tests | 14 run, 13 passed; the one failure is the inherited stale stated owner for `freeze_checkpoint` named in section 4 |
| Registry harness | 30 new entries, 0 without exactly one owner; 27 probes, 27 arrive |
| Reviewer probes from `review-385919`, unmodified | fence-binding, stopped-preflight, stopped-continuation, adoption-clock: all pass |

Not run: the whole boundary inventory, the `scans` group, `tests.manager.test_checkpoint_profiles` (standing instruction), any engine, image or live check.

### Tests changed since `6816e935`

- **Added:** 5 connected cases (fence binding; two reviewer-verification acceptance cases; stopped original end to end; removal refusal); class `TheReviewersRequiredVerificationIsSupervisedAndBounded` (9 cases); 27 inventory probes.
- **Modified, each for a stated reason:**
  - the connected reviewer fixture no longer runs the verification in the scripted provider — the real adapter runs it, and the cases read the adapter's own record from the frozen result;
  - the delivered-document assertion includes the new requirement member;
  - `fence_kind` references follow the rename to private; the `_current_fence` assertion checks the typed refusal rather than a sentence; the fence's absent `gate` member;
  - the two review-phase cases now also run `settlement-remove` and assert the item names it;
  - inventory: `checkpoint_of` fingerprint, one retired shadow entry and its witness's expected labels, four stated owners.
- No case was removed.

## 8. Corrected acceptance matrix, and what is not proved

The matrix in `final-K-385915/REPORT.md` section 4 stands, with these changes:

| Row | Now |
| --- | --- |
| Reviewer runs its own verification | by the real adapter, supervised and bounded; `test_the_ordinary_reviewer_runs_and_its_verdict_is_collected` reads the adapter's record |
| 900-second reviewer command bound | **enforced** for the required verification command (section 3); provider-chosen tool commands: not individually bounded (stated limit) |
| R1 reader integrity | row-bound (section 2) |
| Stopped original | held before approval; supported removal; connected through to verdict (section 5) |
| Boundary registry | candidate-added set owned and probed (section 4) |
| Qualification preparation | executable script (section 6), not executed |

Source blockers remaining, as I see them: none of C1–C5. Open points for the reviewer:

- whether the C2 limit above (provider-chosen commands) is acceptable under the contract's wording;
- the four `freeze_checkpoint` registry relations inherited from the base;
- a held verdict still stays open until the recovery's deadline (unchanged);
- a running manager serves only the bindings it started with (documented, unchanged).

Later, separately selected checks — none attempted: image builds and digests; container user, mounts, network and confinement; real deadline cessation; installed-bundle command and reviewer delivery; rebuilt-image engine gates. Source fake-engine results are not evidence for any of them.
