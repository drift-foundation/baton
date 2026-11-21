# Native agent messaging, handoffs and discovery

Owning Work 2b077949-W385331; thread 2b077949-T385331. Owner selected this as the next priority, executed using v12, after labels checkpoint45141ac6.

## Owner decision — 2026-11-20

Owner-selected next priority v12 development outcome: native Work/Job messaging, explicit clarification/review/correction handoffs, and yielded defect discovery with reviewer disposition and dependency-gated resumption. Execute development through v12 using existing CLI/bootstrap/template mechanisms; v11 tracks transitional coordination only, no second authority for the same Work. Routes configurable/system-enforced, agents choose permitted destinations; no mandatory agent intermediary for routine handoffs. First discovery slice yields retained candidate/continuation for reviewer classification; no worker direct host database access/general Work-creation service. Reviewer may return within-scope continuation, file nonblocking Work and resume, create/link blocking prerequisite with atomic dependency+hold, or escalate design decision. Satisfying accepted prerequisite enables resume; rejected/cancelled does not silently unblock. Durable messages/receipts/replay and restart recovery; continuation is distinct from success/failure. Human Git/integration approval retained. Focused deterministic proofs by default. First step: bounded existing-code gap assessment and first executable native slice with mechanical kickoff, not a broad redesign/new launcher. No live launch until exact instance/artifact/task commands reviewed.

This explicitly supersedes the earlier temporary deferral of Job-linked messaging and dependency delivery in the W321608 pilot plan for this bounded slice. It does not authorize backlog migration, automatic host integration, privileged containers or general worker access to coordination stores. Existing routine implement/review workflow is the starting point, not proof these new transitions already exist.

Acceptance: an implementation can yield a finding without claiming completion; reviewer dispositions durably determine continuation or dependency hold; ordinary review/correction handoffs require no human courier; restart/replay preserves messages, exact candidate/continuation, ownership and gates without duplicate Work/effects. Blocking discovery classification creates/links the prerequisite and dependency/hold coherently; mere containment is not blocking. Design/spec decisions still require authorized owner selection. Per-labels operational lessons: required verification must name the disk-backed container root; selected worker image/layout must match; no unsupported create-while-serving command.


## 2026-11-20 — owner-interruption boundary

Owner clarification: the end goal is no human interruption for routine work. Agents/system proceed with implementation, review, corrections, routing, finding classification and dependency handling when the accepted design and delegated authority determine the action. Escalate only a concrete unresolved decision not implied or clear in the design, or an operation genuinely requiring owner authority. Ask with exact ambiguity, evidence, options and recommendation; do not turn normal handoffs, partial progress, retries within selected policy or implementation details into permission gates. Routine worker questions go first to the appropriate reviewer/decision role and reach the human only if that role cannot resolve them from accepted authority. Keep progress observable without requiring acknowledgments or human message relays. This does not delegate human Git ownership or silently broaden selected live execution/privileges; prepare required owner actions fully and consolidate them rather than asking repeatedly.


## 2026-11-20 — K preparation received; bounded review required

M385336/M385337 supply concrete gaps and a proposed discovery-first slice. Proposal is not accepted launch/implementation scope. Review concerns: prioritization of communication, invocation-completion versus yield, clarification versus specification revision, atomic dependency and accepted-base requirements, finite continuation policy, and executable kickoff validity. Resolve design-implied choices without owner interruption.


## 2026-11-20T05:24:56.820507+00:00 — reviewer disposition of K preparation (M385338/E385341)

K discovery-first proposal is superseded as the recommended execution order by FIRST-NATIVE-SLICE.md: durable clarification/in-scope-finding request, reviewer answer and same-task continuation first; Work filing/atomic prerequisite disposition follows on the same foundation, and W385331 remains open through joined acceptance. This is reviewer planning within owner SCH-2a, not a new owner ruling or live selection. NATIVE-TASK.txt supplies the first implementation outcome; KICKOFF-READINESS.md corrects unsupported --like and states missing artifact/config/pool prerequisites. Exact review review-2026-11-20T05-24-56Z.md. Resolve clarification without task-digest revision; distinguish invocation from task completion; explicitly version declared outputs/consumers; separate finite continuation from correction allowance; bind blocking receipt/Work/edge/hold atomically and require accepted integrated base when needed. No owner product ambiguity found. No implementation/tests/build/instance/model/engine/Git action performed. Return baton.decide for coordinator packet selection; no new graph allocation was made.


