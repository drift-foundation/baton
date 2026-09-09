# Progress

## 2026-09-08 — baton.claude, claim 122089

### Revalidation

Read this FINDING/PLAN, the approved `CONSUMER-RECOVERY-PLAN-2026-09-08.md` and
the originating `review-2026-09-08T19-50-55Z.md`. The four owned paths at claim
time:

    c2706af1732ed1a802050f404f89028ff7db3a56a864bca01105ff08e835fbd8  664  tools/stage_execution.py
    ff383296aeb75885668d365d3cdc5ff1a280234f5282694acb7f37cc3f4ca47f  664  tools/single_worker.py
    a5f9aba5d853da72e80839b68f22e1280818d0763aceb4d21d309527ddf65779  664  tests/tools/test_stage_execution.py
    af445808743e15c7a95017b9ef3d685c4b96b0a45a439940cc60a553c8a8aa3b  664  tests/tools/test_single_worker.py

`single_worker.py` still hashes to W121887's accepted candidate, so its
forwarding is reused untouched. No path was edited under this claim.

### The FINDING's open boundary, resolved: the provider gap is real

PLAN step 1 requires reporting a missing owner capability before editing. It is
missing, and this is the exact diagnosis.

**The root cause of the second-`conclude` failure is not the line state.** The
refusal is `operation-collision` — "already recorded with a different kind or
signature" — which means the second call derived DIFFERENT operands, not that
`grant_writer` rejected a frozen line. `StageComposition._prepare` passes
`based_checkpoint_id=line["current_checkpoint_id"]`, which is `None` on the
first round and the frozen checkpoint afterwards. `grant_writer`'s replay
short-circuit sits before every line-state check, so an ending that supplied the
SAME operands would replay cleanly and return its writer. What breaks it is that
one operand is read from a mutable pointer that the ending's own freeze moves.

**No accepted public owner answers the durable operand.** The writer row holds
`based_checkpoint_id`, and reading it needs `writer_of(store, writer_id)`.
`writer_id` is derived privately inside `grant_writer` as
`_id("writer", {line_id, attempt_id, generation})`; the review side is the same
shape at `review_cycles.py:934`, `_id("review", {checkpoint_id, attempt_id,
generation})`. I surveyed the public surface — `line_of`, `writer_of`,
`checkpoint_of`, `review_of`, `verdict_of`, `integration_checkpoint`,
`audit_checkpoint`, `line_status` — and none is keyed by attempt.
`line_status` projects only the line's state, revision and current checkpoint.

Copying either derivation into the deployment is what this record forbids, and
routing through `line["current_checkpoint_id"]` is the mutable dependency the
19:50Z review already rejected. So the approved four paths cannot obtain the
original selector through an accepted owner.

**Proposed provider gap**, for owner allocation rather than taken here: a
public reader in `worker_manager/review_cycles.py` answering the committed
grant for an attempt, in the shape the other historical readers already use —

    writer_for_attempt(store, *, attempt_id, generation)      -> writer row or None
    review_for_attempt(store, *, attempt_id, generation)      -> attachment or None

Genuine absence answers `None`; a present record must be validated and bound to
the attempt and generation exactly as `writer_of`/`review_of` bind theirs. Both
are local reads of rows that module already owns, and they make the deployment's
`based_checkpoint_id` and `attachment_id` recoverable from durable state without
a process cache, a mutable pointer or a copied identity derivation. That is
precisely what the required historical entry needs.

### What was not done, and why

Nothing was edited. The ordered ending's other halves — the W119733 intent and
settlement, the W119548 discharge through the original port, and
`end_review_from_result` replacing `deployment.verdict` — are implementable
without this selector for the ORDINARY path, but the required historical entry
in `single_worker.py` and the frozen-before-cleanup and after-later-movement
recovery controls all depend on it. Delivering the ordinary half alone would be
a second partial handback of exactly the kind this record's step 4 forbids, and
it would bake the mutable-pointer dependency into the ending's shape before the
durable selector exists.

