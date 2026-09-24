"""Claim-249713: the cancellation fix I REPORTED but never applied, and a
`finally` around publication.

EVERY REPLACEMENT HERE IS VERIFIED. The previous edit script printed
"corrected" unconditionally, one of its two replacements silently matched
nothing, and I passed the Work back claiming a fix that was not in the file.
`swap` raises when the old text is absent and the caller checks the result, so
this script cannot lie about what it did.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

OLD_CANCEL = '''    measured["cancellation"] = {}
    for attempt_id in sorted(gate.launched):
        measured["cancellation"][attempt_id] = baseline._guarded(
            lambda one=attempt_id: operations.cancel(one), None,
            what=f"the cancellation of {attempt_id}",
            uncertainty=uncertainty, interrupted=caught)             if hasattr(operations, "cancel") else "no cancellation port"
'''

NEW_CANCEL = '''    # THE ACCEPTED CANCELLATION PATH. This called `operations.cancel`, which
    # NO composition exposes -- the port is `cancel_attempt` -- so every
    # attempt was recorded as "no cancellation port" while the run still
    # reported its stop. That is reporting a LEAK AS A CLEAN STOP.
    # `_cancel_active` fences the exact participant and generation at the
    # Authority before ordering quiescence, and reports honestly when a
    # composition really does offer no port.
    measured["cancellation"] = baseline._guarded(
        lambda: baseline._cancel_active(
            operations, control,
            {"deployment": {"config_path": deployment_path}},
            dict(gate.launched), dict(held.get("states") or {}), uncertainty,
            reason=measured["stopped"], launched=set(gate.launched),
            interrupted=caught),
        {}, what="the cancellation of what was still executing",
        uncertainty=uncertainty, interrupted=caught)
'''

OLD_PUBLISH = '''    # THE OUTCOME IS PUBLISHED ON EVERY PATH, including this one, and the
    # handler is restored only after it is on disk.
    baseline._publish(outcome_path, measured)
    termination.restore()
'''

NEW_PUBLISH = '''    # THE OUTCOME IS PUBLISHED ON EVERY PATH, including this one, and the
    # handler is restored in a `finally` -- a publication that raises must not
    # leave this process holding a signal handler that belongs to a run that
    # is over.
    try:
        baseline._publish(outcome_path, measured)
    finally:
        termination.restore()
'''


def swap(body, old, new, what):
    if old not in body:
        raise SystemExit(f"REFUSED: {what} is not in the file as written; "
                         f"nothing was changed")
    return body.replace(old, new, 1)


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")
    body = swap(body, OLD_CANCEL, NEW_CANCEL, "the cancellation block")
    body = swap(body, OLD_PUBLISH, NEW_PUBLISH, "the publication block")
    place.write_text(body, encoding="utf-8")
    # AND THE RESULT IS READ BACK, because a script that reports its own
    # success is the thing that failed last time.
    written = place.read_text(encoding="utf-8")
    # THE CALL, not the word: the comment above the fix NAMES the method that
    # was wrong, and a check that cannot tell an explanation from a call
    # refuses a correct file.
    for absent in ("operations.cancel(", 'attempt_id] = "no cancellation'):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the file")
    for present in ("_cancel_active", "finally:\n        termination.restore()"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("cancellation and publication corrected, and verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
