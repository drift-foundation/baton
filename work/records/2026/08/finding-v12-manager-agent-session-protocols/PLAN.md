# Plan: manager agent-session and runtime adapter protocols

1. [done 2026-08-24] Create this dossier and revalidate the frozen
   worker-control, agent-session and assignment-state contracts and the closed
   W4 record against the current tree. Recorded in `FINDING.md`: three
   vocabularies (runtime axis, session state, posture) that must not be
   collapsed; the deliberate asymmetry between the consent and execution
   runtime enums; and what W4 already ships, so this Job consumes it rather
   than restating it.
2. [blocked on W6592] Define the agent-session state machine over the frozen
   `sessionState` vocabulary, with consent and execution as distinct axes and
   `posture` as its own closed value. It hangs off W6592's public composition
   boundary rather than beside it, which is what the dependency is for.
3. [blocked on item 2] The adapter protocol contract: what an agent adapter
   must answer, typed, with **positive absence of a session** distinguished
   from an absent runtime — an agent that is gone and a container that is gone
   are different facts and the manager acts differently on each.
4. [blocked on item 3] Certified typed observations, effectively-once operation
   identities and restart reconciliation, reusing W4's journal rather than
   adding a second one.
5. [blocked on item 4] Cancellation ordering — fence, then agent, then runtime —
   preserved exactly as `request_cancellation` already orders it, with the
   session's own quiescence added without reordering the two that exist.
6. [blocked on item 5] Tests, evidence and independent review.

## Note on scope, for whoever routes this next

The title is broader than the gap. The runtime axes, their transitions and
their journalled observations are **already built** in W4 and green. What is
missing is the agent-session half and the adapter protocol document. Item 1
records the measurement; a reviewer may want to narrow the title to match it
rather than leave the Job looking larger than it is.

## Implementation — 2026-08-25

Status: **implemented and verified; awaiting independent review.** W6592 closed
satisfying, so items 2–6 were unblocked and are done.

2. [done] The agent-session state machine over the frozen nine, with consent
   and execution as distinct axes and `posture` as its own closed value.
   `sessions.SESSION_SUCCESSORS` is the §7.3 table; `unknown` is terminal and
   never becomes `closed`; `satisfies_runtime_quiescence_gate` always answers
   false and proves its argument rather than ignoring it.
3. [done] The adapter protocol contract — `AGENT_ADAPTER` (two operations) and
   `SESSION_OBSERVATIONS` (two closed SHAPES), with positive session absence
   distinguished from an absent runtime by a third recovery-evidence kind.
4. [done] Certified typed observations, an effectively-once opening identity
   derived from `(attempt, posture, intent)`, and `reconcile_agent_session` as
   the session half of restart reconciliation. W4's journal is reused; no
   second one was added.
5. [done] Cancellation ordering preserved exactly — fence, then agent, then
   runtime — with the session's own announcement added where the runtime
   axis's already was.
6. [done] Tests and evidence: `tests/manager/test_sessions.py`, 73 cases; the
   boundary inventory's ownership, probe and witness tables extended for every
   new entry; the text sweep's table extended for every new exported callable;
   the declared-operand list extended. `evidence/gate-baseline-2026-08-25.txt`
   and `evidence/gate-after-2026-08-25.txt` bound what this slice changed.
7. [changes requested 2026-08-25] Independent review accepted the implemented
   session-axis/posture/reconciliation/cancellation slice, but found the later
   confirmed interrogation extension absent. See
   `review-2026-08-25T05-24-03Z.md`.
8. [done 2026-08-25] Extend the not-yet-certified
   agent-adapter contract with two distinct operator interrogations: `probe`
   for immediate typed control-plane observation without a model turn, and
   `inquire` for a queued conversational request with separate delivery
   acknowledgement and correlated model answer. Bind both to the exact
   assignment/session/operation identity and deadline; journal and expose
   queued, delivered, answered, timed-out, unreachable and runtime-absent
   outcomes without treating timeout as cancellation. The Worker Manager,
   never the worker, publishes conversational answers into Baton.
