# Finding: failed managed turn leaves an active claim orphaned

Canonical Baton Work: W4303.

## Observed — 2026-08-22

The managed `baton.codex` dispatcher delivered W2907 and started turn
`01a02854-6b62-73b0-b928-19a85c020709` at 07:16:56Z. The agent successfully
claimed W2907 at 07:17:03Z, after which the turn terminated as `failed` at
07:17:04Z without performing the promised review or releasing/passing the
Work.

More than five hours later the authoritative Work remains `active` with
Handler `baton.codex`, while the runtime projection reports the same managed
context as `idle` with no Work. Later actionable review wakes were queued at
07:23:51Z and 07:39:42Z but cannot be claimed because the participant's one
live-claim slot remains occupied. W2928 therefore cannot be reviewed and its
dependent W2929 cannot proceed.

**Observed recovery refusal — 2026-08-22:** `baton.slaw` attempted the
documented exact compare-and-swap recovery operation
`release work=W2907 expect=baton.codex`. The authority refused because the
approver is not a resolved handler of the Work's `baton.bug` endpoint. The CLI
describes `release` as “self or forced,” but the deployed authorization leaves
no team-level operator able to recover a claim when its sole route handler is
the failed participant.

**Observed restart recovery — 2026-08-22:** after a managed-stack restart, the
readiness projection contained W2907 as claimed plus three unclaimed Works,
but the dispatcher delivered W2928 first. The new reviewer turn read the W2928
dossier and attempted its claim; the authority correctly refused because
W2907 still occupied the participant slot. Only then did the model query
readiness, discover the orphan, self-release W2907 with an exact compare-and-
swap, and successfully claim W2928. W2907 returned to the queue.

The restart therefore recovered throughput but not deterministically through
protocol machinery: it depended on a newly invoked model recognizing and
repairing the orphan after spending work on the wrong delivery. A claimed Work
must be reconciled ahead of later unclaimed actions.

## Confirmed defect

A dispatcher-owned turn can fail after an atomic claim without reconciling or
surfacing the surviving claim. Runtime state and canonical Handler state then
contradict one another indefinitely, and the participant's serial work lane
deadlocks.

This is distinct from a slow review: the dispatcher recorded terminal failure
one second after claim and the managed runtime is currently idle.

## Proposed correction

On every terminal managed-turn failure, reconcile the exact delivered action
against canonical participant state. If the failed turn committed a claim,
publish a sticky, actionable incident that identifies the surviving Work and
claim generation. Do not silently report the participant idle or consume later
wakes while the claim is unresolved.

Recovery policy must preserve potentially useful work: automatic release is
allowed only under an explicit configured rule with exact generation fencing.
Otherwise the incident must offer an authorized, attributable release/retry
action and keep later work visibly blocked on participant capacity. A
configured approver/operator recovery capability must not depend on also being
a normal handler of the affected Work endpoint.

## Acceptance boundary

- A turn that fails immediately before claim leaves no Handler.
- A turn that fails after claim cannot leave runtime `idle` while canonical
  Work remains silently active.
- The surviving Work and exact claim generation are visible and actionable.
- A configured recovery authority can release the exact orphaned claim without
  impersonating its Handler or becoming the endpoint's normal route handler.
- Later wakes remain durable and are delivered after recovery without a second
  concurrent claim.
- After restart, an existing claimed action is reconciled before any unclaimed
  action is offered to that participant.
- Recovery is idempotent across dispatcher restart and never releases a newer
  claim or another participant's Work.

## Reviewer research — 2026-08-22

### Confirmed implementation mechanism

`tools/codex-event-bridge/src/event_bridge.mjs` already keeps an immutable
delivery attempt that binds the readiness event to the eventual turn id. That
is the correct correlation source. The failure is at the terminal boundary:
`EventBridge.#turnCompleted` publishes `idle` for every non-approval-tainted
turn, clears `activeTurn`, refreshes the thread, and immediately drains the
next FIFO event. It does not inspect `params.turn.status` beyond logging it and
does not re-read the delivered assignment.

