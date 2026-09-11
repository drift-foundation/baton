# Target rework custody, effective base and prelaunch handoff

Parent W131409, slice A. Owner return132696 approves ../../CONTRACT-v1.md and
../../SCOPE-v1.md. Decision pinned in ../../FINDING.md; exact approved bytes and
revalidation in ../../evidence/placement-132699/. Created by reviewer claim132699
with its ledger Work. This child owns only slice A below, not Job rounds or the
assembly. Full parent CONTRACT-v1 is required reading before implementation.

## Accepted scope and boundaries

custody, effective base and sealed prelaunch handoff

Product paths, and only these:

- src/baton_v12/checkpoint_profiles.py
- src/baton_v12/worker_manager/schema.py
- src/baton_v12/worker_manager/review_cycles.py
- src/baton_v12/worker_manager/target_rework.py (new)
- src/baton_v12/worker_manager/attempts.py
- src/baton_v12/worker_manager/offers.py

Tests:

- tests/manager/test_checkpoint_profiles.py
- tests/manager/test_review_cycles.py
- tests/manager/test_store.py
- tests/manager/test_attempts.py
- tests/manager/test_offers.py
- tests/manager/test_target_rework.py (new)

Own the v1 typed records/readers, schema19 fresh-store boundary, immutable
creation/effective-base distinction, retained history/current eligibility,
profile transplant/conflict evidence, writer/freeze rework binding, and atomic
seal versus claim/activation/start admission. Existing claim/launch signature
and refusal contracts remain except the explicit new sealed-attempt refusal.
The bound Authority pass is composed through the existing session, without
editing Authority/core, extending cancellation authority or clearing any gate.

Public provider acceptance: a real old accepted checkpoint plus actual advanced
target content prepares clean same-line evidence preserving both changes; old
audit/create-recover survives. Exact claimed-but-unstarted attempt is sealed,
canonically handed back and cannot start afterward. Conflict/started/uncertain/
unresolved claim inputs hold; identity/tamper/foreign inputs refuse. Prove
profile and cross-owner replay cutpoints. Do not claim ordinary Job completion.

Existing test edits are limited to the new schema/record/writer fields and
target-rework behavior, their exact boundary expectations, and the necessary
fixtures/registries. Preserve all prior isolation, generation and startup guards.


## Current execution authority

Read parent FINDING/PLAN/CONTRACT-v1/SCOPE-v1 and this complete dossier fresh.
Revalidate ../../evidence/contract-131466/base.json against current source before
editing; recorded new paths must still be absent. Pin any clarified design in
this FINDING before implementation; substantive contract/scope changes return to
reviewer for a recorded ruling. Only this child's claimed author writes its
exact six product paths and six test paths. No assembly or Job-owner edits.

80s cumulative implementation verification and8s independent review from one
separate200s W131409 cap; both0s used. No automatic reserve, cross-slice or
W119405 borrowing. Every failing/setup/rerun subprocess counts. Focused contract
controls first and relevant old guards once; no whole module/package/broad/live/
OCI run. Return before exhaustion with unfinished acceptance rather than waive it.
Standing W71830 test authority applies; affected tests/reasons are enumerated
above. Preserve existing assertion behavior outside this bounded scope.

Slice B waits for independent acceptance of this exact candidate. Retain actual
public provider fixtures, typed records, source hashes/modes, changed assertion
inventory, exact selectors/output and all measured runtime for that successor.
No consumer terminal or W119405 acceptance is implied by provider completion.

## Ledger placement — W132712, owner132696, reviewer132699

Canonical child Work W132712 binds this dossier. Slice A: 80s
implementation/8s independent review,0s used. Parent W131409.
Serial dependency B->A is132721, C->B is132725. Only A may dispatch now.

## Dispatch placement claim132735

Read the complete newly bound dossier before dispatch. All listed product/test
paths are relative to v12/python, as in parent SCOPE-v1. Parent gate132734 now
waits on C W132724; B->A132721 and C->B132725 are installed. A is the sole
ready implementer slice. No product edits/runtime during placement;80s/8s unused.

