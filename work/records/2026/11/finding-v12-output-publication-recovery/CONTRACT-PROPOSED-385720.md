# Retained-output publication recovery — revised proposed contract

W385695, M385718, E385720; baton.codxpc, 2026-11-22. **Proposed; awaiting K delta check and consolidated owner selection.** This replaces CONTRACT-PROPOSED-385699.md as the current proposal; the previous file and its digest remain immutable history. No DESIGN or product change is made by this document. Source checked at ce6e1b2b; Stage1-B correction82e1cd87 is an unaccepted design reference, not a dependency.

## 1. Exact proposed normative addition

Add after REC-8 in v12/DESIGN.md; leave REC-8 and ART-7/ART-8 unchanged:

> **REC-9. Owner-approved retained-output publication recovery.** After completed implementation fails at output publication, the owner MUST be able to inspect the failure and retained output, approve an exact corrective publication disposition, and resume publication, collection and independent substantive review without redispatching implementation. The original Job, accepted task identity, admitted inputs, terminal, deadlines and historical evidence MUST remain unchanged. A new linked recovery Job reuses the original open Work and effective scope, with fresh execution assignments and separately selected finite limits. It MUST NOT publish as the stopped producer or claim that the failed Job succeeded.
>
> The trust root is the original attempt output held by the host owner, resolved from that attempt and read through its owner under positive writer cessation and exclusion. Dossier or other copies MAY be used only after byte-for-byte agreement with that original is established. A missing, unreadable, substituted or unverifiable original MUST hold recovery; an agent-authored manifest or copied artifact MUST NOT become the sole trust root. Original bytes MUST be protected from writable reuse and delivered read-only to the new execution.
>
> The owner decision MUST bind the exact failed execution/command, candidate and output bytes, adapter-attributed producer verification and context, corrective output declaration, selected stages, profile identity/digest and reviewer requirements. Producer verification evidence is valid for reuse only when the adapter's command from the read-only task and exit status from process wait are attributable to the exact candidate and context. It is producer evidence, NEVER independent acceptance. Reuse means the recovery pipeline does not repeat that producer verifier. The substantive reviewer MUST still perform required independent verification and investigation, including tests, under the selected command and invocation limits.
>
> The manager MUST validate owner authority, exact evidence, positive cessation and resource exclusion through their respective owning APIs. A separately selected deterministic publication worker uses no provider and invokes neither implementation nor the producer verifier. It adopts exact retained bytes under its own fresh assignment and declaration, preserving original producer and recovery provenance. Normal completion, custody and collection checks apply to this new execution. Review MUST remain non-runnable until attributable publication custody and the exact candidate handoff are validated; it MUST then proceed automatically to the configured independent substantive reviewer. Structural checks or reused producer evidence MUST NOT establish acceptance.
>
> Admission and all effects MUST have stable replay identities, durable intent and defined restart reconciliation. Cancellation, expired authority, uncertain cessation, invalid or unknown evidence MUST prevent new conflicting effects and be reported explicitly. Old clocks MUST NOT reset. Failed/expired recovery retains evidence and returns an owner item without automatic retry or recursive analysis. Status MUST distinguish original failure, recovery progress, custody and review outcome. ART-7 execution release remains independent of result acceptance; ART-8 explicit adoption, DB-3 through DB-5 and REC-1 through REC-6 continue to apply.

## 2. Eligibility, trust and retained input (G1, G2, N2)

First slice is a completed producer with failed output publication, a complete final proposal, and attributable successful producer verification. Provider failure/timeout, verification failure, clarification yield, explicit cancellation, unknown provider outcome or changed candidate are not eligible. No broad exceptional-ending redesign.

`publication-inspect` resolves Job/stage/episode → host-owned attempt/output identity through published owner APIs. It does not accept an arbitrary host path as authoritative. Host owner establishes exact original root identity, positive cessation, no unresolved launches/writers and preservation against writable reuse. Filesystem work happens outside database transactions. Original runtime exit alone is not byte integrity; copied logs and reconstructed commits alone are not authoritative verification attribution.

