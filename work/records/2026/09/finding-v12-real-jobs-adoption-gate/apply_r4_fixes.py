"""Claim-249687: the three R4 defects this reviewer found that I can close."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")

    # 1. THE ACCEPTED CANCELLATION, not a method name I guessed.
    body = body.replace(
        '''    measured["cancellation"] = {}
    for attempt_id in sorted(gate.launched):
        measured["cancellation"][attempt_id] = baseline._guarded(
            lambda one=attempt_id: operations.cancel(one), None,
            what=f"the cancellation of {attempt_id}",
            uncertainty=uncertainty, interrupted=caught) \\
            if hasattr(operations, "cancel") else "no cancellation port"''',
        '''    # THE ACCEPTED CANCELLATION PATH, not a method name I guessed. Review
    # 2026-09-23T17:44:56Z: this called `operations.cancel`, which no
    # composition exposes -- the port is `cancel_attempt`, and the supported
    # way to reach it is `baseline._cancel_active`, which fences the exact
    # participant and generation at the Authority BEFORE ordering quiescence.
    # Reporting "no cancellation port" for every attempt was reporting a leak
    # as a clean stop.
    measured["cancellation"] = baseline._guarded(
        lambda: baseline._cancel_active(
            operations, control, {"deployment": {"config_path":
                                                 deployment_path}},
            dict(gate.launched), {}, uncertainty,
            reason=measured["stopped"], launched=set(gate.launched),
            interrupted=caught),
        {}, what="the cancellation of what was still executing",
        uncertainty=uncertainty, interrupted=caught)''')

    # 2. SUCCESS IS PRODUCED, NOT MERELY UNOBJECTED-TO.
    body = body.replace(
        '''    held_because = []
    if measured["outstanding_cleanup"]:''',
        '''    held_because = []
    # A RUN THAT ADMITTED NOTHING HAS NOT SUCCEEDED. Review
    # 2026-09-23T17:44:56Z: an empty serve published `settled` with zero
    # admissions and no verdicts, because "settled" was defined as "nothing to
    # complain about". Success is what the run PRODUCED: four admissions, and
    # a positive cleanup for every runtime it started.
    expected = sum(dict(gate._caps).values())                 # noqa: SLF001
    if sum(measured["admissions"].values()) != expected:
        held_because.append(
            f"this run admitted {sum(measured['admissions'].values())} of the "
            f"{expected} stages it is configured for: "
            f"{measured['admissions']}. A run that admitted less than its "
            f"workload did not serve it")
    if not measured["admitted_attempts"]:
        held_because.append(
            "no runtime was ever launched, so there is nothing this run can "
            "claim to have stopped or cleaned up")
    if measured["outstanding_cleanup"]:''')

    # 3. THE TERMINATION HANDLER IS INSTALLED AND RESTORED.
    body = body.replace(
        '''    serving_failure = interrupted = None
    try:
        serve(job, gate, clock=clock, sleep=sleep,''',
        '''    serving_failure = interrupted = None
    # THE HANDLER IS INSTALLED AROUND EVERYTHING AND RESTORED AT THE END, as
    # it is in the accepted supervisor: a SIGTERM arriving during
    # cancellation, cleanup or publication must not resume the default
    # behaviour and kill the process with no outcome on disk. Review
    # 2026-09-23T17:44:56Z found it constructed and never installed.
    termination.install()
    try:
        serve(job, gate, clock=clock, sleep=sleep,''')
    body = body.replace(
        '''    # THE OUTCOME IS PUBLISHED ON EVERY PATH, including this one.
    baseline._publish(outcome_path, measured)''',
        '''    # THE OUTCOME IS PUBLISHED ON EVERY PATH, including this one, and the
    # handler is restored only after it is on disk.
    baseline._publish(outcome_path, measured)
    termination.restore()''')
    place.write_text(body, encoding="utf-8")
    print("cancellation, success derivation and termination corrected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