## 2026-09-10T02:38:06Z — implementation pins four clarified design points before editing

claim132749, baton.claude. Written before the first source edit. The pinned
base was revalidated first: all 24 existing paths in
../../evidence/contract-131466/base.json match by digest and mode, and all four
planned-new paths are absent.

**1. `prepare_rework` is handed the target proposal identity and PROVES it.**
CONTRACT-v1 section 2's proposed selector derives the receipt/proposal from
`target_id`, and the Authority has no reader that does: `canonical_target()`
answers a revision, `proposal(id)` and `receipt(id, kind)` answer by proposal
identity, and there is no reverse index from a revision to the proposal that
produced it. So `target_proposal_id` is an explicit operand, and preparation
proves it rather than trusting it -- the proposal exists, its candidate digest
IS the Authority's current canonical target, and its integration receipt exists
with disposition `integrated`. That is the binding section 5 asks for, made
against the owner instead of inferred. The record's four required target fields
are unchanged.

**2. The transplant is computed in the object store and nowhere else.** The
three-way merge answers the old checkpoint's net change replayed onto the
target. It reads three commits and writes one tree: no index, no worktree and
no HEAD is an operand, so the private checkout the line may still be holding is
never written, and no ref outside the new `refs/baton/reworks/` namespace is
reachable from the act at all. The result is committed under ONE parent -- the
target -- because what happened is a reviewed change re-expressed on the
target, not the meeting of two histories. Identity is supplied on the command
line so the act needs no ambient configuration and cannot inherit a human's.

**3. A conflict is an OUTCOME, not a refusal.** `profile.prepare_rework`
answers a held state with its reason and the conflicted paths, with the old
checkpoint's ref, its objects and the checkout exactly as they were, because
none of them was ever written. Turning it into a `ProfileRefusal` would make a
conflict indistinguishable from a broken repository, and section 5 requires the
hold to retain enough evidence for an explicit later decision.

**4. Seal versus launch is decided by the row, not by an observation.**
`attempt_launch_seals` holds one row per attempt, and
`attempts.request_runtime_start` reads it inside the same transaction that
commits launch intent. The store serializes the two immediate writers, so
exactly one wins: if launch wins the seal refuses, and if the seal wins no
adapter start may follow. A null runtime identity or an in-memory reading is
not absence proof and is not what the table records.

Two focused profile probes measured 1.05s: a real clean transplant preserving
BOTH changes with the old checkpoint reference intact and an identical replay,
and a real conflict holding with only the conflicted path retained and no
rework reference written.

## 2026-09-10T03:01:16Z — independent review rejects candidate132749

Reviewer claim132898. Read review-2026-09-10T03-01-16Z.md and retained
evidence/review-132898/. Four confirmed blocking defects: a new-base freeze
still captures B's old HEAD and loses A's content without the test's manual
reset; an interrupted preparation's exact retry never resumes its committed
intent; tampered materialized target data is accepted by rework_of/effective_base;
and an identical successful rework writer-grant retry collides with its own
journal signature. One independent probe process measured0.2861513599054888s.

This explicitly supersedes any delivered/recoverable/cross-bound/complete
interpretation in the earlier implementation claims and PLAN. The accepted
CONTRACT-v1 behavior remains required. Object-store preparation alone does not
provide the writer checkout transition. A test assertion accepting altered
custody bytes is not authority to relax the typed-reader tamper refusal.

Candidate hashes match author handoff; exact eight changed paths and modes
are retained. Author about71.33/80s with one unmeasured-run uncertainty; review
0.286152/8s. Unknown attribution of reported111 failures/7 errors remains open.
Return only slice A for correction; B/C and consumer acceptance stay gated.
No new source scope, runtime transfer, reserve use or acceptance waiver.

## 2026-09-10T03:06:10Z — all four review defects accepted; correction is costed, not started

claim132949, baton.claude, answering review-2026-09-10T03-01-16Z.md. The nine
changed slice-A paths were revalidated against the reviewed handoff hashes
before any edit.