Inspection checks the original proposal/result/task/handoff/adapter invocation records. The Git-aware consumer in confinement validates commit/base/path-set and candidate correspondence; the generic manager does not interpret Git or scan the nominated source checkout. Copies must match original selected files including types, sizes and digests; missing original or any mismatch holds with the exact selector/path/operation. An operator cannot waive these checks by approving a copy. For W385624, the agent-made dossier bundle/archive remain useful preservation and source-review inputs, but do not alone authorize native recovery.

Valid producer verification attribution requires: adapter-produced record whose argv agrees with the read-only admitted task, exit0 from the adapter's observed wait result, exact candidate/base/content binding, declared context/input identity and unambiguous execution linkage. Provider-authored stdout or claims are not this evidence. `claude_agent.py`'s verification.txt/result.json are adapter attribution; verification.txt expressly asks the operator to rerun from the collected candidate. Code tested inside the producer may have been provider-edited and had access to credentials; its pass is not independent acceptance. Recovery preserves that producer account and skips only the pipeline's redundant rerun. The reviewer receives the evidence qualification and independently runs required checks, including that command if required by acceptance. Invalid attribution holds; there is no blind reverify or reinterpretation as success.

**Delivery mechanism:** after fresh recovery claim and host exclusion, the host owner stages only the approved original output/evidence through its existing no-follow copy-and-measure primitive into a recovery-owned input root. The source-aware adapter validates the staged payload. The staged input manifest binds original root/attempt, measured digest and owner decision; content is compared with the approved selection before launch. Mount that root read-only within `/input` using the normal input-manifest/containment contract; output and private scratch are separate. No writable original mount, no original output.json rewrite, no arbitrary extra delivery role. Private staging is not custody. Once staging is validated and immutably held, recovery may reconcile it by exact digest without rereading unprotected paths; establishing the original trust root cannot be skipped on first admission. No automatic deletion of originals or incomplete staging.

## 3. Revisions, stage vocabulary, lane and worker (G4)

These are proposed owner-selected additions, checked unused in inspected source. Existing identities/bytes remain unchanged.

| Contract | Proposed identity/change |
|---|---|
| Recovery Job submission | `baton.v12.job-submission/4`, with recovery lineage and exact ordered publication/review stages |
| Recovery template | `baton.v12.job-template.output-publication-review/1` |
| Recovery role descriptor | `baton.v12.development-role-contract.output-publication-review/1` |
| Recovery selection/decision | `baton.v12.output-publication-recovery/1`, `baton.v12.output-publication-decision/1` |
| Worker-pool revision | `baton.v12.worker-pool/2`, adding explicit publication lane/worker kind |
| Job store generation | proposed schema10 after current9, preserving old rows; older readers/writers refuse the newer store |
| Finite profile | `output-publication-review/1` |

Old submission/1–/3 retain their three-kind vocabulary. Only the recovery/4 shape admits `publication`, with exactly one publication stage followed by one review stage, one approved recovery selection and no implementation/integration/verification stage. Existing ordinary creation/submit/fresh-attempt cannot misuse the recovery profile or template. Older binaries must reject /4 and pool/2 instead of treating publication as implementation. The profile is admitted exclusively through the recovery owner.

Current scheduler._lane maps non-review to implementation and schema9 constrains lanes to implementation/review. The new revision must explicitly map publication→publication, never fall through. Pool/2 declares a dedicated deterministic publication worker/participant and profile, no provider configuration, credential mount or implementation instruction. It reserves publication capacity and its own principal; the ordinary implementation lane cannot serve it. Extend the schema-constrained allocation, pool-membership and affinity tables under the new generation, preserving old entries. Select/match installed worker/profile/input/policy/Work by the same exact rules as existing workers; a missing publication binding refuses admission. Deployment/role validators must recognize this new worker kind explicitly; unsupported configurations refuse. Initial deployment upgrade installs this reusable worker once, not per recovery.

