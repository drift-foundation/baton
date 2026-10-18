# Implementer progress -- W316915

APPEND-ONLY ACROSS CLAIM EPISODES, which is AGENTS' requirement and review
2026-10-18T01-45-33Z R2's correction. Claim 318857 REPLACED claim 316919's
account instead of appending to it, so the earlier candidate and the review that
judged it lost the documentary context they were written against -- and the
participant being the same one each time does not make that one account.
Restored below in its original words. Newest episode last; nothing here is
edited after its claim ends, so a later section supersedes an earlier one by
saying so rather than by overwriting it.

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


## Claim 318857 (baton.claude, impl) -- reconciled to the NARROWED contract

Read first: canonical `detail` at snapshot318856, the whole handoff through
`work-events` (events316915 -> 318857), and both `thread` messages on T316915
(316915 and 318836, total 2, no pagination). Then the bound dossier.

### THE SCOPE CHANGED MID-CLAIM, and this is what happened

The FINDING and PLAN I bound at claim time carried the 01:06:05Z ruling: status
must perform NO filesystem write, SQLite sidecars included, and must succeed on
a cleanly closed WAL store under an unwritable directory. I implemented exactly
that -- a `baton_v12.sqlite_snapshot` module that read the store's bytes and its
write-ahead log's own valid committed frames, assembled the last committed
transaction in memory, verified the instant held still before and after the read
and refused otherwise, served it through an in-memory `query_only` connection,
and new `JobStore.open_snapshot`/`ControlStore.open_snapshot` openers over it.
It worked: the closed-WAL/no-sidecar store read under a directory this process
was proved unable to write, with the file set byte-identical and nothing created.

While that was under test the owner reversed the requirement. The 01:24:52Z
FINDING entry, the current PLAN checkpoint and `v12/DESIGN.md` OBS-1 now say the
concern is DATABASE STATE and not SQLite's internal sidecar handling, that
normal sidecar and locking behaviour is acceptable, that status need not succeed
in an unwritable directory with missing sidecars, and -- explicitly -- "do not
build a custom snapshot reader solely to avoid SQLite-managed effects".

SO I REVERTED IT RATHER THAN ARGUING FOR IT. The snapshot module is gone and
`job_manager/store.py`, `worker_manager/store.py`, `tools/job_manager.py` and
`tests/job_manager/test_tool.py` were restored to HEAD -- the exact bytes of the
previously reviewed candidate -- before this claim's real work started. Nothing
of the snapshot reader survives in the tree. `git show HEAD:<path> > <path>` was
used for the restore; no Git state was mutated.

### REVALIDATED AGAINST THE SELECTED CONTRACT, as the PLAN requires

The 01:24:52Z contract is: validated SQLite read-only connections; no change to
application data or schema; no initialization or migration; no writable retry;
clear reporting when a read-only open or query fails; authority/schema
validation, status shape and submit/serve behaviour preserved.

Everything but the reporting clause was ALREADY MET by the accepted candidate
and I confirmed each against the current tree rather than against the record:

  `JobStore.open_readonly` -- `mode=ro`; absent or non-regular path refused
  before SQLite is asked; empty database refused rather than initialized; schema
  must be EXACTLY this build's, through the non-mutating `_recognized` and never
  `_adopt`, so no migration; no `PRAGMA journal_mode = WAL`; no `immutable=1`;
  every failure closes the handle and no failure path reopens writably; the
  Authority binding still proved.

  `ControlStore.open_readonly` -- `mode=ro`; existing regular store required;
  empty store refused without initializing; `_adopt` validates and does not
  migrate; the handle is marked `readonly` so every ACTION on it refuses.

  `tools/job_manager._status` -- both stores through those openers, for the
  ordinary and the `--observe` branch; `_submit` and `_serve` still use the
  writable `_job_store`. UNCHANGED THIS CLAIM, and its bytes are HEAD's.

### THE ONE GAP THE NARROWED CONTRACT LEFT, and the correction

