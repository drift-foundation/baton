# Plan — v12 team hierarchy and shared approvers

1. [done] Record the confirmed need for shared principals, hierarchical team
   scopes, and one-to-one leaf approvers.
2. [done 2026-08-25] Define the principal, organizational node, membership, role
   grant, repository and route records without conflating their identities.
3. [done 2026-08-25] Rule inheritance, local binding, masking, alternatives and
   quorum semantics with concrete positive and ambiguous examples.
4. [done 2026-08-25] Define deterministic resolution, audit evidence, unified inbox,
   capacity and runtime projections.
5. [done 2026-08-25] Add conformance cases for shared subtree approval, leaf-local
   approval, absent principals, ambiguous grants and cross-scope isolation.
6. [deferred; clarified 2026-09-04] Design the Teams and Inbox views for
   hierarchy, inherited grants, and one cross-team manager identity before
   implementation. The UI and command surface must select an effective scope
   without manufacturing a separate participant identity per team.

## Reviewer design pass — 2026-08-25

1. [done] Revalidate the requirement against the current Python v12 authority:
   participant identity, global capabilities, opaque routes and actor-only
   receipts cannot represent scoped shared principals safely.
2. [done 2026-08-25] Rule a strict organizational forest, separate canonical
   principal/scope/membership/grant/mask/route/repository records, augmenting
   inheritance with explicit masks, and authority-derived effective scope.
3. [done 2026-08-25] Rule explicit one-of/all-of/threshold decision policy;
   freeze approval eligibility and threshold at the proposal policy generation.
4. [done 2026-08-25] Keep inbox, runtime and capacity principal-global while
   keeping availability operational and never authority-changing.
5. [implementation-gated] After W1431/W1433 ordering, decompose schema and
   resolver, assignment/receipt migration, scheduler/manager projections,
   conformance, and Teams/Inbox UX into independently reviewable M6 Jobs.
6. [verification-gated] Run the positive/negative/race/retry matrix pinned in
   `FINDING.md`; no production implementation is authorized by this design
   pass.

## Confirmed ordering — 2026-08-25

Slawomir approved the complete M6 baseline in T9901 message 10740. Design and
conformance specification are complete. Items 5-6 in the reviewer pass remain
gated behind W1431/W1433 and will be decomposed into new implementation Jobs;
W9901 does not authorize production edits while those gates remain.

## Ordering clarification — 2026-08-26

The final sentence above is superseded for compatibility work: W9901 still
does not authorize the full M6 hierarchy feature, but its approved model is a
binding constraint on M2-M5 foundations now. The W1431/W1433 identifiers are
pre-migration history; current full implementation remains ordered through W9
to W10.

1. [done 2026-08-26; W16793] Audit active v12 authority and Worker Manager
   foundations for irreversible flat `team.member`, actor-only receipt,
   route/scope and principal-locality assumptions.
2. [queued as W16821, W16823 and W16830] Correct only incompatibilities that
   would invalidate current work later. Authority principal/scope provenance,
   trusted-manager execution context and approval attestations are separate
   provider Work; approver obligation 16832 owns the serial dependency edges.
3. [still deferred to M6] Implement the complete hierarchy resolver, grants,
   masks, approval policy, projections and Teams/Inbox UX.

## Next planning action — owner clarification 2026-11-21

Capture complete; W9901 remains parked pending explicit scheduling, not executing. Revalidate existing principal/scope decisions and historical milestone references against current code and DESIGN. Map the confirmed multi-project/team operating model, cross-team filing and clarification dependencies, shared visibility, resource reuse and operator view to current capabilities; identify concrete gaps and update normative DESIGN before dependent implementation. Reuse W385331 rather than duplicate its clarification/discovery work. Prepare a read-only v11 migration inventory and bounded two-project pilot; no backlog copy, new authority, broad implementation, advanced scheduling or automatic launch selected. Current clarification proof remains the active priority.

## Selected next priority and decision gate — 2026-11-21

Supersedes the earlier unspecified scheduling: owner selects this as next PLANNING priority after acceptance/checkpoint of current clarification proof. Before dependent implementation, revalidate old milestones and DESIGN, produce concrete user workflows and gap/coverage map, and bring every unresolved product/UX ambiguity to the owner with scenarios/options/recommendation. Do not manufacture semantics or start a broad teams rewrite. Select the smallest two-project proof and coordinate with W385331 discovery/dependency work. Ledger activation/routing follows the current checkpoint; this note alone changes no graph gate.

