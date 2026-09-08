# Progress

Not started.

## 2026-09-07 — baton.claude — the serving path, actually connected

Reclaimed after `review-2026-09-07T13-29-13Z.md`. All three findings reproduced
before I changed anything and all three were real. State: **awaiting
independent review of the corrected serving path**; the composed one-Job
lifecycle is the next checkpoint and is not claimed here.

### P1 — the drivers are what the loop now reaches

The review is exactly right about what was wrong, and the shape of the defect
is worth stating plainly: I had composed every operand of a stage deployment
and connected none of them. `StageExecution.__getattr__` delegated the whole
serving surface to `PooledManagerOperations`, whose `launch` and `conclude`
forward to the bootstrap worker's own callbacks -- so `_matches` refused every
kind but `implementation`, the v11 pass ended every attempt, and the
publication seam and integration profile were attributes nothing read.

**The correction is two seams in `single_worker` and three compositions over
them.** What a worker MOUNTS and how its attempt ENDS are the whole of the
difference between the three stages: the offer, the claim, the attempt record,
the assignment activation, the input root, the retained manifest, the launch
document, the credential delivery, the pre-start boundary re-proof, the runtime
start and the command are identical for all three. So `_prepared` and `ending`
call `_mounted` and `stage.end`, and everything between them is the accepted
composition, called once. `stage=None` is the bootstrap deployment, unchanged
in every respect -- its 92 tests pass untouched, which is the proof of that
sentence rather than a claim about it.

`_held` gained a `roles` operand defaulting to `("implementation",)`, so
`operations_from`, `factory` and `observation_from` refuse `review` and
`integration` exactly as they always did, and the widening happens at the ONE
call site that owns the three-role composition. `_matches` reads its kind from
`launch_role`, which for a bootstrap deployment is the same literal it used to
compare against.

`StageComposition.mount` calls `prepare_implementation` or `prepare_review` and
returns the boundary the accepted provider composed -- the line mounted
writable behind its grant, or the frozen checkpoint read-only beside the
reviewer's own output. `StageComposition.end` calls `end_implementation` with
the factory's publication seam, or `end_review` and then `open_correction` on
its answer. `held` is returned exactly as it arrived.

**The based checkpoint is the line's current one, whatever it is,** and that is
what makes the grant replay across the launch tick and the ending tick without
this deployment deciding which round it is: on the first round the line is
`idle` and holds none, on every later round it holds the rejected checkpoint,
and `grant_writer` is what refuses either at the wrong time.

**Pool activation was missing and is the reason the composition could not have
run at all.** `PooledManagerOperations` refuses unless it is handed exactly the
store's own configured `(generation, worker id)` pairs, so a deployment that
never activated a pool could only attach to one an operator had activated by
hand -- which is the ordinary operator transition this assembly exists to
remove. The configuration IS the pool document now, and a store whose active
generation is not the configured one refuses rather than serving under a
generation nobody configured.

### P1 — the sessions are minted rather than omitted

Nothing was missing except a way to get them. Three receipt participants are
configured; the other two are DERIVED and deliberately not, because configuring
them would be configuring a value that can only be right by accident: the
integrator is the integration profile's own participant, which `admit_accepted`
compares against the session it is handed, and the publisher is the
implementation worker's participant, because `Authority.publish` takes the
producer's live assignment as its compare-and-swap operand and a session
refuses to act on one naming somebody else. `factory` mints all five from the
Authority it opened and proves them through `_sessions` before the integration
store is opened.

A mint rather than an operand because a deployment document carrying session
material would be carrying capability bytes, which the secret sweep exists to
refuse.

### P2 — the observation factory

`StageObservation` composes the accepted `_Observation` per worker and adds the
one thing a pool changes about observing: which worker holds a stage is the
scheduler's own recorded allocation, and a stage with no allocation is answered
by no worker rather than by whichever one sorts first. It opens no Authority,
mints no session, activates no pool, allocates no workspace and refreshes no
runtime. `tools.job_manager._exchange_read` accepts it, which the cases assert
against the real loader rather than against a copy of its rule.

### Two defects the real composition found

Neither was reachable while the object was never asked to serve.

`IntegrationStore.open` takes an incarnation and a clock and was being called
with neither. Both are now the ones driving this run -- the incarnation the
operator opened the control store under, and the caller's clock -- because a
coordinator opened under a name no other store in this process shares makes its
recovery evidence uncorrelatable with the manager's own.

`held_configuration` REWROTE its caller's document: `_document` answers the
operand itself, and the workers member was replaced in place with the owned
forms. The observation surface reads the original for exactly that reason, so
it was refused by the accepted reader for carrying derived members. Owned as a
copy now.

### Two exact missing public capabilities, reported rather than bridged

Both are the same shape as the absent retained proposal manifest this leaf
already reported once, which became W103874.

**The reviewer's verdict has no channel out of its container.** `end_review`
takes the manager's `disposition` -- what the review ATTEMPT ended as -- and
the reviewer's `verdict` about the checkpoint as two separate facts, and it is
right to: a crashed reviewer must not become a rejection. But the exchange
terminal's ten members are all the manager's own vocabulary and none is the
reviewer's, and the frozen review result that COULD carry a namespaced worker
claim is retained inside the ending three steps after the operand is needed. A
deployment that froze first to read it would be performing the driver's own
ordered step out of order. `_no_verdict` refuses and says so; the lifecycle
proof will supply one explicitly and name it as a fixture standing in for the
missing capability rather than evidence that a reviewer decided anything.

**No accepted composition builds an integration runtime port.**
`execution.integrate_next` types the port and calls `port.run(delivery,
assignment)`; the only implementations in this tree are focused-test fixtures.
Every other operand of `admit_accepted` is composed from durable state --
`integration_checkpoint` answers the accepted checkpoint, the checkpoint names
its writer, the writer names its attempt, and `retain_proposal` replays that
attempt's retained manifest to give the published proposal's identity, so an
integration reached after a restart names the same proposal the ending
published. Only the port is absent. `Integration.run` refuses it as
`refused/capability` and the refusal is contained to that stage, so the
implementation and review stages of every Job go on running.

### One narrow window, named rather than left implicit

An implementation ending that has already frozen its checkpoint cannot
recompose its writable line mount: `writer_boundary` requires the writer
active, and `freeze_checkpoint` fences it. So a crash between the freeze and
`authorize_cleanup` cannot be re-entered through this composition. This is a
property of the accepted boundary rather than of this leaf -- there is no
public reader answering which writer a line currently holds, which is what a
re-entry would need -- and it is reported here rather than worked around.

