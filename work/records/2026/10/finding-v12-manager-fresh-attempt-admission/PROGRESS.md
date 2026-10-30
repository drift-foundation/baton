# W358969 — implementer progress

## claim358995 — the manager operation, its CLI verb and its proof

Answers `FINDING.md` and DESIGN REC-7 under handoff358992. Base commit
`302453869d07eb5579e79a6572586d3c3cf62a5c`; every path this candidate touches
was clean in the working tree at claim start and is **unchanged there now** —
the candidate is `candidate-358995/`, manifest
`88a1ef8c6b624f8e10909de9268bb0f8d25e913f0de7805cdd5a765d9b45cfd3`, which
records each member's base digest beside its candidate digest.

### What is delivered

A supported fresh-attempt admission that a Job manager owns, reached through
the installed command as

    baton-v12-stack manager --store … --incarnation … --authority-uuid … \
        fresh-attempt --prior-job quickstart-c --control … --authority … \
        --instance …

and nothing else is required of the operator. No Job id, no Work id, no
submission id, no document: the identities are derived and the specification
is the prior Job's own.

Eleven files. Three are new — `job_manager/fresh_attempt.py` (the operation),
`tools/fresh_attempt_ports.py` (the three owner adapters) and
`tests/job_manager/test_fresh_attempt.py` (42 cases). Four product files
change: the Job store schema gains one relation at version 8, `documents`
gains one contract, the package exports the operation, and
`tools/job_manager.py` gains the verb. `tools/stage_execution.py` gains a
public rule discussed below. Three existing test files gain one line each.

### The shape, and why it is this one

**A new Job on the PRIOR Work.** The pilot's helper chose a new Work and then
measured that new workers were needed to carry it, because
`stage_execution._disagreements` compares a worker's manifest Work against the
Job's binding. Two new workers per retry is per-retry configuration, which
REC-7 says is not required. The prior Work is already authorized, already
bound and already served by the configured workers, and the failed Job holding
it is over — so the fresh attempt reuses it and the only configuration that
changes is one additive `job_bindings` entry. A caller may still select
another Work with `--work-id`; the operation then creates it if the Authority
does not hold it, under a replayable operation identity.

**The specification is carried as BYTES, not rebuilt.** `_prior` reads the
prior submission document out of the store and copies its Job entry, changing
exactly three things: the Job id, the stages' Work if one was selected, and
the dependency references that named the old Job. Rebuilding from the `jobs`
and `stages` rows would normalize a `/1` document into a `/2` identity and
turn an absent `execution_limits` member into an empty one — so the preserved
3600/900 the pilot cares about is preserved by not being touched.

**No retry was invented.** `submission.submit` already journals by submission
identity and `_unclaimed` already refuses a Job identity another submission
holds; `episodes.restart_abandoned_correction` already requires receipts an
expired credential does not produce. All three are correct and none of them is
a retry. This is the operation that was missing, composed from them.

### The cuts, and what a crash leaves behind

Reservation first, in this store, under a PRIMARY KEY taken inside the write
lock — so two concurrent requests for one identity cannot both win. Then the
host is asked **again**, because a check taken before a reservation is a check
about the past. Then the binding, which is inert while no Job exists. Then the
submission, which is where the Job becomes real. Then the completion.

A case drives the cut that matters: the deployment owner dies after writing
the binding, the intent row is left `intended` with no `admitted_at`, and the
same command run again finishes rather than refusing itself as a duplicate.

### Enforcement is in the manager, and the adapters hold no rule

Each port reports a fact from an owning API and performs at most one named
effect. `HostExclusion` composes `attempts.runtime_recovery_inventory`;
`WorkAuthorization` is `project_work` plus `create_work`, with absence
confirmed by `work_creation` rather than by reading a refusal's prose;
`DeploymentBinding` prepares the additive binding through `bootstrap.prepare`
and asks the scheduler's own selector what can serve it. **No store is opened
that was not handed in, no database file is read directly and nothing is
copied** — the boundary the previous review refused a helper for.

A CLI case proves the command holds no rule: it passes `job_id`, `work_id` and
`submission_id` through as `None`, hands over the three ports, and opens the
control store **read-only** — `open_readonly` once, `open` never, so an
admission cannot change the evidence it is judging.

### One product seam added, and why it is not a copy

