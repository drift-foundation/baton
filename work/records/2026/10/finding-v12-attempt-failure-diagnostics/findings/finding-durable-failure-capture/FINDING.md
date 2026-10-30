# Durable typed failure capture and replay

2026-10-20, reviewer baton.rvpc claim341344, decomposition of W333486 within its accepted diagnostic scope. Parent owns joined ordinary status/report, installed-bundle and full acceptance. This child owns an independently reviewable producer contract before downstream composition.

Observed: run340352 hit its900-second lease, returned no frozen candidate and never ran its verification gate. Partial tracked.diff plus four new files survive in parent evidence/run-340352/retained-partial/. They are unverified input, not a proposal or accepted patch. Parent evidence/review-341344/evidence.json verifies14 copies and6 source pairs. Preserve originals and derive a separately pinned recovery input in preparation; verify tracked diff base and new-file hashes before isolated application. Do not mutate or resume the old instance.

Bounded outcome: durable pre-effect cessation intent and separately typed outcome at reclaim, settlement and cancellation boundaries; exact attempt/assignment/start/domain/generation/token-bound runtime/operation attribution; reader distinguishes unknown, typed failure, intent-only and positively observed cessation. Replay preserves historical evidence and later observations without making an old uncertainty permanent or converting collision into authority for different effects. Both release paths and existing fencing/cleanup behavior remain required.

Concrete static concern in retained failure_cause.py:ensure_cessation_intent (lines403-442): an operation-collision is treated as proof an intent exists and permits effects, without proving that old intent describes the current facts. A different runtime/correlation signature is not durable authorization for the new effect. Reject or resolve that mismatch explicitly; exact replay and changed-signature collision need distinct acceptance evidence. This is a static finding, not an executed reproduction. Revalidate the partial implementation rather than assuming the handoff assertion that item C was not reached; this function and outcome revision chain show C was attempted.

First slice acceptance: isolated deterministic production-boundary tests establish intent ordering under recording failure and crash; exact replay vs conflicting runtime/operation; token-bound-before-attachment; stop failure vs unknown cessation; absent vs quiescent; uncertain-to-positive observation history; reclaim/settlement release attribution; secret-safe bounded fields and honest old-record unknown. Deliver versioned producer shape/read API, exact base/path/digest candidate and actual v12 Job/attempt/evidence. Keep tests focused to this slice; parent retains full joined gate and historical failure classification.

Ownership: configured baton.impl owns isolated child preparation/candidate/PROGRESS. Primary producer paths are worker_manager/failure_cause.py, documents.py, intake.py, attempts.py and focused producer tests. These identify allocation, not an exclusive edit restriction; coordinate any additional shared contract path before parallel edits. Parent status/report work is serially blocked until child acceptance, so no concurrent edit owner. The retained whole partial snapshot is preserved; select only necessary producer changes for this child and leave downstream partial changes available to parent. No product source edits in host tree.

Authority: reviewer decomposition ruling permits this finite split without new scope approval. Owner341187 selected the completed one invocation only; no next start, lease extension, host product-test fallback, deployment or Git mutation selected. Prepare exact isolated v12 operands, then independent preparation review and applicable execution selection. A routine correction is not an owner scope gate. No extra live provider solely for deterministic verification.

## 2026-10-20T19:26:13Z — producer preparation independently accepted

Review341441 accepts execution341360 preparation manifest0c4730e7e8757dd873517c7744577b949702d55d066dd44a7984064e708b0fa5; review-2026-10-20T19-26-13Z.md.43 seals,52 probes, input verification and33 composed fixture hashes pass. Three producer diff sections and two new files match preserved parent bytes (global file-section order differs, no hunk changes). Recovery remains unverified input. Supersede preparation-in-progress state only; product acceptance and new execution selection remain outstanding. Parent dependency341370 remains.

## 2026-10-20T19:50:05Z — second lease interruption; verify and return first

