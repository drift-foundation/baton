# Progress

## Step 1 — the axis (2026-08-18)

`PHASES` is now `queued | active | waiting | parked`, terminal null.
`STAGE_PHASES` — the role-to-phase map — is deleted, and with it the
idea that a handoff's destination role says anything about whether the
Work is running.

One helper does the derivation everywhere a claimant is released:
`_unclaimed_state()` returns `(phase, wait_type)` from the committed
gates. `pass`, `release` and the readiness path all call it, so they
cannot disagree about the same state.

`claim` now sets `active` in the same statement that records the
handler, and every phase the `phase` verb can reach is an unclaimed
state, so it releases. `active` is not settable at all: asking for it
refuses and names `claim`.

Creation lost its `phase=` operand. A new Work is open, unclaimed and
ungated, so `queued` was the only value it could take — an operand with
one legal value is noise, and W73 set the precedent for removing one
rather than narrowing it.

Storage: `handler_team/handler_member` (was `current_*`), schema 18 ->
19. Projection: `handler` replaces `current`, `handler=` replaces the
`current=` filter. `PROJECTION_VERSION` 8.0 -> 9.0, because the phase
VALUE SET in participant-action envelopes changed; both readiness
bridges accept 7/8/9 in the same candidate, as the finding requires.

## Step 2 — two bugs the invariant found

Neither was in the finding; both came out of making `active iff Handler`
actually hold.

**A late gate left `active` with nobody on it.** `_recompute_ready`
releases the claimant when a dependency arrives on claimed Work — the
one path that releases without being asked to. Releasing without moving
the phase produced exactly the contradiction this Work exists to remove,
arriving through the least obvious route. It now lands `waiting`, which
is what the gate means anyway.

**A derived `waiting` was unwakeable.** My first version of `pass`
derived the phase but cleared `wait_type`, and `_sweep_wakes` only
reconsiders rows whose condition it can evaluate. A gated handoff would
therefore have been gated forever, even after the blocker closed. The
wake condition now rides with the phase out of the same helper, which is
why they are returned together rather than as two calls.

## Step 3 — acceptance

`tests/work/test_w38_scheduler_phase.py`, 13 checks. The load-bearing
one is `_invariant()`, which walks EVERY open row after each transition
rather than the row under test — a contradiction introduced anywhere
else fails the nearest test rather than surviving to a later one.

Covered: the closed vocabulary; `active` unsettable and absent from the
creation grammar but present in the FILTER, because asking what is
running is an ordinary question; claim/release; a handoff landing queued
for every destination role; a gated handoff landing waiting AND waking;
the late-gate release; every settable phase releasing; terminal clearing
both; a losing claim race; and the projection's route/handler/next.

Break-sweeps: restoring role-derived phases reds 2; dropping the wake
condition reds the wake test; releasing without moving the phase reds
the late-gate test.

## Step 4 — the suites

`test_w73_route_derived_phase.py` tested the exact contract this Work
supersedes, so it is repurposed rather than deleted: it now proves every
destination role lands the same way, that a stageless role no longer
refuses, that a gated handoff lands waiting, and that `pass` still takes
no `phase=` operand — W73's surviving half.

`test_w108_active_claim.py`'s thesis was that claim and phase are
ORTHOGONAL. W38 inverts that, so its matrix now asserts they move
together, while W108's own contributions — atomic claim, exclusivity,
compare-and-swap release, handoff evidence — are untouched.

Roughly a hundred other assertions moved mechanically. Two mistakes are
worth recording because both were mine and both were caught by tests
rather than by reading: a blanket park-sweep turned several parked ->
queued RESUMES into double-parks, and an earlier sweep left a duplicated
claim. Both are the same failure as the stale-bytecode false green
earlier this session — a mechanical edit that changed meaning where I
only checked the pattern.

## Step 5 — flagged, not decided

`hot_work` had a second clause: "runnable REVIEW Work someone needs to
claim". W38 makes it inexpressible — there is no review phase, and the
review-ness of Work is its Route's role, so reinstating it would put
role-shaped matching back into presentation, which is what this Work
removed from the authority. The zone reduces to "somebody is executing
it", which is now the same statement as `phase == active`.

That NARROWS a ruled cue, and the narrowing is a consequence of W38
rather than a decision this Work was asked to make. Flagged for the
reviewer.

## Evidence

- Gate: **1094 passed** + 13 serial + acp 36/36 on 32 cores.
- Break-sweeps: 3, each reddening its own property.
- Whitespace check clean.

## Step 6 — review round 1 (2026-08-18)

R1-R3 were real, and they share one root cause: I derived the scheduler
state where a CLAIMANT was released rather than wherever READINESS
changed. That covered the paths I was thinking about and left the
ordinary ones contradictory.

