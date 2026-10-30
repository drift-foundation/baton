# W371073 — safe adapter refusal through existing diagnostics

Proposal, not an approved wire contract or implementation. baton.codxpc, claim E371189, owner E370866. Independent review returns to baton.bug; W370747 joins the plans and obtains owner approval before DESIGN or product changes. W371076 consumes this proposal. All versions below are proposed, not installed compatibility claims.

## Revalidated baseline

**Observed:** ClaudeAgent._selected raises TaskRefusal for invalid shared declarations, including a required output that the current role does not write. TaskRefusal is also used elsewhere; its class alone does not establish a declaration cause. The worker exchange loop catches arbitrary exceptions and publishes fault_code=agent. _faulted publishes a correlated terminal with no exception text. The manager exchange reader accepts terminal/1, a closed fault vocabulary, and an exact reachable receipt/state/terminal history. Generic exception secrecy is intentional and must remain.

**Observed:** W333486's accepted failure_cause composition describes cessation intent/outcome, start/preparation failure, token/runtime/cleanup facts. Its cause.component is expiry-reclaim, settlement or cancellation, not the adapter. Delegation observes the exchange and separately composes diagnostics; projection publishes both under Job status/7. The supported report reads diagnostic/1 and validates each fact without echoing rejected values. Status/report are read-only. The accepted review is baton:work/records/2026/10/finding-v12-attempt-failure-diagnostics/review-2026-10-22T18-36-05Z.md. Preserve its cessation answer and absence semantics, recording degradation and execution-limit provenance.

**Inferred:** a typed adapter-owned refusal can cross the existing terminal and diagnostic boundary without a second journal or logging platform. A present durable exchange terminal is sufficient evidence of what the worker reported, not independent proof of the declaration defect, provider execution, cessation or acceptance. Deleted/unreadable historical exchange evidence cannot retrospectively establish a cause.

Source hashes and exact current symbol anchors are in evidence/claim-371189/SOURCES.json. Earlier exploratory job_manager/exchange.py locator did not exist; the verified owner is worker_manager/exchange.py. PROGRESS.md did not exist at assignment start and is created here. Neither missing exploratory path is treated as read evidence. Source line numbers drifted during prior Work; this proposal binds hashes and symbols, not remembered offsets.

## Narrow producer contract

Introduce a worker-owned AdapterDeclarationRefusal type in the shared worker boundary, used only at explicit pre-provider declaration checks. It is not a general TaskRefusal serializer. Construct it from built-in literals and validated role selection, never exception text, class name, repr, a provider record or inferred string matching. The adapter changes the selected shared-role declaration checks to raise it. All other TaskRefusal instances and exceptions retain generic agent behavior.

The exact payload has three members: component=`role-adapter`, code in the table below, role=`implementation` or `review`. No output name, path, free text, adapter name, provider identifier or arbitrary descriptor value travels in this payload. Thus even an unknown output name containing a credential cannot become an identifier in status. Role is selected from the trusted task dispatch; the manager checks it against the current stage role. A provider cannot supply an arbitrary safe-looking identifier through this interface.

| code | Exact producer condition at selected shared-role declaration check |
| --- | --- |
| declaration-set-invalid | outputs is not a nonempty list, or has duplicate names |
| declaration-name-unsupported | a name is outside the adapter's closed supported set |
| role-output-missing | a member of this role's built-in produce set is absent |
| other-role-output-required | a declared output outside this role's produce set is required |

Use existing check order: set shape, duplicates, unsupported names, missing role output, required nonproduced output. Malformed declaration member shapes that fail earlier/general validation keep their existing refusal; do not classify arbitrary KeyError as one of these codes. No provider-failure codes are added. No mapping from the proposed W371072 descriptor is required to emit these four current adapter checks. Future descriptor-specific causes require a separate reviewed version; the sibling's descriptor vocabulary remains symbolic pending approval.

