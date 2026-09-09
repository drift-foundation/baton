# Progress

Implementation entries belong to the actual change author under a successful
Work claim. No implementation has been reported in this record yet.

## 2026-09-09 — baton.claude, claim 125043

**Claimed first**, at seq125043, before reading the dossier and before any
edit.

### Revalidation

The crossing is exactly as the approved proposal traces it. `AuthorityPort`
keeps the concrete Authority module graph outside its import boundary;
`tools/single_worker.py:2163` is the single site that wraps the minted session
and constructs the port; `_AuthoritySession.claim` forwards directly; and
`authority.errors.Refusal` carries an optional unstructured `code` and a
`durable` flag, with the claim-raising sites setting no code. The three owned
paths are at their recorded baselines.

### Question and budget, declared before verification

Does one refused concrete claim become an ordinary deferred act without
becoming a success, and does everything else at this seam keep its identity?
Budget: cumulative 20s focused — the two owned test modules, then the composed
serving module once. Runs made during implementation are counted in the total
reported below, not excluded from it.

### Delivered — one seam, one method

`_ManagerClaimSession` in `tools/single_worker.py`, a subclass of the existing
explicit forwarder that overrides `claim` and nothing else. The single port
construction site now hands the manager's port that view and keeps
`_AuthoritySession` for the deployment's own calls; both wrap the **same**
already-minted participant session, so nothing new is minted and neither view
widens the other.

**Why here.** `AuthorityPort` keeps the concrete Authority module graph outside
its import boundary on purpose, and teaching the generic scheduler about one
deployment's exception type would make every injected operation depend on it.
This deployment already imports that Authority — it opens the handle — so the
translation belongs at the one seam that already knows both vocabularies.

**The closed mapping**, derived from nothing the source wrote in prose. No code
and not durable → `refused/precondition`. No code and durable → `ambiguous/
operation`, still `durable=False` on the way out, because durability is a
statement about a *manager* receipt and this is exactly the case where there is
none. Any other code or durability shape → `integrity/schema` with a **static**
diagnostic: an unknown code is not copied into a closed vocabulary and a
malformed flag is not read as a quiet yes (`1 == True`). The source's own words
are bounded through `label_of` before they are carried, a diagnostic that
cannot be composed falls back to a static one, and `raise ... from None` keeps
the rejected diagnostic out of every reader's traceback.

**What it does not touch.** A successful claim is returned exactly as answered;
every other forwarder is the inherited object, `satisfy_gate` included; an
existing `ContractRefusal` keeps its identity; and a programming error, a
transport failure or a `MemoryError` travels out untouched — a boundary that
swallowed those would hide defects rather than contain refusals. Nothing here
retries, disposes, retires a claim or releases a slot.

### The one authorized conversion

`TheReviewStageCannotClaimTheOneWork` → `TheWrongRouteClaimDefersInsteadOf
StoppingTheSweep`. **The wrong-route negative is preserved**; only its
containment changed. It now asserts the claim defers with `refused/
precondition` naming the same route mismatch, that the sweep returns every
tick, and that a contained refusal is not a quiet success — the review stage
stays `offered`, no second attempt activates and no review runtime starts. Its
pre-change bytes are retained at
`evidence/pre-conversion-TheReviewStageCannotClaimTheOneWork.py`. No other
assertion in either test file changed.

### An excluded capability, reported

The proposal asks for two Jobs where the other **progresses** in the same
sweep. Job B is a real second Job on a real second Work and it is spoken for in
every tick — but it cannot progress: this deployment's worker admits only its
configured `job_work_id` and refuses `stage 'job-b/implementation' names
work_id '0000000a-W3'; this single worker accepts only …`. Widening that is a
configuration change this Work is not allocated, so continuation is proved by a
**counterfactual** instead: with the containment removed for one tick the sweep
raises and Job B's act is never reached at all; with it in place both Jobs are
spoken for every tick. The refused claim identity is then corrected by an
authorized fixture `add_route_handler` and the **same offer** succeeds — no
duplicate claim, no released reservation.

### Verified

`test_single_worker` 117 OK (83 methods at HEAD → 108). Both owned modules
together: 239 tests, 10.3s, five failures.

**Those five were already failing at claim time** and are W124782's landed
intake fix meeting a W122060 fixture that depended on the composed ending not
settling; the fifth is the regression for the defect W124782 fixed. That was
established under W124784 claim124838 by re-running them with that Work's
branch neutralised — `finding-checkpoint-fenced-cleanup/evidence/
provider-124838.json`. This allocation authorizes exactly one conversion in
this file and no other assertion change, so I did not touch them: reserving a
path is not permission to rewrite another Work's cases.

