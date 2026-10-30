# Serving renewal correction

2026-10-19, baton.rvpc, parent W325959 claim333470. Owner selection is parent FINDING.md, “owner execution, resource expiry and actionable failure reporting”; incident identities and attributed evidence are in ../finding-v12-native-pilot-instance-packet/OWNER-FAILURE-EVIDENCE-20261019.md. This is a correction provider, not a duplicate of the native quickstart Work.

Confirmed by read-only source inspection: worker_manager/tokens.py defines LIFETIME_SECONDS=900, STOP_GRACE_SECONDS=30, RENEWAL_LIMIT=4 and public renew(control, token, execution, operation, expected_revision, seconds). Recursive search of product Python finds no production invocation. tools/job_manager.py:_reclaiming composes overdue reclamation/settlement; job_manager/manager.py:serve sweeps then reclaims without renewing. Historical W275775 PLAN explicitly excludes production-consumer migration. Its API acceptance remains valid but does not establish serving integration. The incident is consistent with this missing integration; do not invent an exact reclaim journal operation from absent evidence.

Required outcome: trusted serving host explicitly renews eligible same-execution tokens before expiry using the accepted atomic API, while expiry/revocation still terminates the exact container and uncertain cessation retains ownership. Eligibility must bind current assignment/attempt, resource/generation, launch operation and exact runtime; reject ended, superseded, cancelled, revoked, returned, expired or ambiguous executions. Activity alone grants nothing. Preserve original Job invocation deadlines and limits across renewal and restart.

Policy boundary: retain the accepted 900-second maximum extension, four-renewal bound and 30-second stop grace; do not increase these constants to conceal the defect. Use current committed revision/deadline and trusted host time, with explicit bounded scheduling before expiry. Implementer must pin and justify the scheduling lead and exact eligibility predicate in the candidate packet, including worst-case scan latency and exhaustion behavior. This is implementation-policy preparation under existing TOK-9, not permission to change the normative contract. A 3600-second provider invocation must not be terminated at the initial 900-second lease when eligible host renewal can support it. Do not advertise these finite leases as an unlimited or cumulative Job budget; separately expose genuinely exhausted permission. Any requirement to expand the accepted bound is a concrete owner decision, not a silent default.

Verification: deterministic controlled-clock serving composition, actual public token decisions and fake engine/provider boundaries inside isolated v12 Jobs. Show success beyond initial lease, exact stop/cessation on expiry and exhaustion, no renewal after cancellation/end, two contenders, stale observations, lost reply/replay, restart before/after commit, clock ambiguity, slow/unreachable engine and fairness to unrelated attempts. Preserve populated Job limits and no external I/O in transactions. Tests must exercise the production composition, not just tokens.renew.

Ownership: assigned baton.codx handler owns this dossier's packet/PROGRESS/evidence and its own isolated v12 candidate; reviewer owns FINDING/PLAN/reviews. Expected primary surfaces are tools/job_manager.py serving composition, job_manager/manager.py and a dedicated renewal module/tests if useful. These are evidence/coordination locations, not an exclusive allowed-file list. Sibling diagnostics owns its separate candidate. No shared-tree product edits; overlapping candidate paths are declared before integration and integrated serially into a reviewed combined candidate. Preserve existing unrelated verification-context/image edits. No live pilot mutation, retry, deployment, credential access, provider run or Git mutation is selected.

## 2026-10-19 — preparation scope clarification after first return

Review review-2026-10-19T16-20-30Z.md under claim333518 accepts the newly identified synchronous reclaim latency concern as a planning input, not the untested120/30 scheduling proposal. No candidate or Job delivered. The no-provider/deployment exclusion prevents launching an unselected authoring run; it does not prohibit preparing its proposed immutable inputs and exact operator commands for later selection. This clarifies the earlier combined preparation/execution wording: current milestone is complete preparation, independent preparation review, then exact separate authoring-execution selection before implementation in v12. Parent's desired correction and no-host-fallback remain unchanged.

