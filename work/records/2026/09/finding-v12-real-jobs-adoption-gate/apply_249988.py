"""Claim-249988: seams on `main`, so the ENTRY POINT can reach a success."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

OLD = '''def main(argv=None, *, stream=None):'''
NEW = '''def main(argv=None, *, stream=None, credential_provider=None,
         engine_run=None, clock=None, checkout=None, turns=None):'''

OLD_COMPOSE = '''        composed = stage_execution.operations_from(deployment, job, control)'''
NEW_COMPOSE = '''        # THE SEAMS, and every one of them defaults to PRODUCTION. A caller
        # that supplies none gets the real provider, the real engine, the real
        # clock and no worker turn -- which is exactly what an operator typing
        # the documented command gets. Review 2026-09-23T18:26:13Z asked for
        # the entry point to be reachable by a deterministic witness with a
        # disposable provider and registry; these are where that witness
        # stands, at the same boundary the accepted lifecycle fixtures use.
        composing = {}
        if credential_provider is not None:
            composing["credential_provider"] = credential_provider
        if engine_run is not None:
            composing["engine_run"] = engine_run
        if clock is not None:
            composing["clock"] = clock
        if checkout is not None:
            composing["checkout"] = checkout
        composed = stage_execution.operations_from(deployment, job, control,
                                                   **composing)'''

OLD_RUN = '''        measured = supervise(
            job, control, composed, job_ids=job_ids,
            bounds={"total_seconds": chosen.total_seconds,
                    "cleanup_seconds": chosen.cleanup_seconds},
            outcome_path=chosen.outcome,
            deployment_path=chosen.deployment)'''
NEW_RUN = '''        measured = supervise(
            job, control, composed, job_ids=job_ids,
            bounds={"total_seconds": chosen.total_seconds,
                    "cleanup_seconds": chosen.cleanup_seconds},
            outcome_path=chosen.outcome,
            deployment_path=chosen.deployment,
            turns=turns)'''


def swap(body, old, new, what):
    if old not in body:
        raise SystemExit(f"REFUSED: {what} is not in the file as written")
    return body.replace(old, new, 1)


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")
    body = swap(body, OLD, NEW, "main's signature")
    body = swap(body, OLD_COMPOSE, NEW_COMPOSE, "main's composition")
    body = swap(body, OLD_RUN, NEW_RUN, "main's supervised run")
    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ("credential_provider=None,", "composing[\"engine_run\"]",
                    "turns=turns)"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("main seams added, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
