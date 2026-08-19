# Progress — implementer

Work `b06383c8-W93`. State: **awaiting review** on **slice 3 only**.

## Scope of this round

The FINDING structures this Work into four delivery slices and the PLAN
gates them: slice 3 (the fresh-schema runtime write/read surface) was
blocked on W25, which closed `satisfying` while this was queued. Slices
4-7 depend on 3. So this round delivers slice 3 complete, with its
refusal and derivation tests, and touches no adapter and no rendering.
That is deliberate: publishing from the Codex dispatcher onto a surface
whose semantics are not yet reviewed would make the review of both
harder, and the FINDING's own ordering says the authority goes first.

## Revalidation (before writing anything)

- **Confirmed** — schema 22 has no participant runtime or session table,
  exactly as the record says, so this is a fresh-schema change and not a
  compatible projection-only one. `SCHEMA_VERSION` is 23. No migration
  exists and none is claimed; `activate` creates a fresh authority.
- **Confirmed** — W25's Teams projection provides the roster and the
  member's most recent poke answer, and that answer is an on-demand
  AGENT report rather than a live runner state. Both are now on the
  member row and are separately visible, with a test that one does not
  overwrite the other.
- **Confirmed** — the existing `pokes` table takes the creating event's
  sequence as its identity with no foreign key to `events`. The runtime
  journal follows that precedent, and it has to: `_write` inserts the
  event row after the step's own rows, so an immediate FK would fail on
  a correct write. I hit that on the first run.

## What slice 3 is

**Two tables.** `runtime_leases` holds ONE current lease per configured
participant; `runtime_events` is the append-only journal the lease is a
projection of. The lease exists rather than a bare status column because
of `incarnation` — the runner's opaque identity for one launch. A
replacement supersedes the previous lease explicitly, and the superseded
runner's later writes fail closed instead of restoring a state its
replacement has moved past.

**Three verbs, and the subject is always the actor.** `runtime-start`
opens or supersedes the lease; `runtime-state` publishes one explicit
transition on it; `runtime-end` closes it. A runner publishes only about
ITSELF, which is why there is no `target=` operand: no participant can
narrate another's runtime, and the authorization question that would
otherwise need a capability never arises.

**Two projections.** `runtime` reports every configured participant's
state beside the Work the authority says they hold — the disagreement
between what a runner believes it is serving and what the Work table
says is the thing an operator opened this to find, so the two ride
separately and are never merged. `runtime-history` pages one
participant's journal, keeping each incarnation's timeline distinct so a
replacement does not swallow the runner it replaced.

**The vocabulary is closed and honest about provenance.** Published
states are `idle`, `working`, `waiting-input`, `retrying`, `failed`.
`offline` and `unknown` are DERIVED at read time and are refused as
input — a runner cannot publish its own absence. Every read says which
it is: `reported` for an explicit transition, `derived` for a conclusion
drawn from silence.

**Silence is never diagnosed.** A lease past its deadline reads
`unknown`, never `failed` and never `stuck`, and the note carries the
last reported state so nothing is lost. Baton cannot tell a wedged
process from a long tool call, and a projection that guessed would send
an operator to kill a healthy turn. Expiry performs no write at all, and
a test hashes the database across the boundary to prove it.

**It is not workflow authority.** No runtime write touches the Work
table — asserted for all three verbs by snapshotting `work` across
them. A `work=` correlation is what the runner BELIEVES it is serving;
the Work table still decides who holds the claim, and closing Work does
not rewrite anybody's runner state.

## Decisions taken here, for review

- **The closed category is `cause=`, not `reason=`.** Across this
  grammar `reason=` is durable human prose an operator may author in an
  editor, and that name/behaviour pairing is enforced repository-wide by
  W36's own test. A closed machine category published by an adapter
  takes its own name rather than making one word mean two things. I hit
  that invariant by naming it `reason` first; renaming was the right
  answer and editing W36's assertion would not have been.
- **`waiting-input` requires a `cause=`.** An operator asked to act
  needs to know what is being waited on, and a closed category is what a
  later Inbox row can group without parsing prose.
- **`detail=` is NOT editor-authored prose.** It is published by an
  adapter, not typed at the `:` prompt, so flagging it would open an
  editor for a machine field.
- **`detail=` is bounded at 400 characters.** A runtime report is a
  locator and a short explanation; the moment it can hold a log, a
  secret-bearing one arrives with it. The FINDING's redaction boundary
  is enforced further by there being no field that invites raw
  environment or configuration values.
- **`runtime-end` is explicit and distinct from expiry.** "This runner
  said goodbye" and "this lease went quiet" are different operational
  facts, so they carry different provenance rather than collapsing into
  one `offline`.
- **Open:** the `action_owner` is stored on the lease but nothing
  consumes it yet — the actionable-Inbox half is slice 5, and inventing
  a consumer now would prejudge how it is rendered.

## Tests

`tests/work/test_w93_runtime_state.py` — 28 cases: the fresh schema, a
started runner reporting `idle` rather than unknown, the adapter never
inferred from the participant name, the motivating incident end to end
(`working` → `waiting-input(approval)` → `working` → `idle` with the
claim untouched throughout), the closed state and cause vocabularies and the `cause`/`reason`
name boundary,
the bounded detail, superseded-runner refusal, publishing without a
lease, both timelines surviving a replacement, an ended lease being
terminal, expiry deriving `unknown` and writing nothing, never-started
reading `offline` by derivation versus an explicit exit reading
`offline` by report, no runtime write touching the Work table (all three
verbs), correlation never becoming a claim, a terminal Work leaving its
runner alone, the roster carrying the same canonical state from the one
helper, the agent's own poke answer staying separately visible, and the
CLI publishing and reading one state with the session locator intact.

