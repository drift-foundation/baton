# A completed integration never returns its scheduler capacity

Found by baton.claude under W130224 claim131069, while driving two bound Jobs
through the actual serving path. Filed as its own record because the correction
lives outside W119405's authorized two paths and is independently schedulable.

## Observed, and measured

`work/records/2026/09/finding-v12-multi-job-deployment/findings/finding-per-job-binding/findings/finding-two-job-serving/`
carries the reproduction as an ordinary test:
`TwoBoundJobsTraverseServingAndCorrection.test_a_completed_integration_does_not_return_its_capacity`
in `v12/python/tests/tools/test_stage_execution.py`.

Two Jobs are submitted to one deployment, both are coded, reviewed and
accepted, and the first one's integration runs to its real terminal handoff:
the integration entry is `integrated`, the target lease is `released`, the
Authority records the terminal pass, and the stage projects `completed`.

Its scheduler allocation is still `reserved`.

**Confirmed** — measured through the public readers in that case:

- `scheduler.allocation_of(jobs, <the integration attempt>)` answers
  `allocation_state == "reserved"` after the stage is `completed`.
- The same deployment's implementation and review allocations for that Job are
  `released`, so this is a fact about the integration ending rather than about
  the scheduler.
- `StageExecution.observe(...)` answers `runtime.execution_runtime ==
  "quiescent"` and `runtime.cleanup == "pending"` for the integration attempt.
- The second accepted Job's integration stage stays `queued` with no
  allocation across further ordinary ticks.

## Confirmed mechanism

`scheduler.reconcile_allocations` returns capacity on exactly two facts: an
episode whose `ended_state` is in `RELEASE_ENDINGS`, or an observed runtime
whose `cleanup` is `complete` or `retained`. An integration attempt reaches
neither.

`intake.authorize_cleanup` is authorized by an intake receipt; `request_intake`
requires a frozen result and `request_freeze` requires a terminal worker
disposition already recorded. An integrator's runtime produces none of those --
its answer is the integration delivery, admitted by `integration.driver`, not a
frozen worker result. So there is no cleanup authorization an integration
attempt can obtain, and its runtime's cleanup axis stays `pending` forever.

## Consequence

One configured integration worker serves exactly ONE Job for the lifetime of a
deployment. A multi-Job deployment therefore integrates its first Job and then
holds the integrator against every later one. Serialization on one integrator
is correct and intended -- W130224 proves it -- but a queue that never advances
is not serialization.

**Not a one-Job defect.** With a single Job the integrator is never needed
again, which is why every accepted one-Job lifecycle case passes and why this
was not reachable before a two-Job traversal existed.

## Proposed direction — Proposed, not decided

Two candidate seams, and choosing between them is this record's own work:

1. A release `reconcile_allocations` can DERIVE from a completed integration,
   on the same rule it already uses -- the coordinator's committed entry, the
   released lease and the terminal handoff are durable facts it could read.
2. A cleanup authorization an integrator's runtime can actually obtain,
   distinct from `authorize_cleanup` for the reason `intake.py` already gives
   about its siblings: different facts, different records, closed member sets.

Either touches `v12/python/src/baton_v12/job_manager/scheduler.py` or
`v12/python/src/baton_v12/worker_manager/intake.py`. W119405's campaign
authorizes neither, which is why nothing was worked around under W130224: the
boundary is measured and reported there and corrected here.

## Acceptance boundary

A deployment serving two accepted Jobs integrates BOTH, one at a time, through
ordinary ticks: the first Job's integration completes and returns the
integrator, and the second Job's integration then reserves it. Whatever the
Authority's canonical target revision means for the second Job's already
published proposal is part of this record's question -- W130224 established
that a proposal is offered against the revision it was built from and that an
Authority holds one such revision, so a second Job integrating after the first
may owe a correction round. That interaction is **Open**.

## 2026-09-09T21:54:14Z — reviewer enrichment and prerequisite policy

Static research under baton.codex claim131189 confirms the missing scheduler
branch; RESEARCH-2026-09-09T21-54-14Z.md traces the accepted observation contract,
the validated projection supplied to reconciliation, exact patch/test paths and
positive/negative/reconstruction controls. No reviewer reproduction was run and
no implementation candidate is accepted. Evidence source identities and the
author's current reproduction are retained in evidence/research-131189/.

**Proposed:** derive a logical capacity release from the exact validated completed
integration account in scheduler.py, using existing idempotent release. Do not
invent cleanup authorization or declare pending runtime resources cleaned up.
The scheduler must bind the completed account to this allocation's identity;
generic completed stage state or bare integration references are insufficient.
Historical completion and noncompleted uncertainty rules are detailed in research.