Existing independently reviewed continuation329953 supplies a supported preparation reference at the same base. Revalidate and adapt only its vehicle, preserving historical packet/instance and excluding unrelated checkpoint files. Resolve routine proposed operands and safe fresh destinations within this dossier, without reading credential contents or granting execution. Owner receives the concrete sealed packet, not an unspecified configuration question. No new product/spec choice or graph gate introduced; implementation evidence remains wholly unstarted.

## 2026-10-19 — sealed preparation reproduced; selected supervisor differs from pilot

Review review-2026-10-19T16-29-00Z.md independently verifies execution333532 manifest96e8d690 and repeats nine preparation checks. It supersedes the missing-sealed-packet finding, preserving unstarted implementation. Source review finds baseline.py:1207 omits the optional reclaim callback, unlike the native pilot's tools/job_manager.py composition. The stated900-second risk therefore does not prove shutdown at token expiry; overall4800/provider3600 limits are different mechanisms. Preparation remains unsuitable for launch recommendation pending exact safe authoring enforcement or an evidenced bounded alternative. No runtime behavior was fabricated from this static finding. Retain immutable packet and prepare a corrected proposal; no new live execution or broad supervisor work selected.

## 2026-10-19 — prerequisite substantiated for owner disposition

Review review-2026-10-19T16-34-00Z.md verifies enforcement333593 manifest a44b24d8 and independently repeats both simulated counterexamples with held cleanup. This supersedes routine packet-correction continuation as the immediate next step: the selected authoring vehicle needs an execution-boundary decision. No safe replacement established among the two inspected compositions; no exhaustive impossibility claim. All prior preparation evidence remains valid and unlaunched.

Reviewer proposes a narrow temporary isolated direct-implementation/deterministic-verification exception solely for authoring enforcement, ending at independent acceptance. No live/deployment/Git authority, token-bound increase or production-renewal bypass. Exact proposal and accepted-vehicle alternative are in latest review. This is NOT an owner ruling or permission. Record actual owner selection before prerequisite allocation/implementation. Parent dependencies and sibling ownership unchanged.

## 2026-10-19T16:45:49Z — owner approves bounded prerequisite exception

Owner M333721, reroute E333722, read under reviewer claim333725: “Approve the temporary exception proposed in review-2026-10-19T16-34-00Z.md: isolated direct implementation and deterministic verification of the authoring deadline/expiry-enforcement prerequisite and required tests. Preserve exact-runtime cessation, unknown holds, invocation limits and retained results. No live provider, deployment, pilot retry, token-duration increase, broad refactor or Git mutation. Exception expires at independent prerequisite acceptance. Pin this ruling before implementation, allocate bounded prerequisite Work and dependencies, then return to reviewed v12 execution for production renewal.”

This explicitly supersedes the pending-owner-decision/no-exception state above only for the bounded authoring prerequisite. Production renewal and diagnostics retain the v12 execution boundary. Reviewer does not become implementer. Allocate the independently reviewable enforcement prerequisite to baton.codx in its own isolated candidate, with W333485 depending on acceptance. The joined acceptance consumer remains W325959; no failed pilot retry or old-packet launch follows from this ruling. Existing source evidence/review16-34 and enforcement333593 continue to define the exact gap.

Decomposition: one coupled supervisor/serving/cancellation enforcement outcome merits its own Work because its execution exception ends at independent acceptance and its result is a prerequisite for later v12 authoring. Do not broaden into production renewal or a generic scheduler refactor. Diagnostics preparation continues under its existing claim and ownership; any dependency for its executable phase must be coordinated at a safe handoff, not by suspending an active preparation allocation. Actual shared-path integration remains serial.

## 2026-10-19T18:58:35Z — prerequisite closed; fresh preparation resumes

