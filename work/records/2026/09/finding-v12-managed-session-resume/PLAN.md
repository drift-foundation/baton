# Current action — independent review 250440

The retained-input assessment is accepted by
[review-2026-09-23T19-33-41Z.md](review-2026-09-23T19-33-41Z.md).
Return to baton.decide for selection of an eligible correction subject or a
new neutral implementation/review pair. The existing accepted subject remains
untouched. A successful production restore is still unproved; the concrete
packet, exact commands, deterministic execution and cleanup evidence remain
required after subject selection. No live execution is selected by this review.
Engineering a particular review verdict is not a selected requirement.

The assessment below remains supporting evidence; this current-action entry
supersedes its suggestion that only composing a live packet remains.

# Retained assessment — after claim 250376

Owner reroute 250274 routed the remaining resume proof to implementation with
prerequisites W239528 and W239533 closed satisfying, and asked for the real
continuation input and any additional selection it needs. This claim read it
rather than assuming it.

## What the retained subject actually leaves

[CONTINUATION-250376.md](CONTINUATION-250376.md) is the finding;
`RESUME-STATE-250376.json` is the read-only receipt and `test_resume_state.py`
asserts it in 10 checks.

  * **The context to resume EXISTS and is ready.** The producer attempt's
    provider context is finalized at generation 0 with status `ready` — the
    exact predecessor a generation-1 restore requires. It survived the
    runtime's destruction and the `retained` cleanup.
  * **The verdict that would open a correction DOES NOT EXIST.** The line is
    `accepted`, its accepted verdict is its integration eligibility, no
    correction operation exists for the frozen checkpoint, and
    `correction_feedback_of` refuses by name.
  * **The subject cannot be reopened.** `attach_review` admits `review-ready`
    only; `changes-requested` is the sole disposition producing
    `correction-ready`; and the restore reader holds both the verdict and the
    retained report to `changes-requested`.
  * **The acceptance was honest.** The executed review criteria say every one
    of the three verdicts is valid and that none is better for the reviewer.

## The pinned product seam is retired

PLAN pinned an `v12/worker/claude_agent.py` change as unavoidable for
stage-specific requirements. The owner's split retires it: W239533's review Job
carried its own task document with review criteria the implementation Job never
saw. It was the COMBINED-Job shape that needed a seam. Asserted against the
executed criteria. No product byte was changed and none is proposed.

## THE SELECTION THIS JOB NEEDS — for the owner

A new subject whose review honestly asks for a correction, because no packet
can guarantee its own precondition. Recommended: a new implementation + review
pair under neutral criteria, with a packet that treats `accepted` as a valid
end state and records that no correction was required rather than manufacturing
one. It also needs a fresh run identity — the old grant is consumed — and a
bounded one-restore correction Job. The three options and their costs are in
CONTINUATION-250376.md.

## REMAINING

The owner's selection. After it: compose the bounded correction packet, and the
live question this Job exists to ask — whether the production CLI restores a
real conversation, which is the one seam the deterministic evidence stands in
for.

## Ownership

Reviewer-owned and immutable: every `review-*.md`, `review-*.json`/`.log` and
`review-checks-*`. baton.claude owns the rest of this dossier.

---

# Current action — bounded resume continuation, owner 2026-09-23

W239528 and W239533 are closed satisfying. This supersedes waiting/routing
instructions below. Owner selected continuation; implementation routed250274.

1. Revalidate actual retained context and review provenance. Accepted verdict
   is not changes-requested: establish meaningful continuation input honestly.
2. Prepare separate restored-context execution on supported disposable
   coordination with deterministic providers. Prove actual restoration,
   continued work, attribution, stopped execution and cleanup.
3. Deliver independently reviewable digest-bound packet, exact commands and
   specific live-provider question. Identify any genuine missing selection.

