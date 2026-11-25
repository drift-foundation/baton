# Plan — W385830

Status: queued for owner/coordinator selection; no executor assigned.

1. Revalidate provider adapter/composition/profile support and existing spike/context work.
2. Propose minimal bounded implementation and focused deterministic acceptance, plus any necessary real-provider qualification question.
3. Implement and independently review exact candidate; qualify image/runtime and verify explicit requested versus observed model behavior.
4. Enable selected Codex-to-Claude/Fable native Jobs only after accepted qualification and operator kickoff.

No current live instance change; no new model identifier guessed. Coordinate worker-file ownership with W385695 and W385263 before parallel implementation.


## Current next step — 2026-11-23

Prepare bounded implementation-ready contract before A1 execution: inventory production/spike/context code; minimal Codex adapter/image/composition and explicit Claude model selection; normal exchange/custody/failure/stop paths; deterministic tests and necessary provider-specific qualification. Reuse existing tools and avoid a second orchestration framework. Identify concrete owner decisions, shared files and staged acceptance. No coding or launch yet.


## Current — proposed implementation contract awaiting owner decisions (2026-11-23)

IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md is the current proposal (K, M385843). Next: owner decisions D1–D7 (contract §7); D5 (tool policy digest) is proposed first because it decides whether a mixed-provider Job is admissible and unblocks slices N1 and N2. Then contract review, assignment to codexpc for direct bootstrap implementation slice by slice, independent exact-byte review, image rebuild and qualification, and only then a separately selected first native Job. Serial with W385695 on pool.py, stage_execution.py, parallel_test.py and DEPLOYMENT.md; a rebuilt Claude image is a new digest and does not affect running or admitted Jobs. No coding, build, launch or credential access yet. W385263 A1 remains held behind this prerequisite per M385843.


## D5 settled — 2026-11-23

Owner selects shared provider-neutral tool policy plus separately digest-bound per-worker command/environment configuration. Preserve policy enforcement; no generic exclusion of tool_policy_digest. K updates contract and next unresolved decision. Other D1–D4/D6–D7 remain pending; no live operations.


## Current — contract revision 2 (delta) awaiting next owner decision (2026-11-23)

Supersedes the previous Current entry. Current contract: IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md as amended by IMPLEMENTATION-CONTRACT-REV2-2026-11-23.md. Settled: D5 (provider-neutral shared policy; provider commands bound in adapter identity; no weakened validation); D4 (refuse and hold) was already selected. Next owner decision: whether every worker must name an explicit model, Codex included (REV2 §4). Then D1 pins, D2 identifier values, D3 Codex credential, D6 provider-home mount, D7 execution selections. Slice N2 is specifiable now; N1 after the next answer. No coding, build, launch or credential access yet.


## Current — explicit models approved (2026-11-23)

Supersedes the preceding entry's pending REV2 §4 decision: option A is approved for every worker in the new composition. Attribution binds requested and evidenced reported model, provider/CLI version, attempt and candidate/verdict; missing or conflicting evidence prevents acceptance. D4 and D5 remain settled. K updates the contract and presents the next unresolved decision from D1, D2 identifier values, D3, D6 and D7, one at a time. No coding or live operation authorized by this decision.


## Current — contract revision 3 (delta) awaiting next owner decision (2026-11-23)

Supersedes the previous Current entry. Current contract: IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md as amended by -REV2- (tool policy and adapter identity) and -REV3- (explicit model and attribution). Settled: D5; D4; explicit model on every worker with attributable results. Next owner decision: when a provider reports more than one model for one invocation, when does attribution count as matched (REV3 §4). Then D1 pins, D2 identifier values, D3 Codex credential, D6 provider-home mount, D7 execution selections. Slice N2 is specifiable now; N1 after the next answer. No coding, build, launch or credential access yet.


## Current — contributor-list rule settled (2026-11-23)

Supersedes the preceding entry’s pending REV3 §4 decision. All reported models are contributors, none designated primary; requested model must appear. Additional contributors are recorded without a helper allowlist. K updates the contract and presents the next unresolved owner decision, one at a time. D1 pins, D2 identifier values, D3 credential, D6 home mount and D7 execution selections remain open. No coding or live operations selected.


## Current — contract revision 4 (delta) awaiting next owner decision (2026-11-23)

Supersedes the previous Current entry. Current contract: IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md as amended by -REV2- (tool policy and adapter identity), -REV3- (explicit model and attribution) and -REV4- (contributor-list rule). Settled: D5; D4; explicit model on every worker; contributor-list attribution with no primary designation and no allowlist. Slices N1 and N2 are fully specified; N3 waits on D1, D3, D6. Next owner decision: which Codex CLI build is pinned for the Codex worker image (REV4 §7). Then D1 Claude pin, D2 selector and mapped-identity values, D3 Codex credential, D6 provider-home mount, D7 execution selections. One reading in REV4 §9 (all evidenced sources feed one contributor set) is open to owner correction before N1 is assigned. No coding, build, launch or credential access yet.


## Current — Codex CLI 0.169.0 selected (2026-11-23)

Supersedes the open Codex-build portion of D1: owner selects 0.169.0; exact-image qualification remains required and unclaimed. Contributor evidence is limited to actual participation in the invocation, with no primary designation. K updates the contract and presents the next unresolved decision. Claude pin, D2 identifiers, D3 credentials, D6 home mount and D7 execution selections remain open. No coding or live operation selected by this entry.


## Current — contract revision 5 (delta) awaiting next owner decision (2026-11-23)

Supersedes the previous Current entry. Current contract: IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md as amended by -REV2- (tool policy and adapter identity), -REV3- (explicit model and attribution), -REV4- (contributor-list rule) and -REV5- (Codex pin 0.169.0; participation-source evidence). Settled: D5; D4; explicit model on every worker; contributor-list attribution from participation sources only, no primary, no allowlist; Codex CLI 0.169.0. Slices N1 and N2 are specified; N3 waits on D6 and D3. Next owner decision: D6, where a provider that needs a writable home gets one (REV5 §6). Then D3 Codex credential, D1 Claude pin, D2 selector and mapped-identity values, D7 execution selections. Exact-image qualification of 0.169.0 remains required and unselected. No coding, build, launch or credential access yet.


## Current — D6 stable disk-backed worker homes selected (2026-11-23)

D6 is settled: each worker has a distinct stable retained provider-home work area outside the source checkout. It survives container replacement and restart/resume; no memory-backed disposable home and no reliance on provider subdirectory conventions. Existing execution ownership prevents concurrent writer collisions. This supersedes earlier per-attempt-disposable-home suggestions. K updates the contract using existing work-area machinery and presents the next unresolved decision. No claim of qualified session reuse, no live operation or implementation selected here. Coordinate any instruction-delivery overlap with W385853.


## Current — contract revision 6 (delta) awaiting next owner decision (2026-11-23)

Supersedes the previous Current entry. Current contract: IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md as amended by -REV2- (tool policy and adapter identity), -REV3- (explicit model and attribution), -REV4- (contributor-list rule), -REV5- (Codex pin 0.169.0; participation-source evidence) and -REV6- (stable retained per-worker provider home). Settled: D5; D4; explicit model on every worker; contributor-list attribution; Codex CLI 0.169.0; D6 retained disk-backed home per worker. Slices N1 and N2 are specified (N2 now carries the home); N3 waits on D3. Next owner decision: D3, the Codex credential kind (REV6 §7). Then the W385853 ordering (proposed: N2, then its delivery delta), D1 Claude pin, D2 selector and mapped-identity values, D7 execution selections. Coordination proposal posted to T385853; no shared runtime path edited by either Work. No coding, build, launch or credential access yet.


## Current — D3 option C selected (2026-11-23)

D3 credential kind is settled: subscription login with refreshed copy retained in the private stable worker home. Registry/reference and pinned-build behavior remain unqualified. Start ownership check prevents simultaneous writers; only explicitly named Baton-owned instruction/configuration files may be replaced, never provider session data or refreshed credentials. K updates the contract and presents the next unresolved decision. No credential read, live call, build or overlapping runtime edit authorized here.


## Current — contract revision 7 (delta) awaiting next owner decision (2026-11-23)

Supersedes the previous Current entry. Current contract: IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md as amended by -REV2- (tool policy and adapter identity), -REV3- (explicit model and attribution), -REV4- (contributor-list rule), -REV5- (Codex pin 0.169.0; participation-source evidence), -REV6- (stable retained per-worker provider home) and -REV7- (subscription login seeded and retained in the home; one-writer confirmation; managed entries limited to Baton-owned files). Settled: D5; D4; explicit model on every worker; contributor-list attribution; Codex CLI 0.169.0; D6; D3 option C. Slices N1, N2 and N3 are specified to the limit of what qualification must establish (REV7 §5, U1–U9). Next owner decision: D1 Claude pin (REV7 §7). Then U8 (which registry login seeds the Codex worker), D2 selector and mapped-identity values, D7 execution selections. Ordering with W385853 is coordination in progress (T385853 M385863, M385866); no overlapping runtime edit assigned. No coding, build, launch, credential or registry access yet.


## Current — both CLI pins selected (2026-11-23)

D1 is settled: Codex 0.169.0; retain Claude 2.1.247, qualifying explicit Fable selection and contributor evidence. Failure to meet requirements may justify a separately selected upgrade, not automatic substitution. Login-copy invalidation risk remains open before sharing a seed; re-seed proposal remains pending. Next: remaining credential-reference/model-value/qualification decisions, one at a time. No live operations authorized by this decision.


## Current — contract revision 8 (delta) awaiting next owner decision (2026-11-23)

Supersedes the previous Current entry. Current contract: IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md as amended by -REV2- to -REV8- (REV8: Claude pin 2.1.247 with qualification requirements C1–C5; re-seed act withdrawn; one login per home until qualified). Settled: D1 (Codex 0.169.0, Claude 2.1.247), D3 option C, D4, D5, D6, explicit model on every worker, contributor-list attribution, home safeguards. Slices N1, N2 and the deterministic part of N3 are specified. Next owner decision: whether K consolidates the contract into one self-contained document for approval of deterministic work now, leaving qualification decisions until images exist (REV8 §7). Open afterwards, all qualification-stage: D2 requested selectors, U8 seed login, D7 selections, D2 mapped identities, U5, the lapsed-login recovery gap. Ordering with W385853 is coordination in progress. No coding, build, launch, credential or registry access yet.


## Current — consolidate for deterministic implementation review

Supersedes next-question sequencing in REV8: option A selected. K prepares one self-contained contract; historical deltas remain preserved. Remove the unapproved one-login/one-home composition prohibition; shared-login refresh risk must be qualified before shared use. Re-seeding remains an undecided recovery mechanism, not a prohibition on recoverability. Consolidation is not implementation or live-execution approval. Qualification selections remain pending for their relevant boundary.


## Current — consolidated contract returned for review (2026-11-23)

Supersedes the previous Current entry. Current contract for reading: IMPLEMENTATION-CONTRACT-CONSOLIDATED-2026-11-23.md (self-contained; earlier proposal and REV2–REV8 preserved as history). Status: for review, not approved; no assignment; no execution authorized. Next: owner/coordinator review of the consolidated contract — approval or correction of its [P] proposals, the proposed DESIGN sentence (needs explicit approval and pinning before dependent implementation), and the order with W385853 and W385695. Then assignment of deterministic slices N1, N2 and N3's deterministic part for direct implementation with independent exact-byte review. Qualification-stage decisions (engine gates, requested selectors, seed login, Q1/Q2, mapped identities, U5, lapsed-login recovery) are raised at their boundaries. No coding, build, launch, credential or registry access yet.


## Current — consolidated contract corrections

M385878 needs correction: homes are keyed to the specific Job and worker, never shared across unrelated Jobs; split preliminary pinned-image inventory from final qualification to remove N3/N4 cycle; distinguish stable normalized contributor fields from evidence digests that change with raw output. Owner confirmed Job-bound home interpretation. Exact DESIGN clarification approval remains pending. K returns a self-contained correction; no coding or live operations selected.


## DESIGN clarification applied

Owner approved the shared-policy/per-execution-adapter clarification; it is now in v12/DESIGN.md under ID-4. The previous pending exact-text gate is satisfied. K still owes the M385881 corrections and a self-contained contract for narrow review before implementation assignment. Git checkpoint remains human-owned; unrelated DESIGN edits preserved.


## Current — consolidated contract revision 2 returned for narrow review (2026-11-23)

Supersedes the previous Current entry. Current contract for reading: IMPLEMENTATION-CONTRACT-CONSOLIDATED-REV2-2026-11-23.md (self-contained; first consolidated contract, first proposal and REV2–REV8 preserved as history). Corrections applied per M385881 and M385882: Job-and-worker-keyed provider homes; inventory gate (N3) separated from adapter (N4) and image qualification (N5); proof 11/12 corrected; approved DESIGN wording quoted. Status: for narrow review, not approved; no assignment; no execution authorized. Next: narrow review of changes R1–R4; then approval or correction, and the order with W385853 and W385695; then assignment of N1 and N2. Selection of the N3 inventory (an engine operation) can be raised independently of N1 and N2. Later boundaries: N5 gate, requested selectors, seed login, Q1/Q2, mapped identities, U5 before a login is used from more than one home, lapsed-login recovery. No coding, build, launch, credential or registry access yet.


## Current — N1/N2 approved, implementation not yet released

Owner approved N1/N2 against consolidated REV2, with canonical identity-safe home paths and correction of the later N3 event-fixture evidence claim. Coordinate shared-file edits serially after codexpc W385695 checkpoint-2 recovery; preserve that active assignment. Next: bounded N1/N2 assignment and real graph gates before release. W385853 delivery follows accepted N2 interface. Engine inventory, image/provider qualification and native use are not selected. Decision details and exact contract hash in FINDING.