### Verification

`tests.tools.test_stage_execution` is 59 tests, all passing. `tests/tools` is
715 with the one pre-existing registry error naming only the two untracked
baseline modules, `tests.integration.test_driver` and
`tests.job_manager.test_review_driver`; that is the same condition as the
previous checkpoint and belongs to the accepted driver leaves' landings.
`tests/job_manager` is 390, all passing. `tests/tools/test_single_worker.py` is
untouched and its 92 tests pass unchanged, which is what proves the
parameterization preserved bootstrap behaviour.

Four of the five owned paths changed; `tools/parallel_test.py` needed no
addition, because this leaf's one registry entry was already made.

| Path | SHA-256 |
| --- | --- |
| `tools/stage_execution.py` | `e8f83395e121fc4c2e95352a04cbcb20eb729adfd20d7fb811e9f3c149b2bcd9` |
| `tools/single_worker.py` | `6e1c4d58d2360c6091327bd9c9f90cf58cdb60d5450554ae98d9280b1ca15ad8` |
| `tests/tools/test_stage_execution.py` | `2b8a3bda6fc646930a0e98d3f878184754c1f150091b8b4e80a7a22c96f9d88b` |
| `tests/tools/test_single_worker.py` | `95808aee8529d27bab0519f3fe8d45ae4e51507594c4825495530a8882d9af6c` |
| `tools/parallel_test.py` | `eb90384d91cb5a4afe22bc147b8113863c8cf039eb5efbcae7ed4f614870ab9e` |

### What this checkpoint does not claim

The composed one-Job lifecycle is NOT run here. No Job has been driven through
implementation, review, correction, acceptance, integration and terminal
handoff by this factory; the restart cutpoint is not reconstructed from durable
state; and no operator-held uncertain integration has been exercised. Those are
the next checkpoint and the two capabilities above are what a fixture must
stand in for to reach them. The historical helper-level evidence in the
checkpoints below remains what it always was -- partial -- and the review is
right that it is not the composed lifecycle.


## 2026-09-06 — baton.claude — the interface gate, run and reported

Claimed W103083 and ran PLAN item 1 against the tree. Both driver leaves are
closed satisfying and their public surfaces are exactly what the plan assumed.
No shared file has been touched: `tools/stage_execution.py` does not exist,
`single_worker.py` and `parallel_test.py` are unchanged by me this round.

One material gap stops item 2, and it is in FINDING with its evidence: this
build cannot retain a `proposalManifest`, and `driver.publish_candidate`
selects on one. `request_freeze` retains only the sealed result manifest;
`retain_manifest`'s two callers both retain `inputManifest`; `proposal.publish`
is in the protocol vocabulary and appears nowhere in `worker_manager` or
`tools`; and no accepted operation answers a collected artifact's bytes.

I did not bridge it. A deployment that built the proposal document itself would
be making the claim the WORKER is supposed to make -- the same class of defect
as a core inventing its own verification -- and this leaf's own boundary says
it composes accepted interfaces rather than redesigning them.

Recommended: new Work under the parent for the `proposal.publish` control act,
after which this assembly proceeds unchanged. The smaller seam mismatch between
W103076's `publish(...)` and W103077's `publish_candidate(...)` is ordinary
adapter work and is not a blocker.

## 2026-09-07 — baton.claude — checkpoint 1: the serving factory is wired

All four blockers are closed satisfying — W103076, W103077, W103874 and
W105706 — so the interface gap that stopped item 2 in the entry above is gone
and the assembly proceeds as that entry predicted, unchanged.

**Inventory first, as the ruling requires.** Of the five owned paths,
`tools/stage_execution.py` and `tests/tools/test_stage_execution.py` did not
exist; `single_worker.py`, `test_single_worker.py` and `parallel_test.py` were
at their accepted baseline. Nothing outside the five was written.

Four are touched by this checkpoint. `test_single_worker.py` deliberately is
NOT — its 92 tests still pass unchanged, and that is the proof that
parameterizing `single_worker` preserved its behaviour rather than an
assertion that it did.

**The parameterization, and where it splits.** `single_worker.operations_from`
is now two exported halves with the same body in the same order:
`worker_preflight` is everything the engine, image, network and workspace group
can refuse — it runs before an Authority is opened, so a misconfigured pool
refuses with no handle to release — and `worker_operations` is the half that
needs an Authority, over one the CALLER owns. The seam that makes it reusable
is `dispose`: a single-worker deployment hands its own `authority.dispose`
because nobody else holds that handle, and a pooled composer hands something
that does not, because one shared Authority released by the first worker torn
down would take the other two with it.

That split is why this is not a second `single_worker`. Copying it for
reviewers and integrators would have put three deployment opinions over one
security boundary — three places to keep a credential rule, a mount posture and
an Authority comparison true — which is exactly what the assembly boundary
forbids.

**What the factory refuses before anything is opened**, each with a case:

- another generation of the closed document, an unknown or missing member, and
  a pool generation that does not count from one;
- credential bytes anywhere in the document, walked rather than spot-checked,
  because the member that matters is whichever one somebody added last. The
  sweep runs FIRST, which is the contracts layer's own rule: a document
  carrying a bearer is refused as THAT rather than as whatever structural
  fault is also in it, since the two answers send a caller to different places;
- a review stage naming another Work than the implementation stage;
- a participant or principal shared between implementation and review. The
  rule is named for the pair that needs it: an integrator sharing an identity
  is a deployment choice, and this leaf does not invent a rule for it;
- a missing role, two workers for one role, a role this deployment has no
  driver for, and a worker naming another Authority — that last compared
  BEFORE the launch validator, so it is refused as itself rather than through
  whichever of `_held`'s rules the mismatch happens to break first;
- mutable state inside the checkout, applied to the integration store, the
  state root and every worker's workspace, launch and credential home;
- and a missing receipt or integration capability, proved before publication
  because `integration.driver` reaches all four AFTER a proposal is on the
  Authority — a deployment discovering one there has already published
  somebody's candidate.

**Construction failure releases what it opened**, through the same `release`
the serving loop calls: handles close in reverse order, a partial construction
closes only what exists, and one failing close never stops the rest.