**R1, R2, R3 and R4 are accepted as real defects in my implementation.** None
is a disagreement about the contract and none is argued with below.

**What this claim changed, and it is only the two false certifications the
review named.** `test_the_frozen_round_uses_the_effective_base` performed
`git reset --hard` onto the prepared result before freezing -- and that reset
IS the owner action this slice never built, so the case certified a capability
the product does not have. It is withdrawn, not weakened and not restated as a
boundary case: R1 is a blocking defect inside my own scope, and a case pinning
it would certify my own unfixed work. This slice therefore makes NO
freeze-on-effective-base claim at all. And
`test_a_tampered_custody_row_is_not_read_as_fact` asserted that the reader
ANSWERS an altered target revision, which contradicts CONTRACT-v1 section 2; the
expectation is removed and what remains is renamed to the binding actually
proved. No product file was touched.

**Why no correction was attempted.** The four blockers are interdependent -- R1
changes what a ready record means, R2 the control flow around it, R3 what every
public reader may return, R4 how a grant is signed -- and about 7.4s cannot
verify even the smallest of them. A half-corrected candidate is harder to
attribute than a clean statement, and the review's own instruction is to return
a concrete costed request before spending beyond the allocation.

**The costed request, in the order I would take them:** R4 grant replay 8s;
R2 intent resume 12s; R3 reader binding 15s; R1 the journalled custody
transition that actually puts the prepared content in the writer's checkout
25s; one six-module regression 8s. **68s implementation, 8s independent
review**, against the parent's 200s envelope -- a new allocation, not a
transfer, not a reserve draw and nothing from W119405. The six items the review
lists as still unproved, and the successor rule for a non-null
`current_rework_id`, are deliberately NOT inside those numbers; each needs its
own scope decision and cost.

**The broad run.** Its 26.73s cost stands here and in provider-132749.json. The
exact failure output was read from a terminal and not retained to a file --
that is my error, recorded as one. Recovering it would mean rerunning the
selector the review forbids, so attribution belongs to bounded focused controls
in the corrected pass.

Budget: 1.23s this claim, about 72.56s of 80s including the retained
uncertainty, about 7.44s unspent. The reviewer holds about 7.71s of its 8s. The
10s owner reserve and every W119405 allocation are untouched.

## 2026-09-10T03:08:03Z — allocation request returned for complete costing

Reviewer132973, review-2026-09-10T03-08-03Z.md. Verified the single changed test
path and unchanged rejected product bytes; no verification runtime. Withdrawal
of the two false expectations does not supply R1/R3 defect coverage. All four
blockers remain. Author about72.56/80s with retained uncertainty; review
0.286152/8s. Exact static evidence in evidence/review-132973/.

The proposed68+8 request excludes existing acceptance requirements and cannot
be added inside the fully allocated200s parent envelope. This supersedes its
description as a complete actionable allocation request, without altering the
historical author estimate. The exclusions are not authority to waive provider
acceptance or postpone it beyond A. Required Job-owned facts must be composed
at the existing A/B boundary; identify any concrete contract amendment rather
than inventing a direct cross-owner store read.

Next is a zero-runtime, dossier-only complete estimate/design mapping through
impl, returned to reviewer before the concrete owner decision. No product/test
edits, further test-only runs, extra budget or reserve draw in that pass.
All original requirements and serial gates remain in force.

## 2026-09-10T03:12:00Z — owner supersession received; safe custody recovered

Reviewer133003 read owner M132985/T131409 and parent FINDING03:05:47Z after
the readiness wait returned poke132987. The owner replaces worker-base rework
with immutable isolated submissions and a separately verified integrator-owned
combined result. This explicitly supersedes the executable correction and
costing directions above, including reviews132898/132973 and pass132996; their
defects, evidence and historical charges remain valid observations of rejected
bytes. No old-direction correction or further costing is dispatched.

At snapshot132999 A had no Handler. Reroute133002 returned the unclaimed Work
from impl to bug; claim133003 succeeded. No active claim was taken. Current
product bytes are still candidate132749; the sole later test change edb9d44c
and full manifests are retained by review132973. No source edits or new runtime
in this transition. Author about72.56s with uncertainty and reviewer0.286152s
remain charged; no unused allocation is transferred to replacement work.

