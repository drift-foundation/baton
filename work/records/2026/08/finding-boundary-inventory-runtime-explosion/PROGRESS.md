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

## 2026-08-31 — second implementer round (`baton.claude`, W54182 impl claim)

Answering `review-2026-08-31T16-16-32Z.md` and the supervision note at message
54907. Both findings are closed.

### [P1] The leaked SQLite handle — closed as W54881

The child is closed satisfying. `ControlStore.open` now proves the clock inside
its close-on-error region, so a refused clock answer closes the connection
before the exception escapes, and the prior ruling that a configured clock's
own exception propagates unchanged is preserved by the handler that re-raises
it. The 549-probe driver no longer emits an unclosed database. Full account:
`findings/finding-refused-store-open-clock-leak/PROGRESS.md`.

### [P2] The immutable-source claim was false, and is now narrow and measured

You were right and I overclaimed. `_sources()` returns an immutable TUPLE whose
members are `ast.Module` objects, and an AST node is mutable — your
reproduction (clear one module's `tree.body`, recompute a projection, lose the
live `run` crossing) is real. Three things were saying more than that: the
header comment above the projections, the `_sources()` docstring, and
`test_no_caller_can_poison_a_cached_projection`, whose name promised the strong
property while its `_sources()` assertion only checked the outer container's
type.

Corrected by taking BOTH halves the supervision note offered rather than
choosing one.

**The text is narrowed.** The header now separates the two cases: the derived
projections are immutable VALUES whose members are strings and tuples of
strings, so handing the cached object out is safe; the source snapshot is an
immutable container of mutable nodes, held safe by an INVARIANT this file owns
— every walker here only reads. The `_sources()` docstring says the same and
names the test that holds the rule. The old case is renamed
`test_no_caller_can_poison_a_cached_derived_projection` and its `_sources()`
assertion moved out, so its name and its content agree.

**And the invariant is measured rather than promised.**
`test_the_shared_trees_are_never_mutated_by_a_projection` fingerprints every
cached tree with `ast.dump`, clears and recomputes all five projections, and
requires the fingerprints unchanged. `ast.dump` renders the node graph, so a
lost statement, a rebound call target and an attribute assigned in place all
change it.

**The detector is proved twice, in both directions.**
`test_the_mutation_check_can_actually_notice` stages your exact hazard — pops a
statement from `oci.py`'s body — requires the fingerprint to notice, puts it
back, and requires the fingerprint to return to what it was; no projection runs
while the tree is short. And separately, with `columns_read` deliberately
edited to `tree.body.pop()` on every module it walks,
`test_the_shared_trees_are_never_mutated_by_a_projection` fails with "a
projection edited the tree it was given". Restored and green.

This is the smallest actual protection rather than a redesign: no deep copy, no
re-parse, no change to how the cache is shared.

### The focused gates you named, and nothing else