The worker validates the exact payload again, catches this dedicated type before generic Exception, and emits typed information only for operation=work. An invalid payload, unexpected role or use during describe becomes the existing generic agent terminal. Do not invoke arbitrary __str__ or forward exception attributes. Existing WorkerFault codes retain their meanings. Tests must exercise imports used by the actual worker/adapter package so duplicate exception classes cannot silently defeat the catch.

## Closed wire versions and encoding

| Document/interface | Proposed version and precise change |
| --- | --- |
| terminal.json | baton.worker-exchange.terminal/2: all ten /1 members plus mandatory adapter_failure, null or the object below |
| command, receipt, per-operation state, activity | Keep /1, /1, /1, /1 respectively; no member or meaning changes |
| worker launch /1, exchange descriptor /2, Job descriptor /3, context /4 | Unchanged; this is a matched package/image rollout, not negotiation through these documents |
| framed worker transport | Unchanged generic bounded fault; selected new typed scope is production file exchange only |
| baton.v12.attempt-failure-cause | /2: exact /1 shape and semantics plus mandatory adapter_failure composition below; unavailable sentinel carries /2 and keeps its current special shape |
| baton.v12.job-status | /8: existing status shape, now permits terminal/2 projection and diagnostic/2; update documents, delegation, projection and all packaged readers together |
| baton.v12.attempt-diagnostics | /2: existing report shape plus per-row adapter_failure; source diagnostics explicitly reads /1 and /2, supported Job inputs explicitly /7 and /8 |
| durable control records, cessation intent/outcome, result envelopes, submission | No version or semantics changes; no new journal kind or persistence action |

terminal/2 adapter_failure is either null or exactly {component, code, role, operation, operation_id}. The first three fields are the payload above; operation is literal work; operation_id is copied from the commanded work entry, never from the adapter. Non-null is legal only with ending=faulted, fault_code=agent, disposition=null, manifest_digest=null and answered=[describe]. Require receipt, describe=answered, work=faulted and no impossible tail, as today. Non-adapter faults, lost endings and answered endings have adapter_failure=null. These rules do not widen fault_code or disposition. terminal/1 cannot carry the added member. The normalized exchange terminal includes this field only under the new reader contract; /1 maps to missing typed evidence, not to a clean adapter result.

Existing outer session, attempt_id, sequence_id and command_digest still come from the command. Manager recomputes sequence/operation identities using existing functions and compares against its delivery/launch, validates the complete history, then verifies role against the canonical Job stage. Matching a string grammar alone is insufficient. Identity values exposed downstream come from manager-owned expected identities, after equality validation, not arbitrary worker operands. Job/stage/episode/runtime identities remain supplied by the existing owner/projection, not repeated in the adapter payload. A foreign, stale or inconsistent terminal is untrusted, never a typed declaration refusal for this stage.

Retain the existing raw-byte SHA256 command_digest (including exact command file whitespace). Do not replace it with a canonical command digest. For evidence identity, add no field to the terminal: calculate terminal_digest as sha256 of the exact bounded terminal file bytes validated in the same read. Do not reopen a mutable file to compute its digest. JSON readers reject duplicates, trailing values, invalid UTF-8, NaN and Infinity; retain existing outer exchange limits and set the added object to at most 1024 UTF-8 bytes and depth 1. Exact keys, built-in strings only, each at most 512 UTF-8 bytes; allowlists/equality are the safety gate, lengths only a backstop. The terminal file remains subject to existing overall size limits. No digest authenticates a worker; it identifies bytes.

The synthetic terminal example and command bytes in evidence/claim-371189 use exact derived sequence/operation IDs and a real raw-byte command digest. They illustrate a proposed /2 document; they are not a real execution receipt or accepted attempt.

## Existing diagnostic and report composition

