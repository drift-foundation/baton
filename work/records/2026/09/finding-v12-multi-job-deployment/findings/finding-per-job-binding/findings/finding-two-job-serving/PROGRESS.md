# Progress

Implementation entries belong to the participant making changes under its claim.

## claim131069 — two Jobs through serving and correction, and where it stops

Evidence: `evidence/provider-131069.json`. Candidate, both mode 0664 relative
to v12/python:

- tools/stage_execution.py `2b1a4324443b39d92e8aadee9146e6216321525eace81ff9a4ea00fe3a77a3b0`
- tests/tools/test_stage_execution.py `a5b0e048be970a5e17dc89af20991780142792f54f64d4e3f7924ed306e7abbf`

The accepted W130216 candidate was revalidated byte-identical before any edit,
and the selected repair was pinned in FINDING at 2026-09-09T21:33:08Z BEFORE
the first edit — the chronology caveat the last review raised.

**Two global fallbacks removed, both inside the authorized two paths.** The
terminal completion check proved the settlement against `required_tests()` with
no Job, which refuses outright once a deployment configures two producers; it
now names this stage's own bound Job. And the integration runtime port was one
injected object for the whole deployment while `IntegrationRuntimePort` is
composed over one accepted line, one proposal and one target — all per-Job
facts. `operations_from` now takes one port per bound Job, keeps the single
object for one binding, and REFUSES one bare port for a deployment binding
several rather than running the second Job's integration against the first
Job's line.

**What the traversal drives, all on ordinary ticks.** Both Jobs coding at once
on their own producers and their own persistent lines; one Job in review while
the other is still coding; a changes-requested verdict reopening the SAME line
its rejected checkpoint was written on while the other Job does not move; the
second Job reaching its own reviewer and its own accepted checkpoint; both
accepted Jobs' integration stages eligible with exactly one holding the single
configured integrator and both proposing into one canonical target; two
required-test selections from two producers' two tasks; and one Job's actual
integration and terminal handoff inside the two-Job pool.

**Three fixture facts the traversal forced, and each is a real one.** A task
DECLARES ITS BASE, so a Job on its own line needs its own task — Job B's
producer could not have run a turn otherwise. The Authority knows which
participants serve a route, so the second producer and reviewer are declared on
theirs exactly as the first Job's already were. And the accepted engine models
ONE container: two Jobs coding simultaneously reported each other's runtime, so
this class composes an engine that answers about the container it was asked
about. The accepted `Engine` is not changed.

**Where it stops, reported and not accepted.** A completed integration never
returns its scheduler capacity: after Job A's integration finishes for real its
allocation is still `reserved` while that Job's implementation and review
allocations are `released`, because `reconcile_allocations` releases on an
ended episode or a runtime whose cleanup is `complete`/`retained` and an
integrator's runtime can obtain no `authorize_cleanup` at all. So Job B's
integration stays `queued` forever. One integration worker serves one Job per
deployment lifetime. The correction is in `job_manager/scheduler.py` or
`worker_manager/intake.py`, outside this campaign's two paths — so nothing was
worked around: the boundary is measured here by
`test_a_completed_integration_does_not_return_its_capacity` and filed as
**W131187**, `work/records/2026/09/finding-v12-integration-capacity-return`.
**Both Jobs are not carried to terminal, and that is stated rather than
claimed.**

**Verification, and the residual gap.** The full module (235 tests) was run
twice; each run found a regression the focused runs could not. After the final
two-line constructor correction, 69 tests were re-run and pass — the 40
covering every direct `Integration` construction and both composed lifecycle
classes, and the 29 of the traversal class. The full module has NOT been re-run
after that last change; three cases in `TheObservationSurfaceIsSeparateAndReadOnly`
reach that constructor with one argument, which is not a dict and takes the
same branch as before. That is the one open verification gap.

