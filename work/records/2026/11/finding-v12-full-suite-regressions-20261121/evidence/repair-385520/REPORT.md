# W385517 / E385520 — focused repairs ready for independent review

All ten owner-reported failures are resolved by the focused candidate evidence. **Not full-suite acceptance:** independent review, reviewed-byte integration, human checkpoint and the owner's selected complete rerun remain required. W385517 stays open through that gate; W9901 is not unblocked here.

## Candidate identity and files

Base `c06befa89f557f2999a57ef0758bf6f6d7007bb9`. Tree `c5ec0445e7215ce84188f3eb6884300fc67fcbd75dabbb922451f083123d9d15`. Manifest SHA256 `ecf0cfbd205aed3e4ba1ed262f59aa90b0781b47c13b5b860e67a25f51a8bd5d`. `manifest.json` binds five base/candidate files plus `candidate.patch`; complete snapshots live under `base/` and `candidate/` here. Disposable implementation copy: work/scratch/w385517/candidate. No host source import, protected Git mutation or installed-instance change.

1. `v12/python/tests/tools/test_stack.py`: publish at actual write time instead of synthetic `now+1`; freshness query happens after write. New explicit future-mtime negative preserves stale/unknown refusal. No production freshness threshold changed.
2. `v12/python/tests/tools/test_dogfood_retry_engine.py`: Authority/setup store and grant timestamp use the same deployment clock as public `_launched` capability construction. No claim check, expiration or deadline is weakened.
3. `v12/python/tools/authoring_enforcement.py`: after child final accounting/guard stop/publication, SIGTERM/SIGINT become OS-level SIG_IGN dispositions. Work-phase cooperative stopping remains; outer shutdown request, deadline, SIGKILL, reap and success classification remain unchanged.
4. `v12/python/tests/tools/test_next_run_flow.py`: exiting-child assertion now requires SIG_IGN instead of a callable child_main handler; completed outcome/status0 and deadline kill/held assertions remain.
5. `v12/python/tests/tools/next_run_flow_fixture.py`: bounded atexit delay simulates loss of callable Python signal handlers before the real controller's late stop, while preserving SIG_IGN. This makes the finalization window deterministic rather than depending on suite load.

One new method, zero removed tests, no new modules/registry changes. The existing signal-disposition expectation changes because the earlier callable-handler lifetime assumption is precisely what failed; success, recovery, failure accounting and finite-bound assertions are preserved.

## Diagnosis from retained run and baseline

**Freshness (6 cases):** fixture publish_snapshot always advanced mtime at least one second into the observer's future. Retained log reports observed age0/written age-1. Shared freshness correctly refuses negative age. All six reproduced on isolated baseline. Actual write time fixes fixture ordering, and the new negative proves future timestamps still cannot claim idle/runtime absence.

**Docker public retry (3 cases):** fixture grants supplied historical W.NOW while ordinary capabilities reopened ControlStore with deployment `_now`. Acceptance derives settle_by from supplied now; submit_claim reads store time, finds settlement expired, and cannot commit a claim. activate_assignment correctly refuses this attempt's missing committed claim. The isolated baseline reproduced all three exact errors before worker execution. Aligning fixture clocks lets the actual public claim/activation/worker/custody/retry path run. All three Docker cases pass, including retained candidate verification and explicit discard behavior. Real engine and scripted worker only; no live model.

**Recovery (1 case):** do not attribute to a failed worker or just increase limits. Retained recovered outcome was settled, implementation completed, candidate verification passed, no operator signals/faults; outer child_status=-15 caused exit1/held. Final enforcement publication was recorded. `retained-next-run-results.json` preserves the complete original results before fixture cleanup; `retained-recovery-diagnosis.json` extracts exact facts. Ordinary isolated baseline recovery passed (timing-sensitive). A late parent SIGTERM during interpreter teardown can lose the Python callable-handler protection; the strengthened fixture models that cut explicitly. Original product plus tightened fixture fails with SIG_DFL; candidate survives the same stop with SIG_IGN, exit0 and completed. The never-exiting sibling still dies -9 at the unchanged deadline and remains held. The original log establishes the late SIGTERM outcome, not an instruction-level trace of interpreter teardown; the deterministic fixture supplies that missing controlled interleaving.

## Verification and exact accounting

Prepared `/home/sl/.local/state/baton-v12-venv/bin/python`, existing `just test-one`, explicit disk-backed TMPDIR and both test-root variables. Groups tools-pure, manager-pure, manager-engine. No broad suite rerun. Each run has `.log`, command/duration `.json`, per-ID `.summary.json`, and `.source.json` beside this report. Final complete input identity is `source-identity.json`; consumed dossier inputs copied into isolation and listed in consumed-inputs.json.

| Run | Collected / executed | Pass | Failure | Error | Skips | Wall |
| --- | --- | --- | --- | --- | --- | --- |
| baseline-ten | 10 / 10 | 1 | 6 | 3 | 0 | 14.476638s |
| candidate-ten | 10 / 10 | 10 | 0 | 0 | 0 | 105.108289s |
| baseline-finalization | 1 / 1 | 0 | 1 | 0 | 0 | 5.067993s |
| candidate-adjacent | 222 / 222 | 222 | 0 | 0 | 0 | 66.322338s |

Total measured verification **190.975258s** including failed baseline/control. Candidate232 pass executions represent **225 distinct passing IDs**, not232 distinct tests;7 original pure failures are also in the adjacent222-case selection. Zero duplicate or unaccounted IDs within any run. Baseline failure/error counts remain explicit; none counted as candidate successes. Ledger comparison uses prepared-interpreter collection and test-one verbose results, not a claim of parallel_test --account execution. A parser initially refused a status split by fixture stderr; corrected bookkeeping without rerunning tests.

Exact original ten IDs: failing-ids.json. Their baseline/candidate outcomes: baseline-ten.summary.json and candidate-ten.summary.json. All10 candidate IDs pass. The final adjacent selection includes complete test_stack, test_next_run_flow, test_authoring_enforcement, ActivationNeedsAllThreeToAgree and test_job_observation; all222 pass including newly strengthened late-finalization and future-mtime negatives. The Docker cases ran before the final test-strengthening edits; their fixture/product dependencies are unchanged. Per-run source headers explicitly reconstruct the pre-strengthening tree and do not relabel it as final-tree execution. No redundant Docker rerun was needed for edits limited to unrelated stack/finalization test coverage.

The negative-control finalization run uses candidate tests with ORIGINAL authoring_enforcement.py, intentionally not the whole unchanged baseline. It fails at the explicit SIG_DFL-vs-SIG_IGN assertion; the original full-run data separately records -15. Candidate run establishes actual exit0 and the stuck-manager -9 behavior.

## Preservation, limits and next action

Protected HEAD/index compare equal before/after, host v12 clean (protected-before/after.json). Fixture engine cleanup completed: only unrelated pre-existing mdb114-a remained in Docker's running list; no live instance touched. Scratch is not the only candidate/evidence copy. Candidate test paths are serially owned under this claim; no overlap with other product edits observed.

No unresolved bounded implementation blocker or product decision. Independent review must assess the signal lifetime change and modified test expectations against retained completion/kill behavior, and exact five-path provenance. Owner full-suite rerun after accepted import/checkpoint is still the final gate; the prior11841-case run was failing and is not retroactively green. No broader stress/provider validation is claimed.

Human checkpoint due after review/import. Suggested commit: `fix(v12): preserve completed child exit and align regression fixture clocks`. This handoff does not stage, commit, import or close Work. Pass baton.decide for independent review routing; verify claim release.