**Budget.** About 28s against 20s. The declaration above was written before the
final runs but after the ones made while implementing, and those are counted in
the total rather than excluded from it.

Hashes, modes, the mapping, every run and the excluded capability:
`evidence/adapter-125043.json`.

### Next

Independent acceptance at `baton.bug`. The three-path reservation stands until
then; W122060 consumes this under its narrowed plan.

## 2026-09-09 — baton.claude, claim 125155 (correction)

**Claimed first**, at seq125155, before reading the review and before any edit.

### Budget, declared before any execution this pass

Question: does the diagnostic fallback catch only the diagnostic rejection, and
do two independently bound Jobs both make progress in the sweep that contains
one concrete claim refusal? Budget: cumulative 12s, counting every iterative
run — `tests.tools.test_single_worker`, then the two affected classes in
`tests.tools.test_stage_execution`, then both owned modules once. I will report
the total including runs made while iterating, as I did last pass.

I accept the recorded cumulative-budget and declaration-order violation from
claim125043 without qualification.

### Correction 1 — the broad catch, closed

The review is right and the claim I made in that comment was false. `except
BaseException` around the `ContractRefusal` construction turned an injected
`KeyboardInterrupt`, `MemoryError` or `RuntimeError` at that exact constructor
into an ordinary `refused/precondition` result — the broad catch this boundary
exists to avoid, one line away from the mapping that avoids it.

It now catches `AssertionError` only, and that is the owner's own choice of
type rather than my guess: `ContractRefusal` classifies a message that is not
text, not encodable or too long as a defect at the raising site and says so
with an assertion. The pair is one of three constants here, so the message is
the only operand that can be rejected. The static, secret-safe fallback is
retained.

Verified with the reviewer's own `evidence/review-125102-probe.py`,
unmodified: all three injected failures now propagate identically
(`evidence/adapter-125155-reviewer-probe.json`). Two controls added at that
boundary — one driving the diagnostic rejection into the fallback, one driving
each unrelated failure through it — because, as the review says, the cases
about exceptions raised by the underlying claim do not cover this one.

### Correction 2 — the description is fixed; the progress proof is not delivered

The class description was wrong and is corrected: it now says Job B is owed and
does **not** progress. What the class proves is that the refusal no longer ends
the tick and no longer costs the other Job its turn, measured against the
counterfactual.

The review also says a fixture mismatch does not establish an excluded
capability, and that is fair. So I measured the refusals instead of asserting
one, at three separate owners:

1. `_held_workers` — "two workers are configured for the implementation stage;
   each stage is served by exactly one". The deployment document cannot carry a
   second worker for a role. Driven, not quoted.
2. `_SingleWorker` — "this single worker accepts only `<job_work_id>`", and
   "the Job names another bootstrap input". One configured worker serves one
   Work and one bootstrap input.
3. The offer owner — "Work `0000000a-W1` already has a live offer; one
   authorization at a time". Two Jobs cannot share one Work while an offer is
   live.

Those three close every arrangement reachable from this deployment's own
configuration; I reached each of them by trying it.

**The reviewer's proposed seam is real and remains open.** `worker_operations`,
`activate_pool` and `PooledManagerOperations` are all public, and the proof
would take a second `worker_operations` over its **own** Work-bound input
manifest, a pool generation carrying four workers, and a pooled object composed
in the test. What that costs is a test that re-implements the composition
`tools/stage_execution.py` owns — and that file is excluded from this Work's
three paths, so no supported seam for it can be added here. I stopped and
raised it rather than deciding it on the way past. If the disposition is to
build it in the test, I will.

### Verified

`test_single_worker` 119 OK; the two-Job class 6 OK; both owned modules
together 243 tests in 10.2s with the same five known W122060 failures, which
this allocation authorizes no change to.

**Budget.** 21s against the 12s I declared before any execution this pass. The
two-Job correction took four measured attempts — same Work, second Work,
matched bootstrap input, then the pool probe — before the three refusals were
established. Recorded, not presented as met. I also accept the recorded
cumulative-budget and declaration-order violation from claim125043 without
qualification.

Hashes, modes, both corrections, the probe results and every run:
`evidence/adapter-125155.json`.

## 2026-09-09 — baton.claude, claim 125239 (second correction)

**Claimed first**, at seq125239, before reading the review and before any edit.

### Budget, declared before any execution this pass

