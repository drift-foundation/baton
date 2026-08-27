# Carry principal-aware execution context through the Worker Manager

## Discovery and ownership

Discovered by W16793 as the Worker Manager consumer of the authority correction
in W16821. Ledger Work W16823 is bound to this record. The record is promoted to
a top-level dossier because the discovery record already occupies the permitted
second child level.

## Confirmed incompatibility

The Worker Manager correctly fences an execution by the frozen four-part
assignment `(authority UUID, Work id, participant, generation)`, but it treats
that endpoint participant as every identity needed below the authority:

- `worker_manager/authority_port.py` exposes a `participant`-bound port, calls
  `slot_holder(participant)`, and accepts claim answers containing only the
  four-part assignment;
- `worker_manager/schema.py` persists `offers.participant`,
  `attempts.assignment_participant`, execution `agent_sessions.participant`
  and interrogation assignment participants, with no principal or effective
  authorization context;
- `worker_manager/attempts.py:_runtime_labels` labels runtimes by authority,
  Work, participant and generation;
- `worker_manager/documents.py` seals `assignment` and `runtime.labels` to those
  same fields.

The four-part assignment remains useful operational fencing and must not be
weakened. It is insufficient for W9901's separate canonical principal and
authority-derived effective scope: two endpoint addresses mapped to one
principal produce unrelated runtime labels, stores and capacity observations,
and no retained record explains which scope/grant authorized activation.

The frozen worker-control and agent-session 1.0 schemas also use the four-part
assignment with sealed objects. That is not automatically a defect: the
sandboxed agent needs a fenced execution reference, not authority to choose its
principal or scope. Changing an existing required identity field would require
a new major protocol version under the frozen version rules. This Work must
first keep the authorization context on the trusted manager/adapter side and
only version a wire contract if a concrete remote consumer must receive it.

## Required correction boundary

1. Consume W16821's authority-owned claim/assignment projection with canonical
   principal, effective scope and authorization provenance in addition to the
   existing endpoint assignment.
2. Persist that context atomically with offer acceptance/claim activation and
   include it in manager replay signatures wherever changing it would change
   authorization meaning.
3. Label and reconcile execution runtimes by principal-global identity as well
   as the existing assignment fence, so two endpoint spellings cannot create
   two supposedly independent runtime identities for one principal.
4. Keep consent posture pre-claim and authority-free. Keep workers unable to
   select or mutate principal, scope, grant or policy generation.
5. Preserve the exact four-part assignment for generation fencing. Treat
   participant as an operational endpoint, not as proof of the principal.
6. Do not alter frozen 1.0 worker-control or agent-session meanings by stealth.
   If a wire-visible field is proved necessary, create the explicit negotiated
   version/provider Work required by the frozen compatibility policy.

## Acceptance

- With endpoint addresses `org_a.worker` and `org_b.worker` mapped by the
  authority to one principal, offers and attempts retain the same principal
  identity and cannot evade principal-global capacity/runtime reconciliation.
- An injected claim answer with a well-formed but wrong principal, effective
  scope, authorization provenance or policy generation is refused before a
  manager row or runtime is created.
- Replay under the same operation identity collides when the authorization
  context differs; an exact replay preserves the original result.
- A worker/agent input cannot supply principal or scope, and no new Baton,
  SQLite, repository or canonical-write capability crosses the isolation
  boundary.
- Existing assignment generation, runtime adoption, cancellation and cleanup
  tests remain green.