**R1.** A gate arriving on unclaimed queued Work committed
`queued/ready=false/wait_type=null` — non-runnable Work in the state
that means runnable, with no condition to wake on. `_recompute_ready`
now derives for the unclaimed case too. `parked` is deliberately
excluded: a gate appearing under a deliberate deferral does not revoke
the decision.

**R2.** Resuming a park wrote `queued` verbatim, so a dependency added
during the park produced queued with `ready=false`. Leaving the park now
reveals what the gates say — the same derivation, at the other end.

**R3.** The subtlest, and the one I would not have found. `_sweep_wakes`
treated the stored `wait_type` as the whole scheduler condition, so
answering an obligation woke Work that had independently acquired a
dependency — and minted an actionable episode for it. It now retargets
the wait to the remaining gate and stays waiting.

That retarget emits NO event. My first version emitted a `wake` whose
`from` and `to` were both `waiting`, which put a false actionability
signal into every trail that reads the journal; two suites caught it
immediately. The transition that satisfied the old condition is already
audited and the new condition is visible on the row.

## Step 7 — the rest of the round

**R4.** The Codex bridge matrix still asserted the old error wording and
an explicit projection-9 REFUSAL; both corrected, and the ACP suite
gained explicit projection-9 acceptance plus a 10.x refusal. Codex 42/42,
ACP 38/38.

**R5.** The operator documentation is updated in this candidate, per the
review: `AGENTS-MAILBOX-PROTO.md`, `EFFECTIVE-BATON.md` and
`BATON-WORK.md` now describe the scheduler axis, Route/Handler/Next, and
a handoff landing queued or waiting rather than deriving from the role.
`BATON-WORK.md`'s retired `>` marker paragraph went with it — W15 had
removed the marker but that document still taught it.

**R6.** `PHASE_COMPACT` no longer maps `research`, and the neighbouring
comments say Handler.

## Consequences worth the reviewer's attention

**Waiting Work cannot be parked, and R1 makes that bite much harder.**
The rule that waiting leaves only through its condition-bound wake is
unchanged, but far more Work is now waiting — including every parent
with an open child. Two existing tests had to park a leaf instead. I did
not relax the rule, because it is ruled; flagging that the ordinary
"defer this while it is blocked" move is now unavailable.

**More wake events.** A gated dependent now genuinely sits in `waiting`,
so closing its last blocker emits the wake it always should have. Three
event-trail assertions grew by one entry.

## Evidence

- Focused W38: 16 passed, including the reviewer's three regressions.
- Gate: **1097 passed** + 13 serial + acp 38/38 on 32 cores.
- Break-sweeps: reverting each of R1, R2, R3 reds exactly its own
  regression.
- Whitespace check clean.

## Step 8 — review round 2: R7 (2026-08-18)

I had rewritten the vocabulary and left the MODEL. The round-1 pass
renamed Current to Handler and fixed the phase list, and stopped there —
so the guide still carried a `kind -> route -> role -> phase`
composition diagram, still said the role decides the phase a handoff
lands in, and still told a reader that claiming leaves the phase at
`queued`. Those are the two false models this Work exists to remove,
sitting in the straight-through path a reader meets first.

Corrected:

- the composition chain now ends at `role + handlers`, with phase shown
  as the separate axis it is and its four states spelled out;
- the claim paragraph says what claiming DOES — the phase becomes
  `active` in the same transaction, because Handler and phase are one
  fact seen twice;
- `BATON-WORK.md`'s three remaining labels now say what each sentence
  actually means: release and unblock are ROUTE-handler authority, and
  the Events list says phase/Route/Next.

Executable specifications too, since they teach the next maintainer just
as effectively: `test_phase.py`'s "six-phase enum / Current-route-handler"
contract, `test_w80_pass.py`'s test whose NAME asserted the inverse of
its own body, and `wfdriver.py`'s "every open Work has exactly one
Current" — which is now false by design, because Handler is nullable
unless claimed. That invariant helper gained the two checks it should
always have had: `active` iff a handler, and terminal Work carrying
neither.

### The regression

Five checks. Two scan the active documents for each false model, one
scans every suite in `tests/work` for the same phrases, and one is the
POSITIVE half — the guide must actually state the invariant, because a
scan for absent phrases passes trivially on an empty file. That
positive check is the one that would have caught this round's gap; the
negative ones would not, since the old prose was present rather than
missing.

The forbidden phrases are composed from fragments so this file can be
scanned alongside the others without matching itself. My first draft
claimed that and only did it for two of them, and the scan caught its
own file — which is exactly what the composition is for.

Break-sweeps: reinstating the role-derived sentence reds the document
scan; weakening the invariant sentence reds the positive check; a single
regressed suite docstring reds the specification scan.

## Evidence

- Focused W38: 24 passed.
- Gate: **1105 passed** + 13 serial + acp 38/38 on 32 cores.
- Whitespace check clean.

No authority or schema change in this round, as the review required.