## Owner priority supersession — full-suite failure, 2026-11-21

W385517 is now the current showstopper: resolve the ten full-suite failures and obtain clean owner-run acceptance before moving on. This supersedes immediate W9901 planning after the clarification checkpoint. Team/UX decisions remain valid; do not begin W9901 implementation or restart product planning while the blocker is unresolved.

## Planning release — 2026-11-21

The temporary W385517 full-suite stop above is satisfied: owner-run acceptance at 73506123 accounts for 11844 tests, 11842 passed and 2 optional skips, with zero failures/errors/unaccounted. Evidence is committed at 9fa0ec37 and W385517 is canonically closed. W9901 is now the selected planning assignment. This supersedes the temporary instruction not to restart planning; production implementation remains unselected.

Codexpc owns the bounded planning pass after routing, unpark and successful claim: revalidate current DESIGN, code and historical decisions; deliver concrete two-project operator workflows, a capability/gap map, an explicit unresolved-decision list, read-only migration inventory, and the smallest deterministic two-project proof plan. Coordinate with W385331 without transferring its implementation scope. Preserve confirmed decisions; propose specification deltas for owner review wherever semantics remain unsettled. No product edits, live runs, instance changes or migration in this pass. Return evidence and a concise decision packet in T9901, then pass to baton.decide and verify claim release.

## Native planning preparation — supersedes direct execution, 2026-11-21

The owner selects the complete workflow and v12 execution, as recorded in FINDING. M385538's direct planning default is superseded. Codexpc's immediate host assignment is bounded preparation: inspect existing supported native Job tools/templates and current installed instance readiness read-only; prepare the planning task and exact minimal kickoff commands, required inputs, routing, verification and retained-result consumer. Reuse existing tooling; no new bespoke launch helpers or extended qualification framework. Report any concrete blocker with the exact unsupported operation and smallest remedy. Do not use incomplete target functionality as a generic blocker or silently execute the substantive planning directly instead.

The native planning task must deliver the workflows, capability/gap map, decisions and bounded two-project proof plan above, with complete native workflow acceptance explicit. Planning proposals do not authorize product/spec changes. Existing no-live-run/no-instance-write boundary applies to this preparation: return the concrete launch packet to the coordinator for the supported operator execution sequence. Independent review and human Git checkpoint remain required; v11 retains the canonical coordination record until explicit cutover. No full-suite rerun is needed merely to prepare this task.

## 2026-11-21 — baton.codxpc E385541 native planning packet

M385539 execution selection revalidated. Preparation complete at evidence/native-planning-385541/REPORT.md and KICKOFF.md, task TASK.txt. Existing /3 template supports native planning and independent review; do not perform substantive planning on host. Installed source ac17a5ad/7ac02c7f cannot be replaced by manager create --source (installed only); current selected base9fa0ec37 requires the prepared fresh bootstrap/composer sequence. Latest owner ruling is carried explicitly in task statement. No live actions, product edits or new launcher. Static command/input checks passed; future installation/readiness and launch remain operator steps. Return packet to baton.decide; native planning results and later complete automatic-workflow proof remain pending.

## Planning acceptance addendum — Work lifecycle, 2026-11-22

Evaluate the native planning result against the owner-confirmed Work lifecycle in FINDING: durable discussion, design, plan creation/review, implementation, verification/review and human integration/acceptance; flexible templates with explicit transition conditions and correction/question/discovery paths. Identify who may satisfy each condition and escalate unsettled authority/UX choices. The running w9901-native-planning-1 was submitted before this addendum; do not claim it received these new bytes or mutate its frozen assignment. Reconcile this ruling during result review and arrange a bounded follow-up if the returned plan omits it. This addendum neither stops nor restarts that Job.

## Planning acceptance addendum — typed Job phases, 2026-11-22