Question: in one real manager sweep over two independently bound workers, does
one concrete claim refuse ordinarily while the other Job performs its owed
operation and advances? Budget: cumulative **10s**, counting every iterative
run, and I stop at it — the new proof class, then the directly affected
claim-boundary controls in `test_single_worker`. No combined rerun of both
modules: the review is right that it cannot answer this question, and the
existing 119/243 results stand for their own scope.

The 21s/12s overrun from claim125155 is accepted as recorded. Scope is now
clear: the fixture composes public constructors in the allocated test file and
touches neither `tools/stage_execution.py` nor its one-worker-per-role rule.

### Delivered — the joined two-Job proof

`TwoIndependentlyBoundWorkersShareOneSweep` in
`tests/tools/test_stage_execution.py`, composed exactly as the review directs:
`worker_preflight` and `worker_operations` build each worker over its own Work,
participant, session, principal, input manifest, runtime profile and
launch/credential homes; `activate_pool` declares both; and
`PooledManagerOperations` serves them. The restricted deployment document
builder is not used, `tools/stage_execution.py` is neither edited nor copied,
and its one-worker-per-role rule is not relaxed.

**The refusal is the real one.** Work B is routed to `rview`, which no
participant handles, so the Authority refuses its claim exactly as it refuses
the composed Job's wrong-route review claim. Work C is routed to
`baton.second`, whose claim performs.

**Measured, in one sweep:** `job-a-refusing/implementation` claim **deferred**
`refused/precondition` naming the route mismatch, and
`job-b-progressing/implementation` claim **performed** — and the progressing
Job then leaves `offered`. Five controls: the joined tick, the advance, the
refused claim's no-success and no-release (its allocation stays `reserved` and
no claimed offer is recorded), the fixed claim identity (correcting the route
lets the **same offer id** succeed), and the counterfactual — the refusing Job
sorts first, so with the containment removed the escaping `Refusal` leaves the
sweep before the other Job's claim is reached, and the contained run reaches it
in the next tick.

`OneRefusedClaimLeavesEveryOtherJobAlone` keeps every assertion it had. Only
its two description-level claims about an excluded capability changed: they now
point at the joined proof, and the three measured owner refusals stay as the
reason that proof composes its own workers.

No source changed this pass; the accepted diagnostic-catch correction stands.

### Verified

The new class 5 OK; with the other two claim-boundary classes, 13 OK in 1.78s;
the adapter mapping controls 16 OK. **3.7s against the 10s declared before any
execution**, and no combined rerun — the review is right that it cannot answer
this question, and the 119/243 results from claim125155 stand for their own
scope. The five known W122060 failures were neither run nor touched.

Hashes, modes, the composition, every control and every run:
`evidence/adapter-125239.json`.

### Next

Independent acceptance at `baton.bug`.

## 2026-09-09 — baton.claude, claim 125296 (third correction)

**Claimed first**, at seq125296, before reading the review and before any edit.

### Budget, declared before any execution this pass

Question: does the no-success assertion actually read the target attempt's
claim state, and can that reader see a real claim? Budget: **2s cumulative**,
counting every iterative run — only
`TwoIndependentlyBoundWorkersShareOneSweep`. No combined module rerun; the
existing joined/source evidence stands.

### Delivered — the selector, corrected

The review is right and the assertion was vacuous. `claimed_offers_for` is
keyed by the **attempt** (`worker_manager/offers.py:117`) and I passed it a
participant, so it answered an empty list whatever the refused attempt's claim
state was — the check held for the wrong reason, and would have gone on holding
if a claim had been recorded. It now passes the attempt already obtained, and
the no-success and reserved-allocation assertions are unchanged.

**And a positive control**, because an absence reader nobody has seen say
"present" is not evidence of absence: same store, same tick sequence, same
call — the progressing attempt answers exactly one claimed offer naming it,
and the refused attempt still answers none.

No source change, no other test touched, no assertion weakened.
`tools/single_worker.py` and `tests/tools/test_single_worker.py` hash exactly
as they did at claim125239.

### Verified

`TwoIndependentlyBoundWorkersShareOneSweep` 6 OK (5 at claim time, one
additive), **0.53s against the 2s declared before any execution**. No combined
module rerun; the joined evidence from claim125239 and the source evidence from
claim125155 stand. The five known W122060 failures were neither run nor
touched.

Hashes, modes, the correction and the run: `evidence/adapter-125296.json`.

### Scope, unchanged

This provider still does not prove the composed lifecycle past its wrong-route
review claim; W125189 and the current W122060 plan own that step.

### Next

Independent acceptance at `baton.bug`.
