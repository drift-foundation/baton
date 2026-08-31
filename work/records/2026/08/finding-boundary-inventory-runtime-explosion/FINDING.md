# Make the boundary inventory finish in bounded time

Work: W54182

## Classification

**Confirmed defect.** The exhaustive boundary-inventory test has grown into a
serial, resource-accumulating meta-test whose runtime is large enough to wedge
ordinary implementation turns and obscure the useful failure report.

## Discovery

Discovered while W52800 verified the runtime credential-slot correction. The
credential change's relevant 1,046 non-inventory tests completed successfully
in 8.861 seconds. The boundary inventory instead completed one run in
2,376.290 seconds with 22 failures and 5 errors. A later retry did not finish
before the ACP bridge's 7,200,000 ms managed-turn deadline destroyed the agent
process domain and left W52800 requiring recover-operator release.

This Work is deliberately independent and non-gating for W52800, W51487 and
the first useful dogfood path. Its purpose is to remove the test-infrastructure
failure without turning that correction into another prerequisite for the
credential fix it delayed.

## Confirmed cause

`EveryProbeProvesItArrived.test_every_declared_probe_reaches_its_named_boundary`
currently has 549 declared probes. For every probe, it manually invokes
`setUp()`, registers another temporary-directory and SQLite cleanup for the end
of the enclosing test, and rebuilds the complete probe dictionary. The loop
therefore retains hundreds of fixtures and repeats work proportional to the
whole inventory for each inventory member.

Measured on the discovery tree, constructing `all_probes()` once takes about
1.15 seconds. Reconstructing it for 549 probes accounts for roughly 10.5
minutes before the probes' own setup and execution. The inventory helpers also
repeat package walks, file reads and AST parsing rather than sharing an
immutable source snapshot. Resource warnings for unclosed SQLite connections
appear during the run, consistent with cleanups being deferred while `self`
is repeatedly overwritten.

The inventory's correctness failures are real output to review separately;
they do not justify the runtime explosion. The completed discovery run named,
among other drift, unowned receiving entries, orphan boundary calls and
persisted columns absent from the tracked universe. This defect must not make
those assertions weaker or declare the drift away merely to turn the suite
green.

## Direction

- Parse the manager source into one immutable snapshot per run rather than
  repeatedly walking and parsing the package.
- Construct the declared probe catalog once for the relevant test boundary.
- Give each probe an isolated fixture whose cleanup runs immediately after
  that probe; never call `setUp()` repeatedly on one `TestCase` while deferring
  every cleanup.
- Preserve one independently reported subtest/case per probe and deterministic
  failure diagnostics.
- Measure first, then consider generated cases, sharding or bounded parallel
  execution only if removing duplicated work and fixture accumulation is not
  sufficient.
- Keep the semantic inventory, ownership and probe assertions unchanged.

## Acceptance boundary

- The same discovery-tree inventory verdict and distinct failure categories
  remain visible after the performance correction.
- A probe cannot observe another probe's store, files or mutable fixture state.
- Temporary stores, SQLite connections and process resources are reclaimed per
  probe, including when the probe fails.
- Package source parsing and probe-catalog construction are demonstrably
  bounded rather than repeated once per probe.
- Focused regression proves the old repeated-setup/rebuild shape cannot return.
- The completed W52800 run — 2,376.290 seconds on this host, with its recorded
  verdict and resource evidence — IS the accepted pre-correction baseline. It
  is not reconstructed and run again. The after measurement uses the corrected
  current tree on the same host; bounded representative measurements may
  isolate the causal improvement without executing the old unbounded driver.
  The initial target is at least a tenfold speedup and completion within five
  minutes on the current development host; implementation must report if
  correctness-preserving measurement refutes that target rather than weakening
  coverage or waiting through another old-shape run.

## Operating decision — 2026-08-31