Under claim334634, read owner close E334628 and complete T333735 through334625. Owner closed W333735 satisfying after exact reviewed integration,72 focused integration tests and human checkpoint `a9f4fa4da2323a357ae15aefbc5d7d22d41487b6`. Canonical dependency wake334629 removes the prerequisite gate; no reviewer edge removal was needed. Independently checked all six committed file hashes against candidate-333964-final/CANDIDATE.json. Accepted enforcement review is baton:work/records/2026/10/finding-v12-authoring-expiry-enforcement/review-2026-10-19T17-25-12Z.md; integration evidence is INTEGRATION-20261019.md there. Temporary direct-execution exception expired at acceptance and is not available to this Work.

This supersedes the waiting-for-prerequisite checkpoint and the old base selection for new preparation. Next bounded milestone: baton.codx prepares a fresh sealed isolated v12 authoring packet at the accepted committed base, using tools.authoring_enforcement and exact accepted source pins, with concrete commands and disposable deterministic preparation evidence. Preserve execution333532 and enforcement333593 untouched; the old packet must not launch. Fresh packet review and exact separate execution selection precede actual authoring. No implementation on the host, provider run, deployment or pilot retry is authorized by this continuation.

Enforcement does not add production renewal. A valid initial token can still expire at900 seconds and the accepted wrapper will stop/hold authoring then; provider3600/supervisor4800 ceilings do not grant3600 seconds of resource permission. New packet must disclose effective authoring stop/cleanup behavior and retained-results/recovery handling without extending leases or resetting invocation limits. Production acceptance still owes controlled-clock serving proof through3600 with eligible explicit renewal. PACKET.md's120/30 scheduling proposal remains unaccepted pending latency/eligibility proof.

Ownership remains separate: baton.codx owns this packet/PROGRESS and isolated renewal candidate; reviewer owns FINDING/PLAN/reviews. T333485 M333677 declares diagnostic paths, with no expected tools/job_manager.py or job_manager/manager.py edit, but intake.py is a potential intersection and diagnostics also uses attempts.py changed by the accepted prerequisite. Prepare against the committed enforcement base and declare actual later overlaps before serial integration. One coupled production-renewal outcome remains appropriate; no new split, scope expansion or sibling claim change. W325959 retains joined acceptance.

## 2026-10-19T19:05:07Z — fresh enforced preparation accepted

Review review-2026-10-19T19-05-07Z.md independently accepts execution334650 preparation, manifest e3b70f5bc3749b9c83fbfa175b1ecc0c64dc36acdc0e7c30e04b6289e9747b7f. All59 seals and10 disposable preparation checks pass. Generated start binds accepted tools.authoring_enforcement and committed prerequisite bytes. This supersedes the fresh-preparation-in-progress checkpoint, not the prohibition on unselected execution. Exact proposed owner execution operands and remaining preflight/900-second permission limits are in the review and sealed OPERATOR. No Job or product implementation exists yet; old execution333532 stays forbidden. Pass concrete proposal for separate owner selection, preserving sibling ownership and joined acceptance.

## 2026-10-19 — owner withdraws launch readiness; shared guard dependency

Reviewer claim334932 read owner reroute334915 and complete T333485 through334909. Owner M334765 had selected one renewal authoring invocation, but later E334915 explicitly withdraws execution334650 launch readiness after the diagnostics startup failure and requires the shared dependency gate. No launch, rerun or extension of the expired exception is authorized. This supersedes prior execution-readiness recommendation and pending-selection checkpoint; preserve all sealed preparation evidence and implementation ownership.

Shared provider W334910, baton:work/records/2026/10/finding-v12-authoring-manager-guard, follows closed W333735. Actual diagnostic startup evidence and confirmed source chain show Guard.operations_from acquires the workspace manager guard before child_compose.operations_from tries to acquire it from another process. Renewal334650 uses the same pinned topology, so it is affected without needing another live reproduction. Prior preparation checks verified pins/composition documents but did not exercise real parent/child preflight/guard ownership; this review gap is recorded in provider FINDING. Closed acceptance history is preserved, not treated as current full-composition readiness.

Install W333485 -> W334910 as actual required input edge at this safe handoff. W333486 already depends on the same provider; no duplicate correction or whole-diagnostics dependency. Provider is at owner disposition for viable correction execution boundary, because old direct exception remains expired. Preserve baton.codx renewal allocation, diagnostics allocation, actual overlap rules and W325959 joined acceptance. No new tests, Job/attempt, source edit or live operation this coordination claim.

