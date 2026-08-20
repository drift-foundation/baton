# Finding: make overdue claim pickup explicit

## Observation — 2026-08-20

W2780 was passed from `baton.claude` to `baton.codex` and became ready,
unclaimed Work. The authority correctly projected `pickup=overdue`, and the
Codex readiness bridge recorded that it forwarded the actionable episode, but
the reviewer did not act on it. The ordinary Jobs presentation did not make
the overdue pickup explicit enough to distinguish this condition from benign
queued Work.

This is not a stale-claim or heartbeat problem: nobody holds the Work. It is
the interval after a real handoff during which an eligible recipient has not
claimed ready Work.

## Confirmed ruling — 2026-08-20

**Confirmed by Slawomir.** Baton must visibly say when claim pickup is overdue.
The existing canonical `pickup` states remain the source of truth:

- `pending` means ready, handed-off, unclaimed Work is still inside the pickup
  grace period;
- `overdue` means that same Work has not been claimed before the configured
  threshold;
- `claimed` means a Handler now holds it; and
- blocked, parked, terminal, or never-handed-off Work has no claim-overdue
  alert.

This supersedes only the earlier presentation ruling that suppressed elapsed
pickup alerts. It does not restore claimant-heartbeat alarms: a claimed agent
may be busy inside one model turn, while overdue pickup proves that no Handler
started execution at all.

Phase remains the scheduler state and Handler remains the actual claimant.
Presentation must not encode either fact falsely. The Jobs list exposes a
separate compact `Claim` cue (`pending`, `overdue`, or `-`), and Work detail
spells the condition out as `claim pending` or `claim overdue`. JSON continues
to expose structured `pickup`; clients never parse TUI wording.

## Acceptance boundary

- A real pass/return to ready unclaimed Work shows `pending`, then `overdue`
  at the existing canonical threshold without an authority mutation.
- Claiming clears the alert and records the Handler atomically.
- Release or a later pass starts the correct new pickup episode.
- Dependency- or Message-blocked Work, parked Work, terminal Work, and fresh
  Work with no handoff never claim overdue pickup.
- The cue is visible in Jobs and Work detail and remains structurally
  represented as `pickup` in JSON.
- Focused projection, TUI, refresh, parity, packaged-app, and boundary tests
  distinguish pickup overdue from claimant heartbeat silence.

## Related history

This ruling explicitly supersedes the pickup-alert suppression in
`work/records/2026/08/finding-recursive-target-graph/findings/finding-tui-held-duration/findings/finding-unclaimed-work-cue/FINDING.md`.
That record's decisions about Handler honesty, scheduler Phase, blocked Work,
and heartbeat silence remain in force.

## Placement ruling — 2026-08-20

**Confirmed by Slawomir.** Horizontal space is scarce, so the Jobs table does
not gain a net-new attention column beside `New`. Remove the `New` column and
put `Claim` in that presentation budget.

- Keep `Msg/My`: `Msg` exposes total conversation activity and `My` exposes
  unresolved directed actions the viewer can answer.
- Remove only the Jobs-list `New` column. Personal unseen state remains
  canonical JSON and remains visible where it drives action: Inbox, Threads,
  Message indexes, Work detail, and explicit `new` reads.
- `Claim` renders `pending` for ready, queued, handed-off Work inside the
  pickup grace period; `overdue` after the existing canonical threshold; and
  `-` once claimed or whenever pickup is not currently possible or applicable.
- In the Jobs table, `Claim` sits immediately after `Phase`, before `Cat`:
  `Id Title Wait Pr Phase Claim Cat Msg/My Endpoint Via Handler Run Next Held`.
  This groups the scheduler state with its pickup state while keeping Handler
  reserved for the actual participant that won the claim.
- A blocked or parked row therefore never says `pending` merely because it
  retains historical handoff data. The cue answers whether somebody should
  claim now, not whether a handoff once happened.
- Preserve the full words `pending` and `overdue`; this operational condition
  is not compressed into a glyph. Retain `Claim` ahead of lower-value
  informational columns under width pressure.