Own this dossier initially; coordinate product paths before editing. Preserve
accepted/failed artifacts and consumed grants. No live run, deployed mutation,
destructive recovery, automatic integration or combined mega Job is selected.
Routine corrections go directly to impl; accepted preparation or genuine
owner decisions go to decide. W247941 remains independent of reuse completion.

---

# Current action — remaining resume proof after separate prerequisites

Owner239562 and OWNER-SPLIT-20260922.md select separate Jobs and supersede
continuing the combined baseline/review/resume Job or its proposed R2 product
seam. W236087 retains ONLY restored-context correction after independently
accepted W239528 (implementation through proposal/stop/positive cleanup) and
W239533 (independent retained-proposal review through verdict/stop/positive
cleanup). Bind actual open context and real review provenance; never fabricate
restore inputs or weaken acceptance.

Return baton.decide with review-2026-09-22T14-56-01Z.md and preserved hashes in
review-evidence-239589.json. After claim release, owner records W236087 blocked
by W239533; W239533 is already blocked by W239528. Route only W239528 first.
Current partial corrections and diagnosis are retained for reuse and independent
validation after explicit file ownership handoff, not accepted for a live run
by this preservation turn. Preserve failed-run evidence, outstanding cleanup and
the consumed grant. No live execution, destructive recovery, enabling or closure.

# Historical action -- claim 239485; R2 seam pinned for the next claim

## Active ownership -- claim 239485, baton.claude

Owner reroute 239483. Dossier files only: `supervisor.py`,
`test_supervisor.py`, `test_generated_packet.py`, `LIVE-RUN-239365.md`,
`OPERATOR-239485.md`, `SELECTIONS-239485.json`, `PACKET-INPUTS-239485.json`, a
superseded-header line on `OPERATOR-239365.md`, and
`verification-20/21.json/.log`. No file under `v12/` was edited; the ten
candidate paths are unchanged. 255 focused checks pass, 37.435480670s.

R1, R3 and R4 are complete; details in the claim-239485 PROGRESS entry.

## PINNED PRODUCT SEAM -- required for R2, and NOT begun

Recording it here is the pin; no product byte has been changed under it.

    v12/worker/claude_agent.py
        the task document gains an OPTIONAL review-instructions member, and
        `_review_prompt` presents THAT as the requirements to assess when it is
        present, falling back to `instructions` when it is absent. `_prompt`
        keeps reading `instructions` alone, so the implementation role never
        sees the review's criteria.
    v12/python/tools/packet_bindings-side composition
        emits the two strings: the initial requirement for the implementer and
        the acceptance criteria for the reviewer.

Why a product change is unavoidable: one Job carries ONE digest-sealed input
manifest; `single_worker._held` compares each worker's `task_document` bytes
against the manifest's `human_contract` digest, so both workers necessarily
read the same document, and `_review_prompt` today frames that same string as
the reviewer's requirements. There is no existing seam that delivers different
requirements to the two roles.

Until it lands, the packet cannot guarantee the selected
open -> changes-requested -> restore sequence without scripting a verdict, and
the supervisor's sequence requirement is NOT weakened to make a first
acceptance count as success.

Also outstanding and owner-side: the faulted attempt's recovery (end the
assignment, then authorize cleanup so the runtime can be positively excluded),
and a new run identity if another run is selected -- the grant is spent.

# Historical action — complete the live-failure correction under239355

Review review-2026-09-22T14-38-24Z.md requests changes. Distinguish positive
no-allocation reads from failed reads before skipping cancellation/cleanup;
align reported turn counts with that classification. Preserve the selected
role-specific correction workload rather than asking the first implementer for
the final target. Complete the agent-fault and missing-cleanup diagnosis without
live cleanup; generic agent fault is not a proved causal explanation. Explicitly
supersede the stale replay-safe/unconsumed paragraph in OPERATOR-239365, since
the same document now reports a consumed grant. Return baton.decide recommending
existing-scope continuation and independent review. No live rerun/enabling/closure.

