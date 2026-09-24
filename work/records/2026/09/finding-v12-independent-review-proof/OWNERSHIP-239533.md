# File ownership for W239533

Claim 244629, baton.claude.

## What this claim created and owns

    attachment.py             the supported checkpoint-attachment arrangement
    test_attachment.py        15 real-boundary cases over review_cycles
    review_bindings.py        the review-only composer
    test_review_bindings.py   19 composition cases over a real line
    verify.py                 the measurement that writes the receipt
    verification-1.json/.log  that receipt
    records_244629.py         this claim's dossier writer
    PROGRESS.md               this implementer's record
    OWNERSHIP-239533.md       this file

`FINDING.md` and `PLAN.md` were appended to and rewritten respectively, as the
owner reroute directs ("Update FINDING/PLAN for the satisfied prerequisite").

## What it READS and did not edit

`work/records/2026/09/finding-v12-single-implementation-proof/` in full. It is
W239528's, that Work is open pending owner disposition, and its accepted live
review is this Job's prerequisite. `review_bindings.py` IMPORTS its
`baseline_bindings` helpers -- reuse, not modification -- and `verify.py`
records that module's digest so a drift is visible in the next receipt.

`work/records/2026/09/finding-v12-review-job-preparation/` in full. It is
W244180's. Nothing here was written into it; G1, G2 and G3 are answered or
carried forward in this dossier's own files.

`work/records/2026/09/finding-v12-managed-session-resume/` was not touched.

## Product and deployment

**No file under `v12/` was edited.** `tests.manager.test_review_cycles` is
imported as a fixture and `review_cycles`, `review_driver` and
`stage_execution` are read; all four digests are recorded in the receipt.

`/home/sl/baton-runs/single-implementation-244216/` was READ and not modified.
Its control store is opened only through SQLite `mode=ro`. That read CREATED
`control.sqlite3-shm` and a zero-length `control.sqlite3-wal` beside it, which
is what SQLite does when a `wal` database is opened without `immutable=1`; the
store's own bytes, its rows and the line state are unchanged, and `PROGRESS.md`
records the trade and the exact files. No image was built, retagged or removed.
No store was migrated, no runtime started and no Git operation performed.

## Claim 244759 -- R1 corrected

Edited: `attachment.py`, `test_attachment.py`, `review_bindings.py`,
`test_review_bindings.py`, `verify.py`, `FINDING.md`, `PLAN.md`, `PROGRESS.md`,
this file. Added: `records_244759.py`, `verification-2.json/.log`.

`verification-1.json/.log` is claim 244629's receipt and is KEPT rather than
replaced: it measured the implementation R1 refused, and deleting it would
delete the evidence of what was corrected.

**No file under `v12/` was edited and NO DEPLOYED STORE WAS OPENED under this
claim.** The producer's retained control store was not read this turn at all;
the `control.sqlite3-shm` and zero-length `control.sqlite3-wal` that claim
244629's survey created beside it are preserved and disclosed, not cleaned up.
Both images, W244180's dossier and W236087's dossier are untouched. W239528 is
now canonically closed satisfying and its dossier remains read-only here.

## Claim 244877 -- the two P2 test items

Edited: `test_attachment.py`, `verify.py`, `FINDING.md`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `records_244877.py`,
`verification-3.json/.log`.

`verification-1.json/.log` and `verification-2.json/.log` are earlier claims'
receipts and are KEPT: each records what the following round corrected.

**No file under `v12/` was edited and no deployed store was opened.** The
product's own admission fixtures (`tests.manager.test_offers`,
`tests.manager.input_roots`) are imported read-only and their digests are
bound in the receipt. The `control.sqlite3-shm` and zero-length
`control.sqlite3-wal` that claim 244629's survey created beside W239528's
retained control store are preserved and still disclosed. Both images,
W244180's dossier and W236087's dossier are untouched.

The reviewer's files -- `review-2026-09-23T04-40-30Z.md`,
`review-2026-09-23T04-50-12Z.md`, `review-evidence-244729.json`,
`review-evidence-244799.json` and `review-tests-244799.log` -- are append-only
history and were not modified.

## Claim 247159 -- the review supervisor and the packet

Added: `review_supervisor.py`, `test_review_supervisor.py`,
`SELECTIONS-239533.json`, `OPERATOR-239533.md`, `records_247159.py`,
`verification-4.json/.log`.

