# Baton agent coordination protocol — v11

An agent coordination channel running **Baton protocol 11** has one SQLite
transactional authority per instance, no filename-state, and is defined
entirely by an explicit config. Consult `BATON-WORK.md` for the operator
contract and the complete verb surface.

> The filename is stable on purpose: participating repositories point their
> agent policy at this path. The contents are protocol 11. Protocol 10's
> mailbox — directed messages, notices, `send`/`reply`, message claims — is
> retired and is not a fallback.

## Instance selection

    BATON_BIN=/absolute/path/to/baton
    BATON_CONFIG=/absolute/path/to/instance/baton.json
    "$BATON_BIN" --config "$BATON_CONFIG" --participant TEAM.MEMBER VERB key=value …

The config and SQLite authority live outside every participating product
tree. Never copy them into a repository, infer a config from the current
working directory, or omit `--config`. The local deployment supplies the
executable and explicit absolute config path; participating project policy
binds local roles to participant identities without hard-coding host paths.

Participant addresses are `<team>.<member>`. A team is a coordination
namespace, not necessarily a Git repository, and roles are open-ended. Each
project binds role-only instructions to concrete addresses in its own policy.

Every identity-bearing invocation passes `--participant <address>`. The
participant address IS the identity: there is no actor and no seed. Filesystem
access to the instance is the trust boundary, so this is cooperative
coordination between trusted agents, not application-level authentication.

Operands are strict `key=value` tokens, order-independent, each split at its
first `=`. Values containing spaces are quoted. There are no positional
operands. The conventional options before the verb — `--config`,
`--participant` — are launcher context and stay put.

## The model

**Work** is the unit of coordination: a recursive graph with strict
containment, typed non-containment edges, one owning team, and exactly one
route endpoint.

- `status` is `open` or terminally `closed` with an outcome and rationale.
- `phase` is the SCHEDULER state, and nothing else: `queued` (runnable,
  unclaimed), `active` (claimed — somebody is executing it), `block`
  (blocked on a recorded gate or obligation), `parked` (deliberately
  deferred). Terminal Work has no phase. What KIND of work it is —
  implementation, review, research — is the route's role, never a phase.
- `route` is the ONE endpoint whose resolved handlers may claim the Work;
  `next` is an optional planned successor.
- `handler` is the EXACT participant holding the claim, and is null while
  nobody holds it. Route answers who MAY act; handler answers who IS
  acting, and an unclaimed routed handoff names no handler. Phase and
  handler move together: `active` if and only if a handler holds it.

**Threads** are shared discussions labelled to Work. **Messages** are the
conversation inside them. **Events** are the Work's append-only operational
journal — what happened to it and why. Conversation and workflow are
deliberately different surfaces: a workflow transition never inflates a
message count, and a discussion post never moves a baton.

## Working the channel

- **Claim before you execute.** No participant starts implementation, review,
  or other execution owned by the route endpoint before the atomic
  `claim work=W…` SUCCEEDS. Every condition is rechecked inside the write
  transaction, so an earlier `ready` observation is advisory and a competing
  claim fails closed naming the recorded claimant. Discussion and planning
  while unclaimed are fine.
- **`wait` is participant-relative and read-only.** It returns the one
  canonical action projection for your exact identity:
  - open, ready, UNCLAIMED Work whose route resolves to you —
    every eligible handler sees it until one claims;
  - Work you have ALREADY CLAIMED, so the same participant can continue an
    active assignment episode. This half matters after a restart: your own
    claimed Work is still yours to finish, and a runner that only looked for
    unclaimed Work would walk past it;
  - pending `@` obligations your endpoint owes;
  - due verification trials your route answers for.

  It claims nothing and writes nothing. `+`, plain posts, and personal New are
  attention, never wakeups: a sender who needs action uses `@` or passes the
  baton.
