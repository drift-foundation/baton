# Progress — keep readiness armed until claim

Implementer: `baton.claude` (`impl`). Baton Work: W11910.

## State

**Awaiting review.** Plan items 1–8 are done and item 9 is done except for the
live smoke, which needs a deploy this role does not perform. Item 10 is the
reviewer's and the operator's.

## What was implemented

**One claim-aware level, shared by both adapter families.** `ReadinessOffers`
in `tools/codex-event-bridge/src/codex_baton_bridge.mjs`, imported and
re-exported by `tools/acp-baton-bridge/src/baton_readiness.mjs`, which no
longer defines its own `DeliveryMemory`. Per-action state scoped by authority
uuid + participant + action key, exactly the old identity:

- non-Work actions keep the old rule verbatim — delivered once while present,
  forgotten on disappearance, re-emitted on return;
- a ready unclaimed Work is `pending` -> `presented` -> `acknowledged`, where
  `presented` records a spent turn and its retry deadline and ONLY canonical
  `claimed:true` reaches `acknowledged`;
- a Work first seen already claimed is delivered once (restart recovery) and is
  then its own acknowledgement;
- while any Work reports `claimed:true`, no unclaimed offer is admitted; the
  claim-slot transition back to free resets retained offers' backoff so a
  deferred offer serves no penalty it never earned;
- at most one unclaimed offer is admitted per poll, in canonical order;
- `markWithdrawn` carries the W49 stale-episode drop, so that path is unchanged;
- disappearance retires every local trace, backoff included.

**ACP bridge** (`acp_baton_bridge.mjs`): `markDelivered` after a returned
prompt became `markPresented`; the stale drop became `markWithdrawn`; `now` is
an injected clock; `usage()` names the claim-based rule and the `--once`
caveat.

**Codex producer** (`codexBatonBridge`): the `delivered` Map became
`ReadinessOffers`; `claimedFirst` is retained and now runs before the offer
memory; a dispatcher answer of `in-flight` is treated as neither failure nor
acknowledgement; `now` is injected; `usage()` updated.

**Codex dispatcher** (`event_bridge.mjs`): `state.inFlight` retains the exact
v11 event id from admission through queued/starting/ambiguous/active,
independently of `dedupWindowMs`, and `enqueue` answers
`{accepted:false, reason:"in-flight"}` for a retry of a delivery it is still
holding. `#releaseDelivery` runs on canonical withdrawal (the `#episodeIsOver`
drop) and at the top of `#settleTurn`, which every terminal ordering reaches —
the ordinary `turn/completed`, the completion that beats its own `turn/start`,
both ambiguous reconciliations, and the resume paths. It ALSO runs from the
active turn's own event wherever that turn is cleared, because `#settleTurn`
releases from the bound attempt and a turn id `#bindAttempt` could not bind
would otherwise strand the identity — which is this Work's own defect one layer
down. Retention applies only to events carrying a v11 action key.

## Decisions taken, and why

All four are recorded in `FINDING.md` under **Implementer revalidation and
clarifications — 2026-08-25**: a backed-off head does not hold the queue behind
it; the dispatcher refusal is its own `in-flight` reason rather than a reused
`duplicate`; the 60s retry cap is adopted as proposed; and the level is
implemented once and imported rather than copied. The confirmed ruling is
unchanged and nothing in it is superseded.

## Tests

Two existing assertions were replaced, both named in the reviewer revalidation
as protecting the defect, and both replaced rather than deleted:

- `busy sessions serialize wakes; turns never overlap` fed three unclaimed
  Work actions and required three model turns. The property it exists for is
  that a busy session is never steered by a second wake, which is not about
  Work — it now asserts the same trail on three pokes, which do all belong in
  one poll.
- `revalidation passing leaves ordinary delivery untouched` asserted that one
  returned prompt suppresses a still-live episode, which is the defect written
  as an assertion. It still requires exactly one delivery; what suppresses the
  repeat is now the canonical claim.
- Codex `a persistent set is level-triggered: suppressed while present, no busy
  loop` and `claiming the same Work does not duplicate its wake` were split
  into an unclaimed-offer case and a claim-acknowledgement case, as the plan
  directs.

Added, covering the finding's regression matrix in both families: a no-claim
turn keeps the offer armed and the SAME process re-offers it after its deadline
(asserted against the session log, so restart-independence is explicit); the
claim acknowledges without a second turn even long past any deadline; a bridge
starting on a live claim still delivers one recovery prompt; an unclaimed offer
waits for the claim slot and lands when it frees (the W10265 shape); two
unclaimed Works yield only the canonical head until its outcome is known;
obligations/trials/pokes beside a deferred Work keep their own rule; a retained
offer withdrawn while it waits is never delivered; and a dispatcher `in-flight`
answer keeps the offer armed without reporting a failure.

