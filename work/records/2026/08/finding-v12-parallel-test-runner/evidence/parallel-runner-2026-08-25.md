# W9707 parallel runner evidence — 2026-08-25

Implementer `baton.claude`. Companion to the 07:10 serial baseline in
`serial-pure-baseline-2026-08-25.txt`, which this does NOT replace: that one
measured the canonical single-process gate, this one measures the new runner.

## The tree these numbers describe

Every run below was taken against ONE tree state, hashed before the matrix and
re-verified unchanged after it:

    cd v12/python
    find src tests tools -type f -name '*.py' -o -type f -name '*.json' \
      | sort | xargs sha256sum | sha256sum
    -> 9abe4053ce80b1c3422160cbf5594ac7d1fcd8729ed10f6254bdaba5fe779f7c

That state includes UNCOMMITTED work owned by other contexts, and it is named
rather than glossed: `tests/manager/test_oci.py` (+39 lines) and
`tests/manager/test_oci_engine.py` (+33) were modified at 09:07 by the W6632
reviewer, alongside `finding-v12-oci-adapter-core/review-2026-08-25T15-07-37Z.md`.
W9707 modified none of those files. This is also why the failure count differs
from the 07:10 baseline's 12: `d36ca47` (08:57) and those edits added tests,
including deliberately-red ones for W6632's open [P0] findings.

ONE PRECISION NOTE ON THE BINARY. Default run 1 was taken before per-shard
durations were added to the runner's STDERR progress stream; runs 2 and 3 and
all three jobs=1 runs include it. The change touches no stdout, no scheduling
and no result, and run 1's 116.73s sits inside the spread of runs 2 and 3, but
the six runs were not all produced by byte-identical source and saying so is
cheaper than having it found.