9. [done 2026-08-25] Re-run the focused session/interrogation suite and the
   boundary, dependency and text inventories; record the exact full-gate delta
   against the existing red baseline; return the complete adapter contract for
   independent re-review and certification.

## Implementation — the interrogation split — 2026-08-25

Status: **implemented and verified; awaiting independent re-review.**

8. [done] `probe` and `inquire` are two operations, not one with a mode.
   - `worker_manager/interrogation.py`: `PROBE_ANSWERS` (`observed`,
     `unreachable`, `runtime-absent`) and `INQUIRY_ACKNOWLEDGEMENTS`
     (`queued`, `delivered`, `unreachable`, `runtime-absent`) are two closed
     sets. `answered` is deliberately NOT an acknowledgement: an adapter that
     could answer synchronously would be reporting a model turn it has not
     had. `_PROBE_OUTCOME`/`_INQUIRY_OUTCOME` translate each onto the durable
     axis as tables rather than branches.
   - `_ask` is the shared half: it binds the four identities from durable
     state and the live authority, journals the request THROUGH `store.transact`
     BEFORE the adapter is reached, and reports which of commit-or-replay
     happened through a commit marker rather than by reading the returned
     document — a fresh commit and a replay both answer `requested`, because
     that is what the row said both times. An exact retry therefore asks the
     adapter nothing, which for `inquire` is the difference between one model
     turn and two.
   - `schema.INTERROGATION_OUTCOMES` is the per-kind successor table over
     eight outcomes; the `interrogations` DDL CHECKs all eight, permits an
     `answer` only on an `inquire`, and refuses a `published_at` without one.
   - A timeout is the manager's observation about its own waiting: `timed-out`
     still admits `answered` (probe: `observed`), and nothing about it
     cancels.
   - `documents.interrogation_requested` and `documents.interrogation` are
     closed constructors; an absent probe observation is OMITTED, never
     nulled.
   - `AuthorityPort.publish_answer` is the manager's own act.
     `publish_inquiry_answer` refuses to publish what nobody answered, and is
     idempotent by the row. No worker holds a Baton or SQLite capability at
     any point.
9. [done] `tests/manager/test_interrogation.py`, 51 cases: positive and
   negative `probe`/`inquire` shapes, replay and operation collision, restart
   between enqueue/delivery/answer/journal/publication, deadline expiry
   without cancellation, `adapter-unreachable` versus `runtime-absent`, answer
   correlation, safe-turn delivery, and capability isolation. The boundary
   inventory's ownership/probe/witness tables, the text sweep, the declared
   operands and the §13 sweep are extended for every new entry. The exact
   full-gate delta is `evidence/gate-after-interrogation-2026-08-25.txt`:
   **nothing added to the red baseline**, one baseline failure removed by a
   commit that is not this claim's, and four reviewer-authored cases from
   W6630 and W6633 reported rather than fixed.

## Note on scope, resolved

The earlier note asked whether the title should narrow to match the measured
gap. It was not narrowed, and it did not need to be: the runtime axes W4 ships
are CONSUMED here rather than restated — the cancellation ordering and the
observation journal are W4's, extended — and the agent-session half plus the
adapter protocol are what this slice built. A reviewer expecting runtime axes
will find them where they already were, referenced.

## Independent re-review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T08-48-15Z.md`; the preceding awaiting-review status is
superseded.

10. [required] Make an exact `probe`/`inquire` retry independent of the
    manager's later wall clock. The operation signature uses stable operands;
    the first committed absolute deadline remains the durable replayed fact.
11. [required] Persist a successful probe's full closed observation atomically
    with `outcome: observed`, reconstruct it on lookup/list/replay/restart, and
    enforce observation/outcome coherence in the store.
12. [required] Own every adapter-provided observation value before it crosses:
    session state against the frozen vocabulary, last activity as an instant,
    and diagnostics against its bounded document/value contract.
13. [verification] Make the three additive reviewer regressions green, then
    rerun focused, inventory, full source, and locked installed-layout gates
    and record the exact delta against the standing red baseline.

## Second re-review correction — 2026-08-25