# Historical action -- claim 239365 complete; independent review next

## Active ownership -- claim 239365, baton.claude

Owner reroute 239355. Dossier files only: `supervisor.py`,
`packet_bindings.py`, `test_supervisor.py`, `test_packet_bindings.py`,
`test_generated_packet.py`, `LIVE-RUN-239365.md`, `live-239365/`,
`OPERATOR-239365.md`, `SELECTIONS-239365.json`, `PACKET-INPUTS-239365.json`,
a superseded-header line on `OPERATOR-239174.md`, and
`verification-18/19.json/.log`. No file under `v12/` was edited; the ten
candidate paths are unchanged.

The live run's two defects are corrected and regressed: the task document
states requirements only so the implementation role cannot execute a review
script, and attempts are classified by what this run actually started so a
never-allocated episode is named rather than charged a cleanup record that
could not exist. 252 focused checks pass, 39.574366914s.

Outstanding and NOT acted on: the quiescent implementation runtime with cleanup
pending, and the consumed qualification grant. Both are recorded for the owner
in `OPERATOR-239365.md` and `LIVE-RUN-239365.md`.

# Historical action — code-boundary correction accepted; owner state confirmation

Read review-2026-09-22T14-05-58Z.md and review-evidence-239228.json. Actual copied
source imports through production composition pass deterministic correction and
timeout checks. Current239174 program/packet hashes are accepted. Reviewer
ControlStore.open_readonly assessment refused with OperationalError; it did not
establish current grant/preparation state. Preserve author-attributed assessment
and the failed launched packet. Owner confirms current state and unchanged
preparation operands through supported readers before selecting a relaunch and
regenerating the concrete packet. Do not repeat already completed selections or
infer unconditional replay safety. No further product correction requested;
return baton.decide. No live rerun/enabling/closure by review.

# Historical action -- claim 239174 complete; independent review next

## Active ownership -- claim 239174, baton.claude

Owner pass 239172. Dossier files only: `supervisor.py`, `packet_bindings.py`,
`test_supervisor.py`, `test_packet_bindings.py`, `test_generated_packet.py`,
`OPERATOR-239174.md`, `SELECTIONS-239174.json`, `PACKET-INPUTS-239174.json`,
superseded-header lines on the 238827 records, and
`verification-16/17.json/.log`. No file under `v12/` was edited; the ten
candidate paths are unchanged.

The code boundary is bound in the packet and read by both preparation and
runtime; the relocated-layout inference and the owner's exact refusal are
covered deterministically. The prepared instance was assessed read-only: the
qualification grant is unconsumed, so steps 5 and 6 are safe to re-run. 247
focused checks pass, 37.612951821s.

Remaining is owner-side: step 5a, the six selections, and the exact
live-command selection.

# Historical action — correct relocated-source composition boundary

Owner launch on 2026-09-22 failed during composition because the runtime inferred
`/home/sl/baton-runs` as its checkout. See the dated relocated-source finding in
FINDING.md. Preserve prepared state and reviewed bytes. Next bounded correction:
use a consistent, bound code exclusion boundary in preparation and runtime;
exercise the actual copied-source layout deterministically, independently review
updated provenance, and assess existing preparation before selecting another
live launch. No live rerun has been performed by baton.prompt.

# Historical action — preparation accepted; owner inputs and execution selection

Review review-2026-09-22T13-07-41Z.md accepts the current bounded packet
preparation, including the formerly hidden workspace prerequisite. Prior R2a/R2b
and product acceptance stand. PACKET-INPUTS-238827.json and exact program hashes
are bound by review-evidence-238861.json. Historical packet loss is explicitly
recorded in LOST-ARTIFACTS-238827.md; do not invent missing bytes. Leave future
digest-bound predecessors unchanged and put supersession in successor records.