## Wall clock, three runs each

    jobs=1 (the runner's own serial mode)
      run 1  elapsed=444.94  user=439.20  system=3.58  cpu=99%   maxrss=195004KB
      run 2  elapsed=444.34  user=438.49  system=3.69  cpu=99%   maxrss=194776KB
      run 3  elapsed=440.50  user=434.65  system=3.60  cpu=99%   maxrss=194700KB
      MEDIAN 444.34s

    default (32 workers, the host's available CPUs)
      run 1  elapsed=116.73  user=565.38  system=7.00  cpu=490%  maxrss=195080KB
      run 2  elapsed=118.00  user=556.58  system=7.08  cpu=477%  maxrss=194964KB
      run 3  elapsed=117.19  user=533.78  system=5.94  cpu=460%  maxrss=193536KB
      MEDIAN 117.19s

    Median speedup 444.34 / 117.19 = 3.79x.

`cpu=99%` against `cpu=460-490%` is the property the finding asked to change,
and it changed. But 490% is NOT 3200%, and the reason is measured below rather
than left as a shrug.

MAXRSS IS NOT AN AGGREGATE. `/usr/bin/time` reports the largest resident set of
any SINGLE process in the tree, so the near-identical ~195MB in both columns
says the biggest individual shard is the same size either way — it does NOT say
the parallel run's total footprint is unchanged. The concurrent footprint is
bounded above by workers x largest shard and is not measured here; a reviewer
who needs a memory ceiling should treat that as an open number rather than read
this line as reassurance.

## Why 3.79x and not more: the run is at its structural floor

From default run 2's per-shard durations (stderr progress), the six slowest
shards:

    117.58s  test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_every_receiving_entry_has_an_owning_validator
     80.30s  test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_every_boundary_call_belongs_to_an_entry_or_is_declared
     79.47s  test_boundary_inventory.EveryProbeProvesItArrived.test_the_missing_probe_check_can_actually_fail
     79.08s  test_boundary_inventory.EveryProbeProvesItArrived.test_every_owned_entry_has_exactly_one_probe
     70.64s  test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_no_entry_is_owned_twice
     57.84s  test_boundary_inventory.EveryProbeProvesItArrived.test_every_declared_probe_reaches_its_named_boundary
      3.36s  the seventh-slowest shard, and everything after it is smaller

Run 2 took 118.00s wall against a longest single shard of 117.58s. **The
scheduler contributes about 0.4s.** Those six methods are ~483s of the ~557s
total CPU; the other 197 shards together account for ~73s.

Two consequences, both worth the reviewer's attention:

1. The pinned method-split decision was right and is already fully exploited.
   Module-level fan-out would have left one ~485s pole; class-level would have
   left two. The split produced six poles, which is what makes 3.79x possible.
2. **More cores cannot go faster than ~118s on this suite.** The floor is one
   test METHOD, and no test runner can subdivide that. Going below it means
   decomposing `test_every_receiving_entry_has_an_owning_validator` itself —
   a test-design decision owned by the boundary-inventory work, NOT by this
   Work, and deliberately not attempted here.

Stating this so 3.79x is not read as the ceiling of the approach. It is the
ceiling of this suite's current shape.

## Result parity: six runs, one answer

All six runs produced identically:

    203 shards, 1120 tests, 11 failures, 2 errors, 1 skipped

and, checked by `diff` rather than by counting:

- the same 203 `[pass]`/`[FAIL]` shard verdict lines, in the same order;
- the same 13 failing test ids.

WHAT IS DELIBERATELY NOT COMPARED, AND WHY. Whole-stdout comparison is
impossible on this tree for a reason that has nothing to do with this runner:
the currently-failing v12 assertions interpolate unordered `set` objects into
their failure text, so the text reorders every run. Proved against the CANONICAL
single-process runner —

    for i in 1 2; do env PYTHONPATH=src python3 -m unittest \
      tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_every_receiving_entry_has_an_owning_validator \
      2>&1 | md5sum; done
    -> f41c6014bd067e2bfb8552c8ccf498f4
    -> fa2044f7617c761d1c83c2cfe9fbb482

— two runs of ONE test through plain `unittest`, two different digests. Filed
as `W10265` (kind `bug`, routed to review) rather than worked around, and those
assertions were not touched. The parity claim above is therefore over shard
verdicts and failing ids, which ARE stable, and this paragraph is the reason
the stronger claim is absent.

One stdout line legitimately differs between worker counts: `[parallel] jobs=N`,
which reports the variable under test. The runner's own regression normalizes
exactly that line by name and compares everything else, so a second line
drifting apart would still fail.

## Collection covers exactly what the canonical gate collects

    runner parallel phase   1120 ids
    runner serial registry    44 ids
    ---------------------------------
    total                   1164 ids

    unittest discover -s tests -t .   1164 ids

`diff` of the two sorted lists is empty. Neither phase invents, drops or
duplicates a test relative to the gate this is meant to be comparable with.

## The registry fails closed, demonstrated rather than asserted

The first real invocation of the runner refused, before its own test file
existed:

    [runner] refused: these registered test modules are not in the tree:
    ['tests.tools.test_parallel_runner']

Unregistered modules, absent registered modules, doubly-registered modules and
a module matching `test*.py` but not `test_*.py` each stop the run with exit 2.
`tests/tools/test_parallel_runner.py` holds the real registries against the real
tree, so ADDING A v12 TEST MODULE FAILS THE SUITE until somebody decides which
phase owns it. That failure is the feature.

## The runner's own regressions

31 cases, 3.1s, no ResourceWarnings. They drive the real runner over disposable
fake trees: deterministic output under inverted completion order (proved by
recording each fake test's interval and asserting the completion order actually
inverted), jobs bounds, failure propagation, drain-don't-abandon, serial/parallel
non-overlap by timestamp, interrupt reaping of a grandchild process, result-root
removal on failure and on refusal, a shard that kills its own interpreter, and
an unimportable module refused at collection.

## Known limitation, stated because the registry looks stronger than it is

The serial registry serializes the two Docker-owning modules WITHIN ONE RUNNER
INVOCATION. It cannot serialize two invocations, two processes, or two agent
contexts sharing one Docker daemon on this host — there is no cross-process
lock. Running W6633 or W6632 concurrently with this gate would collide on image
builds and make the survivor checks report another context's containers as
leaks. Raised on T6633 and T6632; recorded here so the limitation travels with
the evidence rather than living in a message thread.

## The serial registry: alone, and after the parallel phase

Both stages ran on this host with Docker reachable and Podman absent.

    serial ALONE                     elapsed=23.13s  worker_container 22.52s, oci_engine 0.59s
    serial AFTER the parallel phase  elapsed=23.19s  worker_container 22.57s, oci_engine 0.60s

Identical results either way: 2 shards, 44 tests, 3 failures, 0 errors, 5 skips.
The 5 skips are the Podman half of `test_oci_engine`, which skips narrowly when
the binary is absent — that module's own documented policy, not a swallowed
failure.

The two modules ran ONE AT A TIME in registry order, `test_worker_container`
then `test_oci_engine`, and never beside the parallel phase.

### The 3 serial failures are not this Work's

Reproduced under the CANONICAL single-process runner, which is the check that
settles ownership:

    PYTHONPATH=src python3 -m unittest \
      tests.manager.test_worker_container.TheBuiltImageIsWhatTheRecipeSaid.test_two_independent_builds_have_one_pinnable_image_identity \
      tests.manager.test_oci_engine.TheEngineGateLeavesNothingBehind
    -> Ran 5 tests, FAILED (failures=3) — the same three.

- `test_cleanup_queries_the_label_namespace_the_tests_create` and
  `test_a_failed_cleanup_query_is_not_positive_absence` are the two methods the
  W6632 reviewer ADDED at 09:07, confirmed against the checked-in revision:
  red tests for that review's positive-cleanup finding.
- `test_two_independent_builds_have_one_pinnable_image_identity` is W6633's
  image-reproducibility gate; two builds produced different image ids.

### Cleanup: nothing survived

Checked before and after every stage:

    containers named baton-w6633-test    none
    containers named baton-w6632-engine  none
    containers named baton-runtime       none
    images matching baton-w6633*         none
    total image count                    2 before, 2 after
    /tmp/v12-parallel-test-* roots       none

## Interrupt against the REAL tree

A full default run was interrupted with SIGINT after 12 shards were live:

    [runner] signal 2; terminating 9 live shards

Afterwards, counted by walking `/proc` rather than by `pgrep` — which
self-matches its own command line and gave a false positive the first time:

    surviving runner or shard processes: 0
    the runner's own result root:        removed

WHAT DOES REMAIN, AND WHY IT IS NOT THE RUNNER'S. 14 `v12-worker-manager-*`
directories, created by the TESTS' own `TemporaryDirectory` objects, survive in
the private TMPDIR. A terminated process does not run those finalizers. This is
inherent to killing a Python test process mid-test rather than anything this
runner does, and it was VERIFIED rather than assumed:

    SIGTERM the CANONICAL single-process runner mid-suite
    -> temp dirs left behind: 1  (v12-worker-manager-ccj4fo2o)

The canonical gate leaks the same way; the parallel runner has more shards in
flight, so it leaves proportionally more. The acceptance criterion is about
state OWNED BY THE RUNNER, and that is clean. Making killed tests clean up
their own temporary stores is a separate concern belonging to those tests.

## The locked installed layout, and an exact reconciliation

`just build` ran unchanged: the lock resolved with `--require-hashes`, the
wheel built, both slices imported from site-packages, the frozen schema assets
travelled, and the whole suite replayed from the installed layout in 443.70s.

    installed layout   1164 tests, 14 failures, 2 errors, 5 skipped
    this runner        1164 tests, 14 failures, 2 errors, 6 skipped
                       (1120 parallel: 11 F, 2 E, 1 S
                        +44 serial:     3 F, 0 E, 5 S)

Test count, failures and errors reconcile EXACTLY. The one-skip difference is
explained rather than tolerated, and it is intentional behaviour:

`tests/manager/test_dependencies.py` skips when the ambient environment is not
the locked one and RUNS when it is. This host's ambient interpreter resolves
`jsonschema 4.19.2` (plus four other unlocked versions) while the lock pins
`4.26.0`, so that case skips in every source-tree run and converts to a PASS
inside `just build`'s disposable environment. That is exactly the mechanism the
`justfile` describes — the locked stage is what proves the pin — so 6 skips at
source and 5 in the locked layout is the correct pair of numbers, not a
discrepancy.

This also confirms the new `tests/tools/test_parallel_runner.py` passes from
the INSTALLED layout, where `PYTHONPATH` is empty and `tools.parallel_test`
resolves through `-m unittest`'s top-level directory rather than through
`PYTHONPATH=src`.

## The `just` entry points, exercised rather than described

    just parallel-test 8
    -> [parallel] jobs=8 (available CPUs 32)
    -> 203 shards, 1120 tests, 11 failures, 2 errors, 1 skipped

Identical results to jobs=1 and jobs=32, so the recipe's override plumbing is
proved and not merely present. The lower-only bound refuses through the same
documented path:

    just parallel-test 99   -> refused: jobs must be a whole number 1..32 (this host's available CPUs); got 99
    just parallel-test 0    -> refused: jobs must be a whole number 1..32 (this host's available CPUs); got 0
    just parallel-test 8.5  -> refused: jobs must be a whole number 1..32; got '8.5'
    just parallel-test abc  -> refused: jobs must be a whole number 1..32; got 'abc'

WHAT WAS NOT RUN END TO END, SAID PLAINLY. `just parallel-gate` was NOT
executed as one complete chain, because it cannot complete on this tree: the
source phase has 13 real failures and the recipe fail-fasts there by design,
exactly as `gate` would. Its three stages were each executed individually —
`version` as part of the recipe, the source phases through `just parallel-test`,
and the locked `build` directly. The chain itself is therefore unproved until
the tree is green, and a reviewer should treat it that way rather than reading
the stage evidence as covering it.

## After review R1 — the interrupt fix, re-measured

Everything above was measured BEFORE `review-2026-08-25T16-21-40Z.md`, which
found that `Run.shutdown()` could abandon a SIGTERM-ignoring descendant whose
shard leader exited first. The finding was correct; `PROGRESS.md` records the
response and the correction. What the numbers do here:

    the reviewer's regression, before the fix
      AssertionError: True is not false : the TERM-ignoring descendant 3327090
      survived the interrupt

    after the fix
      AnInterruptLeavesNothingBehind          2 tests, OK
      tests.tools.test_parallel_runner       32 tests, OK   (was 31 pass + 1 fail)

    real tree, default workers, after the fix
      elapsed=117.05  user=576.75  system=7.12  cpu=498%  maxrss=194616KB
      203 shards, 1121 tests, 11 failures, 2 errors, 1 skipped

The failing-id set is byte-identical to the pre-fix runs, and 117.05s sits
inside the 116.73-118.00s spread already recorded, so the correction changed
cleanup behaviour and nothing else.

COVERAGE PARITY WAS RE-PROVED RATHER THAN ASSUMED, because the tree changed:

    runner   1121 parallel + 44 serial = 1165
    unittest discover -s tests -t .     = 1165        diff empty

The totals moved from 1164 to 1165 because the review ADDED one regression to
`tests/tools/test_parallel_runner.py`. Every earlier figure in this document
refers to the 1164-id tree and is left as it was measured; nothing above has
been retrofitted to the new count.

Afterwards: no orphaned runner or descendant processes, no leftover
`/tmp/v12-parallel-test-*` roots, `git diff --check` clean. (Both times a
`pgrep`-style check reported a survivor it was matching its own command line;
the counts here come from walking `/proc`.)

## After review R2 — the ordinary-completion leak, re-measured

`review-2026-08-25T16-30-55Z.md` signed off R1 and found R2: `drive()` released
a completed shard's group before the phase verdict existed, so a shard that
failed an assertion and exited 1 NORMALLY could leave a process running. R1's
fix did not cover this, because the ordinary completion path never reaches
`shutdown()`. `PROGRESS.md` records the response.

    the reviewer's regression, before the fix
      AssertionError: True is not false : the failed shard's descendant … survived the run

    after the fix
      AFailingRunAlsoLeavesNothingBehind      3 tests, OK
      tests.tools.test_parallel_runner       33 tests, OK   (was 32 pass + 1 fail)

    real tree, default workers, after the fix
      elapsed=116.36  user=548.18  system=6.33  cpu=476%  maxrss=194868KB
      203 shards, 1122 tests, 11 failures, 2 errors, 1 skipped

    serial/Docker phase, after the fix
      elapsed=23.21s   2 shards, 44 tests, 3 failures, 5 skipped
      image count 2, no baton-w6633-test or baton-w6632-engine containers

116.36s sits inside the 116.36-118.00s spread now recorded across every
measured configuration. The failing-id set is byte-identical to the post-R1
run, and exactly ONE shard verdict line moved —
`AFailingRunAlsoLeavesNothingBehind` from 2 tests to 3, which is this review's
own added regression.

    runner   1122 parallel + 44 serial = 1166
    unittest discover -s tests -t .     = 1166        diff empty

Coverage parity was re-proved rather than carried over, for the third time,
because each review round adds a test: 1164 -> 1165 -> 1166. Earlier sections
of this document state the count they were measured against and have not been
retrofitted.

Afterwards: 0 surviving shard processes (counted from `/proc`), no leftover
runner temp roots, Docker clean.

PORTABILITY, now load-bearing. `has_exited()` uses `os.waitid` with `WNOWAIT`,
which makes this runner explicitly POSIX-only. It already was in practice —
`os.killpg`, `os.getpgid` and `start_new_session` are all POSIX — but this is
the first place the dependency is essential rather than incidental, and it is
essential for a reason: `Popen.poll()` reaps, and reaping is precisely what
destroys the ownership proof both R1 and R2 turn on.
