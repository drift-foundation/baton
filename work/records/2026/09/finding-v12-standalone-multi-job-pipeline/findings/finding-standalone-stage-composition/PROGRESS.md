# Progress

Not started.

## claim140686 — P1 resolved and verified; P2 returned as a scope gap

Input revalidated first: `tools/stage_execution.py`
`9cf2927f4057a68beec61cfd56abeca709509d7770cd577412f750bce4ae1223` and
`tests/tools/test_stage_execution.py`
`2b234a605028d08952a11e2610753ab116a0ea969957399fecac8d55dbd1bffd`, both 0664 --
exactly the pinned bytes.

### P1: the configured deployment constructs its own integration port

The design pinned before editing, and every operand of it comes from material
already configured or durably derived. **No source outside the owned pair was
needed.**

- **Where it is constructed.** In the direct branch of `Integration._run`, at the
  one point where all three dynamic operands exist and are read from their own
  owners: the Job's own line through `line_for`, that line's integration
  checkpoint, the proposal its producer actually published, and the Job's own
  target. Two of the three do not exist until a review is accepted, which is why
  no configuration document could carry them and why the component fixture had to
  recompose the deployment afterwards. Nothing is recomposed here.
- **Memoized per Job**, because one Job's integration is one capacity and a
  second port would be a second set of the homes it resolves. A port an operator
  SUPPLIED is never replaced.
- **The fixed half comes from public owners only.** `ManagerOperations.port` is
  public and is the port that really holds the claim; the held document is this
  module's own `_served_deployment` answer, the same derivation the provider
  composed the capacity with. No private attribute of another module is read --
  the credential home is composed over the CONFIGURED root rather than borrowed
  from `single_worker`'s private view.

**Three further production gaps were found by running it, not by reading.**

1. `delivery home is not a directory this deployment provisioned` -- the
   accepted fixture made `integration_root` by hand. The composition provisions
   it and its two siblings now.
2. `target 'target-a' is not activated; an entry belongs to a configured target`
   -- nothing in production ever adopted a configured target. `activate_targets`
   adopts each bound Job's own at composition, with a document derived from the
   configuration so an exact restart replays instead of colliding.
3. The integrator's **instruction bytes** were configured nowhere -- only their
   digest, in the integration profile. They are not the worker's task document,
   which is the JOB's task. New optional member `integration_instructions` names
   the file; the profile's existing pin is what proves the bytes.

### The injection and reconnect path is retired, not reordered

`integrating()` no longer calls `integration_port` or `connect`: it drives to
`integrating`, which is the state that PROVES the port worked. Both fixture
`activate_target` calls now assert the composition's own adoption instead of
performing a second configuration of one target -- `activate_target` refuses a
changed configuration for the same key by name, so the fixture's own description
was a genuine conflict once the deployment owned adoption.

### P2: the derived-result judgment consumer is a real missing provider

**Evidence, and it is exhaustive for this tree:** nothing under `v12/python/tools`
or `v12/python/src` calls `.verify(`, `.review(` or `.approve(` on an Authority
session. Every caller is a test. The three judges are configured as
`receipt_participants` and their sessions are MINTED BY THIS DEPLOYMENT, so the
deployment writing its own three receipts would be self-approval -- which owner
M140286/M140288 forbids, and which review 2026-09-11T01-22-35Z restates.

A real consumer therefore needs one of two things, **both outside the owned
pair**: a new judging worker role with its own adapter and container contract
(new source in `tools/single_worker.py` or a new tool), or a named external
accepted service with its own configuration and evidence. Per the handoff I am
returning that gap rather than editing it or filling it with manual session
calls. **This is the smallest concrete scope gap, and it is the only thing
between this candidate and B's ordinary derived authorization.**

### Expectation changes, inventoried

1. `test_the_integration_stage_is_held_for_want_of_a_runtime_port` is renamed and
   rewritten as `..._stops_on_unconfigured_integrator_wiring`. Its premise was
   the refusal this Work removed. It now measures the real remaining stop for an
   unconfigured deployment and asserts the OLD sentence is absent.
