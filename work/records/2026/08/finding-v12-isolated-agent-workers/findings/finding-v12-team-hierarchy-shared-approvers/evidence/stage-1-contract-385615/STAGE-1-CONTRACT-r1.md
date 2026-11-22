# Stage 1 contract — retained verification failure to independent review

Proposal for K's independent check; E385604 / M385603, 2026-11-22. No coding or live recovery authorized. Behavior is owner-selected; wire names and bounded allocation below are proposed implementation contracts. Preserve accepted CONSOLIDATED-PLAN r2 (`76aa436a…`) and STAGE-1-CLARIFICATIONS.md (`b6adc6bf…`) unchanged. Authority: M385597–598/K review-2026-11-22T04-21-24Z.md; owner M385599 dedicated analysis role, M385600 finite analysis-failure endpoint, M385601 exact retained verification/review recovery; current FINDING/PLAN corresponding headings.

## 1. One complete outcome and its trigger

First usable result: retained candidate → automatic analysis → supported owner diagnosis/options/decision → linked isolated verification → automatic independent substantive review. A reader or analysis report alone is not acceptance. Bind “exceptional phase” to the existing execution stage; general typed phases, team forests and pool-control machinery are not prerequisites.

Trigger: a durably attributed terminal `verification-failed` execution with retained candidate, provider status0 and required verification failure. Concrete fixture: w9901-native-planning-1, candidate `7a030bc069ac570364c0d3e9e12d34b902ec2a44`, base `9fa0ec37a244a388a55be108fd73cb854846245c`, retained NATIVE-PLANNING.md SHA256 `dc2c516c298f0703f626361640f2caae44670e8e62956fd17cf328fe8cd618c4`; malformed Python argv exits1. Runtime destroyed/reservation released are checked through their owners, not inferred from verifier exit. Candidate/evidence validation failure is reported explicitly and never treated as eligible recovery input.

Proposed stable failure key: authority + Work + execution Job + stage + attempt + terminal-result identity. A successor's verification failure has its own key. Repeated publication/notification of the same ending does not create another analysis or owner item. Analysis-role failures are explicitly excluded from recursive triggering.

The original task, candidate, command, exit/output, deadline and failure remain immutable. The new behavior does not repair the historical Job in place, and this contract does not select a live historical recovery.

## 2. Authority and retained records

Use versioned records with bounded bodies and existing canonical identities/digest conventions. These are required facts, not a mandated table layout:

| Record | Required attributable facts |
| --- | --- |
| Failure/recovery item | Failure key; original Work/Job/stage/attempt/task; candidate identity, base and content manifest/digest; original verification argv and declared execution context; error/output locators; runtime/resource settlement references; current recovery disposition. |
| Analysis execution/report | Exact failure key and input manifest; configured role/participant/principal/pool/model/profile generation; analysis attempt/limits; diagnosis separating facts from hypotheses; options/tradeoffs/recommendation; proposed exact corrected argv/context if applicable; report/partial-output digests and ending. |
| Owner decision | Authenticated Slawomir principal and authority-derived scope/grant; operation identity; exact failure/report/candidate digests; original versus corrected verifier inputs; verification/review-only scope; chosen immutable limits/profile; any explicitly approved plan change; decision/result and provenance. |
| Successor intent/result | Unique successor Job/submission and verification/review attempt identities; failure and decision references/digests; exact retained candidate manifest; corrected verification input digest/context; consumed decision/effect; admission time/finite limits; verification output/exit and exact candidate delivered to independent review; refusal/uncertainty/review outcome. |

A candidate commit name alone is insufficient: bind and validate retained bytes and base/content manifest. Arguments, working directory, environment and tool/runtime selection must be bound where they affect verification; a command string alone must not hide changes to its execution context. Preserve paths as evidence locators, not authority to read arbitrary host files.

Dedicated **analysis** responsibility is configured through the existing agent-pool machinery with an explicit participant/principal, profile and permitted outputs; no hard-coded provider/model. It may inspect attributable retained inputs and write only its analysis report/partial output. It cannot mutate candidate/product/verifier inputs/execution state or authorize recovery. Host manager records state transitions; the agent supplies a bounded report, not store access. Unsupported/missing analysis binding is an actionable configuration refusal/owner item, not substitution of a coder or silent success. Independent review retains existing principal/context separation. Model/pool changes remain owner-only.

Slawomir's decision authority is settled. A generic “retry”, viewing/acknowledging the item, a review approval or an analysis recommendation cannot authorize a successor. The supported decision surface presents original verifier, exact correction, candidate and proposed verification/review scope before recording approval. If a phase-plan change is required, it must be explicitly covered by owner approval, not inferred from recovery permission. Denial/hold launches nothing; a later explicit disposition is a new attributable act, never overwriting old evidence.

