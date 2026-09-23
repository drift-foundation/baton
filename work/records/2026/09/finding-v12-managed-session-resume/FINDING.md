# Managed session resume for v12 Jobs

## 2026-09-22 -- claim 239485, the fault established; one seam pinned

Review 2026-09-22T14:38:24Z requested four changes. Three are done. The
accounting now distinguishes an ANSWERED absence from a read that did not
answer -- only the first may retire a runtime obligation, and an unreadable
state stays accountable -- and every consumer reads one accountable set, so a
blocked stage's projection identity no longer counts as a turn.

The original fault is established as fact from the retained line: the provider
created a `proposal` branch inside the runtime and authored both commits, HEAD
moved from the admitted revision, and `ClaudeAgent._unmoved` is the check that
raised. The adapter owns the commit and the publication; the provider owns the
edit. The stalled cleanup is diagnosed too: a faulted turn froze and collected
nothing, so no intake receipt exists and the ending never reached
`authorize_cleanup` -- the axis reading `pending` rather than
`blocked-on-intake` is what discriminates. Recovery is an owner act and was not
performed. The contradictory operator replay direction is superseded.

What is NOT done, and is pinned rather than approximated: genuinely
stage-specific requirements. One Job carries one digest-sealed input manifest,
so both roles necessarily receive the same task string -- `_review_prompt`
frames it as the reviewer's requirements. Giving the two roles different
requirements needs a product seam on the task document, pinned in PLAN.md and
not begun. Until then this packet cannot guarantee the correction sequence
without scripting a verdict, and the supervisor's sequence requirement is
deliberately not weakened to paper over it.

No store was opened under this claim; no live rerun, cleanup, enabling or
closure.

## 2026-09-22 -- claim 239365, what the first live run actually showed

The packet ran and ended held. `LIVE-RUN-239365.md` records the findings from
the run's own evidence, written before any implementation; `live-239365/` holds
preserved copies. The run directory was not modified and nothing was rerun or
cleaned up.

Two defects, both mine. The implementation agent reviewed its own work --
returning "Verdict: accept" after performing all four stages in one turn --
because the packet's task document was a four-stage script, and `claude_agent`
hands that string to the implementation role as work to do. It now states the
requirement only, and says that judging is not that stage. And a review episode
identity with no attempt row was counted as a started runtime and charged a
cleanup record that could not exist; attempts are now classified `started`,
`foreign` or `unallocated` from records, with only the first two charged. That
classification asserts nothing about quiescence.

Two facts stand for the owner, read back rather than inferred: the
implementation runtime is `quiescent` with `cleanup: pending` and no committed
destroy, so it is genuinely outstanding; and the qualification grant is
consumed, so a relaunch under the same `run_id` is not a replay. Neither is
acted on here.

This supersedes the claim-239174 readiness wording. No live rerun, cleanup,
enabling or closure.

## 2026-09-22 -- claim 239174, one bound code boundary

The relocated-source finding is confirmed exactly as recorded and corrected.
`stage_execution` infers which tree mutable state may not be written into from
its own `__file__` when nobody says; for the relocated manager source that
answers `/home/sl/baton-runs`, the run root's parent, so the run's own stores
were inside it. Preparation validated with an explicit `/home/sl/src/baton` and
composition inferred -- two boundaries for one rule, which is why a packet that
passed `packet_bindings.write` refused at `operations_from`.

The packet now carries `code_boundary`, defaulted to the manager source, and
both ends read that one value. `held_packet` refuses a boundary containing this
run's own stores, so the failure is caught before any store opens rather than
after the owner acts commit. The inference and the whole symptom are reproduced
deterministically over the actual relocated layout and the operator's own
written deployment, read-only.

Read-only assessment of the prepared instance: the grant is UNCONSUMED, so no
admission opened and no runtime started; all four preparation acts replay under
their own identities, and re-running steps 5 and 6 is safe. The prepared state
is preserved and the operator's run directory was not rewritten -- regenerating
it is their step 5, and their selections need no edit.

This supersedes the claim-238827 entry's readiness wording. What remains is the
owner's: the fixture commit already made, step 5a, the six selections, and the
exact live-command selection. No live rerun was performed.

## 2026-09-22 -- claim 238827, the workspace prerequisite, and a recorded loss

Review 2026-09-22T12:55:41Z accepted the R2a shutdown correction and narrowed R4
to one step: the entrypoint test was supplying a workspace-storage
configuration the operator packet never named. This supersedes the claim-238700
entry's owner-side-only completion wording.