## Current — N1/N2 approved; contract wording recorded; awaiting assignment (2026-11-23)

Supersedes K's previous Current entry; consistent with the coordinator's "N1/N2 approved, implementation not yet released" entry above.

Accepted facts:
- Approved contract: IMPLEMENTATION-CONTRACT-CONSOLIDATED-REV2-2026-11-23.md (sha256 dc3245c0c5594f15d22c87cd9b9a19352c633c3e4ef9a52f070f24d87960bd87), slices N1 and N2 only (M385887). Read with IMPLEMENTATION-CONTRACT-N1N2-ADDENDUM-2026-11-23.md, which records the two review qualifications: fixture provenance (proof 50a; N4a/N4b) and digest-derived, record-bound home paths (proofs 31, 31a–31d).
- The shared-policy clarification is in v12/DESIGN.md under ID-4 (M385882).
- Not approved or selected: N3 inventory, N4, N5 gate and provider questions, native use; any credential or registry read, image build, install, engine operation or live call.
- Routine in-scope deterministic corrections need no further owner approval round.

Next executable milestone: the coordinator's bounded N1/N2 assignment and real graph gates, serial behind codexpc's W385695 checkpoint-2 recovery (not interrupted or reallocated). Then direct implementation, exact candidate, independent exact-byte review. W385853 runtime instruction delivery follows the accepted N2 interface; no runtime edit ownership assigned.

Parallel-edit coordination: tools/pool.py, tools/stage_execution.py, tools/parallel_test.py, DEPLOYMENT.md with W385695; worker/claude_agent.py, worker/Dockerfile.claude and the context prompt/argv builders with W385853's later delivery.

Pending at their boundaries: N3 selection; source of Codex turn-event evidence before N4b; N5 gate; requested selectors, seed login, Q1/Q2; mapped identities and C1–C5 outcome; refresh invalidation before a login is used from more than one home; lapsed-login recovery mechanism.

Checkpoint due: none yet for this Work (no product bytes). W385263 A1 remains held behind this Work.


## Current — N1/N2 assignment prepared against 9f979022; gates await the owner (2026-11-24)

Supersedes K's previous Current entry.

Accepted facts:
- W385695 is closed satisfying; owner checkpoint 9f979022. The serial-behind condition on N1/N2 is met.
- Approved contract and addendum unchanged (sha256 dc3245c0… and c4d2c4b7…, re-measured).
- Assignment and handoff: ASSIGNMENT-N1N2-2026-11-24.md (sha256 ae9dfac38ba3bd61d628c23c98637e9a8eb2e68ac50b8592b0717063992d3b22). Work body for the create command: ASSIGNMENT-N1N2-WORK-BODY.txt (sha256 ff3b0dfcef20ab28b7287139e12e84cee23357712989680db5a991cfa3770703).
- The contract's cited code was re-read at 9f979022 (assignment §3). Findings stand; locations moved. New at the checkpoint: a provider supervisor (worker/bounded_command.py), a publication worker and lane that invoke no provider, and a second candidate-accepting path through publication recovery.
- The approved ID-4 sentence is in the working tree of v12/DESIGN.md only; 9f979022 does not contain it.

Next executable milestone: the owner installs the gates and releases with the five commands in assignment §4.1 (create the N1/N2 Work under W385830; block W385853 on it; block W385263 on W385830; read back; reroute to baton.codx). K could not: both mutations were refused for lack of route authority, and nothing was changed. Then codexpc claims and implements N2 then N1 as one candidate from a disposable copy at 9f979022; independent exact-byte review; owner import and checkpoint.

Open owner decision (one): attribution when a new-composition candidate is published by an approved publication recovery — assignment §5; K recommends refusing such recovery (option A). It gates N1 acceptance, not the start.

Not selected: N3 inventory, N4, N5, N6, any build, engine, credential, registry, provider or native operation. Pending boundaries are unchanged from the addendum §5.

Checkpoint due: the ID-4 text in v12/DESIGN.md and this dossier are uncommitted.


## 2026-11-24 — owner selected B, recovery attribution

Slawomir approved B: carry and enforce original producer attribution through publication recovery for new-composition Jobs. ASSIGNMENT-N1N2-OWNER-B-2026-11-24.md supersedes the pending assignment decision and narrowly extends recovery scope. DESIGN ID-4 reflects the ruling; owner Git checkpoint remains pending. No implementation or live execution performed. Owner script will create the bounded child, install W385853 and W385263 gates, read back the graph, and release to baton.codx. Until that script succeeds, no graph or assignment change is claimed.


## 2026-11-24 — W385965 active, codexpc E385969

Gates installed and canonical claim succeeded. Implements N2 then N1 including owner B original attribution through recovery from pinned9f979022 in disposable work/scratch/w385965-n1n2/repo. Current approved DESIGN is read-only task context beside the copy; not part of candidate delta. Scope and verification: approved contract proofs1–47,32a,31a–d and owner-B recovery cases; focused deterministic tests only. Main-area files exclusively owned by this claim; W385853 gated and W385263 held. Candidate/evidence starts at evidence/implementation-385969/START.json. No source implementation yet, no blockers, no build/provider/native/credential authority. Child T385965 read throughM385965 and eventsE385969; parentT385830 throughM385964. Next: N2 composition/launch/home integration, then N1 attributable results and recovery checks. Independent K review required; owner checkpoint/import remains pending.

## 2026-11-24 — W385965 incomplete implementation checkpoint (baton.codxpc)

No acceptance or gate discharge. Candidate sha256:f88403d06ef393421acfb0a3ae75a0b9f47bead87bdd901890d6390d246cc295, original base 9f9790222dfd004bc8f19d5c378c3acdb00fd4ca, preserved under evidence/implementation-385969/. Current continuation is [CHECKPOINT-N1N2-385969.md](CHECKPOINT-N1N2-385969.md). One next executable milestone: finish the connected N2 admission/launch/home/pending/restart lifecycle with deterministic production-path proofs, then N1 and owner-B as already approved. The /7 execution refusal remains until required enforcement is connected. No unresolved owner decision is asserted; normal implementation remains authorized. K review is still pending the complete joined candidate.

## 2026-11-24 — current W385965 completed candidate for K review (supersedes partial checkpoint state)

N2, N1 and owner-B implementation is complete as a review candidate under E385975. Exact identity `sha256:2abcd54485ab85ab0deb81db2a94447c54f72a2805461cfdc9f3742576eb7887`, pinned upstream base `9f9790222dfd004bc8f19d5c378c3acdb00fd4ca`, 35 paths. [Handoff](HANDOFF-N1N2-385975.md), [proof table](PROOF-TABLE-N1N2-385975.md), implementation account in PROGRESS, durable `evidence/implementation-385975/` archive/manifest and joined ledger: 2791/2791 unique passes. Historical partial checkpoint and old waiting-for-routing statements are superseded only for current execution state.

One next milestone: independent K review of these exact bytes and deterministic evidence. No source acceptance/import yet; W385853 remains gated on accepted N2. No implementation blocker or new product decision. Container/provider qualification remains unselected. Preserve pinned current DESIGN context; owner must checkpoint its approved amendment before/with any accepted source import. Suggested eventual human commit message: `Add explicit provider attribution and retained Job-worker homes`. No earlier independent review of this completed candidate exists yet; retain the next review as a fresh review file at this dossier root.


## 2026-11-24 — K independent review of W385965 candidate 2abcd544: corrections requested

Review: review-2026-11-24T10-12-37Z.md (sha256 65cb8a185d184ae82f9a38fa3574693ce2fade248763f89a505918ed9f4ef14f); evidence/review-K-385978/ (packet.sha256 f22181eccd84408591e2e9e9c14479da54595c075861873fd4d1f6c43b42422f). Not accepted as it stands; four bounded corrections, then a delta review. R1: a holder that never started a runtime blocks its Job's home permanently. R2: proof 39's test fails when the temporary root is under a directory named home. R3: a held attribution shows as answering with no reason. R4: provenance wording and the proof 37 mapping. Verified: packet and identity, 2791-test accounting recounted from raw logs, legacy composition byte-identical, attribution enforced and held across passes and restart, original-producer attribution through recovery including the real worker's result file. The September raw participation output is not retained anywhere; the Claude participation list is therefore drafted and unqualified, which contract section 7 permits. One owner confirmation: keep the drafted list until qualification (recommended) or empty it now. Next milestone: R1–R4 by the implementer as routine corrections; W385853 stays gated; no import.


## 2026-11-24 — owner decision settled; R1–R4 correction milestone

Owner confirmed keeping the Claude contributor list drafted and unqualified; FINDING records the ruling and supersession. No remaining owner decision blocks these corrections. Resume candidate 2abcd544 under W385965: address R1–R4 in review-2026-11-24T10-12-37Z.md, preserve original packet, retain a delta manifest and focused proof evidence, then independent K delta review. R1 requires both successor progress after proven pre-start failure and continued waiting after a requested start without cessation; R2 tests the exact creation fault under /home; R3 exposes typed cause and owner action in the stage reason; R4 corrects provenance and proof 37. W385853 remains gated; no import or native qualification. Nonblocking review notes remain disclosed for later qualification, not silently claimed resolved.

## 2026-11-24 — E385982 correction executing

Read through M385980 / E385982; current owner ruling retained. Prior 2abcd544 manifest files and modes verified before edits; original packet remains immutable. Owned correction paths: worker_manager attempts/provider_home, job_manager projection, shared job_observation, their focused lifecycle/home/display tests, one-worker scheduling proof, and PROVIDER-SELECTION documentation. R1 adds positive ended-before-start evidence with a transaction-time delayed-start fence; R2 targets the exact dir_fd-relative creation and runs under /home; R3 carries a typed read-only hold cause to status/monitor without creating owner records or changing lifecycle; R4 corrects written provenance and proof 37. Logical groups: manager-pure, tools-pure, job_manager; focused deterministic test-one only, exact logs/collection/source/accounting in evidence/correction-385982/. Next: finish focused regression and return exact delta for K review. No further decision, native execution, builds or import selected.

## 2026-11-24 — current R1–R4 candidate returned for independent delta review

Supersedes the executing E385982 milestone: R1–R4 corrected in candidate `sha256:4980bb47c07ed40503945d2926681590f393b657d9413293079c2e6520679053`, base unchanged `9f979022`; nine-path delta against reviewed `2abcd544`, full 37-path candidate. [Current handoff](HANDOFF-N1N2-385982.md), [proof table](PROOF-TABLE-N1N2-385982.md), PROGRESS and `evidence/correction-385982/` preserve exact bytes, owner ruling, review, tests and limitations. Final focused 765/765 passes, zero skips/errors/failures/unaccounted; original review/packet unchanged. One next milestone: K independent exact-delta review. No R1–R4 blocker or new owner decision; W385853 remains gated. Claude source list remains drafted/unqualified, native use requires retained exact-build raw output qualification. Review section-5 notes remain open qualifications; no source acceptance, import or human checkpoint is claimed.


## 2026-11-24 — K delta review of W385965 candidate 4980bb47: one bounded defect remains

Review: review-2026-11-24T16-45-42Z.md (sha256 19bfb553cd53e3331577705ef2d70d14416e4fb1b45beb0eaae0e23007f3dd26); evidence/review-K-385983/ (packet.sha256 848314eb16d1e8f8946c4aea40c65e6a0f909fb549c376e5693190cb0c7147fa). Not yet accepted. R2, R3, R4 accepted. R1 corrected for the reported case and the start fence holds inside the transaction; R1a remains: a holder whose attempt ended while the home record is still `preparing` blocks every successor, because `provider_home.acquire` refuses that branch before consulting cessation (probe D5). One next milestone: implementation corrects R1a with its two proofs through the configured route, then a K delta review of that change. W385853 stays gated. No owner decision open. Earlier evidence and disclosed qualification limits unchanged.


## 2026-11-24 — R1a correction returned for K delta review

Current candidate sha256:5b76e7000b38c77b8405b92215f5ed7d82aeb20dab62bd2ccc2fe23a13ed5b62; evidence/correction-prompt-r1a/REPORT.md and exact manifests/archives. Three-path delta, 49/49 focused passes; prior failing reproduction retained. One next milestone: K independent R1a delta review. Prior R2–R4 acceptance preserved. No product import, native execution or claim held; W385965 at baton.decide and W385853 still gated. Owner-directed interactive correction exception ends on this handoff.


## 2026-11-24 — K delta review of R1a, candidate 5b76e700: accepted on the bytes; one owner ruling on review independence

Review: review-2026-11-24T17-01-44Z.md (sha256 d6849149715381e2542d388138fa44fb392827b81a4500bce12bd4e577ee4fa4); evidence/review-K-385988/ (packet.sha256 73800bbf4a7be1c1355c69650db702376fe27813e93be4371abc95444a991d2c). R1a corrected: takeover of a `preparing` home requires proved cessation of the exact recorded holder; thirteen unproved evidence forms stay pending with no write. R1–R4 and R1a closed; no remaining defect. Open for the owner: the R1a correction and this review are both by participant baton.prompt (different sessions), so the review is not independent by identity; accept it for this two-line change or have baton.rvpc confirm the three-path delta. One next milestone: that ruling, then the owner import/checkpoint decision for candidate 5b76e700. W385853 stays gated until acceptance is recorded.


## 2026-11-24 — owner accepts K independent-context review and selects import

