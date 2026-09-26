# W275513 — implementation alignment with accepted DESIGN

Author baton.rvpc, claim275515, 2026-09-26. Scope: one bounded source/evidence
audit, not implementation acceptance. Read canonical assignment T275513/275513,
events through275515; binding275521. Return to baton.decide for selection.

## Verdict and next decision

**The current implementation does not conform to the accepted DESIGN.** The
critical shared gaps are container-bound resource permission, host enforcement
of that permission, and token-bound maintenance for every governed filesystem
writer. They cannot be repaired by moving deletion outside a transaction alone.
**W270664 requires a shared prerequisite; it cannot independently deliver the
selected token/maintenance design.** Preserve its existing identity and candidate
as the deletion consumer of that prerequisite. Do not start another local token
implementation in its workspace helper. No dependency or route was changed here.

There is substantial connected machinery worth retaining: canonical claims,
principal-aware pool reservation, durable launch/command identities, ordinary
producer shutdown before review, immutable result/checkpoint handling, fresh
attempt recovery, context qualification, per-invocation limits and a read-only
viewer. These are components and historical proofs, not certification of the
expanded target. The accepted live-detach experiment remains valid evidence of
its mechanism; adopting live handoff is explicitly deferred by the new design.

## Authority, bytes and evidence limits

Normative input `v12/DESIGN.md` SHA256
`7f504a5edbb46acae739cab0727173fc1c51098300ae8048d25b56bba274cee0`
matches the accepted W274875 checkpoint. Its normal-shutdown amendment and all
governed-mutation placement requirements apply. Its earlier absence during
W270664 review is historical, not a present operational blocker.

`source-sha256.json` records 114 source/design files read for byte identity;
this is an inventory, **not a claim that every function was traced**. Focused
body/call-chain inspection covered the paths below. No product modules were
imported; no tests, providers, containers, deployment changes or Git operations
were run. Static Python used only file reading/hashing and evidence generation.
Current source plus immutable historical reports supports the classifications.
Dynamic contention, shutdown, restart and actual provider restoration were not
executed in this audit. Negative caller searches covered Python src/tools and
were checked against the worker entry boundary; they do not prove absence of
an external deployment plugin.

Operational discovery: guessed files `v12/python/tools/job_status.py`,
`job_monitor.py` and `parallel_runner.py` were unreadable because they do not
exist. Repository discovery found `job_manager.py`, `job_viewer.py` and
`parallel_test.py`. No conclusion depends on the guessed files. The bound
dossier, accepted design and required current references were readable.

## Source reference catalog

Paths are repository-relative. References name current bytes in the manifest;
line numbers locate the symbol, not a promise about subsequent edits.

