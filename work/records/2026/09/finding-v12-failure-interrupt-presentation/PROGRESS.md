# Research progress — baton.tuner claim306616

Read canonical events through306616/thread306614 and bound dossier306619. Completed retained-file inspection, current/frozen-source mapping, two deterministic localization witnesses and bounded proposal.2PASS0.002s; no failed test iteration. EVIDENCE.json pins artifacts; FINDING distinguishes observations, owner report and inferred implications. PROPOSAL.md preserves unrelated runnable Jobs, original failure, exact cessation/hold and exception boundary. No product/active W247941 edits, deployed store reads, live provider/engine, rerun, cleanup or graph change. Await independent research review and later coordinated Claude selection. Missing exact failure timestamp/transcript and provider-diagnostic adapter compatibility are explicit limitations, not new adoption blockers.


# Implementation progress — baton.claude claim 307593

READ: `detail work=W306614`, the WHOLE of T306614 (one message, `next_after: null`), every event
from creation through my claim — tuner research 306616/306662, the independent research acceptance
306676, owner `add_dependency` 306697, **owner reroute 306698 selecting implementation**, and the
`wake` at 307583 — plus `FINDING.md`, `PROPOSAL.md`, `PLAN.md`, `EVIDENCE.json`,
`CANDIDATE-306616.json`, `review-2026-09-29T14-51-38Z.md` and `test_diagnosis.py`, all in full.

## What I implemented, both causes, in `two_job_supervisor.py`

**CAUSE A — per-Job failure reporting and a stop that means something.** `should_continue` recorded
generations, optional turns, caps and the serving deadline and never asked whether the selected Jobs
could still progress. It now classifies EACH selected Job through the accepted single-Job boundary —
`baseline._attempts_of` filters the status projection to one Job, `baseline._terminal` reads that
Job's own stage states — and:

    REPORTS each newly observed failed pipeline IMMEDIATELY, through a `report` sink that defaults to
    stdout with `flush=True`, naming the Job, its stage states, its attempts and the fact that this
    run has no retry. Deduplicated by WHAT WAS OBSERVED, so a repeat tick is silent and a Job that
    fails differently later is reported again.
    STOPS serving only when EVERY selected pipeline is terminal — `held["stop"] = "pipelines-terminal"`.
    One Job failing does not end the other's serving.
    TREATS AN UNREADABLE PROJECTION AS UNKNOWN, never terminal: the entry is dropped rather than
    remembered, so the deadline stays the backstop. The uncertainty is recorded ONCE per distinct
    failure rather than once per tick, because `_guarded` would have published one hold reason per
    tick for a run that could not read its status.
    RECORDS the per-Job facts in the outcome as `pipelines`, and a Job that ended exceptionally is
    its own `held_because` entry — the outcome used to name only the missing verdicts, so a reader
    could not tell a Job that failed from one that never started.

`_terminal` is applied PER JOB and never to a flattened map of both Jobs' states, which is the one
thing `PROPOSAL.md` explicitly warns against: its any-exceptional rule would end a healthy Job
because the other failed.

**CAUSE B — the interruption is presented, not leaked.** `main` now catches exactly
`baseline.SupervisorInterrupted` around `supervise`, prints the interruption, WHERE the outcome was
retained, the ORIGINAL per-Job failures (so the first cause survives the last event), the state, the
stop reason, the held-reason count and the unresolved-cleanup count, and returns **130**. The catch
is narrow: a held run still exits 1, a settled one 0, and a programming fault still raises. The
lower-level publish-then-raise contract is untouched.

## Verification, and one measured surprise

    W306614 dossier          9 PASS 0.007s (`test_diagnosis.py` converted + `test_correction.py`)
    W247941 `test_two_jobs`  101 PASS **43.2s**, previously 77.4s
    W247941 `test_useful_tasks` 20 PASS 0.074s

