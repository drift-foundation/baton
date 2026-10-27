# Implementation progress

## claim364837 — the retry keeps the task it was created with

Answers the bound `FINDING.md` and `PLAN.md` under thread364834. Baseline is
the parent's `candidate-364768` (manifest
`edceb4cd4b38cb7e1ebee2c09759a3e13cfaea96add3671e3e3855404d605b54`) over base
`19f02ce1295b4517a85f0822d48754efc982f388`; this child's candidate is
`candidate-364837/` and its manifest records inherited versus changed bytes
member by member. Every earlier candidate, in this dossier and the parent's,
is preserved byte-untouched.

### What was wrong, confirmed against the current tree

Both code facts the FINDING names are real and I reproduced the consequence.

1. `fresh_attempt._bound` asked `binding.serving(...)` with no task. A retried
   template Job submits the prior Job's input digest — `_composed` carries it
   verbatim, and for a created Job that digest IS its own task's Job-scoped
   identity — so every configured worker was compared against the INSTALLED
   document and the retry was refused as unservable by the very pool that had
   served the original.
2. `creation.job_task_of` read `template_jobs` alone, a relation a retry
   identity has no row in. Past admission the delivery would have been the
   installed task beside a Job declaring its own, which
   `single_worker._matches` refuses as "another bootstrap input".

An honest note on the reproduction: my first probe drove the real
`fresh-attempt` command against a really installed instance, and that
instance's own serving loop materializes its line through the real `git`
checkpoint profile — "Git line materialization failed". I may not run version
control, so the reproduction that completes is the suite's, over the injected
profile seam. The probe is kept in the evidence directory for what it
establishes about the environment.

### The fix

**`creation.job_task_of` follows the retry lineage.**
`fresh_attempts.prior_job_id` is the retry relation's own NOT NULL column —
the schema's stated reason for keeping two relations rather than widening one
— and the read walks it. So a retried Job's task is owned by the creation that
made it, immutable where that creation wrote it, and reachable from every
successor. Nothing is copied into the retry's row, which would be a second
account of one fact; nothing is recovered from the deployment's installed
bytes, which a configuration change moves. The walk is bounded and refuses a
circular lineage rather than looping, because answering a delivery question
from a corrupt lineage is worse than saying so.

**`fresh_attempt.admit` reads that task and passes it on.** It reads the PRIOR
Job's task from the store — the Job owner's own answer, not a remembered value
— and hands it to `_bound`, which forwards it to the selector. `None` is every
Job with no own task, and the selector then compares the installed document
exactly as before.

The port contract gained the operand in the parent's claim364551, so the
fresh-attempt fakes that implement it were updated with it here. One of them
had drifted: `test_fresh_attempt`'s interrupting wrapper still declared
`serving(self, job_id, kind)` — a shape the port has not had since review R3 —
and would have raised if anything had reached it. Nothing did, because it
interrupts one step earlier.

### What is proved

`tests/tools/test_retry_task_lineage.py`, **17 cases**, over a real Job store,
a real control store, the real `creation.create_template_job`, a real pool
composed by `stage_execution.operations_from` with its own serving loop, a
real in-image worker turn that faults, and the real `fresh_attempt.admit`.

- ADMISSION: the prior Job's own task reaches the servability question, once
  per stage, and is not the installed document; a Job with no own task asks
  with `None`; the fresh Job answers the prior task through the lineage and
  its submission declares the prior identity; a retry of a retry follows the
  whole chain; nothing copied the task into the retry's row; the original
  creation row, the first attempt's recorded input identity and its
  exceptional stage are untouched; the same request again answers the same
  fresh Job with one retry row.
- DELIVERY: the reader the serving path calls answers the inherited task for
  the retry; the per-stage document a worker would serve it under carries
  those bytes, is a fresh document rather than the installed one, and its
  Job-scoped identity is what the retry submitted — which the real `_matches`
  then admits; and the pool's own `_job_workers` admits the retry for both
  stages.
- REFUSALS: a circular lineage refuses `integrity/schema` naming the cycle; a
  hand-submitted Job and a Job nobody submitted both answer `None`.

### Where this stops, measured rather than assumed

A faulted attempt's material is PRESERVED (DESIGN ART-7), so its allocation
stays held and the pool answers the retry's offer with "every effective
worker/principal capacity is reserved or recovery-required". One case reads
that exact refusal out of the loop's own report. Releasing that capacity is
the recovery path's act, not an admission's and not a delivery's, so the
retried Job's own STARTED container is outside this outcome — and everything
the runtime would use for it is asserted by the objects that compose it.