Review341624 verifies14 copies and6 source pairs from run341360; review-2026-10-20T19-50-05Z.md. No frozen candidate and verification not-run; source/test growth is not acceptance. Owner341467 invocation consumed. Correct campaign narrative: parent340016 did retain a failed-verification candidate; zero candidates are accepted, not zero retained. Preserve immutable evidence.

Current milestone supersedes open-ended producer authoring: fresh isolated continuation from latest preserved bytes, focused gate first, only evidence-driven fixes, then supported provider completion with planned600s editing cutoff/720s return target under unchanged900s lease. Pin actual supported completion instructions into worker task, not only outer PROGRESS. This is task planning, not a controller/lease change or new execution selection. Parent remains blocked on actual child acceptance.

## 2026-10-20T20:00:52Z — verification-first preparation accepted

Review341697 accepts execution341637 manifest1f191e7b2f0f0ac033550a3fb235ec48624171d714c0cfb02e47124dcea3e3df; review-2026-10-20T20-00-52Z.md.48 seals,55 probes, input verification and38 composed fixture hashes pass. Worker-visible COMPLETION/TASK pin verification-first and600/720 planning targets under unchanged lease. Provider return enables but does not guarantee freezing/publication; actual external evidence remains acceptance. Supersede continuation-preparation-in-progress only. No new run selected; parent remains blocked.

## 2026-10-20T21-46-50Z — selected run failed provider authentication

Review342415 (review-2026-10-20T21-46-50Z.md) verifies10 evidence hashes,6 source pairs, custody diagnostics/empty patch and unchanged48-member seal. The attempt reports supported authentication_failed; no verification or product acceptance. Owner342358 selection consumed. This supersedes the prior no-run-selected state: execution341637 has now run and its root must be preserved. Structural preflight does not establish session validity. Operational credential repair and a separately selected continuation are outstanding; fresh identity/root binding is necessary unless a supported recovery path is explicitly selected. Accepted producer/task/recovery scope is unchanged; parent341370 dependency remains.

## 2026-10-21 — owner reports provider access restored

Slawomir reports in the interactive prompt: "I logged into claude and providers-check (just) finished ok". Recorded by baton.prompt as owner-reported operational evidence; no credential contents inspected and no independent provider check repeated. This supersedes the outstanding credential-repair prerequisite above, not the historical failed attempt or its consumed selection.

Continue the existing bounded preparation milestone: retain reviewed execution341637 task/recovery bytes and limits, prepare only necessary fresh run identity/root bindings and resultant seals, and preserve the failed instance. Return for independent preparation review and applicable exact invocation selection. This report does not select a new live invocation or establish producer acceptance. Current canonical read before coordination: snapshot345035, unclaimed queued baton.decide, episode342420; latest review remains review-2026-10-20T21-46-50Z.md.

## 2026-10-21T10-13-48Z — fresh identity preparation accepted

review-2026-10-21T10-13-48Z.md accepts execution345039 manifest5db5b9bad674f4b9ae3e6141c54d9551ade6644f9c2ebe52694c773db2857e6b.51 new seal lines, complete52-file inventory,48 previous seal lines,41 composed fixture hashes and unchanged gate verified. Input check passes0.118200679s. Supersedes fresh-binding preparation-pending state only; no new execution selected and no product acceptance. Required exact invocation selection remains with owner; preserve consumed341637 and parent dependency341370.

## 2026-10-21T10-42-55Z — retained candidate, failed gate and concrete fixture-path diagnosis

review-2026-10-21T10-42-55Z.md verifies run345039 evidence and candidate1599471c21d9427e83883a6346d9e846295c3f222296c320b68933f178b0b096. Owner345206 invocation consumed; completed gate864 tests12.817s fails9/errors7, all test_maintenance. This supersedes no-execution-selected/current-preparation-only state. Static unchanged-base fixture paths retain /proc/self/fd aliases while product composition requires canonical paths; two subprocess empty-output errors plausibly share descriptor-path cause and need dynamic confirmation. No gate exclusion or claim of a passing base. Next bounded correction is same-environment fixture compatibility and full unchanged-module gate, prepared through baton.impl with retained candidate provenance before applicable exact execution selection. No producer acceptance or parent unblock.

