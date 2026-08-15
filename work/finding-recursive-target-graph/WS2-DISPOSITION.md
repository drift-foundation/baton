# WS-2 adversarial disposition

Author: `baton.implementer`
Date: 2026-08-14
Responding to: `04ed75fc66f1594637ab9ff2e55bf671` (challenge decisions
before implementation)

I walked all eight WS-2 workflows and all seventeen focused-regression
classes against the current (WS-1-accepted) authority, deliberately hunting
for contradictory transitions, missing states, ambiguous authorization,
non-atomic boundaries, unrepresentable JSON, and conclusions that do not
follow from the pinned model. **No blocker requiring a new Slawomir ruling
remains.** One genuine model tension exists (T1) with a resolution inside
the pinned model; the rest are ambiguities the battery leaves to mechanical
choice, each named below with the choice I will use. Anything the reviewer
dislikes here is cheap to change before code exists.

## T1 — a due "event" cannot exist at T under pure reads (WS2-WF-03.2)

The pinned model has pure reads, no daemon, and no scheduler. At `review_at`
nothing runs, so no durable event ROW can exist "at T" — only the DERIVED
due state can. Yet WS2-WF-03.2 says "At T, assert one due review event",
and the Due-time regression row says "one deadline generation produces at
most one notification across reads and restart" — the "across reads"
phrasing itself confirms reads must not create it.

Resolution (inside the model, mirroring the wake mechanism): due-ness is
derived at read time and shown actionable in every projection immediately;
the durable due-notification audit event is emitted level-triggered by the
FIRST committing write transaction at or after `review_at`, guarded in-lock
by a per-round deadline generation so restarts and racing writers cannot
duplicate it. WS2-WF-03.2's assertion therefore runs after any committing
act (the story's own step-4 extension suffices; a test may also use any
innocuous act). Work/phase/Current/candidate/assignments remain untouched
either way, exactly as the story demands. If the reviewer wants a due event
that exists with NO subsequent write ever occurring, that requires a
scheduler and is a product gap needing a ruling — I do not believe the
battery requires it, and I will not build one silently.

## T2 — deterministic time needs an injectable clock

"Before/at/after `review_at` boundaries are deterministic" is untestable
against a wall clock. The authority will take an injectable UTC time source
(production default: wall clock; tests inject). `review_at` is stored as
UTC ISO-8601 and compared as such — storage order cannot be altered by
any display timezone, satisfying the clock-zone row without a ruling.

## Ambiguities resolved mechanically (each named, none guessed silently)

1. **Provider-outcome scope.** "Every provider close names exactly
   satisfying|non-satisfying." A work is a provider iff, at commit, it has
   at least one incoming dependency edge OR has ever had a verification
   round (the time-based ruling requires the close to record the round
   summary and disposition, so a round forces the explicit outcome even if
   every dependent already closed). Outcome is permitted and recorded on
   any close. Omission where required refuses in-lock.
