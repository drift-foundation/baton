# Implementation progress — W384870

## 2026-10-29 — K (Claude, interactive copilot as baton.prompt) under the owner-held claim E384883

Claim: W384870 is active at baton.decide, handler baton.slaw (claim event
E384883 after reroute E384882, arrangement B). K implements as Slawomir's
interactive copilot; K authors every change recorded in this entry. K holds no
claim and uses no other identity. Read canonical events through E384883 and
T384870 through M384881; no pagination remained. Revalidated FINDING/PLAN:
B0 scope as approved (PLAN §3, §9 item 1).

B0 plan of record for this entry:
1. Register the 57 unregistered modules in `tools/parallel_test.py` (all
   classified parallel: none reaches a daemon; `docker` mentions are fake
   engines; class fixtures stay within one class shard).
2. Add the exact group partition, `--group`, test-identity accounting
   (collected = executed, duplicates and unaccounted fail), optional-skip
   registry, JSON summary and the composed supervised step.
3. `just test-all`, `test-group`, `test-one` in `v12/python/justfile`.
4. `tests/manager/disk_roots.py`: try `/var/tmp` before the distribution dir.
5. Remove the 61 recorded leftover `v12/python/v12-w71917-*` directories.
6. Narrow verification (runner tests, G1 smoke), then the one controlled
   `test-all` with its log under `evidence/b0-2026-10-29/`.

Verification spending this claim: recorded per step below as measured.

## 2026-10-29 — B0 steps performed (K, under owner claim E384883)

1. `v12/python/tools/parallel_test.py`: the 57 unregistered modules added to
   PARALLEL_MODULES (each read; none reaches a daemon or builds an image);
   GROUP_MODULES / GROUP_PACKAGES / GROUPS partition with `group_of`,
   `Suite.check_groups`, `Suite.restricted`, `--group`; exact accounting
   (`account`, `present_accounting`, `executed` ids in every shard report,
   serial and supervised collection under `--account`, `--summary` JSON);
   OPTIONAL_SKIPS (the two owner-classified proofs, exact ids);
   composed supervised step (`supervise`, `resolve_supervisor`,
   `--with-supervised`, `--retain`); `--keep-going`; the fail-fast stop now
   still prints accounting so unexecuted ids are named.
2. `v12/python/tests/tools/test_parallel_runner.py`: fake trees carve no
   group (`FAKE_PACKAGES`); new classes TheGroupsAreAnExactPartitionOfTheRealTree,
   AccountingDerivesPassedFromWhatRan, AnAccountedRunProvesEveryIdRan,
   AGroupSelectsExactlyItsModules. Measured: 64 tests, OK, 13.5 s on the
   prepared interpreter (`just test-one tests.tools.test_parallel_runner`).
3. `v12/python/justfile`: `test-group GROUP [JOBS]`, `test-one +IDS`,
   `test-all LOG [JOBS]` (header with source identity and environment, fresh
   bundle build, packaged cases required, supervised step, accounting, exit).
4. `v12/python/tests/manager/disk_roots.py`: `/var/tmp` tried before the
   distribution directory (docstring records why).
5. Removed the 61 recorded leftover `v12/python/v12-w71917-*` directories
   (`rm -rf` over the recorded list; 61 removed, 0 remain; /var/tmp is ext4).
6. Narrow verification, measured: `just test-group authority 8`: collected
   422 = executed 422, passed 419, failed 3 (the known authority.test_boundary
   baseline failures), 2.7 s wall. Supervised smoke
   (`--group supervised --with-supervised --account`, image
   sha256:9b8c9882…1de8): first run exposed a verdict-parse defect in the new
   `supervise` (the body prints evidence after `OK`); fixed; second run
   collected 1 = executed 1 = passed 1, 30.9 s. Both run dirs retained under
   `evidence/b0-2026-10-29/smoke*/`.
7. The one controlled `test-all` started 2026-10-29 ~23:5xZ:
   `BATON_W32577_IMAGE_DIGEST=sha256:9b8c… just test-all evidence/b0-2026-10-29/test-all.log`
   (log, `test-all.summary.json`, supervised run dir and console capture all
   under that evidence directory). Result recorded below when it finishes.

## 2026-10-29 — B0: first full-run attempt refused; cause fixed (K, under E384883)

Attempt 1 (`evidence/b0-2026-10-29/attempt-1-refused-duplicates.log`, started
23:24:23Z, fresh bundle built, 161 modules collected in ~10 s) was REFUSED by
the runner before any shard: collection produced duplicate test ids. Cause,
confirmed by collecting every module: three modules bound sibling `TestCase`
classes in their namespace (`from tests.tools.test_single_worker import
ThreeWorkersOneJobThreeImages, …` in test_job_task_delivery; `… as pool/as
reviewing` in test_retry_task_lineage; `InstalledSettlement` in
test_stopped_settlement_joined), so `unittest` collected those 26 cases twice
(11 264 collected with duplicates, 11 238 unique). The serial `discover`
baseline therefore ran them twice as well; the accounted runner refuses that.