## 2026-10-21T11-01-38Z — fixture-correction preparation independently accepted

review-2026-10-21T11-01-38Z.md accepts execution345388 manifestb895cc72c8458c7988a6c9182ab964ba5450a31dcc39c1af79eb48e3dc8b204d as preparation only.57 seals/full58 files, exact retained candidate patch,45 composed fixture hashes and unchanged full verification argv verified; targeted downstream run-evidence mismatch refusals pass. Supersedes correction-preparation-pending state only. Exact one-invocation selection remains outstanding, owner345206 consumed, producer candidate unaccepted and parent341370 blocked.


### Post-review coordination — message 345516

After review345501 and pass345519, read T341357 through345516. Prompt reports owner M345512 selected integration of W339626 candidate345109, with prompt owning its bounded 17-path main-tree import. Overlap with this work is `v12/python/src/baton_v12/worker_manager/attempts.py` and shared input `tools/authoring_enforcement.py`. Preserve W341357 retained candidate, sealed continuation inputs and pinned base unchanged; report later integration overlap explicitly rather than silently rebasing or weakening pins. This notice selects neither a W341357 main-tree import nor a new invocation. Preparation acceptance remains limited to the sealed packet; executor-boundary preflight must evaluate current inputs before any selected execution.

## 2026-10-21T11-37-58Z — second candidate fails storage gate; classification corrected

Review345793 (review-2026-10-21T11-37-58Z.md, evidence/review-345793.json) verifies14 evidence copies/13 source pairs and gate864/12.515s/16 subtest errors in4 methods. Candidate5a7d5976/content5c0fca78 remains unaccepted; producer/test patch sections unchanged. disk_roots existed at base; only canonical spelling changed. This explicitly supersedes pass345775 claims of a newly introduced helper, count-alone coverage proof and proven new-disk-root causation. Repeated setup/deferred fixture cleanup is confirmed statically, exhausted filesystem remains unmeasured. Next minimal continuation measures those4 methods and fixes demonstrated fixture lifetime/storage with preserved assertions/full gate and durable nonsecret report. No owner scope choice required for routine fixture correction; exact fresh invocation still requires selection because345560 consumed. No host test or live run.

## 2026-10-21T11-53-41Z — continuation preparation accepted, no execution selected

Claim345911 accepts execution-345822 manifest6d4e875e3991aa084062985fb258ef60fa021123cd9b03ced6db20c4e71c3e87 for exact owner invocation selection. See review-2026-10-21T11-53-41Z.md and evidence/review-345911.json. All61 seals and unchanged composed gate verified. Explicitly supersedes residual prose claiming every prior assertion passed: no-failures is not proof of reached assertions; actual storage cause stays unmeasured. Final candidate head is externally correlated if unavailable before worker return. No product acceptance or live start.

## 2026-10-21T15-30-10Z — passing fixture gate; producer acceptance withheld

review-2026-10-21T15-30-10Z.md verifies16 copies/15 source pairs and sealed864-test12.631s OK. This supersedes failed-gate current status only. Candidatee9d292ed/content59d666d9 remains unaccepted: fresh A->B->A settlement observations are value-deduplicated as old replay,falsely retaining B as current; multiple acting paths discard returned outcome-recording degradation. These are static confirmed code paths,not host-executed tests. Correct both as one producer milestone; preserve fixture/report evidence and original historical observations. Disk-full345388 cause remains unknown; no resource change selected. Owner347178 consumed; parent341370 stays blocked.

## 2026-10-21T15-43-57Z — R1/R2 continuation preparation accepted

review-2026-10-21T15-43-57Z.md and evidence/review-347497.json accept execution-347396 manifest7df8bcbc5ac4d8549bc15501b07d27f53b9127e28a614953ed199ba559dd2ed3 as preparation only.67 seals/full69 files,unchanged programs/gate and56 generated fixture inputs verified; read-only input check0.122s. R1/R2 fixes remain owed,product unaccepted,parent blocked. Fresh exact selection outstanding,347178 consumed. Keep FIXTURE filename; no machinery churn needed.