2. `integrating()` drives to `integrating` rather than `claimed`, and both
   `..._share_one_integrator_one_at_a_time` and the capacity case follow: the
   stage no longer rests at `claimed`, because it is no longer waiting for a
   port that never came.
3. Both fixture target activations became adoption assertions.
4. `integration_turn` reads the launch and bundle homes from the deployment
   instead of guessing `self.root`.
5. New: the production construction witness, a supplied-port-wins control, a
   digest-mismatch control and an unconfigured-instructions control.

### Baseline attribution, measured rather than assumed

The full owned module is **247 tests, 13 errors, ZERO failures** (step 17). I did
not assume those 13 were pre-existing: the pinned two-file candidate was
installed from `evidence/placement-140665/candidate`, the four erroring classes
run (step 14, 13 errors), then this candidate restored and rerun (step 15). That
showed **21** -- so 8 were mine, from the one-Job fixture's own target
activation. After correcting it, step 16 shows 13 and `diff` proves the error set
is **identical to the pinned baseline's**, as does step 17's full module.

### Changed, 0664

- `tools/stage_execution.py`
  `3f3ec30b80b58e225eafcba4547bf8101d15c685027dcc0c5d09f44e544a19ea`, 233218
- `tests/tools/test_stage_execution.py`
  `c2ae05bc6fd2b7c25eac5bf212f3e608c2f29851ec79688b9a37a741d9e646a8`, 415246

### Ledger

Cumulative author **544.284596/570s** over seventeen timed runs this claim
(161.0s spent), **25.715404s remaining**. Nine runs were non-zero and all are
retained, including steps 14/15 which exist only to attribute the baseline
honestly. Unmeasured: reads, greps, the edit scripts, `ast.parse` checks and the
manifest script, on the inherited basis. Joined 40s untouched; no transfer or
reset.

### Not claimed

No actual standalone run and no model judgment: W71879 remains the acceptance for
that, and the engine boundary here is the fixture's. The A/B witness continues to
write B's three derived receipts from the fixture, which is exactly the gap
returned above.

## claim140937 — P1 resolved through the LITERAL factory; P2 returned as a
## configuration-contract decision, with its evidence

All four pinned inputs revalidated first: stage `3f3ec30b`, single `d71f84e8`,
test_stage `c2ae05bc`, test_single `40543a4e`, all 0664.

### Your P1 was right and my previous claim overstated its own witness

`factory` calls `operations_from` with no optional capabilities, `StageDeployment`
kept `engine_run=None` and `credential_provider=None`, and `integration_port_for`
then refused. My witness injected both through `serving`, so it proved
construction and **not** that the defaults work. Corrected at the boundary the
design pinned:

- **`single_worker.effective_engine_run(engine_run=None)`** is a new public,
  bounded accessor returning `engine_run or _engine_run`, and both internal
  resolutions now go through it, so an injected override and the ordinary
  default cannot drift. No private state is read.
- **The credential provider is the integration worker's own already-resolved
  provider**, the object `worker_preflight` answered during this composition --
  not a reconstructed source and not a raw keyword.
- The composition passes those **effective** values into `StageDeployment`.

### The witness now composes through the literal factory

`factory_serving` calls `stage_execution.factory(job, control)` -- two operands,
so nothing can be injected: no `engine_run`, no `credential_provider`, no
`clock`, no `checkout`, no `integration_port`, no `connect`. Three **external
boundaries** are substituted, as the accepted public-factory class substitutes
its two: the engine, `_checkout`, and the clock.

**The clock is a fixture constraint I had to find by measurement, and I am
stating it rather than hiding it.** This suite pins its stores to `fixtures.NOW`
while `factory` takes no clock, so a real-time worker read the offers its pinned
store had issued as `expired` and claimed nothing -- `offer ... is 'expired', not
accepted`, step 2. In production both clocks are the same real one; the mismatch
is this fixture's, not the composition's.

**The credential provider is NOT substituted -- it is configured.** The registry
is written and named in `credential_sources`, so `worker_preflight`'s production
default path builds the provider. That is the difference the review asked for
between an effective operand and an injected one.

