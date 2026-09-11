# Prove the composed one-Job lifecycle and retained custody

## Current acceptance clarification — M124896, 2026-09-09

The campaign04:13Z owner ruling explicitly supersedes mandatory intermediate
same-attempt continuation, pre-intent adoption and no repeated starts. The
concrete committed-handoff boundary, minimal restart/abandonment proof and
provider dispositions are pinned in
`baton:work/records/2026/09/finding-v12-composed-ending-consumer/RESTART-ACCEPTANCE-2026-09-09.md`.
Use that current acceptance with the complete joined lifecycle/custody and
uncertain-effect hold. Earlier stronger cutpoint text below is historical,
not an additional acceptance gate. No source/test authority expands.

Ledger Work: W119114. Created by baton.codex under W103083 claim119091.
Historical decisions, candidate snapshots and reviews remain permanently in
../finding-shared-stage-assembly/. This record owns the remaining executable
proof, not a replacement version of that history.

## Confirmed acceptance inherited without expansion — 2026-09-08

Owner M103961's bounded delivery, owner111426's mandatory custody proof,
M115946's held-producer/continuation contract, and M118923/M118986's completion
instruction remain binding. Read the full assembly FINDING and PLAN plus its
review-2026-09-08T12-41-47Z.md, and the accepted port contract at
../finding-integration-runtime-port/HANDOFF-CONTRACT-2026-09-08.md.

Use the actual serving factory and normal manager ticks to carry one submitted
Job through implementation, independent review, one correction on the same
persistent line, acceptance, integration and terminal handoff. Use real local
Authority/Job/Control/Integration stores, accepted ending drivers, the real
retained-manifest producer and public intake/retention/cleanup operations.
The existing deterministic local runtime allowance remains; canned frozen
results, seeded custody receipts, helper-only stage calls or a manufactured
review verdict cannot prove the composed path.

Correlate launched attempt, durable line/object pin, completion and frozen
sealed result with actual public intake/retention receipts. After ordinary
manager-authorized cleanup, reopen retained manifest/artifact bytes at their
recorded locators, verify digests, and reopen/validate the same line pin.
Show sibling custody stayed outside every writable worker mount. Reuse the
accepted configured-access/checkpoint evidence from
baton:work/records/2026/09/finding-v12-private-line-custody-locators/.
Cross-link the new proof and independent acceptance there and in the parent
composition record. Custody teardown and path comparisons do not substitute.

Using this same assembled fixture, prove one representative reconstructed
manager restart from durable state and one uncertain integration that remains
operator-held with no duplicate start. Preserve actual read-only status and
role/session separation. Expanded restart/status/failure matrices remain in
baton:work/records/2026/09/finding-v12-stage-composition-hardening/.
The known post-fence replay defect is not waived: select an unaffected
representative cutpoint or report the actual blocking defect.

## Exact serial ownership

After the preparation correction is independently accepted, baton.claude owns
only the original five paths: v12/python/tools/stage_execution.py,
v12/python/tools/single_worker.py,
v12/python/tests/tools/test_stage_execution.py,
v12/python/tests/tools/test_single_worker.py, and
v12/python/tools/parallel_test.py. Existing assertion limits remain in force;
add focused tests/fixtures within those paths and preserve unrelated assertions.
Preserve the existing W116014 serial registry entries. No new module/path,
provider redesign or additional test-weakening permission follows from this
split. Fix concrete composition defects inside that scope as the proof exposes
them; report a missing external capability as separate accountable Work.

The lifecycle, cleanup and chosen restart controls share one actual attempt/
result/line chain and one fixture. Keep that joined evidence in this single
bounded proof; this does not authorize an exhaustive hardening campaign.
Reassess decomposition if another independently deliverable capability appears.
The original assembly retains final independent joined acceptance and all its
consumer gates. Proof completion alone does not release the whole campaign.
No new live model/OCI or production target authority and no mutating Git use.

## 2026-09-08 — what the first composed run measured, claim119398

**Confirmed.** The implementation half of the composed one-Job lifecycle runs
end to end over the real `operations_from` factory and ordinary
`job_manager.sweep` ticks, with no operator transition after the submission.
Real local Authority/Job/Control/Integration stores; the real checkpoint profile
over a real version-controlled source; the real `claude_agent` workload entered
through `baton_worker.serve_exchange` over the namespaces this deployment
mounted; the accepted ending driver. Measured at each owner's own record: the
private line materialized at the declared base, the writer mounted it writable,
the worker committed it and declared its objects, `output` reached `sealed`, a
real intake receipt was recorded, one artifact was retained under the configured
policy, the proposal was published while the producer assignment was still live,
the checkpoint froze, and ordinary cleanup settled at `retained` with
`execution_runtime = destroyed`.