ManagerOperations.observe reads the validated exchange once and passes that same immutable observation into failure_cause composition. Extend that composition's API with an optional observation operand; omitted means not observed, preserving existing non-Job callers. Do not independently reread the terminal for diagnostics. Carry the actual status snapshot observed_at into composition as the observation coordinate; the report must never call a clock. All data acquisition remains in existing read-only owners. The runtime read remains independent even if exchange is malformed.

Diagnostic/2 adapter_failure is an object with exactly state and facts. state is one of known, absent, unavailable. known has facts containing exactly component, code, role, operation, operation_id, session, sequence_id, command_digest, terminal_digest, observed_at. Each uses the existing known leaf shape {known:true,value:...,source:...}; sources are fixed literals: worker-exchange.terminal for the first four, worker-exchange.command for operation_id/session/sequence_id/command_digest, worker-exchange.terminal-bytes for terminal_digest, job-status.observed_at for observed_at. observed_at is a validated UTC snapshot instant (existing status instant grammar), not worker occurrence or first durable observation time. The source status may later be stale. There is no invented cause.at and no inference from token expiry or file mtime.

absent has facts=null: no typed adapter refusal in the available /1 history, no terminal, or a valid /2 terminal with null. This means absence of typed evidence, not evidence no refusal occurred. unavailable has facts=null: the exchange was not read, unsupported, unreadable or failed identity/history/role validation. No unknown version or offending value is echoed. Known cessation/start/preparation and cleanup facts remain readable beside either state. Failure of this added projection alone must not collapse the whole existing diagnostic to unavailable.

Report/2 mirrors this closed state/facts object using its existing scalar sanitization, then checks code/component/role/operation allowlists, digest grammars, expected current attempt-derived operation and existing stage/runtime correlation again. Invalid new fields produce unavailable for the added branch without echoing any rejected content; retain valid neighboring diagnostic facts. Report/2 normalizes a /1 diagnostic to absent and preserves all prior fields. Unknown diagnostic version preserves the existing diagnostic-unavailable behavior. Job/version parsing accepts only the explicitly supported /7 and /8 shapes, not every older schema and never /6. A mismatched /7 envelope carrying /2 diagnostics is rejected; a /8 envelope may carry /1 historical diagnostics with adapter_failure=absent. Unknown top-level status schema refuses safely as today. Existing report readers remain strict; they do not silently read /2.

Use the existing report diagnostic locator and operator-supplied retained-output operand, unchanged. Do not publish exchange directories, host paths, provider transcripts or generated shell commands using worker input. The terminal digest identifies the source when it is still retained; it is not a promise the artifact can be recovered. Existing exchange retention owns the evidence lifetime. Cleanup may leave only a saved status snapshot or no typed evidence; the latter is honestly absent/unavailable. This proposal does not promise a new persistent post-cleanup history service.

All cessation answer_of behavior stays /1-equivalent. A known adapter failure can coexist with cessation unknown or positive cessation; it neither orders nor proves a stop, releases a token, allows retry, changes acceptance, fabricates output nor marks the Job successful. Likewise it does not fill the existing cessation unknown with an adapter cause. Stopped-failed settlement belongs to the sibling, with no writer/API changes hidden here.

## Compatibility and deployment boundary

Recommend matched host package, worker image and installed adapter qualification for emitting /2, consistent with DESIGN DEP-2. New readers explicitly support /1 and /2 terminal shapes, distinguishing absent typed evidence from unknown schema. New publisher emits /2 consistently; old manager rejects it rather than interpreting a widened /1. No automatic downgrade, dual terminal files or optimistic runtime negotiation. Installation/capability validation must reject an old host with the new publisher before execution. W371072's eventual approved capability binding supplies the version pairing; do not freeze that sibling's pending descriptor here. For this proposal's own future tests use explicit matched binaries/images. No rollout is authorized by this planning Work.

This proposal intentionally does not type every adapter failure, alter framed transport or claim real deployed compatibility. If owner requires those or durable post-cleanup retention, they are separate selected scope decisions, not implicit implementation work.

## Finite implementation and acceptance plan