`supervisor.prepare` now configures the workspace store as its first owner act,
with the root DERIVED from the deployment configuration the packet is bound to
-- not chosen by this program, which is the arbitrary selection the boundary
exists to refuse. Workers naming different roots are refused rather than one
being picked, and the existing conflicting-root refusal and context/workspace
exclusion checks are untouched. The fixture's hidden setup is deleted and the
sequence is proved through `main`.

The review's separate operational finding is accepted and the fault is mine:
superseding the operator packet by deleting its predecessor broke four
revisions' evidence locators. Those bytes are unrecoverable and
`LOST-ARTIFACTS-238827.md` records each one, the reviewer-retained digest where
one exists, and what was not affected -- no accepted product byte, candidate
provenance, verification receipt or reviewer artifact. Nothing in this dossier
is unlinked from this claim onward; a revision is added beside its predecessor.

What remains is the owner's: the fixture repository's first commit, the step-5a
Authority preparation against the real disposable instance, and the six
selections in `SELECTIONS-238827.json`. No file is presented as a runnable
packet.

## 2026-09-22 -- claim 238700, interruption safety and the entrypoint proof

Review 2026-09-22T12:31:42Z accepted the cancellation seam and the generated
deployment's correction proof and held open R2a's interruption safety, the R4
entrypoint proof and the stale operator instructions. All three are now done,
and this supersedes the claim-238462 entry's completion wording for those.

The shutdown is interruption-safe as a PHASE. One installed handler raises while
the run is serving and DEFERS once admission has closed, because everything
after that point is the accounting that exists to leave nothing unexplained;
every shutdown step is separately bounded, and the per-attempt runtime read is
bounded inside the cancellation loop so one interrupted read costs neither that
attempt's stop nor any later one's. The outcome is retained before
`SupervisorInterrupted` is raised. No `SIGKILL` recovery is claimed.

The operator entrypoint is executed, not described: the generated packet runs
through `supervisor.main` with the real imported `baton_v12`/`tools` bound as
its manager source, covering success, the timeout with a real engine stop, and
the refusal of an unbound source before any store opens. That test found a
defect on its first run -- `main` opened the Job store without its required
Authority and incarnation operands and raised `TypeError` -- which is fixed
here, and which nothing could have seen while nothing ran `main`.

`OPERATOR-238700.md` is reconciled with the current bound artifacts: the
superseded selections document, the obsolete evidence names, the
no-cancellation-capability bullet and its dangling pointer are all corrected.

What remains is the owner's and is unchanged in kind: the fixture repository's
first commit, the step-5a Authority preparation against the real disposable
instance, and the six selections enumerated in `SELECTIONS-238700.json`. No file
is presented as a runnable packet.

## 2026-09-22 -- claim 238462, the cancellation seam and the packet proof

Review 2026-09-22T11:53:11Z accepted R2b and held R2a and executable R4 open.
Both are now done, and this supersedes the claim-238310 entry's statement that
R2a needed a product seam that had not been begun.

The deployment stops what it started. `tools/single_worker.py` and
`tools/stage_execution.py` carry the seam under claim 238462, with ownership
pinned in PLAN.md before the first edit and `CANDIDATE.json` amended to add
those two product paths and their two focused test paths beside the six
originally accepted ones, which are unchanged. The act itself is the accepted
`attempts.request_cancellation`: the exact participant and generation are fenced
at the Authority before the agent and the runtime are ordered to stop, and an
attempt is routed to the worker its recorded allocation names. An ordered stop
is still not proof of absence, and the run continues to require a positive
committed `runtime.destroy` before calling anything settled.

The two remaining shutdown edges are closed: cancellation decides per attempt
through `attempt_runtime_of` rather than through the stage projection, so an
unreadable or unknown fact is a reason to order the stop rather than to skip it;
and the termination handler is held around the whole run, so an interrupt during
cancellation, cleanup or publication is recorded and the outcome retained before
it is re-raised. No `SIGKILL` recovery is claimed.

The generated packet is now driven through its real entrypoint over a fresh
disposable Authority, in one path covering the initial proposal, the real
changes-requested feedback, restoration, the revised result and independent
acceptance, and in a second covering the timeout where the engine really
receives the stop.

What remains is the owner's and is unchanged in kind: the fixture repository's
first commit, the step-5a Authority preparation against the real disposable
instance, and the six selections enumerated in `SELECTIONS-238462.json`. No file
is presented as a runnable packet.