Recovery publication consumes only the approved read-only retained input. It emits identical proposal bytes plus **separate** declared recovery provenance, with original producer attribution and the new publisher identity. It invokes zero models and zero producer-verification commands. It uses the normal fresh-assignment completion envelope, output measurement, sealing and intake. No manual freeze record and no fake implementation stage. Proposal100MiB and100-entry/media/link constraints come from W385694's exact selected declaration; unrelated output limits remain unchanged. Recovery provenance must have its own bounded descriptor (proposed16384 bytes/1 regular file, no links); it never alters the original proposal tree digest.

**Reviewer binding:** /4 explicitly names `publication` as the producer edge; the review driver consumes that stage's collected proposal checkpoint/result manifest plus the immutable recovery selection. Its candidate identity must equal the approved original. Implement this typed producer binding in composition/review consumer; do not rename the stage to implementation or look up a nonexistent implementation stage. Enforce reviewer independence against both the original implementation principal and the publication principal; a new Job must not erase the original producer exclusion. Existing review profiles still govern substantive verdict format and acceptance.

**Readiness:** review depends_on publication in the submitted graph AND has a closed recovery-handoff gate. That gate binds decision, failed attempt, original candidate, new publication attempt/result/custody/intake receipt and reviewer input/servability. It opens only when all bindings are present and valid, normal publication collection has completed, outgoing execution is ceased, and no cancellation/expiry/uncertain authority intervenes. Completion without custody or an unattached candidate never opens it. Projection, owed-acts and offer admission enforce the same gate; allocation rechecks current facts before effects. Before this mechanism is implemented, review stays blocked even if an operator journals a verification account or approval. Actual first sweep after approval MUST issue no review offer.

The unaccepted W385624 correction's closed-gate pattern is the reference: durable owner records, one projection, defense before allocation, no caller bypass. W385695 supplies its own positive publication-handoff predicate rather than importing candidate82e1cd87 or granting an unconditional open. Share the eventual accepted gate interface where practical; no dependency on unaccepted bytes and no weakening of Stage1-B's hold.

## 4. Reused Work, authorization and binding (G5)

**Reuse the original open Work and its effective scope.** This supersedes the previous proposal's fresh-Work choice. No new Work/link operation or separate scope is needed. New Job/decision/admission lineage attributes recovery while retaining original task digest and failed Job reference; history is append-only. Current original assignment is not silently stolen, rewritten or declared successful.

Use WorkAuthorization.work_of/project_work and the trusted participant-bound approve capability in the Work's own scope. Reject terminal Work, changed scope, unauthorized owner and cancellation. DeploymentBinding adds the recovery Job binding `like=prior_job_id`, preserving job_work_id/review_work_id, source identity and configured pool; the /4 binding adds exact recovery input and publication worker/profile. Servability must compare actual submitted input/policy/profile/task/Work rather than self-confirm a worker's own fields. This extends the binding owner for the new stage without changing `_disagreements` to tolerate wrong Work identities or per-recovery reinstallation.

Fresh assignments on reused Work still require the previous assignment to be ended/fenced through the Authority's existing exact-expect transition and positive host cessation. A host-only stopped-settlement receipt does not release the Authority claim. Reconcile the existing manager ending path through its properly bound participant Session.end (release/recovered), then normal authorized routing/offer/claim under a fresh generation; preserve the earlier assignment events. The recovery owner cannot impersonate the old participant or use raw SQL to make Work available. If that existing ending is unavailable or another handler owns the Work, report the exact held assignment and stop before publication effects. A serving composition must demonstrate the supported ending→fresh-claim path with real Authority APIs; a proposed factory that simply mints arbitrary Sessions is not acceptance. No new recovery-only takeover power is selected.