Slawomir explicitly accepted K's review-2026-11-24T17-01-44Z.md as the independent review of candidate 5b76e700, despite both contexts recording baton.prompt. This is a candidate-specific independence ruling, not a general shared-identity waiver. K did not implement the correction and independently reconstructed and probed its bytes. R1–R4/R1a are accepted. The coordinator prepares exact-byte host import and human checkpoint; no Git mutation, image build or native qualification selected. Qualification limitations remain unchanged.


## 2026-11-24 — accepted N1/N2 exact-byte host import verified

Owner accepted the independent-context K review M385989 for candidate 5b76e700. Imported all 37 reviewed files after whole-path base/type/ownership/write preflight; existing modes preserved and new files 0644, final exact bytes verified. Evidence: evidence/import-5b76e700/preflight.json and postflight.json. Host integration: 64 collected/executed/passed, no failures/errors/skips/duplicates/unaccounted, 12.176209s, stable source identity; supported test-one on prepared interpreter, groups manager-pure/tools-pure/job_manager. No full-suite, image or native qualification claim.

Next milestone is Slawomir's Git checkpoint. Prepared owner script stages the 37 reviewed paths, this dossier and only the provider-policy/recovery-attribution ID-4 amendments in DESIGN; unrelated W385263 OBS-2 changes remain in the working tree. No protected Git mutation by coordinator. W385965 closure and W385853 gate discharge follow observed checkpoint; umbrella W385830 remains open for later slices and qualification.


## 2026-11-24 — N1/N2 owner checkpoint and closure

Checkpoint 317351e73c92749e201f536ba115c9fdf213077d observed; W385965 closed satisfying, handler cleared. Closure receipts in evidence/import-5b76e700/closure-receipts.jsonl. N2 dependency is satisfied; W385853 instruction delivery can proceed through its own assignment. W385830 remains open for later slices and qualification. No native-use qualification is asserted.


## 2026-11-24 — N3 preparation E386002 (baton.codxpc, impl)

M386000/E386001 authorized only inventory preparation; checkpoint 317351e73c92749e201f536ba115c9fdf213077d. Completed exact packet [operator handoff](evidence/n3-preparation-386002/README.md), manifest sha256:5591a82b61325f7134f042ba86f5c4463cb82e631d59297a91923944a87d3bef, archive sha256:7edd762c1589e7104708f500a848308e54d0ce869af879351890f12cdb4fa827. K ownership M385999 preserved: no product or shared recipe/runtime/instruction edits. Last thread read M386004; its I1–I6 requests are mapped in the handoff with unknowns preserved. No new instruction-loading claim, N4 work, credentials, registry, build/container or provider execution.

Static preparation checks 27/27, exit 0, 0.016341272s; raw stdout/stderr, command/source/timing header and exact context retained in evidence/n3-preparation-386002/. These are not product tests or runtime qualification. Runner prepares anonymous pinned-version build and five offline help/version probes; exact base/image identity captured only on selected execution. Build timeout does not prove daemon cessation; stop/diagnose before retry. No preparation blocker. One next milestone: owner execution selection of the exact packet, followed by evidence assessment; umbrella remains open and qualification pending. /tmp script is expendable; durable copy and archive retained.


## 2026-11-24 — owner selects direct N3 inventory execution by codexpc

Slawomir answered yes to codexpc executing the exact prepared Codex-only packet directly: one anonymous public base-image pull, one minimal inventory-image build with Codex 0.169.0, and five network-disabled version/help/read-only variants. Selected packet: evidence/n3-preparation-386002/README.md; manifest5591a82b61325f7134f042ba86f5c4463cb82e631d59297a91923944a87d3bef; runnerac17d16ba4c8f578011c7094719995772d4a9263b2c11499bbab8c05bf11f9c0. Run id n3-386002-01 and exact packet bounds/ownership/cleanup apply. No credential or registry reads, login, provider/model calls, production deployment, N4 or security relaxation selected. Host CODEX_HOME=/home/sl/.codex-pushcoin does not authorize mounting that home into the probes.

Claim before execution; coordinate shared Docker engine use, preserve K product ownership, verify pinned packet, then use the retained runner run command with --confirm-execution. Completed phases are reused after hash validation. A failed/interrupted phase requires diagnosis; do not infer Docker daemon cessation from a client timeout or blindly retry. Report a concrete correction/retry need if encountered. Required next milestone: retained exact-image CLI inventory and evidence assessment, not native qualification. Store raw help/traces and measured timings, verify owned container cleanup, publish the final handoff and release the claim. No execution performed by coordinator in recording this selection.


## 2026-11-24 — N3 selected execution complete (baton.codxpc, E386008)

Supersedes the pending N3 execution milestone only. E386007 selected the exact M386005 packet; claimed E386008, consumed through M386005/E386008 and posted shared-engine notice M386009. One invocation of retained runner completed all seven phases and five offline probes on attempt 1, exit 0, 14.653826 measured seconds; no retry, timeout or security relaxation. Exact result and limitations: [N3 execution report](evidence/n3-execution-n3-386002-01/REPORT.md). Image `sha256:17d250b7f620cf69fce0fd96dc1ccbb5b76151a2a6f6bae4fedb2027076f6b0c`; observed `codex-cli 0.169.0`. Raw help, traces, image/container inspection, command/timing records and packet retained; 173 phase artifacts rehashed. All five probes and six build intermediate containers independently confirmed absent after runner cleanup.

Read-only HOME help exits 0 with a PATH-alias warning; writable HOME help/version creates `.codex/tmp/arg0-linux` aliases. These observations establish no turn-mode instruction, writable-home, auth or contributor behavior. M386004 I4 covered; I3 limited to selected startup modes; I1/I2/I5 and provider qualification unresolved. No credentials/model calls, product/K path edits, N4, product tests or protected Git mutation. No product logical group affected. Exact local image retained, but no image backup/reproducible-build claim; required evidence awaits human Git checkpoint/backup.

Next bounded milestone: independent evidence assessment and disposition of N4a/qualification boundary through baton.decide; umbrella remains open. No packet execution blocker. Report and evidence manifest identify the deliverable; suggested human checkpoint after acceptance: `Record selected N3 Codex 0.169.0 inventory and cleanup evidence`.


### N3 handoff update — M386011 consumed before release

K coordination M386011, revalidated against W385853 FINDING and DELIVERY-CONTRACT-REV2-2026-11-24.md section 7: I1/I2 are informational, no longer native-use gates. I6 now asks a separately selected qualification turn to state its role and delivered instruction digest. I3/I4/I5 unchanged. This supersedes the previous I6 mapping for continuation; no further execution requested or performed. REPORT.md updated. N4 inherits the execution-context prompt label; offline inventory did not establish a turn-mode home instruction filename. Last discussion read M386011, last claim event E386008.


## 2026-11-24 — N4a independent preparation E386020 (baton.codxpc, impl)

E386019 resolves the old claimability blocker; E386020 claimed. Prepared [bounded N4a implementation packet](evidence/n4a-preparation-386020/README.md), manifest SHA256 `4685195b4da1b70d127dae63c002a88113939331ca8dda57256ef24c9a6d5a70`, against checkpoint317351e7 and retained exact N3 image/help/version evidence. Includes proposed argv (no guessed model), observed version, exact source seams, recipe direction, focused acceptance and explicit missing provider facts. Product inputs match the checkpoint; current DESIGN and pending D contract are preserved as context, not modified. This is completed preparation, not an implemented adapter or native-use qualification.

Confirmed source gaps: claude_agent.provider_version accepts bare/Claude versions but not observed `codex-cli 0.169.0`; _prepared_home still selects the module-level Claude credential slot; provider_policy.adapter fixes the dogfood entrypoint. Codex cannot inherit terminal exit-zero success or Claude turn parsing. These bounded future changes are named to K; no broad refactor selected. N3 establishes no auth filename, instruction target or turn/session format. Null targets in ARGV-PROPOSAL are preparation markers, never admissible product configuration. N4b parsing and sources remain gated; no positive turn fixture invented.

K confirmed ownership in M386022, OWNERSHIP-N4A-DELIVERY-2026-11-24.md SHA256 f0f41390b152f40b45090606e8954a683b651002440523e0d61ba363a512d16c; acknowledged M386024. N4a owns new Codex adapter/entry/recipe/dedicated tests and optional entry factory seam. D owns label/package/home-prompt/ending/status work. Shared realization/hooks/registry/docs follow D accepted/imported checkpoint; D whole-contract approval and implementer assignment remain pending. Additional host role guards in pool.py/single_worker.py named for allocation, not silently claimed. No overlapping edits. Last parent discussion consumed M386023; K M386022; claim E386020.

Verification: 33/33 static provenance/source/option/unknown-boundary checks, zero failed, 0.001107898 seconds, plus confirmed ownership-record digest. These are preparation checks, not product tests or behavioral proof; no affected product group. Future implementation groups manager-pure/tools-pure, exact modules and one registry each, with logs/ledger/source header per TESTING. No build, engine, credential, provider call, resume, source import or protected Git mutation. Exact files retained in dossier; human checkpoint/backup still required for machine-loss recovery.

Next bounded milestone: disjoint N4a implementation candidate under the confirmed allocation, then serialized shared join after D checkpoint. No repeat N3 or automatic N4b. Preparation handed back for independent assessment; umbrella remains open.


## 2026-11-24 — K: assessment of N4a preparation packet

review-2026-11-24T21-10-45Z.md (sha256 e632a4d3a03f0fda3eb2a528209969f470408e75b8f3744562180f7ea3aa973d), by baton.prompt (K), no claim, reading only. Packet evidence/n4a-preparation-386020 accepted as preparation; no blocker to the disjoint N4a implementation; D-first order for shared files preserved. Required in the disjoint step: R1, refuse a prompt operand that is empty, begins with `-` or equals a Codex subcommand word. Join conditions: J1, the Codex realization cannot land until a selected source establishes the credential path (owner selection, not needed before the disjoint step); J2, the named claude_agent.py hooks and the pool.py/single_worker.py guards and slot naming are allocated to N4a in the join step. Accounted tests and acceptance review are at the join; proofs 48 and 49 belong to N4b.


## 2026-11-24 — disjoint N4a draft E386029 (baton.codxpc, impl)

E386028 and the owner selected M386027 disjoint implementation with R1. Completed seven-new-path candidate on checkpoint317351e7: [draft report](evidence/n4a-draft-386029/REPORT.md), manifest SHA256 dac8d6bd2b5541a3779c255725fe74101ad323bbdfd084c464293684635fd00c. Codex argv and early prompt refusal, fresh/role/build subclass guards, unclassified terminal outcome, existing validated/supervised entry reuse, pinned source-only recipe and dedicated inventory-backed tests. All 1,144 existing base files byte-identical; no shared edit or protected import. K D notice M386030 consumed, acknowledged M386032; D-first ownership preserved.

Focused supported test-one on prepared interpreter: 14 collected/executed/passed, zero failures/errors/skips, 0.445947458 measured seconds. Explicitly unaccounted draft per M386027 and owner; future group manager-pure, registry and accepted accounting at serialized join. Exact logs, collection/per-ID summary, source header and recoverable candidate retained. No builds, engine, credentials, provider calls, resume or protected Git mutation. Scratch retained, no launched adapter process or container to clean up.

Next bounded milestone: independent draft assessment, then joined accounting/acceptance only after D accepted/imported human checkpoint. Shared version decoder, delivered credential slot, host role/fresh guards, policy/registry/docs remain join work under J2; inherited version decoder still rejects Codex prefix. Home/session paths deliberately refuse until evidence/integration exists; current policy still refuses Codex composition. J1 credential-path source selection and N4b exact-build turn parsing stay gated. No native qualification or completed joined adapter claimed. Required recovery bytes are in the dossier; human checkpoint/backup pending.


## 2026-11-24 — owner checkpoint observed; N4a shared join

After Slawomir reported the checkpoint complete, the interactive coordinator read HEAD as `ac034bc1c9fae525b94a1a5f21d9721c677dc39e` (Deliver native worker instructions and execution-context label under provider selection). W385853 candidate 6580545d import is recorded in its evidence/import-6580545d/IMPORT.md; acceptance is M386046 for implementation/review only. This is the checkpoint for the N4a shared-file join under OWNERSHIP-N4A-DELIVERY-2026-11-24.md and review M386027. Continue retained draft M386033; preserve R1, use the delivered shared label/instruction interface, register tests and collect accounted focused evidence. Credential-path J1 and N4b evidence remain gated; no guessed paths, successful turn parsing, builds, credentials, providers or resume selected. W386048 remains open; provider-selected integration is not claimed. No protected Git mutation by coordinator.


## 2026-11-24 — completed bounded N4a join (baton.codxpc, E386051)

Supersedes the pending join milestone only. Exact candidate `sha256:e9e9c84f39ddaf2cd7aa4f358d68682dd27eb45bf51e04eef4cb5dc3b465657f`, 17 paths on ac034bc1: [report](evidence/n4a-join-386051/REPORT.md), manifest and full candidate archive retained. Shared hooks/host guards consume D's accepted interface under M386027 and the ownership agreement; D-first checkpoint observed. No protected product import. J1 credential/managed-path selection and N4b parsing remain gated; no builds, credentials, provider calls or resume. W386048 remains separate, with its implicated shared methods unchanged.

Final focused verification: 391 collected/executed/passed, 35.446493069 seconds, zero skips/errors/unaccounted or source drift. Earlier accounted affected groups: manager-pure 4522/4532 and tools-pure 3651/3691 passing; all tests executed, no skips, no drift. Two candidate inventory omissions were corrected and pass in the final focused run; the other 48 outcomes independently reproduce on the unchanged base. No broad-group green claim or waiver. Complete failure classification and logs/ledgers/source identities retained. Initial fixture-root Git-discovery incident, refused outer checkout attempt and audit limitations are disclosed in the report; final HEAD unchanged and index diff empty, run process groups absent.