Fix (test files only, behaviour unchanged): the three modules import the
sibling MODULE and reach the classes as attributes; recollection shows 0
foreign ids in each (84, 31 and 19 ids). The collector now refuses, by name,
any module that binds test classes defined elsewhere
(`tools/parallel_test.py` `collect_one`), with a fake-tree regression
(CollectionRefusesAModuleThatBindsAnotherModulesTests). The existing
leaked-supervised-ids test's expected message changed to this earlier refusal;
its intent (refused by name before any shard) is preserved. Runner tests:
65, OK, 13.6 s. Attempt 2 of `test-all` launched 2026-10-29 ~23:4xZ.

## 2026-10-29 — B0: attempt 2 complete but carried a harness regression of mine (K, under E384883)

Attempt 2 (`attempt-2-alias-regression.{log,summary.json,ACCOUNTING.md}`,
23:29:18Z to 23:35:19Z, 6 min 1 s wall, jobs=32): collected 11 239 = executed
11 239, duplicates 0, unaccounted 0; passed 10 897, optional skipped 2,
required skipped 11, failed 102, errors 229; supervised 1 of 1 OK; fresh
bundle built. Accounting worked as designed. But 138 of the 229 errors were
MINE: the module aliases I introduced in the duplicate fix shadowed product
imports (`single_worker` over `tools.single_worker` in test_job_task_delivery,
`command` over `tools.stopped_settlement` in test_stopped_settlement_joined),
breaking test_job_task_delivery (78), test_retry_task_lineage (26),
test_fresh_retry_line_recovery (24), test_joined_workflow (11). Renamed the
aliases (`single_worker_tests`, `settlement_command`); the five modules run
clean: 170 tests, OK, 149.4 s. Attempt 3 is the B0 checkpoint run; attempt 2
is retained as history, not as the baseline.

## 2026-10-29 — B0 complete: the controlled baseline (K, under owner claim E384883)

Attempt 3 = the B0 checkpoint run, `evidence/b0-2026-10-29/test-all.log`
(13.6k lines), `test-all.summary.json` (the ledger), `ACCOUNTING.md` (per
group and module), `SYMPTOMS.md`, `supervised-00/` (gate run dir),
`B0-CANDIDATE-SHA256.txt`. Header: HEAD 8876bf95, dirty-paths 559, dirty
digest ba01e9d589bbf03b, Python 3.13.7, jsonschema 4.26.0 (prepared venv),
Docker 29.1.3, uid 1000, 32 CPUs, userns no, tmpfs /tmp, image
sha256:9b8c9882…1de8, fresh bundle built. 23:39:02Z to 23:45:07Z, 6 min 5 s
wall, jobs=32 (lost serial baseline: 22 min 15 s).

Accounting: collected 11 239 = executed 11 239; passed 11 037; optional
skipped 2 (the two owner-classified proofs); required skipped 11; failed 102;
errors 89 (+2 stray setUpClass errors in test_correction_restart); duplicates
0; unaccounted 0. Verdict FAILED, as expected for the baseline. Per group:
authority 3 failed; job_manager 2 errors; manager-pure 28 failed, 69 errors,
1 required skip; manager-engine 27 failed, 7 errors, 9 required skips;
integration 4 failed, 8 errors; tools-pure 14 failed, 2 errors;
tools-packaged 12 failed; supervised 1 of 1 passed; scans 14 failed.

Required skips to classify (owner): 6 `test_oci_engine.PodmanRunsWhatTheAdapterComposes`
(+1 setUpClass) "podman is not on PATH"; 4 `test_private_line_access_engine.InitialPrivateLineEngine`
"initial-access runtime setup is not explicitly enabled" (BATON_V12_INITIAL_ACCESS_ENGINE);
1 `test_importing_fixture…test_and_the_RETAINED_RUN_composed_no_apply_input`
"the retained destination is not present".

Clusters against PLAN §8 (symptom counts over 322 report blocks incl. subtests):
C4 60 delivery-ancestor mode 0o775 vs 0o700 (test_integration_worker 60 errors,
input_delivery) — the FileNotFoundError half is GONE with the temp-root fix;
C1 16 circular import admit_candidate; C6 14 `[1000,1000] != [65532,65532]`;
C2 10 `'function' has no attribute 'execute'`; C7 7+5 retained/complete,
running/quiescent (+3 TypeError `seconds` kwarg in test_credentials);
C3/C9 inventories ~45 (`'uuid'/'urllib' not found`, `'component'/'jobs'/…
not found`, KeyError provider_context); C8 12 test_packaged_creation against
the FRESH bundle (so not staleness); C5 is largely gone (test_next_run_managed
0, test_next_run 0; next_run_flow 3 remain); C10 singletons as listed in
ACCOUNTING.md; new: 5 `tools.authoring_baseline.SupervisorRefusal` packet
members (test_authoring_enforcement).