Dispatcher retention, in `test/stale_episode.test.mjs` with `dedupWindowMs: 1`
so the fingerprint timer provably is not what refuses: a retry while the same
delivery is starting; a retry while the delivered turn is still running; a
terminal turn releasing the identity so a later retry becomes a new turn; a
withdrawn delivery releasing it; a completion whose turn id never bound still
releasing it; and a generic event keeping exactly its old dedup rule.

## Verification

- `just test-v11`: 3067 passed (parallel) + 52 passed (serial), then the
  `test-acp` sub-gate 62/62.
- `npm test` in `tools/codex-event-bridge`: 355/355, which includes
  `policy_syntax`, `cross_work_fence`, `failed_turn_settlement`,
  `stale_episode`, `event_bridge`, and `runtime_publisher` untouched-behaviour
  coverage.
- Pre-change baselines reproduced first: ACP 55/55, Codex focused 134/134.

## Not done, and why

- **The live smoke** in plan item 9 — one participant finishing Work A and
  receiving already-pending Work B without a restart, and a corrected-runner
  retry after environment repair — requires deploying this bridge and
  restarting a managed runner. That is plan item 10's deploy, an operator
  decision, and outside this role. The focused suites prove the same two
  shapes against a real fake-agent subprocess and a real dispatcher.
- **No Git state was touched**, per repository policy. The working tree carries
  the change for review.

## Review correction — 2026-08-25

Second claim, answering the two [P1]s in `review-2026-08-25T22-04-16Z.md`.
Both reproduced from the current tree and both are corrected.

**A failed claimed-Work recovery wake is not a claimed offer.** The review is
right and the cause is that `pending` was carrying two unrelated meanings —
"an offer nobody has answered" and "a wake nobody received". The
`claimed:true` branch acknowledged both, so a participant whose one recovery
wake failed sat on a live claim with no wake and no retry until a restart:
this Work's own defect, on the one path it had added. A fourth status,
`recovering`, is created for a Work first seen ALREADY claimed and is cleared
only by its own successful delivery. `claimed:true` still acknowledges
`pending` and `presented`, so the acknowledgement everything turns on is
untouched.

**One unclaimed Work becomes a turn at a time — and my first attempt at it was
at the wrong boundary.** The review's asymmetry is exact: in the ACP bridge
`markPresented` runs after the prompt returns, so rotation is sound; in the
Codex producer it runs on socket acceptance, before the turn starts.

I first refused the second unclaimed Work at `enqueue`. That broke three W99
cases — two `Work B never starts on the context W A was interrupted in`
orderings and `an unrelated target keeps draining` — all with "the later Work
was dropped rather than retained". W99 requires the later Work to be QUEUED and
held for a fresh context, and the same review says not to weaken the quarantine
retention paths. **Refusing at the socket conflates "must not become a turn"
with "must not be retained", and retention is what keeps the offer alive.**

So the gate is where a delivery becomes a turn. The pre-turn revalidation each
queued event already performs now answers two questions from one canonical
read: `over` (dropped, as before), `deferred` (the participant holds a claim —
held at the queue head and re-asked every `claimSlotRetryMs`, default 15s), and
`live`. A claimed Work's own recovery delivery is never deferred, because it is
the claim.

**Asked of the authority rather than tracked locally**, and that is better than
the socket refusal quite apart from W99: a claim taken by an interactive turn,
by another adapter, or by an operator at a terminal is invisible to this
dispatcher's bookkeeping and exactly as occupying.

## One difference from the review's wording, stated rather than smoothed over

It asks that B be "neither queued nor started". **B may be queued here; it
provably never starts.** The harm the review names — B spending a model turn
against an occupied claim slot — is closed, and the retention the same review
protects is intact. If socket-level refusal is wanted as well, that is a ruling
about W99's retention contract and is the reviewer's to make, not mine to
assume.

## Verification

`evidence/gate-after-review-correction-2026-08-25.txt`.

- New `tools/codex-event-bridge/test/claim_slot.test.mjs` crosses the
  producer/dispatcher boundary the review named: the producer's own emissions
  are fed to a real `EventBridge`, A's turn is held open, the unchanged
  `[A, B]` level is polled four times, and exactly one turn starts. Then A
  claims and completes — B still does not start — and when the claim
  disappears the same retained delivery is spent with no restart and no new
  event.
