# Readiness offers clear before a successful claim

## Trigger

On 2026-08-25 the Baton implementation lane became idle while four ready,
unclaimed Works remained queued and showed `pickup=overdue`: W6630, W6632,
W6633, and W10265. Dispatch was running, `baton.claude` reported an idle live
runtime, and no participant held a claim.

This is a confirmed v11 readiness-delivery defect. It is not a dependency
gate, a paused-dispatch condition, or an agent scheduling choice.

## Observed evidence

**Observed:** W6630, W6632, and W6633 were each delivered to
`baton.claude` while that runner's configured Baton executable was an obsolete
build that refused the current authority. The agent turn returned without a
claim, but the bridge retained each action key as delivered.

**Observed:** action `work:2b077949-W10265:11470:g2` was delivered while
`baton.claude` still held W6627. The agent explicitly read W10265 but correctly
did not claim it because the one-live-claim rule kept W6627 authoritative.
After W6627 passed and closed, W10265 stayed queued and overdue while the
runner reported idle. No restart-independent redelivery followed.

**Confirmed code path:** `DeliveryMemory` in
`tools/acp-baton-bridge/src/baton_readiness.mjs` records a Boolean delivered
value by authority, participant, and action key. `runBridge` in
`tools/acp-baton-bridge/src/acp_baton_bridge.mjs` calls `markDelivered` when an
agent prompt returns successfully, without establishing that the Work was
claimed or otherwise ceased to be actionable. `sync` then suppresses the same
still-present key on every subsequent `wait` result.

**Confirmed sibling path:** `codexBatonBridge` in
`tools/codex-event-bridge/src/codex_baton_bridge.mjs` likewise records a key as
delivered after the event socket accepts it, then suppresses that key while it
remains in the actionable projection. Socket acceptance is transport
acknowledgement, not workflow acknowledgement.

**Confirmed documentation conflict:** both bridge documents describe this as
level-triggered whole-set delivery, but their actual clearing condition is
successful prompt/event delivery. A restart happens to empty the in-memory
delivery set; it is a workaround, not part of the correctness model.

## Confirmed ruling — 2026-08-25

Slawomir confirmed that readiness is a level-triggered condition and this
correction must ship in v11:

- `ready && unclaimed` keeps the Work offer asserted;
- forwarding an event or completing an agent prompt does not acknowledge or
  clear the offer;
- the exact successful atomic `claim` is the acknowledgement that clears the
  unclaimed offer;
- if the participant already holds another Work, additional Work offers stay
  armed without repeatedly interrupting the busy agent;
- release or pass makes the newly claimable assignment an armed offer again;
  reroute, block, park, or terminal closure withdraws the old offer according
  to canonical state;
- polling and ordinary runner recovery must make progress without a process
  restart.

This ruling supersedes the bridge comments, documentation, and tests that
treat one successful prompt/event delivery as sufficient reason to suppress a
still-ready unclaimed Work indefinitely.

## Correction boundary

The v11 correction owns readiness delivery and acknowledgement in both managed
adapter families:

- `tools/acp-baton-bridge/src/baton_readiness.mjs`;
- `tools/acp-baton-bridge/src/acp_baton_bridge.mjs`;
- `tools/codex-event-bridge/src/codex_baton_bridge.mjs` and the dispatcher
  acknowledgement/retention boundary it feeds;
- their focused tests and user-facing bridge documentation.

The SQLite authority and atomic claim operation remain the only workflow
authority. The bridge must not manufacture claims, mutate Work to force a new
episode, or use raw database access. The implementation may retain and
throttle an offer locally, but must distinguish transport delivery from a
canonical claim acknowledgement.

## Required behavioral model

1. Polling observes the complete participant-relative actionable level.
2. A ready unclaimed Work becomes a retained offer.
3. If the participant already has a claimed Work, the retained offer waits
   locally; it is not forgotten and does not start another Work turn.
4. Immediately before presentation, the bridge revalidates the exact action
   key as it does today.
5. After a Work turn or dispatcher delivery, canonical state determines the
   result. A matching successful claim acknowledges the offer. A still-ready
   unclaimed Work remains pending and is retried with bounded backoff or on the
   participant's claim-slot transition; it is never permanently suppressed.
