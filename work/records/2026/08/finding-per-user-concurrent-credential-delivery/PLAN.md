# Plan

1. [gate first] Block this Work on W38956 and do no further work until the
   first useful dogfood task closes satisfying.
2. Revalidate the live credential-slot permission reproduction and the
   current provider-source configuration boundary.
3. Specify user-scoped credential-provider configuration and concurrent
   attempt allocation without changing protocol vocabulary prematurely.
4. Correct attempt-slot access and worker readability preflight with focused
   positive, negative and teardown tests.
5. Prove two user-scoped runners can execute concurrently with distinct
   provider sources and attempt-private slots.
6. Remove the global manual staging requirement from the supported operator
   path and document migration from the private-box workaround.

## Revalidated scheduling state — 2026-08-31

1. [done, gate not satisfied] W38956 is terminal `non-satisfying`, not the
   satisfying close required above. Its terminality cleared the ledger edge but
   did not authorize steps 2-6.
2. [parked] Preserve this confirmed defect and its accepted direction without
   research or implementation. Resume only under an explicit superseding
   scheduling ruling or a recorded replacement successful-dogfood gate.
3. [not started] Original steps 2-6 remain the implementation-ready sequence
   once the scheduling gate is validly superseded or satisfied.

## Resumed vertical slice — 2026-09-01

1. [done] Record Slawomir's explicit scheduling supersession after W55758 and
   select W52821 as the first real repository change run through the supervised
   v12 worker path.
2. [done, reviewer revalidation 2026-09-01] Revalidate the current
   `--credential-file` path, credential home and slot materialization seams;
   freeze the smallest input set and task contract for one user-scoped runner.
   The current manager already owns attempt-private delivery, exact teardown,
   worker readability and lazy post-activation materialization. The open seam
   is the user-local `(provider, reference)` source resolver. Evidence and
   proposed task: `evidence/research-2026-09-01/`.
3. [done, approved 2026-09-01] Use the explicit private
   `--credential-sources` registry and remove the direct-file bypass; require
   current-uid/private ordinary-file proof; and permit a host path only in
   user-local configuration. Use one live worker now and prove future
   concurrency through isolated contexts and focused tests.
4. [run2 retained; changes requested in review-2026-09-01T13-04-03Z.md]
   Implement the ruled user-scoped provider resolution and command wiring
   without changing the manager's credential, OCI or worker-readable-slot
   contracts and without a shared `/run/baton/credentials/*` source, global
   lock or process-global active attempt. Run2 produced a bounded five-path
   proposal but invented a second provider/reference vocabulary and left
   descriptor read failures untyped.
5. [run2 evidence incomplete; changes requested] Prove with two distinct
   configured user and provider contexts that source resolution, slots and
   teardown do not share mutable state. Run2's synchronized stand-ins passed,
   but the production command and manager seam were never imported by the
   focused suite and the recorded generation values were not consumed.
6. [done, run2 rejected] Independently inspect the retained proposal and rerun
   the focused test outside the worker. The required 62-test rerun passed, the
   real help surface was correct, and independent contract probes found three
   P1 findings. Do not import run2.
7. [deferred follow-up] Exercise two real OS-user runners concurrently after
   the single-worker path is in ordinary use.

## Run2 correction

8. [run4 retained; changes requested in review-2026-09-01T13-57-01Z.md] Correct the three P1
   findings in `review-2026-09-01T13-04-03Z.md`: use the manager-compatible
   opaque provider/reference shape, translate post-open descriptor failures
   into safe typed refusals, and exercise the actual command/manager seam
   rather than stand-ins. Run4 corrects the first two code defects and adds
   real-seam tests, but its retained-tree run silently skipped all 27 real-seam
   cases because the manager package was absent.
9. [run4 verification rejected] The exact candidate command reported 83 tests
   passing with 27 production-seam skips. With the host manager explicitly on
   `PYTHONPATH`, all 83 pass without skips, but the existing real operator help
   test fails after overlay because it still requires the removed
   `--credential-file`; the source/edit boundary omitted that suite.
10. [done, run4 rejected] Independently inspect the retained correction before
    repository import. `review-2026-09-01T13-57-01Z.md` requests changes; do
    not import run4.
11. [approved 2026-09-01; next isolated v12 correction] Preserve run4's
    manager-compatible identity rule and typed descriptor failures, but make
    production-seam imports mandatory, provide the complete manager/operator
    context to the worker, update the existing dogfood-operator cases affected
    by the removed flag, and render opaque identities only as fixed semantic
    labels plus optional safe length—never raw text or a prefix.
12. [next, focused verification] Run the corrected module with zero skips plus
    the affected existing dogfood-operator and credential-manager cases in the
    worker. Independently repeat that verification against the retained
    artifact.
13. [next, reviewer] Reinspect the next retained correction before any import.
    Import remains prohibited until an append-only review signs off.
14. [pending operator claim] Hold W52821 at `baton.ops` while one fresh
    correlated v12 attempt starts from the retained run4 candidate. Do not
    route this code change through `baton.impl`, start a second worker, or
    import output before item 13.
15. [done, run5b retained unresolved] Preserve the six-path candidate and
    operator evidence. No container remains, but the task verification context
    was incomplete and the exact v12 assignment remains logically live.
16. [done, separated follow-ups] Record the verification/review materialization
    defect as W61981 and the quiescent-assignment finalization defect as W61984.
    Do not fold either platform correction into W52821.
17. [done, independent review 2026-09-01] Materialize a complete read-only
    review copy, overlay the retained candidate, rerun the bounded zero-skip
    gate with its declared import and fixture context, and inspect the six
    changed paths. The fresh copy ran 102/102 passing with zero skips, errors
    or failures; see `review-2026-09-01T14-56-49Z.md`.
18. [signed off for operator import] The exact run5b digest is accepted with
    no candidate finding. The v11 operator may import it and run
    repository-level verification under its own claim. W61981 and W61984 stay
    separate; do not fold their platform corrections into this import.
19. [repository gate failed safely] Importing the six paths reported relative
    to run5b's immediate source omitted inherited run4 operator changes. W62098
    owns the separate import-base/lineage defect; commit nothing.
20. [done, bounded integration] Preserve the current W61599 edits and
    integrate only the signed W52821 operator changes into the overlapping
    file. The exact W52821 gate passes 102/102, the W61599 overlap gate passes
    15/15, and the broader affected modules pass 852/852.
21. [done, final review 2026-09-01] Inspect the combined diff for scope and
    conflict. Six W52821 paths are byte-identical to the signed candidate; the
    overlapping operator differs only by the preserved W61599 observation
    slice. The complete-context W52821 gate passes 102/102, the overlap gate
    passes 15/15, the broader affected modules pass 852/852, and
    `git diff --check` is clean. See
    `review-2026-09-01T15-17-19Z.md`.
22. [next, operator acceptance] Return W52821 to `baton.ops`. The final review
    accepts the bounded W52821 integration but does not accept parked W61599,
    close W62098, or turn the whole dirty worktree into one candidate.