| Key | Exact code references and bounded evidence |
| --- | --- |
| A | `v12/python/src/baton_v12/authority/core.py:1352` `claim`, generation increment1414; `assignment_of:1196`, principal resolution296/371; authority store transactional replay. Canonical identity and claim source. |
| J | `v12/python/src/baton_v12/job_manager/submission.py:41` submit, immutable limits136/202; `scheduler.py:158` activate_pool, `reserve:316` atomic principal capacity and hard exclusions; `manager.py:106` sweep, `_launch:410`, `_recover_endings:331`, `serve:804`; `ending.py:523/562` intent/settlement. |
| H | `v12/python/tools/stage_execution.py:1239` StageComposition, mount1276 and prepare_context1304; `StageExecution:4546`; `v12/python/tools/single_worker.py:1933` assignment_workspace, start2063, ending2522, launch materialize2980. Connected host composition, not a fixture. |
| E | `v12/python/src/baton_v12/worker_manager/attempts.py:766` activate_assignment, `request_runtime_start:1454`, reconcile2360, cancel2890, quiescence3251, finalize3393. Durable start operation precedes adapter effect; held lane and original identities survive restart. |
| D | `v12/python/src/baton_v12/worker_manager/oci.py:1233` run_vector, restrictions166, start2265, list2982, stop3067, destroy3087, observe3697. stop orders exact runtime then observes; not mere acknowledgement. |
| R | `v12/worker/baton_worker.py:1211/1350/1372` input/assignment agreement, handle1666, command2051, serve_exchange2216 (receipt2265–2275 before dispatch); publish_completion1552. `v12/worker/claude_agent.py:3695` provider subprocess supervision, `_verify:4028`, publication5274. |
| T | `v12/python/src/baton_v12/worker_manager/workspaces.py:2408` token_of, bind2433, revoke2468, terms2532, admission2701, completion2852, removal3029, explicit usable control3060. Binding/revoke have no product callers in src/tools. Three historical failing token probes apply to identical bytes. |
| F | `v12/python/src/baton_v12/worker_manager/review_cycles.py:1427` create_line, locked act1505 and filesystem1523–1524; restore path3204/3249/3344; `v12/python/tools/stage_execution.py:5003` restoration_launcher, cessation5157. Host filesystem execution remains. |
| C | `v12/python/src/baton_v12/job_manager/review_driver.py:362` exact stop+quiescent gate, end_implementation614, end_review1222/1352, correction1664; `worker_manager/oci.py:3482` seal -> `sealing.py:710` sealed_result, `_staged:244`, `_commit:451`; retained bytes/claims are distinct. |
| M | `v12/python/src/baton_v12/worker_manager/custody.py:1024` narrow helper vector, `_claim_episode:1860`, normalize2059, adopted2161, `_recorded_store:2249`, custody_act2326/recovered2536. Existing Docker normalization helper is a useful seed, not common renewable resource-token enforcement. Its old vector docstring claiming no recovery must not override the later concrete recovery functions. |
| X | `v12/python/src/baton_v12/worker_manager/provider_context.py:670` _facts, admission710 onward, transition629, bind_context_invocation1176; `context_delivery.py:327` materialize, seal444, discard534. Connected from H:1311–1314; disposal itself has no src/tools product caller found. |
| L | `v12/python/src/baton_v12/job_manager/execution_limits.py:145/184/192` closed positive overrides and frozen compatibility defaults; `submission.py:235/273` effective delivery. `worker_manager/deadlines.py:52` policy permits report-only/cancel; runtime deadlines are not resource tokens. |
| O | `v12/python/tools/job_manager.py:99` status, _Observing153 and _ReadOnly250; `job_manager/projection.py:728` status and stage783; `v12/python/tools/job_viewer.py:168` read_snapshot, activity326, render492/560. Read-only observation is deliberately separate from manager sweep. |
| S | `v12/python/src/baton_v12/worker_manager/credentials.py:228` resolved_delivery, CredentialHome390; D:806 exact RO credential mounts, context mounts3952; `v12/worker/claude_agent.py:3976` prepared HOME. Closed validation exists; complete secret-flow/confinement audit not performed. |
| P | `v12/python/tools/bootstrap.py:389/482/529` validated config/layout/composition, conflicts1038; `worker_image.py:159/173/384` recipe/base facts/build; `stage_execution.py:516` held_configuration, operations_from6278. Deployment/provenance entry points, not inspected live configuration. |
| B | W270520 DB findings revalidated in the next section; exact current chains there. |

## Connected lifecycle trace

1. **Admission and launch.** Submission pins Jobs/stages/limits (J). Sweep resolves
   eligibility; scheduler.reserve atomically excludes occupied worker/principal
   and independent-review principals. Authority.claim (A) owns the assignment.
   H composes the attempt, workspace roots, manifests, credentials and launch
   delivery; E pins the assignment and journals a stable start before D.start.
   D constructs the confined Docker invocation. **Missing:** a common resource
   token reserved before preparation, preparation in a maintenance execution,
   settled maintenance shutdown, task-token admission, and exact launch-to-token
   binding. Current allocation/materialization is host code. A Work claim or
   worker lane is not that resource permission.
2. **Execution.** Docker runs `baton_worker`; input/assignment/launch and command
   identities are validated. `serve_exchange` persists the receipt before calling
   `handle` and the agent; re-entry with a receipt does not repeat dispatch.
   Claude adapter owns the provider process and local verification; output.json
   is a claim published last. Host consumes exchange evidence independently.
   No token delivery/renewal/enforcement connection was found at this boundary.