6. If the key disappears because the Work was blocked, rerouted, parked,
   superseded, or closed, the retained offer is withdrawn.

## Reviewer revalidation — 2026-08-25

**Confirmed — authority shape:** `participant_actions` in
`src/baton_work/projection.py` emits both a participant's one claimed Work and
every ready unclaimed Work the participant is eligible to claim. Claiming does
not change the action key: `work:<id>:<episode_seq>:g<generation>` remains the
same and only `claimed` changes from `false` to `true`. The authority preserves
the canonical Work-list order; the Codex producer's `claimedFirst` helper is a
managed-adapter scheduling rule, not an authority guarantee.

**Confirmed — ACP loss:** `DeliveryMemory.sync` has only two states, absent and
delivered. `runBridge` calls `markDelivered` immediately after
`AcpAgentSession.promptText` returns, before another canonical read. A completed
turn that did not claim is therefore indistinguishable from a successful
claim. The next unchanged projection is filtered forever. The existing test
`revalidation passing leaves ordinary delivery untouched` asserts that exact
suppression and must be replaced with claim-aware cases.

**Confirmed — ACP busy violation:** the test `busy sessions serialize wakes;
turns never overlap` feeds three unclaimed Work actions and requires all three
model turns. Serialization prevents concurrent prompts but does not respect the
one-claim slot: after the first offer, the other two must wait for canonical
claim/no-claim resolution. This test currently protects the live defect.

**Confirmed — Codex loss:** `codexBatonBridge` records the key in `delivered`
when the event socket answers `accepted` or `duplicate`. The producer never
observes whether a managed turn claimed. The same unchanged unclaimed action is
therefore suppressed after queue admission. The tests `a persistent set is
level-triggered: suppressed while present, no busy loop` and `claiming the same
Work does not duplicate its wake` conflate two different rules: an unclaimed
offer must remain armed, while the transition to `claimed:true` is the
acknowledgement that suppresses it.

**Confirmed — dispatcher retention gap:** `EventBridge.enqueue` deduplicates an
event fingerprint only for `dedupWindowMs`. A claim-aware producer that retries
an unclaimed key cannot safely rely on that timer: a long model turn can outlive
the window, allowing the same action to be queued behind itself. The dispatcher
already retains queued and active event objects, so it can reject the same
v11 event id while that exact delivery is queued, starting, ambiguous, or
active. It must release that local delivery identity after a completed no-claim
turn so a later bounded retry can become a new turn.

**Confirmed — successful no-claim is presently invisible:**
`EventBridge.#settleTurn` returns immediately for `status === "completed"` and
performs no authority read. That is correct for failed-turn orphan detection,
but it means the producer/dispatcher pair has no acknowledgement channel other
than polling canonical `wait`. The correction does not need a new Baton
mutation or socket protocol: the producer can observe `claimed:true`, while the
dispatcher only needs exact in-flight identity retention so those polls cannot
queue duplicate turns.

**Confirmed — stale withdrawal remains sound:** both adapter paths already
revalidate the exact action key with `wait timeout=0` immediately before a
model turn. A missing key is authoritative withdrawal and must retire the local
offer. A different episode or accepted-configuration generation already has a
different key and is a new offer.

**Observed baseline:** before correction, `npm test` in
`tools/acp-baton-bridge` passed 55/55 tests, and
`node --test test/codex_baton_bridge.test.mjs test/stale_episode.test.mjs
test/failed_turn_settlement.test.mjs` in `tools/codex-event-bridge` passed all
three focused files. These are green baselines, not evidence that claim-based
acknowledgement exists; the conflicting assertions above explain why.

## Proposed implementation shape

This section is reviewer decision support. The confirmed ruling above is the
authority; the implementer must revalidate these mechanics against the current
tree before editing.

1. Replace Boolean delivered-key memory with per-action delivery state scoped
   by authority UUID, participant, and action key. Preserve the existing
   delivered-until-disappearance rule for obligations, trials, pokes, and
   runtime refreshes. Work actions additionally distinguish `pending`,
   `presented`, and `acknowledged`.
