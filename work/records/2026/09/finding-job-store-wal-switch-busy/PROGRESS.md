# Progress

## 2026-09-06 — baton.tuner implementation start

Claimed W101661 and revalidated the accepted ruling against the current tree.
`JobStore._initialize` still requests WAL only after the atomic schema and
Authority-binding commit; `_adopt` validates or migrates the schema, proves the
immutable Authority binding and enables foreign keys, but never retries WAL.
`JobStore.open` still closes the connection and re-raises every WAL failure.

Implementation is limited to a post-ownership WAL helper in
`job_manager/store.py` and additive regressions in the already discovered
`tests/job_manager/test_store.py`. Schema, migrations, Authority identity,
ControlStore and the integration store remain untouched.

## 2026-09-06 — baton.tuner implementation result

Moved the WAL request out of the initialization-only tail and placed it in
`JobStore.open` after either initialization or full adoption has established
store kind, schema and immutable Authority ownership. The local helper
tolerates only SQLite errors whose structured primary result code is BUSY or
LOCKED. Every other failure is re-raised as the same object through the
existing close-on-error region, and every later open asks for WAL again.

Added five focused regressions in the existing Job store module. A
deterministic real SQLite interleaving pauses immediately after the atomic
schema/Authority commit, holds a second connection's `BEGIN IMMEDIATE` while
the opener requests WAL, proves the returned store remains correctly bound and
usable, then proves a later open promotes it to WAL. Synthetic edges prove an
extended LOCKED code is tolerated without its prose, structured IOERR and
busy-looking prose without a structured code both escape unchanged with no
leaked descriptor, and ControlStore/foreign/wrong-schema/wrong-Authority
databases receive no WAL request and retain their bytes.

Verification:

- `PYTHONPATH=src python3 -m unittest tests.job_manager.test_store.WalIsAPostOwnershipRequest`
  — 5 tests passed.
- `PYTHONPATH=src python3 -m unittest tests.job_manager.test_store`
  — 47 tests passed, including the existing migration and Authority-binding
  cases.
- `PYTHONPATH=src python3 -m unittest discover -s tests/job_manager -t .`
  — 338 tests passed.
- `git diff --check -- v12/python/src/baton_v12/job_manager/store.py v12/python/tests/job_manager/test_store.py`
  — passed.
- `just parallel-test` could not create its generated recipe script under the
  managed read-only `/run/user/1000/just` directory. Invoking the recipe's
  checked-in command directly as `python3 tools/parallel_test.py` ran 569 pure
  shards / 3,996 tests and reported six failures plus one error, all outside
  W101661's paths: the Authority catalogue does not yet include a concurrently
  added test module, the concurrently added integration runtime lacks
  `WITNESS_MEMBERS`, and five existing Worker Manager receiving-boundary
  inventory assertions report drift. The fail-fast runner did not enter its
  serial phase, so no broad green result is claimed.

No schema, migration, Authority identity, public return shape, registry,
ControlStore or integration-store byte changed. Ready for independent review
of the exact production and existing-test diff.
