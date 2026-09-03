# Recover abandoned Job-stage offers after restart

Ledger Work: W73629

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-concurrent-stage-scheduling/`

## Observed — 2026-09-02

The Worker Manager correctly abandons an `issued` offer owned by an earlier
manager incarnation because no durable fact proves its bearer was delivered.
The Job manager, however, retains the stage's `admit` receipt, derives the
stage as `offered`, and continues to owe only `claim`. The canonical offer is
now `abandoned-after-restart`, so every claim attempt is an ordinary deferred
precondition and the stage never returns to an admissible state.

The retained reproduction is
`/tmp/w71877-abandoned-offer-repro.py`. Against `efbad19` it reports:

```text
{'recovered': {'abandoned': ['offer:job-a/implementation'], 'recoverable': []}, 'stage_state': 'offered', 'owed': ['claim'], 'offer_state': 'abandoned-after-restart'}
```

This predates W71877's pool implementation. Adding a durable worker
reservation around the existing path would turn the stage wedge into a pool
capacity leak as well.

## Confirmed boundary

An abandoned offer is immutable history and its receipt must not be deleted or
rewritten. Recovery needs a new offered-and-claimed execution episode with
fresh offer and runtime-attempt identities, while the status projection keeps
the abandoned episode visible. The Worker Manager remains the owner of offer
settlement; the Job manager consumes a public canonical offer observation and
decides that a new episode is owed.

W71877 must not hide this by freeing a slot while leaving the stage permanently
`offered`, nor by treating the old offer as live. Scheduler reservation release
may compose the corrected canonical ending once this Work closes.

## Approved level-triggered event boundary — 2026-09-03

**Confirmed:** Worker Manager recovery remains wholly owned by the Worker
Manager. The Job Manager neither reads its tables nor re-decides whether an
offer is abandoned. The normal communication boundary is a regenerable,
level-triggered Worker Manager state event, not a one-shot transition notice
and not Job Manager polling of Worker Manager storage.

After recovery, and again whenever a consumer attaches or reconnects, the
Worker Manager enumerates the relevant canonical offer rows and publishes
their current state as `offer.state` events. An event carries at least the
offer and attempt identities, canonical state, and a monotonic state revision.
The event transport is not authoritative: the Worker Manager store is, and
the same state event can be reconstructed from it at any time. An in-process
delivery is sufficient for the current combined Python process; a later
socket, broker, or remote adapter changes transport only.

Delivery is at least once. Republishing the same event immediately, after a
restart, or periodically is explicitly safe and has the same effect as one
delivery. The Job Manager records or applies the observed state idempotently,
ignores an older revision after a newer one, and constrains one abandoned
stage episode to at most one replacement episode. A duplicate abandonment
notice therefore cannot mint a second offer, attempt, assignment, or worker
reservation.

This ruling supersedes any interpretation of the earlier "public canonical
offer observation" language as a request/response read used for ordinary
recovery. A public diagnostic query may still exist, but recovery progress is
driven by replayable state events. A durable transition-event log is not
required for this slice because the retained offer row can regenerate the
current terminal state; preserving every intermediate Worker Manager
transition would be a separate requirement.

### Non-reentrant delivery

**Confirmed:** in-process does not mean inline callback. Publishing an event
only appends its owned document to a transient queue and returns. A top-level
run-to-completion pump dispatches queued events after the producer has
committed and released every store transaction and lock. A handler processes
one message, records its durable effect or owed action, enqueues any follow-up
command or event, and returns; it never waits for another event and never
recursively invokes another handler.

Worker-directed or otherwise blocking activity is outside the event pump. Its
request is represented durably, execution reports completion through a later
event, and the pump remains free to serve unrelated state. The current
single-process implementation needs only a small standard-library queue and
explicit pump; it does not require `asyncio`, a third-party signal package, or
a broker. The queue is not durable authority: losing it on restart is safe
because owed commands and current state events are regenerated from the two
canonical stores.

## Acceptance

- A restart after offer issuance but before acceptance records the old offer
  as abandoned and makes a fresh stage episode admissible.
- The fresh episode has distinct offer, attempt, and assignment identities;
  the old receipt and abandonment remain auditable.
- Reconciliation is idempotent across a second restart and cannot issue two
  live offers for one stage episode.
- A delivered-and-accepted offer remains recoverable and is never replaced.
- Status distinguishes the abandoned episode from the new queued/offered
  episode without storing a shadow copy of offer state.
- Startup and consumer attachment regenerate the current canonical
  `offer.state` assertions; losing an earlier delivery cannot wedge the stage.
- Repeating one state event, including periodic republication, is a no-op after
  its one corresponding Job Manager effect has committed.
- A stale lower revision cannot regress a stage or replace the fresh episode.
- No event is delivered inline under a Worker Manager or Job Manager
  transaction, and a follow-up event is queued rather than dispatched
  recursively.
- A handler that needs a later fact records that need and returns; it cannot
  block the pump waiting for the fact it expects another event to deliver.

## Test-change authority

This Work authorizes additive tests and edits under `v12/python/tests/job_manager/`
for abandoned-offer observation, episode replacement, restart races, and
status history. No deletion, weakening, or unrelated test change is authorized.

## Implementer decisions — 2026-09-03 (`baton.claude`)

The approved boundary above fixes the COMMUNICATION shape and leaves four
mechanism choices open. They are pinned here before implementation, with the
reasoning, because each one is a durable product decision a later reader would
otherwise have to reconstruct from code. **Every one of them is flagged to the
reviewer as an implementer decision rather than a ruled one.**

### The state revision is DERIVED from the canonical state, not stored

The event carries "a monotonic state revision". Adding a revision column to
the Worker Manager's `offers` table would bump that store's schema for every
existing manager deployment, and W71875's own record already refused to make
the manager's schema a scheduler concern.

It is not needed. An offer's canonical lifecycle is already monotone —
`issued` precedes `accepted`, and every terminal state (`declined`, `expired`,
`abandoned-after-restart`, `claimed`, `claim-refused`, `settlement-expired`)
follows both — so a fixed RANK over `OFFER_STATES` is a monotonic revision
that can be recomputed from the offer row at any instant. That is exactly the
property the level-triggered ruling asks for: the event is regenerable from
the store because it is a pure function of it. A stored counter would be a
second account of the same fact and could disagree with the row after a
restart.

The cost is that this revision cannot distinguish two different terminal
states from each other. It does not have to: the state travels in the same
event, and an episode records at most one ending. Ordering only ever has to
answer "is this event older than what I already applied".

### Worker Manager publication is driven from the seam, and `offers.py` is
### not touched

Publication happens in a new `worker_manager/events.py`, called by the Job
Manager's operations seam AFTER `recover_on_restart` has returned and every
one of its transactions has committed. Putting a publish call inside
`_settle_terminal` would be publishing under the settling transaction, which
the non-reentrancy ruling forbids, and would make the event's existence depend
on being on that code path rather than on the row it describes.

So the Worker Manager still owns offer settlement and still owns the
enumeration; what it does not do is emit from inside its own write. `offers.py`
is unchanged by this Work.

### The Job store gains schema 2, with an explicit transactional migration

Recovery needs per-episode offer and attempt identities and per-episode
receipts, so the Job store gains an `episodes` relation and `receipts` gains
`episode` in its primary key. `stages.offer_id` and `stages.attempt_id` are
REMOVED rather than kept beside the episode rows: two accounts of one
episode's identity is the shadow state this package refuses everywhere else.

Schema 1 stores are migrated in one transaction after the schema-1 object set
and metadata validate, rather than refused: a persisted submission is a real
pipeline and discarding it because the next slice added a relation would be
this build deciding an operator's work is disposable. The migration gives every
existing stage episode 1, carrying exactly the identities its stage row already
held, and stamps every existing receipt with episode 1 — so a migrated store's
canonical operation identities are unchanged and its receipts still reconcile
against the manager journal rows they already named.

W71877's revalidation proposed this same rule for its own scheduler relations.
Taking it here settles it for the Job store generally; that leaf inherits the
mechanism rather than re-deciding it.

### Episode identities: episode 1 keeps the derived spelling

`offer:{stage_id}` and `attempt:{stage_id}` remain episode 1's identities, and
episode N>1 is `offer:{stage_id}#{N}` / `attempt:{stage_id}#{N}`. Identities
are STORED on the episode row from the moment it is opened, and the derivation
is used only when minting a new one — so a migrated store keeps every identity
the manager journal already holds, and no reader recomputes an identity it
could get wrong.

