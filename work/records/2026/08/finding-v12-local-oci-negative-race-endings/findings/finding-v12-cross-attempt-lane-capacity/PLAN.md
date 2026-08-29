# Plan

1. Revalidate authority claim capacity, W16821/W16823 principal context,
   offers/attempts, posture slots, runtime start and cleanup settlement.
2. Pin the cross-attempt lane identity, ownership/restart rules and exact
   release condition without using attempt id or endpoint spelling as the
   canonical capacity identity.
3. Version manager persistence/projections and compose lane acquire/release
   with runtime start and complete cleanup.
4. Add predecessor/successor, concurrent winner, restart, retry, uncertainty,
   provider-unresolved, retained/quarantined and principal-isolation tests.
5. Run focused daemon-free and required Docker gates, then return for
   independent review before W32382 can close.

## 2026-08-29 — implemented

1. [done] Revalidated against the delivered tree rather than the brief: both
   gates closed satisfying, manager schema 12, `assignment_principal` and
   `assignment_scope` on the attempt row, no lane table.
2. [done] The identity is pinned in `FINDING.md` and in `lanes.py`'s header,
   with each of the four parts argued and each of the three exclusions --
   attempt id, generation, participant -- argued separately.
3. [done] Manager schema 13 and the `runtime_lanes` table. Acquire composed
   into `request_runtime_start`'s journalled transaction; release composed into
   the cleanup ending.
4. [done] `tests/manager/test_runtime_lane.py`: predecessor/successor,
   concurrent winner over three real threads, restart, second start, double
   release, uncertainty, provider-unresolved, retained/quarantined, failed
   cleanup, cancellation, principal isolation and the projection.
5. [done] Focused and full daemon-free gates plus the four real-daemon serial
   suites. Every guard measured by removal.

## 2026-08-29 — independent review

4. [done] Corrected the stated acceptance limit with an additive real
   offer/claim/activation regression and added the distinct-principal race that
   isolates the in-transaction per-Work interlock.
6. [changes requested] Own the relational integrity of each adopted
   `runtime_lanes` row: its stored `lane_id` must derive from its four stored
   identity parts before either projection path uses it. Keep the failing
   corruption regression green, rerun the focused lane suite and boundary
   inventory, and return for independent review.
7. [changes requested] Apply that relation owner to the two remaining
   persistence reads: `_no_predecessor_holds` and `_occupy_lane`'s
   insert-conflict lookup. Keep both additive corruption regressions green,
   enumerate all four reads in the boundary inventory, rerun the focused lane
   suite and mutation evidence, and return for independent review.

## 2026-08-29 — the start-path lane reads

- [done] `_no_predecessor_holds` and `_occupy_lane`'s conflict path select the
  COMPLETE row and pass it through `_adopted` before reading any member, so a
  split relation refuses `integrity/schema` rather than being reported as an
  ordinary predecessor or an ordinary race loss.
- [done] `lane_probes` enumerates all four `runtime_lanes` reads, with a
  predecessor driver and a primary-key-collision driver for the two the
  inventory did not previously see.
- [done] Two mutations, two named failing cases; `test_runtime_lane` 29 OK
  including both reviewer regressions.

## 2026-08-29 — independent final disposition

- [accepted] Both start-path reads own the complete persisted lane relation
  before classifying contention.
- [accepted] The boundary inventory reaches all four lane-read sites; the two
  correction mutations each fail their named regression and restore cleanly.
- [done] W32649 satisfies the lane identity, acquisition, release, race,
  restart, provider, projection and real-successor acceptance and can close.