## 2026-10-20 — corrected manager checkpoint releases fresh preparation

Reviewer claim337420 read owner close337414 of W334910 and complete provider thread through M337376. Owner accepts candidate-335047, its review-2026-10-19T20-01-02Z.md and integration under M337376, then releases both consumers for fresh exact-source preparation and independent review. Human checkpoint is `fb48797903160aa764229d58f3a5beaf29648bfc`. Independently hashed both committed files: authoring_enforcement.py matches bc8c0363e44fedeae09c15a9065733227f08e279164ed68dc4b0e9e058a7c50f and test_authoring_manager_guard.py matches 085852ceea66efc359c1c27a76e102755ca3c55e367c035cf809c32c4cfa49a0. Provider evidence is baton:work/records/2026/10/finding-v12-authoring-manager-guard/INTEGRATION-337376.md and its newest independent review. The integration record predates human commit; owner close337414 supplies the subsequent checkpoint and disposition. Canonical detail337432 shows both W333735 and W334910 closed satisfying, zero open blockers, and W325959 still dependent on this Work.

This explicitly supersedes the waiting-for-shared-guard milestone, not the withdrawn execution selection. Neither execution-333532 nor execution-334650 may launch. Both temporary implementation exceptions remain expired. Prepare one new sealed packet from the human checkpoint, using the corrected single-manager authoring composition and fresh proposed identities. Reuse accepted deterministic process/guard evidence; verify the new packet actually stages and invokes those exact bytes. Provider integration reports79 focused passes in15.278021919s; no repeat of that unchanged suite is needed for this coordination. No tests, provider, engine, Job or attempt were run by this reviewer claim.

The accepted correction still does not add serving renewal: initial900-second permission can stop authoring before the3600-second provider ceiling. Disclose effective stop/cleanup, retained results and held-only recovery; do not enlarge token bounds or reset invocation limits. Independent preparation review and exact separate execution selection precede actual v12 implementation. The next milestone remains one coupled renewal packet, with no further useful split before its accepted production-composition outcome. baton.codx retains packet/PROGRESS/candidate ownership; reviewer retains FINDING/PLAN/reviews. Sibling diagnostics allocation and actual-overlap serial integration remain unchanged; W325959 owns joined acceptance.

## 2026-10-20T01-54-13Z — corrected-controller packet preparation accepted

Review review-2026-10-20T01-54-13Z.md independently accepts execution-337440 preparation, manifest d3b9bc7ca0eb0f60f0cee5718ca5ca282781abee3ddaeb88f95a00c7f0ddd1fc. All35 seals,306 archive hashes and ten disposable preparation checks pass; exact corrected controller is staged and invoked. This supersedes preparation-in-progress only. Separate exact owner execution selection remains required; no old selection or expired exception revives. OPERATOR carries the concrete proposal and honest900-second initial permission, unknown holds and recovery boundary. No product candidate or actual Job/attempt delivered. W325959 joined acceptance and diagnostics ownership remain unchanged.

## 2026-10-20T02-20-52Z — selected run expired; retained partial continuation

Owner M337501 selected execution337440; reroute337690 requests assessment only after initial lease expiry. Review review-2026-10-20T02-20-52Z.md records exact container absence/token return, independently repeated read-only absence, manager-9 without final snapshot, pending cleanup/reserved allocation and absent workload outcome. This supersedes the unselected-first-execution checkpoint; no recovery/rerun or acceptance follows. Three digest-bound partial files are retained under evidence/review-337693, with timing-interference and eligibility-fence gaps and missing tests. Recommend fresh independently reviewed continuation preparation using unaccepted partial inputs, then separate exact execution selection. Preserve original instance, packets and partial checkout; no direct exception revives.

## 2026-10-20T02-25-56Z — partial-input continuation preparation accepted