"Report an open/query refusal clearly" was NOT met, and this is the clause the
narrowing kept rather than dropped. Both openers reported the exception CLASS
and nothing else:

    the Job store at '...' could not be read through its non-writing
    opener (OperationalError); no write-capable fallback was attempted

    the existing manager store could not be read through its non-writing
    opener (OperationalError); no write-capable fallback was attempted

Three things are wrong with that, and all three are concrete:

  SQLITE'S OWN WORDS WERE DROPPED. The Authority and the integration
  coordinator openers -- the siblings this file's own docstrings cite -- already
  report `type(failure).__name__: failure`. These two kept only the class.

  "OperationalError" IS THE SAME ANSWER FOR DIFFERENT CONDITIONS. An unwritable
  directory holding a closed WAL store and an unreadable file both arrive as
  `OperationalError`, and the remedies are not the same. The discovery evidence
  in the FINDING is exactly that string, diagnosed by hand afterwards.

  THE CONTROL STORE NAMED NO STORE AT ALL. A status names two stores and could
  fail without saying which one an operator should look at.

The correction is one shared public helper, `worker_manager.store.reading_refusal`,
used by both openers. It is in that module and not copied into the Job store's
for this file's own stated reason: `seal_refusal` and `revive_refusal` live there
because a second implementation would be a second chance to get one wrong, and a
diagnostic an operator depends on is no different. It reports the store, the
exception class, SQLite's words rendered inertly and bounded, and then the three
facts that separate the conditions SQLite spells the same way -- whether this
process may read the store, may write it, and may write the DIRECTORY a sidecar
would have to be created in -- plus which sidecars are beside it. When ALL of
the known-unreadable shape's conditions hold (the store's own header says WAL,
the directory is not writable by this process, and no `-wal`/`-shm` is present)
that shape is named outright with its documented remedy. The facts are a
DIAGNOSTIC AND NEVER A DECISION: nothing branches on them to choose a different
open, they are read after SQLite has already refused.