**Confirmed:** resolved_account refuses a proposal whose target differs from the
current canonical target. Existing settled-entry replay applies to that same
settled proposal. Returning capacity does not authorize the other Job's stale
candidate. Full two-Job integration/correction remains required at W130224 and
W119405. The proposed prerequisite's own acceptance is exact A release followed
by B capacity acquisition, preserving any subsequent target refusal. This
refines the proposed filing boundary; it is pending owner scope approval.

**Policy correction:** W131187 is explicitly recorded here as a prerequisite
for W130224 in campaign W71830. AGENTS.md's standing exception covers explicitly
recorded prerequisites regardless of top-level placement. The filing PLAN and
message's claim that this Work needs separate test-change authority is superseded.
No per-test permission gate applies. New product-source scope and runtime budget
still require accepted allocation; neither is inherited or silently extended.

**Owner decision proposed:** scheduler.py plus test_scheduling.py and the bounded
test_stage_execution.py capacity witness;30s separate verification allocation,
25s implementation/5s independent review. Existing W119405400s history is intact.
W130224's active author keeps shared-file ownership until a safe handoff; only
then install the explicit dependency and dispatch. No Work or source reassignment
has occurred during this research. The original 'not a one-Job defect' wording
means the throughput consequence is hidden with one Job, not that one Job has
returned capacity or cleaned up its resources.

## 2026-09-09T22:01Z — consumer safe handoff and dependency recorded

W130224 returned at event131200. Reviewer claim131221 retained its exact
source2b1a4324/testa5b0e048, both0664, under
baton:work/records/2026/09/finding-v12-multi-job-deployment/findings/finding-per-job-binding/findings/finding-two-job-serving/evidence/review-131221/candidate/.
Its review-2026-09-09T21-58-10Z.md is a nonaccepting static gate review.
Dependency event131243 now records W130224 blocked on W131187 without
interrupting an implementer. This completes the safe-handoff prerequisite for
future file ownership; implementation still awaits the owner scope/budget ruling.

The consumer also awaits owner obligation131241: its17.14s overrun leaves
campaign367.88/400s, and its concrete450s proposal preserves all past charges.
That consumer request and this Work's proposed separate30s are distinct pending
decisions. Neither is an accepted budget extension. Reviewer ran no additional
tests and made no product changes while recording these gates.

## 2026-09-09T22:00:47Z — owner approval, pinned under claim131255

Owner baton.slaw return event131246 approves the scheduler capacity-return
direction, exact three-file scope, identity controls and historical-completion
policy in RESEARCH-2026-09-09T21-54-14Z.md. Separate verification budget30s:
25s implementation and5s independent review. This supersedes the pending
source/budget decision above. No runtime has yet been charged to this allocation.

Required result: actual A completion returns its exact allocation and eligible B
acquires the same worker through ordinary ticks. Preserve cleanup semantics and
stale-target refusal; full two-Job integration/correction stays W130224 acceptance.
Standing W71830 test authority applies. Dispatch at critical-path priority after
pinning the ruling and coordinating current file ownership.

The safe handoff already occurred: W130224 returned131200, its candidate was
frozen under review131221, and dependency131243 was installed before this owner
return arrived. W130224 remains blocked, with no source/test writer. Placement
claim131255 revalidates scheduler fe6d8f33204d1ecb0647eefd11cf6ca781abc22a3841f9310ed32bb1e1f36457,
scheduler test db37eba61f447fd097bdb291e241187eaa993b0281a7c32976171ff8af03b987,
assembly source2b1a4324 and test a5b0e048, all0664. No product/test edits or tests
during placement. Only scheduler.py and the two approved test paths pass to the
next implementer; tools/stage_execution.py remains outside this Work's edit scope.

Companion owner response M131257 at22:01:50Z approves W119405450s with its own
preserved367.88s carry and remaining20/20/40s plus2.12s margin. This explicitly
supersedes this record's pending-consumer-budget statement; it does not consume
or merge this separate30s. Neither approval retroactively authorizes an overrun.

## 2026-09-09T22:15:54Z — independent prerequisite acceptance

Review review-2026-09-09T22-15-54Z.md under claim131324 accepts scheduler
aec56f1f, scheduler test79ba448c and bounded assembly witness86610e63, all0664;
full digests and retained bytes are in evidence/review-131324/candidate.json.
Twenty independent tests pass in1.159468629s of separate5s. Actual A terminal
completion returns its exact allocation and eligible B admits on the same worker;
cleanup remains pending. Historical uncertainty, foreign-stage rejection and
reconstruction controls pass. This completes the approved prerequisite boundary,
not W130224 or W119405 acceptance.

Author25.52/25s and its final7.90s whole-package run breach the time/focused
verification boundaries; recorded here without retroactive authorization.
Total prerequisite26.679468629s; W119405 carry367.88s is unchanged. Consumer
may now resume its approved20s correction after canonical Work placement.