Read-only authorization helpers available only in unaccepted W385624 remain unavailable dependencies. Independently deliver the minimal public seam if needed, or reuse it after exact acceptance and ownership coordination. The required outcome is real authorized admission, not reliance on unreviewed code.

## 5. Timing and enforcement (G3, N1)

Owner M385703 selects **3600s for the entire reviewer invocation including tests and investigation**.20min is only an ordinary inspection estimate, not a timeout or reasoning budget. Implementation's approved7200s is unchanged and no implementation is run by this recovery.

Proposed remaining profile: Job9960s from durable admission including queue, stage4800s from persisted stage execution admission, correction/retry/clarification allowance0. Review-provider3600s starts at actual invocation, not activity/dispatch. **Each reviewer verification/test command is bounded at900s**, also bounded by the remaining3600s invocation and stage/Job deadline. The900s setting is not dormant and does not prohibit reviewer tests. Independent required verification remains owed until performed and accepted under the review contract.

Publication has an additional900s bound from its persisted publication-stage execution admission/start origin, not from restarting a process. The manager's job_control evaluation stores/derives this publication deadline and fences the stage when reached; the existing host token/engine owner enforces cessation. The deterministic worker's command supervisor receives the same absolute deadline and terminates its child at the remaining bound, with host enforcement covering worker loss. It is not merely a worker-local900s timer reset by restart. Staging/publication work charged to this stage cannot occur before its durable start; queue time is charged to the Job. Report the absolute origins and enforcement/cessation evidence. Cleanup/termination is bounded by existing host stop policy; deadline expiry is not proof of cessation.

These additional numeric/template selections still require consolidated owner approval. Persist immutable profile/descriptor identities and canonical digests, explicit sub-bound and selected stage set. Use existing monotonic-watermark rollback handling; no deadline extension on replay. Recovery expiry/failure retains all evidence, fences further effects and holds an owner item; no auto-retry. Later review-only recovery from completed publication is NOT an invented command in this first slice: report retained custody and the unsupported continuation precisely until a separately supported disposition exists.

## 6. Public commands, decisions and bounded status (N4)

Proposed installed `baton-v12-stack manager` verbs (not currently runnable):

```text
publication-inspect --instance INSTANCE --participant OWNER --job JOB --stage STAGE --episode N
publication-decide --instance INSTANCE --participant OWNER --document SELECTION_JSON --decision-id ID --approve|--hold|--deny
publication-resume --instance INSTANCE --participant OWNER --decision-id ID
publication-status --instance INSTANCE --decision-id ID
```

Inspect is read-only, with no reservation or trusted state manufactured from agent copies. It returns a canonical digest-bound selection or exact holds: original authority/Work/scope/task and Job/stage/episode/attempt, command/input/policy/terminal, host output identity/digests, candidate/base/paths, adapter verification argv/exit/context and qualification, cessation/exclusion observations, proposed corrected output revision/profile/stages and reviewer binding. Do not include raw provider output, credentials or unbounded filesystem content. Detail files remain behind their existing evidence access boundary.

Decide records one exact owner approval/hold/denial without launch. Same decision ID/digest replays; changed data collides. Resume checks current capability/scope, exact selection, original trust root, cessation/assignment availability and installed composition, then durably reserves and admits one deterministic linked Job. Intent precedes cross-owner effects. Same resume reconciles that Job; it never generates another identity or renews limits. Persistent manager proceeds publication→review automatically once its genuine gates open, with no owner messenger between stages.

Publication-status has no participant operand because it exposes only recovery-item-style public operational facts under the existing local instance trust boundary: IDs/digests, finite limits/origins, original failure versus recovery state, custody/refusal/reviewer verdict status, unknowns and exact pending operation references. No raw task/log/evidence contents, credentials, private context or privileged authorization grants. Limit each status to the named decision and its one lineage; any histories use bounded pagination. Preserve15s freshness/stale qualification and explicit observation timestamps; a fresh rendering does not refresh old facts.