I first tried to arrange the first attempt's end with an engine that refuses
the launch; that leaves the allocation `recovery-required` for the same
reason, and the case said so. The faulted turn is the pilot's own shape and is
what the fixture uses.

### Verification

Candidate root `/tmp/w364834`, the whole of `v12/`; `PYTHONPATH=src:.`

- **`tests.tools.test_retry_task_lineage`: 17 OK.**
- **Whole `tests/job_manager`: 1375 OK.**
- **Six tools suites** (retry_task_lineage, connected_creation,
  creation_ports, job_task_delivery, bootstrap, instance): **384 cases, OK** —
  no failures.

### Cost

Reading `fresh_attempt`'s cut order, `_bound`, `_composed`, `successor_of`,
the `fresh_attempts` and `template_jobs` schemas and their stated reason for
being two relations, `creation.job_task_of`/`created_job_rows`, and
`test_fresh_attempt`'s fixture. Probes: three — the retry against an installed
instance (refused: the original had not settled), the same after a pool loop
(refused: real version control in the line materialization), and the capacity
refusal. Test runs: the new suite six times (five failing — a stub manifest
the frozen schema refused, ports answering for another instance, the admission
passing `None` because I had changed `_bound` without wiring its caller, and
twice on the capacity hold); `tests/job_manager` twice; the tools group once.
No live provider, no container engine, no deployed-instance mutation, no
version-control operation.

### Boundaries

No Git operation of any kind, and no test fixture that performs one was run.
The canonical `v12/python` tree is byte-unchanged. The parent's candidates and
evidence and this dossier's `FINDING.md`/`PLAN.md` are untouched; I wrote
`candidate-364837/`, `evidence/claim-364837/` and this file.

## claim364962 — the retry driven into the loop, and where the line stops it

Answers `review-2026-10-27T00-18-27Z.md`: drive one supported fresh retry
through admission and the serving loop into runtime startup, correct the stale
capacity docstring, and record a distinct defect's reproduction rather than
assuming its scope. `candidate-364962/` is seeded from `candidate-364837`; one
member changed — the test file — and no product byte.

### The docstring correction, and the discovery behind it

A faulted turn does NOT release the pool's capacity; ART-7 retention is why,
and `RetryLineageCase.agent` now says so instead of claiming the opposite.

