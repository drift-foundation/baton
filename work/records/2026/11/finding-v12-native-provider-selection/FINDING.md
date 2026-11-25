# Native provider selection — W385830

## Owner selection — 2026-11-23

Separate Work authorized alongside W385263 REV11 option A. Intended native pipeline: Codex implementation and independent Claude/Fable review. W385263 source survey at 6079ad78 reports no production Codex adapter/image in v12/worker and explicit Claude model selection only on the provider-context path. These are source-survey findings, not installed qualification. Revalidate existing implementations and prior spike/reuse work before designing additions.

Deliver supported native Codex worker integration and explicit Claude model selection with attributable reported-model evidence; no silent fallback. Reuse existing CLI-based architecture and owner-selected container permission policy. Bound adapter/image, normal exchange/output/diagnostic handling, composition, credential delivery and deterministic qualification. Live qualification must state its provider-specific question and obtain required execution selection; no implicit credential access or live launch. Preserve isolation, attribution, custody and review independence. No main Git mutation.

This Work does not gate direct W385263 A1 delivery. Later native slices require accepted/qualified provider support. Cross-reference W385263 FINDING first-slice exception. No scheduler dependency edge installed by this record; selected dependent execution must be gated explicitly when assigned.


## Priority preparation — 2026-11-23

Following discussion of prioritizing native Codex support before A1, owner confirms no A1 work was handed off. Coordinator verified both Works unclaimed and returned A1 to decide. Next step is bounded W385830 implementation planning, to enable native Codex implementation and explicit Claude/Fable independent review without human message relaying. Existing CLI-based provider architecture, isolation and full in-container provider tool permissions remain the target. No adapter design, CLI model identifier, credentials, live qualification or execution profile is selected by this priority step; research existing paths first.


## 2026-11-23 — K research and proposed implementation contract

Under M385843 (no claim), K wrote IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md (sha256 68599861e3af9f0763f08d97ff9b44dcb75c36581155a9c4f173b1ce2891c9d7); host CLI help captures in evidence/research-385843/ (host builds codex-cli 0.169.0 and Claude Code 2.1.330 — not the pinned builds; only --version and --help were run). Research/design only; nothing built, launched or tested; no provider call; no credential read. Findings at 6079ad78: the worker seam is one work() method and about 85% of the 7379-line Claude adapter is provider-neutral; credential delivery, per-worker image/profile, network, handoff, custody and stop paths are reusable unchanged. Gaps: no Codex adapter/entry/image (spike only); the fresh Claude invocation passes no model, the profile's "opus" is a hard-coded label nothing delivers or enforces, and retained real output shows the account default was used; the pinned Claude build's result has no direct model field (modelUsage names the selected model plus a helper), while the worker reads only the direct field and the host drops the observed-model check; tool_policy_digest (provider argv/environment) is part of the Job input identity, so a Codex lane beside a Claude lane would be refused today; compose-worker has no provider or model operand; separation_class is an unverified constant; Codex needs a writable non-temporary home, colliding with the read-only-root posture; Codex's child outlives a signal to its parent; the provider inherits stdin. Proposed: provider hooks on the existing agent class with a CodexAgent subclass; explicit model selected at composition, delivered by a versioned launch member, applied in argv, observed from the terminal record, enforced on the host at the ending (refuse and hold), and shown; provider-neutral tool policy with provider argv in the per-worker adapter document; a narrow provider-home mount; mirrored Codex image. Slices N1–N6; deterministic acceptance per slice; engine-only image gates where the pinned-build flag inventory is taken; two narrow real-provider questions. Codex argv, event shapes, session-file location and credential file name are deliberately not fixed before the pinned build is inventoried. Seven owner decisions D1–D7 (pins; model selectors; Codex credential; mismatch policy; tool policy digest; home mount; execution selections). Not approved; no coding.


## D5 provider-neutral policy selected — owner 2026-11-23

Owner approves D5's recommended approach in IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md §4.4: retain a provider-neutral tool-permission/environment policy in the shared Job identity. Bind each provider's exact command and environment configuration separately to its worker adapter identity. Codex and Claude need not have identical CLI arguments to participate in one Job; both must implement the same selected shared policy. A lane with a different selected permission policy is refused. Do not simply exclude the policy digest from identity or weaken admission validation.

This selects the policy/implementation separation, not an exact unreviewed schema or migration. Preserve old admitted identities and evidence; apply revised composition semantics through explicitly versioned supported contracts where required. K should define the minimal normative/contract delta and deterministic positive mixed-provider and negative policy-mismatch proofs. Other owner decisions remain open. No provider call, image build, credential access, live change or blanket coding authorization selected here.


## 2026-11-23 — K contract revision 2 (delta) after D5

Under M385845, K wrote IMPLEMENTATION-CONTRACT-REV2-2026-11-23.md (sha256 df42c0387f13eecaa45dd23685d536a2c3bbd0cb50c80ec2ae070919dffae955), a delta on the first contract, which is preserved unchanged. Research/design only; nothing executed. Recorded: D5 settled; D4 (refuse and hold on model mismatch) was already selected and is withdrawn as an open decision. Proposed: shared baton.worker-tool-policy/2 with provider-neutral members (interaction, tool permission, provider sandbox, user configuration, credentials, environment, ephemera, no model substitution) as the Job's tool_policy_digest; per-worker baton.single-implementation-adapter/2 carrying the provider's exact argv and environment policy and implements_tool_policy; honesty by one owned provider table from which the composer builds adapter documents, an added admission check that the adapter implements the Job's policy beside the unchanged cross-lane equality, and the worker refusing to start a provider whose actual argv differs from its delivered policy. Versioning: already-composed documents keep stored /1 digests and validate as today; new composition emits /2 by explicit selection; /1 and /2 lanes cannot mix (unequal digests); worker manifest contract unchanged; context-bound path untouched; capabilities requalified. Normative: fits ID-4 and ID-6; one clarifying sentence proposed, not drafted into DESIGN. Proofs added: mixed-provider positive, five policy-mismatch negatives, three preservation cases. Next owner decision raised: must every worker name an explicit model, the Codex implementer included (A yes, recommended; B recorded provider default allowed). Remaining: D1, D2 values, D3, D6, D7. Not approved; no coding.


## Explicit models and attributable results — owner 2026-11-23

Owner selects option A in IMPLEMENTATION-CONTRACT-REV2-2026-11-23.md §4: every worker in the new composition must name an explicit model, including Codex implementation. This supersedes the earlier allowance for an account-level default for these new compositions; existing admissions remain unchanged. Exact model identifiers and CLI pins remain to be selected.

The purpose is attribution and traceability: when code, implementation or review has an issue, its producing model must be identifiable. Retain the explicitly requested model, the provider-reported model and its evidence, provider and CLI version, and bindings to the exact attempt and resulting candidate or review verdict. Requested model is intent, not proof of the model that ran. Missing or conflicting model evidence prevents acceptance under the selected refuse-and-hold rule; never silently substitute or infer the observed identity from the requested one. Owner may explicitly select another model for subsequent execution.

This approval selects the requirement and rationale, not unverified model identifiers, a particular evidence parser, credential access, builds or live calls. K is to fold it into the contract and raise the next unresolved owner decision, one at a time.


## 2026-11-23 — K contract revision 3 (delta) after explicit-model ruling

Under M385847, K wrote IMPLEMENTATION-CONTRACT-REV3-2026-11-23.md (sha256 3a3d36c372866330e6c4d632917985820bfd1a4fe03c1204ef60c01c196451d6), a delta replacing the first contract's §4.3 and N1 verification; earlier contract files preserved unchanged. Research/design only; nothing executed. Folded in: every worker in the new composition names a model (composition refuses otherwise; account default not allowed there; old compositions unchanged and shown as "not selected (account default)" instead of the hard-coded label). Attribution record per provider-invoking attempt: attempt, provider, CLI build selected and CLI build evidenced (measured by the worker from the program — today it is copied, not measured), model requested, expected and observed, evidence digest and retained log, outcome matched/missing/conflicting; identities and digests only. Travel and binding: selected at composition, delivered by a versioned launch member, applied in argv with no fallback option, recorded in the attempt's own frozen result, bound on the host in the existing ending settlement beside the candidate checkpoint or verdict id, enforced there (only matched with equal CLI build proceeds; otherwise typed refusal and hold), shown in diagnostics and available to W385263 History. Sixteen N1 verification behaviours. Next owner decision raised: when a provider reports more than one model for one invocation (measured on the pinned Claude build: selected model plus a helper), when is attribution matched — A declared helper list per profile (recommended), B expected identity present is enough, C exactly one identity. Remaining: D1, D2 values, D3, D6, D7. Not approved; no coding.


## Contributor-list attribution — owner 2026-11-23