Return baton.decide for fixture commit/base, operator5a real isolated-instance
setup, six final selections and exact live-command selection. No new preparation
loop for unchanged accepted bytes. No live execution/enabling/closure follows
this review. Author's prospective execution packet remains to be concretely
generated from the owner's inputs under the accepted program.

# Historical action -- claim 238827 complete; independent review next

## Active ownership -- claim 238827, baton.claude

Continues the 238696 authority under owner reroute 238822. Dossier files only
this claim: `supervisor.py`, `test_generated_packet.py`,
`LOST-ARTIFACTS-238827.md`, `OPERATOR-238827.md`, `SELECTIONS-238827.json`,
`PACKET-INPUTS-238827.json`, a superseded-header line added to
`OPERATOR-238700.md`, and `verification-14/15.json/.log`. No file under `v12/`
was edited; the ten candidate paths are unchanged.

R4's workspace prerequisite is now a supervisor act derived from the validated
deployment, and the fixture's hidden setup is gone. The deleted historical
packet revisions are recorded as an unrecoverable loss with their
reviewer-retained digests, and superseded records are kept from now on. 239
focused checks pass, 37.582261871s.

Remaining work is owner-side only: the fixture commit, step 5a, and the six
selections in `SELECTIONS-238827.json`.

# Historical action — complete the workspace preparation prerequisite

Read review-2026-09-22T12-55-41Z.md. R2a shutdown correction and R2b are accepted.
The main-entrypoint tests pass only after their prepared_stores helper records
workspace storage; the operator sequence omits this prerequisite and fresh main
refuses before composition. Make that preparation explicit through the supported
API, preserving root-conflict and exclusion checks, and verify the same operator
sequence deterministically. Refresh provenance. Existing owner238696 authority
applies; no new preparation permission loop. Also resolve the recorded absence
of historical238462 operator/packet/selections artifacts without inventing bytes.
Return baton.decide. No live/enabling/closure; accepted product bytes preserved.

# Historical action -- claim 238700 complete; independent review next

## Active ownership -- claim 238700, baton.claude

Continues the 238460 authority under owner reroute 238696. This claim edits the
four product/test paths already pinned and owned under claim 238462 plus the
dossier's own files; `stage_execution.py` is unchanged and the six originally
accepted candidate paths stay read-only and byte-identical.

R2a interruption safety, the R4 `main` entrypoint proof and the operator
corrections are complete; 237 focused checks pass, 36.544513340s. Details are in
the claim-238700 PROGRESS entry. Remaining work is owner-side only: the fixture
commit, step 5a, and the six selections in `SELECTIONS-238700.json`.

# Historical action — complete shutdown interruption safety and command proof

Review review-2026-09-22T12-31-42Z.md accepts the added product cancellation
seam and deterministic generated-deployment correction evidence. R2b stays
accepted. R2a remains open: interruption at cancellation's runtime read escapes
with no stop or retained outcome. R4 remains open: generated tests bypass main,
and their synthetic source binding refuses at that actual entrypoint. Complete
shutdown-wide interruption handling and one fresh deterministic generated-packet
command run with normal source checks and composition; reconcile stale operator
selection/source references. Existing owner238460 authority applies, without a
new preparation approval loop. Return baton.decide with this independent review.
No live/enabling/closure. Review evidence is reviewer-owned and append-only.

# Historical action — finish authorized R2a and generated-packet proof

Read review-2026-09-22T11-53-11Z.md. R2b accepted; R2a cancellation and executable
R4 remain open. Owner238308 already selected the pinned seam: next implementer
claims exact source/test ownership, completes attempt-owned cancel/fence/stop and
positive exclusion, fixes unknown-state and interruption gaps, and amends candidate
provenance/source artifacts. No extra permission gate follows merely from the
required product-path pin. Verify GENERATED packet through actual entrypoint and
fresh deterministic test Authority; no real deployment mutation needed. Correct
stale operator selection/preflight examples. Return baton.decide recommending
continued bounded implementation, then one complete independent review.
No live/enabling/closure. Original accepted implementation remains preserved.