## 2026-10-21T15-52-04Z — owner347548 makes supported execution permission a prerequisite

review-2026-10-21T15-52-04Z.md records claim347551. Explicitly supersedes immediate invocation-selection readiness and independence from W333485: accepted preparation347497 remains preserved, but effective900s cannot support requested3600s by relying on prior completion or planning targets. Current PreparedGovernance.reserve omits seconds; token acquisition defaults900. Existing W333485 owns the approved production correction; W345732 amendment alone changes no host permission. Record actual dependency on W333485, preserve sealed inputs, then join independently accepted policy through a minimal immutable successor binding before exact owner selection. R1/R2 and parent acceptance unchanged. No executable invocation, live-token mutation or host implementation authorized or performed.

## 2026-10-21T18-36-26Z — accepted supplier releases successor preparation

Owner348699 closed W333485 satisfying. review-2026-10-21T18-36-26Z.md records claim348704 and exact accepted host binding; read-only114-member verification passed0.128282538s. Explicitly supersedes the waiting-on-W333485 current state. Prepare the minimal successor through baton.impl with separate host/worker provenance,actual executor capability and effective envelope derivation; no live invocation selected. R1/R2/product nonacceptance and parent341370 gate remain unchanged.

## 2026-10-21T18-48-05Z — successor source accepted, current instruction contradictions remain

review-2026-10-21T18-48-05Z.md records claim348787: all71 seals/70 payload hashes/full72-file inventory and read-only input verification pass. Host archive consumption is correct; COMMANDS,OPERATOR,PACKET and PROVENANCE still present old900/600/720 instructions and controller identity as current. This supersedes preparation-ready assertions in pass348784,not the supplier acceptance. Correct the bounded current-document/provenance inconsistency and reseal a successor; reuse unchanged code/preparation evidence. No live selection or product acceptance.

## 2026-10-21T18-54-41Z — partial document correction verified, remaining contradictions enumerated

review-2026-10-21T18-54-41Z.md records claim348838. All72 seals/71 payload hashes/full73-file inventory and read-only input check pass0.065750245s. Current machine-readable permission and controller fixed. PACKET still carries720 cutoff and mixed old/new composition evidence; OPERATOR still excludes owed producer work. Pass348836 assertion of complete correction is superseded by these exact observations. Finish the same bounded correction; no product or live execution selected.

## 2026-10-21T19-00-34Z — coherent executable preparation accepted

review-2026-10-21T19-00-34Z.md accepts execution-348852 manifest3bf3d7df222fd91b79527ea37f8e656ccbcc6fa507dae0f72bd878f54d043a5f. All73 seals/full74 files,114 staged runtime members,61 fixtures and8 generated artifacts independently verify; input check0.067757113s. Explicitly supersedes documentation-correction-pending state. Current task/operator permission and provenance agree; inherited PREFLIGHT narrative fields are qualified as historical by the review,not current proof. Exact invocation selection remains outstanding; no product acceptance,live start or parent unblock.

## 2026-10-21T19-12-38Z — consumed invocation exposes incomplete supplier artifact

review-2026-10-21T19-12-38Z.md verifies five run348852 evidence hashes and missing deferred import tools.authoring_baseline. Owner348925 consumed before any Job; producer unchanged. Explicitly supersedes complete-runtime/start-readiness acceptance of114-member archive,not individual byte or envelope-code proofs. Reviewer acknowledges artifact-closure review gap. New prerequisite W348979 owns corrected immutable packaging and dependency proof; W341357 waits,then owns successor preparation/selection and R1/R2 acceptance. Preserve failed root and closed supplier history.

## 2026-10-21T23-00-29Z — packaging prerequisite closed; resume consumer preparation

Owner350489 accepted W348979 and released full115-member successor preparation. review-2026-10-21T23-00-29Z.md records claim350495 and unchanged accepted binding/archive hashes. Explicitly supersedes waiting-on-W348979 checkpoint. Route minimal consumer preparation to baton.impl; preserve failed348852/consumed348925 and worker recovery. No new run selected; R1/R2 and parent341370 remain.

