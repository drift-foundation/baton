# Progress

## 2026-09-08 — baton.claude, claim 121029

### Verification question and budget, before running

Does a real `retain_proposal` + `publish_candidate` leave a local record a
REOPENED manager can read back and correlate; does a retained-only proposal
still answer absence; and does the added commit change any existing assertion
in the affected set? Retained evidence cannot answer it — the record did not
exist. Budget: about 20s cumulative — the added controls, then
`tests.integration.test_driver`, `tests.integration.test_coordinator`,
`tests.tools.test_stage_execution` (the consumer of `publish_candidate`) and
`tests.manager.test_secrets` once. No broad campaign.

### Delivered

`publish_candidate` now commits a closed publication record in the existing
Worker Manager journal after its successful publish and exact readback, and
before returning; its ordinary return contract is unchanged. The record is
journalled under `integration.publication` at an identity derived from the
attempt and the proposal-manifest selector, signed over the operands the
Authority was asked for, so an exact republication replays one row.

`integration.publication_of(manager, *, attempt_id,
proposal_manifest_digest)` reads it. No publisher operand, so no branch can
republish, re-grant or ask the Authority anything. It re-derives the operands
from the retained proposal, the frozen result and the fixed assignment,
compares the journalled signature against them, holds the receipt to
`PUBLICATION_RECEIPT`, and compares the recorded Authority answer against the
one those operands ask for. Genuine absence answers `None`, and that means "no
local record" — never "not published": ordinary recovery re-enters
`publish_candidate` under the already-owned publication identity.

### Verified

12 added controls OK: reopened read-back with every selector and the
Authority's own answer correlated; retained-only answers absence; exact
republication replays one row; the remote-success/local-record interruption
answers absence and is then completed by ordinary recovery under the same
identity, with the two publish operands identical; a wrong remote answer and a
disagreeing readback record nothing; and foreign kind, underivable signature,
foreign selectors, malformed receipt and a disagreeing recorded answer each
refuse. 487 OK across test_driver, test_coordinator, test_stage_execution and
test_secrets. Commands, hashes, modes and fixture limits:
`evidence/verification-121029.json`.

### Limitations

`PublicationCase`'s stand-in manager is now a real `ControlStore`, because
publication commits a record; both of that class's existing assertions are
unchanged. The new controls replace `frozen_output_of` and `assignment_of` as
the existing producer suite does — this fixture retains real manifests without
writing the attempt rows those two read. No fourth path was needed:
`test_secrets` scans `worker_manager.__all__`, not this package's.

### Next

Independent acceptance at baton.bug. W120425 composes both providers after it.

## 2026-09-08 — baton.claude, claim 121097 (correction)

### Question and budget, before running

Does a boolean generation now refuse at both the local commit and the
historical read, does an honest integer generation still read back after
reopening with the publisher forbidden, and does the type proof change any
existing assertion? Retained evidence cannot answer it — it was taken against
the accepting bytes. Budget: about 10s — the added controls, then
`tests.integration.test_driver` and `tests.tools.test_stage_execution` once.

### Corrected

[P2] accepted. `True == 1`, so comparing the recorded assignment by value alone
accepted a boolean generation wherever the real one is 1, and the journal
signature could not close it: that signature is derived for integer generation
1 and says nothing about the types the recorded result carries. `driver` now
owns both accounts of the assignment through `_typed_assignment` — which reuses
`boundaries.generation`, whose contract already excludes `bool` for this exact
reason — before any value comparison, at the local commit in
`_retain_publication` and at both members on historical read. A readback
carrying a boolean generation therefore commits nothing, so the ending is not
reported complete.

### Verified

15 added controls OK (12 plus 3): the boolean readback commits nothing and the
reopened read answers absence; a boolean generation in either recorded
assignment refuses on read; and an honest integer generation reads back
identically after reopening with both publisher methods forbidden and zero
writes. 203 OK across `test_driver` and `test_stage_execution`. Commands,
hashes and budget: `evidence/correction-121097.json`.

### Limitations

Unchanged from the first pass: `PublicationCase`'s stand-in manager is a real
`ControlStore`, and the new controls replace `frozen_output_of` and
`assignment_of` as the existing producer suite does. No existing assertion was
changed.

### Next

Independent acceptance at baton.bug; releases W120425.