### Verification

None run, and none needed for this claim: no candidate byte changed, and the
retained 107/456 results from W119114 claim121999 still describe these bytes.
The evidence question and budget for the implementation pass will be declared
when the selector is available.

### Next

Owner allocation of the two-reader provider gap above (or a ruling that some
existing owner supplies it that I have missed), then this leaf implements the
full ordered ending and historical entry in one pass and returns baton.bug.

## 2026-09-09 — baton.claude, claim 124551

**Claimed first**, at seq124551, before reading past the thread and before any
edit. W124331 is accepted, so the provider gap reported at claim122089 is
closed and this Work's own four paths are implementable.

### Question and budget, before running

Does the composed ending register, run, discharge, route and settle in that
order, and does it re-enter after its own cleanup without any live evidence?
Budget: the FINDING's proposed ~20s focused, then the affected sweep once.

### Delivered — the ordered ending, in four paths

**`tools/stage_execution.py`.** `StageComposition.end` is now the order and
nothing else: register the obligation, run the accepted driver, discharge the
quiescence gate the ending's own fence installed, route what the answer earned,
settle. Five is last because three and four are not the driver's — a settlement
written when the driver returned would close an obligation with the gate still
holding the Work, and the retry that is the only thing left to perform it would
go with it. A held review settles nothing: an unresolved reviewer claim is not
an ending that finished.

`end_review_from_result` replaces `deployment.verdict`. That seam took a verdict
as an operand, so the only deployment that could supply one was a deployment
deciding the review; `_no_verdict` refused honestly and made the composed review
stage unreachable, and supplying one would have been worse.

**`_prepare` recovers through W124331's accepted readers.** The first attempt at
this asked whether the RUNTIME was destroyed and then read the LINE'S CURRENT
CHECKPOINT, and both were wrong: the runtime test excluded the window this
exists for — a freeze that has happened with the cleanup still deferred — and
the line pointer is moved by every later round. `writer_for_attempt` and
`review_for_attempt` answer from the attempt and its generation, so the mutable
operands are read exactly once per attempt and a second `conclude` cannot derive
different ones. The boundary is composed only while the record is live;
`mount` now **refuses** rather than handing on the `None` the caller subscripts.

**`tools/single_worker.py`.** An attempt with a registered obligation and a
destroyed runtime goes to the composition directly, before the exchange
delivery, the mount and the credential. Its disposition and terminal come from
the recorded intent — the same operands the first pass used, so it is one ending
re-entered rather than a second composed from whatever can still be read. An
attempt with no intent is not migrated, defaulted or assumed.

**And there are no roots left to compose an adapter over**, which is measured
rather than asserted: after cleanup the attempt's home holds `credential-state`,
`credentials` and `custody` at mode 0555, and `inputs` and `workspace` are gone.
`assignment_workspace` refuses with a `PermissionError` and
`adopted_assignment_workspace` proves roots that no longer exist. The driver
types its whole adapter surface before deciding which ending it is performing,
so `_RecordedRuntime` crosses instead: the one configured custodian identity,
and every verb refusing. That makes "the adapter is not touched" a property of
the object rather than a promise about the code path.

### The three scheduled conversions, and nothing else

Owner event119712's exact three, with the class renamed to
`TheComposedHandoffCarriesItsOwnQuiescenceEvidence`: the absent-capability
assertion became exact `satisfy_gate` forwarding; the gated completed
implementation became a queued, ungated, ready Work; the refused review offer
became an ordinary tick performing `admit` and leaving the review stage
`offered`. No other assertion in either test path changed.

### Two boundaries REPORTED, not worked around

