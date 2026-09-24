"""Claim-250071: `main` forwarded its clock to the composition alone."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def swap(body, old, new, what):
    if old not in body:
        raise SystemExit(f"REFUSED: {what} is not in the file as written")
    return body.replace(old, new, 1)


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")

    # ONE CLOCK FOR THE WHOLE COMMAND. Review 2026-09-23T18:38:26Z's lead:
    # `main` forwarded `clock` to `operations_from` and to NOTHING else, so
    # both store openers and the supervisor kept `baseline._moment` while the
    # composition stamped a different instant. A run whose composition and
    # whose manager disagree about the time is not one run.
    body = swap(
        body,
        '''        job = JobStore.open(chosen.job_store,
                            authority_uuid=deployment["authority_uuid"],
                            incarnation=chosen.incarnation,
                            clock=baseline._moment)''',
        '''        moment = baseline._moment if clock is None else clock
        job = JobStore.open(chosen.job_store,
                            authority_uuid=deployment["authority_uuid"],
                            incarnation=chosen.incarnation,
                            clock=moment)''',
        "main's Job store opener")
    body = swap(
        body,
        '''        control = ControlStore.open(chosen.control_store,
                                    incarnation=chosen.incarnation,
                                    clock=baseline._moment)''',
        '''        control = ControlStore.open(chosen.control_store,
                                    incarnation=chosen.incarnation,
                                    clock=moment)''',
        "main's control store opener")
    body = swap(
        body,
        '''            deployment_path=chosen.deployment,
            turns=turns, monotonic=monotonic, sleep=sleep)''',
        '''            deployment_path=chosen.deployment,
            turns=turns, monotonic=monotonic, sleep=sleep, clock=clock)''',
        "main's supervised run")

    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ("moment = baseline._moment if clock is None else clock",
                    "clock=moment)", "sleep=sleep, clock=clock)"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    if "clock=baseline._moment)" in written:
        raise SystemExit("REFUSED: an opener still pins its own clock")
    print("one clock forwarded through the whole command, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