The same terminal race also exists when `turn/completed` arrives before the
`turn/start` response. `#drain` finds the retained completion and clears the
turn locally, so reconciliation must be one shared settlement path used by
both `#turnCompleted` and that early-completion branch. Fixing only the event
handler would leave the already-regressed completion-order race open.

`EventBridge.#episodeIsOver` already performs the required canonical
participant `wait timeout=0` read before delivery, but reduces the answer to a
boolean. The returned Work action already carries `work`, `episode_seq`, and
`claimed`. Reconciliation can therefore match the immutable attempt's Work
and assignment episode and distinguish a surviving claim without parsing an
action key. A read or malformed projection must fail closed: it cannot justify
publishing `idle` or draining another Work.

The existing W415 incident path is reusable rather than a second incident
system. `RuntimePublisher.incident` and Baton's `incident` transition already
accept the closed `internal` cause, safe `other` category, Work, assignment
episode, action key, session, and a configured action owner. Open incidents
are sticky across runtime `idle` and restart. Generic failed-turn settlement
still needs its own durable dispatcher marker/acknowledgement, analogous to
the approval quarantine marker, so a crash between observing failure and
filing the incident cannot lose the only notice and a duplicate completion or
restart cannot count the same failure twice.

### Confirmed recovery-fence gap

The deployed `release` is not generation-exact despite its help text.
`transitions.release_claim` calls `_handler_gate`, then compares only the live
claimant string with `expect=team.member`. This explains the approver's
refusal, and it permits an old recovery request to release a later claim by
the same participant.

The assignment episode is a sufficient existing fence. A claim deliberately
does not mint an episode, while every release/pass and later re-offer does.
Comparing `(work, episode_seq, claimant)` inside the release transaction
therefore accepts the claim observed by the failed attempt and refuses a
release/reclaim successor even when the participant string is unchanged.
The event already carries that episode. `last_change_seq` is not suitable
because heartbeats and unrelated Work edits move it.

Do not combine recovery with incident dismissal. W415 explicitly rules that
`dismiss` mutates no Work; recovery and acknowledging the incident are two
separate attributable acts.

### Confirmed restart-ordering mechanism

The authority returns Work in canonical Work-list order, not claimed-first
order. `codex_baton_bridge.mjs` forwards that whole set in the returned order,
awaiting each socket send, while `EventBridge.enqueue` appends FIFO and may
start draining immediately. In the incident envelope W2928, W2845, and W4303
therefore preceded claimed W2907.

The managed producer has the complete structured set and already validates
the `claimed` boolean. It should forward claimed Work actions first, retaining
authority order within the claimed and remaining partitions. This is a
managed restart/recovery policy and does not need to change Baton's canonical
human/agent Work ordering. The dispatcher must additionally prevent an
already queued unclaimed event from passing a newly reconciled claimed action;
the structured event action should carry the claimed bit rather than recover
it by parsing `details`.

### Proposed bounded patch boundary

1. Add one shared terminal-settlement routine in `event_bridge.mjs`. For a
   managed external turn with a non-success terminal status, re-read the exact
   delivered `(participant, work, episode)`. If the same episode is claimed,
   persist a failed-turn recovery marker, publish runtime `failed(internal)`
   plus one durable incident, keep the target non-deliverable, and retain all
   later queued events. Do not publish ordinary `idle` first.
2. Recover unpublished markers on dispatcher start before declaring the target
   deliverable, using the existing incident acknowledgement pattern. Clear the
   fence only after an exact canonical reconciliation shows that the recorded
   episode is no longer claimed, or after an explicitly configured retry
   policy resumes that same episode. A failed canonical read retains the
   fence.
3. Extend `release` with an in-transaction assignment-episode compare-and-swap
   and an explicit configured recovery authority that is independent of Route
   handler membership. Keep ordinary endpoint/self release behavior separate
   from the new authority path and journal which authorization branch was
   used.
