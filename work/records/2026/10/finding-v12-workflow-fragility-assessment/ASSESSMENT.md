# Bounded design assessment — W370747

## Recommendation

Keep the current architecture and correct the places where its owners disagree. For v12, make the selected template executable against the installed role adapters before admitting work; make observation reconstruct the same resolved execution inputs as serving; preserve safe failure causes; and give a failed execution an explicit settlement path independent of review success. Prove those together through the supported ordinary command with deterministic providers. Do not make a universal workflow engine or a new central store a prerequisite.

These are recommendations, not specification amendments or implementation assignments. Owner E370747 selects assessment only. W370555 and W370688 remain the current correction owners; this assessment neither expands their acceptance nor blocks them.

## Evidence and limits

The selected documentation Job reached a real implementation candidate, then a faulted review with no verdict. Its accepted preparation had inherited a single-role pilot's required `proposal` output. The source review adapter requires `findings` and `logs` and rejects other-role required outputs. W370560 independently checked the retained input and reproduced both refusals. The exact image/source byte equivalence and retained exception text are not established; the declaration incompatibility is confirmed, and is a strong explanation of the runtime failure.

W370555 reproduced the observation identity defect: serving uses the Job-composed manifest while observation uses the installed manifest. The only changed launch-context member in the focused probe was runtime_input_digest; serving adoption succeeded, observation refused, installed-task control passed. The actual implementation later completed without intervention. The fixture proves the source mismatch, not full installed-binary equivalence.

W370560's supported disposition pending read shows native review assignment generation2 still active and no authority verification/review receipts. The worker's verification exit0 is distinct from an authority receipt. Source projection gives faulted exchange no conclude act; ordinary ending performs intake/pass before cleanup. A stopped review container is therefore compatible with an active workflow assignment and unsettled cleanup. This does not prove every recovery hook is absent. No standalone installed reclamation command was identified. Its prepared closure command is not a cleanup command and has not been executed.

W370268 also records fresh-install startup problems: create required an existing control store, serving held the instance guard needed by create, a workspace directory prerequisite was missing, and standalone observation required configuration omitted by the packet. The observed start/stop/create/start workaround is evidence of a gap, not the proposed routine design.

Canonical evidence:

- `baton:work/records/2026/10/finding-v12-useful-documentation-execution/PROGRESS.md` and evidence/claim-370272, claim-370433.
- `baton:work/records/2026/10/finding-v12-template-job-observation-identity/review-2026-10-28T02-03-46Z.md` and evidence/claim-370577.
- `baton:work/records/2026/10/finding-v12-documentation-review-startup-fault/review-2026-10-28T02-09-13Z.md`, CLEANUP-RESEARCH-370686.md and evidence/research-370686.

## Design map and bounded changes

| Area | Current DESIGN requirement | Smallest v12 outcome | Later consolidation |
| --- | --- | --- | --- |
| Template stage contracts | SCH-1/1a, ID-1/4, ART-2/3, REV-1/2 | Resolve and validate the selected template's actual role/input/output contracts together before effects; maintain per-role required results | Extensible template language, generalized plugin registry or arbitrary workflow graph tooling |
| Resolved execution inputs | SCH-1/6, ID-3/4, DB-4/5/7, HOST-2/3 | Reuse pure composition and pinned owner facts across consumers; fix W370555's demonstrated disagreement | Repository-wide immutable execution-description framework and broad deduplication |
| Safe typed failure | OBS-3, RUN-6, REC-1/3 | Persist bounded known refusal cause and originating boundary with exact attempt/operation and safe locator | Universal exception taxonomy, rich dashboards and diagnostics platform |
| Recovery/settlement | Primary lifecycle, HOST-1/6, ART-7/9, TOK-5/6, REC-1 through7 | Expose and resume exact owed settlement for stopped failed attempts, preserving evidence and honest holds | General recovery planner, automatic reset/repair, cross-deployment migration |
| Deterministic workflow proof | Section17, REV-1 through4, OBS-1, SCH-1a | Exercise real role adapters and output validators through ordinary admission, review, correction/failure and report-and-hold | Broad stress, exhaustive provider matrix and performance campaign |
| Routine startup | OBS-0/0a, HOST-8, DB-3 through7 | Install prerequisites once and support create on the normal running deployment without manual supervisor cycling | General installer/supervisor redesign |

### 1. Template-owned stage contracts

SCH-1a already assigns input/output and failure/correction rules to the template. The present split permits a template to name logical consumed/produced results while an unrelated installed manifest supplies incompatible concrete declarations. Merely copying the right union into the next packet fixes that packet; it does not enforce the template promise for the next operator.