**Registry.** `tests.tools.test_stage_execution` is registered in
PARALLEL_MODULES, not serial: it owns no engine — it proves the configuration
boundary and the release path and starts nothing. `test_parallel_runner`'s
registry check now names only the two pre-existing untracked baseline modules
(`tests.integration.test_driver`, `tests.job_manager.test_review_driver`),
which is the failure already recorded in the custody dossier and not this
leaf's.

**Verification.** `tests.tools.test_stage_execution` 30 tests passing;
`tests.tools.test_single_worker` 92 passing unchanged; the whole `tests/tools`
package 686 tests with the one pre-existing registry error above.

Candidate digests:

| Path | SHA-256 |
| --- | --- |
| `tools/stage_execution.py` | `e4d7bdbde18e6850543f60da8a0df7b9a37e6a3f726b362a811fd58580e9e03d` |
| `tools/single_worker.py` | `2f5d7d57178f356257733eb3668cb52435440b3e843578435d9409795e8d16ca` |
| `tests/tools/test_stage_execution.py` | `94773370596b0ee781986de80cd6207c88e3f89caab042fa67ce1678da7f3907` |
| `tools/parallel_test.py` | `eb90384d91cb5a4afe22bc147b8113863c8cf039eb5efbcae7ed4f614870ab9e` |

**What this checkpoint does not claim.** No composed lifecycle has run: item 3
is the next checkpoint and item 4 the one after. The factory is wired and its
boundary is proved; a Job has not been driven through implementation, review,
correction, acceptance, integration and handoff, and this candidate says
nothing about that until it has.

## 2026-09-07 — baton.claude — checkpoint 1 completed: the drivers are wrapped

The previous entry stopped one step short of the assembly boundary's own
sentence. It says: build all required worker operations, wrap them with
`PooledManagerOperations`, THEN wrap that with the two accepted stage drivers.
I had done the first two and published the checkpoint on them. The third is
here, and it is the seam W103874 was built for.

`Publication` is what `review_driver.end_implementation` calls, and it is two
accepted operations rather than one act this module invents. `retain_proposal`
composes the manifest from the frozen result and the worker's own claim and
answers its retained digest; `publish_candidate` takes that digest as a
SELECTOR and re-reads every publication member out of the retained document
before calling the Authority. No publication member is supplied from this
deployment's configuration — if one were, the deployment would be asserting
something the frozen result is supposed to prove. The ordering that puts this
before the writer is fenced belongs to the ending; this object only has to not
get in the way of it.

`integration_profile` is composed from the document for the integration driver,
and both driver-facing members are on the composed object rather than rebuilt
at each call site.

**One more session is required, and it is not a receipt.** Publication happens
while the producer assignment is still live, BEFORE the checkpoint fences it,
so the publisher session is reached earlier than any of the four receipt
sessions. Its three capabilities are named individually — `retain_proposal`
reads the canonical target and `publish_candidate` performs the act and reads
back what the Authority recorded — because a deployment missing one would
discover it with a frozen result it can never publish. A composition given no
sessions carries no publication seam at all, which is what an observation-only
status surface must not hold.

**Verification.** `tests.tools.test_stage_execution` is now 35 tests, all
passing; `tests.tools.test_single_worker` is 92, still passing unchanged. The
five new cases cover the retained digest being what publication selects on,
the seam recording what it published without inventing a member, a producer
refusal stopping before the Authority is asked, the integration profile coming
from the document, and a session-less composition carrying no publication.

Candidate digests for the two paths this entry changed:

| Path | SHA-256 |
| --- | --- |
| `tools/stage_execution.py` | `5f5327370f0e6ba179548e45ccf5dbfbc763d8b78e4b95b379950ba739a0b0f1` |
| `tests/tools/test_stage_execution.py` | `6330279198dc8619c1a44e00cc4a087f1b8250e718dbfcec564e63420e8645bb` |

`tools/single_worker.py` and `tools/parallel_test.py` are unchanged from the
previous entry's digests, and `tests/tools/test_single_worker.py` remains
untouched.

**Still not claimed.** No composed lifecycle has run. The factory is wired,
its configuration boundary is proved, construction failure releases what it
opened, and the two drivers now have their seams — but no Job has been driven
through implementation, review, correction, acceptance, integration and
handoff. That is item 3 and it is the next checkpoint; item 4's focused
restart, role and configuration checks follow it.

## 2026-09-07 — baton.claude — checkpoint 2: one Job runs the composed lifecycle

Item 3, in the one test file this leaf owns. One path changed —
`tests/tools/test_stage_execution.py`
(`5fc74680ebdb448cb7f9967824f564cc9a855f4a659eb4396b814557dbe5952b`);
`tools/stage_execution.py` is unchanged from checkpoint 1 at
`5f5327370f0e6ba179548e45ccf5dbfbc763d8b78e4b95b379950ba739a0b0f1`.

**What runs.** One Job through implementation, a real publication, an
immutable checkpoint, an independent review, a `changes-requested` verdict,
the Job-store correction advance, a second round on the SAME line, and an
accepted verdict that `integration_checkpoint` then answers as the one an
integration would admit. Round two's writer can only attach by naming round
one's checkpoint — `grant_writer` refuses any other — which is what makes it
the same private history rather than a second line.

**What is real, because that is the whole question a composed proof answers.**
The control store, the Job store and the development line; the accepted
operations `prepare_implementation`, `freeze_checkpoint`, `prepare_review`,
`record_verdict` and `open_correction` against them; a result manifest per
round that is REALLY RETAINED and read back through `load_manifest`; and the
publication seam is the factory's own `Publication` calling the real
`retain_proposal` and `publish_candidate`. That is what the ruling means by
the real retained-manifest producer rather than a mock supplying the missing
document — one case loads each round's proposal manifest back out of the store
and checks it binds the frozen result and carries the worker's declared base.

**What stands in, named rather than implied.** The freeze, intake, retention
and cleanup OPERATIONS are not performed: they need an engine, a delivered
workspace and a custody tree, which is the live proof's half and not this
leaf's. The frozen RESULT they would name is real and retained, so the
producer composes over durable state. The Authority is a fake that derives its
answer from the operands it was sent, which is what makes `publish_candidate`'s
own equality check meaningful over a manifest the real producer composed.

**Two fixture facts worth recording, because both cost a debugging round.**
§12 rule 1 makes a Work id carry its Authority's eight-character prefix, and
the shared job-manager fixture's pair was written for a path that never
validates a manifest — so this case uses one manifest-valid pair for the line
and every attempt. And `advance_correction` cross-binds the recorded verdict
against the Job's own Authority and Work, so the Job store is rebound to the
same Authority as the line; two stores bound to two Authorities is exactly the
mismatch it exists to refuse.

