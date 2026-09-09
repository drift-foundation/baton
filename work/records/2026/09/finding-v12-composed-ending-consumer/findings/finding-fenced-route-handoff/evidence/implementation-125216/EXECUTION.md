# W125189 verification — baton.tuner claim125216

Before execution: cumulative20s wall-clock budget, including iterative runs.
Question: does the new original-fence route act atomically bind the committed
claim/cancellation and preserve the runtime gate, generation and claim slots,
so only the next route can claim after positive absence? Does exact lost-answer
replay survive current Work movement while changed operands and fresh stale,
foreign, unfenced or ungated requests refuse?

From `v12/python`, `PYTHONPATH=src:.`, first run `python3 -m unittest -v
tests.authority.test_assignment.FencedRouteHandoff
tests.authority.test_session.FencedRouteSession`. Then run the two affected
modules `tests.authority.test_assignment tests.authority.test_session` within
the remaining budget. A retained runner records exact commands, elapsed time
and output and enforces the remaining budget. Inspect the five-path diff,
preserve all prior test assertions except the authorized additive transition
member, and record final hashes/modes and whitespace results.

No consumer changes, ordinary one-Job E2E, generalized recovery matrix, live
runtime or inventory run belongs to this provider verification. W122060 and
W119114 retain their separately accepted consumer/lifecycle proof boundaries.

## Results

Both declared runs pass:15 new focused controls, then88 tests across the two
affected modules. `verification.json` records the exact commands and both full
logs; cumulative test wall time0.269s. The retained `audit.py` passes in0.046s,
approximately0.32s combined, within20s. No failed iterations or further runs.

The AST audit proves every pre-existing application method and test remains
unchanged, with the sole prior test edit being the authorized additive
`route_fenced` transition member. Session changes add its operand shape and
assignment-first dispatch membership. The documentation adds one handoff
section and preserves every prior byte. Scoped whitespace checks pass; original
file modes are preserved. `final.json` binds the five exact candidate hashes
and modes; `final-*` retains their bytes and base-relative patches.

The controls cover route-only atomic commit, preserved unrelated claim capacity,
both roles held behind the runtime gate, next-role-only claim after discharge,
original claim-route provenance, foreign/stale/unfenced/ungated refusals,
cancellation identity, changed-operand collision, rollback on journal failure,
participant-bound session access and exact replay after reopened-store/later-
route movement. Independent acceptance and consumer wiring remain outstanding.
