# Progress

## 2026-08-31 — baton.claude (impl), W54182 claim

Implemented plan items 3 and 4. The change is entirely test-local, in
`v12/python/tests/manager/test_boundary_inventory.py`; no `src/` file and no
existing assertion was touched.

### What changed

**One parsed source snapshot, and memoised pure projections.** `_sources()` was
a generator, so every projection re-walked and re-parsed the package.  It now
returns one immutable `tuple` of `(path, tree)` under `functools.cache`, and the
pure derived projections are cached with it: `_helper_returns()` (the
`_returned_origins` fixpoint, previously recomputed by three callers),
`_crossings()`, `receiving_entries()`, `columns_read()`, `owning_validators()`
and `propagated_owners()`. `MEMOISED` names all seven in one tuple, which is
what the boundedness regression clears and counts.

Every cached answer is handed out immutable — a `tuple`, a `frozenset`, or a
`types.MappingProxyType` whose values are `frozenset`s — so a shared projection
cannot be edited by one assertion under a later one.

**The probe driver's fixture lifetime.**
`EveryProbeProvesItArrived.test_every_declared_probe_reaches_its_named_boundary`
now takes the sorted KEY universe once, releases the fixture `unittest` itself
opened before entering the loop, and then per probe opens one fixture inside a
`try` whose `finally` calls `doCleanups()` — so a probe's temporary directory
and SQLite connection are reclaimed immediately, including when the probe fails
and when `setUp()` itself fails. The fixture-bound catalog is rebuilt inside
each fresh fixture rather than retained, because its closures capture stores,
credential homes and ports (reviewer clarification, option 1).

**Two new focused regression classes**, both of which fail against the
pre-correction shape (mutation-proved below):
`TheDiscoveryProjectionsAreBoundedAndImmutable` and `TheProbeDriverIsBounded`.

### Bounded focused evidence, with the exact commands

All from `v12/python` on this host and tree. `MEASURE` is
`../../work/records/2026/08/finding-boundary-inventory-runtime-explosion/measure_probe_driver.py`,
which never runs the whole driver: it times the projections and one catalog,
then runs the first twenty keys through the driver's loop shape.

BEFORE, measured with the pre-correction file still in place —
`PYTHONPATH=src python3 $MEASURE 20`:

| measurement | before |
| --- | --- |
| `receiving_entries()` (968 entries) | 0.366 s, and 0.387 s again |
| `owning_validators()` | 0.307 s |
| `propagated_owners()` | 0.271 s |
| `columns_read()` | 0.044 s |
| `_crossings()` | 0.044 s |
| `all_probes()` (549 probes) | 1.118 s |
| `ast.parse` calls to reach one catalog | 441 |
| 20 probes in the driver's loop shape | 22.601 s (1.130 s each) |
| cleanup stack after those 20 probes | 42 |
| process file descriptors | 4 → 87 |
| 549 probes, extrapolated | 620.410 s |

AFTER, same command and same script, whose loop now mirrors the shipped one:

| measurement | after |
| --- | --- |
| `receiving_entries()` (968 entries) | 0.306 s, then 0.000 s |
| `owning_validators()` | 0.097 s |
| `propagated_owners()` | 0.082 s |
| `columns_read()` | 0.017 s |
| `_crossings()` | 0.000 s |
| `all_probes()` (549 probes) | 0.003 s |
| `ast.parse` calls to reach one catalog | 21 |
| 20 probes in the driver's loop shape | 0.097 s (0.005 s each) |
| cleanup stack after those 20 probes | 0 |
| process file descriptors | 4 → 4 |
| 549 probes, extrapolated | 2.668 s |

The whole probe class, which is the acceptance run this Work owns —
`PYTHONPATH=src python3 -m unittest
tests.manager.test_boundary_inventory.EveryProbeProvesItArrived`:

    Ran 5 tests in 2.077s      real 0m2.303s