Driving the review's "use supported recovery" found the thing that actually
moves the chain: **a turn that RAISES and a turn that ANSWERS are different
endings.** `finalize_quiescent_assignment` refuses an attempt whose "worker
disposition is 'none'" — a raised turn leaves a `faulted` terminal with no
disposition, and the Work stays claimed, which is the state my earlier claim
reported as a capacity hold. An ANSWERED `unable` is an ending the product
settles itself: the composed ending finalizes the assignment (calling it again
from the fixture was refused as "already recorded with a different kind or
signature", which is the journal saying the act had happened), and the retry is
then OFFERED. An `unable` answer must still produce artifacts — "a retention
decision names at least one artifact" — so the agent withholds only the
proposal, which is what `unable` means.

### How far the retry now gets

With a spare producer configured and authorized for both routes the Work passes
through, the retry is **offered, claimed by the spare and prepared**, carrying
the task it inherited. The acts are read out of the loop's own reports.

The one-producer pool is kept as its own case and now says what it really
measures: the retry is offered, and its claim is deferred because the first
ending passed the Work to its `review_route` — "route 'rview' does not resolve
to 'baton.claude'". That is the v11 route doing its job, and it is why the
runtime class authorizes its spare producer for both routes.

### Where it stops, with the exact reproduction

    line state 'review-ready' does not admit a writer

One Work has ONE development line — `create_line`'s identity is
`(authority, work)` — and a retry is a NEW Job on that same Work, so it is
granted a writer on that same line. The first round's ending left the line
`review-ready`, and the accepted provider refuses a writer there. A line
awaiting review is advanced by a VERDICT (a correction round through
`open_correction`); a fresh attempt is not a correction. So the retry reaches
preparation and is refused before any container, with no task or identity
disagreement anywhere in it.

`test_the_retrys_preparation_is_refused_by_the_lines_own_state` asserts that
refusal from the composition the loop asked, and that both Jobs resolve to one
line. The two supported ways past it are a correction round, or a retry on its
own Work and line — and the second collides with the carried input identity,
which includes `work_ref` (so the prior Job's input digest, carried verbatim by
`_composed`, would match no worker on another Work). Both are somebody else's
outcome; this is the reproduction, recorded for decomposition.

### What is asserted about the delivery itself

The document the spare producer would serve the retry under carries the
inherited task bytes; the reader the serving path calls answers them; that
document's Job-scoped identity is what the retry submitted, which the real
`_matches` admits; and the pool's own `_job_workers` admits the retry for both
stages. The first attempt's stage, attempt, allocation, recorded identity and
input root are untouched by all of it, and a reopened store replays the same
admission to the same retry.

### Verification

Candidate root `/tmp/w364962`; `PYTHONPATH=src:.`

- **`tests.tools.test_retry_task_lineage`: 20 OK.**
- **Whole `tests/job_manager`: 1375 OK.**
- **Five tools suites: 270 cases, OK.**

### Cost

Reading `finalize_quiescent_assignment`, `intake`'s retention dispositions,
`review_cycles`'s line states, `StageComposition._prepare`, and
`_ConcurrentEngine`. Probes: five — the Work-claim refusal, the disposition
configuration, the finalization's disposition precondition, the retention
decision's artifact rule, and the line-state refusal. Test runs: the suite ten
times; nine failing, each for a reason now in the code — a wrapper member the
worker schema does not carry, an ambiguous role lookup in a two-producer pool,
the Work's claim, the Work's route, a finalization already performed, an
`unable` answer with nothing to retain, a single-container engine shown the
first attempt's runtime, and two assertions about states the projection shapes
differently. No live provider, no container engine, no deployed-instance
mutation, no version-control operation.

### Boundaries

No Git operation of any kind, and no fixture that performs one was run. The
canonical `v12/python` tree is byte-unchanged and no product file changed in
this claim. `candidate-364837/` and its evidence are preserved exactly; I wrote
`candidate-364962/`, `evidence/claim-364962/` and this section. The bound
`FINDING.md`/`PLAN.md` and every review are the reviewer's and are unmodified.


## claim365848 — the joined task and provenance acceptance

Answers `review-2026-10-27T14-36-28Z.md`, which names exactly four things the
owner-accepted recovery candidate does not yet establish and asks for no
broader matrix than those. `candidate-365848/` is seeded from the accepted
child `candidate-365537`
(`e2f18f9b4a40e2e4eccd42e2648262cb2ead62d9edb114fd49ae26b16a00d58e`); **one
member changed — the test file — and no product byte changed in this claim.**

### What was revalidated before anything was written

All 28 members of `candidate-365537` re-hashed to their recorded candidate
digests, and all 28 `base` digests re-hashed to the current tree: no drift.
The base has moved from `19f02ce1` to `39e83746` and the only `v12/` change
between them is `DESIGN.md` gaining the **SCH-1a** paragraph this Work
implements, so every pinned decision still holds.

### The review runtime's own bytes and its full bound identity

`:789` compared the original and successor IMPLEMENTATION roots and `:750`
proved the review container started; neither read what the INDEPENDENT
REVIEWER was handed — and the whole finding is a Job whose delivery is the
installed document while its declared identity is its own task's, so the role
that JUDGES the proposal is exactly the one that must not be reading the
deployment's task.

Three cases, over the same real loop that already carries the retry to both
containers:

- **the bytes**, read off disk out of the review attempt's own input root:
  they are the inherited task and not the installed document, and read as the
  document they are they carry the ORIGINAL creation's `task_id`, its
  statement, every acceptance criterion and every selected work and test scope
  path, its template version and its Work — compared against
  `creation.resolution_of`, which is the store's own provenance row and
  re-owns and re-digests itself before answering, rather than against this
  fixture's request. The source half (`schema`, `verification`, `source_root`,
  `source_profile`, `declared_base`) is compared against the INSTALLED
  document, because those are the deployment's facts and `job_task.SUBSTITUTED`
  is a closed two-member rule.
- **the identity, in all four places it has to agree**: the manifest the
  review stage is served under, the manager's durable `recorded_input_of`, the
  launch context (asserted by having `launch.adopt` ACCEPT it — that function
  refuses a context it would not have written), and the stage-less adapter a
  restart identifies the attempt through. The Job-scoped projection of all of
  them is the identity the retry's own PERSISTED SUBMISSION declares, read out
  of the document the store kept, and that is the original creation's.