### Replacement is a CLOSED set, and it holds one member in this slice

`REPLACEABLE_ENDINGS = ("abandoned-after-restart",)`. That is the ending this
Work reproduced and was asked to correct.

`expired` produces the same wedge shape and is deliberately NOT included yet.
The two are not equivalent: an abandoned offer's bearer was never accountably
delivered, which is why the manager abandons it, whereas an expired offer was
delivered and the worker did not accept in time — whether that stage should be
re-offered to the same worker, a different one, or reported, is a scheduling
policy decision belonging to W71877 rather than to a recovery correction.
`declined` is a worker's deliberate answer and is even more clearly a policy
decision.

Nothing is hidden by leaving them out. An episode that ends in any non-`claimed`
ending outside the closed set is recorded, kept visible in the status history,
and projected `exceptional` — an operator sees a stopped stage rather than one
that silently retries forever. Widening the set is a NAMED later decision,
recorded in PLAN item 6.

### Status becomes `baton.v12.job-status/2`

The document gains a per-stage `episodes` history so the abandoned episode
stays visible beside the fresh one, and its `offer_id`/`attempt_id` now name
the CURRENT episode. That is a shape change, so the schema name's version
moves with it rather than letting an old reader mistake the new document for
the one it knows.

## Discovered during implementation — 2026-09-03

