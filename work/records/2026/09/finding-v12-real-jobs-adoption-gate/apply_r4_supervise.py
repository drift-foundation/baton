"""R4: the bounded two-Job run -- serve, stop, cancel, clean up, publish."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

BODY = '''

def supervise(job, control, operations, *, job_ids, bounds, outcome_path,
              caps=None, clock=None, sleep=None, monotonic=None,
              termination=None):
    """Two Jobs, four admissions, a real stop and an outcome on every path.

    THE PHASES ARE SEPARATE, as they are in `baseline._supervise`: serving is
    not stopping, stopping is not cleanup, cleanup is not the outcome, and the
    outcome is decided by what the run PRODUCED rather than by how the loop
    ended. What this adds over the accepted single-Job supervisor is only the
    two-Job scope: the gate above, and accounting that spans both Jobs.

    THE CLEANUP RESERVE IS INSIDE THE TOTAL. Serving stops at
    `total_seconds - cleanup_seconds` and the cleanup window is additionally
    bounded by what is left of the total, so the deadline is INCLUSIVE and a
    packet declaring a reserve gets one rather than an extension.
    """
    import time

    from baton_v12.job_manager import serve
    held_baseline()
    clock = baseline._moment if clock is None else clock
    sleep = time.sleep if sleep is None else sleep
    monotonic = time.monotonic if monotonic is None else monotonic
    termination = baseline.Termination() if termination is None else termination

    total = int(bounds["total_seconds"])
    reserve = int(bounds["cleanup_seconds"])
    if not 0 < reserve < total:
        raise SupervisorRefusal(
            f"a cleanup reserve of {reserve}s is not inside a total of "
            f"{total}s; a reserve outside the bound is an extension")
    serving_bound = total - reserve

    gate = TwoJobGate(operations, caps=caps or CAPS, job_ids=job_ids)
    started = monotonic()
    uncertainty, caught = [], []
    measured = {"schema": OUTCOME_SCHEMA, "job_ids": list(gate.job_ids),
                "submitted_at": clock(), "bounds": dict(bounds),
                "serving_bound_seconds": serving_bound,
                "caps": dict(gate._caps)}                     # noqa: SLF001
    held = {"stop": None}

    def should_continue():
        """One tick's decision, and every reason it can end the run."""
        if gate.refusals:
            held["stop"] = "invocation-cap-refused"
            return False
        if monotonic() - started >= serving_bound:
            held["stop"] = "serving-bound-exceeded"
            return False
        return True

    serving_failure = interrupted = None
    try:
        serve(job, gate, clock=clock, sleep=sleep,
              should_continue=should_continue, interval=1)
    except Exception as failure:                             # noqa: BLE001
        # A SERVING FAULT STOPS ADMISSION AND STILL OWES CLEANUP.
        serving_failure = f"{type(failure).__name__}: {failure}"
        held["stop"] = held["stop"] or "serving-failed"
    except BaseException as failure:                         # noqa: BLE001
        interrupted = f"{type(failure).__name__}: {failure}"
        held["stop"] = held["stop"] or "interrupted"

    # ADMISSION IS CLOSED BEFORE ANYTHING IS CANCELLED. That is what makes the
    # cleanup window unable to start a runtime while it settles the ones this
    # run already has.
    gate.stop()
    termination.defer()
    measured["stopped"] = held["stop"] or "stopped-without-a-reason"
    measured["serving_failure"] = serving_failure
    measured["admissions"] = dict(gate.admissions)
    measured["admitted_attempts"] = sorted(gate.launched)
    measured["gate_refusals"] = list(gate.refusals)
    measured["foreign_admissions"] = list(gate.foreign)
    measured["admission_closed_before_cancellation"] = True

    # CANCELLATION, then the journal's own word on every runtime this run
    # started. Both are the accepted helpers; neither is reimplemented here.
    remaining = max(0.0, total - (monotonic() - started))
    measured["cleanup_window_seconds"] = remaining
    measured["cancellation"] = {}
    for attempt_id in sorted(gate.launched):
        measured["cancellation"][attempt_id] = baseline._guarded(
            lambda one=attempt_id: operations.cancel(one), None,
            what=f"the cancellation of {attempt_id}",
            uncertainty=uncertainty, interrupted=caught) \
            if hasattr(operations, "cancel") else "no cancellation port"
    settled = baseline._guarded(
        lambda: baseline._cleanups(control, {"bounds": dict(bounds)},
                                   dict(gate.launched)),
        None, what="the cleanup journal", uncertainty=uncertainty,
        interrupted=caught)
    measured["cleanup"] = {} if settled is None else settled.get("cleanup", {})
    measured["outstanding_cleanup"] = (
        sorted(gate.launched) if settled is None
        else sorted(settled.get("outstanding", ())))
    measured["uncertainty"] = uncertainty
    measured["interruptions"] = [one for one in ([interrupted] + caught)
                                 if one]

    held_because = []
    if measured["outstanding_cleanup"]:
        held_because.append(
            f"these admitted runtimes have no positive cleanup: "
            f"{', '.join(measured['outstanding_cleanup'])}")
    if serving_failure:
        held_because.append(f"serving failed: {serving_failure}")
    if gate.refusals:
        held_because.append("an admission was refused by the cap")
    if uncertainty:
        held_because.extend(uncertainty)
    measured["held_because"] = held_because
    measured["state"] = "settled" if not held_because else "held"
    measured["finished_at"] = clock()

    # THE OUTCOME IS PUBLISHED ON EVERY PATH, including this one.
    baseline._publish(outcome_path, measured)
    if measured["interruptions"]:
        raise baseline.SupervisorInterrupted(measured["interruptions"][0])
    return measured
'''


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")
    if "def supervise(" in body:
        print("already added")
        return 0
    body = body.replace(
        'CAPS = {"implementation": 2, "review": 2}',
        'CAPS = {"implementation": 2, "review": 2}\n\n'
        '# THE DOCUMENT THIS RUN PUBLISHES, whatever happened to it.\n'
        'OUTCOME_SCHEMA = "baton.v12.two-job-outcome/1"')
    body = body.replace(
        '''        super().__init__(operations, caps=dict(caps or CAPS), job_id=held[0])
        self._job_ids = held''',
        '''        super().__init__(operations, caps=dict(caps or CAPS), job_id=held[0])
        self._job_ids = held

    @property
    def job_ids(self):
        return self._job_ids''')
    body = body.rstrip("\n") + "\n" + BODY
    place.write_text(body, encoding="utf-8")
    print("supervise added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