`review-2026-08-25T08-48-15Z.md` accepted the split as materially implemented
and named three defects. All three are corrected and all three of its additive
regressions are green and kept as written.

10. [done] **[P1] Wall time left the operation signature.** `_ask` signed the
    derived absolute `deadline_at`, so the same operation identity with the
    same caller operands collided with its own journalled request whenever the
    manager's clock had moved — which is exactly the ordinary restart the
    durable journal exists to survive. The signature carries
    `deadline_seconds`, the duration the caller actually asked for; the
    absolute deadline stays the operation's committed RESULT, written by `act`
    and returned by a replay, so the manager's FIRST observation is what every
    later caller sees. Two of my own cases pin both halves: a replayed request
    answers with the first deadline and asks the adapter nothing, and a
    DIFFERENT duration under one identity still collides.
11. [done] **[P1] The observation is durable.** `interrogations` gained an
    `observation` column, written in the SAME statement as the `observed`
    transition — a probe that recorded the outcome and then failed to record
    what it saw would leave exactly the row the schema now refuses. Two CHECKs
    state the pairing both ways: no observation on any other outcome, and no
    `observed` probe without one. `settle_interrogation` refuses the same pair
    in this build's own vocabulary first, so a caller reads a sentence instead
    of an `IntegrityError`. `_view` takes no observation argument any more —
    what a view says is what the row holds — so the replay, the single lookup,
    the list and a restart all report the reading. Schema version 9 → 10.
12. [done] **[P1] The observation is TYPED, not merely shaped.**
    `boundaries.alternative` closes member names and deliberately does not own
    their values, and the probe path did nothing afterwards, so a runtime-axis
    `running` crossed as an agent-session state and collapsed two vocabularies
    this Work exists to keep apart. `_observation` owns `state` as injected
    text and then against the frozen §7.3 nine — the same pair
    `reconcile_agent_session` already applied to its own observation —
    `last_activity_at` as an instant, and `diagnostics` through `_diagnostics`,
    which makes the provider's free-form report an exact bounded document.
    It matters more here than it did there because the value is now durable:
    an unowned reading would be written into the row and read back by every
    later lookup as though this manager had established it.

    `diagnostics` is bounded in BOTH dimensions — 32 entries, 2000 characters
    per value — because "bounded" has to mean bounded in the dimension a
    careless adapter would grow, and nested structures are refused: a durable
    column is not a place to put whatever an adapter felt like.
13. [done] The boundary inventory grew one delegation
    (`agent.probe.diagnostics` → `_diagnostics`) and three probes, one per
    newly owned member. `test_store`, the text sweep, the declared operands
    and the §13 sweep were re-derived rather than assumed.

## Third re-review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T10-26-49Z.md`.

14. [next] Defer the manager clock read and absolute-deadline arithmetic to the
    fresh transaction action, so an exact replay consults the journal without
    allowing the later clock to refuse or change it. Keep duration in the
    stable signature and the first absolute deadline in the committed result.
15. [next] Apply the observation owner and exact-provider-session binding at
    exported `settle_interrogation` as well as the fresh adapter path; re-audit
    repeated same-outcome settlement with a different observation.
16. [next] Bound diagnostic key text as well as entry count and values. Keep
    the additive long-key/safe-integer regression.
17. [next] Make the three additive regressions green, rerun focused and
    adjacent inventory gates, record the exact full/installed-layout delta,
    and return for independent review.

## Third re-review correction — 2026-08-25

`review-2026-08-25T10-26-49Z.md` confirmed the three previous corrections and
found three remaining boundary defects. All three are fixed and all three of
its additive regressions are green and kept as written.

14. [done] **[P1] No clock is read before the journal decides.** Moving
    `deadline_at` out of the signature removed the ordinary collision, but
    `_ask` still called `store._now()` and `boundaries.deadline(...)` BEFORE
    `transact` could decide replay — so an exact retry at a valid but late
    instant refused in the deadline arithmetic, a request whose durable answer
    already existed rejected because a NEW deadline would not fit. Both are
    inside the transacted `act` now, which `transact` runs only when it did
    not replay. The claim the previous correction made — that the second
    caller's clock decides nothing — is true at this boundary now rather than
    nearly true. My own case asserts the property rather than one instant: the
    replay path reads the clock ZERO times.
