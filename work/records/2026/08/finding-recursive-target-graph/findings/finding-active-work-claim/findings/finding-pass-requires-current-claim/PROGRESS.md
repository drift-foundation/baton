# Progress

Implementer-owned. Work `W2571`, claimed by `baton.claude` 2026-08-20.

## Revalidation (PLAN item 1)

Both halves of the pinned reproduction check out against the current tree.

- `transitions.pass_work`'s in-lock guard refused a peer passing UNDERNEATH a
  claimant and said nothing about unclaimed Work: `if live["handler_team"] is
  not None and (...) != (actor_team, actor)`. An unclaimed pass reached the
  commit on `_handler_gate` route eligibility alone, exactly as the W1568
  event-2544-to-2555 sequence records.
- The superseded W171 decision is where the finding says it is, and the
  reviewer's dated supersession is already appended to
  `finding-v11-messaging-cutover-gate/findings/finding-pass-is-work-event/`
  (FINDING and PLAN). The two records agree; neither needed correcting.
- The side-effect-free requirement needed no new machinery: `Authority._write`
  runs `mutate` inside `BEGIN IMMEDIATE` and rolls back on any exception, and
  the operation record commits with the effect or not at all. Proved rather
  than assumed — see the refusal tests below.

## Implemented (PLAN items 2-4)

`src/baton_work/transitions.py` — `pass_work`'s in-lock gate now refuses an
unclaimed pass before any mutation, and the peer refusal is unchanged beside
it. The two are one sentence read from two sides: the actor releasing the claim
must be the actor holding it. `reroute_work` is untouched, and no implicit or
synthetic claim was added anywhere.

`src/baton_work/cli.py` — `pass` help says the actor must be the current
claimant and names `claim` and `reroute` as the two ways forward; `reroute`
help says it is the operation for work nobody holds.

`docs/BATON-WORK.md`, `docs/EFFECTIVE-BATON.md` — the protocol contract and the
operating guide state the rule, the reason it exists (the W1568 incident), and
the blocked/parked consequence below. The guide gains a short
**Reroute moves Work nobody holds** section: the ruling makes that operation
essential, and the guide taught `pass` without ever teaching its counterpart.

## The consequence the pinned decision did not state

**This is the one judgement I made beyond the pinned text, and it wants
review.** Measured, not inferred:

- `claim_work` refuses `block` and `parked` Work.
- `_recompute_ready` releases the claimant the moment a gate arrives
  (`finding-active-work-claim` R3), and a W159 blocking request does the same.

Together with this ruling, that means **gated and parked Work can no longer be
passed by anyone**, and `pass` can only ever land `queued` — a claimant's Work
is runnable by construction. The `block` destination phase that W38 and W73
pinned as part of the pass contract is now unreachable through `pass`.

Nothing about the derivation changed, and nothing is lost: `reroute` derives
the destination phase through the same `_unclaimed_state`, so a gated Work
moved by the owning team still lands `block` with its wake condition recorded
and still wakes on the sweep. That is coherent with the ruling — "moving
unclaimed Work is `reroute`" — but it retires a property two earlier records
pinned, so I did not delete those tests. Each is restated against `reroute`
with a dated in-place supersession note naming this record, keeping every
assertion it always made:

- `test_w73_route_derived_phase.py::test_a_gated_move_lands_waiting`
- `test_w38_scheduler_phase.py::test_a_gated_move_lands_waiting_and_can_still_wake`
- `test_w108_active_claim.py::test_a_blocked_move_lands_waiting_and_refuses_claim`

`pass_work` now names the phase in that refusal rather than sending the
operator to a claim that would refuse for a second reason. If review prefers a
different reading — for instance that gated Work should keep a passability
carve-out — the gate is three lines and the restatements are three tests.

## Observation filed separately, not acted on

`reroute_work` re-derives the phase through `_unclaimed_state`, which returns
only `queued` or `block` — so rerouting a PARKED Work silently un-parks it.
That is pre-existing behaviour this Work did not introduce, but this ruling
makes `reroute` the ONLY way to move unclaimed parked Work, so the interaction
now matters more than it did. Logged as its own finding rather than fixed
inside Work I am holding, per AGENTS.md:
`work/records/2026/08/finding-reroute-unparks-deferred-work/`, ledger Work
`W2645`, created with the dossier and bound to it.

## Adapting the suites (PLAN item 5)

The gate broke 146 tests across 38 files, all of them because setup moved Work
with an unclaimed `pass`. Two mechanisms, chosen so the adaptation cannot hide
the rule:

- `fixtures.hand_off()` — a documented TEST-ONLY claim-then-pass helper for the
  ~60 call sites whose subject is route selection, phase derivation, projection
  columns or episodes rather than pass authority. It claims only when
  UNCLAIMED, and `claim=False` suppresses it for op-id retries and for replays
  against closed Work, where acquiring anything would be wrong.
- `fixtures.post(pass_to=...)` states the same claim for its own pre-W2571 call
  sites — the identical shape, and for the identical reason, as the `wait=False`
  note W159 already left in that adapter.

Both docstrings say in terms that tests ABOUT pass authority call `pass_work`
directly and never come through them: routing those through a helper that
quietly claims first is exactly how a regression for this defect would stop
being able to fail. `test_w2571_pass_requires_claim.py` never uses either.

Suites where the pass IS the subject were hand-edited instead, and the
operator-facing workflow stories (`wf01`, `wf04`, `wf06`, `wf08`, `wf10`,
`wf12`, `wf13`), the gate scenario, the packaged archive and the packaged
console now claim explicitly — they are contracts, so they teach the rule.
`wf01` goes further and asserts both refusals in the narrative, including the
parked one, because that story is where an operator meets the phase.

## Regressions (PLAN item 5)

`tests/work/test_w2571_pass_requires_claim.py`, 19 cases on a two-handler
route with an alternate — the live incident's exact shape:

- an eligible handler cannot pass Work it has not claimed, and the refusal
  names BOTH ways forward;
- the second handler of the alternate route — the `baton.gemini` position — is
  refused, then claims and passes normally;
- route eligibility is checked BEFORE the claim, so a non-handler learns that
  rather than being told to claim Work they could never claim;
- the peer-underneath-a-claimant refusal still holds and stays textually
  distinguishable from the unclaimed one, and `reroute` refuses there too, so
  the claim has no side door;
- side-effect freedom on every axis the acceptance boundary names: the database
  file digest, the whole Work row compared field by field, the event journal,
  the sequence, messages, obligations, personal New counters, and the operation
  id — which stays unconsumed and then commits the corrected retry;
- a committed pass still REPLAYS after its own release left the Work unclaimed,
  because WS-5 answers a committed identity before the claim gate runs;
- blocked and parked Work is refused with its phase named and pointed at
  `reroute`, and a late gate on claimed Work ends its passability in one
  sequence;
- `reroute` still moves unclaimed Work on owning-team authority, the journal
  keeps the two operations distinguishable (`reason` versus `comment`), and
  moving a queue leaves no claim event — nobody has to pretend to execute;
- the whole lifecycle through the public CLI: the refusal W1568's pass should
  have received, then claim, then pass, with the journal proving a claim
  precedes every transfer.

Confirmed non-vacuous: with the gate reverted, 11 of the 19 fail.

## Verification (PLAN item 7)

- `test_w2571_pass_requires_claim.py` — 19 passed.
- Full v11 gate on the final tree — 2653 parallel, 51 serial, 55 ACP, all
  passed.

## State

Awaiting independent review.