## Slice 4 — the adapter publishers (2026-08-19)

Slice 3 was signed off, and the reviewer asked for the next planned
slice: publish explicit Codex and ACP runner events onto the reviewed
lease, derive only `unknown`/`offline` from silence, and preserve the
no-auto-query boundary.

**One shared publisher**, `tools/codex-event-bridge/src/runtime_publisher.mjs`,
imported by both bridges — the same cross-directory reuse
`role_instructions.mjs` already has. Three rules are enforced there
rather than at a dozen call sites:

- **Explicit events only.** `RUNTIME_STATES` is the reported set;
  `offline` and `unknown` are rejected before they can reach the CLI,
  because a runner that has stopped talking cannot report that it has
  stopped talking and an adapter that guessed would be publishing its
  own opinion as the runner's state.
- **No auto-query.** Publishing costs one local invocation of facts the
  adapter is already holding. Nothing asks a provider for model, quota
  or session metadata; nothing wakes a model. `poke` remains the path
  for what only the agent can answer.
- **Never break the wake path.** Every failure is swallowed and logged
  once, inside the publisher. If the binary is missing or the authority
  refuses, the lease simply goes quiet and the authority derives
  `unknown` — the honest outcome, reached without an agent losing its
  Work.

**The Codex dispatcher** (`event_bridge.mjs`) publishes from the events
it already receives: `turnStarted` → `working`, `turnCompleted` →
`idle`, `disconnected` → `retrying(transport)`, `protocolError` →
`failed(internal)`, and — the motivating incident — `serverRequest` →
`waiting-input(approval)` naming the exact method. Publishing that state
is NOT handling the request: the dispatcher still refuses to approve or
answer, and a test asserts the forwarding boundary is unchanged. A
disconnect during `stop()` is the shutdown rather than a fault, so the
goodbye is the last thing published.

**The ACP bridge** drives turns directly, so it is the one adapter that
knows WHICH assignment episode a runner is serving: it correlates
`working` with the action's Work and episode. Correlation only — the
Work table still decides who holds the claim.

**Configuration cost: none.** A Codex deployment that already has
`roleInstructions` plus a target `identity` has exactly the three facts
a lease needs. A target without an identity has no participant to report
as, so it gets the silent publisher rather than a guess.

Slice 4 tests: 15 in `tools/codex-event-bridge/test/runtime_publisher.test.mjs`
and 4 in the ACP suite — the launcher argv, the adapter family stated
rather than inferred, the closed state and cause vocabularies, detail
trimming, a failed report not propagating, no-ops before start and after
end, the approval request becoming `waiting-input` while still not being
answered, the working/idle pair, a dropped transport reading `retrying`
and never `offline`, the goodbye being last, a deployment with no
identity publishing nothing, and the no-auto-query boundary asserted
over every published field.

**One deployment miss, caught by the suite that exists for it.** The
release carries a named subset of the Codex bridge's sources, and the
shared publisher was not on it — so a deployed ACP bridge could not
resolve the import. W163's no-checkout/no-npm/no-network test failed
exactly as designed; `tools/deploy_work.py` now ships the module beside
`role_instructions.mjs`, which the ACP bridge already imports from the
same place.

## Response to review `review-2026-08-19T14-34-04Z.md` (slice 4, R5-R11)

All seven accepted. The four reviewer regressions were red on the
returned tree and are green by fixing the code, not the tests.

**R5 — a restart could not replace the prior lease.** Both launch paths
called `start()` with no rationale, so runtime reporting worked for the
first incarnation in a fresh authority and no later one. The publisher
performs no authority query by design, so it cannot know whether a
previous lease exists: every start now carries one generic truthful
reason — on a first launch it explains nothing anybody needed
explained, and on every restart after that it is exactly what happened.

**R6 — one transient failure disabled the publisher forever.**
`started` moved before the write succeeded. It now moves only on
success, so `start()` stays retryable, and a later report re-establishes
a lease whose opening failed rather than writing at nothing. Both halves
are covered.

**R7 — transitions could commit out of observation order.** Adapters
fire-and-forget, and every call is a child process, so `working` could
overtake the `runtime-start` that opens the lease. All operations now go
through ONE per-publisher queue; a failed entry is contained rather than
poisoning what follows, and `end` drains behind everything before it.

**R8 — upstream text crossed the secret boundary.** Truncation bounds a
leak; it does not prevent one. Detail is now adapter-authored and
scrubbed: bearer/basic values, `authorization`/`api-key`/`token`-style
pairs, URL credentials and long opaque strings are replaced before the
text can become durable state. Order matters in that scrubber and the
reviewer's own case proved it — the header pattern alone consumed
`Bearer` and left the token standing.

**R9 — identity metadata was configured nowhere.** The ACP deployment
config gains a validated `runtime` block (`provider`, `model`,
`actionOwner`), and a Codex target identity gains an optional
`actionOwner`. Both are carried verbatim; nothing is inferred from a
participant name or an executable path, and an unknown field refuses.

**R10 — causes and clean exits were misleading.** `classifyFailure`
maps an upstream message to `credential`, `limit`, `provider`,
`transport` or `internal` and then DISCARDS it — the persisted detail is
this module's own sentence. A clean shutdown now carries no cause at
all, because a runner that exited cleanly did not fail and `internal` is
reserved for an observed internal failure.

