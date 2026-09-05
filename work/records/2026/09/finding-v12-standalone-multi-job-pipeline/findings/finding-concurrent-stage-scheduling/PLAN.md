# Plan

0. [done] Preserve the approved scheduler contract until the one-worker
   production launch seam and immutable-source/persistent-workspace boundary
   are integrated. Both prerequisites are now present in the committed
   baseline.

1. [done, reviewer revalidation 2026-09-03] Inventory the public offer, claim,
   attempt, session, cleanup and runtime-lane operations and the integrated Job
   projection. Append-only stage-episode recovery is part of the baseline; the
   focused 188-test Job-manager suite passes at that checkpoint.
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
   affinity/index shapes still shown in the relation list), inverted ownership
   between the scheduler and checkpoint/correction leaves for the
   provider-neutral `AgentSession` identity, and a test-boundary gap that makes
   the four-capacity acceptance vacuous on the current single-principal
   fixture. Decision 1's direction is otherwise sound and needs no redesign.
   See the FINDING's implementer revalidation.
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
   live uniqueness per worker, principal and stage episode. This scheduler
   leaf records no durable `AgentSession`; the checkpoint/correction leaf owns
   that identity and its continuity rules.
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
4. [done, operator acceptance 2026-09-03; revalidated 2026-09-05] Add the
   scheduler relations in one transactional schema migration. Schema 3 is now
   occupied by the integrated Authority binding, so this leaf advances 3 -> 4;
   schema 1 advances transitively through 1 -> 2 -> 3 -> 4. Preserve existing
   Job state and roll back the complete step on failure.
5. [done, tuner implementation 2026-09-05]
   Implement atomic
   selection/reservation and durable slot lifecycle around the existing
   concrete-offer and authority-claim boundary. Bind adopted offers to the
   selected participant, preserve append-only stage episodes, and migrate the
   Job store only under the accepted schema ruling. Persist lane and logical
   worker only; the checkpoint/correction leaf introduces the durable
   provider-neutral `AgentSession` identity and its correction/review
   continuity mechanics.
6. [done at the W71877 scheduler boundary 2026-09-05] Compose implementation
   and review launch/settlement through the selected generation/worker's
   distinct participant-bound Worker Manager operations. Reuse the integrated
   source and workspace boundary and leave checkpoint, correction, verdict,
   integration, and provider-neutral AgentSession identity to their owning
   leaves; do not reimplement them here.
7. [done, focused verification 2026-09-05] Prove two implementation and two review slots, offer/claim races,
   fallback from unavailable affinity, independent reviewer separation,
   review-ahead, launch failure, canonical cleanup release, wedged isolation,
   participant-bound adoption, explicit pool variants and separation classes,
   cross-lane operation separation, generation-preserving restart/reconfiguration,
   and settlement recovery. The focused Job-manager suite is 313 tests, including
   23 scheduler cases; the single-worker deployment regression is 92 tests.
8. [changes requested 2026-09-05] Independent review bound proposal
   `sha256:c65246632153bd23dd2ebbe991d70c7f7a5fa28df8d3338bc8d7b33c8d8796b5`,
   its 18 exact paths and every existing test change. See
   `review-2026-09-05T11-17-00Z.md` and retained
   `repro-2026-09-05T11-17-00Z.py`.
9. [done 2026-09-05] Fail closed on all seven reviewed gaps: revalidate
   principals for active and live prior generations at restart attachment;
   refuse stage operations without exact allocations; do not release on a
   broad durable admission refusal without canonical no-assignment evidence;
   validate the complete schema-3 object set before 3 -> 4 migration; make
   deliberate reactivation of a historical variant a new active generation;
   preserve operation-collision checks when release/recovery is replayed with
   changed operands; and actually drive four distinct-principal plus alias
   fake claims/runs through the accepted Authority-like slot boundary.
