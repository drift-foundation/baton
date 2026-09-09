# Progress

## 2026-09-08 — baton.claude, claim 121797

### Question and budget, before running

Does a cold manager with no remembered selector find the same validated
publication from the attempt alone, without reaching a publisher or writing;
and are absence, foreign, ambiguous, mis-filed and unclassifiable records each
answered as themselves? No retained evidence answers it — the reader did not
exist. Budget: about 15s — the added controls, then
`tests.integration.test_driver` and `tests.tools.test_stage_execution` once.

### Pinned before editing

**Selection.** The publication identity is a digest over the attempt AND the
selector, so the attempt alone derives nothing and no enumeration is possible.
The reader therefore scans rows of `integration.publication` — a kind this
module writes and no other party produces — decodes each, and keeps those whose
own `attempt_id` is this one.

**Corrupt-record boundary.** Three answers, not two. A well-formed record about
another attempt is skipped; one about this attempt answers its selector; and a
row this reader cannot classify refuses, because deciding a record is *not*
about this attempt requires reading it, and a scan that skipped what it could
not read would answer absence with a real record in front of it. A row whose
own members do not derive the identity it sits at refuses for the same reason:
`publication_of` re-derives that identity, so a mis-filed record would be
invisible to it.

**Ambiguity.** Two committed publications for one attempt refuse. One attempt
publishes once while its producer assignment is live; choosing by row order
would invent which one happened.

### Delivered

`integration.publication_for_attempt(manager, *, attempt_id)` — no publisher,
no selector. It finds WHICH record and hands the selector to `publication_of`,
so exactly one place decides whether a publication record is sound and both
entry points answer the identical validated receipt. `publication_of` and
`publish_candidate` are unchanged.

### Verified

11 added controls OK; 214 OK across `test_driver` and `test_stage_execution`.
The cold cases forbid `publish`, `proposal`, `canonical_target` and
`retain_proposal` outright and assert zero control writes, so "no publisher and
no write" is measured rather than asserted in prose. Commands, hashes, budget
and the existing-assertion count: `evidence/verification-121797.json`.

### Limitations

The row scan reads `integration.publication` rows directly — no enumeration is
possible, because the identity is a digest over the attempt *and* the selector
— and it is bounded to a kind this module alone writes. `frozen_output_of` and
`assignment_of` remain this suite's declared stand-ins, as in the existing
producer cases; the publication record, its journal row and the retained
manifests are real.

### Next

Independent acceptance at baton.bug; releases W120425's two-path correction.