- ACP gains the end-to-end pair for the other delivery boundary: a recovery
  prompt that FAILED is delivered again, and one that SUCCEEDED is never
  repeated.
- **Both were measured to fail without the correction**: reverting the
  `deferred` verdict and the `recovering` status gives 3 failures in the new
  Codex file and 1 in the ACP suite. Both files were restored byte for byte.
- ACP **64/64** (62 before), Codex **382/382** (355 before). Nothing removed;
  every stale-episode, fence, quarantine, ambiguous-start, overload,
  orphan-claim, refresh, obligation, poke, trial, `--once` and
  transport-failure case is green unchanged.

## Two existing tests moved, and neither lost an assertion

- `failed_turn_settlement.test.mjs`'s "promotion never displaces a delivery
  already in flight" scripted its canonical read as `[unclaimed, CLAIMED]` — a
  projection in which, under the confirmed ruling, the unclaimed offer must not
  start at all. Its subject is queue-position safety, so the read is now
  scripted in the realistic order: the unclaimed Work revalidates while nothing
  is claimed and the promotion arrives after. No assertion changed.
- The producer's `two unclaimed Works yield only the canonical head until its
  outcome is known` is renamed to
  `the producer admits one unclaimed Work per poll, in canonical order`,
  because this file cannot observe an outcome — `markPresented` runs on socket
  acceptance. What it asserts is unchanged and true; the boundary it does not
  assert is proved in the new cross test, which the comment now points at.

## Documentation

Both READMEs said "at most one unclaimed Work is admitted at a time". That was
the producer's rule and it was not the whole truth: the producer admits one per
POLL, and the claim-slot boundary is the dispatcher's. Both now say which is
which, and both record that a claimed-Work recovery wake whose delivery failed
stays eligible.

## Still the operator's

PLAN item 9's live smoke and item 10's deploy. This correction cannot prove the
live queue advances without being deployed to it, and nothing here was verified
against the running deployment.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Second review correction — 2026-08-26

Both [P1]s are defects in the claim-slot gate I added last round, and they are
the same mistake made twice: deciding a canonical question from something
other than the canonical answer.

**The Codex gate read `claimed` off the QUEUED EVENT.** That bit describes the
world when the producer emitted it, not the entry the pre-turn read just
returned — and the gate had no action-kind test at all. So an unclaimed offer
that was claimed while it waited here was deferred behind the very claim it
existed to recover, and a non-Work obligation, which carries no `claimed`
field, read as unclaimed and was swallowed by a Work-only rule.

Nothing had to be parsed or added to the event to fix it. The read already
returns the exact matching action with its kind and its current claimed state,
and that is what the verdict comes from now: absent is over; a non-Work action
is live; a claimed Work is live as its own recovery and can never wait behind
itself; only a current unclaimed Work defers, and only while a Work claim
occupies the slot.

**ACP had the same gap and a boolean could not say otherwise.**
`episodeStillLive` answered exact-key membership, so a claim taken between the
outer poll and the immediate pre-turn read — by another adapter, an interactive
turn, or an operator — still let the turn be spent. `false` meant the episode
was over and withdrew the offer permanently; `true` started the turn; and an
offer that is still perfectly good but waiting on somebody else's claim is
neither. `episodeVerdict` derives the same three answers from one envelope, and
a deferred offer is retained with **no prompt, no withdrawal and no
presentation** — a turn nobody spent is not an attempt.

**One derivation, two adapters**, which is the point: my previous correction
fixed the Codex path and left ACP answering a different question about the same
authority.

## Which half each case covers

Worth naming, because they are not interchangeable. The review's ACP case
injects `revalidate` and therefore exercises `runBridge`'s HANDLING of a
deferred verdict — it would pass whatever the derivation did. My added case
drives the derivation itself over one envelope: live, over, deferred, a claimed
Work as its own recovery, and a non-Work action beside a claim. Both are needed
and the evidence says which is which.

## Verification

`evidence/gate-after-second-review-correction-2026-08-26.txt`.

- ACP **66/66** (64 before); Codex **396** with one failure that is W12229's.
- **Both corrections measured to fail without them**: reverting the Codex gate
  to the event's own `claimed` fails the two claim_slot cases, and reducing the
  ACP verdict to exact-key membership fails the derivation case. Restored byte
  for byte.
- Three existing boolean injections moved to the verdict vocabulary, since the
  review is explicit that the boolean cannot express the distinction. No
  assertion changed, and the seam has ONE vocabulary — two spellings of one
  answer is how the next reader learns the wrong one.
- Whitespace check clean.

## Reported and not fixed

**W12229**, `--start-thread refuses a relative Baton source before reading
it` — a reviewer regression posted mid-correction and a real defect in that
Work: the bootstrap requires all six operands and refuses an empty one, but
never required the Baton executable and config to be ABSOLUTE, so a relative
path is accepted and the context receives a launcher contract whose paths mean
nothing without a working directory nobody named. `validateConfig` already
refuses that shape for the dispatcher. **Measured** to fail identically with
this Work's change reverted to HEAD, so it is not this turn's. Reported on
T12229 with the direction I would take.

## Still the operator's

PLAN item 9's live smoke and item 10's deploy. Nothing here was verified
against the running deployment.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Third review correction — 2026-08-26

The finding is one I had written the right words for and the wrong code. The
catch branch logged "the event is retained" and returned `live` — and `live` is
the verdict that opens the turn immediately and dequeues the event.

**The sentence used to be true.** Before the claim-slot correction, not
DROPPING an uncertain event was the whole of retention and delivering it was
harmless. That correction gave this read a second job, and I did not revisit
what its failure paths meant: the immediate read must now prove the exact
episode still exists AND prove an unclaimed Work is not waiting behind another
claim, and **a read that failed proves neither**. Delivering anyway spends a
turn against a slot nobody established was free — the thing the gate exists to
stop — while ACP's equivalent failed read throws into its delivery boundary and
retries without prompting.

**A fourth verdict rather than a mapping onto an existing one.**
`over` / `deferred` / `uncertain` / `live`. A failed invocation, unreadable
JSON and a missing actionable set all answer `uncertain`, and the drain holds
such an event exactly as it holds a deferred one: at the queue head, in-flight
identity not released, no turn spent, re-asked on the same bounded cadence.

**One cadence for both, deliberately.** "Come back and ask again" is the same
act whichever of the two questions went unanswered, and a second interval would
be a second thing to tune for one behaviour. What does differ is what an
operator should do, so `actionDeferred` carries `reason: "unreadable"` — an
occupied slot and an unreachable authority call for different actions.

A deployment with no `roleInstructions` still answers `live`: that is a
deployment which never revalidates at all, not a read that failed.

## Two assertions revised, and they had been fair proxies

`a failed revalidation retains the event rather than dropping it` and `a reply
with no actionable set retains the event` both established retention by
requiring the event to BECOME A TURN. That was a reasonable proxy when
delivering an uncertain event was harmless. Under the review's explicit
confirmation, retention is asserted where it actually lives — the event is
still queued — and the turn is required not to have been spent. Their subject
is unchanged and each asserts strictly more.

One test helper gained a `claimSlotRetryMs` passthrough so the new re-ask case
need not wait fifteen seconds. Additive; no assertion touched.

## Verification

`evidence/gate-after-third-review-correction-2026-08-26.txt`.

- `claim_slot` **30/30** with the review's cross-boundary regression kept as
  written; `stale_episode` **22/22** with one added case — an unreadable
  authority is re-asked and delivers once it answers, because retention that
  never retries is a queue nobody drains.
- **Measured to fail without the correction**: restoring both catch branches
  to `live` fails all four. Restored byte for byte.
- Codex **403/403**, ACP **67/67**. **Both Node suites fully green**, and
  nothing is reported as another Work's because there is nothing left to
  report on this side.

## Still the operator's

PLAN item 9's live smoke and item 10's deploy. Nothing here was verified
against the running deployment.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Fourth review correction — 2026-08-26

The review is right, and the shape of it is worth naming: **three consumers
read one envelope from one binary, and only two applied the contract.** Both
producers have validated this exact command's output since W148, and the ACP
bridge validates inside `waitOnce`. The dispatcher's canonical read — the one
that decides whether a model turn is spent — consumed `kind` and `claimed`
raw. An entry carrying a Work key while claiming the `obligation` kind, a
shape the contract rejects on its own locator, was read as an ordinary
non-Work action and walked past an occupied claim slot.

**I fixed more than the review named, twice, and both were the same defect a
step over.**

The review's malformed entry was the MATCHING one. Typing only the match would
have made its regression pass and left the hole open, because the
occupied-slot question is answered from the entries that are NOT the match —
`some(kind === "work" && claimed === true)`. An unreadable neighbour
disqualifies the read exactly as much, and that is now its own case.

And the ruling's second sentence — do not mistake an ignored unknown-kind
entry for authoritative withdrawal — was live in the **ACP bridge** too, by a
different route: `waitOnce` validates, so by the time `episodeVerdict` runs
the unknown kind is already in `ignored_actions` and the key's absence from
`actionable` read as `over`. Same ruling, same correction, second bridge.

## What let 403 green tests stand over this

**The fixtures.** Four dispatcher suites scripted `wait timeout=0` as
`{result:{actionable}}`. The real authority never emits that, and no other
consumer would accept it — only the untyped read did. So the suites were
proving the behaviour of a reply that does not exist, which is why applying
the contract turned 13 of them red before a single one of them was wrong about
what it asserted. They are canonical envelopes now. **The deliberately
unreadable fixtures were left exactly as they are**, and still reach the
uncertain path they assert.

## Verification

`evidence/gate-after-fourth-review-correction-2026-08-26.txt`.

- Codex focused **32 -> 36**, ACP **67 -> 69**. The review's additive case is
  kept exactly as written and passes.
- **Every added case measured to fail without the correction** — 4 of 36 in
  the Codex suite, 2 of 69 in the ACP suite — with the canonical fixtures left
  in place, so the failures are the correction's and not the fixtures'. All
  three sources restored byte for byte against recorded md5s.
- One added case passes with AND without the correction on purpose: a key the
  authority no longer names at all is still dropped. Retention that never lets
  go would be this Work's defect inverted.
- Codex **408/408**, ACP **69/69**, no trailing whitespace.

## Still the operator's

PLAN item 9's live smoke and item 10's deploy. Nothing here was verified
against the running deployment.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Fifth review's [P1] corrected — 2026-08-26

**A validated field is not the same as a required one, and the difference was
the whole defect.** `validateEnvelope` rejected a `claimed` that was present
with a non-Boolean value and accepted its absence, while both consumers decide
the claim slot with `claimed === true`. So a Work that IS claimed but does not
say so answered "the slot is free" about a slot it holds itself.

**Revalidated before editing**, as the review's own premise required:
`participant_actions` emits a Boolean for every Work action unconditionally
(`projection.py:2799`, `row["handler_team"] is not None`). Omission is not a
canonical variant this build has to tolerate, so the field is required rather
than defaulted.

**Two guards rather than one**, because they are two different authority
faults and the older one already had a name: an ABSENT field is an answer the
authority did not give ("carries no claimed verdict"), a WRONG type is an
answer this build cannot read ("claimed is not a boolean"). Both take the
bounded `uncertain` path the third and fourth reviews established, so nothing
new was invented for this.

**One edit, both families.** The ACP bridge imports and re-exports this exact
validator and validates through `waitOnce` before `episodeVerdict` reads
`entry.claimed === true`. That is the finding's own "one implementation,
imported by both families" decision doing its job: the second bridge needed no
second correction.

**The revised assertion is the one the review explicitly authorized.** The
optional-descriptive-fields case described a bare Work with no `claimed` as
valid. The rule the set is drawn on is unchanged -- a field this build
SCHEDULES on is not descriptive -- and `local_id`, `title` and `phase` still
are, so the same case still proves they may be absent.

**Additive on the ACP side.** The review's dispatcher regression is kept
exactly as written; the same defect reached the ACP side by the same route and
the review named no case for it, so one was added there.

### The first measurement was wrong, and saying so is the point

Mutating away the new `=== undefined` branch left both suites green, and that
did not prove the correction was unnecessary -- it proved the mutation was not
one. `typeof undefined !== "boolean"` is true, so the remaining branch still
caught absence and only the message changed. Re-measured against the GENUINE
pre-change guard, one case fails on each side of the shared validator: the
review's in Codex, the added one in ACP. Source restored byte for byte.

### Verification

`evidence/gate-after-fifth-review-correction-2026-08-26.txt`.

- Codex **409/409** (408 -> 409: the review's case now passes rather than
  failing), ACP **70/70** (69 -> 70: the added cross-adapter case).
- The whitespace check is clean.

## Still the operator's

PLAN item 9's live smoke and item 10's deploy, unchanged. Nothing here was
verified against the running deployment.

## State

**Awaiting independent re-review.** No repository state was mutated.


## Sixth review's [P1] corrected — 2026-08-26

**A Work-only gate was governing the whole FIFO by queue position.** `#drain`
selects only `queue[0]`, so a deferred Work at the head retained itself and
returned, and nothing behind it drained. The impact is not ordering
preference: the directed obligation a participant must answer to FINISH the
Work whose claim B waits behind can be the thing queued behind B, so A waits
on an answer that waits on A.