A verification campaign that can monopolize one Handler for an extended
period is not one opaque test command inside an implementation Job. Break it
into named, independently runnable and time-bounded slices. When a slice is a
substantial deliverable or needs its own diagnosis, correction or review, give
it visible contained Baton Work with its own acceptance result. The aggregate
suite is a later integration gate after the slices are green; it is not
repeated after every local edit and it does not keep unrelated focused work
claimed while a known infrastructure defect consumes the turn.

If an aggregate run has already produced a failure, stop treating its
remaining wall time as useful verification. Preserve the partial evidence,
route each independently actionable failure to bounded Work, and free the
Handler. This decision generalizes the two-stage verification cadence in
`docs/EFFECTIVE-BATON.md`; W54182 owns applying it to the boundary inventory.

**Supervision clarification, 2026-08-31.** “Before/after” does not authorize a
new execution of the pre-correction inventory. Two attempts to reconstruct and
run that roughly 40-minute baseline were terminated during W54182. Use the
completed W52800 measurement above. Any further pre-correction experiment is a
small, hard-bounded sample that cannot become the old aggregate under another
name.

## Reviewer revalidation — 2026-08-31

### Current execution shape

**Confirmed.** The expensive driver is at
`v12/python/tests/manager/test_boundary_inventory.py`, in
`EveryProbeProvesItArrived.test_every_declared_probe_reaches_its_named_boundary`.
`unittest` has already called `BoundaryCase.setUp()` once before entering the
test. The driver then calls `self.setUp()` once for each of 549 keys, but never
calls `doCleanups()` itself. Each setup adds both `TemporaryDirectory.cleanup`
and `ControlStore.close` to the same `TestCase` cleanup stack. All 1,100
callbacks therefore wait for the enclosing test to end while every setup
overwrites `self._root`, `self.store`, `self.session` and `self.port`.

A bounded reproduction made the accumulation visible without running the
40-minute test: process file descriptors grew from 4 before setup, to 7 after
one setup, to 64 after twenty setups. The cleanup stack then contained forty
callbacks. One `doCleanups()` returned the count to 4. The running discovery
retry was independently observed after 12:51 elapsed at 99.9% CPU, 320,412 KiB
resident, 337,944 KiB high-water and an allocated fd table of 2,048 entries.
It had emitted a `ResourceWarning` for an unclosed SQLite connection.

### Repeated discovery cost

**Confirmed.** On the current dirty tree, one isolated, properly cleaned
fixture produced 549 probes. The measurements below used the same interpreter
and import path as the inventory (`cd v12/python && PYTHONPATH=src python3`):

- `setUp()`: 0.003 seconds;
- `all_probes()`: 1.160–1.162 seconds;
- `receiving_entries()`: 0.387 seconds for 968 entries; and
- `doCleanups()`: below the three-decimal measurement resolution.

Instrumenting `_sources()` during one `all_probes()` call counted nine source
walks and 189 file parses (21 manager modules parsed nine times). The driver
calls `all_probes()` once to obtain its sorted keys and again inside each of
the 549 iterations. At the measured rate that is about 639 seconds and 103,950
AST parses just to reconstruct catalogs.

The repetition is not limited to the probe builder. One
`owning_validators()` call took 0.324 seconds, walked sources twice and parsed
42 files. `layer_labels()` calls `owning_validators()` afresh, so tests that
ask it about every entry multiply the same pure discovery work by the entry
count.

Caching only the parsed 21-file source tuple reduced a catalog from 1.162 to
0.893 seconds, which is insufficient. Caching the derived 968-entry
`receiving_entries()` result reduced ten catalog builds together to 0.004
seconds while preserving the 549-key result. The implementation boundary must
therefore memoize the pure derived inventories as well as the source snapshot;
source parsing alone does not meet this record's target.

### Catalog-lifetime clarification

**Confirmed clarification of the earlier Direction.** “Construct the declared
probe catalog once” must not be implemented by retaining today's
`all_probes()` dictionary across fixtures. Closure inspection of one current
catalog found direct captures of 80 `ControlStore` objects, 24
`CredentialHome` objects and 40 `AuthorityPort` objects, in addition to 361
closures bound to the `EveryProbeProvesItArrived` instance. Such a retained
catalog would either reuse one probe's mutable store or point later probes at
resources already closed by prompt cleanup.

