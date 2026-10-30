# Verifier descriptor paths and descendant subprocesses — W325695

Observed 2026-10-18 during W321528 reviewer claim325674. Independently reproduce exact candidate0addd2af focused command:186 pass with ordinary paths; same command with initial verifier inheriting TMPDIR=/proc/self/fd/3 yields40 failures/20 errors matching retained worker log. Exact source/input/environment and logs: baton:work/records/2026/10/finding-v12-failed-run-candidate-reporting/evidence/review-325674/{CANDIDATE.json,VIEW.json,FOCUSED-COMPLETE.json,FOCUSED-COMPLETE.log,FOCUSED-FD.json,FOCUSED-FD.log}. Real engine/provider not used. The candidate worker is byte-identical to its prior retained version; not attributed to this continuation's collector edits.

Confirmed source: v12/worker/claude_agent.py:_pinned_environment opens owned verifier roots and substitutes /proc/self/fd/N; _verify passes fds to immediate subprocess only. AdapterCase tests use tempfile paths under TMPDIR; nested subprocess closes fds, making its path nonexistent; nested _checked_directory also refuses resolved versus lexical scratch. Thus compatibility breaks before intended tests. Descriptor pinning protects against provider pathname substitution; removing it or sharing provider HOME is not an authorized workaround.

Independent finding because environment/security compatibility and reporting have different acceptance and ownership. Not a new gate on W321528, not acceptance of failed formal verification, not authorization to broaden W321776 or bypass it. Product/spec changes and any live execution retain selection boundaries. Initial assignment research/preparation only: identify smallest safe supported verification context, coordinate overlap with W321776/W61981 and W321528, then reviewed v12 packet. No direct product fallback or Git mutation.

## 2026-10-18T19:39:11+00:00 — bounded diagnosis and preparation boundary, claim325776

Confirmed against current worker SHA25618c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d: _pinned_environment:3186 sets HOME/TMPDIR/cache paths to /proc/self/fd/N; _verify:4064-4070 passes handles only to initial command. Evidence research-325776/DESCENDANTS.json independently shows initial child can resolve TMPDIR, ordinary grandchild with default descriptor closure cannot, and lexical/realpath differ. This inert OS probe uses no provider, engine, credentials or product modifications. Prior186-test reproduction remains the full affected-command evidence; it was not rerun here.

Current W321776 detail325776 remains blocked on W321528, W321780 closed. Its paired context implementation does not yet exist. DESIGN VER-1..5 requires task /3 and derived worker/operator views but does not make ordinary /2 descendant breakage acceptable. No supported existing paired-context remedy was found. W324214 historical integration stall remains UNKNOWN: M325733 and its evidence do not establish this cause.

Smallest useful outcome: existing verifier commands using ordinary subprocess defaults can use private HOME/temp/cache roots and create nested workspaces without losing their roots or tripping lexical/realpath guards, while roots remain bound to the intended objects despite provider pathname substitution. Preserve closed environment, private credential-free HOME, safe output, timeouts, cleanup and exact candidate provenance. This is distinct from /3 declarations, imports, required-input inventory and paired view materialization; those remain W321776. One coupled runtime/security acceptance result, no further child split.

Preparation must establish a concrete safe mechanism before implementation selection. Merely resolving descriptor aliases to provider-writable paths reopens the documented check/use race. Making fds inheritable does not override descendants' close_fds defaults. /proc/<holder-pid>/fd aliases alone do not establish nested canonical-path compatibility, lifetime or absence of credential access. These are rejected as unproved fixes, not a prescription for a new namespace architecture. Demonstrate the selected mechanism against root replacement, ordinary descendants and nested adapter use; if no bounded supported composition works, report the exact missing isolation operation and scope decision. Do not silently widen the protocol or weaken existing guards.

Ownership: this dossier/evidence belong to reviewer; next preparer owns a new preparation directory and attributable PROGRESS only. No product source is allocated by this research handoff. W321528 preparation-325711 carries retained worker/test bytes unchanged and selects a baseline collector correction; preserve those bytes and its active execution selection. W321776 retains /3 paired-context ownership. Before any v12 product execution, pin current accepted source and explicitly coordinate actual worker/test overlap. No reverse dependency on this finding is installed; no implementation or launch authorized by this diagnosis.

## 2026-10-18T19-43-03Z — mechanism diagnosis accepted; mount-root preparation selected