Proposed v12 boundary: the selected development template/profile supplies a versioned role-contract descriptor that binds stage, adapter compatibility, consumed result kinds, produced result kinds, per-role requiredness and relevant constraints. Admission/preflight validates its composition with installed capabilities before claim/launch/provider effects. Choose one owner for composition; do not add another helper that checks a duplicate contract and then bypasses the manager.

Keep the generic host artifact-neutral under ART-2. Generic validation can check declared shape/identity and descriptor compatibility; development adapter/profile code owns the meanings of proposal/findings/logs. Do not import provider implementation into the generic manager or let arbitrary template callbacks run under database transactions.

The current shared manifest may use optional outputs across roles, but an implementation still owes a valid candidate and review still owes a valid verdict and required evidence. Optional-in-shared-declaration must never mean optional-for-success. W370688 is already selected to correct and prove this shared composition; do not redesign its delivery mid-claim. After acceptance, separately assess whether reusable admission enforcement is still missing. New descriptor/schema/version semantics require owner approval before any DESIGN amendment or dependent implementation.

Acceptance proposal: actual composed inputs admit both adapters; missing review outputs and required other-role output refuse before provider dispatch; wrong artifact types/constraints and missing role-required results fail consumption; no receipt or verdict is fabricated; old installed single-role workloads retain their selected semantics.

### 2. One resolved execution description, without a second authority

Recommend one logical resolution, not one mutable global object. A Job contract, an execution specification, an attempt and its observations remain different things under ID-1/4. A review execution legitimately consumes the producer checkpoint and may have different runtime inputs from implementation. Requiring all stages' runtime digests to be equal would violate that distinction.

For the immediate fix, shared pure composition plus owner-supported read-only task access is sufficient. W370555 owns it. Preserve the Job/template/configuration versions and exact task/policy/limit/source bindings used by an attempt; consumers must reproduce or read those pinned facts, not reinterpret them using today's defaults. Observation reads, collection validates produced bytes, and recovery reconciles physical effects: sharing resolution does not share those capabilities or authorize observation to perform recovery.

Do not have observation trust launch.json as its expected identity: that makes the evidence validate itself. Do not cache a replacement authority in a sidecar, open another store inside a transaction, or add cross-store atomicity. If a later versioned resolved record is selected, each owner still owns its facts; the record binds references and versions, with stale/missing facts producing an explicit held/refused result. A broad migration of all paths to a new carrier is v13 unless a concrete v12 failure requires it.

Acceptance proposal: two distinct Jobs sharing a worker, standalone fresh observation and manager restart reproduce exact appropriate inputs; changed configuration does not reinterpret the attempt; composed/installed task controls and nondefault limits work; wrong-attempt/corrupt launch refuses; status changes no application state. Extend to collection/recovery only at their actual consuming boundaries, without calling serving factories to make the test pass.

### 3. Safe typed failures

The generic `agent` fault preserves secrecy but loses the known declaration refusal. OBS-3 already requires a bounded actionable cause. Printing arbitrary exception messages would trade an observability defect for credential/path disclosure.

Proposed bounded outcome: define a small allowlisted cause for known adapter preconditions, with exact originating component, attempt/operation, observation time and safe diagnostic locator. For this case, `role-output-contract-mismatch` is an illustrative proposal, not a selected wire enum. Carry structural role/output identifiers only after bounded validation; no prompt, credential, provider output, stack trace or unconstrained exception prose. Preserve generic unknown-agent failure for unclassified exceptions and explicitly mark missing details.

Known contract incompatibility should normally refuse at preflight; the worker still needs a typed defensive failure if drift or malformed input reaches it. Both sides need version/compatibility treatment: do not silently widen an old closed terminal schema. The choice of wire version and code vocabulary needs owner approval before implementation. Existing logs/cause evidence must remain readable.

Acceptance proposal: deterministic real adapter refusal reaches public diagnostics with stable safe cause and exact identity; malicious secret-shaped inputs and arbitrary exceptions cannot leak; unsupported failure schema is explicit; provider failures remain distinguishable from contract refusal; recording failure cannot erase the original failed state or create success.

### 4. Explicit recovery states and owed operations

REC-1 calls for independent axes. A single `exceptional` label cannot answer whether a provider is running, a result awaits consumption, an assignment is active, a token is held, or cleanup is owed. Show facts plus the precise next supported operation and its preconditions; do not invent a new monolithic state machine merely to rename those facts.