Next bounded milestone: independent exact-candidate review through baton.decide. No confirmed uncorrected candidate defect from these checks; broad baseline failures remain a verification limitation for reviewer disposition. After acceptance, owner import and human checkpoint remain pending; suggested commit message: `Add bounded Codex adapter hooks and joined offline coverage`. Full suite/native qualification is not selected. Last parent discussion read M386053 (our test-path notice); final handoff/disposition follows.

Disposition: M386054 publishes the exact final candidate and evidence. Atomic pass E386055 returned W385830 to baton.decide for independent review routing; fresh detail snapshot386055 verified Handler/claimed_at null, phase queued and zero pending obligations. Claim E386051 released. No candidate edits after release.


## 2026-11-24 — K: independent review of N4a join e9e9c84f

review-2026-11-24T23-40-10Z.md (sha256 d38fa34d330765cd093bb0381e88a699b9dc89f8ed570b514b92086b1454230d), by baton.prompt (K), no claim. Candidate sha256:e9e9c84f39ddaf2cd7aa4f358d68682dd27eb45bf51e04eef4cb5dc3b465657f accepted on bytes for the bounded N4a join: identity, archive and base hashes verified; 1008/1008 in my own run outside the checkout; Claude adapter identity unchanged; J1/N4b gates intact; 48 classified failures reproduced on 317351e7, ac034bc1 and the candidate with no candidate-attributable difference. NOT accepted as written: the fixture-isolation incident record. Finding I1: at 16:07:09-16:07:10 test_checkpoint_profiles fetched into the protected repository, creating refs/baton/source/main (821fe1b9), loose objects, a pack and FETCH_HEAD; only the checkout was refused. Required: corrected incident record by codexpc; inspection and decision on the ref by Slawomir (command in the review; not run by me). Evidence evidence/review-K-386054/.


## 2026-11-25T00:09:08.753765+00:00 — incident correction, M386056 I1 (baton.codxpc)

The earlier account that no successful protected mutation was observed is **incorrect and superseded**. The protected-repository fetch succeeded: it created `refs/baton/source/main` at `821fe1b94e4ea58e8b4a7670a16ee5dd64b2fb79`, wrote loose objects (prefixes `53485ec9`, `a2f63724`, `821fe1b9`, `51915b90`, `aa86046a`, `cb9f9f62`) and pack `pack-90ca7232…`, and rewrote `FETCH_HEAD`. **Only checkout was refused**, because tracked files were dirty. Evidence source: K independent review M386056, review-2026-11-24T23-40-10Z.md, I1, observed local 16:07:09–16:07:10.

My HEAD/index audit was insufficient to support the original conclusion. I accept the correction and responsibility for selecting unsafe fixture roots. The original prose and original JSON fields are preserved as history; JSON now appends a dated correction. The exact original JSON is retained under finding-v12-git-fixture-isolation/evidence/. Review observed no HEAD/index/tracked-file damage, but that does not negate successful metadata mutation. Object/pack contents and config remain uninspected here. No protected ref/object/FETCH_HEAD/config cleanup was performed or is authorized; inspection and disposition belong to Slawomir.

Tracked separately as W386057, dossier `work/records/2026/11/finding-v12-git-fixture-isolation`. No affected-group rerun. Accepted N4a `sha256:e9e9c84f39ddaf2cd7aa4f358d68682dd27eb45bf51e04eef4cb5dc3b465657f` and its 17 files/archive are unchanged; M386056 accepts those bytes. W386048, J1 and N4b remain separate.


## 2026-11-25 UTC — N4a join imported, checkpoint pending (baton.prompt)

Accepted candidate `sha256:e9e9c84f39ddaf2cd7aa4f358d68682dd27eb45bf51e04eef4cb5dc3b465657f` (17 paths) is imported byte-for-byte on base `ac034bc1c9fae525b94a1a5f21d9721c677dc39e`; coordination M386064; record `evidence/import-e9e9c84f/IMPORT.md`. Human checkpoint pending: `evidence/import-e9e9c84f/owner-checkpoint.py` (copy `/tmp/baton-w385830-n4a-checkpoint.py`), message `Join deterministic Codex adapter, entry and recipe candidate under provider selection (N4a)`. The W386057 isolation paths are separate and excluded. Commit identity to be recorded here once observed. J1, N4b, qualification and native use stay gated; W386048 separate.


## 2026-11-25 UTC — bounded J1/N4b qualification preparation (baton.codxpc, no claim)

Owner requested planning only. W385830 remains queued at baton.decide; no claim/routing change. K confirmed packet-only ownership M386064 during exact N4a import, acknowledged M386065. Completed [one qualification packet](evidence/qualification-preparation/README.md), identity `sha256:f9d41f9caa43bf5b1d6d870d98d48ef55a1ca6c7a22d81af4a465e76746b6460`, archive sha256 `fa46fc0a659734279e396c7510bd5e9e24a154772a35ee6e29829113ecc98dea`. Pins accepted e9e9c84f 17-path archive/base and retained exact Codex 0.169.0 image/inventory. No accepted adapter/shared-file writes.

Stage A proposes explicitly selected network-none login help/status tracing in empty homes, with exact-build subscription-loader/source corroboration before any credential path is accepted. No filename/schema guessed. Stage B proposes one bounded fresh CLI invocation to capture actual terminal/contributor sources and verify implementation role plus delivered instruction digest through the same accepted label/argv functions. It is a protocol-capture harness, not a native Job or N5 image qualification. No successful output fixture is invented; missing contributor evidence or unobserved terminal classes remain gated. The one invocation may use multiple internal provider requests; no automatic retry.

Owner selections remain: exact credential source/custodian and seeded-copy/refresh/retention policy; accepted credential/backend and managed-path evidence; explicit model and later exact reported-identity mapping; offline and live execution authorizations, network/posture/limits/run roots. Reviewable scripts render argv only by default and refuse null selections; execution payload remains unrun. Detailed evidence, redaction/quarantine, cleanup/cessation and acceptance criteria are in README. W386048/W386057 remain separate; protected metadata disposition is untouched.

Validation: 22/22 static preparation checks, 0.001910530 s; AST/input hashes/pure renderer only, not product-test or runtime qualification. No builds, containers, credential reads, provider calls, Git mutations or product test groups. Next milestone: owner/K packet review and possible Stage A selection; Stage B stays gated.

Qualification-preparation disposition: packet published M386068, no claim held or route changed. Consumed K import notice M386067 before ending: accepted 17-path filesystem import is reported complete, human checkpoint still pending. Packet is frozen at its preparation snapshot and pins the retained accepted archive/base; this later import notice does not change its bytes or select execution. All 17 paths remain untouched by codexpc. Last thread position read M386068.


## 2026-11-25 — N4a owner checkpoint observed

Interactive coordinator verified HEAD ad6dcad0aa38f8ccc17fd6a50bd92bf6f2d8c402 after the owner reported the checkpoint complete: Join deterministic Codex adapter, entry and recipe candidate under provider selection (N4a). Exact-byte import is recorded in evidence/import-e9e9c84f/IMPORT.md; acceptance M386056 remains bounded. W386057 isolation edits are separate and not part of this checkpoint.

M386068 has already returned the planning-only J1/N4b qualification packet at evidence/qualification-preparation/README.md, so no duplicate preparation assignment is needed. Next milestone: independent assessment of that packet, followed by explicit selection of any offline execution; live execution, credentials and model selection remain unselected. Codex native use remains gated.


## 2026-11-25 UTC — N4a checkpoint observed; qualification packet reviewed (baton.prompt)

Human checkpoint observed: `ad6dcad0aa38f8ccc17fd6a50bd92bf6f2d8c402` "Join deterministic Codex adapter, entry and recipe candidate under provider selection (N4a)", 17 product paths, working tree equal to the manifest of `sha256:e9e9c84f39ddaf2cd7aa4f358d68682dd27eb45bf51e04eef4cb5dc3b465657f`. Packet M386068 reviewed: [review](review-2026-11-25T00-46-03Z.md). Stage A selectable after capture corrections A1–A3; Stage B blocked by B1–B3 and the owner selections listed there. Next: owner decision on Stage A and the J1 closure standard.


## 2026-11-25 — owner selects J1 closure standard B1 option 1

Slawomir explicitly approved B1 option 1 from review-2026-11-25T00-46-03Z.md (M386069). Offline exact-build lookup evidence may justify the path for staging a credential copy in a later explicitly selected live probe; that observation alone does not close J1. J1 closes only when the selected Stage B run proves authentication using that one staged file. A local login-status check precedes exec, with output private; a wrong path stops before spending the single invocation. No automatic retry or alternative credential source is selected.

This selects the closure standard only. Stage A engine execution/settings, credential source/custodian/copy/refresh/retention, explicit model and live-call authorization remain separate pending selections. Next packet correction follows M386069: A1 connect tracing, A2 offline home metadata, A3 tool presence; B2 reading evidence beyond an echoed digest; B3 resolve the image/tool prerequisite before a live call; source export at ad6dcad0aa38f8ccc17fd6a50bd92bf6f2d8c402. Return exact proposed Stage A commands/settings for execution selection. No product realization/parser, credential access, build, engine or provider operation authorized by this ruling. Recorded by the interactive coordinator; no claim held.


## 2026-11-25 UTC — qualification packet corrected after M386069 (baton.codxpc, planning only)

Prepared [revision 2](evidence/qualification-preparation-r2/README.md), packet `sha256:71c44a1521938308d16a6ddacc1efb2b5075454e418535396738c1fc7caeff87`, archive `cb3e6ac684a1edcf7a1a7133090f7dd945cb81b3f4cfb589d5f018746a24bcdd`; original M386068 packet preserved unchanged. Source is checkpoint ad6dcad0aa38f8ccc17fd6a50bd92bf6f2d8c402, with 1152 v12 blobs pinned for source-export verification. No accepted adapter/shared-file edits. Same ownership allocation M386064; correction notice M386070.

A1 file+connect tracing; A2 home-before/after-version/after-every-phase snapshots; A3 executable git/sha256sum inventory. B1 option 1 uses the approved closure standard: offline lookup allows later selected credential staging, local login status precedes exec, and J1 closes only from authenticated selected live execution with that one staged file. B2 asks for digest plus undisclosed byte count/first line; tool evidence remains observed-only. B3 refuses live execution if git/sha256sum missing and requires owner tool/image choice, with no flag/build/install substitution. Model-shell access to the staged credential is explicitly treated as possible disclosure into private streams.

[Exact Stage A proposal](evidence/qualification-preparation-r2/STAGE-A-COMMANDS.md): operator baton.codxpc, fresh /var/tmp/baton-codex-q1-a-r2, UID:GID1000:1000, retained image17d250b7, network none, read-only root/nonroot/cap-drop/no-new-privileges, 512MiB/1CPU/128pids/128MiB tmpfs, 60s outer bound per phase. First login-help, then login-status only after exact help verifies it. No credential mount. Authorization remains null; no execution selected. Full vectors, staging/cleanup conditions and output bounds retained.

Validation: 39 static checks and 5 mocked control-flow cases; zero engine/probe subprocess, credential read or provider call; no successful turn fixture fabricated. Last discussion read M386070. Next bounded milestone: owner selection of exact Stage A commands/settings; Stage B still awaits path/source/model/tool/image/network/live authorization choices. No claim held or route changed.


## 2026-11-25 UTC — owner selects Stage A execution (baton.codxpc)

Owner explicitly selects M386071 packet71c44a15, retained image, UID:GID1000:1000 and fresh /var/tmp/baton-codex-q1-a-r2, network none, documented bounds/cleanup; login help first, status only if evidenced. No retry/build/pull/credentials/Stage B. Initial claim refused stale decide route; E386072 supported reroute aligned explicit assignment, E386073 claim succeeded. Current handoff read through M386071/E386073. Evidence under evidence/stage-a-execution-386073. The original proposal remains immutable; this entry supersedes only its unselected Stage A state.


## 2026-11-25 UTC — selected Stage A complete (baton.codxpc, E386073)

[Execution report](evidence/stage-a-execution-386073/REPORT.md). Packet71c44a15 unchanged; retained image17d250b7, two phases once each, no retry/build/pull/credentials/provider/Stage B. Login help0 established status; empty-home status1 emitted Not logged in. Observed read-only lookup `$CODEX_HOME/auth.json` returned ENOENT (trace line199). Zero connect calls in these paths only. Home snapshots1→8→8 show transient arg0 startup aliases; workspaces empty. Git absent from PATH; sha256sum/python3/strace present. B3 tool/image prerequisite remains blocked; J1 authentication, schema/refresh/session and N4b remain unproved.

All17 control/setup invocations retained; measured command sum1.849826333s, observation window80.181744s; probe durations approximately0.0501s each. Both containers positively exited then removed; exact no-such-object responses and empty run-label queries verified. Raw streams/traces/metadata/inspect/timing evidence promoted. No protected product/Git changes. Initial stale-route claim refusal corrected through supported unclaimed reroute E386072 under explicit owner assignment before claim E386073.

Next milestone: independent evidence assessment, then owner image/tool/path and later credential/model/live selections; no automatic Stage B. Evidence and image retained; owner checkpoint/backup pending.

Stage A disposition: M386075 reports results; atomic pass E386076 returned W385830 to baton.decide. Fresh detail snapshot386076 confirms Handler null, queued, no pending obligations. Claim E386073 released. Evidence REPORT/manifest remain unchanged; no further execution selected.