Apply FINDING's Job-versus-phase ruling: every user-facing Job has phases selected according to its type; separate child outcomes are Jobs with their own phases. Propose the explicit mapping to existing Work/Job/stage/attempt identities and distinguish lifecycle phases from scheduler state. Do not silently rename persisted identities or impose one universal phase sequence. Reconcile this later owner ruling at review of the already-running native planning Job; no frozen-input update or in-flight delivery is claimed.

## Planning acceptance addendum — defect sequence, 2026-11-22

Carry the owner-selected defect phases into the proposed typed Job model: reproduce/diagnose -> fix -> write tests based on reproduction -> review -> verify. Reconcile against the running planning result at review; its frozen assignment has not been changed.

## Planning acceptance addendum — immutable templates, 2026-11-22

Apply FINDING's immutable-template ruling: multiple Job-type templates; each Job starts from an identified immutable template and can explicitly adapt its own phase plan while retaining evidence and acceptance obligations. Job outcomes can produce new templates with provenance, never silently mutate originals or other Jobs. Identify unsettled publication/plan-change authority and runtime transition semantics as owner decisions rather than inventing them. Reconcile this addendum during review of the running native planning result; no in-flight delivery or mutation of its frozen assignment is claimed.

## Planning acceptance addendum — model-diverse review, 2026-11-22

Carry the owner-confirmed preference for different model families across implementation and independent review into future pool/routing planning. Preserve a disclosed same-model, separate-context fallback when the alternate model is unavailable. Do not alter the current native planning run; reconcile this ruling at result review. Identify unsettled availability/fallback semantics explicitly.

## Retained planning recovery review — 2026-11-22

Native w9901-native-planning-1 failed its malformed submitted Python verification argv (literal newline within a string), not a demonstrated planning-content defect. Retained proposal reports provider exit 0, candidate 7a030bc069ac570364c0d3e9e12d34b902ec2a44 on 9fa0ec37, one NATIVE-PLANNING.md path. Coordinator extracted committed bytes into evidence/native-planning-verification-failure-20261122; SHA256 dc2c516c298f0703f626361640f2caae44670e8e62956fd17cf328fe8cd618c4. All five intended heading predicates pass; this is structural verification only. Original proposal files and error evidence retained. Published view reports engine destroyed and implementation reservation released; no state mutation performed.

Next bounded action: codexpc independently reviews the retained candidate and provenance, reconciles the later owner lifecycle/template/model rulings, and returns a concise decision packet. No repeat provider implementation, live change, source import or Git mutation. This explicitly uses the temporary external review bridge for the failed native attempt; do not mark native review or full native recovery accepted. Preserve the native failure as evidence of the remaining recovery gap. Classify already-settled questions against the latest owner decisions instead of asking them again.

## 2026-11-22 — E385551 independent retained planning review

Candidate7a030bc0 over9fa0ec37 verified against original bundle/patch/extracted72907-byte document; SHA256 dc2c516c298f0703f626361640f2caae44670e8e62956fd17cf328fe8cd618c4. Malformed submitted verification argv independently fails compilation; intended five heading checks pass. Evidence: evidence/review-385551/provenance.json. External recovery review only, not successful native review. Verdict: retain useful research; required corrections before executable-plan acceptance. Append-only review-2026-11-22T00-28-23Z.md reconciles M385544–548, corrects the purported thin owner-answer step (existing API refuses escalation replies), separates settled requirements from five owner choices, and proposes smallest next native read-only message/escalation surface followed by authorized owner-decision→retained-continuation under W385331. Preserve unchanged deadlines and no-courier final acceptance. No repeated provider work, live action, product import or protected Git change. Return review to baton.decide; plan/spec implementation remains separately selected.

## Review reconciliation and exceptional-phase gate — 2026-11-22

M385552/review-2026-11-22T00-28-23Z.md confirms candidate provenance and structural checks, retains useful research, and requests executable-plan corrections. Native review/recovery is not accepted. Do not repeat the planning run. Incorporate later owner lifecycle/template/model rulings and the conservative exceptional-phase analysis rule above. The proposed read-only reader is only a prerequisite: complete acceptance requires automatic analysis, owner-facing options/recommendation, recorded owner disposition and supported continuation. Review Q2's routine in-scope plan-change proposal must not be mistaken for authority to perform exceptional-phase recovery automatically; the new owner gate applies there. Remaining substantive choices are recorded in the review, to be resolved without re-asking settled requirements.