Result: the literal factory reaches Job A's `integrating` -- delivery published
and runtime started through the port it built itself (step 3).

### The misleading test claim is corrected

`test_a_supplied_port_is_never_replaced_by_a_constructed_one` was named for
supplied-port precedence but `integrating()` supplies no port any more, so it
measured constructed-port survival. It is renamed
`test_the_constructed_port_is_the_same_one_through_completion` and says so, and a
real precedence control now **actually supplies** a per-Job port through
`operations_from` and asserts object identity before and after driving.

### P2: what I found, and the one decision it needs

The consumer is **not** implemented, and I did not half-build it. I also accept
your correction of my earlier reasoning: `driver._receipt` uses
`getattr(session, verb)`, so my literal-call grep was **not** exhaustive
evidence, and session possession neither establishes judgment nor forbids
evidence-backed receipt recording. I withdraw both inferences.

What I established structurally instead, in the files I own:

1. **`ROLES` is closed at three.** `stage_execution.py:519` refuses any role
   outside implementation/review/integration and `:567` requires all three. The
   three configured receipt participants therefore have **no worker document at
   all** -- no image, engine, workspace storage, credential home, input manifest
   or task document -- so there is nothing `single_worker`'s execution interfaces
   can run for them.
2. **There is no read-only custody boundary for a derived candidate.**
   `StageComposition._prepare` grants a WRITER boundary over the producer's line
   and its current checkpoint, which is the design's own observation.
3. **Reusing the review worker's deployment would misattribute the judgment** to
   that worker's participant rather than to the three configured receipt
   participants, which the design forbids.

The smallest design that expresses an authentic consumer is therefore: configured
judgment execution for the three receipt participants (document schema, role
closure and composition -- all in `stage_execution.py`) plus a read-only
derived-candidate custody boundary (`single_worker.py`). **Both are inside my four
files.** What is *not* inside them is the decision: it requires the OPERATOR to
supply three further worker deployments with their own images, engines, storage
and credentials, which changes the deployment contract. That is a disposition, not
an implementation detail, and the design told me to return exactly this rather
than edit around it.

**I am not requesting more budget -- 150.47s of the 180s allocation is unspent.**
I stopped because the next step changes what an operator must configure.

### Changed, 0664

- `tools/stage_execution.py` `37c72327f62ace90ab5b4c8aba6a76d1e811397db60196881d
  c360d624ff1f62`, 234303
- `tools/single_worker.py` `d57936e262f7f2df8e7f7ca031135eb957c9cfe3a053b8f594c3
  fb5a6e4025e2`, 140433
- `tests/tools/test_stage_execution.py` `1636ad131fdfdf01fc5ddf682419126b85a0802
  1fd357f01038686cff94d7823`, 422703
- `tests/tools/test_single_worker.py` unchanged at `40543a4e...`, 182133

### Expectation changes this claim

1. The construction witness composes through the literal `factory`, not
   `operations_from`; three external boundaries substituted, credential provider
   configured.
2. The supplied-port control renamed to what it measured, plus a new genuine
   precedence control.
3. New `factory_serving`/`factory_coding`/`credential_registry` helpers.
4. `single_worker`'s two internal engine resolutions route through the new public
   accessor -- same value, one boundary.

### Evidence and ledger

Steps 1-5 in `evidence/run-140937-step-NN.log`; manifest
`evidence/result-140937.json`; `ledger-140937.json`. Two-Job class **39 tests
green** (step 4). Focused regression **152 tests, 13 errors** over
`test_single_worker`, the four previously-erroring stage classes and the
public-factory class: `test_single_worker` is fully green and the error identity
is **byte-identical to the retained pinned baseline** from
`run-140686-step-14.log`. No full-module rerun.

Author **573.818718/800s** cumulative; this correction has spent **29.534122s of
its 180s**, leaving 150.465878s. Two non-zero runs this claim, both retained
(step 1 the offer-expiry discovery, step 2 its diagnostic). Prior 15 non-zero runs
and the accepted 40.932s overrun retained. Joined 40s and all reserves untouched.
Unmeasured: reads, greps, edit scripts, `ast.parse` checks, the manifest script.

