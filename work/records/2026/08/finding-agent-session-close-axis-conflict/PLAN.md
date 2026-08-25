# Plan: reconcile agent-session close with the observation axis

1. [done 2026-08-23] Preserve the frozen-table probe and record the four
   forbidden transitions currently taken by `closeAgentSession`.
2. [done 2026-08-23] Revalidate §3.3, §7.3, the executable successor table, the partial
   unique index, session open/close callers, transport-loss paths, and the
   posture-release assumptions in signed-off tests.
3. [done 2026-08-23; approved] Rule how an ordered/aborted session end, an observed
   terminal turn fact, provider absence, `unknown`, and posture reuse compose
   without either inventing knowledge or permanently stranding the posture.
   Keep the observation axis unchanged; add a separate manager-owned
   `available -> occupied -> recovery-required -> available` posture axis.
   Recovery is explicit and evidence-backed. For the OCI adapter, verified
   stop or absence of the exact assignment container recovers the slot
   immediately while outputs remain pending separate disposition.
4. [queued for implementation] Append an explicit correction or supersession to the
   owning ACP record and update the model, schema/store constraints, close and
   observation entry points, recovery path, and focused race/restart tests as
   one change.
5. [queued] Re-review W4 composition and every adapter consumer against the
   corrected lifecycle before W4 closes.
4. [done 2026-08-23] Implemented as one change. Schema 13 -> 14 removes the
   partial unique index on `agent_session_state` and adds `posture_slots`;
   the superseded index's comment is kept and marked superseded rather than
   deleted. `posture_slots.mjs` carries `occupySlot` (a compare-and-set inside
   `openAgentSession`'s own transaction), `requireSlotRecovery`, `releaseSlot`
   and `postureSlot`. `RECOVERY_EVIDENCE` is a closed two, and a stop request,
   an elapsed deadline and a disconnect are named non-members;
   `runtime-absent` requires the exact identity observed. `closeAgentSession`
   is the NORMALLY OBSERVED end: it moves the observation through the axis
   boundary and releases the slot on that observation. The correction is
   appended to the owning ACP record, superseding nothing in §3.3 or §7.3.
   Two signed-off cases migrated on this record's authority, each preserving
   what it proved and gaining an assertion that recovery rewrote no history.
   Eight mutations, all witnessed; one check MEASURED as unreachable behind
   the column's CHECK constraint. 16 new cases.
   Evidence: `evidence/implementation-2026-08-23.txt`.
5. [queued] Re-review W4 composition and every adapter consumer against the
   corrected lifecycle before W4 closes. Unchanged by item 4: this Work
   delivers the lifecycle, and W4's integrated composition must still be
   revalidated against it.
6. [changes requested 2026-08-23; independent review round 1] Bind ambiguity
   and release mutations to the exact session epoch; bind normal-close and
   runtime-absence evidence to the corresponding durable observation and
   exact attached runtime identity; compose transport loss with the same
   epoch's `recovery-required` move across retry/restart; and make the five
   additive reviewer regressions pass. Rename the now-false signed-off test
   title under the case-specific authority recorded in the review. Evidence:
   `review-2026-08-23T18-49-02Z.md` and
   `evidence/review-round1-2026-08-23.txt`.
4. [changes requested 2026-08-23; first review] Three P1s in
   `review-2026-08-23T18-49-02Z.md`: slot mutations were not bound to
   `sessionEpoch`, so delayed epoch-1 evidence moved or freed epoch 2;
   evidence NAMES were accepted without proving the named durable fact; and
   `handleTransportLoss` recorded `unknown` without moving the same slot to
   `recovery-required`. Evidence: `evidence/review-round1-2026-08-23.txt`.
4. [done 2026-08-23] All three closed. Both mutations take `sessionEpoch` and
   compare it inside the write transaction, including in the idempotent
   branches; `occupySlot` takes the same operand name so the module says one
   thing. `proveEvidence` reads the named fact — `provider-session-closed`
   requires the same epoch's durable `closed` observation and `runtime-absent`
   requires the exact `attempts.runtime_id` — and runs BEFORE the slot state
   is read. Transport loss and close each compose observation and slot
   movement in ONE transaction through new `...In` variants, so a crash
   leaves both or neither. AND ONE THING THE REVIEW DID NOT ASK FOR BUT ITS
   CASE REQUIRED: a delayed close still RECORDS its observation and releases
   only if the slot is still its own, reporting `releasedSlot: false`
   otherwise — epoch 1's session really did close whatever the posture has
   done since. Seven mutations, all witnessed; one reported zero because a
   case was missing rather than because an instrument was wrong, and the case
   was added. The signed-off title is renamed on the review's authority with
   every assertion retained and three added. 22 posture-slot cases; W771's
   suites are green.
   Evidence: `evidence/correction-2026-08-23.txt`.
5. [queued] Re-review W4 composition and every adapter consumer against the
   corrected lifecycle before W4 closes. NOT discharged by item 4: that round
   composed the two product entry points W771's own rule reaches; the sweep of
   every consumer remains this item's.
4. [changes requested 2026-08-23; independent review round 2] Preserve an
   exact epoch's transport-loss observation when its slot has already been
   positively recovered or now belongs to a newer epoch. Keep the strict slot
   APIs strict; in the product composition, move only an applicable slot,
   retain the independent `unknown` observation, report the slot fact that
   actually holds, and make both additive retry/delay regressions pass.
   Evidence: `review-2026-08-23T19-28-58Z.md` and
   `evidence/review-round2-2026-08-23.txt`.
4. [changes requested 2026-08-23; second review] One P1 in
   `review-2026-08-23T19-28-58Z.md`: `handleTransportLoss` still rolls an
   exact-epoch observation back when its slot has separately advanced.
   Evidence: `evidence/review-round2-2026-08-23.txt`.
4. [done 2026-08-23] Closed. Transport loss composes like a delayed close: the
   observation lands, the slot moves only when it is this epoch's AND
   occupied, and the answer reports the occupancy that ACTUALLY holds. The
   strict slot API is unchanged — what changed is that the composition no
   longer asks it a question that does not apply. THE REVIEWER TAUGHT ME THIS
   ASYMMETRY IN ROUND 1 and I applied it to `closeAgentSession` and not one
   function over; the added case is therefore shaped as a shared PROPERTY over
   both endings rather than a third instance. Four mutations, all witnessed —
   one of them first showed witnesses belonging to another Work, which is a
   reminder that a mutation's witnesses must be checked for whose they are.
   25 posture-slot cases; W771's suites green.
   Evidence: `evidence/correction-round2-2026-08-23.txt`.
5. [queued] W4 integration review against the corrected lifecycle. The second
   review's own consumer sweep found no additional `v12/src` posture-slot
   consumers, so what remains is the integration review rather than a search.
5. [done 2026-08-23; independent sign-off] Re-reviewed the current W4
   composition and every `v12/src` posture-slot consumer. The only product
   compositions are atomic occupation in `openAgentSession`, normal-close
   release in `closeAgentSession`, and ambiguity handling in
   `handleTransportLoss`; no adapter consumer derives capacity from provider
   observation. The round-2 retry and delayed-epoch regressions pass, both
   endings report the occupancy that actually holds, and the direct slot API
   remains strict. W771's focused gates are 25/25, 18/18 and 16/16. Full v12
   is 646/652, with all six failures independently owned by W543, W641 and W4.
   Review: `review-2026-08-23T19-48-06Z.md`; evidence:
   `evidence/signoff-round3-2026-08-23.txt`.