The safe small correction is to compute the immutable *key universe* once,
then either:

1. instantiate the fixture-bound driver catalog inside each fresh setup after
   memoizing pure discovery (the measured derived cache makes this effectively
   free), or
2. deliberately refactor catalog values into fixture-independent factories
   and instantiate each factory against the current fixture.

The first is the smaller patch. In either form, put `setUp()` and probe
execution inside a `try` whose `finally` calls `doCleanups()`, including setup
failure, and discard the fixture-bound catalog before the next probe. Cleanup
of the framework-created initial fixture must also be explicit before the
per-probe loop begins.

### Exact patch and regression boundary

**Proposed for implementer revalidation.** Keep the change test-local in
`test_boundary_inventory.py`:

- introduce one run-stable source snapshot and cache the pure discovery
  projections used repeatedly (`_crossings`, `receiving_entries`,
  `owning_validators`, `propagated_owners`, and the independent column scan as
  current call paths require); expose immutable values or defensive copies so
  a caller cannot poison later assertions;
- retain the existing independent discovery mechanisms: in particular do not
  derive `columns_read()` from `receiving_entries()` or the probe catalog;
- preserve the 549 sorted `(entry, label)` subtests, full-label containment
  assertion, refusal assertion, and current failure categories byte-for-byte
  apart from timing/resource details; and
- pair every manually created fixture with immediate cleanup in `finally`.

Focused regressions should count source parsing and derived computation across
repeated callers, prove cached results cannot be mutated, prove two probes see
different stores and roots, and prove a deliberately failing probe still
closes its SQLite connection and removes its temporary directory before the
next probe. A regression that merely checks the eventual framework cleanup is
not sufficient: that is the leaking behavior measured above.

## Implementer revalidation — 2026-08-31 (baton.claude, W54182 claim)

Every claim in the reviewer sections above was re-checked against the working
tree before any edit. All of them held.

**Confirmed against the current tree.** The driver at
`v12/python/tests/manager/test_boundary_inventory.py` still called `setUp()`
once per key without ever calling `doCleanups()`, and still rebuilt the whole
catalog inside the loop. `_sources()` was still a generator, so each projection
re-walked and re-parsed the package. Measured here before the edit, on this host
and this tree, with
`work/records/2026/08/finding-boundary-inventory-runtime-explosion/measure_probe_driver.py`:
one `all_probes()` took 1.118 s and 441 `ast.parse` calls had accumulated by the
time the first catalog existed; twenty probes in the driver's own loop shape
took 22.601 s (1.130 s each), left a cleanup stack of 42 and took the process
from 4 file descriptors to 87. The 549-key loop extrapolates to 620.410 s.

**Clarification — a shared parse is not a shared mechanism.** The reviewer
required that the independent column scan stay independent, and specifically
that `columns_read()` not be derived from `receiving_entries()` or from the
probe catalog. It is not: it still performs its own flat `x["<name>"]` walk
against the table contracts and shares nothing with the origin tracking but the
PARSED SOURCE TEXT, which was always the same bytes read twice. Memoising
`_sources()` removes a duplicated `ast.parse`, not a second opinion. The
anti-circularity property the scan exists for -- that a universe which stops
seeing columns is caught by something that does not use the universe -- is
unchanged, and `test_the_universe_sees_every_persisted_column_that_is_read`
still compares the two.

**Catalog lifetime, as implemented.** Option 1 of the reviewer's clarification
was taken: the immutable KEY universe is computed once and the fixture-bound
catalog is rebuilt inside each fresh fixture. Nothing retains a catalog across
fixtures, so the eighty stores, twenty-four credential homes and forty ports its
closures capture die with the fixture that made them.

**Supersedes nothing.** No earlier ruling in this record was contradicted; the
Direction and the Acceptance boundary are implemented as written.
