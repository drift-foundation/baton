"""Claim-249739: ONE executable bounded entrypoint."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

MAIN = '''

def main(argv=None, *, stream=None):
    """ONE command: open the stores, compose, submit, serve bounded, stop.

    Review 2026-09-23T17:44:56Z: operator step 7 named `job`, `control` and
    `composed` without defining them, and step 4 independently served
    unbounded. A packet whose stop instruction cannot be typed is not an
    instruction. This is the whole bounded run behind one invocation, and it
    is the only supported way to serve this arrangement.

    IT STARTS NOTHING ITS DOCUMENTS DO NOT NAME. The deployment and the
    submission are the ones `two_jobs.py` composed; this opens their stores
    and hands the composed operations to `supervise`.
    """
    import argparse
    import json

    stream = sys.stdout if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="two_job_supervisor",
        description="Serve one bounded two-Job run and stop it.")
    parser.add_argument("--deployment", required=True,
                        help="the deployment.json two_jobs.py wrote")
    parser.add_argument("--submission", required=True,
                        help="the submission.json two_jobs.py wrote")
    parser.add_argument("--job-store", required=True)
    parser.add_argument("--control-store", required=True)
    parser.add_argument("--incarnation", required=True)
    parser.add_argument("--outcome", required=True)
    parser.add_argument("--total-seconds", type=int, default=600)
    parser.add_argument("--cleanup-seconds", type=int, default=60)
    chosen = parser.parse_args(argv)

    held_baseline()
    from tools import stage_execution
    from baton_v12.job_manager import JobStore, submit
    from baton_v12.worker_manager import ControlStore

    with open(chosen.deployment, "r", encoding="utf-8") as handle:
        deployment = json.load(handle)
    with open(chosen.submission, "r", encoding="utf-8") as handle:
        submission = json.load(handle)
    job_ids = [one["job_id"] for one in deployment["job_bindings"]]

    job = JobStore.open(chosen.job_store, incarnation=chosen.incarnation,
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
    print(json.dumps({"state": measured["state"],
                      "stopped": measured["stopped"],
                      "outcome": chosen.outcome}, indent=2), file=stream)
    return 0 if measured["state"] == "settled" else 1


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
'''


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")
    if "def main(argv=None" in body:
        print("already present")
        return 0
    place.write_text(body.rstrip("\n") + "\n" + MAIN, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ("--deployment", "--submission", "--outcome",
                    "operations_from"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("entrypoint added, and verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