## 2026-11-25 — owner-selected interactive product-image preparation

Prepared evidence/product-image-preparation/owner-build.py and /tmp/baton-w385830-product-image.py directly at owner request; see README.md and manifest.json. --check passed; runner and embedded offline probe syntax checked. Exact source checkpoint ad6dcad0, separate W386057 edits excluded. No engine query, build, credentials or provider call performed. Next: owner may select --run for public pull/build and one offline source/tool/version check. Native use, J1 authentication and N4b remain gated.


## 2026-11-25 — actual Codex image build refuses provider_policy COPY

Owner-run product-image packet failed after11.325s with exit1, not timeout. Retained 04-build.stderr at /home/sl/baton-qualification/w385830-codex-product-ad6dcad0-1 shows COPY python/src/baton_v12/provider_policy refused. The directory exists in the exact committed ad6dcad0 export, but v12/.dockerignore omits its re-include. This is a product build-context defect, missed by the preparation preflight; source-only recipe checks did not establish buildability. It also affects any recipe copying this package with that context. Required product correction: include exactly python/src/baton_v12/provider_policy before cache exclusions and preserve exclusion of bytecode. No broad context widening.

Read-only engine checks after failure: the helper's exact temporary image tag is absent and no product-probe container bears this run label. This is not a claim that all legacy-builder intermediate containers or dangling layers were removed. Logs show ordinary synchronous build failure and no timeout/cleanup exception. No automatic retry, pruning or protected Git mutation.

Interactive coordinator prepares revision2 using a fresh run root and an explicit, retained build-context-only .dockerignore patch in the exported source. This is a disclosed qualification stopgap pending product correction/review/checkpoint; it does not silently amend accepted source or enable native use. The first packet and run remain intact.

Next owner command: python3 /tmp/baton-w385830-product-image-r2.py --check, then --run if selected. No product source bytes changed by preparation.


## 2026-11-25 UTC — build-context correction reviewed and imported, checkpoint pending (baton.prompt)

One-line `v12/.dockerignore` re-include of `python/src/baton_v12/provider_policy` accepted: [review](review-2026-11-25T01-12-48Z.md). Imported on `ad6dcad0aa38f8ccc17fd6a50bd92bf6f2d8c402` (before `b7da7ead…`, after `04e364e4…`), coordination M386077, record `evidence/import-dockerignore-04e364e4/IMPORT.md`. Human checkpoint pending: `/tmp/baton-w385830-dockerignore-checkpoint.py`, message `Allow provider_policy into the worker image build context`; commit identity to be recorded once observed. Follow-up noted, not selected: a deterministic test that every worker-recipe COPY source is reachable through the allowlist. Image `46a46ee4…` is B3 tool evidence only; J1, N4b, qualification and native use stay gated.


## 2026-11-25 UTC — checkpoint c1727ad6 observed; credential lifecycle candidate reviewed (baton.prompt)

Human checkpoint observed: `c1727ad68ffa0f5015b07f27202a66be00848143` "Allow provider_policy into the worker image build context". Candidate `sha256:7f45e1e53d5f4608123cb8f6dba9ec9a701f6b5f89ac4c7e65ad0660eb6066b8` reviewed: [review](review-2026-11-25T01-46-59Z.md). Accepted for import for seven paths; C1 excludes `v12/DESIGN.md` (owner applies or approves that paragraph); C2 (first-start failure and recovery procedure) and C3 (4,096-character delivery bound) are due before a Codex realization selects seeded-retained. Ownership request M386082/M386084 answered there. Next: owner decision on C1, then exact import and checkpoint.


## 2026-11-25 — credential lifecycle draft ready for independent review (baton.codxpc)

Current bounded milestone: independently review candidate `sha256:7f45e1e53d5f4608123cb8f6dba9ec9a701f6b5f89ac4c7e65ad0660eb6066b8`, 8 product/doc/test paths on c1727ad68ffa0f5015b07f27202a66be00848143 plus the separately pinned inherited DESIGN before-image. [Report](evidence/credential-lifecycle-386081/REPORT.md), [ruling and acceptance](evidence/credential-lifecycle-386081/RULING-AND-PLAN.md), [successor qualification launcher](evidence/credential-lifecycle-386081/qualification-successor/README.md). Focused manager-pure/tools-pure selection: 314 collected/executed/passed in22.036232572s, no skips/unaccounted/drift. No broad group/full-suite/engine/build/provider execution.

Ownership: M386082/M386084/M386085 proposed shared allocation and isolated fallback. K reply pending; main product and existing dossier files untouched. Candidate includes proposed exact append content here, not an asserted imported amendment. Before import confirm ownership and current target bytes; preserve inherited DESIGN paragraphs, K image files and W386057 isolation changes. No overlap edits or owner Git operations delegated. After independent acceptance, exact coordinated import and human checkpoint remain pending. Suggested commit: `Initialize retained provider credentials once and preserve refresh on restart`.

Remaining selections: original credential source/configuration and access, model, image/tools and live execution. J1/N4b and native activation remain gated. The successor copy launcher is implemented, but Stage B still requires a separately reviewed image/tool execution choice; original image17d250b7 lacks git. No live success or native-use claim.


## 2026-11-25 — accepted credential lifecycle imported

Interactive coordinator imported seven exact accepted paths from7f45e1e5 after whole-set drift/type/mode preflight and applied only the owner-approved DESIGN paragraph, linking FINDING. Prior42 DESIGN lines and W386057 edits preserved. Seven final hashes/modes verified; no tests rerun on the mixed host tree. Independent314/314 evidence at review-K-386086 remains applicable to those exact bytes; this is not joined/full-suite qualification. Human checkpoint script is evidence/import-7f45e1e5/owner-checkpoint.py, copied to /tmp/baton-w385830-credentials-checkpoint.py. C2/C3, J1/N4b and native activation remain gated.


## 2026-11-25 — owner selects qualification model and credential-copy source

Slawomir explicitly selected gpt-6-astra as the qualification explicit_model, matching the model-related setting read from codexpc config.toml. Earlier in this conversation he authorized the qualification launcher to automatically copy /home/sl/.codex-pushcoin/auth.json into its private retained home, leaving the source unchanged. Reference: codex-pushcoin-subscription; custodian Slawomir. No credential file was read or copied by the coordinator.

Current editable selection draft: config/qualification-selection.json, based on the accepted lifecycle successor template. explicit_model is set; live/offline execution authorization fields remain null, as do unresolved placement/refresh/retention/settings. Existing image/source defaults in that draft are historical template values, not newly selected image/runtime authority; the final launcher must reconcile them with accepted product-image evidence and committed lifecycle source before execution. No live model call authorized. Reasoning effort was not separately selected by this model decision.


## 2026-11-25 — owner requests configurable Codex fast mode

Owner requests a way to enable fast mode explicitly through configuration. Add a separately selected service_tier beside explicit_model; the interactive coordinator added a null field to config/qualification-selection.json to record the unset selection, not runtime support. Current CLI documentation describes service_tier=fast via -c; exact pinned0.169.0 support and request behavior remain to be qualified. No fast mode or live call was selected by this capability request.

Bounded implementation requirement: optional fast tier must be carried from JSON through validated adapter configuration into the exact argv (Codex -c service_tier="fast"), with identity binding, consistent qualification launcher rendering and requested-tier reporting. Unset preserves existing behavior; do not describe unset as proved Standard. Reject unsupported configured values; do not infer actual tier from requested configuration. Preserve legacy identities/behavior when unset if feasible, otherwise disclose the admission compatibility consequence. Tests should prove forwarding, refusal and unchanged unset behavior; help or mocked evidence is not proof the server honored fast mode. Update owning contract/DESIGN consistently before product implementation. Coordinate with codexpc current qualification packet and avoid a separate unrelated feature expansion.


## 2026-11-25 UTC — optional service tier candidate ready for review (baton.prompt)

Owner-selected slice, coordination M386089. Candidate `sha256:9c365d72625de16e193198d2f1938d82cc51cedad59d3dd54f1cd259db66c458`, eight paths on `1ed26970e74ea48013e3e533e057e6ace08d0058`: [report](evidence/service-tier-386089/REPORT.md). Selected `fast` forwards `-c 'service_tier="fast"'` for Codex 0.169.0, is bound into selection, runtime profile and adapter identity; unset is byte-identical; requested is recorded, observed is never inferred. 604/604 focused. Not verified: that 0.169.0 recognizes the key (retained help evidences only `-c key=value`). Launcher lines for codexpc: `evidence/service-tier-386089/LAUNCHER-DELTA.md`. Next: independent review, then import and human checkpoint. No live call; no tier selected.


## 2026-11-25 — independent service-tier review and successor preparation (baton.codxpc, E386092)

Owner selected independent review of K M386090 and a credential-free offline proposal, with no engine/provider execution. [Review](review-2026-11-25T02-52-55Z.md) accepts exact candidate `sha256:9c365d72625de16e193198d2f1938d82cc51cedad59d3dd54f1cd259db66c458` (8 paths, base1ed26970e74ea48013e3e533e057e6ace08d0058) for owner import/checkpoint, not native qualification.604/604 independently collected focused tests passed in61.768519333s, with no skips/unaccounted/source drift. Independent unset snapshots match byte-for-byte. Candidate and main product unchanged.

[Successor packet](evidence/qualification-tier-386092/README.md), `sha256:8b9c0492453d2c574d81b4f90ca36008b91625d1eabd4187b0925651aa68323d`, applies LAUNCHER-DELTA only in new files, carries automated credential copying and pins the exact base plus reviewed overlay.29 static/mocked checks, two source-only context generations and code-only lifecycle pin check pass. Requested-tier metadata must match actual argv. No prior packet was altered.

Correction to the offline-evidence interpretation in M386090: exit0 or help acceptance cannot establish service_tier recognition; unknown overrides may be ignored and help may bypass loading. No authoritative effective-config surface or exact-build loader proof is retained. [Offline proposal](evidence/qualification-tier-386092/OFFLINE-CHECK.md) provides exact network-none help discovery and the required typed-effective-config/unknown-key/ignore-user-config matrix. The effective-config command remains unresolved until exact-build help/source proves one; no guessed diagnostic or exec turn is selected. Recognition, effective requested config, and actual served tier stay distinct; fast is not selected.

Current FINDING source/model selections are preserved; none were read/used for credentials or provider execution. Lifecycle C2/C3 remain open before Codex activation. J1/N4b/native use, W386048 and W386057 remain separate.

Next bounded milestone: owner imports/checkpoints the accepted exact service-tier candidate; separately select the concrete offline help-discovery packet/settings if wanted. No engine/live authority follows from this acceptance. Source/model already selected in the prior ruling; execution settings, image/tool reconciliation, private retention/refresh disposition and later native credential gates are still required. Suggested commit: `Add optional provider service tier to selection, Codex adapter and attribution`. Current reviewer last read M386093/E386092; final result and atomic release follow on T385830.


## 2026-11-25 — owner-selected interactive service-tier import

Slawomir asked the interactive coordinator to handle the accepted import here. Imported exactly eight paths from9c365d72 after whole-set candidate/archive/base/drift/type/mode preflight. Independent acceptance M386094 (review-2026-11-25T02-52-55Z.md),604/604 focused checks. Final eight hashes and modes equal reviewed bytes; no reruns on the host with unrelated W386057 edits. DESIGN and other source edits preserved. Evidence/import-9c365d72 contains preflight/postflight and human-only selective checkpoint script. No protected Git mutation, image/build/engine, credential read or provider call. This accepts configuration/forwarding only: pinned CLI recognition, actual served tier, C2/C3, J1/N4b and native qualification remain open. Current draft service_tier=null is not selection of fast mode; successor maps unset to omitted product field. Next milestone: human checkpoint, then the bounded qualification successor, not additional feature scope.


## 2026-11-25 — qualification next offline packet (baton.codxpc, E386097)

Observed human checkpoint f875ed01b51b6b7541ad169b560004e47731ad34; all eight service-tier candidate paths match accepted9c365d72 exactly. This supersedes the pending tier-import/checkpoint status above. [Bounded packet](evidence/qualification-next-386097/REPORT.md), `sha256:451a4f08983e1643c7626616a898b20979b9a12b76871cad9ba9a82086cd90e0`, carries gpt-6-astra and the already selected codex-pushcoin-subscription automatic first-copy source; source unchanged, refreshed retained copy preserved, no silent re-seeding. Fast remains unselected. No product or earlier packet edits.

Next executable milestone, pending execution selection: exact credential-free help-discovery in retained17d250b7 image, network none, UID:GID1000:1000, fresh /var/tmp/baton-codex-tier-discovery-386097. Exact commands/settings, discovery-versus-recognition pass/unknown rules and bounded cleanup are in the packet. No authoritative typed effective-config diagnostic is yet established; exit0/help/schema alone cannot close recognition. No engine, builds, credential reads or provider calls performed. 54 source/static packet checks passed; prior604/604 product evidence reused, not rerun.

Only remaining combined-live choices: proposed runtime/image/placement settings (46a46ee4 CLI/tool image, f875 host-generated detached harness, not older image worker code), private registry/custody/refresh disposition and subscription attestation, then explicit live/network execution selection. Model and source/copy do not need reselection; no fast or reasoning override proposed. Exact live renderer reconciliation is a mechanical prerequisite before execution, not an invented selection or a runnable claim in this offline packet. J1 requires authenticated same-run success after local status; N4b requires actual turn/contributor evidence, with role/instruction digest checked in that single turn. C2/C3/native activation, W386048 and W386057 stay separately gated. Ownership notice M386098; last incoming discussion M386094, canonical scope E386097.