review-2026-10-18T19-43-03Z.md independently verifies preparation-325806 manifest and reruns its inert probe. Diagnosis accepted, no runnable packet. Next preparation investigates manager-established private mount roots using existing OCI composition, with explicit resource, compatibility and lifetime requirements. This supersedes the open choice between holder-fd and mount-root preparation only; neither is accepted product behavior. No worker privilege increase, source change or engine launch authorized. Exact scope/spec conflict, if found, must be stated rather than inferred from ordinary design work.

## 2026-10-18T19-49-22Z — concrete packet runner corrections required

review-2026-10-18T19-49-22Z.md checks preparation-325842 manifest and independently reproduces lost cleanup evidence with mocked subprocesses. Engine-proof runner infers ambient identity and does not enforce documented receipt deadline. These concrete corrections supersede packet-ready status only; selected mount-root design preparation remains. Exact failure probe evidence/review-325891/FAILURE-PROBE.json; no engine/product execution.

## 2026-10-18T19-54-03Z — revised packet accepted for owner execution selection

review-2026-10-18T19-54-03Z.md accepts preparation-325908 manifest34f80cd19db542f479545285555a8b5844260e9729c33e1c2fe13018c73414fb after independent pin/artifact verification and16 mocked execution scenarios. Prior proof-runner findings resolved; correction product/kernel evidence remains outstanding. This supersedes correction-due checkpoint only. No launch, source allocation or engine selection; later kernel proof still requires reviewed image/identity.

## Owner poke325957 — overlap/base sequencing

OVERLAP-325957.md verifies accepted14e52d80 but identifies actual _verify/shared-test overlap with preserved W321528 retained candidate and running continuation. Recommend serial accepted-checkpoint rebind before W325695 execution; final compatible checkpoint is not yet available. Owner retains ledger routing; no graph changes or pilot gate. Supported active-status evidence retained; no launch or takeover. Packet acceptance remains valid preparation, not combined-source acceptance.


## 2026-10-28 — current-state revalidation E370978

Owner E370881 revalidation confirms the descendant defect on committed f36bcd75. See REVALIDATION-370978.md and evidence/revalidation-370978: exact current validator/inert probe reproduces lost self-fd grandchild roots, holder-alias canonical mismatch/lifetime and unsafe plain-path replacement. All17 preparation325908 files remain intact; baseline.py and three source pins drifted. October22 AGENTS supersedes historical mandatory-v12 authoring; recommend bounded direct correction, not old packet execution. Mount design/kernel/capacity remain unproved. W321776 owner E370982 now selects direct paired continuation with justified sequencing; coordinate shared worker edits after separately selected root correction. No source, engine/provider, graph or Git mutation performed.


## 2026-10-28 — owner selects direct correction E371012; routing E371025

Owner accepts REVALIDATION-370978.md and selects bounded direct implementation on current accepted source. This supersedes revalidation-only/pending-selection status and historical v12-only authoring requirements, not product acceptance. Preserve anti-substitution, credential boundaries, reporting and committed Stage-A additions; preparation325908 remains immutable historical input, not a launch vehicle. Focused deterministic source acceptance and exact candidate review are selected; actual corrected-image/kernel proof, engine/provider runs and deployment remain separately selected.

W321776 owner E370982 selected paired continuation with justified sequencing. Dependency E371024 now makes W321776 wait on W325695; canonical readback confirms phase block and no handler. Shared worker/test edits are serial. This correction owns necessary verifier-root/OCI/image-layout source and tests under baton.impl claim; W321776 owns later /3 paired-view behavior. Implementer chooses actual paths within scope and records overlaps; reviewer owns this dossier FINDING/PLAN/reviews, handler owns candidate/PROGRESS/evidence. No extra child needed for the coupled root security/lifetime outcome. Route baton.impl now; no additional routine approval or old-packet preparation round.


## 2026-10-28T03:09:09Z — partial source review E371130 requests correction

review-2026-10-28T03-09-09Z.md verifies exact two-file candidate and20 focused passes but does not accept it. R1 auto-detection/fallback replaces selected explicit runtime-layout compatibility; R2 mountpoint-only admission omits selected topology/identity/options/immutable-ancestor validation, independently reproduced with simulated ext4/rw mount table; R3 configured image/layout/capacity source composition remains absent. These source obligations are distinct from separately selected real kernel proof. Continue directly under E371012 without another routine owner gate. W321776 is downstream, not implementation scope here; its dependency remains. Prior partial candidate/evidence retained unchanged.