Review review-2026-10-20T02-25-56Z.md accepts continuation337717 preparation, manifestaae95b5d7dbdb5607af593056860b249ccb309140180be8331f261f783001789. All43 seals and exact three interrupted-input hashes verify; ten preparation checks and five independent copy/refusal checks pass. Review discloses original negative-fixture helper mode failure and ordinary writable-copy adaptation; no sealed bytes changed. This supersedes continuation-preparation-in-progress only. Partial code remains unaccepted, old run held, no new invocation or recovery selected. Exact separate owner selection must name fresh packet and inherited partial inputs.

## 2026-10-20T02-49-22Z — repeated expiry; owner shutdown checkpoint

Owner M337767 selected continuation337717; reroute337902 limits this turn to assessment and durable checkpoint before server shutdown. Review review-2026-10-20T02-49-22Z.md and RESTART-20261020.md supersede the waiting-for-continuation-selection checkpoint. Second run held954.105s, manager-9/missing final report/no workload outcome, exact container absent/token returned but cleanup pending/allocation reserved. Three partial files preserved and hashed; only renewal.py changed, to8ec602a1c89068f459a60d6ef86e1d3f19badffb2ac9d1031a14f485fe16a1d9. Timing callers unchanged, Job-ending race explicitly remains, no tests. No acceptance or execution continuation. Recommend separately bounded deterministic finalization research before another identical authoring attempt; no new gate/child or exception asserted.

## 2026-10-20 — owner resumes bounded diagnostic preparation

Owner reroute337938 supersedes shutdown-disposition waiting: assessment/preparation only. Claim337943 revalidated all latest original evidence/partial hashes, both exact container absences and all four recorded process absences. Repeated finalization uncertainty now has bounded diagnostic child W337955 at baton:work/records/2026/10/finding-v12-authoring-expiry-finalization, follow-up of closed W334910, suspected-defect classification. This is not a product fix or reopened exception. Install actual W333485 -> W337955 gate before further authoring; diagnostic-only local fixtures, no retained-run mutation.

Feasible next renewal milestone after diagnosis: one coherent scheduling-and-eligibility implementation plus dedicated controlled-clock acceptance, starting from newest three unaccepted inputs. First define admissible timing through all real blocking seams and ownership-consistent serialization for Job/Authority ending before spending another authoring turn. Necessary bounded owner-side edits are allowed by accepted outcome with overlap coordination; partial module assertion that such edits are out of scope is not authority. Require one proof through3600 plus cancellation/end race before expanding regression matrix; this is sequencing, not reduced final acceptance. If this cannot be completed in one initial900-second authoring lease, prepare finite intermediate evidence and explicitly accounted further selection rather than claim a guaranteed fit or enlarge tokens. No new provider invocation selected now.

## 2026-10-20 — accepted shutdown correction releases bounded preparation

Reviewer claim339420 follows owner339385. W338305 closed satisfying339412 after
owner commit bc925cf5c62d69426ed5862af4d41f4d2a967b0f and independent six-path
verification INTEGRATION-339397.json in correction dossier. Diagnostic evidence
gate removed339409 as fulfilled; W337955 owner closure remains owed, preserving
containment. Wake339413 confirms this Work runnable with no open input blocker.
This supersedes waiting for diagnostic assessment. All direct exceptions expired.

Continue preparation through baton.codx, preserving newest unaccepted three-file
partial checkpoint evidence/review-337905/INDEX.json and originals. Produce a new
sealed packet with corrected committed host/controller, baseline and shutdown
helper, exact fresh root/run/image/runtime operands and concise operator commands.
Pin and disclose any proposed partial overlay against the new base before any
future restoration; prior restoration selection applied only to the old run.
No old packet retry, retained-instance recovery or live invocation here.

Do not repeat an identical900-second authoring task: first milestone is real timely
serving composition plus serialized eligibility and controlled-clock3600 and
cancellation/end-race proof. Account explicitly for remaining full matrix if one
invocation cannot finish; no claim of guaranteed fit. Accepted final scope stays
unchanged. Preparation can propose a finer bounded split if independently useful;
shared timing/fence behavior must have integrated acceptance. Diagnostics W333486
is preferred for the immediate next useful run and independently prepares through
baton.impl; no new dependency on diagnostics or serial preparation queue.