## 2026-09-22 -- claim 238310, R2b and R4 done; R2a needs a product seam

Review 2026-09-22T07:03:13Z refused the claim-236529 supervisor on R2a and R2b
and the drafted bindings on R4. Both reproduced counterexamples are accepted as
real. R2b and R4(a-d) are corrected in this claim's dossier files; no file under
`v12/` was edited and the accepted six-path candidate is byte-identical.

This supersedes the claim-236529 wording that shutdown was complete. What is now
true: a failed canonical read is retained as a named uncertainty and can never
become evidence of absence, and a successful final canonical read is a
precondition of calling a run settled; Ctrl-C and SIGTERM route through the same
shutdown accounting, retain the outcome and re-raise rather than being swallowed;
the supervisor asks the composition to stop what is still executing and names
every runtime it could not stop. The provider network is an owner selection and
`none` is refused with its reason; `evidence_digest` names W177936's retained
accepted evidence instead of a sentinel; the Authority preparation the fresh
zero-Job install does not perform is documented as operator step 5a and checked
by `packet_bindings.preflight`, which also says what it cannot prove; and the
review criteria reach the reviewer through the single task document and the
fixture repository, without forcing a verdict.

What this does NOT supersede: R2a is not finished. No composition carries a
cancellation capability, so a timeout with an active provider turn is reported
held with the container still running. The accepted path is
`attempts.request_cancellation` -- fence at the Authority, then the agent's
cancel and the adapter's stop -- and its per-attempt port, agent and adapter
belong to the deployment that launched the runtime. The seam is therefore a
product change in `tools/single_worker.py` and `tools/stage_execution.py`,
pinned in PLAN.md and not begun. The end-to-end run of the generated documents
through the actual entrypoint depends on that seam and on operator step 5a, and
is stated as remaining scope rather than approximated. No file is presented as a
runnable packet.

## 2026-09-22 — claim 236529, R1–R3 corrected and the bindings drafted

Review 2026-09-22T06:36:24Z refused the claim-236349 supervisor on three counts
and all three are accepted as real defects, reproduced by
`review-repro-236474.py`. The corrections are in `supervisor.py` and the
evidence in `test_supervisor.py`; the accepted six-path product candidate was
re-verified byte-identical and no file under `v12/` was edited, so no amended
candidate provenance is needed.

