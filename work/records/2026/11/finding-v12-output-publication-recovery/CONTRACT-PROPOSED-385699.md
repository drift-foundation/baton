# Proposed retained-output publication recovery contract

W385695 / M385696 / E385699, baton.codxpc, 2026-11-22. **For owner approval; not normative yet.** Source inspected: ce6e1b2bf12519a84a3792f06562b7727dfe3021; preserved Stage1-B candidate5bc260b6 is unaccepted and is not a runtime dependency. No product or DESIGN edit, tests, live operation or Git mutation in this preparation.

## Decision requested

Approve the exact REC-9 addition below and the bounded new recovery template/profile in section3. Coordinate the separately owned W385694 cap revision as specified in section6. Recommended mechanism: one new linked two-stage Job, deterministic **publication** then independent **review**. Publication uses a fresh authorized isolated worker with no model/provider invocation; normal completion, custody and collection run under that worker's new assignment. Neither completed implementation nor its still-valid verifier runs again. This avoids inventing success for the failed producer or relaxing the normal freeze preconditions.

This is an explicit owner-selected recovery execution, not an automatic maintenance launch or a change to normal execution-gate release. It preserves the original task identity and accepted source, not a fresh implementation task copied from an old prompt. Normal review can inspect and test the candidate as its substantive obligations require; “reuse verification” means the recovery pipeline does not blindly re-execute the already successful required verifier.

## 1. Exact proposed normative amendment

Add after REC-8 in v12/DESIGN.md, leaving REC-8 unchanged:

> **REC-9. Owner-approved retained-output publication recovery.** When implementation completed but output publication failed, the owner MUST be able to inspect the exact failure and retained output, approve a bounded corrective publication disposition, and resume publication, collection and independent substantive review without redispatching implementation. The original Job, task identity, admitted inputs, terminal, deadlines and evidence MUST remain unchanged. Recovery is a new linked execution with separately selected finite limits and current authority, never publication on behalf of a stopped or revoked generation.
>
> The decision MUST bind the failed execution and command, retained candidate and output bytes, verification evidence and context, corrective output declaration, selected stages, profile identity/digest and review requirements. The manager MUST validate owner authority through its owning API, positive prior-writer cessation and resource exclusion through the host owner, and retained identity/integrity through the selected artifact consumer. Missing, inaccessible, invalid or unknown evidence MUST hold explicitly. A copied log or owner assertion alone is not proof that a verifier ran on the selected candidate.
>
> An explicitly selected deterministic publication execution MAY adopt valid retained output under its own fresh assignment and output declaration, preserving original producer and recovery provenance. It MUST call neither the implementation provider nor a verification command whose successful evidence remains valid. Its successful publication and new custody are not retrospective success of the failed execution and do not establish independent acceptance. Valid publication MUST automatically hand the exact candidate and attributable evidence to the selected independent substantive reviewer. Invalid or unknown verification requires explicit owner disposition; it MUST NOT trigger blind re-verification or implementation.
>
> Recovery admission, publication, custody, collection and review handoff MUST have stable replay identities and durable intent before external effects, with restart reconciliation at every effect boundary. Cancellation, expired authority or uncertain cessation MUST prevent new conflicting effects. Old deadlines MUST NOT be reset. Recovery failure or expiry MUST retain evidence and return an owner item without automatic retry or recursive analysis. Repeated requests MUST neither duplicate publication/review nor alter an already bound decision. Status MUST distinguish original failure, recovery progress, custody and review outcome. ART-7 execution release, ART-8 evidence adoption, DB-3 through DB-5 and REC-1 through REC-6 continue to apply.

No change to ART-8 is needed: it already permits a later authorized consumer to adopt useful evidence without claiming the old execution succeeded. REC-9 supplies that bounded supported path. This does not generalize to arbitrary failures, verifier corrections, partial implementations or edited candidates.

## 2. Admission and evidence contract

