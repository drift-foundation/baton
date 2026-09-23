# The expired-credential run: what happened, and the two things that were wrong

Claim 242687, baton.claude, W239528, under owner pass 242683. Every fact here
is read out of the run's own retained evidence or out of the product's source.
`/home/sl/baton-runs/single-implementation-239528/run` was read and not
modified; no store belonging to it was opened. Copies of the evidence are in
`live-242687/` beside this file.

## What the run did

The owner ran the accepted bounded command on the fresh isolated instance. One
implementation container started. `outcome.json`:

    state              held          stopped        overall-bound-exceeded
    job_id             job-single-implementation-239528
    admissions         implementation 1
    stage_states       implementation answering
    served_seconds     901.0         cleanup_sweeps 55
    preexisting_jobs   []            foreign_admissions []
    outstanding_cleanup  [attempt-e2433024...]

## The provider failed in 31 milliseconds, and said so clearly

`live-242687/logs/provider.stdout.log`, the CLI's own terminal record:

    is_error          true
    terminal_reason   api_error
    duration_ms       31
    result            "Failed to authenticate: OAuth session expired and
                       could not be refreshed"

## The adapter was right

`live-242687/events/terminal.json`:

    ending            answered
    disposition       unable
    fault_code        null
    manifest_digest   sha256:fb3a0bc3...

It answered rather than faulting, published a real result manifest, and placed
no proposal claim on the output -- which is exactly what
`claude_agent._ended` does when it has no candidate. **Nothing in the adapter
is changed by this correction.**

## Defect one -- publication was an unconditional step of the ending

`review_driver.end_implementation` runs nine steps and performs publication as
step seven, for every disposition. `integration.retain_proposal` refuses -- and
is right to -- when the frozen result is not `completed`:

    attempt '...' has no completed frozen result to propose

So steps one to six committed (quiesce, observe disposition, freeze, correlate,
intake receipt, retention) and steps **eight and nine never ran**: the
assignment was never fenced and `authorize_cleanup` was never called.
`_ending_owed` stayed true, the stage projected `answering`, and every sweep
re-attempted `conclude` and recorded the same durable refusal.

**The manager's own deferral row names it.** Reproduced deterministically from
the retained provider bytes:

    stage_id  job-a/implementation   act  conclude   category  refused
    message   "attempt '...' has no completed frozen result to propose"

**This is not W236087's cleanup stall.** That one never reached
`authorize_cleanup` because a faulted turn froze and collected nothing, so no
intake receipt existed and the axis read `pending`. Here the receipt DOES
exist; the ending is blocked one step further on.

## Defect two -- the composed stage confused two different holds

Correcting defect one made cleanup commit positively. **The stage still sat in
`answering` for the whole bound.**

`stage_execution`'s composed conclude, for a contextual worker:

    if context["disposition"] != "completed":
        provider_context.hold_context_use(..., reason="invocation-unknown")
        return dict(answered, outcome="held", reason="provider-context-unknown")

Holding the CONTEXT USE is correct and is kept: a provider generation whose
turn did not complete cannot be accounted for and must never be finalized.
But `outcome: "held"` is the REVIEW vocabulary for "nobody may be scheduled on
this", and `_finished` reads it as "the ending did not finish" and returns
before `settle_ending`. So the registered ending obligation stayed owed, and
`_ending_owed` asks that first -- before the cleanup axis it would otherwise
have been satisfied by.

Two different facts had one answer. They are separated now: the context use is
held and travels as its own member, and the stage ending settles.

## The correction, and what it does not do

1. `review_driver`: `PUBLISHABLE = ("completed",)`, applied in the ordinary
   ending and in both resume entries. A result with no candidate publishes
   nothing, reads back nothing on resume, and still reaches steps eight and
   nine. `published` is `null` rather than absent -- the step was reached and
   was not owed.
2. `stage_execution`: a non-completed contextual turn holds its context use,
   carries `context_use: "held"` and `context_hold` in its answer, and
   proceeds to `_finished` so the obligation settles.

**It does not touch the adapter, the retention decision, the intake receipt,
the context hold, or the `provider-context-unproved` branch** -- a COMPLETED
turn whose context finalization refuses still owes its ending, and the cases
covering that are unchanged and still pass.

## What it measures

Same retained bytes, same real adapter, real ending driver, real composed
stage, real cleanup journal:

    before   stopped overall-bound-exceeded at tick 901
             implementation answering, cleanup null, outstanding 1
    after    stopped exceptional at tick 3
             implementation exceptional, cleanup retained/absent, outstanding 0
             state held, no proposal, no false success

`test_failure_path.py` asserts all four of the owner's requirements
separately, and pins the retained bytes by digest so a later edit to the
evidence is a failing test.

## Accepted tests whose expectations changed, and why

Nine cases in `tests/manager/test_claude_context.py` asserted, through
`assert_owed`, that an unhealthy provider terminal leaves the ending obligation
owed. **Their subject is unchanged and is still asserted**: the terminal is not
accepted and the context use never becomes `ready`. What changed is the stage
half, which is the behaviour owner pass 242683 ruled wrong.

`assert_owed` is KEPT for the cases that genuinely still owe an ending -- a
completed turn whose context finalization refuses -- and those call sites are
untouched and still pass. The new `assert_reported_and_held` carries the
corrected contract and says in its own docstring why it exists.

This is the highest-risk part of the change and it is called out here so a
reviewer looks at it first.

## Still outstanding, and not done here

The credentials are expired by owner decision and were not renewed. No live
rerun. The run directory is preserved. W236087's outstanding runtime is
untouched. No reviewer stage and no resume.
