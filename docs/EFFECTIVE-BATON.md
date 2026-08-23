# Using Baton effectively

This is the practical operating guide for working inside a Baton
**protocol-11** coordination authority. It assumes you can already run the
executable; [BATON-SETUP.md](BATON-SETUP.md) covers creating a home and
[BATON-WORK.md](BATON-WORK.md) is the exhaustive operator contract. When this
guide and those documents disagree, they are the authority — this one explains
how a participant works *safely*, and why each step matters.

Protocol 10's directed messages, notices, `send`/`reply`, and message claims
are retired. They are not a fallback, and nothing here degrades to them.

Every command and every quoted result below was executed against the release
candidate that ships this guide, in a throwaway coordination home. Where an
error message appears, it is the real refusal text.

## The one-paragraph model

**Work** is the unit of accountability. It has one owning team, one **Route**
endpoint whose handlers owe the next decision, a **phase** that says what stage
it is in, and a **Handler** — the participant executing it right now, null
while nobody holds the claim. Route and Handler are different questions and
Baton keeps them separate: who MAY act, and who IS acting.

Phase is a closed SCHEDULER axis: `queued` (runnable, unclaimed), `active`
(claimed), `block` (one named gate is holding it), `parked` (deliberately
deferred), and nothing at all once the Work is closed. It never says what KIND of work this is —
that is the route's role. Discussion
happens in **Threads** and **Messages**; what actually happened to the Work is
its append-only **Events** journal. Nothing is inferred from your working
directory, your shell history, or a wake-up prompt.

## Setup you only do once

    mkdir -p ~/coord
    baton init directory=~/coord          # scaffolds baton.json; creates no database
    $EDITOR ~/coord/baton.json            # teams, roles, routes, kinds, roots
    baton --participant app.ops activate directory=~/coord

`init` refuses a directory that does not exist — it writes only into one you
chose deliberately. `activate` is the single authoritative validation: it
creates the SQLite authority only if the document passes, and a refusal leaves
nothing behind, so edit and retry freely. Refusals are specific:

    route handle 'research' is 8 display cells; the limit is 6.
    Shorten the canonical handle and put the long form in the display name.

Thereafter every invocation names the config and your identity explicitly:

    BATON="baton --config ~/coord/baton.json --participant app.mina"

There is no ambient configuration, no actor, and no seed. The participant
address **is** the identity, and filesystem access to the instance is the trust
boundary. This is cooperative coordination between trusted agents, not
application-level authentication.

### How an endpoint resolves

Configuration composes in one direction, and it is worth reading once:

    kind      ->  route   ->  role + handlers
    app.bug   ->  impl    ->  impl,  [mina, ops]
    app.rview ->  rview   ->  rview, [juno]

An **endpoint** is `team.kind`. Each kind names a **route**; each route
carries a **role** and a handler list. The chain ends there: the role says
what KIND of work this endpoint does, and it says nothing about phase.

Phase is a separate axis entirely, and it answers only two questions — can
this run, and is it running:

    queued   runnable, nobody has claimed it
    active   a handler holds it, so somebody is executing it
    block    one displayed gate is holding it — another Work, or a
             directed Message obligation
    parked   deliberately deferred, with a reason
    (terminal Work has no phase at all)

A handoff lands `queued` when the Work is runnable and `block` when a gate
holds it, whatever the destination role — which is why you never supply a
destination phase by hand.

The Work's `route` is that endpoint — eligibility. Its `handler` is the exact
participant who claimed it, or null. Authorization always resolves from the
route, never from a handler's name, so a routed handoff nobody has picked up
projects `handler: null` and phase `queued` rather than pretending somebody is
on it.

## Basic command quick reference