**Confirmed — the mandatory W105982 custody check is complete.** Its
`review-2026-09-07T15-46-38Z.md` named exactly one remaining acceptance: retain
the actual sealed result outside the writer mount, perform ordinary manager
cleanup, then reopen and verify those same artifact bytes and the persistent
line. All four halves now hold and are proved over bytes rather than pathnames:

- the retained artifact reopens at its own recorded `custody_locator` and its
  measured tree digest equals the digest the intake receipt carries;
- the retained result manifest reopens through `load_manifest` and names that
  same artifact identity and digest;
- the custody tree is outside `roots['workspace']` — the directory this
  attempt's container actually had writable, which under this profile is the
  line checkout itself — and is the line's own sibling rather than an unrelated
  directory; and
- the line survives that cleanup at `review-ready` revision 1 and its checkpoint
  pin REVALIDATES through the accepted profile against the real repository.

Evidence: `evidence/implementation-119398/EXECUTION.md`, and the four cases in
`TheRetainedResultReopensAfterOrdinaryCleanup` and
`TheComposedImplementationHalfRunsOnOrdinaryTicks`. Cross-linked from
`baton:work/records/2026/09/finding-v12-private-line-custody-locators/`.

**Confirmed blocking defect, reported rather than invented — W119548.** The
checkpoint freeze fences the producer assignment and the Authority installs
`runtime-quiescence:<generation>`. The review stage of a composed Job is another
assignment of the SAME Work, so its offer is refused every tick with "an offer
is issued only against open, queued, unclaimed, ungated Work", and the composed
lifecycle stops at the implementation-to-review handoff. Nothing in this build
discharges the gate: `worker_manager.SESSION_OPERATIONS` omits `satisfy_gate`,
no production caller of it exists, and `attempts.py` states the omission
deliberately. The manager DOES hold the evidence the gate requires, because
`authorize_cleanup` observed the exact runtime positively absent — so what is
missing is an accepted act carrying that recorded observation across, which is
outside this Work's five paths. Filed as W119548 with canonical record
`baton:work/records/2026/09/finding-v12-quiescence-gate-discharge/`. The three
cases in `TheComposedHandoffStopsAtTheUndischargedQuiescenceGate` are its
regression and will fail when it lands.

**Observed, in this record's own scope and NOT yet corrected.** The composed
ending is not re-enterable after a successful `end_implementation`.
`_SingleWorker.ending` calls `mount` before it reaches `end`, and
`StageComposition.mount` calls `_prepare` UNCONDITIONALLY rather than through
the `_prepared` cache `end` uses — so a second `conclude` for the same attempt
re-runs `review_driver.prepare_implementation`, whose `grant_writer` refuses
once the checkpoint has frozen and the line has left `writing`:

    operation 'review-line.grant-writer:writer-…' is already recorded with a
    different kind or signature; reusing an id with different operands changes
    nothing (§4.2)

This contradicts `end_implementation`'s own contract that "a process death
between any two steps re-enters here and finishes", and it is reachable whenever
a step after the checkpoint freeze defers — the manager keeps the stage
`answering` until its cleanup axis is terminal and asks `conclude` again every
tick. It was measured during this claim while the cleanup axis was left
non-terminal. It is NOT a hypothetical and it is NOT fixed: the correction
belongs in `tools/stage_execution.py` inside this Work's existing scope, with a
regression that defers cleanup once and requires the next tick to finish the
ending. Recorded here rather than attempted at the end of a claim, because the
right fix reads the existing writer back rather than re-granting one and that is
a design decision a reviewer should see stated before it is coded.

**Decision — the reviewer verdict channel is wired in the NEXT pass, not this
one.** W110772 has since delivered and independently accepted
`review_driver.end_review_from_result`, the production channel that reads the
reviewer's own namespaced claim out of the immutable frozen review result and
cross-binds it to the attempt, the assignment generation and the checkpoint
evidence. Its own record says the shared `tools/stage_execution.py` hookup is the
assembly author's, and this Work's acceptance forbids a manufactured review
verdict — so `StageComposition.end`'s current `deployment.verdict` seam cannot
carry this proof and must be replaced by that entry point.

