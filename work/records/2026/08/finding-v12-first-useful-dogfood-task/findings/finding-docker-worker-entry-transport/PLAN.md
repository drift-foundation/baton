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
5. [non-gating hardening; superseded 2026-08-30] W39666 retains the three
   recorded inventory entries after shared-registry ownership settles. It no
   longer blocks this checkpoint or the dogfood path.
6. [done, signed off 2026-08-30] Independently accepted the bounded transport
   result in `review-2026-08-30T05-33-39Z.md`; close W39356 so the operator
   checkpoint's transport gate can clear.

## Initial file ownership

- `v12/python/src/baton_v12/worker_manager/worker_entry.py`
- transport/network/interactive additions in
  `v12/python/src/baton_v12/worker_manager/oci.py`
- `v12/python/tests/manager/test_worker_entry.py`
- additive focused cases in `v12/python/tests/manager/test_oci.py`
- the `test_worker_entry` registration in `v12/python/tools/parallel_test.py`

`v12/python/tests/manager/test_boundary_inventory.py` is excluded until its
current owner records a handoff.

## 2026-08-29 — first implementation round under W39356

1. [done] **[P1] A scalar program can no longer become argv characters.**
   `exec_vector` requires an explicitly supported sequence shape — `list` or
   `tuple` — instead of applying `list(program)` and letting Python decide what
   a string means. A word ceiling came with it: an unbounded operand is an
   unbounded argv.
2. [done] **[P1] Surplus stdout after the final expected answer is refused.**
   The channel contract gained `close_input`, because the order is the content:
   the worker's loop ends on a clean end of input, so its stdout cannot reach
   EOF until its stdin does. `converse` now closes the send side on every path,
   drains stdout to EOF under a bound, and makes any surplus `lost` — on the
   faulted path as well as the answered one.
3. [done] **[P2] The two start operands are held at their own boundary.**
   Eight cases in `test_oci.py` covering default composition, explicit
   posture, exactly-one `--network`, grammar refusals, construction refusal and
   the untouched remainder of the restriction table.
   `OciAdapter.__init__` now uses `type(...) is not bool` rather than
   `not in (True, False)`, which admitted `0` and `1` by equality. The module
   contract text at the top of `oci.py` names the one substitutable entry.
4. [done] **`EXEC_SECONDS` removed** rather than wired up: how long a provider
   turn may take is the operator checkpoint's policy, and an unread constant is
   a claim that this module owns it.
5. [done] **The export question is decided and written into `__init__.py`.**
   Neither `exec_vector` nor `converse` is exported; the transport is reached
   as a component like `oci`, `launch`, `credentials` and `custody`. Exporting
   `converse` was tried and reverted: it makes it a public operation, and
   `test_dependencies` then requires its parameters in the shared
   declared-operand vocabulary — a widening the operator checkpoint should
   decide, since it is the caller.
6. [done] **The real-engine gate exists.** `tests/manager/test_worker_entry_
   engine.py`, registered as the twelfth serial module: one real container,
   started through the accepted operations, answering `describe` and `work`
   over `docker exec`, returning the session's own status, keeping stderr
   apart, and writing a declared output the host reads back through the
   inherited workspace group. Plus the cross-session refusal, the removed
   runtime, and the non-interactive default that proves what the operand buys.
7. [done, and it was owed] **Six undeclared public operands.** The previous
   round introduced `network`, `interactive`, `program`, `channel_port`,
   `operations` and `operation_ids` without declaring them, and
   `test_dependencies` had not been run against them. Each is now declared with
   the claim that registry requires.
8. [NOT DONE, unchanged] The three boundary-inventory entries. That file still
   carries another participant's uncommitted edit; PLAN item 5's condition — a
   recorded handoff from its owner — has not occurred.

## 2026-08-29 — second implementation round under W39356

1. [done] **[P1] A receive failure can no longer escape `converse`.**
   `_Reader._more` called the injected `receive` outside any exception
   boundary, so a channel enforcing the caller's own `seconds` bound by
   raising `TimeoutError` went past all three closed endings and out to a
   caller that was promised peer behaviour always answers one of them. Every
   read failure is now a bounded `lost` naming the read step.
2. [done] **[P1] The drain no longer fabricates a byte count.** It returned
   `1` for every failure, so a timeout while draining was reported as "the
   worker wrote 1 byte" — a measurement nobody made, and the more alarming of
   the two readings. `surplus()` answers `(bytes, why)`: the count is only
   ever bytes actually read, and a drain that failed says so instead. Three
   regressions hold the three outcomes apart.
3. [done] **[P2] The export rationale describes the current boundary.** Its
   registry-widening half was made false by this same checkpoint and is
   removed rather than annotated; the reason recorded now is the component
   boundary, which is the reason that is actually true.
4. [non-gating hardening after 2026-08-30 ruling] **[P2] The three boundary-
   inventory entries.** W39666 owns them and remains open. The inventory scan
   raises before it attributes anything, so entries written now could not be
   checked against the gate they exist to satisfy; this bookkeeping no longer
   delays final transport review or the first positive dogfood slice.
