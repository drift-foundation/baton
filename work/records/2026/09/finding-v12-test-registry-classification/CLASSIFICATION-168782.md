# Source classification — W168703 / claim168782

2026-09-14. **Proposed for independent review**, not runtime certification or
execution permission. inventory-168782.json binds every source path, full SHA256,
fixture extract and resource-related source line. Actual Suite.discovered and
check_registry found 117 modules: 78 parallel, 19 serial and the original 20
missing. Runner digest: 1c1af72d611dcc6b83eb131f953d30f2e81d8d04cc46e531a7e2cbb4940c6031.

## All 20 missing modules

Module names below have prefix `tests.`; source paths are under `v12/python/`.
P proposes the existing parallel class-shard registry. G proposes a separate
supervised-only classification, never ordinary serial or parallel membership.

| Module | Class | Governing Work | Isolation and resources |
| --- | --- | --- | --- |
| integration.test_managed_execution | P | W161230 | Portable document values; no runtime actor or process. |
| integration.test_managed_storage | P | W161230 | Coordinator/Result/Capacity fixtures own temporary stores, real local Git and disposable Authority; owned thread barriers/joins. Worker import changes sys.path. Custody URLs are document values. |
| integration.test_reconciliation | P | W133117 | Temporary Authority/IntegrationStore and real Git repositories; bounded local subprocesses, private Git environment and cleanup. |
| job_manager.test_execution_limits | P | W156162 | Documents and JobManagerCase temporary SQLite, including migrations. |
| job_manager.test_managed_integration_capacity | P | W161230 | Real disposable Authority and per-case Job/Worker stores; fake adapters and owned threads. Not in-memory-only. |
| manager.test_execution_limits | P | W156162 | Temporary launch/storage fixtures, fake provider. |
| manager.test_reconciliation_task | P | W161230 | Real local Git/Python and fork/timeout cleanup in private roots; sys.path imports worker. Unix process support and bounded cleanup required; no OCI/model. |
| manager.test_reconciliation_worker | P | W161230 | AttemptCase temporary ControlStore, fake session/adapter, no-start assertions. |
| manager.test_runtime_deadline_engine | G | W32577 | Actual Docker lifecycle; class setup requires supervisor gate directory and reviewed preloaded immutable image. Reserved cleanup belongs to surviving supervisor. |
| manager.test_runtime_deadline_engine_budget | P | W32577 | Fake clock/process/Docker responses; custom load_tests selects EngineBudget only despite importing DeadlineDocker. |
| manager.test_runtime_deadlines | P | W32577 | Temporary attempts and fake runtime/clock; custom load_tests preserves selected authored-method matrix. |
| tools.test_execution_limits | P | W161230; W156162 contract | Composed stage/worker fixtures own roots/stores; local Git/Python where exercised; provider/OCI replaced. Global mocks restored by context/cleanup. |
| tools.test_job_viewer | P | W167896 | Temporary/read-only store views and composed TwoBoundJobs/capacity fixtures; no interactive terminal/provider. |
| tools.test_live_ab | P | W71879 | Temporary document-rendering subprocess and source mismatch refusal before mocked engine access. Credential path is emitted data, not a credential read. |
| tools.test_managed_integration | P | W161230 | Real Git in TemporaryDirectory; fake execution/target/materializer/adapter boundaries. |
| tools.test_managed_preparation | P | W161230 | Temporary real Git and local worker Python; fake external execution; worker sys.path import. |
| tools.test_scheduler_trace | P | W103525 | Existing fixed deterministic composed Job/Worker/Authority schedules over private roots, fake execution; does not select parked stress campaign. |
| tools.test_stage_execution_hardening | P | W103950 | ServingCase private resources, fake Engine, failure/cleanup injection. |
| tools.test_stage_execution_status_hardening | P | W129844 | One class, private fixture; optional BATON_STATUS_HARDENING_EVIDENCE output needs an unset or per-run destination. |
| tools.test_standalone_ab | P | W71879 | Synthetic provider is local Python over copied fixtures and temporary Git; model-shaped arguments simulated. Docker scenario stays operator-only. |

## Shared state and scheduling conditions

Preserve one module per collector child and fresh interpreter per TestCase shard.
sys.path mutations, module caches, secrets helpers and subprocess mocks are not
safe grounds for in-process concurrent cases. Preserve existing METHOD_SPLIT;
keep methods of every newly registered class sequential. No proposed P module
defines setUpClass/tearDownClass/setUpModule/tearDownModule. Imported/inherited
fixtures and custom load_tests require collection fidelity: the budget module
must never enroll DeadlineDocker as a runnable class.

Shared fixtures inspected: tests/integration/fixtures.py,
tests/job_manager/fixtures.py, tests/manager/test_attempts.py,
tests/manager/disk_roots.py, tests/tools/test_single_worker.py and
tests/tools/test_stage_execution.py. Their roots/stores are per case; Engine is
a fake boundary. disk_roots uses unique mkdtemp children even under a shared
BATON_V12_DISK_ROOT parent. Its disk-backed filesystem requirement remains real.

Leave BATON_STATUS_HARDENING_EVIDENCE unset or use a unique per-run destination.
One class shard prevents within-run collisions; serial registration would not
cure two independent invocations writing the same destination. Real Git/Python
timeout cases cost wall time and require a sensible enclosing timeout and
process cleanup. Some existing managed-integration helper subprocess calls lack
explicit timeouts; no helper fix or runtime cleanup proof is claimed here.

## Ownership and current boundaries

M168793 requested coordination; M168816 on T168703 is the full answer. W161230
retains eight rows above and asserts no ownership of either shared runner path.
SLICE2-SCOPE-165724.md selects nine source/eight test paths; accepted slice1
candidate165182 retains reconciliation_worker and managed_integration. The
already registered test_stage_execution.py is a moving W161230 fixture, distinct
from the missing hardening modules. The implementer will not pre-empt shared
runner integration. No interruption or dependency was requested.

owner-states-168782.json preserves canonical detail snapshots and bindings:
W161230 active review; W156162 blocked; W103525 parked; W103950 blocked;
W167896, W133117, W129844, W71879, W32577 and W9707 closed at observation.
These are snapshots, not assignments. Revalidate active leaves and shared
fixtures before implementation. Closed W32577 does not grant future engine
execution; registering existing scheduler regressions does not resume deferred
stress/performance/priority work.

Proposed total: 97 parallel, unchanged 19 serial, 1 supervised-only = 117 exactly
once. No missing module is proposed as ordinary serial. Existing serial entries
already include engine workloads; their execution is outside this assignment.

## Operational observations and limits

A candidate documentation read of v12/python/README.md returned ENOENT. That path
does not exist and is not a required assignment input. Actual recipe behavior
was read in v12/python/justfile. Required policy and bound dossier were readable.

No tests were imported, collected or executed; no engine/model, package install
or image operation occurred. Source-supported classification and no-import
registry validation do not establish parallel runtime acceptance.