## 2026-11-20 — corrected communication-first preparation accepted

Coordinator disposition of M385342: accept communication-first decomposition as planning within owner-selected scope. FIRST-NATIVE-SLICE.md and NATIVE-TASK.txt define first native implementation; subsequent atomic discovery/dependency slice remains required for W385331 completion. No new product decision or live run selected. Current final-proposal runtime implements the future handoff feature; testing new handoff runtime follows separate source acceptance/qualification. Keep clarification digest unchanged and yield distinct from Job success. One-continuation planning default applies to new qualified profile only, not documentation/1 mutation.

Next: checkpoint approved DESIGN and records, then K prepares exact ordinary source/artifact/config/pool commands against that checkpoint. Reuse already qualified current image for ordinary source-development where applicable; do not introduce new runtime qualification framework or rebuild worker without concrete need. Verify actual image/layout identity, not live provider probing. Prepare one concrete packet; no more broad design research. Build/install/live selection follows reviewable actual inputs, consolidated for owner; no operational command with invented UUID or unsupported flags.


## 2026-11-20T19:39:15Z — independent recovery review, E385358

M385357 candidate ce757322b59fbd5ca14f6ec1cd1ecec14c2781fc10c1d53c235392aeb674b866 is changes-requested. Exact append-only review: review-2026-11-20T19-39-15Z.md; evidence/review-385358/. Independently310 required tests pass; reviewer probes establish lost continuation delivery, failed actual continuation replay, and cross-Work response acceptance. Supported routing/grant configuration is also incomplete. Current continuation is correction of R1–R4 on K's isolated candidate, then refreshed digest-bound delta review; supersedes the earlier kickoff-preparation state as the actionable step. No host import or live operation. Schema6→7 fresh-store refusal is covered by DESIGN734–736 and accepted M385342; the candidate's extra-ruling gate is obsolete, not a new owner decision. Larger discovery/dependency milestone remains open.


## 2026-11-20T20:53:37Z — delta review E385364

M385363/M385361 tree766f97f2e49809c5a2ebedece65d3ebd6f6d4d933b795efd2490b4726368345a: R1–R3 resolved; R4 positive supported operator path proved, but R4a remains: bootstrap accepts/persists nonempty malformed participant addresses and reports installation success, after which native_routing refuses. Supersedes the prior four-open-findings status: only bounded R4a canonical participant validation before effects is required now. Exact append-only review review-2026-11-20T20-53-37Z.md and evidence/review-385364/.342 required tests and all4 original probes pass; malformed-address public install probe fails. Preserve prior fixes, unknown-cause transient regression disclosure and copy/build/hazard limitations. No new owner decision, import, live run or schema gate. Return corrected digest-bound delta for independent review; larger discovery milestone stays open.


## 2026-11-20T21-32-47Z — R4a independent delta acceptance, E385370

Supersedes the prior R4a changes-requested state: tree f62bbaab53c7d6a7f9730b726d68fac8cefe48a92130cdc176924acd1ec64028 (36 paths; manifest 4925897d2bdf6e343d6eac229544b7c2c308f31fbf59ce01ec8b70b9c2aafd24) is accepted for the first native handoff source slice. Both addresses use shared Authority validation before installer effects; refused repeats preserve policy/input. R1–R3 bytes unchanged. Independent 538 focused tests +2 reviewer probes pass, 0 failures/errors/skips, 49.771687 s measured wall. Exact review `review-2026-11-20T21-32-47Z.md` and `evidence/review-385370/`. One existing refusal-text assertion changed correctly despite packet wording claiming no expectation changes. Prior baseline/copy/hazard/transient limitations remain; no live qualification or blanket green suite. Return baton.decide; owner integration/runtime selection and later discovery/dependency outcome remain open. No product edits or Git mutations.


## 2026-11-20T23-15-20Z — composer review E385378, changes requested

M385377/M385375 tree77ca513b409e9fc18caeeb2fdb1e27e9a27efed315a09d730bee9202b3739aeb over331dd737: supported composer positive path proved, but C1 actual-input native admission, C2 canonical output constraints, and C3 qualification checkpoint/evidence commands require correction. Independent842 passes and2 reproducing failures,0 errors/skips,98.894690s wall. Exact `review-2026-11-20T23-15-20Z.md`; `evidence/review-385378/`. DESIGN706–718 already decides admission; no new owner ambiguity. Return bounded correction to implementation. Earlier accepted first-slice product bytes remain intact; this does not revoke R1–R4a acceptance or authorize live qualification. Current next step is corrected digest-bound composer/admission packet for delta review; later discovery/dependency outcome remains open.


