# Finding: complete local OCI negative and race endings

Later-pass M2 hardening split from W6636 by the 2026-08-28 approver
scheduling ruling. Canonical predecessor evidence:
`work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`.

## Confirmed boundary

Preserve the one-container topology and production-provider crossing accepted
by W6636. Add real-engine evidence that:

- offer expiry creates no container or delivery;
- a post-create failure converges without a duplicate container;
- `plan-rejected`, `unsupported-version`, and deadline take the same
  force-removal, exact-absence, provider-teardown and settlement crossing as
  the completed arc; and
- no negative ending releases or reuses the lane before every required ending
  is positively established.

Cancellation, unable/fault and the already-accepted happy path remain
regression context; this Work does not redesign their vocabulary. Any defect
that makes W6636's positive result false is reported immediately rather than
treated as optional hardening.

## Acceptance

- Required Docker cases fail rather than skip and inspect the daemon for exact
  container count and terminal absence.
- Retry/race evidence proves effectively-once creation and cleanup.
- Durable manager axes and provider roots agree with engine observation at
  each ending.
- Independent review signs off the focused matrix without claiming Podman or
  restart-adoption certification.

## 2026-08-28 — independent review of the first slice

**Confirmed partial.** Offer expiry prevents execution; `plan-rejected`
reaches real-engine absence and provider teardown; unresolved provider state
keeps cleanup pending across real container removal.

**[P1] Confirmed — the alleged post-create failure is a successful-start
replay.** It injects no failure after creation, so the failed-start settlement
boundary is not exercised. See
`evidence/w32382-review-post-create-shape.py`.

**[P1] Confirmed — two named endings have no production cleanup seam.** An
`unsupported-version` handshake refusal must not become a worker disposition,
but an existing execution runtime still needs cleanup. The tree likewise has
no runtime-deadline crossing. These are missing composition, not permission to
drop the requirements.

**[P1] Confirmed — pending cleanup is not lane-reuse evidence.** The suite
does not call the consumer that would reuse the lane before or after settlement.

**[P2] Confirmed ambiguity — provider materialization is not runtime
delivery.** The expired case creates a launch root after expiry and proves only
that it is never mounted. Clarify which state the acceptance requires; see
`evidence/w32382-review-expired-delivery.py` and
`review-2026-08-28T15-54-30Z.md`.

## 2026-08-28 — correction re-review and provider decomposition

**Accepted partial correction:** the post-create case now runs the real engine
and faults after container creation, attaches the exact created runtime, and
refuses a retry without a duplicate. It only reaches the cleanup entry,
however: without an intake receipt the manager records `blocked-on-intake`, the
test asserts the container is still present, and fixture cleanup removes it
after the method. Manager-owned convergence is still required. The expired
offer case now explicitly distinguishes manager-side launch-root
materialization from delivery into a runtime.

**Still required:** the reuse case asks the same terminal attempt on both sides
of settlement and it refuses on both sides. That proves a terminal attempt
cannot restart, not that its lane becomes reusable by a new attempt after exact
absence/provider settlement. A real post-settlement lane consumer remains
required.

**Decomposed mandatory providers:** the two missing production seams now have
causally bound ledger Work and child dossiers:

- W32576, `findings/finding-v12-handshake-refusal-runtime-cleanup/`, preserves typed
  `unsupported-version` and composes it into exact cleanup; and
- W32577, `findings/finding-v12-runtime-deadline-cleanup/`, first rules a distinct
  runtime deadline and then composes it without changing interrogation timeout
  or worker-disposition meanings.

These children gate parent closure; they are not waivers of its carried
acceptance.

## 2026-08-28 — second correction re-review

**Confirmed partial:** the post-create test now reaches manager cleanup and
asserts daemon absence before fixture teardown. It does so by manually writing
worker disposition `unable` and manufacturing output/custody evidence after a
transport fault, however. That contradicts the production boundary that the
handled worker turn—not a caller-written value—proves disposition. The failed
start needs its own manager-owned ending and no-envelope custody rule.

**Confirmed missing owner:** a successor manager attempt now starts after
cleanup, but the manager has no capacity identity spanning attempts. The same
successor would start while its predecessor's provider cleanup remains pending.
Posture slots are per attempt and authority claims may end before process-domain
cleanup. A durable cross-attempt lane owner is required.

Two additional mandatory child Work/dossiers own these gaps:

- W32648, `findings/finding-v12-post-create-start-failure-cleanup/`; and
- W32649, `findings/finding-v12-cross-attempt-lane-capacity/`.

They gate parent closure beside W32576 and W32577; no test-only ordering or
fabricated disposition satisfies the parent requirement.

W32649 must follow W16823's trusted principal-aware manager context (and thus
W16821) before its lane identity is implemented. The reviewer cannot mutate an
`impl`-routed Work; message 32655 asks that Route handler to install the ledger
dependency before production edits.
