# Progress

## claim370661 — observation reconstructs the per-Job manifest

Owner E370626 accepts the diagnosis and selects the bounded source
correction. Written **before the first source edit**.

### Revalidated at claim (read-only)

    HEAD            42bed8bb04a53380e565b1a63fb2bc702677f0d0
    v12 porcelain   clean
    the defect      still present: tools/single_worker.py _Observation.
                    _job_execution (~4117) reads `given = self.given`
                    while _SingleWorker._job_execution (~3328) reads
                    `given = self._given_for(stage)`

### What the two paths actually do

`_SingleWorker._given_for(stage)` → `_for_job(stage)`: asks the read-only
`self.job_task` reader for the Job's own task, and when there is one composes
a **fresh** document through `tools/job_task.py` — `manifest_for` and
`delivered_bytes` — never writing to `self.given`. `None` from the reader is
the installed delivery, which is every Job that predates the per-Job task.

`_Observation` already receives `job_store` and already builds a read-only
`job_execution_reader` over it. It does **not** build the task reader, so its
`_job_execution` names the installed `manifest_digest` — and
`launch.adopt` compares re-authored canonical bytes exactly, so the delivery
refuses `policy/denied` and every Job-bound launch reads `unreadable` on every
status pass. That is the whole defect.

### The correction

One shared pure composition, called by both, so the two cannot drift again —
drift between two copies of one rule is exactly what produced this defect and
what `_given_for`'s own docstring was written to prevent on the serving side.

### The change

**`tools/single_worker.py`** — one new module function and two call sites.

`given_for_job(given, reader, stage)` is now the single account of the rule:
ask the read-only task reader for this stage's Job, return the shared
installed document **itself** when there is no own task, and a **fresh** copy
carrying the composed manifest and task bytes when there is. It resolves
nothing else — the policy digest, the limits, the launch contract, the role
and the allocation stay exactly as the deployment configured them.

* `_SingleWorker._given_for` and `_for_job` now read it. Behaviour unchanged;
  `_for_job` keeps its signature because other callers want the pair.
* `_Observation.__init__` builds `job_task_reader(job_store)` beside the
  `job_execution_reader` it already built — the same narrow read-only reader
  the serving composition uses, over the store the factory already opened.
* `_Observation._job_execution` reads `given_for_job(...)` instead of
  `self.given`.

It is a module function rather than a method on either class **because the
defect was two copies of one rule disagreeing**. A method on `_SingleWorker`
would have left `_Observation` free to drift again.

**The exact-byte check is untouched** and nothing is adopted from the launch
document under examination. The expected identity is composed from the Job
owner's own record; a launch whose bytes really do disagree still refuses,
which is what makes the readable ones worth anything.

### Tests — `tests/tools/test_job_task_delivery.py`, +296 lines

Two new case classes on the suite that already owns per-Job delivery, reusing
`TheRuntimePathDeliversAndRecoversOneIdentity`'s harness so each question is
asked of a **real** materialized launch: the production composition, a real
Job store with a real submission, a real control store, the serving loop's own
`reconcile`/`status`, the recorded attempt, the launch adapter and an engine
start.

`ObservationReproducesTheDeliveredIdentity` — 7 cases:

| case | what it holds |
| --- | --- |
| the two compositions agree on the launch context | **the Work in one assertion**: serving's and observation's contexts are the same document, and it names the Job's identity, not the installed one |
| the observation adopts the materialized launch | through the real `observe_exchange`; `unreadable` is produced only by a refusal, so anything else proves adoption succeeded |
| the policy digest and the limits are still the deployment's | only the manifest and the task move |
| a fresh reader over the same state reproduces the context | restart, over fresh store handles under a new incarnation |
| the installed delivery is still what a jobless task gets | the fallback every pre-W363066 Job relies on |
| the shared configuration is never written to | by **identity** (`is`), not serialization — and the resolved document is proved to be a different one, or nothing was being kept apart |
| two Jobs on one worker resolve their own contexts | asked in both orders, because a reader that cached would answer the first Job's identity for the second |