## Owner-decision reconciliation — team interface and escalation, 2026-11-22

Carry FINDING's confirmed team boundary and accountable cross-team delivery into the planning amendment. Teams own execution/context domains; callers address a team interface and do not manage its internal workflow. Retain a specific return address and originating request/Job/phase; allow a response-specific reply-to. Receiving-team routing resolves/escalates member -> project -> team -> human operator, retaining one accountable obligation until explicit resolution. Delivery/seen is not an answer. Resolve remaining timing/role-binding details one question at a time; do not re-ask the confirmed terminal operator or assume project/repository cardinality was selected. No live Job/config/schema mutation is authorized by this documentation update.

## Decision settled — phase-plan changes, 2026-11-22

All Job phase-plan changes require explicit owner approval for now. Incorporate FINDING's selected authority; remove independent-review approval of in-scope plan changes from proposed defaults. Agents propose and reviewers assess; owner authorizes mutation. Preserve automatic ordinary progression through the approved plan and the separate exceptional-recovery owner gate. No live assignment or phase plan is changed by this record.

## Decision settled — new template publication, 2026-11-22

All new reusable-template publication requires explicit owner approval for now. Agents prepare proposals and review evidence; owner authorizes publication. Reconcile the review's maintainer-authorized recommendation accordingly. Preserve immutable templates, provenance and unchanged existing Job bindings. No new template is published by this decision record.

## Decision settled — open cross-team filing, 2026-11-22

Any team may file defects, feature requests and questions through another team's public interface; destination owns triage. Apply the confirmed open-intake policy while preserving identity, attribution, return routing, access separation and no automatic execution/dependency merely from filing. Do not re-ask per-team filing consent. Answer-role binding and other unresolved details remain separate.

## Decision settled — busy alternate review capacity, 2026-11-22

Wait for the alternate model when busy; no timer-based same-model fallback merely for busy capacity. Include operator reassignment as the intended intervention capability, explicitly identifying current support versus later delivery. Keep actual-unavailability fallback distinct and preserve admitted limits, ownership and independent-review constraints. No current Job is reassigned by this record.

## Decision reconciliation — shared pools and operator-directed failover, 2026-11-22

Incorporate FINDING's shared subscription-pool model: one team/project does not reserve an agent; pools serve multiple projects with compatible-context affinity. Start without a Baton-imposed pool concurrency cap and collect attributable observations. Preserve existing execution safety/limits and distinguish busy capacity from unavailable provider/exhausted subscription. Operator alone selects a replacement pool for now; same-vendor or weaker-model standby is allowed when selected, without waiving independent review. Plan supported retained continuation and exact cessation/fencing, with no silent live reassignment or deadline reset. Supersede any fixed team-to-worker interpretation and do not treat model diversity as mandatory during owner-selected unavailable-pool fallback. Current changes are decision records only, not a launch or broad scheduling implementation authorization.

## Pool incident policy refinement — 2026-11-22

Use pause-first handling for suspected shared provider/subscription trouble: pause affected work for an initial roughly one-to-two-minute grace period instead of immediate failover. If persistent, present pool-wide retirement/reassignment to the operator under the existing manual-selection rule. Preserve retained state and distinguish suspected pool trouble from confirmed individual execution failure. Settle precise grace/recheck/admission behavior before implementation; no live pool retired or work resumed by this note.

## Decision settled — queue admission and future bounded pools, 2026-11-22

Keep pool queues accepting assignments during transient provider trouble; do not add automatic admission suspension or reassignment. Expose backlog size, waiting age and provider trouble for operator decisions. Separate queue admission from execution-capacity checks so future bounded pools limit concurrent starts while retaining queued assignments. Initial uncapped-per-pool selection remains unchanged; no queue-size bound or automatic reallocation policy is selected.

## Decision settled — throttling and individual review reassignment, 2026-11-22

Model effective capacity separately from configured capacity and availability. Support operator-selected temporary throttling without retiring a pool. Preserve queue admission and account for existing executions separately. Reviewer responsibility must not be bound permanently to a provider: operator can move one review to another pool/provider, retaining exact candidate and handoff evidence with independent context and disclosed same-model fallback when needed. Distinguish individual reassignment from pool-wide moves and preserve manual selection. Identify unsupported operations as gaps rather than claim current implementation.

