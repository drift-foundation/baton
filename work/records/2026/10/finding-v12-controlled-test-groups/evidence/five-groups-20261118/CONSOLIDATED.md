| group | collected | executed | passed | opt skip | req skip | failed | errors | fixture skip | fixture err | dup | unacc | uncoll | stray | verdict | exit | elapsed s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| authority | 423 | 423 | 423 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | OK (source stable) | 0 | 3 |
| job_manager | 1524 | 1524 | 1524 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | OK (source stable) | 0 | 20 |
| manager-pure | 4420 | 4420 | 4419 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | FAILED (source stable) | 1 | 66 |
| tools-pure | 3341 | 3322 | 3318 | 0 | 0 | 4 | 0 | 0 | 2 | 0 | 19 | 0 | 0 | FAILED (source stable) | 1 | 173 |
| integration | 796 | 796 | 796 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | OK (source stable) | 0 | 9 |

non-passing entries: 26; KNOWN-G2 22 of 22 known ids; NEW 4

## KNOWN-G2 (still failing)
- tests.tools.test_correction_restart.CountedReopen.test_manager_recomposition_preserves_both_positive_counts — failed
- tests.tools.test_correction_restart.CountedReopenInvalidEvidence.test_absent_actual_reopen_is_rejected — unaccounted
- tests.tools.test_correction_restart.CountedReopenInvalidEvidence.test_changed_verdict_checkpoint_or_attempt_is_rejected — unaccounted
- tests.tools.test_correction_restart.CountedReopenInvalidEvidence.test_duplicate_engine_is_rejected_independently — unaccounted
- tests.tools.test_correction_restart.CountedReopenInvalidEvidence.test_duplicate_provider_is_rejected_independently — unaccounted
- tests.tools.test_correction_restart.CountedReopenInvalidEvidence.test_forged_context_receipt_is_rejected — unaccounted
- tests.tools.test_correction_restart.CountedReopenInvalidEvidence.test_missing_positive_baseline_is_rejected — unaccounted
- tests.tools.test_correction_restart.TransactionBoundaryThroughTheConnectedPath.test_no_external_reader_runs_inside_a_control_transaction — failed
- tests.tools.test_correction_restart.UsefulCorrection.test_useful_correction_reaches_managed_target — failed
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_a_MISSING_or_DUPLICATED_token_observation_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_a_REUSED_runtime_id_on_the_restored_use_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_a_RUNNING_predecessor_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_a_STALE_token_generation_on_the_restored_use_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_a_WRONG_token_CONTAINER_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_a_WRONG_token_LAUNCH_operation_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_an_ALREADY_ACTIVATED_new_token_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_an_UNRETURNED_opening_token_at_the_restored_activation_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_identical_revised_code_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_missing_or_forged_changes_requested_verdict_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_reviewer_context_or_writable_line_access_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_target_receipt_naming_original_is_rejected — unaccounted
- tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence.test_unexecuted_or_wrong_byte_verifier_is_rejected — unaccounted

## KNOWN-G2 ids NOT in the remainder (now passing or not collected)

## NEW (not in the known G2 list)
- setUpClass (tests.tools.test_correction_restart.CountedReopenInvalidEvidence) — fixture_errors
- setUpClass (tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence) — fixture_errors
- tests.manager.test_diagnostic_rendering.TheRuledAssertionsRenderThroughSortedCollections.test_the_missing_probe_check_compares_a_sorted_list_with_an_empty_list — failed
- tests.tools.test_operator_verification_view.TheOperatorsViewRefusesWhatThePacketSays.test_the_view_is_gone_after_every_refusal — failed

## optional skips (registry)