Owner selects contributor-list attribution: retain all provider-reported models as contributors, with no primary designation. Keep the requested model separately as intent. The requested model must appear in the evidenced contributor list (using the explicitly selected selector-to-reported-identity mapping, not an invented equivalence). Additional reported contributors are recorded; no helper allowlist or primary-role requirement is selected. This settles REV3 §4 as option B with contributor terminology, superseding the proposed declared-helper-list recommendation. A match establishes reported participation, not predominance or exclusive authorship. Missing evidence or absence of the requested model still refuses and holds; existing evidence binding and no silent fallback rules remain. No identifiers, CLI pins, live calls or implementation are selected by this ruling.


## 2026-11-23 — K contract revision 4 (delta) after contributor-list ruling

Under M385849, K wrote IMPLEMENTATION-CONTRACT-REV4-2026-11-23.md (sha256 c9c99b5e52180e283659aa4989b0052110011bc476105e60326e40d301e8d0b6), a delta on the first contract as amended by REV2 and REV3; all earlier contract files preserved unchanged. Research/design only; nothing executed. Folded in: record members renamed and redefined — "model, mapped identity" (owner-selected identity the provider reports for the requested selector; exact whole-string equality; no alias/prefix/case matching; one identity per selector; no mapping means composition refuses) and "contributors" (every reported identity, as a sorted set, no quantities, no roles, bounded). Outcome: matched = mapped identity among contributors on the selected CLI build; conflicting = contributors read but mapped identity absent, or CLI build differs; missing = nothing readable. Additional contributors never change the outcome; no allowlist exists. K's reading, flagged for correction: all evidenced sources (direct field, usage entries) feed one set, so REV3's "single-model field naming a different model is conflicting" is dropped; usage quantities stay only in the retained raw output. Surface wording fixed: "Requested", "Reported contributors", "Requested model reported: yes/no/no evidence"; never primary/helper/share/"produced by". Separation class computed from provider and requested model. N1 verification: REV3 items 4 and 14 replaced, items 17–22 added. Real-provider questions capture the full contributor list to inform the owner's mapping selection, not to approve any list. REV3 §4 withdrawn. N1 and N2 are now fully specified; N3 blocked on D1, D3, D6. Next owner decision raised: which Codex CLI build is pinned (Codex half of D1) — A 0.169.0 (recommended; only retained flag inventory, unproved in container), B 0.150.1 (spike container experience, flags unverified), C another named build. Remaining after that: D1 Claude pin, D2 values, D3, D6, D7. Not approved; no coding.


## Codex CLI pin selected — owner 2026-11-23

Owner selects D1 Codex CLI option A: pin 0.169.0 for the Codex worker image. Retained host flag inventory is preparation evidence, not proof of container compatibility. Qualify the exact pinned build in the selected container posture before native use; this selection alone does not authorize builds, credential access or live provider calls. Claude pin, exact model identifiers and other open decisions remain pending.

Contributor interpretation clarification: collect identities only from provider fields that evidence actual model participation in this invocation, not arbitrary model-name mentions in output. No primary designation. A single-model field naming another contributor is not by itself conflicting if the requested model is also evidenced among contributors. Preserve the source evidence; do not infer participation from request/configuration text.

K: fold the pin and clarification into the contract and raise the next unresolved owner decision, one at a time.


## 2026-11-23 — K contract revision 5 (delta) after Codex pin and contributor-evidence clarification

Under M385851, K wrote IMPLEMENTATION-CONTRACT-REV5-2026-11-23.md (sha256 a87f38a63ea828356f258ba11751f2c6c750fa49a5060196a8c3bfeb2a6d6171), a delta on the first contract as amended by REV2–REV4; all earlier contract files preserved unchanged. Research/design only; nothing executed. Folded in: Codex CLI 0.169.0 as the image pin (recipe pin and version gate; "CLI build, selected" for a Codex worker; adapter written against the inventory taken inside the image; host captures are drafting guidance only; spike findings F9/F10 were measured on 0.150.1 and are carried as questions for 0.169.0). Contributor evidence: each adapter carries a closed, per-pinned-build list of participation sources (provider fields meaning "this model did work in this invocation"), covered by the adapter identity digest; never collected from the request, argv, profile, configuration-echo records, generated text, tool output, prompts or error messages; an empty list yields missing. All participation sources feed one set with no primary; a single-model field naming another model is matched when the requested model's mapped identity is also evidenced, conflicting when it is not. Record gains "contributor sources" (field names per contributor, no values). N1 verification: item 4 replaced, items 23–29 added. Not chosen, flagged: whether an all-zero usage entry evidences participation; usage quantities remain excluded from the record as K's reading. Next owner decision raised (D6): where a provider that needs a writable home gets one — A declared private memory mount at the provider home (recommended), B inside the existing writable disk work area, C decide after the engine-only gate. Remaining after that: D3, D1 Claude pin, D2 values, D7. Not approved; no coding.


## Stable retained provider homes — owner 2026-11-23

Owner selects D6: treat the provider home as a retained, disk-backed work area managed mechanically by Baton. Each worker gets its own stable home; implementation and review do not share one even when they use the same provider. Do not rely on providers or models selecting non-colliding subdirectories. The home survives container stop/removal/replacement and supported restart/resume; its identity must not be regenerated merely because a container or attempt restarts. Keep it outside the source checkout/proposal paths. Credentials remain separately delivered; do not expose the operator home.

This supersedes the proposed private memory mount and the coordinator's earlier suggestion of an automatically disposable per-attempt home. Owner does not select elaborate home access controls or require another permission gate for successor access: treat it as retained work storage. Prevent concurrent writers from colliding in the same home through the existing execution ownership mechanism. Retaining files does not assert provider-session resume is implemented or qualified. More elaborate sharing/model-switch behavior is deferred.

K: fold this into the contract, state the stable worker/home binding and lifecycle using existing work-area machinery, and present the next unresolved owner decision. Coordinate instruction-delivery overlap with W385853 (codexpc); no runtime edits, builds or live calls are authorized by this ruling.


## 2026-11-23 — K contract revision 6 (delta) after retained-home ruling