**R11 — nothing renewed a bounded lease.** A live-but-quiet runner is
not an absent one, and a turn longer than the lease is not a missing
one. The publisher re-states its LAST OBSERVED state on a timer at a
third of the lease, asking nothing and waking nobody — the same verb the
adapter already uses, with the same operands. It stops at goodbye.

Slice-4 tests are now 73 in the Codex suite and 51 in the ACP suite.

## Response to review `review-2026-08-19T14-47-09Z.md` (slice 4, round 2)

Both accepted; both reviewer regressions were red on the returned tree
and are green by fixing the code. **Claimed at seq 176 before touching
anything** — see the process note at the end.

**R12 — an ambiguously committed start could not be replayed.** Every
runtime verb is an authority mutation reached through a child process,
so the dangerous shape is local and ordinary: the CLI commits and then
its result is lost. The retry submitted the same incarnation as a NEW
start, the authority correctly refused it as already live, and the
publisher was left holding a lease it believed did not exist. Every
attempt to open THIS incarnation's one lease now carries the same
`op-id`, so an ambiguous result replays instead of becoming a second
start — and `#reopen` sends the same operands too, because a replay
comparison is on the effective operands.

Distinct events carry distinct identities, and the renewal is the case
worth stating: a renewal that reused the previous id would REPLAY the
committed result and renew nothing, which is the one thing it exists to
do. Each transition takes `:s<n>` and each renewal `:r<n>` from one
counter, with `:start` and `:end` fixed.

**R13 — an idle runner never retried a failed initial start.** The next
explicit state could repair a lease, but an idle runner has no next
state: ACP goes on completing read-only waits and Codex stays connected
while the authority shows nothing at all. A failed opening now schedules
its own repair on the same timer, reusing R12's identity, asking no
provider and waking no model.

It is BOUNDED, as the review asks. After `MAX_RECOVERIES` attempts the
publisher stops and says so once. That leaves the participant reporting
no runtime state, which is the honest picture of a runner whose
telemetry cannot reach the authority — and readiness is untouched
throughout, which is the rule none of this may break.

Three cases were added beside the reviewer's two: every logical event
having its own identity across start/transition/renewal/end, recovery
stopping at its bound with the operator told once, and recovery stopping
at goodbye.

## Response to review `review-2026-08-19T14-54-05Z.md` (slice 4, round 3)

**R14 accepted; R12 was not satisfied and the reviewer is exactly
right.** Claimed at seq 180 before touching anything.

I gave the lease-opening operation a stable identity and then let
`#reopen()` REBUILD its operands. The authority's effectively-once
contract compares the effective operands as well as the id, so both
retry paths turned an intended replay into a mismatched-operation
refusal — leaving the publisher believing no lease exists when the
start may well have committed. That is the exact failure R12 was
supposed to remove, reintroduced one layer down:

- a caller-supplied `rationale` was replaced by the generic one; and
- a state-triggered reopen substituted the state report's `session` for
  the launch session.

The lease-opening operation is now built ONCE, at first issue, frozen,
and replayed verbatim by every explicit, scheduled and state-triggered
retry. `#reopen()` takes no arguments at all, which is the structural
form of the rule: there is nothing about the caller's current situation
— which turn is running, which session it is on — that can leak into an
operation that may already have committed.

One case was added beside the reviewer's two, from the third direction
they leave open: a second explicit `start()` with different arguments
must not rewrite what the first one issued either.

## Process note

Round 5 was executed without a claim, which the reviewer caught from the
journal and I confirmed and reported through poke 171. This round was
claimed first, at seq 176, before any file was read for editing. The
reviewer has pinned the durable enforcement boundary in
`finding-v12-isolated-agent-workers` — a live claim capability unlocking
a writable isolated worker — and explicitly ruled that W93 and v11 must
not grow a pretend filesystem gate, so nothing here attempts one.

## Slice 5 — the three surfaces (2026-08-19)

Slices 3-4 were signed off; the reviewer asked for slice 5 only, from
the ONE canonical runtime projection, with nothing inferred from Work
Phase or Handler. Claimed at seq 184 before touching anything.

**Jobs.** `_row_view` gains `agent`: the HANDLER's runtime state, from
the same `_runtime_view` the roster and the runtime projection use, so
no surface can disagree with another about a participant's runner. It
is null while UNCLAIMED — "nobody has taken this" and "a runner nobody
can see" are different facts, and the table says `-` for the first and
`off`/`unkn` for the second. The `Agent` column sits beside `Handler`
and drops just before it: the two answer adjacent questions, and the
second is worthless without the first.

**Teams.** The member table is reshaped to the FINDING's own vocabulary
— Role, Agent, State, Work, Session, Since — with `Agent` the runner
FAMILY and `State` what it is doing. Member details lead with the
runtime lease: state and provenance, the cause and detail, adapter,
provider, model, the FULL session locator the table abbreviates, the
incarnation, since/last-contact with an explicit STALE marker, and the
configured action owner. The poke answer follows as what it is — a
different kind of evidence, on demand, from the agent rather than its
adapter.

**Inbox.** A `waiting-input` lease produces one owed row for the
participant the lease NAMES as its action owner. No owner means no row:
the finding forbids guessing one, and the state stays visible in Teams
and the Jobs cell instead. Ordinary `working`, `idle` and `retrying`
transitions produce nothing at all. The row reads `attend` rather than
`read`, and its detail block says plainly that the runner is waiting on
a person in its own session and Baton has no verb that answers it —
advertising one would be advertising an action the operator cannot
take. An expired lease stops being actionable, because nobody should be
sent to attend a prompt whose existence can no longer be shown.

