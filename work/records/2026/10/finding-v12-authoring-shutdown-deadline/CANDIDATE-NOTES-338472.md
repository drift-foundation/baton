# W338305 correction candidate — direct exception provenance

Author baton.codxpc, claim338472. Base fb48797903160aa764229d58f3a5beaf29648bfc.
Candidate is candidate-338472; canonical product files remain untouched. This is
owner-selected direct disposable execution, NOT a v12 Job/attempt. Packet338345
remains sealed and unlaunched. Independent acceptance is still owed.

## Change and reasoning

The outer controller preserves its original cleanup reserve and kill/reap cutoff.
Before SIGTERM it writes the exact manager cutoff to a fresh per-incarnation request.
The manager never gains a later cutoff: its shutdown budget is bounded by that
request, the original envelope, and its first local shutdown observation. Repeated
signals and later steps cannot refresh the allowance. The monotonic value is local
to the same host/boot and ephemeral manager incarnation, never a persisted token
permission or a recovery clock substitute.

A new authoring_shutdown helper allocates cleanup, accounting, workload publication,
guard join and final snapshot deadlines within that cutoff. Main-thread blocking
steps have a SIGALRM deadline; expired steps do not start. The original outer
process kill/reap remains the backstop for blocked or noncooperating native code.
The guard thread's I/O remains separate and its join is bounded. Phase evidence
names the last entered step, run and Job, deadline and observed faults; it is not
an invented stack trace or a runtime cessation receipt. Snapshot observation and
outer result publication use remaining time too, without a fresh reporting window.
If the final outer publication cannot finish, prior workload/manager/progress bytes
remain; a missing report is incomplete evidence and never success.

Baseline's cleanup loop consumes the shared deadline; cancellation/read/accounting
calls are bounded, with existing fail-closed fallbacks. Final logging and operation
close are also bounded after shutdown begins. Cleanup failures now update the
reported serving_failure field, which previously retained its pre-cleanup value.
No token acquisition/renewal/settlement, admission policy, Job limit or workspace
ownership rule is changed. Known exact cessation remains independent of output
quality; concrete unknown runtime/launch state retains its existing holds.

## Changed test paths and reasons

- v12/python/tests/manager/test_authoring_shutdown_deadline.py: new fast deadline
  checks and eleven real-process composition cases; verifies final reporting,
  timeout attribution, original limits, token release despite pending cleanup,
  uncertainty holds, reaping and manager-guard release.
- v12/python/tests/manager/shutdown_fixture.py: candidate-native fixture adapted
  from the accepted diagnostic. Imports this candidate rather than exporting the
  old Git base. Real controller/baseline/guards/stores; fake engine/provider and
  source-materializer seams. No accepted output/checkpoint is manufactured.
- v12/python/tests/manager/test_authoring_manager_guard.py: existing workload stub
  accepts the new optional shutdown argument. Existing assertions are unchanged.

Other changed paths: tools/authoring_enforcement.py and new tools/authoring_shutdown.py
under v12/python, and work/records/2026/09/finding-v12-single-implementation-proof/
baseline.py. These are changes only in the disposable candidate. Base and candidate
manifests enumerate exact bytes; candidate patch is a review convenience.

## Reproduction

Use the candidate as source, with writable disk-backed fixture/evidence storage.
No live engine/provider, credential content or mutating Git call is needed. From
candidate-338472/v12/python, set PYTHONDONTWRITEBYTECODE=1 and PYTHONPATH to that
absolute directory and its src subdirectory. Optionally set BATON_SHUTDOWN_EVIDENCE
to a fresh absolute disk-backed path to retain all eleven case traces and stores.
BATON_V12_DISK_ROOT can explicitly choose writable disk storage for existing tests.
Then run (150s outer command timeout; each new process case20s plus5s reap):

    python3 -B -m unittest tests.manager.test_authoring_shutdown_deadline tests.manager.test_authoring_enforcement tests.manager.test_authoring_manager_guard

The new tests prove cooperative blocked-sweep expiry, absent writer/pending cleanup,
normal refusal return, pre-serving cancellation, repeated deferred SIGTERM, delayed
and stuck snapshot publication, stuck workload publication, stuck cleanup sweep,
stuck accounting and unknown-engine expiry. Existing tests retain unbound/late-launch,
wrong-runtime, original-envelope/restart, single-admission and manager-loss coverage.
The normal return fixture is an orderly fake-create refusal, not successful authored
provider output. Existing full Git-backed proposal tests were not run: this selected
verification uses non-Git source fixtures and does not mutate even a private Git repo.
No live-provider authentication, real Docker cessation or deployed readiness claim.

## Iteration history

Initial existing40-test run: six fixture-signature failures,11.722782779s. After
fixing the stub, first44-test run: unknown-engine case finished before token expiry,
60.515017772s; fixture now blocks until expiry without weakening the hold assertion.
Second44-test run: stuck-cleanup timeout exposed the stale reported failure field,
73.422302254s. Third44-test run passed,73.772974933s. Tightening outer report/read
budgets then exposed one startup-refusal snapshot-read regression in the fourth
44-test run,73.622819292s. The fallback now passes remaining time to the snapshot
reader. Final run and cumulative measured spending are in PROGRESS and evidence
RUNS.json; failed runs and all traces are retained. Case times are components of
these command totals, not additional spending. Source/drafting/hash overhead is
unmeasured; no full-turn bound is asserted.

## Delivery boundary

Independent reviewer owns acceptance and scope/review files. The direct exception
expires on independent acceptance. Human integration/checkpoint and real isolated
v12 validation are separate selections; W333485/W333486 gates remain through an
observed accepted corrected base. Proposed human checkpoint after acceptance:
`fix(v12): coordinate authoring shutdown deadlines and final reports`.
