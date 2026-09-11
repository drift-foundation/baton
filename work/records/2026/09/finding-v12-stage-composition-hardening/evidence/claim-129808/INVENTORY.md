# Coverage selection, claim 129808

Source inventory at 2026-09-09; this is not a fresh acceptance of old tests.

| Original scope | Existing evidence surface | Current disposition |
| --- | --- | --- |
| Publication restart | `tests/tools/test_stage_execution.py::TheFocusedChecksItemFourNames` | Reuse; no duplicate. |
| Fenced cleanup and historical reconstruction | `tests/job_manager/test_review_driver.py::TheFencedEndingFinishesTheCleanupItStillOwes`, `TheImplementationResumeReadsRealCommittedCustody`; assembly `TheComposedEndingIsOrderedAndSettledFromItsOwnRecord` and `OrdinaryTerminalLifecycle.test_committed_handoff_recovers_before_local_acknowledgement` | Reconcile remaining cutpoints in a separate bounded review. W110783 still parked at snapshot129815; do not claim its closure. |
| Interrupted integration held | `tests/integration/test_recovery.py::RestartAlwaysHolds`, assembly `AFreshPortReentersANeverStartedDelivery.test_a_runtime_this_execution_did_not_start_is_still_held` and `OrdinaryTerminalLifecycle.test_uncertain_integration_effect_stays_held` | Reuse; no new interruption matrix. |
| Status and logs in exceptional/held states | Integration `StatusAndExplicitRecovery`; assembly read-only completion and exchange observation controls | Component and completed-state evidence exists; joined exceptional/held status and log locators need a separate slice. |
| Construction failure cleanup | Assembly `ConstructionFailureReleasesWhatItOpened` directly builds fake handles; authorization/pool refusal tests check early ordering | Selected gap: actual factory partial construction and concrete close interfaces. |

All test paths above are relative to `v12/python/`. The recent ordinary and
reconstruction acceptance is retained in
`../../../finding-v12-composed-ending-consumer/review-2026-09-09T09-54-24Z.md`
(canonical owning record: `work/records/2026/09/finding-v12-composed-ending-consumer`).

## Execution question and limit

Does the real factory unwind exactly the handles it acquired, preserving the
original construction failure and refusing before pool activation? Existing
fake-handle tests cannot detect a mismatch with concrete worker methods.
Run the new three-case module directly from `v12/python`, with `PYTHONPATH=src:.`,
using `python3 -m unittest -v tests.tools.test_stage_execution_hardening`.
Expected under 3 seconds; subprocess ceiling 10 seconds; stop and retain a red
result before considering any broader run. No Docker, live provider, registry
change or full-suite run. This Work has no inherited W122060 execution budget.

## Operational finding

An exploratory read of guessed path
`v12/python/src/baton_v12/worker_manager/operations.py` failed because it does
not exist. `rg --files` resolved the actual implementation to
`tools/single_worker.py::_Operations` and
`src/baton_v12/job_manager/delegation.py::ManagerOperations`; those sources were
read. This was a locator mistake, not an unavailable required input or Baton
defect.
