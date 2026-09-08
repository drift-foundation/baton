# Plan

## Current state — independently signed off, owner acceptance pending

Review claim113125, review-2026-09-07T20-11-58Z.md, resolves the remaining three
findings and signs off the exact four candidate hashes. All83 focused tests pass;
independent source-substitution reads remain bound to the held descriptor. The
four Git vectors and parsers also pass against existing real committed objects.
Full production-runner composition remains W110774 scope. The earlier blanket
unproved Git interoperability statement below is superseded to this limited
extent; historical broad failures remain unwaived.

Return W112630 to baton.ops for acceptance/closure. W110935 remains gated until
that disposition, then revalidates the accepted API before implementing its
worker entry/import/result scope. No additional child implementation is queued.

## Historical handoff — second correction claim113036, awaiting independent review

The three remaining findings of review-2026-09-07T19-51-54Z.md are corrected
inside the existing four-path scope, and each of that review's reproductions now
resolves. The root is TRAVERSED from the filesystem root one component at a
time, so an alias, an alias with a trailing dot and a linked ancestor all refuse
while the valid root still reads. The extraction is BOUND to an open directory
descriptor: the runner contract is now runner(argv, *, directory), every vector
lost its repository operand, and a transient swap of the pathname cannot
redirect a read. Shared content is charged once, keyed by the retained object
identity, so a blob two rows share no longer refuses as oversized against a
bound its own reader accepts. The re-run is retained at
evidence/correction-113036/.

One claim from the previous entry is WITHDRAWN, there and in FINDING.md: a
before-and-after pathname check is detection, and I described it as if it were
the binding review112857 asked for. The post-extraction owner re-resolution is
kept, because it answers a different question.

Focused module 83 passing. Measured against the reviewed candidate: 72 before,
83 after, 0 removed, 11 changed, 11 added, every change a mechanical operand
move the pinned interface change forced. The FINDING pin predicted four such
methods and the measured answer is eleven; that under-count is corrected there.
Subtree gate 4913 tests, distribution unchanged, count moved by exactly the 11
added. Registry entry byte-identical to the reviewed one. Real Git command
interoperability remains unproved and is stated as such.

## Superseded — remaining corrections from review112989

review-2026-09-07T19-51-54Z.md verifies direct/interior link refusal, persistent
source/account drift detection and the corrected251-path manifest limit. All72
focused tests pass; all55 prior methods and original evidence snapshots match.

Three probes still require correction: alias-plus-dot/root ancestor links pass;
a transient source swap restored before the second nomination publishes without
bound reads; shared blob content can falsely exceed the producer budget before
deduplication. evidence/review-112989/ retains exact candidates and reproductions.

Return to baton.impl within the existing four-path scope. Complete root-path
descriptor traversal, bind runner reads to the proved source while keeping
post-extraction checks, and reconcile early shared-content budget accounting.
Pin the concrete runner capability/lifetime contract before coding. Add focused
boundary cases, preserving72 existing tests and all evidence. No parent use,
unrelated registry/core repair, Git mutation or live work. W110935 remains gated.
This supersedes the pending-acceptance claims below; the verified manifest fix
and251-path bound remain current.

## Previous state — correction claim112902, awaiting independent review

All three P1s are corrected inside the existing four-path scope, and each of the
review's own reproductions now refuses: symlinked evidence, blobs and root are
refused at a descriptor-bound every-component traversal; a line directory
replaced during extraction is caught by a second nomination and the complete
accepted account, checkpoint, line and seven projections are re-resolved and
compared; and every digest, count and size bound is computed before the rename,
with MAX_PATHS now DERIVED as (512 - 9) // 2 = 251 from the manifest's own
canonical array bound. The reviewer's unmodified probe and a re-run of its three
seams are retained at evidence/correction-112902/.

The revised bounds and interface were pinned in FINDING.md before the code was
written. One check I built and then removed — an open directory descriptor
re-fstat-ed after extraction, which can never fail because a descriptor names
one inode whatever happens to the name — is recorded there rather than left in.

Focused module 72 passing, all 55 earlier cases preserved. Subtree gate 4902
tests, 11 failures and 1 error, distribution unchanged and the count moved by
exactly the 17 tests added. The registry entry is byte-identical to the one the
review checked. Historical registry and broad failures remain unwaived, parent
W110935 stays gated, and real Git command interoperability remains unproved and
is stated as such.

## Superseded — changes requested by independent review112857

review-2026-09-07T19-29-28Z.md records three reproduced blockers: worker readers
follow intermediate/root symlinks; a line-directory replacement during extraction
is not revalidated before publication; and252 distinct edits publish513 files
before the manifest digest refuses. Evidence and exact four-file snapshots are
in evidence/review-112857/. The existing55 tests pass but miss these boundaries.

Return to baton.impl within the existing four-path scope. Correct descriptor
traversal, post-extraction custody/accepted-evidence revalidation, and complete
pre-publication digest/count/size checks. Reconcile producer/reader blob totals
and enforce the declared evidence-byte limit. Add focused boundary/drift/retry
cases without weakening assertions. Pin revised bounds/API before changing them,
preserve historical evidence and return for independent review. No parent use,
unrelated registry repair, shared-core edit or live run is authorized.

This supersedes pending independent acceptance below; W110935 remains gated.

## Previous state — implementation claim112654, awaiting independent review

Items 1 and 2 are delivered and item 3 is delivered in part. The exact public
interface, layout, named producers and finite bounds are pinned in FINDING.md
and are returned unchanged for parent consumption; two recorded changes
(`MAX_PATHS` 512 for a measured serializer reason, and a new per-projection
evidence bound) and one open decision (the bundle carries the launch DIGEST,
never the session-bearing document) are recorded there.

All four assigned paths are written: new `v12/worker/integration_contract.py`,
new `v12/python/tools/integration_bundle.py`, new
`v12/python/tests/tools/test_integration_bundle.py` and exactly one additive
`tools/parallel_test.py` registry entry. No other source, test or dossier is
touched. Candidate hashes and precise red/green outcomes are in PROGRESS.md.

**What item 3 still owes**, stated so review does not have to find it: the
producer's version control is proved through a deterministic read-only runner
over real temporary files — the methodology the parent finding fixes for this
producer — so no `git` process is executed anywhere in this suite. The seam
answers only argv the module itself composes, and the composed vectors are
asserted word for word, but nothing here proves a real `git` binary answers
those vectors in that shape. The manager half is not seamed at all: the real
`_OrdinaryAdmissionWorld` supplies real custody, real Authority receipts, a
real accepted checkpoint and a real Job store.

1. [done; claim112654] Claim, revalidate the parent baseline and pin the exact
   producer API, layout, named producers and finite bounds before coding. All
   thirteen baseline hashes re-measured and matching.
2. [done; claim112654] Implement the closed standard-library contract and the
   public-owner bundle producer in the two assigned source paths, the additive
   test module and the exact registry entry.
3. [delivered in part; claim112654] Read-back, digest, provenance, refusal,
   atomic publication, packaging isolation and real-owner composition are
   proved. A real `git` binary answering the composed vectors is not.
4. [pending] Independent review accepts this provider before W110935 consumes
   its frozen contract. Parent retains the actual-entry import/result proof and
   the W110774 consumer gate. No implementation or live acceptance is inferred.

Parent research and current revalidation evidence remain in the parent dossier;
this is the one canonical child binding for W112630, not a duplicate record.