- **both runtimes as one question**, because "both runtime input identities"
  is a claim about their AGREEMENT: two attempts, two input roots, the same
  inherited bytes, each role's durable record equal to the document that role
  is served under, each role's launch context adopted, one Job-scoped identity
  across the pair — and neither role recorded against the installed manifest.
  The two roles' installed manifests are ONE document in this deployment, so
  that last assertion is the one that distinguishes the delivery from it; an
  earlier draft asserted the two recorded digests DIFFER and was measuring the
  fixture, which is why it says what it says now.

### The connected admission adapter boundary

The review is right that the cases above cannot establish this: every one of
them composes `test_fresh_attempt`'s `FakeBinding`, which that suite says in
as many words RECORDS a binding rather than performing one. Recording is what
lets a case assert what travelled, and it is also why none of them shows the
real adapter selecting a worker for a retry that inherited its task.

`TheConnectedAdmissionCarriesTheTask` asks the same outcome of the real
owners, on `test_connected_creation`'s really-installed fixture: the instance
is installed by `bootstrap.main`; the prior Job is created by the real
`job_manager.main create`, so it is template-created with its own task and its
own derived identity; and the admission is composed with
`fresh_attempt_ports.DeploymentBinding`, `WorkAuthorization`,
`InstanceOwnership` and `HostExclusion` over that instance's own
configuration, Authority, install document and stores. Five cases:

- the real adapters **bind and select**: the retry is admitted, the Work is
  reused rather than minted, and the binding the real selector answered names
  the configured workers for BOTH stages (`implementation: [impl-a]`,
  `review: [review-a]`) — which is the fact a recording fake cannot produce.
  It is PUBLISHED: `bootstrap.prepare` revalidated the whole deployment and
  wrote `deployment.json`, `install-inputs.json` grew the retry additively,
  and the producer, declared base and canonical target are DERIVED from the
  Job being replaced. The task is reached through the lineage, the retry's own
  row holds no copy and no creation, and its submission declares the
  creation's identity.
- **the operand is what decides**, asked of the real adapter directly: the
  same published binding, configuration and submitted operands answer both
  stages when asked with the inherited task and NOTHING when asked with
  `None` — which is what this adapter was asked with before W364834. And
  `None` is still right for a Job that has no own task: asked for the
  installed identity the same adapter answers the installed pool, which is
  the legacy behaviour this Work preserves.
- **reopen and replay**: a second manager incarnation, a second control-store
  handle and a second real `DeploymentBinding` over the configuration the
  first one published answer the recorded document exactly, with one retry row
  and one published binding rather than two.
- **retry of retry**: the second retry's row names the first, which has no
  creation of its own, so the task is reached by walking to the creation that
  made it; the real selector serves the second retry for both stages on that
  answer and its submission still declares the original creation's identity.
- **missing provenance** is refused by the real selector. What this case
  FOUND, and what it now asserts instead of what I first wrote: the
  reservation and the BINDING both survive the refusal, because `_owned`'s cut
  B publishes the Work authorization and the binding before the servability
  question is asked — "the binding is inert until the Job exists, so it is the
  safe half to publish first" — and `_incomplete` says the rest out loud. So
  the case asserts what is true: an inert binding, no Job (`job_of` refuses
  with "this store holds no such Job"), no stage, nothing a serving loop could
  dispatch, and the reservation still `intended`. Then it restores the
  creation's own bytes and runs the SAME request again, which resumes from the
  reservation and completes — proving the intermediate state is resumable
  rather than wedged, which is the only thing that makes that ordering safe.

### Missing, substituted and inconsistent provenance, through the dispatch

`:857`/`:870` cover a cycle and a legacy absence. The FINDING's actual
sentence — provenance that is missing, substituted or inconsistent must refuse
truthfully without false success or dispatch — is asked of the DISPATCH, after
a CLEAN admission, because that is where a wrong answer becomes a container
running the wrong task. Five cases, each editing the lineage origin's row by
hand (no operation writes any of them) AFTER the retry is admitted, then
driving the ordinary ticks:

- **missing** (`NULL`): the lineage answers `None`, which is an ordinary
  answer for a Job that never had a task — and that is exactly why it matters
  here, because this Job's declared identity IS its task's.
- **substituted**: another creation's coherent task document in that row.
- **inconsistent**: one member edited, so the row is provenance for a Job
  whose task document names another.
- **not a document at all**: recorded because it is the case a reader expects
  to behave differently and it does not.
- **emptied to `''`**: refused one layer earlier, by `created_job_rows` owning
  the row on the way out, as `integrity/schema` naming `task_document`.

