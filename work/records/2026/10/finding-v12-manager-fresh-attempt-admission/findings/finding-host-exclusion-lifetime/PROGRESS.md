# W359719 — implementer progress

The reviewer recorded the absence of this file as an operational finding under
preparation claim360416. It is created here, by the implementing claimant, at
the start of this child's first execution. No earlier implementation of this
child exists.

## claim360435 — the exclusion outlives every borrower, and the host is proved

Answers the parent review's R13 and R14 under handoff360423, against this
child's `FINDING.md` and `PLAN.md`. Cumulative candidate `candidate-360435/`,
manifest `69553a3977f143cec187df89e75364f5ef5f413f75c40a78af02f5af46b8b1ce`,
fourteen members consumed from the **accepted** sibling `candidate-359821`
(`9f06dbe3…`); **five** changed in this slice — `workspaces.py`,
`fresh_attempt.py`, `fresh_attempt_ports.py`, `job_manager.py` and
`test_fresh_attempt.py`. Base `302453869d07eb5579e79a6572586d3c3cf62a5c`; the
canonical tree is untouched and every parent and sibling candidate is
preserved. The accepted submission behaviour is carried forward unchanged.

### R13 — a check before an acquisition is not an acquisition

`hold_manager_instance` is a *lifetime* hold: a manager takes it once and keeps
it until it stops. A fresh attempt needs the same exclusion for the length of
its own work, and the first cut built that out of "ask whether it is held, then
acquire, then release unless it was borrowed". Two overlapping admissions both
saw it unheld, both received the same cached descriptor, and the **first** one
to finish closed it while the second was still running.

`workspaces.borrow_manager_instance` is the owning module's own counted hold.
Each borrower increments; the last one out releases, and only if this chain of
borrows is what acquired the guard rather than finding a serving owner already
holding it. The count lives beside `_HELD_GUARDS` and is cleared by the same
fork handler, so the process-global cache and the fork rule are exactly as they
were — a case asserts the child inherits no borrow. `borrowers_of` is a reader
for the cases.

### R14 — a caller naming a path twice is not evidence

The CLI passed the `--control` operand to the host port as the path that
operand was supposed to be checked against. `instance_identity(root)` now
derives the four store paths from `bootstrap.layout` and the Authority from the
emitted configuration — facts about the deployment rather than echoes of the
command line. The command holds every operand to them before opening anything.

And the check is not only the command's. Each port declares which instance it
answers for, from its own owner's facts, and `fresh_attempt._one_instance`
refuses before the first read unless they are one instance *and* that
instance's Authority is the one this Job store is bound to. A port that
declares nothing is unbound and accepted — the unit stand-ins answer for no
deployment, and refusing them would be this rule dictating how a caller must
build its ports rather than that they agree.

### A flaky case I shipped two slices ago, found and fixed

`test_same_incarnation_concurrent_requests_bind_once` passed every time I ran
it and then failed on the first full-suite run this claim. The barrier only
guaranteed both admissions had *entered* the ownership port, not that they
overlapped at the invocation lock: when the winner finished first, the loser
found nothing in flight and both were admitted. That is a defect in the case,
not in the product, and it went out in `candidate-359459`. The fake now holds
the winner inside its critical section until the loser has tried, so the
interleaving the case claims is the one it gets. **Four consecutive whole-suite
runs** are recorded in `SUITES.txt` rather than one.

### Verification

`evidence/claim-360435/`. **Red to green:** the two new classes produce one
failure and thirteen errors against the accepted `candidate-359821` host bytes
and pass here. The one *behavioural* red is
`test_overlapping_lifetimes_in_either_exit_order` — the probe's own
interleaving, where the first context exits first; the rest are the new API
and the identity binding being absent, and I am labelling them as that rather
than counting thirteen reds. `R13-R14.txt` is the verbose run.

Twelve new cases: nested and sequential overlap, both exit orders, an error
exit, a serving owner never released by any borrower, the borrow count
returning to zero, the fork rule; an unrelated control store refused before any
effect, ports answering for two deployments refused, a configuration for
another Authority refused, the right instance still admitting with every port
bound, and the actual CLI refusing a store the instance does not own.

Focused suite **113 cases**. Whole `tests/job_manager` **1131 cases, one
failure** on each of four consecutive runs — the same pre-existing
`test_native_permission` case. `test_bootstrap`, `test_scheduler_trace`,
`test_single_worker`, `tests.manager.test_custody` and
`tests.manager.test_workspaces` 780 cases with the one pre-existing
`test_single_worker` failure. The four inventory suites produce the identical
116 failures as the canonical base.

