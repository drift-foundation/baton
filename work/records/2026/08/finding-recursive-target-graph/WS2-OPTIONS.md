# WS-2 options and recommendations for the three held mappings

Author: `baton.implementer`
Date: 2026-08-14
Responding to: `5fba3a24dafb64a908cddd4ce833cca1`
No source or test edits have been made; the tree is the accepted WS-1 state.

## Q1 — due notification under pure reads

The requirement: the responsible reviewer is actionably notified when
`review_at` arrives; reads are pure; there is no daemon.

- **Option A — derived-only due (RECOMMENDED).** Due-ness is a pure
  function of the stored `review_at`, the injected clock, and the round's
  deadline generation. No durable "became due" event row exists at all —
  it would record no information the audit trail does not already hold
  (`review_at` and its generation are recorded when set; every decision
  after it is audited). "Notifies its responsible reviewer" means: the
  moment `now >= review_at`, the round appears as DUE and actionable in
  the reviewer's default projections — the team summary gains an
  always-visible `due` count beside `parked` (same in-the-faces rule), the
  work detail and round projection say `due: true`, and the actionable
  list for the responsible route includes the due round. "At most one
  notification per deadline generation across reads and restart" is
  trivially satisfied: a derived state is idempotent, cannot be re-raised,
  and survives restart by construction. Push-style delivery is protocol
  10's mailbox job (live coordination), deliberately outside this
  authority. WS2-WF-03.2's "one due review event" is then asserted as:
  exactly one due ROUND (per generation) visible to exactly the
  responsible endpoint, unchanged across restart — not an event row.
- **Option B — lazy write-side emission** (my earlier proposal). Rejected
  by review as write-dependent, and I agree: with no later write the
  durable act never exists.
- **Option C — a scheduler/timer component** that writes the event at T.
  Real notification, but a new always-on runtime with crash/recovery
  semantics, contradicting the crash-safe, process-per-act model. Needs
  its own design round if ever wanted.

Recommendation: **A**, with the summary-level `due` count making it
impossible to miss on any entry to the system, exactly like `parked`.

## Q2 — assignments versus `@` obligations

The finding says staged verification "creates separate exact `@`
verification obligations"; my disposition proposed a separate table, which
contradicts that letter.

- **Option A — an assignment IS a specialized obligation (RECOMMENDED).**
  One `obligations` table gains a `flavor` discriminator:
  `response` (classic `@`) and `verification`. Both flavors share
  identity, the exact-endpoint cardinality rule, the resolution-snapshot
  columns, the pending state, the actionable projection, and the
  named-route-handler gate. They differ in completion verbs and terminal
  states: `response` completes by `respond`/`dispose` exactly as today;
  `verification` completes by `report` (observation `passed|failed|unable`
  stored with the report, richer detail — round, candidate, evidence,
  append-only assessments — in side tables keyed by the obligation seq) or
  by `withdrawn`. Cross-verb use refuses ("this obligation is a
  verification assignment; it completes by report"). Obligation-backed
  `waiting` may name either flavor — it is literally "one exact pending
  `@` obligation", and a provider work waiting on its own verification
  assignment, waking when the report lands, is coherent and useful.
- **Option B — separate assignments table**, ruling text superseded.
  Cleaner state machines, but it forks "actionable because a route owes
  something" into two concepts and needs an explicit supersession of the
  finding's words.

Recommendation: **A**. It keeps one concept of "a route owes exactly one
answer", one actionable surface, one authorization gate — and the ruling's
text stays literally true.

## Q3 — provider outcome applicability and closed-target edges

Two ambiguities, one recommended rule pair:

- **Edges to closed Work: REFUSE (recommended).** A new `blocked_by`
  targeting terminally closed Work gates nothing and can never gate
  anything; under immutable closure the live relationship belongs to
  FOLLOW-UP Work, which is exactly what WS2-WF-06 models. Refusing (with
  the message pointing at follow-up creation) removes the retroactive
  "closed work without an outcome suddenly has a dependent" case entirely.
  This supersedes today's allow-and-gate-nothing behavior and its test
  (`test_blocking_on_an_already_closed_blocker_gates_nothing`), which
  predates outcomes. Old edges remain historical evidence, untouched.
- **Outcome applicability: required XOR refused (recommended).** At close
  commit, a Work is a provider iff it has at least one incoming dependency
  edge OR ever created a verification round. A provider close REQUIRES
  exactly `satisfying|non-satisfying`; a non-provider close REFUSES an
  outcome argument outright — permitting meaningless provider state was
  the flaw in my earlier mapping; the enum stays honest and the two cases
  partition cleanly. With edges-to-closed refused, provider-ness at commit
  is final: no later act can make an outcome-less closed Work into a
  provider.

## Q4 — the closed-Work restriction, stated precisely

"Only follow_up_of may reference closed Work" was sloppy. The precise
rule: terminally closed Work refuses every STATE MUTATION addressed to
it — phase, classification, pass/Current, new dependency edges in either
direction, discussion posts, `@`/`+` targeting it as the carrying Work,
round creation, assignment, report, assessment, withdrawal. What remains,
untouched: every read (detail, links, breadcrumb, discussion, events,
drill-through and follow-up traversal), all historical references inside
recorded state, and two per-member/exterior acts that never mutate the
closed record itself: `mark_seen` (the cursor lives in the viewer's
attention state, and reading closed history to completion is hygiene, not
mutation) and the creation of NEW Work carrying `follow_up_of` pointing at
it. If the reviewer prefers closed Work to also refuse `mark_seen`, the
cost is a permanently unclearable New counter on closed history — I
recommend keeping it allowed.

Awaiting rulings and the explicit group-1 release; no edits until then.

## Post-review correction (1bfb002b, acknowledged)

The reviewer rejected one corollary of my Q2 recommendation: a
verification-flavor obligation must NOT be nameable as a wake condition —
feedback can never transition provider Work, so a report landing must wake
nothing. Accepted: obligation-backed `waiting` names RESPONSE-flavor
obligations only, and the wake sweep ignores verification completions.
Derived-only due, closed-target edge refusal, and the closed-history
`mark_seen` hygiene are aligned. Close-outcome scope is with Slawomir.
