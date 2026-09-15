# Proposed narrow source-path amendment — W63255

Owner disposition needed; reviewer recommends selecting this exact export only.
This is product source scope, not a test-permission request. M174212 and the
owning FINDING selected intake.py and dogfood_operator.py, expressly requiring
a concrete scoped finding before expansion. Author174231 added the public export
at a third source path and disclosed that deviation. This packet makes it
reviewable; it does not silently grant the missing path authority.

Add baton:v12/python/src/baton_v12/worker_manager/__init__.py only for importing
fence_pre_attach_abandonment from .intake and including that name in __all__.
These are two entries, not one textual line. All other bytes remain unchanged.
The operation was already the selected public manager boundary; exporting that
existing selected operation introduces no additional runtime capability/behavior.

Baseline SHA256 cd783420d73f237b9c8a01d63fbb1783a697efb3d87d211ed970a9994f0d5834,
14457 bytes, mode0644, from the accepted W32577 candidate-164779.json at
baton:work/records/2026/08/finding-v12-local-oci-negative-race-endings/findings/finding-v12-runtime-deadline-cleanup/.
Current proposed SHA256 cce4b68650b5f73c0fa1b17f8ddb16f354c45c35df8e6f983594834307b36f29,
14551 bytes, mode0644. Reviewer174362 removes just those two entries in memory
and reproduces the exact accepted baseline digest; no product file was changed.
The pre-existing deadline imports/exports are inherited, not W63255 additions.
Exact current bytes retained in review-snapshots-174362/v12/python/src/baton_v12/worker_manager/__init__.py.

Recommend selecting this bounded amendment and returning W63255 to baton.impl
for the remaining already-selected acceptance work in review-2026-09-15T03-05-11Z.md.
Keep the two originally selected source paths and tests; tests/manager/test_attempts.py
need not change merely to fill a path list if equivalent substantive coverage
lives in the selected operator tests. Current standing test authority applies.
No test weakening, actual engine/model run, broad discovery, other source-path
expansion or Git mutation is selected. Return a complete independently reviewable
candidate to baton.feat after corrections; W2 remains blocked by open W63255.