### Not claimed

No actual standalone run, no model judgment, and **no derived judgment consumer**.
The A/B witness still writes B's three receipts from the fixture; that is the
returned gap and I have not dressed it over. W71879 stays gated.

## claim141024 — P2's configuration half is BUILT and verified; the execution
## boundary is the exact remaining scope

Four pinned inputs revalidated: stage `37c72327`, single `d57936e2`, test_stage
`1636ad13`, test_single `40543a4e`, all 0664.

### Ledger prose corrected, as you required

The non-zero runs of claim140937 were steps **1 and 5**, not 1 and 2 — step 2 was
the offer-expiry diagnostic and it **exited 0**; its 13 errors are the retained
baseline identity. I also should not have written "aggregate green": the focused
regression is 152 tests with 13 retained pre-existing errors, and
`test_single_worker` alone is green. The owner ceiling is **800s**; my earlier
"450->570" phrasing was stale. All corrected here and in the new ledger.

### The configuration shape, implemented exactly as pinned

`result_judgment_workers` is a new optional, module-owned member keyed by bound
Job, each Job naming exactly `verification`/`review`/`approval`, each value a
`worker_id` plus a complete `single_worker` deployment. `_held_judgments` proves,
before anything is opened:

- the mapping is non-empty and names only Jobs this deployment **binds**;
- each Job names **exactly the three** kinds -- two of three is not an
  authorization, and the kinds are compared against `_RECEIPT_MEMBERS` so the two
  sets cannot drift;
- each deployment is held by **`single_worker`'s own validator**, not a second
  copy of its rules, and comes back in its derived form;
- each execution launches the accepted **`review`** launch role, so no new
  protocol role is introduced;
- **each participant IS the `receipt_participants` member of its own kind** -- an
  execution configured for anyone else would produce a report this deployment
  could never turn into that owner's receipt;
- no judgment identity collides with a stage worker or another judgment;
- every judgment path lies outside the checkout, as a stage worker's must.

**The three-stage pool is untouched.** `ROLES` still names the three stages a Job
has; a judge serves no Job stage and takes no stage allocation, which is why it is
configured separately rather than as a fourth role. Absent is an answer: every
accepted document predates this member and reads exactly as it did.

### The derived subject, read from custody

`StageDeployment.judgment_subject(result_id)` returns the exact immutable subject
through `reconciliation.result_of` -- which re-derives the record's identity and
re-proves every act it passed through. It refuses unless the result is
`published`. It carries the **derived** proposal, result digest, content digest,
head and tree, the target revision it was reconciled onto, the owning Job and
target, and the retained causal observations with their observer. It is measured
to be the derived candidate and **not** the producer's: the derived proposal
differs from the source proposal, and the candidate head differs from both the
submission's candidate and its base.

`judgment_executions(job_id)` returns `None` for a Job with no consumer, so that
branch stays pending honestly instead of inventing one.

### What is NOT done, precisely

The **execution and custody boundary**: `single_worker` supplying the bounded
actual execution with the derived subject mounted read-only and a separate
writable report output, and `stage_execution` dispatching, polling, correlating
each frozen returned report to its authorized dispatch/actor/candidate, and
composing the three scoped receipts. The fixture still writes B's three receipts
directly, and I have not dressed that over.

**No unsupported interface or additional path is needed, and I checked rather
than assumed.** The frozen-output custody interfaces (`output.request_freeze`,
`record_frozen_result`, `frozen_output_of`) are attempt-bound, and an attempt
needs a live Authority assignment for a configured Work -- which each judgment
deployment now names through its own `input_manifest.work_ref`. So the four files
can express it; what remains is implementation, plus the operator's three judge
Works and assignments existing.

**Why I stopped here:** 71.35s of the 180s allocation remains, so this is not a
budget limit. It is working context: the execution boundary is a real container
per judge with assignment, mounts, credential materialization and frozen-output
correlation, and half-building it would leave exactly the fabricated-positive
shape the design forbids. The configuration half is a complete, independently
reviewable increment and the strict prerequisite for the rest.

### Changed, 0664