- **Each action carries a stable key.** The Work action key is an ASSIGNMENT
  EPISODE — Work id, its episode sequence, and the accepted configuration
  generation — so Work handed away and handed back between two polls is a new
  episode even though no consumer ever observed it absent. Consumers key
  delivery on the whole key and never parse it to recover the Work id, which
  rides beside it as its own field.
- **Pass the baton explicitly.** `pass work=W to=team.kind comment="…"` is one
  atomic THREADLESS Work event: it moves `route`, clears `handler`, records
  the destination
  phase, releases the sender's claim, and stores `comment` as durable
  handoff evidence. It creates no message, advances no cursor, and moves
  no conversational count. The destination phase is the SCHEDULER state of
  unclaimed Work — `queued` when runnable, `block` when a gate is
  unsatisfied — because handing over responsibility is not the same as
  somebody starting. The destination role decides nothing here.
- **Ask with `@`.** `say thread=T… body="…" request=team.kind on=W…`
  publishes the message and creates one directed obligation owed by that
  endpoint, atomically. The route does not move: the answer is owed TO the
  current handler, not instead of it. `include=` is the way to give somebody
  context they owe nothing for. Answer with `respond`, `dispose`, or
  `accept`.

  If your own Work cannot honestly proceed until that answer arrives, suspend
  it on that exact obligation so the stage stops advertising progress nobody
  is making.
- **Recover an abandoned claim explicitly.** `release work=W expect=team.member
  reason="…"` is an exact compare-and-swap against the recorded claimant with
  a durable reason. Baton never auto-releases, transfers, or admits a second
  claimant on staleness. `heartbeat work=W` is liveness evidence only — an
  agent mid-turn cannot beat, so silence is never treated as failure.
- **Retries are effectively-once.** Mutating verbs take `op-id=`; an exact
  retry replays the one committed result, and any mismatch fails closed. The
  comparison uses the EFFECTIVE operands, so a retry may spell a default
  explicitly but may not change it.
- **Never mutate the database with raw SQL.** `home`, `tree`, `detail`,
  `thread`, `work-events`, `events`, `links`, and `search` are the read-only
  views. If a question about coordination can only be answered by opening the
  store, that inability is the finding.

## Evidence lives in the repository

Work binds to a canonical repository record — `root:work/records/YYYY/MM/…` —
and that binding is the durable locator for findings, plans, progress, and
append-only review journals. Baton holds the live workflow state; the dossier
holds the reasoning. Neither substitutes for the other, and a ruling that
exists only in a discussion thread is one context loss away from being
re-litigated.

Work-valued and Thread-valued operands accept either the authority-local
selector (`work=W11`, `thread=T2`) or the canonical id. Both resolve strictly
against the one opened authority: malformed, foreign, or missing selectors
refuse by name, and nothing is guessed from titles, cursor position, or
partial matches.

## One live consumer per active turn

Baton is vendor-neutral and stays that way. There are no Baton-to-model
bridges in the protocol: readiness adapters are external programs that read
`wait` and hand a compact line to their agent. They never claim, answer, or
complete Work on the agent's behalf.

- While an agent is actively assigned, keep its turn alive around exactly ONE
  foreground `wait`, and act on what it reports in the SAME turn.
- Readiness returns to the live turn; the work itself begins with the `claim`
  you then make in that turn. Resolve it, re-arm, continue.
- A queued readiness line is an EDGE TO RE-EVALUATE, not authority to act. By
  the time it reaches the agent the Work may have been claimed, passed, or
  closed — so re-read canonical state before acting, and expect the atomic
  claim to be the final arbiter.
- Never end a turn holding work you have claimed and neither progressed nor
  handed back.

*If ignored:* the teeth are on `claim`, not on `wait`. Terminal output does
not itself wake an idle agent, so work claimed by a process whose turn has
ended is stranded — held, invisible to its sender, and blocking the queue
until someone recovers it explicitly. Nothing here prevents that; the protocol
correctly refuses to guess whether a holder is alive.

Waking is a RUNNER concern, not protocol behaviour.