2. On every canonical snapshot, process Work state before selecting turns.
   `claimed:true` for a previously presented key acknowledges it. A claimed key
   first seen after adapter restart is delivered once so the existing claimed-
   Work recovery contract remains intact. A disappeared key retires all local
   state; a new episode or generation starts fresh.
3. Admit at most one unclaimed Work offer while the participant has no claimed
   Work. Retain every other unclaimed Work locally in canonical order. If any
   Work is `claimed:true`, admit no unclaimed Work; when that claim disappears,
   the first retained offer becomes eligible on the next poll. Non-Work actions
   keep their current relative order and delivery semantics.
4. A successful transport/prompt records `presented`, not `acknowledged`.
   Unchanged `claimed:false` schedules a retry with backoff; it does not clear
   the offer. Delivery failure remains an immediate retry input under the
   existing failure policy. Reset Work-offer backoff on claim-slot transition,
   disappearance, episode/generation change, or a newly selected head offer.
5. Use an injected clock/delay in focused tests. A suitable no-new-config
   default is exponential offer retry based on the existing `retryMs`, capped
   at 60 seconds. The exact cap is **Proposed**, not a protocol value; it must
   remain slow enough not to spend repeated model turns and fast enough that a
   corrected runner recovers without restart.
6. In the Codex dispatcher, deduplicate the exact v11 event id for the full
   queued/starting/ambiguous/active lifetime, independent of the generic
   fingerprint window. Release it after withdrawal or terminal settlement so
   a later producer retry of an unclaimed offer can be accepted. Do not weaken
   the existing stale-episode, ambiguous-start, overload, quarantine, or
   orphan-claim retention paths.
7. Keep `--once` as a transport smoke boundary, but document that acceptance of
   one event/prompt is not claim acknowledgement and does not certify the
   production retry loop.

## Focused regression matrix

- ACP: Work A is claimed and Work B is unclaimed in every poll; B receives no
  prompt until A disappears, then receives exactly one prompt without bridge
  restart.
- ACP: one unclaimed key completes a turn without claiming, remains suppressed
  before its retry deadline, and is prompted again after the deadline; changing
  the runner configuration between attempts proves restart-independent
  recovery.
- ACP: `claimed:false -> claimed:true` for the same key acknowledges the offer
  without a second prompt; a bridge starting on `claimed:true` still emits one
  recovery prompt.
- Both producers: two or more unclaimed Works yield only the canonical head
  offer until its claim slot outcome is known; obligations, trials, pokes, and
  refreshes beside them keep their existing behavior.
- Codex dispatcher: retries of one id during queued, active, ambiguous-start,
  overload, and orphan-fenced states cannot duplicate the queue or model turn;
  a completed no-claim attempt becomes eligible after producer backoff.
- Both adapters: blocked, rerouted, parked, closed, superseded, changed episode,
  changed generation, authority switch, and participant switch retire or renew
  state exactly as their canonical identities require.
- Preserve the current stale-episode, cross-Work fence, failed-turn settlement,
  quarantine, role-instruction, runtime-refresh, unknown-kind, `--once`, and
  transport-failure suites.

## Acceptance boundary

- Reproduce an unclaimed Work delivered while the participant holds another
  claim; after the held Work passes or closes, prove the original Work is
  offered and claimable without restarting any bridge.
- Reproduce a successful agent turn that cannot claim because its CLI/config
  is incompatible; after correcting the environment, prove the unchanged
  action key is offered again without restart.
- Prove a successful claim suppresses duplicate Work prompts while that claim
  remains live.
- Prove blocked, rerouted, parked, and terminal Work withdraw stale retained
  offers, and a genuinely new assignment episode is delivered normally.
- Bound retries so a persistent unclaimed level neither busy-loops the Baton
  CLI nor spends repeated model turns while the participant is known busy.
- Cover ACP and Codex-backed participants. Preserve existing stale-episode,
  cross-Work fence, quarantine, runtime-refresh, obligation, poke, and trial
  behavior.
- Update bridge documentation so `level-triggered` names the canonical
  claim-based clearing rule rather than transport delivery.

## Implementer revalidation and clarifications — 2026-08-25

