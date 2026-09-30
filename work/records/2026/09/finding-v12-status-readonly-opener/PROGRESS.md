# Implementer progress -- W316915

## Claim 316919 (baton.claude, impl) -- status opens both stores read-only

Bound FINDING and PLAN read; scope taken as written. The PLAN's coordination
note is honoured: the only shared path with W316918 would be
`tools/job_manager.py`, W316918 is unclaimed and I edited nothing in its bound
dossier.

### Revalidated before implementing, as the FINDING requires

`JobStore.open_readonly` exists and is exactly the needed contract: `mode=ro`,
no creation, no initialization of an empty file, NO MIGRATION (it calls the
non-mutating `_recognized` rather than `_adopt`), no WAL request, NO WRITABLE
FALLBACK, and the Authority binding still proved. `ControlStore.open_readonly`
exists too and additionally marks the handle `readonly`, so every action on it
refuses -- "a read-only manager or read snapshot performs no action".

### The correction

`tools/job_manager.py`: a new `_observing_job_store(taken, clock)` calling
`JobStore.open_readonly`, used by `_status`; and `_status`'s control store now
opens through `ControlStore.open_readonly`. `_job_store` is untouched and
`_submit` and `_serve` still use it, because they act and need an opener that
may create and adopt. No other product file changed, no raw SQL workaround, no
store repair, and the status document's shape is unchanged.

### THE HONEST BOUNDARY, measured rather than assumed

The acceptance asks that status run without directory or database write
authority. It now does for a read-only DATABASE FILE. IT DOES NOT for a
cleanly-closed WAL store in a read-only DIRECTORY, and that is SQLite's
requirement rather than the opener's: the writable openers put these stores in
WAL mode, a clean close removes the `-wal`/`-shm` sidecars, and a read-only
connection to a WAL database must CREATE the shared-memory file, which needs
directory write access. Measured, all four cases:

    read-only FILE, writable directory ................. reads
    WAL sidecars present, read-only directory .......... reads
    cleanly-closed WAL store, read-only directory ...... REFUSED (OperationalError)
    a stable COPY with its sidecars, read-only dir ..... reads

The third is the shape the deployed failure took, and the correction does not
remove it. What the correction does fix is the part that was actually wrong: the
refusal is now HONEST -- no creation, no initialization, no migration, no WAL
request and explicitly no write-capable fallback -- so a status that cannot read
says so instead of quietly opening the store for writing. The measured remedy
for an unwritable directory is the one the W236087 evidence already used: read a
stable copy, which a case proves works.

AND SQLITE'S SIDECAR WRITES ARE NAMED RATHER THAN HIDDEN. A read-only
connection to a WAL database creates `-shm` and `-wal` when the directory
allows it. That is a directory write attributable to status. It changes no store
byte, which is what the digests assert, and claiming "status writes nothing at
all" would have been untrue -- so the tests assert the claim this correction can
actually make: no store byte moves, and anything new is a sidecar.

### Focused acceptance -- 13 cases in `tests/job_manager/test_tool.py`

The writable openers replaced with ones that FAIL IF CALLED, for both stores;
submit still uses the writable one; no store byte changes across status with and
without a control store; a missing Job store and a missing control store refused
with no file and no sidecar created; an empty database refused and still empty;
another Authority's store refused untouched; another schema refused with
"carries no migration" and "Nothing was changed" and nothing carried forward;
both status shapes preserved with the same document members; `--observe` still
observational and writing nothing; and the two WAL/read-only-directory cases
above. Permission changes are used as a CONDITION, never as the proof -- the
proof is the file digests, as the FINDING requires.

### Measured

    tests.job_manager.test_tool + test_status + test_recovery +
    tests.tools.test_stage_execution_status_hardening: 160 PASS in 4.96s.
    tests.job_manager.test_sweep + test_ending + tests.tools.test_stage_execution:
    569 PASS in 192.7s -- the suites that drive this CLI hardest.
    2 mutations, each re-breaking one opener, both caught; unmutated and
    restored runs clean (MUTATIONS-316919.json).
    No live run, no deployed read or repair, no integration act, no credential
    change, no Git or graph act.

### Files

Product: `v12/python/tools/job_manager.py` (6a374552f879). Product tests:
`v12/python/tests/job_manager/test_tool.py` (cb58c4a9f347). Dossier: this record,
`MUTATIONS-316919.json`, `CANDIDATE-316919.json`. FINDING and PLAN are the
reviewer's.
