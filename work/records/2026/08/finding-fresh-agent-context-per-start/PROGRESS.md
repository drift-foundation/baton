# Progress

Implementer-owned.

## Slicing, and why

The plan has five steps and the acceptance boundary spans the lifecycle
controller, the deployment contract, the Codex dispatcher's
configuration, and a deployment proof. That is more than one reviewable
change, so it is sliced — the same shape W93 used:

1. **[this slice] the mechanism.** `tools/infra.py` learns to MINT a
   per-start context, record it privately, hand it to the services that
   need it, and refuse to inherit one. Plan steps 1 and 2 for the
   controller, plus step 3's restart coverage and step 4's failure
   coverage at the controller level.
2. **the deployment contract.** Move the real Codex Thread ids out of
   `conf/infra.example.json` and the operator-maintained
   `codex-event-bridge.json` onto this mechanism, and update the
   connectivity guide's start sequence.
3. **the deployment proof** (plan step 5's second half), which needs a
   real app-server and is not reachable from this gate.

Passing after slice 1 rather than at the end is deliberate: the
mechanism is the part every later slice depends on, and a mistake in it
is cheapest to find now.

## Revalidation against the current tree — 2026-08-19

`tools/infra.py` is a strict, well-guarded controller: it owns only what
it launched, proves identity through `/proc` start ticks and argv,
refuses to adopt anything, and keeps private state under `MAILBOX/run/`
at 0600. None of that changes here — the new concept had to fit inside
those guarantees rather than beside them.

Two facts shaped the design:

- a service is a long-lived process with readiness, a pid to own and a
  rollback. A context is none of those: it is a short command that
  exits, and what it leaves behind is a locator. So `contexts` is a
  separate manifest concept rather than a service with a flag.
- the Codex dispatcher reads a config FILE. Placeholders in argv alone
  could not reach it, so a start must be able to write one.

W424 landed in this same tree and is what makes minting per start
viable: `--start-thread` now records a durable first turn and proves
the thread resumes on a second connection before printing its locator.
Without that, minting on every start would produce a fresh unusable id
every start. The two Works fit together exactly as W424's revision 1
says: W424 owns the same-start handoff, W459 owns not reusing it later.

## What this slice does

**`contexts`** — a manifest array beside `services`. Each entry has a
name, an absolute command, optional `after`/`cwd`/`env`/`requires`/
`participant`, and a `timeoutSeconds`. It runs once its `after`
services are ready, must exit 0, and must print one JSON object with at
least `threadId`. Every minted field is recorded, stringified, with a
`mintedAt`, in `MAILBOX/run/infra-state.json` under `contexts`.

**`{{context.NAME.FIELD}}`** — resolves in a service's `command`,
`cwd`, `env` values and `requires`, from the context minted THIS START.

**`renders`** — a service may declare templates to render. The
operator's template is read and never written; the result goes to
`MAILBOX/run/context/NAME.json` at 0600 with the same substitution
applied, and the service names it with `{{render.NAME}}`. That is how a
config-file consumer gets fresh locators without learning a new flag.

**Freshness, enforced rather than assumed:**

- the context map starts EMPTY on every start and the previous start's
  rendered files are cleared before anything can read one;
- a context that cannot mint — non-zero exit, unreadable output, or no
  `threadId` — fails the start. It does not fall back on an older
  locator, which is the entire decision;
- a start that rolls back completely removes its rendered files, so the
  next start cannot read a locator this one abandoned;
- a placeholder naming a context or render this start does not have
  refuses at LOAD, before any process launches — a manifest that would
  fail halfway through a launch with processes already running is a
  worse discovery than one that fails before anything starts;
- a render nothing references refuses too: a file written for nobody is
  a configuration mistake, not a feature.

**Two existing behaviours needed care rather than change:**

- pre-flight validation ran on the literal command, which would now
  refuse every path containing a placeholder. It skips only the strings
  that carry one, and the full check still runs in the launch loop on
  the RESOLVED service, so nothing is validated less than before.
- `status` compared the recorded argv with the manifest's. It now
  compares against the manifest resolved with the contexts the state
  records, so like is compared with like. What it protects is unchanged:
  an operator editing the manifest under a running set still reads
  `configuration-changed`, and so does a service pointed at a locator
  this start did not mint.

## What this slice does NOT do

`conf/infra.example.json` still carries `--target baton-tuner` against a
dispatcher config the operator maintains. Moving the real deployment
onto contexts is slice 2, and doing it here would have mixed a
mechanism nobody has reviewed with a contract change that depends on it.

Nothing here touches the ACP bridge. Its sessions are created per
process start already; whether that satisfies "fresh contexts for every
configured agent" is a question for slice 2, when the real manifest is
in front of me.

## Verification

- `tests/work/test_w459_fresh_contexts.py` — new, **18 passed**, driving
  the real controller as a subprocess against a fake bootstrap that
  mints a numbered locator and a fake service that records the argv it
  was launched with. Covered: a start mints and hands the locator to
  its service; the locator lives only in 0600 `run/` state and the
  operator's manifest still holds the placeholder; a SECOND start with
  unchanged configuration mints a different locator and the two starts
  saw different ones; the participant identity is what stays stable
  across them; placeholders resolve in `env` as well as argv; a
  rendered file carries the fresh locator at 0600 while the template
  is untouched, and is replaced on the next start; an unknown context
  or an unreferenced render refuses before anything launches; two
  contexts cannot claim one participant; a context that exits non-zero,
  prints garbage, or prints no `threadId` fails the start with no
  service launched and no state left behind; a failed start removes the
  rendered file a previous start wrote; an unreadable template refuses;
  a manifest with no contexts starts exactly as before; and `stop`
  still owns and rolls back what it started.
- `test_w20_infrastructure_lifecycle.py` — **46 passed**, unchanged.
- `docs/BATON-SETUP.md` documents the manifest surface AND the decision
  behind it, with the refusal rules listed.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2485 passed** (parallel), **40 passed** (serial), both bridge
  suites green.


## Response to review `review-2026-08-19T22-11-46Z.md` (slice 1 round 1)

All three accepted. Two of them contradicted the guarantee this slice
was written to give, which is the part worth saying plainly.

**P1 — context availability was not part of the ordering.** I checked
that a referenced context was DECLARED and stopped there, so a manifest
whose context waited on a service launched after the referencing one
passed preflight, started the first service, and then failed at
substitution with a process already running. The whole point of
refusing at load is that the alternative is discovering it there.

Services and context availability are now one ordering problem. A
context is minted once every service in its `after` set has started, so
it is available to service S if and only if all of them come strictly
BEFORE S in the launch order — and a cycle spanning both kinds of edge
fails exactly that test, which is why it is expressed as ordering
rather than as a separate cycle check. The refusal names the services
that come too late.

**P1 — a rendered file could overwrite a symlink target.** I opened the
target by pathname with `O_CREAT|O_TRUNC` and chmod'd afterwards, while
the lock, the state and every log in the same controller go through
`_open_owned`. A private directory is not the boundary: the same user,
a faulty context command, or a race can plant an entry there, and the
open would then truncate a file outside the mailbox. Rendered targets
now use `_open_owned`, which refuses the symlink, the hard link, the
non-regular file and the group-readable one — the four parts its own
docstring explains, none of which I had any business reimplementing
loosely.

**P2 — an empty `threadId` was accepted.** Presence is not usability. It
started the service and reported the stack healthy while `_load_state`
refused that very document on the next read; a start that cannot be
re-read is not a start. An empty or whitespace locator now fails the
mint.

One of my own assertions moved with the message it reads
(`printed no threadId` → `printed no usable threadId`). The reviewer's
three regressions pass unedited.

- `tests/work/test_w459_fresh_contexts.py` — **21 passed** (18 mine,
  3 the reviewer's).
- `test_w20_infrastructure_lifecycle.py` — **46 passed**, unchanged.
- The complete v11 gate exits 0 after the round: **2488 passed**
  (parallel), **40 passed** (serial), both bridge suites green.


## Response to review `review-2026-08-19T22-28-23Z.md` (slice 1 round 2)

**P1 accepted.** I validated placeholders in a service's command,
requires, env and cwd — and then read its templates at LAUNCH. So a
template was the one part of a service's configuration that escaped
preflight entirely: an unknown or not-yet-available context hidden in
one let the manifest load, let predecessor services start, and failed
at substitution with processes already running. That is precisely the
guarantee this slice is for, and I left a hole in it the shape of a
file.

Templates are now read in `_renders` at LOAD. Their bodies are scanned
with the service's own fields, under the same existence and ordering
rules, and the refusal names the render and its template path so an
operator knows which file to open — a placeholder in argv and one in a
template are the same mistake, but not in the same place.

`_render_files` renders from the body validated at load rather than
reading the file again, as the review asks: a second read would
reintroduce the readability and content race preflight had just
removed. An unreadable or non-UTF-8 template now refuses at load too.

One rule the change made necessary: a template may not reference
another render. There is no deterministic order in which one render
could be built from another, and quietly resolving it to whatever
happened to exist would be worse than refusing.

The reviewer's regression passes unedited. Three cases were added
beside it for the rules the round introduced: a template reaching a
context that is not minted until after its own service refuses at load
on the ORDERING half; a render built from another render refuses; and
a context command that rewrites the template between load and launch
does not change what is written, which is the race the validated body
closes.

- `tests/work/test_w459_fresh_contexts.py` — **25 passed** (21 mine,
  4 the reviewer's across both rounds).
- `test_w20_infrastructure_lifecycle.py` — **46 passed**, unchanged.
- `docs/BATON-SETUP.md` states both new rules.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2492 passed** (parallel), **40 passed** (serial), both bridge
  suites green.


## Slice 2 — the deployment contract moves onto the mechanism

Slice 1 was signed off in `review-2026-08-19T22-38-14Z.md`. This slice
does what the plan's step 2 asks: the operator no longer maintains a
file containing Thread ids.

**`conf/codex-event-bridge.template.json`** is new and shipped. It is
the dispatcher's configuration with `{{context.reviewer.threadId}}` and
`{{context.tuner.threadId}}` where the hard-coded locators used to be.
Everything else about it — servers, identities, roles, the socket, the
queue and reconnect bounds — is the same document the dispatcher has
always read.

**`conf/infra.example.json`** declares a context per Codex participant,
each waiting on `codex-app-server` and running `--start-thread` with
its participant and role named, and the `codex-dispatcher` service now
renders the template and reads `{{render.dispatcher}}` instead of an
operator-maintained path.

**`tools/deploy_work.py`** ships the template beside the manifest. A
release with one and not the other would ship a manifest that cannot
load — the loader reads the template, so the two are one artefact in
practice and are now one in the release too.

**Both operator guides** point at the controller-managed path first and
keep the manual form for driving the backend without the controller:
`docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md`'s step 2 is no longer a
manual step under `just start`, and the bridge README says not to
maintain thread ids by hand at all when the controller is in play.

### One consequence worth naming

Slice 1's round-2 correction reads render templates at manifest LOAD.
That is right, and it means a manifest referencing a template cannot be
INSPECTED — `status` included — until the template exists. The shipped
example carries `/absolute/path/to/codex-event-bridge.template.json`
like every other placeholder in it, so a test that exercises the
example must supply the file the way an operator does: by replacing the
placeholder with a real path. `test_w20_infrastructure_lifecycle`'s two
example cases now do exactly that, through one helper, and still prove
what they always proved — that the shipped example satisfies the
controller's own schema and keeps one isolated readiness path per Codex
participant.

I am flagging it rather than treating it as settled. If an operator
running `status` against a half-configured mailbox should get a service
list rather than a refusal, the fix is to defer a MISSING template to
the pre-launch check (which still refuses before any process starts)
while keeping load-time validation for one that exists. I did not make
that change: it would alter behaviour reviewed and signed off one round
ago, on my reading of a cost rather than on a reported one.

### The ACP question from slice 1 — and a conflict I will not settle alone

I said slice 2 would answer whether the ACP bridge needs anything. It
needs a RULING, not code, and I read the tree before writing this
because my first draft of the answer was wrong.

`runBridge` has no locator in its configuration, but it does have a
persisted session SELECTION under `stateDir`, and W27 rules what
happens to it:

- `session.mode: "new"` — what `examples/acp-bridge-claude.json` ships
  — creates a session per run. But `preflightSessionSelection` REFUSES
  a `new` run when the state file already selects a session: "refusing
  rather than replacing it — resume that session with a 'load'
  configuration". So a second managed start with the shipped
  configuration does not silently rotate; it stops.
- `session.mode: "load"` deliberately resumes the persisted session,
  and W27's own comment says an agent PROCESS dying is not the ACP
  session dying.

W459's decision says agent sessions are replaceable runtime state and
every managed start creates fresh ones. W27 ruled the opposite for ACP
continuity, on purpose and with its own review. Those cannot both hold
for a managed restart of an ACP participant, and deciding which wins is
not an implementer's call to make inside a slice about Codex Threads.

So the manifest's `claude-acp` service is unchanged, and I am asking
rather than choosing. Concretely, the question for the record is:
under `just start`, should an ACP participant's persisted selection be
cleared (fresh session, W459) or resumed (continuity, W27)? If W459
wins, the mechanism this Work already built is enough to express it —
the state file is exactly the kind of per-start artefact `run/` is for
— but the change belongs to a Work that owns the conflict.

## Verification

- `tests/work/test_w459_fresh_contexts.py` — **30 passed**. Slice 2
  adds: the example mints a context per Codex participant, each waiting
  on the app-server, with `--start-thread` and an explicit `--role`;
  the dispatcher reads `{{render.dispatcher}}` and declares the render;
  the shipped template carries placeholders and no hard-coded locator
  (the old `019c0000…` ids are asserted absent); the manifest and the
  template agree on context NAMES, which is the one way this pair can
  be wrong without either half looking wrong alone; and the release
  ships the template beside the manifest.
- `test_w20_infrastructure_lifecycle.py` — **46 passed**, with the two
  example cases supplying the template.
- `test_deploy_v11.py` — **12 passed**.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2497 passed** (parallel), **40 passed** (serial), both bridge
  suites green.

Slice 3 — the deployment proof against a real app-server — remains, and
is not reachable from this gate.


## Response to the slice 2 review — the ACP half

**P1 accepted.** The reviewer ruled the conflict I raised rather than
leaving it open: W459 is the later, narrower decision for MANAGED
restart boundaries, W27 remains authoritative for same-run process
recovery and explicit manual persistent deployments, and the
supersession is pinned in `FINDING.md`. That is the ruling I asked for,
and it is the right one to have come from the record rather than from
me.

What the correction had to preserve was as specific as what it had to
change: do not weaken W27 into overwriting an existing selection, and
do not delete the preceding session as though it were not history.

**`{{start.id}}`** is the mechanism. The lifecycle state now records an
identity for the start itself — random rather than a counter, so two
mailboxes cannot collide and a controller killed between starts cannot
reuse the identity before it — and it substitutes in a service's
command, cwd, env and requires, and inside render templates, exactly
like a context field.

**`conf/acp-bridge.template.json`** is new and shipped: the ACP bridge
configuration with `stateDir` ending in `{{start.id}}/baton.claude`.
The example manifest's `claude-acp` renders it and reads
`{{render.claude-acp}}`.

That satisfies the acceptance without touching a line of the ACP
bridge. Each managed start hands the participant its own selection
LOCATION, so:

- the session is genuinely new, which is W459's requirement;
- `session.mode` stays `new` and W27's refusal is untouched — absence
  is precisely what that mode requires, and it now finds absence
  because the location is fresh, not because anything was removed;
- the previous start's `session.json` stays exactly where it was, under
  its own start id, as history.

The alternative shapes — clearing the directory, or configuring `load`
— are the two the review named as unacceptable, and both were avoided
by changing WHERE rather than WHAT.

`tools/deploy_work.py` ships this template too, for the same reason it
ships the dispatcher one.

## Verification

- `tests/work/test_w459_fresh_contexts.py` — **36 passed**. The ACP
  half adds: two starts give a service different ids; the id is a
  32-hex identity, recorded in state, reaching the service, and
  `status` still recognises what it launched; the id reaches a render
  template; the shipped example renders a per-start ACP configuration
  whose `stateDir` carries it while `session.mode` stays `new`; the
  release ships both templates; and the setup guide explains the
  boundary, including that the previous selection is preserved.
- `test_w20_infrastructure_lifecycle.py` — **46 passed**, with the
  example harness supplying both templates.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2503 passed** (parallel), **40 passed** (serial), both bridge
  suites green.

Slice 3 — the deployment proof against a real app-server — remains.


## Slice 3 — the two-start proof

Slice 2 was signed off. The review scoped slice 3 exactly: "a real
managed two-start proof must show that the participant identity and
actionable Work survive while both the Codex Thread locator and ACP
session selection change."

It is in two halves, and I am being explicit about which is which
because only one of them can run in this gate.

**The half that runs here.** Two managed starts through the real
controller, against a real Baton authority, with a real Work routed to
a real participant — read through the public `wait` CLI by the service
itself, not by the test. What is stood in for is the vendor processes:
this gate runs no Codex app-server and no ACP agent, and it should not
pretend to.

The stand-in ACP service does what the real bridge does at the point
that matters: it reads its RENDERED configuration, publishes a session
selection where that configuration points, and asks Baton what it is
supposed to be doing. Across two starts the test asserts

- SURVIVES: the participant address, and the actionable Work — the
  same `W…` on both starts, from the participant's own projection;
- CHANGES: the `stateDir`, the ACP selection (both starts see an
  absent one and create fresh), and the minted Codex-shaped locator;
- REMAINS: the first start's `session.json`, under its own start id,
  with a different session from the second's.

That last assertion is the one worth having. It is easy to satisfy
"fresh context" by deleting the old one, and the review named that as
unacceptable — so the proof checks that the previous selection is still
there rather than only that the new one is new.

**The half an operator runs.** `docs/BATON-SETUP.md` gains "Proving a
restart against real backends": two starts, and the four comparisons —
what must change (start id, every minted `threadId`, the rendered
`stateDir`), what must not (participant addresses, and the actionable
Work each `wait` returns), and what must still be there afterwards
(the previous start's selection). An agent's position comes from
Baton, not from the context it happens to be running in, and that
sentence is the whole reason this Work is safe.

I did not fabricate a vendor-level proof. If the reviewer wants the
real backends exercised inside the repository, that needs a Codex
app-server and an ACP agent in the gate, which is a deployment
decision rather than an implementation one — and it is not what the
acceptance boundary asks for.

## Verification

- `tests/work/test_w459_fresh_contexts.py` — **39 passed**, including
  the two-start proof and the guide check.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2506 passed** (parallel), **40 passed** (serial), both bridge
  suites green.