## 2026-10-21T23-28-31Z — corrected runtime consumer preparation accepted

review-2026-10-21T23-28-31Z.md accepts execution-350529 manifest6be3fb90a1037c992e7e22510363953c51c99133a2a87572e5066aa3980bc6ff.78 seals/full79 files,115 staged members,66 fixtures and8 generated artifact hashes verified; input check0.068206638s. Explicitly supersedes consumer-preparation-pending state. Deferred dependency included; generated permission text corrected. No dynamic startup claimed or new run selected; R1/R2 and parent341370 remain.

## 2026-10-22T14-45-31Z — corrected supervisor path independently accepted as preparation

review-2026-10-22T14-45-31Z.md records claim352340. Explicitly supersedes execution350529 selection-ready state: owner352153 was consumed by startup path-identity refusal before any Job. Accept execution352156 manifest9bda87e4ad655da1c1a452b901f994c5da7b4647d1a64c02ab2287866086dc2e as preparation only. Independent regenerated115-member/68-fixture composition and three startup verifiers pass; durable evidence/review-352340 replaces reliance on missing temporary author preflight. No dynamic controller start or product acceptance claimed. Exact invocation selection outstanding; R1/R2 and parent341370 unchanged.

## 2026-10-22T15:17Z — OWNER352577 SELECTED EXACTLY ONE INVOCATION OF execution-352156

Pinned by implementer baton.claude, claim352586, **before execution**, because
reroute352577 requires this selection to be pinned in FINDING and PLAN first.
This section records the owner's selection; it does not alter accepted scope,
and the reviewer retains ownership of every other part of this document.

Selected operands, exactly as reroute352577 names them:

| operand | value |
| --- | --- |
| packet | `execution-352156`, manifest `9bda87e4ad655da1c1a452b901f994c5da7b4647d1a64c02ab2287866086dc2e` |
| acceptance | `review-2026-10-22T14-45-31Z.md` (reviewer claim352340) |
| run id | `durable-capture-w341357-352156` |
| root | `/home/sl/baton-instances/durable-capture-w341357-352156` — fresh, revalidated absent |
| invocation | **one**, no retry, `report-and-hold` |
| bounds | provider 3600s, verification 30s, total 4800s, cleanup 60s |
| permission | execution stop at original origin + 4740s, expiry at origin + 4800s |
| procedure | revalidate seals and root absence, pre-stage capability, post-bind actual-boundary preflight, then `COMMANDS.md` and the **generated enforced** `AUTHORING-COMMAND.json` only |
| preservation | all prior roots preserved; no rerun, recovery or re-bind |
| not authorized | integration, product acceptance |

Revalidated before any action this claim: manifest `9bda87e4…` byte-identical
to the selected value; seal 80 of 80 with zero failures and **both ways** — 81
files on disk, no extras, nothing sealed-but-missing; input check exit 0 in
0.067s with 115 manager files, 68 task inputs, 59 decision snapshots, 2 pinned
recovery inputs and 1 gate module still owed; proposed root absent. The input
check reports `DECISION-SOURCE DRIFT` on this `FINDING.md` and on `PLAN.md`
because the reviewer updated both after sealing — **reported and deliberately
not resealed**, since resealing would change the manifest the owner selected.
The pin written above adds a second, intentional source of that same reported
drift for the same reason.

Pre-stage executor capability: **capable, zero denials**, 0.081s, bound to that
manifest — engine answers, image `baton-v12-claude-worker:w239528-244216`
config digest `sha256:c862c055…` equal to the pin, runtime binary `04aa459a…`
equal to the pin, credential reference `w202663-development` present in the
registry with its backing file present and **no credential value read**. The
author's claim352156 copy of this check lived under `/tmp` and is absent after
the announced wipe (T341357 message352206), so this is a **regenerated** check
against the same packet pins, not recovered historical bytes.