**Budget, every run wall-timed, and it is over.** 92.14s against the 75s
increment — **17.14s over**. The two full-module runs are 53.16s of that; both
were necessary and both found regressions. Campaign carry is about 367.88s of
400s, leaving 32.12s against the 20s observation and 27s joined increments
still to come. This overrun therefore eats into successors and is the owner's
decision, not this Work's to absorb silently. No untimed run and no new
uncertainty.

State: awaiting independent review through baton.bug.

## claim131378 — the port preflight moves, and the second Job owes a rebase

Evidence: `evidence/provider-131378.json`. Candidate, both mode 0664 relative
to v12/python:

- tools/stage_execution.py `28ee42a2aaca4e9f596ff5accfebb60f5bc1c6f888e1c9e3c128d7ee93993302`
- tests/tools/test_stage_execution.py `1ebba932945b8f1c93f80aaa61835b3188ef489073fb39887a20806d6b7fe93c`

The pinned baseline `2b1a4324…`/`86610e63…` was revalidated byte-identical
before any edit.

**Both static corrections from review-2026-09-09T21-58-10Z.md are delivered.**
`_integration_ports` now resolves in `operations_from`'s pure prologue, beside
`held_configuration`, the Job store's Authority comparison and `_profile_of` —
before `worker_preflight` configures the control store's workspace group and
storage and before the integration store is opened. The reviewer's point rests
on this function's own opening paragraph: a refusal that has already changed
durable state is not a refusal, and the shape of an injected capability is a
fault this module can know for free. `Integration.port_for`'s duplicated `/1`
block — an accidental double application of the previous claim's edit — is
gone, with no other reformatting.

**Three new controls prove the ordering rather than assert it.** A `/2`
document is composed over store DOUBLES: a Job store answering only the
Authority binding it names, and a bare object for the control store — so a
clean `ContractRefusal` is itself the evidence that `worker_preflight` never
reached it, since it would have faulted with an attribute error instead. A bare
port for two bound Jobs and a mapping naming an unbound Job each refuse with no
integration store on disk. The positive control pins the three shapes this
deployment does accept, including that a mapping covering only some bound Jobs
is not a fault — a Job with no port refuses at its own integration stage with
the capability sentence that has always said what this build lacks.

**The remaining acceptance item is not delivered, and capacity is no longer
why.** Job A reaches terminal integration; Job B reserves the integrator, so
W131187's release works. What Job B cannot do is publish. An Authority holds
ONE canonical target revision and `authority/core.py` advances it to the
integrated candidate when it writes the integration receipt; Job B's line is
still declared at its original base because `create_line` is create-or-recover
by `(authority, work)` and refuses disagreeing operands, so a declared base is
immutable and nothing in `review_cycles` advances one. `published_proposal` on
Job B's accepted checkpoint refuses with the provider's own "a proposal is
offered against the revision it was built from". A correction round would
produce another candidate on the same superseded base.

All three candidate directions are outside this Work's two paths, so the
boundary is measured here by
`test_the_second_jobs_candidate_is_stale_once_the_first_integrates` and filed as
**W131409**, `work/records/2026/09/finding-v12-line-rebase-after-target-advance`.
No stale-target bypass, no fabricated completion, no manual transition.

**Verification.** 128 selected executions pass across every class that reaches
the changed code — the two-Job traversal class whole, the preflight class, the
accepted integration port class, every composition and observation class, both
`/2` fixture classes, and the `/1` composition that supplies a runtime port
through `operations_from`. `OrdinaryTerminalLifecycle` was NOT re-run: alone it
is about 7.5s and would have taken this correction past its increment. What it
would exercise is the reorder of a pure binding check and a comment-only
de-duplication, and the `/1`-with-port path it shares is covered by two classes
that were re-run. That is the one open verification gap.

**Budget.** 15.37s of the 20s increment, every run wall-timed, no untimed run.
4.63s left unspent deliberately, because the ruling says report insufficiency
before spending past 20s. Campaign carry about 383.25s of 450s; observation 20s,
joined 40s and the 2.12s margin untouched.

State: awaiting independent review through baton.bug.