What it now says, measured:

    the Job store at '/.../jobs.sqlite3' could not be read through its
    non-writing opener (OperationalError: 'attempt to write a readonly
    database'); no write-capable fallback was attempted and nothing was
    changed. This process may read and may write the store, and may not write
    its directory '/...'; the SQLite sidecars beside it are none. THAT IS THE
    KNOWN UNREADABLE SHAPE: ... Read a stable copy of the store, or give this
    process write access to the directory. A status is not required to read
    this shape and will not open the store writably to do it.

    the Job store at '/.../unreadable.sqlite3' could not be read through its
    non-writing opener (OperationalError: 'unable to open database file'); ...
    This process may not read and may not write the store, and may write its
    directory '/...'; the SQLite sidecars beside it are none.

### Documentation aligned, not just code

`JobStore.open_readonly` and `ControlStore.open_readonly` now state the boundary
the owner selected -- `mode=ro` is read-only over the DATABASE and not over the
directory, SQLite's sidecars are accepted, no snapshot reader is wanted -- so a
reader cannot take the old "filesystem-read-only" reading from the docstrings.
`tests/job_manager/test_tool.py`'s class docstring, `unchanged()` and the
closed-WAL case say the same: these are the SELECTED CONTRACT and no longer an
unresolved limit awaiting a decision.

### Focused acceptance -- test paths and reasons

Under the standing test-change authority (owner 2026-09-13, AGENTS.md), recorded
here as that ruling requires:

  `tests/job_manager/test_tool.py` -- the closed-WAL/read-only-directory case
  keeps its refusal expectation and now also asserts SQLite's words, the
  measured condition and the named shape; its `chmod` became `denied()`, which
  PROBES the denial and fails the case if this process could still write the
  directory (review 2026-09-30T15-46-18Z asked for exactly that, and the FINDING
  forbids chmod as proof); a new `declared_journal_mode()` asserts the WAL
  precondition from the store's own header rather than assuming it. FOUR NEW
  CASES: an unreadable store refused with a DIFFERENT report and no known-shape
  paragraph; a two-store status refusal that says WHICH store; the control
  store's own refusal naming its own store; and a refused read never retried
  with write access, with both writable openers replaced by ones that fail if
  called and the file set measured unchanged. Reframing edits are docstrings and
  comments; no existing assertion was weakened or removed.

  `tests/job_manager/test_store_readonly.py` -- one new case at the opener's own
  boundary for the clear report.

  `tests/manager/test_store.py` -- one new case for the control store's half,
  which is the one that named no path.

### Measured

    tests.job_manager.test_tool ......................... 70 PASS   0.54s
    tests.job_manager.test_store_readonly
      + tests.manager.test_store ........................ 95 PASS   0.32s
    test_tool + test_store_readonly + test_store
      + test_status + test_recovery + tests.manager.test_store
      + test_workspaces + test_w197661_verifier
      + tests.tools.test_stage_execution_status_hardening
      + tests.authority.test_store
      + tests.integration.test_managed_storage
      + test_coordinator ............................... 941 PASS   9.23s
    tests.tools.test_execution_limits
      + tests.job_manager.test_sweep + test_ending ..... 244 PASS  73.2s
    tests.tools.test_stage_execution .................. 477 PASS 201.6s

FOUR MUTATIONS, each removing one thing the new report claims -- SQLite's words,
the known-shape paragraph, the store's name, the measured facts -- ALL FOUR
CAUGHT; unmutated and restored runs clean. `MUTATIONS-318857.json`, driver
`mutate-318857.py`.

Cumulative verification this claim: roughly 285 measured seconds of test
execution plus the four mutation runs over the 165-case vector. The snapshot
reader that was reverted cost a further ~350s of runs whose evidence is
superseded and is not claimed as acceptance of anything.

No live provider or engine run, no deployed store read, repair or cleanup, no
integration act, no credential change, no Git mutation, and no graph act beyond
this Work's own claim and handoff.

### Files

Product: `v12/python/src/baton_v12/worker_manager/store.py` (2c2d56a16c71),
`v12/python/src/baton_v12/job_manager/store.py` (593bcee78c10). Product tests:
`v12/python/tests/job_manager/test_tool.py` (2423bea62f96),
`v12/python/tests/job_manager/test_store_readonly.py` (6366ab826560),
`v12/python/tests/manager/test_store.py` (d5d682a37757). Dossier: this record,
`CANDIDATE-318857.json`, `MUTATIONS-318857.json`, `mutate-318857.py`.
`v12/python/tools/job_manager.py` is HEAD's and was not touched this claim.
FINDING, PLAN and the reviews are the reviewer's and prompt's; untouched.

### NOT CLAIMED, and one observation for the reviewer

The deployed store is not repaired and was not read this claim, and the
owner-environment cause remains only partly classified -- no corruption
conclusion is drawn. A status under an unwritable directory with no sidecars
still REFUSES, which is now the selected contract rather than a gap.

ONE THING I FOUND AND DELIBERATELY DID NOT CHANGE. The PLAN asks to "preserve
ordinary consistent SQLite observations", and `job_manager.projection.status`
reads its rows through many separate autocommit statements with no enclosing
read transaction on the Job store -- so on a store a manager is actively
advancing, different parts of one status document can come from different
instants. The control store has `snapshot()` for exactly this; the Job store's
reader has no equivalent boundary. That is a pre-existing property rather than
anything this claim changed, wrapping it would alter `status()` for `serve`'s
callers as well, and the narrowed contract does not name it. Reported here for
the reviewer to classify rather than fixed inside this handoff.


## Claim 319137 (baton.claude, impl) -- review R1/R2 correction

Read first: canonical `detail` at snapshot319135 (queued, unclaimed, routed
baton.impl, next baton.decide, no obligations, no open blockers), then the
standalone claim; then `work-events` complete -- the first page plus the
`after=318669` continuation, so events316915 through 319137 with nothing
filtered -- and `thread` T316915, all 4 messages, `next_after` null so no
pagination remained. Then review-2026-10-18T01-45-33Z.md and the current
FINDING/PLAN, whose checkpoint is the reviewer's 01:45:33Z one over the
01:24:52Z owner contract.

Two changes were requested. Both are done and nothing else was touched.

### R1 -- THE REVIEWER IS RIGHT, AND I REPRODUCED IT BEFORE FIXING IT

The claim-318857 helper decided the WAL/permission diagnosis ITSELF, from the
store's header byte 19 and the absence of sidecars. Run against the reviewer's
own fixture -- 120 bytes of `x` with byte 19 set to 2, no sidecars, containing
directory at 0500 -- `JobStore.open_readonly` produced exactly what R1 says:

    ... (DatabaseError: 'file is not a database'); ... THAT IS THE KNOWN
    UNREADABLE SHAPE: the store's own header says WAL, a clean close removed
    its -wal and -shm ... Read a stable copy of the store, or give this
    process write access to the directory.

Three mistakes in one, and all three are the same mistake: a format version
read out of a file with NO SQLITE SIGNATURE AT ALL; a CLEAN CLOSE asserted as
history from the mere absence of two files; and a root cause inferred where the
driver had already given a different one. The diagnostic contradicted the error
it existed to clarify.

THE CORRECTION IS THAT THE DIAGNOSIS IS SQLITE'S AND NOT THIS BUILD'S. SQLite
already separates these conditions itself, in the EXTENDED RESULT CODE this
module reads for contention a few screens up -- and measured here rather than
assumed:

    cleanly closed WAL store, directory 0500 ... SQLITE_READONLY_DIRECTORY 1544
    120 bytes of `x`, byte19 = 2 ............... SQLITE_NOTADB            26
    store file chmod 0 ......................... SQLITE_CANTOPEN          14

So `_declares_wal` is GONE -- the header byte is not read at all any more --
and the hint is opened by exactly one thing, `_readonly_directory`, which is
true only when the driver's own code is `SQLITE_READONLY_DIRECTORY`. A failure
carrying no structured code earns no hint, which is this module's existing rule
that free-form prose does not decide storage questions. The hint is also now
phrased as SQLite's finding and a CONDITION -- "SQLITE REPORTS THE DIRECTORY AS
THE OBSTACLE ... if that is this store's condition" -- and claims nothing about
how the store came to be in that state. `sqlite_errorname` is reported too,
because it is the driver's own answer: an operator now sees
`OperationalError/SQLITE_READONLY_DIRECTORY` rather than three different
conditions wearing one exception class.

The measured facts stay, and stay where they were: readable, writable,
directory-writable and which sidecars are present. R1 asks for observed facts
to remain authoritative, and these are observations. Absent sidecars are
reported as absent and no longer as evidence of anything.

Measured after the change, all four shapes, both openers:

    MALFORMED byte19=2, dir 0500 ... DatabaseError/SQLITE_NOTADB, NO hint
    closed WAL, dir 0500 ........... OperationalError/SQLITE_READONLY_DIRECTORY, hint
    control store, same ............ same, hint -- the helper is shared
    unreadable file, dir writable .. OperationalError/SQLITE_CANTOPEN, NO hint

### R2 -- the prior account is restored, and this record is append-only now

Claim 318857 wrote PROGRESS.md whole and so replaced claim 316919's account.
Recovered from the committed copy at HEAD and verified by digest: the recovered
bytes are `83e96b576f85`, which is exactly the PROGRESS hash claim 316919's own
pass recorded, so what is above is that account in its original words rather
than a reconstruction. Claim 318857's account follows it unedited, and this one
follows that. The header now states the append-only rule so the next episode
does not have to rediscover it. No Git state was mutated.

### Focused acceptance -- test paths and reasons

Standing test-change authority (owner 2026-09-13); paths and reasons recorded
here as that ruling requires.

  `tests/job_manager/test_tool.py` -- TWO NEW CASES, which are R1's negative:
  a malformed file carrying byte19=2 under a directory whose denial is PROVED,
  asserting `SQLITE_NOTADB`, SQLite's words, the measured facts, and the
  ABSENCE of the directory hint, of "wal-index", of "stable copy" and of "clean
  close"; and the same negative at `ControlStore.open_readonly`, because the
  helper is shared and a correction holding for one store only would be half a
  fix. A `malformed()` helper builds the fixture and asserts the precondition
  that makes the case a regression guard -- `declared_journal_mode` still reads
  `wal` off that file, so the heuristic that used to decide the diagnosis WOULD
  have fired. The positive closed-WAL case and the unreadable-file case are
  retained and now assert `SQLITE_READONLY_DIRECTORY` / `SQLITE_CANTOPEN` and
  the corrected hint prose.

  `tests/job_manager/test_store_readonly.py` and `tests/manager/test_store.py`
  -- the existing new cases from claim 318857 now also assert `SQLITE_NOTADB`
  and the ABSENCE of the directory hint for a non-database input.

No assertion was weakened or removed; no test from another Work was touched.

### Measured

    tests.job_manager.test_tool + test_store_readonly
      + tests.manager.test_store ....................... 167 PASS   0.86s
    that vector + test_store + test_status + test_recovery
      + tests.manager.test_workspaces + test_w197661_verifier
      + tests.tools.test_stage_execution_status_hardening
      + tests.authority.test_store
      + tests.integration.test_managed_storage
      + test_coordinator ............................... 943 PASS   9.30s
    tests.tools.test_execution_limits
      + tests.job_manager.test_sweep + test_ending ..... 244 PASS  71.9s
    diff whitespace check ............................. clean

SIX MUTATIONS, all six caught, unmutated and restored runs clean. One of them is
R1 ITSELF AS A REGRESSION: `_readonly_directory` forced to answer true, which
reinstates the defect of opening the hint for every failure -- 5 failures. The
others remove SQLite's words, SQLite's condition name, the hint entirely, the
store's name and the measured facts. `MUTATIONS-319137.json`, driver
`mutate-319137.py`.

Cumulative verification spending across this Work's three implementer claims:
claim 316919 about 198s; claim 318857 about 285s plus a further ~350s on the
reverted snapshot reader, whose evidence is superseded and is claimed as
acceptance of nothing; claim 319137 about 82s of focused vectors plus seven runs
of the 167-case vector for the mutation check. `tests.tools.test_stage_execution`
was NOT rerun this claim: the product change is confined to one refusal
message's prose, that suite passed 477 in 201.6s on claim 318857 against these
same openers, and its vector does not reach `reading_refusal`. Stated so the
reviewer can require it rather than assume it was run.

### Files

Product: `v12/python/src/baton_v12/worker_manager/store.py` (587552eb2699) --
the only product file changed this claim; `v12/python/src/baton_v12/job_manager/store.py`
(593bcee78c10) is unchanged from candidate318857 and still matches the hash the
review verified. Product tests: `tests/job_manager/test_tool.py` (e2cf65ee2804),
`tests/job_manager/test_store_readonly.py` (330aa45e66c7),
`tests/manager/test_store.py` (a92d2167236b). Dossier: this record,
`CANDIDATE-319137.json`, `MUTATIONS-319137.json`, `mutate-319137.py`.
`v12/python/tools/job_manager.py` remains HEAD's bytes and was not touched in
either of the last two claims. FINDING, PLAN and the reviews are the reviewer's
and prompt's; untouched.

### NOT CLAIMED

The deployed store is still not repaired and was not read; the owner-environment
cause remains only partly classified and no corruption conclusion is drawn. A
status under an unwritable directory with no sidecars still REFUSES, which is
the selected contract. The hint is a HINT: it reports what SQLite reported and
what follows from it, and it does not establish that this particular store was
closed cleanly or that the directory is the only thing wrong with it.

The projection consistency concern I reported last claim was independently
reproduced by the reviewer as a `KeyError: job-a/implementation` crash and is
recorded as W319114, parked with no dependency edge. I did NOT expand this patch
to fix it, as the handoff directs, and the review's note that a future fix must
honour DB-1/DB-4 rather than wrapping status in one transaction is the direction
I would have gone wrong in -- recorded here so the next claim on W319114 has it.

A human Git checkpoint remains due on eventual acceptance, not on this routine
correction pass; the suggested message is unchanged:
`v12: report a refused read-only store open clearly (W316915)`.
