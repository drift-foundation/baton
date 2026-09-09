# Proposed prerequisite split — owner allocation required

Prepared by baton.codex under W120425 claim120624, following independent
review-2026-09-08T16-18-42Z.md. **Proposed**, not implementation authority.
The current two-path driver allocation cannot supply the missing public owner
capabilities. Create two separately bound provider Works, high serial
baton.impl returning baton.bug, and gate W120425 on both actual acceptances.
Neither provider depends on the other. Existing W119733/W119114 gates remain.
Use top-level permanent dossiers to keep independent capability ownership clear;
each provider receives exactly one Work and its own FINDING/PLAN/PROGRESS.

## Provider A — read committed ordinary cleanup without external acts

Proposed exact paths under v12/python:

- src/baton_v12/worker_manager/intake.py
- src/baton_v12/worker_manager/__init__.py (public export only)
- tests/manager/test_intake.py (additive controls; preserve all assertions)

Proposed interface: cleanup_of(store, *, attempt_id,
retention_policy_digest) -> owned ordinary cleanup receipt or None for genuine
absence. The policy operand is necessary to select the same deterministic
destroy operation as authorize_cleanup; do not assume attempt alone selects
one policy. No port or adapter is accepted, and no Authority/runtime/session
operation or store write can occur. This provider covers ordinary runtime.destroy
only; recordless/failed-start families remain excluded.

Revalidate existing destroy_operation, _absence_proof, _committed,
intake_receipt_of and historical_directory_custody. Own full result/nested
shape, selected operation/signature, attempt/assignment/runtime/receipt/policy
and root custody relationships before returning evidence. Present invalid or
foreign is never absence. Missing intake or selected operation must have an
explicit non-success contract; do not enter authorize_cleanup's serving branch.
Preserve existing discharge and ordinary cleanup behavior. No schema/store/
Authority/custody implementation change; report any required expansion.

Acceptance: actual ordinary retain and discard cleanups, reopen/read/replay
with zero writes or external calls; missing/refused/wrong-kind/malformed/foreign
records, runtime/policy changes and empty/foreign nested custody controls.
Begin with added tests then the smallest affected cleanup/discharge set, named
question and about20s budget; reuse adequate provider evidence, no broad suite.

## Provider B — durable evidence that publication actually committed

Proposed exact paths under v12/python:

- src/baton_v12/integration/driver.py
- src/baton_v12/integration/__init__.py (public export only)
- tests/integration/test_driver.py (additive controls; preserve all assertions)

Use the existing Worker Manager operation journal, not a new schema/store or
an integration queue. After publish_candidate has completed publisher.publish
and its existing exact proposal readback, commit a closed correlated local
publication result before returning success to the ordinary driver. Preserve
the current live publish return document and assignment checks; a failure to
retain that local evidence must not report a completed ending. Pin the exact
operation identity, input signature and stored receipt contract before edits.

Proposed public historical reader:
publication_of(manager, *, attempt_id, proposal_manifest_digest) -> owned
committed history or None for genuine absence. It requires no publisher and
performs only local reads. Bind selected attempt, immutable assignment,
proposal/result/manifest and the actual successful publication answer. Reuse
the existing retained proposal to select, never to infer publication success.
Expose enough stable evidence for W120425's published_of seam to preserve its
correlated answer. No remote read or republish is allowed in the reader.

Acceptance: real retain_proposal + publish_candidate over a valid declared
git-change-proposal output and named deterministic publisher transport, followed
by reopened-manager read. Retained-only is not published. Cover failed/wrong
remote answer and readback, absent/foreign/malformed journal evidence, exact
replay and the remote-success/local-record interruption. Local-history absence
after an interrupted publish cannot be upgraded to success; ordinary recovery
must use the already-owned publication identity while its assignment permits
it, before a later ending may freeze/clean up. No new grant/fence/publish act
in the historical reader. Preserve all existing integration assertions.
Focused added-publication controls then affected driver cases, named question
and about20s budget; no broad suite or live Authority required.

## W120425 remains the consumer and component proof owner

Keep its original review_driver.py and test_review_driver.py allocation.
After both independent acceptances, compose their read-only interfaces;
validate complete retention vs kept-material separately; require exact real
custody; preserve original tests and add real publication/custody restart
controls. Demonstrate retained checkpoint recovery after later line movement;
report a further missing public selector if revalidation requires one. Do not
silently claim the mutable current pointer is historical proof.

The seven removed tests must be restored under the existing preservation rule.
This proposal does not approve their deletion or replacement. If a behavioral
assertion cannot be preserved, return a concrete enumerated old/new proposal
for that test before further mutation. No extra planning-only approval cycle
is needed for unchanged existing driver scope; only these new public-provider
paths require owner allocation.
