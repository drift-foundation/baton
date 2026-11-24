# W385965 N1/N2 and owner-B proof table

Candidate: `sha256:2abcd54485ab85ab0deb81db2a94447c54f72a2805461cfdc9f3742576eb7887`. Base: `9f9790222dfd004bc8f19d5c378c3acdb00fd4ca`.

Joined accounting: **2791/2791 unique tests passed**, zero failures/errors/skips/unaccounted. See `evidence/implementation-385975/joined-accounting.json` for per-test run locators, duration and exact collection.

All provider/engine behavior is explicitly simulated at its normal boundary; no image, daemon, credential registry, provider network or native execution is qualified. Real local owners, stores, worker entry, disposable Git, output freezing, custody and recovery handoff are exercised.

| Proof | Named deterministic evidence (all passed) |
| --- | --- |
| 1 | `tests.tools.test_pool.ExplicitProviderPolicy.test_missing_selection_members_and_unknown_provider_refuse`<br>`tests.manager.test_model_attribution.Participation.test_1_model_selection_changes_only_worker_profile_identity` |
| 2 | `tests.tools.test_pool.ExplicitProviderPolicy.test_new_selection_binds_profile_adapter_and_shared_policy`<br>`tests.manager.test_provider_home.SharedProviderPackageBoundary.test_provider_launch_round_trip_and_cross_attempt_refusal` |
| 3 | `tests.manager.test_model_attribution.BuildProbe.test_3_probe_is_bounded_and_never_invocation_start_evidence`<br>`tests.tools.test_provider_selection.SelectedCase.test_14_conflicting_build_holds_before_checkpoint` |
| 4 | `tests.manager.test_model_attribution.Participation.test_4_9_union_sources_and_exact_mapping` |
| 5 | `tests.manager.test_model_attribution.Participation.test_3_5_missing_malformed_partial_oversize_and_build` |
| 6 | `tests.manager.test_model_attribution.Participation.test_6_7_text_echo_error_and_unlisted_fields_never_contribute` |
| 7 | `tests.manager.test_model_attribution.Participation.test_6_7_text_echo_error_and_unlisted_fields_never_contribute` |
| 8 | `tests.manager.test_model_attribution.Participation.test_8_10_unrestricted_contributors_but_case_prefix_suffix_do_not_match` |
| 9 | `tests.manager.test_model_attribution.Participation.test_4_9_union_sources_and_exact_mapping` |
| 10 | `tests.manager.test_model_attribution.Participation.test_8_10_unrestricted_contributors_but_case_prefix_suffix_do_not_match` |
| 11 | `tests.manager.test_model_attribution.Participation.test_11_12_normalized_participation_and_exact_retained_byte_digest` |
| 12 | `tests.manager.test_model_attribution.Participation.test_11_12_normalized_participation_and_exact_retained_byte_digest` |
| 13 | `tests.tools.test_provider_selection.SelectedCase.test_13_positive_implementation_binds_frozen_result_and_checkpoint`<br>`tests.tools.test_provider_selection.SelectedCase.test_13_review_binds_its_own_evidence_to_verdict` |
| 14 | `tests.tools.test_provider_selection.SelectedCase.test_14_17_missing_output_holds_without_publication_or_retry`<br>`tests.tools.test_provider_selection.SelectedCase.test_14_conflicting_build_holds_before_checkpoint`<br>`tests.tools.test_provider_selection.SelectedCase.test_14_review_without_requested_contributor_records_no_verdict` |
| 15 | `tests.tools.test_provider_selection.SelectedCase.test_15_foreign_attempt_in_real_frozen_result_is_held` |
| 16 | `tests.tools.test_provider_selection.SelectedCase.test_16_restart_between_result_and_ending_uses_original_evidence`<br>`tests.tools.test_provider_selection.SelectedCase.test_16_frozen_evidence_survives_store_reopen_and_detects_log_tampering` |
| 17 | `tests.tools.test_provider_selection.SelectedCase.test_17_legacy_result_without_attribution_is_held_under_new_selection` |
| 18 | `tests.manager.test_model_attribution.Participation.test_18_19_diagnostic_words_and_legacy_default`<br>`tests.tools.test_provider_selection.SelectedCase.test_18_35_40_47_home_and_credentials_are_not_output_or_session_resume` |
| 19 | `tests.manager.test_model_attribution.Participation.test_18_19_diagnostic_words_and_legacy_default`<br>`tests.tools.test_pool.ExplicitProviderPolicy.test_legacy_composition_is_unchanged_by_explicit_absence` |
| 20 | `tests.tools.test_provider_selection.SelectedCase.test_20_separation_is_composed_from_selected_providers_and_models` |
| 21 | `tests.manager.test_model_attribution.Participation.test_21_participation_sources_are_adapter_identity` |
| 22 | `tests.manager.test_claude_agent` (287 exact IDs enumerated in proof-table.json) |
| 23 | `tests.manager.test_claude_agent.ProviderProcessBoundary.test_stdin_is_disconnected_for_actual_and_injected_provider` |
| 24 | `tests.manager.test_claude_agent.ProviderProcessBoundary.test_timeout_kills_term_ignoring_group_and_drains_its_pipe` |
| 25 | `tests.tools.test_provider_selection.SelectedCase.test_25_simulated_codex_and_claude_share_policy_and_admit_distinct_lanes` |
| 26 | `tests.tools.test_provider_selection.SelectedCase.test_26_actual_argv_or_environment_drift_refuses_before_provider`<br>`tests.tools.test_provider_selection.SelectedCase.test_26_environment_drift_refuses_before_build_probe` |
| 27 | `tests.tools.test_provider_selection.SelectedCase.test_27_28_changed_tool_policy_refuses_before_any_runtime` |
| 28 | `tests.tools.test_pool.ExplicitProviderPolicy.test_adapter_digest_and_implements_binding_tamper_refuse` |
| 29 | `tests.tools.test_pool.ExplicitProviderPolicy.test_unknown_policy_member_value_refuses_composition`<br>`tests.tools.test_pool.ExplicitProviderPolicy.test_missing_selection_members_and_unknown_provider_refuse` |
| 30 | `tests.tools.test_pool.ExplicitProviderPolicy.test_legacy_composition_is_unchanged_by_explicit_absence`<br>`tests.tools.test_provider_selection.SelectedCase.test_30_legacy_and_selected_lanes_refuse_one_job_before_effects` |
| 31 | `tests.manager.test_provider_home.RetainedProviderHome.test_31_same_job_worker_restart_and_distinct_worker`<br>`tests.tools.test_provider_selection.SelectedCase.test_31_override_home_location_refuses_before_runtime` |
| 31a | `tests.manager.test_provider_home.RetainedProviderHome.test_31a_hostile_ids_only_enter_bounded_digest_components` |
| 31b | `tests.manager.test_provider_home.RetainedProviderHome.test_31b_structured_identity_has_no_join_collisions` |
| 31c | `tests.manager.test_provider_home.RetainedProviderHome.test_31c_wrong_missing_record_and_symlink_refuse_without_repair` |
| 31d | `tests.manager.test_provider_home.RetainedProviderHome.test_31d_plain_identity_and_holder_live_outside_mounted_home` |
| 32 | `tests.manager.test_provider_home.RetainedProviderHome.test_32_retention_and_32a_new_job_starts_empty`<br>`tests.tools.test_provider_selection.SelectedCase.test_32_38_correction_reuses_home_after_positive_runtime_cessation`<br>`tests.tools.test_provider_selection.SelectedCase.test_32_restart_after_review_reuses_retained_home`<br>`tests.tools.test_provider_selection.SelectedCase.test_41_42_43_seeded_provider_refresh_survives_correction_without_export`<br>`tests.manager.test_provider_home.RetainedProviderHome.test_32_failed_holder_release_and_return_from_another_job_preserve_bytes` |
| 32a | `tests.manager.test_provider_home.RetainedProviderHome.test_32_retention_and_32a_new_job_starts_empty`<br>`tests.manager.test_provider_home.RetainedProviderHome.test_32_failed_holder_release_and_return_from_another_job_preserve_bytes` |
| 33 | `tests.manager.test_oci.TheVectorsAreClosedAndOrdered.test_the_run_vector_is_exact_for_both_engines`<br>`tests.tools.test_pool.ExplicitProviderPolicy.test_legacy_composition_is_unchanged_by_explicit_absence` |
| 34 | `tests.manager.test_provider_home.RetainedProviderHome.test_34_protected_storage_overlap_in_both_directions`<br>`tests.tools.test_provider_selection.SelectedCase.test_34_cross_worker_context_and_checkout_overlap_refuse_preflight`<br>`tests.tools.test_provider_selection.SelectedCase.test_31_override_home_location_refuses_before_runtime`<br>`tests.manager.test_provider_home.ProviderHomeMount.test_inode_replacement_invalidates_mount` |
| 35 | `tests.tools.test_provider_selection.SelectedCase.test_18_35_40_47_home_and_credentials_are_not_output_or_session_resume`<br>`tests.tools.test_provider_selection.SelectedCase.test_32_38_correction_reuses_home_after_positive_runtime_cessation` |
| 36 | `tests.manager.test_provider_home.RetainedProviderHome.test_31d_plain_identity_and_holder_live_outside_mounted_home`<br>`tests.manager.test_provider_home.RetainedProviderHome.test_32_retention_and_32a_new_job_starts_empty` |
| 37 | `tests.job_manager.test_scheduling.Capacity.test_participant_aliases_contribute_one_effective_capacity` |
| 38 | `tests.manager.test_provider_home.RetainedProviderHome.test_38_unknown_stale_uncertain_and_wrong_attempt_hold_then_retry`<br>`tests.tools.test_provider_selection.SelectedCase.test_32_38_correction_reuses_home_after_positive_runtime_cessation` |
| 39 | `tests.manager.test_provider_home.RetainedProviderHome.test_39_crash_after_record_before_home_creation_replays_same_holder` |
| 40 | `tests.manager.test_provider_home.WorkerHomePreparation.test_40_delivered_reference_never_reads_credential_bytes`<br>`tests.tools.test_provider_selection.SelectedCase.test_18_35_40_47_home_and_credentials_are_not_output_or_session_resume` |
| 41 | `tests.manager.test_provider_home.WorkerHomePreparation.test_41_seed_once_and_42_keep_provider_refresh_despite_changed_or_missing_delivery`<br>`tests.manager.test_provider_home.WorkerHomePreparation.test_45_same_seed_may_initialize_distinct_empty_homes`<br>`tests.manager.test_provider_home.WorkerHomePreparation.test_41_second_job_uses_delivery_not_first_jobs_refreshed_seed` |
| 42 | `tests.tools.test_provider_selection.SelectedCase.test_41_42_43_seeded_provider_refresh_survives_correction_without_export` |
| 43 | `tests.tools.test_provider_selection.SelectedCase.test_41_42_43_seeded_provider_refresh_survives_correction_without_export` |
| 44 | `tests.tools.test_provider_selection.SelectedCase.test_44_simulated_authentication_failure_has_no_key_or_fallback`<br>`tests.tools.test_provider_selection.SelectedCase.test_26_environment_drift_refuses_before_build_probe` |
| 45 | `tests.manager.test_provider_home.WorkerHomePreparation.test_45_same_seed_may_initialize_distinct_empty_homes`<br>`tests.tools.test_provider_selection.SelectedCase.test_41_42_43_seeded_provider_refresh_survives_correction_without_export`<br>`tests.tools.test_provider_selection.SelectedCase.test_45_same_seed_reference_allows_two_workers_and_two_jobs` |
| 46 | `tests.manager.test_provider_home.WorkerHomePreparation.test_46_exact_managed_entries_replace_without_touching_provider_state`<br>`tests.manager.test_provider_home.WorkerHomePreparation.test_46_credential_session_and_digest_collisions_refuse_before_writes`<br>`tests.tools.test_provider_selection.SelectedCase.test_46_managed_credential_collision_refuses_composition` |
| 47 | `tests.tools.test_provider_selection.SelectedCase.test_18_35_40_47_home_and_credentials_are_not_output_or_session_resume` |
| B1 | `tests.job_manager.test_provider_attribution_recovery.OriginalProducer.test_B1_original_attribution_travels_through_admission_custody_and_handoff` |
| B2 | `tests.job_manager.test_provider_attribution_recovery.OriginalProducer.test_B2_B3_missing_conflicting_and_cross_attempt_hold_inspection_and_admission` |
| B3 | `tests.job_manager.test_provider_attribution_recovery.OriginalProducer.test_B2_B3_missing_conflicting_and_cross_attempt_hold_inspection_and_admission` |
| B4 | `tests.job_manager.test_provider_attribution_recovery.OriginalProducer.test_B4_cross_candidate_substitution_after_decision_refuses` |
| B5 | `tests.job_manager.test_provider_attribution_recovery.OriginalProducer.test_B5_log_tampering_after_admission_refuses_custody_and_handoff` |
| B6 | `tests.job_manager.test_provider_attribution_recovery.OriginalProducer.test_B6_reopen_replays_admission_and_handoff_without_repeating_publisher` |
| B7 | `tests.job_manager.test_provider_attribution_recovery.OriginalProducer.test_B1_original_attribution_travels_through_admission_custody_and_handoff` |
| B8 | `tests.job_manager.test_publication_recovery_admission / tests.job_manager.test_publication_recovery_execution` (274 exact IDs enumerated in proof-table.json) |

## Scope of the evidence

- 17 simulates a pre-change output by removing the attribution member through the real worker/freeze path; it does not execute an old container image.
- 25 simulates a Codex table row for shared-policy lane admission. N3/N4 inventory and a real Codex adapter remain outside this slice; 44 tests the shared closed environment and typed failure path, not live Codex authentication.
- 32/32a combine connected normal ending/correction/removal/restart with the home owner’s explicit failed-holder and unrelated-Job mount proofs. A failed terminal alone cannot authorize another writer.
- 35 exercises real cleanup, frozen manifests and custody exclusion with marker/sentinel bytes, and verifies retained home state. It does not claim a new live orphan-sweep qualification.
- 39 injects a crash after the durable holder record and before home creation, then replays the same holder.
- 45 admits two synthetic Jobs and two seeded workers using the same configured credential profile; separate home/seed tests prove isolation. No claim about provider account concurrency is made.
- Owner-B B1/B7 use the provider-free publication path; B6 reopens the durable control store and repeats admission/handoff without another publisher. B8 retains all 274 legacy recovery-admission/execution passes.
- Participation-source provenance is the retained September independent review, copied as participation-source-review-235117.json. Its named original temporary raw file is absent; no fresh raw/live qualification is claimed.