## 2026-11-21T00-55-22Z — C1–C3 delta review E385384

C1 bounded direct /3 declaration admission/dispatch and C2 canonical descriptors resolved on treebb5fa7050da82902b87d07b6a21447fe1fc14963cddebf879b0456794375e365 (manifestfa01b73d811ffabee510d333f18a97153ab197a21bf16ea32f92736be8ce1e77). C3 remains: contradictory hashes on five overlaps, stale output order and non-stopping shell guards/pipelines. Earlier composer packet was overwritten; reviewer recovered exact round1 manifest and five candidate files into evidence/review-385384/recovered-round-1; current complete packet snapshot in reviewed-packet. Exact review `review-2026-11-21T00-55-22Z.md`.417 passes plus1 disclosed harness-only failed assertion,0 errors/skips,23.088384s. No queued/serving creation proof claimed for this direct-only checkpoint. Current action: correct qualification/evidence packet, preserve product candidate and existing passes, then delta review. Prior messaging acceptance/coverage limits stand; no live/build/import/Git action.


## 2026-11-21T01-49-15Z — C3 helper review E385390

Previous C3 overlap/order/control-flow defects resolved on helpers4cc1469e/8f4c2663 and packetf009ba6a; productbb5fa705/fa01b73d unchanged. Six independent deterministic checks pass in1.264641s, including synthetic binding refusal through actual committed-byte checks. Remaining blocker: qualify.sh create branch directly opens Authority store; require supported readback or explicit missing observation, not dossier store access. Exact `review-2026-11-21T01-49-15Z.md`, evidence/review-385390/. Custody history/partial recovery limits verified. Current action is bounded helper/document correction to implementation; no product/live/build/Git change authorized.


## 2026-11-21T02-04-24Z — narrow create-readback acceptance E385396

M385395/M385393 helper/document delta accepted. Direct-store read removed; supported create stdout/stderr captured and attributed to returned Work/bound routing. Five independent tests pass,0 failures/errors/skips,0.927917s wall, including real create and exact helper validator on accepted composer fixtures. Exact `review-2026-11-21T02-04-24Z.md` and evidence/review-385396/. Productbb5fa705/fa01b73d, binder and prior safeguards unchanged. Report is command-time evidence only; independent after-the-fact policy/grant read remains unproved, not a new feature gate. First author probe log overwrite and older custody limits retained. Current continuation: baton.decide for owner checkpoint/selected qualification; no actual build/install/live or Git action performed; larger discovery outcome remains open.


## 2026-11-21T02-34-34Z — qualification-guard review E385406

M385405/M385403 changes requested: G1 finite path must not gate unrelated/retained records on commits; G2 preserve truthful capture-time stamp semantics through evidence writes; G3 verify qualified bundle identity before bootstrap effects. Exact append-only `review-2026-11-21T02-34-34Z.md` and `evidence/review-385406/`. Independent 6 probes:1 pass,5 reproducing failures,0 errors/skips,0.113628021s wall. Selected7ac02c7f and accepted product/43-path binder preserved. This supersedes qualification-guard readiness only. Current action: K bounded helper correction then delta review; no new owner decision, checkpoint/rebind/build/install/live authority.


## 2026-11-21T02-49-22Z — round6 delta review E385413

G1 and historical stamp timing resolved; all five old failing probes now pass. Current7ac02c7f check passes with final inputs record unchanged. Remaining G3 complete runtime (not launcher only) identity and G2 capture-excused output through outer guard require correction. Exact `review-2026-11-21T02-49-22Z.md`, `evidence/review-385413/`. Final12 probes10pass/2reproductions,0errors/skips,0.204460898s; total measured verification0.952635274s including disclosed harness iteration and host check. Supersedes prior three wholly-open findings with these two narrow residuals. Accepted product/binder preserved; return implementation then delta review, no new owner decision or live/Git authority.


## 2026-11-21T03-23-53Z — round7 delta acceptance E385420

Round7 resolves remaining G2 outer/source-identity reconciliation and G3 complete-runtime qualification. Exact `review-2026-11-21T03-23-53Z.md`, `evidence/review-385420/`.17 final independent tests pass,0 failures/errors/skips; cumulative verification1.237948910s including disclosed reviewer fixture correction/strengthening and host check. Actual7ac02c7f check passes; original0525ddb1 preserved in verified3-transition chain, current inputs unchanged. Supersedes round6 changes-requested status for bounded helper only. Current action: baton.decide for accepted packet and separately selected qualification; no build/image/install/live/Git action by reviewer. Prior product acceptance and broader discovery limits remain.