`stage_execution.servable_workers` is the second half of `_job_workers`, split
out unchanged; `_job_workers` is now that function plus the two facts only a
live deployment holds. The manager must know whether a fresh Job's stage could
be served **before** the Job exists, and until now the only way to ask needed
a `Deployment` object — which needs a control store and an authority the
question has nothing to do with. That is exactly the gap the superseded
helper's `MISSING_PROJECTIONS` named, and the alternative actually tried was a
second copy of the comparison in a script. A case asserts the two share one
rule by reading `_job_workers`' own source.

### What it refuses, every one driven

Unknown host evidence (REC-4's "unknown is not permission", and the helper's
mistake); a runtime that is `running` or `uncertain`; cleanup this host still
owes; a workspace resource not returned; a Job with a stage still live; a Job
settled but not failed; a completed Job; a Work that is not open; a deployment
where the selector can serve no worker; a deployment binding the fresh Job to
another Work; a second fresh attempt at one failure, refused durably **naming
the first**, because a fork is two Jobs on one Work; the same identity with
changed operands, refused as an `operation-collision` with the first admission
intact; and an absent owner port. In every refusal case the fresh Job is
absent from `jobs` and the reservation is absent from `fresh_attempts`.

A detail worth naming: the pilot's own shape is implementation `exceptional`
and review `blocked`, and `blocked` is not a terminal state. A blocked stage
is settled **only when every gate it names can no longer open** — so the real
failure admits and a blocked stage waiting on something still running does not.

### Evidence

`evidence/claim-358995/`. Focused suite 42 cases, 0 failures. Whole
`tests/job_manager` suite 1060 cases with **one** failure,
`test_native_permission.NativeStageComposition.test_the_native_factory_delivers_the_policy_to_both_stage_workers`,
which is **pre-existing**: `PREEXISTING.txt` is that same test failing the
same way on the canonical tree at HEAD, with `BATON_V12_STACK_TEST_ROOT` set,
before any byte of this candidate. It builds its disk-backed root inside the
checkout and `held_configuration` refuses it; it is recorded here as an
operational finding and is not this Work's scope. `tests.tools.test_bootstrap`
and `tests.tools.test_scheduler_trace` 279 cases, OK;
`tests.tools.test_stage_execution` 477 cases, OK, run against the
`servable_workers` refactor. The four inventory suites produce **the identical
116 failures** on candidate and canonical base — `INVENTORY-BASE.txt` and
`INVENTORY-CANDIDATE.txt` diff to nothing added, which is the tree-wide
condition already recorded under W325959.

### Limits, stated rather than left to be found

- **The deployment binding adapter is not driven against a built instance in
  these cases.** `DeploymentBinding.bind` calls `bootstrap.prepare`, which is
  the supported in-place call the pilot measured, and the whole
  `tests.tools.test_bootstrap` suite passes beside it — but no case here
  installs an instance and then adds a binding to it end to end. What **is**
  proved deterministically is the rule the adapter feeds:
  `servable_workers` against the real deployment-document fixture, including
  the Work disagreement and the producer-affinity narrowing. A live
  instance-level case is the first thing to add.
- **Nothing was run against instance 3** or any retained instance, and no Job
  was submitted, served or started anywhere.
- The engine, the provider and the Authority are never reached in these
  cases: the Job store and the Worker Manager control store are real and on
  disk, the operations object is `test_status`'s own strict fake, and the
  Authority port is a fake in the operation cases and a mock in the CLI case.
  **A fake provider is not live authentication**, and whether a fresh attempt
  SUCCEEDS is not proved — only that it is admitted, bound, selectable,
  unique, replayable and linked to what it replaces.
- `successor_of` derives `<base>-retry-<n+1>`. A prior Job whose own name ends
  in `-retry-<digits>` continues that chain; anything else starts one. This is
  a routine implementation choice under the FINDING's "Work identity policy
  and exact syntax are implementation choices".

### Cost

Read-only research across `submission`, `store`, `schema`, `documents`,
`projection`, `episodes`, `attempts`, `tokens`, `authority/api`, `bootstrap`,
`stack_command` and `stage_execution`. Test runs: the focused suite five
times during development (three failing — two on my own wrong assertions about
which refusal a case reaches, one on a persisted document I expected decoded),
`tests/job_manager` twice whole, `tests.tools.test_stage_execution` once whole
at 252s, `tests.tools.test_bootstrap` plus `test_scheduler_trace` once at 72s,
and the four inventory suites twice — once on the candidate and once on the
canonical tree, which is what makes the 116 a baseline rather than a claim.
No product execution, no instance operation, no total manufactured.

### Boundaries