Under M385859, K wrote IMPLEMENTATION-CONTRACT-REV6-2026-11-23.md (sha256 a7b2fadeb2b388b2cc91742a53238584a668a4d8f744d199841687088b148ecb), a delta on the first contract as amended by REV2–REV5; all earlier contract files preserved unchanged. Research/design only; nothing executed; no runtime edit. REV5 §6 (K's private-memory-mount recommendation) withdrawn as not selected. Surveyed: no existing directory is both container-writable and worker-keyed (attempt scratch is per attempt, the Claude context store per Job/Work, the review line is a checkout); the per-worker derivation pattern exists for the source nomination (tools/pool.py:790); one live allocation per worker is a store uniqueness rule (job_manager/schema.py:312-314); five ending kinds release a slot without that code reading runtime state (scheduler.py:33, 585-589) — whether a container can still be alive there is not established. Folded in: home keyed by instance and worker id only, at <instance>/state/provider-homes/<worker_id>/home with a manager-owned holder record beside it; one new deployment member under a new deployment schema version; new typed mount family at one constant path (spelling fixed at the image inventory); used by every worker of the new composition, Claude included; refused if overlapping workspace root, source nomination, launch/credential home, context store, repository or operator home; never an output or in custody; untouched by attempt cleanup; removed only by explicit operator act; no size bound or expiry selected. One writer: the worker's allocation, plus a holder check at start that passes automatically once the previous runtime is proved gone (K's addition for the unestablished release path; no owner gate). Credentials: link to the read-only delivery only, re-made each start, never copied. Retention asserts no session resume. Overlap with W385853: the home is part of each provider's instruction chain; contract offers no host seeding, a closed per-adapter list of managed home entries re-placed each start, and binding through adapter identity /2; proposed serial order N2 then W385853's delivery delta (proposal, not assignment; explicit dependency is the owner's). Eighteen verification behaviours added to N2. Next owner decision raised (D3): Codex credential kind — A API key (recommended), B login file kept read-only, C login file with refreshed copy kept in the home. Remaining after that: W385853 order, D1 Claude pin, D2 values, D7; model-switch/sharing deferred. Not approved; no coding.


## Subscription credential refresh in retained home — owner 2026-11-23

Owner selects D3 option C: use subscription login credentials for the Codex worker, permitting the provider to retain its refreshed credential copy in its own stable retained home. Do not substitute API-key billing. Exact credential registry/reference, seed delivery and the pinned CLI refresh behavior remain to be established/qualified; this decision does not authorize reading credentials or a live provider call. Never write refreshed credentials back into the operator home or expose them in ordinary candidate/evidence/log output.

Owner also accepts the discussed home safeguards: prevent simultaneous writers by refusing a new container on the same home until the earlier runtime is confirmed stopped; admission proceeds without another owner approval once prior runtime settlement establishes that condition. A stale/missing observation is not positive cessation.

Baton-managed replacement is limited to explicitly identified Baton-owned instruction/configuration files. Do not overwrite provider session data or refreshed credentials on startup. The home remains retained work storage, not a disposable per-attempt directory. Use existing execution ownership and work-area machinery; no new manual babysitting or general successor-access gate.

K: fold this ruling into the contract, keep the engine/provider qualification limits explicit, and present the next unresolved decision. Proposed delivery ordering with W385853 remains coordination to settle; this message does not assign overlapping runtime edits.


## 2026-11-23 — K contract revision 7 (delta) after subscription-credential and home-safeguard ruling

Under M385865, K wrote IMPLEMENTATION-CONTRACT-REV7-2026-11-23.md (sha256 042025f78b95d5e3b7890ab49185c2bc6d53ec01df219ce5ef2a07aa0912bfff), a delta on the first contract as amended by REV2–REV6; all earlier contract files preserved unchanged. Research/design only; nothing executed; no credential or registry read. REV6 §7 (K's API-key recommendation) withdrawn as not selected. Folded in: two credential modes declared per adapter and bound in adapter identity — delivered (Claude, unchanged) and seeded-and-retained (Codex): the registry login arrives by the existing read-only delivery, is copied into the home only when the home has none, and thereafter belongs to the provider; never replaced or compared at start; never copied outward (delivery, registry, operator home, output, custody, log, diagnostic); no API-key slot or variable, authentication failure is a typed failure with no other billing route. K's proposal, flagged: one explicit operator re-seed act, allowed only while no runtime holds the home. One writer: confirmed stopped means runtime recorded absent/destroyed with cleanup complete or retained; no observation, a stale one, uncertain, an unconfirmed stop, or an ending/exit/token expiry alone are not confirmation; refusal is a pending state that clears automatically, no owner item. Managed entries: only Baton-owned instruction/configuration files by exact path, never credentials or provider session data; the list is empty until W385853's delivery names files; a managed path colliding with a provider-written path is reported, not overwritten. Qualification limits U1–U9 stated, including U5 (whether a refresh in the worker home invalidates other copies of the same login) and U8 (which registry login seeds the worker); Q1 extended. REV6 verification items 13, 14, 16 replaced; 19–27 added. Next owner decision raised (D1 Claude): stay on 2.1.247 and move only if Q2 shows it cannot select the model (recommended), move to 2.1.330 now, or another named build. Remaining: U8, D2 values, D7; W385853 order is coordination in progress. Not approved; no coding.


## Claude CLI pin retained — owner 2026-11-23

Owner selects D1 Claude option A: retain CLI 2.1.247 for this Work. Qualify that exact pinned build against selected requirements, including explicit Fable selection and evidenced contributor reporting. Upgrade only if qualification establishes it cannot meet those requirements; an alternative version still needs explicit selection and qualification, not silent substitution. Codex remains pinned to 0.169.0.

Credential-refresh invalidation across copies remains an unresolved qualification question before sharing a login across worker homes. The proposed explicit re-seed operation is not approved by this choice; keep it pending until the actual recovery requirement is established. No credential/registry read, build, provider call or live change selected here.

K: fold the pin and qualification condition into the contract and raise the next unresolved owner decision, one at a time.


## 2026-11-23 — K contract revision 8 (delta) after Claude pin ruling

Under M385872, K wrote IMPLEMENTATION-CONTRACT-REV8-2026-11-23.md (sha256 adcca6f3e02ff1cba9b05dcd182bc3ced253f46e1fbea2c9cf0ac2da320db551), a delta on the first contract as amended by REV2–REV7; all earlier contract files preserved unchanged. Research/design only; nothing executed. Folded in: Claude CLI 2.1.247 retained (image rebuilt only for the adapter change; selected build for a Claude worker; participation sources drafted from the September output of the same build). Qualification requirements C1–C5 for 2.1.247 (K's reading, flagged): reports its version offline; accepts an explicit model selector on a fresh turn; runs the selected Fable selector without refusal or substitution; output carries a participation source; contributors include an identity the owner accepts as the requested model. Any failure is the demonstrated need; nothing changes by itself — the pin stays, the reviewer stays unqualified, the owner selects an alternative which is qualified from the start; version gate and worker refuse any other build; no code path tries a second build. Withdrawn as not approved: the explicit re-seed act (REV7 §2.2 item 6, second half) and REV7 verification item 27; stated gap: no supported recovery for a home whose login lapsed, pending an established requirement. Login sharing: until U5 is answered, composition refuses two seeded-mode workers in one instance naming the same credential reference (K's mechanisation; cross-instance and operator-session sharing cannot be seen by Baton). Verification items 28–30 added. Both halves of D1 now settled; N1, N2 and N3's deterministic part are specified; every remaining open item concerns qualification. Next owner decision raised: consolidate the eight contract files into one self-contained contract for approval of deterministic work and raise qualification decisions when images exist (A, recommended), settle D2/U8/D7 first (B), or consolidate N1 and N2 only (C). Not approved; no coding.


## Consolidate contract; no invented login-sharing restriction — owner 2026-11-23

Owner selects REV8 §7 option A: consolidate now into one self-contained contract for review/approval of deterministic implementation. Preserve the historical proposal/deltas unchanged. Consolidation itself is not implementation approval. Qualification must pass before native use; later implementation approval does not authorize live provider calls or other separately selected operations. Raise model selectors, seed reference, engine-gate and provider-call selections at the relevant qualification boundary.

Required correction: the proposed one-login/one-worker-home composition prohibition was not owner-selected. It conflicts with the intended subscription pool serving multiple workers. Remove it as a selected requirement; retain refresh invalidation across login copies as an unresolved risk to qualify before shared-login use. Do not invent a permanent restriction or silently claim sharing is proved safe.

The proposed re-seed command remains undecided. Its lack of approval is not an owner decision to make homes permanently unrecoverable. Describe the concrete recovery gap and pending mechanism accurately, without adding a new ban.

K: prepare the consolidated contract with these corrections, distinguish selected rules from implementation proposals and unproved qualification obligations, then return it for review. Keep live Jobs and their admitted limits unchanged. No coding, credential read, build, install, engine operation or provider call selected by this consolidation ruling.


## 2026-11-23 — K consolidated contract for review (M385877)

Under M385877, K wrote IMPLEMENTATION-CONTRACT-CONSOLIDATED-2026-11-23.md (sha256 6dbdd641de4b7fb9c4a7b0d9b85828e4a5e205462aab0765e046374271cd0fe4): one self-contained contract replacing, for reading, the first proposal and deltas REV2–REV8, which are preserved unchanged and listed there with their hashes. Research/design only; nothing executed; for review, not approved; no assignment. Every rule is marked [S] selected by the owner with its source message (S1–S16), [P] K's implementation proposal, or [Q] an unproved qualification obligation. Corrections applied per M385877: the one-login/one-home composition refusal (REV8 §5, its test) is removed — no sharing restriction exists, a deterministic case asserts two workers naming one credential reference are admitted, and refresh invalidation across copies of a login stays an unresolved risk (U5) to qualify before shared-login use, with no claim that sharing is safe; re-seeding is described as an undecided pending mechanism and the lapsed-login state as a concrete recovery gap, not a ban. Content: provider hooks; tool-policy/2 and adapter/2 identity; explicit model and attribution record with contributor evidence from participation sources; retained per-worker provider home with holder check; delivered and seeded-and-retained credential modes; Baton-managed entries (empty until W385853 names files); pins Codex 0.169.0 and Claude 2.1.247 with requirements C1–C5; qualification gates and questions Q1/Q2 and unknowns U1–U9, none authorized; slices N1–N6 with 51 deterministic verification behaviours; proposed DESIGN sentence awaiting explicit approval; overlap and proposed order; what approval would and would not do; decisions listed at their boundaries. K's own readings are listed in its §18 for correction.


## Job-bound homes and consolidated-contract review — 2026-11-23

Coordinator review of consolidated contract M385878: changes requested before implementation approval.

Owner clarification: provider homes belong to the specific Job work area, separate for each worker within that Job. Same Job/worker restart or resume reuses its stable home; another worker gets a separate home; an unrelated Job gets a separate work area and home. Sections 8.1/8.3 and proof 32 must not key only by instance/worker or carry a home across unrelated Jobs. This explicitly corrects the proposal, not an approval of cross-Job sharing. Preserve existing operator-home protection, credential refresh and single-writer rules.

Required technical correction: remove the N3/N4 planning cycle (N3 requires N4 inventory; N4 requires images). Distinguish a minimal pinned-image inventory gate from completed adapter/image qualification. Do not guess pinned flags or treat inventory as final qualification. Engine operations still need their selected execution boundary.

Required technical correction: N1 proof 11 cannot require byte-identical entire attribution records when changed raw usage/output changes the evidence digest. Require stable normalized contributor fields for equivalent participation, and the correct distinct evidence digest for different retained bytes. Preserve per-attempt binding and source-field evidence.

The proposed §14 DESIGN clarification matches the approved policy/adapter distinction but exact normative text still awaits owner approval. K: incorporate corrections in a self-contained revised contract, preserve original, and return for narrow review. No implementation or live operation selected.


## Shared-policy DESIGN clarification approved — owner 2026-11-23

Owner explicitly approved the coordinator-proposed normative wording following M385881. Added under ID-4 in v12/DESIGN.md:

The tool-permission and environment policy a Job is admitted under is
provider-neutral and shared by every execution of the Job. Each execution's
provider-specific command and environment configuration is bound to its own
adapter identity and MUST implement that shared policy. Different provider
commands are allowed; a different policy or an adapter that does not implement
it MUST be refused.

This supersedes the pending exact-text approval in the contract/PLAN; use these approved bytes rather than the earlier proposed §14 wording. Existing unrelated DESIGN edits preserved. This records the shared-policy/per-execution-adapter distinction and selects no implementation, build or live execution.


## 2026-11-23 — K consolidated contract revision 2 for narrow review (M385881, M385882)

K wrote IMPLEMENTATION-CONTRACT-CONSOLIDATED-REV2-2026-11-23.md (sha256 dc3245c0c5594f15d22c87cd9b9a19352c633c3e4ef9a52f070f24d87960bd87), self-contained; the first consolidated contract (sha256 6dbdd641de4b7fb9c4a7b0d9b85828e4a5e205462aab0765e046374271cd0fe4), the first proposal and REV2–REV8 are preserved unchanged. Research/design only; nothing executed; for narrow review, not approved; no assignment. Its opening table lists the four changes so review can be confined to them. R1 (owner clarification): provider home keyed by instance, Job id and worker id, inside that Job's work area at <instance>/state/job-work/<job_id>/provider-homes/<worker_id>/ (a new directory family — no per-Job directory exists today); same Job and worker reuse it on correction, restart, resume, replay; another worker, or the same worker on an unrelated Job, gets a separate home; nothing copied between Jobs; a start with no Job id is refused; "same Job" read as same Job id (K's reading, flagged). Stated consequence: each Job's Codex home is seeded separately, so copies of one login in several homes are the ordinary case from the second Job on; U5 must be qualified before that, and remains unqualified-not-forbidden; a lapsed home affects only its Job. R2: slice cycle removed — N3 is a minimal pinned-image inventory (engine operation needing selection; needs no adapter; not qualification), N4 the Codex adapter and recipes written against it, N5 the image qualification gate then Q1/Q2, N6 packets and joined proof; N1 and N2 depend on none of these; no option is guessed if N3 is not selected. R3: proof 11 now requires equal normalised participation fields for equivalent participation, and proof 12 a correct, distinct evidence digest and attempt binding per record. R4: the approved DESIGN wording is quoted from v12/DESIGN.md ID-4 (lines 188–193, read not edited) and mapped to section 5 and proofs 27–29. Proofs 31, 32, 32a, 36, 41, 45, 50a adjusted or added.


## N1/N2 deterministic implementation approved — owner 2026-11-23

Owner approves deterministic implementation slices N1 and N2 of IMPLEMENTATION-CONTRACT-CONSOLIDATED-REV2-2026-11-23.md (sha256 dc3245c0c5594f15d22c87cd9b9a19352c633c3e4ef9a52f070f24d87960bd87), with the following review qualifications. This is not approval of N3 engine inventory, N4 beyond its prerequisites, N5 real-provider/image qualification, or native use. No credential/registry read, image build, install, engine operation or live call is selected here; ordinary private compilation and focused deterministic tests remain authorized within N1/N2.

N1: explicit model request, contributor attribution/evidence binding and enforcement, diagnostics and separation classification. N2: provider hooks, shared policy/per-worker adapter identity, Job-and-worker-bound retained disk homes, single-writer protection and selected credential/managed-entry behavior. Preserve old admissions. Exact reviewed candidate and independent review remain required.

Technical qualifications: (1) N3 no-provider inventory cannot supply real turn-event shapes. Later adapter fixtures must trace to retained exact-build evidence or separately selected provider qualification, not invented observations. Correct proof 50a and related wording accordingly; this does not block N1/N2. (2) Derive home paths with safe, collision-resistant encoding/binding of canonical Job and worker identity; never concatenate arbitrary Job text as filesystem path components. Job-bound persistence and separate-worker homes remain selected.

Execution order: keep shared-file implementation serial behind codexpc current W385695 checkpoint-2 recovery. Do not interrupt or reallocate that claim. W385853 runtime instruction delivery follows the accepted N2 interface; no runtime edit ownership is assigned by this message. K may record the corrected contract/verification wording now. Coordinator will establish the bounded assignment and actual graph gates before releasing dependent execution. Do not treat this discussion record alone as an installed dependency.

Qualification questions remain pending at their selected boundaries; no new owner approval is needed for routine in-scope deterministic corrections.


## 2026-11-23 — K addendum recording the two M385887 qualifications

K wrote IMPLEMENTATION-CONTRACT-N1N2-ADDENDUM-2026-11-23.md (sha256 c4d2c4b7ebe4c60b6e5eb9543ff4664d2fd86511c6b8a4f538c2b58e27d07117). The approved contract file (sha256 dc3245c0…) is not edited, because the approval names its hash; the addendum is read with it and changes nothing else. Nothing executed. Qualification 1: a no-provider inventory sources only options and start-time facts; turn-event shapes, exit behaviour and participation sources must trace to retained exact-build real output (exists for Claude 2.1.247 in the September dossier; none for Codex 0.169.0) or to a separately selected provider qualification; never another build, host captures or expectation. Proof 50a replaced: every adapter fixture carries a recorded source of the right kind, synthetic fixtures may prove only refusal; N4 split into N4a (arguments, entry, recipe, home handling; after N3) and N4b (turn-event parsing; after exact-build evidence or Q1); until then the Codex participation list is empty and results are missing. Qualification 2: home path components are fixed-length digests of one canonical, unambiguously encoded identity (authority, Job id, worker id), the same construction as the context store; no Job or worker text in the path; the manager-owned record stores the plain identity and is checked at every start; proof 31 replaced and 31a–31d added (hostile ids, naive-join collisions, wrong or missing record, diagnostics from the record). Order recorded, not installed: N1/N2 shared-file implementation serial behind codexpc's W385695 checkpoint-2 recovery; coordinator establishes assignment and graph gates; W385853 delivery follows the accepted N2 interface.


## 2026-11-24 — K revalidation at 9f979022 and N1/N2 assignment

W385695 closed satisfying at 9f979022, after changing 56 paths under v12/ (most of the files this contract cites). K re-read each cited place and wrote ASSIGNMENT-N1N2-2026-11-24.md (sha256 ae9dfac38ba3bd61d628c23c98637e9a8eb2e68ac50b8592b0717063992d3b22). Nothing executed; contract and addendum not edited. Observed: F2, F3, F5, F6, F7, F8, F10, F11 and F14 still hold at moved locations (table in assignment §3). Observed, new: (1) the approved ID-4 sentence is only in the uncommitted working tree of v12/DESIGN.md; (2) worker/bounded_command.py supervises a required review's provider and ends its descendants, while every other turn still ends only the direct child and inherits stdin, so proofs 23 and 24 remain owed; (3) a publication worker and lane exist and invoke no provider. K's reading, open to correction: the model, adapter-identity, home and attribution rules apply to provider-invoking workers and the publication worker is composed as today. Confirmed conflict: (4) job_manager/publication_execution.py accepts an implementation candidate (take_custody, hand_off, deliver_review_item) without passing through review_driver.end_implementation, so under the new composition a recovered candidate would reach review with no attribution, against S2 and proof 14. Raised as one owner decision (assignment §5): A refuse such recovery (recommended), B carry and enforce attribution through recovery, C accept unattributed. Not established: how the existing lane-equality check treats the publication lane. Graph gates: none installed; K's create (child of W385830) and block (W385263 on W385830) were refused because baton.prompt is not a handler of baton.decide; the owner commands are in assignment §4.1.


## 2026-11-24 — owner selected B, recovery attribution

Slawomir approved B: carry and enforce original producer attribution through publication recovery for new-composition Jobs. ASSIGNMENT-N1N2-OWNER-B-2026-11-24.md supersedes the pending assignment decision and narrowly extends recovery scope. DESIGN ID-4 reflects the ruling; owner Git checkpoint remains pending. No implementation or live execution performed. Owner script will create the bounded child, install W385853 and W385263 gates, read back the graph, and release to baton.codx. Until that script succeeds, no graph or assignment change is claimed.


## 2026-11-24 — owner confirms drafted, unqualified Claude participation list

Slawomir answered yes to retaining the contributor parser/list as drafted and unqualified pending qualification, following K review M385980 (review-2026-11-24T10-12-37Z.md section 3). The September raw output is unavailable; its digest and an independent written description are not retained raw output. This explicitly supersedes the addendum's claim that retained exact-build raw evidence exists and permits the draft for deterministic N1/N2 implementation only. It does not qualify a provider shape or authorize native use. Synthetic fixtures remain labelled; documentation must cite the actual written records and disclose the missing raw output. Qualification must retain actual exact-build raw output by dossier path and digest and validate the drafted sources before native use. Missing/conflicting/invalid attribution continues to hold; no fallback, new provider call or acceptance waiver is selected.


## 2026-11-24 — owner-selected interactive R1a correction

Owner explicitly requested this interactive coordinator handle the bounded R1a fix here instead of codexpc and instructed proceed. Canonical W385965 had no handler; rerouted from baton.codx to baton.decide at E385987 to remove competing readiness. This is a task-specific direct execution exception for R1a only, not impersonation or a managed prompt claim. No protected source import or Git mutation authorized. Prior candidate 4980bb47 remains preserved; correction in an isolated copy, focused manager-pure/tools-pure tests, exact delta to independent K review. Exception ends on handoff.


## 2026-11-24 — owner accepts K independent-context review and selects import

Slawomir explicitly accepted K's review-2026-11-24T17-01-44Z.md as the independent review of candidate 5b76e700, despite both contexts recording baton.prompt. This is a candidate-specific independence ruling, not a general shared-identity waiver. K did not implement the correction and independently reconstructed and probed its bytes. R1–R4/R1a are accepted. The coordinator prepares exact-byte host import and human checkpoint; no Git mutation, image build or native qualification selected. Qualification limitations remain unchanged.


## 2026-11-24 — owner selects separate host OpenAI subscription homes

Owner specifies interactive copilot uses /home/sl/.codex and codexpc uses /home/sl/.codex-pushcoin, representing separate OpenAI subscriptions. Preserve separate account/session homes and do not copy credential contents between them. This host-launch mapping is not selection of a credential seed for a future native Job. Current copilot process ancestry is under .codex app-server with CODEX_HOME unset; existing Codex CLI processes inspected also have no explicit CODEX_HOME, so codexpc separation is not yet verified. No credential contents read, account/login change, process restart or active-work interruption performed.


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


## 2026-11-24 — disjoint N4a draft E386029 (baton.codxpc, impl)

E386028 and the owner selected M386027 disjoint implementation with R1. Completed seven-new-path candidate on checkpoint317351e7: [draft report](evidence/n4a-draft-386029/REPORT.md), manifest SHA256 dac8d6bd2b5541a3779c255725fe74101ad323bbdfd084c464293684635fd00c. Codex argv and early prompt refusal, fresh/role/build subclass guards, unclassified terminal outcome, existing validated/supervised entry reuse, pinned source-only recipe and dedicated inventory-backed tests. All 1,144 existing base files byte-identical; no shared edit or protected import. K D notice M386030 consumed, acknowledged M386032; D-first ownership preserved.

Focused supported test-one on prepared interpreter: 14 collected/executed/passed, zero failures/errors/skips, 0.445947458 measured seconds. Explicitly unaccounted draft per M386027 and owner; future group manager-pure, registry and accepted accounting at serialized join. Exact logs, collection/per-ID summary, source header and recoverable candidate retained. No builds, engine, credentials, provider calls, resume or protected Git mutation. Scratch retained, no launched adapter process or container to clean up.

Next bounded milestone: independent draft assessment, then joined accounting/acceptance only after D accepted/imported human checkpoint. Shared version decoder, delivered credential slot, host role/fresh guards, policy/registry/docs remain join work under J2; inherited version decoder still rejects Codex prefix. Home/session paths deliberately refuse until evidence/integration exists; current policy still refuses Codex composition. J1 credential-path source selection and N4b exact-build turn parsing stay gated. No native qualification or completed joined adapter claimed. Required recovery bytes are in the dossier; human checkpoint/backup pending.


## 2026-11-24 — completed bounded N4a join (baton.codxpc, E386051)

Supersedes the pending join milestone only. Exact candidate `sha256:e9e9c84f39ddaf2cd7aa4f358d68682dd27eb45bf51e04eef4cb5dc3b465657f`, 17 paths on ac034bc1: [report](evidence/n4a-join-386051/REPORT.md), manifest and full candidate archive retained. Shared hooks/host guards consume D's accepted interface under M386027 and the ownership agreement; D-first checkpoint observed. No protected product import. J1 credential/managed-path selection and N4b parsing remain gated; no builds, credentials, provider calls or resume. W386048 remains separate, with its implicated shared methods unchanged.

Final focused verification: 391 collected/executed/passed, 35.446493069 seconds, zero skips/errors/unaccounted or source drift. Earlier accounted affected groups: manager-pure 4522/4532 and tools-pure 3651/3691 passing; all tests executed, no skips, no drift. Two candidate inventory omissions were corrected and pass in the final focused run; the other 48 outcomes independently reproduce on the unchanged base. No broad-group green claim or waiver. Complete failure classification and logs/ledgers/source identities retained. Initial fixture-root Git-discovery incident, refused outer checkout attempt and audit limitations are disclosed in the report; final HEAD unchanged and index diff empty, run process groups absent.

Next bounded milestone: independent exact-candidate review through baton.decide. No confirmed uncorrected candidate defect from these checks; broad baseline failures remain a verification limitation for reviewer disposition. After acceptance, owner import and human checkpoint remain pending; suggested commit message: `Add bounded Codex adapter hooks and joined offline coverage`. Full suite/native qualification is not selected. Last parent discussion read M386053 (our test-path notice); final handoff/disposition follows.


## 2026-11-25T00:09:08.753765+00:00 — incident correction, M386056 I1 (baton.codxpc)

The earlier account that no successful protected mutation was observed is **incorrect and superseded**. The protected-repository fetch succeeded: it created `refs/baton/source/main` at `821fe1b94e4ea58e8b4a7670a16ee5dd64b2fb79`, wrote loose objects (prefixes `53485ec9`, `a2f63724`, `821fe1b9`, `51915b90`, `aa86046a`, `cb9f9f62`) and pack `pack-90ca7232…`, and rewrote `FETCH_HEAD`. **Only checkout was refused**, because tracked files were dirty. Evidence source: K independent review M386056, review-2026-11-24T23-40-10Z.md, I1, observed local 16:07:09–16:07:10.

My HEAD/index audit was insufficient to support the original conclusion. I accept the correction and responsibility for selecting unsafe fixture roots. The original prose and original JSON fields are preserved as history; JSON now appends a dated correction. The exact original JSON is retained under finding-v12-git-fixture-isolation/evidence/. Review observed no HEAD/index/tracked-file damage, but that does not negate successful metadata mutation. Object/pack contents and config remain uninspected here. No protected ref/object/FETCH_HEAD/config cleanup was performed or is authorized; inspection and disposition belong to Slawomir.

Tracked separately as W386057, dossier `work/records/2026/11/finding-v12-git-fixture-isolation`. No affected-group rerun. Accepted N4a `sha256:e9e9c84f39ddaf2cd7aa4f358d68682dd27eb45bf51e04eef4cb5dc3b465657f` and its 17 files/archive are unchanged; M386056 accepts those bytes. W386048, J1 and N4b remain separate.


## 2026-11-25 UTC — bounded J1/N4b qualification preparation (baton.codxpc, no claim)

Owner requested planning only. W385830 remains queued at baton.decide; no claim/routing change. K confirmed packet-only ownership M386064 during exact N4a import, acknowledged M386065. Completed [one qualification packet](evidence/qualification-preparation/README.md), identity `sha256:f9d41f9caa43bf5b1d6d870d98d48ef55a1ca6c7a22d81af4a465e76746b6460`, archive sha256 `fa46fc0a659734279e396c7510bd5e9e24a154772a35ee6e29829113ecc98dea`. Pins accepted e9e9c84f 17-path archive/base and retained exact Codex 0.169.0 image/inventory. No accepted adapter/shared-file writes.

Stage A proposes explicitly selected network-none login help/status tracing in empty homes, with exact-build subscription-loader/source corroboration before any credential path is accepted. No filename/schema guessed. Stage B proposes one bounded fresh CLI invocation to capture actual terminal/contributor sources and verify implementation role plus delivered instruction digest through the same accepted label/argv functions. It is a protocol-capture harness, not a native Job or N5 image qualification. No successful output fixture is invented; missing contributor evidence or unobserved terminal classes remain gated. The one invocation may use multiple internal provider requests; no automatic retry.

Owner selections remain: exact credential source/custodian and seeded-copy/refresh/retention policy; accepted credential/backend and managed-path evidence; explicit model and later exact reported-identity mapping; offline and live execution authorizations, network/posture/limits/run roots. Reviewable scripts render argv only by default and refuse null selections; execution payload remains unrun. Detailed evidence, redaction/quarantine, cleanup/cessation and acceptance criteria are in README. W386048/W386057 remain separate; protected metadata disposition is untouched.

Validation: 22/22 static preparation checks, 0.001910530 s; AST/input hashes/pure renderer only, not product-test or runtime qualification. No builds, containers, credential reads, provider calls, Git mutations or product test groups. Next milestone: owner/K packet review and possible Stage A selection; Stage B stays gated.


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


## 2026-11-25 — actual Codex image build refuses provider_policy COPY

Owner-run product-image packet failed after11.325s with exit1, not timeout. Retained 04-build.stderr at /home/sl/baton-qualification/w385830-codex-product-ad6dcad0-1 shows COPY python/src/baton_v12/provider_policy refused. The directory exists in the exact committed ad6dcad0 export, but v12/.dockerignore omits its re-include. This is a product build-context defect, missed by the preparation preflight; source-only recipe checks did not establish buildability. It also affects any recipe copying this package with that context. Required product correction: include exactly python/src/baton_v12/provider_policy before cache exclusions and preserve exclusion of bytecode. No broad context widening.

Read-only engine checks after failure: the helper's exact temporary image tag is absent and no product-probe container bears this run label. This is not a claim that all legacy-builder intermediate containers or dangling layers were removed. Logs show ordinary synchronous build failure and no timeout/cleanup exception. No automatic retry, pruning or protected Git mutation.

Interactive coordinator prepares revision2 using a fresh run root and an explicit, retained build-context-only .dockerignore patch in the exported source. This is a disclosed qualification stopgap pending product correction/review/checkpoint; it does not silently amend accepted source or enable native use. The first packet and run remain intact.


## 2026-11-25 — owner selects interactive C1 import

Slawomir explicitly selected import here of the seven accepted paths from candidate 7f45e1e5, plus only its credential-lifecycle DESIGN paragraph with a FINDING link. Preserve the existing42 DESIGN lines and stage them separately from this change. The ruling is configure once, manager seeds a new Job/worker home only at first initialization, retained/refreshed credentials survive restart without reading the source, and missing or incomplete state requires explicit recovery rather than automatic reseeding. Qualification launchers automate the selected copy. No writeback to the credential source; no real credential or live-call authorization. C2 first-initialization failure recovery and C3 delivery size mismatch remain open before Codex activation. The interactive import selection is limited to these accepted bytes and this approved DESIGN paragraph; no protected Git mutation by the agent.


## 2026-11-25 — owner-selected credential lifecycle correction (baton.codxpc, E386081)

Owner instruction following M386079 selects automatic first initialization only, source-independent restart preserving refresh, explicit recovery for lost credentials, and automatic copying in qualification launchers. Supersedes seed-if-absent and manual per-Job staging prospectively; old packets/evidence remain immutable. Ruling and acceptance are pinned in [RULING-AND-PLAN](evidence/credential-lifecycle-386081/RULING-AND-PLAN.md), prepared before candidate implementation. Candidate/report: [REPORT](evidence/credential-lifecycle-386081/REPORT.md). This selects no real credential access, source, model, build, engine/provider call, native-use qualification or resume implementation.

The first seed now runs during host preparation, under durable initialization intent outside the worker mount. Both host and worker receipts bind the credential path; retained restarts inspect metadata only and never resolve the original source. Missing/corrupt/incomplete state requires explicit recovery, including crash after copy before final receipt. No automatic migration of unmarked seeded homes. Legacy delivered Claude credentials retain their prior behavior. Product lifecycle/helper and successor launcher are synthetic-verified draft bytes, awaiting independent review and coordinated exact import.

Observed human build-context checkpoint: c1727ad68ffa0f5015b07f27202a66be00848143. No protected Git mutation by codxpc. W386048/W386057 remain separate.


## 2026-11-25 — owner selects qualification model and credential-copy source

Slawomir explicitly selected gpt-6-astra as the qualification explicit_model, matching the model-related setting read from codexpc config.toml. Earlier in this conversation he authorized the qualification launcher to automatically copy /home/sl/.codex-pushcoin/auth.json into its private retained home, leaving the source unchanged. Reference: codex-pushcoin-subscription; custodian Slawomir. No credential file was read or copied by the coordinator.

Current editable selection draft: config/qualification-selection.json, based on the accepted lifecycle successor template. explicit_model is set; live/offline execution authorization fields remain null, as do unresolved placement/refresh/retention/settings. Existing image/source defaults in that draft are historical template values, not newly selected image/runtime authority; the final launcher must reconcile them with accepted product-image evidence and committed lifecycle source before execution. No live model call authorized. Reasoning effort was not separately selected by this model decision.


## 2026-11-25 — owner requests configurable Codex fast mode

Owner requests a way to enable fast mode explicitly through configuration. Add a separately selected service_tier beside explicit_model; the interactive coordinator added a null field to config/qualification-selection.json to record the unset selection, not runtime support. Current CLI documentation describes service_tier=fast via -c; exact pinned0.169.0 support and request behavior remain to be qualified. No fast mode or live call was selected by this capability request.

Bounded implementation requirement: optional fast tier must be carried from JSON through validated adapter configuration into the exact argv (Codex -c service_tier="fast"), with identity binding, consistent qualification launcher rendering and requested-tier reporting. Unset preserves existing behavior; do not describe unset as proved Standard. Reject unsupported configured values; do not infer actual tier from requested configuration. Preserve legacy identities/behavior when unset if feasible, otherwise disclose the admission compatibility consequence. Tests should prove forwarding, refusal and unchanged unset behavior; help or mocked evidence is not proof the server honored fast mode. Update owning contract/DESIGN consistently before product implementation. Coordinate with codexpc current qualification packet and avoid a separate unrelated feature expansion.


## 2026-11-25 — independent service-tier review and successor preparation (baton.codxpc, E386092)

Owner selected independent review of K M386090 and a credential-free offline proposal, with no engine/provider execution. [Review](review-2026-11-25T02-52-55Z.md) accepts exact candidate `sha256:9c365d72625de16e193198d2f1938d82cc51cedad59d3dd54f1cd259db66c458` (8 paths, base1ed26970e74ea48013e3e533e057e6ace08d0058) for owner import/checkpoint, not native qualification.604/604 independently collected focused tests passed in61.768519333s, with no skips/unaccounted/source drift. Independent unset snapshots match byte-for-byte. Candidate and main product unchanged.

[Successor packet](evidence/qualification-tier-386092/README.md), `sha256:8b9c0492453d2c574d81b4f90ca36008b91625d1eabd4187b0925651aa68323d`, applies LAUNCHER-DELTA only in new files, carries automated credential copying and pins the exact base plus reviewed overlay.29 static/mocked checks, two source-only context generations and code-only lifecycle pin check pass. Requested-tier metadata must match actual argv. No prior packet was altered.

Correction to the offline-evidence interpretation in M386090: exit0 or help acceptance cannot establish service_tier recognition; unknown overrides may be ignored and help may bypass loading. No authoritative effective-config surface or exact-build loader proof is retained. [Offline proposal](evidence/qualification-tier-386092/OFFLINE-CHECK.md) provides exact network-none help discovery and the required typed-effective-config/unknown-key/ignore-user-config matrix. The effective-config command remains unresolved until exact-build help/source proves one; no guessed diagnostic or exec turn is selected. Recognition, effective requested config, and actual served tier stay distinct; fast is not selected.

Current FINDING source/model selections are preserved; none were read/used for credentials or provider execution. Lifecycle C2/C3 remain open before Codex activation. J1/N4b/native use, W386048 and W386057 remain separate.


## 2026-11-25 — owner-selected interactive service-tier import

Slawomir asked the interactive coordinator to handle the accepted import here. Imported exactly eight paths from9c365d72 after whole-set candidate/archive/base/drift/type/mode preflight. Independent acceptance M386094 (review-2026-11-25T02-52-55Z.md),604/604 focused checks. Final eight hashes and modes equal reviewed bytes; no reruns on the host with unrelated W386057 edits. DESIGN and other source edits preserved. Evidence/import-9c365d72 contains preflight/postflight and human-only selective checkpoint script. No protected Git mutation, image/build/engine, credential read or provider call. This accepts configuration/forwarding only: pinned CLI recognition, actual served tier, C2/C3, J1/N4b and native qualification remain open. Current draft service_tier=null is not selection of fast mode; successor maps unset to omitted product field. Next milestone: human checkpoint, then the bounded qualification successor, not additional feature scope.


## 2026-11-25 — qualification next offline packet (baton.codxpc, E386097)

Observed human checkpoint f875ed01b51b6b7541ad169b560004e47731ad34; all eight service-tier candidate paths match accepted9c365d72 exactly. This supersedes the pending tier-import/checkpoint status above. [Bounded packet](evidence/qualification-next-386097/REPORT.md), `sha256:451a4f08983e1643c7626616a898b20979b9a12b76871cad9ba9a82086cd90e0`, carries gpt-6-astra and the already selected codex-pushcoin-subscription automatic first-copy source; source unchanged, refreshed retained copy preserved, no silent re-seeding. Fast remains unselected. No product or earlier packet edits.

Next executable milestone, pending execution selection: exact credential-free help-discovery in retained17d250b7 image, network none, UID:GID1000:1000, fresh /var/tmp/baton-codex-tier-discovery-386097. Exact commands/settings, discovery-versus-recognition pass/unknown rules and bounded cleanup are in the packet. No authoritative typed effective-config diagnostic is yet established; exit0/help/schema alone cannot close recognition. No engine, builds, credential reads or provider calls performed. 54 source/static packet checks passed; prior604/604 product evidence reused, not rerun.

Only remaining combined-live choices: proposed runtime/image/placement settings (46a46ee4 CLI/tool image, f875 host-generated detached harness, not older image worker code), private registry/custody/refresh disposition and subscription attestation, then explicit live/network execution selection. Model and source/copy do not need reselection; no fast or reasoning override proposed. Exact live renderer reconciliation is a mechanical prerequisite before execution, not an invented selection or a runnable claim in this offline packet. J1 requires authenticated same-run success after local status; N4b requires actual turn/contributor evidence, with role/instruction digest checked in that single turn. C2/C3/native activation, W386048 and W386057 stay separately gated. Ownership notice M386098; last incoming discussion M386094, canonical scope E386097.


## 2026-11-25 — owner selects direct live qualification here

Slawomir explicitly said run here after the offered M386099 settings: one network-enabled gpt-6-astra invocation, automatic private copy from ~/.codex-pushcoin/auth.json, fast unset, turn180s/outer255s, no retry, private evidence/home retained pending classification. Coordinator prepares and executes the detached harness directly, no managed handler impersonation. Image46a46ee4 with overridden entrypoint, f875ed01 source functions, UID1000:1000, HOME/run/baton/provider-home with codex/auth.json and instructions/WORKER.md, fresh /var/tmp/baton-codex-q1-live-386097, receipt outside mounts. Source remains unchanged. Native composition/attribution acceptance not implied; C2/C3 and N4b stay gated. Source registry is private reference/path JSON outside mounts, created automatically.


## 2026-11-25 — direct selected live probe completed

One selected detached Codex call succeeded (11.23s), local login and service-backed completion proved; delivered instruction digest/length/role matched. CLI turn_context records gpt-6-astra; stdout has no model field, so backend identity is not independently attested. Container/network cleanup completed; source credential metadata unchanged. See [report](evidence/live-probe-prompt/REPORT.md) and safe RESULT.json. J1 selected authenticated-success criterion met; N4b and native activation remain gated. Raw evidence/home retained privately outside repository, no retry.


## 2026-11-25 — bounded N4b terminal interpretation selected (baton.codxpc)

Owner confirms M386103: implement observed terminal parsing with explicit missing attribution; turn_context.model is configuration/context diagnostic only, never contributor evidence. Contributor requirement and acceptance hold remain unchanged. E386104 routes, E386105 claims, M386106 confirms K ownership. Independent candidate at f875ed01; Codex adapter, dedicated tests/fixtures and Codex provider documentation allocated. No shared Claude edit planned; no DESIGN/W386057 edits. Retain sanitized exact-build fixtures only; private raw sessions and credentials remain outside repository. Focused manager-pure/tools-pure verification; no provider/build/native execution. Current milestone: complete bounded candidate for independent review; attribution participation gap and native qualification remain gated.


## 2026-11-25 — bounded N4b candidate ready (baton.codxpc, E386105)

Completed eight-path candidate `sha256:5539eef92754e69d38e93c79abd6e020f9ed5368cc0b23f423beb9fc8da5fbe1` on f875ed01b51b6b7541ad169b560004e47731ad34. [Report](evidence/n4b-386105/REPORT.md), archive/manifest and sanitized exact-build fixtures retained. Owner-confirmed M386103, routing E386104 and ownership M386106 consumed; last thread read through M386106. Terminal completion recognized only for the observed complete bounded event family. Codex contributor evidence remains explicitly missing; turn_context.model is not participation, and host acceptance stays held. No production realization, session reader, resume, fast selection, Claude worker edit or protected source import.

Final focused manager-pure/tools-pure selection:380/380 collected/executed/passed in37.196738566s, no skips/unaccounted/drift. First380/380 run in37.297730094s retained but superseded for a concurrent documentation change/source drift; total74.494468660s, no broad group/full run. Twelve Claude attribution snapshots byte-identical to base. Five isolation inputs inherited in disposable source only and excluded; fixture root empty, private evidence/home preserved. No additional provider/build/engine/native operation or credential read.

Next milestone: independent exact-byte review of the complete bounded candidate, then owner import/checkpoint. Pending suggested commit: `Parse evidenced Codex terminal completion while holding missing attribution`. Actual participation source remains a concrete acceptance gate; native realization/image/combined pipeline qualification, C2/C3, shared-login refresh and explicit Claude qualification remain open. Fast and resume stay unselected; W386048/W386057 remain separate.


## 2026-11-25 — offline participation investigation (baton.codxpc, E386111)

Observed N4b checkpoint99b69626a44e806860abadc2854920914f1cf0dc and consumed K acceptance M386109. [Report](evidence/participation-386111/REPORT.md), evidence packet `sha256:ffdead6647a64d9e71ba3a2068d91fae433c70e71960f4399422c0a0d89194e7`. Inspected selected seven-event stdout and25-record session structurally, preserving private content. No actual-participation model field established. Additional model mentions are base-instruction provenance, world-state/collaboration settings and thread_settings_applied; they do not supersede M386103. Two token_usage_record entries have distinct response IDs and a common turn ID, but neither names a model. Proposed future binding requires each actual service receipt plus attempt/candidate and host-revalidated evidence, never configuration substitution.

Local installed package is0.172.0, not executable proof for0.169.0. Local app-server schema has an unqualified model/rerouted lead, not exact-build provenance or actual-generation semantics; client attestation is not backend attribution. Exact-build source/export semantics and private provider-store contents remain unestablished/uninspected. Do not turn this bounded absence into a claim that the binary exposes no source anywhere.

Next bounded milestone: review evidence gap, then separately select the prepared credential-free pinned-image version/app-server-help/debug-help probe or exact-build source inspection. Prefer supported offline export of the existing responses; authenticated existing-response retrieval only if supported and explicitly selected; a new turn only after proving a diagnostic can capture the missing service field. No new turn recommended merely to repeat stdout. Product unchanged, no tests rerun, no engine/build/network/provider operation or credential-content read. Attribution stays missing; native activation, C1 and all other qualification gates remain unchanged. Last incoming discussion M386109; scope notice M386112.


## 2026-11-25 — exact-build deeper help complete (baton.codxpc, E386116)

[Report](evidence/participation-help-386116/REPORT.md), packet `sha256:62d29d7b9b2d6300b3d3623b0c10fe1decdc5d4b43bd7b9509a9e870632c42a3`. Retained17d250b7 image: Codex0.169.0 version and generate-json-schema/debug app-server help passed once each offline. Zero connect syscalls observed, network none enforced, no credentials/model/daemon; exact container ceased/removed and label absent. Source unchanged.

Documented export prepared only: `codex app-server generate-json-schema --experimental --out /schema`, proposed fresh64MiB schema tmpfs, empty home, same pinned image and bounds. Latest owner wording selects preparation, not export execution. Debug lists send-message-v2 only; no retrieval established. No actual model-participation field was exposed by help; exact-build schema/semantics remain pending. Configuration fields never count; current attribution missing/acceptance held unchanged.

Next bounded milestone: select offline schema export and inspect actual response/model fields, requiring service-origin generation semantics and response/turn/attempt binding before any participation change. No live call or native activation. Scope notice M386117; last canonical handoff E386116/M386113.


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


## 2026-11-25 — configured-model attribution candidate (baton.codxpc, E386137)

Observed owner checkpoint b5ca8e12eac41c93c6a9f115a480f8ce32e04f15; consumed accepted amendment M386135 and R1–R3/C1 addendum. [Report](evidence/attribution-386137/REPORT.md). Complete 12-path candidate `sha256:79b648fed4c6e2cb5abb40948fd8bc0089c249dd83143dfb7a5e83041332c4e1` retained with exact archive/manifest/diff. Independent disposable source only; shared product targets still match checkpoint. M386138 coordinates candidate ownership; K/owner retains shared import, no overlapping edit performed. Five inherited isolation prerequisites retained separately and excluded from candidate.

Codex /2 configured-model basis is selected by admitted provider, bound to exact measured build/image/selection and separately retained content-free invocation receipt; actual participation unknown, contributors empty. Unqualified consistent build refuses. Host reparses complete supported stdout and checks receipt; known source-defined reroute error refuses, silence means only no reroute observed. LF-only parser includes C1. Existing Claude /1 participation and legacy behavior remain. Original producer evidence survives recovery and real deterministic Codex-to-Claude pipeline checks; missing Claude contributors still block verdict. No production realization/image/native activation enabled.

Final focused verification:626 collected/executed/passed in43.752878s, zero skips/unaccounted/source drift, groups manager-pure/tools-pure/job_manager. All logs/ID ledger/header/source identities retained. Prior624-case runs had2 new pipeline failures then1 stale metadata-fixture error, corrected without baseline waiver;132.612843s across three accounted runs. Developer smoke evidence/limitations described in report. Fixture root empty; no real credentials/provider/build/engine/native operation or protected Git mutation.

Next bounded milestone: independent exact-byte candidate review, then owner import/checkpoint under shared ownership and target drift preflight. Proposed commit: `Accept labelled Codex configuration evidence with retained invocation binding`. Native image/realization, expanded observed task shapes, joined native qualification, shared-login/refresh and explicit Claude gates remain. Current shared source remains pre-candidate; no historical evidence relabelled. Last incoming M386135; read through scope M386138.


## 2026-11-25 — checkpointed attribution; finite native-readiness route (baton.codxpc, E386143)

Observed d0760de6acdf9cd1e055d1f08137757adb223cc0: all12 accepted79b648fe bytes match; codex parser100644. Consumed M386141 review, canonical through E386143; scope M386144. [Bounded readiness plan](evidence/native-readiness-386143/PLAN.md), checkpoint verification retained alongside. No source/runtime operation or test executed.

F1 is first: prior candidate accounts bind image to admission only, not retained launched-image observation. This corrects any reading of the earlier implementation entry as proving engine image identity. oci.py:1634 compares selected values; list validates engine image then drops that field in its returned record. I1 retains host engine/runtime/attempt/start/image evidence and binds it to attribution and original-producer recovery, with separate admitted/observed diagnostics. No backend attribution research or relaxation.

Finite dependencies: I1 image binding → I2 production realization/home and credential-C2/C3 decisions/corrections → selected Q1 build/offline image gate → selected Q2 one editing capture → I3 observed parser fixtures/completion → selected Q3 final image → selected Q4 Codex implementation/Claude review/verdict. Three new provider calls proposed on the main route, none authorized now, no retries. Reuse authentication/instruction/path/source/model evidence; preserve adapter-reported CLI and unknown actual Codex contributors, stronger Claude evidence. Exact reviewed/checkpointed code required at each implementation boundary.

Open decisions: explicit failed-initialization recovery semantics; unified file credential size/representation; engine/build/live packets and Claude selection if unsettled; placement of separately bounded refresh/shared-login qualification. Shared-login or actual refresh is not proved by the first two-role Job or synthetic tests and remains an explicit unqualified scope, not silently waived. W386048 remains separate: prior M386046 says optional provider-selected integration is unnecessary for the selected two-role review/verdict endpoint; no integration call added. Review-C2/C3/C4 have finite ordinary dispositions in the plan. Fast/resume/W386057 remain separate.

Next milestone: review this packet and route I1 ordinary implementation under fresh claim/shared ownership; D1/D2 decisions precede dependent I2 changes. This planning claim does not implement or activate any step. No shared-file reservation, real credential read, build, engine/provider call, protected Git mutation or native activation.


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

## 2026-11-25 — Q1 build/offline packet prepared (baton.codxpc, E386185)

M386183/E386184 select preparation only from I2 checkpoint54fa5319. Claimed
E386185; ownership M386186 is new packet evidence plus append-only dossier,
with no product/shared-source edits. The complete packet is
[evidence/q1-preparation-386185/REPORT.md](evidence/q1-preparation-386185/REPORT.md).
All22 I2 paths match the checkpoint. Candidate archive SHA256
`5a9d8f8239ff1b65b2aa11445c19b7ef1e071b98c627677a5ca48973def34b0d`
contains27 paths; execution payload manifest SHA256
`95b750b5484d247f29b9c364bbcc0b9e051ceb1613fea1bc185cc03562930289`.

The proposed selected run is one pinned-source build and one production-entry
container through real manager/OCI owners, with synthetic Authority/login,
network none and UID:GID1000:1000. Real F1 engine observation must persist after
positive exact-container removal and manager reopen. Local build image/config-ID
binding is explicit; registry digest resolution is not guessed. The default
owner-run check has no engine capability. Deterministic preparation passed;
engine/image/native outcomes remain unknown. No build, engine operation, real
credential read, provider call or native activation occurred. Independent packet
review and owner execution selection remain separate gates. Existing attribution,
Claude requirements, baseline failures and finite Q2/I3/Q3/Q4 route are unchanged.


## 2026-11-25 — owner-selected local Q1 correction

B1/B2 corrected in evidence/q1-correction-prompt/REPORT.md, original preserved. One launcher keyword change; three end-to-end fake execute scenarios and two existing preparation scripts pass. Candidate 5b6db7649c2518a0d9142164c2641f67721a677b8425761dc6981ad0f57e0916, payload 07cdf3c098202c8f4f925d6868fc73450c4b63e87e5a2fc42a7799f2bb44697f. Independent narrow delta review next; no build/engine/provider/credential execution selected. Copilot direct scope M386190; no handler claim held.


## 2026-11-25 — Q1 executed once and passed

Owner selection M386193; evidence/q1-execution-386185/REPORT.md and RESULT.json. Image sha256:34364fb17d18b9abd1d155c33123888313a31141cc433322e68a7ad170a98fa7 from54fa5319. Real manager/engine receipt survives removal/reopen; offline identity/tools/home checks pass; container ceased/removed. Zero provider calls, synthetic credentials only. No native Job qualification claimed. Next: concrete Q2 editing-capture selection packet; no execution selected.

## 2026-11-25 — Q2 fixed selections and complete preparation (baton.codxpc)

The owner's Q2 instruction carries forward gpt-6-astra, fast unset,
codex-pushcoin-subscription sourced from ~/.codex-pushcoin/auth.json, automatic
private first-copy into the Job/worker home and no source writeback. These are
settled choices; they supersede the earlier Q1 review wording that the model
and credential source still needed selection. Credential access and execution
are NOT selected. M386197 confirms packet/dossier ownership, E386198 resolves
routing and claim E386199 authorizes preparation only.

[Q2 complete packet](evidence/q2-preparation-386199/REPORT.md) proposes one native
editing attempt through the actual manager/file-exchange/production entry,
using accepted Q1 image34364fb1 and source54fa5319. Fresh private placement,
bridge egress without an allowlist,180s turn/15s verification/300s outer plus90s
cleanup, one CLI invocation and no retry are concrete proposed settings for
subsequent owner selection. Private raw evidence is distinct from a fixed public
projection; novel events and all acceptance remain held for private review.
Actual contributors stay unknown; stronger Claude requirements are unchanged.
No build, engine operation, real credential access or provider call was made.

Candidate archive79 paths, SHA256
`abb0f083ef37f1a6fd7a2985a8bc93f1b57786ddd1829fbd8668e5181d74fbfc`;
payload SHA256
`6841dc66747ab5c5bfc2c9ccd4a7f614bbdc93526b3ef2cbaad33b8921f42f14`.
Six accounted preparation checks pass; they include real execute-path negatives
and a real Codex adapter path stopped at the substituted provider seam. Synthetic
edit/terminal evidence is labelled and is not an invented successful provider
fixture. No product edit or acceptance relaxation. Q1's92 retained evidence
hashes verified read-only; I2 remains1237/1240 with its three baseline failures.


## 2026-11-25 — phase ending is not substantive success

Owner ruling pinned in evidence/phase-ending-owner-ruling/RULING.md: reviewer judgment of artifacts, uncertain judgment escalates to Slawomir; no inferred success from activity stream. Supersedes event-family enumeration as a phase-ending gate. Owner knowingly accepts current Docker-contained sandbox bypass/copied login/open egress posture, no egress restriction work selected. No new Q2 execution selected.
