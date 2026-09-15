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

## 2026-09-14 - the carried acceptance, completed against the landed providers

All four mandatory children closed `satisfying`, and the two claims this Work
had explicitly DEFERRED to them are now measured rather than qualified.

**The lane ordering is enforced.** W32649's cross-attempt lane owner exists, so
"no negative ending releases or reuses the lane before every required ending is
positively established" is now a refusal this Work asserts instead of a
relation it said was unenforced. A real successor attempt -- offered, claimed,
activated -- is refused while the predecessor's ending is unproved, creates
nothing, and starts only after the predecessor settles.

**A guard overlap worth recording.** Two guards in `_occupy_lane` refuse a
same-assignment successor: the by-Work predecessor query and the lane table's
own primary key. They are different facts -- an unsettled predecessor versus
two callers racing for one lane -- and a case asserting only the word "lane"
passes on either. Measured directly: neutering `_no_predecessor_holds` left the
first version of the case green. The case now pins the predecessor sentence.

**The runtime deadline reaches the ordinary registry.** W32577's own real-engine
gate proves the crossing under an environment-supervised supervisor that
`SERIAL_MODULES` does not run. This Work's acceptance is that the deadline takes
the SAME crossing as the completed arc, so it is asserted here beside
`plan-rejected` on the same daemon, fixture and seams.

**`unsupported-version` is satisfied by W32576's `test_refused_session_engine`**,
which is in the same serial registry on the same fixture and proves the whole
crossing on a real daemon. It was revalidated by running it; a second copy here
would be coverage without evidence.

**Operational finding, not this Work's:** `tools/parallel_test.py` refuses to
start because twenty modules belonging to other in-flight Works are in no
registry. The full parallel/serial gate prior rounds ran could not be run.


## 2026-09-14T11:10:46Z — independent parent completion, claim168683

review-2026-09-14T11-10-46Z.md accepts the selected parent negative/race matrix against
candidate93ab889ad2d9b119a2124e2b8f93aece58b9e4feb1c4d1d408db2e72980f7e75.
All four children are canonically closed satisfying. The added deadline and
pre-settlement successor assertions match the unchanged accepted owners; prior
child engine/verification evidence is reused with its original scope. Author
M168679 fresh run reports remain attributed, not independently rerun or furnished
with invented raw logs/image identities/timing. Exact candidate/source/review
bindings are in review-audit-168683.json; parsing and scoped whitespace pass.

This supersedes all older missing-provider/voluntary-order/deadline-absence
statements as current requirements. Offer expiry, post-create convergence,
plan rejection, typed unsupported-version, deadline cleanup and enforced lane
reuse are accounted for in the review matrix. No selected parent implementation
or verification requirement remains; ready for satisfying closure. W3/W33755
retain their own scope and no parent certification is implied.

The20-module registry refusal is independently reproduced by the read-only
Suite completeness check. W168703 now owns classification/integration while
preserving explicit engine/live-provider gates. This is separate from the
completed parent focused matrix, with no new dependency or broad-run waiver.
The blanket claim that every missing module belongs to an in-flight Work is
superseded: W32577 is closed and its engine test remains deliberately supervised.
No registry/source/test/PROGRESS/Git mutation or reviewer runtime execution.
Static check0.015659008000511676s; no test child cost, other time unmeasured.

Canonical closure168717 completed with satisfying outcome. Detail at168719
confirms closed status, no Handler/claim/Route, four closed children and W3/W33755
still open. The preceding ready-for-closure decision is now executed.
