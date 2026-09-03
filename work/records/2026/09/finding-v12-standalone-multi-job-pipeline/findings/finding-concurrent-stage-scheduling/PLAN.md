# Plan

1. [done, reviewer revalidation 2026-09-03] Inventory the public offer, claim,
   attempt, session, cleanup and runtime-lane operations and the integrated Job
   projection. W73629 is integrated at `4876751`; the focused 188-test
   Job-manager suite passes.
2. [done, operator acceptance 2026-09-03] Define the closed pool document,
   scheduler-owned virtual workers and allocation axis, exact lane/profile
   eligibility, lane-scoped soft affinity, hard producer/prior-reviewer
   exclusions, stage-scoped dependency use, and the existing attempt/runtime
   identity mapping. Implementation and review workers, principals and agent
   sessions are disjoint even when a named degraded posture reuses a provider.
   Canonical principal joins worker and participant as a persisted
   capacity/independence key; aliases count as one effective slot. Pool
   configuration is immutable per explicitly activated generation, and the
   first deployment proves two simultaneous implementation plus two
   simultaneous review capacities.
2b. [resolved through items 2d-2g, 2026-09-03] Implementer revalidation of accepted
   decision 1 found two naming collisions with existing closed v12
   vocabularies (`posture`, and scheduler occupancy against `SLOT_OCCUPANCY`),
   three recording gaps (no contracted surface for canonical-principal
   resolution, no pool generation on any durable relation, and superseded
   affinity/index shapes still shown in the relation list), an inverted
   W71877/W71918 ownership for the provider-neutral `AgentSession` identity,
   and a test-boundary gap that makes the four-capacity acceptance vacuous on
   the current single-principal fixture. Decision 1's direction is otherwise
   sound and needs no redesign. See the FINDING's implementer revalidation.
2c. [done, operator clarification 2026-09-03] Treat the completed review-only
   implementer pass as implementation preflight: it validates that a complex
   plan is executable before implementation is handed off, but is neither an
   independent review verdict nor authority to change code or tests.
2d. [partly resolved 2026-09-03] Use `pool variant` plus an auditable
   `separation class` instead of overloading Worker Manager posture. Name the
   scheduler axis `allocation state` with `reserved`, `recovery-required`, and
   `released`. Resolve the remaining principal, generation, relation-shape,
   AgentSession-ownership, and fixture corrections before implementation.
2e. [superseded by item 2h, 2026-09-03] The proposed read-only
   `AuthorityPort.canonical_principal()` would cross the restricted Authority
   session boundary and is not implemented.
2f. [done, operator resolution 2026-09-03] Persist final pool-generation,
   worker, stage-allocation and lane-affinity relations, with cross-generation
   live uniqueness per worker, principal and stage episode. W71877 records no
   durable `AgentSession`; W71918 owns that identity and its continuity rules.
2g. [done, operator resolution 2026-09-03] Correct the acceptance fake to
   enforce one live claim per canonical principal. Prove the four-capacity path
   with four distinct principals, the alias-collapse negative case, and restart
   revalidation of persisted worker/principal associations.
2h. [done, operator resolution after final implementer preflight 2026-09-03]
   Trusted deployment resolves each participant through the Authority
   API/bootstrap face during pool activation and supplies the resolved
   principals to the scheduler. Persist and revalidate those associations on
   restart, fail closed on mismatch, and compare every returned claim principal
   with its reservation. Do not change `AuthorityPort` or the participant-bound
   Authority session.
3. [done, operator acceptance 2026-09-03] Apply the closed settlement table:
   safe no-assignment endings and cleanup `complete`/`retained` release an
   allocation; uncertain survival or cleanup failure requires recovery and
   retains capacity. Only `abandoned-after-restart` retries automatically;
   other endings remain visibly exceptional until an explicit retry.
4. [done, operator acceptance 2026-09-03] Add schema 3 as a transactional
   2 -> 3 migration, with schema 1 advancing transitively through the already
   integrated 1 -> 2 migration. Preserve existing Job state and roll back the
   complete step on failure.
5. [ready for implementation after a committed decision baseline]
   Implement atomic
   selection/reservation and durable slot lifecycle around the existing
   concrete-offer and authority-claim boundary. Bind adopted offers to the
   selected participant, preserve append-only stage episodes, and migrate the
   Job store only under the accepted schema ruling. Persist lane and logical
   worker only; W71918 introduces the durable provider-neutral `AgentSession`
   identity and its correction/review continuity mechanics.
6. [pending W71917/W71918 composition] Compose implementation and review
   launch/settlement so every slot owns separate runtime, workspace,
   credential, output, and log identities. W71917 is approved and ready for
   operational submission; W71918 is blocked behind it. Reuse their outputs and do not implement their
   mount, checkpoint, correction, or verdict semantics here.
7. [pending focused verification] Prove two implementation and two review slots, offer/claim races,
   fallback from unavailable affinity, independent reviewer separation,
   review-ahead, launch failure, canonical cleanup release, wedged isolation,
   participant-bound adoption, explicit pool variants and separation classes,
   cross-lane session non-reuse, and restart recovery.
8. [pending independent review] Bind the verdict to the immutable proposal and
   enumerate every changed production and test path.

Child status: W73629 closed satisfying and is integrated at `4876751`. Its
append-only stage-episode recovery contract is now this leaf's baseline.

W32577 and unrelated exhaustive hardening do not gate this leaf unless a
measured failure makes the happy-path concurrency claim false.
