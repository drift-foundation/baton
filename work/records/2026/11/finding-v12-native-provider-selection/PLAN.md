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