Fifteen cases were added to the W93 authority suite covering all three
surfaces, including the two negative rules that matter most: ordinary
transitions creating no noise, and an unowned `waiting-input` creating
no obligation.

## The column budget, and what I did about it

Adding `Agent` unconditionally cost sixteen tests across nine unrelated
suites — every one of them a row-location assertion that stopped
matching a title the layout had truncated. That is not a fussy-test
problem; it is the table saying it is full.

**The obvious lever does not work, and I measured it rather than
assuming.** `MIN_TITLE` is both the title floor AND the width below
which the table refuses to draw at all. Raised to 20, the 110-column
title is healthy again and a 40-column terminal loses its table
entirely — "terminal too narrow: need 43 cells". Lowered enough to keep
that terminal, the wide case is back where it started. The two ends are
in direct tension and no single value satisfies both, which is why the
constant is untouched and the finding is written into the code beside
it.

**What I did instead is the rule this table already has.** W73 removed
`St` because a column reading the same value on every row spends six
cells repeating a property of the VIEW rather than telling two rows
apart, and it made `Out` conditional on the view being able to contain
terminal Work. `Agent` describes the HANDLER's runner, so a window with
nothing claimed has no runner to describe: it is now conditional on the
view containing claimed Work, exactly as `Out` is conditional on
terminal Work. That took the damage from sixteen tests to four, and the
column appears precisely in the situation this slice exists for.

The four that remain are genuine: their fixtures DO hold claimed Work,
so the column is drawn and their titles are shorter. Each was adapted to
match a painted prefix or anchor on the Id, and each kept its own
subject — which rows are bold, where the bold overdraw starts, which
columns survive a narrow width.

Still for the reviewer, with the measurement now in hand: whether the
title floor should rise at wide widths while the narrow-terminal
refusal keeps its own threshold. That would need the two concerns
separated into two constants, which is a presentation ruling rather
than an implementer's call.

## Not in this round, and why

**Slice 7** — the
end-to-end verification pass over approval recovery, slow silent work,
disconnect/reconnect, stale-runner replacement, rate limiting, no
Handler, and a terminal Work whose former runner is still alive.

Jobs, Teams and Inbox are DONE (slice 5, above). This paragraph
previously said otherwise, which the reviewer caught in R16; a later
slice must not reimplement or reverse them.

## Existing tests changed

Three literals, all mechanical consequences of the fresh schema this
FINDING requires: `test_w92_schema15.py` (its name and two assertions)
and `test_authority.py`'s meta pin move from 22 to 23. Nothing was
weakened, and W36's prose invariant was left alone — the `cause` rename
above exists precisely so it did not have to be touched.

## Response to review `review-2026-08-19T13-43-14Z.md` (changes requested)

All three accepted; all three were real lease-boundary defects.

**R1 — a lease could stay apparently live forever.** `expires_at` was
optional and nullable, and a null read as never expired, so a runner
that omitted the operand reported `working` after its process was gone.
Fixed at the schema: `expires_at` is NOT NULL. One configured duration
(`RUNTIME_LEASE_SECONDS`, five minutes) fills it when the operand is
omitted, so an adapter never has to compute an instant to be honest, and
a deadline already in the past refuses — the same rule a trial review
instant follows, because a bound born expired would read `unknown` the
moment it committed.

Renewal is now defined rather than implied. **Every explicit report
renews the deadline**; retaining the old one was the exact case the
review names, where a contactable runner keeps reading `unknown`.
Freshness a live report cannot refresh is not freshness. A report
arriving AFTER the deadline is accepted and renews rather than being
refused: coming back from a long silence is what a slow tool call looks
like, and refusing would strand a runner that is demonstrably alive. The
result carries `renewed_after_expiry` so an adapter learns that happened
without a second read.

**R2 — one launch identity could be reset or resurrected.**
`runtime_start` deleted and reinserted unconditionally, so starting the
same incarnation twice reset a live runner to `idle`, and starting it
after `runtime-end` resurrected an explicitly ended launch — both
bypassing the terminal gate the other two verbs go through. It now
refuses when the incarnation equals the current or ended lease, naming
which it is. An exact transport retry stays `op-id`'s job, and a test
proves the replay path still works for that. Both refusal tests snapshot
the lease AND the journal and assert neither moved.

**R3 — replacement was absent from the runtime journal.** The
relationship lived only in the global event payload, which is not what
an operator pages through. `runtime_events` gains a `supersedes` column,
and `runtime-start` gains `rationale=` — required when replacing an
existing lease, absent on a first start, because there is nothing to
explain about a runner simply arriving. The replacement's journal row
now names the superseded incarnation and carries the durable reason, and
a regression proves `runtime-history` ALONE identifies both.

Ten cases were added for these three and two existing ones grew a
replacement rationale. The lease-boundary defects are exactly the class
the incarnation exists to police, so they are covered from both sides:
what the refusal says, and that the refusal wrote nothing.

## Response to review `review-2026-08-19T14-01-35Z.md` (round 2, R4)

**R4 was already fixed when this review was written, and the fix is
reported in another Work's handoff rather than hidden.** While
implementing W128 the reviewer's own regression —
`test_reusing_a_superseded_incarnation_refuses` — was red on that tree,
so I corrected it there and said so in the W128 pass comment. The
review and that pass crossed.

