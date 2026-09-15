# `golden-schema4.sqlite3` — a Job store the PREVIOUS build wrote

W156162. `tests/job_manager/test_execution_limits.py` needs a populated Job store
at **schema 4** — one that already holds a `baton.v12.job-submission/1` Job and
its signed submission operation, and that has never seen the
`job_execution_limits` table this Work adds. A store this build wrote and then
had rows deleted from is not that: it proves a missing-row fallback, which is a
different fact and is covered by its own narrower case.

## How it was produced

A copy of the working tree was made in an isolated directory, this Work's two new
files were removed from it, and the **committed** (pre-W156162) versions of the
**five** `job_manager` source files this Work changes — `documents.py`,
`schema.py`, `store.py`, `submission.py` and `projection.py` — were written over
their copies. `submit(store, tests.job_manager.fixtures.submission())` was then
run **there**. Nothing in this Work's code wrote a row in it.

**What that does and does not pin.** Those five files are the whole of this Work's
change to the Job owner, so the store's schema, its rows and its signed operation
are the previous build's. Everything else in that tree — the rest of the package,
the Worker Manager, the fixtures — came from the working tree as it stood, and
carries whatever other Works had in flight. This is a five-file reconstruction,
not a checkout of an old build, and the metadata beside it enumerates exactly the
five digests that were replaced. Corrected 2026-09-13 per review
2026-09-13T01:44:11Z, which found this file claiming six files including
`__init__.py` while the metadata listed five.

- Generator: `work/records/2026/09/finding-v12-per-job-budgets/golden-schema4-156492.py`
- Metadata, including the SHA256 of each of the five REPLACED source files, the
  table list and the recorded operation:
  `work/records/2026/09/finding-v12-per-job-budgets/golden-schema4-156492.json`
- Byte-identical original, retained as history:
  `work/records/2026/09/finding-v12-per-job-budgets/golden-schema4-156492.sqlite3`

SHA256 `bb9fa3aba268f461f46cc38098faed7bbe8699d0da5918f62f0fc9c44a6b7866`,
schema version `4`, Jobs `job-a` and `job-b`, one committed
`submission.record` operation.

## Why the copy lives here

Review 2026-09-13T01:36:01Z R6: the test reached out of the Python tree into the
research dossier for it, so the migration regression depended on the whole record
layout and was not inside the product candidate. AGENTS.md keeps stand-alone
tests and their artifacts outside dossiers. The dossier copy stays as history;
this one is what the test reads, relative to itself.

## Regenerating it

Re-running the generator against a *later* commit would produce a store from a
different old owner, which is a different artifact and not this one. If a future
Work needs a fresh golden, generate it deliberately, record the same metadata
beside it, and give it its own name rather than overwriting these bytes.