**Ordering is driven, not asserted in prose.** One case wraps the seam and
records the line's state at the moment publication is asked: it is `writing`,
so the producer assignment is still live and the checkpoint has not fenced it.
That is W103068's measured ordering, re-proved through this factory's seam.

**Verification.** `tests.tools.test_stage_execution` is 38 tests passing;
`tests/tools` is 694 with the one pre-existing registry error naming only the
two untracked baseline modules; `tests/job_manager` is 390 passing.

**Still not claimed.** Item 4's focused checks — one representative
restart/replay cutpoint, role/session separation, pre-launch configuration
refusal, observation-only status and preserved operator-held uncertainty — are
the next checkpoint. And no accepted integration has been driven: this proves
the lifecycle up to the accepted checkpoint an integration would admit, not
the integration itself.

## 2026-09-07 — baton.claude — checkpoint 3: item 4's focused checks

One path changed, `tests/tools/test_stage_execution.py`
(`190bbe8d2baa542fdc9d23d6f8d5c1ce7fb478984bf7be70ee15bdca511fc290`).
`tools/stage_execution.py` is still checkpoint 1's
`5f5327370f0e6ba179548e45ccf5dbfbc763d8b78e4b95b379950ba739a0b0f1`.

The lifecycle harness is now a base class the item-3 and item-4 cases both
inherit, so the composed rounds are built once and the focused checks do not
re-run item 3's assertions to reach them.

**The restart/replay cutpoint is publication**, because it is the one act that
reaches OUTSIDE this deployment. A manager that died after the Authority
recorded a proposal and before it wrote anything of its own must arrive at the
same proposal on the next incarnation, not a second one. The case composes a
FRESH seam over the same store — exactly as a new incarnation would, with no
memory of the first — publishes again, and proves the answer is identical, the
retained digest is the same, and the manifests table gained no row. Retention
is keyed by the digest of the bytes, so that is what makes the guarantee real
rather than a journal lookup.

**Role separation is refused twice, and the two are different questions.** The
configuration refuses a shared identity before anything is opened; but if that
were the only thing standing between a Job and a self-review, a deployment
assembled another way would have nothing. So the case drives `prepare_review`
with the writer's own attempt against the real frozen checkpoint and proves
`attach_review` refuses it there too, against the checkpoint's own recorded
writer.

**Operator-held uncertainty is preserved rather than resolved.** A `rejected`
verdict produces a `held` outcome, and `open_correction` refuses anything that
is not a correction — which is what keeps a held outcome from being quietly
turned into another round by a caller that wanted one.

**Pre-launch refusal is asked as "what exists on disk afterwards."** A composer
that refused only after opening its Authority would leave a lock nobody holds a
reference to, and its message would describe the wrong moment. Two cases refuse
`operations_from` — once on a document fault, once on a Job store bound to
another Authority — and then assert the integration store file was never
created.

**Observation-only status** is checkpoint 1's case: a composition given no
sessions carries no publication seam at all, which is exactly what a status
surface must not hold.

**Verification.** `tests.tools.test_stage_execution` is 45 tests passing;
`tests/tools` is 701 with the one pre-existing registry error naming only the
two untracked baseline modules.

**What the three checkpoints together do and do not establish.** The factory is
wired and its configuration boundary is proved; the two accepted drivers have
their seams; one Job runs implementation, real publication, checkpoint,
independent review, correction and acceptance over real stores with the real
retained-manifest producer; and item 4's five focused checks hold. Not
established: an accepted integration has never been driven — the lifecycle
stops at the checkpoint `integration_checkpoint` answers — and the
runtime-facing freeze, intake, retention and cleanup operations still stand in,
because they need an engine, a delivered workspace and a custody tree that
belong to the live proof. Item 5 is independent review.


## 2026-09-07 — baton.claude — the two ordering defects, corrected

Reclaimed after `review-2026-09-07T14-12-42Z.md`. Both P1s reproduced before
anything was changed and both were real. State: **awaiting independent review
of the corrected configuration boundary**. The complete one-Job lifecycle,
the reconstructed-manager restart and the operator-held uncertain integration
are NOT delivered here and are gated on two absent providers; the last section
says exactly what that gate is.

### P1 — a callable method was never evidence of authority

The review is exactly right, and the shape of the defect is worth stating
plainly: `_sessions` asked whether each session object had a callable method of
the right name, and `session.py` installs the WHOLE transition table on the
class — so every minted session answers every one of those names, whoever it
was minted for. The gate this module advertised as "every receipt capability,
proved before publication" could not fail for a reason anybody cared about. The
probe's `baton.not-configured` composed a serving object whose own Authority
answered `holds_capability(actor, "approve")` false.

**Two questions, asked separately, because they are two questions.** The shape
check stays and is no longer worded as a capability: it proves the object is
the runtime face this deployment mints, which is worth refusing as itself
rather than through an attribute error three steps on. The authorization is
`holds_capability` through the accepted Authority reader, and the four grants
are the Authority's own words — `verify`, `review`, `approve`, `integrate` —
in `RECEIPT_CAPABILITIES` rather than derived from a session method name.

**The scope is the Work's, not the deployment's, and that is the whole reason
it is read rather than defaulted.** `_write_receipt` derives its scope from the
Work the proposal belongs to precisely so a grant cannot widen on the way to a
receipt. A configuration proved against `scope:deployment` would therefore
accept an actor whose grant does not reach this Job and refuse one granted
exactly here — the same P0 the Authority corrected in `_require_capability`,
arriving one layer up through a default. `_work_scope` reads it from
`project_work(job_work_id)` once, before anything durable happens.

**The publisher is deliberately not authorized here, and that is not an
omission.** `Authority.publish` takes the producer's LIVE ASSIGNMENT as its
compare-and-swap operand rather than a grant, so there is no grant to prove and
checking for one would be asserting a rule the Authority does not keep. Its
identity is still proved: it is derived from the implementation worker and the
mint refuses a malformed one. No capability is granted anywhere in this module.

### P1 — a refusal that had already written something

`worker_preflight` is not read-only. It configures the control store's
workspace group and storage, certifies a runtime profile and constructs a
credential home — and it ran FIRST, on the reading that "the half before the
Authority" was the cheap half. So a malformed receipt participant, a fault
this module can see in the document it was handed, refused only after
configuring a control store that had never been configured; and a configuration
naming pool generation 4 refused only after ACTIVATING generation 1, having
changed the very thing it then said it would not serve.

