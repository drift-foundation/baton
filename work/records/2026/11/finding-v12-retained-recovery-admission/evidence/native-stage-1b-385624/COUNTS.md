# Measured verification — W385624 Stage 1-B

Ambient interpreter (`just` and the prepared environment are absent here; see
REPORT.md). `BATON_V12_DISK_ROOT` and `TMPDIR` on disk-backed ignored scratch.
Durations are wall clock as the runner reported them; the group runs overlapped
with each other on this host, so their durations are upper bounds and are
marked as such rather than cleaned up.

## The focused acceptance entry

| Run | Collected | Passed | Failed | Errored | Skipped | Duration |
| --- | --- | --- | --- | --- | --- | --- |
| `tests.job_manager.test_retained_recovery_admission` | 63 | 63 | 0 | 0 | 0 | 12.896 s |

Verbatim, from the EXACT command this Work is accepted by, run from the
repository root with nothing else loading this host (`focused.log`):

    Ran 63 tests in 12.896s

    OK

Exit status 0. Earlier runs of the same module while three accounted group
runs shared this host measured 116 s, 169 s and 20 s for the same 56-62 cases;
those are contention, not the module, and are not reported as its duration.

## Groups declared affected

| Group | Collected | Passed | Optional skips | Required skips | Failures | Errors | Verdict | Log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `authority` | 511 | 511 | 0 | 0 | 0 | 0 | OK | `authority.log` |
| `job_manager` | 1925 | 1836 | 0 | 0 | 88 | 1 | FAILED (all pre-existing) | `job_manager.log` |
| `scans` | 494 | 489 | 2 | 1 | 0 | 2 | FAILED (all environmental) | `scans.log` |
| `tools-pure` | 504 shards started, 502 completed; NOT accounted | — | — | — | — | — | INCOMPLETE in this container | `tools-pure-partial.log` |

`tools-pure` was started and is reported as INCOMPLETE rather than as a
verdict. 502 of its 504 shards completed; two long `test_standalone_ab`/
`test_stage_execution` shards were still running when this slice finished, and
81 of the completed shards exited non-zero. Every one of those 81 is a
consumer of `tests/tools/test_stack.py::_disk_root_outside_the_checkout`, which
this container cannot satisfy — measured directly:

    AssertionError: no disk-backed directory outside the checkout was found
    for the v12 stack composition case; tried /var/tmp (it is not a directory
    this process can write), ~/.cache (it is not a directory this process can
    write), /output/work/scratch/t (it is inside the checkout at /output).
    Set BATON_V12_STACK_TEST_ROOT to a directory on real storage outside
    /output.

So the group cannot produce a meaningful accounted verdict here at all, and
one is not claimed. What IS verified for this slice is the tools-pure module
its change actually bears on — the execution registry and the declared
consumed input: `tests.tools.test_parallel_runner`, 73 collected, 73 passed,
51.715 s, OK (`parallel-runner.log`).

## Every non-passing id, classified

- `job_manager`, 85 ids in `tests.job_manager.test_fresh_attempt`:
  **pre-existing/environmental.** Each refuses in `setUp` from
  `tests/tools/test_stack.py::_disk_root_outside_the_checkout` — this host has
  no non-tmpfs storage outside the checkout. Measured at the base commit with
  the same cause: `baseline-fresh-attempt.log`.
- `job_manager`, 1 id in `tests.job_manager.test_native_permission`:
  **pre-existing/environmental**, the same cause reported by
  `stage_execution._outside`.
- `job_manager`, 3 ids
  (`test_tool.TheStatusSurfaceOpensBothStoresReadOnly` x2,
  `test_store_readonly.EveryFailurePathRELEASESItsHandle` x1):
  **pre-existing/environmental**, a long temporary path sampled out of a
  refusal message. Both runs retained:
  `baseline-path-messages.log` (base commit, 3 failures) and
  `baseline-path-messages-candidate.log` (candidate, the same 3).
- `scans`, 2 ids in `tests.manager.test_boundary_inventory`:
  **environmental**, `subprocess.run(..., timeout=2)` exceeded while three
  accounted group runs shared this host's CPUs. Zero FAILURES in `scans`, so
  no inventory, dependency, text-sweep or source-boundary rule is violated by
  the new files.
- `scans`, 1 REQUIRED SKIP in `tests.manager.test_dependencies`:
  **environmental**, the prepared locked environment is absent
  (`jsonschema` 4.19.2 resolved, 4.26.0 pinned). `just build` runs that
  assertion inside the environment where it holds.
- `scans`, 2 optional skips: registry entries with recorded owner rulings.

No non-passing id involves a changed product path or this Work's own
acceptance module.

## One more environment note, for whoever runs this elsewhere

`/tmp` here is a 32 MiB tmpfs and several suites default to it for their
`tempfile.TemporaryDirectory` roots, so a run that does not set `TMPDIR`
can exhaust it and surface as `sqlite3.OperationalError: database or disk is
full` from an unrelated module (observed once in
`tests.authority.test_boundary.EveryCallerTextFamilyIsBounded`; the same module
passes 25/25 with a disk-backed `TMPDIR`, and the accounted `authority` group
run above was 511/511 OK). THE ACCEPTANCE ENTRY ITSELF DOES NOT NEED IT: the
exact command this Work is accepted by sets only `BATON_V12_DISK_ROOT`, and it
was run repeatedly that way with `/tmp` at 70%+ use and finished 63/63 OK each
time, leaving its own temporary roots cleaned up (measured before and after).