1. After owner approval, reviewer pins the exact decision and updates DESIGN before implementation. Implement shared typed producer and terminal/2 writer/reader with mirrored closed constants and real adapter tests. Own worker adapter/transport and manager exchange boundary serially; no overlap with admission edits to selectors until ownership is agreed.
2. Extend existing diagnostics composition, delegation/status projection, viewer and packaged report as one matched slice. Run bounded deterministic ordinary status/report integration against real temporary stores and actual terminal reader. No status write, engine call or live provider. Coordinate shared stage_execution/deployment capability changes with admission and ordinary workflow proof, not parallel unowned edits.
3. Independently review exact bytes and evidence, then join into W371076's native workflow proof. Admission refusal should prevent the mismatch ordinarily; deliberately exercising a stale/defective admitted adapter tests this defensive path without weakening admission. W370747 remains the acceptance consumer. Tests may be added/changed under standing authority, with actual paths/reasons recorded at implementation; locations here identify owners, not an exclusive edit restriction.

| Future acceptance behavior | Required proof, not a prescribed command |
| --- | --- |
| Each of four causes, both roles | Real ClaudeAgent selection through actual worker exchange, real manager history validation, ordinary status and packaged report; provider spy shows zero calls for these pre-provider checks |
| Correct shared declarations | Adapter proceeds; output collection and semantic result validation remain required, no typed failure inferred |
| Arbitrary exception, unrelated TaskRefusal, provider failure | Generic existing route; provider failure classification retained separately; no declaration code guessed |
| Secrecy | Credential-shaped unknown output, exception message/class/attributes, malformed typed payload, forged component/code/role, Unicode/oversize/nested/duplicate fields; no such bytes in public report or generated diagnostics |
| Correlation | Wrong attempt/session/sequence/command digest/operation/role/runtime, stale episode, missing receipt, impossible state vector and terminal-only forgery refuse typed evidence and cannot yield success |
| Compatibility | /1 history, /2 matched producer-reader, unknown terminal/diagnostic/status versions, mixed versions, /6 refusal; new readers preserve old diagnostic semantics and old readers reject new documents |
| Time and immutable read | Clock advances between reads; same captured terminal bytes supply digest/facts; snapshot observed_at stays distinct from occurrence/cessation; report has no clock or filesystem acquisition |
| Isolation of evidence failures | Unavailable/malformed adapter branch retains known cessation/token/limit facts; deleted terminal stays unknown; unavailable sentinel and process-local degradation remain truthful |
| Read-only and no fabricated effects | Snapshot/report writes no control/Job state, calls no engine/provider, creates no journal and changes no completion/acceptance/token/cleanup decision |

Planning verification is limited to source inspection and inert example/hash checks. These are not product coverage or a successful end-to-end run. Future focused deterministic checks use sensible per-run timeouts and measured durations, not a live model/engine or broad stress run. Historical unknown verification seconds remain unknown.

## Proposed DESIGN addition for owner approval

Insert after OBS-3, without weakening it:

> Known role-adapter declaration refusals cross the worker boundary as a closed, versioned typed payload bound to the exact commanded operation and validated attempt history. Arbitrary adapter exceptions and provider text do not supply diagnostic prose or identifiers. Existing attempt diagnostics and the supported read-only report expose these facts separately from cessation, token, cleanup and acceptance evidence. A manager observation instant is labelled as such, never invented as a failure occurrence time. Missing historical typed evidence remains explicitly unknown. Matched producer/reader versions are qualified before deployment; unsupported versions do not silently widen a contract. Reporting a refusal neither proves cessation nor authorizes retry, acceptance or success.

Owner decision requested through review: approve the four-code file-exchange-only boundary, terminal/2 + diagnostic/2 + status/8 + report/2 compatibility matrix, observation-time/retention limits, and this DESIGN addition. No unresolved taxonomy is delegated to the implementer. The admission capability identifier remains the sibling's decision and must be reconciled at the joined approval before implementation.