### Limits

No engine, provider, runtime or credential is reached, so **that a fresh
attempt succeeds is still not proved**. The guard and invocation-lock proofs
spawn real second processes; the serving-manager refusal at the manager
boundary still uses a recorded port, because standing up a real serving loop
needs the engine. `tests.tools.test_stage_execution` was not re-run: no member
it exercises changed since the parent candidate, where it passed 477 cases.

### Cost

Nine focused-suite runs (four failing: two assertions about a fixture
configuration shape, a `ControlStore` opened with a `Path` where it requires
text, and the flake above); two edit scripts that aborted on their own
assertions, one of which left the file needing repair; one deliberate red run
against the accepted predecessor; the whole `tests/job_manager` package eight
times, four of them consecutively for the flake check; the tools and workspace
group once at 97s; the inventory suites once against the retained canonical
baseline. No product execution, no instance operation, no total manufactured.

### Boundaries

No Git, no live provider, engine, credential read, install, deployment or
retained-instance operation. No store opened, copied or traversed outside the
disposable ones the cases create. The accepted `candidate-359821`, the parent
and sibling candidates and the reviewer's records and evidence are untouched. I
wrote only this child's candidate, its evidence and this file.

## claim360582 — the lifetime is atomic, and no owner is excused the question

Answers `review-2026-10-24T00-41-56Z.md` R16 and R17 under handoff360571.
Candidate `candidate-360582/` supersedes `candidate-360435` (preserved),
manifest `3f8a3a1c8319fe423979f705708c6fedf0003acbd2e29f47437151c3acc1709b`,
fourteen members; **four** changed this round -- `workspaces.py`,
`fresh_attempt.py`, `fresh_attempt_ports.py` and `test_fresh_attempt.py`.
Base `302453869d07eb5579e79a6572586d3c3cf62a5c`; canonical tree untouched; the
accepted submission behaviour and every prior candidate are preserved.

### R16 — ordering is not synchronisation

The counted borrow obtained the cached guard and THEN registered, so a probe
could pause between the two while the last borrower decremented to zero and
closed the descriptor. Sequential contexts passed; two threads did not.

`_BORROWING` is one module-level lock. Asking whether a guard stands,
acquiring it and registering the borrow are now one critical section, and
decrementing and releasing are another. The lock covers this module's own
bookkeeping and the bounded `open`/`flock`/`fstat` beside it -- **the yield is
outside it**, so an admission's whole body never runs under a mutex.
Nonblocking process exclusion, error cleanup and the fork rule are unchanged.

### R17 — an undeclared port is not an exempt one

`_one_instance` skipped ports that declared nothing, so a real `HostExclusion`
built with no identity sat beside three bound ports and an admission read an
unrelated empty control store as this instance's history. Every port must now
declare, and the stand-ins declare a synthetic instance exactly as the real
ports declare a real one -- **being a fixture is not a reason to be trusted
without saying what you answer for**, which is the reviewer's point and the
right one.

Two owner capabilities are also proved at birth rather than at first use: the
host port refuses a control store that is not the one the instance owns, and
the Work authorization port refuses an Authority whose uuid is not the
instance's. A port that could be constructed over another deployment and only
refuse later is one a caller can hold while believing it is bound.

### Verification

`evidence/claim-360582/`. **Red to green:** the two new classes produce five
failures and one error against `candidate-360435` and pass here; `R16-R17.txt`
is the verbose run. The R16 reds are both behavioural -- the paused
interleaving and the four-thread contention case.

Eight R16 cases and four R17 cases. The lifetime case pauses the second
borrower exactly where the probe did, then attempts the first borrower's exit
on another thread and asserts it **cannot complete** until the registration is
done; the instance stays excluded from a spawned process throughout. Every
`multiprocessing` spawn happens on the main thread -- spawning from a worker
thread of a process that also forks guards is its own hazard, and a case about
a lock should not become a case about that.

Focused suite **125 cases**, three consecutive runs. Whole `tests/job_manager`
**1143 cases, one failure** on each of three runs -- the same pre-existing
`test_native_permission` case. `test_bootstrap`, `test_scheduler_trace`,
`test_single_worker`, `test_custody` and `test_workspaces` 780 cases with the
one pre-existing `test_single_worker` failure. The four inventory suites
produce the identical 116 failures as the canonical base.

### Limits

