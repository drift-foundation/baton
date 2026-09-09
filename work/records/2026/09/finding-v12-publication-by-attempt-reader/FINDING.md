# Committed publication lookup by attempt

Created by baton.codex under W120425 claim121781, 2026-09-08. Provider for
W120425, separately accepted before the consumer correction resumes.

Canonical ledger binding: **W121793**, created121793, High baton.impl.

**Confirmed authority:** Slawomir event121773 approves exactly
`baton:work/records/2026/09/finding-v12-composed-ending-recovery/findings/finding-historical-implementation-proof/TEST-AND-SELECTOR-DISPOSITION-2026-09-08.md`.
Its separately acceptable provider section owns the contract, scope and
acceptance matrix. Read it and the originating
review-2026-09-08T17-37-36Z.md before implementation; that review owns the
technical explanation and retained cold-recovery probes.

Deliver `publication_for_attempt(manager, *, attempt_id)`: the same validated
committed receipt as publication_of, or None for genuine absence, without a
publisher or remembered manifest selector. Use the existing local publication
journal and existing owner's validation; reject ambiguous, malformed or
contradictory candidate evidence. Pin exact local selection and corrupt-record
boundaries before edits. No schema, store infrastructure, new journal or remote
fallback. W120763 remains accepted for its original selector-taking API.

Exactly three paths under v12/python:

- src/baton_v12/integration/driver.py
- src/baton_v12/integration/__init__.py (public export only)
- tests/integration/test_driver.py (additive; preserve every existing assertion)

The four test exceptions in the approved document apply only to W120425's
test_review_driver.py candidate, not this provider's tests. Consumer and
assembly paths are excluded here. About15s focused verification, question and
commands recorded before running, with retained output/timing. Cover real
publication and reopened local recovery with forgotten selector, forbidden
publisher/SQL writes, absence/retained-only, foreign/malformed/ambiguous rows,
replay and later target movement. Consumer lifecycle proof remains W120425's.

High serial baton.impl execution returns baton.bug for independent acceptance.
The consumer and W119733 remain gated until their respective actual acceptance.

## Independent acceptance — 2026-09-08, claim121826

**Accepted**, review-2026-09-08T19-20-38Z.md. This supersedes the pending
provider-acceptance status: exact candidate and additive scope pass review,
including independent cold recovery from actual committed consumer evidence
with publisher access and SQL writes/transactions forbidden. W120425 may resume
its original two-path correction; its lifecycle proof and W119733 acceptance
remain owed.