Retain900 initial permission/four renewals,3600 provider/30 verifier,4800 total/60
cleanup, one invocation/no retry, unknown holds and truthful final-output collection.
Reuse accepted shutdown proof; preparation proves staged exact bytes/composition,
not new product verification. Require final controller/workload result and exact
cessation/partial-output observations from any later selected actual v12 run.
W325959 remains joined consumer. Existing author owns packet/PROGRESS/candidate;
reviewer FINDING/PLAN/reviews; actual overlapping candidates integrate serially.

## 2026-10-20T14-39-37Z — corrected-base continuation preparation accepted

review-2026-10-20T14-39-37Z.md accepts continuation-339444 manifest
0f8eba8caa8eca82639f83b184c90dbafd7a19757be7fe6336c5494ce4329adb.
55 seals,312 archive hashes,10 preparation and5 copy/refusal checks independently
pass; evidence/review-339484, measured3.438703986s. This supersedes preparation-
in-progress only. Product acceptance and exact separate new run/restoration
selection remain owed; old packets and exceptions stay expired/unselected.

## 2026-10-21 — owner selects continuation339444; executor preflight holds

Recorded by baton.codxpc under claim345627. Canonical owner reroute345625 selects
exactly one enforced invocation serving-renewal-w333485-339444 at
/home/sl/baton-instances/serving-renewal-w333485-339444, using accepted
continuation-339444 manifest0f8eba8caa8eca82639f83b184c90dbafd7a19757be7fe6336c5494ce4329adb,
and explicitly selects restoration of its three digest-bound unaccepted buffers.
The owner requires executor-boundary preflight, OPERATOR.md through
 authoring_enforcement, unchanged limits/one invocation/no retry, first timely
renewal and serialized cancellation/end proof, then remaining acceptance. Preserve
independent diagnostics inputs and serial overlapping integration. No deployment
or old-instance recovery is selected.

This supersedes the pending-owner-selection state in the preceding acceptance
entry and PLAN only for this exact invocation/restoration. It does not revive a
direct implementation exception or grant arbitrary alternative execution paths.

Preflight evidence: evidence/executor-preflight-345627/RESULT.json. All55 seals
and the manifest match; the reviewed read-only verify-inputs.py passes committed
source,119 host files,8 task inputs and historical bootstrap pins. The selected
root is absent. Its parent is uid/gid1000, mode0775, but os.access(W_OK) is false
under this executor; supplied writable roots are only /home/sl/src/baton and /tmp.
The first required mutation is prepare.py:stage root.mkdir for that exact root.
It is unavailable under the installed execution boundary. No staging command was
attempted, so this is a preflight capability finding, not a caught stage failure.
No root, bootstrap store, restored candidate, Job, attempt or provider invocation
was created. No credential contents, old stores or runtime were inspected/changed.

Required operational continuation: provide this participant an approved executor
with write capability for the exact selected root and the remaining reviewed
OPERATOR operations; recheck pins/root absence and proceed from stage. The owner
selection itself is already present and the one invocation remains unconsumed.
Do not change the sealed root, use /tmp as a substitute, bypass confinement, run
implementation directly, or treat this preflight as permission for another run.
Return through baton.bug to coordinate the concrete executor correction. Product
implementation/full acceptance and W325959 joined acceptance remain outstanding.

## 2026-10-21 — owner lease-policy correction: remove arbitrary authoring truncation

Owner: "15 min lease is arbitrary and if if stops real work needs to be modified asap". Recorded by baton.prompt as an explicit policy correction. Observed evidence already satisfies that condition: retained renewal runs337440/337717 and diagnostic runs341360/340352 reached the initial900-second permission boundary before completion, despite larger selected provider/outer limits. tokens.py declares LIFETIME_SECONDS=900 and RENEWAL_LIMIT=4 as implementation-profile choices, not normative constants. Implementing a renewal API without a production caller has not provided the longer execution budget.

