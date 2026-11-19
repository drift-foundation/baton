# W385222 candidate for independent review

Participant baton.codxpc, role impl, claim E385224; base `a62bc9a3a108acd0f6a1d759034b98af4bd1fa55`. Candidate manifest SHA-256 `c1187bd23f94c8d9721548839bc394205ec3d9a7108827d182da8f33fd5a18a9`; patch SHA-256 `e936fbe3286e55b66d86587df74c4d8ec34bc8cec3f042eb4f16df63d96d0eae`. `candidate/manifest.json` enumerates eight exact changed paths, base and candidate hashes; `candidate/files/` retains actual candidate bytes and `evidence/base-paths.json` retains base bytes. Primary record locator is this canonical dossier, not the commit.

## Outcome

Positive refused/precondition claim answers now invoke existing Authority settlement, which adopts any actual committed claim before retiring an uncommitted identity. Overdue accepted offers settle through the selected worker during ordinary sweeps even after cancellation/deadline fences. Owner-state republication ends episodes and releases logical capacity; committed terminal non-claim receipts cannot become successful claims. Claim and settled-claim pool answers retain the canonical-principal guard. Unknown/transport failures remain reconcilable; no accepted-offer local expiry CAS or schema change was introduced.

The exact accepted scope and expectation supersession are in FINDING.md; path ownership is in PLAN.md; implementation account is in PROGRESS.md. Existing wrong-route tests now assert permanent positive-refusal retirement, no false success/revival, released logical capacity and other-Job progress. The new module has 11 deterministic cases and is registered in the parallel registry.

## Verification

Final selected run: **370 tests, OK, zero skips**, unittest duration 8.559 seconds, wall 8.871 seconds, timeout 180 seconds. Exact command, environment and measured exit status: `evidence/focused-final-run.json`; verbose results: `evidence/focused-final.log`; runnable selection: `evidence/run_focused.py`. Prepared Python 3.13.7, real disposable Authority/control/Job stores, simulated external boundaries. Covers positive refusal, deadline and explicit cancellation, tick/restart replay, dropped owner event, unknown/transport/committed claim races, selected pool settlement, principal guard, transaction exclusion, adjacent offers/delegation/recovery/cancellation/scheduling, composed other-Job progress and module/group registry completeness. `git diff --check` passed.

Earlier exploratory run: 429 tests, 428 passed and one unrelated failure in `tests.tools.test_parallel_runner.TheDeclaredInputsCoverWhatTheTestsRead.test_every_record_path_in_the_tree_is_declared_or_synthetic` (24.721 seconds). It reports the labels dossier `work/records/2026/08/finding-v12-work-tags/findings/finding-v12-work-label-protocol-cli` missing from CONSUMED_INPUTS for test_bootstrap/test_connected_creation/test_pool. All four involved test files and the CONSUMED_INPUTS AST equal the base; see `evidence/unrelated-input-inventory.json`. No repair or waiver claimed. Full log retained as `evidence/focused-final-1.log`. Earlier implementation/test-author failures are retained, superseded for this candidate by the final focused run; their durations are in their logs where available, otherwise unknown. The baseline diagnosis reproduction is `evidence/baseline-repro.log`.

## Limits and handoff condition

No full suite, packaging build, Docker/live provider or live-instance changes. No Git mutation. This does not repair stopped native-labels-3 or certify a deployment; native-labels-4 remains independent. Physical cessation of actual claimed runtimes is still owned by existing cancellation APIs; a committed uncertain claim is deliberately not reported complete merely because its offer is old. This correction targets accepted offers; issued-offer expiry retains its existing separate behavior.

Return to baton.decide for independent review of these exact bytes and evidence; do not self-close. Reviewer should inspect positive refusal versus unknown outcome classification, bound settlement routing, terminal receipt adoption and no-launch-after-fence. K held host edits during this candidate; resume ownership only through coordinator disposition. Owner retains Git.
