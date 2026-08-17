# Finding: ACP bootstrap silently replaces the resumable session selection

## Observation — 2026-08-17T11:54Z

The first successful `baton.claude` ACP bootstrap created session
`0fff820b-c729-4d14-b725-1fbc1a519734`, delivered W2, and persisted that
selection in the bridge state directory. After the one-shot bridge exited, an
operator accidentally started the persistent bridge with `bootstrap.json`
instead of `load.json`. The second `session.mode=new` setup created
`72a241a9-26b3-408e-b2bf-d2850cb0afaf` and replaced `session.json` before any
Work was claimed.

Starting `load.json` then correctly resumed `72a241a9...`, not the intended
`0fff820b...` session. Both Claude transcript files remain present, and W2
remained unclaimed, so no Baton authority state or prior transcript was lost.
The selected continuity context was nevertheless silently displaced.

## Confirmed boundary

- `session.mode=new` and `session.mode=load` differ only in session selection;
  `--once` independently controls bridge lifetime.
- A successful new-session setup publishes its returned session id to
  `stateDir/session.json`.
- A later bootstrap currently replaces that selection even when the state file
  already names a resumable session.
- The wrong-session load is deterministic and visible in the Claude subprocess
  `--resume=<session-id>` argument; this was operator misuse made dangerous by
  a missing fail-closed guard, not identity leakage or a Baton database defect.

## Immediate recovery

Stop the bridge while W2 is still unclaimed, restore the previously observed
`0fff820b...` selection in `stateDir/session.json`, and restart only with
`load.json`. This is an explicit recovery of surviving bridge-owned state, not
a reconstruction or mutation of Baton authority state.

## Proposed correction

`session.mode=new` should refuse before starting an ACP agent when
`stateDir/session.json` already contains a valid selected session. Creating a
replacement session must require a separate explicit operator action with a
durable reason; merely choosing the bootstrap configuration must never rotate
the active selection silently.

Acceptance must cover:

1. first bootstrap creates and persists one session;
2. repeated bootstrap refuses without spawning an agent or changing the file;
3. load continues to resume the original session after that refusal;
4. malformed/missing state fails clearly without deleting surviving history;
5. an explicit future rotation path, if introduced, never masquerades as
   ordinary bootstrap.

## Reviewer revalidation — 2026-08-17T14:29Z

The defect is present in the current tree and the pinned correction still
matches the implementation boundary:

- `AcpAgentSession.setup()` starts the configured ACP subprocess before the
  `new` path inspects any persisted selection.
- `persistedSessionId()` catches every read/parse failure and collapses absent,
  malformed, and unreadable state into the same `null` result. That is useful
  for neither bootstrap nor load: only a genuinely absent state file permits a
  first bootstrap; malformed or unreadable existing state must be preserved
  and refused by name.
- `persistSessionId()` uses a replacing `writeFileSync`, so a preflight check
  alone would still leave a check/publish race. Final publication must be
  create-only and a collision must preserve the winner byte-for-byte.
- `runBridge()` creates the ACP session lazily after actionable readiness is
  returned. A bad bootstrap configuration can therefore appear healthy while
  idle. The existing-selection refusal must be a bridge-startup preflight,
  before Baton wait and before agent spawn, so the operator gets an immediate
  nonzero result rather than a deferred retry loop.

No rotation command belongs in this correction. The safe supported operations
remain: create the first selection with `new`, then resume it with `load`.
Replacing a selection is a separately specified future operation.

## Implementation clarification — 2026-08-17T14:41Z (baton.claude, W27)

> **The run-owned rewrite clause below was SUPERSEDED at 2026-08-17T14:45Z**
> by the review ruling at the end of this file. Read that ruling before
> acting on anything in this section. The reasoning is kept because it is
> why the current rule is not the obvious one: the observation that
> unconditional create-only breaks in-run recovery was correct, but the
> conclusion drawn from it — create a fresh session and update the record —
> was wrong. A dead agent PROCESS does not mean a dead ACP SESSION, so the
> right answer was to resume the retained id, not to publish a new one.
> What survives here is the first-publication and repeated-bootstrap
> reasoning, which the ruling explicitly left standing.

The pinned ruling above is confirmed and implemented as written, with ONE
scope refinement that revalidation against the current tree exposed. This
clarifies the create-only requirement; it supersedes nothing else.

**"Final publication must be create-only"** cannot mean *every* publication.
`runBridge()` rebuilds its session through `ensureSession()` whenever the
agent dies, and in `session.mode=new` that rebuild legitimately creates a
fresh ACP session. Reading create-only as unconditional makes the FIRST agent
death fatal to the bridge, and the existing acceptance test *agent exit
mid-turn is visible, retried, and readiness survives* fails — observed
directly, not predicted. Worse, refusing the update would leave
`session.json` naming a session that no longer exists, so a later `load`
would faithfully resume a corpse.

The honest boundary is OWNERSHIP, not write count:

- The FIRST publication of a bridge run is create-only. It races other
  bridges, and the loser abandons its own new session rather than replacing
  the winner's bytes. This is the W27 defect and it stays closed.
- Once a run has published, it OWNS that record, and an in-run rebuild
  updates it. That is the run correcting its own selection, not a second
  bootstrap rotating somebody else's.

Ownership is therefore run-scoped state shared across the sessions one bridge
builds, not per-session state. Both directions are pinned by regressions, so
neither can drift: blocking the in-run update reds the rebuild test, and
making publication unconditional reds the create-only test.

This does not reopen rotation. Nothing here lets a SECOND bootstrap replace a
selection it did not create, which is the whole of the finding.

## Review ruling — 2026-08-17T14:45Z

The run-owned rewrite clause in the 14:41 implementation clarification is
**superseded**. The first-publication and repeated-bootstrap portions remain
correct.

An ACP agent *process* dying does not mean the selected ACP session died. The
live W2 proof killed and restarted the Claude adapter, then successfully loaded
the same `0fff820b...` session with its context intact. Creating a fresh session
after process death would discard exactly that continuity and silently rotate
`session.json` from inside the original bootstrap run.

After a `new` run has successfully published its first session selection, every
agent-process rebuild in that run is therefore a `load` of that exact session
id. If the replacement agent does not support load or the selected session
cannot be loaded, the bridge fails visibly and leaves readiness pending; it
never creates another session and never rewrites the selection. The persisted
selection is immutable during ordinary bridge operation. Any true rotation
still requires the separately specified future operator action.

The earlier crash-retry regression proved only that a prompt was eventually
redelivered. It did not prove retained context or session identity and cannot
authorize a new session. Its continuity form must prove one `session/new`, then
`session/load` of the identical id, unchanged `session.json`, and no second
`session/new`.

## Round-two review clarification — 2026-08-17T14:51Z

The same once-per-run selection rule applies when the bridge starts in
configured `load` mode. The bridge selects the persisted id once, before its
first Baton wait or agent spawn, and every replacement process in that run
loads that retained id. It never rereads `session.json` to choose a different
session after process failure.

This closes the symmetric path left by the round-one correction: caching the id
only after `new` protects bootstrap runs, but a `load` run that rereads the file
on every rebuild can still be steered onto another session. Missing, malformed,
or unreadable load state is likewise a startup selection error, not a deferred
agent-setup retry.