## Active ownership -- claim 238462, baton.claude

Owner reroute 238460 continues the already-authorized scope of 238308, and
review 2026-09-22T11:53:11Z states plainly that no additional permission gate
applies and names the canonical paths. Ownership is recorded HERE, before the
first product byte is changed.

**Product paths owned by claim 238462**, with their pre-edit bytes:

    v12/python/tools/single_worker.py
        80370d122ff4a2c712f98d26f7bb110b93de51a62345ce29a3cd803d935109e9
    v12/python/tools/stage_execution.py
        0d3a2a495097424006fddd60278b7f935a6f81fbf9611d5c99cd1d94e2eeb167

**Test paths owned by claim 238462**, with their pre-edit bytes:

    v12/python/tests/tools/test_single_worker.py
        2e112440b03fc0330386945c3c41b2b220c199e2d2574061b2b1931d82b873dc
    v12/python/tests/tools/test_stage_execution.py
        2505675a5ce8d3ac1b68354efa080652192799209bff59c85d6c6260f03d5e4e

Dossier files owned: `supervisor.py`, `test_supervisor.py`,
`packet_bindings.py`, `test_packet_bindings.py`, `test_generated_packet.py`,
`OPERATOR-238462.md`, `SELECTIONS-238462.json`, `PACKET-INPUTS-238462.json`,
the amended `CANDIDATE.json`, `MANAGER-SOURCE-238462.json` and this claim's
verification receipts and PROGRESS entry.

The six originally accepted candidate paths stay READ-ONLY to this claim and
are re-verified byte-identical; the amended `CANDIDATE.json` adds the two
product paths beside them rather than reopening them.

### What the seam is

    single_worker._SingleWorker.cancel_attempt(attempt_id, reason)
        derive this attempt's ordinary allocated roots, build the adapter the
        identify/observe path already builds (`_adapter(roots, None, None,
        None)` -- `OciAdapter.stop` needs only a runtime id and an operation
        id), supply a cooperative agent that REPORTS that this deployment's
        file-exchange worker has no cooperative cancellation channel instead of
        pretending one, and call the accepted
        `attempts.request_cancellation(control, port, agent, adapter, ...)`,
        which fences the exact participant and generation at the Authority
        BEFORE ordering quiescence.
    single_worker._Operations.cancel_attempt
        delegate.
    stage_execution.StageExecution.cancel_attempt
        route an attempt to the worker that owns it, through the recorded
        allocation rather than by guessing a role.

`request_cancellation`'s return does NOT prove absence. The supervisor keeps
driving the manager-owned ending path afterwards and still requires a positive
committed `runtime.destroy` before it calls anything settled.

# Historical action — partial R2b/R4 handoff; R2a seam pinned

## Active ownership — claim 238310, baton.claude

Claim 238310 owns dossier files only: `supervisor.py`, `test_supervisor.py`,
`packet_bindings.py`, `test_packet_bindings.py`, `OPERATOR-238310.md`,
`SELECTIONS-238310.json`, `PACKET-INPUTS-238310.json` and
`verification-8/9.json/.log`. **No file under `v12/` was edited**; the six
accepted candidate paths were re-verified byte-identical and the working tree
is clean apart from them and this untracked dossier. The 236529-suffixed
operator, selections and packet-inputs files are superseded by their 238310
replacements.

R2b and R4(a-d) are complete; 58 focused checks pass, 15.918496504s. Details
are in the claim-238310 PROGRESS entry.

## PINNED PRODUCT SEAM -- required for R2a, and NOT begun