## 2026-10-28T03-25-24Z — partial checkpoint E371265; continue selected correction

review-2026-10-28T03-25-24Z.md verifies candidate pins and 28 focused cases (one skip), without accepting connected source delivery. R1/R2 remain open at actual identity/topology/lifetime boundaries; author explicitly leaves R3 composition incomplete. Existing owner E371012 still authorizes continuation. No owner gate from a voluntarily ended turn. Keep one owner for joined configuration/worker/image source acceptance after reassessing decomposition; W321776 stays gated.

## 2026-10-28 — E375793 connected source review remains changes-required

Eight candidate pins match and477 focused tests pass with one skip. review-2026-10-28T17-58-14Z.md and evidence/review-375793/ record source counterexamples: installed configuration omits layout delivery although the image marker requires it; selected mount argv omits the UID/GID/mode the worker enforces; unselected runs inherit the new roots and /tmp redistribution. These supersede the candidate's connected-complete/unchanged-legacy claims, not its preserved progress. Continue the already-approved configuration/composition outcome under E371012; schema bookkeeping alone is not an owner gate. No source acceptance or kernel claim.

W375445 has actual single_worker.py overlap but no active claim. Attempted reviewer dependency and request on its baton.codx route refused; no edge was installed. M375833 corrects erroneous installed wording in M375823. Supported asynchronous M375836 requests authorized-handler serialization or explicit disjoint ownership. Existing W321776 gate remains; no takeover or silent graph change. One cohesive source correction remains appropriate; separate image/kernel selection stays outside this turn.

## 2026-10-28 — coordination completion E375838 / M375839

After the reviewer refusal described above, authorized baton.codx installed W375445 blocked by W325695 at E375838 and responded M375839. Independent canonical detail confirms both W325695 and W375444 edges, phase block, no handler. This supersedes the pending/no-edge checkpoint in review-2026-10-28T17-58-14Z.md and the E375851 handoff coordination sentence; review defects/disposition remain unchanged. Shared single_worker.py writes are serialized: W325695 configuration/adapter completion first, then W375445 revalidation and settlement commands. No semantic prerequisite or scope expansion.

## 2026-10-28 — E375996 two source blockers resolved, configuration still absent

Review review-2026-10-28T18-21-11Z.md independently verifies all eight pins and206 tests (1.216671393 seconds wall). Source mount UID/GID/mode and selected-versus-legacy scratch corrections resolve blockers2/3 of the prior review. Blocker1 remains: installed single_worker deployment does not select/deliver the layout. No joined-source acceptance. Return directly to baton.impl for that single remaining authorized milestone; no owner gate or additional parallel split. E375838/W321776 gates and explicit first single_worker.py ownership remain unchanged. Actual image/kernel proof remains separately selected.

## 2026-10-28 — E376056 complete-path claim disproved at _held

Review review-2026-10-28T18-29-29Z.md verifies nine candidate paths and69 passing topology tests but reproduces the actual configuration refusal: deployment/6 is unconditionally contextual, requires non-null provider_context, requires receipt declarations and excludes review. CONFIG-PROBE.json/ROLE-PROBE.json under evidence/review-376056 preserve real-entry results. E376054's joined-complete claim is superseded; prior mount/legacy source corrections remain progress. Required correction keeps layout selection independent of supported role/context semantics and proves real configured composition, not only layout_delivery helper calls. Return directly to baton.impl under E371012; no scope change, owner gate, kernel run or source acceptance. Existing ownership/dependency gates remain.

## 2026-10-28 — E376146 fresh admission corrected, combined context/layout still refused

Review review-2026-10-28T18-40-44Z.md verifies both changed pins and76 focused passes. Complete real-entry probes show /5 rejects verifier_layout and /6 rejects provider_context: the correction separates capabilities into mutually exclusive schemas rather than supporting their valid combination. Fresh implementation/review correction is verified progress; joined source remains unaccepted. Continue one bounded contract correction under existing E371012, preserving context/receipt enforcement and established gates; no new owner decision or image/kernel run.

## 2026-10-28 — E376215 bounded source milestone accepted