In every case the retry's stage stays `queued` with no allocation, the ONLY
runtime row in the control store is the first attempt's `destroyed` one, and
the loop's own act report says `admit` / `deferred` with the operand that
disagreed — for the first four, "no worker this deployment configures for the
'implementation' stage can serve Job ...: {...: ['the submitted input']}",
which is `servable_workers` refusing before the scheduler reserves anybody.
The first attempt's input root still carries its own bytes, its recorded
identity is still recorded and its allocation is still its own producer's.

**Said plainly because a reader will expect otherwise:** an unreadable task
document and a substituted one are refused by the SAME rule, as a digest
disagreement, because the host does not parse this document —
`single_worker._task_bytes` holds the delivered bytes to the artifact that
names them and `claude_agent` owns that vocabulary at the receiving end. That
is the right rule: it needs no second reader of the task contract to be
correct, and it refuses without false success or dispatch either way. No
product change was made for it.

### One structural change, and no product change

`TheRetriedJobReachesItsOwnRuntimes`'s fixture is now the base class
`RetryRuntimeCase` and its cases are unchanged in its subclass. Nothing moved
but the class statement those methods sit under: this suite's rule is "THE
HELPERS ARE BORROWED AND THE CASES ARE NOT", a sibling that subclassed the
case class would re-run all eleven of its assertions under two more names, and
a sibling that re-bound its `setUp` would meet zero-argument `super()`
resolving against a class it is not an instance of.

### Verification

Candidate root `/tmp/w365848`, the whole tracked tree at `39e83746` with the
accepted candidate and this one's test file overlaid; `PYTHONPATH=src:.`

- **`tests.tools.test_retry_task_lineage`: 37 OK** (24 accepted, 13 new).
- **Whole `tests/job_manager`: 1375 OK.**
- **Seven tools suites** (retry_task_lineage, connected_creation,
  creation_ports, job_task_delivery, fresh_retry_line_recovery, bootstrap,
  instance): **429 OK**.
- **`test_single_worker` + `test_stage_execution`: 720 cases, 719 OK and ONE
  FAILURE that is PRE-EXISTING ON THE BASE** —
  `AFaultedTerminalSurvivesTheContainerThatWroteIt`
  `.test_a_real_observing_status_run_mutates_no_durable_state`, which finds
  `control.sqlite3-wal`/`-shm` and four input-root files added by an observing
  status run. No product byte changed in this claim or in the accepted
  candidate, so neither can cause it; the proof is the same class run in
  `/tmp/w365848-base`, the tracked tree at `39e83746` with NO overlay at all,
  failing identically. Both logs are in the evidence directory.

`evidence/claim-365848/` with `HOW-THESE-WERE-RUN.txt` and all five logs.

### Cost

Reading `_bound`, `_owned`'s cut order, `_composed`, `_settled`/`_over`,
`creation.job_task_of`/`created_job_rows`/`resolution_of`/`_task_agrees`,
`job_task`'s whole composition, `single_worker._matches`/`_for_job`/
`_given_for`, `stage_execution._served_deployment`/`servable_workers`/
`_disagreements`/`_job_workers`, `fresh_attempt_ports.DeploymentBinding`,
`tools/job_manager`'s `_fresh_attempt` and `_create`, and the connected
creation and review-delivery fixtures. Probes: four — the connected admission
over the real adapters, the replay and retry-of-retry over them, the
provenance corruptions through the dispatch (which is where the unreadable and
empty-text cases were measured rather than guessed), and the review runtime's
four identity sites. Test runs: the lineage suite eight times (three failing —
a helper named `created` that shadowed the owning fixture's and made
`answered` recurse into it, an assertion that the two roles' recorded digests
differ when this deployment configures one manifest for every worker, and
`submission.job_of` refusing an absent Job rather than answering `None`);
`tests/job_manager` twice; the tools group twice; the wider pair twice; the
base tree once. No live provider, no container engine, no deployed-instance
mutation, no version-control operation.

### Boundaries

No Git operation of any kind, and no fixture that performs one was run. The
canonical `v12/python` tree is byte-unchanged and **no product file changed in
this claim**. `candidate-364837/`, `candidate-364962/`, the accepted child
`findings/finding-fresh-retry-line-recovery/` and every earlier evidence
directory are preserved exactly; I wrote `candidate-365848/`,
`evidence/claim-365848/` and this section. The bound `FINDING.md`/`PLAN.md` and
every review are the reviewer's and are unmodified.
