"""Claim-249739: bounded ending EXECUTION inside the reserved window."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

OLD = '''    settled = baseline._guarded(
        lambda: baseline._cleanups(
            control, {"deployment": {"config_path": deployment_path}},
            dict(gate.launched)),
        None, what="the cleanup journal", uncertainty=uncertainty,
        interrupted=caught)
'''

NEW = '''    # THE RESERVED WINDOW IS DRIVEN, not merely recorded. Review
    # 2026-09-23T17:44:56Z: "remaining deadline only recorded, no bounded
    # cleanup execution". Closing the gate stops the NEXT runtime; what
    # settles the ones already started is the manager's ordinary sweep, and
    # with admission closed it can finish endings without being able to admit
    # anything. Each pass is inside what is left of the TOTAL, so the reserve
    # is a window rather than an extension.
    from baton_v12.job_manager import sweep

    measured["cleanup_sweeps"] = 0
    settled = None
    while monotonic() - started < total:
        settled = baseline._guarded(
            lambda: baseline._cleanups(
                control, {"deployment": {"config_path": deployment_path}},
                dict(gate.launched)),
            None, what="the cleanup journal", uncertainty=uncertainty,
            interrupted=caught)
        if settled is not None and not settled.get("outstanding"):
            break
        if not gate.launched:
            break
        baseline._guarded(lambda: sweep(job, gate, now=clock()), None,
                          what="a cleanup sweep", uncertainty=uncertainty,
                          interrupted=caught)
        measured["cleanup_sweeps"] += 1
        if measured["cleanup_sweeps"] >= CLEANUP_SWEEPS:
            break
'''


def swap(body, old, new, what):
    if old not in body:
        raise SystemExit(f"REFUSED: {what} is not in the file as written")
    return body.replace(old, new, 1)


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")
    body = swap(body, OLD, NEW, "the cleanup read")
    body = swap(
        body, 'OUTCOME_SCHEMA = "baton.v12.two-job-outcome/1"',
        'OUTCOME_SCHEMA = "baton.v12.two-job-outcome/1"\n\n'
        '# HOW MANY ENDING SWEEPS THE RESERVED WINDOW MAY DRIVE. A bound on\n'
        '# the window alone would let a fast clock spin; this bounds the acts.\n'
        'CLEANUP_SWEEPS = 12',
        "the outcome schema")
    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ("cleanup_sweeps", "from baton_v12.job_manager import sweep",
                    "CLEANUP_SWEEPS = 12"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("bounded ending execution added, and verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
