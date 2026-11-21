# W385331 / E385510 — connected clarification proof ready for independent review

M385508 and the owner standing disposable-repository rule resolve the prior execution blocker. This report supersedes the **partial/not-ready** disposition of M385505 and clarification-proof-385503/REPORT.md; those historical inputs and results remain unchanged. No further product change was needed. Independent review remains required; this does not close the larger discovery/dependency Work or accept a live deployment.

## Candidate and overlap

Pinned base `939c7adfe591cc413f29ab44d41392b583aaa5e5`. Candidate tree `ea6ffd7e395894adf1a0b7220b7439aa265572cae299098457a7591f42b21b8c` (same bytes as M385505). Exact manifest: `manifest.json` here, SHA256 `3578e83136c44b200a7c7b07c006e0daf4580ed30eb7bdce1299153896f166b4`. Two additive test-only paths:

- `v12/python/tests/authority/test_work_messages.py`: two close/reopen tests with fresh sessions; request/reply exact retries and changed-operand refusal, plus durable escalation replay.
- `v12/python/tests/tools/test_native_handoffs.py`: one connected escalation-serving-restart test asserting retained messages/owner hold, no successor attempt, no continuation or integration, and no handler.

No changed existing expectations, product code or registry entries. Existing module registration covers new methods. Candidate/base bytes and candidate.patch remain at `../clarification-proof-385503/`; current manifest binds exact locations and hashes. No host import. Protected HEAD advanced to `3c449083124a45af32073aeab4d6e3532f0ceb24`, but `git diff 939c7adf HEAD -- v12` is empty. All 1112 tracked v12 paths were checked: only the two intended candidate paths differ; none missing. Base is preserved rather than rebased solely for record changes.

## Connected evidence and coverage

All 14 existing connected tests pass on unchanged baseline. All 15 connected candidate cases pass, preserving the baseline assertions. Real serving factory, Authority/Job/Control/Integration stores, bootstrap-installed routing/grants, worker `serve_exchange`, adapter, Git checkpoint retention and final verification/review handling are exercised. The provider is scripted at its normal process boundary; engine calls are daemonless fixtures. Neither live judgment nor a live engine is claimed.

- `AClarificationResumesTheSameTaskWithNoHumanAct`: exact attributed request/checkpoint retention before any publication; actual authorized reviewer reply; unchanged task digest and checkpoint-based writer; exact retained read-only continuation bytes and text at resumed provider boundary; final submission then ordinary independent technical review; one continuation, zero correction rounds and no courier.
- `test_zero_human_acts_to_the_ordinary_final_review` reaches completed implementation and review, with the resumed writer's accepted checkpoint eligible for integration. The fixture's mandatory `python3 harness.py` verification runs as a real subprocess through the provider seam. This is not a claim of running the separate four-module worker-image qualification or of host integration.
- `AGenuineAmbiguityEscalatesOnceAndStaysHeld` and NEW `AnEscalationSurvivesServingRestart`: exactly one attributed escalation to owner, unchanged durable hold after fresh serving object and repeated ticks, no implementation/review attempt preparation, no continuation, blocked integration, no fabricated owner approval.
- Existing continuation replay, fault after continuation commit/before ending settlement, and fresh serving after yield/answer tests pass: exact durable message/episode identities, no duplicate effect/allowance, only one active writer. NEW Authority tests close/reopen the database connection with fresh sessions and replay request/answer/escalation exactly.
- Existing negatives still pass: missing routing refuses before runtime, malformed request cannot publish success, unsolicited ordinary-review response earns no reply, zero-edit yield and in-scope finding preserve the same mechanism. Host-side selection additionally proves cross-Work/checkpoint/attempt/grant refusal, cancellation, finite allowance and unchanged deadlines.

Current coverage map is this section plus the per-ID ledgers. The earlier coverage map's unrun connected rows are now resolved by these exact baseline/candidate logs.

## Verification/accounting

Affected groups: authority, job_manager, tools-pure. Focused `just test-one` commands, prepared interpreter `/home/sl/.local/state/baton-v12-venv/bin/python`, timeout180s each, explicit disk roots and TMPDIR. No broad group/full-suite execution.

| Run | Collected / executed / passed | Failures / errors / skips / unaccounted | unittest time | Wall |
| --- | --- | --- | --- | --- |
| Unchanged connected baseline | 14 / 14 / 14 | 0 / 0 / 0 / 0 | 14.587s | 15.177430s |
| Candidate connected + Authority + host handoffs | 165 / 165 / 165 | 0 / 0 / 0 / 0 | 20.412s | 20.730710s |

Current-turn test wall **35.908139s**; cumulative with retained prior three runs **49.460230s**. Prior history: initial missing vectors fixture caused68 errors in148 attempts, then complete-input baseline148 and candidate150 passed on ambient Python; retained as historical, superseded for final candidate verification by this prepared-interpreter165-case result. No hidden retries. A bookkeeping parser initially duplicated method names; corrected against existing log IDs without rerunning tests.

Exact commands/environments/durations: connected-baseline-run.json, candidate-focused-run.json. Full logs, collected IDs and per-ID `.summary.json` ledgers retained. The ledgers compare independent prepared-interpreter unittest collection to every verbose result; this is focused test-one accounting, not a claim of invoking parallel_test --account. Source identity documents hash the entire isolated input trees and consumed vectors input; candidate manifest binds the delta and base. Both selections have zero duplicate/uncollected IDs.

## Isolation and limits

Preflight verified no candidate symlink or shared Git metadata. Test fixtures allocate their own disk-root source/line/output repositories; clone uses --no-hardlinks --no-local. Git ceiling prevents accidental ancestor discovery from the isolated copy. Trace files record1262 Git starts from profile-side operations; all observed -C and clone target operands are inside the disposable disk root. Fixture/provider environment intentionally clears ambient variables, so these traces are not a complete syscall audit. Their Git targeting was also inspected in source. No fixture roots remain in the designated disk directory after cleanup.

Postflight verifies protected HEAD/index unchanged, host v12 clean, candidate hashes unchanged. No live instance, engine/model, protected Git mutation or host import. Serving restart means reconstructed serving object over retained stores; separate Authority tests close/reopen its connection. This does not claim full OS crash/reboot, network/provider reliability or every possible crash cut. No broader discovery/dependency outcome is accepted by these tests.

## Handoff

Ready for independent exact-byte review. Review the three additive test methods, preserved behavior, and logs against manifest; no unresolved implementation blocker or owner decision remains in this bounded outcome. Mainline import is not performed. After independent acceptance and selected import, human milestone checkpoint is pending; suggested commit message: `test(v12): prove durable clarification and escalation restart`. Larger W385331 discovery/dependency milestone stays open. Pass through baton.decide for independent review routing and verify claim release.
