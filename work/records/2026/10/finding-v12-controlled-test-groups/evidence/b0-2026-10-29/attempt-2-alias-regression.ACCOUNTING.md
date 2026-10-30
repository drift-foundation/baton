| group | collected | passed | failed | errors | optional skip | required skip | unaccounted |
|---|---|---|---|---|---|---|---|
| authority | 422 | 419 | 3 | 0 | 0 | 0 | 0 |
| job_manager | 1521 | 1519 | 0 | 2 | 0 | 0 | 0 |
| manager-pure | 4383 | 4285 | 28 | 69 | 0 | 1 | 0 |
| manager-engine | 334 | 291 | 27 | 7 | 0 | 9 | 0 |
| integration | 794 | 782 | 4 | 8 | 0 | 0 | 0 |
| tools-pure | 3315 | 3159 | 14 | 142 | 0 | 0 | 0 |
| tools-packaged | 24 | 12 | 12 | 0 | 0 | 0 | 0 |
| supervised | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| scans | 445 | 429 | 14 | 0 | 2 | 0 | 0 |
| total | 11239 | 10897 | 102 | 229 | 2 | 11 | 0 |

| module | failed | errors | required skip | unaccounted |
|---|---|---|---|---|
| tests.tools.test_job_task_delivery | 0 | 78 | 0 | 0 |
| tests.manager.test_integration_worker | 2 | 60 | 0 | 0 |
| tests.tools.test_retry_task_lineage | 0 | 26 | 0 | 0 |
| tests.tools.test_fresh_retry_line_recovery | 0 | 24 | 0 | 0 |
| tests.manager.test_input_delivery | 19 | 3 | 0 | 0 |
| tests.tools.test_packaged_creation | 12 | 0 | 0 | 0 |
| tests.tools.test_joined_workflow | 0 | 11 | 0 | 0 |
| tests.integration.test_admission | 1 | 8 | 0 | 0 |
| tests.manager.test_boundary_inventory | 9 | 0 | 0 | 0 |
| tests.manager.test_authoring_enforcement | 7 | 1 | 0 | 0 |
| tests.manager.test_authoring_manager_guard | 5 | 2 | 0 | 0 |
| tests.manager.test_credentials | 0 | 4 | 0 | 0 |
| tests.manager.test_custody_engine | 0 | 4 | 0 | 0 |
| tests.tools.test_execution_limits | 2 | 2 | 0 | 0 |
| tests.authority.test_boundary | 3 | 0 | 0 | 0 |
| tests.integration.test_driver | 3 | 0 | 0 | 0 |
| tests.manager.test_dependencies | 3 | 0 | 0 | 0 |
| tests.manager.test_launch | 1 | 2 | 0 | 0 |
| tests.manager.test_secrets | 3 | 0 | 0 | 0 |
| tests.tools.test_correction_restart | 3 | 0 | 0 | 0 |
| tests.tools.test_next_run_flow | 3 | 0 | 0 | 0 |
| tests.manager.test_ended_runtime_adoption | 2 | 0 | 0 | 0 |
| tests.manager.test_execution_limits | 2 | 0 | 0 | 0 |
| tests.manager.test_lifecycle_composition | 2 | 0 | 0 | 0 |
| tests.manager.test_negative_race_endings | 2 | 0 | 0 | 0 |
| tests.manager.test_reconciliation_worker | 2 | 0 | 0 | 0 |
| tests.manager.test_runtime_lane | 2 | 0 | 0 | 0 |
|  | 0 | 1 | 1 | 0 |
| tests.job_manager.test_native_stop_restart | 0 | 1 | 0 | 0 |
| tests.job_manager.test_serving_renewal | 0 | 1 | 0 | 0 |
| tests.manager.test_authoring_shutdown_deadline | 1 | 0 | 0 | 0 |
| tests.manager.test_credentials_engine | 1 | 0 | 0 | 0 |
| tests.manager.test_integration_image | 1 | 0 | 0 | 0 |
| tests.manager.test_oci_integration | 1 | 0 | 0 | 0 |
| tests.manager.test_source_boundary | 1 | 0 | 0 | 0 |
| tests.manager.test_text_sweep | 1 | 0 | 0 | 0 |
| tests.manager.test_worker_entry_engine | 1 | 0 | 0 | 0 |
| tests.manager.test_worker_image | 1 | 0 | 0 | 0 |
| tests.tools.test_environment | 1 | 0 | 0 | 0 |
| tests.tools.test_operator_verification_view | 1 | 0 | 0 | 0 |
| tests.tools.test_quiescent_assignment_finalization | 1 | 0 | 0 | 0 |
| tests.tools.test_single_worker | 1 | 0 | 0 | 0 |
| tests.tools.test_stage_execution | 1 | 0 | 0 | 0 |
| tests.tools.test_stage_execution_hardening | 1 | 0 | 0 | 0 |
| tests.tools.test_stopped_settlement_joined | 0 | 1 | 0 | 0 |
| tests.manager.test_importing_fixture | 0 | 0 | 1 | 0 |
| tests.manager.test_oci_engine | 0 | 0 | 5 | 0 |
| tests.manager.test_private_line_access_engine | 0 | 0 | 4 | 0 |

stray errors (not collected ids, e.g. setUpClass): 2
duplicates: 0 uncollected: 0 ok: False