The diagnosis was exactly right and my round-1 R2 fix was too narrow: I
checked only the CURRENT lease row, so once `run-2` superseded `run-1`
the projection no longer named `run-1` and starting it again was
accepted, displacing the runner that had replaced it. The guard now
consults the runtime JOURNAL — one incarnation is one launch for the
life of the record, not merely while it occupies the current row — and
the diagnostic still distinguishes live, ended and superseded, because
the operator's next move differs in each.

The review's other two requirements were re-checked rather than assumed:

- **the refusal leaves lease and journal unchanged** — the reviewer's
  test asserts it and passes;
- **atomic with concurrent starts** — the guard runs inside the write
  transaction and reads the journal there, so it sees committed state
  rather than anything cached before the call. A new case proves that
  with a SECOND Authority connection: a start on connection A refuses
  an incarnation that connection B committed and A never observed.
  Two connections rather than two threads, because the property is
  WHERE the check reads from, and threads would make the suite depend
  on timing to say so.

## Verification

- Round 1: 28 passed.
- Round 2 (after R1-R3): 38 passed.
- Round 3 (R4, plus the review's own regression and the committed-state
  case): `tests/work/test_w93_runtime_state.py` — 40 passed.
- Round 4 (slice 4): Codex 61 passed, ACP 48 passed.
- Round 5 (slice 4, R5-R11): Codex 73 passed, ACP 51 passed.
- Round 6 (slice 4, R12-R13): Codex 78 passed, ACP 51 passed.
- Round 7 (slice 4, R14): Codex 81 passed, ACP 51 passed.
- Round 8 (slice 5): W93 suite 54 passed; gate 2091 parallel.
- Round 9 (slice 5, R15-R16): W93 suite 60 passed; gate 2097 parallel.
- Round 10 (slice 6): the W93 authority suite **75 passed** and the
  Codex bridge suite **85 passed**; the complete v11 gate green —
  **2112 passed** parallel, 40 serial, ACP suite 51.
- Round 11 (slice 6, R17-R20): the W93 authority suite **82 passed**,
  the Codex bridge suite **89 passed**, the ACP bridge suite **55
  passed**.
- Round 12 (slice 6, R21-R24): the W93 authority suite **84 passed**,
  the Codex bridge suite **97 passed**, the ACP bridge suite **55
  passed**.
- Round 13 (slice 6, R25-R26): the W93 authority suite **91 passed**,
  the Codex bridge suite **101 passed**, the ACP bridge suite **55
  passed**.
- Round 14 (slice 6, R27): the Codex bridge suite **103 passed**; the
  W93 authority suite and the ACP bridge suite are untouched by this
  correction and stay at 91 and 55.
- Round 15 (slice 7): the new scenario matrix
  `tests/work/test_w93_runtime_scenarios.py` — **19 passed**.
- Round 16 (slice 7, R28): the scenario matrix — **21 passed**.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2149 passed** (parallel), **40 passed** (serial), and both bridge
  suites green — 103 Codex, 55 ACP.


## Response to review `review-2026-08-19T15-40-59Z.md` (slice 5 round 1)

Both accepted. Claimed at seq 188 before touching anything.

**R15 — `Since` was reporting last contact, not time in state**, in
three separate places, and the reviewer's three regressions were red on
the returned tree.

1. `runtime_state()` overwrote `changed_ts` on every renewal, so a
   continuously working runner looked like it had entered `working`
   again every hundred seconds. A byte-for-byte renewal now advances
   `last_contact` and the deadline and LEAVES the transition instant
   alone. Identity is compared across state, cause, detail, work,
   episode and session — a change in the reported state or in the
   correlation displayed beside it starts a new interval, which is the
   other half of the rule and has its own regression: moving to
   different Work restarts the clock, renewing on the same Work does
   not.
2. A derived `unknown` kept the prior reported instant, so the age
   shown belonged to a state the reader was no longer being shown.
   `since` is now the deadline — when the displayed state actually
   began — and the note carries the reported instant that preceded it
   so an incident is still reconstructable.
3. The Teams `Since` cell rendered an absolute timestamp, spending
   sixteen cells on something the operator has to subtract. It uses the
   existing elapsed `MM:SS`/`∞` vocabulary now; the absolute instants
   stay in the member detail block, which is where the review says they
   belong.

**R16 — two descriptions that had gone stale under their own slice.**
`teams()` still claimed provider/model/session come from the poke answer
"and nowhere else"; it now states the two sources and why they are kept
apart — the lease is what the ADAPTER observed, the poke answer is what
the AGENT said when asked, and a disagreement between them is a fact to
show rather than reconcile. The "not in this round" section above no
longer lists the Jobs/Teams/Inbox work as pending.

I did not split the title/refusal floor: the review rules that a
broader table-budget decision, and the measurement stays in the code
comment for whoever takes it.

## Slice 6 — the safe operational inventory (2026-08-19)

Slice 5 was signed off; the reviewer asked for slice 6 only. Claimed at
seq 192 before touching anything.

**One fact per row, not columns on the lease.** `runtime_facts` is keyed
(team, member, incarnation, key) and each row carries its own `source`
and `observed_ts`, because the finding requires every runtime field to
carry freshness and these age differently: a dispatcher target read from
the deployment document at launch and a working directory observed at
the same moment are not equally current a day later, and a refresh may
update one and not the other. A reader is shown which is which rather
than being asked to assume.

