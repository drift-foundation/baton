# Progress

## 2026-09-06 — baton.tuner implementation start

Claimed W101621 and revalidated the accepted ruling against the current tree.
`ControlStore._initialize` still requests WAL after its schema transaction,
while `_adopt` does not request it; `ControlStore.open` still closes the handle
and re-raises any resulting SQLite failure unchanged. The manager's established
contention classifier in `attempts.py` uses only the structured primary result
code (`sqlite_errorcode & 0xff`) for SQLITE_BUSY/SQLITE_LOCKED, matching this
record's accepted boundary.

Implementation is limited to a post-ownership WAL helper in
`worker_manager/store.py` and additive regressions in the already registered
`tests/manager/test_store.py`. The separately tracked JobStore is untouched.

## 2026-09-06 — baton.tuner implementation result

Moved the WAL request out of fresh initialization and placed it in
`ControlStore.open` after either initialization or adoption has established
ownership. The local helper tolerates only SQLite errors whose structured
primary result code is BUSY or LOCKED; every other failure is re-raised as the
same object through the existing close-on-error region. Every later open asks
for WAL again.

Added five focused regressions in the existing store module. A deterministic
real SQLite interleaving pauses immediately after schema commit, holds a second
connection's `BEGIN IMMEDIATE` while the opener requests WAL, proves the store
returns usable in its retained mode, then proves a later open promotes it to
WAL. Synthetic edges prove an extended LOCKED code is tolerated without its
prose, a structured IOERR and busy-looking prose without a structured code both
escape unchanged with no leaked descriptor, and foreign/incompatible stores
receive no WAL request and retain their bytes.

Verification:

- `PYTHONPATH=src python3 -m unittest tests.manager.test_store.WalIsAPostOwnershipRequest`
  — 5 tests passed.
- `PYTHONPATH=src python3 -m unittest tests.manager.test_store`
  — 57 tests passed.
- `git diff --check -- v12/python/src/baton_v12/worker_manager/store.py v12/python/tests/manager/test_store.py`
  — passed.
- `PYTHONPATH=src python3 -m unittest discover -s tests/manager -t .`
  — ran 2,433 tests; 17 class prerequisites errored because the Docker socket
  is not accessible in this managed turn, and five existing boundary-inventory
  assertions failed on unrelated receiving-entry inventory drift. Neither
  failure set names or exercises the two W101621 paths; no broader result is
  claimed green.

No registry, schema, public return shape, integration package or JobStore byte
changed. Ready for independent review of the exact production and existing-test
diff.