It is deliberately NOT changed in this pass. The review stage cannot be reached
at all while W119548 is open, so the change could only be exercised through a
helper-only stage call, which this record's acceptance rules out as proof. An
unverifiable source change is worse than a stated one. `_no_verdict` and
`TheReviewersVerdictHasNoChannelAndIsNotInvented` are therefore left byte-for-
byte as they are; no assertion was weakened. **This entry supersedes
`_no_verdict`'s docstring claim that "nothing in this build carries the
reviewer's verdict out of its container"** — that was true when it was written
and is not true now; the history stays where it was written and this is the
current rule.

**Not delivered here, and not claimed.** The review round, the same-line
correction, the acceptance, the integration through the real port, the terminal
handoff, the reconstructed-manager restart and the preserved operator-held
uncertain integration are all downstream of the W119548 handoff and remain
undelivered. This claim delivers the composed implementation half, the mandatory
custody proof, and the two defects the attempt exposed.

## 2026-09-08 — consumer recovery proposal following M119628

**Proposed, pending disposition.**
`CONSUMER-RECOVERY-PLAN-2026-09-08.md` specifies durable retry after terminal
cleanup, safe historical driver resume, the exact six-path shared prerequisite
and the original five-path consumer glue. It proposes separate accountable
shared recovery Work before the joined W119114 proof. The plan explicitly
schedules conversion of the three quiescence-gap assertions and preserves all
other existing assertions. No implementation path was changed to prepare it.

**Authority clarification.** M119587 requested an explicit schedule for those
assertion changes; it did not itself approve them. The earlier next-pass claim
that M119587 schedules their conversion is superseded by this clarification.
M119628 approves W119548's six-path provider only and requires disposition of
this consumer plan before its additional source/test edits.

## 2026-09-08 — approved recovery placement, owner event119712

**Confirmed decision.** baton.slaw approved the exact
`CONSUMER-RECOVERY-PLAN-2026-09-08.md` split, contracts, six shared-provider
paths, five consumer paths and explicitly scheduled three test conversions.
This supersedes the pending consumer-authority status above. It does not
authorize unrelated test changes or accept either implementation.

Shared provider **W119733** now binds
`baton:work/records/2026/09/finding-v12-composed-ending-recovery/` and is a
W103068 sibling delivery. It waits for W119548 actual acceptance (119734).
W119114 retains that original direct gate and additionally waits for W119733
actual acceptance (119735). Owner event119711 returned W119114 to baton.bug
for these mutations, resolving the previously recorded route refusal. Serial
implementation follows those gates, then independent joined acceptance remains
owed. W119673 closes only its approved placement task.

## 2026-09-08T19:26Z — parallel tuner allocation requested by Slawomir

Slawomir requested useful critical-path execution by tuner alongside Claude.
Revalidation finds one independent, already-approved consumer addition:
`_AuthoritySession` still lacks `satisfy_gate`, although W119548's accepted
AuthorityPort and underlying Authority session already carry it. The forwarding
does not depend on W120425's changing historical driver. Both target files are
currently outside any active writer's scope.

Allocate lightweight **W121887** to baton.tuner, returning baton.bug, for
only `v12/python/tools/single_worker.py`'s `_AuthoritySession.satisfy_gate`
forwarding and directly relevant wrapper documentation, plus additive controls
in `v12/python/tests/tools/test_single_worker.py`. Carry the exact operand
document to the existing session; preserve its result and refusal. Do not
derive evidence, discharge a live deployment gate, change ending orchestration,
or edit any other implementation/test path. Preserve all existing assertions.
Focused proof must exercise the wrapped AuthorityPort/session crossing and
exact operands, successful answer and refusal propagation. Declare one question
and a cumulative 10-second focused budget; reuse provider evidence and existing
fixtures instead of running the assembled suite. Retain one concise evidence
note under this record and return for independent acceptance.

This explicitly supersedes serial allocation to Claude only for that forwarding
slice. Tuner holds both files until acceptance; W119114 requires a dependency on
W121887 and keeps all existing recovery-provider gates. Claude continues
W120425 in its separate driver paths. The assembled lifecycle, remaining
single-worker recovery glue and test conversions stay with W119114 after the
gates. Keep deferred inventory work parked; no additional research campaign.

The prompt participant cannot attach a child to W119114's implementation
Route. W121887 is separately scheduled lightweight Work; baton.claude, the
consumer Route Handler, is asked to install its dependency before resuming
W119114. No provider gate is removed and no prompt claim is taken.

## 2026-09-08T19:41Z — independent prerequisite acceptance