Review review-2026-10-28T18-49-59Z.md accepts the ten-path deterministic source correction, exact manifest 28abb7c366bd24c266db548b9046d64fca9bcc0e6aa061066319330d26eaa2cb. Valid context/layout now composes through actual entry/delivery/adapter/worker reader; fresh/review and required context checks remain.744 tests produce742 pass,1 skip and the independently reproduced four-SQLite-sidecar failure, not aggregate green. Prior changes-required source disposition is superseded; actual image/kernel/ENOSPC remains open and separately selected. Return owner for source checkpoint/remaining proof selection; no silent gate removal or operational execution.

## 2026-10-28 — owner E376411 accepts source and selects proof preparation

Owner accepts review-2026-10-28T18-49-59Z.md / manifest28abb7c366bd24c266db548b9046d64fca9bcc0e6aa061066319330d26eaa2cb. Work stays open for real image/kernel/capacity acceptance. Reviewer E376414 prepares a new bounded no-provider packet with exact current inputs, image identity, resource/cleanup/acceptance and commands; no image build/run or historical preparation325908 execution authorized. Human checkpoint remains due. New preparation-376414 freezes all ten accepted paths and full recipe COPY inputs, so subsequent serialized single_worker editing need not invalidate this frozen proof source. Reassess E375838 serialization-only gate with authorized W375445 handler; W321776 acceptance gate stays. Operational finding: historical preparation325908 has no PLAN.md (read returned ENOENT); its available OPERATOR.md/ENGINE-PROOF.md and source artifacts were read instead as historical inputs, not execution authority.

### E376414 coordination and source checkpoint completed

M376428 reports human checkpoint ef703336b890a4ff08503bc4f293fbeb559f478d; reviewer independently verified all ten committed path bytes against the accepted manifest (preparation-376414/CHECKPOINT.json). Pending-source-checkpoint wording is superseded; no agent Git mutation. Authorized codx handler removed only serialization edge W375445 on W325695 at E376433, confirmed M376434 and independent canonical detail: W375445 still blocked solely on W375444, no handler. W321776 acceptance dependency remains. Frozen packet/source provenance allows later shared single_worker edits without mutating this proof input.

### E376414 proof packet prepared for owner selection

review-2026-10-28T19-17-18Z.md records new preparation-376414 packet c4cf8e64d959a8345145812757be74255d40d744e58f9b1e90a5f739fbb3ecf7, exact frozen inputs, two-stage build/image-selection boundary, bounded no-provider kernel/ENOSPC/cleanup question and mocked checks. No build/run or actual proof executed. OPERATOR.md carries commands and honest full-workload/diagnostic limitations; image digest remains unknown until selected build. Return owner with concrete preparation, Work stays open.

## 2026-10-28 — selected build E376511/E376514; independent review E376674

Owner E376511 selected Selection A only: one1800s candidate build, requested2GiB/1CPU, network dependencies permitted, no model/deployment/retry/prune/deletion, then exact image selection for separate Selection B. E376543 hands back successful build receipt and selection. This supersedes pre-build/unknown-image current-state language above and in historical OPERATOR/review; it does not select kernel execution.

Review review-2026-10-28T19-36-25Z.md verifies all32 original pins, matching successful build receipt/image.id and closed selection, plus direct read-only Docker image inspection. Exact image sha256:47e733834bb690fd4601e102f81e527a08b6ffe55da8b8cb345f45edfcb1517e; selection7ab020e2d08f74296fb08bf1d0a44b8bfd1b8d8b76a34f96727502520fd6eac1. Bounded build handback accepted for owner Selection B; no image contents/kernel acceptance yet. No extra child is useful: existing sequential build/selection/probe boundaries suffice and do not overlap active source writers.

Two reporting corrections: build.log shows only early cached steps and later COPY/RUN execution, contradicting PROGRESS/E376543's all-layers-cached explanation for0.414s. Preserve reported timer, causal explanation unknown; no rebuild is needed merely to settle timing. Source checkpoint ef703336 is already observed and verified; E376543's final claim it remains due is superseded by M376428 and the recorded E376414 verification. Prior artifacts remain immutable.

Operational evidence distinction: nested Python-launched Docker inspect hit socket permission denial; direct installed-policy docker image inspect succeeded with exact ID, Created19:20:32.634149399Z and user65532:65532. Both results retained; no escalation request or engine mutation. Actual image-byte/mount/descendant/ENOSPC/cleanup outcomes await separately selected probe. W325695/W321776 remain open, no gate changes or implied full-workload/provider/deployment acceptance.

