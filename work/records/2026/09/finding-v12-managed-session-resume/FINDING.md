# Managed session resume for v12 Jobs

## 2026-09-23 -- claim 250376, the continuation input, read rather than assumed

Owner reroute 250274 routed the remaining resume proof to implementation and
asked for the real continuation input. Reading W239528's retained stores
read-only, through the pinned manager snapshot, answers it in two opposite
halves.

**The context to resume exists and is sound.** The producer attempt's provider
context is finalized at generation 0 with status `ready` -- the exact
predecessor a generation-1 restore requires -- and it survived the runtime's
destruction and the `retained` cleanup.

**The verdict that would open a correction does not exist, and this subject
cannot produce one.** The line is `accepted` and that acceptance is its
integration eligibility; no owner-committed correction exists for the frozen
checkpoint; `correction_feedback_of` refuses because the only context use is an
`open` invocation. `attach_review` admits `review-ready` alone, so no second
review can attach; `changes-requested` is the only disposition that yields
`correction-ready`; and the restore reader holds both the verdict and the
retained report to `changes-requested` from frozen custody. The acceptance was
a judgement rather than an artefact of the criteria, which say in terms that
all three verdicts are valid and none is better for the reviewer.

So this Job needs a NEW SUBJECT, not a repair, and the selection is the
owner's. [CONTINUATION-250376.md](CONTINUATION-250376.md) sets out three
options and recommends one: a new implementation and review pair under neutral
criteria, with a packet that treats `accepted` as a valid end state rather than
manufacturing a correction. It also needs a fresh run identity, since the old
qualification grant is consumed.

**The product seam this dossier pinned as unavoidable is retired.** Separate
Jobs already carry their own task documents -- W239533's review Job did -- so
stage-specific requirements need no change to `claude_agent.py`. It was the
combined-Job shape that needed one. No product byte was changed under this
claim and none is proposed.

What remains unproved is what it has always been: that the production CLI
restores a real conversation. The provider subprocess is the one seam the
deterministic evidence stands in for.

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


## 2026-09-23 — owner selects bounded resume continuation

Owner requests resolving W236087 after W239528 and W239533 closed satisfying.
Retain the separate resume/correction scope; W247941 adoption is not blocked
on reuse. W239533 returned accepted, not changes-requested: do not fabricate
correction feedback. Establish the supported continuation input and identify
any additional execution selection needed. Preserve actual context, proposal,
review provenance, failed evidence and consumed grants. No live execution,
deployed-store mutation, destructive recovery or broad refactor selected.
Prepare actual executable deterministic proof and independently reviewed packet
with exact commands. Initial ownership is this dossier only; coordinate exact
product paths before changes. Routine corrections return directly to impl.

## 2026-09-23T19:33:41Z — retained assessment independently accepted

Reviewer baton.rvpc, claim 250440, accepts the retained-input assessment in
CONTINUATION-250376.md. Independent ten-check read-only verification passed in
0.22724047498195432 seconds with all answering modules pinned. See
review-2026-09-23T19-33-41Z.md and review-verification-250440.json.
The retained producer context is ready, but the accepted line/verdict cannot
open the supported reviewer-correction path. Return to baton.decide for the
genuine additional subject selection requested in owner reroute 250274.
Actual restoration remains unproved. Exact executable preparation, deterministic
proof, attribution, stopped execution and positive cleanup remain outstanding;
this does not close W236087 or authorize live execution. The current PLAN
supersedes any reading that a live packet alone is the remaining obligation.
Recommendation: an eligible real correction subject or a new pair under neutral
criteria; deliberately steering the verdict is not selected. Preserve the
accepted subject and all prior failed-run and consumed-grant evidence.

## 2026-09-25 — owner selects bounded Tuner disposition assessment

Owner approved an evidence-only Tuner assessment of W236087: recommend defer, narrow remaining scope, or the smallest suitable future proof, with one exact owner disposition command. This supersedes the current subject-selection next action for this assessment turn only; it does not select a new subject or any execution. Preserve the accepted proposal/verdict and historical evidence. A recommendation is not acceptance of production restore.

Tuner owns a new DISPOSITION-20260925.md recommendation and any appended coordination summary in FINDING/PLAN under its claim. No product/test edits, tests, harness, live model/engine operations, deployed-store access, recovery or Git mutation. Use existing dossier evidence and read-only coordination/source inspection. Return directly to baton.decide with the recommendation and command. Do not add an adoption prerequisite or expand the recovery -> fresh packet -> two-Job proof -> bounded real v12 work path.


## 2026-09-27 — W285642 current-spec/policy supersession

DESIGN sections1,9,18 and the September23 required-reuse ruling supersede the
optional-final-delivery statement in DISPOSITION-20260925.md and any matching
historical scheduling text. Reuse is REQUIRED for final v12 delivery; supported
fresh contexts may establish initial adoption first. Parking is preserved and is
not acceptance or waiver of the remaining managed restore/correction proof.
Keep W177936 closed with its accepted qualification evidence. The current accepted
subject has no honest changes-requested verdict; do not rewrite it to create one.
On selected eligible work, pin a real correction subject and retained context plus
workspace, use a fresh execution/token after confirmed predecessor termination,
and prove useful restored continuation, attribution and cleanup/unknown holds.
Governed context materialization/save/disposal must consume shared token-bound
maintenance; admission/binding must obey DB-1–DB-7. The inherited accepted W239533
edge stays satisfied; no initial-adoption gate is added. The stale parking command
in the historical disposition is not a new command to run. Owner selects the real
subject/live provider question when needed; ordinary deterministic preparation
and honest acceptance remain distinct.

Coordination-only update by baton.tuner under claim285648/handoff285645;
current execution remains in PLAN and canonical Baton state. Historical evidence
and independent reviews are unchanged. No product/test/live execution selected.

## 2026-09-29T17-14-33Z — owner-selected resumption and implementation preparation

Owner E307633/E307644/E307645 explicitly supersedes the Sep25 parked scheduling
disposition: prepare then pass directly to baton.tune for bounded implementation.
Required reuse remains a v12 deliverable; initial parallel adoption is accepted.
PREPARATION-307667.md pins current scope, ownership, finite acceptance and proposed
useful development Job. No live execution/deployment selection or verdict steering.

Confirmed DB-1/2/4 defect: provider_context admission and binding call _facts from
ControlStore transaction callbacks, reaching filesystem and other-store readers.
RESEARCH-307667.json observes two filesystem calls inside public admission's
transaction (0.012545002973638475s excluding cleanup); SOURCE-307667.json pins
inspected bytes. Admission/restore correction must preserve freshness and replay.

Current Sep28 DESIGN also supersedes Sep27 mandatory context-maintenance wording
for the primary path: exclusive host preparation, one leased container, confirmed
termination, status/release; no automatic maintenance or output-validation release
gate. Protected context generations and honest failed-save/refusal remain required.
Accepted historical subject cannot be rewritten as changes-requested. No new graph
gate; inherited W239533 edge remains satisfied. W306614 ownership stays separate.
Reviewer changes only finding/plan/preparation/evidence/review; no product edits.

## 2026-09-29 — implementation ownership reassigned to baton.claude, PINNED BEFORE EDITS

