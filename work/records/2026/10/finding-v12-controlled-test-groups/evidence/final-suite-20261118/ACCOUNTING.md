ledger: work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118/test-all.summary.json
verdict ok: False

| collected | executed | passed | opt skip | req skip | failed | errors | fixture skip | fixture err | dup | unacc | uncoll | stray | unexp. success |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11265 | 11265 | 11237 | 2 | 0 | 22 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

| group | collected |
|---|---|
| authority | 423 |
| integration | 796 |
| job_manager | 1524 |
| manager-engine | 237 |
| manager-pure | 4423 |
| scans | 494 |
| supervised | 1 |
| tools-packaged | 24 |
| tools-pure | 3343 |

accounting identity: passed 11237 + optional skipped 2 = 11239 of collected 11265

## failed (22)
- tests.manager.test_maintenance.ARepeatedPreparationDecidesAtTheJournalBeforeTheEngine.test_a_completed_preparation_is_not_repeated_and_creates_nothing
- tests.manager.test_maintenance.ARepeatedPreparationDecidesAtTheJournalBeforeTheEngine.test_a_create_whose_reply_was_lost_is_resumed_with_one_effect
- tests.manager.test_maintenance.TheAnswerIsNotACapability.test_a_holder_cannot_revise_one
- tests.manager.test_maintenance.TheContainersOwnExitDecidesTheOutcome.test_a_nonzero_exit_is_recorded_AND_STILL_HOLDS_THE_RESOURCE
- tests.manager.test_maintenance.TheContainersOwnExitDecidesTheOutcome.test_exit_zero_is_the_positive_control_and_still_settles
- tests.manager.test_maintenance.TheExclUSIONIsDecidedUnderTheWriteLockBothWays.test_a_custody_claim_is_refused_while_a_maintenance_window_stands
- tests.manager.test_maintenance.TheHostSettlesOnEvidenceAndHoldsEverythingElse.test_an_expired_grant_holds_the_resource_and_admits_no_replacement
- tests.manager.test_maintenance.TheHostsOwnSettlementIsDurable.test_it_is_committed_before_the_token_goes_back
- tests.manager.test_maintenance.TheHostsOwnSettlementIsDurable.test_the_real_programs_own_values_are_the_ones_that_validate
- tests.manager.test_maintenance.TheHostsOwnSettlementIsDurable.test_the_receipt_names_the_generation_the_container_and_the_object
- tests.manager.test_maintenance.TheLaunchIsTwoActsAndTheJournalDecidesBetweenThem.test_the_container_is_created_inert_then_bound_and_admitted_then_started
- tests.manager.test_maintenance.TheLaunchIsTwoActsAndTheJournalDecidesBetweenThem.test_the_token_is_returned_only_after_the_absence_is_proved
- tests.manager.test_maintenance.TheOrderingMatrixIsProvedInBothDirections.test_a_preparation_excludes_a_cleanup_admission
- tests.manager.test_maintenance.TheOrderingMatrixIsProvedInBothDirections.test_a_preparation_excludes_an_adoption_admission
- tests.manager.test_maintenance.TheOrderingMatrixIsProvedInBothDirections.test_a_preparation_excludes_an_allocation_admission
- tests.manager.test_maintenance.ThePreparationEffectHappensInsideTheExecution.test_the_host_creates_nothing_at_all_on_this_path
- tests.manager.test_maintenance.ThePreparationEffectHappensInsideTheExecution.test_the_result_root_is_established_by_the_program_and_nothing_else
- tests.manager.test_maintenance.TheTokenIsTheTasksOwnAndNotASecondJournal.test_a_task_start_cannot_acquire_while_the_preparation_holds_it
- tests.manager.test_maintenance.TheWorkspaceEntriesAreExcludedWhileAPreparationWrites.test_a_SETTLED_window_is_history_and_refuses_nothing
- tests.manager.test_maintenance.TheWorkspaceEntriesAreExcludedWhileAPreparationWrites.test_a_removal_ownership_is_not_admitted_beside_a_preparation
- tests.manager.test_maintenance.TheWorkspaceEntriesAreExcludedWhileAPreparationWrites.test_allocation_itself_is_refused_while_a_window_stands
- tests.manager.test_maintenance.TheWorkspaceEntriesAreExcludedWhileAPreparationWrites.test_the_chokepoint_refuses_while_a_window_stands

## errors (4)
- tests.manager.test_attempts.TheFailedStartEndingSurvivesInterruption.test_the_record_must_name_the_runtime_being_destroyed
- tests.manager.test_attempts.TheFailedStartReachesTheRuledEnding.test_the_record_must_name_the_runtime_being_destroyed
- tests.manager.test_maintenance.NoStandingWindowIsEverAdopted.test_the_settlement_and_the_token_return_are_correlatable
- tests.manager.test_maintenance.TheHostsOwnSettlementIsDurable.test_a_fresh_store_handle_reads_the_settlement

## unaccounted (0)

## duplicates (0)

## uncollected (0)

## unexpected_successes (0)

## required_skipped (0)

## fixture_skipped (0)

## fixture_errors (0)

## optional_skipped (2)
- tests.manager.test_source_boundary.CleanupNeverRemovesMaterialThisManagerDidNotCreate.test_a_real_same_filesystem_bind_mount_is_refused — this run cannot create a mount namespace, so the REAL same-filesystem bind mount is not exercised here; test_a_same_filesystem_mount_is_refused_though_its_device_matches proves the same boundary from 
- tests.manager.test_source_boundary.TheWorkspaceIsStorageAndScratchIsBounded.test_more_than_the_scratch_bound_really_fits_in_the_workspace — the >64 MiB disk-workspace proof writes more than the bootstrap container's whole 64 MiB tmpfs; set BATON_V12_LARGE_WORKSPACE_PROOF=1 on a host with room to run it

## stray_errors (0)

## phases
{
 "parallel source": {
  "errors": 4,
  "failures": 22,
  "ok": false,
  "ran": 10752,
  "shards": 1443,
  "skipped": 2
 },
 "serial source": {
  "errors": 0,
  "failures": 0,
  "ok": true,
  "ran": 512,
  "shards": 19,
  "skipped": 0
 },
 "supervised source": {
  "errors": 0,
  "failures": 0,
  "ok": true,
  "ran": 1,
  "shards": 1,
  "skipped": 0
 }
}
