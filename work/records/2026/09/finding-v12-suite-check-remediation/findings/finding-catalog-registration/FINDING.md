# Register missing v12 test catalog members

Work W116014. Parent: ../../FINDING.md, owner-assigned scope dated 2026-09-08.
The accepted diagnosis is
`work/records/2026/09/finding-v12-unresolved-suite-checks/review-2026-09-08T03-46-00Z.md`, group A.

Checks1/2 omit two driver modules from the parallel runner registry and one
authority test filename from its exact migration catalog. Add only
`tests.integration.test_driver` and `tests.job_manager.test_review_driver` to
`v12/python/tools/parallel_test.py` SERIAL_MODULES, and
`test_work_label_exposure.py` before `test_work_labels.py` in
`v12/python/tests/authority/test_catalog.py`. Preserve all equality, uniqueness,
root-absence and other assertions. No driver implementation edits.

Claude retains parallel_test.py until its assembly write episode explicitly
ends; no registry edit based on an assumption of inactivity. Catalog-only work
is disjoint. Independent assessment must bind both final file changes and
targeted evidence, without certifying unrelated suite failures green.

## 2026-09-08 — exact third catalog exposed by required verification

Observed under claim116111: original checks1/2 now pass, but the declared
two-module regression reports one failure in41 tests (12.757s):
`tests.tools.test_parallel_runner.TheRealRegistryDescribesTheRealTree.test_the_serial_modules_are_the_ones_that_own_an_engine`
compares SERIAL_MODULES to a second exhaustive expected tuple that omits the
same two new driver members. No other failure was reported. The diagnosis's
two-file write set omitted this required third catalog; no runtime failure
or independent justification for parallel promotion was demonstrated.

Proposed precise extension: append the same two members, in the same order,
to that existing equality tuple, preserving all prior members, tuple equality
and serial/parallel exclusion assertions. The proposed third-path bytes are
retained in evidence/proposed-runner-candidate.py with SHA-256
`690241cb9f51e1405c6d3246bd8a66620a95d4f8ecf561e8d5d4553dfd736406`;
proposed-runner-extension.patch is the exact change. The actual runner test
file has not been edited. Request disposition of the explicitly bounded
two-file scope before importing this third-path addition. The additive-member
repository rule is consistent with the proposed assertion; this request is
about the narrower assigned path set, not a request to weaken equality.

## 2026-09-08 — bounded extension approved, revalidated under claim118934

Slawomir's canonical disposition M118927 in T116014 approves the exact proposed-runner-candidate.py SHA256690241cb9f51e1405c6d3246bd8a66620a95d4f8ecf561e8d5d4553dfd736406. It extends the write set only to v12/python/tests/tools/test_parallel_runner.py, appending tests.integration.test_driver then tests.job_manager.test_review_driver to the named exhaustive serial expectation. Previous members, equality and exclusion guards must remain; no further registry edit or whole-suite run is authorized. This explicitly supersedes the pending-extension state above, not its historical diagnosis.

Before implementation, baton.tuner revalidated the live third file against the retained base: both SHA256c1d5752eec92dd23527ef7ac8ac4ce6e28e9ca794677d16120cb187da6dc6d39. The retained candidate matches the exact approved digest. Both prior live catalog files still match evidence/hashes.txt and their retained candidates; no drift or new registry write episode is needed. Apply only the approved third-file bytes, then obtain independent review of the joined three-file result.

## 2026-09-08 independent acceptance — claim118966

The joined three-file result is accepted; review-2026-09-08T12-25-46Z.md binds
all exact hashes and M118927 authority. Independent identity/AST audit confirms
only the authorized member additions, with every prior guard unchanged.
All41 required catalog/runner tests pass in retained final evidence, including
original checks1/2. This supersedes awaiting-independent-review state only;
no further catalog implementation remains. Other W115981 checks and its final
ordinary suite gate remain separately governed.