Edited: `test_review_bindings.py`, `verify.py`, `FINDING.md`, `PLAN.md`,
`PROGRESS.md`, this file.

**No file under `v12/` was edited and no deployed store was opened.**
W239528's `baseline.py` is IMPORTED and its digest is bound in
`review_supervisor.BASELINE_SHA256` and in the receipt; it was not edited,
copied or monkeypatched. Earlier receipts are kept: each records what the
following round corrected. The `control.sqlite3-shm` and zero-length
`control.sqlite3-wal` that claim 244629's survey created beside W239528's
retained control store are preserved and still disclosed. Both images,
W244180's dossier and W236087's dossier are untouched, and every reviewer file
in this dossier is append-only history that was not modified.

## Claim 247318 -- R1 through R4

Edited: `review_supervisor.py`, `attachment.py`, `test_review_supervisor.py`,
`test_attachment.py`, `OPERATOR-239533.md`, `verify.py`, `FINDING.md`,
`PLAN.md`, `PROGRESS.md`, this file. Added: `records_247318.py`,
`verification-5.json/.log`.

**No file under `v12/` was edited and no deployed store was opened.**
W239528's `baseline.py` is imported and unchanged at its accepted digest
`f27f3cd7...3df18fd5`, which `review_supervisor.BASELINE_SHA256` binds and the
receipt records. The `control.sqlite3-shm` and zero-length
`control.sqlite3-wal` beside W239528's retained control store are preserved
and still disclosed. Both images, W244180's dossier and W236087's dossier are
untouched, and every reviewer file in this dossier is append-only history that
was not modified.

## Claim 247423 -- the selected product change, and R3a

Added: `OWNER-PRODUCT-CHANGE-247423.md`, `PRODUCT-CHANGE-247423.json`,
`records_247423.py`, `verification-6.json/.log`.

Edited in this dossier: `review_supervisor.py`, `review_bindings.py`,
`test_review_supervisor.py`, `verify.py`, `FINDING.md`, `PLAN.md`,
`PROGRESS.md`, this file.

PRODUCT PATH EDITED, under owner selection 247421 and pinned before the edit:

    v12/python/tools/stage_execution.py
        before ebc9be29d2bd23cf129afe33943f5336832df2ef24256c724708004220032896
        after  318e9a4bdf111cb3b93bddbe63c6d6fe6911702023db7196c507fbae54d18d11

**Nothing else under `v12/` was edited**, and no product test was weakened:
`tests/tools/test_stage_execution.py` is unmodified. The four new cases for
the boundary live in this dossier and drive the real product function.

`review_driver.open_correction` is untouched -- the decision to call it moved,
the act did not. W239528's `baseline.py` is unchanged at its accepted digest,
both images are unchanged, no deployed store was opened, the disclosed
`control.sqlite3-shm` and zero-length `control.sqlite3-wal` beside W239528's
retained control store are preserved, and every reviewer file in this dossier
is append-only history that was not modified.

## Claim 247666 -- item 5, and a comment repair

Added: `preexisting_errors.py`, `PREEXISTING-ERRORS-247666.json`,
`records_247666.py`, `verification-7.json/.log`.

Edited in this dossier: `test_review_bindings.py`, `PRODUCT-CHANGE-247423.json`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file.

PRODUCT PATH: `v12/python/tools/stage_execution.py` moved from
`318e9a4bdf111cb3b93bddbe63c6d6fe6911702023db7196c507fbae54d18d11` to
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801` for a
COMMENT REPAIR ONLY -- a shell backtick had eaten the word `routed` from one
comment line. No behaviour changed and no test moved with it.

**Nothing else under `v12/` was edited** and no product test was weakened.
W239528's `baseline.py` is unchanged at its accepted digest, both images are
unchanged, no deployed store was opened, the disclosed `control.sqlite3-shm`
and zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.

## Claim 247757 -- the admitted-reviewer fixture

Added: `test_review_lifecycle.py`, `records_247757.py`.

Edited in this dossier: `PLAN.md`, `PROGRESS.md`, this file.

**No file under `v12/` was edited under this claim** -- the product path stays
at `6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, the
digest claim 247666 recorded. W239528's `baseline.py` is unchanged at its
accepted digest and is SUBCLASSED for its fixture, not modified. No deployed
store was opened, both images are unchanged, the disclosed
`control.sqlite3-shm` and zero-length `control.sqlite3-wal` are preserved, and
every reviewer file in this dossier is append-only history that was not
modified.