## 2026-11-25 — selected live evidence available

Next bounded milestone: consume evidence/live-probe-prompt/REPORT.md and RESULT.json, retain sanitized exact-build turn/session fixtures from the private root, then implement and verify N4b terminal/contributor parsing. No further live call selected. J1 authenticated-success criterion met for this probe; CLI-context versus backend-model attribution distinction must remain explicit. Native qualification and C2/C3 remain open.


## 2026-11-25 — bounded N4b terminal interpretation selected (baton.codxpc)

Owner confirms M386103: implement observed terminal parsing with explicit missing attribution; turn_context.model is configuration/context diagnostic only, never contributor evidence. Contributor requirement and acceptance hold remain unchanged. E386104 routes, E386105 claims, M386106 confirms K ownership. Independent candidate at f875ed01; Codex adapter, dedicated tests/fixtures and Codex provider documentation allocated. No shared Claude edit planned; no DESIGN/W386057 edits. Retain sanitized exact-build fixtures only; private raw sessions and credentials remain outside repository. Focused manager-pure/tools-pure verification; no provider/build/native execution. Current milestone: complete bounded candidate for independent review; attribution participation gap and native qualification remain gated.


## 2026-11-25 — bounded N4b candidate ready (baton.codxpc, E386105)

Completed eight-path candidate `sha256:5539eef92754e69d38e93c79abd6e020f9ed5368cc0b23f423beb9fc8da5fbe1` on f875ed01b51b6b7541ad169b560004e47731ad34. [Report](evidence/n4b-386105/REPORT.md), archive/manifest and sanitized exact-build fixtures retained. Owner-confirmed M386103, routing E386104 and ownership M386106 consumed; last thread read through M386106. Terminal completion recognized only for the observed complete bounded event family. Codex contributor evidence remains explicitly missing; turn_context.model is not participation, and host acceptance stays held. No production realization, session reader, resume, fast selection, Claude worker edit or protected source import.

Final focused manager-pure/tools-pure selection:380/380 collected/executed/passed in37.196738566s, no skips/unaccounted/drift. First380/380 run in37.297730094s retained but superseded for a concurrent documentation change/source drift; total74.494468660s, no broad group/full run. Twelve Claude attribution snapshots byte-identical to base. Five isolation inputs inherited in disposable source only and excluded; fixture root empty, private evidence/home preserved. No additional provider/build/engine/native operation or credential read.

Next milestone: independent exact-byte review of the complete bounded candidate, then owner import/checkpoint. Pending suggested commit: `Parse evidenced Codex terminal completion while holding missing attribution`. Actual participation source remains a concrete acceptance gate; native realization/image/combined pipeline qualification, C2/C3, shared-login refresh and explicit Claude qualification remain open. Fast and resume stay unselected; W386048/W386057 remain separate.


## 2026-11-25 UTC — N4b candidate reviewed (baton.prompt)

Candidate `sha256:5539eef92754e69d38e93c79abd6e020f9ed5368cc0b23f423beb9fc8da5fbe1` accepted as source for its bounded claim: [review](review-2026-11-25T03-29-39Z.md), evidence `evidence/review-K-386107/`. 380/380 reproduced outside the checkout. C1 (split on the newline byte only) recommended, fails closed, not blocking. Seven native-qualification gates listed there; the first practical one is that the parser knows only the single observed turn shape, so a file-editing turn would be unclassified. The attribution decision (no participation source in 0.169.0 output) is recorded separately for Slawomir and not decided. Next: owner import and checkpoint of the eight paths; then the attribution decision.


## 2026-11-25 — accepted N4b imported; human checkpoint pending

Exact eight-path candidate 5539eef9 imported under owner direction, review M386109. See evidence/import-5539eef9/IMPORT.md. Checkpoint script /tmp/baton-w385830-n4b-checkpoint.py. No native activation; attribution decision and C1 remain open. Next implementation is not assigned by this import.


## 2026-11-25 — N4b human checkpoint observed

Owner checkpoint 99b69626a44e806860abadc2854920914f1cf0dc contains all eight accepted candidate 5539eef9 paths byte for byte. This supersedes the pending checkpoint above. Native activation remains gated on participation evidence and remaining qualification. Next bounded milestone: offline investigation of authoritative participation evidence; no additional live call or attribution relaxation selected. C1 remains a separate recommended correction.


## 2026-11-25 — offline participation investigation (baton.codxpc, E386111)

Observed N4b checkpoint99b69626a44e806860abadc2854920914f1cf0dc and consumed K acceptance M386109. [Report](evidence/participation-386111/REPORT.md), evidence packet `sha256:ffdead6647a64d9e71ba3a2068d91fae433c70e71960f4399422c0a0d89194e7`. Inspected selected seven-event stdout and25-record session structurally, preserving private content. No actual-participation model field established. Additional model mentions are base-instruction provenance, world-state/collaboration settings and thread_settings_applied; they do not supersede M386103. Two token_usage_record entries have distinct response IDs and a common turn ID, but neither names a model. Proposed future binding requires each actual service receipt plus attempt/candidate and host-revalidated evidence, never configuration substitution.

Local installed package is0.172.0, not executable proof for0.169.0. Local app-server schema has an unqualified model/rerouted lead, not exact-build provenance or actual-generation semantics; client attestation is not backend attribution. Exact-build source/export semantics and private provider-store contents remain unestablished/uninspected. Do not turn this bounded absence into a claim that the binary exposes no source anywhere.

Next bounded milestone: review evidence gap, then separately select the prepared credential-free pinned-image version/app-server-help/debug-help probe or exact-build source inspection. Prefer supported offline export of the existing responses; authenticated existing-response retrieval only if supported and explicitly selected; a new turn only after proving a diagnostic can capture the missing service field. No new turn recommended merely to repeat stdout. Product unchanged, no tests rerun, no engine/build/network/provider operation or credential-content read. Attribution stays missing; native activation, C1 and all other qualification gates remain unchanged. Last incoming discussion M386109; scope notice M386112.


## 2026-11-25 — pinned offline diagnostic discovery completed

See evidence/participation-offline-prompt/REPORT.md. Version and app-server/debug help passed; network disabled, no credentials/provider calls, container removed. Exact-build schema generation is supported; response retrieval/participation still unestablished. Next: deeper offline help and exact-build schema inspection, with no attribution relaxation.


## 2026-11-25 — exact-build deeper help complete (baton.codxpc, E386116)

[Report](evidence/participation-help-386116/REPORT.md), packet `sha256:62d29d7b9b2d6300b3d3623b0c10fe1decdc5d4b43bd7b9509a9e870632c42a3`. Retained17d250b7 image: Codex0.169.0 version and generate-json-schema/debug app-server help passed once each offline. Zero connect syscalls observed, network none enforced, no credentials/model/daemon; exact container ceased/removed and label absent. Source unchanged.

Documented export prepared only: `codex app-server generate-json-schema --experimental --out /schema`, proposed fresh64MiB schema tmpfs, empty home, same pinned image and bounds. Latest owner wording selects preparation, not export execution. Debug lists send-message-v2 only; no retrieval established. No actual model-participation field was exposed by help; exact-build schema/semantics remain pending. Configuration fields never count; current attribution missing/acceptance held unchanged.

Next bounded milestone: select offline schema export and inspect actual response/model fields, requiring service-origin generation semantics and response/turn/attempt binding before any participation change. No live call or native activation. Scope notice M386117; last canonical handoff E386116/M386113.


## 2026-11-25 — exact-build schema export completed

See evidence/schema-export-prompt/REPORT.md. Offline export passed and container removed. RawResponseCompletedNotification provides response/turn correlation and opaque upstream usage metadata, but no documented model identity. Next bounded research: establish exact-build origin/access/retention semantics for that channel; no further live call selected. Attribution remains missing.


## 2026-11-25 — usageMetadata access/retention trace (baton.codxpc, E386121)

[Report](evidence/usage-metadata-386121/REPORT.md), packet `sha256:6bd7a15d9620bd72acbe670e2db4f9c98b3098cfca3b04a5ad52a43b84b420fd`. Verified all479 exact-build schema files. Internal-only RawResponseCompletedNotification has optional nullable opaque usageMetadata, no declared model field. Neither the86-method ServerNotification union nor184-method ClientRequest union references it; schema export does not establish a callable/subscribable/replayable method. experimentalApi is not an evidenced internal-channel opt-in. Runtime metadata construction/emission control flow remains unavailable without matching0.169.0 source/provenance.

Resolved prior uninspected status for three selected private provider stores through immutable read-only forensic checks (no nonempty WAL/journal, bytes/mtime unchanged): history has one selected turn/four items with no model/usage/response-ID fields; state holds configured selector only; logs has zero rows. Both rollout response-linked usage records omit usageMetadata and model. No private rows/IDs/prose copied, no credential or Baton-store reads. Cannot recover actual model identity for existing responses through inspected retention or any established supported operation. Do not infer global backend absence or which runtime stage omitted metadata.

Current attribution missing/acceptance held unchanged. Next bounded milestone: matching exact-build source/provenance trace of constructor, upstream decoder, notification filtering and persistence/supported reader. No new live call, network, daemon, engine, build, product edit/test or attribution relaxation. Scope notice M386122, last incoming discussion M386118, canonical E386121.


## 2026-11-25 — final exact-build source trace (baton.codxpc, E386126)

[Report](evidence/source-provenance-386126/REPORT.md), packet manifest SHA256 `4569091bc8f5e2e320103471c433ac9b51956c2c46fe5d054f708d83052209bd`. Official release/npm provenance resolves Codex0.169.0 to source d32063f96c2dff1dc96af839b3952abb6acfeda4; retained17d image binary exactly matches published platform package (SHA256 b452ca20f838a8855a88a41050ee4a694033fff4ea3ecdad5633e6e0e8d13f2b). Signature verification/reproducible rebuilding not performed; official content/provenance correspondence established. Relevant source retained verbatim.

Supersedes earlier runtime-unavailable uncertainty: rawResponse/completed is emitted internally to connected clients and deliberately stripped from exported JSON unions, not absent from runtime. usageMetadata holds opaque usage/cost metadata, overwritten with raw usage when present; no model semantics. Rollout explicitly excludes raw completion; persisted usage records lack model/metadata; exec JSON drops it. Separate ServerModel consumes server model headers, ignores response.model, logs matches and emits only mismatch notices, with no complete per-response contributor binding. Existing retained responses remain without qualifying attribution. Absence of reroute is not participation proof.

Final bounded investigation complete. Next milestone is owner attribution decision; S7 and acceptance hold unchanged, no further research/live probe selected. No product/build/provider/credential operation or protected Git mutation. Byte-copy container never started, removal verified; public scratch retained, durable evidence promoted, private home untouched. Last incoming thread M386123; scope M386127. Other native gates and separate work unchanged.


## 2026-11-25 — owner-approved bounded Codex attribution change (baton.codxpc, E386131)

Owner explicitly approves configured-model acceptance for the bounded Codex path: record requested model, exact executed invocation/configuration and CLI/image identity; never present configuration as actual participation. Missing required evidence or observed mismatch/reroute refuses. Report no reroute observed, never rerouting proved absent. Other providers retain stronger contributor evidence. This supersedes prior Codex-only participation-presence acceptance holds (S7/N4b/M386103 and final investigation), not contributor semantics or Claude requirements. Existing accepted code/evidence is not retroactively relabelled.

[Amendment and implementation/acceptance plan](evidence/attribution-amendment-386131/AMENDMENT.md) and exact DESIGN.patch/proposed bytes prepared for independent review and Slawomir checkpoint before implementation. Shared DESIGN not edited because it contains other work; owner/K application ownership preserved, M386132. Attempt to include baton.prompt refused (no live endpoint); plain owning-thread coordination retained. No runtime implementation, test run, provider/credential call, native activation or Git mutation. Current code remains fail-closed until reviewed delivery. Next milestone: review amendment, apply narrow hunk under shared ownership, observe human checkpoint; then implement bounded paired worker/host evidence semantics and A1–A10 checks. Other native gates and separate Work remain.

## 2026-11-25 — K review of the Codex attribution amendment (M386133)

[Review](review-2026-11-25T04-49-35Z.md): amendment and DESIGN hunk accepted as faithful to the owner ruling; patch verified against current shared DESIGN bytes (`8a7b4a5d…` → `c9f1611e…`), shared file untouched. Required before the implementation candidate is reviewed: R1 unqualified-but-consistent build refuses, R2 host-derived basis (claimed basis or Codex contributors refuse), R3 observation surface named with the "no reroute observed" rule. Next: owner applies the single hunk and checkpoints it apart from the 42 existing uncommitted DESIGN lines; implementation follows the observed checkpoint. No claim held.


## 2026-11-25 — configured-model DESIGN checkpoint observed

Owner checkpoint b5ca8e12eac41c93c6a9f115a480f8ce32e04f15 contains the exact accepted narrow DESIGN amendment and evidence; index snapshot matches and unrelated DESIGN edits were excluded. Required R1–R3 and C1 are in evidence/import-attribution-amendment/ACCEPTANCE-ADDENDUM.md. Next bounded milestone: implementation under canonical claim/ownership, followed by focused verification and independent review. No provider call or native activation selected.


## 2026-11-25 — configured-model attribution candidate (baton.codxpc, E386137)

Observed owner checkpoint b5ca8e12eac41c93c6a9f115a480f8ce32e04f15; consumed accepted amendment M386135 and R1–R3/C1 addendum. [Report](evidence/attribution-386137/REPORT.md). Complete 12-path candidate `sha256:79b648fed4c6e2cb5abb40948fd8bc0089c249dd83143dfb7a5e83041332c4e1` retained with exact archive/manifest/diff. Independent disposable source only; shared product targets still match checkpoint. M386138 coordinates candidate ownership; K/owner retains shared import, no overlapping edit performed. Five inherited isolation prerequisites retained separately and excluded from candidate.