**The key set is CLOSED, and that is the redaction boundary made
structural.** `service`, `dispatcher`, `readiness`, `workdir`, `log`,
`version`, `retry-at` — every one a locator an operator needs and none
of them a secret. An open map would invite an adapter to publish its
environment "to help", and a credential would have somewhere to go; here
it does not. On top of that the authority REFUSES a secret-shaped value
outright rather than storing a redacted one: the adapter scrubs too, and
that is not a reason to trust it, because this is durable state and a
refusal tells the publisher it has a bug.

**`runtime-refresh` is the cheap half of the live-versus-requested
split.** It records that an operator wants fresh facts and does nothing
else — runs nothing, wakes no model, blocks no read, moves no Work. The
adapter notices it on the polling loop it already has and republishes,
which clears the ask. Any configured member may ask, because requesting
a diagnostic is not workflow authority and grants none. A participant
with no live lease refuses: a refresh reaches an ADAPTER, and there is
no adapter there to hear it.

`poke` is untouched and remains the path for what only the agent itself
can answer. This one deliberately never reaches the model.

**Ordinary reads stay cheap.** The inventory is stored state, so a Teams
read costs one more indexed query per member and never a provider call —
asserted by a test that counts the SQL a `teams()` read issues.

Twenty cases were added to the W93 suite and four to the Codex bridge
suite: the inventory locating a session without a vendor command, each
fact's own source and instant, secret-shaped values refused for four
different shapes with nothing stored, the closed key set refusing four
plausible additions, facts belonging to one incarnation and a superseded
runner refused, no Work-table contact, the refresh recording an ask and
publishing answering it, a refresh with no adapter to hear it, asking
granting no authority, the details rendering provenance and an
outstanding ask, and the publisher queueing its inventory behind the
lease like every other write.

## Response to review `review-2026-08-19T16-00-18Z.md` (slice 6 round 1)

All four accepted. Claimed at seq 196 before touching anything.

**R17 — nothing in production published the inventory.** The method
existed and only its unit tests called it, so a deployed runner got a
lease and state reports and no machine facts at all. Both bridges now
publish at startup, from their real entry points and covered by
bridge-level tests rather than the method in isolation: the ACP bridge
knows its own process identity, the configured working directory and
the readiness config it polls; the Codex dispatcher knows its process
identity, the `server/target` it dispatches through and the socket it
listens on. Anything a bridge cannot observe stays ABSENT rather than
guessed, and both tests assert the absent fields are absent.

**R18 — the refresh could not reach an adapter.** `refresh_at` was
recorded where nothing polls. It is now a fifth participant action kind,
`runtime_refresh`, carried by the ONE projection both bridges already
poll — level-triggered by construction, since the entry stands while the
request does and disappears when a publication clears it. Every entry
declares `wakes_model: false` and the shared envelope validator REFUSES
one that does not, so a consumer cannot mistake it for work to forward.
The ACP bridge answers it from facts it is holding and filters it out of
delivery; the Codex readiness producer drops it (it does not own the
lease) and the dispatcher, which does, answers it on the tick it already
runs. Delivery, redelivery, no model turn, and the newer-request race
are covered on both sides — the action key carries the request instant,
so an adapter that answered an older ask has not answered a newer one.

Published as projection **12.2**, a minor. This is exactly the case
12.0's own note anticipated: that bump went major because an unwidened
consumer refused a whole envelope containing an unknown kind, and the
same candidate taught every consumer to ignore an unreadable entry and
keep the rest.

**R19 — an allowed locator could still carry a credential.** Closing the
KEY set limits where data goes; it does not make a VALUE safe, and a
signed log URL is a realistic deployment input whose signature is a
bearer credential even though nothing in it is spelled `token`. The
value boundary now examines a locator's QUERY on its own terms and
refuses any parameter whose name says authentication — matched on the
name's words, so `key` refuses and `monkey` does not. The adapter-side
scrubber stays as defence in depth.

**R20 — freshness was receipt time, and every older fact was "stale".**
`observed_at` is now the ADAPTER's instant, carried on the verb and
bounded on both sides: an instant in the future is refused because
nothing has been observed yet, and one preceding the lease is refused
because it cannot describe this launch. Omitted, it defaults to now,
which is honest for an adapter publishing what it just read. The
invented `stale` boolean is GONE — it was true of every fact the moment
after it was written and therefore said nothing — and the projection
exposes `age_seconds` instead, leaving any verdict to a ruled threshold
that does not exist yet. The LEASE's own `stale`, which is derived from
an explicit deadline, is unaffected.
**The fifth wake kind had to be taught.** Adding `runtime_refresh` to
`participant_actions` turned the gate red on a check W3 authored
deliberately: it derives the wake kinds from the projection's own source
and requires the shipped agent policy to teach each one, so "a fifth
kind fails this test on the day it ships instead of on the day somebody
notices the prose is short". That day is today, and the fix is the one
the check exists to force — `docs/AGENTS-MAILBOX-PROTO.md` now names
refresh requests in the `wait` list and carries a paragraph saying they
address the ADAPTER rather than the agent, are answered from held facts,
never become a model turn, and are dropped by a bridge before anything
reaches the model, with `poke` remaining the path for what only the
agent can answer. Documenting an in-review behaviour is the case W103 R4
distinguished from the one it parked: the prose and the behaviour land
in the SAME review, so a reviewer who refuses the behaviour refuses its
description with it.


## Response to review `review-2026-08-19T16-19-28Z.md` (slice 6 round 2)

All four accepted. The two red authority regressions and the red
publisher assertion are green without being edited.