## Claim 247823 -- the settled lifecycle

Edited in this dossier: `test_review_lifecycle.py`, `test_review_supervisor.py`,
`review_supervisor.py`, `verify.py`, `PLAN.md`, `PROGRESS.md`, this file.
Added: `records_247823.py`, `verification-8.json/.log`.

**No file under `v12/` was edited under this claim.** The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. W239528's
`baseline.py` is unchanged at its accepted digest and is SUBCLASSED for its
fixture, not modified. No deployed store was opened, both images are unchanged,
the disclosed `control.sqlite3-shm` and zero-length `control.sqlite3-wal` are
preserved, and every reviewer file in this dossier is append-only history that
was not modified.

## Claim 247870 -- item 3's gate order, bounds and exact outstanding identity

Edited in this dossier: `test_review_lifecycle.py`, `verify.py`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `records_247870.py`,
`verification-9.json/.log`.

**No file under `v12/` was edited under this claim.** The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. W239528's
`baseline.py` is unchanged at its accepted digest: the recording gate
SUBCLASSES `baseline.AdmissionGate` and the patch is on
`review_supervisor.AdmissionGate`, the name this module under test resolves.
No deployed store was opened, both images are unchanged, the disclosed
`control.sqlite3-shm` and zero-length `control.sqlite3-wal` are preserved, and
every reviewer file in this dossier is append-only history that was not
modified.

## Claim 247908 -- the reached bound and the observed shutdown

Edited in this dossier: `test_review_lifecycle.py`, `verify.py`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `records_247908.py`,
`verification-10.json/.log`.

**No file under `v12/` was edited under this claim.** The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. W239528's
`baseline.py` is unchanged at its accepted digest. No deployed store was
opened, both images are unchanged, the disclosed `control.sqlite3-shm` and
zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.

## Claim 247947 -- the successor manager source

Added: `snapshot_247947.py`,
`MANAGER-SOURCE-independent-review-247947.json`, `records_247947.py`,
`verification-11.json/.log`.

Edited in this dossier: `SELECTIONS-239533.json`, `OPERATOR-239533.md`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file.

OUTSIDE THE CHECKOUT, NEW and replacing nothing:

    /home/sl/baton-runs/independent-review-247947/manager-source
        106 files, carrying the correction_policy change

PRESERVED and verified as part of the build:

    /home/sl/baton-runs/single-implementation-242687/manager-source
        W239528's producer snapshot, byte-identical to its own manifest

**No file under `v12/` was edited under this claim.** The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. W239528's
dossier was READ ONLY -- `MANAGER-SOURCE-242687.json` was opened to verify the
predecessor and nothing was written into that dossier. Both images are
unchanged, no deployed store was opened, the disclosed `control.sqlite3-shm`
and zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.

## Claim 247997 -- the documented commands on the successor bytes

Edited in this dossier: `test_review_bindings.py`, `OPERATOR-239533.md`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file. Added:
`records_247997.py`, `verification-12.json/.log`.

**No file under `v12/` was edited under this claim, and the successor snapshot
was not modified** -- it was READ, with `PYTHONPATH` bound to it, and its
manifest compared against the packet the documented command wrote. The product
path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` is unchanged at its accepted digest, its producer snapshot is
untouched, both images are unchanged, no deployed store was opened, the
disclosed `control.sqlite3-shm` and zero-length `control.sqlite3-wal` are
preserved, and every reviewer file in this dossier is append-only history that
was not modified.

## Claim 248032 -- the startup, through `main`

Edited in this dossier: `test_review_bindings.py`, `OPERATOR-239533.md`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file. Added:
`records_248032.py`, `verification-13.json/.log`.

**No file under `v12/` was edited under this claim and the successor snapshot
was not modified.** It was READ, with `PYTHONPATH` bound to it. The product
path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` and its producer snapshot are unchanged, both images are
unchanged, no deployed store was opened -- the Job and control stores `main`
opened are the disposable fixture's -- the disclosed `control.sqlite3-shm` and
zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.

## Claim 248090 -- the no-progress structure

Edited in this dossier: `test_review_lifecycle.py`, `verify.py`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `records_248090.py`,
`verification-14.json/.log`.