10. [done 2026-09-05] Add focused negative,
    restart, migration, replay and concurrency regressions for item 9; rerun
    the Job-manager and disk-backed single-worker suites; compare inherited
    red aggregate gates by exact failure text; then publish a new immutable
    proposal with exact base, path manifest and digest.
11. [changes requested 2026-09-05] Independent correction review found the
    schema-3 shape check still accepts changed partial-index predicates and
    omits CHECK constraints; the four-principal fixture still stops before
    launch/run, bypasses the pooled scheduler in its alias case, and does not
    prove failed-slot settlement. The handoff supplied a mutable working-tree
    content manifest, not the immutable proposal item 10 required. See
    `review-2026-09-05T11-57-43Z.md` and retained
    `repro-2026-09-05T11-56-00Z.py`.
12. [done 2026-09-05] Compare full schema-3 index predicates and table
    constraints before migration, with changed-predicate and changed-CHECK
    rollback regressions. Complete the four-principal composed launch/run,
    pooled alias, and durable failed-slot-settlement proof. The comparison is
    over `sqlite_schema.sql` with only comments, identifier quoting and
    punctuation spacing normalised, each reconciling one measured spelling
    difference between an installed and a migrated schema-3 store.
13. [changes requested on custody only 2026-09-05] Publish one new immutable proposal
    with exact base, base/candidate members, patch, path/mode/member manifest
    and recomputable digest. Reconstruct it independently, rerun focused and
    clean single-worker verification, inspect every correction and changed test
    assertion, and approve only that exact digest. Proposal `d4cfef92...`
    passes every content, reconstruction, behavior and test check, but its
    package directories are owner-writable `0775`, so its `0444` members remain
    replaceable. See `review-2026-09-05T12-16-39Z.md`.
14. [done; custody passed 2026-09-05] Freeze
    `/tmp/w71877-correction` and every directory beneath it to `0555`, retaining
    all evidence files at `0444` and changing no bytes. Recompute the same three
    digests and return the unchanged `d4cfef92...` proposal for a custody-only
    recheck. All 43 directories and 40 files now pass; all digests are
    unchanged. Review then found the proposal's three dossier import targets
    conflict with review-era append-only history.
15. [done 2026-09-05] Reseal the unchanged fifteen
    accepted production, test, and runner members as the import proposal.
    Exclude FINDING, PLAN, PROGRESS and every other dossier artifact as
    preserved evidence, naming them in the dirty-path exclusions. Recompute the
    new proposal and member-manifest digests, prove each of the fifteen members
    equals its `d4cfef92...` counterpart, and return for exact path/digest/test-
    authority sign-off. See `review-2026-09-05T12-22-21Z.md`.

    Done: the package is the fifteen members alone, every dossier artifact is
    named in its exclusions as preserved evidence, and no accepted member byte
    changed. The reason it must be that way is durable rather than incidental:
    append-only review history lands in FINDING and PLAN, so sealing them as
    importable members guarantees two targets that match neither base nor
    candidate by the time the proposal is reviewed.
16. [done; independently approved 2026-09-05] Recompute the package, prove its
    fifteen members equal the already accepted `d4cfef92...` members, repeat
    the exact test-change accounting, and route to operator target preflight.
    Proposal `ae076df9...` passes exact digest, path, byte, mode, custody,
    reconstruction, 333-test focused and 92-test disk-backed single-worker
    checks. See `review-2026-09-05T12-30-04Z.md`.
17. [queued for operator preflight, then integration] Restore only the 13
    modified proposal targets to exact base `6532e6f...` bytes and the two new
    targets to absence, preserving the whole W71877 dossier and every unrelated
    dirty path. Then route to `baton.merge` for strict preflight and exact
    15-member import of approved proposal `ae076df9...`; any drift or overlap
    returns for a new review rather than being repaired during integration.

Append-only stage-episode recovery is this leaf's baseline.

Unrelated exhaustive hardening does not gate this leaf unless a measured
failure makes the happy-path concurrency claim false.
