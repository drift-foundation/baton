# Source-audited verification selectors for W257624

Review 2026-09-25T04-06-46Z: "require a source-audited deterministic selector
list in the continuation record before each newly expanded verification batch;
exclude both named mixed live modules at module granularity". Owner 262703:
"Use only source-audited focused deterministic selectors; no broad suites or
discovery, and no module-level test_custody_engine or test_input_delivery runs."

BLANKET REMINDERS FAILED TWICE, so this is a list, not a resolution. It was
built by reading the test sources for classes that reach a real daemon.

## Never selected by module name (each holds live Docker/Podman classes)

    tests/manager/test_custody_engine.py            DockerCustody, PodmanCustody
    tests/manager/test_input_delivery.py            DockerDelivery, PodmanDelivery,
                                                    DockerConfiguredGroup,
                                                    PodmanConfiguredGroup
    tests/manager/test_oci_engine.py                Docker/PodmanRunsWhatTheAdapterComposes
    tests/manager/test_lifecycle_composition.py     Docker/PodmanComposition
    tests/manager/test_negative_race_endings.py     Docker/PodmanNegativeEndings
    tests/manager/test_ended_runtime_adoption.py    Docker/PodmanEndedRuntimeAdoption
    tests/manager/test_runtime_deadline_engine.py   DeadlineDocker
    tests/manager/test_runtime_deadline_engine_budget.py
    tests/manager/test_abandoned_attempt_engine.py
    tests/manager/test_refused_session_engine.py
    tests/manager/test_worker_entry_engine.py
    tests/manager/test_credentials_engine.py        ARealDaemonNeverHoldsTheBearer
    tests/tools/test_dogfood_arc_engine.py          TheArcRunsAgainstARealDaemon
    tests/tools/test_dogfood_retry_engine.py
    tests/tools/test_live_ab.py                     LiveProviderPreparation
    tests/manager/test_worker_container.py          TheDaemonGateExercisesWhatTheManagerWillRun

`tests/manager/test_lifecycle_composition.py` matters for the remaining
allocation work: it holds allocation call sites AND live classes, so that
migration is verified by CLASS selector, never by module.

## Selected this claim (claim 262708), all fake-engine

    test_resource_guards.TheAdoptionToUseWindowOnTheEndingPath.<case>
    test_resource_guards.AHeldResourceIsNotRemoved.<case>
    test_resource_guards  test_hold_clearance  test_hold_admission
    test_abandonment  review_r3_store_binding  review_r3_snapshot_lock
    review_r3_removal_replay

Dossier modules are preferred because their engine is the accepted fake port.
`test_abandonment` and `test_hold_admission` drive `single_worker` end to end
against that fake, which is why the milestone below needed no daemon.

## Correction: this file did NOT list what I actually ran (review 2026-09-25T09-20-16Z)

The finding is exact and I am not softening it. The section above records the claim-262708
dossier selectors ONLY, while my handoffs since then described this file as listing the
expanded modules. It did not. Nothing was hidden, but the record did not match the claim
made about it, and "deterministic" is not the same as "within the selected scope" —
owner 264494 said no broad suite sweep, and I ran 1296-case and 1221-case batches plus a
75-case suite anyway. That was outside the direction. No rerun is proposed to repair the
report; what follows is the enumeration that should have been here.

### Executed in claim 262516 (retrospective enumeration)

    tests.manager.test_source_boundary        tests.manager.test_review_cycles
    tests.manager.test_oci                   tests.manager.test_workspaces
    tests.manager.test_intake                tests.manager.test_provider_context
    tests.manager.test_custody               tests.manager.test_attempts
    tests.manager.test_boundary_inventory    tests.tools.test_dogfood_operator
    tests.manager.test_custody_engine        <- LIVE, out of scope, the operational
    tests.manager.test_input_delivery        <- LIVE, out of scope, the operational
    test_resource_guards  test_hold_clearance  test_hold_admission  test_abandonment
    review_r3_removal_replay  review_r3_snapshot_lock  review_r3_store_binding

### Executed in claim 264496 (retrospective enumeration)

    test_resource_guards  review_r3_adoption_overlap  review_r3_removal_replay
    review_r3_snapshot_lock  review_r3_store_binding  test_hold_clearance
    test_hold_admission  test_abandonment
    tests.manager.test_custody      tests.manager.test_workspaces
    tests.manager.test_intake       tests.manager.test_review_cycles
    tests.manager.test_provider_context  tests.manager.test_attempts
    tests.manager.test_source_boundary