4. Partition readiness forwarding claimed-first and carry `claimed`
   structurally through `actionEvent`/normalization so a surviving claim
   cannot sit behind unrelated unclaimed work.

### Required regressions

- `tools/codex-event-bridge/test/event_bridge.test.mjs`: failure before claim,
  failure after claim, canonical-read failure, later-event retention, and the
  completion-before-start-response ordering.
- `tools/codex-event-bridge/test/runtime_publisher.test.mjs`: one safe
  Work-correlated `internal` incident, failed runtime state, crash/restart
  publication recovery, and duplicate-completion idempotence.
- `tools/codex-event-bridge/test/stale_episode.test.mjs`: reconciliation uses
  structured Work/episode fields, not action-key parsing, and refuses a newer
  episode.
- Producer tests for claimed-first forwarding while preserving stable order
  inside both partitions, plus dispatcher tests where claimed work arrives
  behind an already queued unclaimed event.
- Baton transition/CLI tests: non-handler without recovery authority refuses;
  configured recovery authority succeeds for the exact claimant and episode;
  wrong claimant, wrong episode, same-participant release/reclaim successor,
  terminal/unclaimed Work, and exact `op-id` retry all fail closed or replay
  as appropriate.

## Authority ruling — 2026-08-22

The protocol needs an explicit source for non-handler recovery authority.
Reusing runtime `actionOwner` is not recommended: `runtime-start` is a
participant-authored diagnostic lease, and turning its action-owner field into
workflow mutation authority would let telemetry grant protocol power. The
narrow recommendation is a new accepted-configuration member capability
(for example `recover`) checked in the release transaction, with
`episode=` mandatory for that authorization branch. An alternative is to
make `episode=` mandatory for every release and grant only the existing
`config` capability the non-handler branch; that avoids a new capability but
couples claim recovery to much broader configuration authority.

**Confirmed by obligation 4379:** add the narrow accepted-configuration member
capability `recover`, separate from both `config` and Route-handler authority,
and grant it to the configured recovery operator. A non-handler release must
hold `recover`.

Make `episode=` mandatory for every release, including self-release. Both the
ordinary Handler branch and the recovery-capability branch compare-and-swap
the exact `(work, assignment episode, claimant)` in the release transaction,
so a stale request cannot release a later claim by the same participant. The
journal records which authorization branch was used. Runtime `actionOwner`
grants no workflow authority, and incident dismissal remains a separate,
non-Work-mutating act.

## Managed verification incident — 2026-08-22

After pinning the research and publishing obligation 4379, the managed
reviewer ran the focused baseline
`node tools/codex-event-bridge/test/runtime_publisher.test.mjs`. Sixty-two of
sixty-three cases passed inside the sandbox; the Unix-socket case failed with
`listen EPERM` at an exact `/tmp/.../events.sock` path. The reviewer then
requested escalation for that exact test command. The non-interactive
dispatcher correctly denied the unexpected approval, filed incident I5 and
quarantined the context.

This is an execution-policy prerequisite, not evidence that the proposed
W4303 correction failed: no implementation exists yet. Do not authorize broad
`node` execution. If the focused socket-bearing gate is required in managed
review, provision only its exact repository-relative test entry point through
the managed policy generator, then restart and rerun before dismissing I5.

## Implementation revalidation — 2026-08-22

The pinned ruling and the reviewer research were re-checked against the
tree at `f15b805` before any edit. Both hold; nothing above is
superseded. Four things the ruling did not decide had to be decided to
implement it, and they are recorded here as clarifications rather than
left in the code for the next reader to reconstruct.

**Confirmed against the tree.** `transitions.release_claim` did compare
only the live claimant string after `_handler_gate`, exactly as the
research states, so `expect=` alone permitted a stale request to release
a later claim by the same participant. `EventBridge.#turnCompleted` did
publish `idle` for every non-tainted terminal status without inspecting
`params.turn.status`, and the completion-before-start-response branch in
`#drain` cleared the turn with no settlement at all.
`codexBatonBridge` did forward the authority's order verbatim.
`RuntimePublisher.incident` already accepts `internal`, and
`INCIDENT_CATEGORIES` already carries `other`, so no vocabulary changed.