## Reassignment scope clarification — 2026-11-22

Generalize provider/pool reassignment across all agent roles, not only reviewers. Keep role responsibility/authority separate from provider capacity, preserving task identity, evidence and safe continuation. Review-specific independence remains an additional constraint. This explicitly corrects any narrow reading of the preceding review example.

## Decision settled — non-preemptive capacity reduction, 2026-11-22

Lowering pool concurrency affects only new starts. Always let running agents finish; hold starts until usage falls below the chosen limit, and admit no new execution at zero. Do not evict active agents to satisfy a cap. Preserve queue admission and separately enforced execution deadlines/cancellation. No live capacity mutation selected by this record.

## Decision settled — queued work moves, healthy executions finish, 2026-11-22

Operator-selected pool reassignment moves queued work while healthy active agents finish in their original pool. Preserve original execution attribution and avoid duplicate starts. Handle exceptional executions via the separately approved recovery path. Future-assignment routing is not implicitly changed by this queue move. No live assignment changed by this record.

## Decision settled — persistent pool redirect, 2026-11-22

Apply operator-selected redirection to queued work and future assignments until the operator explicitly changes it. No automatic failback on original-pool recovery. Expose active redirect and preserve attributable changes, original healthy executions and distinct exceptional-recovery handling. Reconcile the preceding future-routing unknown as settled by this ruling.

## Decision settled — project > team > global redirects, 2026-11-22

Resolve applicable pool redirects by explicit project > team > global precedence. Preserve persistent operator control and non-preemptive execution handling. Do not infer global scope from a project/team redirect. Include this precedence in the consolidated planning revision and deterministic acceptance scenarios; configuration representation remains design work.

## Selected consolidation and independent fidelity review — 2026-11-22

Owner authorizes codexpc to consolidate the retained research, independent review and subsequent confirmed decisions into one revised executable planning proposal. This is the bounded revision of existing work, not another native provider planning run or product implementation. Codexpc owns a new CONSOLIDATED-PLAN.md and attributable PROGRESS entry; preserve the immutable native candidate, earlier reviews, FINDING decision history and prior evidence. Make the current proposal readable without requiring readers to reconstruct append-only history, but include exact provenance for each requirement and supersession.

Separate complete Job/phase/conversation/escalation/recovery workflow from shared subscription pools/context reuse/scoped redirection, then order the smallest implementation slices with dependencies and outcome-based focused acceptance. Correct review-2026-11-22T00-28-23Z.md findings. Reconcile T9901 through M385568 and current FINDING/PLAN; distinguish owner decisions from coordinator interpretation, reviewer recommendations and unresolved details. Include the failed native planning run as a concrete automatic-analysis, owner-disposition and retained-recovery scenario. Do not expand advanced scheduling/hardening scope or claim complete/native recovery acceptance. No product/schema/spec edit, live run, instance mutation, main Git mutation or full-suite run.

After codexpc returns the exact consolidation and posts its handoff, K independently reviews fidelity against canonical T9901 messages and recorded owner rulings, as explicitly requested by owner. K checks omissions, contradictions, unauthorized defaults, altered scope, supersession accuracy, implementable ordering and acceptance; message text is coordination evidence and must be checked against pinned decisions. K writes a new append-only review, not edits to codexpc's consolidation. Serial ownership: K starts only after codexpc handoff and supported manual assignment; no overlapping edits. Return to coordinator/owner after this independent review before implementation selection. Preserve existing claims and role protocols rather than impersonating a handler.

## K fidelity review and latest model decision — 2026-11-22

K review-2026-11-22T03-50-15Z.md / M385577 requests bounded correction before acceptance. Reconcile F1-F3 (existing W16830 ownership, shared principal inbox/manager surface, model-diverse assignment ownership), minor corrections and latest provider/model options and deferral ruling. Latest owner confirmation that changing model or pool is manual resolves F4's authority question; availability classification remains open. F5 new starts during transient suspicion, F7 redirect chaining and F6 historical ordering confirmation remain explicitly unresolved, not implementation defaults. Preserve prior candidate/review and provide a separately identified revised consolidation for K delta review. No implementation, live execution or graph-edge change selected.