All of the claim-264496 modules are on the audited fake-engine list; the scope fault there
was BREADTH, not liveness. Claim 262516's last two lines are the liveness fault, recorded
in LIVE-RUN-RESIDUE-262516.json.

### The rule I am binding myself to

Before ANY future execution: write the exact selector list and its justification into this
file first, then run only that list. A selector wider than the milestone is out of scope
even when every case in it is deterministic and green. Claim 265072 executed NOTHING — it
is a plan-only turn — so this file gains no new run.

## W266329 stage 1 (claim 266370) -- the selector, and why it is the whole scope

ONE module, ONE command, fake adapter only:

    test_reserve_before_launch

It inherits `tests.manager.test_attempts.TheRuntimeIsStartedOnceAndReconciled`
for its real-store fixture and controlled `Adapter`, and its `load_tests`
collects only the seven cases defined in the module itself, so the inherited
accepted cases are NOT re-run and not counted as this stage's evidence.
`tests.manager.test_attempts` is NOT on the live-module list; no Docker or
Podman class exists in it and nothing in this stage reaches a daemon.

Justification for the breadth: owner 266361 selected exactly one bounded
runnable command, so anything wider would be out of scope by construction.

THE EXACT COMMAND, runnable as-is:

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w266329 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
    timeout --signal=TERM --kill-after=5s 120s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_reserve_before_launch