THE SUITE GOT 34 SECONDS FASTER, and that is the fix showing up as a measurement rather than as an
argument: runs that used to sit in the predicate loop until their serving bound now stop when their
pipelines finish.

I GUESSED ONE ASSERTION WRONG AND MEASURED IT RIGHT: I expected one sweep in the both-failed case and
got zero. `serve` asks the predicate BEFORE its first sweep, so a run whose Jobs are already terminal
when serving opens ends without sweeping. In a real run the first tick finds queued stages and
serving proceeds normally; the fixture starts at the end on purpose. The case says so.

## The two W247941 cases I had to change, and why that is the coordination question

`PROPOSAL.md` says to coordinate ownership of `two_job_supervisor.py` and `test_two_jobs.py` before
editing, and owner 306698 asks for behaviour that lives in exactly those files. Two W247941 cases
asserted the OLD behaviour and could not both stay and be right:

    `test_an_INTERRUPTION_through_the_command_publishes_and_still_raises` asserted `assertRaises` out
    of `main`. That IS the defect. Renamed to `..._and_REPORTS_it`, it now asserts status 130 and the
    retained-outcome line, and its docstring records what it used to assert. The LOWER-LEVEL twin,
    `test_an_interruption_publishes_the_outcome_and_still_raises`, is untouched and still passes.
    `test_the_DOCUMENTED_COMMAND_reaches_four_attempts_and_two_verdicts` asserted
    `stopped == "serving-bound-exceeded"` for a fully successful run. It now asserts
    `pipelines-terminal` and both pipelines `completed`.
    `test_the_run_stops_at_total_minus_cleanup_and_publishes` still holds the deadline for a run with
    no work to finish, so the backstop is still covered.

**AND THE CONSEQUENCE THE REVIEWER MUST WEIGH:** `two_job_supervisor.py` moved from `5b3045e66bd4` to
`fca165f70eed`, and W247941's `OPERATOR-307388.md` launch command for the not-yet-performed run
`two-jobs-247941-03` names THIS file by path. If the owner launches run 03 now, it runs the changed
supervisor. I am not deciding that: W247941's reviewer should revalidate the supervisor before run 03
is launched, or run 03 should be deferred until this change is accepted. I did not edit any W247941
record, packet document or operator sheet.

## Not done, deliberately

No live run, no provider or engine, no deployed store opened, no rerun, no cleanup action, no
consumed-instance mutation, no Git or graph mutation. No new provider-text parser and no schema
expansion: the `failure_observation` helper reuse stays an open scope choice, unneeded for these two
causes. The connected two-Job fixture in `test_two_jobs` is the acceptance vehicle `PROPOSAL.md`
names, and it passes; the dossier's own fixtures remain deterministic localisation-grade, not
connected live acceptance.

`CANDIDATE-306616.json` pinned the RESEARCH state, including `test_diagnosis.py` at
`e72f5a8a05b8…`. That file is now `1f3c69c5019f` because `FINDING.md` required the witnesses to be
converted into regressions. Everything else it pinned is unchanged.


# Corrections — baton.claude claim 307757, answering review 307718

READ: `detail work=W306614`, events after 307675 (my pass 307678, reviewer claim 307718 and the
changes-requested pass 307754), `review-2026-09-29T17-20-22Z.md` and `review-evidence-307718.json`
in full, and T306614 again. Three findings, all fair, all corrected.

## R1 — an interruption in the status read now stops admission at once

`_observed` caught `BaseException`, recorded it and carried on, so a Ctrl-C arriving inside the new
status read left admission open until the serving deadline. The reviewer's own probe measured
`stopped=serving-bound-exceeded` with only the cleanup reserve left. A non-`Exception` is now
RE-RAISED into the serving interruption handler `supervise` already installs, which sets
`stopped=interrupted`, closes admission before anything is cancelled, and publishes. An ordinary
failure is still UNKNOWN. The regression asserts the interruption reaches the caller,
`stopped == "interrupted"` and NOT `serving-bound-exceeded`, and that admission closed first.

