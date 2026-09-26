# Requirement-to-code/evidence matrix

Read with AUDIT.md: source keys expand to exact current file/symbol/line references;
G keys identify bounded proposed Jobs, existing owners and dependency order.
**Supported** means the stated source/policy mechanism was found; it does not
certify all dynamic cases. **Partial** means substantial machinery exists but
the complete requirement is not established. **Contradicted** names a concrete
incompatible path. **Unproven** means this bounded audit cannot establish it.
**Deferred** applies only to expressly later scope, never to a known v12 defect.
No row claims a new test run. Historical W270664 results have exact matching bytes;
other historical campaigns retain their original, narrower acceptance boundaries.

| Requirement | Classification | Code / evidence and precise limitation | Gap / next action |
| --- | --- | --- | --- |
| ID-1 | Partial | A claims Work; J submission creates bounded Jobs/stages. Complete campaign subdivision and dependency semantics not traced. | G7 |
| ID-2 | Supported | A:claim1352 and assignment_of1196 distinguish canonical assignment from J reservation; H activates before start. Scope: inspected canonical claim path. | Preserve in G1/G7 |
| ID-3 | Supported | A:claim increments Work generation1414; E fixes authority/Work/participant/generation. No observed identity substitution in traced path. | Preserve in G1 |
| ID-4 | Partial | E offer/attempt/activation and D label/profile/digest binding; X qualification. All fresh/reattach and migration combinations unexecuted. | G1/G4/G9 |
| ID-5 | Partial | A principal binding; J.reserve excludes canonical principals and fail-closed eligible set. Organizational ambiguities outside inspected path. | G7; broad hierarchy deferred |
| ID-6 | Partial | J separates kind/profile and hard exclusions from affinity. Complete model-level independence configuration not audited. | G7/G9 |
| ID-7 | Unproven | E lane/J capacity/R receipt constrain duplicates. Actual deployment readiness consumers were not inspected; no shared token yet. | G1/G7/G9 |
| DB-1 | Contradicted | B:F1/F3/F4 filesystem and F5–F11 cross-store calls inside transactions; recordless intake4137 residual. | G3/G4/G5 |
| DB-2 | Contradicted | F:create_line callback performs tree/access work; X:discard callback deletes before commit. Callback shape does not exempt effects. | G2–G5 |
| DB-3 | Partial | T removal reserves then effects/settles; E start intent before adapter. Common resource-token decision absent. | G1/G2/G3 |
| DB-4 | Partial | Distinct Authority/Job/Worker/Integration owners exist, but B nests external store reads instead of composing durable facts. | G5 |
| DB-5 | Partial | E rechecks lane/admission; T conditional completion and X identity checks. Missing shared generation enforcement and cross-store conditional protocol. | G1/G4/G5 |
| DB-6 | Partial | T:_asking_control3060 refuses unusable thread/closed handle, no implicit reopen; exact W270664 evidence preserved. Every operational API not audited. | Preserve G3; G9 for remaining APIs |
| DB-7 | Partial | Store operation signatures, E launch and R command receipt; T stale-generation failures prevent universal replay/retirement claim. | G1/G5/G6 |
| TOK-1 | Contradicted | T admission uses first historical standing record, permits third generation beside live second; historical failing probe matches bytes. No common allocation/context token. | G1 |
| TOK-2 | Contradicted | T token terms are removal-local; production H/D launch not bound to token; no complete resource/op/profile/launch ownership contract. | G1 |
| TOK-3 | Partial | Removal ownership and custody/attempt holds persist, but token generations do not safely exclude and are not universal. | G1 |
| TOK-4 | Contradicted | E journals launch but no shared-token binding; T accepts late binding of revoked/superseded unbound generation. | G1 |
| TOK-5 | Partial | C ordinary producer ending positively stops exact container; shared-token return and every maintenance/role handoff absent. No claim that live detach is required. | G1/G2/G6 |
| TOK-6 | Contradicted | T revoke helper has no product caller; callback not connected to D; actual host writers cannot be stopped by container expiry. | G1/G2 |
| TOK-7 | Contradicted | H workspace/launch materialization, F restoration, X context copying, C sealing and T deletion mutate on host. M normalization containers alone insufficient. | G2–G4/G6 |
| TOK-8 | Partial | E separates cancellation/finalization from runtime axes; T truthy cessation and generation failures undermine shared physical exclusion. | G1/G6 |
| TOK-9 | Contradicted | T computes expiry with store clock but no connected renewable current deadline revision/expiry arbitration; default900 is not pinned policy selection. | G1; pin policy first |
| TOK-10 | Unproven | E/D uncertainty and M holds exist; no serving shared-token overdue enforcement/restart path found. No engine outage exercise. | G1 |
| TOK-11 | Contradicted | T accepts stopped="false", old generation release and late bind; three exact-byte historical negative probes. | G1 |
| TOK-12 | Contradicted | F restoration is bounded host helper; no reset maintenance token/execution followed by separate settlement and gated next admission. | G1/G2/G3 |
| HOST-1 | Contradicted | H/E claim and profile checks precede task start, but preparation performs governed effects on host without maintenance-token shutdown/settlement. | G1/G2/G3 |
| HOST-2 | Partial | J recover_endings/E reconcile/R receipt recover durable identities; no token/maintenance overdue recovery. | G1/G2/G6 |
| HOST-3 | Partial | D closed run/start/list/observe, exact image/runtime identity; selected deployment platform/provenance not validated live. | G9 |
| HOST-4 | Partial | D restrictions/mount composer disallow broad host authority and constrain input/output; S exact credentials. All negative overlap/confinement cases unexecuted. | G2/G9 |
| HOST-5 | Partial | M/D use trusted configured execution identity. F:create_line still recursively establishes access; compatibility with narrow normalization obligation needs selected migration, not startup probe invention. | G3/G9 |
| HOST-6 | Partial | E/intake cleanup axes and M custody holds preserve owed work; T release/alias/interruption obligations and common token missing. | G1/G3/G6 |
| HOST-7 | Unproven | J serve is persistent loop; no production binding of T expiry helpers or audited external service supervision. | G1/G9 |
| RUN-1 | Partial | R validates input/assignment/launch/commands before provider; full launch capability and secret-delivery combinations not traced. | G9 |
| RUN-2 | Supported | R:serve_exchange2216 publishes durable receipt before handle/provider, returns on old receipt, leaves receipt-without-terminal uncertain. Source-level claim only. | Preserve through G1/G6 |
| RUN-3 | Partial | R/claude_agent supervise provider and verification, activity and envelope. Not an API-only runner certification or live provider qualification. | G4/G9 |
| RUN-4 | Partial | Claude runner/private tool path and D confinement support broad local tools. Every runtime profile's consent/tool behavior unproved. | G9 |
| RUN-5 | Partial | R subprocess supervision/E cancellation exist; no granted-token loss/renewal boundary connected. Host must stop hung container independently. | G1/G6 |
| RUN-6 | Partial | C parses independent claims; sealing rejects absent required output; plan rejection/reoffer path not traced end-to-end. | G6/G7 |
| ART-1 | Partial | R input+assignment/output envelope; D separate source/credentials/context/exchange mounts. All optional integration profiles not exhaustively audited. | G2/G9 |
| ART-2 | Partial | D source mount1052 is nominated RO; H generic control and source-specific composition coexist. Full no-host-source-walk/format neutrality not proved. | G3/G9 |
| ART-3 | Contradicted | H/E compose and pin manifest identities, but H assignment_workspace1933/launch.materialize2980 install on host, not postclaim maintenance. | G2/G3 |
| ART-4 | Partial | H.mount1276 selects persistent writer line or frozen RO review checkpoint; C positive producer stop. Universal token exclusion and handoff cuts unproved. | G1/G6 |
| ART-5 | Partial | F/T descriptor/object/alias checks and copied-manifest paths exist; remaining W270664 alias/both-root/final-entry proofs open. | G3 |
| ART-6 | Supported | R publish_completion1552 and C sealing710 require real declared artifacts and correlate envelope/digest. Source-level behavior; not complete fault-injection certification. | Preserve in G6 |
| ART-7 | Contradicted | D.seal3482 calls host sealing/staging; no maintenance-token runtime/cessation receipt bound into the new custody contract. | G2/G6 |
| ART-8 | Partial | output._request235 checks live Authority, intake._seal748 quarantines stale generation; cross-store decisions and token-bound publication remain incomplete. | G1/G5/G6 |
| ART-9 | Contradicted | Retention/custody axes exist, but T deletion and X context cleanup are host effects; X disposal even under transaction. | G2/G3/G4/G6 |
| CTX-1 | Partial | X provider use/generations, E attempts, R processes separate; historical detach experiment preserved, production shutdown/restoration contract not fully proved. | G4; live detach deferred |
| CTX-2 | Partial | X qualification/_facts pins producer, purpose/profile/line/job/principal. Source and prior qualification not proof of complete useful current reuse. | G4 |
| CTX-3 | Partial | X serial use/finalization and protected generations; common token and maintenance save missing. Failed-save/new-container cuts unexecuted. | G1/G4 |
| CTX-4 | Partial | X:_facts670 binds workspace object, source, assignment, profile and limits. F historical restoration accepted narrowly; connected matching restoration unproved here. | G3/G4 |
| CTX-5 | Partial | X closed context deliveries and S credential separation exist. Complete positive-inclusion and transcript/credential secrecy audit not done. | G4/G9 |
| CTX-6 | Partial | C.open_correction1664 and Job episodes support correction; repository policy carries routine continuation. All automated routing/partial-turn outcomes not traced. | G6/G7 |
| CTX-7 | Unproven | Durable dossiers/checkpoints are project policy; no supported runner compaction/obligation-preserving Job operation was verified. | G4/G9; no invented exhaustion gate |
| SCH-1 | Partial | J.submit41, stage normalization and limits generation persist contract. Every amendment/profile compatibility path not inspected. | G7/G9 |
| SCH-2 | Partial | J.sweep/serve and atomic reserve hold canonical principal capacity; missing shared resource token means no full parallel exclusion claim. | G1/G7 |
| SCH-3 | Unproven | Pool supports multiple workers; this audit runs no 2+2 useful concurrency proof. W202663 narrower history does not fill it. | G7 |
| SCH-4 | Unproven | J stage/owed_acts/gates machinery exists; each stage-specific dependent admission rule not traced. | G7 |
| SCH-5 | Unproven | Accepted-base tool exists and optional integration composition exists; no source-to-consumer proof of every explicit accepted integrated base here. | G7 |
| SCH-6 | Partial | J.activate_pool158 persists generations and reserve reads old occupied principals; deployment rebinding and recovery combinations unexecuted. | G7/G9 |
| REV-1 | Partial | C distinct result/verdict/checkpoint and J ending/integration stages; complete terminal-policy separation not audited. | G6/G7 |
| REV-2 | Partial | H read-only checkpoint plus separate reviewer output; J hard principal exclusion; C verdict parser1581. All model/context exclusions and exact candidate transitions not exercised. | G6/G7 |
| REV-3 | Partial | C correction1664 and immutable review journals support bounded repair. Material scope expansion/automatic reoffer not fully traced. | G6/G7 |
| REV-4 | Unproven | Retained publication/proposal path exists (C846); default reviewed proposal-only delivery selection not established for every submission/deployment. | G6/G7 |
| REV-5 | Supported | AGENTS reserves canonical Git to owner; worker source carries isolated output behavior. Audit itself performs no Git changes. Policy conformance here, not certification of every deployment script. | Preserve; G9 for deployment |
| REV-6 | Unproven | Optional isolated integration package exists; no proof mandatory integration is absent from every selected workflow. Generic manager vs source driver boundary needs bounded check. | G6/G7 |
| REV-7 | Partial | C publication/provenance and source/integration tools carry base/artifact identities. Full ancestry/transport/drift import path not audited. | G6/G9 |
| REC-1 | Supported | E runtime/worker/cleanup axes, J ending and O projection retain separate facts. Full token axis absent, covered separately by G1/G8. | Preserve; G1/G8 |
| REC-2 | Partial | E cancellation/fences and exact D stop observation; shared-token delayed-launch/physical hold failures remain. | G1/G6 |
| REC-3 | Partial | E launch, R receipt, C endings and M custody journals have before/after operations. Every required crash cut including maintenance/token not proved. | G1/G2/G6 |
| REC-4 | Contradicted | F host restoration/reset cannot satisfy new maintenance-token requirement; existing holds do not erase this placement defect. | G1/G2/G3 |
| REC-5 | Partial | E reconciliation and J replacement preserve fresh attempts; W266337 historical fresh proof retained. Useful qualified reuse/current shared-token exclusion still missing. | G1/G4/G7 |
| REC-6 | Partial | J ending523/562 and C resumed/cleaning ending branches preserve owed steps. Shared-token settlement/maintenance custody not composed. | G2/G6 |
| SEC-1 | Partial | D confined selected images; audit does not claim hostile kernel/admin resistance or full mount isolation proof. | G9 |
| SEC-2 | Partial | S resolved_delivery228 and D exact RO mount806; current deployed credential slots/file modes not inspected. | G9 |
| SEC-3 | Unproven | Closed secret validators and R bounded event payloads exist; every argv/log/artifact/private context flow not audited. | G4/G9 |
| SEC-4 | Supported | Normative trust boundary explicitly excludes same-UID in-container credential isolation; D container separation is the mechanism. No claim HOME is a kernel boundary. | Preserve in G9 documentation |
| SEC-5 | Partial | R closed manifests/commands, contracts validation and C artifact parser; exhaustive version/size/capability refusal not executed. | G9 |
| LIM-1 | Partial | L positive per-invocation overrides, frozen defaults and H launch context. Effective actual values at every runner/restore boundary not rerun. | Existing W156162; G9 |
| LIM-2 | Contradicted | Distinct runtime deadlines/offers exist, but T resource expiry is not enforced by host container shutdown. Report-only runtime policy must not substitute. | G1 |
| LIM-3 | Deferred | Advanced cumulative/role/currency/shared capacity contracts explicitly deferred; L explicitly per invocation. Measured vs estimated/unknown preserved in audit. | No v12 gate invented |
| LIM-4 | Partial | E/J owed cleanup and failed endings remain; no universal token shutdown enforcement. No cumulative development budget gate applied. | G1/G6/G9 |
| OBS-1 | Partial | O read-only viewer/status separated from serving; shared token/expiry/maintenance display absent from traced projection. No fresh all-store no-mutation proof. | G8 |
| OBS-2 | Partial | R receipt/activity + O freshness distinguish awaiting vs dispatched/answer; all required observed/configured states not exercised. | G8 |
| OBS-3 | Partial | E start failures, R bounded fault code, J per-stage containment and O diagnostics; enforcement-loss/token diagnostics not connected. | G1/G8 |
| OBS-4 | Supported | Project durable record policy; this flat permanent dossier bound to W275513 at275521. Existing historical nested locators preserved. Not a filesystem migration claim. | Preserve |
| OBS-5 | Supported | Current checkpoint/handoff/new discussion read in this claim, earlier immutable evidence preserved; human WIP is optional. Runner-wide automatic enforcement unproven. | Preserve; G9 if product automation selected |
| DEP-1 | Partial | P explicit configuration/storage/deployment layout and authority identities. No live installation/root audit. | G9 |
| DEP-2 | Partial | P image base/provenance and H/D pinned digests; complete installed image/provider/build coherence unverified. | G9 |
| DEP-3 | Unproven | Explicit store schemas and L compatibility generations exist; all migrations preserving unknown token/runtime obligations not audited and new token schema absent. | G1/G9 |
| DEP-4 | Supported | Owner scope excludes cutover; this audit uses only v11 coordination and changes no deployment/backlog/authority. No inferred v12 production adoption. | Owner selection only |
| Sections 1–2 | Partial | Python host and worker provider separation are connected (A/J/H/D/R). Accepted DESIGN is normative; module comments/old experiments do not override it. Shared maintenance role missing. | G1/G2 |
| Section 17 | Unproven | No dynamic conformance run authorized. Historical W270664 evidence exactly byte-bound; this source matrix cannot certify its required boundary proofs. | Acceptance listed in G1–G9 |
| Section 18 | Partial | Reliable parallel Jobs/reuse/monitor remain target; concrete isolation/false-success gaps remain v12. Live detach, broad stress/performance, richer TUI, distributed/generalized engine work deferred. | First connected G1–G7 slice; no broad refactor gate |
| Section 19 | Contradicted | Host resource mutations, absent shared renewal/enforcement/reset contradict selected policy. Numerical token/grace/schema policy must be pinned before execution, not assumed from TOKEN_SECONDS. | G1/G2 |
| Section 20 | Supported | Historical references are preserved with explicit supersession; no old acceptance rewritten or treated as expanded design acceptance. | No historical evidence deletion |

Uncovered subclauses remain explicitly partial/unproven rather than silently
covered by a neighboring passing mechanism. G9 is not permission for a broad
campaign: the owner should select each narrow assurance question separately.