What this selection does not establish: that the controller starts, that the
provider session is valid, that a Job is admitted or that a turn completes.
Three selected invocations in a row failed at startup; the last two are closed
windows and neither closure is a prediction. R1, R2, the complete five-module
gate with no skips, the extended `W341357-VERIFICATION.json` and independent
producer review remain owed, and parent W333486 stays blocked by341370.

## 2026-10-22T16:23:29Z — Owner priority: native v12 cutover and proportionate review

Slawomir directs the current review and subsequent approval recommendations to prioritize native v12 coordination and execution, ending the temporary v11-to-v12 orchestration. Do not spend another hour-long run on minor issues. Distinguish concrete correctness, isolation, recovery, attribution or false-success blockers required for the selected cutover from polish and broader hardening that can be recorded for v13. This clarifies delivery priority; it does not waive independent acceptance, alter the specification, approve a new run or silently change dependencies.

Before recommending another execution selection, identify the exact essential acceptance gap, why retained evidence or focused deterministic verification cannot resolve it, and the smallest bounded correction/proof with an honest cost estimate. Reuse retained candidate 2d313602 and applicable evidence rather than restart completed work. Report nonblocking follow-ups separately. No legacy bridge implementation is selected; the owner's maximum-60-second polling preference remains a temporary operational convention.

Recorded by baton.prompt from the interactive owner instruction. Current reviewer owns PLAN and review disposition; incorporate this priority in that checkpoint and carry it into the parent/native-cutover handoff. Prompt appended only this ruling and did not change the active review, implementation or graph.

## 2026-10-22T16-25-04Z — completed run; replay attribution correction remains

review-2026-10-22T16-25-04Z.md records claim353042 and candidate2d313602/contentc509bd42. Explicitly supersedes invocation-selection-pending: owner352577 consumed by completed run352156. Evidence copies and custody bytes verify; no producer acceptance. Fresh A-B-A is retained, but subsequent exact old-A replay returns current equal-value revision because failure_cause.py626 checks value before observation coordinate. Correct that same bounded producer milestone, preserve R2/fixture work, and complete the current-turn report without inventing historical observations. Parent341370 remains unsatisfied.

## Owner priority applied — M353069, poke353070 (2026-10-22)

Read owner FINDING ruling2026-10-22T16:23:29Z and M353069 after pass353080. Canonical353083 shows child unclaimed on baton.impl; reviewer does not reclaim or alter that allocation. Native v12 cutover is the delivery priority. Existing review is narrowed as follows; no acceptance or graph change is implied.

The remaining replay finding is a bounded exact-attribution contract defect: explicit replay returns another observation's identity/document. It does NOT append rows, change the current reader tip, order effects or release resources. Retained evidence proves the broader fresh-observation and R2 work; reuse it. Preserve the small exact-replay correction as the remaining producer acceptance item, without describing it as a newly demonstrated isolation or false-success incident. No new generalized replay framework or broad hardening is selected.

The missing current-turn report subsection is nonblocking historical-report clarification: record actual unknowns and external evidence separately in the dossier. Supersedes any implication in review16-25-04 that this omission alone requires another candidate/live run. Broader194 failures, storage-pressure research and prose polish do not gate this bounded correction and are not selected for repair here.

No further live-provider verification is justified by the replay gap. Deterministic verification can resolve it: an exact A0-B1-A2 then replay-A0 case (and middle revision), unchanged history/tip, retained same-value dedup, then the existing five-module gate on corrected bytes. Historical focused module about0.389s/full gate11.152s suggests seconds of test execution, with the existing30s per-command ceiling; this is an estimate, not a measured new result. A local recorder correction/review should be minutes rather than another hour-long run; provider authoring duration is unknown and must not be sold as measured. Reuse candidate2d313602 and proven runtime/preparation. Do not rerun completed engine/authentication/envelope proofs or broad modules.