## 7. Restart and refusal contract

| Cut | Required reconciliation |
|---|---|
| decision committed / lost reply | same exact decision returns; changed selection collides |
| admission reserved / owner effects incomplete | reconcile exact owner operations and same Job binding; unknown holds |
| old assignment release or new claim reply lost | read actual Authority events/generation; no claim takeover or second claim |
| staging interrupted | exclude writer; reconcile private staged bytes against approved original identity; no original mutation |
| publication launch reply lost | observe exact host runtime/token; no second launch while uncertain |
| worker completed / freeze or intake reply lost | validate normal new-assignment completion and actual immutable custody; replay real receipts only |
| review gate/open allocation reply lost | same binding and allocation; no second reviewer invocation |
| review verdict reply lost | collect and attach exact verdict once; original Job remains failed |
| cancellation/expiry/revocation at any cut | fence/revoke and establish cessation through owners; retain evidence and report outstanding effects |

Durable before/after identities cover each external action. Restart is not a new attempt. Approval, passed producer evidence, candidate hash or an agent-written receipt alone cannot open a gate. Scope excludes general failure recovery, verifier correction, candidate editing, default retries and broad supervisor changes.

## 8. Internal checkpoints and connected acceptance (N3, N5)

Three internal review checkpoints, all within one connected outcome:

1. Trust-root inspection, exact owner decision, versioned admission and immutable lineage; demonstrate all proposed jobs non-runnable when execution/handoff unavailable.
2. Deterministic publication worker, read-only staging, deadline enforcement and real fresh-assignment custody/intake; demonstrate closed review gate until exact handoff exists.
3. Production review binding/gate opening, independent reviewer tests/verdict, cancellation/restart and packaged installed CLI acceptance.

A checkpoint is partial evidence, **never “resume supported.”** W385695 delivers only the connected installed command→real authorization/admission→publication→custody→substantive review path. No library-only success or fabricated receipt is sufficient.

Focused deterministic acceptance uses normal-boundary fake engine/provider, real owners/stores/composition/measurement/custody and valid substantive review output. Count zero implementation-provider and zero pipeline producer-verifier calls, but demonstrate reviewer test execution under900s/3600s limits. Exercise exact candidate/task/input/argv/context/profile/stages, byte-matched and mismatched copies, missing/unreadable original, original replacement, unauthorized scope, claimed Work/unknown cessation, malicious links/types/paths, size/entry overflow, cancelled/expired producer and recovery, every restart cut above and lost replies. Tampered or absent adapter attribution holds. Verify reviewer independence includes original producer. First sweep after approval and every incomplete-custody sweep makes zero review offers; valid custody and candidate binding opens exactly one. Ordinary stages/old vocabulary retain behavior; older binary/schema refuses new revisions. Never call a green producer result independent acceptance. Retain exact candidate digests, counts/failures/skips and durations for review.

W385694 owns proposal-only100MiB descriptor/template revision (`native-handoff.proposal100m/1`, `implementation-review/4` proposed in M385700). W385695 consumes the exact declaration and owns recovery submission/pool/store revisions, publisher and gate/CLI composition. Proposed dependency W385695→accepted W385694 must be installed/read back before dependent execution. Serialize shared role_contract/templates/pool, documents/schema/scheduler, job_control, CLI and stage_execution paths. K's Stage1-B review remains independent. No hidden dependency on unaccepted Stage1-B; its gate fix is a pattern, not accepted source authority.

Next: K delta check of this revision, then consolidated owner selection of REC-9 and remaining exact reusable revisions/profile fields (reviewer3600s already selected), then pin DESIGN before isolated implementation. Work reuse removes the prior G5 fresh-Work choice; no further product decision is requested for G1–G5 clarifications. This proposal selects neither deployment nor a live recovery. Actual W385624 eligibility and assignment availability must still be proved by the supported command once delivered.