This placement does not change unread-message semantics or authority state.
It reallocates one list column from passive traffic to missing execution.

## Definition gap — 2026-08-20

**Clarification by Slawomir.** The need for a visible claim-overdue cue, the
removal of the Jobs-list `New` column, and `Claim` immediately after `Phase`
are confirmed. The earlier text overstates agreement on the underlying overdue
policy. The existing six-minute projection is prior implementation, not a new
ruling.

Implementation is blocked until the following are decided:

- which event starts a pickup episode: only a pass/return handoff, or every
  entry into ready `queued` state including creation, reroute, and unblock;
- whether time spent blocked, parked, or otherwise unclaimable is excluded and
  a later return to `queued` starts a fresh episode;
- the threshold and whether it is fixed or deployment-configurable; and
- whether overdue means only that a Work-level claim deadline elapsed, or
  attempts to infer that a particular eligible agent was idle and failed to
  act. The latter requires an explicit capacity/assignment rule and cannot be
  inferred from a multi-handler Route alone.

Until those questions are ruled, `pending`/`overdue` placement is a UI shape,
not an implementation-ready semantic contract.

## Capacity ruling — 2026-08-20

**Confirmed by Slawomir.** Queued Work is not claim-overdue merely because it
waited while its eligible agent was executing another Job. That is occupied
capacity, not a missed pickup.

- A claim-opportunity interval exists only while the Work is ready and queued,
  has no Handler, and at least one member eligible through its live Route has
  free execution capacity.
- If every eligible member is actively handling another Job, `Claim` renders
  `-`; that interval accrues no overdue time.
- When capacity first becomes available, a fresh continuous opportunity
  interval begins. If all eligible capacity becomes occupied again before the
  threshold, that interval ends rather than aging invisibly; later availability
  begins a new interval.
- On a multi-handler Route, the cue belongs to the endpoint. It says that at
  least one eligible slot was continuously free and nobody claimed this Work;
  it does not accuse a particular member.

**Still open:** v11 must define the capacity unit before implementation. The
recommended simple contract is one active Work claim per participant across
all Routes, with a second claim refused. A configurable capacity greater than
one would require a separately explicit model; absence of a limit makes
`free capacity` unknowable and therefore makes the overdue cue dishonest.

## Ownership supersession — 2026-08-20

**Confirmed by Slawomir.** The Jobs `Claim` column and Work-detail Claim field
ruled above are superseded and must not be implemented. A Job is queued and
unclaimed; it is not the entity that owes a claim. The AGENT with available
capacity owes pickup. Showing the condition on every eligible Job would turn
one idle participant into N duplicate overdue rows and falsely attach a
member-level failure to Work records.

- Remove the Jobs-list `New` column as already confirmed, for horizontal-space
  priority, but add no `Claim` replacement to Jobs.
- Surface claim-overdue state on the Teams/member surface. One participant is
  overdue at most once, regardless of how many actionable Jobs it could claim.
- The member-level condition may identify the canonical next actionable Work
  for diagnosis, but that Work does not own the alert.
- A participant actively handling another Job is busy, never claim-overdue.
- The prior Work-level `pickup` projection is not authority for this new cue.
  Whether it remains as handoff history or is retired in a later schema is a
  separate compatibility/cleanup decision.

The exact Teams presentation, opportunity start, participant availability
test, threshold, and clearing rule remain open. W2938 returns to design until
those are confirmed.

## One obligation per participant — 2026-08-20

**Confirmed by Slawomir.** Assigning ten Jobs to one participant does not make
ten Jobs overdue. The participant can owe at most one pickup action:
**claim one actionable Job**.

- A participant handling any claimed Job is busy and owes no pickup.
- An idle participant with no actionable Work owes no pickup.
- An idle participant with one or many actionable Jobs has one pending pickup
  interval and, after the ruled threshold, one claim-overdue state.
- Adding, removing, reprioritizing, or reordering Jobs while that actionable
  pool remains nonempty neither multiplies nor resets the interval.