**B does not move.** It stays at the head with its in-flight identity
unreleased, no turn spent and the same bounded retry. What changed is that the
queue behind it is offered the barrier one action at a time.

**The verdict decides, not the event's own `action` block** — that block is a
historical bit from producer time, and scheduling from it is the defect the
third review found one layer up. `live` is exactly the set that may pass, and
all four of the review's requirements fall out of it: a non-Work action passes,
a claimed Work passes as its own recovery (promotion preserved without a
special case), another unclaimed Work answers `deferred` against the same
occupied slot and cannot, and unreadable or withdrawn answers pass nothing.
Two candidates are skipped before the read: an event with no action block,
which `#revalidate` calls `live` by construction because it has nothing to ask
about, and an ambiguous one, which belongs to the head's own path.

### The second measurement corrected my own added case

Three cases were added, because a rule that holds by CONSEQUENCE is one
nothing would notice losing. The generic-event case first asserted only that
no turn started — and it passed with the guard removed, which proved the
assertion could not see what the guard does rather than that the guard was
unnecessary.

**Removing the guard does not produce a rotation. It produces a fault loop**:
the scan reaches an event with no action block, faults composing a log line
about a key that is not there, the drain's own catch marks the head ambiguous,
and every retry repeats it. Turn order survives that. The case records the
warning channel and requires it empty now, and that is what discriminates —
41/41 with the guard, 40/41 without. So the honest statement is that the guard
prevents a fault loop, not a leak: without it the barrier breaks rather than
lets a generic event past.