`TheObservationStillRefusesALaunchItCannotReproduce` — 5 cases, because the
wrong correction is a credulous reader: a stage naming another attempt, a
stage naming another Job, a **corrupted launch document** on disk, an unbound
execution, and the surface still holding no act and no engine.

**The harness substitution is the inherited one, and it is written down.** The
suite already substitutes the per-Job task reader on the serving worker — a
Job store row carrying a `task_document` is written by
`creation.create_template_job`, which needs an installed deployment and a Work
binding this suite has neither of. `observing()` now applies the *same* answer
to *both* sides, so what the cases measure is whether the two **compositions**
agree given one answer. `TheReaderOverARealStore` drives the real
`job_task_reader` against a real store, and one case asks an **unsubstituted**
observation whether it builds a real reader at all.

### Verification

Every run: `PYTHONPATH=src:. BATON_V12_DISK_ROOT=/var/tmp/baton-w257624
BATON_V12_STACK_TEST_ROOT=/var/tmp/baton-w257624 python3 -m unittest <module>`
from `v12/python`.

    tests.tools.test_job_task_delivery      93 tests   OK        (65 before)
    tests.tools.test_single_worker         243 tests   1 failure (pre-existing)
    tests.tools.test_stage_execution       477 tests   OK
    tests.tools.test_stage_execution_status_hardening   2 tests  OK
    tests.tools.test_stage_execution_hardening          3 tests  1 failure (pre-existing)

**The new cases fail without the fix**, which is the only thing that makes
them worth anything. Against the pristine committed `single_worker.py`,
5 of the 12 fail — including the two that *are* the defect:

    FAIL  test_the_two_compositions_agree_on_the_launch_context
          observation 303a1a8b… vs serving 7cf28d1b…
    FAIL  test_the_observation_adopts_the_materialized_launch
          state unreadable {category: policy, code: denied}
    ERROR test_the_shared_configuration_is_never_written_to
    ERROR test_two_jobs_on_one_worker_resolve_their_own_contexts
    ERROR test_the_observation_still_holds_no_act_and_no_engine
          — the three reference the new seam, so they error rather than fail

The preservation cases (installed fallback, restart, policy/limits, and all
five refusals) pass both ways, which is what preservation means.

### Two pre-existing failures, verified as pre-existing

I nearly attributed the first to myself. Both fail **identically** on the
pristine committed source, which I confirmed by running the suites against
`git show HEAD:…` extracted to a temp file:

* `test_single_worker … test_a_real_observing_status_run_mutates_no_durable_state`
  — the four `*.sqlite3-shm/-wal` sidecars survive the run on this host. HEAD:
  243 tests, this one failure. Candidate: identical.
* `test_stage_execution_hardening … test_worker_construction_failure_closes_every_acquired_handle`
  — HEAD: 3 tests, this one failure. Candidate: identical.

Neither is caused by this change and neither is fixed by it. I am not
silently carrying them: they are reported as found.

### What this does not establish

The retained deployment is **not** updated — it runs the `18e771f0` bundle and
this correction is source only, so the live instance would still report
`unreadable` until an owner selects a rebuild. No deployment update, live
retry, provider run or change to retained execution evidence was performed.
The fixture substitutes the task reader's *answer* for the reason the suite
already documents; `TheReaderOverARealStore` covers the read itself. No
container, engine, provider or credential was involved in any run here.

### Boundaries

Changed: `v12/python/tools/single_worker.py`,
`v12/python/tests/tools/test_job_task_delivery.py`, this PROGRESS and this
dossier's new evidence. Nothing else in `v12` is touched. Parent evidence, the
accepted packets, the diagnostic evidence and the installed instance are
unchanged. No Git mutation — the only version-control calls were
`rev-parse`, `status`, `diff` and `show`, all reads. I attempted `git stash`
once to isolate a baseline; the deployment hook refused it, correctly, and I
used `git show` to a temp file instead.