## 3. Transition and effect contract

1. **Record/observe ending and schedule analysis.** Manager deduplicates by failure key and persists analysis intent before admission/dispatch. Consume retained evidence only through supported custody and ownership boundaries; unknown runtime/retention state remains qualified and cannot authorize conflicting execution.
2. **Analyze and deliver owner item automatically.** The configured agent receives the fixed input and produces diagnosis/options/recommendation. Owner-facing read/decision delivery is part of the product path—no coordinator arranging a review handoff. Failed analysis retains partial evidence and notifies Slawomir directly, with no automatic retry or recursive analysis. Original failure and analysis failure remain distinct.
3. **Decide.** Validate owner identity/scope and exact referenced inputs. Approval covers both corrected verifier inputs and the new verification/review-only execution. Changed inputs after approval require a new decision. A unique per-failure recovery admission fence prevents concurrent decisions producing conflicting successors; it is not a cross-store transaction.
4. **Admit linked successor.** NEW manager-owned admission, not `fresh-attempt`. Revalidate candidate bytes, decision, cancellation, finite limits, authorization and positive cessation/resource exclusion through owning APIs. Reserve unique identity and persistent intent, then reconcile binding/launch through existing owner boundaries. No implementation stage, provider coding prompt or implementation redispatch is permitted. Expired original deadlines remain unchanged; successor has its own explicitly selected admission/limits (section5).
5. **Verify retained bytes in isolation.** Materialize from the exact retained candidate/base into a new private verification workspace. Original custody is immutable; scratch/generated test outputs are separate. Execute only approved corrected inputs, retain exit/stdout/stderr and timing. Do not publish verifier-mutated source as a new candidate. Subsequent review consumes the same bound candidate, not an unverified changed workspace.
6. **Review or report renewed failure.** Successful verification automatically prepares independent substantive review with candidate, original failure, owner decision and verification evidence. Structural heading checks do not certify content. Existing independent review/acceptance rules remain; this contract never manufactures an accepted verdict. A successor verification failure creates one new failure-key analysis and owner item, **never an automatic further successor**. Each recovery round needs a new owner decision. Failed analysis again goes directly to owner without recursion.

Review rejection follows its existing authorized review disposition; it is not silently classified as this verification-failure trigger. General exceptional-ending classification and automatic analysis are an explicit later Stage2 outcome per the accepted addendum; provider failure, timeout, review outcomes and unknown cessation are examples to classify, not blanket new triggers here. W9901 cannot close without that later outcome or explicit owner disposition.

## 4. Replay, restart and safety

Exact operation retry returns the committed decision/admission/effect; changed operands under the same key refuse. Persist intents before external effects; restart resolves the same owner facts and effect identities. Lost launch/dispatch replies must not cause blind redispatch. Distinct stores retain their ownership; reconcile a partial multi-owner operation without inventing an atomic transaction across Authority, Job and control stores.

Cancellation of the target or successor blocks new admission; a cancelled execution is never revived. Recheck cancellation/ownership at admission and dispatch. Prior termination, outstanding-launch exclusion and resource release come from host control evidence; unknown is a hold, not proof of safety. New successor identity cannot evade an unresolved old writer or cancellation. Original terminal failure remains visible even after a successful recovery.

Fault cuts: ending notification → analysis intent → possible analysis launch → report publication → owner decision → successor reservation/binding → possible verification launch → verification result → review handoff. Each cut needs an observation/replay rule and exact effect identity; acceptance injects failures at these boundaries. Do not claim “exactly once” provider execution from message deduplication alone.

## 5. Finite limits — proposed initial selection, not an installed profile

M385601 requires concrete successor limits before coding. Proposed conservative initial values reuse existing finite native-control magnitudes, but form **new explicitly approved profiles**, not mutations of documentation/1 or native-handoff/1:

| Execution | Bound proposal | Clock origin |
| --- | --- | --- |
| Analysis | Job4800s; stage4800s; provider turn3600s; no automatic retry/correction | Job accepted analysis admission (queue included); stage execution admission; provider invocation start. |
| Verification/review successor | Job9960s; verification stage4800s with command900s; review stage4800s with provider turn3600s and any required verification command900s; zero automatic correction/retry | New accepted successor admission (queue included); each stage's execution admission; each command/invocation's real start. |
| Shutdown | Existing LIM-5 bounded120s shutdown attempt with unresolved cessation retaining the hold | Existing cancellation/expiry handling; not an extension of work time or proof of termination. |

Persist resolved profile identity/digest, admission timestamps and effective deadlines, per-invocation/command ceilings, correction policy and original-versus-successor linkage. Owner decision names the profile; admission checks exact agreement. Analysis/owner waiting must not pretend to extend the failed Job; an owner decision alone creates no live execution. No activity/dispatch timestamp substitutes for invocation start. Restart preserves admitted deadlines, not fresh clocks. Unknown timing holds admission.