These are independent lookup forms, not one workflow to run in order. Replace
the sample Work and Thread ids with the ones from your authority. `$BATON`
keeps the explicit config and participant identity established above.

    $BATON home
    $BATON detail work=W2
    $BATON create team=app kind=bug title="escape handling fails" \
        origin=external-report classification=suspected-defect \
        body="reproduces on every checkout"
    $BATON claim work=W2
    $BATON say thread=T2 body="the tokenizer drops the destination"
    $BATON say thread=T2 body="please confirm the expected escape" \
        request=app.rview on=W2
    $BATON pass work=W2 to=app.rview \
        comment="fix and regression are ready for review"
    $BATON close work=W2 outcome=satisfying \
        rationale="reviewed fix and regression both pass"
    $BATON release work=W2 expect=app.mina episode=41 \
        reason="the original runner cannot continue"
    $BATON dispatch
    $BATON drain reason="host kernel upgrade"
    $BATON resume reason="upgrade complete"

**Protocol 11 uses `say`, not retired `send`.** A plain `say` discusses the
Work; adding `request=` and `on=` creates one directed obligation. `pass` is a
threadless Work handoff, not a message.

The three obligation dispositions are `respond`, `dispose`, and `accept`; see
[Cross-team work: providers and consumers](#cross-team-work-providers-and-consumers)
for the detailed choice and forms. The CLI help is the authoritative operand
grammar:

    baton --help
    baton --help VERB

## The straight-through path

Most Work never needs anything cleverer than this.

    $BATON create team=app kind=bug \
        title="nested escapes drop the destination" \
        origin=external-report classification=suspected-defect \
        body="reproduces on every consumer checkout"
    # -> {"work_id": "…-W2", "thread": "…-T2", "seq": 2}

Creation mints the Work and its born Thread in one act. `classification=` is
required and `unknown` is refused: say what you actually think it is, and
`classify` later when you know more.

    $BATON claim work=W2
    # -> {"claimant": "app.mina", "seq": 3}

**Claim before you execute**, because only a successful claim populates the
handler. Not before you read, discuss, or plan — before
you *do* the thing the route owns — and claiming is what makes the Work
`active`, because active means somebody is doing it. The claim is atomic and rechecked inside the
write transaction, so an earlier readiness observation is advisory and a
competing claim fails closed:

    W2 is already claimed by app.mina; conflicting claim attempts fail closed
    (an exact retry replays through its operation id)

Note what claiming *does*: the phase becomes `active` in the same
transaction. Handler and phase are one fact seen twice — `active` means
exactly that a handler holds it — so there is no window where the board shows
work in progress that nobody is doing.

Classification is a separate axis and moves freely while you hold it:

    $BATON classify work=W2 as=confirmed-defect

The route already says whether this is research, implementation or review,
so there is no stage to move. Then hand it on:

    $BATON pass work=W2 to=app.rview \
        comment="reproduced; escape handling confirmed at the tokenizer"
    # -> {"to": "app.rview", "destination_phase": "queued"}

`pass` is one atomic **threadless** event. It moves the route, clears the
handler, records the destination phase, and stores `comment` as durable handoff
evidence. It creates no message and moves no conversational count. You cannot
supply `phase=` — it is refused as unknown — so a handoff can never advertise a
stage nobody is in.

**Only the current claimant passes.** A pass hands on what you hold and
releases the claim in the same act, so there is nothing to hand on until you
hold it. Route eligibility says who MAY claim; it is not a licence to pass Work
you are not doing:

    W2 is unclaimed; a pass is the current claimant's handoff and releases the
    claim it holds — claim it first if you are executing it, or reroute it on
    the owning team's authority to move it unclaimed

This is not ceremony. An eligible handler who could pass without claiming could
review a Work, run its gate and hand it on having never been its Handler —
canonical state saying nobody worked on it while the runtime log and the
filesystem said otherwise. That happened, and it is why the rule exists.

Blocked and parked Work is unclaimed AND unclaimable, so it cannot be passed at
all; the refusal names the phase and points at `reroute`. Moving Work nobody
holds is what [`reroute`](#reroute-moves-work-nobody-holds) is for.

Review may send the same Work straight back for another round. That is
ordinary, not a failure state — and it lands `queued`, because the recipient
has not started yet:

    $BATON pass work=W2 to=app.bug set-next=app.rview \
        comment="fix is right but the regression only covers the quoted form"
    # -> destination_phase: active

`set-next` records the planned return destination. **Next neither transfers nor
claims anything** — it is a plan, and the route is still the only thing that
owes a decision.

### Reroute moves Work nobody holds

`pass` and `reroute` are not two spellings of the same act. A pass is the
claimant's handoff; a reroute is the owning team correcting where UNCLAIMED
Work is offered, and it takes the owning team's authority rather than the
resolved route handler's:

    $BATON reroute work=W2 to=app.impl route=impl2 \
        reason="the default route's runner is not taking it"
    # -> {"to": "app.impl", "route": "impl2", "phase": "queued"}

Reach for it when nobody owes the Work yet: a queue sitting at the wrong
endpoint, an alternate whose agent is offline, or Work whose gate or park makes
it unclaimable. Requiring a pass there would mean waking the very runner you
are routing around — which strands the Work exactly when moving it matters.

**It corrects WHERE, never whether the Work may run.** The scheduler phase
comes out the way it went in: a gated Work stays `block` with its wake
condition, and a parked Work stays parked with the reason somebody recorded
for deferring it. Route and phase answer separate questions, so correcting one
does not get to decide the other, and a deferred Work resumes only through the
explicit `phase to=queued` — at its corrected route:

    $BATON reroute work=W9 to=app.rview reason="review owns this queue now"
    # -> {"to": "app.rview", "phase": "parked"}   still deferred, now theirs

It refuses claimed Work, and the race is decided under the write lock: a claim
that commits first makes the reroute refuse, and a reroute that commits first
is simply the state the claim then re-reads. Neither leaves a half-move behind.
Do not fake a claim to redirect a queue; that is what this operation is.

### Say it in the discussion before you hand it over

The pass comment is durable, authoritative, and **not a message**. It lives in
the Work's Events journal, where the transfer itself is audited. That is the
right home for it — a workflow transition must not inflate a discussion count
or make somebody choose a thread — and it has one consequence worth planning
for: an operator reading Messages will not see it.

So when continuity through the discussion matters, post the recap first and
then hand over:

    $BATON say thread=T2 body="tokenizer escape handling is fixed and both
        forms are regression-covered. Left alone deliberately: the reader's
        narrow-width wrapping, which is W48's and not this Work's. Next: a
        review round on the two new cases."
    $BATON pass work=W2 to=app.rview comment="fix and regressions ready for review"

Two records, each doing its own job: the message carries the reasoning to
whoever is reading the conversation, and the pass carries the authoritative
transfer.

**Handing Work to a human reviewer or approver, the message is not optional.**
Before the pass, leave one concise discussion Message that states

- the result or current status,
- the decision or action now expected from the human, and
- the recommended next step.

A human must not have to reconstruct that instruction from a series of Work
Events. Synthesising the journal into a clear handoff is the agent's job, and
it is the whole difference between "here is a Work id" and "here is what I
need from you". The `pass` that follows is still the authoritative transfer;
Events still hold the complete audit.

Baton requires the pass comment to be non-empty and cannot judge whether prose
is a sufficient recap. This is an operating convention, kept because it works,
not a rule the authority enforces.

    $BATON close work=W2 outcome=satisfying \
        rationale="escape handling fixed and both forms regression-covered"

Every close names exactly one outcome — `satisfying`, `non-satisfying`,
`rejected`, or `cancelled` — and a non-empty rationale. **Closed Work never
reopens:**

    W2 is closed; a closed work refuses phase changes

If later evidence contradicts a closed decision, that is new linked follow-up
Work, not a reopening.

## Saying why something is not moving

Phase must tell the truth. Three states mean genuinely different things, and
conflating them is the most common way a board becomes fiction.

- **`block`** — held by ONE displayed gate, and the row names it: `W…` for a
  blocking Work, `M…` for the source Message of a directed obligation. The
  `gate` field carries the kind, the locator, and the instant that gate became
  the one holding the Work — which is what the Held timer measures. Requires
  `wait=` when you set it by hand.
- **`parked`** — an explicit, un-gated deferral. Requires `reason=`. It stays a
  visible loose end; it is not a quiet grave.
- **A dependency edge MOVES the phase.** A gate arriving puts the Work in
  `block` and releases its Handler in the same transaction — an unmet gate
  invalidates execution, so the claim cannot survive it. The row then reports
  `ready: false` and refuses claims:

      W23 has 1 unmet dependency gate(s); blocked work cannot be
      claimed — readiness is decided here, in the write transaction

`block` is not a flag beside some other stage; it IS the phase such Work is
in. Blocked and parked Work cannot be claimed at all, and cannot be passed
either — a pass is the claimant's handoff and there is no claimant:

    W13 is blocked; blocked and parked work cannot be claimed

## Discussion, attention, and directed requests

Threads carry prose. Events carry acts. Keep them separate and both stay
readable.

**`include=` is attention only.** It fans a message out to endpoints who owe
nothing:

    $BATON say thread=T13 body="heads up, this will touch the shared lexer" \
        include=lib.bug
    # -> {"kind": "post_message", "included": ["lib.bug"]}

The recipient's obligation list stays empty and no phase moves. Include takes
*endpoint* selectors, not participant addresses; a selector matching nothing is
refused at tag time rather than discovered later.

**`request=` creates exactly one obligation**, and by default it blocks:

    $BATON say thread=T13 body="lib: can the lexer expose spans?" \
        request=lib.bug on=W13
    # -> {"kind": "request", "work": "…-W13", "wait": true}

In one transaction that publishes the message, creates the obligation owed by
`lib.bug`, moves your Work to `block` on that exact obligation, displayed as `M<seq>`, and
releases your claim.

Two facts move differently here, and the difference is the point. **The route
does not move** — your Work still belongs to the same eligible endpoint, and
the answer is owed *to* that endpoint rather than instead of it. **The handler
clears**, because entering the wait releases your claim: nobody is executing
Work that is blocked on somebody else's answer, and the phase says `block`
rather than pretending otherwise.

Because a blocking request suspends the Work *you* are executing, you must
actually be executing it:

    a blocking request suspends W16, which is unclaimed;
    claim it first or send the request with wait=false

    W16 is claimed by app.mina; a blocking request suspends the work its own
    executor is doing, never somebody else's

When the answer lands, the Work returns to the phase it left:

    $BATON say ... # as lib.rai:
    baton --participant lib.rai respond obligation=17 \
        body="yes — spans are already tracked internally; exposing them is additive"
    # W13: phase block -> queued, gate -> null

Use `wait=false` when you genuinely can proceed meanwhile. It is a deliberate
statement, not a convenience:

    $BATON say thread=T13 body="lib: confirm the span type when you can" \
        request=lib.bug on=W13 wait=false
    # -> {"wait": false}   — phase untouched, claim retained

The result always reports which form committed, so you never have to read
Events back to find out. A plain message with no request omits the key
entirely rather than inventing a choice:

    {"seq": 21, "kind": "post_message", "included": []}   # no "wait" key

An obligation is answered with `respond`, `dispose` (no answer is owed, with a
reason), or `accept`. Somebody else contributing to the thread does not
silently discharge it.

## Cross-team work: providers and consumers

When a request turns out to be somebody else's deliverable, the receiving
endpoint **accepts** it — creating the provider Work and the dependency edge in
one transaction:

    baton --participant lib.rai accept obligation=25 \
        body="agreed — this is ours; opening the chunked writer" \
        create=true kind=feat classification=design-choice \
        title="chunked writer for large payloads"
    # -> {"created": true, "provider": "…-W26", "work": "…-W23",
    #     "edge": {"work": "…-W23", "blocker": "…-W26", "via_obligation": 25}}

Read that result carefully: `work` is the **consumer**, `provider` is the newly
created **provider**. Use `into=` instead of `create=true` to gate on provider
Work that already exists — one provider may gate many consumers.

The consumer's obligation wait is now resolved, but it is not ready, because
the dependency replaced it. The two lanes are independent from here: the
provider team claims, implements, reviews, and closes its own Work on its own
schedule. When it closes, the gate ends — and that is *all* it does:

    # provider closed satisfying -> consumer: ready true, blocked_by [(W26, closed)]

**Closing a provider never decides or closes a consumer.** The consumer team
claims its own Work and reaches its own conclusion. If a gate turns out to be
wrong, `unblock work= on= rationale=` corrects the live edge without closing or
rewriting either Work, and Events preserve both acts.

## Containment versus dependency

Parent/child containment organizes a deliverable; it is not an execution
dependency. A parent may proceed while children are open, but it cannot close
while any remain:

    W71 has open children (W75); root closure while required descendants
    remain open is refused

"May proceed" is the whole of it, and it is worth being exact about: an open
child does not touch its parent's readiness, phase, Handler or displayed gate.
Attaching a child to Work somebody is executing leaves them executing it, and
closing the last child neither wakes the parent nor mints it a new assignment
episode, because the parent was runnable throughout. A parent that cannot run
is blocked by a dependency or an obligation — never by its own decomposition.
Containment shows up in the tree, in the roll-ups, in the closure refusal
above, and in the union-graph cycle check; it never shows up in `Wait`.

Dependency edges are separate, explicit, many-to-many, and independently
reviewable. Each one carries a durable rationale:

    $BATON block work=W23 on=W26 rationale="export cannot stream without the chunked writer"

Use a child when the requirement is *separately accountable*. Use a dependency
when this Work simply cannot finish first.

## Changing the contract of assigned Work

Discussion may refine what assigned Work means, but outsiders **propose** —
they do not edit scope underneath the person doing the work. Promotion is a
compare-and-swap performed by the **exact current claimant**, who must also
still be eligible through the live route:

    $BATON revise work=W71 message=73 expect=0 \
        rationale="agreed in discussion; backoff belongs in the same contract"
    # -> {"revision": 1}

Being *eligible* is not enough. A route peer who holds no claim may argue in
the thread all day, but cannot rewrite the contract of Work somebody else is
executing:

    revise: W71 is claimed by app.mina; a route peer may propose in the
    thread but never rewrites assigned scope underneath its executor

Unclaimed Work refuses too — promotion waits for somebody to be accountable
for it. Losing the claim ends the authority immediately, so a pass, a release,
or a forced recovery all take it away mid-flight.

The message stays the durable contract text; the revision records who promoted
it and why. A stale expectation refuses rather than clobbering:

    W71 is at revision 1, not 0; the edit is stale — re-read and retry
    against the current state

If the new requirement is separately accountable, create child Work instead.
The test is whether it deserves its own close.

## Verification trials

A reviewer may put one **immutable candidate** in front of exact verifier
endpoints:

    baton --participant app.juno try work=W51 \
        candidate=build-2026.08.18-a assign=app.bug assign=lib.bug
    # -> {"trial": 1, "assignments": [56, 57]}

Verifiers file a raw observation and where the evidence lives; the reviewer
files a separate assessment. These are two immutable axes and both are audited:

    baton --participant app.mina report obligation=56 observation=failed \
        evidence=product:work/records/2026/08/finding-clock-drift/trial-1-app.md
    baton --participant app.juno assess obligation=56 as=accepted \
        rationale="reproduced above 5k/sec"

Observations are `passed`, `failed`, or `unable`. Assessments are `accepted`,
`rejected`, or `inconclusive` — a reviewer may accept a *failure* report, which
is exactly what happened above. **Counts and elapsed time never decide
anything.** A trial with every report in and every one assessed still sits
`open` until a human acts.

Opening a new trial supersedes the previous one rather than refusing, and the
superseded trial and all its evidence remain in the record:

    trials: [(1, "superseded", "build-…-a"), (2, "closed", "build-…-b")]

`extend` moves an open trial's review instant; `abandon` ends one unresolved
with a reason. Both are separate audited acts.

## Readiness

`wait` is a **read-only, participant-relative** projection. It claims nothing
and writes nothing:

    $BATON wait timeout=30
    # -> {"timed_out": false, "actionable": [
    #      {"kind": "work", "work": "…-W16", "local_id": "W16",
    #       "action_key": "work:…-W16:16:g2", "claimed": false,
    #       "episode_seq": 16, "config_generation": 2, "phase": "queued"}]}

It returns open ready **unclaimed** Work whose route resolves to you, Work
**you have already claimed** so you can continue after a restart,
pending obligations your endpoint owes, and due trials you answer for. That
second category matters: a runner that only looks for unclaimed Work walks past
its own unfinished assignment.

`action_key` is an **assignment episode** — Work id, episode sequence, and
accepted config generation. Work handed away and handed back between two polls
is a new episode even though nothing observed it absent. Key delivery on the
whole string; never parse it to recover the Work id, which rides beside it as
its own field.

A readiness line is an **edge to re-evaluate, not authority to act.** By the
time you see it the Work may have been claimed, passed, or closed. Re-read
canonical state, and let the atomic claim be the final arbiter.

`timeout=` is your deadline and nothing else. While the wait is empty it
re-derives the projection about **once a second**, so something committed
while you are blocked reaches you within roughly a second rather than
instantly — coordination happens on seconds-to-minutes timescales, and a
poll per participant twenty times a second bought latency nobody could
perceive at a cost the database could. The interval never extends your
deadline: `timeout=0` is a single read, and a shorter timeout returns when
you asked, not at the next interval.

`include=`, plain posts, and personal New are attention, never wakeups. A
sender who needs action uses a request or passes the baton.

External Codex/ACP adapters may wake a model runner, but they are outside the
protocol: they never claim, answer, or complete Work for you. Recover your
context from `wait`, `detail`, Messages, Events, and the bound dossier — not
from the wake prompt's prose.

**Never end a turn holding Work you have claimed and neither progressed nor
handed back.** The teeth are on `claim`, not on `wait`: Work held by a process
whose turn ended is stranded — invisible to its sender and blocking the queue
until somebody recovers it explicitly.

## Recovery

Baton never auto-releases, transfers, or admits a second claimant on staleness.
`heartbeat work=` is liveness evidence only; an agent mid-turn cannot beat, so
silence is never treated as failure. Recovery is therefore explicit, and it is
a compare-and-swap against **both** the recorded claimant and the exact
assignment episode that claim was offered under:

    baton --participant app.ops release work=W76 expect=app.mina episode=41 \
        reason="runner died mid-turn; no heartbeat for 40 minutes and the
                operator confirmed the host is gone"
    # -> {"released_claimant": "app.mina", "episode": 41,
    #     "authorization": "handler"}

A wrong guess refuses rather than guessing for you:

    W76 is claimed by app.mina, not app.juno; the compare-and-swap refuses —
    recovery never guesses whose execution it is interrupting

`episode=` is mandatory on every release, self-release included, and `detail
work=` publishes it as `episode_seq`. The claimant alone is not a fence: a
participant that released and re-took the same Work is still `app.mina`, so a
recovery request written against the first claim would silently abort the
second. Claiming deliberately does not mint an episode and every release, pass
and re-offer does, so the episode names one assignment and no successor to it:

    W76 is claimed under assignment episode 58, not 41; the compare-and-swap
    refuses — a release aimed at one assignment never ends a later one, even
    when the same participant holds both

That also makes recovery single-use. A dispatcher retrying a stale
failed-turn settlement, or an operator re-running a command from scrollback,
refuses instead of releasing whatever claim happens to be live.

### When the route's only handler is the one that died

Ordinary release authority is the Work's live Route endpoint, which covers
self-release and one handler recovering another. It does not cover the case
this exists for: a managed turn that failed one second after claiming, on a
route whose only handler is that same failed participant. There is then no
resolved handler left to recover it, and the participant's one claim slot
deadlocks — for five hours, in the incident that produced this rule.

So a member of the Work's **owning team** may instead hold the `recover`
capability:

    "participants": {
      "ops": { "display": "Ops", "roles": ["dev"],
               "capabilities": ["recover"] }
    }

    baton --participant app.ops release work=W76 expect=app.mina episode=41 \
        reason="the managed turn failed holding this claim"
    # -> {"released_claimant": "app.mina", "episode": 41,
    #     "authorization": "recover"}

`recover` is deliberately narrow and deliberately separate. It is not `config`,
which rewrites who may act on everything; it is not route membership, which
would make the recovery operator a normal executor of every Work that endpoint
owes; and it is never derived from a runner's `actionOwner`, which is
participant-authored telemetry and grants no workflow authority at all. It is
also still bounded by ownership — a capability says what kind of act you may
perform, not whose work is yours. The `authorization` field records which
branch a release went through, because "a handler released its own claim" and
"an operator recovered somebody else's" are different operational events.

Without either, the refusal names both paths:

    release: app.juno is neither a resolved handler of app.bug (route 'main',
    handlers ['mina']) nor a member of app holding the `recover` capability;
    recovering a claim its own route handlers cannot reach is a configured
    operator capability, and contribution never grants it

Releasing does **not** stop the external agent that may still be running.
Coordinate with its operator before forcing one.

### Retry safely

Mutating verbs take `op-id=`. An exact retry replays the one committed result;
any mismatch fails closed without mutating:

    $BATON claim work=W76 op-id=recover-1     # -> committed
    $BATON claim work=W76 op-id=recover-1     # -> replayed, byte-identical
    $BATON phase work=W76 to=parked reason=a op-id=recover-1
    # op-id 'recover-1' was already used by app.ops for a different request;
    # conflicting reuse refuses without mutation

The comparison uses the **effective** operands, so a retry may spell a default
explicitly but may not change it. An interrupted operation is retried through
the public API. Authority state is never reconstructed by hand — and
`home`, `tree`, `detail`, `thread`, `work-events`, `events`, `links`, and
`search` are the read-only views. **If a question about coordination can only
be answered by opening the SQLite file, that inability is the finding.**

## Maintenance: draining managed dispatch

A running deployment keeps the pipeline saturated. The moment one handler
relinquishes a claim, readiness offers the next eligible Work to whoever can
take it — which is correct in ordinary operation and leaves no deterministic
moment to restart the stack. An operator waiting for "the current item to
finish" can miss the gap repeatedly, because somebody else has already
started the next one.

`drain` draws the boundary explicitly:

    $BATON drain reason="host kernel upgrade"
    # -> {"mode": "draining", "generation": 7, "boundary_seq": 4711,
    #     "live_claims": 2, "blockers": ["app.mina holds W76", ...]}

Claims live at that instant finish normally — their holders may pass, close,
release, or otherwise end them exactly as before. Nothing later is admitted:
a new claim refuses in the write transaction, whichever route it arrives by.

    W12 cannot be claimed: managed dispatch is draining; no new claim is
    admitted until an authorized `resume`

When the last live claim ends, the deployment reaches `paused` in the same
authority instant as the act that ended it. Ask at any time:

    $BATON dispatch
    # -> {"mode": "draining", "generation": 7, "blocking_claims": 1,
    #     "blockers": [{"work": "W76", "handler": "app.mina",
    #                   "episode_seq": 58, ...}], ...}

**A drain never cancels anything.** A failed or orphaned claim stays a
visible blocker with its exact identity rather than being force-released, and
a runner reporting `failed` does not retire it — recovery is the separate,
audited `release` above. If the deployment will not reach `paused`, the
blocker list names precisely who to talk to.

Resume is explicit, and only explicit — restarting the services does not
resume:

    $BATON resume reason="upgrade complete"

**Who may.** `drain` and `resume` require the accepted-configuration
`dispatch` capability, granted in `baton.json` and separate from every other
authority: a Route or a held role is local scheduling responsibility, a
runtime action owner is transient adapter state, `recover` releases one
orphaned claim, and `config` authors the roster. Reading `dispatch` requires
nothing — a participant that cannot tell why it is not being woken would have
to guess.

**What a managed agent sees.** While draining, managed readiness delivers a
participant only the Work it already holds; while paused, nothing that would
spend a turn. The answer is immediate and says why, so a drained deployment
never looks like an idle one. Obligations, pokes and unclaimed Work stay
visible in `home` and `inbox` throughout — drain suppresses model wakes, not
your view of the board.

**With the lifecycle manager.** A version-2 `infra.json` names one canonical
control identity, and then:

    tools/infra.py drain   MAILBOX --reason "host kernel upgrade"
    tools/infra.py dispatch MAILBOX          # mode, generation, blockers
    tools/infra.py stop-drained MAILBOX      # refuses unless paused
    tools/infra.py stop    MAILBOX           # immediate; unchanged

`stop-drained` reads the canonical state and refuses **before signalling any
service** unless the deployment is paused, so a refused graceful stop leaves
everything exactly as it found it. Plain `stop` is unchanged and remains the
immediate one — it must keep working when the authority cannot be reached at
all, which is when you need it most. `dispatch` answers even with every
service stopped, because "the stack is down" and "the deployment is paused"
are different facts.

## Evidence lives in the repository

Baton holds what is true *now*; the dossier holds *how it got that way*.
Neither substitutes for the other, and a ruling that exists only in a
discussion thread is one context loss away from being re-litigated.

Work binds through a configured root to a canonical record path:

    $BATON bind work=W76 root=product \
        path=work/records/2026/08/finding-handle-leak expect=0 \
        rationale="canonical record for the descriptor leak"
    $BATON resolve locator=W76
    # -> {"root": "product", "absolute": "/tmp/repo/work/records/2026/08/finding-handle-leak"}

Bindings are compare-and-swap with append-only history. Never bind to
`work/open`, a checkout-absolute path, or a remembered commit — those are not
portable across the participants who must read them.

Inside a dossier the roles are fixed, and they exist so two participants can
write concurrently without fighting:

- `FINDING.md` — confirmed decisions and the acceptance boundary.
- `PLAN.md` — actionable state, kept truthful as steps land.
- `PROGRESS.md` — **implementer-owned**, one writer.
- `review-*.md` — append-only review evidence. Corrections append a dated
  marker; they never rewrite what a reviewer already said.

## Configuration changes

A proposed generation is inert until an authorized participant accepts it:

    # edit baton.json, bump "generation"
    baton --participant app.nia home
    # baton.json is edited but not accepted: its digest is bd47381e5f4d…
    # and the accepted configuration is 10c3dd72606b…

    baton --participant app.mina regen
    # app.mina does not hold the config capability in the currently accepted
    # generation 1; a proposal cannot authorize its own acceptor

    baton --participant app.ops regen
    # -> {"generation": 2, "changes": {"added": ["member:app.nia"],
    #     "rerouted": ["app.impl"]}, "digest": "bd47381e5f4d…"}

The acceptor is authorized by the **currently accepted** generation, so an
edit cannot grant itself the capability to be accepted.

## The short version

1. Read canonical state before acting; a wake line is a hint, not authority.
2. Claim before you execute. Never hold a claim you are not progressing.
3. Let phase tell the truth — `block` names its gate, `parked` names its
   reason.
4. Pass with real handoff evidence; the route decides the phase.
5. Ask with a directed request, and let it block when you honestly cannot
   proceed.
6. Close with one outcome and a rationale that will still make sense in a year.
7. Put the reasoning in the dossier, because the authority only remembers what
   is true now.