Proposed bounded outcome: make the stopped/faulted review case reconcilable through a supported manager operation with durable intent, exact assignment/attempt/runtime/resource bindings and idempotent result. It must separate execution cessation/ownership settlement from result acceptance, assignment disposition and optional destruction. UNKNOWN runtime/launch state remains held; exact positive cessation and the selected primary lifecycle permit execution ownership release without a successful verdict. Preserve workspace/output and retain the absence of a verdict. Closing Work must not imply container cleanup, and an exited container must not imply accepted work.

The existing ordinary answered-ending chain is evidence of a code/spec mismatch where it gates execution settlement on intake/review success. Primary lifecycle/HOST-1/ART-7 take precedence over historical mandatory freeze/intake/cleanup language when defining execution-gate release. This does not retroactively revoke the specific W370268 operator grant's cessation-plus-settled-cleanup condition before supervisor stop; any exception or live operation still needs the owner's separate selection. Do not delete a container merely to make the status look settled.

Acceptance proposal: actual faulted adapter, confirmed exact stop, persisted failed execution and preserved candidate; no accepted verdict; physical uncertainty refuses release; restart at intent/effect/record cuts resumes without duplicate provider/container effects; replay and stale-assignment refusal work; no mandatory helper/normalization launch or evidence deletion. Test the native command and read-only status, including active authority assignment versus quiescent runtime. A library-only API or hand-authored SQL is insufficient. Changed invalid input needs a new selected contract/revision, not an unchanged automatic retry; REC-7's installed-configuration reuse remains the routine target, while any deployment migration is explicit DEP-3/4 work.

### 5. Complete deterministic workflow coverage

Replace confidence from independently green preparation steps with one reusable composed regression for this exact template. Keep component tests; add the missing joins. Use actual role adapters and validators, simulated providers at their normal invocation boundary, and deterministic engine observations supplied through the owning APIs. The fixture must not write authority receipts or mark cleanup successful itself.

Required outcomes to propose as independently reviewable acceptance:

1. Start from a disposable supported installation/configuration; ordinary input-only create resolves the template and admits both roles without supervisor cycling or per-run packet programming.
2. Implementation produces a candidate on the selected base; its verification evidence stays distinct from authority verification. The real collection boundary retains exact bytes and attribution.
3. Independent review consumes that exact frozen candidate under separate ownership, publishes a valid verdict, and report-and-hold exposes it without integration.
4. A changes-requested verdict yields one correctly bound correction, followed by independent review; an agent/contract fault yields a typed failure and supported settlement, not a fabricated correction or review.
5. Restart/replay at the relevant launch/receipt/handoff/settlement cuts preserves identity and prevents duplicate effects. Missing/malformed output and altered checkpoint cannot pass.
6. Observation stays truthful and read-only throughout. Two independent Jobs sharing installed resources demonstrate that one held Job cannot corrupt or falsely complete the other; actual parallel readiness remains a separate evidence claim if this fixture runs serially.

The routine-startup 60-second requirement retains its actual endpoints. Deterministic timing can detect orchestration overhead but cannot establish real-provider startup/authentication latency. No new live run is proposed here merely to repeat an integration test; reuse relevant actual evidence and select a live question only when fake boundaries cannot answer it.

## Scheduling recommendation and owner decisions

At canonical readback370761, W370555 is active at baton.claude, W370688 at baton.codxpc, and W370560 waits on W370688. Keep those assignments and existing dependencies. No new edges or correction Works were created by this planning assessment.

- Consume W370555 for the source identity agreement and W370688 for corrected preparation/role collection proof; W370560 joins preparation with settlement research and exact pending commands. Do not duplicate those deliverables.
- If selected, allocate template admission/adapter compatibility enforcement only for the residual gap after W370688, with one explicit owner for shared contract material. It can be independently reviewed before the broader workflow proof.
- If selected, allocate safe typed refusal delivery and stopped-failed-execution settlement as separate outcomes. Coordinate the worker-exchange schema and source file ownership before parallel edits; serialize shared-file changes. Neither should require broad workflow refactoring.
- If selected, allocate reusable supported-path deterministic workflow proof after the exact candidates it consumes are independently accepted. Record real dependency edges then. W370268/W321608 remain existing adoption consumers; this assessment creates no second authority or new live gate.
- Startup create/serve compatibility and installer prerequisites are a concrete OBS-0a residual to classify before the next ordinary deployment; do not normalize the start/stop/create/start workaround as the target.

Owner decisions requested: select which residual v12 outcomes to schedule; approve any new role descriptor or failure wire contract before DESIGN changes; select the eventual failed native Job disposition/settlement separately. General descriptor frameworks, arbitrary workflow engines, comprehensive recovery planners and broad stress/TUI work remain v13. No specification change, code change, test execution, live run or deployment action was performed for this assessment.