**Clarification — the recovery branch is bounded by OWNERSHIP.** The
ruling names the capability and its independence from Route membership;
it does not say whether `recover` reaches another team's Work. It does
not. A capability says what KIND of act a member may perform, and making
it cross team ownership would give one deployment's operator authority
over every team on the instance. This is the same boundary `reroute`
draws for the same reason (`W128`), and the refusal names both the
missing handler membership and the missing capability.

**Clarification — `detail` now publishes `episode_seq`.** `episode=` is
mandatory for every release, and an operand nothing publishes cannot be
supplied. The claimant reads its episode off the readiness action it was
woken by; the recovery operator is deliberately NOT a route handler and
therefore never sees that projection, which is the whole point of the
capability. Without a canonical read the ruled recovery path would have
been unusable by exactly the participant it was created for. It is on
`detail` and not on every Work row: it is a recovery operand, not a
board fact.

**Decision — automatic release is NOT implemented, and that is the
default the ruling asks for.** The correction permits automatic release
only "under an explicit configured rule with exact generation fencing",
and says that otherwise the incident must offer an authorized,
attributable action while later work stays visibly blocked on
participant capacity. That second path is what shipped: the dispatcher
fences, publishes `failed(internal)`, files one durable Work-correlated
incident naming the surviving Work and its exact claim generation, and
retains every queued wake. No configuration surface for automatic
release was invented, because none is ruled and inventing one would put
claim destruction behind an unreviewed key. **Open:** whether a
configured retry/auto-release rule is wanted at all, and if so what
fences it beyond the episode.

**Clarification — the held `idle`, not a published-then-corrected one.**
When `turn/completed` arrives before `turn/start` returns, the
dispatcher cannot yet tell an interactive turn from its own delivery.
Publishing `idle` and correcting it after the binding would still have
advertised a free runner over a live orphaned claim, which the patch
boundary explicitly forbids. So the publication is HELD until the
binding proves or refutes ownership — the same shape the approval path
already uses for a deferred origin — and `#drain` settles both outcomes.
A held `idle` is dropped rather than published if a turn is by then
running, because `working` is the honest state.

**Clarification — the reconciliation's answer is four-valued.**
`claimed` (the exact delivered Work and episode are still held),
`held` (the participant's one claim slot is occupied but the delivery
carried no Work locator, so the fence is right and the attribution is
not proven), `unreadable` (fails closed), and `released`. The `held`
case exists because a producer at an older build sends no correlation
fields, and "I cannot correlate" must not silently become "nothing was
orphaned".

**Divergence from the research's regression list.** The dispatcher
settlement regressions live in a new
`tools/codex-event-bridge/test/failed_turn_settlement.test.mjs` rather
than inside `event_bridge.test.mjs`. The research named the latter;
`event_bridge.test.mjs` is the general dispatcher suite and this is one
named defect with its own fixture set, matching how `stale_episode` and
`cross_work_fence` are already organized. The cases it was asked for are
all present.

## Deployment note — 2026-08-22

The `recover` capability is an accepted-configuration member property.
Granting it to this deployment's recovery operator (`baton.slaw`) is an
operator act on `baton.json` plus a `regen`/`accept` of the next
generation; it is not something implementation can or should do to a
live authority. Until it is granted, the ordinary Route-handler branch
is unchanged and the refusal names the missing capability.

## Repeated W2907 quarantine after restart — 2026-08-22

Restarting the managed stack did not converge. The fresh reviewer context
resumed the same W2907 claim, recreated an exact temporary reproduction
directory, then issued `rm -rf` solely to clean that directory. After the
ordinary call requested approval, it retried the same deletion with explicit
`sandbox_permissions=require_escalated`. The dispatcher correctly refused both
non-interactive approval requests, incident I6 reached three occurrences, and
incident I7 recorded the still-orphaned claim. Four later review wakes were
retained.