**A — a discharge receipt that can never be journalled.**
`Authority.satisfy_gate` answers `kind` with the EVIDENCE's kind
(`runtime-absent`, and it *requires* that evidence kind for a quiescence gate),
and `intake.discharge_quiescence_gate` requires that member to be the GATE kind
(`runtime-quiescence`). So the remote act commits — the gate is cleared and the
Work returns to `queued` — and the local act then refuses, `store.transact`
never runs, and `gate_discharge_of` stays `None` forever. The provider's own
step two exists for exactly this shape and its replay can never fire, because
nothing is recorded for it to replay. `intake.py` is W119548's and
`authority/core.py` is the Authority's; neither is in these four paths.
Regression: `TheDischargeReceiptIsNeverJournalled`.

**B — the boundary behind the gate.** With the gate discharged the review offer
is issued and accepted, and the reviewer's CLAIM is refused by the Authority:
`route 'baton.impl' does not resolve to 'baton.reviewer'`. A composed Job's
review stage is another assignment of the SAME Work by configuration, one Work
carries one route, and nothing in these four paths moves it — a v11 pass is the
bootstrap ending's own handoff, and the composed implementation ending publishes
a proposal and freezes a checkpoint instead. A second and separable fact: the
Authority answers `authority.errors.Refusal`, which is not a `ContractRefusal`,
so `_delegate` does not contain it and it leaves the sweep entirely. Regression:
`TheReviewStageCannotClaimTheOneWork`. Both cases are written to fail when the
owning Work lands.

### Verified

`test_stage_execution` 117 OK (93→117 methods); `test_single_worker` 103 OK
(83→94); with `test_review_driver`, `test_driver` and `test_ending`, 521 OK in
16.3s. Cumulative about 26s against the proposed 20s — the two focused runs are
9.7s and the third is the affected sweep the FINDING allows after them.
`tools/parallel_test.py` was not touched. Hashes, modes, every run, both
boundaries: `evidence/consumer-124551.json`.

### Still owed, and not claimed

W119114 keeps the full assembled lifecycle: the same submitted Job through real
review, correction, acceptance, integration and terminal handoff; the three
reconstructed-manager cutpoints; and the operator-held uncertain integration
with its retained-byte and pin checks. Boundary B stands between this component
and that proof.

### Next

Independent component acceptance at `baton.bug`, and owner disposition of A and
B.

## 2026-09-09 — baton.claude, claim 125334

**Claimed first**, at seq125334, before reading past the thread and before any
edit. All six provider gates are closed and satisfying: W124331, W124782,
W124784, W124786, W125032, W125189.

### Revalidation

- `Authority.route_fenced(expect, *, operation_id, fence_operation_id,
  from_route, to_route)` exists (core.py:1487) and is in the session's
  transition table (session.py:94). It is **not** on `AuthorityPort` — so it is
  a deployment act, reached through `_AuthoritySession` like `pass_work`.
- The committed cancellation this handoff must name is recorded on the
  checkpoint's own fence: `checkpoint["fence"]["intent"]["authority_operation_id"]`.
- The original claim route is `claimed_offers_for(control, attempt_id)`'s
  `work_route`, exactly as MINIMUM-ALLOCATION-2026-09-09.md directs, and the
  outgoing route is the worker's existing configured `review_route`.

### Question and budget, declared before any execution

How far does one submitted Job get through the ordinary lifecycle, and what is
the exact refusal at the boundary where it stops? Budget: **cumulative 40s**,
counting every iterative run — the composed fixture's own classes first, then
the two owned test modules once if the lifecycle completes. I will report the
furthest completed transition and the exact next blocker rather than component
counts, and I will stop at the budget and report rather than extend it silently.

### Furthest completed transition

**Implementation completed and discharged → Work handed off to the review
route while its gate still held → the reviewer claimed → its own container ran
a real review turn → an accepted verdict, read from the reviewer's own frozen
result → Work handed off again → the integration stage queued, offered and
CLAIMED by the integrator.**

The campaign's furthest transition had been "implementation completed, then a
wrong-route review claim" for its whole length. That boundary is cleared.

### What moved it