**The Worker Manager's boundary-probe inventory is already failing, and this
change adds three entries to it.**

`tests/manager/test_boundary_inventory.EveryProbeProvesItArrived` requires one
declared probe per owned boundary entry in that package. At `b4e33cb` it
already fails with **49** unprobed entries, before this Work touches anything;
adding `worker_manager/events.py` takes it to **52**. The three are exactly:

```text
(('caller', 'events.py:offer_state_revision', 'state'), 'a canonical offer state')
(('caller', 'events.py:publish_offer_states', 'offer_ids'), 'an offer id')
(('caller', 'events.py:publish_offer_states', 'queue'), "the transport's publish")
```

Six further entries were avoided by CORRECTING this change rather than by
declaring an exemption. `offer_state` originally re-owned `offer_id`,
`runtime_attempt_id` and `state` off a row `offers._offers` had already proved
against `OFFER_COLUMNS` — the blanket revalidation of a trusted internal value
that PLAN 4bz rules against, and three inventory entries asserting what another
entry already asserts. That is fixed here because it was this change's defect.

The remaining three are genuine boundaries and genuinely want probes. They are
NOT written in this Work: the gate is red on arrival for 49 other entries, so
probes added here could not be verified green, and repairing another leaf's
inventory is not this correction's acceptance. Recorded as PLAN item 7 rather
than left for the identity-level sweep comparison to hide — comparing failing
test IDENTITIES reports an empty delta for this, because the gate was already
failing under the same name. The failure TEXT is what shows it, and that
comparison is what found it.

## Independent review — changes requested 2026-09-03

The episode schema, transactional schema-1 migration, level-triggered
publication seam, derived revision rank, and the one-member replaceable set are
coherent in isolation. The review accepts `abandoned-after-restart` as the only
currently authorized replacement cause and agrees that `expired` and
`declined` remain named scheduling-policy work. It does not accept treating
every terminal OFFER state as an ending of the STAGE execution episode.

After an accepted offer is claimed, a first restart correctly recovers and
claims episode 1. On the next restart, the publisher regenerates canonical
state `claimed`; `apply_offer_state` includes that state in the generic
terminal-offer set and ends the episode. With no live episode and no
replaceable ending, the projection reports the stage `exceptional`, clears its
current offer and attempt identities, and stops observing its runtime or
output. The retained review reproduction
`/tmp/w73629-claimed-restart-repro.py` reports:

```text
before: state=claimed, episode=1, offer=offer:job-a/implementation
after:  state=exceptional, episode=null, offer=null
history: [(1, claimed)]
```

This violates the accepted recoverability rule and would strand a running or
completed stage after a later process restart. A `claimed` offer is terminal
on the offer axis but its attempt is the stage's continuing execution; the
correction must preserve that current episode identity, or explicitly model a
successor execution identity before ending it. Add a real-manager regression
that accepts, claims, restarts again, and proves the same current
offer/attempt, claimed/running/completed projection, and dependency evidence
survive.

Two secondary contract gaps also require correction. First, the new
`_ReadOnly.attach` and `drain` methods say a status run consumes regenerated
assertions, but neither `_status` nor `status` calls them. The retained
`/tmp/w73629-status-attach-repro.py` observes canonical
`abandoned-after-restart` while the read-only projection still says `offered`
and the episode ending remains null. Decide whether read-only status owns a
non-mutating current-state overlay or whether only the serving reconciler is a
consumer attachment, then make code, documentation, and tests agree.

Second, this candidate adds three owned Worker Manager boundary entries while
the exhaustive inventory gate is already red. The exact test now reports 52
unprobed entries instead of the baseline 49. A pre-existing failure identity
does not make that regression invisible: declare and independently exercise
the three new probes, restoring the candidate's missing-entry set to the
baseline without weakening or exempting the gate.

