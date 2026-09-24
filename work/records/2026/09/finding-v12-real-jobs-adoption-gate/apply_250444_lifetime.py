"""Claim-250444: the handler lifetime is the WHOLE run, not just publication.

Review 2026-09-23T19:22:24Z injected a fault in the final clock call, after
serving and cleanup, and measured the result: `installed=True`,
`restored=False`, `outcome_exists=False`. My `finally` surrounded `_publish`
alone, so every line between `gate.stop()` and the publication ran outside the
protection I said covered the run -- and a fault there left this process
holding a signal handler for a run that was over, with nothing on disk.

The comment above that block already claimed "INSTALLED AROUND EVERYTHING AND
RESTORED AT THE END". It was not, and the comment is why I did not look again.

WHAT THIS CHANGES:

  * An OUTER `try` spans everything from `install()` to the end, with the
    restoration in its `finally`. Nothing installed can now escape unrestored.
  * A fault anywhere after serving is CAUGHT, named in the document as
    `finalization_failure`, forced into `held`, published, and then re-raised.
    It is not converted into a tidy return and not swallowed.
  * The outcome is completed from honest defaults before publication, so a run
    that died half-accounted still writes a readable document that says which
    members it never reached rather than a partial one that reads like a
    finished run.
  * `finished_at` is taken through the guard, because the fault the reviewer
    injected WAS the clock -- a finalizer that re-raises on the same call it
    is recovering from protects nothing.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "two_job_supervisor.py"

OLD_INSTALL = '''    serving_failure = interrupted = None
    # THE HANDLER IS INSTALLED AROUND EVERYTHING AND RESTORED AT THE END, as
    # it is in the accepted supervisor: a SIGTERM arriving during
    # cancellation, cleanup or publication must not resume the default
    # behaviour and kill the process with no outcome on disk. Review
    # 2026-09-23T17:44:56Z found it constructed and never installed.
    termination.install()
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

    # ADMISSION IS CLOSED BEFORE ANYTHING IS CANCELLED.'''

NEW_INSTALL = '''    serving_failure = interrupted = None
    finalization_failure = faulted = None
    # THE HANDLER IS INSTALLED AROUND EVERYTHING AND RESTORED AT THE END --
    # and now it actually is. Review 2026-09-23T19:22:24Z injected a fault in
    # the FINAL CLOCK CALL, after serving and cleanup, and measured
    # `installed=True, restored=False, outcome_exists=False`: the `finally`
    # surrounded `_publish` alone, so every line between `gate.stop()` and the
    # publication ran outside the protection this comment claimed. A fault
    # there left this process holding a signal handler for a run that was over
    # with nothing on disk. The comment is part of why I did not look again.
    #
    # The outer `try` below spans from here to the end; its `finally` attempts
    # the outcome and restores the handler whatever happened in between.
    termination.install()
    try:
        try:
            serve(job, gate, clock=clock, sleep=sleep,
                  should_continue=should_continue, interval=1)
        except Exception as failure:                         # noqa: BLE001
            # A SERVING FAULT STOPS ADMISSION AND STILL OWES CLEANUP.
            serving_failure = f"{type(failure).__name__}: {failure}"
            held["stop"] = held["stop"] or "serving-failed"
        except BaseException as failure:                     # noqa: BLE001
            interrupted = f"{type(failure).__name__}: {failure}"
            held["stop"] = held["stop"] or "interrupted"

        # ADMISSION IS CLOSED BEFORE ANYTHING IS CANCELLED.'''

OLD_TAIL = '''    measured["held_because"] = held_because
    measured["state"] = "settled" if not held_because else "held"
    measured["finished_at"] = clock()

    # THE OUTCOME IS PUBLISHED ON EVERY PATH, including this one, and the
    # handler is restored in a `finally` -- a publication that raises must not
    # leave this process holding a signal handler that belongs to a run that
    # is over.
    try:
        baseline._publish(outcome_path, measured)
    finally:
        termination.restore()
    if measured["interruptions"]:
        # THE RETAINED OUTCOME TRAVELS WITH IT, as the accepted exception
        # carries it: an interruption is owed to the operator who sent it, and
        # a caller that wants to read what the run left behind still can.
        raise baseline.SupervisorInterrupted(measured["interruptions"][0],
                                             measured)
    return measured'''

NEW_TAIL = '''        measured["held_because"] = held_because
        measured["state"] = "settled" if not held_because else "held"
        measured["finished_at"] = _moment_of(clock)
    except BaseException as failure:                         # noqa: BLE001
        # A FAULT AFTER SERVING IS ACCOUNTED FOR, NOT LOST. It is named in the
        # document, forced into `held`, published by the `finally` below and
        # re-raised after the handler is restored -- a run that broke while
        # accounting for itself must not return as though it had finished.
        faulted = failure
        finalization_failure = f"{type(failure).__name__}: {failure}"
        if not isinstance(failure, Exception):
            caught.append(finalization_failure)
    finally:
        # THE OUTCOME IS ATTEMPTED ON EVERY PATH and the handler is restored on
        # every path, including the ones where the attempt itself fails.
        publication_failure = None
        try:
            _completed(measured, gate, clock,
                       finalization_failure=finalization_failure,
                       uncertainty=uncertainty, caught=caught)
            baseline._publish(outcome_path, measured)
        except BaseException as failure:                     # noqa: BLE001
            publication_failure = failure
        finally:
            termination.restore()

    if publication_failure is not None:
        # NOTHING IS ON DISK, which is the most serious ending this run has
        # and the only one an operator cannot read about afterwards.
        raise publication_failure
    if faulted is not None:
        raise faulted
    if measured["interruptions"]:
        # THE RETAINED OUTCOME TRAVELS WITH IT, as the accepted exception
        # carries it: an interruption is owed to the operator who sent it, and
        # a caller that wants to read what the run left behind still can.
        raise baseline.SupervisorInterrupted(measured["interruptions"][0],
                                             measured)
    return measured'''

# THE HELPERS THE NEW SHAPE NEEDS, placed above `supervise`.
OLD_ANCHOR = '''def supervise(job, control, operations, *, job_ids, bounds, outcome_path,'''

NEW_ANCHOR = '''# WHAT AN OUTCOME OWES A READER even when the run never reached the code that
# fills it. A half-written document that omits members reads like a finished
# run with nothing to report; these defaults make the absence explicit.
_OWED = (
    ("stopped", "stopped-without-a-reason"), ("serving_failure", None),
    ("admissions", dict), ("admitted_attempts", list),
    ("gate_refusals", list), ("foreign_admissions", list),
    ("admission_closed_before_cancellation", False),
    ("cleanup_window_seconds", None), ("cancellation", dict),
    ("cleanup_sweeps", 0), ("cleanup", dict), ("outstanding_cleanup", list),
    ("uncertainty", list), ("interruptions", list), ("generations", dict),
    ("verdicts", dict), ("held_because", list), ("finished_at", None),
)


def _moment_of(clock):
    """The instant, or None -- because the injected fault WAS the clock.

    Review 2026-09-23T19:22:24Z made the final clock call raise. A finalizer
    that re-raises on the same call it exists to recover from protects
    nothing, so this one answers None and the document says the instant was
    never taken.
    """
    try:
        return clock()
    except BaseException:                                    # noqa: BLE001
        return None


def _completed(measured, gate, clock, *, finalization_failure, uncertainty,
               caught):
    """Make `measured` publishable, whatever the run reached.

    IT NEVER OVERWRITES what the run already recorded -- a default is for a
    member the run never got to, and replacing a real value with a default
    would be this function inventing the account it exists to complete.
    """
    for name, default in _OWED:
        if name not in measured:
            measured[name] = default() if callable(default) else default
    measured["finalization_failure"] = finalization_failure
    if finalization_failure is not None:
        measured["held_because"] = list(measured["held_because"]) + [
            f"this run faulted after serving and did not finish accounting "
            f"for itself: {finalization_failure}"]
    measured["uncertainty"] = list(uncertainty)
    measured["interruptions"] = [one for one in measured["interruptions"]
                                 if one] or [one for one in caught if one]
    if measured.get("finished_at") is None:
        measured["finished_at"] = _moment_of(clock)
    # THE STATE IS DECIDED LAST, from the reasons that exist at publication.
    measured["state"] = "settled" if not measured["held_because"] else "held"
    del gate
    return measured


def supervise(job, control, operations, *, job_ids, bounds, outcome_path,'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def indent_block(body):
    """Everything between the two edited ends moves one level in.

    The serving-to-accounting run is now inside an outer `try`, so the lines
    the two swaps do not themselves rewrite have to be re-indented. Doing it
    by slice rather than by hand keeps the edit reviewable: the bytes are the
    same bytes, four columns over.
    """
    start = body.index("        # ADMISSION IS CLOSED BEFORE ANYTHING IS "
                       "CANCELLED.")
    start = body.index("\n", start) + 1
    end = body.index('        measured["held_because"] = held_because')
    middle = body[start:end]
    if "\n    measured[" not in middle:
        raise SystemExit("REFUSED: the block to re-indent is not where "
                         "expected; it may already have been moved")
    moved = "".join(("    " + one if one.strip() else one)
                    for one in middle.splitlines(keepends=True))
    return body[:start] + moved + body[end:]


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "_completed(" in body:
        raise SystemExit("REFUSED: the lifetime correction is already applied")
    body = swap(body, OLD_ANCHOR, NEW_ANCHOR, "the helper anchor")
    body = swap(body, OLD_INSTALL, NEW_INSTALL, "the install block")
    body = swap(body, OLD_TAIL, NEW_TAIL, "the publication block")
    body = indent_block(body)
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for absent in ("    try:\n        baseline._publish(outcome_path, "
                   "measured)\n    finally:\n        termination.restore()",):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the file")
    for present in ("def _completed(", "def _moment_of(",
                    "finalization_failure", "raise publication_failure",
                    "raise faulted"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("the handler lifetime now spans the whole run, verified on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
