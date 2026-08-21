# Finding: clean up v12 test-owned temporary fixtures

Canonical Baton Work: W1466.

## Forwarded — 2026-08-21

This independently scheduled cleanup is promoted to top-level Work W1478 at
`work/records/2026/08/finding-v12-test-fixture-leaks/`. W1466 is closed
cancelled without implementation. Continue from W1478; this path remains
immutable forwarding history.

## Observed — 2026-08-21

The v12 tests create many directories with `mkdtempSync` and leave them under
the host temporary directory after the test process exits. The shared
`scratch()` helpers are used roughly three times per placement-suite run and
more than fifty times per unit-suite run. Repeated gates therefore accumulate
`v12poc-placement-*` and `v12poc-test-*` directories without bound.

This predates W1395 and is outside its narrow correction. W1395's new
`v12poc-entry-unowned-*` fixture does clean itself in `finally`.

## Proposed correction

Make each test file own one or more bounded temporary roots and register
reliable cleanup that runs after success or assertion failure. Preserve tests
that deliberately remove or retain a path as part of their assertion, and do
not introduce cleanup of fixed, ambient, or merely name-matching paths.

## Acceptance boundary

- A complete `npm test` run leaves no new `v12poc-placement-*` or
  `v12poc-test-*` directories.
- Cleanup removes only roots created by that test process.
- Failure-path and ownership assertions keep their present semantics.
- The complete self-contained v12 gate remains green.