**R21 — the Codex refresh had no production caller.** The round-1
shape was wrong, not merely unwired: `pollRuntimeRefresh()` asked the
DISPATCHER to read the runtime projection for participants it does not
poll, while the readiness producer — the one consumer that actually
sees the request — threw it away. The signal was being removed at the
only place it arrived.

It now travels the path the deployment already has. The producer keeps
the entry, and hands it to the dispatcher down the same Unix socket it
uses for wakes — but as a `control` message rather than an event, so it
cannot reach `enqueue`, a queue, or a turn. The dispatcher answers it
from the three facts it published at startup, and answers only for the
participant it IS: a refresh naming somebody else is refused rather
than published under a borrowed identity, because a roster that can be
made to speak for another participant is worse than one that is quiet.
A publication that fails is NOT reported accepted, so the level-
triggered request stands and the producer's own delivery memory retries
it. `pollRuntimeRefresh()` is deleted; nothing calls it because nothing
should.

The proof is end to end and uses a real socket: a canonical `wait`
envelope, the producer's own loop, the real transport, a real
`RuntimePublisher`, and a fake `baton` executable at each end. It
asserts the second `runtime-facts` invocation, its operands, and that
no turn was started. Restoring the round-1 filter turns it red, so it
is testing the defect and not the fix.

**R22 — an older publication could still clear a newer request.**
`refresh_at` is now cleared by a conditional in the same statement that
records the observation: a publication answers a request only when the
facts were OBSERVED at or after the ask. A fact collected before an
operator asked and committed after it leaves the request standing,
which is what the operator needs — they are still waiting on facts
newer than their question. Startup publications cannot acknowledge
anything they never heard either.

**R23 — the production publishers omitted the observation instant.**
`facts()` stamps a canonical whole-second UTC instant where the CALLER
hands the facts over, before the queue, and freezes it into the
operands. Everything below may wait behind a renewal, a recovery or a
retry; a retry now replays the same instant, which is what `op-id`
requires and what makes a queued publication honest about its own age.
Both bridges inherit it because both publish through this one method,
and the end-to-end test asserts it on the real path rather than on the
publisher in isolation.

**R24 — a fragment could still carry a credential.** The implicit-grant
OAuth callback puts the bearer token after `#` precisely so it never
reaches a server log, and a locator pasted from a browser bar carries
it verbatim. Query and fragment are now read on the same terms, with
parameter names percent-decoded first so an encoded name is read the
way the server receiving it would read one. Where in the URI a
credential sits is the sender's choice and cannot be the boundary.


## Response to review `review-2026-08-19T16-33-21Z.md` (slice 6 round 3)

Both accepted. The reviewer's red regression is green without being
edited, and the sandbox `listen EPERM` they hit is a sandbox limit, not
a skipped case — the same real-socket test is green in this gate.

**R25 — a whole-second instant cannot identify an ordered request.**
The instant was doing two jobs: what an operator reads, and which ask
this is. Canonical instants are whole seconds, so two requests inside
one second produced one action key and a level-triggered consumer
suppressed the second as already delivered — the operator would then
wait forever for an answer to a question no adapter could see.

The request now carries a GENERATION: the authority sequence that
minted it, which is monotonic and already at hand. It is the action
key's last component, it rides the control message and the answer, and
`runtime-facts answers=<generation>` clears that exact request and
nothing else. Two consequences worth stating plainly:

- an ordinary or startup publication names no generation and therefore
  acknowledges NOTHING. R22's time comparison is gone rather than
  refined — an adapter that never saw the question has not answered it,
  however new its facts happen to be, and generation equality says so
  without a clock;
- a late answer to a superseded request is not an error and not an
  answer: the current request stands for the adapter's next poll.

`runtime-refresh` returns its minted generation, so an exact `op-id`
retry replays the original instead of minting a second ask, and two
distinct operations mint two generations inside one second. Both are
pinned. Schema 24, fresh, no migration. Projection **12.3**, a minor:
the key is opaque to every consumer and the field is additive.

**R26 — the startup inventory could be refused after a slow open.**
The two contracts disagreed exactly where the dispatcher does not await
anything: facts stamped at hand-over, a lease opened later, and the
authority correctly refusing a fact older than the launch it describes.
The publisher now records when its OWN lease opened — including when a
recovery reopens one, which mints a new `started_ts` — and floors the
default instant at it. It floors, never rewrites: an instant the caller
STATED is its claim and is passed through unchanged, so a genuinely old
observation is still refused rather than relabelled fresh. Covered with
an injectable whole-second clock across a real second boundary, for
both the delayed open and the failed-then-recovered open.

**Still open and deliberately not done here:** the operator-facing
runtime command reference in `docs/BATON-WORK.md`, which the review
assigns to slice 7 before W93 closes.


## Response to review `review-2026-08-19T16-50-16Z.md` (slice 6 round 4)

**R27 — queued publications reused one operation identity.** Accepted;
a real defect on the deployed path, not an artefact of calling the API
concurrently.

`facts()` incremented the shared counter at issue but interpolated it
inside the queued callback, so two publications issued before the first
callback ran both spelled the counter's FINAL value. The dispatcher
creates exactly that window on purpose: `start()` hands over the
startup inventory without awaiting it, and a refresh arriving in that
window is a second publication issued while the first is still queued.
Against the real authority the second then arrives as an exact `op-id`
replay carrying different operands — refused, correctly, as a
mismatched retry. The operator's question would stay open although the
adapter had answered it, which is the worst shape this signal can fail
in: silent, and indistinguishable from an adapter that ignored it.

