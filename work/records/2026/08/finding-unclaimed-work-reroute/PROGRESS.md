# Progress — implementer

Work `b06383c8-W128`. State: **awaiting review**.

## Revalidation (PLAN step 1)

The defect reproduces exactly as recorded, and I hit it from the other
side of the same incident: W30 and W39 were both routed to `impl2` while
the runner that route resolves to was not taking them, my readiness kept
offering them to me, and every claim refused. The only path the
authority offered was to wake that runner so it could hand over Work it
had never touched.

`pass`'s boundary is right and is not what changed. `_handler_gate`
restricts a pass to the resolved route handler because a pass is the
baton changing hands, and moving Work underneath somebody who holds it
would be the W171 defect. What was missing is that this reasoning has no
force when NOBODY holds it: there is no executor to protect, and the
gate was protecting a runner's exclusivity over Work it had not taken.

## What was implemented

**`reroute work= to= [route=] reason=`** — a new public transition whose
authority is OWNERSHIP rather than route eligibility. Any active member
of the Work's owning team may correct where unclaimed Work is offered.
Route eligibility still decides who EXECUTES; the owning team decides
where its own work is queued.

Everything is decided inside the write lock: the owning team, the
absence of a claim, the no-op comparison (endpoint AND selected route,
since selecting an alternate on the same endpoint is a real move), and
the destination resolution — so a regen that withdrew the alternate
between the operator's choice and the commit refuses rather than
silently routing to the default. The claim/reroute race falls out of
that: exactly one commits against the observed unclaimed state, and the
loser refuses having changed nothing.

Preserved deliberately: identity, binding, messages, dependencies,
containment, priority, classification, and the planned Next. The phase
is re-derived only to assert that a route change moves nothing about
readiness. A new assignment episode is minted, because the Work is now
offered to a different set of handlers and they must be woken even if it
was delivered to them before.

`detail` advertises `reroute` to owning-team members exactly while the
Work is unclaimed, and it disappears the moment somebody claims —
discovery matching what the writer would grant, rather than
discovery-by-attempt.

## One correction outside this record, and why

`test_both_projections_agree_about_the_new_route` failed on a defect
that is **W30's subject**: `projection.links`'s far-row resolution
dropped `route_selected`, so `links` reported the default route while
`detail` reported the alternate. Two views disagreed about which agent a
neighbour is offered to.

I fixed it here, in one call, because **this record's own Required
behavior says "project the new Route consistently through direct and
linked Work views"** — a reroute whose result the linked view
contradicts has not met W128's boundary. The comment at the site names
W30 as the record that identified it first.

**For the reviewer:** W30 is still open, unclaimed, and routed to
`impl2`. Its remaining scope may now be empty, or may cover more than
this one call — that is a judgement about W30's contract, not mine to
make. W128 itself is what makes W30 movable without waking the runner
that is not taking it, which is a pleasing way for this to have closed
the loop but is not a reason to absorb it silently.

## Tests

`tests/work/test_w128_unclaimed_reroute.py` — 19 cases on a fixture
whose `lang.impl` offers an alternate to a different member: W30's exact
situation rerouted off the alternate; primary-to-alternate; a different
endpoint entirely; every other column of the Work row asserted
byte-identical across the move; the planned Next surviving; no-op
refusal in both spellings; the foreign-team refusal with the Work
unmoved; terminal refusal; claimed refusal plus both stated
alternatives (the claimant passes, or a release comes first); a required
reason; a withdrawn alternate refusing rather than falling back; the
claim/reroute race in BOTH orderings with the loser proved to have
changed nothing; an exact retry replaying through `op-id`; the
correction appearing in Work Events and not as a Message; direct,
linked and tree projections agreeing; readiness moving to the new route
and leaving the old one; and the CLI surface.

## Existing tests changed

- `test_phase.py` — its availability matrix asserted that `prioritize`
  was the ONLY ownership operation offered to a non-handler owning-team
  member. W128 adds the second one by ruling, so `reroute` joins that
  closed set. The test's question — participation must not leak
  ownership operations — is unchanged, and the claimed case below it
  still sees neither.

Nothing else needed touching. `test_w245_route_and_current.py`'s guard
against the word "current" meaning route eligibility caught my first
draft of the verb's help text, which said "rather than the current
route's"; the help now says "rather than the resolved route handler's".
That guard was right and the wording is better for it.

## A W93 review test that landed while this was in flight

`test_w93_runtime_state.py::test_reusing_a_superseded_incarnation_refuses`
arrived from that Work's review and was red on this tree. It is correct
and my R2 fix was too narrow: I checked only the CURRENT lease, so a
superseded incarnation could come back and displace the runner that had
replaced it. The guard now consults the runtime JOURNAL — one
incarnation is one launch for the life of the record, not merely while
it occupies the current row — with the diagnostic still distinguishing
live, ended and superseded, because the operator's next move differs in
each. That is W93's fix, made here only because it was failing here;
it is reported in this handoff rather than folded in silently.

## Verification

- Focused: `tests/work/test_w128_unclaimed_reroute.py` — 19 passed;
  `test_w93_runtime_state.py` — 39 passed including the review's new
  case.
- The complete v11 gate, `just test-v11`, exits 0 on this tree: **2063
  passed** (parallel), **40 passed** (serial), ACP acceptance green.