Ownership must be claimed and this pinned before the first edit. Recording it
here is the pin, and no product byte has been changed under it.

    tools/single_worker.py      add `cancel_attempt(self, *, attempt_id,
                                reason)` to the composed per-worker
                                operations: derive the attempt's mounted roots
                                the way the ending already does, build the
                                adapter with `_adapter(roots, None, None,
                                None)` -- `OciAdapter.stop` needs only the
                                runtime id and an operation id -- supply a
                                cooperative agent that reports that this
                                deployment's file-exchange worker has no
                                cooperative cancellation channel rather than
                                pretending one, and call the accepted
                                `attempts.request_cancellation(control, port,
                                agent, adapter, attempt_id=..., reason=...)`.
    tools/stage_execution.py    route `cancel_attempt` to the worker that owns
                                the attempt, on `StageExecution`.

Why it is a product change and not a supervisor one: `request_cancellation`
fences the generation at the Authority BEFORE ordering quiescence, and its
port, agent and adapter are per-attempt objects only the deployment that
launched the runtime holds. A supervisor that rebuilt them from another
module's private state would be a second controller composing a security
boundary it does not own. The supervisor already calls the capability, so the
seam landing is the whole of the remaining change on the supervisor side.

Also remaining and dependent on it: driving the generated documents through the
actual entrypoint over a freshly composed instance, which additionally needs
operator step 5a -- an Authority mutation, and therefore the owner's.

Independent review of this claim's corrections next, then baton.decide on the
seam and the composition run. No live run, enabling or Work closure follows.

# Historical action -- finish shutdown and generated live-binding composition

Review review-2026-09-22T07-03-13Z.md requests changes under claim236644.
R2a: stop active runtimes on timeout/failure/interruption through supported manager
operations, then finish bounded cleanup. R2b: preserve failed canonical refresh
as a hold reason. R4: correct live networking, bind fresh-instance preparation,
real evidence and review criteria, and verify the GENERATED packet through normal
deterministic entrypoint/composition. Preserve accepted six-path product bytes;
pin any needed product seam before editing. Return baton.decide recommending
bounded Claude correction then independent review. This supersedes shutdown-
complete wording below while retaining the confirmed admission/source fixes.
No live command, enabling, closure or global fresh-attempt restriction.

# Historical action — R1–R3 correction handoff

## Active correction ownership — claim 236529, baton.claude

Owner reroute 236525 selects the bounded R1–R3 corrections and completion of the
concrete packet bindings. Claim 236529 owns only dossier files: `supervisor.py`,
`test_supervisor.py`, `packet_bindings.py`, `test_packet_bindings.py`,
`MANAGER-SOURCE-236529.json`, `PACKET-INPUTS-236529.json`,
`OPERATOR-236529.md`, `SELECTIONS-236529.json`, `verification-6/7.json/.log`
and its PROGRESS entry. **No product-path change was required**, so none was
made: the six accepted candidate paths were re-verified byte-identical and no
file under `v12/` was edited. `PACKET-INPUTS-236349.json` and
`OPERATOR-236349.md` are superseded by their 236529 replacements; reviewer-owned
files are untouched.

R1, R2 and R3 are implemented as PROGRESS records in detail: caps refused at the
admission boundary, the declared provider-turn ceiling bound into the Job and
checked as effective, the required correction sequence read back before a run is
called settled; admission closed at the operations boundary before cleanup with
every launched runtime recorded at the call and the canonical history re-read
after faults; and the manager source that is actually imported bound and proved
before a store opens. 47 focused checks pass, 13.783267718s. The reviewer's four
counterexamples no longer confirm.

The per-Job bindings are now drafted and validated rather than declined:
`packet_bindings.py` composes both worker deployments, the sealed input
manifest, the candidate context profile, the submission and `PACKET.json`, and
holds them with `stage_execution.held_configuration` before writing. It grants
nothing and runs nothing. Two owner-side items remain and are isolated by name:
the fixture repository's first commit (prohibited to this implementer) and four
participant/credential selections in `SELECTIONS-236529.json`.

Independent review of these corrections next, then baton.decide. No live run,
enabling, or Work closure follows this handoff.

# Historical action — correct supervisor before executable packet acceptance

