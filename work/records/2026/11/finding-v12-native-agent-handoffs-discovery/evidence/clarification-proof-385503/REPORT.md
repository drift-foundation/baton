# M385501 / E385503 — partial clarification proof, execution boundary

**Not ready for acceptance.** Base `939c7adfe591cc413f29ab44d41392b583aaa5e5`. Candidate tree `ea6ffd7e395894adf1a0b7220b7439aa265572cae299098457a7591f42b21b8c`. Two test-only paths, additive assertions; no production changes, registry changes, live/provider/engine/installed-instance changes, host import or Git mutation. Canonical candidate/base snapshots and diff are beside this report; manifest.json binds both paths and the required fixture. Scratch copy is disposable and is not the only retained candidate.

## Coverage map

| Required behavior | Existing proof / disposition at this checkpoint |
| --- | --- |
| Durable attributed request and authorized exact reply; replay/conflicting operands | tests.authority.test_work_messages; rerun permitted, passes |
| Yield before publication; no false task success or acceptance receipt; exact checkpoint/task/continuation; authorized delivery; cancellation, deadline and finite allowance | tests.job_manager.test_native_handoffs; rerun permitted with fake checkpoint profile, passes |
| Scripted provider through actual serve_exchange, storage/routing/grants, retained checkpoint -> answer -> same-task resumed writer | tests.tools.test_native_handoffs.AClarificationResumesTheSameTaskWithNoHumanAct, including exact continuation bytes/prompt; existing, not rerun due Git boundary |
| Mandatory task verification then independent ordinary technical review | same class.test_zero_human_acts_to_the_ordinary_final_review; its parent provider runs actual task argv (python3 harness.py), but not rerun; not a live-model or four-module image qualification claim |
| Genuine ambiguity reaches owner and stays held without fabricated continuation | AGenuineAmbiguityEscalatesOnceAndStaysHeld; existing connected case unrun; lower Authority/host-state proofs pass |
| Retry at continuation/settlement cut; restart after yield/answer; no duplicate messages, allowance or writers | existing tools cases (fault between continuation and settlement, exact continuation retry, ARestartBetweenTheCutsDuplicatesNothing); unrun |
| Actual Authority connection close/reopen, fresh participant sessions, exact request/reply replay and conflicting changed request refusal | NEW DurableRestartPreservesCorrespondence, 2 passing tests; one answer and one escalation path |
| Escalation hold survives serving-object restart and repeated scheduler ticks with no new attempts/continuation/integration | NEW AnEscalationSurvivesServingRestart; syntax checked, **not run** |

The existing 14 connected tests already implement most requested proof. Their scripted provider replaces only the provider at its normal process boundary; daemonless engine, real local stores/worker protocol/checkpoint Git remain. A fixture inserts the admitted template row; bootstrap composes real routing/grants. `reconnected` recreates serving operations, not OS processes or all store connections. The two new Authority tests explicitly close/reopen that store; neither is represented as a whole-system restart. No new launcher or fake Git substitute.

## Execution and accounting

- Initial isolated baseline: 148 tests, 80 passes and 68 errors, 0 skips; unittest 3.501s, wall 3.966572s. Every error was the omitted dossier vectors.json input (baseline-tests.log); not a product failure. Exact referenced fixture copied into the isolated tree, hash in manifest.
- Complete-input unchanged baseline: 148 pass, 0 failures/errors/skips; unittest 4.579s, wall 4.767378s (baseline-complete-inputs.log/json).
- Candidate permitted selection: 150 pass, 0 failures/errors/skips; unittest 4.596s, wall 4.818140s (candidate-tests.log/json). Includes both new Authority restart cases.
- Total measured test wall: 13.552090s, including initial incomplete-input run. Two changed files parse successfully. No connected case attempted or marked skipped: 14 existing + 1 new remain explicitly unexecuted.

Exact permitted argv: `python3 -m unittest -v tests.authority.test_work_messages tests.job_manager.test_native_handoffs`, cwd isolated `candidate/v12/python`; PYTHONPATH=src:., TMPDIR=work/scratch/w385331-385503/tmp and both BATON_V12_STACK_TEST_ROOT/BATON_V12_DISK_ROOT=work/scratch/w385331-385503/disk (absolute /home/sl/src/baton prefixes). Timeout120s per run. JSON records retain argv/time; baseline JSON retains environment.

## Exact blocked operation and proposed boundary

M385501 preserves the no-mutating-Git policy and does not extend the exact-two-viewer-test exception. Connected fixtures fail that authority check before execution, regardless of being deterministic. No new product decision is needed. Owner ruling needed only for the following disposable fixture operations if these connected cases are to run:

- `ComposedOneJobCase.setUp`, tests/tools/test_stage_execution.py:4333–4338: `git -C SOURCE init -q -b main`, `add --all`, `commit -q --message base`; SOURCE is the test-owned `<disk-root>/v12-w71917-*/source` (disk_roots fixture), never the host repo.
- GitCheckpointProfile.materialize: `git clone --no-hardlinks --no-local SOURCE LINE`, then detached declared-base checkout in LINE; conditional fetch of SOURCE refs or configured supplement into LINE if the declared object is missing. Source vectors in source_profiles/checkout.py:143/160; profile checkpoint_profiles.py:319–427.
- GitCheckpointProfile.freeze: `git -C LINE update-ref refs/baton/checkpoints/... HEAD`; restore: `git -C LINE reset --hard <exact retained head> --`, `clean -f -d -x --`. LINE is test-owned storage `.baton-review-lines/<line>/...` under the fixture disk root, selected by real review_cycles, not host source. checkpoint_profiles.py:80–119,428–495.
- Worker `claude_agent._commit`: real `git -C LINE add --all -- .`, commit with fixture adapter identity and hooks disabled; `_proposal`: `git -C LINE bundle create --quiet <fixture proposal>/objects.bundle <base>..HEAD`. claude_agent.py:2992–3000,3452–3454. Actual basename uses adapter BUNDLE constant. Normal read-only object/status/diff commands also run.

Requested finite boundary: only existing `tests.tools.test_native_handoffs` (14 baseline cases, then 15 candidate cases, plus focused correction reruns if needed), real Git effects confined to newly allocated fixture roots under the named disk/tmp roots; no host repo/index/history mutation, no installed instance, network, engine or live model. Before any authorized run, verify actual resolved fixture paths and no symlink/alternate escape; retain argv/target evidence. This packet is a request for that exception, not a claim it already exists. Future fixture Git may remove disposable test files through reset/clean and fixture cleanup; retained evidence here is outside those roots.

## Continuation / handoff condition

After an explicit fixture execution ruling, reconstruct isolated candidate from base plus manifest-bound snapshots, include exact vectors fixture, and run the unchanged 14-case connected baseline before the candidate 15-case module. Confirm the new restart assertions against real serving behavior and preserve any failures; do not weaken real pipeline assertions. Return completed connected evidence and refreshed digest for independent review. Until then this candidate is PARTIAL and the requested whole-pipeline proof is unestablished. Larger discovery/dependency delivery remains out of this bounded scope. Passing to baton.decide for this exact execution boundary, releasing claim; not declaring W385331 complete.