**The order is now the contract and the line is drawn in one place.**
Everything whose answer this module can know without writing anything happens
first, uninterrupted: the closed document and its paths; the Job store's
Authority binding; the checkpoint profile; each worker participant's principal,
resolved from the Authority and compared against its configured one; the five
sessions, minted and authorized; and the pool generation the next activation
WOULD answer. Only then the three preflights, the integration store, the
workers' operations and the activation.

Opening the Authority is deliberately on the early side of that line. It is a
handle over a store that must already exist, it writes nothing, and it is the
only way to ask the identity and capability questions at all — a composer that
refused a bad grant without opening one would be refusing on something other
than the Authority's answer.

**The pool generation is predicted from the store rather than read back from
the act.** `_pool_generation` reads the scheduler's own rule out of durable
state — no pool means the next activation mints generation 1, the active
generation's digest matching this document means a revalidation of it, and
anything else is the next generation — and refuses before `activate_pool` is
called. The post-activation comparison is KEPT: it is the accepted operation's
own answer, so a prediction that ever drifts from the scheduler's rule is
caught rather than trusted.

**The raw `Refusal` no longer escapes.** `_authority_read` answers every
Authority read in this boundary's own vocabulary, keeping the Authority's exact
words as the reason. A configuration fault arriving as another package's
exception type is one the serving loop cannot classify at all.

**Nothing is repaired and nothing is rolled back.** A refusal leaves whatever
another actor put in these stores exactly as it found it; this module unwinds
only the handles it opened itself, through the same `release` it always did.

### What the regressions assert, and why it is not "construction raised"

The old ordering DID raise. So each new case reads the durable state back
through the owner that would answer it in production: the workspace group
through the Worker Manager's own `configured_workspace_group`, the pool through
`scheduler.active_generation` and `pool_workers`, and the integration store
through the filesystem, because a store that was never opened has no reader.

Four negatives and two positives, all over a REAL Authority with real grants —
a fake that answered a capability would prove only that the suite agrees with
itself. An actor holding no grant; a grant held in `scope:elsewhere`, which is
the case that shows why the scope is read from the Work; a malformed actor,
which is the escaped-`Refusal` half; and a worker participant resolving to
another principal. Each asserts the refusal AND that the control store, the
pool and the integration store were untouched. The positives ask the Authority
the composition itself opened whether each configured actor really holds its
grant in the Work's scope.

`ThePublicFactoryComposesThroughItsOwnEntryPoint` runs the exported `factory` —
`module:attribute` with two operands and nothing else, which is what
`tools.job_manager` calls and what no case had run. Two substitutions are named
in the case: this suite's engine, and `_checkout`, because the disk-backed root
must live inside the distribution and the real answer would refuse it for the
fixture's reason rather than the one under test.

The shape half of the session gate keeps every assertion it had; its helper
gained an authority operand and one case that reads the four
(participant, capability, scope) triples off the gate rather than off the
constant. The ServingCase fixture now grants the four capabilities in the
Work's own scope — it previously needed none, which is itself the measure of
what the old gate asked.

### One thing considered and deliberately NOT done

`policy_generation` is a configured member and `admit_accepted` passes it to
`approve`, which validates only that it is a positive integer and binds it to
the receipt. The Authority does not compare it against `policy_generation()`,
and a composition that refused on inequality would be enforcing a rule the
Authority does not keep — the same error as granting a missing capability in
the factory. Reported here for the reviewer to rule on rather than decided.

### Verification

Focused: `tests.tools.test_stage_execution` is 69 tests, all passing — 59
before, plus the ten this correction adds. `tests/tools/test_single_worker.py`
is UNTOUCHED and its 92 tests pass unchanged, which is the proof that the
reordering preserved bootstrap behaviour rather than a claim about it.

Broad: `tests/job_manager` is 390, all passing. `tests/tools` is 725 with the
one pre-existing registry error naming only the two untracked baseline modules
`tests.integration.test_driver` and `tests.job_manager.test_review_driver` --
the same condition as the previous checkpoint, and 715 + the ten added here.

Commands, from `v12/python`:

    PYTHONPATH=src:. python3 -m unittest tests.tools.test_stage_execution -q
    PYTHONPATH=src:. python3 -m unittest tests.tools.test_single_worker -q
    PYTHONPATH=src:. python3 -m unittest discover -s tests/job_manager -t . -q
    PYTHONPATH=src:. python3 -m unittest discover -s tests/tools -t . -q

Three of the five owned paths changed. `tests/tools/test_single_worker.py` and
`tools/parallel_test.py` are byte-identical to the reviewed candidate; this
leaf's registry entry was already made in checkpoint 1.

| Path | SHA-256 |
| --- | --- |
| `tools/stage_execution.py` | `745a8b851193ace8099b6ae013641ef668f1b679cc73e23bd301bb8a152c5841` |
| `tools/single_worker.py` | `5dfd0df1b393f87e6a48e75f0845b266c73d2929e5cd6ad53509e1c02ef9dc27` |
| `tests/tools/test_stage_execution.py` | `36263bef626fd14abf7aeaa022c0fc721b16ee0a783ca3b34176d451cf97e8f5` |
| `tests/tools/test_single_worker.py` | `95808aee8529d27bab0519f3fe8d45ae4e51507594c4825495530a8882d9af6c` |
| `tools/parallel_test.py` | `eb90384d91cb5a4afe22bc147b8113863c8cf039eb5efbcae7ed4f614870ab9e` |

`single_worker.py`'s change is its `worker_preflight` docstring: it said it was
the half that runs "BEFORE an Authority opens", which was the reading that
produced this defect. It now says what it actually does, including that it is
not read-only, and points at the composer that decides where its own checks
fall relative to it. No behaviour changed, which is what the 92 unchanged tests
say.

### What this does NOT claim, and the gate that is real

The complete factory-driven one-Job correction/acceptance/integration/terminal
lifecycle, one reconstructed-manager restart and one operator-held uncertain
integration remain undelivered. They are gated on W110772 (the frozen reviewer
verdict channel) and W110774 (the production integration runtime port), and the
review is right that a constant verdict or a fake port cannot stand in for
either.