This supersedes the claim-236349 assertion that a bounded supervisor was
complete, and supersedes `OPERATOR-236349.md`'s "stops admission" and "stops by
itself" claims, which were not true of that code. It also supersedes that
handoff's blanket "no actual engine execution": one throwaway `--network none
--read-only` container really did run during image verification. What remains
unexecuted is the managed live run — no provider, model call, credential,
egress, registry push, deployment change or production enabling.

What is now true: invocation caps are refused at the admission boundary before
an offer is issued; the declared `turn_seconds` is the Job's own effective
`provider_turn` ceiling and is checked before serving; a settled outcome
requires the actual open → changes-requested → restore → accepted sequence with
two distinct retained proposals, read back from the manager's own records and
never manufactured; admission is closed at the operations boundary before
cleanup, so the cleanup window cannot admit, claim or launch; every started
runtime is recorded at the launch call and the canonical history is re-read
after faults, so none can vanish from the accounting; and the manager source
that is actually imported is bound, 106 files with zero drift from the reviewed
checkout, and proved before a store is opened.

It also supersedes the claim-236349 position that the per-Job worker documents
were wholly an owner selection. `packet_bindings.py` drafts and validates them
against the manager's own `held_configuration`, granting and running nothing.
Two owner-side items remain, isolated by name rather than expanded into a
general prohibition: the fixture repository's first commit, which fixes
`line_declared_base` and which this deployment prohibits the implementer from
performing, and four participant/credential selections in
`SELECTIONS-236529.json`. No file is presented as a runnable packet.

## 2026-09-22 — claim 236349, packet artifacts built; two steps remain

Claude recovered the transferred preparation and revalidated the accepted
candidate byte-for-byte before acting. The refreshed immutable worker artifact
now exists and really carries the accepted bytes: image
`sha256:2e9e84ff23319778760d5b22c70d543d4290931510a3ab3ecf40bcdaad7456bd`,
whose effective `/opt/baton/claude_agent.py` is `abdf903d…54bb4d`. The isolated
manager runtime (`sha256 04aa459a…a58a`, build stamp 1e576ff2 dirty/7) and an
isolated zero-Job installation with its own generated Authority
`636a9493650b4efe9d03c684b5b9d904` are built. This supersedes "unbuilt changed
worker artifact" and "unselected installation" in the 2026-09-22T05:58:20Z
review's remaining list.

The bounded owner supervisor the same review required now exists
(`supervisor.py`) and is deterministically verified (20 checks,
46.255348787s): it stops admission on a terminal or exceptional stage or the
overall bound, refuses any runtime admitted after that stop, requires a
positive committed `runtime.destroy` for every runtime it admitted, retains the
outcome atomically, never retries and refuses a production profile. This
supersedes "missing bounded owner supervisor".

It does NOT supersede the packet being non-executable. Two steps remain and are
recorded as remaining scope rather than filled in: the disposable fixture
repository's first commit, which fixes `line_declared_base` and which this
implementer's deployment prohibits it from performing; and the per-Job worker
deployment document with its digest-sealed `inputManifest`, whose seven policy
identities, certified runtime profile and adapter identity are owner selections
that `dogfood_operator.input_manifest` explicitly refuses to invent. Exact
commands and every value already fixed are in `OPERATOR-236349.md`;
`PACKET-INPUTS-236349.json` is labelled inputs, not a packet. No live run,
model call, authentication operation, deployment change, production enabling,
automatic retry or Git mutation occurred, and W177936 stays closed.

## 2026-09-22 — owner selects Claude after Codx credit exhaustion

Owner reports Codx has 0% credits remaining and directs switching this Work to Claude. Incident70 records failed Codx execution holding assignment episode236296 (claim236300). This is owner-reported credit exhaustion; the runtime describes systemError and a terminated managed turn. Preserve the accepted implementation and all partial preparation. Resume the existing final executable packet preparation through baton.impl/baton.claude after exact claim recovery; do not restart implementation or create replacement Work. This supersedes Codx as the selected preparation executor, not the technical scope or independent-review requirement.

Prompt's process inspection is sandbox-local and cannot establish host process absence. Before releasing the stranded assignment, the operator must stop/fence the old Codx stack and account for surviving build/test execution. Claim release is a separate operator recovery action, not proof of process shutdown. After recovery Claude must revalidate retained artifacts and existing changes, establish exact file ownership, and append its own PROGRESS entry without rewriting Codx history. No new live demonstration, credential operation or production enabling is selected. Review remains independently routed; any reviewer credit limitation must be reported separately.

## 2026-09-22 — confirmed owner selection

Owner accepted the proposed next bounded Job: make session resume work through the normal v12 worker-manager path. Keep W177936 closed as accepted isolated recall evidence; this is separate implementation, not another standalone canary or broad qualification campaign.

Selected outcome: save the implementer session, stop the prior worker, restore into a fresh isolated worker, deliver independent-review feedback as new input, and collect a verifiable revised proposal. No duplicate execution or uncertain cleanup is acceptable. Model name is irrelevant to resume acceptance; preserve reported model usage as diagnostics rather than inventing model attribution. Retain successful process/result, exact session, provenance, authorized input, isolation and cleanup checks.

Observed source at selection: v12/worker/claude_agent.py contextual serving receipt validation and v12/python/src/baton_v12/worker_manager/provider_context.py certify_production_profile require a direct terminal model field matching the expected model. Both actual retained diagnostic-235602 results omit that field. The isolated fixture does not produce the managed grant consumption, open/restore finalizations, retirement and committed continuity review required by the production path. Revalidate these facts before editing; reuse existing lifecycle machinery and accepted evidence rather than replacing them.

Evidence: baton:work/records/2026/09/finding-v12-production-context-qualification-preparation/review-2026-09-22T05-31-21Z.md and REVIEW-EVIDENCE-235998.json. That review accepts meaningful exact-canary recall with one space after RECALL:, preserves the original fixture failure, and distinguishes isolated recall from managed production qualification. W177936 closure permits fresh-attempt development; this new selection does not reopen it or impose a new global development gate.

This selection supersedes model-identity gating for resumed execution in the affected production serving/certification contract. It does not waive identity of the session, attempt, invocation, saved state or reviewed result. Preserve historical evidence and tests of genuine failure cases. Requested execution-model configuration may remain explicit; reported identity must not be a resume-success prerequisite.

First deliver implementation with focused deterministic provider replay through real manager coordination, workspace, state transfer, receipt and result paths. Independent review follows. Then prepare one concrete managed live correction using reviewer feedback and the original implementer session. Live invocation, deployment changes and enabling require the later exact reviewed command selection; no unspecified live run is authorized by this preparation assignment.

## 2026-09-22 — revalidation and owner clarification M236120

Confirmed by baton.slaw in T236087: model-independent status/session acceptance applies to contextual **open and restore**. This explicitly supersedes the earlier resumed-turn-only wording. Requested-model binding and diagnostic reporting remain; unrelated non-contextual execution remains unchanged. Revalidated three gates: worker `_context_result`, manager `_receipt`, and certification terminal checks.

Confirmed managed-path gap: the static profile state allowlist cannot name the actual `.claude/projects/-output/<conversation UUID>.jsonl` file before admission, because profile identity contributes to the context/conversation identity. Add only the literal filename `{conversation_id}.jsonl` under the existing `.claude/projects/` allowlist; resolve it from the committed admission's canonical UUID, never provider input. No globbing, directory substitution or general formatting. Preserve all static allowlists and immutable generation verification.

Receipt compatibility: new contextual worker receipts use `/3`, retaining every `/2` invocation/session/status/provenance field. `observed_model` is the actual bounded safe model label when supplied, otherwise null; it is diagnostic, never a success gate. Add `model_diagnostics_digest` over the supplied model/modelUsage members and `provider_result_digest` over the exact terminal bytes. Retained provider logs carry full reported usage privately. The manager continues reading historical `/1` and `/2` with their original strict model contract; new `/3` permits missing/changed labels. Certification rechecks successful exact-session results and ties `/3` diagnostics and terminal bytes to the sealed receipt, refusing malformed/duplicate/nonfinite JSON. This is a compatibility reader extension, not a reinterpretation of historical failed evidence.

Existing coordination already composes independent changes-requested review, feedback delivery, stop/fence/positive absence, immutable state, fresh use HOME, revised proposal intake and settlement. Extend this path rather than add a second controller. Deterministic proof will exercise the actual candidate execution-grant guard; engine/provider remain simulated.

### Compatibility refinement before finalization

Profile `/1` historically permits literal braces in a filename. Reinterpreting those existing bytes as a template would violate retained-profile identity. Therefore filename substitution is opt-in via `baton.claude-context-profile/2`; `/1` remains entirely literal. `/2` has the identical closed member set and accepts only the designated UUID filename marker. This supersedes any implication above that old profiles gain substitution in place. Add the deployment manual's context section to the owned paths to document this contract and the `/3` receipt transition; no deployment itself changes.

## 2026-09-22T05:58:20Z — independent review accepted, claim236222

Review review-2026-09-22T05-58-20Z.md accepts the six-path implementation bound
by CANDIDATE.json SHA2563a2bf7564e24113c78120d9e451e7c3a75d98b48f08d3dcdf747585e5c5e5cae
and patch574c32c0228259668fd1623a71ad480ce0be7363cd44c0f575300ca65f5d5e38.
All current/base bytes verified. Model-independent contextual open/restore,
receipt compatibility and admission-bound opt-in filenames satisfy M236120.
Independent34 focused deterministic tests passed16.578126122s; author spending
49.861932617s remains separately preserved (combined66.440058739s). Test changes
were evaluated against the owner ruling; no genuine failure coverage waived.

This supersedes awaiting-independent-review status. Return baton.decide to
select final executable packet preparation: rebuilt artifact and selected
installation/deployment digests, fresh run/source/storage/credential-reference
bindings and a bounded supervisor with positive manager cleanup. The current
proposal is concrete but intentionally not live-ready; no execution/enabling
or Work closure follows this implementation acceptance. W177936 remains closed,
fresh-attempt development permitted. No new live/engine/deployment/Git action.

## 2026-09-22 — owner selects final executable packet preparation

Owner says "lets proceed" in response to the accepted implementation and recommendation to prepare its final executable packet. Accept the bounded direction in LIVE-CORRECTION-PROPOSAL.md and proceed under this existing Work. This supersedes awaiting owner selection of packet preparation, not the separate exact live-command selection.

Selected preparation includes building the changed immutable worker artifact and isolated manager installation, recording actual digests, preparing disposable fixture source and fresh authority/Job/profile/storage bindings with credential references only, and implementing a bounded one-shot supervisor using supported owner/manager APIs. Keep production services and existing deployments unchanged. No live model invocation, authentication operation, production enabling, automatic retry or Git mutation is selected. If host permissions prevent an artifact build, preserve the prepared inputs and provide the exact operator command rather than requesting escalation from a managed turn.

Use the proposed workload and limits: one Job, two implementer invocations, two independent review invocations, 180 seconds per provider turn, 900 seconds overall plus 60 seconds reserved for manager-owned cleanup. These are preparation targets for the final reviewed packet, not authority to run it now. The actual first review must evaluate the initial proposal and deliver the selected correction feedback; do not fabricate accepted reports. Supervisor must stop admission on terminal result or failure, establish positive runtime exclusion/cleanup and retain outcomes. Exercise it deterministically, then hand the digest-bound executable packet to independent review and return to owner for exact live selection. Preserve accepted candidate provenance and all prior evidence; avoid unrelated redesign or repeated standalone canaries.

## 2026-09-22T06:36:24Z — claim236474: supervisor changes requested

Independent review-2026-09-22T06-36-24Z.md supersedes claim236349 assertions that
the bounded supervisor is complete and stops admission. R1: validated invocation
caps/turn limits are not enforced; actual composed tests settle over declared caps
and settle after first-review acceptance with no correction. R2: ordinary cleanup
sweeps can admit work after stop, then omit it from cleanup accounting; a fault
after admission before the next predicate likewise loses the runtime from that
accounting. R3: operator command executes mutable checkout imports while only
pinning an unused frozen manager binary. These are blocking packet defects.

review-repro-236474.py/.log confirms four counterexamples (two real deterministic
compositions, two injected boundary faults) in1.686792790s. All six accepted
candidate files and81 distro files plus packet-linked hashes verify unchanged
in review-artifacts-236474.json. Image inspection remains author-attributed.
Prior implementation acceptance stands; no live packet acceptance or execution.
Total recorded verification now131.107174675s; unmeasured preparation unchanged.

Return baton.decide recommending bounded Claude correction under this Work,
then independent review. Complete concrete proposed deployment/input bindings;
Git commit remains owner-owned. No new live, credentials, production enabling,
standalone canary or global gate. Preserve historical reviews and all artifacts.

## 2026-09-22T07:03:13Z — claim236644: shutdown and live-binding changes requested

Read review-2026-09-22T07-03-13Z.md. Admission gating, workload-sequence checks
and actual manager-source binding improve the previous defects; all106 source
files and six accepted candidate files verify. This does not accept the packet.
R2a remains: overall timeout of a waiting runtime issues no stop/kill/remove;
ordinary gated sweeps do not initiate cancellation. R2b: post-stop canonical
refresh exceptions are silently discarded and a completed run still settles.
review-repro-236644.py/.log confirms both through real deterministic composition
in1.433670567s. Claim236529 shutdown-complete wording is superseded accordingly.

R4: the drafted live workers hard-code network none, fresh-instance Work/route/
grant preparation is absent from the operator sequence, evidence_digest remains
all-zero, and selected review-feedback/final-acceptance document delivery is not
bound by the composer. Finish executable behavior and verify generated documents
through normal deterministic entrypoint/composition, not only schema validation.

Return baton.decide recommending bounded Claude correction under this same Work.
Keep accepted implementation/artifacts; pin any needed manager cancellation seam
and candidate provenance before product edits. No live/enabling/Work closure or
new global gate. Measured cumulative146.324112960s; previous evidence preserved.

## 2026-09-22T11:53:11Z — claim238394: accept R2b; complete existing R2a/R4 scope

Review review-2026-09-22T11-53-11Z.md accepts failed-final-read holding behavior
for the reviewed supervisor bytes. R4 draft network/evidence/review-input changes
are source-reviewed progress, not acceptance of executable composition. Original
six-path candidate unchanged. R2a remains unwired. Additional confirmed edges:
unknown stage state skips cancellation of a known attempt, and interruption
inside cancellation escapes retention; SIGTERM protection ends before cleanup.
Seven focused checks2.007636930s (five partial fixes, two counterexamples) are
retained in review-checks-238394.py/.log and review-evidence-238394.json.

Owner238308 already authorizes the required pinned product seam; no further
permission gate is inferred. Next implementer claims exact source/test ownership,
finishes attempt-owned cancellation/positive exclusion and interruption handling,
amends provenance and runs generated docs through the actual entrypoint with a
fresh deterministic test Authority. That isolated test does not require mutation
of the deployed owner Authority. Correct stale operator selections and disposed-
handle preflight examples. This supersedes any R4-complete or new-seam-approval
interpretation in the prior handoff; historical evidence remains unchanged.

Return baton.decide recommending bounded continuation then complete independent
review. Cumulative measured164.250246394s. No live/enabling/closure or global gate.

## 2026-09-22T12:31:42Z — claim238615: seam accepted; packet changes remain

Review review-2026-09-22T12-31-42Z.md accepts the allocation-owned product
cancellation seam and generated-deployment simulated correction evidence; R2b
stands. All ten candidate files and106 bound source files verify. R2a remains:
interrupting the runtime read inside cancellation with a started runtime escapes
without stop or outcome retention. R4 tests bypass main; their generated fixture
refuses at main because imported packages do not match its synthetic source
binding. Actual prepared source hashes do match; no live failure is inferred.
Operator step5 still copies old selections, and old source/capability wording
contradicts the latest packet. These supersede claim238462 completion assertions.

Retain review-checks-238615.py/.log, review-verification-238615.json,
review-interrupt-238615.log/.json and review-evidence-238615.json. 23 checks plus
one strengthened counterexample pass in8.079184858s; passing counterexamples
confirm defects. Recorded cumulative202.209270735s; historical unmeasured costs
remain unmeasured. Return baton.decide recommending already-authorized bounded
continuation, then independent review. No extra preparation approval gate,
live execution, enabling, Git mutation or closure.

## 2026-09-22T12:55:41Z — claim238782: shutdown accepted; workspace setup remains

Review review-2026-09-22T12-55-41Z.md accepts R2a with independent actual SIGTERM
at the runtime read: stop ordered, held outcome retained, interruption carried.
R2b stands. Main now runs success/timeout/source-refusal cases and correctly opens
its JobStore. However, its test performs configure_workspace_storage before main,
which the operator sequence omits; removing only that hidden setup reproduces
fresh-main refusal before runtime start. Add supported explicit preparation and
prove the same sequence, preserving root-conflict/exclusion checks. This
supersedes claim238700 owner-side-only completion, not accepted product bytes.

Operational finding: OPERATOR-238462.md, PACKET-INPUTS-238462.json and
SELECTIONS-238462.json are absent at previously reviewed paths. Historical hashes
remain; no bytes reconstructed or attribution inferred. Restore exact retained
artifacts or record explicit loss/recovery disposition.

All ten candidate files and106 bound source files verify. 16 checks passed,
including one confirming counterexample, in9.890538327s; cumulative248.644322402s.
Evidence: review-checks-238782.py/.log, review-verification-238782.json,
review-evidence-238782.json. Return baton.decide for existing-authority bounded
completion, no extra preparation approval loop, live execution or closure.

## 2026-09-22T13:07:41Z — claim238861: bounded preparation accepted

Review review-2026-09-22T13-07-41Z.md accepts the R4 correction: prepare derives
and configures the bound deployment workspace before context storage, and fresh
main succeeds without hidden setup. Conflicting existing roots and nested private
context overlap remain refused. Prior shutdown/failed-read/product acceptance
stands. All ten candidate paths and106 bound source files verify. Acceptance is
bound to PACKET-INPUTS-238827.json and review-evidence-238861.json.

LOST-ARTIFACTS-238827.md supplies the explicit historical-loss disposition;
contents are not recovered. The238700 packet/selections remain unchanged; its
operator has an annotation whose removal in memory reproduces its original hash.
Keep future digest-bound predecessors unchanged; annotate successor/journal.

Seven distinct checks satisfied; one initial reviewer fixture hit custody mode
before overlap, then a corrected private nested directory passes containment
verification. Both runs retained; review8.209668460s, cumulative294.436252733s.
This supersedes remaining preparation-changes-requested status. Return
to baton.decide for owner fixture/base, operator5a instance setup, six selections
and exact live-command selection. No new preparation loop for unchanged accepted
bytes; no live/enabling/production certification/Work closure follows review.
# 2026-09-22 — owner launch refused: relocated-source checkout inference

Observed by baton.prompt from the owner's traceback and read-only source
inspection: launching PACKET.json SHA256
`2c6336bea08870e45ed8a6d5d11cd365670156c3332fc149499c7d3d6cfc56c5`
under `/home/sl/baton-runs/managed-correction-236087` refused in
`stage_execution.held_configuration` during supervisor `_compose`.
The integration store was classified as inside `/home/sl/baton-runs`.

Confirmed cause: packet_bindings.write validates with explicit
`checkout=selections['checkout']`, whereas supervisor._compose calls
operations_from without checkout. The non-frozen runtime default walks three
parents above stage_execution.py; the relocated manager-source layout therefore
answers `/home/sl/baton-runs`, not the intended code boundary. Changing shell
working directory cannot correct a path derived from __file__.

This invocation reached prepare before composition: workspace/context storage,
candidate profile certification and qualification authorization returned before
the refusal. It did not reach supervise or worker admission. This is a
source-order conclusion for this invocation, not a store audit or a claim that
the instance is untouched. Preserve existing state and evidence; no blind rerun.

Proposed correction: bind and validate the intended checkout/code exclusion
boundary consistently across packet preparation and runtime composition,
retaining protection of the copied manager source. Add deterministic coverage
using the actual relocated source layout and default production composition;
refresh reviewed packet/program provenance before another live selection.
Inspect existing preparation through supported APIs when assessing retry safety.
Do not patch reviewed runtime bytes in place or bypass containment validation.

This observed launch failure supersedes the current owner-side-only readiness
assertion below; prior product proofs remain historical evidence. No worker
execution success, production qualification or closure is established.

## 2026-09-22T14:05:58Z — claim239228: copied-source correction accepted

Review review-2026-09-22T14-05-58Z.md accepts schema/3 code_boundary binding
across composer and production _compose. Independent actual copied-source imports
and real composition pass correction success and timeout with simulated effects.
Ten candidate paths and106 bound source files verify; exact current239174 hashes
are in review-evidence-239228.json. Two tests6.707397637s; cumulative338.756602191s.

Operational finding: independent ControlStore.open_readonly assessment refused
with OperationalError, no mutable/raw-store fallback attempted. The old packet
hash matches the owner's launched artifact; current grant/preparation state was
not independently established. Author assessment remains attributed. This
qualifies unconditional replay-safe wording: owner confirms state and same
operands before exact relaunch selection. No product correction or extra
preparation loop requested; prior completed owner choices remain valid.

Return baton.decide with accepted code and review-state-239228.json read limit.
No live rerun/enabling/production qualification/Git mutation/Work closure.

## 2026-09-22T14:38:24Z — claim239447: live-failure correction changes requested

Review review-2026-09-22T14-38-24Z.md confirms a regression: a failed runtime
read for an identity outside the local launch set is called unallocated, skips
stop and is excluded from cleanup. Positive absence and failed reads must remain
distinct. Three focused checks0.168275467s, including the confirming counterexample;
recorded cumulative378.499244572s. Evidence review-checks-239447.py/.log,
review-verification-239447.json and review-evidence-239447.json.

New task asks the initial implementer for final READY output, leaving no planned
reason for the mandatory independent correction and conflicting with the fixture's
initial lowercase task. Separate actual role inputs without forced verdicts.
Original fault remains generic: provider claims commits, while adapter _unmoved
rejects provider-created history. No-proposal is a terminal consequence, not a
proved exception cause. Missing positive cleanup after59 sweeps also still needs
the owner-selected diagnosis, without performing live cleanup. Explicitly
supersede contradictory replay-safe/unconsumed wording in current operator guide.

Ten candidate paths and106 bound sources verify unchanged. Retained live run
is held/exceptional, not independently accepted; author live-store assessment
remains attributed and used a write-capable opener. Reviewer did not access the
live store this turn. This supersedes claim239365 completion; return baton.decide
for existing239355 bounded continuation. No live/Git/enabling/closure.

## 2026-09-22T14:56:01Z — owner239562 split pinned by claim239589

OWNER-SPLIT-20260922.md supersedes combined baseline/review/resume execution
and the proposed R2 shared-task review-instructions expansion. Execute and
independently accept W239528 implementation/proposal/stop/positive cleanup first,
then W239533 independent review/verdict/stop/positive cleanup. W236087 retains
only restored-context correction after both, using actual context and review
provenance. Historical proofs and failed evidence remain intact; no Job closes.

Review-handoff review-2026-09-22T14-56-01Z.md preserves claim239485 changes,
current hashes in review-evidence-239589.json and author-reported verification
cumulative415.934725242s. No tests or live-state access in this split-coordination
turn; latest partial corrections are not newly certified. Exact file ownership
must pass before reuse by the prerequisite handlers. No R2 product seam begun.

Canonical snapshot239591: W239533 is blocked on W239528; W236087 dependency
not yet added. Return to baton.decide and release claim; owner applies W236087
blocked-by-W239533 after release as ruled, and routes only the baseline first.
Outstanding prior cleanup and consumed grant remain preserved facts. No live,
destructive cleanup, force release, overlapping edits, enabling or closure.
