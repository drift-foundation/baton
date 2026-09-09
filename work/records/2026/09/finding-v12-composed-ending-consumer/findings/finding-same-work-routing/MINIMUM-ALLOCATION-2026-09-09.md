# Minimum ordinary handoff correction

W124786 claim125044, responding to owner124967 and M125007. This supersedes
the larger `ALLOCATION-PROPOSAL-2026-09-09.md` as the actionable proposal.
No additional test campaign was run; existing concrete session evidence proves
late pass refusal and the old-route reclaim interval. No source edit is made.

## Required transition

The ordinary path must move the Work to the next route while its original
quiescence gate still prevents a claimant from writing. Propose one narrow
Authority `route_fenced(expect, *, operation_id, fence_operation_id,
from_route, to_route)` act; use its committed receipt as the selected handoff
commit, associated by the consumer with its retained checkpoint/verdict.

For a new operation, in the Authority transaction require the exact original
v12 assignment and committed cancellation fence, current open/unclaimed Work,
unchanged generation counter, original `runtime-quiescence:<generation>` gate
and block phase, and the original from_route. Bind from_route to that
generation's committed claim authorization, not just today's caller operand.
Change only route, preserving phase/gate/generation/claim slots. The operation
journal atomically retains its exact assignment/fence/from-to/phase/gate
receipt. The participant-bound session cannot act for a different participant.
Exact replay returns the committed handoff before current eligibility checks;
changed operands collide. A new operation cannot retarget a later generation
or use an already moved route as if it were the original claim route.

**Removed from the earlier proposal:** fresh routing of arbitrary already-
discharged historical attempts, a migration/adoption mechanism, generalized
later-round recovery, and mandatory same-attempt intermediate continuation.
A lost handoff answer uses the same stable operation; uncommitted computation
may be discarded/repeated under the ordinary safe assignment protocol.
Intermediate journal/artifact commits do not themselves select a next stage
or require completing that attempt. Preserve their custody/history and any
committed external effect; unresolved external outcomes still hold.

The order amendment remains necessary to close the demonstrated reclaim race:
owned driver completion -> committed route change with gate intact -> positive
absence discharge -> local ending acknowledgement. This explicitly replaces
owner119712's discharge-before-route ordering for the composed fenced handoff.
At-fence route mutation would instead change cancellation/finalization and
checkpoint/verdict operands and signatures; this small post-fence act avoids
that provider cascade. No current gate can be bypassed by this transition.

## Reuse existing route operands; no configuration version change

Use the existing per-worker `review_route` for the ordinary outgoing route:
implementation's configured next route is review; review's configured next
route on acceptance is integration. For changes-requested, the retained
checkpoint identifies its writer and producer attempt; existing public
`claimed_offers_for(control, producer_attempt_id)` supplies that attempt's
original `work_route`. Require exactly one correlated committed claim, not a
current Work projection or a guessed role/participant mapping. The current
single-worker `_claim` already consumes this reader.

Configure those existing operands explicitly in the fixture/deployment. No
new stage_routes map, `/2` deployment schema, manager selector or private SQL
crossing is needed. The earlier statement that a new route map was required is
superseded by this public committed-claim route source. A correction is opened
only after its handoff is committed; held outcomes select no route.

## Exact proposed allocation and execution order

One High provider, proposed baton.tune returning baton.bug, disjoint from the
currently assigned W125032 adapter paths. Reserve these five existing paths:

- `v12/python/src/baton_v12/authority/core.py`
- `v12/python/src/baton_v12/authority/session.py`
- `v12/python/tests/authority/test_assignment.py`
- `v12/python/tests/authority/test_session.py`
- `v12/python/REVIEW-CYCLES.md` (document the selected handoff and intact gate)

Tests additive, including any additive exhaustive transition member. No schema,
existing cancel/pass behavior or unrelated assertion changes. Focused proof:
ordinary move with gate intact; next role claims only after discharge; original
route cannot reclaim; foreign/stale/non-fenced/ungated attempts refuse; exact
lost-answer replay preserves one route effect. Cumulative20s, declared before
execution. Reuse existing generation/journal tests; no broad recovery matrix.

After independent provider and W125032 acceptance, W122060 consumes the new
direct session capability in its existing four paths, with the explicit order
amendment and existing route operands. Add actual ordinary review/correction/
acceptance handoff controls and retain the already authorized test conversions.
The W125032 negative wrong-route case remains negative; add a separate positive.
Preserve all other assertions and all shared provider/ending schemas.

First drive the actual composed one-Job fixture through review, correction,
accepted integration and terminal handoff; the exact failed ordinary transition
determines any next repair. Then one committed-handoff lost-answer restart and
safe scratch abandonment establish the narrowed restart boundary. Ordinary E2E
is progress, not full restart/custody acceptance. No same-attempt cutpoint or
pre-intent adoption portfolio is reintroduced.

## Decision

Approve or amend this five-path provider (tune may run alongside disjoint
W125032), its original-fence handoff contract and the consumer order amendment.
Create its separately bound Work and actual-acceptance gate before this research
closes. This is the one outstanding ordinary routing allocation, not a new
research portfolio. The earlier new-schema/map proposal is withdrawn.