## Owner selection — deterministic clarification pipeline proof, 2026-11-21

Following the successful useful native implementation/review cycle (checkpoint 939c7adf), owner explicitly selected a scripted scenario with fake providers at the normal provider boundary and real Baton coordination. Prove durable clarification plus retained checkpoint, automatic authorized reviewer answer, exact answer/checkpoint delivery to resumed implementation, mandatory verification and independent review completion without human/model courier. Also prove a genuinely unresolved design decision reaches the owner gate without fabricated approval; restart/retry boundaries must preserve attribution and avoid lost/duplicate messages or continuation. Label all scripted evidence deterministic, not live-model judgment proof.

First inspect/reuse existing accepted coverage; extend only missing connected proofs. No live models, installed-instance changes, broad suite or activity-summary UX. Larger discovery/dependency delivery follows this bounded proof. No specification change selected; SCH-2a remains normative. Product fixes discovered here must remain bounded to this accepted outcome and independently reviewed; do not silently waive failed acceptance. Existing Git policy remains, with no expansion of the prior exact-two-viewer-test exception.


## 2026-11-21 — E385503 partial deterministic proof (baton.codxpc)

M385501: permitted baseline148 and candidate150 tests pass; two new durable Authority restart cases pass. Initial68 fixture-input errors retained and corrected by supplying exact dossier vectors. Two additive test paths preserved in evidence/clarification-proof-385503/candidate; tree ea6ffd7e395894adf1a0b7220b7439aa265572cae299098457a7591f42b21b8c, base 939c7adfe591cc413f29ab44d41392b583aaa5e5. No product/host import or Git mutation. Connected14existing+1new cases remain unexecuted because inherited fixture Git mutations are outside current exception. REPORT.md there contains coverage map, operation/target boundary, counts/durations and exact continuation. This is partial, not acceptance; next action is an explicit confined fixture-execution ruling, then unchanged connected baseline and candidate proofs. Claim returned through Baton; no broadened scope or invented product decision.

## Owner standing disposable-repository authority — 2026-11-21

Owner clarified that main development Git state/publication belongs exclusively to the human; agents may use necessary tools, including mutating Git, in authorized disposable staging/test/container repositories. AGENTS.md Git usage now pins the boundary and supersedes earlier exact-two-case fixture restrictions. Disposable operations must not reach protected Git state through shared metadata/mounts/remotes; required evidence survives cleanup. This resolves M385505 execution authority for the connected baseline and candidate tests; it is not broader live/engine/deployment authority.


## 2026-11-21 — E385510 continuation under standing disposable authority

M385508 and updated AGENTS supersede the prior fixture-Git blocker. Pinned base939c7adf and candidateea6ffd7e retained. Current HEAD3c449083 has no v12 delta against base; candidate hashes intact. Codxpc owns the same isolated two-test-path candidate; groups authority, job_manager, tools-pure. Run connected baseline14/candidate15 via prepared interpreter and existing test-one; retain per-id accounting, provenance and Git trace under evidence/clarification-proof-385510. Fresh fixture roots only, no protected repository metadata sharing or symlinks; no installed-instance or live-engine/model actions. Prior ambient-interpreter results retained as historical, final permitted selection will be verified on prepared interpreter. Last discussion M385508, current claimE385510.


## 2026-11-21 — E385510 connected proof complete, independent review pending

Supersedes M385505 partial/fixture-blocked disposition under standing disposable Git authority M385508. Base939c7adf and exact candidate ea6ffd7e395894adf1a0b7220b7439aa265572cae299098457a7591f42b21b8c unchanged; HEAD3c449083 has no v12 overlap. Prepared-interpreter baseline14/14 and candidate165/165 pass, no failures/errors/skips/unaccounted. Current test wall35.908139s; cumulative49.460230s including disclosed earlier fixture-input errors and ambient runs. Complete coverage/identity/accounting/limits in evidence/clarification-proof-385510/REPORT.md, manifest.json, logs and per-ID summaries. Main index/HEAD unchanged, host v12 clean; no live/instance/host import. Ready for independent review via baton.decide, not Work closure. Pending after acceptance/import: human checkpoint; proposed message `test(v12): prove durable clarification and escalation restart`. Last discussion M385508; claimE385510.