W121887's exact two-path forwarding slice is accepted in
`review-2026-09-08T19-41-50Z.md`, with hashes, scope audit and retained test
evidence linked there. This supersedes the pending acceptance/reservation
above; W119114 reuses the accepted method and owns remaining recovery glue.
W119733's joined recovery provider is separately accepted at
`baton:work/records/2026/09/finding-v12-composed-ending-recovery/review-2026-09-08T19-39-44Z.md`.
The lifecycle proof and scheduled test conversions remain W119114's work;
no new capability, path or assertion exception follows from either acceptance.

## 2026-09-08 — partial handback and consumer split, review122032

`review-2026-09-08T19-50-55Z.md` records changes requested on claim121999's
two-seam partial delivery. Its source/probe evidence is the canonical account.
The author's statement that preparation recovery closes re-entry is explicitly
superseded: cold mount reconstruction still refuses, the recovered boundary is
None, and mutable-current-checkpoint/destroyed-only selection misses approved
recovery windows. The public attempt-only publication forwarding is retained
useful progress. Main ending wiring and full lifecycle proof remain unstarted.

Standing decomposition policy now allocates the independently acceptable
consumer ending/recovery result to **W122060**, canonical
`baton:work/records/2026/09/finding-v12-composed-ending-consumer/`, under W103068.
It owns tools/stage_execution.py, tools/single_worker.py,
tests/tools/test_stage_execution.py and tests/tools/test_single_worker.py,
relative to v12/python, serial baton.impl returning baton.bug. This supersedes
the previous allocation of that remaining implementation directly to W119114;
the same owner119712 contracts and three test conversions apply, with all other
assertions preserved. No new provider/schema path is authorized. W119114 waits
for actual component acceptance before shared-file execution, then retains its
full same-Job lifecycle/restart/custody/uncertain-integration proof. The accepted
registry remains unchanged. All original evidence and final joined acceptance
remain here and in W103083; decomposition does not convert partial proof into
completion.

## 2026-09-09T04:13Z — Owner permits repeated work after restart