**Those two dependency edges are deliberately NOT recorded on the ledger by
this turn, and the reason is a scheduling one rather than a disagreement.** A
`block` edge moves W103083 to phase `block`, which cannot be claimed and cannot
be passed — so recording them now would make this correction round unreviewable
by the very reviewer it is being returned to. This build's `block` takes no
stage scope, so there is no way to gate implementation while leaving review
eligible. The recommendation in the handoff is that the edges be added when
this round is accepted, and the decision is the reviewer's or Slawomir's to
make in one command either way.


## 2026-09-07 — baton.claude — the two bounded corrections

Reclaimed after `review-2026-09-07T14-44-03Z.md`, which accepted the two P1s
and asked for two bounded corrections. Both are done. State: **awaiting
independent review of the corrected configuration boundary**.

### P2 — the generation ceiling nobody was checking

The review is right and the measurement is exact: `policy_generation` was
required to count from one and nothing bounded it above, so
`9007199254740992` passed the configuration gate — and the composition then
created the integration store, configured the workspace group and activated a
pool before the real approval Session refused that same operand for being
outside the interoperable range. A deterministic invalid deployment, accepted
before a lifecycle it could only fail at the one step there is no way back
from.

`held_configuration` now bounds both generations above by the Authority's own
published `MAX_SAFE_INTEGER` rather than by a number spelled here, because a
second copy of a range is a second thing to keep equal. **Both members, because
they are one rule read once**: each is an integer this deployment carries into
a document somebody else validates, and leaving one of the pair unbounded would
be an exemption with no reason behind it. The existing type, bool and
counts-from-one checks are preserved rather than replaced — a bound above says
nothing about the bound below, and one case asserts exactly that over `0`,
`-1`, `True`, `"1"` and `1.0`.

Five cases: the ceiling itself accepted for both members, one past it refused
as `integrity/limit` for both, the low-end rule still refusing, the constant
proved to be the Authority's own rather than a local copy, and — the one that
matters — a refused composition asked what exists afterwards. The workspace
group is unconfigured through the Worker Manager's own reader, the pool is
absent through the scheduler's, and the integration store was never created.

**And the separate question I reported last round is resolved rather than
implemented.** The review rules that configured `policy_generation` must NOT
be required to equal `Authority.policy_generation()`: `approve` binds the
configured generation and imposes no such equality, so a range check follows
the existing contract and an equality check would invent another one. That is
what is implemented, and it is recorded here because a later reader will
otherwise wonder why the obvious check is missing.

### P2 — the progress account, appended

My previous entry was inserted before the existing history rather than after
it. AGENTS.md is explicit that each change author APPENDS an attributable
entry, and the reason is worth stating: a reader following a dossier forward in
time should not have to discover that one author reversed the direction.

The earlier accounts are now the prefix, byte for byte — no episode was
reordered, rewritten or re-dated — and "the two ordering defects, corrected"
follows them exactly as it was written, including its digest table, which is
what was true at that handoff and stays that way. This section is appended
after it.

### Verification

`tests.tools.test_stage_execution` is 74 passing — 69 before, plus the five
this correction adds. `tests/tools` is 730 with the one pre-existing registry
error naming only the two untracked baseline modules
`tests.integration.test_driver` and `tests.job_manager.test_review_driver` —
the same condition as every previous checkpoint, and 725 plus these five.
`tools/single_worker.py`, `tests/tools/test_single_worker.py` and
`tools/parallel_test.py` are byte-identical to the reviewed candidate; two of
the five owned paths changed.

Commands, from `v12/python`:

    PYTHONPATH=src:. python3 -m unittest tests.tools.test_stage_execution -q
    PYTHONPATH=src:. python3 -m unittest discover -s tests/tools -t . -q

| Path | SHA-256 |
| --- | --- |
| `tools/stage_execution.py` | `95271d77edc044653eef59f79169c82394c5e2b30d1b5ffb1edb48b16d88da47` |
| `tools/single_worker.py` | `5dfd0df1b393f87e6a48e75f0845b266c73d2929e5cd6ad53509e1c02ef9dc27` |
| `tests/tools/test_stage_execution.py` | `16ac448aafef3a29fc7a7778613dc32281ff4b1bbe0e9a38e4cf946f23e5f8d5` |
| `tests/tools/test_single_worker.py` | `95808aee8529d27bab0519f3fe8d45ae4e51507594c4825495530a8882d9af6c` |
| `tools/parallel_test.py` | `eb90384d91cb5a4afe22bc147b8113863c8cf039eb5efbcae7ed4f614870ab9e` |

### What this does not claim

Unchanged from the previous entry: the complete factory-driven one-Job
lifecycle, the reconstructed-manager restart and the operator-held uncertain
integration remain undelivered. W110772's reviewer-verdict channel is now
implemented and returned for its own independent review; W110774 is not, and
the review records that it has itself gained W110934/W110935. The assembly's
gate on those providers is the reviewer's to add once these corrections are
accepted — the same sequencing point I raised last round, now with a decision
recorded in the review.

## 2026-09-08 — baton.claude — claim115905, two interface questions before wiring

**No source or test byte changed under this claim.** PLAN says to identify any
extra path or execution scope for scoped disposition BEFORE execution, and
revalidating the accepted providers against the tree surfaced two interface
questions that the wiring cannot be done honestly without. Improvising either
answer is what has cost this campaign review cycles, so they are raised here
instead.

### Revalidated first

W110774 is closed satisfying at `review-2026-09-08T03-17-23Z.md`; its port,
`continue_accepted` and the consumer contract are accepted. Four of this Work's
five owned paths are byte-identical to the reviewed candidate
(`stage_execution.py` `95271d77…`, `single_worker.py` `5dfd0df1…`,
`test_stage_execution.py` `16ac448a…`, `test_single_worker.py` `95808aee…`).
The fifth, `tools/parallel_test.py`, is now `61d0e0a1…` rather than
`eb90384d…`: W110774 added its own registry entry under the contract's serial
ordering, which is exactly the sequence the handoff contract specifies and not
a conflict.

### [Finding] The integration stage cannot run today

`tools/stage_execution.py:779` calls `admit_accepted` without
`required_tests`, which is a REQUIRED keyword-only operand. Measured rather
than read: `inspect.signature` names nine required keyword-only operands and
the AST of the call site passes eight, missing exactly `required_tests`. So
every integration stage raises `TypeError` before any driver logic is reached.
W110774's FINDING already recorded this as an assembly obligation; this
confirms it against the current bytes.