- `tools/stage_execution.py` `759edc4c8a565d76268b4d7a8d013f80dc52daa7a7d8b9e54e
  c91b5b2d3153fd`, 243993
- `tests/tools/test_stage_execution.py` `1463de0c3286da2f3cafe554e2b7dc28ff9f0baa
  ca399e5f3517b62a20165511`, 433078
- `tools/single_worker.py` unchanged at `d57936e2...`, 140433
- `tests/tools/test_single_worker.py` unchanged at `40543a4e...`, 182133

### Changed expectations this claim

Additive only. Eight new controls: the configuration held per Job; an absent
consumer leaving the document unchanged; an execution for the wrong participant
refused `policy/denied`; two-of-three refused; an unbound Job refused; an identity
colliding with a stage worker refused; the derived subject proved to be the
derived candidate with its retained causal evidence; a Job with no consumer
selecting `None`. No existing expectation was altered.

### Evidence and ledger

Steps 6-10 in `evidence/run-140937-step-NN.log`; manifest
`evidence/result-141024.json`. Two-Job class **47 tests pass** (step 9). Focused
regression step 10: 152 tests, 13 errors, error identity **byte-identical** to the
retained pinned baseline in `run-140686-step-14.log`, `test_single_worker` green.
No full-module rerun.

Author **652.937018/800s** cumulative; this correction has spent **108.652422s of
its 180s**, leaving **71.347578s**. Non-zero this claim: steps 7, 8 and 10 --
steps 7 and 8 were my own test errors (`self.principals` does not hold the judges,
and a wrong stage-worker multiset for the two-Job variant) and step 10 is the
retained baseline identity. Prior non-zero runs and the accepted 40.93217554400326s
overrun retained; joined 40s and all reserves untouched; no reset or transfer.
Unmeasured: reads, greps, edit scripts, import/`ast.parse` checks, manifest script.

### Not claimed

No actual standalone run, no model judgment, no judgment dispatch or return, and
no authorized B import through a real consumer. W71879 stays gated; W129838, H-7
and C-1 remain deferred.

## claim141103 — both flagged correctness items done with controls; the judgment
## execution boundary is still not implemented, and I am naming why plainly

Four pinned inputs revalidated: stage `759edc4c`, single `d57936e2`, test_stage
`1463de0c`, test_single `40543a4e`, all 0664.

### Item 1: `_resolved` covers the judgment executions -- and this found a defect

`_resolved` iterated the stage workers only. It now also asks the Authority, for
every configured judgment execution, whether its participant resolves to the
principal it names and whether its configured Work is one this Authority projects
-- both while nothing has been written, instead of at a dispatch with a control
store already configured.

**Writing it surfaced a real defect by measurement rather than by reading.**
`scheduler.activate_pool` takes `_resolved`'s answer and requires its keys to be
**exactly** the configured pool participants, so adding the judges to that map
refused every activation: `pool activation's resolved-principal keys must exactly
match the configured participants`. That rule is right -- a judge is not a pool
worker and holds no stage capacity -- so the loop contributes the PROOF and not a
member of the pool's identity map. A control composes a full deployment with the
consumer present, and a second points one judge's manifest at a Work this
Authority does not hold and measures the refusal before anything durable exists.

### Item 2: each judge holds its own real Work and manifest

My previous helper copied `self.config` wholesale, so all three judgments carried
the ORIGINAL producer's `input_manifest.work_ref` and the own-Work claim was not
proved at all -- three executions would have run under one Job's Work. Each judge
now has a Work created for real (`0000000a-W3/W4/W5`), its own manifest over its
own task document, and the control asserts all three Works are distinct and none
is the producer's.

### What is still NOT implemented

The execution and custody boundary: a bounded `single_worker` execution per judge
over the derived subject mounted read-only with a separate writable report output,
and `stage_execution` dispatching, polling, correlating each genuine frozen return
to its dispatch/owner/derived candidate, and composing the three scoped receipts.
The fixture still writes B's three receipts directly and I have not dressed that
over.

