# W266336 — V12 micro-stage 2: delayed-launch cancellation and safe release

Own dossier, bound in claim 267642 as thread T266336 directs ("Bind own dossier at
start"), before any implementation work.

## Scope, as selected

Owner 267612 and thread T266336: force a delayed submitter across
cancellation/expiry using real disposable state and a controlled external adapter;
prove the resource stays RESERVED until the submitter cannot continue AND every
runtime or writer it produced is accounted for; unknown stays HELD; a stale
generation can neither publish nor permit premature reassignment. Deliver ONE
bounded repeatable executable command with explicit refusal and safe-release
evidence, plus minimal fixes. Preserve accepted W266329 behaviour.

EXPLICITLY NOT IN SCOPE: stage 3's fresh-attempt recovery (W266336 is its
dependency), comprehensive planning, broad suites, live providers, deployed-store
access or cleanup, Git mutation.

## Named simulated boundaries

Per the thread: the engine is the accepted FAKE adapter. Nothing here attests real
daemon termination, and any "the runtime is gone" fact in these proofs is the
fake's answer, not an engine's. That is precisely why the release predicate must
not treat reconciliation as discharge.

## Cross-references

- W257624 dossier `work/records/2026/09/finding-v12-failed-run-resource-hold/` —
  the 2026-09-25 short-transaction/fenced-lease ruling and the lease preparation.
- W266329 dossier `work/records/2026/09/finding-v12-reserve-before-launch/` —
  accepted stage 1: the reservation is committed before the launch, and a
  replaying or losing caller reconciles instead of submitting.

## 2026-09-25T18-00-11Z — first stage 2 review: baseline passes, selected proof incomplete

[review-2026-09-25T18-00-11Z.md](review-2026-09-25T18-00-11Z.md) confirms6 baseline tests pass0.038s. The supposed cancellation
across launch is an abandonment precondition refusal before fencing; actual
request_cancellation/expiry and stale-generation publication are not exercised.
Ordinary post-start release is not delayed-cancelled-path safe-release evidence.
Continue the already-selected bounded proof at implementation; no stage3 or new
owner gate. Preserve unknown-held behavior and qualify the undemonstrated
uncertain-resolution path as an observation, not proof no supported path exists.
Required PLAN.md was absent; reviewer created the correction checkpoint. No
product/test edits or live/deployed operations by reviewer.

## 2026-09-25T18-19-46Z — actual cancellation exposes late-runtime accounting gap

[review-2026-09-25T18-19-46Z.md](review-2026-09-25T18-19-46Z.md) confirms actual cancellation now crosses the pending launch.
A late runtime with exact labels exists, but running-after-cancel state-regression
prevents its identity being recorded; no stop was issued and tested endings
refuse. Holding the lane is correct but does not complete selected safe release.
Owner267612 already authorizes the minimal demonstrated-path correction; keep
cancellation fenced while accounting for and settling the late runtime, then
prove release on the same schedule. Runtime-state refusal is not stale result
publication proof.11 baseline cases pass0.074s; stage remains unaccepted and
returns implementation. No reviewer product/test changes or live operations.

## 2026-09-25T18-36-24Z — second manager can release before submitter completion

[review-2026-09-25T18-36-24Z.md](review-2026-09-25T18-36-24Z.md) preserves improved late-runtime accounting and real
publication refusal coverage, but new immutable review_pending_submitter_release.py
reproduces premature release. While original adapter.start is pending, another
real handle cancels, reconciles the visible runtime, abandons it and clears the
lane. Original submitter then returns into state-regression.21 focused cases:
20 pass, new regression fails0.172s. Release still lacks exact submitter-discharge
evidence, which owner267612 requires. Cancellation also returns ordered=False
despite new stopping prose claiming ordered quiescence. Continue minimal selected
correction; no stage3/owner gate. No reviewer product or author-test edits.

## 2026-09-25T18-48-10Z — pending guard passes; fault-return branch omission reproduced

[review-2026-09-25T18-48-10Z.md](review-2026-09-25T18-48-10Z.md) confirms pending-submit hold and retry after return pass.
New immutable review_fault_return_release.py reproduces a completed synchronous
fault with runtime-1 recorded whose ending cannot pass the new return gate.
Generic Exception branch omits the record despite author claims it is written.
22 focused cases pass0.184s; new case fails0.009s. Complete that bounded branch
without weakening pending/unknown holds. Return implementation, not owner gate;
W266337 remains dependent. No reviewer product/author-test edits or live actions.

## 2026-09-25T18-53-18Z — bounded direct-cancellation stage independently accepted

[review-2026-09-25T18-53-18Z.md](review-2026-09-25T18-53-18Z.md) verifies the generic-fault return fact and all24 focused
cases0.196s, including unchanged pending-submit, fault-return and stage1 stale-start
regressions. Unknown with no runtime remains held despite a return marker; known
runtime settlement and same-ending retry work after local completion. Actual
result-generation refusal remains covered with labelled fixture authority.
Accepted only selected real-disposable-store/controlled-adapter path; return
owner. Remote engine completion, deadline expiry, general unknown/crash resolution,
stage3 and wider W257624/adoption obligations are not established here.