Read review-2026-09-22T06-36-24Z.md and review-repro-236474.py/.log.
Claim236474 requests changes: R1 enforce invocation/time limits and require the
actual correction outcome; R2 stop admission before cleanup, refresh all attempts
after faults and account for every runtime; R3 execute/pin the actual manager
runtime instead of an unused frozen executable. This supersedes the supervisor
completion/stop-admission claims below, not the accepted six-path implementation.

Return baton.decide with recommendation for bounded Claude correction under
existing W236087, then independent review. Preserve artifact digests and prior
accepted candidate. Prepare concrete missing packet bindings; isolate genuine
owner choices and owner-owned fixture commit. No live command or enabling until
corrected runnable packet review and separate owner selection. W177936 stays
closed; fresh-attempt development remains permitted.

# Historical action — prepare the final managed live packet (owner selected)

Executor update: owner selects baton.impl/baton.claude because Codx credits are exhausted. Recover the failed Codx episode236296 only after host execution is stopped/accounted for, then route this existing Work to Claude. Claude continues the accepted packet-preparation scope below, preserving candidate bytes and prior evidence; Codx executor references below are superseded. Prompt cannot prove host absence from its sandbox-local process view. Independent review and later exact live selection remain separate.

Owner "lets proceed" selects the final preparation described in the latest FINDING entry. Codxpc prepares the refreshed immutable worker/isolated manager artifacts, real digests, disposable source and fresh execution bindings, credential reference, and bounded owner supervisor. Pin exact preparation/test paths before edits and preserve the reviewed six-path candidate. Build operations for these artifacts are selected; existing live services, model calls, auth operations, production enabling and Git mutations are excluded. Verify supervisor lifecycle and failure cleanup deterministically. Deliver an executable, zero-placeholder packet via baton.bug independent review, then baton.decide for separate live selection. Any host-permission obstacle must carry exact operator build commands and retained inputs; it is not an invitation to escalate from a managed turn.

## Active preparation ownership — claim 236349, baton.claude

Claim 236349 owns only NEW dossier files: `supervisor.py`, `test_supervisor.py`,
`fixture/`, `IMAGE-ARTIFACT-236349.json`, `MANAGER-ARTIFACT-236349.json`,
`PACKET-INPUTS-236349.json`, `OPERATOR-236349.md`, `verification-4/5.json/.log`
and its own PROGRESS entry. The six accepted candidate paths are READ-ONLY to
this claim and were re-verified byte-identical before and after; no source,
test or documentation file under `v12/` was edited. Build outputs live outside
the checkout at `/home/sl/baton-runs/managed-correction-236087/`.

Steps 1–3 of the packet (refreshed worker artifact, isolated manager runtime,
isolated zero-Job installation) are built with real digests. The bounded owner
supervisor is implemented and deterministically verified. Steps 4–5 (the
fixture repository's first commit, and the per-Job worker document with its
sealed `inputManifest`) are NOT done: the first is prohibited to this
implementer by the deployment's Git policy, the second is an owner selection a
managed turn may not make on the operator's behalf. Both carry exact commands
and pinned inputs in `OPERATOR-236349.md`. Nothing here is presented as a
runnable packet. Independent review next, then owner decision on those two
steps; no live run, enabling or Work closure follows this handoff.

# Historical action — implementation accepted, preparation awaiting owner

Independent review review-2026-09-22T05-58-20Z.md accepts the six-path candidate
at CANDIDATE.json SHA2563a2bf7564e24113c78120d9e451e7c3a75d98b48f08d3dcdf747585e5c5e5cae.
Review verification34/34 passed16.578126122s; exact bytes/base validated.
This supersedes pending independent implementation review below. Return to
baton.decide. Keep Work open: LIVE-CORRECTION-PROPOSAL.md still requires actual
artifact/installation/deployment/source/storage/authority bindings and a bounded
owner supervisor before a reviewed executable packet and separate exact live
selection. No live run, rollout or production enabling is approved by this review.
No standalone canary repetition or broad campaign; fresh-attempt work remains allowed.