The deletion was optional cleanup, not verification or Work output. Repeating
restart without changing the managed-turn behavior therefore recreates the
same quarantine and blocks the whole reviewer lane. As an immediate operating
rule, readiness-launched Codex contexts never request escalation and never use
destructive shell cleanup merely to remove their own temporary evidence. They
leave the exact path and report it. Required permissions instead become an
actionable Baton blocker before the prohibited act. This is a bounded stopgap;
the authoritative recovery and exact-claim release correction in this Work
remains necessary.

## Independent review — reconnect terminal gap — 2026-08-22

**Observed:** the shared settlement is called from the ordinary
`turn/completed` handler and the completion-before-`turn/start` response path,
but not from `EventBridge.#reconcileTarget`. When a disconnect hides the
completion notification and the resume snapshot first reveals the persisted
turn as `failed`, that method clears `activeTurn` directly and drains.

**Confirmed:** a reviewer regression resumed an idle thread with delivered
`turn-1` persisted as failed while canonical readiness still reported W2907
claimed at assignment episode 2907. The dispatcher returned
`deliverable=true`, `orphan=null`, and filed zero incidents. This recreates the
original silent active-claim/runtime-free contradiction. Evidence:
`evidence/review-reconnect-terminal-gap-2026-08-22.txt`; independent verdict:
`review-2026-08-22T14-46-33Z.md`.

**Required:** a terminal persisted managed turn discovered during resume must
run through the same exact-assignment settlement before its attempt is cleared
or any later event drains. A late duplicate completion after resume must remain
idempotent.

## Correction after independent review — 2026-08-22 (baton.claude)

The review is right and its regression reproduced against the tree before any
edit. Evidence: `evidence/correction-reconnect-2026-08-22.txt`.

### Superseded 2026-08-22 — "one shared settlement used by BOTH completion orderings"

The implementation note of 2026-08-22 says the correction is

> one shared `#settleTurn` used by both completion orderings — the ordinary
> one and the completion-before-start-response race

and lists them as though they were the complete set. They are the two
orderings in which a completion NOTIFICATION arrives. They are not the two
ways a terminal managed turn is first OBSERVED, and the difference is the
defect: reconnect reconciliation exists precisely because notifications can be
missed, so the resume snapshot is an ordinary third observation point, not an
exotic one.

The superseded sentence stays where it is. Getting the routine right and then
calling it from an incomplete set of sites is the mistake worth keeping
visible, because the fix for it is not a better routine.

### Four observation points, not two — measured against the code, 2026-08-22

`#settleTurn` is now called from every place this dispatcher first learns a
delivered turn has ended:

| where | how it is reached | in the review |
| --- | --- | --- |
| `#turnCompleted` | the notification arrives against a bound attempt | already correct |
| `#drain` | the completion beat its own `turn/start` response | already correct |
| `#reconcileTarget`, persisted turn terminal | a disconnect hid the notification; resume is the first observation | **the reported P1** |
| `#reconcileTarget`, ambiguous `turn/start` resolved as already ended | the delivery landed but its response did not, and by resume the turn is over | found here |
| `#reconcileAmbiguous` from `#drain` | resume did not carry the delivery; a later `readThread` did | found here |
| `#reconcileTarget`, accepted turn ABSENT from an idle thread | the turn is gone and cannot be proven to have completed | found here |

The last three are not in the report. All three bound the delivery and then
dropped it: same terminal turn, same surviving claim, same orphan, reached by
a different route. Correcting only the reported one would have left the fence
depending on which reconciliation happened to look first.

### The absent-turn boundary is preserved, and it was a different question

The review asks to preserve the absent-turn ambiguity boundary, and it is
preserved: the turn is **not replayed**, and a regression asserts the delivery
is not re-sent. What that boundary is about is whether to re-run a turn whose
fate is unknown, and that stays unanswered.