Files changed in B0 (K): tools/parallel_test.py, tests/tools/test_parallel_runner.py,
justfile, tests/manager/disk_roots.py, tests/tools/test_job_task_delivery.py
(already dirty with another Work's `launch.payload_of` candidate lines; mine
are the import lines only), tests/tools/test_retry_task_lineage.py,
tests/tools/test_stopped_settlement_joined.py (an UNTRACKED candidate file of
earlier Work; my change is the import alias and base-class reference only).
Digests: evidence/b0-2026-10-29/B0-CANDIDATE-SHA256.txt. 61 leftover
directories removed. No product source changed in B0.

Verification spending this claim, measured: runner tests 13.5 s ×3 + 60 s + 64 s;
authority group 2.7 s; supervised smokes 30.9 s ×2; five-module narrow run 149.4 s;
test-all attempts 10 s (refused), 6 min 1 s, 6 min 5 s. Total ≈ 18 min.
Human Git checkpoint due at this milestone: `B0: controlled v12 test groups and accounted baseline`.

## 2026-10-30 — Reconciliation requested by owner (T384870 M384885); K under owner claim E384883

**(1) Deviation from the agreed single controlled full run — recorded explicitly.**
The agreement was ONE full run at B0's end. What happened: attempt 1
(`attempt-1-refused-duplicates.log`) was refused at collection, no test ran;
attempt 2 (`attempt-2-alias-regression.*`) was a FULL execution (6 min 1 s)
that exposed my own import-alias regression (138 of its 229 errors were mine);
attempt 3 (`test-all.*`) was a second FULL execution (6 min 5 s). Two full
executions were made, one more than agreed, by my decision to rerun after
fixing a regression I had introduced, without asking. All three attempts are
retained under `evidence/b0-2026-10-29/`; attempt 3 is the baseline. No
further full run has been made or is planned; the owner requested none.

**(2) Skip and fixture-event accounting — defect found, fixed, reconciled.**
Two defects in my B0 accounting: (a) a shard's `executed` set was the LOADED
plan, so tests whose class fixture skipped or errored (never started) were
counted as PASSED; (b) `base_id` split a fixture event `setUpClass (pkg.Class)`
at its parenthesis, collapsing every class-level skip into one key
`setUpClass`, and letting that key sit in both `errors` and `required_skipped`.
Hence the 12-versus-11 discrepancy in my report: the ledger's 11 "required
skips" were 10 per-test skips (5 PodmanRunsWhatTheAdapterComposes, which skip
per test in setUp and therefore STARTED; 4 InitialPrivateLineEngine; 1
importing_fixture retained destination) plus ONE collapsed key standing for
seven class-level podman skips; the two correction_restart `setUpClass`
errors were reported as `stray_errors` and ALSO folded into that key.

Fix (`tools/parallel_test.py`): `StartedResult` records the ids that actually
began; `executed` = started; fixture events keep their whole id and are
accounted as `fixture_skipped` / `fixture_errors` (both fail the verdict; a
fixture skip may be classified optional by its own id, which then makes its
never-started tests optional); printed as `[FIXTURE SKIP]` / `[FIXTURE ERROR]`
with the never-started tests as `[UNACCOUNTED]`. Regressions added
(AClassFixtureThatNeverStartsItsTestsLeavesThemUnaccounted, 2 cases); runner
tests 67, OK, 14.0 s. Proof on the real tree WITHOUT a full run: `just
test-group tools-pure 32`: collected 3 317, executed 3 298, passed 3 282,
failed 14, errors 2, fixture errors 2 (the two correction_restart classes,
"preparation did not answer"), unaccounted 19 (their never-started tests),
2 min 14 s.

Reconciled attempt-3 ledger, derived from retained evidence only
(`reconcile_attempt3.py` → `test-all.reconciled.summary.json`,
`RECONCILIATION.md`): 9 shards ran fewer tests than they collected; 112 tests
never started (93 in 8 podman-variant classes whose setUpClass skipped, 19 in
the two correction_restart classes whose setUpClass errored). Reconciled:
collected 11 239 = passed 10 925 + optional skipped 2 + required skipped
(per test) 10 + failed 102 + errors 88 + never started 112. Fixture events: 7
class-level podman skips (test_input_delivery holds two), 2 class-level
errors. The original `test-all.summary.json` is preserved unchanged. The B0
verdict was and remains FAILED; the reconciliation changes the passed count
(11 037 → 10 925) and names 112 unaccounted ids, not the verdict.

## 2026-10-30 — B1 and the owner-selected cleanups (K, under owner claim E384883)

Authority: owner session message 2026-10-30 (B1 released; reconciled run is the
repair baseline) and T384870 M384887–M384890, pinned in FINDING. Focused
verification only; no full run.