### Verification

`evidence/gate-after-sixth-review-correction-2026-08-26.txt`.

- Codex **413/413** (410 -> 413: the review's case plus the three added),
  ACP **70/70**, unchanged and correctly so — this is the dispatcher's queue
  discipline and the ACP loop already continues after a deferred Work, as the
  review notes.
- Every added case measured against the pre-change source; restored byte for
  byte, md5 a350f4d6ab59446abad6149c7ddc30dd.
- The whitespace check is clean.

## Still the operator's

PLAN item 9's live smoke and item 10's deploy, unchanged.

## State

**Awaiting independent re-review.** No repository state was mutated.


## Seventh review's [P1] corrected — 2026-08-26

**Ambiguity followed the queue position instead of the candidate.** The sixth
correction lets a live non-Work action pass a deferred Work at the head, and
`#drain` starts that candidate's turn — but both reconciliation paths looked at
`queue[0]`, which is the retained Work, and the scan skips ambiguous candidates
on every retry. A turn the server actually created was therefore never bound:
completion could not be correlated, the delivery could not settle, and the lane
sat behind an active server status.

Both sites find the ambiguous entry wherever it sits now, reconcile it before
any replay, and leave B at the head with its original in-flight identity.

### The two halves are not equal, and I nearly reported them as if they were

- `#reconcileTarget` reverted alone: **2 failures**. It carries the fix.
- The `#drain` selection reverted alone: **43/43 still passing**. It is not
  measured by either case.

Saying "both halves are the correction" would have been the comfortable
summary and the wrong one.

### One path is left uncovered, and it is named rather than implied

The drain half covers something the reconcile half does not: `turn/start`
failing while the client is CONNECTED reconciles immediately in the catch, but
a dropped transport skips that branch by its own guard, leaving the next
ordinary drain as the only thing that runs. **I wrote a case for it and it
hung** — the disconnect mid-`turn/start` left the suite unable to terminate —
and a hanging test is worse than an uncovered path, so it was removed rather
than shipped.

So the drain change is reasoned, not measured. The reviewer's call: cover that
path with a construction that terminates, or remove the drain selection as
unreachable-in-practice.

### Additive

The review required "preserve B at the head with its original in-flight
identity" and nothing asserted it. `the deferred Work keeps the head and its
in-flight identity throughout a passing action's ambiguity` re-enqueues B's
unchanged offer and requires `in-flight` — without that identity, the
producer's next level-triggered re-send would queue B behind itself.

### Verification

`evidence/gate-after-seventh-review-correction-2026-08-26.txt`. Statuses
captured, never piped: `CODEX_STATUS=0` (415/415, from 413),
`ACP_STATUS=0` (77/77), `DIFFCHECK_STATUS=0`.

## State

**Awaiting independent re-review.** No repository state was mutated.