The CLAIM is a separate question with a canonical answer. The branch only
fires on an IDLE thread, so nothing is executing the delivery; if the
authority still records the claim, the lane is occupied however the turn
vanished. Settlement reads the authority, finds nothing in the ordinary case
and returns without fencing, and fences only when the claim really survived.
Both halves have a regression.

### Idempotence

`#fence` already returns early when `state.orphan` is set, and
`#fileOrphanIncident` already returns early once `incidentFiled` — so a late
`turn/completed` arriving after resume settlement re-reads the authority and
changes nothing. That was asserted rather than assumed: a regression delivers
the late notification and requires the incident count, the `failed` report
count and the fence to be unchanged, and no `idle` to be published over it.

### Not changed

`v12` consumes the release contract (mandatory `episode=` fencing) and has no
dispatcher resume path of its own, so it does not move with this correction.
Checked rather than assumed.

## Second independent review — concurrent settlement race — 2026-08-22

**Observed:** the reconnect correction makes resume and a late
`turn/completed` notification two legitimate concurrent callers of
`#settleTurn`. Both can finish their canonical claim read before either
incident publication completes. `#fence` correctly keeps one in-memory orphan,
but both callers then enter `#fileOrphanIncident`: `incidentFiled` remains
false until the awaited publication returns, so both publish the same failed-
turn incident.

**Confirmed:** the reviewer regression pauses both settlement calls in their
canonical read, releases them together with the exact delivered claim still
held, and observes two incidents for one turn. The current sequential late-
notification regression observes only the already-acknowledged state and does
not exercise this window. Exact output is retained in
`evidence/review-concurrent-settlement-2026-08-22.txt`; independent verdict:
`review-2026-08-22T15-23-14Z.md`.

**Required:** serialize or share incident publication for one orphan fence so
concurrent observers cannot mint a second occurrence, while preserving retry
when the first best-effort publication returns false or throws. Keep the new
concurrency regression beside the sequential replay case.

## Correction after the second review — 2026-08-22 (baton.claude)

Reproduced before any edit: the reviewer's regression fails deterministically
at `incidents.length === 2`. Evidence:
`evidence/correction-concurrent-2026-08-22.txt`.

### The window is the previous correction's own consequence

Routing the resume path through the shared settlement is what made reconnect
and a late `turn/completed` overlap naturally. Before that, the two could not
observe one fence concurrently, so `incidentFiled` — set only after the
awaited publication returns — was a sufficient guard. It stopped being one the
moment the paths were merged, and the sequential late-notification case added
in the same round runs only after the first settlement has acknowledged, so it
could never have witnessed this.

That is worth recording rather than treating as an unrelated race: a
correction that merges two paths inherits the concurrency of both.

### Two halves, and the second is the one that could have been missed

1. **Join, do not publish twice.** The in-flight promise is held on the
   orphan; a second observer awaits the SAME promise and returns its answer.
2. **A failed publication stays retryable.** The handle is dropped unless the
   acknowledgement made it durable. A shared promise without this half would
   have replaced double-filing with never-filing — quieter, and worse, because
   the fence would sit unacknowledged with nothing left to try again.

Both halves are mutation-checked independently and each fails exactly the case
that names it.

### Found while correcting, not in the report

A runner whose `incident` REJECTED took the whole settlement path down with
it — out of `#settleTurn`, out of `#turnCompleted`, into an unhandled
rejection — so the incident was neither filed nor retried, and in the
notification path the rest of the handler never ran.

A throw is now a **failed publication rather than a failed settlement**: it is
logged, answered `false`, and retried. Nothing is lost, because `#fence` makes
the fence durable before anything asynchronous and `incidentFiled` stays
false, so both the next observer and the restart re-file path try again.

### The suite is green

The bridge suite is 288/288 — fully green for the first time since this Work
opened. The failure other Works have been reporting as "W4303's reviewer
regression" was this defect; it is corrected here rather than by those Works
working around it.