No Git. No change to any file outside `candidate-358995/`'s eleven members —
the canonical tree is untouched, including the dirty files the PLAN says to
preserve. No live provider, engine, credential read, deployment, install or
retained-instance operation. No store opened, copied or traversed outside the
disposable ones these cases create. The superseded helper and its historical
manifests under `../finding-v12-native-pilot-instance-packet/` are untouched.
Per the PLAN's split I wrote only the candidate, its evidence and this file,
leaving FINDING.md, PLAN.md and the reviews to the reviewer.

## claim359299 — the four blockers, corrected and driven

Answers `review-2026-10-23T21-38-33Z.md` (R1–R4 and its remaining acceptance
note) under handoff359295. Candidate `candidate-359299/`, manifest
`7ee13790535c2ecf43f25ffbd2526c448a9fd17ec42be4638813bc3636d1e1cb`, twelve
members; the manifest records each member's base digest, its candidate digest
and whether it changed since `candidate-358995`, which is preserved untouched.
Base `302453869d07eb5579e79a6572586d3c3cf62a5c`. The canonical tree is still
byte-unchanged.

**All four findings were real and all four are reproduced as cases.** The
reviewer's probe is the better part of this round: every one of them was a
defect my own 42 cases had been written around.

### R1 — the adapter could never have run

`bind` wrote `job_work_id` into a bootstrap Job input. That is the EMITTED
binding's spelling; the input contract is `bootstrap._JOB`, which names
`work_id` once. The real `prepare` refused every call. Corrected, and now
driven against a **real disposable instance** built by `ValidFixture` and real
`bootstrap.prepare`: the additive bind lands, the prior binding survives
byte-for-byte with its own source worker and declared base, and both stages of
the fresh Job are selectable through the real emitted configuration.

The review also required that an installed input not be assumed equal to the
current configuration. `_reconciled` proves it: a configuration binding a Job
the install document does not name refuses **by name**, before anything is
prepared, instead of reaching `conflicts` late with a sentence about a Job that
"stops being named".

### R2 — two requests forked one failure

`_unforked` was a SELECT before the transaction, which is a read-then-write
check, and the reviewer's two-connection probe drove both past it.
`fresh_attempts_one_successor` is now a UNIQUE index on `prior_job_id`: two
writers meet at the index inside the loser's own transaction, and the loser
reads who won and is told. The probe is now a case — two real Job store
connections, two supported identities, synchronized at the host read — and
exactly one is admitted with exactly one successor recorded. The reservation
also checks the ordinary `jobs` table inside the same lock, so an identity
another submission already holds is refused before any owner is touched.

### R3 — the selector was asked a question it could not fail

`serving` built the Job's input digest and every stage's profile out of the
implementation worker it was about to compare them against. A configuration
consistent with itself, and a review stage judged by the implementation
worker's profile. The port now takes the **composed submission's own** stage
and job operands and passes them through untouched; `_bound` supplies them. A
connected case mutates the submitted input and the admission refuses before the
Job exists, and another asserts both roles select under their own profiles.

### R4 — an effect before the operation was admitted

`_authorized` ran before `_reserved`, so a changed request minted a Work and
then refused as a collision. The reservation is now first and nothing outside
this store is touched before it; a connected case asserts the rejected Work
does not exist on the real Authority afterwards and the configuration is
unchanged.

The second half of R4 was the publication cut. `bind` now writes the install
document **first** and prepares second — the surviving inconsistency is then an
input naming a Job the configuration does not yet bind, which is harmless and
repairable, rather than a configuration the input cannot reproduce, which
`conflicts` refuses and which would make every later retry impossible. A case
drives the interrupted state and resumes it without appending a second entry.

And the refusals stopped lying. Every refusal past the reservation now names
the reserved identity, says the attempt is **incomplete rather than undone**,
and gives the one way forward.

### The remaining acceptance note, answered honestly

`runtime_recovery_inventory` documents that its caller must exclude concurrent
writers. **No supported operation reserves the control store against its own
serving loop for a read-only consumer.** I did not simulate one. The read is
now taken inside `ControlStore.snapshot()`, which is the strongest supported
thing — it makes the answer describe one state of that store rather than
several — and the residual is named in `fresh_attempt_ports.UNRESERVED_EXCLUSION`
as an operational finding: a coherent observation is not a reservation, which
is why the manager asks again after its reservation. An operator who needs the
stronger statement stops the serving loop first.

### A measured fact worth keeping

