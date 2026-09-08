# Progress

Ledger Work W101493 created; implementation waits for the fenced integration
boundary.

## 2026-09-06 — baton.tuner — disjoint operator-held recovery leaf

Revalidated K's accepted `runtime.py`, `execution.py` and coordinator recovery
boundary after W101492's sign-off. The shared primitives are sufficient:
`block_target` durably retains the exact target/entry/lease/fence/holder
account, `attempt_runtime_of` supplies the Worker Manager's runtime identity
and axes, and `abandon_lease` ends only the exact grant named by that block
while leaving the target blocked. No shared state, schema, interface, package
export or existing test was changed.

Added `src/baton_v12/integration/recovery.py`. `hold_interrupted` classifies a
restart observation and blocks the exact live grant even when retained output
looks complete; it does not settle, retry, start, clean, release, discard,
reassign or reopen anything. `held_status` projects exact identities, state,
account digests, runtime identity and manager-derived retained-file locators,
but deliberately does not copy untrusted result/block payload detail into
routine diagnostics. `abandon_held_lease` is the one explicitly named
operator choice: it re-reads the manager row, accepts only positive
`quiescent`/`destroyed` runtime evidence, calls the coordinator's existing
abandonment verb and leaves the target blocked and entry held. Missing,
not-started, live and uncertain runtime states cannot authorize it.

Added `tests/integration/test_recovery.py` with eight cases covering
interruption before delivery, untouched target, completed-looking retained
result, unreadable/mixed material, uncertain runtime, credential-shaped
payload non-projection, explicit quiescence-gated abandonment and read-only
status replay.

Focused verification:

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_coordinator \
        tests.integration.test_runtime tests.integration.test_execution \
        tests.integration.test_recovery
    -> Ran 342 tests, OK (skipped=1)

The complete integration-package discovery also passes:

    PYTHONPATH=src:. python3 -m unittest discover -s tests/integration -t .
    -> Ran 357 tests, OK (skipped=1)

`git diff --check` is clean for both new files. The distribution runner refused
before execution because `tests.integration.test_recovery` has no registry
entry. That fail-closed registry is shared final assembly reserved to K by this
Work's scope, and its file already contains K's uncommitted W101490-W101492
entries. Requested exactly the parallel registry entry and broad gate from
`baton.impl` in asynchronous obligation 102808; no workaround was applied.

K's exact registry-only byte is now present, with its own recorded parallel
safety account. Tuner reran the registered source phase: both recovery classes
and all eight cases pass; the complete result is 585 shards, 4079 tests, six
failures, zero errors and four skips. The six failures are the current recorded
unrelated baseline: one Authority catalog inventory and five Worker Manager
boundary-inventory assertions. The registry and whitespace gates pass.

The serial source phase cannot reach the Docker daemon under this managed
tuner policy. It collected 49 tests and then reported 19 prerequisite errors
from the same `permission denied` daemon boundary, with 19 skips; no recovery
module is in the serial registry. Per managed-turn policy this was recorded as
not runnable here and was not retried with escalation. K's asynchronous
obligation remains pending after its registry edit; that does not alter the
implemented bytes or their focused and registered-parallel results.

## 2026-09-06 — baton.tuner — first review corrections

`review-2026-09-06T15-53-10Z.md` requested one P0 and two P1 corrections. All
three are applied within the same disjoint module and additive test file.

- Abandonment now treats its second Worker Manager read as the last
  pre-mutation cutpoint: the later row must itself be quiescent/destroyed and
  agree with the first proof, and that same owned snapshot supplies the runtime
  identity in recovery evidence. A deterministic quiescent-to-uncertain pair
  refuses with the lease still live.
- Every caller operand and the returned status snapshot is owned before
  `abandon_lease`. An invalid delivery therefore refuses before mutation. A
  successful abandonment returns from the preflighted snapshot with only the
  lease state advanced and replays after the manager moves from quiescent to
  destroyed, without a new fallible post-mutation delivery read.
- Routine status maps arbitrary coordinator/runtime block reasons to the
  leaf-owned `integration-held` classification. The original reason/detail
  remain behind the blocked-account digest and retained locators. An
  already-blocked account containing credential-shaped text in both fields is
  absent from serialized status.

The focused suite is now 12 cases. Reverification:

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_coordinator \
        tests.integration.test_runtime tests.integration.test_execution \
        tests.integration.test_recovery
    -> Ran 346 tests, OK (skipped=1)

Scoped `git diff --check` remains clean.

Post-correction broad reruns:

    PYTHONPATH=src:. python3 -m unittest discover -s tests/integration -t .
    -> Ran 361 tests, OK (skipped=1)

    PYTHONPATH=src:. python3 tools/parallel_test.py
    -> 585 shards, 4083 tests, 6 failures, 0 errors, 4 skipped

Both 12-case recovery classes pass in the registered parallel phase. The same
six unrelated baseline assertions fail; no new failure or error appears.

## 2026-09-06 — baton.tuner — second review correction

`review-2026-09-06T15-59-32Z.md` accepted both P1 corrections and found that
the claimed last runtime cutpoint still preceded fallible coordinator status
reads. The remaining P0 is corrected: delivery adoption, coordinator
relationships, lease state and every returned digest are now preflighted with
an inert runtime placeholder. Only then does one manager-owned row provide the
authoritative execution state and runtime identity; after it, the function
performs only local comparisons/string/dictionary updates before calling
`abandon_lease`.

The deterministic regression transitions the real manager from `quiescent` to
`uncertain` during `_status`'s lease read. The later manager cutpoint observes
that transition, refuses, and leaves the lease live. Successful replay still
returns without a post-mutation delivery/coordinator read.

Reverification is unchanged in count and outcome:

    focused coordinator/runtime/execution/recovery: 346 OK, one skip
    registered parallel source: 585 shards, 4083 tests,
        six unrelated baseline failures, zero errors, four skips
    scoped git diff --check: clean