2. **Duplicate route selection in one round** (battery says "refuses or
   canonicalizes"): REFUSES. Silent dedup is for `+` wildcard fan-out;
   an exact selection listing one endpoint twice is an authoring error the
   author should see.
3. **`follow_up_of` targets closed Work only.** Every story uses a closed
   target and the matrix ties follow-up to preserving CLOSED history; a
   "follow-up" of open work is ordinary relation and would blur the one
   deliberate exception to closed-work immutability.
4. **Assessment window.** Reports in ANY round (open, abandoned, closed
   round) remain assessable and re-assessable while the WORK is open —
   adjudication is about the work's evidentiary record; rounds control
   assignments, not judgment. Closed work refuses assessment (matrix).
5. **Extend semantics.** `extend` sets `review_at` to a value strictly
   greater than both the current clock and any prior `review_at`; it may
   give a deadline to a round created without one (that is "setting a
   later review_at" from none). Creating or extending to a time already in
   the past refuses — a deadline born expired is a loose end.
6. **Notification form.** "Notified" (withdrawals, due) = an audit event
   carrying the route's resolution snapshot, committed atomically with its
   causing act, plus projection visibility. v11 has no push channel; the
   live-coordination mailbox is protocol 10's job, not this authority's.
7. **Assignments are their own records**, not obligation rows: their state
   machine (pending → passed|failed|unable reported, or → withdrawn, plus
   append-only assessments) does not fit obligation semantics, and WS-1's
   obligation-backed waiting must keep naming classic `@` obligations
   only. Assignments surface beside obligations in the team's actionable
   projection. A late `respond` against an assignment is impossible by
   construction (different verb, `report`), satisfying WS2-WF-08.4.
8. **Round identity** is work-scoped ordinal (1, 2, …); the candidate
   string is required, non-empty, and immutable per round.
9. **Reports carry evidence as text** (like message bodies/disposition
   rationales); dossier/artifact binding is WS-6's deferred surface and no
   WS-2 assertion requires more.

## Decision/test impact inventory (superseded surfaces)

- `reopen_work`, its CLI verb, its projection availability, its wake-sweep
  hook, and both in-lock reopen regressions plus the
  hide-reopen-under-closed-parent availability regression are removed —
  authorized by PLAN ("replace the accepted-but-superseded reopen
  implementation/tests").
- WF-05 step 6 and WF-06 step 5 (reopen legs) are rewritten; their
  level-triggered close assertions survive; WS2-WF-06 owns the
  contradiction story now.
- Refusal messages that ADVISE reopening ("reopen it first, visibly" on
  post/block/child-creation/classify) are reworded — advice to use a
  removed operation would be the surface lying about the model.
- `was_current_*` stays recorded in close events as historical evidence
  (history is where cleared facts live); nothing reads it for restoration
  any more.
- The close event's atomic scope grows: outcome, round closure, pending
  withdrawals + their notifications, dependency recomputation, wakes, and
  the audit rows commit together or not at all (fault-injection proven,
  per the Atomic-close row).

## Classes challenged with no remaining issue

- **Authorization**: every round/report/assess/close authority maps to the
  two existing in-lock gates (Current-handler; named-route-handler), both
  already proven under reassignment. No ambiguity found: "responsible
  reviewer" is everywhere the LIVE Current handler, so authority follows
  `=>` mid-round by design, and historical snapshots are already immutable.
- **Cardinality**: exact-endpoint refusal machinery exists (`@`/`=>`);
  assignment selection reuses it.
- **State machines** (assignment, round): all transitions enumerable, all
  terminal states named, no unreachable or contradictory state found;
  every mutation gets the established in-lock recheck.
- **Counters**: `reported/assigned` with separate withdrawn count is
  internally consistent in every story including WS2-WF-03.6 (1/3 + 2
  withdrawn) and WS2-WF-08.3; no story implies a decrementing assigned.
- **Reviewer discretion / provider outcome / immutable close / follow-up**:
  checked against WS-1 wake and gating rules — either terminal outcome
  closes the gate, wake fires only on the last gate, `waiting` consumers
  queue, others hold, Current never moves; representable with current
  machinery plus the new columns. No automatic transition sneaks in
  anywhere: every branch in every story has an explicit audited actor.
- **Races/rollback/restart**: each named race serializes to the in-lock
  recheck pattern; the atomic-close fault injection is testable through
  the `_write` seam already used by four accepted regression families.
- **JSON/projection/TUI parity**: every field the matrix lists is
  representable; round detail adopts `home`'s one-snapshot read
  transaction so all four counts, per-assignment axes, due state, and
  `snapshot_seq` describe one snapshot. The raw-report-versus-assessment
  two-axis display fits the bounded renderer with an explicit compact map
  (labels to be ruled like R5 — I will NOT invent compact labels; the
  canonical words render fully in detail views and the bounded table can
  carry them until a vocabulary ruling, failing visibly on anything
  unmapped, consistent with the R5 precedent).
- **Audit**: every act's payload composition is already the established
  pattern (actor + resolution snapshot + generation + rationale fields).

Awaiting release of implementation group 1.