Execution still follows the v12 boundary. Before proposing ANY new invocation, implementer must show the smallest supported isolated correction/proof route, distinguish authoring from tests, and explain any real-provider need that deterministic coverage cannot answer. No real-provider behavior is currently at issue; a live test is not recommended. If existing tooling cannot run the focused proof without expensive authoring, record that exact operation gap and return for proportional owner selection rather than automatically proposing3600/4800 again. No host-test fallback, retry or new execution authorized.

Carry this classification into parent W333486 and native-cutover consumer W325959: parent remains the joined status/report and bundle acceptance owner; producer exact attribution remains an explicit gate until resolved or owner-approved scope decision. Do not silently close/remove341370. Reviewer retains record ownership; implementer preparation/PROGRESS remains exclusive.

## 2026-10-22 — owner selects isolated-host replay correction

Following the explanation of the A0-B1-A2 replay identity defect and the proposed bounded direct-host exception, Slawomir directs: "let's stop-drain and assign to fix". Authorize the configured implementer to correct this exact defect from retained candidate 2d313602 in an isolated host directory, run focused deterministic replay regressions and the existing five-module gate, and return the exact candidate for independent review. Authorize the reviewer to perform the corresponding focused deterministic host verification. Reflect this ruling in the current PLAN before execution.

This prospective exception supersedes the preceding no-host-execution boundary only for this correction and its independent verification, and expires at independent acceptance. Preserve original/middle replay identity, unchanged tip/history, fresh A-B-A/B-A-B, same-value dedup, R2 and fixture coverage. No new v12 Job, live provider/engine verification, broad-module campaign, shared-tree integration, deployment, historical-run retry or Git mutation is selected. Preserve the retained candidate and evidence; extract/copy exact input bytes without mutating shared Git. Minor report clarification remains nonblocking. Current W339626 ownership is not interrupted; W341357 is already queued on baton.impl. Dispatch resumption is a separate operator command; this ruling does not claim it has happened.

## 2026-10-22 — M353196 direct workflow applied to reviewer checkpoint

Read canonical W341357 snapshot353202: active baton.codxpc on baton.codx; preserve claim353177 and its isolated candidate ownership. Read AGENTS Temporary direct development workflow and W321608 FINDING/PLAN/M353196. Routine correction and focused deterministic independent verification now run directly under existing v11 claims. No v12 Job, new launch packet, per-correction host exception or separate routine execution selection is needed. This explicitly supersedes this PLAN's older no-host/preparation-only/mandatory isolated-v12-invocation instructions; previous evidence and live-operation exclusions remain historical facts.

At the present safe boundary continue the already-owned minimal replay correction from retained2d313602 in codxpc's isolated candidate. Its current correction/provenance and test scope remain unchanged: original and middle replay identity, unchanged reader/history, fresh A-B-A and same-value dedup, preserved R2/fixtures, focused module then five-module no-skip gate. Independent reviewer receives exact frozen bytes and may run focused deterministic host verification under a successful review claim. Do not duplicate the active executor or edit its candidate/PROGRESS. The prior bounded exception remains historical authority but is no longer a prerequisite under the standing workflow.

Native v12 delivery remains the priority. Historical report clarification is nonblocking; no additional live run, engine/provider exercise, deployment, installation, migration or file-journal cutoff selected. Existing graph341370 and independent acceptance/Git/serial-overlap rules remain. Current child/parent timing estimates and retained evidence are reused; no broad repeat verification.


## 2026-10-22T17-27-09Z — producer candidate independently accepted

review-2026-10-22T17-27-09Z.md accepts correction353177 manifest0143f146b8f7562ef60f22c4f0984670301f338e2687af806ebff6df2e08b807/full patchecb9e391455a5f6626bf2ffb07f0d85a237ae909dc3b7012a1b326a393f3d6f8. Explicitly supersedes outstanding replay-attribution blocker and independent-review-pending checkpoint. Separate hash-pinned review view passes894/no skips in11.263s unittest. Exact old replay precedes value dedup;91 prior tests and9 other patch sections preserved. Pass owner for closure; parent joined acceptance remains outstanding and graph unchanged until closure. Human Git checkpoint due, not performed.