Selecting a fresh Work now has a case of its own, and it refuses: the real
Authority mints the Work and then **no configured worker can serve the stage**,
because the installed manifests name the instance's Work. That is the
measurement behind reusing the prior Work by default, and it is now asserted
rather than argued.

### Evidence

`evidence/claim-359299/`. Focused suite **55 cases, 0 failures** (42 before,
plus the real binding adapter, the connected retry, the race, the ordering and
the fresh-Work measurement). Whole `tests/job_manager` **1073 cases, one
failure** — the same pre-existing `test_native_permission` case baselined last
claim in `evidence/claim-358995/PREEXISTING.txt`, unrelated and not repaired.
`tests.tools.test_stage_execution` 477 OK; `tests.tools.test_bootstrap` plus
`test_scheduler_trace` 279 OK. The four inventory suites produce the identical
116 failures as the canonical base — `comm -13` is empty.

### Limits

The engine and the provider are still never reached and no runtime is started,
so **that a fresh attempt succeeds is still not proved** — what is proved is
that it is admitted, bound, selectable under its own operands, unique against a
real race, replayable, and linked to what it replaces. The operations object
remains the manager's own strict fake; `fixtures.FakeOperations` now takes an
`authority_uuid` so a case against a real instance derives episode identities
in that instance's namespace, defaulting to the fixture Authority so every
existing case means what it meant. Nothing ran against instance 3.

### Cost

Five focused-suite runs (four failing: the port signature change, a shared
SQLite handle across threads, a missing `_publish_install` I deleted with the
block I replaced, and the fresh-Work case that turned out to be measuring the
real refusal); `tests/job_manager` three times whole; `test_stage_execution`
once at 251s; bootstrap plus scheduler-trace once at 72s; the inventory suites
once more against the retained canonical baseline. No product execution, no
instance operation, no total manufactured.

### Boundaries

No Git, no live provider, engine, credential read, install, deployment or
retained-instance operation. No store opened, copied or traversed outside the
disposable ones the cases create. `candidate-358995` and the reviewer's
`evidence/review-359263/` are untouched, as is the superseded helper under
`../finding-v12-native-pilot-instance-packet/`. I wrote only the new candidate,
its evidence and this file.

## claim359459 — ownership across the effects

Answers `review-2026-10-23T22-00-41Z.md` R5, R6 and R7 under handoff359455.
Candidate `candidate-359459/`, manifest
`b99ba986ddbd849ef3f92e4edcdeaf722433be0ccf63addd7c175de3d8ed0359`, thirteen
members; `candidate-359299` and `candidate-358995` are preserved untouched and
the manifest records what changed since the last one. Base
`302453869d07eb5579e79a6572586d3c3cf62a5c`; the canonical tree is still
byte-unchanged.

All three findings were real. The thread running through them is one thing:
the first cut had **identity** ownership and no **execution** ownership.

### R5 — a replayed intent did not own the operation

A reservation says an identity is spoken for. It says nothing about who may
act on it, so two identical concurrent requests -- one inserting the intent,
one replaying it -- both went on to publish a binding.

Two mechanisms now, because there are two kinds of collision.