## R2 — the original failure is attributed, and it cannot disappear

TWO DEFECTS, both real. `baseline._attempts_of` answers attempt ids and stage states and DISCARDS
the exchange, the episode/assignment and the artifact locators, so nothing I reported could explain
the failure it was reporting. And `_inspect` popped the pipeline entry on any later unreadable
status, which erased a confirmed failure.

    ONE CANONICAL READ PER TICK, KEPT WHOLE. `status(job, gate, ...)` is asked once and the stage
    entries are kept; `baseline._terminal` still classifies ONE Job's states at a time, never a
    flattened map.
    `failures` IS IMMUTABLE and separate from `pipelines`. The first failure per Job is recorded
    once and never rewritten or popped; `pipelines` is current eligibility and is cleared when a
    read does not answer. The hold reasons and `main`'s post-interruption report are derived from
    `failures`, so an unreadable status can no longer turn a failed run into one that merely has no
    verdicts.
    THE FACTS ARE THE PROJECTION'S OWN: job, stage kind, stage_id, work_id, state, episode,
    attempt_id, offer_id, runtime assignment/runtime_id/execution_runtime, the canonical exchange
    STATE, and the observation time.
    THE CAUSE IS VALIDATED OR EXPLICITLY UNKNOWN. `_supported_diagnostic` is a bounded
    packet-specific adaptation of the reviewed `failure_observation._supported_detail` contract: it
    admits the recognised OAuth constant or an explicit unknown and refuses everything else,
    including a diagnostic whose explanation is not the supported constant. There is no parser over
    provider text and no schema anywhere. When nothing validates, the record says `unknown` and
    names the manager's own artifact LOCATORS -- never their contents.
    THE HELPER IS NOT SILENTLY CLAIMED. The review says it belongs elsewhere now; the adaptation is
    recorded here rather than taken.

## R3 — the connected failure evidence, through the real path

Two new cases in W247941's connected fixture, using its own provider seam (`status=1`, so the
provider really runs and really fails) with the real adapter, ending, custody and projection:

    BOTH IMPLEMENTATIONS FAILING: each reported, `stopped=pipelines-terminal`, `state=held`,
    `failures` carrying both attributions, zero review admissions and no verdicts.
    ONE FAILING, ONE HEALTHY: job-a reported and job-b implemented, REVIEWED and producing its own
    attributed verdict -- one review admission, `verdicts == ["job-b"]`, job-b `completed`, job-a
    `exceptional`, and the run still held because job-a produced none.

WHAT IS STILL SIMULATED, said plainly: failed-read-after-failure and the R1 interruption are driven
at the dossier level, where a status read can be made to fail or to raise. Injecting those into the
connected fixture would mean mocking its projection too, which is the same simulation with more
machinery. Publication failure and cleanup uncertainty remain covered by W247941's existing cases.

## Measured

    W306614 dossier          14 PASS 0.010s (was 9; five new: R1, attribution, malformed
                             diagnostic, absent diagnostic, failed-read-after-failure)
    W247941 test_two_jobs    103 PASS 43.365s (was 101; two new connected failure cases)
    W247941 test_useful_tasks 20 PASS 0.076s

Two of my own fixtures needed correcting when the read became one-per-tick rather than one-per-Job,
and the interruption case had to carry `failures` rather than `pipelines`; the count case caught
`ADOPTION-247941.md` at 101 again and it now says 103.

I withdraw the run-03 warning from the previous claim: the reviewer states run 03 completed and was
independently accepted before this implementation began and W247941 is closed. I have not touched any
accepted packet, operator sheet or historical digest record.

Files: `two_job_supervisor.py` (2e580ad6402b), `test_two_jobs.py` (e2a372272d72),
`ADOPTION-247941.md` (58a9c7337a8b), `test_correction.py` (acc0f41b5618), `test_diagnosis.py`
(1f3c69c5019f, unchanged this claim).


# Correction 2 — baton.claude claim 307851, answering review 307831

