# Committed publication history

W120763, provider for W120425. Created by baton.codex under claim120753.
**Confirmed authority:** Slawomir event120736 approves Provider B in
`baton:work/records/2026/09/finding-v12-composed-ending-recovery/findings/finding-historical-implementation-proof/PROVIDER-SPLIT-PROPOSAL-2026-09-08.md`.
Read that exact section and the originating review-2026-09-08T16-18-42Z.md
before implementation; they own the technical explanation and full acceptance
matrix. The proposal's unallocated status is superseded by that owner ruling.

**Confirmed gap:** retained proposalManifest precedes actual publication and
cannot prove it. Commit a closed local result in the existing Worker Manager
operation journal after publish_candidate's successful publish and exact
readback, before returning success; preserve the ordinary return contract.

Exact scope under v12/python:

- src/baton_v12/integration/driver.py
- src/baton_v12/integration/__init__.py (public export only)
- tests/integration/test_driver.py (additive; preserve all existing assertions)

Approved interface: publication_of(manager, *, attempt_id,
proposal_manifest_digest). It takes no publisher and performs only local reads.
Bind attempt, immutable assignment, proposal/result/manifest and actual answer.
Pin operation identity/signature/receipt before edits. Genuine absence answers
None; retained-only never establishes publication. No schema/store changes.

Acceptance uses real retain_proposal and publish_candidate with valid declared
git-change-proposal output and deterministic publisher transport, then reopen.
Cover wrong/failed remote answers, malformed/foreign local evidence, replay and
remote-success/local-record interruption as specified in Provider B. About20s
focused budget, declared before running. Further expansion requires a concrete
failure of the agreed demonstration.

High serial baton.impl execution follows actual W120762 acceptance and returns
baton.bug. This is a scheduling dependency; neither API consumes the other.
W120425 waits for both independent acceptances before driver composition.

## Independent review — 2026-09-08, claim121070

**Changes requested.** review-2026-09-08T17-15-33Z.md supersedes the pending
implementation-complete disposition. Boolean generation true passes as integer1
in either retained assignment and can be committed from publisher readback.
The review and evidence/review-121070-* retain exact candidate bytes, probes,
scope audit and one bounded typed-validation correction. Publication ordering
and local replay otherwise meet this provider's scope; W120425 remains gated.

## Independent acceptance — 2026-09-08, claim121144

**Accepted.** review-2026-09-08T17-24-17Z.md supersedes the prior
changes-requested disposition. All three original boolean probes now refuse;
honest local replay remains read-only. Provider B is complete. W120425 retains
the composed consumer correction and actual lifecycle proof.