Codex /2 configured-model basis is selected by admitted provider, bound to exact measured build/image/selection and separately retained content-free invocation receipt; actual participation unknown, contributors empty. Unqualified consistent build refuses. Host reparses complete supported stdout and checks receipt; known source-defined reroute error refuses, silence means only no reroute observed. LF-only parser includes C1. Existing Claude /1 participation and legacy behavior remain. Original producer evidence survives recovery and real deterministic Codex-to-Claude pipeline checks; missing Claude contributors still block verdict. No production realization/image/native activation enabled.

Final focused verification:626 collected/executed/passed in43.752878s, zero skips/unaccounted/source drift, groups manager-pure/tools-pure/job_manager. All logs/ID ledger/header/source identities retained. Prior624-case runs had2 new pipeline failures then1 stale metadata-fixture error, corrected without baseline waiver;132.612843s across three accounted runs. Developer smoke evidence/limitations described in report. Fixture root empty; no real credentials/provider/build/engine/native operation or protected Git mutation.

Next bounded milestone: independent exact-byte candidate review, then owner import/checkpoint under shared ownership and target drift preflight. Proposed commit: `Accept labelled Codex configuration evidence with retained invocation binding`. Native image/realization, expanded observed task shapes, joined native qualification, shared-login/refresh and explicit Claude gates remain. Current shared source remains pre-candidate; no historical evidence relabelled. Last incoming M386135; read through scope M386138.

## 2026-11-25 — K review of configured-model candidate 79b648fe (M386139)

[Review](review-2026-11-25T05-07-27Z.md): accepted as source for owner import/checkpoint on b5ca8e12; 626/626 reproduced outside the checkout; R1–R3 and C1 confirmed by probe; Claude /1 records byte-identical to base. Open limits: F1 image identity is the admitted profile value, not launch evidence; F2 CLI build is adapter-reported. Follow-up C2–C4 recommended. Native gates unchanged apart from the attribution basis. No claim held; import not prepared (not selected).


## 2026-11-25 — configured-model implementation imported

Owner selected exact-byte import here; candidate 79b648fe accepted M386141. Twelve paths verified and imported; checkpoint pending via /tmp/baton-w385830-configured-checkpoint.py. See evidence/import-79b648fe/IMPORT.md. F1 launch-image binding and remaining native gates stay open; C2–C4 remain recommended follow-up, not silently corrected during import.


## 2026-11-25 — checkpointed attribution; finite native-readiness route (baton.codxpc, E386143)

Observed d0760de6acdf9cd1e055d1f08137757adb223cc0: all12 accepted79b648fe bytes match; codex parser100644. Consumed M386141 review, canonical through E386143; scope M386144. [Bounded readiness plan](evidence/native-readiness-386143/PLAN.md), checkpoint verification retained alongside. No source/runtime operation or test executed.

F1 is first: prior candidate accounts bind image to admission only, not retained launched-image observation. This corrects any reading of the earlier implementation entry as proving engine image identity. oci.py:1634 compares selected values; list validates engine image then drops that field in its returned record. I1 retains host engine/runtime/attempt/start/image evidence and binds it to attribution and original-producer recovery, with separate admitted/observed diagnostics. No backend attribution research or relaxation.

Finite dependencies: I1 image binding → I2 production realization/home and credential-C2/C3 decisions/corrections → selected Q1 build/offline image gate → selected Q2 one editing capture → I3 observed parser fixtures/completion → selected Q3 final image → selected Q4 Codex implementation/Claude review/verdict. Three new provider calls proposed on the main route, none authorized now, no retries. Reuse authentication/instruction/path/source/model evidence; preserve adapter-reported CLI and unknown actual Codex contributors, stronger Claude evidence. Exact reviewed/checkpointed code required at each implementation boundary.

Open decisions: explicit failed-initialization recovery semantics; unified file credential size/representation; engine/build/live packets and Claude selection if unsettled; placement of separately bounded refresh/shared-login qualification. Shared-login or actual refresh is not proved by the first two-role Job or synthetic tests and remains an explicit unqualified scope, not silently waived. W386048 remains separate: prior M386046 says optional provider-selected integration is unnecessary for the selected two-role review/verdict endpoint; no integration call added. Review-C2/C3/C4 have finite ordinary dispositions in the plan. Fast/resume/W386057 remain separate.

Next milestone: review this packet and route I1 ordinary implementation under fresh claim/shared ownership; D1/D2 decisions precede dependent I2 changes. This planning claim does not implement or activate any step. No shared-file reservation, real credential read, build, engine/provider call, protected Git mutation or native activation.

## 2026-11-25 — K review of the native-readiness plan (M386145)

[Review](review-2026-11-25T05-15-41Z.md): plan accepted with amendments P1 (receipt requirement Codex /2 only), P2 (engine-sourced digest binding), P3 (Q2 boundary named, native attempt preferred), P4 (offline Claude-qualification inventory before Q4). First executable slice: I1. Owner decisions pending in order: D1, D2, shared-login placement, Claude reviewer model/source if unsettled. W386048 is not a prerequisite of the two-role route (corrects gate 5 of review 05-07-27Z). No claim held.


## 2026-11-25 — owner approves D1 and D2 (baton.codxpc, E386151)

The owner explicitly approves both credential-policy decisions. This supersedes
prior entries describing D1/D2 as unresolved, including the native-readiness
plan; it does not authorize I2 implementation before its checkpoints.

D1: explicit audited recovery may withdraw a failed first-initialization receipt
only if initialization never succeeded, the retained home is verified unchanged,
and no runtime can write. Otherwise retain the hold and evidence. Preserve the
original receipt and the recovery decision as audit history. No automatic reset
or reseeding is selected; withdrawal itself grants neither credential access nor
runtime launch. Successfully initialized homes retain refreshed credentials and
must not depend on the original source on restart. Missing credentials after
successful initialization remain an explicit recovery condition.

D2: subscription-login files have one consistent 1,048,576-byte maximum, including
qualification copy paths. Preserve exact bytes; do not decode, normalize or
re-encode them. Legacy token limits remain unchanged. Required synthetic checks:
1,048,575 / 1,048,576 / 1,048,577 bytes, multibyte content counted in bytes,
byte-identical accepted copies and secret-free refusals.

[Narrow DESIGN amendment](evidence/credential-policy-386151/AMENDMENT.md) is
prepared separately from pre-existing shared DESIGN edits for review and owner
checkpoint. I1 continues independently under accepted P1/P2 and confirmed file
ownership. I2 requires I1 acceptance/checkpoint and the credential-policy
checkpoint. No engine, provider call, native activation or real credential read
is selected by these rulings. Ownership request M386152 remains outstanding.


## 2026-11-25 — credential-policy packet and I1 ownership checkpoint (baton.codxpc)

E386151 claim; current handoff/discussion consumed through M386153, canonical
work events through E386151. Owner D1/D2 ruling pinned above. Exact amendment
packet manifest sha256:291813564c9481a042a921999119d90dbbc8fc532b6bc5c3194fd296fa549416;
[amendment](evidence/credential-policy-386151/AMENDMENT.md), CHECK.json and
DESIGN.patch retained. Patch reproduction passed; shared DESIGN unchanged.
No tests, engine operations, credential reads or provider calls executed.

I1 implementation is incomplete: M386148 allocation and asynchronous directed
ownership request M386152 await K confirmation. Read-only preflight identifies
OCI start as a closed runtime_id/labels return, OCI observe as the engine-fact
boundary, attempts._observed as a state/why consumer, and model_attribution as
the durable result/recovery consumer. Do not add receipt fields to start without
updating its paired contract. P1 limits the new hold to Codex /2; P2 requires
engine-derived digest resolution. No implementation files edited or candidate
created. Independent work completed here is the approved D1/D2 policy packet.

Return through baton.bug for narrow amendment review and ownership response;
then route I1 back to baton.codx for a fresh claim and complete bounded candidate.
This is an ownership gate, not a new scope/engine approval request. I2 remains
after I1 acceptance/checkpoint and the credential-policy checkpoint. Suggested
policy commit: `Specify audited credential initialization recovery and file byte limit`.

## 2026-11-25 — K review of D1/D2 amendment and I1 ownership (M386153, M386152)

[Review](review-2026-11-25T05-23-23Z.md): SEC-2 hunk accepted as faithful to the D1/D2 rulings; patch verified against current shared DESIGN (`c9f1611e…` → `91bd29af…`), not applied. I2 acceptance additions X1 (all four enforcement points of the byte bound), X2 (withdrawal replay and new receipt), X3 (zero-length refusal). I1 allocation of M386148 confirmed free; boundary is the six uncommitted paths (DESIGN and the five W386057 paths). W385830 currently routed to baton.bug review; reroute to baton.codx may be needed for the I1 claim and was not performed. No claim held.


## 2026-11-25 — I1 candidate complete (baton.codxpc, E386158)

[Report](evidence/i1-386158/REPORT.md). Complete 11-path candidate
`sha256:e3656475c5594b7b1a350cdba2f1d6252a42e4da4323ce691148d50665261ccd`
on d0760de6acdf9cd1e055d1f08137757adb223cc0, with exact archive, manifest,
diff, accounted logs and cleanup check retained. M386155 confirms allocation;
shared import belongs to K/owner. All shared import targets remain unchanged.
DESIGN and the five W386057 paths were not edited; the latter were used unchanged
as separately retained verification prerequisites.

I1 retains engine Id/Image/StartedAt and generation-bearing assignment labels,
engine-derived registry-digest resolution, host journal reference/digest and
original-producer result/recovery binding. P1: Codex /2 alone requires the new
receipt; Claude /1 and legacy behavior remain. P2: mapping is engine evidence,
not a profile/worker echo. Review-C2 diagnostics now label unknown/unqualified
surfaces honestly. Actual Codex contributors remain unknown. A conflicting
observation holds current acceptance without rewriting the frozen assessment;
missing receipt does not delay cessation/token release.

Final focused run:884/884 collected/executed/passed, zero skips/unaccounted/drift,
48.755065s; manager-pure/tools-pure/job_manager. Six accounted development runs
total200.114100s, with all intermediate failures retained and corrected; no
baseline waiver. No full suite or real engine/provider/build/credential/native
operation. Fixture root empty and removed; no protected Git metadata mutation
or cleanup. No new module registration needed: tests extend existing modules.

Next milestone: independent exact-byte I1 review, then owner import/checkpoint.
Suggested commit: `Bind Codex attribution to retained launched-image evidence`.
I2 still requires I1 acceptance/checkpoint and credential-policy checkpoint;
M386155 X1–X3 are retained acceptance obligations. D1/D2 approval does not
select I2 early. Remaining native route and P3/P4 are in the report and
[evidence/native-readiness-386143/PLAN.md](evidence/native-readiness-386143/PLAN.md).
No native qualification claim; W386048/W386057, fast and resume remain separate.
Canonical incoming discussion consumed through M386157; claim E386158.

## 2026-11-25 — K review of I1 candidate e3656475 (M386159)

[Review](review-2026-11-25T05-41-23Z.md): accepted as source for owner import/checkpoint on d0760de6; 884/884 reproduced outside the checkout; F1 closed at source level, P1/P2 and review-C2 confirmed. No correction round. Limits for Q1: no real engine asked, Podman bare image id, resolution branch unexercised, F2. Follow-ups C5–C8 recommended with I2. Import not prepared (not selected). No claim held.


## 2026-11-25 — combined I1 and D1/D2 checkpoint pending

Accepted I1 e3656475 and credential-policy amendment imported exactly. /tmp/baton-w385830-i1-checkpoint.py checkpoints both, excluding unrelated DESIGN edits. See evidence/import-i1-credentials/IMPORT.md. I2 starts after observed checkpoint, under canonical claim and ownership; no engine/live selection implied.


## 2026-11-25 — combined checkpoint verified

Owner checkpoint 2d9a1f5afd84bfdcef461798d2418be3e6d65a9d contains the eleven accepted I1 paths, narrow D1/D2 DESIGN amendment and pinned evidence exactly. Both I2 checkpoint gates are satisfied. Next bounded milestone: complete I2 production mapping and credential fixes through focused verification and independent review under canonical claim/ownership. Address applicable I1 follow-ups within that scope, escalating only genuine policy ambiguity; no engine, build, real credential or provider access selected.


## 2026-11-25 — I2 ownership response pending (M386167)

Independent preflight/baseline complete; no implementation edit or I2 candidate
exists yet. M386162/M386166 and poke386163 received no reply through M386166.
M386167 is a supported directed ownership request to review, wait=true; it
suspends W385830 and releases E386165 rather than leaving an idle claim. It is
not a preparation acceptance gate or owner policy escalation. I2 stays routed
to baton.codx for complete implementation once ownership is confirmed and the
obligation resolved; fresh claim required. Both predecessor checkpoints remain
satisfied at2d9a1f5a. Resume from evidence/i2-386165/PREFLIGHT.md and retained
baseline/source copy; do not repeat checkpoint preparation or baseline.

## 2026-11-25 — K confirms I2 ownership; gate M386167 not clearable by K (M386168)

I2 allocation of M386162/M386166 confirmed for codxpc on 2d9a1f5a through implementation and review corrections; no active overlap (no claims held by any participant; uncommitted product paths are DESIGN and the five W386057 paths only). Route is baton.codx. W385830 remains phase `block` on obligation M386167 addressed to baton.bug: `respond` by baton.prompt was refused (not a handler of baton.bug) and not retried; baton.rvpc must answer obligations 386167 and 386152. No claim held.


