# Plan

1. [done, changes requested] Inspect the parent episode's four-file transport diff
   against `baton_worker.py`, the accepted OCI lifecycle and the recorded
   daemon probe.
2. [done] Run the focused 45-case suite and accepted OCI regressions. Findings
   are in `review-2026-08-29T13-43-10Z.md`.
3. [next implementation] Correct only transport/vector boundaries and focused
   tests. Do not begin provider, operator or task work here.
4. [engine proof] Run the real worker-container and lifecycle composition
   gates once unrelated shared-tree failures no longer prevent the serial
   phase.
5. [boundary ownership] Add the three recorded inventory entries only after
   the shared registry owner hands off that file.
6. [complete] Independently accept the bounded transport result, then close
   W39356 so the operator checkpoint's transport gate can clear.

## Initial file ownership

- `v12/python/src/baton_v12/worker_manager/worker_entry.py`
- transport/network/interactive additions in
  `v12/python/src/baton_v12/worker_manager/oci.py`
- `v12/python/tests/manager/test_worker_entry.py`
- additive focused cases in `v12/python/tests/manager/test_oci.py`
- the `test_worker_entry` registration in `v12/python/tools/parallel_test.py`

`v12/python/tests/manager/test_boundary_inventory.py` is excluded until its
current owner records a handoff.