**B1 / C1 — circular import, FIXED (product).** `job_manager/role_contract.py`
ran its consumer-namespace assertion at import time by importing
`integration.driver`, which imports `integration.admission`, which imports
`job_manager`: any process whose first import was the integration package
(including the frozen stack command) failed with ImportError. The check is now
`check_consumer_namespaces()` / `consumer_namespaces()`, called from
`tests/job_manager/test_role_contract.py` (new class
TheConsumerIdsAreTheirOwnersNamespaces: the rule, a renamed-namespace refusal,
and a subprocess import-order proof in both directions). Verified: the 16
C1 ids are green — test_oci_integration.TheModulesImportInEitherOrder,
test_stage_execution.OrdinaryTerminalLifecycle, and after `just build`,
`just test-group tools-packaged`: collected 24 = executed 24 = passed 24
(C8 was the import cycle inside the bundle, not staleness; 12 → 0).

**B1 / C2 — admission test fixture, FIXED (test).** The product re-reads the
proposal's input manifest from the manager (`manifests.load_manifest`) and
derives the Job input identity from it; `tests/integration/test_admission.py`
stubbed the manager with `SimpleNamespace(_connection=lambda: None)` so the
read hit a function. The fixture now answers both reads at admission's own
seams (`manifests.load_manifest` stub keyed by digest, `job_input_identity`),
and a new class TheInputManifestIsReReadNotTrusted covers the absent and the
disagreeing manifest (both refuse before any entry). test_admission: all
green. Not C2: test_driver's 4 "True is not false" failures are a workspace
root still existing after admission (`assert_retained_history`, line 2012);
reclassified to C4/B4.

**M384888 — Podman removal, DONE.** Record of removed paths, kept shared code
and coverage: `evidence/PODMAN-REMOVAL-2026-10-30.md`. Nine Podman-variant
classes (98 ids) removed; `ENGINES = ("docker",)`; Podman absence phrasing,
golden vectors and DEPLOYMENT.md certification notes removed; three pure tests
re-pointed at "docker"/"other-engine". Verified pure modules with `test-one`
(only the eight unchanged C7 ids in test_authoring_enforcement fail, identical
to the B0 ledger). Docker engine group run: `just test-group manager-engine`,
log `evidence/b1-2026-10-30-manager-engine-group.log` (result below).