Revalidated against the current tree before editing. The confirmed ruling of
2026-08-25 above holds unchanged and nothing in it is superseded: the reviewer
revalidation's confirmed facts still describe the code — `DeliveryMemory.sync`
had exactly two states, `runBridge` called `markDelivered` immediately after
`promptText` returned, `codexBatonBridge` recorded a key on socket acceptance,
`EventBridge.enqueue` deduplicated on a `dedupWindowMs` fingerprint only, and
`participant_actions` preserves the action key across a claim. The green
pre-change baselines were reproduced exactly: ACP 55/55, and the focused Codex
files reported by the reviewer.

Four points in **Proposed implementation shape** needed a decision the
proposal did not settle. Each is a clarification of that section, which is
decision support; none touches the confirmed ruling.

**Clarified — a backed-off head does not hold the queue.** Proposal item 3 and
the regression matrix say only the canonical unclaimed head is offered while
the claim slot is free. Read literally that starves everything behind a Work
nobody claims: the head retries forever under its own backoff and the second
offer is never reached. The matrix's own wording is what resolves it — the
head is exclusive *until its claim-slot outcome is known*, and a completed turn
followed by a poll that still reports `claimed:false` IS that outcome. So the
implemented rule is: in canonical order, admit the first unclaimed Work whose
retry deadline has arrived, and at most one per poll. A head still inside its
deadline is retained, not forgotten, and takes its next turn when the deadline
passes.

**Clarified — the dispatcher refusal has its own reason.** Proposal item 6 does
not name what `enqueue` answers when it is already holding the exact delivery.
Reusing `duplicate` would hide the distinction the item exists to draw, so the
refusal is `reason: "in-flight"`, and the producer treats it as neither a
failure nor an acknowledgement: the offer backs off and stands. The retention
is scoped to events carrying a v11 action key; a generic producer's event keeps
exactly its old `dedupWindowMs` rule.

**Clarified — the retry cap is adopted as proposed.** `MAX_OFFER_RETRY_MS` is
60 seconds, exponential from the deployment's own `retryMs`/`--retry-ms`. It is
a managed delivery policy exported by name, not a protocol value.

**Clarified — one implementation, imported by both families.** The claim-aware
level lives in `ReadinessOffers` in
`tools/codex-event-bridge/src/codex_baton_bridge.mjs` and is imported and
re-exported by `tools/acp-baton-bridge/src/baton_readiness.mjs`, following the
existing shared-envelope-validator boundary. The defect was identical on both
sides and a second copy is how the two would drift apart again.

**Observed — CLI poll cadence is unchanged.** The correction bounds MODEL
TURNS, not `wait` invocations. A retained offer inside its deadline leaves the
loop backing off on `retryMs` exactly as a fully suppressed set did before, so
no new load is placed on the Baton CLI and no existing backoff was weakened.

## Independent re-review — 2026-08-26

**Observed — the Codex pre-turn gate schedules from stale event state.** The
dispatcher correctly re-reads the canonical actionable set, but after finding
the exact key it tests the queued event's `action.claimed` field and applies
that test without regard to action kind. The event field is a historical bit
from producer time. If the same Work becomes claimed while queued, the current
claimed action is deferred behind its own claim instead of receiving its
recovery turn. An obligation carries no `claimed` bit, so it too is deferred
whenever any Work claim is present. The focused regressions at
`tools/codex-event-bridge/test/claim_slot.test.mjs` reproduce both outcomes.

**Confirmed — the authoritative matching action decides the pre-turn
verdict.** A missing exact key is `over`. A matching non-Work action remains
`live` under its existing delivery semantics. A matching claimed Work remains
`live` as its own recovery turn. Only a matching current unclaimed Work is
`deferred` while a claimed Work occupies the participant's slot. This is a
clarification of the already-confirmed claim-slot and non-Work boundaries, not
a new protocol rule; no action-key parsing is permitted or needed.