Owner reroute 308630 (baton.prompt, on the owner's authority) reassigns the implementation of this
bounded managed context-reuse work from baton.tuner to baton.claude, on the canonical snapshot 308629
showing the Work queued with no handler. IT SUPERSEDES THE TUNER IMPLEMENTATION ASSIGNMENT ONLY.

WHAT IS PRESERVED EXACTLY AS IT STANDS: the reviewer's preparation `PREPARATION-307667.md`, the
E307708 scope, `RESEARCH-307667.json`, `SOURCE-307667.json`, the latest review, and every historical
author artifact in this dossier. The reviewer keeps FINDING, current PLAN, the preparation and the
review journals; this section is the ownership pin the reroute requires before any edit, and nothing
else in these two documents is altered by me.

IMPLEMENTATION OWNERSHIP NOW HELD BY baton.claude, exactly the set `PREPARATION-307667.md` names:

    v12/python/src/baton_v12/worker_manager/provider_context.py
    v12/python/src/baton_v12/worker_manager/context_delivery.py
    v12/python/tests/manager/test_provider_context.py
    v12/python/tests/manager/test_provider_context_delivery.py
    v12/python/tests/manager/test_claude_context.py

and, for the connected seam only and with baseline digests recorded before editing,
`v12/python/tools/stage_execution.py` and `v12/python/tools/single_worker.py`.

UNCHANGED LIMITS, carried forward rather than re-decided: no edits to W306614-owned
supervisor/tests/diagnostics, no edits to the W247941 accepted packet, frozen manager snapshots,
installed images or DESIGN; no new live execution, deployment change, credential operation or Git
mutation; a specification change goes to the owner. Routine corrections return to baton.impl under
this reassignment (the reroute says so, superseding the preparation's baton.tune routing).

## 2026-09-29T19-50-38Z — independent review308745: boundary correction incomplete

Candidate308641 preserves useful progress, but its claim that qualification and binding status checks are journal-only is superseded by confirmed R1/R2 in review-2026-09-29T19-50-38Z.md. Candidate admission still walks two filesystem ancestries under transaction; finalized binding status can validate generation files. Evidence RESEARCH-308745-followup.json and REVIEW-EVIDENCE-308745.json. Correct within existing scope via baton.impl, then remaining connected proof and packet; no new owner gate. Prior evidence remains unchanged.

## 2026-09-29T20-04-01Z — review308858 accepts R1/R2 correction slice

review-2026-09-29T20-04-01Z.md accepts the candidate308784 code corrections to qualification and finalized binding transaction boundaries, superseding their outstanding-code-defect status in review308745. Item1 remaining proof, item2 connected correction and item3 packet remain open. DESIGN ART-7 and current preserved-workspace cleanup support replacing stale ServingEnding input-absence assertions under standing test authority. Three reviewer diagnostic runs pass with presence asserted; this is not final regression acceptance. No separate approval is required, and no-rematerialization alone does not imply input presence. See REVIEW-EVIDENCE-308858.json / DIAGNOSIS-308858.json. Continue baton.impl under existing ownership/scope.

## 2026-09-29T20-10-41Z — review308912: preservation correction accepted, item1 evidence incomplete

review-2026-09-29T20-10-41Z.md accepts corrected binding comment and restart-preservation expectation; prior R1/R2 acceptance stands. Candidate308879 item1-complete claim is superseded: launch-fence test lacks invocation binding and refuses before facts; unrelated-progress uses one connection after a pretransaction refusal; interrupted replay is completed replay and production refusal misses deployment comparison. COUNTERCHECK-308912.json demonstrates unchanged-repository refusal with zero facts calls. Reuse existing valid ServingBinding authority-fence and qualification request/reopen evidence, fix misleading tests and add selected second-connection progress proof. Continue existing items2/3 without new permission.

## 2026-09-29T20-19-13Z — review308976 accepts evidence corrections; connected proof next

review-2026-09-29T20-19-13Z.md supersedes outstanding evidence-correction status in review308912. Real bound repository-fence refusal and second-connection external-validation progress now observed;33 independent focused tests PASS10.371s. Prior code/preservation acceptance stands. Production deployment-comparison execution remains an explicit connected-matrix coverage limit, not proved by missing-certification refusal. Proceed to item2 connected attributed correction/interruption and item3 exact packet under existing authority. No production restore or live execution claimed.

## 2026-09-29T20-25-55Z — review309023: bounded connected evidence accepted, two gaps remain

review-2026-09-29T20-25-55Z.md supersedes candidate308991 item2-complete claim. Independent export CONNECTED-309023.json preserves accepted deterministic continuity/changed-output/review-isolation/recomposition evidence (3 tests3.304s). C2 does not bind resource tokens or require predecessor destruction: synthetic matching-running runtime passes validator in ORACLE-CHECK-309023.json. New failed-save test is initial-save failure, not preservation of prior saved0 during later failure. Extend existing trace/fixture for exact token/runtime handoff and saved-generation preservation, then packet. No live overlap defect inferred, no new scope.

## 2026-09-29T20-34-52Z — review309087: runtime slice accepted; token gap and fixture diagnosis

review-2026-09-29T20-34-52Z.md accepts runtime destruction/distinctness and first-save relabelling, superseding neither the resource-token nor ordering requirement. Candidate309041 R1-closed claim is superseded: use tokens.py owner readers for actual token/container/return evidence before restored activation. Reviewer resolves R2 fixture blocker: end_runtime receipt mode=open must be restore; both positive restored finalization and injected seal failure independently reach expected outcomes (DIAGNOSIS-309087.json). Proceed saved0 preservation, token proof, labels and packet within existing authority.

## 2026-09-29T20-42-20Z — review309137 accepts saved0 preservation and observes token ordering

review-2026-09-29T20-42-20Z.md accepts R2 saved-generation preservation (2 tests0.141s). TOKEN-RESEARCH-309137-followup.json independently observes real token1 returned before restored token2 activation in same workspace domain, each bound to its own container. Exact acquire/admit_activation observation seam resolves author lookup uncertainty. Complete normal export/negative assertions, simulated labels and packet; preserve positive evidence and prior accepted slices. No live coverage claimed.

## 2026-09-29T20-49-45Z — review309198: token identity lost by validator

review-2026-09-29T20-49-45Z.md preserves accepted observation/export progress but finds generation-only indexing aliases different resource domains: exact opening-only unreturned mutation passes. Wrong container/launch mutation also passes (ORACLE-CHECK-309198.json). Match full token tuple and bound runtime/start operation; retain correct positive evidence. Independent12PASS6.534s; no live product defect inferred. Complete narrow oracle corrections, labels and packet without new permission.

## 2026-09-29T21-02-11Z — review309290 accepts token oracle and deterministic proof corrections

review-2026-09-29T21-02-11Z.md supersedes outstanding oracle corrections from review309198. Full reservation identity and container/launch comparisons plus focused negatives pass; simulation labels accurately delimit evidence. Independent16PASS9.809s and clean diff check. Finite item2 deterministic corrections accepted; executable packet is next. One author-reported boundary failure without retained assertion remains unexplained, not fixed/waived; retain full diagnostics if it recurs without blocking independent packet preparation. Production comparison/actual restore remain unproved.

## 2026-09-29T21-08-40Z — review309336: executable packet not yet delivered

review-2026-09-29T21-08-40Z.md supersedes candidate309306 item3-delivered/nothing-else-missing claims. All machinery hashes match, outcomes useful, but context/Job setup are comments; task/review/bootstrap inputs and enforced bounded supervisor are absent; execution source and reused profile compatibility are not concretely bound. Complete dossier packet code/templates/commands/deterministic checks under existing authority before an exact owner selection. Preserve prior implementation/deterministic acceptance.


## 2026-09-29T21-41-08Z — packet candidate309356 review

Item3 executable claim not accepted: real bootstrap/submission validators refuse
generated inputs; shutdown omits cancellation/discovery/deferred interrupts;
verdict reader expects fields absent from real status; binding adopts intervening
drift. Prior product/item2 acceptance preserved. See review-2026-09-29T21-41-08Z.md and
REVIEW-EVIDENCE-309547.json. Ordinary implementation correction, no owner gate.


## 2026-09-29T22-02-59Z — partial packet correction checkpoint

Candidate309572 improves input validation, shutdown, verdict/episode reading and
drift checks. Independent104 tests PASS0.381s. Author explicitly leaves worker
deployment and connected packet proof unfinished. Continue implementation under
existing scope; no owner gate or final acceptance. See review-2026-09-29T22-02-59Z.md.


## 2026-09-29T22-15-01Z — worker packet incremental review

Candidate309722 focused124 tests PASS0.757s and digests match. Worker validation,
latest canonical generation/verdict lookup and supplier binding progress retained.
Connected packet proof still owed; ordinary implementation continuation. Scripted
fake-provider scenarios are authorized deterministic evidence, never live judgment.
See review-2026-09-29T22-15-01Z.md.


## 2026-09-29T22-23-10Z — enclosing composition correction reviewed

Candidate309811 digests match; two new composition checks independently PASS
0.153s. Correction accepted as incremental evidence. Connected packet proof not
run, unchanged next milestone. Author budget explanation has no accompanying
runner/provider exhaustion evidence; no owner gate follows. See review-2026-09-29T22-23-10Z.md.


## 2026-09-29T22-36-24Z — connected admission refusal localized

Supersedes author309871 admitted-attempt/sweep-timing interpretation: real status
shows workload profile/name mismatch, zero admissions and runtime=null. Job
episode identity is not runtime admission. See review-2026-09-29T22-36-24Z.md and
ADMISSION-RESEARCH-309944.json. Correct generator coherence; no scheduler change.


## 2026-09-29T22-44-32Z — launched runtime and stale fixture lookup

Profile correction verified by running runtime-single-1/generation1 in connected
fixture. Supersedes missing claim/launch or mounted-failure speculation: actual
traceback is inherited turn launch.adopt via old self.config launch_home, then
delivered.document. See review-2026-09-29T22-44-32Z.md, RESEARCH-310001.json and
TRACEBACK-310001.txt. Continue fixture coherence correction, no scheduler change.


## 2026-09-29T22-51-42Z — frozen provider result explains exceptional state

Independent canonical output is unable, proposal provider-failed/start-error/
status1, why provider context terminal identity is unproved. No verification was
attempted. Supersedes checkpoint speculation about verification/test-scope ending
failure; managed/start/preparation failures are null. See review-2026-09-29T22-51-42Z.md
and PROPOSAL-RESEARCH-310055.json. Continue attributed adapter diagnostic work.


## 2026-09-29T22-58-46Z — actual scripted child error captured

Child FileNotFoundError writing docs/v12-context-correction.md exits1 before
terminal JSON. Active provider is process-backed World.provider; generic stub
hypothesis superseded for this run. Diagnostic PIPE capture retained in
CAPTURE-RESEARCH-310105.json; see review-2026-09-29T22-58-46Z.md.


## 2026-09-29T23-04-18Z — finalization refusal and retention mismatch

Provider completes but context held custody-invalid. First refusal old runtime
exclusion is unproved: profile/worker retention5555 differs from composition0f4c.
Confirmed owner-read evidence in RETENTION-RESEARCH-310149.json. Null exchange
is not causal evidence. Also reconcile static provider session path mismatch.
See review-2026-09-29T23-04-18Z.md.


## 2026-09-29T23-17-24Z — connected endings accepted; packet entry still incomplete

Verdict: changes requested, finite packet entry corrections. Candidate310169 hashes all match. Independent focused packet/connected suite: 133 PASS in 9.812s. Evidence: REVIEW-EVIDENCE-310221.json. Read handoff E310219, events through310221 and T236087 through239616 (no new discussion).

Accepted slice: retention/session-path coherence and deterministic connected endings now pass, including actual journal-proved restore and canonical verdicts. Preserve prior items1/2 and lifecycle/guard evidence. This is fake engine/scripted provider/reviewer evidence, not live provider judgment. No product changes reviewed this turn.

R1 — executable fresh-instance entry remains incomplete. correction_packet.bootstrap_document intentionally emits no Jobs/workers. tools.bootstrap.configuration therefore emits job_bindings=[] and no job_work_id. The pure real-builder reproduction in REVIEW-EVIDENCE-310221.json confirms qualified_work_id refuses that output. Commands go straight from bootstrap to bind, which requires this missing identity. Also bind reads instance_root/run/deployment.json while bootstrap.layout emits state_root/deployment.json; these are different under the selected operands. The fixture writes bootstrap.json and an invented preexisting Work binding, bypassing this boundary. Supply the actual supported preparation operations creating/binding the disposable Authority Work and needed Job inputs before bind, and derive paths from the emitted installation. Do not merely inject another fixture identity or submit the execution Job early (baseline.survey rightly refuses collisions).

R2 — command environment/path coherence. Step3 check omits staged PYTHONPATH although held_packet invokes real product validators. Step5 status hardcodes instance_root/db stores whereas bind uses selected stores. Unify these with the installed/selected paths and prove commands under their declared environments, without ambient checkout imports.

Closure: extend focused deterministic evidence from fresh supported installation/preparation outputs through bind/check and the actual supervisor preparation entry (baseline.prepare), then reuse the accepted connected endings. No live bootstrap/provider/engine run is selected; exercise disposable owner APIs and supported document builders, and label any remaining boundary simulation. The requested packet must be executable after owner operands are supplied. Review the final digest-bound candidate after these entry corrections; no broad rerun or lifecycle redesign is requested.

Ownership: Claude owns existing packet/supervisor/trace/tests/operator packet and PROGRESS; reviewer owns FINDING/PLAN/reviews/evidence. No sibling helper, DESIGN, W306614, Git, graph, deployed store/grant or credentials changes. Historical transaction-boundary failure remains UNKNOWN, production comparison/live restore unproved; neither erased nor newly asserted. Ordinary verification has no cumulative approval gate. No owner decision is needed for these in-scope corrections.


## 2026-09-29T23-28-53Z — fresh CLI identity and operator-template refusals

Verdict: changes requested, two concrete executable-entry defects. Candidate310263 and unchanged supervisor hashes match. Independent focused suite139 PASS10.403s. REVIEW-EVIDENCE-310326.json retains the exact pure-reader refusals. Read E310319/events310326 and T236087 through239616, no new discussion.

Accepted: previous path/environment fixes, supported prepare_work acts over disposable Authority, actual baseline.prepare and connected endings. Preserve prior items1/2, restore/token/cleanup evidence and no-implicit-reopen rule. Fake engine/scripted provider/reviewer and installation-record simulation remain labelled. No product/test implementation edited by reviewer.

R1 — fresh CLI Work identity is invalid. prepared_work_id produces 7ea319da-Wmanaged-correction-309356 for the supplied run. Authority identity.check_work_id (called first by Core.create_work) requires <8 hex>-W<positive integer> and refuses it. prepare-work CLI uses this generator; connected_packet_trace.prepare_supported_work instead passes self.work, an existing valid fixture Work, so the fresh-ID path is untested. Use a supported valid identity selection/derivation with collision refusal, and verify the actual CLI operand path creates a previously absent Work in a disposable Authority, then handles exact replay. Do not satisfy this by substituting an existing World Work in the test. No live installation needed.

R2 — supplied operator template has drifted from its generator. held_selections(SELECTIONS-309356.json) refuses missing receipts before even reaching owner placeholders; stores is also absent and participants still includes receipt principals in the old shape. Correct the template to current schema and reflect its current digest and commands in PACKET-309356.md. Demonstrate that replacing only the explicitly named owner operands yields admitted selections; owner selection cannot be asked to reconstruct an undocumented schema. The packet still says three subcommands despite prepare-work, and says no store was opened despite documented disposable-store proofs; clarify as no deployed store opened. These documentation corrections accompany the same executable-template fix, not a new scope.

Closure remains narrow: corrected template -> actual fresh prepare-work CLI -> bind/check -> already accepted baseline.prepare/connected endings. Run focused deterministic regression and present final digest-bound candidate. No new lifecycle implementation, broad rerun, live provider/engine, deployed store/grant, credentials, Git, graph, DESIGN, sibling or W306614 work selected. Claude owns packet/harness/tests/operator docs/PROGRESS; reviewer owns FINDING/PLAN/review/evidence. Historical boundary failure UNKNOWN, production comparison and live restore unproved remain preserved, not waived. No owner decision required for these corrections.


## 2026-09-29T23-40-17Z — preparation collision is not exact replay

Verdict: changes requested for one preparation replay/collision defect. Candidate310345 and unchanged files all match. Independent147 PASS10.425s. Read E310402/events310404/T236087239616 (no new messages). Evidence REVIEW-EVIDENCE-310404.json.

Accepted: valid fresh Work selector and actual CLI creation, corrected fillable operator template, prior command paths/environment, baseline.prepare and connected endings. Prior items1/2 and token/cleanup/restore evidence remain accepted. No implicit reopen; no new product scope.

R1 — a common assignment contract is not preparation identity. prepare_work skips create_work for ANY existing same-contract Work, without checking the original operation identity or bound preparation operands, then grants capabilities in its scope and sets global canonical_target. Independent disposable CLI reproduction created W236087 under unrelated-original-creation and scope:unrelated with the ordinary v12-assignment-1 contract; prepare-work accepted it as created=False and granted its four capabilities in scope:unrelated. Repeating with declared_base changed from a*40 to b*40 also succeeded and reported the new target as a replay. The product journal's collision checks are bypassed by skipping creation; the existing test checks only a different CONTRACT, not an unrelated act under the same contract. This violates the promised exact replay and collision refusal, not a speculative hardening gate.

Required bounded correction: bind preparation to its actual operation and operand identity, refuse unrelated same-contract collisions and changed replay inputs BEFORE grants/policy mutation, and retain recoverable exact replay after partial preparation. Use supported Authority APIs and/or a durably checked preparation record; do not read the store directly or weaken the product identity gate. Cover fresh creation, exact replay, unrelated same-contract creation/scope, and changed base/participant operands with refusal leaving policy/grants unchanged. The connected fixture must stop relying on adoption of an unrelated preexisting World Work as if it proved exact replay; establish the same preparation identity or isolate its accepted connected proof explicitly.

No lifecycle redesign or additional live test is requested. Reuse accepted connected endings after the bounded preparation fix. Claude owns packet/harness/tests/operator docs/PROGRESS; reviewer owns FINDING/PLAN/review/evidence. No product/sibling/DESIGN/W306614/deployed-store/grant/credential/real-engine/Git/graph changes or broad tests. Historical boundary failure remains UNKNOWN and production comparison/live restore unproved. No owner decision required for this in-scope correction.


## 2026-09-29T23-49-58Z — explicit operation-id bypasses operand binding

Verdict: changes requested for the remaining operation-id override bypass. Candidate310425 and unchanged hashes match; independent152 PASS10.453s. Read E310474/events310476/T236087239616, no new discussion. Evidence REVIEW-EVIDENCE-310476.json.

Accepted: default operand-derived preparation identity, unconditional journalled creation gate, unrelated collision refusal, unchanged grants/policy on default-path refusal, partial recovery and fresh connected fixture. Preserve prior accepted items1/2 and packet/connected slices. No implicit reopening.

R1 — the supported CLI override still defeats the fix. main passes taken.operation_id OR preparation_identity, and prepare_work trusts the supplied ID. The same --operation-id fixed-operator-id with base a*40 followed by b*40 succeeds twice, reports created=False, and Authority.policy(canonical_target) changes from a*40 to b*40. The attached independent disposable CLI reproduction records both actual policy values. The product create_work payload contains no base/participants, so reusing a caller ID replays creation while the subsequent changed grants/policy still execute. This is the same defect through an exposed operand, not a new scope.

Close the bypass at the preparation mutation boundary: remove the override if unnecessary, require it to equal the derived identity, or bind the caller namespace together with the exact operands so changed inputs cannot reuse the creation identity. Direct prepare_work callers must not bypass operand binding either. Verify changed-base/participant attempts using a fixed override refuse before grants/policy mutation, while exact and partial replay still succeed. Update the stale option help if retained. Reuse the accepted connected suite; no broader execution needed.

Claude owns packet/harness/tests/operator docs/PROGRESS, reviewer owns FINDING/PLAN/review/evidence. No product/sibling/DESIGN/W306614/deployed store/grant/credential/real-engine/Git/graph or broad test scope. Historical boundary failure UNKNOWN, production comparison/live restore unproved retained. No owner decision required.


## 2026-09-29T23-55-32Z — bounded preparation independently accepted

Verdict: ACCEPTED for the bounded PREPARATION-307667 milestone as subsequently assigned to Claude by E308630. No remaining in-scope candidate correction identified. Delivery to baton.decide; this is not live execution selection or proof of production restore.

Candidate CANDIDATE-310491.json sha256 f6799bd5d89e79882fcc7a89ef36dd85f333afd72e6cd38bfe4e8928ff4ae4e7 and every changed/unchanged candidate file digest match. REVIEW-EVIDENCE-310521.json enumerates exact reviewed bytes and prior accepted product/connected-trace hashes (also unchanged). Independent focused155 PASS10.452s. Read complete E310519/current events through310521 and T236087 through239616, no new discussion. Current PLAN and prior final correction read.

Final defect resolved: prepare_work derives operation identity from its mutation operands inside the helper; no caller identity parameter and no CLI override remain. Journalled create_work runs before grants/policy; changed base/participant and unrelated same-contract creation refuse, exact replay and interrupted preparation complete. The fresh connected fixture creates its own Work. The new tests retain positive/negative behavior without weakening accepted expectations. Existing dossier test paths reviewed: test_correction_packet.py (override/parser/helper/unchanged-effect regressions), test_connected_packet.py (previous fresh preparation/connected assertions preserved). connected_packet_trace.py adapts the call to the closed helper boundary. No product source change in this final candidate.

Finite acceptance ledger:
1. Admission/binding external reads outside transactions with local CAS, replay, qualification and launch fencing: prior acceptance preserved; provider_context.py accepted bytes rechecked.
2. Connected deterministic open/save/stop/review/correction/restore/useful-output, token exclusion/order and failed-save preservation: prior acceptance preserved; correction_restart_trace.py and test_correction_restart.py accepted bytes rechecked. Prior review-2026-09-29T21-02-11Z.md and its16 PASS9.809s remain applicable.
3. Executable digest-bound packet: accepted current correction_packet.py, correction_supervisor.py, operator PACKET-309356.md, fillable SELECTIONS-309356.json, existing provenance/supplier/baseline checks, deterministic command/preparation and four-outcome proof. Current155-test run covers creation/replay/collision/partial recovery, schema/template/command validation, bound supervisor, canonical verdicts, retained generation restore and honest negative outcomes. Prior detailed reviews supply the cumulative audit; no accepted slice implicitly reopened.

The next owner action is select or decline the provider-specific experiment and resolve the ten named template operands (source/base, source exclusion, credential reference, three execution principals and three receipt writers). Generated commands, bounded900s total with60s internal cleanup reserve and invocation limits are the prepared proposal. No fresh Git commit is required by this acceptance; agents do not own Git. Live bootstrap, real engine/model, deployed stores/grants and credentials were not used or enabled. Bootstrap installation itself remains simulated at its output boundary; actual provider CLI restore and production comparison remain unproved. An accepted-without-correction live result would not prove restore and must not trigger a forced rerun. Historical transaction-boundary failure cause remains UNKNOWN, neither fixed nor waived; retain diagnostics if it recurs.

This acceptance completes the selected preparation, not the broader real-provider question. Preserve dossier/candidate/evidence and previous ownership history. No new graph, sibling, DESIGN, W306614, product or integration action requested. Reviewer only changed FINDING/PLAN and append-only review/evidence.


## 2026-09-30T02-44-57Z — owner-selected concrete proposal; command delivery corrections

Authority: owner E311598 accepts E310533 preparation and requests filled selections plus exact setup/run/status/stop commands, independent review then baton.decide live selection. No live run, credential copying, deployment/Git mutation or new framework selected. This owner direction is pinned here; prior implementation acceptance is preserved.

Verdict: changes requested on command delivery only. Candidate311606 and preserved helper/template/packet hashes match. Independent161 PASS10.404s. Six added resolved-selection cases pass, including configured principals/reference and source/base checks. Read E311598/E311641/events311644 and T236087239616 (no new discussion). REVIEW-EVIDENCE-311644.json contains exact hashes and shell/argv evidence.

Accepted portion: filled SELECTIONS-RESOLVED-311606.json has zero unresolved operands and carries the accepted source/base, six principals and credential reference. No credential registry/bytes read. Actual session currency remains unverified. Prior deterministic implementation and packet acceptance stays valid; no live restore/production comparison asserted. Owner must still select whether to run and the final roots.

R1 — shell examples have TWO trailing backslashes, not one, on15 lines. In the indented Markdown code blocks these are literal shell bytes. Bash -n succeeds (syntactically legal), but a stub-only execution of the exact stage example shows python receives arguments correction_packet.py, stage, literal backslash; --selections and --provenance become separate commands. The same fault affects install/bind/check/run/status/outcome examples. Replace with shell-valid continuation or exact single-line commands and validate argv using harmless stubs, never the real setup commands. The status Python expression itself is syntactically valid; initial visual quoting concern was not confirmed and is not a finding.

R2 — delivered RUN-COMMANDS-311606.json step6 contains literal <the uuid tools.bootstrap minted, in <root>/bootstrap.json>, while OPERATOR says the list already substitutes it. No instance exists yet, so the UUID cannot be supplied now. Mark this step pending and point to bind-generated commands.json after installation, or provide an exact safe read-only resolver command. Do not pass the placeholder as an argument. The new test named generator equality checks only verb/environment fragments and absence of shell substitution; it never compares the complete generated command data, and therefore does not establish its claimed equality. Add focused validation that the deliverable cannot present a placeholder as executable and that the operator uses the post-bind status argv. Correct root-change wording: dependent paths/commands must be regenerated coherently, not changed in one isolated string.

Next: Claude corrects only current operator/command artifacts and focused checks, refreshes candidate hashes, returns baton.bug; review then baton.decide for live selection. No new product/helper/lifecycle implementation or broad verification scope needed. Author owns these artifacts/tests/PROGRESS; reviewer owns FINDING/PLAN/review/evidence. Historical boundary failure UNKNOWN and fake-provider/bootstrap-output simulation limits retained. Accepted-without-correction is valid and never a reason to force a restore/rerun.


## 2026-09-30T02-51-33Z — concrete experiment proposal accepted

Verdict: ACCEPTED for owner E311598 concrete proposal delivery. Return baton.decide for live selection. Prior preparation acceptance E310533 remains intact; this is not authorization to execute.

Candidate CANDIDATE-311661.json sha256 1e185b4c42f0faa5f5a9cc41f676e025b1fad240c9cb8ff7db1de949d3d11472. All changed and preserved file hashes match; REVIEW-EVIDENCE-311696.json enumerates the reviewed bytes. Independent165 PASS10.487s. Read E311693/events311696 and T236087239616, no new discussion. Current checkpoint and prior two findings read.

R1 resolved: single shell continuations retain operands in their intended invocation. Independent shell-function stub executed only shell parsing/expansion, logging ten python argument vectors without invoking Python, setup, stores or providers. The stub supplied a synthetic UUID to the read-only resolver and the status argv contains that UUID in exactly the correct operand. This proves shell wiring, not live bootstrap or authentication. Author ARGV-EVIDENCE-311661.json is consistent, with its empty-resolver limitation accurately recorded.

R2 resolved: delivered JSON includes executable steps1-5/7 and explicitly pending status step6, with resolver and pointer to post-bind commands.json. No executable placeholder remains. Tests compare complete delivered command data with generator output and retain schema/selection/connected tests. Existing changed test path test_correction_packet.py reviewed: added exact command equality, pending resolver and continuation regressions strengthen expectations; no product/helper edits in this candidate.

Accepted proposal artifacts: SELECTIONS-RESOLVED-311606.json, RUN-COMMANDS-311606.json, OPERATOR-311606.md at evidence-bound hashes. Source/base, configured principal/reference provenance and zero unresolved selection placeholders retain prior review acceptance. Credential session currency remains unverified; no credential registry or bytes read. Actual live provider restore and production comparison remain unproved, and historical transaction-boundary failure cause remains UNKNOWN. Existing fake-engine/scripted-provider and bootstrap-output simulation limits remain explicit.

Owner choices: select/decline this experiment, confirm credential currency and final roots. This acceptance binds the delivered roots and dependent paths exactly. OPERATOR's residual phrase 'changing it is one edit' must not be interpreted as permission to change only instance_root: any changed roots require coherent selections/path regeneration and validation, as recorded in review311644. That is a scope clarification, not a blocker for the concrete unchanged proposal. No fresh Git commit required. Accepted-without-correction is valid and proves no restore; never force a rerun to obtain correction.

No live setup/run, deployment/store/grant/credential/image, Git or graph mutation occurred. No new framework/product/sibling/DESIGN/W306614 work. Reviewer changed FINDING/PLAN and append-only review/evidence only. No remaining correction blocks this proposed delivery.


## 2026-09-30T03-32-07Z — actual bootstrap correction accepted; status/stop regressions

Authority pinned: owner E311736 reports setup failed before live execution because .py-only staging omitted contracts/schema/worker-control-1.0.schema.json. Later prepare-work/bind/check failures followed missing bootstrap.json/packet.json. Selected correction: resource staging and digest checks, actual disposable stage-to-bootstrap proof without Docker/provider, read-only partial inventory, preserving recovery commands and stop-on-first-error; independent review then owner. No live execution/Git mutation.

Verdict: staging correction and disposable recovery proof ACCEPTED; changes requested on two newly regressed operator commands. This explicitly supersedes the prior executable-setup assurance in review311696 where real bootstrap had not been exercised. Preserve historical acceptance/evidence and accepted lifecycle/connected behavior; do not erase the observed operator failure.

Candidate311743 sha256 65fa60a2487747916199122e2baacc0b164d7464de7ad266e78655c439e62ad6, all changed/preserved hashes match. Independent180 PASS28.456s. Independently executed staged_bootstrap_trace.py: actual stage -> tools.bootstrap -> prepare-work -> bind -> check ALL exit0,108 staged files including both frozen resources, absence reproducer fails as expected, disposable root cleaned by trace. Evidence REVIEW-BOOTSTRAP-311971.json and REVIEW-EVIDENCE-311971.json. No Docker/model/provider or deployed setup. The earlier bootstrap-output simulation limitation is resolved for this disposable setup path, not for live runtime/provider behavior.

Read-only recheck: instance remains absent; four failed partial packet documents retain exactly the recorded hashes. New staging and destination preserve those artifacts. Reviewed declared-package/resource selection, resource import/digest checks, actual checkout boundary guard, step0 origin imports, refusal of unbound staged files, and author stop-on-first-error evidence. No broader rerun needed. Read E311736/E311969/events311971/T236087239616, no new discussion.

R1 — OPERATOR-311743 section4 regresses supported status syntax. It uses --job-store and status --job, lacks required --store/--incarnation and omits the intended --control. The real tools.job_manager parser refuses the displayed shape with exit2 before opening any store (reproduced using nonexistent paths and synthetic UUID). Restore the exact supported status argv already emitted by correction_packet.commands and the earlier operator document; verify the human command against the real parser or disposable status reader, not just a stub that accepts arbitrary options. No deployed read needed.

R2 — section5 labelled Stop contains no stop action. It merely prints DEST/outcome.json, which is also the wrong location; packet and generated step7 use ROOT/run/outcome.json. Restore the previously accepted one-Ctrl-C managed stop instructions and cleanup/interruption semantics, distinguish stopping from reading the retained outcome, and read the actual bound outcome path. Validate operator status/stop/outcome consistency with the unchanged supervisor/generated commands. The new JSON is not a substitute for a correct human recovery/run document.

Next implementation: operator document and focused validation/evidence/candidate only; retain accepted resource staging and disposable proof. No product/helper/lifecycle changes or repeat bootstrap necessary unless code changes. Existing changed test path test_correction_packet.py reviewed for resource/layout/sequence regressions; expectations strengthen prior behavior. staged_bootstrap_trace.py is dossier evidence, not product code. Author owns implementation docs/tests/PROGRESS; reviewer owns FINDING/PLAN/review/evidence.

Credential currency unverified, live restore/production comparison unproved, historical boundary failure UNKNOWN retained. Accepted-without-correction remains valid and cannot force rerun. No deployed cleanup/unbound copying/Git/graph/sibling/DESIGN/W306614 action.


## 2026-09-30T03-42-32Z — corrected recovery/operator proposal accepted

Verdict: ACCEPTED corrected recovery and operator proposal under owner E311736. Return baton.decide for recovery/run selection. This does not execute or authorize live recovery/run. Prior failed setup and accepted lifecycle history preserved.

Candidate CANDIDATE-311994.json sha256 dfee54edb3d71da3764f82172b22630580ea7a3c8af315483d2f430b0c5bc66e. All changed/preserved file hashes match. REVIEW-EVIDENCE-312052.json binds exact reviewed paths/bytes. Read E312044/events312052/T236087239616, no new discussion. Reviewed current checkpoint and prior findings.

Independent focused19 PASS0.767s (TheCORRECTED_OPERATOR_SEQUENCE and TheRESOLVED_SELECTION), including exact human-vs-generated status argv, real parser acceptance/disposable empty status reader, rejection of prior bad flags, explicit stop action and bound outcome path. Independent shell-function-only check: full ten-invocation sequence exit0 with simulated UUID; failures injected at invocations1/2/3 each exit2 with exactly1/2/3 invocations and none following the failure. No actual operator setup was executed by this stub.

R1 resolved: supported --store, --authority-uuid, --incarnation, status --control restored. R2 resolved: ONE Ctrl-C in serving terminal, managed cleanup/interruption behavior and subsequent separate ROOT/run/outcome.json read restored. Source/supervisor/generator bytes unchanged from accepted staging candidate, so prior independent180 PASS28.456s and real disposable stage/bootstrap/prepare-work/bind/check proof REVIEW-BOOTSTRAP-311971.json remain applicable without rerun. Author reports183 PASS; this turn independently ran only the relevant19. New tests in existing test_correction_packet.py strengthen operator behavior; no product/helper/lifecycle change.

Evidence clarification: author STATUS-PARSER-EVIDENCE-311994.json top-level generated_argv accidentally repeats the interpreter/module prefix. It is not a runnable accepted command. The actual operator document, generator, and independently run real-parser test have the correct single prefix; that independent evidence supports acceptance. Preserve the historical artifact rather than silently rewriting it.

Concrete approved recovery proposal: SELECTIONS-RESOLVED-311743.json; RUN-COMMANDS-311743.json; corrected OPERATOR-311743.md. Staging root /home/sl/baton-staging/managed-correction-309356-source and destination /home/sl/baton-instances/managed-correction-309356-packet-311743 preserve the failed source/packet paths; instance root stays /home/sl/baton-instances/managed-correction-309356, observed absent in prior review. Stage includes frozen resources, verifies them and refuses invalid layout; sequence stops on first failure. Operator performs no manual unbound copy or cleanup. Any changed roots/inputs require coherent regeneration/checking.

Owner next selects recovery/run, confirms credential currency and exact roots. No deployed setup/store/grant/credential, Docker/provider, Git or graph mutation occurred this turn. Live restore and production comparison remain unproved; historical transaction-boundary failure remains UNKNOWN. Accepted-without-correction is valid, proves no restore and cannot force rerun. No remaining candidate correction identified; no new scope/dependency/framework. Reviewer changed FINDING/PLAN and append-only review/evidence only.


## 2026-09-30T04-16-34Z — preparation roots proved; pre-validation mutation defect

Authority pinned: owner E312164 reports successful bootstrap/prepare-work/bind/check followed by baseline.prepare failure because run/workspaces was absent. Store opening preceded failure; no context certification/grant/serving reached. Required correction creates needed roots before registration, verifies permissions and replay safety with supported readers, extends real disposable proof without fixture-supplied prerequisites, preserves installation and evidence. No deployed repair/cleanup/live rerun/Git act authorized for agents.

Verdict: changes requested on unsafe root mutation ordering. Candidate312166 sha2567480af27d419be53b0952a6c6e35ea19a19c91427653b017745c62edf4fc2f48; all bound changed/preserved hashes match. Independent18 focused tests PASS1.201s. Independently ran actual disposable stage/bootstrap/prepare-work/bind/check THROUGH baseline.prepare: successful root registrations/profile certification/grant, supported registration readback, and absent-root negative refusal. Evidence REVIEW-BOOTSTRAP-312285.json, REVIEW-EVIDENCE-312285.json. Preserve this successful proof; bootstrap/registration are no longer fixture-only evidence.

Observed owner failure supersedes previous assurance that setup through check establishes all supervisor preparation prerequisites. Existing accepted lifecycle/restore evidence remains historical acceptance, not erased. REPLAY-SAFETY-312166 reports supported readers on disposable copies: neither registration and no Jobs; this supports reusing the installation, no new instance gate. Reviewer did not touch deployed stores or perform repair. Read E312164/E312283/events312285/T236087239616.

R1 — create_filesystem_roots changes permissions BEFORE checking type/canonical ancestry. os.makedirs(exist_ok=True), os.chmod and os.stat/chown follow an existing symlink; verify_filesystem_roots runs only afterwards. Independent ROOT-REPRO-312285.json points the selected private-context root at an unrelated temporary0755 directory: creation changes the TARGET to0700, then validation refuses inaccessible/replaced ancestry. Refusal is too late: a bind the packet correctly refuses has already modified an unrelated path. The workspace root uses the same unsafe order, including group mutation.

Correct at the creation boundary: validate existing root/ancestry without following links before changes, securely create absent directories, and apply modes/group only to the verified directory being established. Reject symlinks/non-directories or changed ancestry before chmod/chown; do not reinterpret refusal as authorization to repair an unrelated target. Preserve exact/no-op valid replay. Add focused cases for leaf and ancestor symlinks (both roles) with unchanged target modes/groups on refusal and successful normal fresh/replay behavior. Use pinned directory handles/no-follow mechanisms as needed; no product refactor or live repair is requested. Bind's later check remains useful but cannot undo earlier effects.

Operator checkpoint clarification: section1 still describes instance/bootstrap/packet as ABSENT while1b describes the now-existing installation. Label section1 explicitly historical (first failed staging) and make1b/current supported-reader checkpoint the recovery state; preserve the old inventory rather than deleting history. Keep existing installation, re-bind/check/run proposal, no manual unbound copy or cleanup.

Author owns root helper/trace/tests/operator evidence/PROGRESS; reviewer FINDING/PLAN/reviews. No live provider/Docker/deployed repair/credential/Git/graph/sibling/DESIGN/W306614. Historical boundary UNKNOWN, credential currency unverified, production/live restore unproved, no forced rerun retained. Return review then owner after this bounded correction.


## 2026-09-30T04:28:04Z — root-ordering correction accepted, claim312359

Verdict: accepted bounded correction; return to owner for existing-installation recovery/run selection. Candidate CANDIDATE-312305.json sha256 3fa432a406376e5f8ee1b7335ecc4331b7b41b33ac267a3ab3828801d202eb47. All20 changed/preserved file digests match. Independent24 focused root/operator tests PASS1.230s; evidence REVIEW-EVIDENCE-312359.json. Author198 tests remain author evidence, not rerun here.

R1 from review312285 resolved: every path component opens with O_DIRECTORY|O_NOFOLLOW from the filesystem root; absent components use parent-descriptor-relative mkdir; leaf ownership is checked and chmod/chown use the pinned descriptor. Leaf and ancestor links refuse without changing their targets. Fresh creation and valid replay preserve required workspace02770/group1000 and context0700. Reviewed changed existing test path test_correction_packet.py: additive root safety/refusal/replay cases match accepted behavior, no weakened requirement. No product changes.

The diagnostic NOTHING WAS CHANGED describes the refused root/target, not an atomic rollback of the whole two-root bind: the first valid root can already have been established before the second refuses. Acceptance does not claim whole-operation filesystem atomicity. O_NOFOLLOW|O_DIRECTORY refuses links (Linux ENOTDIR); it does not open the link, despite imprecise explanatory comments. Neither wording changes the observed target-preservation result.

R2 resolved: OPERATOR-311743.md labels section1 historical and explicitly directs to current section1b for the existing installation. Prior failure evidence remains intact. The previous root-ordering checkpoint is superseded as resolved; historical setup omissions and accepted lifecycle slices remain preserved.

Retain independently executed REVIEW-BOOTSTRAP-312285.json: real disposable stage/bootstrap/prepare-work/bind/check/baseline.prepare, supported registration readback and missing-root refusal. No repeat needed for this narrowly tested directory-opening correction. REPLAY-SAFETY-312166.json remains author supported-reader evidence for existing installation reuse, not permission to repair it here. Owner E312164 remains controlling: recovery is re-bind/check/run against the installation already created, no new-instance gate or manual cleanup.

Read current handoff E312357, events through312359 and T236087 through239616 (no later messages). Reviewer owns FINDING/PLAN/review/evidence only; author owns helper/tests/operator/PROGRESS. No deployed read/repair, provider, Docker, credentials, Git, graph, sibling, DESIGN or W306614 change. Credential currency remains unverified; historical transaction-boundary failure cause UNKNOWN; live restore and production comparison unproved. Accepted-without-correction never forces a rerun. No remaining candidate correction; next act is owner recovery selection, not an agent live run.


## 2026-09-30T04:41:10Z — old-manifest recovery supersession, review312471

Verdict: accepted bounded recovery transition; return to owner. Owner E312403 supersedes the previous recovery-command assurance: beginning at bind was insufficient because the retained manifest correctly rejected the corrected helper. Root safety, prior lifecycle and disposable bootstrap proofs remain accepted; this new failure does not erase them.

CANDIDATE-312411.json sha256 ee1769567e43962f9fcb3944ef73cd2f2c97d2b0a56488bf567a48f6c4431d9f. All23 changed/preserved file hashes match. Independent27 focused root/operator cases PASS1.191s. Author201 cases remain author evidence. Changed existing test path test_correction_packet.py adds bounded recovery-sequence/preservation assertions consistent with selected behavior; no acceptance waiver. No product or helper implementation bytes changed this candidate; changes are trace/tests/operator/evidence.

Independently ran recovery_transition_trace.py through real CLI recovery and baseline.prepare, recorded REVIEW-TRANSITION-312471.json and REVIEW-EVIDENCE-312471.json. Initial bind refused exit2 naming correction_packet.py. Fresh packet destination stage, prepare-work, bind, check all exited0. Real baseline.prepare succeeded and supported readers returned both registrations. The old destination ten documents, bootstrap record and108 staged files remained byte-identical. Temporary execution root was cleaned by the authorized helper. Total trace duration not measured; no invented bound.

Evidence qualification: the trace creates a disposable installation with current code and substitutes the actual historical helper digest into its disposable retained manifest to reproduce the stale-manifest condition. It does not execute the historic helper or copy deployed stores. The recovery itself edits no old manifest and disables no drift guard. This directly tests the reported digest-transition failure; existing prior missing-root proof remains the evidence for absent-root creation. REVIEW-TRANSITION embeds author claim312411 from the trace constant; this independent invocation belongs to reviewer312471. One deployed read obtained the historical manifest digest, zero deployed writes. No provider or Docker execution.

Exact current recovery is RECOVERY-312411.json and OPERATOR-311743.md section1b: stage into fresh managed-correction-309356-packet-312411, prepare-work (derived identities replay), bind, check, then the selected foreground supervisor. Bootstrap is omitted because installation exists. RECOVERY-312166.json remains historical evidence and is explicitly superseded as an executable sequence. Existing staged-tree byte preservation is demonstrated for this reviewed input; stage copies the selected source, so this acceptance is not permission to stage changed product bytes later under the same review.

The author observed inode-bound registration refusal after deleting/recreating roots following committed prepare. Record as an operational constraint: preserve registered roots and investigate any loss; no deletion, reconstruction or fresh-instance operation is authorized by this review. This recovery concerns an installation with no registrations/Jobs per retained supported-reader REPLAY-SAFETY-312166.json. Existing root/correction/lifecycle proofs preserved.

Read E312403, complete E312468 handoff, events through312471, T236087 through239616 with no later messages. No remaining bounded candidate blocker. Next baton.decide selects existing-installation recovery/run. Credential currency unverified; historical boundary failure cause UNKNOWN; production comparison and actual live restore unproved. Accepted-without-correction must not force a rerun. No deployed repair/cleanup, live provider, Git, graph, sibling, DESIGN or W306614 changes. Reviewer owns FINDING/PLAN/review/evidence; implementer retains helper/tests/operator/PROGRESS ownership.


## 2026-09-30T09-31-50Z — diagnosis review and unauthorized-run incident

Verdict: changes requested in the bounded prompt and diagnosis before owner experiment selection. Candidate314263 sha256 4c36fba5a143ac23f45d1de6363da70e643a4dcff289929da46864053be753d3; all11 changed-file digests match. Independent22 contract/operator tests PASS0.775s. REVIEW-EVIDENCE-314389.json records verification. No live experiment executed by reviewer.

Owner E314261 requests retained-evidence diagnosis, cleanup/context status and smallest next experiment, forbidding live rerun/deployed mutation. Complete author handoff E314387 discloses an unauthorized live execution while checking extracted operator commands. Preserve this disclosure and all spent-run evidence. It cannot be retroactively treated as an authorized experiment.

Independent read of both deployed outcome.json files confirms original309356 exceptional/held, implementation destroyed and retained, review never launched; accidental314263 interrupted/held, cancellation ordered and fenced, no committed cleanup. Independent read-only docker inspect of exact accidental runtime b93155adbe765ac5e0a7e9bbff195e7ce48a8668b4a82193f04ab0af27c8cfb9 shows it EXISTS, exited, Running=false, PID0, exit143, finished09:21:10.997467969Z. Author statement 'no runtime left behind' is therefore inaccurate if it means removed. Correct current incident/candidate wording to stopped retained runtime with no committed cleanup proof. Do not remove it. Preserve old statement as explicitly corrected history. Owner must be told precisely what remains.

R1 — scope the new first-action instruction. correction_packet.instructions is the shared task document (worker_documents shared task_document is inherited by implementation and review). It now unconditionally orders creation immediately before any reading. This conflicts with independent review and with retained correction work: a restored implementer must inspect and improve its existing document and correction, not reset it to a skeleton. Restrict early skeleton creation to fresh implementation when the deliverable is absent, after required role/repository instructions. Explicitly preserve existing bytes on resumed correction; reviewer reads/evaluates without creating or rewriting the proposal. Keep complete criteria identical for both roles, cap180s and the single-file scope. Add bounded task-contract assertions for fresh implementation, correction with an existing deliverable and review; do not claim a model follows these instructions merely because string assertions pass.

R2 — distinguish observation from causal hypothesis. Transcript span172.408s and many reads support that the provider received the prompt and spent its observed session exploring without a deliverable. They do not partition model/service latency from tool execution, prove the missing time reminder CAUSED the failure, or prove that writing a skeleton resolves completion within180s. Label prompt ordering as the proposed experiment, with observed counters separately stated; manager5.537s is residual attribution, not directly measured exclusive manager execution. DIAGNOSIS still describes the superseded first-quarter fix as current. Append explicit supersession referring to final scoped prompt; do not erase the interrupted run. No timeout increase requested. An early skeleton alone is not acceptance and does not guarantee final publication.

Context qualification: author supported-copy reader reports context use HELD/invocation-unknown, generation0 revision3. A transcript on disk is retained evidence, not proof of a committed saved reusable generation or permission to restore it. Correct DIAGNOSIS claim that it 'is what a restore would consume' to this distinction. Keep production reuse/live restore unproved and prior accepted deterministic evidence intact.

No new product refactor, new live run, Docker mutation, deployed repair, cleanup, credentials, Git or graph changes. Author owns correction_packet/test_correction_packet/operator/diagnosis/incident/candidate/PROGRESS; reviewer FINDING/PLAN/review/evidence. Existing tests added for prompt wording pass but do not exercise role-specific interpretation, which is the missing bounded protection. Current exact-command proposal remains pending review after correction, not authorized execution. Both spent identities remain spent; next SECOND identity is only proposed. Read E314261/E314387/events314389/T236087239616. Preserve all prior lifecycle/root/recovery acceptance, historical boundary UNKNOWN, currency unverified, and no forced rerun for accepted-without-correction.


## 2026-09-30T09-41-14Z — scoped prompt accepted; owner decisions pending

Verdict: accepted bounded correction and experiment proposal; owner decisions remain pending. CANDIDATE-314414.json sha256 45be9eac3599d6728979e9d1485334cec3042957a30aea82674cd97d119d99f4; all6 changed-file digests match. Independent29 contract/operator tests PASS0.760s, REVIEW-EVIDENCE-314467.json. Author214 tests/mutation/transition results remain attributed author evidence; no repeat live or disposable bootstrap needed for this prompt-only correction.

Review314389 R1 resolved: generated shared task now distinguishes implementation with absent file, implementation preserving an existing correction document, and reviewer who writes no part of it. Instructions precede the fresh skeleton; resumed work reads/preserves/improves existing bytes. Same criteria, single-file scope and180s cap remain. Changed test_correction_packet.py assertions now protect those branches and explicitly state their limit: wording verification is not evidence of model compliance, causality or successful acceptance. Existing early-skeleton assertion was narrowed to the intended branch rather than waiving behavioral acceptance.

R2 resolved for experiment selection: DIAGNOSIS marks prompt cause as hypothesis, first-quarter text superseded, residual attribution distinct from direct measurement, and held/invocation-unknown generation0 transcript as retained evidence, not a committed saved reusable generation. One residual phrase still says provider delay cannot exceed intervals outside the transcript span. That bound is NOT accepted: service/model delay can occur inside the172.408s span. The explicit no-partition caveat governs this review and supersedes any contrary arithmetic inference in the diagnosis. Proposed prompt change is an experiment, not a proven timeout fix. Earlier unscoped wording in NEXT-EXPERIMENT prose is superseded by the reviewed generated task's three branches; exact command vectors remain applicable to the newly generated digest-bound task.

Incident correction accepted as accurate accounting, not retroactive authorization: unauthorized managed-correction-314263 execution remains recorded. Runtime b93155adbe765ac5e0a7e9bbff195e7ce48a8668b4a82193f04ab0af27c8cfb9 is STOPPED AND RETAINED, not removed; prior independent inspection showed exited/Running=false/PID0/exit143. Outcome records no committed cleanup. Author confirms same state and preserves the mistaken statement as corrected history. No fresh inspection needed absent reported change. Instance, packet, staging and retained conversation remain; owner decides their disposition. The original309356 failed/held run and prior accepted lifecycle/root/recovery evidence remain preserved.

Next owner decision: whether to select the proposed managed-correction-314263-second experiment using NEXT-EXPERIMENT-314263-SECOND.json, SELECTIONS-RESOLVED-314263-SECOND.json and OPERATOR-311743.md section1c; the task bytes are generated by this reviewed helper. Both prior identities are spent. No live execution or cleanup selected by this review. The proposed trial changes prompt ordering, retains cap180s and acceptance criteria, and must measure actual useful output/reviewer result; an early skeleton alone is no pass. No forced rerun on accepted-without-correction.

Read complete E314465/events314467 and T236087 through239616 (no later discussion). Reviewer changed FINDING/PLAN/review/evidence only. No product/deployed/provider/engine/credential/Git/graph/sibling changes. Currency unverified, historical boundary cause UNKNOWN, production comparison and actual live restore unproved. No remaining bounded candidate correction; return baton.decide with explicit incident disposition and experiment decisions.


## 2026-09-30T10-04-54Z — reporting accepted; failed-review ending still owed

Verdict: partial acceptance, continue implementation under owner E314549. Interruption reporting correction is accepted; failed-review finalization remains unfixed. Candidate314551 sha25664840a9786cb270c7740363dd5c186a26d179d1316de49bc7be6ccb356c9eb7b; all4 changed-file digests match. Independent22 reporter/refusal/classification tests PASS0.120s. REVIEW-EVIDENCE-314636.json. Preserve these results and all accepted prior slices.

The reporter now reads SupervisorInterrupted.args and outcome instead of nonexistent .why, retains outcome output, identifies unresolved cleanup and exits130. Focused tests cover the accepted exception contract. This is useful independently of the remaining manager defect.

R1 — E314549 explicitly says to fix both the reporting mismatch AND failed-review finalization path. Adding conclusion-refused makes the existing defect stop sooner; it does not finish the owed failed-review ending. Candidate explicitly leaves the manager path untouched on an asserted lack of authority. That interpretation is superseded here by the owner's current explicit instruction: concrete product correction of this observed path is selected; no new owner gate is required for ordinary implementation. This does NOT authorize live repair, discarding sealed evidence, changing acceptance, or container removal.

Investigate and correct re-entry from sealed unable output with pending cleanup using retained authoritative preparation/ending facts. Relevant inspected path: tools/stage_execution.py stage end calls self._prepared.get(attempt_id) or self._prepare(stage) before choosing the role driver (around1559); tools/single_worker.py ending documents re-entry through immutable freeze/intake/retention/assignment/cleanup. A cached preparation miss must not cause a writer to recreate preserved roots during ending. This is a code pointer, not a prescribed patch: confirm the exact failing stack and smallest owning seam. Preserve held review semantics, no invented verdict, and existing token/retention/exclusive ownership guarantees. Coordinate exact product/test paths before edits and record them in PROGRESS/handoff; reviewer owns FINDING/PLAN.

Required focused deterministic regression: real connected review-provider timeout or unable ending, sealed evidence and pending cleanup, then repeated conclusion/restart with preparation cache absent. Prove no preparation writer mutates sealed bytes; prove the supported failed-review ending reaches its correct durable state, preserving unresolved obligations/evidence without false acceptance. Include replay and applicable cleanup ownership assertions. Unresolved cleanup on the already-spent deployed run remains separately reported and untouched; fixing future/replayed deterministic behavior is not deployed repair.

R2 — stop-detector tests do not drive its actual repeated-tick branch. Current test_A_SINGLE_TICKS_REFUSAL_IS_NOT_A_STOP reconstructs fingerprint tuples inside the test and checks STALLED_TICKS; it would pass if the production counter or return were removed. If the stop guard remains, test actual supervise transitions for a one-tick refusal that clears, unchanged refusal reaching the stop, and changed fingerprint resetting the count. Keep tests deterministic and bounded. This supplements, never replaces, R1 connected finalization proof.

Retain author evidence that implementation completed with early file creation, but no reviewer verdict was obtained. Review timeout cause remains unknown beyond the observed cap; absent transcript is an evidence limitation, not a reason to increase timeout. No new live experiment selected. Exact next executable action is deterministic product correction above, followed by independent review; only then return the smallest justified experiment/commands to owner. Packet manifests become stale when reviewed helper/supervisor changes; preserve stage-to-fresh-destination transition and old packet evidence.

Read owner E314549, complete handoff E314629, events314636 and T236087239616 (no later discussion). No live/provider/engine/deployed/credential/Git/graph mutation by reviewer. Retained review runtime and accidental314263 runtime/path disposition remain owner decisions, not cleanup authority. Historical boundary UNKNOWN, currency unverified, production comparison/live restore unproved; accepted-without-correction never forces rerun.


## 2026-09-30T10-22-40Z — partial finalization correction; connected proof remains

Verdict: preserve partial progress and continue the already-selected connected proof. Candidate314654 sha256 ab5126cb7713a24f7c2f5ae09213b8c8ff5b99a286c0d1a3036dcf4050455996; product stage_execution.py matches declared sha256bad0a355abccf7838f2f4c3948947ace93ff7105a625ae2a866e74eec40d606d. Supervisor/test current hashes recorded in REVIEW-EVIDENCE-314759.json. Independent20 ending-reader/refusal-counter/reporter cases PASS0.140s. Author234 dossier and676 product cases remain attributed evidence, not independently repeated here.

Product change reviewed: _recovered optionally omits boundary composition, _retained uses journaled identity without caching a boundary-free record, end consumes that retained identity. Ordinary mount retains its boundary requirement. This addresses the identified unnecessary preparation on recovered ending. Unit cases mock journal readers and boundary composers; they do not run the real end driver, sealed output, cleanup or restart. The not-cached assertion currently checks a newly constructed composition rather than the instance that was read; retain that as a test-quality limitation, not proof of cache behavior. Code inspection confirms no cache assignment in the new method.

R2 counter improvement accepted: serving loop calls blocked_by, whose real state transitions are now exercised for transient, persistent, changed-since and empty reads. The threshold is STALLED_TICKS further equal readings after the initial sample, not total samples; preserve that precise description. Reporting fix remains accepted. No additional redesign requested.

ONE remaining acceptance milestone: connected deterministic failed-review ending through real stores and the accepted fake-provider/engine fixture. Produce unable or timed-out review output, seal it with pending cleanup, recreate the composition with no preparation cache, then drive repeated conclusion/restart. Assert sealed bytes unchanged, no preparation writer admitted, correct durable failed/held review settlement and applicable cleanup/token/retention state, no false verdict and replay without duplicate effects. This was required by owner E314549/review314636 and is explicitly NOT_DONE in this candidate; broad suite passes cannot substitute. Continue it directly under the existing implementation route rather than returning an owner decision for routine fixture work.

Use/extend the accepted product World/fixture and place durable regression under v12/python/tests/tools/test_stage_execution.py or its existing focused companion as appropriate. Test placement is an ordinary implementation choice under standing test authority, not something requiring owner approval. Record exact owned test paths in PROGRESS/handoff before editing and coordinate any overlap; reviewer owns FINDING/PLAN/reviews/evidence. Do not weaken existing assertions. Product changes stay within the observed failed-review finalization defect if the connected proof discovers another required correction.

Reported test_worker_construction_failure_closes_every_acquired_handle failure is preserved as author-reported baseline failure, reportedly reproduced on staged pre-change source38c4cf74db02. Not independently reproduced this turn; do not label the whole product suite green or silently erase it. Carry exact failure diagnostic/baseline comparison with final handoff. No unrelated fix requested.

Live review timeout cause still UNKNOWN, cap unchanged. Existing deployed cleanup and retained runtimes/path disposition remain separate owner matters, not authority for repair/removal. No live run, deployed mutation, credential, engine mutation, operator-script execution, Git or graph change here. Prior accepted evidence remains; no forced rerun. Read E314757/events314759/T236087239616. Return independent review with connected proof before owner next-experiment selection.


## 2026-09-30T10-33-31Z — causal correction: admission is in single_worker

Verdict: research progress accepted, product completion NOT accepted. Candidate314780 sha2564af84aa671c7f19d22a893f317437cfbe479dec6ac5be7b2d82b5d62ef2d048b; current reviewed file hashes recorded in REVIEW-EVIDENCE-314840.json. Independent six new fixture tests PASS0.167s. The candidate honestly states actual live failure and durable failed-review settlement are still uncorrected/unproved. Continue implementation; this is not a new owner scope decision.

Explicit supersession: earlier stage_execution cache-miss diagnosis in reviewer checkpoints314636/314759 and author claims is disproved as the source of the live refusal. Source confirms single_worker._SingleWorker.ending calls _mounted(checkpoint=False), and _mounted admits preparation with the exact live message before stage.end. StageComposition._prepare itself does not perform that admission; new real-store tests demonstrate this. The stage_execution retained-identity change remains partial candidate work, not proof that the failed-review defect is fixed. Preserve history with this correction; do not keep the test class preamble's old causal story as current truth.

Evidence boundary: the new class uses real stores/line/attachment operations, but directly sets sealed/pending/unable axes and inserts an output referencing the implementation manifest. It is a diagnostic fixture, not a review-provider timeout through real freeze/intake/retention. Its repeated read of _retained is not repeated execution of single_worker.ending/end_review_from_result, and no durable settlement is reached. Keep these useful diagnostics, accurately labelled; do not count them as the required end-to-end proof.

Next executable milestone under E314549: correct the actual single_worker ending re-entry and prove it through the real public driver path with deterministic fake provider/engine at their normal boundaries. Distinguish initial sealing/collection from already sealed output whose intake/retention/pass/cleanup remains owed, recovering exact retained roots and identities without opening a preparation writer or changing sealed bytes. Do not blanket-bypass governance, admit new roots after failure, discard evidence to satisfy admission, invent a verdict, or equate quiescence with committed cleanup. Coordinate ownership for v12/python/tools/single_worker.py and affected focused tests in PROGRESS before editing; changes to the discovered owning seam are already authorized by the concrete owner fix request.

Use the accepted runtime-capable test World or extend it: drive actual unable/timeout result, checkpoint at sealed/pending, recreate composition/process state, then call real ending repeatedly. Prove applicable durable failed/held settlement, retention/assignment/cleanup sequence, no preparation writer, sealed-byte identity and no duplicate effects. A fixture that does not provide the engine half needs extending or replacing for this proof, not an owner waiver. Keep focused tests; do not rerun hundreds of cases in place of completing the missing scenario. Claim end or long turn is a continuation checkpoint, not evidence of a new authority requirement.

Prior reporter/counter evidence remains accepted. Baseline hardening failure and HARDENING-FAILURE-314780.json remain recorded as author evidence, not an all-green assertion. Current extra stage boundary avoidance must remain justified within final minimal fix; no broad hardening selected. Return independent review when actual fix and connected proof are present, then owner exact next steps. No deployed repair/removal, live run, credential, operator-script execution, engine mutation, Git or graph work. Existing deployed cleanup and retained runtimes/path disposition remain separate owner matters. Timeout cause UNKNOWN, currency unverified, live restore/production comparison unproved, no forced rerun. Read E314838/events314840/T236087239616.


## 2026-09-30T11-24-20Z — actual seam changed; settlement evidence still owed

Verdict: partial progress preserved; connected settlement proof still required. Candidate315116 sha2564f727cc9a7ae92b88e9cda70184aa56a16ebb19eb8ab8edd0a26633f7e9cd0ac; all4 product/test hashes match. Independent10 diagnostic cases PASS0.264s. REVIEW-EVIDENCE-315186.json. Author821 product/235 dossier passes remain attributed; baseline hardening failure remains separately reported. Recovery E315113/claim315116 and author no-surviving-process checkpoint read.

The actual seam now consults material_is_offered: _mounted skips preparation admission and assignment_workspace revalidates existing roots instead of allocating. This is no longer only the earlier stage cache optimization. However candidate NOT_DONE still excludes end_review_from_result through retention/pass/cleanup with no duplicate effects. The delivered cases exercise component readers and a fabricated sealed/pending fixture, not the full ending. Thus no claim of fixed live finalization is independently accepted yet.

Required next action remains the same concrete acceptance milestone, not another approval request: use/extend the runtime-capable World and drive actual failed review through seal/intake to pending cleanup, recreate execution state, then re-enter real ending and settle according to existing held/failure semantics. Preserve sealed evidence and assert exact journal, assignment, retention, cleanup and replay effects. A fake engine/provider at its normal boundary is expected; engine absence in ComposedLifecycleCase is a reason to select the right fixture, not a scope blocker. Existing examples to inspect include test_stage_execution's two-stage completion/restart case and test_managed_preparation.OneManagedPreparationCompletes frozen/intake/restart cases; adapt only the bounded failure path.

Additional safety assertion for this implementation: _mounted is shared by execution paths and its branch tests only material_is_offered, not an ending-only mode. The comment says a launch still admits its window, but the branch itself does not distinguish caller intent. Demonstrate through actual caller paths that offered material cannot be launched into a writer, rewritten by task/credential preparation, or have missing/replaced roots repaired when the preparation window is omitted. If callers already enforce this, prove it; otherwise narrow the read-only recovery path. Keep existing live-task/token/cleanup exclusion intact. No blanket governance bypass is accepted from component-level revalidation tests.

Finish the scenario rather than another broad suite run or owner return merely because a turn ended. Author owns current product files and coordinated focused test extensions; record additional exact paths in PROGRESS/handoff. Reviewer owns FINDING/PLAN/evidence/reviews and does not implement the fix. Keep working partial changes, accepted reporter/counter evidence and explicitly corrected diagnosis; no acceptance or cleanup waiver.

No live rerun, deployed repair/removal, provider/credential/engine mutation, operator-script execution, Git or graph operation. Deployed cleanup and retained runtime/path disposition stay separate owner decisions. Cap unchanged; timeout cause UNKNOWN; currency unverified; live restore/production comparison unproved; no forced rerun. Read E315113/E315151/events315186/T236087239616. Return independent review with actual finalization proof before owner next experiment selection.


## 2026-09-30T11-33-49Z — ending-only access scoped; scenario not yet executed

Verdict: preserve bounded safety correction; continue required connected settlement scenario. Candidate315206 sha256e76df158b06210d6f870560e01c7a5769440950eac6905afe707010c04c89a95, all3 declared product/test hashes match. Independent14 diagnostic cases PASS0.362s; REVIEW-EVIDENCE-315259.json. No new live/deployed operation.

The source now defaults _mounted(writer=True); only ending passes writer=False, and offered state remains necessary for skipping preparation. This corrects the broad state-only bypass identified in review315186. Missing/replaced root revalidation negatives remain useful. The writer test itself calls admit_preparation directly and the caller test inspects source strings, so these are not execution proofs of real launch/ending caller behavior. Preserve them without overstating coverage.

The sole delivery milestone remains NOT_DONE in the candidate: actual end_review_from_result through retention/pass/cleanup with recreated execution and replay. A recipe is progress but is not the requested result. Next implementation turn starts by executing the recorded TheComposedJobTraversesReviewAndAcceptance scenario using the accepted fake runtime/provider, not another broad-suite run or another recipe-only handoff. Do implemented(), review waiting, a provider turn without usable review report, and capture the actual unable ending. Stop/recreate at the relevant sealed/pending point, re-enter the real ending, and assert correct durable failed/held result and applicable retention/assignment/cleanup sequence, unchanged sealed bytes, no duplicate effects or false verdict. Correct any concrete further blocker discovered in that selected path and continue until this proof runs.

Add real caller exclusion coverage alongside this scenario: a writer/launch path over offered material must refuse before writing or delivering credentials, while the ending recovery proves existing roots without repairing missing/replaced material. Do not infer that no preparation window means no later writes: drive the whole ending so later task/credential/boundary operations are observed. Keep token/governance checks and sealed evidence protection intact. These are required verification of the current product change, not new product scope.

Owner E314549 supplies continuing authority for the actual fix and deterministic fixture work. There is no concrete owner decision blocking this milestone. A long turn or voluntary handoff does not create one; if interrupted, record the exact last executed step/failure and resume under the same authority. Reviewer remains independent and does not author the implementation. Author coordinates owned single_worker/workspaces/stage_execution and focused product tests, records changes in PROGRESS; reviewer records only.

Prior reporter/counter and historical accepted slices preserved; baseline hardening failure still reported separately, not all-green. Read E315256/events315259/T236087239616. No live rerun, deployed repair/removal, credential operation, engine mutation, operator-script execution, Git or graph act. Existing deployed cleanup/runtime/path disposition remains owner-only; timeout cause UNKNOWN, cap unchanged, currency unverified, live restore unproved, no forced rerun. Return independent review with executed scenario result before owner experiment selection.


## 2026-09-30T11-45-12Z — same-execution proof accepted; restart fixture correction

Verdict: accept same-execution failed-review evidence; correct restart proof before final sign-off. Candidate315275 sha25667b508976f40deb3fbe72a0ef833f7212424ae3ffb4d8745030c817b983a8b1a, declared product test hash matches. Independent runtime-world class16 PASS7.350s (six new plus ten inherited). REVIEW-EVIDENCE-315338.json. Accepted prior partial code/reporting/counter evidence preserved.

The new scenario actually drives a Job, implementation, missing-review-report turn and ordinary sweeps with real worker code/fake engine. It reaches unable/sealed/pending with accepted intake, retain decision, no deferral, zero verdicts and active review attachment. Actual _mounted writer call refuses while ending intent reads roots. This is substantive evidence for the fixed same-execution refusal loop. Explicit clarification of earlier review requirements: a held review need not fabricate a pass, verdict or cleanup merely to satisfy a test. Pending cleanup with owed review is not acceptance, but may be the correct durable held state. Preserve sealed evidence and this accurate limitation.

Remaining R1: the two restart tests do NOT establish process death or supported restart recovery. They call self.serving() while held.composed is still open; both close callbacks run only at test cleanup. serving() also creates a NEW self.engine = self.quiescing(), discarding fake engine state instead of carrying external runtime state across a process restart. Thus the assertion that the old execution died is unsupported, and a second execution refusing a still-owned token is not yet a demonstrated restart bug. Unchanged journals while every call is refused prove refusal safety, not successful ending replay.

Correct the fixture: retire the original manager through the appropriate supported close/release boundary for graceful restart and preserve the fake engine runtime state. For abrupt death, explicitly simulate loss of the manager and run the selected normal recovery/expiry/revocation/positive-cessation protocol; do not force token fields or waive governance. Distinguish those two cases and state which one is selected. Then re-enter using persisted facts and verify the same correct held state and immutable evidence without inappropriate writer admission or duplicate effects. If supported restart genuinely remains blocked, produce that exact evidence and identify the missing authorized recovery step/implementation defect; do not create a new owner policy question from a two-live-composition fixture.

Also label recreated-execution tests and candidate wording accurately until fixed: opening another object is not evidence the old run is gone. Preserve current counterfactual as failure-path evidence; it observes a different ownership refusal from the live offered-material message, so do not conflate their causes. No forced cleanup or disposal is required to turn held into success.

Next baton.impl: finish this bounded restart test/recovery question; same-execution unable ending is accepted and need not be re-litigated. No broad suite repeat required absent new product changes. Owner E314549 remains authority; no new live experiment selected. Read E315336/events315338/T236087239616. No live/deployed/engine mutation/credential/Git/graph action by reviewer. Existing deployed cleanup and runtime/path disposition remain separate. Baseline hardening failure preserved; timeout cause UNKNOWN, currency unverified, actual live restore unproved, no forced rerun.


## 2026-09-30T11-58-44Z — restart-to-held proof accepted, reclaim still held

Verdict: ACCEPT the bounded failed-review ending correction and its restart-to-held proof; pass to owner. This is not acceptance of a completed live Job, live restore, resource release or deployed cleanup. Same-execution and earlier accepted slices stay accepted.

Candidate315369 test hash matches. Independent runtime-world class: 18 PASS8.594s (eight scenario cases plus ten inherited). Additional independent probe: 1 PASS0.738s, executing unable_review/ticks/restarted/reclaimed/ticks and asserting no deferrals. REVIEW-EVIDENCE-315435.json records digests and actual results. Author broader 843 PASS204.2s is reported evidence, not independently repeated; existing hardening baseline failure remains preserved.

The first composition now closes through its supported factory boundary, the same fake engine survives, stores reopen with a later clock and an overdue token, and the production reclaim function/adapter run without token edits. The recovered ending has no conclude deferral and reaches implementation completed, review answering, integration blocked. Tests preserve frozen output/intake/retention/artifacts and zero verdicts. This closes R1 for recovery to the correct held review state. It is deterministic simulation, not OS process-crash or live Docker evidence. ticks still supplies the fixture timestamp while reopened stores/composition use the later clock; no broad time/restart claim follows.

Explicit correction to author candidate/PROGRESS wording: reclaim DOES NOT complete all four steps or return the resource in this scenario. The actual result is reclaimed=held, state=absent, because no writer-absence proof exists yet; the revoked generation keeps the resource. intake.reclaim_expired_resource returns before govern.release in this case. Calling the reclaim entry is not proof of release, and revoked alone is not returned. The new tests assert revocation and preserved state, not reclaimed=returned. Our extra probe confirms both this held outcome and no ending deferrals. That bounded result is sufficient for the accepted held-review contract clarified in review315338; forced cleanup/pass is not required and would be wrong. Full resource settlement and deployed cleanup are not newly accepted.

Some comments in the retained SECOND_LIVE_COMPOSITION test still say restart/old run gone despite its corrected name/docstring. Treat those comments as superseded by this review: that case is only concurrent-composition refusal safety. The new closed-composition cases supply the accepted restart model. No additional implementation loop solely for comment cleanup is required.

Current outcome: the owner-selected E314549 reporting/failed-review correction is independently accepted within the above limits. Owner next decides the existing live/deployed disposition and next selected workflow. Actual live restore remains unproved, timeout cause UNKNOWN, credential currency unverified, cap unchanged, no forced rerun. No new live run, operator-script execution, deployed repair/removal, credential, engine, Git or graph operation selected or performed here. Reviewer owns FINDING/PLAN/review/evidence only; author retains product/tests/PROGRESS ownership.

Read handoff E315432/events315435/T236087 through239616 (no new discussion). Latest evidence supersedes the previous next-action restart-fixture request, preserving its historical explanation.


## 2026-09-30T14-50-19Z — settlement accepted; disposition target/commands require correction

Verdict: ACCEPT deterministic cessation-to-release evidence; CHANGES REQUESTED only for the bounded owner disposition packet. Preserve E315449 acceptance and all subsequent accepted slices. No product/test correction requested.

Owner E316504 selects tracing the existing deterministic cessation-to-release path, correcting its cause if necessary, and preparing exact supported disposition and next experiment commands. It excludes live execution, deployed repair/removal, credential changes, broad suite and Git mutation. Author owns test_stage_execution.py, PROGRESS and candidate/disposition/selections; reviewer owns FINDING/PLAN/review/evidence. This entry pins the scope omitted from the current reviewer-owned checkpoint.

Candidate316512 declared test hash matches. Independent focused class22 PASS10.755s (12 scenario cases plus 10 inherited). REVIEW-EVIDENCE-316582.json. The production restart pass calls settle_revoked_resource after reclaim held/returned. New deterministic cases execute that missing second act with the adapter custodian digest: token returned and revoked, original offered evidence preserved, no invented verdict. Without a custodian digest the resource correctly remains held because helper absence cannot be established. Offered-material writer exclusion remains after token return. This resolves the earlier question as missing fixture evidence for this scenario, not a demonstrated product defect. It does not prove release in any deployed instance or completion of its review/cleanup. Prior reclaim-held evidence remains accurate for the first act alone.

R1 — correct the disposition target identity. DISPOSITION-316512.json assigns runtime 1c3943d1fa0f... to managed-correction-309356. The retained REVIEW-TIMEOUT-314551.json instead binds it to incarnation managed-correction-314263-second, stage job-managed-correction-314263-second/review, attempt attempt-fc0b0a1a7dd59f645b3e01e3aebf357354093a3821a0d2c11f516e99ce829891 and full runtime 1c3943d1fa0f14919247690f6b0de1ebcf44a063e09d715a3cca773765c59d60. PROGRESS prior history reports the original309356 runtime gone. A disposition packet must not direct operations to a different instance. Correct current author-owned documents and append explicit supersession to PROGRESS; preserve old evidence. Enumerate original309356 separately if it retains other unresolved resources, without conflating it with the second run. Historical stopped/overdue observations are not a fresh preflight.

R2 — finish the exact supported disposition requested by owner. The deployed-disposition section currently gives prose and internal Python function names, not an operator command with exact instance/config/attempt inputs and implementation provenance. Supply the actual supported entry and commands/preconditions, including how the configured custodian digest is obtained and checked, exact target verification, evidence preservation, and expected held/returned outcomes. Bind the reviewed code/version that will execute; do not silently run an older staged implementation or prescribe direct store writes. If no supported bounded operator entry exists, record that exact operational gap and proposed next step instead of calling the prose executable. No live operation or deployed repair is authorized to validate this packet. A safe inspect/prepare-only validation is sufficient. This is completion of existing scope, not a new live-selection gate.

Next-experiment commands with fresh identity316512 are prepared but not selected or executed. Keep their declared unknown timeout cause/credential currency and lack of live restore; observability is an author recommendation, not a newly imposed prerequisite. Do not force a correction round when a reviewer accepts. Preserve earlier run evidence. The run packet cannot imply that returning a resource creates an accepted Job or completed cleanup.

Verification scope: author reports847 PASS204.7s across three whole modules despite owner asking focused verification and excluding broad suite. No need to repeat those modules for the documentation correction. This review ran only the focused class. Preserve the separate hardening baseline failure. No live/deployed/engine/credential/operator-script/Git/graph action performed by reviewer.

Return directly to baton.impl for R1/R2 only, then independent review. Read owner E316504, handoff E316573/events316582, T236087 through239616 with no new discussion.


## 2026-09-30T14-56-02Z — full serve is not bounded disposition

Verdict: R1 identity correction ACCEPTED. R2 remains documentation-only changes requested. Preserve all product/test acceptance including the independent22 PASS10.755s settlement evidence; no tests repeated and no product changes requested. Candidate316599 and disposition hashes recorded in REVIEW-EVIDENCE-316625.json.

R1: current packet now correctly binds retained reviewer runtime1c3943... to managed-correction-314263-second, identifies accidental314263 separately, and excludes original309356 from the outstanding-runtime list. PROGRESS explicitly supersedes the misattribution. Author reports fresh read-only engine inspection; reviewer did not repeat it. Historical/current token status is not established merely from elapsed time or an outcome document.

R2: the proposed persistent serve command is NOT a bounded disposition-only operation. tools.job_manager._serve constructs the full operations factory. manager.serve first calls reconcile, then every tick calls ordinary sweep BEFORE reclaim. Those operations can perform normal Job actions; the command is not restricted by the listed attempt_id and bypasses the selected experiment supervisor/invocation limits. It cannot be presented as a narrowly safe release of one retained resource without proving and selecting those extra effects. Do not execute it to establish that proof.

The instruction to stop with Ctrl-C once the pass has reported is also incorrect: manager.serve returns only the LAST report after should_continue becomes false; _serve emits it after serve returns. Its initialization diagnostic is not a reclaim report. Waiting for the report before interrupting leaves the persistent loop running. serve --once does not compose reclaim, as the author correctly notes, so it is not the bounded alternative.

The claimed runnable-today exact command remains a template containing unresolved <staged> and <A CUSTODIAN IMAGE DIGEST>. No source digest or exact staged provenance binds execution; old packets may import older code. The missing custodian configuration is a real recorded limitation, but choosing a digest alone does not solve command scope, provenance or stopping. With a digest, returned is a conditional successful outcome, not a guarantee if other runtime/helper evidence remains unknown.

Next author action, R2 only: withdraw the runnable disposition claim and explicitly record the additional operational gap: there is no demonstrated bounded, target-specific supported operator entry for this release; current serve also resumes normal Job execution and does not report each pass. Preserve the serve template only as an unselected broader alternative with those effects and missing operands stated. State the concrete owner decision/next proposed step to provide a bounded entry or separately select broader execution, without implementing new product scope. Alternatively supply an already-supported bounded entry if source evidence establishes one. Do not patch serve or build a new operator helper on this documentation assignment. Bind actual provenance before any future executable recommendation. No live run, deployed repair/removal, credentials, engine mutation or raw store workaround.

This is a documentation correction within E316504 and review316582, not reopening deterministic settlement. Next experiment remains proposed, timeout UNKNOWN, currency unverified, live restore unproved, no forced rerun. Read E316622/events316625/T236087239616. Reviewer owns FINDING/PLAN/review/evidence; author owns disposition/candidate/PROGRESS. Return implementation for this finite correction then review/owner.


## 2026-09-30T15-00-41Z — disposition gap report accepted for owner

Verdict: ACCEPT the documentation correction as an honest operational-gap report; return to owner. This is not approval to execute serve, cleanup, a new live experiment or new product work. R1 identity and R2 withdrawal are complete. Preserve E315449, deterministic settlement22 PASS10.755s and every previously accepted slice. No tests repeated for this documentation-only change. Candidate/disposition hashes: REVIEW-EVIDENCE-316662.json.

The current DISPOSITION-316512.json withdraws the runnable-today and stop-after-report claims. It identifies no demonstrated bounded target-specific operator entry for reclaim plus settlement, records the missing configured custodian digest, and describes serve only as an unselected broader alternative. The corrected retained targets are314263-second/review and314263/implementation; original309356 remains distinct. The proposed next experiment remains unselected. This satisfies the permitted alternative in review316625: state the exact operational gap rather than invent an executable disposition.

Two explicit qualifications supersede overstatements in current author prose without requiring another implementation loop. First, not every reclaim refusal stops serve: the lean tools.job_manager._reclaiming catches per-attempt ContractRefusal and ordinary faults, appends refused results, and continues. An uncaught failure from the supplied reclaim callable can propagate through manager.serve; its generic comment is not the behavior of every configured adapter. Second, retaining resources is not literally zero risk/cost, nor proof of completed cleanup or of current deployed token revocation. It leaves outstanding state and storage retained. The latest engine observations are author-reported historical reads, not a fresh reviewer preflight. A configured digest alone never guarantees return when runtime/helper cessation remains unknown.

Concrete owner choice now: retain both resources and their evidence without mutation; separately select and bound broader serving only after execution provenance, configuration, extra Job effects and stopping are resolved; or commission a bounded operator entry with target checks and observable outcomes. The third option is decision support, not an agent implementation assignment. No graph or new Work was created. Existing W236087 owns this operational finding pending disposition.

Accepted fixture evidence establishes the supported internal cessation-to-release sequence, immutable offered material and writer exclusion. It does not establish an independently usable release command for these deployments. Context reuse still lacks live restore evidence; timeout cause UNKNOWN, credential currency unverified, cap unchanged. No forced rerun or invented verdict. Owner next selects disposition and next workflow; no remaining routine correction in this documentation slice.

Reviewer owns FINDING/PLAN/review/evidence; author retains PROGRESS/candidate/disposition. Read E316660/events316662/T236087239616 (no new discussion). No product/test edits, live/deployed reads or writes, engine actions, credentials, Git or graph mutation in this review.


## 2026-09-30T15-10-14Z — owner retention and fresh experiment instructions reviewed

Verdict: ACCEPT prepared instructions with the self-contained status supplement below. Return to owner for execution selection. Owner E316685 selected retention and preparation ONLY; this review neither executes nor authorizes the live experiment. Prior deterministic settlement and disposition-gap acceptance remain intact.

Candidate316689, experiment, operator, selections and helper hashes are bound in REVIEW-EVIDENCE-316727.json. Both helper digests match the experiment. The fresh instance, packet and staging paths are absent at review. Independent two new instruction tests PASS (reported0.000s); real Python status identity resolver PASS against a temporary JSON fixture. No deployment or provider was invoked, no live store opened. Author237-case and stub argv evidence remains reported, not independently rerun. Product22-case settlement proof stands unrepeated.

Preparation/execution/outcome argv use fresh316689 identities and existing machinery. Bootstrap legitimately mints the authority UUID later; its read-only resolver and bind-generated commands resolve that operand rather than inventing an identity. Caps remain900 total/60 reserve/180 provider/180 verification and two implementation/two review invocations. No correction verdict is forced; accepted-without-correction is not restore proof. Credential currency remains unverified; recorded image/runtime provenance is historical or author-verified, with packet checks required before serving. Source/helper drift must refuse rather than silently change this reviewed experiment.

Instruction clarification: OPERATOR section4 says another terminal but relies on ROOT and IMPORT exported only in section2's terminal. Shell exports do not cross to a separately opened terminal. The following reviewer-owned supplement supersedes that section's implicit environment dependency. It is the same read-only status operation, with explicit paths; it does not repeat preparation. Use after bootstrap/bind, and run in Bash as the preparation already requires pipefail.

```bash
set -e
REVIEW_STATUS_AUTHORITY=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['authority_uuid'])" /home/sl/baton-instances/managed-correction-316689/bootstrap.json)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-staging/managed-correction-316689-source/manager-source/src:/home/sl/baton-staging/managed-correction-316689-source/manager-source python3 -m tools.job_manager --store /home/sl/baton-instances/managed-correction-316689/db/jobs.sqlite3 --authority-uuid "$REVIEW_STATUS_AUTHORITY" --incarnation managed-correction-316689 status --control /home/sl/baton-instances/managed-correction-316689/db/control.sqlite3
```

For outcome reading from a separate terminal, the fully resolved command is already EXPERIMENT-316689.json OUTCOME.step.command (absolute path); OPERATOR section6 assumes the serving terminal's ROOT. Do not rerun setup merely to obtain environment variables. These command clarifications are reviewer-owned documentation, not product changes or authority to execute now.

Owner retention ruling is now pinned: retain all earlier deployed resources/evidence without mutation; missing bounded release entry and custodian configuration stay recorded, with no expansion of implementation. The proposed next experiment tests actual managed review/correction/resume using a real provider, a question deterministic replay cannot establish. Timeout cause UNKNOWN; another timeout remains possible. Observability is a recommendation rather than a new gate. Retention has storage/outstanding-state cost and proves neither cleanup nor deployed revocation. No cleanup, credentials, engine, Git or graph act performed/selected.

Next owner: select or decline execution of the reviewed fresh316689 sequence plus this status supplement; no routine implementation correction remains. Review does not establish live restore or successful experiment. Read E316685/E316724/events316727/T236087239616, no new discussion. Reviewer owns this review/FINDING/PLAN/evidence; author documents and product remain untouched.


## 2026-09-30 review316831 — operational finding: status uses writable opener

Observed: exact generated status argv against completed316689 reproduces sqlite3.OperationalError at JobStore.open -> _objects. File and directory exist (644/775, owner sl). Source tools.job_manager._job_store uses JobStore.open (sqlite3.connect, may initialize/adopt/request WAL), despite status being described as read-only. Thus projection-only does not imply filesystem-read-only. Root cause of owner occurrence remains unconfirmed without its environment; reviewer environment restricts deployed writes. No escalation, chmod or raw SQL workaround selected. For independent retained-evidence inspection only, proposed stopgap is stable copies of completed run DB files to reviewer temporary storage followed by the supported status CLI there; record copy provenance and do not mistake it for fixing deployed status. No raw coordination-store reads.


## 2026-09-30T15-26-48Z — actual managed restoration independently accepted

Verdict: ACCEPT actual provider-context restoration and independently reviewed correction for managed-correction-316689, within the candidate one-open/one-restore experiment. This supersedes the prior statement that actual live restore is unproved for this selected profile/run. It does not certify general production reuse, integrate the proposal, or close all v12 obligations. Return to owner per E316829.

Independent retained-evidence verification is in REVIEW-EVIDENCE-316831.json and STATUS-COPY-316831.json. All16 listed file lengths/digests across four sealed manifests verify. Generated status against the completed deployment reproduces the owner-reported OperationalError. After logging the operational finding, supported status CLI over byte-verified stable copies (no WAL sidecars present, source hashes unchanged during copy) independently reports both stages completed, one correction, separate implementation/review principals and no deferrals. This is a recorded inspection stopgap, not a deployed status fix or fresh live observation from the projection. Temporary copies remain at /tmp/baton-review316831 for operator disposition; no raw SQL used.

Actual restoration: context50485e... uses the same conversation914b0069-2ca8-511c-aaee-ff1f615dfbbf in distinct implementation attempts455912... and41503a..., with distinct runtimes. Receipts report open then restore, status0/complete/terminal success, same observed conversation, matching invocation bindings. Saved generation1 transcript237254 bytes hashes correctly and is an exact prefix of generation2 transcript300822 bytes;30 appended rows contain the correction response and in-place edits. Restored use feedback equals the first review findings exactly. Together the actual invocation receipts, saved transcript continuity and provider correction activity establish restoration beyond a requested session ID or copied log alone. Outcome generation0/1 describes uses; saved snapshots are1/2, not a discrepancy.

Attribution and proposal: first independent reviewer3f2ffc... assigned to baton.review generation2 returned changes-requested for base346a809bf0e4c47e52d881bd46d6d62a611c9816/head e0791399e7ba501357b58e57b0aac869b0a11abc/tree70f5f25c923a89ac8a0b68407ff05b74874bbc67. Findings identify the concrete candidate-vs-production qualification error and two wording errors. Corrected implementation41503a... assigned to baton.impl generation3 produced head83be025c90842e33e7bea22dd543311b0d8623d8/tree151824e9e26a9c83c97e72edaeac0398bfc88308. Second reviewer5eb882... generation4 accepted that exact base/head/tree. Read-only git history confirms corrected head directly descends from the first head; only docs/v12-context-correction.md changed,23 additions/8 deletions. Final proposal artifact digest sha256:1d01cf5f7aa88339d26ed0752d623f65ddeac28d2a8a64f2201d512efea6181b matches the retained status locator/manifests; individual proposal files checked. No proposal imported or canonical Git changed.

Runtime cessation: independent docker inspect of all four exact recorded runtime IDs returns no such object. Outcome records destroyed/absent/cleanup-retained for each, no holds or uncertainty, natural completion at15:21:28.418Z, serving540.938s within840 serving plus60 reserve, two implementation and two review admissions. This is specific to this Job; earlier retained runs are untouched. It is not deletion of retained context or proposal evidence.

Acceptance limits/new operational findings:

1. Status diagnostic: exact paths and UUID reproduce sqlite3.OperationalError: unable to open database file at JobStore.open -> _objects. Files exist and normal owner modes are644/775. tools.job_manager._job_store opens via writable sqlite connection and requests WAL; it does not use the available open_readonly path. Thus advertised projection-only behavior does not establish filesystem-read-only access. Copied stores work, so no evidence here of corrupt/missing completed-run data. The exact cause in the owner's environment remains unconfirmed; reviewer restrictions are consistent with the writable-opener failure. Record this as a concrete diagnostic/read-only usability defect, not failed restore. Fixing/rerunning is not selected in this review.
2. The final reviewer allocation remains reserved (released_at null) in canonical copied status although the runtime is destroyed and cleanup retained. Therefore do NOT broaden outcome no-holds to all scheduler/resource allocations released. This is an observed residual accounting/release question requiring bounded follow-up; it did not erase the accepted verdict/restoration evidence. Do not run another sweep to alter it under this read-only assignment.
3. Receipt observed_model is null. Configured model opus/CLI2.1.247 and successful real conversation restore are evidenced; independent provider model attribution, cache savings, speedup, general production certification, arbitrary repeated generations and parallel context reuse are not established by this one run. Earlier timeout root cause remains UNKNOWN, not solved by this success. Credentials worked for this run, not a claim of future currency.

Remaining v12 work: owner decides candidate-profile qualification/production acceptance using this retained proof, selected parallel workflow with reuse still needs its own aggregate evidence (not inferred from one serial Job), and selected human-plus-agent integration/delivery of the accepted proposal remains unperformed. Preserve existing Work identities and earlier parallel/fresh-attempt proofs; no graph changes or new adoption gate imposed. Keep status read-only opener and final allocation accounting questions pinned here for bounded classification/assignment. Earlier retained resources and missing bounded disposition entry stay under owner E316685 retention, not silently cleaned or reopened. No live rerun required to establish this accepted slice.

Read E316829/events316831/T236087239616. Reviewer owns FINDING/PLAN/review/evidence only; no product/test edits, live provider execution, deployed repair/cleanup, integration, credential or Git mutation. Deployment read-only artifacts and docker inspection only; supported status succeeded solely on declared temporary copies. Return baton.decide with honest limits and actionable diagnostics.


## 2026-09-30T15-35-36Z — bounded follow-ups created; closure recommended

Owner E316900 accepts E316862 within its limits and selects two bounded follow-up Works. Completed this assignment without rerunning or reopening the live proof.

Created and canonically verified:
- W316915, baton:work/records/2026/09/finding-v12-status-readonly-opener, confirmed-defect, routed baton.impl. Scope: genuine read-only Job/Control status openers, authority/schema validation, no initialization/migration/write side effects, preserved submit/serve semantics; focused read-only filesystem/WAL and missing/wrong-store acceptance.
- W316918, baton:work/records/2026/09/finding-v12-final-review-allocation-release, suspected-defect pending deterministic causal reproduction, routed baton.impl. Scope: final review allocation release after proven cessation/cleanup at normal terminal stop, subsequent capacity, idempotence/replay, negatives retaining running/unknown holds. No workspace-token redesign.

Both own permanent top-level dossiers with FINDING/PLAN and exact scope, evidence references, ownership and independent-review return. Implementer owns product/tests/PROGRESS after claim, reviewer FINDING/PLAN/reviews. Shared paths require coordination. Available source search did not find job_manager/allocations.py or pool modules; no such file is assumed. Relevant allocation owner is scheduler.py (release), with manager.py and stage_execution composition to revalidate.

Graph decision: no containment or blocking edge installed. These separately scheduled follow-ups may outlive W236087, and neither depends on the other. Blocking the already accepted context-restore proof on them would silently reopen acceptance. One serial implementation endpoint handles ordering and explicit file ownership; a dependency is not needed just to serialize a shared editor. They are cross-referenced in canonical bodies and dossiers. create follow-up-of requires a CLOSED origin, so no false lifecycle relation was manufactured while W236087 is open. No graph edge requiring removal at closure.

Closure recommendation: CLOSE W236087 satisfying, limited to the independently accepted managed candidate-profile correction/resume proof and its recorded deterministic execution/recovery scope. Owner E316900 accepts that result. The successful run restored the actual provider conversation in a fresh attempt, applied independently attributed corrections, obtained acceptance for the corrected checkpoint, and ceased all four named runtimes. Do not recast the result as general production qualification, parallel-reuse readiness, integrated delivery or zero residual allocation debt. The two explicit Works now own status and allocation debt; retained prior runs and missing bounded disposition entry remain recorded under the owner retention decision, with no cleanup selection.

Qualification disposition: preserve the exact candidate-profile/run receipt/transcript/proposal evidence and reviewer acceptance as qualification input. No production certification record or deployed profile changed. observed_model null, no cache/performance claims, no unbounded-generation or parallel reuse proof. Those are honest limits, not new blanket hardening prerequisites for this Work's closure. Broader qualification/workflow selection belongs to existing delivery planning and any explicitly selected later scope.

Next executable delivery step for owner selection: prepare a digest-bound integration handoff for the accepted retained proposal (do not rerun the model). Source is the exact final custody proposal locator in REVIEW-EVIDENCE-316831.json / STATUS-COPY-316831.json, head83be025c90842e33e7bea22dd543311b0d8623d8, tree151824e9e26a9c83c97e72edaeac0398bfc88308, base346a809bf0e4c47e52d881bd46d6d62a611c9816, artifact sha256:1d01cf5f7aa88339d26ed0752d623f65ddeac28d2a8a64f2201d512efea6181b, path docs/v12-context-correction.md. Human-plus-agent integration remains default: baton.merge first checks base/target/path drift and independent provenance, refuses divergence, and imports only if separately assigned/authorized; no automatic integration or Git act follows this recommendation. The current source has advanced relative to an old fixture base, so clean applicability is not assumed. A preflight refusal calls for a bounded disposition, not forced replay or cherry-pick.

Current immediate implementation queue is W316915 and W316918; each returns baton.bug then owner. W236087 returns baton.decide for closure and delivery selection. No live run, deployed cleanup, integration, credential, product/test or Git mutation occurred. Read E316900/events316903/T236087239616. Prior acceptance/evidence remains append-only.