`fresh_attempts.holder` is a column taken by compare-and-swap inside the same
lock the reservation is taken in, under its own journalled operation
(`fresh_attempt.acquire`, keyed by job AND holder so a second holder cannot
replay the first one's success). The loser is told who holds it. A holder
re-running under the same manager incarnation continues its own interrupted
work; a different incarnation is refused **naming the holder**, because
deciding that an unseen manager has stopped is the inferred cessation this
operation refuses everywhere else. It is deliberately not a lease with a
clock, for the same reason.

And the real publication adapter is now a critical section: an exclusive
`flock` around read/modify/prepare/publish, and a temp name unique to the
writer instead of one fixed `.tmp` path. Two concurrent binds of **unrelated**
Jobs both land and the configuration names all three -- driven, with the
leftover-temp-file check in the same case.

### R6 — ordinary submission ignored the reservation

`submission._unclaimed` knew about half the owners of a Job identity. It now
reads `fresh_attempts` in the same lock as its existing conflict decision and
refuses durably unless the submission **is** the one the reservation exists to
admit. Both orders are driven: an ordinary submission attempted mid-admission
is refused and the retry still finishes; an ordinary Job that came first
refuses the retry before anything is reserved or published.

This is a change to a shared product path and it is the right place for it --
the reservation lives in this store, so the conflict belongs in this store's
own conflict decision rather than in another read before the binding.

### R7 — the exclusion was documented away, and now it is taken

You were right that the blanket claim was not established.
`workspaces.hold_manager_instance` is the product's own guard, described by
its own docstring as what a manager takes "before it dispatches work or
mutates a managed resource", and `single_worker` takes it for the second
reason -- writing a configuration into a manager's store. A fresh attempt does
exactly that, so it takes the same guard, composed as an `ownership` port from
the instance's **own** configuration and held across the host read, the Work
authorization, the binding and the submission.

What that buys, stated exactly: a serving manager holding the instance makes
the admission **refuse** rather than race it; two admissions in two processes
cannot both act on one instance; and the host evidence is read while the guard
is held, which is the difference between a coherent observation and an
exclusion. What it does not buy, equally exactly: it is not cessation
evidence, so the runtime and token axes are still read and still fail closed
on unknown. `UNRESERVED_EXCLUSION` is gone -- there is a mechanism now, not a
warning.

The guard is proved against itself in a **separate process**: the in-process
cache correctly answers the guard this process already holds, which is not the
question, so the probe forks and the second holder is denied by name.

### Also corrected

A refusal at the submission boundary is now reported as the incomplete
admission it is, naming the reserved identity and the continuation, rather
than surfacing the generic submission refusal -- which is what your R6
reproduction saw.

### Evidence

`evidence/claim-359459/`. Focused suite **66 cases, 0 failures** (55 before,
plus the identical-request race, holder continuation, foreign-holder refusal,
both ordinary-submission orders, guard held-and-released, serving-manager
refusal, the three real-guard cases and the concurrent real publication).
Whole `tests/job_manager` **1084 cases, one failure** -- the same pre-existing
`test_native_permission` case. `tests.tools.test_bootstrap`,
`test_scheduler_trace` and `test_single_worker` 522 cases with one failure,
`test_a_real_observing_status_run_mutates_no_durable_state`, reproduced
identically on the canonical tree at HEAD in `PREEXISTING-SINGLE-WORKER.txt`.
`tests.tools.test_stage_execution` 477 OK. The four inventory suites produce
the identical 116 failures as the canonical base.

### Limits

No engine, provider, runtime or credential is reached, so **that a fresh
attempt succeeds is still not proved**. The guard proof forks a real second
process; the serving-manager refusal at the manager boundary uses a recorded
port, because standing up an actual serving loop would need the engine. The
operations object remains the manager's own strict fake. Nothing ran against
instance 3.

### Cost

Nine focused-suite runs during development (four failing: the port signature
change, two barrier placements that were testing the wrong boundary once the
holder CAS started refusing earlier, and a missing `ownership` keyword in two
direct `admit` callers); `tests/job_manager` three times whole;
`test_stage_execution` once at 252s; bootstrap/scheduler-trace/single-worker
once at 92s; the inventory suites once more against the retained canonical
baseline; one baseline run of the single-worker case on the canonical tree.
No product execution, no instance operation, no total manufactured.

### Boundaries

No Git, no live provider, engine, credential read, install, deployment or
retained-instance operation. No store opened, copied or traversed outside the
disposable ones the cases create. Prior candidates and the reviewer's evidence
directories are untouched. I wrote only the new candidate, its evidence and
this file.

## claim359603 — exclusive invocation, immutable intent, borrowed guards, positive resource evidence

Answers `review-2026-10-23T22-22-03Z.md` R8, R9, R10 and R11 under handoff359599.
Candidate `candidate-359603/`, manifest
`ad9a63db1fb83e015cfbe17f73d386d3f2a4ba92087e322cf9fb3d1cb43cab4d`, fourteen
members. Base `302453869d07eb5579e79a6572586d3c3cf62a5c`; canonical tree still
byte-unchanged; the three prior candidates are preserved.

**First, a correction to my own last entry.** I wrote that
`UNRESERVED_EXCLUSION` was gone. It was not -- the constant and the stale
commentary were still in `fresh_attempt_ports.py`, and the reviewer was right
to say so. They are gone now, and what replaced them is a mechanism rather
than a shorter warning: see R11 below. Prose that describes behaviour the
bytes do not have is worse than no prose.

### R8 — a holder is a name; an invocation is a lock

`_holder` is the manager incarnation plus the control store, which is a stable
NAME. Two concurrent calls under one incarnation both satisfied it, and the
previous race only varied incarnations, so it never asked this question.

`ownership.invocation(job_id)` is the lock: a non-blocking exclusive `flock`
on this admission's own file. Two descriptors contend whether they are in two
processes or two threads of one, so a concurrent invocation is refused rather
than admitted -- and the kernel drops the lock when a holder dies, so an
interrupted admission leaves nothing to clear and the same request simply
resumes. That is deliberately not a lease with a clock: a deadline would have
to guess when an unseen manager stopped, which is the inferred cessation this
operation refuses everywhere else. `holder` keeps its separate job -- who may
RESUME -- which is exactly the distinction the review asked for.

Driven: two threads, the SAME incarnation, synchronized in the ownership port
before either takes the lock. One admission, one bind effect, and the loser is
told it is in flight. Separately, the real lock is driven across two spawned
processes, including that a different identity is not blocked by it and that
the lock is free again afterwards.

### R9 — a reservation names an intent, not a name

`fresh_attempts.submission_signature` records the canonical signature of the
document the admission composed, and `submission._unclaimed` now exempts only
a submission whose own signature matches. A same-name/different-document
submission is refused before any Job or stage insert; the retry's own document
still passes. The reservation additionally checks the submission identity
itself against `submissions` before any effect, so that collision is met
before the Work and the binding rather than after.

**One decision worth naming: that refusal is ORDINARY, not durable.** A
durable refusal is a committed outcome for an operation identity, and this
operation identity is derived from the submission id -- which belongs to the
reservation holder. Sealing an intruder's rejection under it would permanently
poison the one submission the reservation exists to admit. I found this
because the first cut did exactly that and the retry could then never finish.
A case proves the retry completes after the rejection.

### R10 — a borrowed guard is left as it was found

`hold_manager_instance` returns the descriptor this process already holds when
it already holds one. The adapter released it unconditionally, so an admission
inside a serving composition dropped an exclusion its owner still believed it
had. `workspaces.held_manager_instance(place)` is a new bounded reader -- the
review's own "add the bounded capability rather than bypass it" -- and the
port asks it BEFORE acquiring: a borrowed guard is never released, on the
error path as well as the ordinary one. Driven with the real guard and a
spawned process, which stays excluded across both exits.

### R11 — an absent token is uncertainty

`attempts.runtime_recovery_inventory` says in its own words that an absent
workspace token is "explicit uncertainty, never a synthetic non-launch proof",
and the candidate only refused when a token existed. Now a missing token
refuses unless never-launched is POSITIVELY established: the runtime axis is
`not-started` AND no runtime identity was ever minted. A `not-started` axis
beside a minted runtime is a contradiction, not proof, and is refused too.

And the store must be this instance's. `HostExclusion` is given the control
store path the instance's own configuration names and refuses a handle that is
not it, because absence in an arbitrarily supplied store is evidence about
another deployment. Every answer now carries the host that gave it, so an
absence is attributable to a named store rather than to "somewhere".

### Evidence

`evidence/claim-359603/`. Focused suite **78 cases, 0 failures**. Whole
`tests/job_manager` **1096 cases, one failure** -- the same pre-existing
`test_native_permission` case. `test_bootstrap`, `test_scheduler_trace`,
`test_single_worker` and `tests.manager.test_custody` 643 cases with the one
pre-existing `test_single_worker` failure baselined last claim.
`tests.tools.test_stage_execution` 477 OK. The four inventory suites produce
the identical 116 failures as the canonical base.

### Limits

No engine, provider, runtime or credential is reached, so **that a fresh
attempt succeeds is still not proved**. The runtime and token evidence in the
unit cases is supplied at the port boundary; what is proved is the DECISION
the manager makes about it, not that a container really stopped. The real
guard and the real invocation lock are driven with spawned processes; the
serving-manager refusal at the manager boundary still uses a recorded port.
Nothing ran against instance 3.

### Cost

Eleven focused-suite runs (five failing: the two port-contract updates, a
barrier placed where the invocation lock now refuses first, and two assertions
about durability that were wrong until the poisoning problem above was
understood); `tests/job_manager` twice whole; `test_stage_execution` once at
251s; the bootstrap/single-worker/custody group once at 95s; the inventory
suites once against the retained canonical baseline. No product execution, no
instance operation, no total manufactured.

### Boundaries

No Git, no live provider, engine, credential read, install, deployment or
retained-instance operation. No store opened, copied or traversed outside the
disposable ones the cases create. Prior candidates and the reviewer's evidence
directories are untouched. I wrote only the new candidate, its evidence and
this file.