No aggregate was run, as instructed.

    PYTHONPATH=src python3 -W error::ResourceWarning -m unittest \
      tests.manager.test_boundary_inventory.TheDiscoveryProjectionsAreBoundedAndImmutable \
      tests.manager.test_boundary_inventory.TheProbeDriverIsBounded
    -> Ran 11 tests in 1.581s, OK        (9 before; the two new ones are P2's)

    PYTHONPATH=src PYTHONTRACEMALLOC=10 python3 -W error::ResourceWarning \
      -m unittest tests.manager.test_boundary_inventory\
.EveryProbeProvesItArrived.test_every_declared_probe_reaches_its_named_boundary
    -> Ran 1 test in 24.863s, OK, and NO unclosed-database warning

    PYTHONPATH=src python3 -W error::ResourceWarning -m unittest \
      tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner \
      tests.manager.test_boundary_inventory.EveryProbeProvesItArrived
    -> Ran 17 tests in 2.155s, FAILED (failures=5)

`-W error::ResourceWarning` throughout, so a surviving warning fails the run
rather than needing to be spotted. The tracing run's 24.863 s is
`PYTHONTRACEMALLOC=10`; the same method without it is 1.967 s.

### Diff semantics: the verdict is the same five failures, and none is mine

The 17-test slice is the inventory's two whole-universe scan classes, and its
five failures are exactly the pre-existing semantic drift, unchanged in kind
and in membership by this correction:

- `test_every_receiving_entry_has_an_owning_validator`,
  `test_every_boundary_call_belongs_to_an_entry_or_is_declared` and
  `test_the_universe_sees_every_persisted_column_that_is_read` — the
  unowned-entry family, owned by W48697;
- `test_every_owned_entry_has_exactly_one_probe` and
  `test_the_missing_probe_check_can_actually_fail` — the 46 owned-never-probed
  entries, owned by W54802.

`test_every_declared_probe_reaches_its_named_boundary` passes: all 549 probes
reach their named boundary. Retained baseline unchanged: the recorded
2,376.290-second, 22-failure, 5-error W52800 run, not re-measured.

### State

Both review findings closed. Awaiting review; passing back rather than closing.

## 2026-08-31 — third implementer round (`baton.claude`, W54182 impl claim)

**Plan item 7 only: the one [P2] regression gap from
`review-2026-08-31T17-23-04Z.md`.** No production source, no inventory
semantics and no aggregate run. The single edited file is
`v12/python/tests/manager/test_boundary_inventory.py`.

### The gap reproduced before it was corrected

The reviewer's measurement, rerun here first:

    clear every MEMOISED cache; warm _helper_returns once
    before CacheInfo(hits=0, misses=1, currsize=1)
    run test_the_shared_trees_are_never_mutated_by_a_projection
    after  CacheInfo(hits=3, misses=1, currsize=1)
    test result: no failures or errors

Exactly as reported. **But `CacheInfo` alone cannot settle it after the fix**,
because `cache_clear()` RESETS the counters — a corrected run that clears and
recomputes also reads `misses=1`, and the two cases are indistinguishable. So
the measurement moved to the walker itself, counting calls to
`_returned_origins`, which is what `_helper_returns` runs over the shared trees:

    reverted five-projection form   the shared-tree walker ran 0 times
                                    between the fingerprints
    corrected every-derived form    the shared-tree walker ran 1 time

### And the correction is proved to CATCH something

A count is not coverage. Staging the hazard itself — a `_returned_origins`
replacement that pops a statement out of `oci.py`'s tree, exactly the mutation
`test_the_mutation_check_can_actually_notice` uses — and requiring the
fingerprints to notice:

    reverted five-projection form   notices the staged mutation: False
    corrected every-derived form    notices the staged mutation: True

That is the whole of why the gap mattered: a mutation written into
`_helper_returns` was invisible to the case that claims to forbid it.

### The correction

`test_the_shared_trees_are_never_mutated_by_a_projection` now takes its cleared
and recomputed set FROM `MEMOISED` rather than from a hand-written list —
every member except `_sources` — and asserts the derived set has more than five
members so a silently shrinking tuple cannot quietly re-open the hole. A
hand-written list is the same failure `MEMOISED` was introduced to prevent, and
deriving it means a projection added later is covered without anybody
remembering this case exists.

`_sources` stays uncleared deliberately, and the docstring now says why:
reparsing would hand the second fingerprint a different node graph, and the
question this case asks is whether a projection edited THIS one.

### Verification — the same bounded slices, no aggregate

    TheDiscoveryProjectionsAreBoundedAndImmutable + TheProbeDriverIsBounded
    -> Ran 11 tests in 1.713s, OK                                  (1.9s wall)

    EveryProbeProvesItArrived
      .test_every_declared_probe_reaches_its_named_boundary
      PYTHONTRACEMALLOC=10, -W error::ResourceWarning
    -> Ran 1 test in 25.497s, OK, no unclosed-database warning    (28.5s wall)

    EveryReceivingEntryHasOneOwner + EveryProbeProvesItArrived
    -> Ran 17 tests in 2.159s, FAILED (failures=5)                 (2.4s wall)

The five are the same separately routed semantic families and the same test
names as the accepted evidence: three inventory-universe failures owned by
**W48697** and two missing-probe failures owned by **W54802**. Nothing here
changes or weakens a semantic assertion, and the diff verdict is unchanged.

The aggregate was not run, as the review directs.

### One thing observed and NOT taken

`test_the_package_is_parsed_once_however_many_projections_ask` still drives a
hand-written list of the same five projections. It is not the case the review
raised and its assertion would not change — `_sources` is cleared there, so the
package is parsed once whichever derived projections run — but it is the same
shape of list, and the next projection added is again invisible to it. Offered
for the reviewer to rule on rather than folded into a bounded correction pass.

Whitespace clean; no line in the edit exceeds the file's width.

### State

Awaiting independent review. Passing back rather than closing.

## 2026-08-31 — fourth implementer round (`baton.claude`, W54182 impl claim)

**Nothing edited. The round is a held gate, and the reason is the review's own
precondition.**

`review-2026-08-31T17-47-05Z.md` accepts the `_helper_returns` correction and
takes up the adjacent [P2] I offered: the parse-once case still drives a
hand-written five-projection list. It also conditions the work — "make this
narrow edit only after that file is released."

That condition is not met. When it was written, W39666 was active with me.
I have since passed W39666 back, and `detail work=W39666` now reports it
**active with `baton.codex` on `baton.bug`** — so
`tests/manager/test_boundary_inventory.py` is under independent review rather
than free. Editing it now would put a W54182 hunk into the exact diff that
review is assessing, in a class W39666 does not touch. That is the attribution
confusion the same reviewer was careful to avoid when it declined to attribute
the five semantic failures to this Work, and an immutable candidate is worth
more than a round.

So I asked instead of deciding: M55527, a directed request to `baton.bug` for
either PROCEED NOW or WAIT with word when the file is free.

**A dependency edge on W39666 was considered and deliberately not used.** A
gate would only clear when W39666 CLOSES, which is several review rounds away;
what is actually needed is one sentence about file ownership, which is what a
directed obligation is for.

The correction itself is prepared and is six lines: derive the exercised
projections from `MEMOISED` excluding only `_sources`, invoke that derived
tuple twice, and keep a non-vacuity assertion of more than five, with the
expected parse set still exactly the package module set. No production change,
no inventory-semantic change, no aggregate. It applies the moment the answer
lands, followed by the same bounded regression classes and arrival method.

### State

Blocked on M55527. Nothing in the working tree changed this round.

## 2026-08-31 — fifth implementer round (`baton.claude`, W54182 impl claim)

**The held gate opened and the correction landed.** M55549 answered PROCEED
NOW: W39666's review completed and passed at seq 55544, and `detail` confirms
W39666 queued and unclaimed, so `tests/manager/test_boundary_inventory.py` was
genuinely released. I re-checked that myself before editing rather than taking
the message's word for it.

One file, one method.

### The correction

`test_the_package_is_parsed_once_however_many_projections_ask` now derives its
exercised projections from `MEMOISED` — every member except `_sources` — and
asserts the derived tuple has more than five members, instead of naming five by
hand. The expected parse set is unchanged: exactly the package module set.

### It catches what the hand-written list could not, and that was measured

A derived list is only worth having if it sees something. So the hazard was
staged: a NEW `MEMOISED` member that reparses the whole package — precisely the
case the review says the old form would miss.

    unmutated                                        0 failing
    corrected derived form, new reparsing member     1 failing   CAUGHT
    reverted hand-written form, same new member      0 failing   MISSED

The reverted form does not notice a new projection reparsing all 21 modules,
because it never invokes it. That is the [P2] exactly, and it is the second
time this file has paid for a hand-maintained list beside `MEMOISED`.

### Verification — the bounded slices the review named, no aggregate

    TheDiscoveryProjectionsAreBoundedAndImmutable + TheProbeDriverIsBounded
    -> Ran 11 tests in 1.699s, OK                                 (1.9s wall)

    EveryProbeProvesItArrived
      .test_every_declared_probe_reaches_its_named_boundary
    -> Ran 1 test in 1.993s, OK                                   (2.2s wall)

No aggregate was run, no semantic assertion changed, and no production code was
touched. The arrival driver's catalog now includes W39666's six worker-entry
probes, which are that Work's and are green here.

### State

Awaiting independent review. Passing back rather than closing.
