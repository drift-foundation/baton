# Public contract — provider A, owner128669

Pinned by baton.codex under W119114 claim128673 before implementation. This
finalizes names/operands within the approved boundary; it adds no path or policy.
All three operations are exported from worker_manager.intake and worker_manager.
Documents are plain JSON-shaped values, validated at this module's owned boundary;
no new document registry/schema allocation is implied.

## Read committed cleanup

`abandonment_cleanup_of(store, *, attempt_id, retention_policy_digest)`

Return None only when no complete committed abandoned cleanup exists for that
selection. Invalid/foreign/colliding records refuse as ContractRefusal; a merely
recorded intent, failed removal or uncertain runtime never supplies successful
absence. Reading creates no transaction journal entry or external act.

A successful result has exactly these members:
- schema: `baton.v12.abandoned-cleanup/1`;
- attempt_id, assignment (the existing canonical fixed assignment reference),
  runtime_id, retention_policy_digest;
- intent: the original closed abandonment-intent document;
- intent_digest: digest of that exact document;
- fence: the original committed Authority fence answer;
- cleanup: the original committed abandoned-cleanup result, including its
  operation identity/signature and positive-absence/retained outcome.

Re-read the owning attempt/declaration/journal; compare the complete operation
kind, stable identity, signature, result shape and all assignment/runtime/policy
bindings. The committed result of runtime.destroy-abandoned carries intent,
fenced and cleanup: adopt that owned evidence, not an answer invented by the
caller. Compare the original fence operation and exact runtime-quiescence token,
fixed Authority/Work/participant/generation, declaration digest, removal and
provider-ending settlement. Changing the row's runtime or assignment may not
reuse another signature's absence. Unsupported cleanup families remain absent
or refuse; they never become abandoned cleanup. Historical successful reads do
not depend on the Work's current route/gate or a still-active assignment.

## Discharge and read the receipt

`discharge_abandoned_quiescence_gate(store, port, *, attempt_id, retention_policy_digest)`
`abandoned_gate_discharge_of(store, attempt_id)`

The act derives every Authority operand from the validated cleanup above:
original Work/Authority, participant, generation, runtime, gate and absence.
Require the exact session participant and Authority ownership before a new
remote act. Use existing port.satisfy_gate; perform no destruction, runtime
refresh, writer/line transition, collection, publication or stage replacement.

Use a family-specific stable operation identity and signature, distinct from
ordinary discharge, incorporating the full original assignment and cleanup
operation identity/signature. Journal the remote answer only after it commits.
Return/read a closed receipt with exactly:
- schema: `baton.v12.abandoned-gate-discharge/1`;
- attempt_id, assignment, runtime_id, retention_policy_digest;
- cleanup_operation (the original operation_id/signature_digest pair);
- operation_id (this discharge's stable remote/local identity), gate, evidence;
- authority_receipt (the exact public satisfy_gate answer).

Gate is the original runtime-quiescence:<generation>; evidence is the existing
runtime-absent document naming the positively absent original runtime. Validate
the public Authority answer using the accepted gate-discharge semantics; never
manufacture its fields. Read None if there is no committed discharge; invalid
owned records refuse. Readers perform no external act.

Recognize exact committed local replay before mutable Work state; after a lost
local acknowledgement retry the identical remote operation so Authority replay
returns the original answer even if the Work advanced. Changed operands collide;
missing/foreign/incomplete cleanup or a newer gate cannot be discharged using
old evidence. Readers/replays preserve historical identity without minting a
session or modifying the ordinary gate-discharge reader/contract.

## Bounded proof and handoff

Add real-store tests for successful explicit abandonment -> exact absence ->
discharge/read/replay; lost remote answer/local receipt; later Work generation;
foreign Authority/participant/attempt/runtime/signature/policy; incomplete,
running/uncertain/failed cleanup; and unchanged ordinary-family behavior.
Use existing disposal fixtures, no live deployment. Declare exact selectors and
enforce20s cumulative across iterations; retain commands/logs/wall times.
Return full candidate bytes/hashes and exact public names to baton.bug. Provider
B consumes these public owned documents only after independent acceptance.