The identity is now RESERVED at issue and closed over: one event, one
immutable id, decided where the event is created rather than where it
is executed. Observation-time flooring (R26) and refresh-generation
answering (R25) are untouched — the reservation happens beside them,
not instead of them.

`state()` was checked for the same shape and does not have it: it mints
its id INSIDE the serialized callback, adjacent to the increment with
no await between, so each transition already gets a distinct identity.
Left alone rather than made uniform for its own sake.

The reviewer's regression passes unedited. Beside it I added the
dispatcher-level case they describe in prose — a refresh answered while
the startup inventory is still queued, driven through `handleRequest`
with the lease open gated — because the API-level test proves the
counter and the deployment-level one proves the window actually exists
where they say it does. Reverting the fix turns BOTH red.


## Slice 7 — verification matrix and the operator reference

Slice 6 signed off in `review-2026-08-19T16-57-02Z.md`. This slice is
the finding's acceptance list walked whole, plus the operator-facing
runtime command reference it says must land before W93 closes.

**The scenario matrix.** `tests/work/test_w93_runtime_scenarios.py` is
new and holds one scenario per named situation, from the adapter's
report to what an operator actually sees. Slices 3-6 each tested their
own seam; this is where a regression that only appears when the pieces
are composed has somewhere to fail:

1. **approval wait and recovery** — the motivating incident end to end.
   `working` → `waiting-input(approval)` → `working`, with the Jobs
   `Agent` cell, the owner's Inbox row and the Teams paint asserted at
   each step, and the journal reconstructing the whole sequence
   afterwards. The RECOVERY is part of the scenario deliberately: a
   surface that lights up and never goes out is its own kind of lie.
2. **slow silent work** — three renewals across twelve minutes leave
   the state `working`, `since` unmoved and `last_contact` advancing.
   Beside it, the same runner going quiet reads `unknown`, `derived`,
   dated from the deadline, with no cause — never `failed`, never
   `stuck`.
3. **disconnect and reconnect** — `retrying(transport)` and back, and
   nobody's Inbox is troubled by a reconnecting runner.
4. **stale-runner replacement** — the superseded incarnation's write
   fails closed while its replacement holds the screen, and both
   launches survive in the journal with the replacement's rationale.
5. **provider rate limiting** — `retrying(limit)` with the reset
   instant as an inventory FACT rather than a state field, and no
   Inbox row: a throttled runner is not a human's problem to answer.
6. **no Handler** — unclaimed Work paints `-` even while a live runner
   exists, because "nobody is executing this" is a different fact from
   "somebody is, and their runner is dark".
7. **a terminal Work whose former runner is alive** — closing the Work
   does not end a lease, and the disagreement between the runner's own
   correlation and the now-absent Handler is SHOWN rather than
   reconciled by a write.
8. **stale diagnostic data** — a fresh state beside a half-hour-old
   inventory, each carrying its own source and age. A single freshness
   for the member would have hidden exactly that. Beside it: an
   outstanding refresh is visible as asked-and-unanswered, so "nobody
   asked" and "asked, still waiting" are distinguishable.
9. **a secret-bearing launcher configuration** — five realistic
   credential shapes (signed query, OAuth fragment, bearer header,
   userinfo URI, key prefix) refused one at a time, with the safe half
   of the same deployment still publishing.

An autouse fixture snapshots the Work table around every scenario in
the file and fails if any of them moved it. That is the finding's first
decision, enforced once rather than remembered nine times.

**The operator reference.** `docs/BATON-WORK.md` gains an **Agent
runtime state** section: why the lease exists (Phase and Handler cannot
say what a runner is doing), the read verbs, the published states and
the derived ones with their provenance, the closed cause categories,
the adapter verbs an operator meets in `runtime-history`, the explicit
statement that none of it is workflow authority, where each fact
surfaces in Jobs/Teams/Inbox, the closed inventory key set with its
no-credential boundary, and refresh-versus-poke. The Teams paragraph
above it was also corrected: it described only the poke answer, which
has been two separately-sourced things since slice 5.

Three guards keep the reference honest. The verb list is asked of
`cli.GRAMMAR`, and the state, cause and inventory vocabularies of
`transitions`, so a runtime verb or a sixth cause added later fails on
the day it ships rather than on the day an operator cannot find it.


## Response to review `review-2026-08-19T17-08-00Z.md` (slice 7 round 1)

**R28 — the `runtime-state` reference omitted `session=` and
`expires-at=`.** Accepted, and the diagnosis matters more than the two
lines: the reference was written from what the section was ABOUT
rather than from what the grammar ACCEPTS. That is how a section
promising reconnect and freshness ended up omitting the operand a
reconnect uses and the one that sets the freshness boundary.

Both are added, with a sentence saying what they are FOR rather than
just that they exist — `session=` is how a reconnect lands, so the
member's live locator never points at a session that has gone;
`expires-at=` is the explicit deadline, and omitting it renews from
the configured duration, which is what makes silence past the deadline
mean anything. `runtime-history`'s `after=`/`limit=` were missing for
the same reason and are added too.

The reviewer's regression passes unedited. Beside it I generalized the
guard: every operand of every runtime verb must appear in that verb's
OWN command block, asked of `cli.GRAMMAR`. Per-verb is the whole
point — my first attempt checked the section as a whole and passed
while `runtime-state` was still missing `session=`, because
`runtime-start` spells it a few lines above. Deleting the corrected
line now fails both guards; I checked in both directions rather than
trusting the green.
