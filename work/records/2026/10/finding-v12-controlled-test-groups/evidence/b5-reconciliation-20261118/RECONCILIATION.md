# C10/B5 reconciliation of the B0 historical adverse ids (M385060)

K, copilot under owner claim E384905, no claim held. Review: `review-2026-11-18T01-59-25Z.md`.
Source: owner commit 438eefa6 plus the accepted B5 diagnostic candidate (errors.py, workspaces.py,
test_workspaces.py; content digest 4ba0810a…, identical before and after the focused run:
`source.json`, `source-after.json`). Docstring nit from the review corrected in `path_value` (prose only).

## Universe

Every adverse id of `evidence/b0-2026-10-29/test-all.reconciled.summary.json`: 102 failed + 88 per-test
errors + 112 never started + 10 per-test required skips + 3 collapsed fixture-event keys = 315 rows
(`b0-adverse-ids.json`; the two B0 optional skips are the registry's and are not adverse). Each row is
classified once in `reconciliation.tsv` (id, B0 outcome, classification, evidence). No discharged id was
re-run merely to reconstruct history: scans ids are discharged by the accepted scans ledger, engine ids by
the child's joined-438eefa6 ledger where that selection completed, and only the 84 present, deterministic,
non-engine, non-scans, non-bundle ids were run (`unresolved-ids.txt`, `unresolved-ids.log`,
`unresolved-ids-outcomes.json`), plus the one pure import-order id of test_oci_integration.

## Totals

| classification | ids |
|---|---|
| accepted at 438eefa6 | 200 |
| verified OK now (this slice) | 43 |
| still failing | 42 |
| unverified | 25 |
| fixture-event key (not an id) | 3 |
| removed/replaced by owner-committed repair | 2 |
| total | 315 |

## By module

| module | accepted at 438eefa6 | verified OK now (this slice) | still failing | unverified | fixture-event key (not an id) | removed/replaced by owner-committed repair |
|---|---|---|---|---|---|---|
| authority.test_boundary | 0 | 0 | 3 | 0 | 0 | 0 |
| integration.test_admission | 0 | 9 | 0 | 0 | 0 | 0 |
| integration.test_driver | 0 | 3 | 0 | 0 | 0 | 0 |
| job_manager.test_native_stop_restart | 0 | 0 | 1 | 0 | 0 | 0 |
| job_manager.test_serving_renewal | 0 | 0 | 1 | 0 | 0 | 0 |
| manager.test_authoring_enforcement | 0 | 8 | 0 | 0 | 0 | 0 |
| manager.test_authoring_manager_guard | 0 | 7 | 0 | 0 | 0 | 0 |
| manager.test_authoring_shutdown_deadline | 0 | 1 | 0 | 0 | 0 | 0 |
| manager.test_boundary_inventory | 9 | 0 | 0 | 0 | 0 | 0 |
| manager.test_credentials | 0 | 4 | 0 | 0 | 0 | 0 |
| manager.test_credentials_engine | 1 | 0 | 0 | 0 | 0 | 0 |
| manager.test_custody_engine | 15 | 0 | 0 | 0 | 0 | 0 |
| manager.test_dependencies | 3 | 0 | 0 | 0 | 0 | 0 |
| manager.test_ended_runtime_adoption | 10 | 0 | 0 | 0 | 0 | 0 |
| manager.test_execution_limits | 0 | 0 | 2 | 0 | 0 | 0 |
| manager.test_importing_fixture | 0 | 0 | 0 | 0 | 0 | 1 |
| manager.test_input_delivery | 45 | 0 | 0 | 0 | 0 | 1 |
| manager.test_integration_image | 1 | 0 | 0 | 0 | 0 | 0 |
| manager.test_integration_worker | 62 | 0 | 0 | 0 | 0 | 0 |
| manager.test_launch | 0 | 0 | 3 | 0 | 0 | 0 |
| manager.test_lifecycle_composition | 34 | 0 | 0 | 0 | 0 | 0 |
| manager.test_negative_race_endings | 7 | 0 | 0 | 0 | 0 | 0 |
| manager.test_oci_engine | 0 | 0 | 0 | 5 | 0 | 0 |
| manager.test_oci_integration | 0 | 1 | 0 | 0 | 0 | 0 |
| manager.test_private_line_access_engine | 4 | 0 | 0 | 0 | 0 | 0 |
| manager.test_reconciliation_worker | 0 | 2 | 0 | 0 | 0 | 0 |
| manager.test_refused_session_engine | 0 | 0 | 0 | 8 | 0 | 0 |
| manager.test_runtime_lane | 0 | 2 | 0 | 0 | 0 | 0 |
| manager.test_secrets | 0 | 0 | 3 | 0 | 0 | 0 |
| manager.test_source_boundary | 1 | 0 | 0 | 0 | 0 | 0 |
| manager.test_text_sweep | 1 | 0 | 0 | 0 | 0 | 0 |
| manager.test_worker_entry_engine | 6 | 0 | 0 | 0 | 0 | 0 |
| manager.test_worker_image | 1 | 0 | 0 | 0 | 0 | 0 |
| setUpClass | 0 | 0 | 0 | 0 | 1 | 0 |
| setUpClass (tests.tools.test_correction_restart.CountedReopenInvalidEvidence) | 0 | 0 | 0 | 0 | 1 | 0 |
| setUpClass (tests.tools.test_correction_restart.UsefulCorrectionInvalidEvidence) | 0 | 0 | 0 | 0 | 1 | 0 |
| tools.test_correction_restart | 0 | 0 | 22 | 0 | 0 | 0 |
| tools.test_environment | 0 | 1 | 0 | 0 | 0 | 0 |
| tools.test_execution_limits | 0 | 0 | 4 | 0 | 0 | 0 |
| tools.test_next_run_flow | 0 | 3 | 0 | 0 | 0 | 0 |
| tools.test_operator_verification_view | 0 | 1 | 0 | 0 | 0 | 0 |
| tools.test_packaged_creation | 0 | 0 | 0 | 12 | 0 | 0 |
| tools.test_quiescent_assignment_finalization | 0 | 0 | 1 | 0 | 0 | 0 |
| tools.test_single_worker | 0 | 0 | 1 | 0 | 0 | 0 |
| tools.test_stage_execution | 0 | 1 | 0 | 0 | 0 | 0 |
| tools.test_stage_execution_hardening | 0 | 0 | 1 | 0 | 0 | 0 |

## Focused run of the 84 unresolved ids

`just test-one` over `unresolved-ids.txt`, TMPDIR/BATON_V12_DISK_ROOT=/var/tmp, 113 s: 65 ran (19 never
started behind two `setUpClass` errors in tests.tools.test_correction_restart), 42 ok, 17 FAIL, 6 ERROR,
identity stable. Per-id outcomes: `unresolved-ids-outcomes.json`.

## Still failing: 42 ids in six causes

G1. Launch-document version drift — 9 ids. Annotation corrected 2026-11-18 (review 02-15-55Z): the Work whose
candidate bytes carried it, W376586, is CLOSED satisfying at E383121 with no handler, so these nine are REQUIRED
under W384870 and the accepted baton.worker-launch/5 protocol is preserved; no repair of them in the G4+G5 slice.
Symptoms: `KeyError: 'provider_context'` / `'session'`, `baton.worker-launch/4` vs `/5`, `/2`/`/3` version
expectations, `SimpleNamespace has no attribute '_given_for'` / `'job_task'`, child `NameError: name 'launch'`.
Ids: tests.manager.test_launch.TheContextLaunchIsClosed (3), tests.manager.test_execution_limits.TheVersionMovesWithTheMember (2),
tests.tools.test_execution_limits (4: AFreshProcessAdoptsBothJobsConfiguredLaunches 1, TheDerivedJudgmentCarriesItsOwningResultsJob 1, TheTwoReadersResolveOneJobIdentically 2).
Not edited this slice.

G2. tests.tools.test_correction_restart — 22 ids, ONE fixture cause: the controller's preparation child exits 1
with an empty log, `"failure": "preparation did not answer"`. Two classes error in setUpClass (19 ids never
start: CountedReopenInvalidEvidence 6, UsefulCorrectionInvalidEvidence 13) and three single tests fail on the
same message (CountedReopen.test_manager_recomposition_preserves_both_positive_counts,
TransactionBoundaryThroughTheConnectedPath.test_no_external_reader_runs_inside_a_control_transaction,
UsefulCorrection.test_useful_correction_reaches_managed_target). Cause unread: the preparation child's exit
needs its retained trace (the historical C10 note 'preparation did not answer' is the same symptom).

G3. job_manager — 2 ids: tests.job_manager.test_native_stop_restart.NativeStopRestart.test_reopened_store_preserves_deadline_and_generation_without_revival,
tests.job_manager.test_serving_renewal.ServingPermission.test_expiry_is_not_revival_or_reuse_and_unknown_cessation_holds.
Both: `ContractRefusal: resource-token.launch for generation 1 of 'workspace:…' is refused: that generation has
been REVOKED` raised from workspaces.reserve -> tokens.journal_launch -> _acting_record -> _owning. The same
symptom is in B0 SYMPTOMS.md, so it predates the renewal-decision change; whether the fixture's revocation
order or the product's launch-after-revoke rule is wrong needs reading before any change.

G4. §13 secrets inventories — 3 ids: tests.manager.test_secrets.EveryDurableWriterIsGuarded.test_every_durable_writer_is_covered
(review_cycles.restore_abandoned_correction writers line_writers/review_lines uncovered),
EveryDurableWriterIsGuarded.test_no_declared_coverage_is_stale (declared entry review_cycles.create_line/review_lines no longer found),
EveryPublicSurfaceIsAccountedFor.test_every_exported_callable_is_in_exactly_one_class (fence_pre_attach_abandonment, observe_deadline
unaccounted). Inventory registries of the C9 shape (B2 noted them for the S1–S4 decision); each needs the real
coverage case or an honest accounting, not an exemption.

G5. tests.authority.test_boundary — 3 ids: EveryDiagnosticIsBoundedByTheRule.test_every_named_site_covers_the_paths_it_was_written_for and
test_no_refusal_renders_an_unbounded_value (store.py `_connect_readonly` line 662 renders `type(failure).__name__` and `failure`
outside the bounding rule / named-site table), Isolation.test_nothing_reaches_for_v11_the_node_host_or_a_dossier
(source_boundary.py carries the word `opt/baton` in `/opt/baton/verifier-layout-marker.json`). Authority package's
diagnostic-bound and isolation rules against two manager modules.

G6. Three tools singletons, distinct causes: tests.tools.test_quiescent_assignment_finalization.TheQuiescentAssignmentIsEndedAndNothingElseIs.test_it_takes_no_agent_and_no_runtime_capability
(the finalizer's signature is now `['store', 'port', 'attempt_id', 'reason']`; the test expects a shorter one);
tests.tools.test_single_worker.AFaultedTerminalSurvivesTheContainerThatWroteIt.test_a_real_observing_status_run_mutates_no_durable_state
(an observing status run added `storage/attempt-…/inputs/assignment.json`);
tests.tools.test_stage_execution_hardening.ConstructionUnwindsConcreteHandles.test_worker_construction_failure_closes_every_acquired_handle
(closed handles `['coordinator', 'authority']`, `implementation` not closed).

## Not run, classified

- Accepted at 438eefa6 (200): 14 scans ids by the accepted scans ledger; 186 engine ids by the
  child's combined joined-B4 ledger (143 + 99 = 242/242 on committed 438eefa6, child review
  2026-11-18T02-08-00Z, parent M385068), including the podman->Docker class renames of afc71d71.
- Unverified at 438eefa6 (25): tests.manager.test_refused_session_engine (8) and test_oci_engine (5) are
  manager-engine modules outside the combined B4 selection (child PREFLIGHT lists them; Docker);
  tests.tools.test_packaged_creation (12) needs a built bundle (C8 gate, tools-packaged group) and no
  build was selected this slice.
- Removed/replaced (2): test_importing_fixture's retained-destination case (owner commit afc71d71);
  test_input_delivery's owner-only-output case renamed by the B4 child (f13f52c4).
- 3 collapsed fixture-event keys are not ids; their classes are classified above.

## Smallest proposed next repair batch

1. G5 + G4 (6 ids): inventory/registry-shaped, no product behaviour change expected, K-owned modules; one
   focused run of tests.authority.test_boundary and tests.manager.test_secrets afterwards.
2. Then G6 (3 ids, three independent small causes), then G2 (22 ids, one fixture cause, needs the preparation
   trace), then G3 (2 ids, product/fixture question in tokens launch-after-revoke).
3. G1 (9) stays required under this Work (W376586 closed); a later batch. The 25 unverified need a Docker engine or bundle selection, not a repair yet.

## 2026-11-18 — G4 + G5 repaired

The six G4/G5 ids are repaired in `evidence/b5-secrets-boundary-20261118/` (six-ids-after.log: 6 OK) and marked REPAIRED in reconciliation.tsv. Remaining: 36 ids in G1 (9, required here), G2 (22), G3 (2), G6 (3).

## 2026-11-18 — the 25 unverified entries resolved

Codexpc's follow-on on committed 438eefa6 collected 30 current ids (8 refused-session, 9 OCI engine, 13 packaged) and passed 30/30 (child review 2026-11-18T02-26-07Z, M385086); the 25 historical unverified rows are marked accepted in reconciliation.tsv. Historical 25 was an estimate; the current collection of 30 is authoritative.
