# Plan: complete local lifecycle and conformance proof

1. [superseded by the ruled bounded pass below] Revalidate all three landed
   implementation slices and the frozen case/register digests.
2. [pending] Build the disposable black-box harness and deterministic scripted
   agent fixtures without implementation backdoors.
3. [pending] Exercise positive, negative, retry, race, restart, cancellation,
   quiescence, credential and cleanup scenarios for both input families.
4. [pending] Assess every applicable local-OCI core case, independently verify
   evidence/digests/projections, and retain the immutable evidence pack.
5. [pending] Append the independent review and return W1425 for final M2
   reconciliation and approval.

## 2026-08-28 — capability-pass revalidation

- [done] Revalidated W5's bounded satisfying outcome and the exact current
  conformance register.
- [blocked decision] The register has 135 local-OCI cases, not 106, and three
  require the superseded consent-container topology. A full certified verdict
  is not presently honest.
- [proposed bounded pass] Seal W6636's accepted real-Docker evidence, assess an
  exact named compatible subset through the frozen assessor, and publish the
  formal `not-certified` result with every unobserved/conflicting case named.
- [proposed later Work] Revise the conformance register explicitly for the
  direct claim-to-one-container topology, then run exhaustive certification as
  its own capability pass.
- [next] Obtain the approver's acceptance-boundary ruling before routing any
  implementation or creating the later Work.

## 2026-08-28 — ruled bounded capability pass

- [done] Approver M33739 selected the proposed bounded pass and explicitly
  removed exhaustive register revision/certification from this vertical-slice
  finish line.
- [done] Implementer revalidated the authoritative register: 136 total cases,
  135 applicable to `local-oci`, all three topology-conflicting cases still
  live, and no current `core` field from which the original verdict could be
  derived.
- [next] Seal the exact accepted W6636 evidence and bind every selected case by
  identity plus fixture/register/case/adapter/profile/evidence digest.
- [next] Run the frozen assessor over that exact compatible subset and publish
  formal `not-certified`, enumerating every unobserved or conflicting
  local-OCI case without count aliases or silent exclusions.
- [next] Publish a separate evidence-backed promising/not-promising conclusion
  about the design and assessment path; do not conflate it with certification.
- [next] Retain immutable evidence, append independent review, and return W3
  for M2 reconciliation.
- [created separately] Direct-topology register revision and exhaustive
  certification are owned by the new top-level dossier
  `work/records/2026/08/finding-v12-direct-topology-conformance-certification/`;
  its ledger Work is parked `W33755`.

## 2026-08-28 — bounded-pass review state

- [done] Retained the all-135 classification, exact digest-bound ten-case
  subset, frozen per-case assessments, formal `not-certified` result, and
  separate promising-design conclusion.
- [done] Independent read-only verification recomputed every submitted digest,
  observation binding, case assessment, and the 10/8/2/125 partition without
  mismatch; see `review-2026-08-28T20-28-19Z.md`.
- [operational limitation] The reviewer deployment is denied Docker-daemon
  access, so it could not independently rerun the required real-Docker probes
  and did not request prohibited escalation.
- [done] Filed the two measured ownership defects as W33935/W33936 and the
  decline-bearing-claim contract conflict as parked decision Work W33937.
- [next] Approver disposition or an authorized independent Docker verification
  must account for the explicit rerun limitation; never call this capability
  pass integration certification.

## 2026-08-28 — the bounded pass, executed

- [done] Sealed the accepted W6636 evidence: 16 files bound by content digest,
  the frozen assessor imported from its own dossier rather than copied.
- [done] Ran the frozen assessor over an exact compatible subset measured on a
  real Docker daemon and published `not-certified`, enumerating all 125
  unobserved local-OCI cases by name.
- [done] Measured the seal's own verdicts by removal: 5 of 8 mutations caught,
  2 survive by a documented redundant pair whose joint removal does flip, 1
  survivor recorded as a real limit on what its verdict establishes.
- [done] Published the promising/not-promising conclusion separately from the
  verdict.
- [next] Independent review, then return W3 for M2 reconciliation.
- [needs owners, none of them W6's] the `/input` pair and workspace ownership
  [P0]s measured inside the container; and the decline-carrying-bearer
  specification conflict, which needs the same kind of ruling the topology
  conflict received.

## 2026-08-28 — after review

- [done] Revalidated the sealed pack against the current tree: exactly one
  sealed input moved (`workspaces.py`, by W33935) and the verdict moved with
  it, from 8 passed / 2 failed to 9 passed / 1 failed. Retained as a separately
  named run rather than in place of the reviewed one.
- [done] Corrected the harness that overwrote the reviewed pack: runs are
  named, and writing different bytes over a retained artifact refuses.
- [relinquished] The independent end-to-end Docker execution the acceptance
  wants cannot be performed by an independent party in this deployment, and a
  rerun by the implementer is not independent. Raised on T6 for approver
  disposition or routing to an authorized independent Docker verifier.

## 2026-08-28 — disposition

- [done] Approver M34887 ruled the independent sealed-pack verification
  sufficient to finish W6 without a second independent Docker execution.
- [done] The result is recorded as a promising but formally `not-certified`
  capability pass, never as integration or exhaustive certification.
- [done] The reviewer transcript and its recomputed digests are preserved as
  the evidence for the overwritten original pack, and the overwrite limitation
  is recorded explicitly.
- [done] Named immutable evidence packs are required and enforced; the refusal
  is re-validated.
- [done] Independent disposition review accepted the bounded result under
  approver M34887 and closed W6 satisfying.
- [next outside W6] Return W3 for M2 reconciliation. Independent Docker
  reproduction and exhaustive current-register certification remain later
  Work.
