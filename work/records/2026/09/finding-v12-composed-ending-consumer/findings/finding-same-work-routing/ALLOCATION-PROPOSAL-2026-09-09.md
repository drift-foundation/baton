# Proposed fenced routing contract and allocation

Research W124786 claim124840; **owner decision required before implementation**.
No protocol or consumer change is authorized by this document.

## Confirmed baseline

`evidence/probe-124840.py` drives the real participant-bound Authority session
over a disposable existing Authority fixture. A successful generation1 cancel
leaves route `impl`; a subsequent pass refuses “assignment generation was
fenced and ended.” After absence evidence discharges the gate, the original
implementer can claim generation2. Replaying the original cancel then returns
its original receipt without changing generation2. Runtime0.0022s under the
declared1s bound. No live store or application file was changed.

Owners: `authority/core.py` claim, pass_work, cancel and _end_assignment;
`authority/session.py` closed transition set and participant binding;
`worker_manager/attempts.py::finalize_quiescent_assignment`; review_cycles.py
freeze_checkpoint/record_verdict; `tools/stage_execution.py::routed`.
Checkpoint/verdict retain the finalization intent's Authority operation id.
Authority schema already retains generation_counter, fenced_generation,
assignment events and the operation journal. No schema addition is proposed.

The deployment schema `/1` has stage-role workers and each single-worker
`review_route`, but no explicit route map for review correction versus accepted
integration. A stage role or participant name is not an Authority route. Do not
infer those routes or broaden route-handler grants to make the fixture pass.

## Proposed result

Add one Authority transition `route_fenced(expect, *, operation_id,
fence_operation_id, from_route, to_route)`. It changes only the Work route.
Its original participant session owns it; it is not an unrestricted reroute.

On a fresh operation, atomically validate all typed operands and the original
committed `cancel` operation: exact Authority/Work/participant/nonboolean positive
generation, fenced true, cancelled cause and that generation's quiescence gate.
Validate the committed signature/result and corresponding retained fence facts,
not merely a caller-supplied receipt. Require open v12 Work, no current Handler,
generation_counter exactly the ended generation, and exact from_route. Permit
only queued/ungated or block/the original quiescence gate; refuse parked,
terminal, foreign gates, later claims (even if later released), unrelated end
causes, missing/foreign/uncommitted fence records and mismatched old route.
Keep phase, gate, generation, claim slots and assignment events unchanged.

The existing operation journal atomically records the route change and a closed
receipt containing the original assignment, fence operation id, from/to routes,
unchanged phase and gate. Exact operation replay precedes current eligibility
checks, including after a later legitimate claim. Changed operands under the
same identity collide. A new operation for the original from_route cannot
overwrite an already moved route. The session must reject another participant
even on replay. This is a proposal for explicit new authority, not an existing
assignment-owner privilege inferred past termination.

**Recommend a narrow order amendment:** driver completion, fenced route change
while retaining the gate, positive-absence discharge, then ending settlement.
This explicitly supersedes owner119712's discharge-before-routing order for
these composed fenced endings only. It removes the newly proved interval in
which the old route is ungated and can reclaim. For old records already
discharged, permit the same exact-generation unclaimed route act; refuse if
any later generation has claimed. Never cancel or repurpose that later claim.
Ordinary no-fence behavior stays unchanged; this act cannot fabricate a fence.

At-fence route movement could be atomic too, but would require a route operand
through cancel, finalization, checkpoint/verdict and their durable signatures,
and still would not route existing committed fences. The separate narrow act
supports both retained history and new endings without modifying those owners.
Leaving routing after discharge is a possible owner choice, with the explicitly
retained old-route reclaim race and refusal rather than automatic recovery.

## Proposed implementation ownership

Create a separate High baton.impl provider, returning baton.bug, owning exactly:

- `v12/python/src/baton_v12/authority/core.py`
- `v12/python/src/baton_v12/authority/session.py`
- `v12/python/tests/authority/test_assignment.py`
- `v12/python/tests/authority/test_session.py`
- New ordinary non-executable `v12/python/FENCED-ROUTING.md`

Tests additive, including necessary additive exhaustive transition-registry
members. Preserve existing pass/cancel assertions, schema and other files.
Prove successful routing with gate preserved, successful already-discharged
history, concrete foreign-session refusal, all stale/foreign/typed negatives,
reopen and lost-answer replay, and transaction races with claim/discharge.
Retain exact hashes/modes and cumulative20s focused verification; no inventory
expansion. Independent provider acceptance gates W122060 before consumption.

**Amend W122060's existing four-path allocation**, after that acceptance:
`tools/single_worker.py` forwards the exact new capability; stage_execution.py
owns the typed receipt and stable operation identity derived from original
stage/episode/attempt, with replay using original fixed operands. Add a closed
`stage_routes` map (implementation/review/integration text values) in a new
stage-execution deployment `/2` schema; reject `/1` explicitly rather than
silently choosing routes. No other schema changes. Configuration changes cannot
redefine a pending route operation: conflicting replay refuses visibly.
Implementation ends route to review; changes-requested review routes to
implementation before opening correction; accepted review routes to integration;
held outcomes route and settle nothing. Preserve independent principals.

Authorize bounded fixture/configuration updates in the two existing consumer
test files solely for `/2` and the explicit map, retaining assertions unless
the version/required-map behavior intentionally changes. The already approved
two defect-test conversions remain exactly scoped. Add real same-Job routing,
pending-gate, lost-answer, old-ending/later-round and no-fence controls. No
consumer edit to shared ending/provider schemas or their private storage.

## Decision requested

Approve or amend the named transition/security contract, five-path provider,
consumer `/2` mapping scope and bounded test updates, and the explicit
route-before-discharge order amendment. Then create/bind the provider and its
actual-acceptance dependency before closing this research. W122060 and W119114
remain unaccepted; research completion does not discharge their routing gate.