Eligible first slice: a real failed output-publication boundary with completed provider execution, a complete retained final proposal and attributable successful required verification. Not a provider timeout, verification failure, clarification yield, ambiguous provider outcome or cancelled producer. A cancelled producer or changed/invalid candidate is held for a separate owner disposition; approval is not permission to override cancellation. Failed/unknown verification is outside this slice and remains REC-8/owner handling.

Read-only inspection resolves from authoritative Job/stage/episode identity, never a caller-selected arbitrary host path. It composes published manager/control evidence and the existing source-profile reader. For preserved copies, an explicit typed retained-evidence reference binds the failed execution and original locator to the copied manifest; normal containment and byte verification still apply. The W385624 dossier hashes/reconstruction prove source bytes, but an inspection must also establish the required verifier-to-candidate/task binding from retained execution evidence. If existing records cannot establish that binding, return that exact missing fact; do not mark W385624 eligible merely because this design exists.

The versioned inspection document contains:

- instance/authority/scope/Work, original task and admitted task digest, failed Job/stage/episode/attempt, command/input/policy digests and fault-terminal digest;
- original producer attribution; proposal tree digest, each retained file digest/length, original artifact locator identity, candidate/base/path-set identity from the source-aware consumer, final-submission evidence;
- successful verification result, exact argv and context digests, source candidate linkage, attributable start/end or explicit historical unknowns, output hashes and dependency/input bindings needed to judge validity;
- positive writer cessation evidence with observation time, unresolved launch/writer/resource facts separately, and original cancellation state;
- proposed new declaration/revision digest, recovery template/profile/digest, selected stages, publication adapter identity and supported reviewer binding/independence; explicit admission refusals and missing facts;
- canonical SHA256 inspection digest. Viewing does not grant custody, reserve a Job, alter a terminal or refresh stale observations into facts.

Approval binds the complete canonical selection, original inspection digest and exact new declaration/profile/stage set. Paths alone are never approvals. A changed selection requires a new decision ID; same-ID different-content is collision. Owner principal/scope come from existing trusted participant-bound Authority resolution, not caller-authored authorization receipts. Reuse the deployed approve-capability checks; if the public read-only authorization seam exists only in unaccepted W385624 bytes, independently deliver that minimal seam rather than importing unreviewed Stage1-B. No new broad owner-role or organizational policy.

Inspection may race storage changes: immediately before adoption, revalidate evidence and obtain host-controlled exclusive preservation of the retained input. Hold original material against writable reuse; release of execution is not permission to overwrite it. Copy/measure once through no-follow descriptors into private staging, validate staged bytes against the approved selection, then publish. Original files stay intact. No Git interpretation in core manager: bundle/commit/base/task semantics belong to the existing Git-aware consumer/source adapter in confinement.

## 3. Concrete revisions and finite execution selection

Proposed new identifiers, checked unused at the inspected source:

| Item | Proposed identity / selection |
|---|---|
| Recovery template | `baton.v12.job-template.output-publication-review/1` |
| Role descriptor | `baton.v12.development-role-contract.output-publication-review/1` |
| Recovery input/decision schema | `baton.v12.output-publication-recovery/1`, `baton.v12.output-publication-decision/1` |
| Finite profile | `output-publication-review/1` |
| Stage set | exactly `publication`, then `review`; no implementation/verification/correction stage |
| Profile fields | Job9960s including queue; stage4800s; review provider3600s; legacy verification ceiling900s (no verifier stage/call permitted); correction_rounds0 |
| Publication sub-bound | 900s from the persisted publication-stage start, inside the4800s stage ceiling; zero provider budget/calls for publication |
| Retries | zero automatic retry/correction/clarification continuation; restart reconciliation of the same effect is not a new attempt |

These are proposed selections, not inherited approval from documentation/1 or REC-8. The900s publication ceiling is a bounded engineering selection, not measured throughput for100MiB. Existing job_control fields can enforce ordinary stage/Job limits; the recovery descriptor supplies the publication-specific sub-bound. Admission binds both descriptor and profile; persists absolute origins/deadlines once. Use existing monotonic-watermark handling on clock rollback. Resume never renews a bound. Provider deadline starts at actual reviewer invocation, not dispatch or observed activity. Expiry retains partial/completed publication and holds the owner item; another execution requires a new exact decision, without repeating a completed publication if its custody is still valid (later review-only selection must itself be supported, not improvised).

