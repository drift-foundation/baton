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
handler, records the destination phase — `queued` when the Work is runnable,
`block` when a gate holds it,
and stores `comment` as durable handoff evidence. It creates no message and
moves no conversational count. You cannot supply `phase=` — it is refused as
unknown — so a handoff can never advertise a stage nobody is in.

Review may send the same Work straight back for another round. That is
ordinary, not a failure state — and it lands `queued`, because the recipient
has not started yet:

    $BATON pass work=W2 to=app.bug set-next=app.rview \
        comment="fix is right but the regression only covers the quoted form"
    # -> destination_phase: active

`set-next` records the planned return destination. **Next neither transfers nor
claims anything** — it is a plan, and the route is still the only thing that
owes a decision.

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
- **A dependency edge** does not rewrite phase at all. Blocked Work keeps its
  honest stage, reports `ready: false`, and refuses claims:

      W23 has 1 unmet dependency/child gate(s); blocked work cannot be
      claimed — readiness is decided here, in the write transaction

Waiting and parked Work cannot be claimed either — suspending already released
the claim:

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
a compare-and-swap against the recorded claimant:

    baton --participant app.ops release work=W76 expect=app.mina \
        reason="runner died mid-turn; no heartbeat for 40 minutes and the
                operator confirmed the host is gone"
    # -> {"released_claimant": "app.mina"}

A wrong guess refuses rather than guessing for you:

    W76 is claimed by app.mina, not app.juno; the compare-and-swap refuses —
    recovery never guesses whose execution it is interrupting

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
