# Integration observation contract, revision1

Pinned by baton.codex under owner M126545 before implementation of W126558.
Producer/consumer: W122060 deployment. Receiving boundary: W126558 Job manager.
This is an in-process, read-only observation document; no persistent schema,
new stage status or exchange vocabulary is introduced.

## Capability and outer shape

`observe_integration(stage)` is optional and returns None or the document below.
ManagerOperations accepts it as an optional named callback. Its canonical
observation gains an optional `integration` member, normalized to None when
absent. Older observation dictionaries and deployments remain accepted with
their exact previous behavior. `_Observing` extracts this member by name from
the observation factory and passes no serving object or runtime-refresh verb.

None means no integration observation is supplied. It preserves prior behavior;
it is neither completion nor permission to invent an assignment. A supplied
document is accepted only for an integration stage with a canonical claimed
offer and an activated fixed assignment. Before activation the callback returns
None; ordinary claim/launch scheduling still applies.

Every document has exactly these keys:

```text
schema: "baton.v12.integration-stage-observation/1"
stage_id: nonempty identity
episode: positive integer (not bool)
attempt_id: nonempty identity
offer_id: nonempty identity
assignment: canonical fixed assignment document
state: "unstarted" | "pending" | "answered" | "completed" | "held"
completion: null | completion document below
```

`assignment` has exactly the existing assignment shape: work_ref with
authority_uuid/work_id, participant, generation. Use existing validators and
compare it to `observed.runtime.assignment`, not today's live Work assignment.
stage_id/episode/attempt_id/offer_id must equal the requested stage operands;
offer_id must also equal the acquired claimed_by identity. The existing
canonical offer binding remains in force. Non-null documents from an unclaimed
or unactivated attempt cannot authorize an act or be projected as completion.
Do not choose another attempt's assignment to make a document fit.

Malformed/unknown documents refuse with the existing ContractRefusal
integrity/schema vocabulary; conflicting ownership refuses with
refused/operation-collision. Known held state remains a visible exceptional
stage. Use the existing per-stage containment/reporting behavior; do not catch
unrelated programming failures or broaden the general exception policy.

## State meanings and scheduling

Earlier durable act refusal, failed preparation/start and ended-episode rules
retain their precedence. A valid integration observation then takes its own
path, without relying on worker frozen output or exchange. It cannot override
those earlier failure records.

| Observation | Existing projected state | Owed act |
| --- | --- | --- |
| unstarted | claimed, only with runtime not-started and no attached runtime | existing launch |
| pending with running runtime | integrating | none; normal refresh continues |
| pending with quiescent/destroyed runtime | answering | conclude, so the driver decides missing/lost-result disposition |
| answered | answering | conclude; owned result or terminal handoff still needs consumption |
| completed | completed | none |
| held | exceptional | none |

Uncertain runtime is exceptional with no automatic conclude for unstarted,
pending or answered. A pending/answered document without a started runtime
identity is inconsistent and fails closed. Contradictory unstarted evidence
also fails closed. An answered file while the runtime still runs cannot earn
completion: conclude delegates to the existing driver, which retains its own
quiescence checks and may return running. Merely calling conclude changes no
Job state; the next observation must prove the result.

Completed is historical committed evidence for the fixed assignment. It does
not require that assignment to be today's live assignment or today's Work
route to remain the destination. The consumer must first prove the committed
account below; a later assignment cannot undo or substitute for that proof.
No local flag or prior in-memory result is sufficient.

## Completion account

completion is null for every state except completed. Completed requires a
dictionary with exactly these keys:

```text
proposal_id: nonempty identity
integration_receipt_id: nonempty identity
entry_id: nonempty identity
lease_id: nonempty identity
fence: positive integer (not bool)
handoff_operation_id: nonempty identity
to_route: nonempty text
runtime_id: nonempty identity
execution_runtime: "quiescent" | "destroyed"
```

These identifiers are references to evidence the deployment has read and
cross-bound through accepted public readers, not proof by their mere presence.
The consumer verifies the integration receipt's proposal/candidate/target;
the exact entry/lease/fence/attempt and integrated settlement/released lease;
proved worker exclusion for this runtime; and the Authority's committed
pass_work operation on the outer fixed assignment to the worker's configured
outgoing review_route. The execution_runtime member reports that proved
exclusion account, not an inference from a worker result. The consumer keeps
all stronger provider preconditions, including positive absence where required.
The provider validates the closed shape and bindings; it does not open another
owner's store to recreate the consumer's proof.

In particular, coordinator producer assignment provenance must not replace the
current integrator fixed assignment. In the retained repro those generations
are3 and5. An integration receipt/settled entry without the terminal handoff
remains answered, not completed. A lost handoff answer remains owed until its
fixed operation is read/replayed; unknown external outcome remains held.

The read-only consumer must not call admit_accepted, continue_accepted,
pass_work, refresh, cleanup, pool activation, credential minting or any other
external act to build this document. Retained committed accounts must survive
reconstruction. Implementing their production discovery is W122060's two-path
consumer work after independent acceptance of this provider.