**No file under `v12/` was edited under this claim and the successor snapshot
was not modified.** The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` and its producer snapshot are unchanged, both images are
unchanged, no deployed store was opened, the disclosed `control.sqlite3-shm`
and zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.

## Claim 248135 -- the Job selector

Edited in this dossier: `test_review_lifecycle.py`, `verify.py`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `records_248135.py`,
`verification-15.json/.log`.

**No file under `v12/` was edited under this claim and the successor snapshot
was not modified.** The inherited `states` helper in
`tests/tools/test_stage_execution.py` is UNCHANGED -- the selection is
overridden in this dossier's own fixture. The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` and its producer snapshot are unchanged, both images are
unchanged, no deployed store was opened, the disclosed `control.sqlite3-shm`
and zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.

## Claim 248173 -- the serving classification, aligned

Edited in this dossier: `review_supervisor.py`, `test_review_lifecycle.py`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file. Added:
`records_248173.py`, `verification-16.json/.log`.

**No file under `v12/` was edited under this claim and the successor snapshot
was not modified.** The change is in this dossier's own supervisor: it now
calls the SAME `_origin` the shutdown path already used, which is W239528's
accepted helper imported unchanged. The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` and its producer snapshot are unchanged, both images are
unchanged, no deployed store was opened, the disclosed `control.sqlite3-shm`
and zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.

## Claim 248209 -- the origin read, corrected

Edited in this dossier: `review_supervisor.py`, `test_review_lifecycle.py`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file. Added:
`records_248209.py`, `verification-17.json/.log`.

**No file under `v12/` was edited under this claim and the successor snapshot
was not modified.** The change is in this dossier's own supervisor.
`baseline._guarded` is UNCHANGED and still imported for the places where
catching `BaseException` into a real `interrupted` list is what is wanted; what
changed is that this one call no longer uses it. The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` and its producer snapshot are unchanged, both images are
unchanged, no deployed store was opened, the disclosed `control.sqlite3-shm`
and zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.

## Claim 248263 -- the packet assembled

Edited in this dossier: `OPERATOR-239533.md` (rewritten as the packet),
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file. Added: `packet.py`,
`test_packet.py`, `EVIDENCE-239533.json`, `records_248263.py`,
`verification-18.json/.log`.

**No file under `v12/` was edited under this claim, no test of the supervisor
or the composer was changed, and the successor snapshot was not modified.** The
product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` is unchanged at
`f27f3cd766f9271c4b3eddb6c657bca4770d18c11a74f377e717bef23df18fd5`, its
producer snapshot is unchanged, both images are unchanged, no deployed store
was opened, the disclosed `control.sqlite3-shm` and zero-length
`control.sqlite3-wal` are preserved, and every reviewer file in this dossier is
append-only history that was not modified.

`EVIDENCE-239533.json` is deliberately absent from `verify.py`'s `OWNED`
digests: a document regenerated by the same program that writes the receipt
cannot carry its own digest in it.

## Claim 248565 -- the live attribution and the template fix

Edited in this dossier: `review_bindings.py`, `test_review_bindings.py`,
`test_packet.py`, `packet.py`, `OPERATOR-239533.md`, `verify.py`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `attribution.py`, `ATTRIBUTION-248565.json`,
`records_248565.py`, `verification-19.json/.log`, and `EVIDENCE-239533.json`
regenerated.

**NOT edited, and deliberately:** every file under `live-review-248377/` is the
reviewer's retained evidence and was READ ONLY -- the attribution export is a
new file at the dossier's top level rather than an addition to their directory.
`SELECTIONS-239533.json` still ships all twelve `<OWNER: ...>` choices
unresolved; the owner's resolved values live in that run's own documents and
are not copied back. No file under `v12/` was edited and the successor snapshot
was not modified.

**The deployed store WAS OPENED, read-only and through the supported opener.**
That is what R1 asked for and what the owner's 248520 pass authorized
("verify retained subject/result attribution ... through supported readers").
It wrote nothing; SQLite recreated `control.sqlite3-shm` and a zero-length
`control.sqlite3-wal` beside the store, as it did at claim 244629, and they are
left in place.

The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` at
`f27f3cd766f9271c4b3eddb6c657bca4770d18c11a74f377e717bef23df18fd5`, its
producer snapshot unchanged, both images unchanged, and every reviewer file in
this dossier is append-only history that was not modified.
