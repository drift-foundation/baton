"""Claim-249772: `main` could not open a store, and leaked on partial failure."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

OLD = '''    job = JobStore.open(chosen.job_store, incarnation=chosen.incarnation,
                        authority_uuid=deployment["authority_uuid"])
    control = ControlStore.open(chosen.control_store,
                                incarnation=chosen.incarnation)
    composed = stage_execution.operations_from(deployment, job, control)
    try:
        submit(job, submission)
        measured = supervise(
            job, control, composed, job_ids=job_ids,
            bounds={"total_seconds": chosen.total_seconds,
                    "cleanup_seconds": chosen.cleanup_seconds},
            outcome_path=chosen.outcome,
            deployment_path=chosen.deployment)
    finally:
        # EVERY HANDLE THIS COMMAND OPENED IS CLOSED, on every path.
        for one in (composed, control, job):
            try:
                one.close()
            except Exception:                                # noqa: BLE001
                pass
'''

NEW = '''    # BOTH OPENERS REQUIRE A CLOCK, and neither was given one -- so this
    # command could not open a store at all. Review 2026-09-23T17:56:23Z
    # confirmed it against the pinned signatures. `baseline._moment` is the
    # instant source the accepted supervisor uses; there is no second clock.
    #
    # AND ACQUISITION IS INSIDE THE `try`. It was above it, so a failure
    # opening the control store or composing the operations leaked the handles
    # already taken. `opened` is appended to as each one succeeds, and the
    # `finally` closes exactly what exists.
    opened = []
    measured = None
    try:
        job = JobStore.open(chosen.job_store,
                            authority_uuid=deployment["authority_uuid"],
                            incarnation=chosen.incarnation,
                            clock=baseline._moment)
        opened.append(job)
        control = ControlStore.open(chosen.control_store,
                                    incarnation=chosen.incarnation,
                                    clock=baseline._moment)
        opened.append(control)
        composed = stage_execution.operations_from(deployment, job, control)
        opened.append(composed)
        submit(job, submission)
        measured = supervise(
            job, control, composed, job_ids=job_ids,
            bounds={"total_seconds": chosen.total_seconds,
                    "cleanup_seconds": chosen.cleanup_seconds},
            outcome_path=chosen.outcome,
            deployment_path=chosen.deployment)
    finally:
        # EVERY HANDLE THIS COMMAND OPENED IS CLOSED, on every path, newest
        # first: a composition closed after its stores would be closing over
        # handles that are already gone.
        for one in reversed(opened):
            try:
                one.close()
            except Exception:                                # noqa: BLE001
                pass
    if measured is None:                                     # pragma: no cover
        return 2
'''


def swap(body, old, new, what):
    if old not in body:
        raise SystemExit(f"REFUSED: {what} is not in the file as written")
    return body.replace(old, new, 1)


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")
    body = swap(body, OLD, NEW, "main's acquisition block")
    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ("clock=baseline._moment", "opened = []",
                    "for one in reversed(opened)"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("main's store contracts and acquisition corrected, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
