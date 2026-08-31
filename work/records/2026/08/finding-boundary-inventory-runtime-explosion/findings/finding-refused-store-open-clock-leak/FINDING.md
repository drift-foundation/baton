# Refused ControlStore.open leaks its SQLite handle after clock validation

Work: W54881

Parent: W54182, `work/records/2026/08/finding-boundary-inventory-runtime-explosion/`

## Classification

**Confirmed defect.** `ControlStore.open()` promises that every failed open
closes the handle, but a refusal from the configured clock occurs after its
close-on-error region and leaks the SQLite connection.

## Observation — 2026-08-31

W54182's focused probe driver succeeds in about two seconds, but this command
still emits one `ResourceWarning` after the successful verdict:

```text
cd v12/python
PYTHONPATH=src PYTHONTRACEMALLOC=10 python3 -W always::ResourceWarning \
  -m unittest \
  tests.manager.test_boundary_inventory.EveryProbeProvesItArrived.test_every_declared_probe_reaches_its_named_boundary
```

The allocation trace points through
`test_boundary_inventory.py:5278` to `store.py:261`. The independently focused
store case makes the defect clearer:

```text
PYTHONPATH=src PYTHONTRACEMALLOC=5 python3 -W always::ResourceWarning \
  -m unittest -v \
  tests.manager.test_store.OwnershipBeforeAdoption.test_a_clock_that_cannot_stamp_a_row_is_found_at_open
```

It reports `OK` and then emits five unclosed-connection warnings, one for each
callable clock that answers an invalid value.

## Confirmed cause

`v12/python/src/baton_v12/worker_manager/store.py:261` opens the connection and
protects schema adoption/initialization with a close-on-error `try`. It then
constructs the `ControlStore` and calls `store._now()` at line 284 **after**
that `try`. A refused clock answer raises before `open()` can return the store,
so the caller has no object it can close and the only connection reference is
left for garbage collection.

This is distinct from the earlier deliberate ruling about a configured clock
that itself raises: its exception may still propagate unchanged. The defect is
resource custody on that failure, not exception translation.

## Acceptance boundary

- Every failure after `sqlite3.connect()` closes the connection before the
  exception escapes, including `_now()` refusal and a clock-raised fault.
- A focused regression observes the actual descriptor/connection lifetime;
  merely proving that another connection can write is insufficient.
- Existing refusal category/message and the deliberate propagation of a clock's
  own exception stay unchanged.
- W54182's focused 549-probe driver emits no unclosed-database warning.