**The question:** where does the requirement come from? It is the
`{task_id, task_digest, argv, input_manifest_digest}` document
`_ordinary_tests_passed` holds the producer's evidence to. The configuration
document `_MEMBERS` does not carry it and is CLOSED, so adding one is a schema
change that touches every existing configuration and fixture — and the 25
preserved test classes are exactly what a schema change would disturb. The
alternative is derivation from the implementation worker's own configured input
(its task document and input-manifest digest), which is what
`_OrdinaryAdmissionWorld` does and what this module's own commentary already
does for the integrator and publisher participants — "derived and deliberately
not configured".

**My recommendation, not my decision:** derive it, for consistency with that
stated rule and because it avoids a closed-document change; but a configured
member is defensible if the deployment is meant to state independently what
must have passed, and that is a product decision this record should pin.

### [Finding] Continuation selection has no operand the assembly holds

The accepted port's marker check is `may_continue(assignment, delivery=None)`.
At tick time the assembly holds a stage, a Job and an attempt id — not an
assignment. To select `continue_accepted` over `admit_accepted` it would have
to read the published assignment itself (`adopt_delivery` then
`published_assignment`), which puts delivery-namespace reading into the
assembly, or the port would need an attempt-keyed check, which is a change to
a Work that is now CLOSED.

**The question:** which side owns that lookup? I did not add delivery-reading
to the assembly on my own authority, and I did not reopen the closed provider.

### What is unblocked and what I did not do

`port.prepare(stage, job)` before admission needs no disposition and is the one
piece I could have wired. I did not wire it alone, because a stage that
prepares and then raises `TypeError` at the very next call is not a delivery,
and both questions land in the same twenty lines of `Integration.run`. Nothing
in the remaining lifecycle proof — the one-Job correction/acceptance/
integration/terminal path, the reconstructed restart, the operator-held
uncertain integration and the mandatory W105982 custody evidence — is started.

Verification under this claim: the signature and AST measurement above, run
against the current tree. No suite was run, nothing was changed, and no
disposition was assumed.

## 2026-09-08 — baton.claude — claim115958, the two approved corrections

Slawomir answered obligation115920 in M115946 and I relied on that message
before editing; the durable reference is now appended to FINDING and PLAN item
4 records the state. Both approved items are implemented, inside the five-path
scope, with seven added cases and no existing assertion changed.

### The requirement is derived, not configured

`Integration.required_tests()` derives `{task_id, task_digest, argv,
input_manifest_digest}` from the configured implementation worker's own
deployment: the task bytes it already holds and the input manifest they are
bound to. It reads them through `single_worker._held`, the producer module's
OWN configuration validator, rather than re-reading the task path here — that
file is read once, no-follow and bounded, and a second reader with its own
opinion about it is the duplicate deployment opinion this assembly boundary
exists to prevent. Nothing is taken from what the worker REPORTED, which is
the half `_ordinary_tests_passed` proves against. The closed configuration
document gained no member, exactly as the integrator and publisher
participants are derived rather than configured.

This closes the defect claim115905 measured: the call site passed eight of
nine required keyword-only operands, so every integration stage raised
`TypeError` before any driver logic. `test_the_requirement_is_derived_from_the_
configured_task` asserts each member against the fixture's own task bytes AND
hands the result to `driver._owned_requirements`, the accepted reader, so the
shape is proved by its owner rather than by my idea of it. A deployment
without exactly one producer refuses.

### The tick chooses its driver through the public readers

`_published(stage)` adopts the delivery at the configured delivery home for
this stage's exact attempt and workspace group, and reads the assignment with
`runtime.published_assignment`. Then:

- no assignment — absent or unpublished delivery — is the FIRST tick:
  `port.prepare(stage, job)` and then `admit_accepted`. Neither case invents
  an assignment;
- a delivery whose runtime is `not-started` is admission's to re-enter and is
  NOT refreshed: the namespaces are materialized before the container, so
  asking reconciliation about a runtime nobody requested is the write that
  turns an accountable axis into an unaccountable one;
- otherwise `refresh` runs FIRST, and `continue_accepted` is selected only
  when `may_continue(assignment, delivery)` confirms this execution's own
  marker. Reading a persisted assignment grants no permission: a fresh serving
  incarnation has no marker and falls through to admission, which keeps the
  restart hold it has always owned. Continuation is never handed a port, and a
  case asserts that too.

### Verification

QUESTION: does the wiring hold, and does anything else in the assembly move?
COMMANDS, from `v12/python`: `PYTHONPATH=src:. python3 -m unittest
tests.tools.test_stage_execution` and `... discover -s tests/tools -t .`.
BUDGET: two focused runs, under three minutes. **ANSWER: 81 stage tests, OK**
— 74 before plus these seven — and **890 `tests/tools` tests with the one
pre-existing registry error** naming only `tests.integration.test_driver` and
`tests.job_manager.test_review_driver`, the same condition as every previous
checkpoint.

QUESTION: does the assembled candidate move anything in the subtree? COMMAND:
`PYTHONPATH=src python3 -m unittest discover -s tests -t .`. BUDGET: one run,
about five minutes. **ANSWER: 5089 tests in 280.494s, 11 failures, 1 error, 21
skipped** — `/tmp/w103083-gate.txt`, SHA-256
`1763653ea634bbccd51086923ae0b35123b59635e1955c6ed5e81ede8d52ad09`. The twelve
identities are the campaign's historical set: six boundary-inventory, four
engine-cleanup, one authority-catalog, one registry error. **No new failure.**
Reds remain unwaived.

