# Bounded Podman removal — owner decision T384870 M384888 (2026-10-30)

Author: K (interactive copilot under the owner-held claim E384883).
Scope: the Podman-SPECIFIC surface; shared OCI abstractions used by Docker are
unchanged; historical Work records and evidence untouched.

## Removed

Product (`v12/python/src/baton_v12/worker_manager/oci.py`):
- `ENGINES = ("docker", "podman")` → `("docker",)`; "podman" is now refused as an engine name like any other.
- `_ABSENT_FORMS["podman"]` (Podman's two "no such container" phrasings).
- Module header no longer claims Podman compatibility.
- Kept, as shared runtime-neutral readers the Docker adapter still goes through:
  `_one_of` (several spellings of one fact), `_labels_of` tolerance of a
  comma-joined label string, the canonical-digest tolerance in `_image`. Their
  comments still mention Podman as the origin of a spelling; they are code
  comments about history, not documentation of support.

Tests (nine Podman-variant engine classes, 98 test ids, all previously skipping
at `setUpClass` or in `setUp` on this host):
- tests/manager/test_custody_engine.py: `PodmanCustody` (11)
- tests/manager/test_ended_runtime_adoption.py: `PodmanEndedRuntimeAdoption` (8)
- tests/manager/test_input_delivery.py: `PodmanDelivery` (5), `PodmanConfiguredGroup` (19)
- tests/manager/test_lifecycle_composition.py: `PodmanComposition` (32)
- tests/manager/test_negative_race_endings.py: `PodmanNegativeEndings` (5)
- tests/manager/test_oci_engine.py: `PodmanRunsWhatTheAdapterComposes` (5); the
  engine-coverage test now asserts the Docker case alone covers `ENGINES`.
- tests/manager/test_refused_session_engine.py: `PodmanRefusedSession` (8)
- tests/manager/test_worker_entry_engine.py: `PodmanWorkerEntry` (5)
- tests/manager/test_oci.py: the Podman golden listing branch, the Podman
  inspect vector (now Docker), the Podman `ImageID` spelling case; "podman"
  added to the refused engine names. The `/run/podman/podman.sock` mount
  refusal stays (a host path is refused whatever it is).
- tests/manager/test_verifier_topology.py: three adapters composed with
  "podman" now use "docker" (the tests are about topology, not the engine).
- tests/manager/test_authoring_enforcement.py: the second engine name in the
  multiple-engine refusal test is now "other-engine".
- tests/tools/test_parallel_runner.py: fake skip reasons no longer say podman.

Documentation: `v12/python/DEPLOYMENT.md` — the `engine` table value is
`docker`; the "Podman half of the matrix" paragraph and the section "Engines:
Docker is certified, Podman is not" are replaced by "Engines: Docker only",
which points at the historical evidence rather than repeating it.
`v12/python/tests/manager/test_lifecycle_composition.py` and
`test_worker_entry_engine.py` module docstrings record the removal.
Comments in `source_boundary.py:894`, `custody.py:828`, `test_custody_engine.py:43`
and inside `oci.py` still name Podman as the origin of a spelling; left as
historical code comments.

## Coverage after removal

The Docker halves of every matrix are untouched (the `Docker*` classes in the
same modules). Required Docker coverage proof: `just test-group manager-engine`
run after the removal, log `b1-2026-10-30-manager-engine-group.log` beside
this file: collected 236 = executed 236, passed 198, required skipped 4
(initial-access, prerequisites pending), failed 27, errors 7, no fixture
events, unaccounted 0; the failing id set is identical to the B0 ledger's for
these 17 modules (34 ids), so nothing Docker-side changed. Pure modules touched: `just test-one tests.manager.test_oci
tests.manager.test_verifier_topology tests.manager.test_authoring_enforcement
tests.manager.test_importing_fixture tests.tools.test_parallel_runner` — the
only failures are test_authoring_enforcement's eight C7 baseline failures,
identical by id to the B0 ledger.

Accounting effect: the 8 class-level podman fixture skips (across 7 modules) and 5 per-test podman
skips of the B0 baseline (98 never-started or skipped tests) no longer exist;
`OPTIONAL_SKIPS` holds only the two owner-classified proofs.