This ruling explicitly supersedes the policy-boundary paragraph's instruction to retain900/four-renewal bounds and later equivalent no-increase restrictions for the prospective bounded correction. DESIGN TOK-9 now records the approved behavior: permission must support selected execution limits through actual timely eligible renewal or an appropriately bounded initial duration; it must not impose an accidental15-minute total-work ceiling. Select the smallest correct mechanism rather than a broad scheduler refactor or another identical truncated run. No arbitrary replacement number is selected here: derive and pin the policy from the Job's existing execution/cleanup envelope, with inspectable effective deadlines.

Preserve cancellation, exact-runtime expiry enforcement, no revival after expiry, identity/replay/restart fencing, unknown holds, exclusive ownership and the selected Job deadline/cleanup reserve. Existing tokens and sealed packets retain their recorded semantics; no live token mutation, hot patch, reset, consumed-invocation retry, host product-execution exception or new deployment is implied. Any prospective changed packet must accurately carry the reviewed effective policy. The policy decision itself needs no repeat owner approval; concrete live/deployment selections retain their existing boundaries.

Urgent coordinated outcome for the configured reviewer/implementer: stop the demonstrated artificial truncation, prove the chosen longer authorized execution and cancellation/expiry/exhaustion behavior with deterministic clocks, return exact reviewed correction. Current pass345648 separately reports executor write-boundary refusal before selected root creation; invocation345625 is unconsumed. Resolve that exact operational capability in parallel where ownership permits, without treating it as permission to bypass confinement. Current diagnostics runtime must finish under its recorded selection; report its actual ending and preserve output. Installation work must account for the corrected policy before advertising longer routine Job support.

## 2026-10-21 — review345717: independent access and policy preparation

Confirmed pass345648 stopped before stage; owner345625 invocation remains unconsumed. Read events339504–345717 and discussion through345677. Existing55-seal/pin evidence is reused, not rerun. Actual boundary denies root.mkdir at the selected absent /home/sl/baton-instances/serving-renewal-w333485-339444. No alternate root/privilege workaround.

DESIGN TOK-9 and owner345677 supersede the old TASK prohibition on token-duration changes and the PLAN keep900/four-renewal paragraph. Preserve continuation-339444 immutable. It is not sufficient to launch that obsolete task unchanged. Prepare only a minimal successor task/spec binding; reuse unchanged sources, restoration buffers, runtime/image and reviewed checks. A changed exact manifest must be reconciled with the existing owner selection before launch; product scope needs no repeat ruling. No live token or active diagnostics semantics change.

Finite decomposition: operational child owns exact baton.codxpc capability correction/preflight for selected root and OPERATOR operations; separate preparation child through baton.codx owns only a minimal unlaunched amendment for the prospective bounded lease-policy correction. Those outcomes can be prepared independently and touch disjoint paths. Parent W333485 joins both before any implementation launch and remains W325959's acceptance provider. Parent dependency edges will be installed/read back before release. No active implementer allocation is displaced: claim345627 was released at345648.

Recommended first working correction is the smallest existing host acquisition policy that derives and records bounded initial permission from the populated Job execution/cleanup envelope, if that avoids introducing the unresolved renewal/cancellation race. Evidence: worker_manager/workspaces.py PreparedGovernance.reserve calls tokens.acquire without seconds; tokens.acquire already accepts explicit seconds, default900. This is a proposal, not authority to replace a constant globally or skip needed serving/restart behavior. Implementer chooses the minimal correct mechanism; actual timely eligible renewal remains an alternative. Prove selected3600 allowance, no Job-limit reset, cleanup reserve, cancellation/expiry/no revival, exact identity/replay/restart/unknown holds with deterministic clocks, starting with one integrated reproduction. No unnecessary broad scheduler redesign. Preserve retained renewal partials as unaccepted evidence, not mandatory implementation.