`route_fenced`, consumed exactly as `MINIMUM-ALLOCATION-2026-09-09.md`
directs, and **the order is the correction**: the committed route change
happens while this ending's own fence still holds the runtime gate, and only
then is the gate discharged. Discharging first returns the Work to `queued` on
the route the *finished* role is served on, which is the reclaim race the
routing record measured. This replaces owner119712's discharge-before-route
ordering for the composed fenced handoff.

Every operand comes from a committed record: the assignment as the ending was
given it, the cancellation this ending itself recorded — the checkpoint's fence
for an implementation, the verdict's `review_fence` for a review — `from_route`
from `claimed_offers_for`'s `work_route`, and `to_route` from the worker's
existing configured `review_route`. No route map, no role guess.

Three fixture facts the lifecycle needed, each a real one: one runtime identity
per started container (the overlay minted one id, so the reviewer's new
container was reported absent the moment it started); the reviewer's read-only
line composed outside a container from the boundary's own nominated source; and
the two next-role routes configured explicitly in the fixture Authority, as the
routing record directs.

### Exact next blocker

`tools/stage_execution.py:1236` — **this build holds no integration runtime
port.** `integrate_next` types one and no accepted composition in this tree
builds one over the integration delivery's namespaces; the only implementations
are focused-test doubles. The deployment reports this as itself rather than
stubbing it, and contains it to the stage: implementation and review keep their
completed state. Supplying a double here would be the helper-only success the
PLAN forbids, so it is reported. Pinned by
`test_the_integration_stage_is_held_for_want_of_a_runtime_port`.

**The smallest missing capability** is that port. It is not a local repair
inside these four paths.

### Two test dispositions, one of which the reviewer should confirm

`TheDischargeReceiptIsNeverJournalled` is **converted** to its positive:
W124782 fixed the defect it pinned, so it now asserts the receipt commits with
the evidence kind and that the settlement names it. The four recovery cases
reach their window deliberately now — `cleaned_up` withholds one discharge,
because with W124782 accepted the ordinary ending settles on its first tick and
that window no longer occurs by accident. All five long-standing failures are
gone.

**`TheWrongRouteClaimDefersInsteadOfStoppingTheSweep` and
`OneRefusedClaimLeavesEveryOtherJobAlone` are retired, and that is a judgement
worth confirming.** Both were about the composed Job's wrong-route review
claim, which this Work's handoff removes — their premise no longer occurs. The
wrong-route negative the PLAN requires to stay is preserved in
`TwoIndependentlyBoundWorkersShareOneSweep`, over a route no participant
handles, and the correctly routed positive is the new lifecycle class.
Owner124767's conversion as amended by owner124970 is what I read as
authorizing this; if that authority is meant more narrowly, the prior bytes are
in this claim's diff and in `findings/finding-concrete-claim-adapter/evidence/`.

### Verified

Both owned modules together: **247 tests, OK, 11.0s**, with no failure left —
including the five that had stood since W124782 landed. The new lifecycle class
is 6 OK. Test methods 93→128 and 83→110.

**Budget: about 85s against the 40s I declared.** The lifecycle advanced
through five successive boundaries, each found by a sub-second probe; the cost
was five full two-module runs at ~12s, and one of those was spent finding and
repairing a splicing error of my own that briefly duplicated two classes.
Recorded, not presented as met.

Hashes, modes, every change, both dispositions and every run:
`evidence/consumer-125334.json`.

### Next

Independent component acceptance at `baton.bug`. This component has not run the
committed-handoff restart proof; it stops at the integration runtime port
above, and W119114 keeps the full lifecycle and custody acceptance.

## 2026-09-09 — baton.claude, claim 125449 (correction)

**Claimed first**, at seq125449, before reading the review and before any edit.

I accept all four findings. Finding 3 is a straight error on my part: I
reported an absent provider that exists and is accepted, and the None guard I
quoted is stale rather than authoritative. Finding 4 is also mine: the PLAN
says preserve those assertions and I retired two classes on my own reading of a
conversion authority that does not cover them.

