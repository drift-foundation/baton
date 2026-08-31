# Progress

## 2026-08-31 — baton.claude (impl), W54881 claim

Plan items 2 and 3 are done and item 4's focused gates are green. Two files
changed: `v12/python/src/baton_v12/worker_manager/store.py` and
`v12/python/tests/manager/test_store.py`.

### Revalidated first

Both recorded facts still hold on the current tree. `ControlStore.open`'s
close-on-error `try` ended after schema adoption/initialization; the
`ControlStore` was constructed and `store._now()` called after it. Reproduced
exactly as the finding records:

    cd v12/python
    PYTHONPATH=src PYTHONTRACEMALLOC=5 python3 -W always::ResourceWarning \
      -m unittest -v \
      tests.manager.test_store.OwnershipBeforeAdoption.test_a_clock_that_cannot_stamp_a_row_is_found_at_open
    -> OK, then five unclosed-database warnings traced to store.py:261

FIVE AND NOT SIX, and the sixth is the interesting one: the `not callable`
clock is refused by `boundaries.capability` BEFORE `sqlite3.connect` runs, so
that subtest has no handle to leak. The count in the finding is right and the
reason is worth writing down, because it says the defect is exactly "everything
after the connect", which is the region the correction widens.

### The correction

`store = cls(...)` and `store._now()` moved INSIDE the existing close-on-error
`try`. Nothing else about the shape changed: the handler still closes the
connection, still swallows a failure from that close, and still re-raises the
original exception unchanged.

That last property is the prior ruling this Work must not disturb — a
configured clock that RAISES is a trusted collaborator's fault and is
deliberately left to raise as itself rather than translated into a manager
refusal (`finding-v12-python-assignment-authority/PLAN.md`: "a clock that
raises is left to raise, as a trusted collaborator's fault, with a case
proving it takes nothing with it"). Widening a `try` whose handler re-raises
changes custody of the handle and nothing about the identity of the exception,
and the new case below asserts both halves at once.

### The regressions, and why they are descriptor-based

`test_store.py` already owns `open_descriptors(path)`, written for the two
earlier refusal paths with the reason spelled out: an earlier version of those
cases wrote from another connection and called that proof, and it was not,
because a leaked connection with no open transaction holds no lock. The
reviewer's "a lock-only proxy is insufficient" is the same requirement, so the
new cases use that same helper rather than a second mechanism.

- `test_a_refused_clock_answer_leaves_no_handle_open` — the five clock answers
  that reach `_now()`, each on its own path so a descriptor leaked by one
  iteration cannot be counted against the next.
- `test_a_clock_that_raises_takes_its_handle_with_it_and_nothing_else` —
  requires `assertIs` on the exact exception object AND the descriptor count
  back at baseline, so the ruling and the custody are proved together.
- `test_a_successful_open_still_holds_its_handle` — the counterweight. A leak
  case that only asserts "back to baseline" passes trivially against an
  `open` that closes unconditionally, so this requires the count to RISE for a
  store that opened and to fall again only on `close()`.

### Each shown to fail first

Against the pre-correction shape (`store._now()` back outside the region),
`OwnershipBeforeAdoption` reports `FAILED (failures=6)` — the five refused-clock
subtests plus the raising-clock case, each `1 != 0 : a refused clock answer left
its handle open`. Restored and green.

The counterweight was measured rather than asserted: with `connection.close()`
added before `open` returns, `test_a_successful_open_still_holds_its_handle`
fails and two other cases error. Restored and green.

### One extra, named because it is beyond the stated boundary

With the clock path fixed, `tests.manager.test_store` STILL reported one
unclosed database. It is not `ControlStore`: `PYTHONTRACEMALLOC=12` traces it to
`test_reopening_our_own_store_adds_nothing`, which read `sqlite_master` through
an unnamed `sqlite3.connect(self.path)` and never closed it. Corrected in place
with `addCleanup`. This is a test-local handle rather than a manager custody
defect, so it is outside this record's acceptance boundary and is reported here
for the reviewer to rule on rather than folded in silently. The reason I fixed
it rather than filing it: a suite that leaks a handle while asserting that
nothing leaks a handle teaches its readers to ignore its own warnings, and the
whole gate below is "no unclosed-database warning".

### Focused gates, with the exact commands

Only the gates the research message named. No aggregate inventory, no suite.

    PYTHONPATH=src PYTHONTRACEMALLOC=5 python3 -W error::ResourceWarning \
      -m unittest -v \
      tests.manager.test_store.OwnershipBeforeAdoption.test_a_clock_that_cannot_stamp_a_row_is_found_at_open \
      tests.manager.test_store.OwnershipBeforeAdoption.test_a_refused_clock_answer_leaves_no_handle_open \
      tests.manager.test_store.OwnershipBeforeAdoption.test_a_clock_that_raises_takes_its_handle_with_it_and_nothing_else
    -> Ran 3 tests, OK

    PYTHONPATH=src python3 -W error::ResourceWarning -m unittest \
      tests.manager.test_store
    -> Ran 52 tests in 0.240s, OK

    PYTHONPATH=src python3 -W error::ResourceWarning -m unittest \
      tests.manager.test_boundary_inventory.EveryProbeProvesItArrived.test_every_declared_probe_reaches_its_named_boundary
    -> Ran 1 test in 1.967s, OK

    PYTHONPATH=src python3 -W error::ResourceWarning -m unittest \
      tests.manager.test_offers tests.manager.test_attempts
    -> Ran 368 tests in 1.798s, OK

    scoped whitespace check on the two changed files -> clean

`-W error::ResourceWarning` rather than `always`, so a surviving warning is a
failing run rather than something a reader has to notice in the output.

ONE TIMING NOTE so a later reader does not read a regression into it. The
probe driver takes 24.783 s under `PYTHONTRACEMALLOC=10` and 1.967 s without
it. The tracing is the cost, not the driver; W54182's 2.020 s figure and this
one are the same measurement.

`EveryProbeProvesItArrived` as a whole class still reports 2 failures under the
same flag — the pre-existing probe-table drift owned by W54802, unchanged by
this Work and unrelated to resources.

### State

Awaiting review; passing back rather than closing. W54182 cannot claim its
per-probe resource acceptance until this child is signed off.