**Remaining preparation:** K checks this numerical/profile proposal; the coordinator pins the reviewed finite profiles before dependent coding under the accepted scope. These are proposed implementation values, not a new product decision or a request for another owner approval. No profile is installed here. Configured concrete analysis participant/pool/profile is a deployment operand to validate, not a new product-role decision or permission to modify a live instance. Later model/pool deferral semantics are outside this narrow recovery contract.

## 6. Revalidated reuse versus new work

At source9fa0ec37:

- `job_manager/fresh_attempt.py:admit`, `_one_instance`, `_excluded`, `_authorized`, `_composed`: reusable admission/exclusion/authority patterns. `_composed` copies prior stage kinds/specification/limits; calling it for this recovery would repeat implementation. New admission must be separate and typed.
- `tools/stage_execution.py:ROLES`, `_held_workers` and bootstrap/composition accept implementation/review/integration, not dedicated analysis. Add bounded declared analysis capability/profile wiring; do not disguise analysis as an authorized coding stage. Existing templates/declarations must remain compatible.
- `authority/messages.py:respond` accepts one reply to a request from its destination; escalation has consumed that reply. New owner decision/effect record and reconciliation are needed, not a CLI alias for this function.
- `job_manager/review_driver.py:prepare_review`, `_quiesced`, `_destroyed`, retention/custody boundaries and existing review isolation are reuse candidates, not proof that a verification-failed candidate is already admissible there. Explicitly validate the new producer/result contract and same-candidate handoff.
- `job_control.py` and DESIGN REC-1–7/LIM-5 supply cancellation/exclusion/finite clock semantics. Preserve them; do not widen fresh-attempt or reset old limits as a shortcut.

No new broad scheduler, full phase-plan engine, team graph, pool redirect framework or generic launcher is necessary. Proposed normative delta is `evidence/stage-1-contract-385604/DESIGN-stage1.patch` (unapplied); it adds REC-8 for this selected behavior and references existing safety/limit rules. It does not rewrite later-stage policy or select the proposed numerical profile.

## 7. Bounded implementation allocation and acceptance

**Proposal only:** create three separately claimed child implementation Works under W9901 after coordinator authority/contract selection, named by outcomes below; do not fabricate Work IDs now. W385331 remains the clarification/discovery/continuation integration interface, **not** the assumed owner of exceptional recovery. If an existing Work is selected instead, explicitly amend its accepted scope and ledger before execution. No graph or claim allocation is changed by this document.

| Outcome | Dependency / ownership proposal | Focused deterministic acceptance |
| --- | --- | --- |
| 1-A: failure-key analysis pipeline | New W9901 child; owns trigger/configured analysis contract/report delivery. | Actual malformed-verifier fixture; one automatic analysis with exact evidence; duplicates/restart safe; analysis cannot mutate inputs; analysis failure retains partials and notifies owner once, no recursion. |
| 1-B: owner decision and retained successor admission | New child; depends on accepted1-A record contract, not live provider behavior. Owns supported read/decision surface, exact correction and manager admission contract. | Wrong actor/digest/argv/scope refuses; generic retry insufficient; decision replay/collision; cancellation/unknown cessation/expiry and concurrent admission safe; no implementation stage; profile pinned. |
| 1-C: isolated verification, review handoff and joined proof | New child; depends on accepted1-B and1-A. Owns verifier execution adapter, exact retained-review handoff and complete loop consumer. | Same candidate before/after, corrected command evidence, automatic independent review; no implementation redispatch; failed verification gives one new analysis/owner item; no further successor without new decision; faults at every listed cut. |

Shared manager/schema/composition files are serially owned at handoff; no parallel edits without an explicit path allocation. Implementers choose necessary paths. Reuse W16830 only for its separate attestation scope, not as recovery ownership. No full-plan or provider planning rerun.

Prefer native implementation→independent-review Jobs using the existing supported template to build each slice; implementing a future analysis role does not require the live runtime to have it first. Pin the source and use deterministic fake/replay providers/daemonless fixtures at normal boundaries. If the existing native execution path cannot deliver a particular retained result, report the exact unsupported operation and preserve it; do not silently replace native work with a manual courier layer.

**Joined acceptance:** scripted analysis demonstrates orchestration/evidence fidelity, not live diagnostic quality. The owner approves removal of the accidental newline from the exact original argv plus the verification/review-only scope; isolated verification passes five structural predicates; independent review judges substance. Original failure/candidate unchanged. Measured test durations and per-ID outcomes retained, including refusals/failure paths. Count zero courier acts and zero implementation redispatches. This is Stage1 acceptance only; full W9901 destination remains staged and open. K's contract check is next, before coding or execution selection.
