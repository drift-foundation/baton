# Baseline classification of the discovery-run failures — 2026-09-07

Filed by baton.claude for W105575's candidate review, which asked that the
classification carry exact commands, failure ids and evidence rather than a
description. No new full discovery campaign was run for this: the eleven ids
below come from the run already reported, and only those ids were re-executed.

## The full run, once, as reported

From `v12/python`:

```text
PYTHONPATH=src python3 -m unittest discover -s tests -t .
```

`Ran 4431 tests ... FAILED (failures=10, errors=1, skipped=17)`.

## The eleven ids

```text
ERROR: tests.tools.test_parallel_runner.TheRealRegistryDescribesTheRealTree.test_every_v12_test_module_is_registered_exactly_once
FAIL:  tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_every_boundary_call_belongs_to_an_entry_or_is_declared
FAIL:  tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_every_receiving_entry_has_an_owning_validator
FAIL:  tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_the_universe_sees_every_persisted_column_that_is_read
FAIL:  tests.manager.test_boundary_inventory.EveryProbeProvesItArrived.test_every_owned_entry_has_exactly_one_probe
FAIL:  tests.manager.test_boundary_inventory.EveryProbeProvesItArrived.test_the_missing_probe_check_can_actually_fail
FAIL:  tests.authority.test_catalog.TheMigrationChecklistIsRead.test_the_suite_is_one_gate_and_not_a_pile_of_files
FAIL:  tests.manager.test_worker_container.TheGateLeavesTheEngineAsItFoundIt.test_no_container_of_this_suite_survives_it
FAIL:  tests.manager.test_worker_container.TheGateLeavesTheEngineAsItFoundIt.test_only_this_run_s_image_tag_exists
FAIL:  tests.manager.test_credentials_engine.ARealDaemonNeverHoldsTheBearer.test_nothing_this_module_made_survives_it
FAIL:  tests.manager.test_output_custody_engine.CustodyIsTakenOfWhatARealWorkerWrote.test_nothing_this_module_made_survives_it
```

## Re-executed, only these ids

From `v12/python`:

```text
PYTHONPATH=src python3 -m unittest \
  tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner \
  tests.manager.test_boundary_inventory.EveryProbeProvesItArrived \
  tests.tools.test_parallel_runner.TheRealRegistryDescribesTheRealTree \
  tests.authority.test_catalog.TheMigrationChecklistIsRead
```

`Ran 26 tests ... FAILED (failures=6, errors=1)`, with these exact subjects:

```text
tools.parallel_test.RunnerRefusal: these test modules belong to no registry;
add each to the parallel or serial list in tools/parallel_test.py after
deciding what it owns:
['tests.integration.test_driver', 'tests.job_manager.test_review_driver']

AssertionError: Lists differ: [('attempts.py:_committed_record', ...)] != []
AssertionError: Lists differ: [('adopted', 'lanes.py:_occupy_lane', ...)] != []
AssertionError: Lists differ: ['operation_id', 'settled_at'] != []
AssertionError: Lists differ: [(('adopted', 'attempts.py:_attempts', ...)] != []
AssertionError: Lists differ: [(('adopted', 'attempts.py:_attempts', ...)] != []
AssertionError: Lists differ: [... 'test_work_label_exposure.py', ...] != [...]
```

The four Docker cases were not re-executed: they need an engine, and their own
reported text is the classification — "an earlier run's image survived it" and
"containers of this suite survived it" are statements about engine state left
by a previous run, not about any source this Work changed.

## Why each is not this candidate's

The subjects name paths, and the paths have provenance:

```text
$ git status --porcelain -- <the named paths>
 M v12/python/tests/manager/test_boundary_inventory.py
 M v12/python/tools/parallel_test.py
?? v12/python/tests/integration/test_driver.py
?? v12/python/tests/job_manager/test_review_driver.py
```

- **`test_parallel_runner`** refuses `tests.integration.test_driver` and
  `tests.job_manager.test_review_driver` for being in no registry. Both are
  UNTRACKED files of the accepted uncommitted baseline (W103077 and W103076),
  and `tools/parallel_test.py` is itself modified in that baseline. This Work
  added no test module; its coverage is additive inside two modules that were
  already registered.
- **`test_boundary_inventory`** (five ids) names
  `attempts.py:_committed_record`, `lanes.py:_occupy_lane`,
  `attempts.py:_attempts`, and the columns `operation_id` and `settled_at`.
  Neither `worker_manager/attempts.py` nor `worker_manager/lanes.py` is
  modified at all, while `test_boundary_inventory.py` IS modified in the
  baseline — so the inventory expects entries its unmodified sources do not
  yet carry. Nothing in the subject touches this Work's four paths.
- **`test_catalog`** names `test_work_label_exposure.py`, an AUTHORITY test
  file, last written by commit `8af006f` and unmodified in the working tree.
  The checklist inside `test_catalog.py` has not been updated for it.
- **The four engine cases** are Docker state from earlier runs of those same
  suites.

None of the eleven subjects names `worker/claude_agent.py`,
`source_profiles/checkout.py`, `tests/manager/test_claude_agent.py` or
`tests/manager/test_source_boundary.py`.

## What this evidence does not claim

It is not a before-and-after comparison against a reverted tree. Reverting
requires restoring the pre-candidate bytes, and this participant may not mutate
Git state to obtain them. What is offered instead is the failure subjects
themselves plus the working-tree provenance of every path they name, which is
why each entry above cites a symbol or a file rather than only a verdict.