3. **Normal handoff.** Review driver's ordinary implementation ending calls
   `_quiesced`: exact runtime stop, positive quiescent observation, reconciliation.
   It then freezes/collects/retains, publishes under live assignment, fences the
   writer, freezes checkpoint and cleans up. Review mounts the checkpoint read-only
   with separate output (H.mount). This is positive shutdown machinery and must
   not be reported as universal live-detach behavior. **Still missing:** token
   return conditional on that exact observation, maintenance token/runtime for
   sealing/retention and proof of every role/maintenance handoff. Generic adapter
   response handling is not the new typed token cessation contract.
4. **Expiry.** Existing runtime deadline selection supports report-only and cancel.
   Those are separate semantics; do not remove legitimate report-only liveness
   merely to pretend it is resource expiry. T's removal-only revoke helper calls
   an injected stop callback, outside the DB, but nothing in the production
   serving loop calls it or binds it to D. No connected shared-token renewal,
   overdue reconciliation or service outage enforcement was found. **Gap G1.**
5. **Restart/cancellation.** E reconciles exact launch labels/runtime, preserves
   uncertain starts and held lanes; J recovers claims/endings and retries owed
   work by operation identity. R preserves dispatch uncertainty via receipts.
   Cancellation/fresh replacement components remain valuable. They do not yet
   reconcile shared resource-token generations, late maintenance launches or
   expired token holders. No full crash-cut execution was done here.
6. **Custody and cleanup.** D.seal first checks runtime quiescence, then calls
   host sealing code which stages/copies/commits bytes. M already launches
   restricted normalization containers and journals their episodes/holds.
   Intake authorizes cleanup and deletion uses T's short ownership transaction,
   host filesystem work, conditional completion. Thus moving deletion outside DB
   locks was useful but **TOK-7/ART-7/ART-9 remain contradicted**. M must be connected
   to shared permission rather than treated as proof that all custody is in Docker.
7. **Context restoration.** H.prepare_context calls X admission, host context
   materialization, invocation binding and prelaunch revalidation. Context has
   profile/producer/workspace identity and generations; workspace repair uses F's
   bounded host helper. Production useful reuse across all selected handoffs is
   not certified by either qualification fixtures or historical provider proofs.
   Both context copying and restoration must migrate behind token-bound maintenance.
8. **Scheduling, delivery, limits and observation.** J has persistent scheduling
   and hard principal exclusion, L pins distinct invocation settings, C carries
   exact verdict/candidate evidence, O separates status from serving. The audit
   did not prove the 2-coder+2-reviewer target, every explicit integrated-base
   dependency, optional-proposal-only delivery or all profile migration cuts.
   No shared-token fields can be considered proven merely because old attempt
   activity and cleanup are displayed. These are explicit partial/unproven rows.

## W270520 revalidation against current bytes

`W270520-byte-comparison.json` compares all 104 original source files: 94 identical,
10 changed. It prevents reusing old line numbers as current source proof.
The original static inventory is useful evidence, not a fresh whole-program proof.