## Decision update — operator chooses provider-problem response, 2026-11-22

Report provider/model trouble and request owner disposition: defer for N minutes/until a time, or select another model/pool. No automatic grace duration or fallback. Reconcile earlier pause-first wording with this explicit owner control. Keep deferral scope, before-decision start handling and at-time resumption semantics explicit until selected; do not hide them behind F5's grace-period options. Queue admission, non-preemption and finite execution safety remain unchanged.

## Decision settled — timed deferral authorizes resumption, 2026-11-22

Resume automatically at expiry of the owner's selected deferral, without another approval prompt. Any renewed failure returns to the owner for a new manual disposition; no automatic repeated retries. Preserve durable due-time/decision attribution and normal safe admission/continuation checks. Incorporate restart and duplicate-trigger cases into focused acceptance. Deferral scope remains separate.

## Decision settled — scoped deferral and selective model change, 2026-11-22

Support explicit individual phase/Job, model-within-pool and whole-pool dispositions. Permit a selected phase/Job to use another/weaker model while other work remains deferred for credit reset with its model choice unchanged. Bound automatic timed resumption to the selected scope and preserve renewed-failure owner handling. Reconcile prior scope unknowns; expose rather than guess interactions of overlapping selections. No live mutation authorized by documentation.

## Decision settled — transitive pool substitutions, 2026-11-22

Reconcile K F7: operator-selected A -> B and B -> C means A-assigned work resolves to C, persistently until canceled/changed. Pools themselves do not decide to redirect. Combine with explicit scoped precedence and non-preemptive healthy execution handling; expose original/effective route and reject cycles/ambiguity without inventing a destination. Include deterministic chain and scope examples in the revision. No live mutation.

## Decision settled and correction assignment — 2026-11-22

Owner confirms W9901 can proceed independently of historical W9 -> W10 ordering, with existing Works/unfinished obligations preserved. This explicitly resolves K F6; no canonical edge is removed here. Codexpc now owns a bounded revision of CONSOLIDATED-PLAN.md against K's review and later owner rulings through this section. Preserve the reviewed r1 bytes in evidence before editing; produce revised identity and change/provenance summary. Resolve F1-F3/minor omissions, reconcile F4-F7 against latest decisions, and carry provider/model options, deliberate timed deferral, automatic authorized resumption with new-failure owner handling, scoped selective model changes and transitive redirects. Any remaining detail truly unsettled stays labelled open; do not invent defaults or re-ask settled decisions. K independently delta-reviews after codexpc releases. No product/spec edits, live actions, new provider run, Git mutation or full suite authorized.

## Current correction assignment refinement — staged delivery, 2026-11-22

Owner approved bounded staged delivery to prevent W9901 becoming a single expanding implementation Job. Codexpc's next revision must incorporate FINDING's staged-delivery ruling: first complete no-courier recovery loop; then explicit typed Job phases; then two-project communication/dependencies; then incremental pool controls. Preserve every confirmed ultimate outcome, but separate first usable acceptance from subsequent requirements and open decisions. Reuse existing provider Work/implementation ownership and mechanisms; propose bounded Jobs with clear outcomes, dependencies and joined acceptance rather than a broad rewrite. Do not install graph edges or create new implementation assignments in this document correction. K independently delta-reviews fidelity and practical sequencing after handoff. M385585 remains active with this refinement; no implementation yet.

## K r2 acceptance and narrow addendum — 2026-11-22

K accepts the four-stage umbrella proposal and prior corrections in review-2026-11-22T04-17-25Z.md. STAGE-1-CLARIFICATIONS.md answers D1–D5 while preserving the reviewed consolidation bytes: new linked verification/review-only successor, general exceptional-analysis later outcome, simulated proof qualifications, redirect examples, deferral restart checks and explicit pending implementation allocation. Narrow K delta-check precedes Stage 1 selection; no implementation or live action authorized.

## Accepted plan/addendum; Stage 1 selection pending — 2026-11-22

K review-2026-11-22T04-21-24Z.md accepts CONSOLIDATED-PLAN r2 plus STAGE-1-CLARIFICATIONS.md with D1–D5 resolved. Their reviewed bytes remain unchanged. Contract, analysis-role binding and implementation ownership are next selections, not yet implementation authorization.