**Observed — ACP cannot distinguish withdrawal from claim-slot deferral at
its final authority read.** `episodeStillLive` returns only exact-key
membership and `runBridge` consumes one boolean: false permanently withdraws
the offer, while every truthy result starts the prompt. If another Work claims
the participant's slot between the outer poll and that immediate read, the
waiting Work remains in the projection and therefore spends a turn against an
occupied slot. The regression at
`tools/acp-baton-bridge/test/acp_baton_bridge.test.mjs` records the required
`deferred -> live -> prompt` behavior; the current bridge instead records
`deferred -> prompt -> live -> prompt`.

**Confirmed — ACP needs the same three-way final verdict.** Its immediate
authority read must distinguish `over`, `deferred`, and `live`; `deferred`
retains the exact unanswered offer without marking it presented or withdrawn,
then retries after the slot can change. The claim-slot rule applies only to
Work. This closes the cross-adapter race required by the finding's “Both
adapters” acceptance boundary.

## Independent third-review observation — 2026-08-26

**Observed, P1:** The Codex dispatcher still spends a Work turn when its
immediate claim-slot read fails or returns no actionable set. `#revalidate`
logs that the event is retained but returns `live`; `#drain` therefore starts
the turn and removes it from the queue without knowing whether another Work
claim occupies the participant's slot. ACP already fails closed on the same
read uncertainty by retaining the offer and retrying without a prompt.

**Confirmed:** A failed or malformed authority read proves neither withdrawal,
claim-slot deferral, nor liveness. Codex needs a distinct retain/retry outcome:
keep the exact event and its in-flight identity, spend no turn, and re-read the
authority on a bounded cadence. The earlier W1224 tests that call immediate
delivery “retention” are superseded for Work by the later confirmed one-claim
slot boundary.

The additive cross-boundary regression and full analysis are in
`review-2026-08-26T02-42-43Z.md`.

## Independent fourth-review observation — 2026-08-26

**Observed, P1:** The new `uncertain` verdict covers an invocation failure,
invalid JSON, and an absent actionable array, but the dispatcher does not
validate entries inside a present array before using their `kind` and
`claimed` fields to schedule. A current matching Work key mislabeled as the
known `obligation` kind is therefore classified as ordinary non-Work and
delivered immediately even while another current Work entry is claimed.

**Confirmed:** The immediate read must validate the canonical envelope fields
on which its verdict depends. A structurally contradictory matching entry is
neither proof that the Work is gone nor proof that it is safe to deliver; it is
`uncertain`, so the exact event remains queued and no turn is spent until a
valid read answers. This is the malformed-envelope case already required by
the third review, not a new protocol rule.

The additive regression and full analysis are in
`review-2026-08-26T03-43-47Z.md`.

## Independent fourth-review finding — 2026-08-26

**Observed, P1.** `EventBridge.#revalidate` found the current entry by
`action_key` and then treated every `matched.kind !== "work"` as `live`,
without applying the typed v11 envelope contract first. A malformed entry
carrying a Work key while claiming the `obligation` kind therefore bypassed an
occupied claim slot and started a turn. Analysis in
`review-2026-08-26T03-43-47Z.md`.

## Implementation decision — 2026-08-26: three consumers, one contract

**Every consumer of the participant projection types it before consuming any
field of it.** Both readiness producers have applied `validateEnvelope` to
exactly this command's output since W148, and the ACP bridge revalidates
through `waitOnce`, which validates. The Codex dispatcher read the same
envelope from the same binary and consumed `kind` and `claimed` untyped. It is
the same contract at the same boundary now, and **any validation failure takes
the bounded `uncertain` path** — a read that cannot be typed proves neither
that the episode still exists nor that the claim slot is free, which is the
existing definition of uncertain rather than a new one.

**Absent from what was KEPT is not the same as withdrawn.** The contract is
deliberately liberal about kinds this build does not know: it drops them from
`result.actionable` and files them under `result.ignored_actions` so a newer
authority can add a primitive without breaking an older bridge. That tolerance
is about DELIVERY — this build cannot act on a kind it has never heard of —
and says nothing about whether the episode is over. An entry carrying the
exact key is the authority still naming it, so its removal is `uncertain`, not
`over`. **In both bridges**: the ACP `episodeVerdict` reached the same defect
by a different route and the review did not name it.

