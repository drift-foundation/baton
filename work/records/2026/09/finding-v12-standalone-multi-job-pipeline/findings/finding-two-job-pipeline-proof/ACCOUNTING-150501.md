# Partial accounting implementation; exact product-reader gap

Owner150498; tuner claim150501. The approved accounting rule is pinned in
FINDING/PLAN. This return is **incomplete**, through baton.bug Next baton.ops,
for the exact missing public contract the owner instructed be returned.
No independent acceptance or executable proof package is claimed.

## Implemented and checked

`prepared-150501/accounting.py` implements elapsed claim time minus the clipped
union of bound judge intervals, cumulative integration120, individual judge180,
implementation240/original review180, whole1200, matching historical claim endings,
winning-clock data, and stale-alarm wake versus definitive whole expiry. Active
judge clocks remain eligible alarm winners while integration is paused. Ended
claims use the same calculation; no reset or double credit.

`prepared-150501/run.py` connects this core to evidence/alarms, includes the fifth
helper in required review bindings, retains known Job failure before new reader
failures or telemetry, and keeps whole-run protection through final tests and
source/target acceptance. Final tests require positive remaining time and use
min(30, remaining whole). New accounting evidence identifies charged/excluded time
and the chosen/expired clock. Existing containment, final test, source/target,
resource, observer and credential guards remain.

The partial BoundJudges reader uses a bounded no-follow subject locator, public
read-only coordinator result_of, immutable subject/result/policy/Job/stage/attempt/
assignment cross-checks, original configured judge Works/participants/generation1,
sealed report consistency, and a planned public launch/exchange observation path.
It **refuses before granting credit when the required WorkspaceGroup capability
cannot be acquired**. The runner currently cannot supply that capability. This is
not a completed prompt derived-judge failure implementation or a live-tested
accounting pipeline. Do not execute it as a model proof.

Offline verification: **82 pass**, the prior63 package cases plus19 new cases.
The new cases cover retained run9 arithmetic (0.158s integration charged and
60.158s verification remaining at the old deadline), overlap, gaps, clipping,
completed-between-polls overruns, repeated polling, absent/wrong bindings,180/120/
1200 expiry, final-test remainder, stale alarms, required owner refusal and the
explicit missing-capability refusal. Synthetic owner/config fixtures are labelled;
no successful live bound-judge read, actual B import or both-terminal proof follows
from them. The remaining judge failure/acceptance and fully joined runner cases
must be completed after the public reader boundary exists.

Changed tests are confined to the new package: additive test_accounting.py;
three copied files test_stats_observation.py (observer injection, fifth helper,
new alarm evidence), test_run9_preparation.py (historical runner equality checked
against its actual old package, permitting this assigned runner delta), and
test_image_preparation.py (fifth helper digest). Original tests were untouched.
The first82-case run had two fixture/metadata failures and a real missing
`docker_stats:null` failure-sample regression. All were corrected; failing output
is retained beside the final pass. No assertion was weakened to hide a required
failure. All unchanged image/task/diagnostic tests remain green.

## Exact missing contract

The source contracts are digest-bound in evidence/accounting-150501/preservation.json:

- `v12/python/src/baton_v12/worker_manager/exchange.py:409`: `_gid` accepts only
  WorkspaceGroup, explicitly rejecting the integer in frozen deployment config.
- `worker_manager/workspaces.py:339,498`: WorkspaceGroup cannot be caller-minted;
  only configured_workspace_group reads the manager's own projection and committed
  configuration to mint it. The public constructor probe refuses policy/denied.
- `worker_manager/store.py:243,254`: ControlStore exposes ordinary open, which may
  initialize an absent/empty store and request a persistent journal mode. There
  is no public open_readonly. The helper must not add a raw SQLite connection,
  private mint token or write-capable fallback to supply the group.
- `tools/stage_execution.py:4502,4553`: StageObservation requires a caller-supplied
  control handle and selects allocated Job stages; the separate derived-judge
  Works have no such Job-stage allocation. Passing a made-up stage would not
  supply the required exact owner observation.

The smallest requested product assignment is a supported non-writing manager
handle compatible with configured_workspace_group (or an equivalent public,
read-only derived-judge observation factory that internally acquires this owner
capability). It must read an existing recognized store, refuse missing/foreign/
inconsistent state, carry no acts, and release all handles. It must expose the
exact judge attempt/assignment exchange and retained outcome without synthesizing
Job-stage allocations. No new worker, provider, protocol or image behavior is
requested. The owner may select the existing suitable public composition if one
was missed; none was found in the inspected sources. This is a concrete capability
acquisition gap, not authority to redesign the product under a proof claim.

The new helper accepts an already-owned WorkspaceGroup for a later composition;
its default explicit refusal is retained. No private mint, raw store, serving
factory or unvalidated provider-file parser is used as a workaround.

## Separate coordinator-opener finding

The explicitly authorized supported read-only re-probe still refuses run9
integration.sqlite3: ContractRefusal(refused, precondition), underlying
OperationalError: unable to open database file. Mode0644 uid1000/gid1000;
WAL/SHM absent. Existing public opener source documents that SQLite may create or
maintain its own sidecars even for mode=ro, so absence alone is not a defect
proof. The managed external root is outside repository writable roots. A
sidecar-access restriction is a plausible operational explanation, not a proven
root cause. No raw database read, copy, alternate connection, manual sidecar,
permission change, checkpoint or repair was attempted. A host-authorized operator
can inspect this exact supported opener boundary; it must work before the live
proof helper can depend on it. The helper propagates required read refusal.

`evidence/accounting-150501/inspect_readers.py` and reader-findings.json preserve
this result and the capability probe. Historical run9 coordinator final state
remains unverified here. A completed; B's accepted review/approval and interrupted
verification remain the prior qualified facts, not a completed B import.

## Remaining scope and handoff

1. Owner assigns the exact product reader contract above and resolves the
   coordinator operational read boundary through supported operations. Product
   files remain outside this tuner assignment; no product bytes were changed.
2. After that independently accepted contract, resume this partial package:
   supply the owned read capability; finish and verify live-capable correlated
   derived-judge rejection/unable/fault/lost handling and frozen-report paths;
   verify exact completed/current assignment timing and stale snapshot/alarm
   races in the joined runner; retain all three real accepted current-policy
   receipts, import/lease/causal checks, final clean target and both-terminal
   predicates. Do not mistake the partial reader branch for an accepted result.
3. Return exact implemented bytes for independent review. Only then prepare any
   separately authorized fresh attempt and genuine input bindings. Run9 is
   consumed; no model retry or historical repair is authorized by this return.

The new package copies old run9 scripts/tasks/policies/recipes only as baseline
fixtures and carries no selected-images.json or execution-review.json. README
explicitly forbids live execution. Its copied evidence/ directory is historical;
current evidence is exclusively evidence/accounting-150501/. Existing198 accepted
input files, the19-file reconciliation and both genuine run9 markers verify exact.

Current measured checks total0.697225147014251s (failed suite0.3458666389924474,
passing suite0.3405658950214274, reader probe0.00021762499818578362,
preservation0.010574988002190366). Cumulative50.928639052884776s plus recorded
untimed/older-failure/host/model-billing/rounding uncertainty. Nine failed runtime
walls2002.0388815780316s remain spent; no model runtime in this claim.
Preserve all resource/success/custody rules and W144335/W144813/W136578/W129838/
fault-C/H7/general-resilience deferrals and run5/run6 uncertainties.