## 2026-10-28 — selected probe stopped at preflight; E376827 correction review

OwnerE376729 selected one exact probe with120s/40s reserve and no automatic retry/rebuild. E376735 execution produced failed-or-uncertain receipt: single inspect status1, ValueError, no create_intent/owned/container_id, successfalse. The original receipt equals the author's retained copy; all32 packet pins remain unchanged. This supersedes earlier no-ENGINE-RECEIPT/no-invocation current state, not accepted source/build identities. No kernel payload ran in this recorded invocation.

Independent direct inspect now returns exit1, stdout/stderr combined as `[]` then `error: no such object: w325695-proof-376414`. Pure replay into engine-proof.py:Proof.inspect rejects this form; both array stdout and lowercase diagnostic independently violate its accepted empty-stdout/uppercase-only forms. This same parser guards final absence, so the bug also risks falsely unresolved cleanup after removal. Evidence/review-376827/{DIRECT-INSPECT.json,CHECK.json} records current observation, five pure classification cases and pins. This is a proof-harness defect, not evidence of failure in the accepted verifier-root product.

Historical causality remains narrower than E376782 claims: original receipt stores only status and exception type, not stdout/stderr. It cannot exclude original socket/daemon denial. Fresh direct exit1 also does not reproduce the author's claimed shell exit0. Preserve the original report rather than rewriting it, and supersede its categorical causal/no-socket assertion with the independently demonstrated parser defect plus unknown original response bytes. The recorded invocation issued no create; that is not global runtime cleanup proof.

Route ordinary bounded harness correction directly to implementation: separately retained successor packet, supported exact-object absence handling, safe discriminating failure evidence, deterministic positive/adversarial/lost-create/cleanup/deadline checks, unchanged image provenance and no execution. Keep original receipt/packet immutable. No automatic retry, rebuild, removal or renewed product approval; later execution of changed runner bytes needs its own exact owner selection. No decomposition is useful for this single parser/evidence correction. W321776 remains gated on actual kernel acceptance.

## 2026-10-28T19-55-29Z — successor preparation requires correction and completion

Review review-2026-10-28T19-55-29Z.md records independently reproduced false-absence classifications and missing runner composition in E376870. Continue the already selected successor packet; preserving old evidence is not a gate to creating new files. No engine retry authorized. Evidence: evidence/review-376881/.

## 2026-10-28T20-00-26Z — exact-match correction still incomplete

Review review-2026-10-28T20-00-26Z.md reproduces name-prefix false absence, unlisted mixed-error false absence, and regression of supported daemon-prefixed no-such-container response.21 helper cases pass but do not establish the closed contract. Successor runner remains absent. Continue complete already authorized packet milestone; no engine execution or new approval gate.

## 2026-10-28T20-05-27Z — transfer successor preparation after unchanged return

review-2026-10-28T20-05-27Z.md confirms E376982 changed no bytes. Transfer next serial implementation claim to baton.codx; prior author released. New successor directory preserves both older preparations/receipts. Scope, independent review and later owner execution-selection boundary unchanged. A complete milestone need not fit one claim, and identifier bytes must not be case-folded.

## 2026-10-28T20-14-59Z — composed successor preparation independently accepted

review-2026-10-28T20-14-59Z.md accepts preparation-377003 pins cdfd88a8cce5191251bae49a0ce28034a1cb2f69936eb659b1e03dbd6762dc53 and selection48bf5fc7a890c652f3a64f817b25279113e7617b85c3e2f59df812fe677753b2 for later owner choice.20 deterministic tests pass; packet check passes;42 historical pins unchanged and retained receipt absent. No engine run or kernel acceptance; W321776 gate preserved.

## 2026-10-28T21-48-41Z — selected real kernel result accepted; interpretation corrected

review-2026-10-28T21-48-41Z.md accepts receipt992a374394a43d9ced6e7edc10d2ce97f1e3c2e25ae97d1a97fac3de3be29123 under owner E377680. All10 packet/42 preserved pins match; real descendant pathname/mount/ENOSPC and exact cleanup proof complete the selected remaining acceptance. Explicitly supersedes E377754/claim377728 explanatory overclaims:9 is a PID, not descendant count; pycache allocation gap is868352 bytes, not4KiB; original failed-run streams and exact cause remain unknown. No rerun required or authorized. Pass owner for satisfying closure; future release/installed/live qualification is separate.
