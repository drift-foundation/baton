# Current checkpoint — independently accepted, owner checkpoint pending

2026-10-18T01:56:12Z, baton.rvpc claim319197: candidate319137 accepted under the
01:24:52Z SQLite read-only/clear-refusal contract. Review:
review-2026-10-18T01-56-12Z.md. Candidate manifest SHA256
ceb895bbf581ca4ca7cf692b5de44ae03f42263061dcc68403563dd9e44569a1;
all listed hashes matched. Independent167 tests PASS0.856s, diff check clean.

R1 diagnostic correction and R2 historical progress restoration are complete.
Prior claim316919 and318857 accounts independently match their original hashes.
No further implementation correction requested. Historical correction findings
remain in FINDING and review-2026-10-18T01-45-33Z.md.

Next: baton.decide owner acceptance and human-owned Git checkpoint. Suggested
commit: `v12: report a refused read-only store open clearly (W316915)`.
Checkpoint is pending, not made; record the actual commit after observing it.
No automatic integration/deployment or live execution selected.

Normal SQLite sidecars are allowed; an unwritable directory without required
WAL sidecars may refuse. No filesystem-no-writes/universal readability claim.
W319114 remains a separate parked projection race with no dependency on W316915;
no coherent multi-statement/cross-store snapshot certification is implied.

Reviewer owns review/FINDING/PLAN; product/tests/PROGRESS remain the implementation
candidate. No parallel edits or new slices required. Read checkpoint E319195,
events319197, T316915 through319097 (no later messages).

---

# Prior checkpoint — SQLite read-only access, clear refusal otherwise

2026-10-18T01:24:52Z, baton.prompt: owner clarified that the concern is database
state, not SQLite's internal sidecar handling. This explicitly supersedes the
01:06:05Z checkpoint below and the original filesystem-no-writes/success-under-
unwritable-directory acceptance criterion. See the latest FINDING entry and
DESIGN OBS-1. Normal SQLite sidecar/locking behavior is acceptable.

Next milestone: revalidate the existing validated read-only Job/Control openers,
preserve no application-data/schema mutation, initialization, migration or writable
fallback, and clearly report read-only open/query failures. Retain authority/schema
validation, status shape and submit/serve behavior. No custom snapshot/reader or
guaranteed closed-WAL/no-sidecar success is required. Use focused deterministic
tests of the selected contract, then independent review against this ruling.
Preserve prior partial acceptance and historical evidence; do not call it full
acceptance of the changed current candidate without review.

Canonical snapshot318960: Claude actively holds claim318857, episode318855.
Prompt owns this decision/PLAN and DESIGN clarification only; Claude retains
product/tests/PROGRESS. Coordinate the changed acceptance with the current Handler
without releasing, replacing or interrupting its claim. Record affected test
changes and reasons under standing test authority. Existing live/deployed/Git
boundaries remain; no new runtime or broad verification campaign selected.

---

# Superseded checkpoint — filesystem-read-only status (01:06:05Z)

2026-10-18T01:06:05Z, baton.prompt: owner retains the original no-filesystem-write
requirement, including SQLite sidecars. See the matching FINDING entry and DESIGN
OBS-1. This supersedes the pending capability decision below; SQL-only read-only
access is not the selected acceptance boundary.

Next milestone: establish and implement a bounded consistency-safe status reader
that succeeds without database/directory write authority, including the closed
WAL/no-sidecar case, then obtain independent acceptance. Preserve validation and
status shape, and submit/serve behavior. Verify no writes on successful reads and
refusals, with realistic WAL/live-reader consistency cases and effective denied
write capability. Ordinary deterministic checks need no further owner approval.
No particular mechanism or exclusive files-to-edit list is prescribed.

Canonical state at snapshot318828: parked, unclaimed, baton.decide. Coordination
must release execution through a configured Handler; this document does not
unpark or claim Work. Prompt changes FINDING/PLAN and the spec clarification;
implementer owns product/tests/PROGRESS after claim, reviewer independent review.
Latest review remains review-2026-09-30T15-46-18Z.md, partial acceptance only.
Discussion previously read through T316915 message316915 and events318669.
No live/deployed repair, cleanup, integration or Git action selected.

Coordination finding: prompt's asynchronous directed request was refused because
prompt is not a resolved Handler of baton.decide. No obligation or transition
was created. This is the expected role boundary, not a product defect. Publish
the ruling as discussion evidence; the owning route must perform the execution
handoff/unpark. Do not claim that preparation or implementation was dispatched.

---

# Historical checkpoint — partial acceptance, owner capability decision (resolved above)

Review317007: candidate hashes match; independent13 PASS0.053s. Validated read-only opener
selection accepted; submit/serve unchanged. Full directory/no-sidecar acceptance NOT MET:
closed WAL without sidecars still refuses in unwritable directory; writable directory may gain
SQLite sidecars. No satisfying closure or implicit waiver.
Latest review: review-2026-09-30T15-46-18Z.md; REVIEW-EVIDENCE-317007.json.
Read E317004/events317007/T316915.

Next baton.decide: explicitly accept narrower SQL-read-only/fail-closed mode and amend original
criterion/documentation, OR retain full filesystem-read-only criterion and select consistency-safe
snapshot/reader design. No immutable live fallback or arbitrary live-store-copy recommendation.
Preserve candidate and accepted tests; no broad rerun needed for this decision. No deployed repair,
live run, credentials, integration or Git act. W316918 independent, W236087 proof preserved.
Ownership unchanged: author product/test/PROGRESS, reviewer FINDING/PLAN/review/evidence.

---

# Current plan

Owner E316900 selects this bounded follow-up. Read FINDING and referenced evidence; implement within its scope, run focused deterministic acceptance, pass to baton.bug for independent review then baton.decide.

Ownership: baton.impl claims before product/test/PROGRESS edits and records exact paths; baton.rvpc owns FINDING/PLAN and append-only reviews. Coordinate any overlap with the other follow-up before editing; no implied parallel edit authority. No live execution, deployed cleanup/integration/credentials or Git mutation. Existing temporary evidence copies are inspection aids, not deployment repair.

Canonical Work W316915; route baton.impl, independent review baton.bug. Coordinate any shared path with W316918. No dependency edge installed: neither correction requires the other.