Carry K's low note into the Stage 1 recovery contract: corrected successor verification failing again yields one new attributable analysis and a new owner item, never an automatic further successor. Each recovery round requires its own owner decision; duplicate/replayed notifications do not create extra analyses. This makes the existing renewed-failure owner gate explicit, without another full-plan review. Analysis failure itself remains separately bounded by the selected contract, not recursively treated as permission for unlimited analysis.

## Stage 1 analysis-role selection — 2026-11-22

Dedicated analysis role selected by owner: inspect evidence and retained output, author diagnosis/options/recommendation, no product/verifier/execution mutation or recovery authority. Use configured pool assignment rather than a hard-coded provider. This resolves the role-purpose/authority selection in U2 for 1-A; concrete configuration binding and finite analysis-failure handling remain contract work. Preserve owner recovery gate. No live assignment is made by this record.

## Stage 1 analysis-failure selection — 2026-11-22

Owner confirms analysis failure goes directly to Slawomir with partial evidence retained and no automatic retry or recursive analysis. Incorporate this finite endpoint into 1-A/U5 acceptance, including duplicate-notification handling and preservation of original versus analysis failure identities. No execution or live operation selected by this decision record.

## Stage 1 recovery behavior selected — 2026-11-22

Owner approves the exact retained-candidate isolated verification plus independent-review successor behavior in FINDING. Next bounded preparation: codexpc writes the Stage 1 contract from accepted plan/addendum and owner selections, with exact identity/input/decision/effect/replay/limit boundaries and finite failure handling. Revalidate existing APIs and required normative DESIGN additions, drafting only changes that faithfully express selected behavior; identify any remaining true decision explicitly. Propose concrete 1-A/1-B/1-C Work allocations and dependencies, reusing existing scope where explicitly authorized, without silently expanding W385331. K independently checks the contract before coding. No live recovery, provider execution, product change, graph mutation or main Git mutation is selected by this preparation.

## Stage 1 E2 resolved — post-verification expiry, 2026-11-22

Owner selects retained verification + held owner item when successor expires before review completes. Owner may authorize a linked review-only execution; no implementation or verification repetition while exact verification evidence remains valid. Amend contract/REC-8 and focused acceptance for this ending, distinct from verification-failed analysis. Existing cancellation/cessation/limits safeguards remain. E1 profile publication approval still pending; no coding yet.

## Stage 1 E1 resolved; bounded contract correction next — 2026-11-22

Owner approves initial analysis 4800/4800/3600 and verification-review 9960/(4800 each)/900 command/3600 review-provider profiles, queue time included in overall limits, no automatic correction/retry. FINDING carries exact clock/ending semantics and publication approval; M385611 supplies E2 expiry handling. Codexpc now corrects contract/REC-8/evidence for K E1–E6, pins immutable profile identities/digests, and preserves prior reviewed bytes. Use delivered principal/scope and declared-worker configuration, without later hierarchy/pool prerequisites. K performs short delta check; no product coding, graph mutation, live run or spec application yet.

## Stage 1 contract accepted; checkpoint before implementation allocation — 2026-11-22

K review-2026-11-22T05-18-37Z.md / M385621 accepts contract r2 (52c2c640...) and REC-8 patch (f3f32e07...), including exact owner-approved profiles and review-only reuse. Coordinator dry-run of the reviewed patch against current DESIGN succeeds with fuzz zero. Owner applies the amendment and checkpoints the dossier plus DESIGN; reviewed patch bytes need no cosmetic change to satisfy acceptance.

Prepared serial implementation outcomes are contract section 7: 1-A failure-key analysis pipeline; 1-B owner decision and linked successor admission, dependent on accepted 1-A; 1-C isolated verification/review and joined proof, dependent on accepted 1-A/1-B. Create the three canonical child Works and actual dependencies through supported owner/handler authority after checkpoint, preserving W385331 scope. Native execution is preferred as selected; concrete source, worker/role and independent reviewer bindings are validated at kickoff. No child identity or graph gate is claimed to exist yet. Both 1-B and 1-C must test exact decision profile identity/digest AND selected stage-set agreement, especially review-only recovery. Serial shared-file ownership; no early coding before normative amendment and allocation.