# Historical action — bounded implementation

1. Revalidate the owner ruling in FINDING.md against current code and later decisions. Read the W177936 final review and existing production-context tests. Inspect current claims and filesystem changes before establishing exact file ownership in this plan; preserve all existing work.
2. Implement the smallest managed save/stop/restore/correction path using existing lifecycle machinery. Remove resumed-turn model-name gating from serving receipt and certification validation consistently; retain truthful optional model diagnostics and all session/status/provenance/isolation checks. Explain any compatibility or receipt-shape change before implementing it. Do not weaken unrelated initial-execution contracts by accident.
3. Exercise real affected manager/runtime behavior with deterministic fake/replay provider inputs. Cover saved-session restoration into a fresh worker, explicit review feedback, attributable revised proposal, absent/changed model labels, wrong session, unsuccessful or incomplete results, stale/mismatched state and receipts, and stop/fencing before re-execution. No broad suite or new live model call by default. Record affected test paths and measured durations; standing test authority applies.
4. Hand the candidate and focused evidence to baton.bug for independent review, then baton.decide. Include exact changed paths, candidate provenance, remaining limits, and a concrete one-shot managed live correction proposal. Reuse accepted image/provider/recall evidence when applicable. Do not introduce a repeated standalone canary or general certification redesign.
5. After separate owner selection of the reviewed live command, demonstrate review feedback returning to the saved implementer session in a fresh worker, revised result collection and independent acceptance. Clearly distinguish deterministic proof, live managed proof and any production enabling. No automatic retry or broad rollout.

Implementation route: baton.codx (baton.codxpc); independent review route: baton.bug. Candidate ownership begins only after successful claim. Expected source boundary: v12/worker/claude_agent.py and v12/python/src/baton_v12/worker_manager/provider_context.py, with context_delivery.py, oci.py and single_worker.py only where a concrete managed-path gap requires them. Focused tests belong to the affected existing manager/worker test modules; pin exact paths before changes. Actual implementer owns PROGRESS.md. No concurrent edits to another claimant's files, no Git mutations, no live service/credential operations in this implementation handoff.

## Active implementation ownership — claim236092, baton.codxpc

M236120 confirms contextual open AND restore model-independent acceptance (superseding step 2's narrower wording). Pin receipt `/3` compatibility and admission-bound filename substitution exactly as FINDING above before edits.

Owned source paths: `v12/worker/claude_agent.py`, `v12/python/src/baton_v12/worker_manager/provider_context.py`, `v12/python/src/baton_v12/worker_manager/context_delivery.py`. Owned tests: `v12/python/tests/manager/test_claude_context.py` (serving receipts, real candidate guard and composed correction/certification proof), `v12/python/tests/manager/test_provider_context.py` (closed profile grammar and state resolution). Standing test authority covers updating obsolete wrong-model expectations while retaining real failure coverage. No oci.py or single_worker.py edits needed on current evidence. Initial source tree has no tracked changes; baseline hashes are in BASELINE.json. Dossier files are also owned for implementation evidence.

Additional owned documentation: `v12/python/DEPLOYMENT.md`, context-profile/receipt migration and current qualification limits. New UUID substitution is opt-in profile `/2`; historical `/1` remains literal.

## Current status — prepared for independent review

Steps 1–3 implemented and verified. Exact candidate is CANDIDATE.json plus candidate.diff; measured results in verification-1/2/3 and PROGRESS. Next baton.bug independently reviews these bytes, then baton.decide selects promotion/preparation. LIVE-CORRECTION-PROPOSAL.md pins one managed correction and its evidence; the final image/deployment/supervisor-bound executable packet follows accepted implementation, without any live call during this handoff. Work remains open; no production enabling or satisfying closure is claimed.