READ: `detail work=W306614`, events after 307820 (my pass 307824, reviewer claim 307831, the
changes-requested pass 307848), `review-2026-09-29T17-33-48Z.md` and `review-evidence-307831.json`,
and T306614 again. R1, the immutable-failure half of R2, and R3's failed/mixed slices are ACCEPTED
and preserved unchanged. One finding remained, and it was right.

## The remaining R2 — I validated a field the publisher does not supply

`_failure_facts` read `exchange["diagnostic"]`. The exchange observation publishes state, command,
receipt and terminal identity; it does NOT publish that. So a valid published OAuth failure could
never reach the branch that recognises it, and my test "proving" it invented the field in a mocked
projection. Copying `_supported_detail` gave me the validator without its data source.

WHAT IS THERE NOW: `_retained_report`, a minimal reader owned in this supervisor, which follows the
accepted helper's identity rules exactly — ONE artifact row whose `artifact_id` is
`<attempt>:<output>`, a `file:` locator with no escaping or traversal, a path under THIS deployment's
own storage whose last three parts are `custody/<attempt>/<output>`, a bounded 64 KiB read with
`O_NOFOLLOW`, duplicate members refused, JSON constants refused, and the report's own `schema` and
`task_id` bound to this Job — and takes the storage root and task id as OPERANDS rather than
hardcoding one packet's layout, which is exactly why the helper is not drop-in. `api-error` alone
still does not establish authentication: the diagnostic is looked at only for an `api-error` with a
nonzero in-contract status, and then only through the closed validator.

`main` supplies both operands from documents it already loads: `_storage_root` from the workers'
agreed `workspace_storage`, and `_task_ids` through `job_bindings` → `source_worker_id` → that
worker's task document → its `task_id`.

THE CANONICAL TERMINAL RECORD IS PRESERVED TOO: `terminal` now carries the closed scalars the
exchange does publish — state, terminal, terminal_reason, disposition, fault, fault_code, command,
receipt — beside the attribution, because `exchange_state` alone does not preserve the cause.

AND A PROVISIONAL UNKNOWN IS NOT FINAL. If the report is retained after the stage first projects
exceptional, a later validated cause is added beside the FIRST canonical failure — same attempt,
same state, same first observation — with `cause_supplemented` and its own `cause_observed_at`.
Nothing is rewritten and nothing is suppressed.

## One binding defect the connected fixture caught

My first `_task_ids` matched the task document's FILE NAME against the Job id. The connected run
measured it returning `{}` — that fixture's documents are `task.json` and `task-b.json` with ids
`w119114-composed-lifecycle` and `w130224-second-job` — and every connected failure then refused with
"the retained report names a different task than this Job's". A convention is not a binding; it now
goes through `job_bindings`.

WHAT THE CONNECTED RUN SHOWS NOW, measured rather than asserted: `availability: available` — the
reader reaches the real retained report through the real custody layout, the real locator and this
deployment's own task binding — with `provider_cause: unknown` and
`why: the report carries no validated provider diagnostic`. That is an HONEST unknown about a
deterministic provider that publishes no structured diagnostic, not a path that cannot reach the
branch. The connected cases now assert `available` rather than tolerating either answer.

## The evidence

    THE POSITIVE, through the real consumption boundary: a report written where the manager writes
    one, declared as the manager declares it, carrying the closed OAuth diagnostic -- the cause
    reaches the prompt report, the retained outcome and the hold reasons.
    THROUGH INTERRUPTION: the same cause appears in `main`'s 130 summary after a signal.
    THE NEGATIVES: wrong task, foreign attempt, two rows for one output, duplicate member, non-JSON
    constant, absent report, unsupported reason, status out of contract, and prose in place of the
    supported constant -- every one an explicit `unknown` with its reason, and the prose never
    appears in the outcome or in any report line.
    THE SUPPLEMENT: a first tick with no report and a second with one.

    W306614 dossier          16 PASS 0.017s (was 14)
    W247941 test_two_jobs    103 PASS 43.419s
    W247941 test_useful_tasks 20 PASS 0.075s

