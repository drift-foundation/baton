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