No engine, provider, runtime or credential is reached, so **that a fresh
attempt succeeds is still not proved**. The guard proofs spawn real second
processes; the serving-manager refusal at the manager boundary still uses a
recorded port. The fork case calls the fork handler directly and is not itself
proof of a real fork -- the reviewer said so of its predecessor and it is still
true. `tests.tools.test_stage_execution` was not re-run: no member it
exercises changed since the parent candidate, where it passed 477 cases.

### Cost

Twelve focused-suite runs (six failing: the Authority uuid read as a call
rather than a property, four port-binding updates after identity became
mandatory, and a first cut of the lifetime case that spawned from a worker
thread and hung until its timeout); one deliberate red run against the prior
candidate; the whole `tests/job_manager` package six times, three of them
consecutively; the tools and workspace group once at 96s; the inventory suites
once against the retained canonical baseline. No product execution, no instance
operation, no total manufactured.

### Boundaries

No Git, no live provider, engine, credential read, install, deployment or
retained-instance operation. No store opened, copied or traversed outside the
disposable ones the cases create. Every prior candidate and the reviewer's
records and evidence are untouched. I wrote only this candidate, its evidence
and this file.

## claim360765 — one ownership rule, the store bound, and a child that is not stuck

Answers `review-2026-10-24T01-09-18Z.md` R18, R19 and R20 under handoff360761.
Candidate `candidate-360765/` supersedes `candidate-360582` (preserved),
manifest `74ee29399f6e12e408799f3f8654e4183398873ad31b361e2dd5d415e249acb9`,
**fifteen** members -- `job_manager/store.py` joins this round. Three changed
or new: `store.py`, `workspaces.py` and `test_fresh_attempt.py`. Base
`302453869d07eb5579e79a6572586d3c3cf62a5c`; canonical tree untouched; the
accepted submission behaviour and every prior candidate are preserved.

### R18 — sharing an Authority does not make two deployments one

`_one_instance` compared four roots and one Authority uuid and never looked at
the Job store it was about to write to. Two real deployments sharing an
Authority admitted one instance's Job through the other's ports.

`JobStore` now carries `database`, read from its own connection -- the fact
`ControlStore` has had since W270664 F2, for the same reason -- and
`_one_instance` refuses when it is not the store the selected instance owns.
A case prepares a **second real instance with the same Authority uuid** through
the real bootstrap and composes its four genuine ports against this store: the
admission refuses and neither deployment is touched.

### R19 — lifetime owners and borrowers are both holders

The borrow chain remembered whether IT had acquired the descriptor and released
on that stale fact, so a serving lifetime taken *during* an admission was handed
the same cached object and had it closed underneath it.

There is now one rule: `_HOLDERS` counts every holder, `hold_manager_instance`
increments it (including on the cached path) and `release` decrements, closing
only at zero. A borrow is a hold that releases itself. Both directions are
driven -- a serving lifetime taken during a borrow survives the borrow's exit,
and a borrow survives a serving lifetime ending under it.

The cache read, the acquisition and the count are also one critical section,
which fixed something the previous round had not: two first-time holders
arriving together raced, and the loser was denied by its own sibling's `flock`.
My four-thread contention case found that.

### R20 — a child cannot release a lock it inherited

`_forget_inherited_guards` now replaces `_BORROWING` with a fresh `RLock`. The
reviewer's bounded probe is a case: a helper thread holds the real mutex, the
main thread forks, and the child borrows an otherwise-unheld instance under a
five-second alarm and reports through its exit code. It is reaped with a
bounded wait. Python's multithreaded-fork warning is expected and the case says
so -- this checks the guard's own fork contract rather than recommending forks.

### Verification

`evidence/claim-360765/`. **Red to green:** the three new classes produce four
failures and two errors against `candidate-360582` and pass here; `R18-R20.txt`
is the verbose run. Four of the six are behavioural -- the cross-instance
admission, both R19 directions, and the child that hung -- and two are the new
`holders_of` reader being absent, which I am labelling as that.

Focused suite **150 cases**. Whole `tests/job_manager` **1168 cases, one
failure** on each of three runs -- the same pre-existing `test_native_permission`
case. `test_bootstrap`, `test_scheduler_trace`, `test_single_worker`,
`test_custody`, `test_workspaces` and `job_manager.test_store` 827 cases with
the one pre-existing `test_single_worker` failure; `test_store` and
`test_workspaces` are in that list deliberately, because this round changed
their subjects. The four inventory suites produce the identical 116 failures as
the canonical base.

### Limits