Two of my own multi-tick fixtures needed correcting: a projection in which every pipeline is already
terminal ends the run at once -- correctly -- so the second tick never arrived until job-b was left
active.

Files: `two_job_supervisor.py` (65b378b41772), `test_two_jobs.py` (028eb272a2a4),
`test_correction.py` (b98669d7336d). `test_diagnosis.py` unchanged this claim.


# Correction 3 — baton.claude claim 307931, answering review 307909

READ: `detail work=W306614`, events after 307900 (my pass 307907, reviewer claim 307909, the
changes-requested pass 307928), `review-2026-09-29T17-44-50Z.md` and `review-evidence-307909.json`,
and T306614 again. Three findings on the new reader, all real, all corrected. The accepted
interruption, immutable-history and connected failed/mixed slices are preserved untouched.

## R2a — the containment claim was not true, and a malformed report could end healthy Jobs

THE ESCAPE WAS REAL, not hardening. `O_NOFOLLOW` on the whole path protects the FINAL NAME only,
and my `relative_to` check read the DECLARED path — so `storage/custody` symlinked at a sibling tree
answered `available` with an `authentication_failed` cause attributed from OUTSIDE the selected
root. The reviewer reproduced it. `_bounded_document` now walks every ancestor with directory
descriptors and `O_NOFOLLOW`, exactly as the reference `_document` does, and opens the file
`O_NONBLOCK` BEFORE the regular-file check so a FIFO cannot block in `open` ahead of `fstat`.

AND THE SHAPE CHECKS WERE OUTSIDE THE GUARD. A report that is `[]` at the root, or whose `provider`
is `[1]`, raised `AttributeError` from the `.get` calls below the caught region — and in `supervise`
that became `serving-failed`, ending healthy Jobs because a SUPPLEMENTARY report was malformed. The
validation is inside the guard now and both shapes answer an explicit unknown. The regression
asserts the consequence too: `serving_failure` is None and the run still stops `pipelines-terminal`.

## R2b — I invented a flat terminal and the publisher does not have one

`worker_manager/exchange.py` `_terminal` returns a NESTED document — `ending`, `answered`,
`disposition`, `fault_code`, `manifest_digest` — and my scalar-only copy skipped all of it, while my
own flat `terminal_reason`/`fault_code` mocks proved nothing about the publisher's shape. The facts
now carry the exchange's own scalars (`state`, `sequence_id`), the nested `terminal` members, and
the `command`/`receipt` step scalars, read where they actually live. The fixture uses the real shape:
`state: faulted` with `terminal.ending: faulted`, `terminal.fault_code: agent` and
`terminal.answered: ["open", "work"]`.

## R2c — the supplement could misattribute, and a new cause could go unannounced

The supplement keyed on `job_id` alone, so a DIFFERENT failure's cause could be attached to the
first one. It now requires the same stage, kind, attempt, episode and assignment; a changed failure
keeps its own facts and supplements nothing. A case proves a foreign-identity later report never
relabels the first failure and never introduces its cause into those facts.

And the announcement key held only stage states and attempt names, so a cause that became known
while the states stayed the same was retained in the outcome and never reported. The validated cause
is part of the key now: the measured sequence is one line for the failure with no cause yet, one
when the cause is validated, and silence for the identical ticks after it.

## Measured

    W306614 dossier          21 PASS 0.022s (was 16; five new: ancestor symlink, special file,
                             wrong JSON shape, foreign-identity supplement, same-identity late
                             report)
    W247941 test_two_jobs    103 PASS 43.404s
    W247941 test_useful_tasks 20 PASS 0.075s

Files: `two_job_supervisor.py` (c53c2778a8a3), `test_correction.py` (a39e5b64f462).
`test_two_jobs.py` and `test_diagnosis.py` are unchanged this claim.