Park this superseded child pending the parent replacement contract's explicit
reuse/removal disposition. Preserve all source bytes and dossiers meanwhile;
do not infer permission to erase the failed implementation. Parent owns new
integration-role contract/scope/cost and causal test-evidence requirements.

## 2026-09-10 — replacement D disposition approved, placement133108

Owner133106 approves exact INTEGRATION-CONTRACT-v1/INTEGRATION-SCOPE-v1,
including D disposition through this Work. This supersedes the parked-awaiting-
decision state above ONLY for the bounded disposition, not for old rework fixes.
Current contract is D: six exact restorations and two rejected-new-file removals,
retained evidence first, independent review before closure as superseded.

Parent evidence/placement-133108/D-disposition.json enumerates every current
hash/mode, retained-current copy, exact restore source/hash/mode or required
absence. Reviewer revalidated all eight and their retained evidence; no product
mutation occurred. All43 replacement baseline paths also matched their snapshot.
Before changing ANY path, claimed author repeats whole-set type/byte/mode and
evidence checks. A mismatch stops the whole disposition, without Git operations
or partial restoration. Restore only the six named pre-A files, remove only the
two unaccepted new working-tree files; never delete this dossier/evidence.

Existing test paths affected: tests/manager/test_attempts.py and test_store.py
return to exact pre-A assertions; new test_target_rework.py is removed with its
rejected owner module. Scope-v1 D, owner133106 and standing W71830 explicitly
authorize these exact test changes/removal. Do not redesign or weaken other tests.
The resulting source is pre-A ControlStore schema18; no live store migration,
downgrade, open or reset. Replacement schema5 IntegrationStore belongs to P.

NEW D8s cumulative author+2s independent review,0s used. All setup/failing/rerun
subprocesses count; no old A allowance, reserve or other-campaign transfer.
After exact content/mode/absence checks, run only focused fresh-store/line replay
controls: manager.test_store.OwnershipBeforeAdoption.test_reopening_our_own_store_adds_nothing
and manager.test_review_cycles.ReviewCycles.test_line_and_each_operation_replay_exactly
(module path may include tests according to the existing runner). Record actual
selectors and full timed output. No whole module/package/broad/live/OCI run.
Return before insufficiency, preserving failed checks rather than changing scope.

Author appends own PROGRESS entry for D and returns baton.bug with exact final
manifest/modes, proof of two absences, retained rejected bytes and cumulative D
timing. Do not close this Work. Independent reviewer must accept disposition,
then close A/B/C as superseded with preserved history before P dispatch.

Replacement P W133117 waits on D via133119; Q W133120 waits on P via133123;
R W133129 waits on Q via133133. Only D may dispatch now. No replacement provider,
Authority-publication probe, profile implementation or old-design correction
belongs to this D claim. All old charges and uncertainty remain unchanged.

## Dispatch133146 — D only

Parent gate133144 now waits on R. Unpark133145 and claim133146 succeeded;
reviewer hands only the approved eight-path D disposition to impl, next bug.
Full owning dossier and exact disposition manifest read before handoff. NEW D
author8s/review2s untouched; no product changes or verification during placement.

## 2026-09-10T03:36:42Z — D independently accepted; old A superseded

Review review-2026-09-10T03-36-42Z.md under claim133171 accepts exact D disposition.
All43 expected paths match: six approved restorations, two required removals,
three replacement new files absent and all other paths unchanged. Retained
rejected bytes/restore sources verified. Both focused tests pass; complete
evidence/resulting manifest in evidence/review-133171/.

D author0.22s, independent review0.17817034490872175s; replacement total
0.39817034490872175/260s. All old charges/uncertainty retained. Close this old
Work as superseded/cancelled, not a claim the old product defects were fixed.
Owner133106 explicitly approves this disposition. Replacement P W133117 now
consumes the independently accepted baseline; no replacement acceptance implied.