The campaign FINDING's "Restart from committed handoffs; repeated work is
allowed" ruling is now authoritative:
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/FINDING.md`.
It explicitly supersedes owner119712's mandatory same-attempt intermediate
recovery/adoption and no-repeat-start acceptance in this record and
CONSUMER-RECOVERY-PLAN-2026-09-08.md. Keep the joined lifecycle, retained custody,
safe worker fencing and uncertain committed-effect hold. The managed reviewer
revises the concrete restart proof together with W122060 under M124896.

## 2026-09-09T14:55Z — independent partial review, claim128617

Confirmed: review-2026-09-09T14-55-17Z.md verifies the added custody/fencing controls
and reproduces the abandoned correction remaining blocked. The missing provider
boundaries include cleanup-family-specific discharge, writer/checkpoint restore,
and episode replacement. ABANDONED-RESTART-ALLOCATION.md proposes exact separate
deliveries for owner scope disposition; no implementation expansion is authorized.
The current pending W122060 prerequisite language is superseded by its accepted
closure128464. Full W119114 restart/joined custody acceptance remains owed.
The review also corrects stale provider status and the verification sum; the
implementation author must append the attributable PROGRESS reconciliation.

## 2026-09-09T15:00Z — owner128669 approves exact provider split

Confirmed by baton.codex, claim128673: owner128669 approved the eleven-path
A/B/C allocation, serial baton.impl returning baton.bug with independent
acceptance before consumption, additive provider tests and20s cumulative each.
The exact gap-test conversion named in ABANDONED-RESTART-ALLOCATION.md is
explicitly authorized; all other assertions and specified negative controls
remain required. This supersedes the pending-scope-decision status in the
preceding review/plan and allocation note, not its technical findings.

The independently accountable implementation Works are W128682 (A), W128692
(B) and W128698 (C), siblings under W103068. Their permanent top-level records
are baton:work/records/2026/09/finding-v12-abandoned-cleanup-discharge/,
baton:work/records/2026/09/finding-v12-abandoned-checkpoint-restore/ and
baton:work/records/2026/09/finding-v12-abandoned-episode-replacement/.
Each CONTRACT.md pins public selectors, closed results, ownership, replay and
negative behavior before edits. Revalidate accepted predecessor bytes/contracts
at dispatch. These are implementation deliveries, not planning Jobs.

The sequence is A independent acceptance -> B independent acceptance -> C
independent acceptance -> W119114 bounded glue and final joined proof. Preserve
explicit abandonment authority, committed effects and exclusion before restore/
replacement writes. The owner requires W119114's usage reconciliation within
its original600s cap without reset. W122060 evidence is reused. No other
source allocation, generic retry feature or whole-suite waiver follows.

## 2026-09-09T17:27Z — accepted provider chain; final consumer dispatch

Claim129617 revalidates all five consumer files byte-identical to
review128617; evidence/base-129617/ retains the exact dispatch baseline.
The separately allocated provider chain is now independently accepted:

- A: baton:work/records/2026/09/finding-v12-abandoned-cleanup-discharge/review-2026-09-09T15-29-15Z.md and evidence/accepted-128851/ in that dossier.
- B: baton:work/records/2026/09/finding-v12-abandoned-checkpoint-restore/review-2026-09-09T16-52-52Z.md and evidence/review-129380/ in that dossier.
- C: baton:work/records/2026/09/finding-v12-abandoned-episode-replacement/review-2026-09-09T17-26-15Z.md and evidence/review-129599/ in that dossier.

Each provider's CONTRACT.md remains the exact public receipt boundary. C uses
the separately named EXCLUSION_ENDINGS reason, preserving terminal offer
vocabulary. Its acceptance proves original Job/checkpoint/episode ownership,
replay and concurrent duplicate closure, not this final assembled lifecycle.
This supersedes provider-pending wording as the actionable plan; history stays.

Standing AGENTS.md#w71830-standing-test-change-authority supersedes older
additive-only/per-method/assertion-preservation permission limits in this
record and allocation note. Record affected tests/reasons and independently
review required behavior; no further per-test approval request is needed.
Source scope and runtime budgets remain unchanged. Provider final accounts
do not reset this Work's600s cap.

Current bounded consumer change: after the explicit abandonment declaration,
call A's abandoned-family gate discharge, B's public review_cycles restore,
and C's episodes restart; let ordinary ticks allocate the next writer. Reuse
the same committed-handoff/unfinished-scratch fixture and retain actual positive
exclusion, exact checkpoint bytes, original publication and route ownership.
Do not turn a timer into abandonment or accept component proof as fresh actual
assignment. Finish corrected-result artifact/manifest/pin correlation after
actual integration and terminal handoff in the same submitted Job.

Before new verification the author must append the review128617 budget and
attribution correction: reported durations sum to approximately353.487s, with
documented uncertainty and missing exact timings, not173.7s. Reuse valid prior
ordinary/reconstruction/read-only/serial evidence; run only required missing or
invalidated checks within the carried600s cap. Separate whole-universe scan
diagnostics remain with W115981/W48697 and are not waived here. If the repaired
transition still fails, retain and diagnose that exact handoff before another
local allocation. No new planning Job or scheduler scope is authorized.

## 2026-09-09T17:41Z — recovered assignment verified; final proof still owed

Review-2026-09-09T17-41-03Z.md independently verifies progression past the old
blocked transition to one fresh assignment, scratch restoration and preserved
effects. Its readback shows that new worker still waiting, with no frozen
output and review/integration blocked. The author's claims that the recovered
worker turn and same Job finish are superseded as current conclusions: the
candidate proves admission, not that remaining execution. The corrected
post-terminal manifest correlation requested by review128617 remains absent.

Current action is to finish this same recovered fixture through terminal
integration and reopen its corrected manifest/artifact/pins. Evidence and
candidate custody are in evidence/review-129681/. Author approximate carry is
457.587/600s,142.413s remaining; prior uncertainty is preserved.

The review audits the requested blanket serial rerun: A/B add explicit new
paths but leave existing engine function bodies and behavior-bearing globals
unchanged, while affected Job/integration drivers were freshly verified.
Reuse retained evidence for those unchanged engine scenarios under the current
evidence-reuse policy, without claiming a new serial pass or waiving the31
parallel failures. This supersedes the proposed300s-extension prerequisite for
that stated reason; complete the missing fixture inside current authority and
reassess only a concrete uncovered execution path. Existing scan remediation
ownership remains W115981/W48697.

## 2026-09-09T17:53:28Z — independent final proof accepted

Reviewer claim129744 accepts provider129718. review-2026-09-09T17-53-28Z.md resolves the remaining
terminal/corrected-manifest P1 from review-2026-09-09T17-41-03Z.md: the recovered
same Job finishes all three stages, commits terminal pass and reopens corrected
custody with matching result, candidate, line and checkpoint evidence. Prior
claims that stopped at fresh assignment remain superseded history. Exact five
files and independent0.889505s proof are in evidence/review-129744/.
Author cumulative charge approximately484.073/600s; serial reuse stands and the
300s request is withdrawn. Outstanding31 parallel scan failures remain with
W115981/W48697. No per-test approval gate under standing W71830 authority.