Finally, PLAN item 5 requires an immutable proposal-bound verdict, but the
handoff expressly supplies only mutable canonical working-tree bytes. The
correction round must form a sealed candidate, enumerate its exact path set,
and provide its digest for the next independent review. No final import or
approval is authorized from this reviewed snapshot.


## Independent review and correction pass 1 — 2026-09-03

Independent review requested changes; see `review-2026-09-03T03-34-03Z.md`.
The core decisions above were ACCEPTED -- the schema migration, seam
publication, derived revision, and abandonment-only replacement. Three
findings and one acceptance gate were not.

### Confirmed P1 — a terminal OFFER is not a terminal STAGE

The first draft used `events.TERMINAL_OFFER_STATES` as the set of states that
end a stage's execution episode. `claimed` is in that set, correctly: the offer
is terminal. But it is the one ending that means the stage is RUNNING. So the
next restart republished canonical `claimed`, the handler ended the episode,
and `status` regressed a working stage from `claimed` with its identities to
`exceptional` with episode, offer and attempt all null -- and stopped observing
the very attempt the claim had authorized. The measured sequence is
`/tmp/w73629-claimed-restart-repro.py`.

**Corrected, and the vocabulary is now two things rather than one.**
`documents.EPISODE_ENDINGS` is the set of offer endings that end an EXECUTION:
`abandoned-after-restart`, `claim-refused`, `declined`, `expired`,
`settlement-expired`. `claimed` is deliberately absent.

Both relationships are asserted AT IMPORT, each where the things it relates are
in scope: `documents.py` asserts that every replaceable ending is an ending,
and `manager.py` -- the one module that holds both vocabularies -- asserts that
`EPISODE_ENDINGS` is a STRICT subset of `TERMINAL_OFFER_STATES` and that the
single member of the difference is `claimed`. Correction pass 2 moved that
second one out of a test and into the build, because review
`review-2026-09-03T04-01-25Z.md` correctly found the proposal claiming a
runtime assertion that only a test was making.

The earlier claimed-offer case checked only that nothing was REPLACED and
passed while the stage was being wrecked. It now asserts the episode and the
projected state, and two real two-restart regressions were added -- one for the
stage itself and one proving it still gates its dependent review stage, because
a gate opens only on `completed` and a stage wrongly reported `exceptional` is
a successor blocked forever.

### Confirmed P2 — which surface attaches, now pinned

The first draft gave the status tool's read-only surface `attach` and `drain`
and claimed a status run drained regenerated assertions. `status` never called
them, so an operator was told a fact had been consumed that was discarded.

**Pinned: ONLY THE SERVING RECONCILER ATTACHES.** Applying a canonical ending
is a durable act and a read-only surface performs none, so the unreachable
methods are removed rather than wired up. The review offered a truthful
non-mutating overlay as the alternative; it was NOT taken, because an overlay
is a second derivation of stage state beside the recorded one, and this package
refuses two accounts of one fact everywhere else.

What that costs is now stated in the code rather than left to be discovered: a
status run reports the pipeline as this store has RECORDED it plus the
canonical observation of each stage's current episode, so an offer that ended
since the last sweep is over canonically and still `offered` here. A serving
deployment is at most one tick behind; a store nobody is advancing is exactly
as stale as that store is. Both halves are regressed.

Note for the reviewer: `/tmp/w73629-status-attach-repro.py` asserts `queued`,
which encodes the overlay alternative. Under the contract taken it stays
`offered`, and the new cases assert that plus the fact that status wrote
nothing.

### Confirmed P2 — the boundary inventory is back to what it inherited

The publisher's three owned entries now have declared probes that the gate's
own `test_every_declared_probe_reaches_its_named_boundary` exercises, so the
missing-probe deficit is 49 -- the inherited count -- rather than 52.

Correcting that surfaced a second deficit the earlier text comparison had not
reached: removing the double validation from `offer_state` left four RECEIVING
entries with no owner, moving `test_every_receiving_entry_has_an_owning_validator`
from 130 to 134. Those four are now declared in `STATED_OWNERS` with the
reason -- the row arrives already proved by `offers._offers`, that module's one
declared crossing -- and witnessed by a test that spoils a persisted column and
requires the publisher to refuse at that owner's document. Both counts are back
to the inherited baseline, and every remaining difference in the broad sweep's
failure TEXT is a line-number shift.

### Acceptance gate — the immutable proposal

PLAN item 5's requirement is met: the corrected candidate is sealed as a
changed-path-set proposal with a manifest, a patch that reconstructs it from
the base, and a whole-proposal digest. Mutable checkout bytes cannot receive
import approval, and the earlier handoff was wrong to offer them.