Publication consumes a read-only retained proposal/evidence input. It emits identical proposal bytes and separately bound recovery provenance under fresh output declarations; metadata must explicitly say adopted/recovered and retain original producer identity. The generic worker completion is truthful: the new worker completed publication, not implementation. Review receives the newly held checkpoint; its candidate digest must equal the approved original candidate. Existing final-submission/review consumers must recognize this linked adoption without a fake implementation stage or fabricated old completion envelope. No extra proposal files are injected that change approved proposal digest; provenance resides in declared separate metadata/output. Proposal100MiB comes from W385694; every other output retains its explicitly selected existing bound and entry/link/media restrictions.

## 4. Public command and owner seams

**Proposed API, not currently runnable.** Extend the installed `baton-v12-stack manager` dispatch, using the existing instance selector and trusted participant context:

```text
manager publication-inspect --instance INSTANCE --participant OWNER --job JOB --stage STAGE --episode N
manager publication-decide --instance INSTANCE --participant OWNER --document SELECTION_JSON --decision-id ID --approve|--hold|--deny
manager publication-resume --instance INSTANCE --participant OWNER --decision-id ID
manager publication-status --instance INSTANCE --decision-id ID
```

`inspect` is read-only and emits the complete selection/refusal document. Owner reviews the digest-bound selection; `decide` records one approval/hold/denial, launching nothing. `resume` atomically records manager admission intent, rechecks current authorization, cancellation, host exclusion and exact selection through their owning APIs, allocates a deterministic successor Job/Work identity, binds installed execution adapters and submits the two-stage plan. An approved decision alone never bypasses admission checks. Once admitted, the persistent manager progresses publication→review automatically; no owner messenger between stages. Same `resume` repeats report/reconcile the existing lineage, never creates another Job. `status` reports exact pending effect, blockers, custody and review, not just a success flag. Existing manager start/serve lifecycle remains; no new launcher, raw-store scripts or per-run bootstrap.

Ownership mapping:

| Responsibility | Existing seams to reuse / bounded addition |
|---|---|
| Owner permission | Authority participant/capability resolution, actual Work scope; existing instance exclusion (`InstanceOwnership`) |
| Failed identity, cessation | exchange observation; attempts/tokens and retained stopped-settlement records; do not treat filesystem receipt as custody |
| Durable admission | JobStore signed operation journal and stable replay/identity reservation patterns; additive recovery admission owner |
| Generic byte safety | worker measurement, workspaces copy/measure, sealing and output/intake owners; normal new-assignment completion/freeze/collection |
| Payload meaning | Git-aware source consumer/proposal validation; no host-manager Git operations |
| Execution | tools/stage_execution.py composition with a deterministic no-provider publication adapter and existing reviewer execution |
| Independent checkpoint/review | review_driver.prepare_review, actual review consumer/verdict; exact candidate binding and existing independence enforcement |
| Status/CLI | tools/job_manager.py dispatch plus recovery wrapper; shared read interpretation and15s freshness policy preserved |

A fresh recovery Work is linked to the original Work under the same effective scope via the authority API, with the accepted original task digest in its immutable selection. It does not steal or finish the old claim. Manager coordinates authority, host and Job owners using intent/reconciliation, not cross-store SQL. No normal execution-gate release is made conditional on successful artifact adoption. Do not broaden this into W385625's verifier execution.

## 5. Restart cuts and focused acceptance

