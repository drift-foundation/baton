# Reached create_line completion I/O — W257627 B3, claim299768

Observed source: review_cycles.create_line commits its preparation reservation
before profile.materialize. Its completion act, passed to ControlStore.transact,
then calls _object, workspaces.prove_line_integrity and establish_line_access.
These perform filesystem identity/traversal/access operations inside the completion
transaction. Thus moving materialize outside did not establish DB-1 for this
reached call. G2's accepted task-handoff I/O proofs are not this earlier line-creation
completion callback. No contradiction or blanket revocation of those proofs.

Exact file: v12/python/src/baton_v12/worker_manager/review_cycles.py:create_line.
This is an already named W257624 create_line residual, not a new unrelated backlog.
No workaround, bypass, runtime edit, guard weakening or graph mutation selected.
Tuner owner291841 permits only four baseline files plus this dossier; the exact
runtime correction is outside that scope. Preserve the runnable regression and
return the reached provider disposition to review, rather than claiming final
packet qualification from a positive result alone.

probe_create_line_299768.py wraps the real reached create_line and observes actual
lstat/fchmod calls and the disposable store connection's transaction flag while
the existing fresh connected-positive test completes. It uses no direct SQL or
live/deployed store. Expected behavior is zero calls inside the transaction; a
failure is retained defect evidence, never an expected-pass waiver.

Measured reproduction: 1FAIL0.243s, process exit1, while the wrapped connected
fresh-positive lifecycle completed. evidence/db1-299768.json captures62 lstat and
1 fchmod calls with in_transaction=true, alongside outside-transaction calls.
The assertions keep required DB-1 behavior (zero such calls); they are deliberately
not changed to expect the defect. Current runtime hashes still match accepted
candidate299662; this is a concrete coverage gap in the separately named residual,
not an unreviewed runtime edit. No remaining cumulative-time approval issue.

Required correction boundary: review_cycles.create_line completion, and its
owned tests, must move exact object/integrity/access I/O outside the transaction
while preserving identity revalidation, interruption/replay safety and exclusion
of stale/competing writers. Do not merely remove integrity/access checks or grant
unproved completion. Existing W257624 owns this residual. Reviewer should classify
and schedule that exact provider scope (or an explicitly bound bounded provider),
then install the corresponding required dependency before consumer freeze. This
report neither assigns its files nor silently modifies a live claim or graph.
