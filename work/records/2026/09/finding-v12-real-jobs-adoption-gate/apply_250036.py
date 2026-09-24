"""Claim-250036: the turn's runtime context, and `main`'s clock seams."""
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

    # 1. THE TURN GETS THE RUNTIME CONTEXT IT NEEDS.
    body = swap(
        body,
        '''        if turns is not None:
            baseline._guarded(lambda: turns(gate), None,
                              what="the deterministic worker turn",
                              uncertainty=uncertainty, interrupted=caught)''',
        '''        if turns is not None:
            # THE CONTEXT A TURN NEEDS, because a turn has to reach the
            # attempt's mounted workspace and that lives on the composition.
            # Review 2026-09-23T18:33:25Z: a callback given only the gate can
            # do no work, which is why the entry-point case proved nothing.
            baseline._guarded(
                lambda: turns(gate, {"operations": operations, "job": job,
                                     "control": control}),
                None, what="the deterministic worker turn",
                uncertainty=uncertainty, interrupted=caught)''',
        "the turn invocation")

    # 2. `main` TAKES THE CLOCK SEAMS, production defaults unchanged.
    body = swap(
        body,
        '''def main(argv=None, *, stream=None, credential_provider=None,
         engine_run=None, clock=None, checkout=None, turns=None):''',
        '''def main(argv=None, *, stream=None, credential_provider=None,
         engine_run=None, clock=None, checkout=None, turns=None,
         monotonic=None, sleep=None):''',
        "main's signature")
    body = swap(
        body,
        '''            deployment_path=chosen.deployment,
            turns=turns)''',
        '''            deployment_path=chosen.deployment,
            turns=turns, monotonic=monotonic, sleep=sleep)''',
        "main's supervised run")

    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ('turns(gate, {"operations": operations',
                    "monotonic=None, sleep=None):",
                    "turns=turns, monotonic=monotonic, sleep=sleep)"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("turn context and main clock seams added, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