**A fixture that abbreviates the envelope is not a fixture of this system.**
Four dispatcher suites scripted `wait timeout=0` as `{result:{actionable}}`,
which is a reply the real authority never emits, and which only an untyped
read could accept. That is why 403 green tests stood over this defect. They
carry canonical envelopes now, with each key expanded into the structured
locator the contract requires it to agree with — except the ones that are
unreadable on purpose, which still assert the uncertain path.

## Independent fifth-review observation — 2026-08-26

**Observed, P1:** Applying `validateEnvelope` does not yet prove the claim-slot
fact the dispatcher consumes. For a known Work action the validator rejects a
wrongly typed `claimed` value but permits the field to be absent. Both the
dispatcher and `episodeVerdict` then interpret absence through
`claimed === true` as unclaimed. A neighboring Work that was claimed but whose
claim verdict is missing therefore reports the slot free and authorizes the
queued Work's turn.

**Confirmed:** `participant_actions` always emits one Boolean `claimed` for
every Work action, and the new scheduler depends on that Boolean. It is no
longer an optional descriptive field: missing is structurally unreadable and
must make the whole revalidation result `uncertain`, just like a string value
does. The additive dispatcher regression and full analysis are in
`review-2026-08-26T04-38-41Z.md`.

## Independent sixth-review observation — 2026-08-26

**Observed, P1:** The fifth-review missing-claim-verdict defect is corrected in
the shared validator, but the Codex dispatcher applies the Work-only claim-slot
gate to the whole FIFO indirectly. `#drain` considers only `state.queue[0]`.
When that head is unclaimed Work B and current Work A is claimed, B is retained
as `deferred` and the drain returns. A later obligation queued behind B is
never examined, even though the confirmed ruling explicitly preserves
non-Work delivery beside a claim.

This can deadlock the managed lane: A remains the live claim, B waits for A's
claim to end, and a directed obligation needed by the same participant to
finish A waits behind B. ACP does not have this gap because its delivery loop
continues past a deferred Work and presents the later non-Work action.

**Confirmed:** retaining B and its in-flight identity is still required, but
that retained Work cannot be a FIFO barrier for obligations, trials or pokes
whose own current canonical action is live. The dispatcher must not let a
second unclaimed Work or an unrelated generic event bypass the gate, and must
preserve claimed-recovery promotion plus ambiguous/active retention.

The additive cross-boundary regression and full analysis are in
`review-2026-08-26T07-46-13Z.md`.

## Sixth-review correction and independent seventh-review observation — 2026-08-26

**Confirmed:** the sixth correction removes the Work-only FIFO barrier. The
dispatcher retains deferred Work B at the head while allowing a later action
whose current canonical verdict is `live` to pass. The positive obligation and
claimed-recovery cases pass, as do the negative second-unclaimed-Work and
generic-event cases.

**Observed, P1:** a passing action can now become ambiguous behind B. After a
non-protocol `turn/start` failure, the catch marks the passing candidate
ambiguous, but reconciliation still inspects only `state.queue[0]` and the
bypass scan skips every ambiguous candidate. Because B remains the head, a
passing obligation whose turn actually started is never found, dequeued or
bound.

**Confirmed:** ambiguity belongs to the attempted delivery, not to a queue
position. The exact behind-head candidate must be reconciled by client message
id before replay, while B remains retained. The additive regression and full
analysis are in `review-2026-08-26T07-57-08Z.md`.

## Independent eighth re-review — 2026-08-26

**Confirmed:** the seventh correction follows ambiguity by exact candidate in
both reconciliation paths. The previously measured connected path is sound,
and the ordinary-drain selection is also necessary after a transport drop: a
reconnect resume can miss the just-created turn once, leaving the passing
behind-head action ambiguous until the next direct thread read.

**Observed:** the additive terminating regression `a disconnected ambiguous
obligation behind a deferred Work is reconciled by the next drain` exercises
that exact ordering. It passes with the correction. In an isolated copy with
only the ordinary-drain selection reverted to `queue[0]`, it is the sole
focused failure: the ambiguous obligation remains queued behind B at depth two
instead of being reconciled to depth one.