### Focused question and budget, declared before any execution

Does one ordinary submitted Job carry a changes-requested review to the
producer's own route, open its correction, come back accepted, and reach the
integration port — with the discharge receipt required before any ending is
acknowledged?

Budget: **the existing 20s cumulative**, not a self-declared figure. I will
develop against focused classes and spend at most one full two-module run, and
I will stop and report at 20s rather than extend it.

### All four findings corrected

**[1] A correction is not forward.** `_handed_off` used the ending worker's
outgoing route for every answer, so a changes-requested review sent the Work to
`integration` and the correction round's implementation claim refused there.
`_next_route` now derives a correction's target from the reviewed checkpoint's
own producer — the checkpoint names its writer, the writer names its attempt,
and `claimed_offers_for` answers that attempt's one committed claim route. The
forward direction stays the worker's configured `review_route`. Driven: the
same submitted Job goes changes-requested, routes back, and its correction
round claims and runs a third container on the same persistent line.

**[2] Owedness is a fact about what this ending fenced.** It was decided from
today's Work projection, which is exactly wrong for the case it must answer:
when the remote discharge committed and its local answer was lost, the gate is
already gone, so nothing looked owed and the ending settled carrying no
reference to the act that cleared it. `_fenced_gate` now reads the gate this
ending's **own** fence installed — committed, and it cannot disappear — and
`_finished` **refuses to settle** while no committed receipt exists. The
accepted provider's stable remote replay is what obtains it.

**[3] My report of an absent provider was wrong.** W110774's
`IntegrationRuntimePort` exists and is accepted, and the None guard I quoted is
stale. It composes from this deployment's own operands and is now wired through
the existing `integration_port` seam; the integration stage reaches it. Two
operands do not exist before acceptance — the accepted line and its published
proposal — so the port is composed after it and handed to a second serving
object over the same durable stores. One fixture deployment operand changed:
the composed integrator declares the credential slot the accepted port reads
its bearer from, because it refuses another.

**[4] The two classes are restored**, with their expected behaviour unchanged
and their precondition made deliberate: `wrong_route` withholds the
implementation handoff, so the Work stays on the implementation route and the
reviewer's claim meets the state these negatives are about — the same shape as
the deliberate pending-ending window the previous pass added for W124782's fix.
Retiring them was not mine to do; the PLAN preserves them explicitly and the
two-Job test does not carry that authority.

### Verified

`test_stage_execution` **140 OK**; `test_single_worker` **119 OK**. Run
separately rather than as a pair.

**Budget: 26.8s against the existing 20s.** Development used focused classes
and sub-second probes only. I was already marginally over at 22.9s after the
first verification run, and then spent 3.7s on `test_single_worker` because
`tools/single_worker.py` changed this pass and its module had not been re-run —
I judged an unverified source change worse than the overrun. Recorded as an
overrun, not presented as met.

Hashes, modes, all four corrections and every run:
`evidence/consumer-125449.json`.

### Next

Independent acceptance at `baton.bug`. The component's committed-handoff
restart proof is still owed, and W119114 keeps the full lifecycle and custody
acceptance. The integration stage now reaches the accepted port; what that port
then answers is its own accepted contract's business and this Work does not
claim it.

## 2026-09-09 — baton.tuner, claim125537

Accepted the bounded fixture/proof takeover in review05:47Z. Only
`tests/tools/test_stage_execution.py` and this record's progress/evidence are
editable; reviewed production bytes are retained. The ordinary lifecycle runs
first, followed by the committed-handoff reconstructed-manager cut. Baselines,
operational lookup findings and the enforced cumulative20s verification plan
are in `evidence/takeover-125537/EXECUTION.md`.