| Persisted cut | Restart behavior / required proof |
|---|---|
| decision written, caller loses reply | same decision/digest returns same result; changed operands collide |
| admission intent, authority/host action incomplete | reconcile exact idempotent owner operations; unknown holds; no second Work/Job |
| accepted submission, caller loses reply | resolve same reserved Job; no duplicate dispatch |
| publication launch intent, engine reply missing | observe exact runtime via existing host owner; never launch another while unknown |
| copy/measurement interrupted | incomplete staging is not custody; same operation resumes/reconstructs only private staging after excluding old writer; original evidence untouched |
| completion published, freeze reply lost | re-read exact new completion/custody identity and reuse same result; no replay of producer or verifier |
| freeze/collection complete, journal acknowledgement lost | compare immutable manifest/artifact and replay owner receipt, never synthesize one |
| review handoff reserved/dispatched, reply lost | reconcile same review allocation; no second provider turn |
| reviewer stopped/verdict arrived, caller lost reply | collect and attach exact verdict once; original Job stays failed |
| cancellation/expiry at any cut | revoke/fence active effects via existing host owner; preserve state; no new stage; status explains cessation/remaining effect |

Implement as one bounded connected capability after cap acceptance; admission-only or publication-only milestones may aid implementation, but cannot be delivered as “resume supported.” No broad recovery framework, recursive analysis or default retry.

Mandatory focused deterministic acceptance drives the **installed public command** through real participant authorization, persisted Job/control owners, production composition, normal publication measurement/custody/intake and substantive review result. Simulate provider/engine at their normal boundaries; do not replace command handlers, admission, sealer or reviewer result validation with helper stubs. The test reviewer supplies an actual format-valid substantive verdict tied to the checkpoint; green verifier or structural schema checks alone cannot satisfy acceptance.

Prove: preserved old terminal/input hashes; original candidate digest and valid verifier reused; zero implementation and verification calls; one publication and one independent review;100MiB proposal declaration and old revision immutability; unauthorized actor/scope, changed decision/input/argv/context/profile/stages/candidate, unknown/missing verifier binding, malicious paths/links/types, root replacement, size/entry overflow and stale cessation all refuse. Include cancellation races, expiry, disk/write failure, invalid/missing review verdict and every restart cut above with effect counters and canonical readback. Distinguish repeated reconciliation from repeated external work. Build/package focused command wiring is required, no live model or full-suite rerun. Retain exact test counts, failures/skips and measured duration, with candidate manifest and independent review.

## 6. Dependencies, ownership and delivery

W385694 should publish `baton.v12.development-role-contract.native-handoff.proposal100m/1` with `baton.v12.job-template.implementation-review/4` (unused at inspected source), preserving existing revisions. These names are **proposed** for joint owner selection, not another Work's unilateral implementation constraint. T385694 M385700 records the coordination proposal. W385694 owns the cap declaration/validator and implementation-review template/compose path. W385695 consumes that exact declaration, owning recovery CLI/admission, deterministic adapter, new recovery role/template and review wiring. Serialize overlaps in role_contract.py, templates/registry, pool.py, tools/job_manager.py and tools/stage_execution.py at actual assignment; implementations choose other necessary files within approved outcome. No concurrent edits to these shared paths.

Recommended dependency: W385695 depends on accepted W385694 before dependent implementation/combined qualification, not before this design review. Coordinator installs and reads back the graph edge when execution is allocated. No dependency on unreviewed W385624 or W385625; if reuse of their eventual accepted helper saves duplication, coordinate explicitly without creating a hidden gate. K's independent Stage1-B source review proceeds concurrently on pinned5bc260b6. W385695 is the joined acceptance consumer for inspect→approve→resume→custody→review. No graph mutation in this preparation.

After owner approval: pin REC-9 in DESIGN and exact selections in FINDING; complete/accept cap revision; implement the recovery path in isolation and independently review; qualify the deployed command; inspect actual W385624 evidence through it; owner approves that exact new selection, then resumes. Specification approval is not approval of an unseen deployment or live recovery execution. Current evidence and old instance remain untouched. If inspection cannot validate retained successful verification or writer exclusion, name the exact blocker and preserve the candidate—never reimplement merely to get past it.

Only pending product decision is approval/change of this bounded amendment and revision/profile selection. New numeric limits and reusable recovery template require explicit owner approval; ordinary implementation choices within the approved contract do not require renewed approval. No claim that a native resume command exists today.