`test_every_declared_probe_reaches_its_named_boundary` PASSES: all 549 probes
reach their named boundary. The two failures in that run are the inventory's own
drift, unchanged by this correction and reported below.

The new regressions — `PYTHONPATH=src python3 -m unittest
tests.manager.test_boundary_inventory.TheDiscoveryProjectionsAreBoundedAndImmutable
tests.manager.test_boundary_inventory.TheProbeDriverIsBounded`:

    Ran 9 tests in 1.069s  OK   real 0m1.303s

### The regressions were proved against the defect, not only against the fix

A regression that passes both before and after proves nothing. Both were run
against deliberately reverted shapes, then the correction was restored:

- driver loop reverted to the pre-correction shape (one `setUp()` per key, no
  `doCleanups()`): `TheProbeDriverIsBounded` → `Ran 5 tests in 0.044s,
  FAILED (failures=6)`. `test_nothing_accumulates_with_the_probe_count`
  reported live fixtures `[2, 3, 4, …, 13]` against the required `[1] * 12`.
- `_sources()` un-memoised: `TheDiscoveryProjectionsAreBoundedAndImmutable` →
  `FAILED (failures=1)`, counting 126 `ast.parse` calls where 21 modules exist.

### The before measurement, and the aggregate run

I reconstructed a pre-correction copy of the module in `/tmp/w54182-baseline/`
to produce a whole-module before verdict. Three attempts to run it were killed
by the execution environment at roughly 60–90 seconds each, and
`baton.prompt` then intervened (poke 54758): do not restart it, use the already
recorded 2,376.290-second W52800 run as the before measurement, and continue
with bounded focused regressions only. That ruling is followed. The
reconstruction remains at `/tmp/w54182-baseline/` — script
`build_baseline.py`, module
`tree/v12/python/tests/manager/baseline_boundary_inventory.py` — for the
operator rather than being cleaned up or rerun.

So the before/after wall time this record carries is: 2,376.290 s recorded for
the boundary inventory during W52800, against 2.303 s for the whole
`EveryProbeProvesItArrived` class now, with the driver's own 549-probe loop
measured at 0.005 s per probe. That is well past the record's tenfold target and
inside its five-minute bound. No aggregate module or suite run has been made
under this claim; that is the later integration gate, not an implementation
command.

### The inventory's own drift, unchanged and unweakened

Two correctness failures survive in `EveryProbeProvesItArrived`, and they are
the same category the finding said must not be declared away:
`test_every_owned_entry_has_exactly_one_probe` and
`test_the_missing_probe_check_can_actually_fail`, both reporting 46 entries that
are owned and never probed — the `handshake.py:certified_agent_session_profile`
profile-body members, `intake.py:retentions_of` retention columns and the rest.
Nothing in this correction touched those assertions, their inputs, or the
entries they name.

They are now **W54802**, filed to `baton.bug` with all 46 entries listed by
site, the 3 probed-but-unowned ones, and a 2.3-second reproduction — so the
drift is bounded, separately schedulable Work rather than something only a long
aggregate run reports. It is filed as Observed and not diagnosed: the clustering
by module is consistent with probe-table drift behind recent feature work, and I
did not investigate further, because enrichment and priority are the reviewer's.

### Plan item 5's slicing clause, revalidated

The named, independently runnable, time-bounded slices item 5 asks for already
exist: W9707's `v12/python/tools/parallel_test.py` shards this suite by
`TestCase` class in a fresh interpreter per shard, and splits the two
whole-universe scan classes — `EveryReceivingEntryHasOneOwner` and
`EveryProbeProvesItArrived` — one test METHOD per shard, precisely because the
baseline showed this module dominating the wall clock. Its registries are
module-level and check their own completeness, so the two classes added here
need no registry entry and ship as one shard each. With the driver at seconds,
the inventory needs no slicing of its own; what item 5 still demanded was the
routing above, and that is done.

### State

Plan items 3, 4 and 5 are done, and item 6 is answered within the bounds ruled
at poke 54758. Item 7 is open: passing to review, not closing.