Ownership: reviewer parent FINDING/PLAN/new review and child FINDING/PLAN; ops child its own operational evidence only, never product/source/sealed inputs; codx preparation child its own amendment/PROGRESS only, never runtime policy or product implementation on the host. Actual source/test changes remain isolated v12 execution after joined readiness and exact binding resolution. W341357 remains undisturbed; actual overlapping candidate paths integrate serially.

Canonical graph readback snapshot345747: dependency345746 on W345730 and345747 on W345732 present; parent phase block, handler null, two open blockers. First block atomically released reviewer claim345717; no redundant pass attempted. W345730 ready at baton.ops (Slawomir), W345732 already claimed by baton.codxpc at345734. Parent remains baton.bug for joined independent acceptance.

## 2026-10-21T11-34-34Z — W345732 amendment accepted; parent launch remains unready

Child review345774 accepts amendment345734 manifest8a46facba604ad3c5e2c1c1b7d76eaf91b84ea1e2aad5e904f296c301a7c7394 as minimal task/spec preparation. Exact child review/evidence retained. Access W345730 remains separate. Changed manifest and conditional-restoration delta need exact selection reconciliation; unchanged host900s permission remains an explicit effective-execution limitation, not fixed by preparation. Preserve graph gates and old bytes; no live invocation.

## 2026-10-21T16-13-50Z — operator prerequisite accepted; joined bootstrap boundary

review-2026-10-21T16-13-50Z.md; claim347720. Child W345730 closed satisfying347718 for owner-selected operator alternative (not restored managed access); W345732 already satisfying. This supersedes pending access/join state. OPERATOR-347720.md and prepare-operator-347720.py provide one preparation helper, not executed. Existing900s host cannot satisfy later lease-before-launch condition merely through amended worker task. Unconsumed345625 is preserved, not a waiver of that condition. A concrete bounded bootstrap implementation/verification exception is proposed for owner disposition; no authority inferred. W341357 and W325959 remain consumers.

## 2026-10-21T16-17-50Z — owner347746 approves bounded host bootstrap exception

OWNER-BOOTSTRAP-347746.md pins the full canonical owner ruling before implementation. It explicitly supersedes pending-exception state and the sealed task no-host rule only for isolated host implementation plus focused deterministic author/independent review of the prospective envelope-derived permission correction. No live provider/engine, deployment/install, existing-token or Git mutation. Expires at independent acceptance. Claim347763 revalidates DESIGN TOK-9 and acquisition seam; configured baton.codx receives routine execution without another approval round. No product changes or tests by reviewer this turn.

## 2026-10-21T16-42-26Z — bootstrap policy independently accepted; exception expired

review-2026-10-21T16-42-26Z.md accepts exact seven-path manifest89cf5d90e86e0505ce13d71dfe2bf2f7d0d9d323c82d3e6ec0cd2879f81db2f8 at based3a7a41c. Independent171+37+46 tests pass, no skips, reviewer4.704084767s; main paths unchanged. Explicitly supersedes pending bootstrap implementation/acceptance state. OWNER-BOOTSTRAP-347746.md expires at this acceptance. Selected authoring fixed-envelope policy is accepted, not a native-wide rollout or live proof. Next minimal immutable consumer host binding only; no stage/bootstrap/live start or obsolete task rerun. Old sealed packets remain900 and cannot be advertised as corrected until new accepted binding. W341357/W325959 remain consumers.

## 2026-10-21T16-49-32Z — consumable supplier binding accepted

review-2026-10-21T16-49-32Z.md accepts host-policy-347952 manifesteb57aa9c3ba74886e2d9856cfe3382ceab6a2bdb1799283512a4943dfeb62d52/archive1693bdd0808b051cb575c11a5f4c290a79d64119a04e34075005beaee41debbd.114 files exactly match independently tested source;108 unchanged/six accounted deltas from consumer. Supersedes pending binding-delivery state. W333485 bounded supplier result complete and passed owner for satisfying disposition; no obsolete renewal-authoring run or repeat policy gate. Consumer W341357 owns successor preparation/selection after graph release, W325959 joined adoption. No deployment/live proof or main-tree integration inferred.