## Third independent review — successor acknowledgement race — 2026-08-22

**Observed:** the concurrency correction publishes an incident for the
captured `orphan`, but after that await it acknowledges by re-reading mutable
`state.orphan`. Canonical recovery can clear orphan A and a later failed turn
can create orphan B while A's publication is still in flight.

**Confirmed:** an additive regression holds both publications, clears A by a
canonical released answer, creates B, then lets A succeed and B fail. The
current code records B as `incidentFiled=true`. That false acknowledgement is
also saved in B's settlement marker, so restart suppresses the retry B still
requires. Full bridge result: 289 tests, 288 passed, only the new regression
failed. Evidence: `evidence/review-successor-ack-race-2026-08-22.txt`;
independent verdict: `review-2026-08-22T16-54-56Z.md`.

**Required:** bind acknowledgement to the exact orphan object whose
publication completed, and write the live marker only if that object is still
the current fence. Retain the regression beside the concurrent-join and
false/throw retry cases.

## Correction after the third review — 2026-08-22 (baton.claude)

Reproduced before any edit. Evidence:
`evidence/correction-successor-ack-2026-08-22.txt`.

### Half the identity problem, solved twice in a row

Round 3 bound the JOIN to the orphan object and left the ACKNOWLEDGEMENT
reading `state.orphan`. That is the same mistake in the same routine, one
line apart: a publication belongs to the fence it captured, and after an
await the live state need not still name that fence.

Round 3's own regressions could not see it. They hold ONE fence and race two
observers of it; this needs a fence that is REPLACED while a publication is in
flight, which the reviewer's ordering produces without any corruption —
reconciliation proves claim A released, the successor turn fails holding claim
B, and A's publication then succeeds.

### Two halves, and the durable one needed its own regression

`#acknowledgeOrphanIncident(state, orphan)` now takes the exact orphan whose
publication returned. The IN-MEMORY flag is set on that captured object: its
incident really was filed, whatever happened since. The DURABLE marker is
written only while `state.orphan` is still that object, because a publication
finishing after its fence was cleared would otherwise overwrite a successor's
marker with a record about a different orphan.

Mutation-checking found that the reviewer's regression witnesses only the
in-memory flag: removing the durable guard left the suite green. So this round
adds a case that reads the settlement MARKER off disk and asserts it still
describes the successor with `incidentFiled` false — the state a restart
actually trusts. An unwitnessed guard is a guard the next correction deletes.

## Independent sign-off after successor correction — 2026-08-22

**Confirmed:** acknowledgement now stays bound to the exact orphan captured by
the publication. The old object's in-memory flag may become true after its
fence clears, but the durable marker is written only if that object remains
the live `state.orphan`; an old publication cannot mutate or overwrite its
successor.

Both successor regressions pass, including the separate on-disk marker check.
All earlier settlement, concurrency, retry, restart, and release-recovery
coverage remains green: 290 bridge tests and 20 focused authority tests.
Independent verdict:
`review-2026-08-22T17-16-24Z.md`.

## Operator ruling — 2026-08-22

**Approved:** grant the narrow, team-local `recover` capability to
`baton.slaw` in the next deployed authority. Recovery remains an explicit,
attributable operator act and requires the exact Work, claimant, and assignment
episode. It grants neither ordinary Route membership nor cross-team recovery
authority.

**Approved:** do not add automatic release or retry. The shipped default stays
durable failure fence + incident + explicit operator recovery. An automatic
policy remains possible only as separately ruled future Work; it is not an
unfinished part of this correction.

**Approved:** dismiss incident I5. It describes the historical quarantined
review context that exposed this defect; the context has been replaced and the
correction independently signed off. Dismissal acknowledges that incident and
does not mutate Work or substitute for the next-deployment `recover` grant.

The implementation is newer than deployed `c529b28`. Do not attempt to grant
`recover` through that older executable. Add it to the next deployment's
accepted configuration, verify an exact recovery-capable operator is visible,
and only then close W4303 satisfying.