15. [done] **[P1] One observation owner, at every receiving door.** `probe`
    owned the adapter's reading and exported `settle_interrogation` took one
    straight from its caller to `canonical_text`, so a direct call could
    persist runtime-axis `running` as an agent-session state — the exact
    collapse the previous review found, surviving at the door nobody had
    checked. The public door now applies `_observation` AND the exact
    provider-session comparison; `_settle` performs the move over a reading
    somebody has already owned. That is PLAN 4bz's split, the same one
    `revive_refusal`/`_revived` uses, rather than owning the value twice —
    and it avoids putting an `owned=` flag on a public signature, which would
    have been internal state in an operand list.

    The idempotence re-audit the review asked for: a second settlement
    carrying a DIFFERENT reading is refused rather than answered with the
    first. Returning the first would tell a caller its observation was
    recorded when it was discarded.
16. [done] **[P1] A diagnostic NAME is bounded like its value.** The
    per-entry bound applied to values alone, so one 2001-character key passed
    and took the durable document past the bound the function states. A bound
    on half of an entry is not a bound on the entry. A case pins both the
    refusal and the exact-length acceptance, because a bound that refused
    legitimate reports would be a different defect.
17. [done] Gate bookkeeping: the durable-writer sweep entry follows the rename
    to `_settle`; the obsolete stated owner for `settle_interrogation`'s
    observation is REMOVED, because the door owns it now and the inventory
    refuses an entry owned twice; five probes were added for the public
    settlement door and two for the newly read columns;
    `interrogations.session_epoch` joins `NO_PROBE` beside the other STRICT
    INTEGER columns SQLite will not let a writer spoil.

## Fourth re-review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T11-30-14Z.md`.

18. [next] Put mutable live-assignment validation inside the fresh journal
    action. Preserve the fresh-operation stale-assignment refusal, but let an
    exact retry replay its durable answer without a second Baton authority or
    adapter decision.
19. [next] Apply `check_no_durable_secret` to the raw probe observation at its
    common receiving owner, before diagnostic construction can quote a
    secret-bearing value and before either receiving door can persist it.
    Correct the durable-writer inventory reason to name the walk that actually
    covers the observation.
20. [next] Make the two additive regressions green, rerun the focused and
    adjacent boundary/section-13 inventories, record the exact full and locked
    installed-layout delta, and return for independent certification.

## Fourth re-review correction — 2026-08-25

`review-2026-08-25T11-30-14Z.md` confirmed the third correction and found two
further boundary defects. Both are fixed and both additive regressions are
green and kept as written.

18. [done] **[P1] The live authority read moved inside the fresh action.**
    `_bound_session` consulted `port.assignment_of` before `store.transact`,
    so an exact retry of an already answered operation was refused once the
    assignment ended — the second authority observation deciding a historical
    operation exactly as the second clock did before the previous correction.
    The DURABLE half stays where it was, because the stable signature is built
    from it; `_still_live` runs inside the action `transact` executes only on
    a fresh commit. A fresh interrogation still requires the live exact
    generation, and a case holds that half — including that a refused fresh
    request is not journalled.

    My own case states the two corrections as ONE property and counts both
    mutable inputs: on the replay path the clock is read zero times and the
    authority is asked zero times. A third mutable input added later now has
    somewhere to fail.
19. [done] **[P1] §13 at the observation's common receiving owner.**
    `_diagnostics` owned shape, count, key and value types and lengths, and
    ownership is not `check_no_durable_secret` — so a diagnostic named
    `claim_token` was owned, accepted and written to the durable column. The
    raw adapter answer is walked in `_observation`, the one owner both the
    fresh path and the exported settlement reach, before the members are
    composed, because the walk's named half is about member NAMES. The
    durable-writer inventory reason names the path that performs the walk.

    The cases iterate `SECRET_MEMBERS` itself rather than a retyped list, so a
    name outside the frozen set is not quietly treated as a secret.
