# Finding: a claim shows age but not whether its handler is still alive

## Observed

Claim Age answers how long a participant has owned Work. It cannot distinguish
healthy long-running implementation/review from a crashed, disconnected, or
abandoned claimant. Treating old claim age itself as failure would create
false alarms during legitimate long tests and careful reviews.

## Confirmed decision — 2026-08-16

**Confirmed by Slawomir during the fresh v11 trial.** Claimed Work has a
separate liveness heartbeat:

- claiming initializes its heartbeat time;
- the current claimant sends one heartbeat every two minutes;
- after three missed heartbeats—six minutes without a successful beat—the Work
  displays a restrained stall alert `!`;
- a successful heartbeat clears the alert immediately.

The alert is informational, not a lease expiry. Baton never automatically
releases the claim, changes Phase or Current, transfers Work, or permits a
second claimant merely because heartbeat is stale. A long tool call, suspended
process, scheduling delay, or temporary disconnect must not create duplicate
work. The existing claimant may heartbeat and continue; another participant
uses the ordinary explicit coordination/recovery path.

Only Work with an active claimant participates. Queued, waiting, parked,
terminal, and unclaimed review Work have no heartbeat alert. Claim Age remains
the total claim duration and does not reset on heartbeat. Heartbeat is not a
message, does not change Phase, and must not trigger the short Phase-change
blink.

The wide Work list renders the alert as a suffix to claim Age, for example
`12:04!`; a healthy value reserves the same cell as `12:04 `. Narrow layouts
may omit the whole Age/alert field. JSON exposes the persisted heartbeat fact
needed for non-TUI clients to reach the same conclusion; no client infers
liveness from messages, keystrokes, claim age, or repository activity.

Persist the current claim's heartbeat time in the authority and audit every
accepted heartbeat. The heartbeat operation is authorized only for the exact
current claimant and rechecks that identity in the committing transaction. It
must not masquerade as a semantic Work change or reorder/change-highlight the
Work row.

This requires a schema revision and is deferred from the current same-schema
trial batch.

## Same-schema journal ruling — 2026-08-16

**Confirmed by Slawomir; this supersedes the schema-revision requirement and
deferral immediately above.** The existing generic append-only event journal
is sufficient for the first implementation. `heartbeat work=Wn` records an
audited heartbeat event whose payload names the Work and exact claimant; the
claim event is that claim's initial heartbeat.

Projection resolves the latest qualifying claim/heartbeat for all active Work
in one batched authority read, never one query per row. It exposes
`heartbeat_at` through canonical JSON, and clients derive the six-minute stall
alert from that recorded fact. Restart/rebuild therefore retains liveness
history while observer-local memory is never mistaken for claimant evidence.

This is same-schema protocol/projection work. A projection-version increment
is allowed. If later event volume justifies a materialized heartbeat field or
index, that optimization belongs to a future fresh schema and must preserve
the event journal as audit evidence.

## Revalidation — 2026-08-16

The current tree confirms the same-schema boundary:

- `claim_work()` already records the exact claimant in the append-only claim
  event and rechecks every claim gate inside `BEGIN IMMEDIATE`;
- release, pass, waiting/parked entry and terminal close already clear the
  active claimant atomically;
- `_claimed_ats()` already performs one batched journal read for a projected
  Work window, while the TUI already derives Claim Age on its single
  configurable refresh cadence; and
- `_touch_work()` is the canonical semantic-change/reordering signal, so an
  accepted heartbeat must deliberately avoid it.

The heartbeat is an explicit claimant operation, not an automatic assertion
made merely because a TUI, bridge or shell remains connected. The public
surface is `heartbeat work=Wn` (with ordinary operation-id/replay semantics),
available through JSON and the shared TUI command grammar. Standing agent and
human operating guidance may request it every two minutes while executing or
reviewing claimed Work. A long command may therefore cause an informational
stall alert; it can never release or transfer the claim.

Projection must bind heartbeat history to the **current claim epoch**. For
each active Work, find its newest claim event, then the newest qualifying
heartbeat at or after that claim whose payload names the same exact claimant.
A heartbeat from an earlier claim by the same member must not make a later
re-claim look healthy. The claim timestamp remains `claimed_at`; the selected
claim/heartbeat timestamp becomes `heartbeat_at`. Perform this for the entire
window in one batched query/read and return null for unclaimed or terminal
Work.

`heartbeat` authorization is stricter than route membership: only the exact
recorded active `team.member` may commit it. The committing transaction
rechecks open status and the exact claimant. If release/pass/close wins the
race, heartbeat refuses without an event; if heartbeat wins first, its audit
event remains history and the later transition clears live heartbeat output
by clearing the claim. Exact retries replay one committed heartbeat.

Canonical JSON exposes `heartbeat_at`; the protocol-fixed six-minute boundary
and a local clock derive the display alert. Negative elapsed time after a
clock correction clamps to healthy zero. The existing five-cell Age field
becomes a six-cell reserved field (`12:04 ` healthy, `12:04!` stale, `-`
unclaimed); responsive layouts still omit it as one whole column. Heartbeat
does not reset `claimed_at`, change Phase/Current/Next/readiness, touch Work
change identity, reorder the row, create a message, alter New, or arm the
phase-change blink.

## Clarification — 2026-08-17: pickup alert is not heartbeat staleness

The later ruling in `../finding-tui-held-duration/FINDING.md` supersedes only
this record's statements that the visible duration is total claim duration and
that unclaimed operational Work has no alert. `Held` now starts at handoff and
continues through claim. Before claim, `>` and then `!` report pending/overdue
pickup; after claim, heartbeat staleness remains the independent liveness fact.
Neither condition mutates workflow authority or resets `Held`, and canonical
JSON exposes both as structured state rather than glyph-encoded strings.