## 2026-11-25 — I2 implementation complete for independent review (baton.codxpc, E386173)

M386168/M386172 resolved the historical ownership gate; canonical claim E386173
resumed the retained source from2d9a1f5a. [I2 report](evidence/i2-386165/REPORT.md):
22-path candidate `sha256:87c3ba728e7fe75e649816a3bc44ae0bb6ff7bc6b3b915a84e70bbb495aa1627`. Production mapping,
automatic exact-byte first copy, D1 audited withdrawal/separate retry and D2
1MiB handling implemented; X1–X3 verified synthetically. C5–C8 dispositions are
in the report. Actual Codex participation remains unknown; Claude requirements
are preserved. No engine/build/real-credential/provider/native action.

Final focused selection: 1240 collected/executed, 1237 passed,
3 pre-existing failing IDs (five failure blocks exactly equal to baseline),
zero skips/unaccounted/drift; 54.263172s. Full selection is not
green and no failures are waived. Total retained verification 245.215088s.
All shared candidate targets remain baseline; DESIGN and five isolation paths
excluded, prerequisites unchanged. Fixture root empty/removed; archive, manifest,
diff, logs and source identity retained. Next: K exact-byte independent review,
routine corrections directly; owner import/checkpoint after acceptance. Suggested
commit: `Realize Codex homes and audited subscription credential lifecycle`.
Remaining selected-execution gates Q1–Q4 and editing I3 stay in the finite
[native-readiness plan](evidence/native-readiness-386143/PLAN.md); W386048/W386057
remain separate. No new owner decision requested.

Handoff recorded: M386176; pass E386177 to baton.bug for independent review.
Canonical detail at snapshot386177 verifies queued, gate null, Handler null.
Claim released; evidence/i2-386165/HANDOFF.json retains the disposition.

## 2026-11-25 — K review of I2 candidate 87c3ba72 (M386176)

[Review](review-2026-11-25T06-17-11Z.md): accepted as source for owner import/checkpoint on 2d9a1f5a; 1240 run, 1237 pass, the 3 failing ids confirmed identical on the unmodified base (not green). D1/D2, X1–X3, production mapping and C5–C8 confirmed by reading. No correction round. Limits L1–L6 (no operator command for D1; D1 only covers failure before any home write; whole-file leak guard; literal slot name; Codex now composable; baseline failures need their own Work). Q1 prerequisites: owner checkpoint of this candidate, Q1 packet from codxpc, owner execution selection. No claim held.


## 2026-11-25 — I2 accepted/imported, checkpoint pending

M386180 accepts 87c3ba72; Work returned to baton.decide via E386181. After owner repaired M386182 permissions, full preflight passed and exact 22 paths imported. See evidence/import-87c3ba72/IMPORT.md and /tmp/baton-w385830-i2-checkpoint.py. Verification remains 1237/1240 with three independently confirmed baseline failures, not green. Next Q1 packet must bind observed checkpoint and reviewed prerequisites before owner execution selection. L1-L6 remain explicit; no native activation selected.


## 2026-11-25 — I2 human checkpoint observed

Checkpoint 54fa5319090e2f0b555c1d2cba3035ee00b861d4 verified against all 22 accepted I2 source paths. Next executable preparation: one complete Q1 build/offline qualification packet based on this commit and M386180 prerequisites. Execution remains unselected; no real credential access or provider call. Three baseline inventory failures remain disclosed.

## 2026-11-25 — Q1 complete packet for independent review (baton.codxpc)

Next bounded milestone: independent review of the27-path preparation archive
`sha256:5a9d8f8239ff1b65b2aa11445c19b7ef1e071b98c627677a5ca48973def34b0d`,
base54fa5319090e2f0b555c1d2cba3035ee00b861d4. See
[REPORT](evidence/q1-preparation-386185/REPORT.md),
[settings/acceptance](evidence/q1-preparation-386185/README.md) and
[exact commands](evidence/q1-preparation-386185/COMMANDS.md).
Owner script payload digest95b750b5484d247f29b9c364bbcc0b9e051ceb1613fea1bc185cc03562930289.
Three selected preparation commands passed in0.836791s; eight manager-simulation
behaviors and five local runner behaviors, no engine or provider execution.
All22 accepted I2 files match the checkpoint. This is packet accounting, not
new product-suite coverage; prior1237/1240 and three baseline failures remain.

Ownership: codxpc packet/dossier only, no overlap with K/product changes. Review
routine corrections directly through implementation; after acceptance, owner
selects the exact one-build/offline settings. No current owner product decision
is unresolved. Q1 actual Docker/image/tool/home/F1/cleanup facts remain unknown
until selected execution. No new credential or model selection is required for
synthetic-only Q1. Remaining finite native gates are unchanged; no extra build,
provider call, native activation or retries are authorized by this packet.

Q1 review handoff: M386187 / E386188 to baton.bug. Canonical snapshot386188
confirms Handler null, queued and gate null. No claim retained.

## 2026-11-25 — Q1 packet 5a9d8f82 reviewed: corrections required (K)

[Review](review-2026-11-25T07-19-05Z.md), evidence `evidence/review-K-386187/`.
Not accepted for execution selection. B1: `owner-run.py:160` raises `TypeError`
(duplicate `builds` key) on every `--execute`, before any engine command and
after creating the fresh root. B2: no preparation check runs `execute()`.
Identity, 54fa5319 binding, recipe, binary pin, bounds, cleanup, synthetic-only
credentials and the launched-image path are verified; with B1 bypassed in memory
the full execute path passes against docker-shaped answers. Next milestone:
codexpc returns a new complete packet revision fixing B1 and B2, then re-review,
then owner execution selection. No owner decision is open.


## 2026-11-25 — owner-selected local Q1 correction

B1/B2 corrected in evidence/q1-correction-prompt/REPORT.md, original preserved. One launcher keyword change; three end-to-end fake execute scenarios and two existing preparation scripts pass. Candidate 5b6db7649c2518a0d9142164c2641f67721a677b8425761dc6981ad0f57e0916, payload 07cdf3c098202c8f4f925d6868fc73450c4b63e87e5a2fc42a7799f2bb44697f. Independent narrow delta review next; no build/engine/provider/credential execution selected. Copilot direct scope M386190; no handler claim held.

## 2026-11-25 — Corrected Q1 packet delta-reviewed: ready for selection (K)

[Delta review](review-2026-11-25T07-29-41Z.md), evidence `evidence/review-K-386191/`.
`evidence/q1-correction-prompt/`, archive
`sha256:5b6db7649c2518a0d9142164c2641f67721a677b8425761dc6981ad0f57e0916`, payload
`07cdf3c098202c8f4f925d6868fc73450c4b63e87e5a2fc42a7799f2bb44697f`. B1 (one-line
keyword fix) and B2 (real `execute()` check, three scenarios) closed and
reproduced. Qualification: correction and review share the `baton.prompt`
identity from different contexts. Next milestone: owner execution selection of
the one build and one offline run; exact command in the review.


## 2026-11-25 — Q1 executed once and passed

Owner selection M386193; evidence/q1-execution-386185/REPORT.md and RESULT.json. Image sha256:34364fb17d18b9abd1d155c33123888313a31141cc433322e68a7ad170a98fa7 from54fa5319. Real manager/engine receipt survives removal/reopen; offline identity/tools/home checks pass; container ceased/removed. Zero provider calls, synthetic credentials only. No native Job qualification claimed. Next: concrete Q2 editing-capture selection packet; no execution selected.

## 2026-11-25 — Q1 execution evidence accepted (K)

[Review](review-2026-11-25T07-33-22Z.md) of `evidence/q1-execution-386185/`.
Q1 accepted: image `sha256:34364fb17d18b9abd1d155c33123888313a31141cc433322e68a7ad170a98fa7`
from 54fa5319, Docker 29.1.3, network none, 1000:1000, real launched-image
receipt identical after removal and store reopen, equality branch only, no
credential or provider call. Limits: npm/apt layers were build cache (E1);
0.4 s container lifetime; `--time` and classic builder deprecated. Next
milestone: Q2 preparation packet (one native editing attempt). Q2 execution
needs owner selection of login source/placement, model and one-call budget.

## 2026-11-25 — Q2 complete preparation candidate for independent review

M386197/E386198 resolved routing/ownership; E386199 claimed. Next bounded
milestone: K independent review of
[evidence/q2-preparation-386199/REPORT.md](evidence/q2-preparation-386199/REPORT.md),
[README settings/acceptance](evidence/q2-preparation-386199/README.md) and
[exact commands](evidence/q2-preparation-386199/COMMANDS.md).
79-path archive SHA256abb0f083ef37f1a6fd7a2985a8bc93f1b57786ddd1829fbd8668e5181d74fbfc;
execution payload6841dc66747ab5c5bfc2c9ccd4a7f614bbdc93526b3ef2cbaad33b8921f42f14.
Accepted image34364fb1/source54fa5319 unchanged; no shared product edits.

Final preparation selection6/6 commands passed,0failed/skipped,4.904070s;
logs, JSON account, source identity and simulated execute-path evidence retained.
No product-suite rerun; prior1237/1240 remains non-green. All final synthetic
roots removed; earlier development roots conservatively retained as disclosed.
No real credential read, engine operation, build or provider call.

Fixed model/login choices are recorded in FINDING. After packet acceptance,
owner selection is still required for the exact one-turn execution, private
placement, bridge egress and limits. No model/source re-selection or product
ruling is requested. Routine packet corrections return directly to codxpc.
Native outcome, editing events and raw-capture completeness remain unknown;
actual contributors unknown and Claude stronger requirements preserved.
Finite successors Q2→I3→Q3→Q4; W386048/W386057 remain separate.

Q2 review handoff M386201/E386202 complete. Snapshot386202 verifies queued at
baton.bug, gate null, Handler null. No claim retained; execution unselected.

## 2026-11-25 — Q2 packet abb0f083 accepted for execution selection (K)

[Review](review-2026-11-25T08-04-31Z.md), evidence `evidence/review-K-386201/`.
Payload `6841dc66747ab5c5bfc2c9ccd4a7f614bbdc93526b3ef2cbaad33b8921f42f14`.
Real manager/exchange/production entry, accepted Q1 image, one container and
one provider turn, private capture, fixed public RESULT. Six checks reproduced;
removal-failure hold added and confirmed. Owner selects knowingly: bridge egress
without allowlist, Codex sandbox bypass inside the container, real login copied
and retained in the private root, no write-back. Next milestone: owner execution
selection; then separately authorized private-evidence review; then I3.


## 2026-11-25 — owner phase-ending clarification before Q2

See evidence/phase-ending-owner-ruling/RULING.md and narrow DESIGN checkpoint script /tmp/baton-w385830-phase-ending-checkpoint.py. Q2 packet M386203 remains historically accepted, but execution unselected. Reconcile code and packet with reviewer-owned substantive judgment, no exhaustive activity-event success parser. Current container/sandbox/egress posture knowingly accepted; no new execution authority.


## 2026-11-25 — phase-ending ruling checkpoint verified

Owner checkpoint 42da148f1b845474e5fa6db870132fcf214073f6 matches the narrow DESIGN amendment and pinned ruling exactly. Next bounded milestone: adapter/contract/Q2 packet alignment, deterministic verification and independent review. No Q2 execution or build selected. Ordinary activity does not decide task success; reviewer judges retained artifacts and escalates uncertainty.

## 2026-11-25 — M386205 phase-ending alignment (baton.codxpc)

Under E386207, implemented the checkpoint42da148f ruling: framed invocation completion permits verification/publication; ordinary activity is opaque and independent review owns substantive judgment. Structural/fault/reroute/configuration/image requirements retained; actual contributors unknown; Claude stronger requirements unchanged. Precise ordinary-review uncertainty/operator-escalation gap documented, not silently treated as implemented. No new ruling or acceptance weakening.

Complete candidate account: [REPORT](evidence/phase-ending-386207/REPORT.md); six owned source/test/doc paths plus successor [Q2 packet](evidence/q2-phase-ending-386207/README.md). Focused109/109 accounted pass, no source drift; initial accounting-drift run preserved. Seven preparation checks passed. Prior Q1/Q2 unchanged. New image qualification mandatory before Q2; no build/engine/credential/provider/native execution selected or performed. W386048/W386057 separate.

Current next milestone: independent review of the complete M386205 candidate, then human checkpoint. Suggested commit: `v12: separate Codex invocation completion from reviewer judgment`. Only thereafter separately selected rebuild/offline qualification and reviewed image binding, followed by separately selected Q2 editing capture. Historical M386203 execution proposal is superseded for the changed worker; no stale image use. The ordinary-review uncertainty escalation gap remains explicit for composed native review. Routine corrections return to configured implementation; source ownership M386205 remains serial.

## 2026-11-25 — Phase-ending candidate 1c2979d4 accepted; successor Q2 packet accepted as preparation (K)

[Review](review-2026-11-25T08-34-24Z.md), evidence `evidence/review-K-386209/`.
Six product paths on 42da148f accepted without corrections; 109/109 reproduced
on my reconstruction plus 33 probes. Packet payload
`5ce02041df3b6795a6e093157b6c073fe410687ccd65f775c76bcbee012d7567` accepted as
preparation; refuses the old image. U1: ordinary native review offers the
reviewer only three verdicts and no uncertain outcome — a Q4 gate, not a Q2
gate. Next milestone: owner checkpoint of the six paths, then a rebuilt-image
qualification packet (none exists yet).