Fixture takeover now reaches an actual successful integration worker result
after correction and accepted second review. Ordinary scheduling then stalls:
three quiescent ticks dispatch to a nonexistent exchange, never invoking the
integration completion consumer. The stage remains starting, entry leased and
Work held by its integrator. Source correction is outside this test-only claim;
returning to baton.bug for a bounded allocation. Exact transition, proposed
consumer path and independent handoff evidence:
`evidence/takeover-125537/FINDING.md` and `probe.json`.

Only additive `OrdinaryTerminalLifecycle` changed in the stage test; all
existing test bytes/AST, both production paths, the single-worker test and
their modes match intake (`final.json`, retained candidate and patch). The
positive selector remains failing at the real scheduling blocker. Ten
test/probe processes used8.7703s/20s; logs include all intermediate fixture
failures. Ordinary terminal completion and the dependent reconstructed-manager
cut remain unproved; no broader suite or recovery expansion was run. Current
state: awaiting independent review/source allocation, not signed off.

## 2026-09-09 — baton.tuner, claim126729

Revalidated owner126545 allocation, provider126698 acceptance and OBSERVATION.md
revision1. Consumer preflight found no supported read-only opener for the
Authority/coordinator handles absent from the observation factory. Public
openers can initialize schema/set persistent journal state; the disposable
probe confirms coordinator creation and Authority refusal in a read-only
directory. Exact source evidence, probe limitations and proposed bounded
provider paths are in `evidence/consumer-126729/FINDING.md`.

Returning to baton.bug to resolve that capability boundary before changing an
excluded provider path. All four consumer and seven accepted provider paths
remain byte/mode-identical (`final.json` and retained `unchanged/`). Three
public-API probe processes used0.464414s/20s, including the corrected clock
operand;19.535586s remains for this consumer piece. No source/test change,
lifecycle advancement, suite rerun or restart proof is claimed. Ordinary
terminal completion still precedes the narrowed reconstructed-manager cut.

## 2026-09-09 — baton.tuner, claim126807

Ordinary serving now consumes the accepted integration observation and completes
the same Job through correction, accepted review, actual integration, owned
receipt/lease release and exact generation5 terminal pass to configured rview.
All three stages project completed. The actual close/reopen manager cut after
committed handoff before local acknowledgement also passes, preserving the
checkpoint/publication/handoff without another start.

Running-worker exclusion, foreign receipt/lease refusal, lost-pass replay across
a later assignment, serving reads without acts and actual uncertain-effect hold
pass.21 distinct focused controls passed; cumulative8.876301s/20s includes prior
claim126729, leaving11.123699s for this consumer piece. One new assertion's claim
response shape was corrected and rerun. No full/provider suite rerun.

Returning the two-path candidate for independent review. Exact hashes, retained
bytes/diffs, public terminal documents, commands and test limitations are in
`evidence/consumer-126807/RESULT.md` and `final.json`. All other reserved/provider
paths and existing tests outside OrdinaryTerminalLifecycle are unchanged.
Separate-process read-only factory consumption remains pending the approved
opener providers; this is ordinary-path progress, not final W122060 or W119114
acceptance. The accepted recovery scope remains unchanged.

## 2026-09-09 — baton.tuner, claim128375

Joined the accepted read-only openers into StageObservation, using the configured
Authority UUID and the same owned completion reader as serving. Reader handles
are local to each call and disposed on success/refusal; non-integration behavior
and the accepted ordinary path remain unchanged.

A fresh process after serving shutdown proves exact committed completion,
missing-handoff owedness, foreign/missing evidence refusal, no serving acts,
balanced handle disposal and unchanged database bytes/modes. The three existing
observation controls also pass. Cumulative10.323860s/20s leaves9.676140s; no
provider/full-suite rerun. Reuse the accepted ordinary and reconstruction proof.

Returning for independent full W122060 acceptance. Exact two-path hashes,
retained candidates/patches,16-path audit, fresh-process evidence and commands:
`evidence/consumer-128375/RESULT.md` and `final.json`. All existing test meanings
and other accepted paths are preserved. No known consumer implementation blocker
remains; W119114 still owns final lifecycle/custody acceptance.