| Prior finding | Current disposition and reference | Correction owner/dependency |
| --- | --- | --- |
| F1 create_line | Still confirmed. Now review_cycles.py:1427, callback1505 calls _object1510, prove_line_integrity1523 and establish_line_access1524 before transact returns1533. Host permission/tree work under DB lock. | Existing W270520 finding; W257624 overlap preserved. G2 then G3; do not undo accepted restoration. |
| F2 removal | Original lock-held deletion chain superseded by W270664 candidate: short admission, external deletion, conditional completion, nesting refusal. No blanket closure: host deletion violates TOK-7; recordless cleanup still reaches filesystem under lock. intake.py:4137 -> _adopted_custody4003 -> custody.adopted_directory_custody2161 -> _recorded_store2249 with no prepared store. Ordinary settlement4594 passes prepared_store; recordless helper does not. | W270664 remains owner of selected removal. Shared G1/G2 before G3. Residual recordless path retained under W270520, owner to select exact scope. |
| F3 context disposal | Same context_delivery bytes; callback555–564 still opens/scans/deletes inside transact. Exported helper, no product caller found; not represented as a deployed failure. | W270520 finding, context consumer W177936; G2/G4. |
| F4 context admission/bind | Same provider_context bytes. _facts670 still reads Job and Authority and opens line/source descriptors inside admission/commit callbacks. Current H.prepare_context1311–1314 connects it. | W270520/W177936; G4 after G1/G2. |
| F5 session open | Same sessions bytes: transact344 -> _open350 -> _live_assignment373/403 -> Authority. | W270520; G5. |
| F6 freeze request | Same output bytes: _request219 -> port.assignment_of235 within transact. | W270520; G5, preserve generation fence. |
| F7 intake | Changed intake file, re-read current _seal732 -> port.assignment_of748 still inside its callback. Quarantine semantics must survive correction. | W270520; G5. |
| F8 interrogation | Same interrogation bytes: act -> _still_live274 under transact296 -> Authority. Provider invocation itself is outside; do not overstate. | W270520; G5. |
| F9 correction restart | Same episodes bytes: act1178–1188 reads Worker control/custody and verdict while Job transaction1218 is active. | W270520/W257624; G5. |
| F10 integration admission | Same integration_capacity bytes: perform1166 -> _prove_grant -> IntegrationStore while Job lock held; transact1182. Connected optional integration tool path. | W270520, W161230 historical consumer; G5. |
| F11 integration ending | Same integration_capacity bytes: perform1407–1408 -> collected content and resolved exclusion -> Worker/Authority reads; transact1422. | W270520, W161230 historical consumer; G5. |

W270520's earlier statement treating custody readers as DB-only is narrowed:
the prepared ordinary cleanup reader avoids external storage proof; the unprepared
recordless reader does not. Cross-store reads remain external even when their
inner transaction is short. Relocating them requires durable conditional evidence,
not a time-of-check/time-of-use gap or an unguarded cached authorization.

## W270664 evidence disposition

`W270664-byte-comparison.json`: **all 12 reviewed source/tool/test/probe paths
match** `candidate-2026-09-26T11-47-38Z.sha256`. Preserve review
`review-2026-09-26T11-47-38Z.md`: historical 40 focused passing tests (0.344s),
three failing independent token tests (0.023s). None rerun here. They show:

* ceased generation1 permits generation3 while generation2 remains live;
* old revoked/unbound reservation can bind a delayed container;
* string `"false"` is accepted as positive cessation by truthiness.

Current T source confirms the same inadequate admission/binding/proof structure.
No product caller makes its bind/revoke helpers an enforced Docker lifecycle.
Preserve its accepted no-implicit-reopen behavior (`_asking_control:3060`),
explicit usable handles, short transaction structure and prior W257624 restoration
evidence. None is a pass for the complete token contract. Remaining adoption
release and alias/hold/interruption obligations in that review remain open; this
audit does not manufacture new test results for them. W266337 fresh-attempt proof
and accepted live-detach/restoration experiments retain their original scopes.

## Proposed bounded Jobs — owner selection required

These G identifiers are audit recommendations, **not new ledger Work identities**.
Existing findings/Work remain authoritative. Every matrix gap points here;
verification listed is proposed acceptance, not performed verification.