**Confirmed:** the code correction is signed off. The live deploy and the two
operator smokes in acceptance remain separate pending operational work; this
review did not infer them from focused tests.

## Tuner deployment audit — 2026-08-27

**Observed:** The signed correction is committed in current `main` at `aa15287`, and the relevant ACP/Codex bridge paths have no working-tree diff. Fresh source gates pass: Codex event bridge 420/420 and ACP bridge 77/77.

**Observed:** The active `/home/sl/baton-v11.14aecfb` services all started on 2026-08-26 at 00:19 local time, before the final review signed off at 10:15. The Codex dispatcher and readiness producers import from the source checkout but have not restarted to load the signed-off bytes. The two ACP services execute the immutable `14aecfb` bridge, whose ACP and shared readiness-gate hashes differ from current signed source. No `aa15287` immutable distribution or matching deployment home exists.

**Confirmed operational boundary:** The official `deploy-v11` entry point packages the complete v11 authority, operator documents, and co-deployed ACP bridge. The present checkout contains unrelated uncommitted authority and documentation work, so publishing it would expand this signed-off bridge correction to unreviewed scope. The approver role owns Git and destructive deployment gates; it must select a clean reviewed commit, publish a new immutable release, cut the live home over, and restart the managed services before either live smoke can be meaningful.

**Pending acceptance evidence:** After that cutover, prove (1) an already-pending Work offer is delivered when the participant's live claim slot frees, without a bridge restart, and (2) an unchanged no-claim action is retried after runner-environment repair. No live-smoke result is claimed from the pre-correction processes.

## Deployment cutover and live-smoke baseline — 2026-08-28

**Observed:** The approver deployed immutable release `dd1dc3e`. At
2026-08-28T05:15:10Z the live Codex dispatcher (PID 2755516), reviewer and
tuner readiness producers (PIDs 2755905 and 2756009), and ACP bridge (PID
2756087) all still had their original 2026-08-28T04:28Z start times. Their
configured Baton operands name the `dd1dc3e` executable and the explicit
`/home/sl/baton-v11.14aecfb/baton.json` authority.

**Observed — claim-slot smoke precondition:** W26291 was claimed by
`baton.claude` at 2026-08-28T04:49:56Z. W28681 became ready, queued and
unclaimed for the same participant at 2026-08-28T04:52:52Z, after that claim
slot was occupied. The live ACP bridge remained PID 2756087 and did not spend
a turn on W28681 while W26291 held the slot.

**Pending:** This baseline is not the smoke result. Acceptance still requires
W28681 (or another Work proved pending during the same held claim) to be
delivered after the slot frees with PID 2756087 unchanged, plus a separately
observed unchanged no-claim action retry after runner-environment repair with
its bridge process unchanged.

**Observed at handoff:** At 2026-08-28T05:39:44Z W26291 still held the claim,
W28681 remained the same queued, ready, unclaimed episode 28975, and ACP PID
2756087 retained its 2026-08-28T04:28:10Z start time. This proves the candidate
was not incorrectly delivered into the occupied slot, but the slot had not
yet released, so the after-release half remains pending.

**Confirmed operational boundary:** Manufacturing the second smoke requires a
managed runner to complete a turn without claiming because its Baton CLI or
config is incompatible, then repairing that runner environment while the
action key and bridge process remain unchanged. The deployed launcher is
currently compatible. Tuner authority does not include replacing or
misconfiguring the installed executable, authority config, or managed runner
to create the failure. That operator-controlled setup must be supplied; an
old generation, changed action, or deliberately disobedient model turn is not
equivalent acceptance evidence.

## Approver closure ruling — 2026-08-28

The approver accepts terminal closure without manufacturing or waiting for the
two pending live-smoke opportunities. The correction has independent code
sign-off, complete focused bridge gates, and deployment in immutable release
`dd1dc3e`; the claim-slot precondition also records that the deployed bridge
retained W28681 while W26291 occupied the participant's claim slot.

This ruling does **not** relabel either live smoke as passed. The after-release
delivery and unchanged-action no-claim retry remain unobserved. A naturally
occurring opportunity may append explicit post-closure evidence to this
permanent record, but it is no longer a gate on W11910's satisfying outcome.
