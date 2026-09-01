# Plan

1. [done] Revalidate W39356's retained three-site debt against the bounded
   current inventory and enumerate every current `worker_entry.py` crossing.
2. [done] Pin the scope split with W48697: W39666 owns all `worker_entry.py`
   entries and the two exact OCI receiving entries represented by the retained
   network/program validator sites; W48697 retains other OCI debt.
3. [done] Correct the raw `TypeError` collection-shape gaps in
   `worker_entry.converse`, then register each slice entry under its real
   direct, delegated, or stated owner. Do not add validators solely to make
   scanner output disappear.
4. [done] Add exact entry-keyed probes/witnesses, including the
   already-owned `ChannelPort.__init__.open_channel` and `converse.session`,
   plus a slice-specific completeness regression that can pass independently
   of W48697.
5. [done] Run the worker-entry functional suite, stated-owner witness
   suite, affected inventory probes, slice completeness check, and the bounded
   aggregate owner/probe classes. Report unrelated residuals rather than
   absorbing them.
6. [done; signed off in review 2026-09-01T03-46-59Z] Independently verify every declaration reaches the
   owner it names, malformed containers cannot escape as Python exceptions,
   and no W48697 OCI entry was silently claimed here. The behavior, scope and
   bidirectional exact-probe assertion pass.

## Expected implementation files

- `v12/python/src/baton_v12/worker_manager/worker_entry.py`
- `v12/python/tests/manager/test_worker_entry.py`
- `v12/python/tests/manager/test_boundary_inventory.py`

The historical network/program ownership is registered and probed in the
shared inventory test; no OCI product change is proposed unless revalidation
finds the existing validator behavior itself defective.

## 2026-08-31 implementer round

7. [done] The proposed ownership model was re-derived from
   `owning_validators()` before any table entry was written, and survived
   unchanged: `'one'` is the loop variable at both per-member call sites, which
   is why `exec_vector.program`, `converse.operations` and
   `converse.operation_ids` are composite STATED owners rather than layer ones,
   and why `run_vector.network` is a DELEGATION to the private helper rather
   than a `NOT_AN_ENTRY` exemption.
8. [done] 4 DELEGATED, 6 STATED_OWNERS with 6 witnesses, 6 probes, and the
   slice check `TheWorkerEntryTransportIsFullyInventoried`. All 22 removed one
   at a time; the slice check catches every one.
9. [done] Residual reported rather than absorbed: unowned 133 -> 123, owned
   but never probed 46 -> 44, probed but never owned 3 -> 3, and the same five
   aggregate failures as the baseline. `exec_vector.engine`,
   `run_vector.interactive`, `run_vector.workspace_group` and
   `exec_vector.runtime_id`'s missing probe remain W48697's.
10. [queued] Restrict declared probes to this slice, assert exact equality
    with the wanted probe set, and mutation-test an added wrong-label probe so
    the slice-specific gate catches both missing and extra registrations.

## 2026-09-01 implementer round

10. [done] Review 2026-08-31T17:55:24Z [P2]: the slice's exact-probe check was
    one-directional, so a wrong-label or stale probe for a slice entry passed.
    The declared set is now narrowed to `slice_entries()` and compared for
    equality in both directions, and four added-probe mutations — wrong label,
    second label, a probe for a stated entry, and the retained OCI entry under
    the wrong label — are each caught. The twelve removal mutations still
    bite.
    145 / 1 / 255 tests OK, the reviewer's own figures.