- Claiming any eligible Job satisfies the one pickup obligation. Remaining
  Jobs are ordinary backlog. When the participant later becomes idle, a
  still-nonempty actionable pool starts one new grace interval.
- The Teams/member detail may show the canonical first actionable Work as a
  diagnostic or suggested next action, but that locator is not the owner of
  the overdue state and does not turn the remaining queue into overdue Jobs.

For a shared Route, each idle eligible participant evaluates its own one
pending-pickup condition; a successful competing claim removes that Work from
the others' actionable pools. The cue never bypasses the atomic claim race.

## Cross-tab attention ruling — 2026-08-20

**Confirmed by Slawomir.** The top-level Teams tab is the persistent cue while
the operator remains focused on Jobs:

- render `[Teams*]` when one or more participants are claim-overdue;
- render ordinary `[Teams]` otherwise;
- use the same `*` attention vocabulary already chosen for Inbox rather than
  inventing another alarm glyph;
- attach no Claim field, suffix, or alert to any Job row; and
- opening Teams exposes the responsible participant rows and their details.

The tab carries no count. One star means “Teams needs attention”; it does not
multiply with Jobs or participants. A separate global banner is not part of
this ruling.

## Complete participant pickup contract — 2026-08-20

**Confirmed by Slawomir.** Claim pickup is one participant-level scheduling
obligation with one-slot capacity, not a Work property.

### Capacity and actionable pool

- A participant may hold exactly one active Work claim. A second claim is
  refused while the first remains live.
- The participant's actionable pool is the unclaimed Work action set returned
  by canonical participant-relative `wait`: open, ready Work whose live Route
  resolves to that exact member. Claimed continuation, obligations, trials,
  pokes, and runtime refreshes are not members of this pool.
- A participant holding any Work is busy and owes no pickup. Runtime-reported
  `working` without a canonical Handler does not make the participant busy;
  it is a useful contradiction, not authority.
- Runtime `offline`, `waiting-input`, `retrying`, `failed`, stale, or unknown
  may explain why pickup is late but never hides the obligation. Configured
  Route eligibility plus canonical Handler/Work state decide it.

### Opportunity interval

- One pending interval starts when an idle participant's actionable pool
  changes from empty to nonempty, or when the participant becomes idle while
  that pool is already nonempty.
- Adding, removing, reprioritizing, or reordering Work does not reset the
  interval while the pool remains continuously nonempty. This includes a
  competing handler claiming one offered Work when others remain actionable.
- A successful claim of any eligible Work clears the interval because the
  participant becomes busy. An empty actionable pool or loss of Route
  eligibility clears it too.
- When a busy participant later becomes idle with actionable Work remaining,
  a new interval begins; elapsed time from the earlier busy period never
  resumes.
- The interval and its start are canonical and survive client/runner restart.
  Passage of time derives `pending` versus `overdue` at read time and performs
  no timeout event or workflow mutation.

### Threshold and configuration

- The default overdue threshold is 360 seconds.
- Deployments may configure the positive threshold as authority policy; all
  clients consume the accepted value and do not carry private thresholds.
- Inside the threshold the member is `pending`; at or beyond it the member is
  `overdue`. The schema/config spelling is an implementation detail, but the
  accepted policy value and interval origin must be exposed structurally so
  JSON clients never parse TUI wording or recompute against local guesses.

### Presentation

- Jobs removes its `New` column and gains no Claim/Pickup replacement. Work
  detail likewise carries no participant pickup field.
- Teams member rows gain `Pickup`: `-`, `pend`, or `late`. An overdue member
  row is bold.
- Member detail spells out `pending` or `overdue`, the elapsed interval, and
  the canonical first actionable Work as a suggested next claim. The locator
  is diagnostic; it does not make that Work the owner of the obligation.
- The top-level tab renders `[Teams*]` if at least one participant is overdue
  and ordinary `[Teams]` otherwise. Pending alone does not add the star.

For a shared Route, every idle eligible participant evaluates its own single
interval. The atomic claim remains the arbiter: after one member wins, every
other member's actionable pool and cue are recomputed from canonical state.