| Gap / proposed correction | Existing owning record or Work; dependency | Bounded path/outcome and required acceptance |
| --- | --- | --- |
| G1 shared resource token and enforcement | W270664 exposes failures; W275513 owns this recommendation; W2 delivery umbrella. New dedicated prerequisite identity only if owner selects. First. | One shared token owner integrated with ControlStore, attempts and OCI: atomic conflict/resource pins; exact launch operation; typed container binding; generation-safe return; bounded renewal vs expiry; overdue restart and unknown hold. Pin duration/grace/version policy before execution. Prove real competing callers, delayed launch, lost reply, stale proof, gen1/gen2/gen3, renewal race and engine failure through deterministic real adapter boundary. No maintenance filesystem migration bundled. |
| G2 token-bound maintenance executor | W275513 recommendation; existing custody M, W257624 recovery and W270664 consumers. After G1. | Generalize the existing narrow Docker custody lifecycle for scoped prepare/freeze/copy/reset/delete verbs; no credentials/authority DB mounts. One first connected allocation-to-task handoff, with stopped-and-settled maintenance before task admission. Prove interrupted/late launch, expiry, restart, exact mounts and cessation; host resource mutation probe. Do not duplicate token ownership in each helper. |
| G3 workspace lifecycle and removal consumer | Preserve W270664, W257624 and W270520 F1/F2; after G1/G2. Owner decides the bounded subdivisions. | W270664 uses shared maintenance for both roots/removal, exact replay/holds and no implicit reopen. Separate create_line/materialization and restoration migration slices if needed. Recordless intake reader fix owns only named siblings. Prove alias/object replacement, two callers, stale owner, no locked I/O, no host mutation, real hold release and interrupted deletion. Preserve all accepted restoration and negative token probes. |
| G4 context save/restore/cleanup consumer | Existing W177936; design record W161234; W270520 F3/F4. After G1/G2 and corresponding workspace checkpoint G3. | Move materialize/seal/discard context effects to maintenance; conditional admission/binding facts outside DB; exact qualified context plus workspace restoration in a new stopped-predecessor container. Prove wrong profile/principal/checkpoint, serial competing use, failed save, credential exclusion, useful correction and fresh fallback. Reuse applicable provider qualification; select a live question only if still required. |
| G5 cross-store decision cleanup | W270520 F5–F11, historical consumers W257624/W161230. Can be designed alongside G1; integrate with accepted ownership semantics. | Small serial Jobs: session/interrogation; freeze/intake; correction restart; optional integration admission/ending. Replace nested authority/store callbacks with durable intents/versioned evidence/conditional settlement. Preserve stale-assignment refusal/quarantine. Transaction probes and races at each exact boundary, not broad mechanical movement of reads. |
| G6 result/review/ending integration | W71830 pipeline, W161230 integration evidence; W275513 gap. After G1/G2 plus required G3. | Ordinary producer -> maintenance freeze/retention -> independent reviewer -> correction/new proposal, every holder stopped before next. Exact digest/base/path provenance, typed token cessation receipts; no automatic mainline success. Prove pending cleanup/unknown engine does not publish false acceptance or free resource. Audit optional integration and proposal-only terminal policy separately before claiming both. |
| G7 parallel useful Jobs and delivery proof | W2, W71830; W202663 pool historical evidence; W247941 unaccepted adoption history. After first connected G1–G6 path. | One selected deterministic 2-coder+2-independent-reviewer composition with stage-specific dependency and explicit accepted integrated base; one held Job while unrelated Job progresses. Verify changed pool generations keep old allocations, and exact reviewed proposal handback. Current scheduling source alone is insufficient acceptance. |
| G8 monitor token/diagnostic completion | Existing O monitor implementation; W275513 owns new gap until owner selects identity. After G1 schema, then G7 composition. | Add token deadline/generation/held/unknown/maintenance and enforcement-loss projections using read-only APIs. Verify status leaves all stores unchanged, distinguishes configured/observed activity and shows failed executor without final output. Source discovery is not a full monitor acceptance run. |
| G9 targeted assurance and deployment alignment | W156162 limits; W202663 deployment; W2 policy. After relevant connected path. | Separate bounded verification Jobs for effective runner limits, closed credentials/context secret flow, version/provenance migration preserving unknowns and explicit deployment separation. Update deployment/review-cycle docs only to implemented behavior. No blanket security certification or live rollout selected by this audit. |

G1/G2 are shared architecture prerequisites, not speculative hardening. G5 may
progress independently where it does not invent competing token semantics. G8
projection work may follow a pinned G1 contract, but end-to-end acceptance follows
the connected path. Do not make full v13 matrices a prerequisite to the first
useful conforming v12 slice. Live detach, advanced scheduling/shared capacity,
distributed engines, rich TUI and cumulative financial accounting stay deferred.

The companion REQUIREMENTS.md supplies a row for every numbered requirement,
plus the unnumbered governing sections. A partial/unproven classification is
an evidence limit, not a claim of a newly reproduced defect.