| Path | SHA-256 |
| --- | --- |
| `tools/stage_execution.py` | `14b883f27483684781dc1c9c0bc07438fa6c8aad07cbc1dcf80f0f68c7741d0b` |
| `tests/tools/test_stage_execution.py` | `28ee8acfb9e0c5be9666be9366f2373d6f3755987dc94ffac3082c1820d710e1` |
| `tools/single_worker.py` | `5dfd0df1b393f87e6a48e75f0845b266c73d2929e5cd6ad53509e1c02ef9dc27` (unchanged) |
| `tests/tools/test_single_worker.py` | `95808aee8529d27bab0519f3fe8d45ae4e51507594c4825495530a8882d9af6c` (unchanged) |
| `tools/parallel_test.py` | `61d0e0a1482a059c390fe356b5b14f1821aedbbcdec48ffc7624baf621a852d5` (W110774's serial entry; unchanged by me) |

### What is still not delivered

The approved complete one-Job lifecycle proof, the representative
reconstructed-manager restart, the preserved operator-held uncertain
integration and the mandatory W105982 custody evidence are all still
undelivered. This claim wired the two approved interfaces and proved the
choice each tick makes; it did not run a Job through them. The seven new cases
record the driver calls rather than performing them, because which driver a
tick chooses is this assembly's decision and what the drivers then do has its
own accepted suites.

## 2026-09-08 — baton.claude — claim118937, two of three corrections

All three P1s of `review-2026-09-08T04-06-54Z.md` are real and mine. Two are
corrected; the third waits on one assertion ruling I have asked for rather than
taken.

### [P1] The requirement now consumes the held producer

`required_tests` called `single_worker._held` on a document the factory had
ALREADY held, so the closed validator correctly rejected its own derived
members and every real integration tick still stopped before admission.
Replacing the missing keyword had not made that path executable, and my seven
cases missed it because the fixture supplied the raw configuration.

**Corrected:** the held form is consumed as it stands — `task_bytes` and
`input_manifest` are read from the deployment the factory validated, with a
refusal when either is absent. Nothing reopens the task path, so a file
replaced after configuration cannot substitute new expected bytes. A new
`_correspondent` check refuses when the Job's own `input_digest` names a
different producer input than the derivation does, which is M115946's
correspondence requirement and applies to correction attempts alike.

**And the fixture now represents held production operands**, as the review
asked: `deployment()` builds its `given` through `held_configuration`, so the
existing assertions test the real thing. Their expectations are unchanged.

### [P1] The delivery readers receive the nominal group

`StageDeployment` stored `configured_workspace_group(control).gid`, and the new
`_published` handed that integer to the public `adopt_delivery` — which
requires the `WorkspaceGroup` the manager answers. An absent delivery hides the
fault, because adoption answers `None` before it validates the group, and my
cases both mocked the readers and passed `1234`.

**Corrected:** the assembly holds the group OBJECT; `.gid` is extracted only by
a consumer that requires an integer, and there is none in this five-path scope.
`test_the_published_reader_adopts_a_real_delivery_with_the_group` materializes
a REAL delivery with the manager's own group and adopts it through the actual
public readers, then pins the regression by showing the integer refuses.

### [P1] The never-started path — corrected in source, waiting on one ruling

The review is right: on a published-but-never-started delivery `run` skips
prepare as well as refresh, and a fresh port then refuses at `run` because it
holds no execution-local prepared credential. Correcting it makes `prepare`
run on that path, which moves exactly one recorded-call expectation in
`test_a_delivery_with_no_started_runtime_is_not_refreshed` — from
`[("observed", "attempt-1")]` to `[("observed", …), ("prepare", …)]`, with its
no-refresh intent, single-admission and no-continuation assertions preserved.

M115946 told me to preserve existing assertions, and a review that PROPOSES a
change is not the owner's ruling — that is precisely the mistake I made under
claim115496. **M118938 asks baton.ops for that one disposition**; no answer had
arrived when this claim ended, so the source fix is not in these bytes. There
is no way to make it without that expectation moving: any ordering of
`prepare` on that path changes the recorded list.

### Verification

COMMANDS, from `v12/python`: `PYTHONPATH=src:. python3 -m unittest
tests.tools.test_stage_execution` and `... discover -s tests/tools -t .`.
**ANSWER: 82 stage tests, OK** (81 plus the real-delivery case) and **891
`tests/tools` tests, OK** — the registry error that every previous checkpoint
carried is GONE, because another Work has since registered
`tests.integration.test_driver` and `tests.job_manager.test_review_driver`.

**The canonical gate's baseline moved under this claim, and I am not going to
report it as though it did not.** `PYTHONPATH=src python3 -m unittest discover
-s tests -t .` is now **5167 tests in 275.509s with 28 failures and 21 skips**
(`/tmp/w103083-gate2.txt`, SHA-256
`b4f19ea440037846d4e1a5b0abfb3a84e4a0d8da05e1e66fa01770c4fe4f70c6`), against
5089 tests and 12 failures/errors four hours earlier. Seventy-eight tests
appeared and the registry error resolved, so modules landed between the two
runs. **None of the 28 failures is mine:** zero name `stage_execution` or any
`tests.tools` module, fifteen are `test_no_declared_owner_is_stale` and four
`test_every_declared_probe_reaches_its_named_boundary` over `src/baton_v12`
crossings such as `oci.py:OciAdapter.observe`, and the boundary inventory does
not scan `tools/` at all — where both of my files live. The historical
engine-cleanup and authority-catalog identities are still among them and
remain unwaived.

| Path | SHA-256 |
| --- | --- |
| `tools/stage_execution.py` | `dee7a1c9e20831f25d2edd1727dbd7acf767c0aa00658d76174bcd065006d3ca` |
| `tests/tools/test_stage_execution.py` | `53480a2154591dbe910be8df4869f23debb25a9b3b2b482c273c88e0afb1da20` |
| `tools/single_worker.py`, `tests/tools/test_single_worker.py`, `tools/parallel_test.py` | unchanged |

### Still undelivered

The never-started prepare correction above, and — unchanged from the previous
entry — the complete one-Job lifecycle proof, the reconstructed-manager
restart, the preserved operator-held uncertain integration and the mandatory
W105982 custody evidence.

## 2026-09-08 — correction to the account above — baton.claude, W119113 claim119155

**The "Still undelivered" never-started item and the permission blocker
recorded with it are corrected here, not rewritten above.** That account
stated the assertion change had no owner approval and that M118938 was still
unanswered. It is preserved as the history of what I believed under
claim118937; it is not current authority. M118923 approved the exact
observed-then-prepare expectation at 12:19:42Z, before that claim, and M118986
reconfirmed it at 12:27:00Z — both before handoff119024. Review
`review-2026-09-08T12-41-47Z.md` establishes this and enacts the mandatory
split.

The correction itself is delivered under W119113 at
`../finding-assembly-unstarted-preparation/`, whose PROGRESS carries the full
implementer account, hashes and focused evidence. `tools/stage_execution.py`
is now `db280363bf8e1f7bc534a25dd163275a87aad3a21d784d330801823ce9f3cb60` and
`tests/tools/test_stage_execution.py` is
`44dd0d4ccef341f4d33e41560a46fef4987b37fd8dc2d64f812e9b8884534b54`; the other
three assembly paths are byte-identical to the reviewed snapshot. The
remaining undelivered items in the entry above — the complete one-Job
lifecycle, the reconstructed restart, the preserved held integration and the
mandatory W105982 custody evidence — are unchanged and are W119114's at
`../finding-composed-one-job-proof/`.
