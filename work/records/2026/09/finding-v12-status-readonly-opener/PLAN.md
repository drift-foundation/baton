# Current checkpoint — partial acceptance, owner capability decision

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