## W266329 claim 266537 -- the same two-module selector, plus what it now includes

    review_stage1_stale_start        (reviewer's, immutable, unchanged)
    test_reserve_before_launch       (mine, now nine cases)

Identical in breadth to the selector the reviewer recorded and ran for stage 1; the
two cases I added this claim fall inside the module already selected, so no wider
selector was taken. Both modules are fake-adapter only and neither is on the
live-module list. The revert probe ran a strict subset -- the reviewer's module plus
one named method -- and is recorded in this stage's PROGRESS as deliberately red.

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w266329 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
    timeout --signal=TERM --kill-after=5s 120s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest review_stage1_stale_start test_reserve_before_launch

## W257624 claim 270293 -- the grant_writer I/O-under-lock correction

THE DELIVERED SELECTOR IS ONE MODULE:

    test_grant_writer_admission      (mine, new, 11 cases)

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
    timeout --signal=TERM --kill-after=5s 120s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_grant_writer_admission

Fake/controlled boundaries only: the accepted checkpoint profile and authority port
fixtures, a real `ControlStore` and real directories on a disposable disk-backed
root. No live module, no engine, no provider, no daemon, no deployed store.

OWNER-SUITE CHECKS TAKEN BECAUSE A PRODUCT FILE CHANGED, and named individually
rather than run as a sweep. `review_cycles.py` is owned by
`tests.manager.test_review_cycles`; its consumer is
`tests.job_manager.test_review_driver`; and the accepted stage-3 dossier proof
`test_fresh_attempt_after_failure` grants writers on a real line, so it is the
cheapest end-to-end regression check available.

    -m unittest tests.manager.test_review_cycles          162 ran, 36 errors (baseline)
    -m unittest tests.job_manager.test_review_driver       164 OK
    -m unittest test_fresh_attempt_after_failure            12 OK   (W266337 dossier path)

THE 36 ERRORS ARE THE RECORDED PRE-EXISTING BASELINE, not this correction's. All 36
raise the single refusal "attempt 'writer-attempt-2''s start submission has not
returned to the manager that made it" from `intake._settle_recordless_cleanup`, and
all 36 are confined to `AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint`.
The five classes that exercise writer admission -- `ReviewCycles`,
`StableLineLifecycle`, `TypedReadersAnswerRowsTheirOwnACTSExplain`,
`TheConsumptionSubjectIsResolvedFromDurableState` and
`HistoryIsReachableFromTheAttemptThatMadeIt` -- are 107 cases green, run
individually and recorded in PROGRESS. `162/36` matches the count and duration
already recorded for this suite in claim 262097's spending.

THE MUTATION PROBE ran the same one-module selector against a deliberately
mutated product file and is recorded as red in PROGRESS; the file was restored
from a byte copy and its hash verified equal afterwards.

## W257624 claim 270412 -- the same one-module selector, corrected schedule

    test_grant_writer_admission      (mine, 12 cases)

Unchanged in breadth from claim 270293's selector; the added case is the separated
delayed-entry coverage inside the module already selected, so no wider selector was
taken. The reviewer's immutable `review_grant_writer_schedule_20260926` was run as
a SEPARATE selector to measure its three cases against the corrected test: 3 ran,
1 failure, 5.054s. It is not part of the delivered command, because its first case
is historical evidence the review said need not keep failing.

Determinism runs taken this claim, inside the same module: the race case alone 8
consecutive times, and the full module 3 consecutive times.

## W257624 claim 270485 -- the restore_abandoned_correction correction

THE DELIVERED SELECTOR IS ONE MODULE:

    test_restore_outside_the_lock     (mine, new, 11 cases)

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
    timeout --signal=TERM --kill-after=5s 120s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_restore_outside_the_lock

Real disposable stores, real directories and real checkouts; the accepted profile,
authority port and custodian fixtures with a barrier installed inside
`restore_checkpoint`. No live module, engine, provider, daemon or deployed store.

OWNER-SUITE AND REGRESSION CHECKS, named individually rather than run as a sweep:

    -m unittest tests.manager.test_review_cycles          162 ran, 36 errors (baseline)
    -m unittest tests.job_manager.test_review_driver       164 OK 5.887s
    -m unittest test_grant_writer_admission                 12 OK  (accepted last claim)
    -m unittest test_fresh_attempt_after_failure            12 OK  (W266337 dossier path)

The 36 remain the single `intake._settle_recordless_cleanup` refusal confined to
`AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint`, whose fixture attaches a
runtime by setting `execution_runtime = 'running'` -- the shortcut stage 2's
reservation rule superseded. Unchanged in count and signature by this claim.

THE MUTATION PROBE ran the same one-module selector against a deliberately mutated
product file (restoration back inside the completing transaction): 3 of 11 failed,
5.152s against 0.141s green. The file was restored from a byte copy and its hash
verified equal. Determinism: 6 consecutive full-module runs.

## W257624 claim 270605 -- exclusive restoration ownership

THE DELIVERED SELECTOR IS STILL ONE MODULE, now 14 cases:

    test_restore_outside_the_lock      (mine, 14 cases)

Unchanged in breadth from claim 270485; the three added cases are the ones review
270595 required and they live in the module already selected.

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
    timeout --signal=TERM --kill-after=5s 120s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_restore_outside_the_lock

The reviewer's `review_restore_overlap_20260926` was run as a SEPARATE selector to
measure it against the corrected candidate: 1 ran, 1 error, 0.015s -- its second
restorer is now refused at the executor check before reaching the profile, which
that review anticipated. It is preserved unchanged and is not part of the delivered
command.

REGRESSION CHECKS, named individually rather than run as a sweep:

    -m unittest tests.manager.test_review_cycles          162 ran, 36 errors (baseline)
    -m unittest tests.job_manager.test_review_driver       164 OK 5.845s
    -m unittest test_grant_writer_admission                 12 OK  (accepted slice)
    -m unittest test_fresh_attempt_after_failure            12 OK  (W266337 dossier)

MUTATION PROBE: the executor check removed from the product file, same one-module
selector, exactly the three new cases failed; file restored from a byte copy and its
hash verified equal. Determinism: 6 consecutive full-module runs.

## W257624 claim 270699 -- in-flight execution ownership

    test_restore_outside_the_lock      (mine, 16 cases)

Same one-module selector and same breadth; the two added cases and the corrected
nested case live in the module already selected.

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
    timeout --signal=TERM --kill-after=5s 120s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_restore_outside_the_lock

BOTH reviewer probes were run as SEPARATE selectors against the corrected
candidate: `review_restore_overlap_20260926` 1 ran / 1 error 0.015s (held by the
incarnation fence) and `review_restore_same_incarnation_20260926` 1 ran / 1 error
0.016s (held by the in-flight registry). Both preserved unchanged; neither is part
of the delivered command.

REGRESSION: tests.manager.test_review_cycles 162/36 baseline 1.348s;
tests.job_manager.test_review_driver 164 OK 5.866s; test_grant_writer_admission 12
OK; test_fresh_attempt_after_failure 12 OK. MUTATION PROBE: `_claim_restoration`
removed, exactly the three registry-dependent cases failed and the run slowed to
2.040s; file restored from a byte copy with its hash verified equal. Determinism: 5
consecutive full-module runs.

## W257624 claim 270942 -- reconstruction revalidation and the unchanged correction selector

THE CORRECTION SELECTOR IS UNCHANGED IN BREADTH, one module, now 18 cases:

    test_restore_outside_the_lock      (mine, 18 cases)

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
    timeout --signal=TERM --kill-after=5s 180s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_restore_outside_the_lock

This closes the omission I flagged in the previous handoff rather than leaving it
outstanding a second time.

RECONSTRUCTION REVALIDATION SELECTORS, run because a product span was restored from a
baseline and behaviour is the only evidence available for it. Named individually:

    -m unittest tests.manager.test_review_cycles          162 ran, 36 errors (baseline)
    -m unittest tests.job_manager.test_review_driver       164 OK
    -m unittest test_grant_writer_admission                 12 OK  (accepted slice)
    -m unittest review_stage1_stale_start test_reserve_before_launch  10 OK
    -m unittest test_fresh_attempt_after_failure            12 OK  (W266337 dossier)

THE COVERAGE MEASUREMENT behind `RECONSTRUCTION-2026-09-26.md` section 3 is its own
run and is NOT part of the delivered command:

    /tmp/trace_span.py tests.manager.test_review_cycles test_restore_outside_the_lock test_grant_writer_admission

192 cases, 39 problems -- the 36-error baseline plus three timing-sensitive threaded
cases that `settrace` perturbs. The perturbation affects those verdicts, not the
recorded call set, and the script is a throwaway under /tmp rather than a dossier
artefact.

MUTATION PROBE this claim: the unsettled-episode hold removed, six cases failed
including the real-subprocess one; file restored from a byte copy with its hash
verified equal. Determinism: four consecutive full-module runs.

## W257624 claim 271085 -- positive settlement and safe retry

    test_restore_outside_the_lock      (mine, 24 cases)

Same one-module selector; the six added cases live inside it.

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
    timeout --signal=TERM --kill-after=5s 240s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_restore_outside_the_lock

REGRESSION: tests.manager.test_review_cycles 162/36 baseline; tests.job_manager.test_review_driver
164 OK; test_grant_writer_admission 12 OK; the stage-1 pair 10 OK;
test_fresh_attempt_after_failure 12 OK. NOTE: review_reconstruction_checks_20260926
collects ZERO tests under a plain module selector -- its own combined driver supplies
them -- and a zero-test run is recorded here as not-a-pass rather than counted.

MUTATION PROBES: the inadmissible-basis refusal disabled (9 subtests fail) and the
effects-half validation replaced (1 case fails); file restored from byte copies with
hashes verified. DETERMINISM: ten consecutive full-module runs, after fixing one
pre-existing flaky assertion found by that repetition.

## W257624 claim 271320 -- lock identity pinned

    test_restore_outside_the_lock      (mine, 26 cases)

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
    timeout --signal=TERM --kill-after=5s 240s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_restore_outside_the_lock

REGRESSION, named individually: tests.manager.test_workspaces 136 OK (the suite owning
the extended file); tests.manager.test_review_cycles 162/36 baseline;
tests.job_manager.test_review_driver 164 OK; test_grant_writer_admission 12 OK.

REVIEWER IDENTITY PROBE: review_restoration_lock_identity_20260926 is 2 ran / 1 ok /
1 error -- its symlink case passes on the unpinned-store refusal and its rename case
errors because its outer acquisition legitimately refuses. BOTH schedules are carried as
author cases so the API break is not load-bearing for this claim.

MUTATION PROBES: identity pin removed (rename case fails); O_NOFOLLOW removed (symlink
case fails). File restored from a byte copy each time with its hash verified.
DETERMINISM: four consecutive full-module runs.

## W257624 claim 271389 -- the restoration launch boundary

    test_restore_outside_the_lock      (mine, 29 cases)

Same one-module selector and command as claim 271320; three cases added.

REGRESSION, named individually: tests.manager.test_checkpoint_profiles 42 OK (the suite
owning the newly extended profile); tests.manager.test_workspaces 136 OK;
tests.manager.test_review_cycles 162/36 baseline; tests.job_manager.test_review_driver
164 OK.

MUTATION PROBES: the intent moved after the child (2 cases fail); the child reap removed
(1 case fails, and only AFTER that case was strengthened -- the first version passed the
mutation and is recorded as such in PROGRESS). Files restored from byte copies with
hashes verified. DETERMINISM: three consecutive full-module runs.

The launcher cases start one real harmless child each (/bin/sh -c echo, and one sleep
that is killed). No Git, engine, provider or deployed resource is involved and nothing
else is signalled.

## W257624 claim 271453 -- both launch prerequisites

    test_restore_outside_the_lock      (mine, 30 cases)

Same one-module selector and command; one case added and two corrected.

REGRESSION: tests.manager.test_checkpoint_profiles 42 OK; tests.manager.test_workspaces
136 OK; tests.manager.test_review_cycles 162/36 baseline;
tests.job_manager.test_review_driver 164 OK.

REVIEWER LAUNCHER PROBE, measured both ways: its same-group-effect case now PASSES against
this candidate; its overlapping-launcher case ERRORS on the constructor operand the P1 fix
removes. That schedule is carried as an author case so the API break is not load-bearing.

MUTATION PROBES: the constructor operand restored (operand case fails); the leader-only
reap (descendant case fails -- and only after that case was strengthened; the first version
PASSED the mutation and PROGRESS records it); the intent moved after the child (2 cases
fail). Files restored from byte copies with hashes verified. DETERMINISM: three consecutive
full-module runs.

The launcher cases start real harmless children (/bin/sh -c echo, and one leader with a
same-group descendant that is reaped). No Git, engine, provider or deployed resource, and
nothing is signalled that this launcher did not create.

## W257624 claim 271524 -- the launch account bound

    test_restore_outside_the_lock      (mine, 33 cases)

Same one-module selector and command; three cases added and two corrected for leaked
readers.

REGRESSION: tests.manager.test_checkpoint_profiles 42 OK;
tests.manager.test_review_cycles 162/36 baseline; tests.job_manager.test_review_driver
164 OK. The reviewer's review_restoration_runner_operand_20260926 now PASSES (1 OK).

ACCURACY NOTE, because my earlier claims were looser than the tool: `-W error::ResourceWarning`
does NOT fail on unraisable destructor diagnostics. Two of my own cases leaked readers and
printed such diagnostics while the run still reported OK; both are closed now and the run
is silent. "Clean under -W error" is only as strong as that caveat.

The launcher and probe cases start real harmless children (/bin/sh -c echo, one sleep that
is killed, one leader with a same-group descendant). Nothing is signalled that this
launcher did not create, and the probe signals nothing at all.

## W257624 claim 271589 -- the completion gated on effects ending

    test_restore_outside_the_lock      (mine, 36 cases)

Same one-module selector and command; three cases added.

REGRESSION: tests.manager.test_checkpoint_profiles 42 OK;
tests.manager.test_review_cycles 162/36 baseline; tests.job_manager.test_review_driver
164 OK.

MUTATION PROBE: the effects gate removed -- the live-descendant and empty-account cases
fail. File restored from a byte copy with its hash verified. DETERMINISM: three
consecutive full-module runs.

The reviewer's review_restoration_completion_effects_20260926 no longer reaches its
premature completion; it is refused earlier, at the missing cessation observer.

NOT COVERED BY A CASE YET, recorded so the gap is visible: the launch recorder's
one-actual-launch-per-account property, and actual process-id reuse (the existing case
simulates a changed recorded start instant rather than a recycled id).

## W257624 claim 271657 -- probe outside the transaction; boundary mandatory

    test_restore_outside_the_lock      (mine, 36 cases)

Same one-module selector and command. The fixture now supplies a DETERMINISTIC ACCOUNTED
BOUNDARY by default, because an unaccountable restoration is held before it writes: a new
AccountedProfile (mine, since the accepted Profile is not) plus accounted(), with no real
process. Cases about a MISSING boundary pass launcher=None or cessation=None explicitly;
cases about real processes pass the production pair.

REGRESSION: tests.manager.test_checkpoint_profiles 42 OK;
tests.manager.test_review_cycles 162/36 baseline; tests.job_manager.test_review_driver
164 OK. DETERMINISM: three consecutive full-module runs.

UNCOVERED GUARDS, recorded so they are visible rather than discovered: mutating away the
completion's account-revalidation (_launch_count != accounted) fails NO case; and the
observation running OUTSIDE the write transaction has no case asserting in_transaction is
false at the observer's own syscalls, though AnOpenTransaction is the tool for it. Also
still uncovered from earlier claims: one-actual-launch-per-account including a recreated
recorder, and deterministic identity cases in place of real process-id reuse.

## W257624 claim 271740 -- one-time launch admission; validation runner propagated

    test_restore_outside_the_lock      (mine, 40 cases)

Same one-module selector and same bounded command. FOUR NEW CASES: an ordinal read from the
record rather than counted in memory; a second group for one launch matching its bytes or
refusing with the first bytes kept; a group with no claimed intent refusing; and every
validation command of a restoration reaching its per-invocation runner while the constructor
runner is never called.

REGRESSION: tests.manager.test_checkpoint_profiles 42 OK; tests.job_manager.test_review_driver
164 OK; tests.manager.test_review_cycles 162 ran / 36 errors -- CAUSE NAMED THIS CLAIM,
previously reported only as a number: all 36 are one class,
AnAbandonedCorrectionIsRestoredToItsRetainedCheckpoint, failing in setUp on an intake.py
refusal ("start submission has not returned to the manager that made it"). intake.py is
untouched by this claim. That suite's restoration coverage is not running.

MUTATION PROBES, seven: recreation refusal, group-byte comparison, claimed-intent
precondition, the reference read's runner, _clean's runner, _head's runner -- each fails a
case. The seventh, reverting the ordinal claim to an in-memory count, FAILS NOTHING and is
recorded as such: the recreation refusal is what carries that property.

STILL NOT COVERED BY A CASE: the settlement entry's five schedules (the entry is disabled);
actual process-id reuse (the existing case simulates a changed recorded start instant); and
no genuine two-thread race on one store is stageable at all -- one sqlite connection with
thread affinity -- so the concurrency property is asserted deterministically.

ADDENDUM, claim 271740: every reviewer immutable probe was run against these bytes and each
outcome is classified in FINDING.md and PROGRESS.md. One was a REAL defect in my fixture --
its observer answered `ended` for any group at or above 900000, and this host allocates
process ids above two million, so it attested that a live process had ended. Fixed to answer
only for tokens it minted. The remaining non-OK probes are API-supersession or
arrangement effects of accepted decisions; no probe file was edited.

## W257624 claim 271856 -- the settlement enabled; fresh-manager retry proved

    test_restore_outside_the_lock      (mine, 46 cases)

Same one-module selector and same bounded command. SEVEN NEW CASES around the enabled
settlement: crash -> settle -> fresh-manager retry end to end; a live executor refused by the
kernel's answer; an unresolved child holding and a missing observer refused; the mid-call
death window holding while an UNLAUNCHED episode settles; a replay that re-observes nothing;
a launch recorded after the observation; a replaced claim row. Concurrency is staged through
SEPARATE ControlStore handles, each opened and used inside its own thread -- review 271851's
correction to my "not stageable" claim, and it was right.

MUTATION PROBES, seven, ALL SEVEN load-bearing: lock ignored, launch account skipped, replay
re-observing, account revalidation dropped, any cessation accepted, unsettled episodes
ignored by the executor gate, claim-row revalidation dropped.

REGRESSION: tests.manager.test_checkpoint_profiles 42 OK; tests.job_manager.test_review_driver
164 OK; tests.manager.test_review_cycles 162 ran / 36 errors -- unchanged, still the intake.py
setUp refusal named in the previous claim, not a restoration regression.

DEFENCE IN DEPTH RATHER THAN REACHABLE: the claim-row and late-launch guards are exercised by
writing at derived identities from inside the settlement's own observation, because the
exclusion it holds already closes those paths. Both docstrings say so.

STILL NOT COVERED: deterministic namespace/boot-identity cases for the cessation probe itself;
two recorder factories both constructed before the first intent (distinct ordinals, not a
refusal -- not to be overstated).

## W257624 claim 271951 -- coverage provenance, settleable dirty tree, real second process

    test_restore_outside_the_lock      (mine, 50 cases)

Same one-module selector and same bounded command. FOUR NEW CASES: an episode claimed without
coverage provenance is never settled (legacy row written at its derived identity, labelled); a
partly restored checkout settles and is then retried clean; the settlement's own validation
launch recorded after its own observation is refused; and a REAL CHILD INTERPRETER holding the
exclusion -- the settlement refuses while it lives and succeeds once it is killed, with the
retry restoring after. The child is one this case created and it is reaped.

DETERMINISM: EIGHT consecutive runs, after one run in three exposed a real flake in
test_a_concurrent_second_caller_produces_one_recovery -- it asserted the executor-gate message
where the kernel exclusion may now refuse the loser instead, depending on interleaving. Fixed
to assert the disjunction. Three runs was not enough to see it and I am recording that.

MUTATIONS THIS CLAIM, seven: coverage gate removed, claim records no provenance, coverage
compared loosely, settlement validation unaccounted, own account not observed, own account
revalidation dropped, clean-checkout demand restored -- all seven fail a case, the sixth only
after I added the case it was missing.

REGRESSION: test_checkpoint_profiles 42 OK; test_review_driver 164 OK; test_review_cycles 162
ran / 36 errors, unchanged intake.py setUp refusal.

REVIEWER PROBES: account_guards, runner_operand, pinned_lock OK. settlement_limits -- its
dirty-tree case passes; its empty-account case fails at the assertion that documented the
defect, because the claim now carries provenance.

STILL NOT COVERED: real-settlement stale-caller completion/replay/successor; a surviving CHILD
holding the settlement through the production pair; deterministic namespace/boot cases.

## W257624 claim 272031 -- the settlement's own retry

    test_restore_outside_the_lock      (mine, 53 cases)

Same one-module selector and same bounded command. THREE NEW CASES: a stopped settlement
validation retried under a FRESH attempt label with the prior attempt bound into the decision;
a settlement's own live child holding the next attempt on `running` and `unknown` and then
ceasing to hold when it ends; an earlier attempt's late launch refused by the writing
transaction.

DETERMINISM: TEN consecutive runs. Three red runs came from my own misplaced scripted edit --
it matched a block present in two cases and landed in the wrong one -- caught by the
determinism set, reverted exactly, then applied inside the target function's span.

MUTATIONS THIS CLAIM, four, all four load-bearing: fixed label restored, prior attempts
counted rather than proved stopped, prior accounts not revalidated, walk skipping ahead
blindly. The third needed its case written after the fact, which is the third revalidation
guard in this Work to need that.

REGRESSION unchanged: 42 OK / 164 OK / 162 ran with the 36 intake.py setUp errors.
REVIEWER PROBES: settlement_retry OK; settlement_limits dirty case OK; account_guards,
runner_operand, pinned_lock OK.

STILL NOT COVERED: real-settlement stale-caller completion/replay/successor; a surviving CHILD
through the production pair; deterministic namespace/boot cases.

## W257624 claim 272105 -- the retired settlement label, and a real surviving child

    test_restore_outside_the_lock      (mine, 56 cases)

Same one-module selector and same bounded command. THREE NEW CASES: the retired
`settlement-<episode>` label's incomplete account holding, and its ENDED account continuing
under a versioned attempt with the retired label bound into the decision; `running` and
`unknown` under that label holding until the probe says ended; and a REAL surviving
same-group descendant holding the settlement through the PRODUCTION launcher and probe, with
the retry restoring once the group is gone.

MEASURED WHILE WRITING THAT CASE: killing the pid the shell recorded left `sleep 30` alive in
the same group and the production probe went on answering `running` -- correctly. The case
signals the whole group, every member of which it started, and waits on the PROBE'S answer
rather than a pid check, because a killed process is briefly a zombie whose group still
answers alive.

ALSO MEASURED: a THIRD legitimate refusal shape for a concurrent race loser -- the line's own
writer attachment, beside the executor gate and the kernel exclusion. All three now observed;
the case asserts the disjunction.

DETERMINISM: NINE consecutive runs at about 1.1s. MUTATIONS, three, all three load-bearing:
retired label ignored, its account counted rather than proved stopped, retired label taken as
a fresh attempt.

REGRESSION unchanged: 42 OK / 164 OK / 162 ran with the 36 intake.py setUp errors.
REVIEWER PROBES: prior_settlement, settlement_retry, account_guards, runner_operand,
pinned_lock OK; settlement_limits dirty case OK.

STILL NOT COVERED: real-settlement stale-caller completion/replay/successor; deterministic
namespace/boot cases.

## W257624 claim 272163 -- the stale caller through a real settlement; probe uncertainty

    test_restore_outside_the_lock      (mine, 58 cases)

Same one-module selector and same bounded command. TWO NEW CASES: a stale caller on the far
side of a REAL settlement and a REAL retry -- nothing planted -- performing no effect, answering
the same document the retry produced, and leaving a real successor's real bytes untouched; and
the cessation probe's namespace/boot uncertainty as deterministic identity cases, six records
this kernel cannot confirm answering `unknown`, then the PRODUCT holding on a launch recorded
under this manager's own group.

MEASURED COVERAGE STATEMENT: removing the completion read inside _admitted_execution fails NO
case. The property is carried by the recovery identity's own replay through store.transact,
which answers a stale caller its committed document first. The read is defence in depth beside
the mechanism that decides -- the fourth such guard reported that way in this Work rather than
counted as covered.

NOT STAGED, and named: a single real-process run in which one manager DIES while leaving an
orphan behind. The pieces are covered separately -- a child interpreter holding the exclusion
and dying, and an orphan descendant surviving an exception-unwound manager -- and neither case
should be read as the combined one.

DETERMINISM: six consecutive runs at about 1.13s. REGRESSION unchanged: 42 OK / 164 OK / 162
ran with the 36 intake.py setUp errors. REVIEWER PROBES: prior_settlement, settlement_retry,
account_guards, runner_operand, pinned_lock OK; settlement_limits dirty case OK.

## W257624 claim 272216 -- the issuing domain of a recorded process number

    test_restore_outside_the_lock      (mine, 60 cases)

Same one-module selector and same bounded command. TWO NEW CASES: the genuine domain
comparison paths -- namespace wrong, boot wrong, both wrong, the legacy no-scope shape, a scope
of the wrong type, and an observer that cannot read its own domain -- each answering `unknown`
even though the number is absent HERE, with only a matching scope read as ended; and an
unscoped launch refused before the fork with nothing recorded. `killpg` is the one call
patched; no process is created.

CHANGED SHAPE: the launch group payload now carries `pid_namespace` and `boot` beside group,
leader and started. Two of my existing cases asserted the old three-field shape and now assert
the five-field one. No module outside this boundary reads restoration_launcher or
restoration_cessation, so nothing else is affected.

MUTATIONS, five, ALL FIVE load-bearing: observer ignoring the domain, comparing only the
namespace, comparing only the boot, launcher recording no domain, unscoped launch performed
anyway.

DETERMINISM: nine consecutive runs at about 1.16s. REGRESSION unchanged: 42 OK / 164 OK / 162
ran with the 36 intake.py setUp errors. REVIEWER PROBES: observer_identity, prior_settlement,
settlement_retry, account_guards, runner_operand, pinned_lock all OK; settlement_limits dirty
case OK; restoration_launcher still errors on the removed constructor operand as previously
classified.

STILL NOT COVERED: the combined single-run real manager death with a surviving orphan.

## W257624 claim 272267 -- the combined real manager death with a surviving orphan

    test_restore_outside_the_lock      (mine, 61 cases)

Same one-module selector and same bounded command. ONE NEW CASE, and it is the last open item
on the selected list: a REAL manager in a REAL interpreter performs an accounted restoration
through the PRODUCTION launcher and probe, starts a same-group descendant that closes its stdio
and stays, and calls os._exit -- gone mid-restoration with its launch recorded, its episode
claimed and its exclusion released by the kernel. A fresh manager then holds while the
descendant lives, the CLAIM STILL NAMES THE DEAD MANAGER'S TOKEN, the probe answers ended once
the group is gone, the settlement succeeds naming that executor, and the retry completes the
restoration. Every process signalled was started by the case; the manager and the group are
both reaped.

ALSO: the failed-record cleanup prose in restoration_launcher no longer claims absence is
"VERIFIED", which contradicted _reap_group's correct disclaimer three lines below it. Wording
only; no semantics changed.

TIMING: the suite is about 0.24s slower than the previous claim, which is this case's real
interpreter. MUTATION: removing the pre-fork record("intent", None) fails four cases and errors
two.

DETERMINISM: six consecutive runs at about 1.40s. REGRESSION unchanged: 42 OK / 164 OK / 162
ran with the 36 intake.py setUp errors. REVIEWER PROBES: observer_identity, prior_settlement,
settlement_retry, account_guards, runner_operand, pinned_lock all OK.

NOTHING FROM THE SELECTED LIST REMAINS UNCOVERED.

## W257624 claim 272315 -- the fourth exclusion outcome, staged deterministically

    test_restore_outside_the_lock      (mine, 62 cases)

Same one-module selector and same bounded command. ONE NEW CASE: a loser that passes the
no-intent decision and then reads the writer AFTER the winner's intent revoked it, staged by
interposing on writer_for_attempt so the revocation provably precedes the read. It asserts the
exact refusal, ONE external effect, one claimed episode, the line at correction-ready, and a
replay answering the winner's document with no second crossing.

THE CONCURRENT CASE'S ASSERTION IS NOW A CONTRACT rather than a growing disjunction: four
permitted outcomes, each named with the deterministic case that owns it, each asserted to be
refused/precondition. Review 272313 refused the alternative -- adding an anchor whenever a
thread schedule surprised me -- and was right.

FIXTURE BUG FOUND BY RUNNING: the new case used the collected answer as its re-entry guard, so
the competitor's own writer read recursed until the interpreter gave up. The guard is taken
before the work it guards now.

PROSE: restoration_launcher's DOCSTRING no longer claims the failed-record group is "verified
absent" -- best-effort signal, nothing certified, unknown holds. Second correction to that same
paragraph; semantics unchanged both times.

MUTATION: letting the fresh path accept a non-active writer fails the new case.

DETERMINISM: eight consecutive runs at about 1.41s. REGRESSION unchanged: 42 OK / 164 OK / 162
ran with the 36 intake.py setUp errors. REVIEWER PROBES: all six current ones OK.
