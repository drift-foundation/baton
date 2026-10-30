# Reconciliation of attempt 3 (B0 baseline) — from retained evidence, no rerun

Shards that ran fewer tests than they collected: 9

| shard label | collected | ran | never started |
|---|---|---|---|
| tests.manager.test_custody_engine | 22 | 11 | 11 |
| tests.manager.test_ended_runtime_adoption | 16 | 8 | 8 |
| tests.manager.test_input_delivery | 80 | 56 | 24 |
| tests.manager.test_lifecycle_composition | 64 | 32 | 32 |
| tests.manager.test_negative_race_endings | 10 | 5 | 5 |
| tests.manager.test_refused_session_engine | 16 | 8 | 8 |
| tests.manager.test_worker_entry_engine | 10 | 5 | 5 |
| tests.tools.test_correction_restart.CountedReopenInvalidEvidence | 6 | 0 | 6 |
| tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence | 13 | 0 | 13 |

Never-started test ids: 112 (listed in test-all.reconciled.summary.json `unaccounted`)
Original ledger: passed 11037, unaccounted 0
Reconciled: passed 10925, unaccounted 112, failed 102, errors 88 per test (+2 fixture errors), optional skipped 2, required skipped (per-test) 10, collected 11239
Check: passed + optional + required-per-test + failed + errors + never-started = 11240

Outcome-set overlap explaining the +1: errors∩required_skipped = ['setUpClass']. That key is NOT a test id: it is the collapsed fixture-event key the first ledger produced (the two correction_restart setUpClass ERRORS landed in `errors` as `setUpClass`, the seven podman setUpClass SKIPS landed in `required_skipped` as `setUpClass`). Removing it: per-test errors are 88, per-test required skips 10, and 10925 + 2 + 10 + 102 + 88 + 112 = 11239 = collected.

Fixture-level events in attempt 3 (from the shard shortfalls above): 7 class-level `setUpClass` SKIPS, all `podman is not on PATH` (PodmanCustody, PodmanEndedRuntimeAdoption, PodmanDelivery, PodmanConfiguredGroup, PodmanComposition, PodmanNegativeEndings, PodmanRefusedSession, PodmanWorkerEntry — the first ledger collapsed them into one `setUpClass` key; test_input_delivery holds two of them), and 2 class-level `setUpClass` ERRORS (test_correction_restart.CountedReopenInvalidEvidence, UsefulCorrectionInvalidEvidence; preparation did not answer). The 5 `PodmanRunsWhatTheAdapterComposes` cases in test_oci_engine skip per test in setUp, so they STARTED and are the 5 per-test podman skips; with the 4 initial-access and 1 retained-destination skips that makes the 10 per-test required skips. 93 podman-class tests + 19 correction_restart tests = 112 never started.

Evidence: test-all.log shard lines (`grep -n '(0 tests)\|test_input_delivery (56 tests)' test-all.log`), test-all.summary.json (`passed` contains the 112 ids; `stray_errors` holds the two setUpClass errors; `required_skipped` holds the collapsed `setUpClass` key), podman-classes.json (the 9 classes and their id counts), attempt-3 shard labels are classes except serial modules and the supervised module.

**Correction 2026-10-30 (owner M384892):** the class-level podman skips above are EIGHT classes (PodmanCustody, PodmanEndedRuntimeAdoption, PodmanDelivery, PodmanConfiguredGroup, PodmanComposition, PodmanNegativeEndings, PodmanRefusedSession, PodmanWorkerEntry) across SEVEN serial-module shards; the text above that says "7 class-level" counted shards, not classes. The 93-id and 112-id totals are unchanged.