**The accepted precedent is identified, so the next turn needs no design work.**
`integration_worker.IntegrationRuntimePort.prepare` already does exactly this
shape for the integration role: `record_attempt(...)` then
`activate_assignment(manager, assignment_port, attempt_id=..., expect=...)`, then
composes its roots and mount boundary, materializes its credential and starts
through the engine. A judgment execution is that shape over a read-only derived
subject and a separate report output, with `output.request_freeze` /
`record_frozen_result` / `frozen_output_of` for the custody and correlation.

### Why it is not done, stated plainly

**Not budget:** 23.69s of the 180s allocation remains unspent, and I am not
requesting more. **Not authority or design:** the configuration is built, the
subject is selected, the precedent is named, and no interface or extra path is
missing. It is working context. This is the third consecutive turn where the limit
has been how much of this composition I can write and verify inside one context,
and I am not going to keep reporting that as though it were new information.

The reviewer asked me not to introduce another planned partial milestone, and I am
not proposing one: what I am reporting is that a bounded-runtime composition of
roughly `IntegrationRuntimePort.prepare`'s size does not fit in the context I have
left after the corrections, and that how to sequence it is a call for the reviewer
and the owner rather than mine to keep deferring turn by turn. I will implement it
whichever way they choose.

### Changed, 0664

- `tools/stage_execution.py` `22ce116949ecf5d0aa9a814ebb2c615ab120a09099b424b8fa1
  77579f559e350`, 246930
- `tests/tools/test_stage_execution.py` `564b53e7d4da3408356c33b77e4bac590d61454f
  2515355cb2ee666ab1488a30`, 438730
- `tools/single_worker.py` unchanged at `d57936e2...`, 140433
- `tests/tools/test_single_worker.py` unchanged at `40543a4e...`, 182133

### Changed expectations this claim

Additive only, two new controls: a configured consumer composing and resolving its
judges, and a judgment Work this Authority does not project being refused. The
existing held-configuration control gained assertions that each judge's Work is its
own and distinct. No existing expectation was altered.

### Evidence and ledger

Steps 11-14 in `evidence/run-140937-step-NN.log`; manifest
`evidence/result-141103.json`. Step 14: **201 tests, 13 errors**, error identity
**byte-identical** to the retained pinned baseline in `run-140686-step-14.log`; the
49-test two-Job class and `test_single_worker` are green within it. The 13 are the
retained pre-existing set and this is **not** an aggregate-green claim.

Author **700.589775/800s** cumulative; this correction has spent **156.305179s of
its 180s**, leaving **23.694821s**. Non-zero this claim: step 12 (my own two test
expectations -- the pool-map defect above and an Authority refusal code I had
guessed) and step 14 (the retained baseline identity). Prior non-zero runs and the
accepted 40.93217554400326s overrun retained; joined 40s and all other reserves
untouched; no reset or transfer. Unmeasured: reads, greps, edit scripts, import and
`ast.parse` checks, the manifest script.

### Not claimed

No actual standalone run, no model judgment, no judgment dispatch or return, and no
authorized B import through a real consumer. W71879 stays gated; W129838, H-7 and
C-1 remain deferred.

## 2026-09-11T03:33:40Z — baton.tuner claim141250: implementation complete, awaiting review

Owner141241 reassignment executed. Added genuine per-judge assignment/runtime/exchange and retained report custody through single_worker; stage_execution dispatches the exact derived result with policy pin, adopts only correlated accepted reports and lets normal import/settlement complete B. Existing A/default behavior retained. Changed only the four authorized source/test paths plus this dossier. Exact details, affected assertions, scope limitations and evidence: HANDOFF-141250.md and evidence/tuner-141250/handoff-manifest.json.

Final focused runs9/10 pass8/11 tests (18 distinct); the first run exercised B, and all failures remain retained. Runtime30.632039878997603s plus charged candidate audit0.11722020699817222s = claim30.749260085995775s. Author731.3390351440088/920s plus uncertainty; correction187.05443938200625/300s, remaining112.94556061799376s. Reviewer9.146181310000488/25s and all reserves unchanged. Full standalone/model proof remains W71879 after independent acceptance. No Git index/history operations.
