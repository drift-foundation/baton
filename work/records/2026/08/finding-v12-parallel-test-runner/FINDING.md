# Finding: run safe v12 tests across available cores

## Observed — 2026-08-25

The v12 Python verification path invokes one standard-library `unittest`
process at a time for focused tests, boundary/dependency/sweep checks, full
discovery, installed-layout discovery and container/build gates. On the
16-core development host this leaves most CPUs idle during a large and growing
test campaign. Repeated ACP log updates are progress reports for the same
process, not concurrent workers.

## Confirmed decision — 2026-08-25

Provide a dedicated v12 test runner and `just` entry point with two explicit
phases:

1. Pure manager/unit test shards run concurrently, defaulting to the host's
   available CPU count and accepting a bounded operator override.
2. Docker, packaging, installed-layout, fixed-name/shared-resource and cleanup
   tests run serially through an explicit registry.

Parallelism is a property of the test harness, never a product/runtime
dependency. Do not apply an undifferentiated `pytest -n` or shell fan-out to
the whole tree: every parallel shard must own its temporary paths and stores,
and every test with process-global, build-tree, image, container, socket or
external-resource effects remains serial until independently proven safe.

## Acceptance

- One documented v12 command runs the complete parallel and serial gate.
- The default worker count uses available CPUs; an operator can lower it
  without editing files.
- Parallel collection is deterministic, failures propagate reliably, and the
  final summary distinguishes parallel from serial results.
- The serial registry is visible, reviewed and protected by tests so a new
  unsafe module cannot silently enter the parallel phase.
- Repeated and failure-path runs leave no worker processes, temporary stores,
  containers, images or build artifacts owned by the runner.
- Evidence compares elapsed time and CPU utilization with the serial baseline
  on the 16-core host without weakening any existing assertion or gate.

## Reviewer inventory and implementation boundary — 2026-08-25

### Observed host and baseline

The development host has 16 physical cores and 32 online/affinity-visible
logical CPUs. Python 3.13 reports `os.process_cpu_count() == 32`; that is the
correct default because it reflects the CPUs available to this process rather
than restating physical topology. The runner caps the default at the number of
ready shards. The operator override may LOWER that value only: a whole number
from 1 through the detected default.

The current pure serial phase ran 1,070 tests from 28 modules in 423.54 seconds
with 422.65 user seconds, 1.38 system seconds, 100% aggregate CPU and 186,824
KiB maximum RSS. It reported the current tree's 12 failures and one skip. Exact
scope and interpretation are in
`evidence/serial-pure-baseline-2026-08-25.txt`. This is baseline evidence, not a
green claim.

### Confirmed parallel-safe source registry

Each shard runs in a fresh interpreter process. That isolation is part of the
safety proof: module `sys.path`/environment state, live-secret registries,
SQLite handles, mocks and worker-entry counters never cross shards. Every
stateful test below creates its own `TemporaryDirectory`; the real-process race
tests create children and stores below that per-test root and already wait for
their children.

All eight authority modules are parallel-safe:

```text
tests.authority.test_assignment
tests.authority.test_boundary
tests.authority.test_catalog
tests.authority.test_contract
tests.authority.test_identity
tests.authority.test_operations
tests.authority.test_session
tests.authority.test_store
```

These twenty manager modules are parallel-safe:

```text
tests.manager.test_attempts
tests.manager.test_boundary_inventory
tests.manager.test_canonical
tests.manager.test_contracts_inventory
tests.manager.test_dependencies
tests.manager.test_frozen
tests.manager.test_handshake
tests.manager.test_interrogation
tests.manager.test_manifest_rules
tests.manager.test_oci
tests.manager.test_offers
tests.manager.test_output
tests.manager.test_pod
tests.manager.test_secrets
tests.manager.test_sessions
tests.manager.test_store
tests.manager.test_text_sweep
tests.manager.test_validate
tests.manager.test_worker_image
tests.manager.test_workspaces
```

The ordinary unit is one concrete `unittest.TestCase` class per subprocess,
collected by the standard loader and sorted by full dotted id. Two aggregate
classes in `test_boundary_inventory` are split one test method per subprocess:
`EveryReceivingEntryHasOneOwner` and `EveryProbeProvesItArrived`. The baseline
showed those whole-universe scans dominating wall time; leaving either as one
class shard would preserve the single-CPU long pole. No source test outside
`test_worker_container` has `setUpModule`, `tearDownModule`, `setUpClass` or
`tearDownClass`; the method split therefore bypasses no shared fixture.

### Mandatory serial registry

`tests.manager.test_worker_container` is one indivisible source serial module.
It owns the Docker daemon, suite-global `baton-w6633-test` names, image builds,
container cleanup and class fixtures. Its two daemon-free source assertions do
not justify importing half the module into the parallel phase; split them into
a separate reviewed module in a later Work if that optimization is wanted.

The locked dependency resolution, package build/install and complete
installed-layout discovery are one later serial stage through the existing
`just build` recipe. It owns a disposable environment, build/install state,
network/index resolution and a second complete test replay. It is never run
concurrently with the source phase or Docker gate. The Python version check is
also a serial prerequisite.

### Proposed runner boundary

Add one repository tool under `v12/python/tools/` and keep it standard-library
only. A collector child imports one registered pure module, uses
`unittest.TestLoader`, and returns exact test ids; the parent never imports test
modules. The parent partitions ids by concrete class, applies the two explicit
method-split exceptions, sorts shard ids, and schedules fresh interpreter
children up to the bounded job count.

Each child captures its own unittest result. Completion order never determines
presentation: the parent drains every scheduled parallel shard, then prints
failures and summaries in sorted shard order. A failed parallel phase prevents
the Docker and installed-layout phases, preserving the current fail-fast phase
ordering, but it does not abandon sibling parallel shards halfway through.

On interrupt or internal runner failure, the parent terminates every live child
process group, waits, escalates only to kill its own remaining children, and
removes its disposable result directory. No shell fan-out, shared log path or
persistent worker pool is part of the design.

Add dedicated `parallel-test` and `parallel-gate` recipes; do not replace the
canonical `gate` recipe until independent review. `parallel-gate` runs the
version prerequisite, the runner's parallel source phase, the explicit source
serial registry and existing locked `build` stage in that order. An optional
recipe argument is passed as the bounded jobs override, so `just parallel-gate
8` is the documented lowering mechanism.

### Required regressions

The runner's tests use disposable fake module trees and prove: deterministic
collection/output despite inverted completion order; exact module-registry
coverage with unknown modules failing closed; no duplicate/missing test ids;
job default and lower-only override bounds; parallel failure propagation;
serial work never overlapping parallel work or another serial item; signal and
failure cleanup of descendant processes and result directories; and jobs=1
versus default producing identical collected ids and outcomes.