No engine, provider, runtime or credential is reached, so **that a fresh attempt
succeeds is still not proved**. The serving-manager refusal at the manager
boundary still uses a recorded port. The fork case now performs a **real**
`os.fork`, which its predecessor did not -- that qualification is retired, and
no other is. `tests.tools.test_stage_execution` was not re-run: no member it
exercises changed since the parent candidate, where it passed 477 cases.

### Cost

Fourteen focused-suite runs (seven failing: the stand-in identities after the
Job store joined the instance identity, a barrier whose party count did not
match its waiters, a contention case that deadlocked because acquisition was no
longer serialized, and three edit scripts -- one of which re-indented four
functions into one and had to be restored from the candidate); one deliberate
red run against the prior candidate; the whole `tests/job_manager` package six
times, three consecutively; the tools, workspace and store group once at 97s;
the inventory suites once against the retained canonical baseline. No product
execution, no instance operation, no total manufactured.

### Boundaries

No Git, no live provider, engine, credential read, install, deployment or
retained-instance operation. No store opened, copied or traversed outside the
disposable ones the cases create. Every prior candidate and the reviewer's
records and evidence are untouched. I wrote only this candidate, its evidence
and this file.

## claim360912 — the final release is one transition

Answers `review-2026-10-24T01-31-06Z.md` R21 under handoff360909. Candidate
`candidate-360912/` supersedes `candidate-360765` (preserved), manifest
`164546f94cc88854271d623a149835e1283e76a4f8d9049bdc68a402656ab13f`, fifteen
members; **two** changed this round -- `workspaces.py` and
`test_fresh_attempt.py`. Base `302453869d07eb5579e79a6572586d3c3cf62a5c`;
canonical tree untouched; every prior candidate and the accepted submission
behaviour are preserved.

### A correction to my own last entry, first

The reviewer is right: **four** paths changed in claim360765, not three. I
named `store.py`, `workspaces.py` and `test_fresh_attempt.py` and omitted
`fresh_attempt.py`, which carried the `_one_instance` Job-store binding --
the R18 correction itself. The manifest recorded its changed bytes correctly,
so the candidate was never misrepresented; the prose was. I have counted the
changed paths off the manifest this time rather than from memory.

### R21 — serializing acquisition is not serializing the transition

`release` decremented and retired under `_BORROWING` and then left that
critical section before calling `_disown`. A new `hold_manager_instance`
could observe the still-cached object, count itself in, and be handed a
descriptor the previous release was already committed to closing -- and a
spawned process then took the instance while that new lifetime believed it
held it.

The retirement and the close now happen inside the same critical section as
the count that decided them. A new holder therefore waits, finds no cache
entry, and opens its own descriptor with its own `flock`: a valid guard
rather than a retiring one.

### Verification

`evidence/claim-360912/`. **Red to green:** the new class produces one failure
against `candidate-360765`'s `workspaces.py` and passes here. That one is the
whole finding; the other two cases in the class already held and are labelled
as the regression cover they are. `R21.txt` is the verbose run.

Three cases: a new holder blocked until the release completes and then given a
live descriptor, with a spawned process refused while it is inside; the cache
retired together with the descriptor; and an error exit from a borrow retiring
it the same way.

Focused suite **159 cases**. Whole `tests/job_manager` **1177 cases, one
failure** on each of three runs -- the same pre-existing
`test_native_permission` case. `test_bootstrap`, `test_scheduler_trace`,
`test_single_worker`, `test_custody` and `test_workspaces` 780 cases with the
one pre-existing `test_single_worker` failure. The four inventory suites
produce the identical 116 failures as the canonical base.

### Limits

No engine, provider, runtime or credential is reached, so **that a fresh
attempt succeeds is still not proved**. The serving-manager refusal at the
manager boundary still uses a recorded port.
`tests.tools.test_stage_execution` was not re-run: no member it exercises
changed since the parent candidate, where it passed 477 cases.

### Cost

Three focused-suite runs, zero failing; one deliberate red run against the
prior candidate; the whole `tests/job_manager` package six times, three of
them consecutively; the tools and workspace group once at 96s; the inventory
suites once against the retained canonical baseline. No product execution, no
instance operation, no total manufactured.

### Boundaries

No Git, no live provider, engine, credential read, install, deployment or
retained-instance operation. No store opened, copied or traversed outside the
disposable ones the cases create. Every prior candidate and the reviewer's
records and evidence are untouched. I wrote only this candidate, its evidence
and this file.