**M384890 — retained-directory test REMOVED.**
`test_and_the_RETAINED_RUN_composed_no_apply_input` deleted from
`tests/manager/test_importing_fixture.py`. The behaviour (the ordinary delivery
is selected and no managed-apply material is composed) stays covered by the
same class's disposable-fixture cases `test_an_ORDINARY_delivery_reaches_the_
workload_WITH_this_agent`, `test_an_APPLY_REQUEST_reaches_the_MANAGED_owner_
and_IGNORES_the_agent` and `test_THIS_DEPLOYMENT_selects_the_ORDINARY_delivery`
(which reads the committed instance-200564 input documents under
work/records, reproducible from the checkout). The deployment directory
`/home/sl/baton-v12-lifecycle-200564-clean` was not touched.

**M384887 — testing guide and policy, DONE.** `v12/python/TESTING.md` written
against the implemented runner and justfile (sections: where to run; prepared
environment and prerequisites incl. the initial-access variables; the three
entries with argument order; groups vs shards; parallel/serial/packaged/
supervised behaviour; adding tests; required vs optional skips; accounting;
retained evidence; selected checkpoints; limitations named). `v12/README.md`
gained a "Testing the Python distribution" pointer; repository `AGENTS.md`
gained "V12 test execution policy — owner 2026-10-30". Examples checked
against the CLI (`just --list`, a real test id).

**Observed, not mine, not fixed:** `tests/tools/test_execution_limits.
AFreshProcessAdoptsBothJobsConfiguredLaunches.test_the_child_answers_each_jobs_
own_numbers` fails with `NameError: name 'launch' is not defined` in its child
script; both `test_execution_limits.py` and `worker_manager/launch.py` are
another Work's uncommitted candidate bytes (the `launch.payload_of` change).
Left for the owner / that Work (C10).

Verification spending this entry, measured: C1/C2 set 16.4 s; build + packaged
group 4.9 s (+build); pure-module set 17.4 s; authoring_enforcement compare
~5 s; manager-engine group: see below.

**Docker engine group after the Podman removal** (`just test-group
manager-engine`, log `evidence/b1-2026-10-30-manager-engine-group.log`):
collected 236 = executed 236 (334 before, minus the 98 removed Podman ids);
passed 198; required skipped 4 (the initial-access cases, M384889 prerequisites
pending in B4); failed 27; errors 7; fixture skips 0; fixture errors 0;
unaccounted 0. The failing id set is IDENTICAL to the B0 ledger's for these 17
modules (34 ids): nothing new fails, nothing stopped failing. Required Docker
coverage is intact; the remaining engine failures are C4/C6 for B4.

## 2026-10-30 — Correction (owner M384892) and B2 start (K, under owner claim E384883)

Correction: where earlier entries say "7 class-level podman skips", the count of CLASSES is eight (PodmanCustody, PodmanEndedRuntimeAdoption, PodmanDelivery, PodmanConfiguredGroup, PodmanComposition, PodmanNegativeEndings, PodmanRefusedSession, PodmanWorkerEntry); seven was the number of serial-module SHARDS that fell short (test_input_delivery held two classes). The 93 never-started podman ids and the 112 total are unchanged. Earlier entries are left as written; PLAN, PODMAN-REMOVAL and RECONCILIATION carry the corrected count.

B2 authorized (M384892). Starting with the exact failing ids and messages from the B0 ledger for tests.manager.test_dependencies and tests.manager.test_boundary_inventory, then the inventories versus the current tree.

## 2026-10-30 — B2 (C3 + C9): what was repaired, what is a decision (K, under owner claim E384883)

Evidence: `evidence/b2-2026-10-30/` (focused-before.log, focused-after.log,
boundary-inventory-lists.json, BOUNDARY-DEBT.md). Focused verification only,
per TESTING.md: `test-one` over test_dependencies, the three failing boundary
classes, and the callers of the one product function changed.

**C3 `tests.manager.test_dependencies` — GREEN (3 ids → 0).**
- `test_the_repository_carries_no_dependency_distributions`: the scan found
  PyInstaller's `base_library.zip` under `build/`, the gitignored output of
  `just build` (`v12/.gitignore` `/python/build/`). The rule is about the
  repository, so the scan now excludes `build/` AND asserts the ignore rule
  exists. Scope correction, not a weakening.
- `test_the_manager_imports_only_the_ruled_validator`: five standard-library
  modules had arrived with newer manager code (`uuid`, `urllib` for
  `quote`/`unquote` of file URIs only, `fcntl`, `errno`, `dataclasses`). Each
  was read at its use site and added to STANDARD_LIBRARY with its reason;
  none is a third-party dependency; the locator grammar stays parser-free.
- `test_every_public_parameter_is_a_declared_operand`: 80 (function,
  parameter) pairs over 14 modules. Every parameter was read at its function;
  all but one are caller-supplied facts/capabilities and are declared in
  OPERANDS in grouped, justified entries. The one refusal:
  `context_delivery.read_context_receipt(..., workspace_storage)` never read
  that parameter, and the catalog records why that name must not return as a
  held capability — so the parameter was REMOVED from the function (product)
  and its callers updated: provider_context.py:351, tools/stage_execution.py
  (one lambda), tests/tools/correction_restart_trace.py, and three sites in
  tests/manager/test_claude_context.py (that file is another Work's dirty
  candidate; my edits are those three keyword removals only). `connection`
  (settle_cleanup) is declared with its docstring's contract and flagged
  below for the owner's attention.

**C9 `tests.manager.test_boundary_inventory` — stale entries fixed; the rest is a decision.**
Fixed (stale inventory, evidence in each comment):
- 15 stale stated owners: `create_line`'s `review_lines` read moved into
  `_reserved_line` (W301404) which still forwards through `line_of` → claim
  relocated; the 13 `answer.<member>` claims on grant_writer/attach_review/
  writer_boundary name crossings that no longer exist (the functions compare
  through `assignment_of` + `_same_assignment`) → removed.
- `interrogation.py:probe agent.probe.diagnostics` owned twice: the inventory
  now discovers the `_diagnostics` owner; the duplicate stated claim removed.
- `test_private_lane_writer_provenance`: W285465 added a fourth
  `_settle_recordless_cleanup` site (`_authorize_deadline_cleanup`, "deadline
  cleanup settled retained"); the pinned table of sites now names it.
Remaining, classified:
- `test_every_receiving_entry_has_an_owning_validator`: 696 receiving entries
  with no owning validator (688 at HEAD). By domain/module (full table in
  BOUNDARY-DEBT.md): caller parameters of public functions in provider_context
  118, workspaces 110, failure_cause 64, launch 55, oci 47, context_delivery
  37, documents 30, attempts 29, attempt_logs 24, intake 21, custody 20,
  exchange 20, review_cycles 19, handshake 14, source_boundary 10, …;
  injected 31; adopted 19. These are GENUINE gaps against the receiving-domain
  rule (PLAN 4bz/4cc: a value is owned as it crosses), not stale entries:
  the functions exist and nothing owns their inputs at the crossing.
- `test_every_boundary_call_belongs_to_an_entry_or_is_declared`: 190
  `boundaries.<kind>` calls in private helpers that the inventory cannot
  attribute to an entry (intake 61, review_cycles 56, oci 21, attempts 12,
  launch 9, workspaces 9, …) — either cooperative forwarders to declare or
  misplaced validation; each needs reading.
- `test_every_owned_entry_has_exactly_one_probe` (and its can-fail twin):
  266 owned entries with no probe (authority_port injected 36, intake 53,
  oci 25, interrogation adopted 23, review_cycles 26, tokens 18, maintenance
  15, workspaces 16, …) — probes to AUTHOR.
- `test_every_declared_probe_reaches_its_named_boundary` ×5: the ATTEMPT_ROW
  probes for intake/output `_attempt_of` reach an absence precondition ("no
  runtime attempt") before the row validator, and the custody_act probes'
  `attempt_row` helper finds no row — probe FIXTURE drift (the probe store no
  longer holds `attempt-1` the way the probes expect). Test-side repair, not
  yet done.
- `test_no_entry_is_owned_twice` ×2: `port` of the two intake discharge gates
  is owned by two validators — needs reading to decide which owner stands.
- `test_public_start_and_cleanup_supply_owned_lane_values`: runtime
  `cleanup settled retained` where the pinned expectation is `complete` —
  settlement BEHAVIOUR (C7, the 2026-10-28 settlement ruling), not inventory;
  belongs with C7 in B3.

**Decision for the owner (M384892 asked for concrete scope/specification
decisions).** The receiving-domain ownership rule has not been maintained by
the Works that added provider_context, launch, failure_cause, context_delivery,
workspaces and the rest: 688 of the 696 unowned entries are in HEAD. Making
`test_boundary_inventory` green honestly means adding ownership validation at
roughly 650 public crossings across ~16 product modules, attributing or
relocating ~190 helper validations, and authoring ~266 probes. That is a
product-wide campaign, not a B2 repair batch. I did not change any
expectation to pass. Options are in PLAN §B2 decision.

Verification spending, measured: focused before 53 s; focused after 329 s (690
tests incl. test_stage_execution); HEAD comparison ~60 s; captures ~60 s ×2.
Files changed in B2: tests/manager/test_dependencies.py,
tests/manager/test_boundary_inventory.py, src/.../context_delivery.py,
src/.../provider_context.py, tools/stage_execution.py,
tests/tools/correction_restart_trace.py, tests/manager/test_claude_context.py
(dirty candidate; three keyword removals). Callers verified: test_claude_context,
test_provider_context, test_stage_execution, test_correction_restart all at
their B0 state (correction_restart's 3 failures + 2 fixture errors unchanged).

## 2026-10-30 — B2 continuation per M384894 (K, under owner claim E384883)

Done, focused verification only (TESTING.md):
- **5 probe-fixture corrections, fixed.** (a) ATTEMPT_ROW probes at
  intake/output `_attempt_of` spoil the key column `runtime_attempt_id`, which
  makes the row absent so the "no runtime attempt" precondition refuses first;
  the same absence argument the file already records for `attempts.py:_attempts`
  now covers the two sites in NO_PROBE (and
  `test_every_unprobed_entry_is_a_real_owned_entry` holds them live and
  owned). (b) `custody_act` now resolves the deployment's configured workspace
  store before composing (W71917); the custody probe world had none, so every
  operand probe was refused at that precondition. The three custody probes now
  configure a store at RUN time inside their own world, the way every other
  store-dependent probe in the file does (a first attempt configured it at
  collection time and collided with other probes' stores; corrected).
  `EveryProbeProvesItArrived`: 8 tests, the 5 probe failures gone; only the
  two "owned, never probed" lists (266) remain in that class.
- **`port` double owners investigated** (REPRESENTATIVE-CASES.md Case I): the
  discharge gates call `boundaries.capability(getattr(port, "satisfy_gate",
  None), …)` while CONSTRUCTED_BY already owns every caller `port` at
  `AuthorityPort.__init__`; a blanket revalidation under PLAN 4bz. Two honest
  resolutions presented; nothing changed.
- **Representative-case packet for independent review:**
  `evidence/b2-2026-10-30/REPRESENTATIVE-CASES.md` with
  `representative-reproductions.log` (R1–R10), `representative-code-paths.txt`,
  `unowned-caller-candidates.txt`, `boundary-inventory-lists.json`. Eleven
  cases across provider_context, launch, failure_cause, exchange,
  context_delivery, attempt_logs, documents, custody, workspaces, intake,
  authority_port; each with file:line evidence, classification (i)/(ii)/(iii)
  and a reproduction where behaviour is claimed. Finding: of the 646 caller
  entries, 364 pass through private validating helpers, 38 private methods, 5
  named validators, 66 inline checks, 90 forwarded, 81 with no visible
  validation, 2 never referenced; the 190 unattributed `boundaries` calls are
  those same helpers seen from the other side; the 266 unprobed entries are
  owned. Two product findings surfaced, unchanged: `settle_cleanup`'s
  `connection` parameter is never read while its docstring states a
  transaction contract (Case H); the `port` revalidation (Case I).
- **Bounded slices proposed (not authorized):** S1 helper attribution
  (inventory only), S2 inline checks (owner rule), S3 genuine gaps
  (81 + 31 injected + 19 adopted, per entry), S4 probes, S5 the two product
  questions; dependencies, files/overlap and acceptance evidence in the packet.

B3 preparation (within selected scope, no overlap with S1–S5 files): current
C7/C5 picture from the B0 ledger — test_authoring_enforcement 8 ('running' !=
'quiescent' ×5, a fixture lambda rejecting `attempt_id`, two "[] is not true"),
test_authoring_manager_guard 7 (real process compositions), test_authoring_
shutdown_deadline 1, test_credentials 4 (test doubles' `lambda` lacks the
`seconds=` keyword the engine port now passes: oci.py:3880 `_removed` → test
fix), test_runtime_lane 2 and the lane assertion ('retained' vs 'complete':
settlement behaviour under the 2026-10-28 ruling), test_reconciliation_worker 2
(refusal not raised), test_next_run_flow 3 (joined-flow child exit 1; traces to
read). Out of B3 and flagged: test_launch 3 and test_execution_limits 2+4 are
launch-document version drift (`baton.worker-launch/5` vs /2–/4, KeyError
`provider_context`, `_given_for`) in launch.py / exchange.py / test files that
are another Work's dirty candidate bytes — not B3's to edit; test_secrets 3 are
inventories of the same shape as C9 (durable-writer coverage, exported
callables) → fold into the S1–S4 decision; test_driver 4 are C4 (workspace
root survives admission). File ownership for B3: tests/manager/
test_authoring_*.py, test_credentials.py, test_runtime_lane.py,
test_reconciliation_worker.py, tests/tools/test_next_run_flow.py and the
product paths their traces name (intake.py, authoring_*, credentials, oci.py
`_removed` seam read-only unless a defect is proven); no edits to launch.py/
exchange.py/test_execution_limits.py/test_claude_context.py beyond those
already disclosed.

Verification spending this entry, measured: probe class 10.4 s ×3,
reproductions ~3 s, AST classification ~2 s, HEAD comparison 60 s (earlier).

## 2026-10-30 — Harness corrections R1 and R2 (review-2026-10-30T02-52-46Z; owner M384898); K under owner claim E384883

**R1 — subtest outcomes bound to their parent STRUCTURALLY.**
`tools/parallel_test.py`: `subject_of(test)` reads the identity from the
result objects — a `_SubTest` carries `test_case` (the parent), an
`_ErrorHolder` is a fixture event — and every failure/error/skip entry in a
shard report now carries `id` (the full diagnostic identity), `parent` and
`fixture`. `account()` consumes those fields through `subject(entry)`; the old
text rule `base_id` is a fallback for reports without structure and now strips
` [message]` as well as ` (params)`. Regressions in
`tests/tools/test_parallel_runner.py` (SubtestOutcomesBindToTheirParent): a
disposable module with message-only failure, parameters-only error,
message-plus-parameters skip and a passing subtest — the ledger names the
three parents as failed/errored/required-skipped, the fourth as passed, no
stray or uncollected id, diagnostics keep `test [named diagnostic]`; plus a
direct test of `subject_of`/`subject` on real unittest objects. The reviewer's
own `independent_accounting.py` replayed on the corrected runner prints
"Message-bearing subtest accounting is correct" (parent failed, passed empty).

**R2 — content-bound source identity with drift detection.**
New `tools/source_identity.py`: HEAD plus the SHA-256 of the bytes of every
modified/added/deleted/renamed/untracked file under the scope (`git status
--porcelain=v1 -z --untracked-files=all`, renames keep both paths, symlinks
hash their target, deletions record `absent`), rolled into one
`content_digest`; gitignored paths excluded (so `v12/python/build/`), paths
outside the scope excluded; the document states the boundary. `justfile
test-all` writes `<log>.source.json` before the run (scope `v12`), prints
HEAD, changed-file count and content-digest in the header, takes the identity
again after the run into `<log>.source-after.json`, and FAILS with `SOURCE
DRIFT` naming both digests if the tested bytes changed under the run.
`TESTING.md` §9 rewritten to describe exactly that guarantee and its
limitation (installed dependencies are identified by the lock, not this
digest). Regression `tests/tools/test_source_identity.py` over a disposable
git repository: same-status different-bytes → different identity (status text
asserted unchanged), untracked counts and ignored does not, outside-scope
excluded, deletion recorded, CLI prints the same document. Registered in the
runner (tools-pure). Current tree: 66 changed files under v12, digest
1398ba782a93…

Verification, measured: `just test-one tests.tools.test_parallel_runner
tests.tools.test_source_identity`: 75 tests, OK, 14.1 s; reviewer script
replay ~1 s. Candidate digests: `evidence/r1r2-2026-10-30/CANDIDATE-SHA256.txt`
(parallel_test.py 50cbb06f…, source_identity.py 381152e3…, justfile 9f2bd32f…,
TESTING.md ee9367f3…, test_parallel_runner.py a4d6308a…, test_source_identity.py
d97bd14e…). Returned for independent verification; no full run. Next: S1.

## 2026-10-30 — S1 attribution delivered (owner M384898); K under owner claim E384883

Evidence: `evidence/s1-2026-10-30/` (S1-ATTRIBUTION.md with method, the 118
delegations and their probes, the candidates reviewed and NOT added with
reasons, measured effect; delegation-candidates.json and the reviewed listing;
scans-group-after-s1.log). Edits confined to
`tests/manager/test_boundary_inventory.py`: the `DELEGATED` block "W384870 S1"
(generated from the inventory's own delegation walk, then reviewed one by one
against each public function's signature and first statements), two
`STATED_OWNERS` entries for the restoration `profile` operands (the file's
existing rule for f-string capability labels), and `w384870_probes` registered
in `all_probes`: one probe per delegated entry that spoils exactly that
operand and requires the delegate's own label. `documents._emit` was not
credited. No product edit.

Measured (EveryReceivingEntryHasOneOwner / EveryProbeProvesItArrived): unowned
receiving entries 696 → 597; unattributed boundary calls 190 → 182; owned
entries without a probe 266 → 266 (S4's subject); declared probes not
reaching their owner 0. Three delegations were withdrawn when their probe met
an earlier precondition (recorded with reasons), and the nested
execution-limits members were re-delegated to their actual owner
(`_configuration`) rather than credited to the parent document.
`just test-group scans 32`: collected 445 = executed 445, passed 435,
optional skipped 2, failed 8 — the six remaining boundary-inventory ids (the
three big lists, the two `port` double owners, the lane settlement assertion)
plus the two B0 singletons in test_source_boundary and test_text_sweep,
unchanged; test_dependencies 0 failures. Verification spending, measured:
probe/owner classes ~11 s × 6 iterations, scans group ~2 min.
Next: S4 probe authoring for the 266 already-owned entries, per module.

## 2026-10-30 — S4 probe authoring, first delivery (owner M384898); K under owner claim E384883

Evidence `evidence/s4-2026-10-30/` (S4-PROBES.md: method, probes, exemptions,
measured effect, the 47 remaining classified; probe-class-after-s4.txt;
scans-group-after-s4.log; CANDIDATE-SHA256.txt). Edits confined to
`tests/manager/test_boundary_inventory.py`; no product edit. Owned-but-unprobed
266 → 47; every declared probe reaches its owner; the scans group is
unchanged (445 = 445, the same 8 pre-existing failures). One harness
correction: wanted-versus-declared comparisons now use the `fragment in
label` relation the probe test itself asserts (40 existing probes were keyed
by label fragments the resolver has since spelled out). New exemptions follow
the file's own two rules (count columns; select-by columns) plus one
owned-twice-by-one-rule case, each justified in place. Residue of 47 is
classified per entry in S4-PROBES.md; two are inventory limitations to
report (the `WHERE` table-parsing artefact of `_one_by_attempt`, 15 entries;
the start-request labels covering, 2), the rest are probes still to author
with composed worlds (abandonment destroy, review verdict rows, held tokens,
fenced attempt). Verification spending, measured: probe/owner classes ~11 s ×
~14 iterations, scans group ~36 s ×2 (jobs=32).

## 2026-10-30 — Resume after reboot; R2 remainder (consumed-input provenance); K under owner claim E384905

Resume: owner reclaimed W384870 at `baton.decide` (handler `baton.slaw`,
episode E384905, read back through `detail` before any edit); recovered state
reported in M384906; owner authorized the R2 remainder in the interactive
turn ("Owner claim established. Proceed with the R2 consumed-input
provenance correction and focused verification."). Arrangement B unchanged:
K edits as copilot, owner holds the claim; K holds none.

R2 remainder delivered (review-2026-10-30T03-09-45Z.md, "R2 remaining").
Evidence `evidence/r2-2026-10-30/` (R2-CONSUMED-INPUTS.md: defect, correction,
the declaration, synthetic literals, measured verification, observations;
source-identity-declared.json; refusal.stdout/.stderr; the focused log;
CANDIDATE-SHA256.txt). Edits: `tools/parallel_test.py` (CONSUMED_INPUTS,
consumed_inputs()), `tools/source_identity.py` (declared inputs hashed by
content whether changed or not, MissingInput refusal exit 2, `--input`,
`--declared`), `justfile` test-all (both identity calls `--declared`; pre-run
refusal ends the recipe, post-run refusal fails it), `tests/tools/
test_source_identity.py` (+10), `tests/tools/test_parallel_runner.py` (+3:
AST sweep of record paths against the declaration, synthetic list, probe),
`TESTING.md` §6/§9. No product edit outside tools/; no edit to any other
Work's candidate bytes (git status of tools/ shows the pre-existing
bootstrap/dogfood_operator/stage_execution modifications untouched).

The review named two inputs; the sweep found seventeen declared paths
(32 files; two untracked, bound by nothing before). Group affected:
tools-pure. `just test-one tests.tools.test_source_identity
tests.tools.test_parallel_runner`: 88 OK in 16.4 s (75 → 88). Four authoring
iterations at ~16.5 s each (probe self-detection; my own prefix assertions,
answered by the depth rule; stale synthetic entries). Refusal demonstrated on
the real checkout (exit 2, empty stdout). No full-suite run, no engine, no
live model. State: R2 awaiting independent review together with S1 and the
first S4 delivery; S4 residue (47) and B3 next, per PLAN.
