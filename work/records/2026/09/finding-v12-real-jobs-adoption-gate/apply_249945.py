"""Claim-249945: the worker-turn seam a supervised review needs."""
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
    body = swap(
        body,
        '''def supervise(job, control, operations, *, job_ids, bounds, outcome_path,
              deployment_path, caps=None, clock=None, sleep=None,
              monotonic=None, termination=None):''',
        '''def supervise(job, control, operations, *, job_ids, bounds, outcome_path,
              deployment_path, caps=None, clock=None, sleep=None,
              monotonic=None, termination=None, turns=None):''',
        "the supervise signature")
    body = swap(
        body,
        '''        gate.generations.update(
            generations_from(control, gate, uncertainty, caught))
        if gate.refusals:''',
        '''        gate.generations.update(
            generations_from(control, gate, uncertainty, caught))
        # THE WORKER-TURN SEAM, and it is a SEAM rather than a capability.
        # In a real deployment the runtime IS the turn: the manager starts a
        # container and the worker answers on its own. This build has no
        # daemon, so a deterministic driver stands exactly where the container
        # would, at the same boundary the accepted lifecycle fixtures use. A
        # caller that supplies none gets a run that starts nothing -- which is
        # what every case before this one measured.
        if turns is not None:
            baseline._guarded(lambda: turns(gate), None,
                              what="the deterministic worker turn",
                              uncertainty=uncertainty, interrupted=caught)
        if gate.refusals:''',
        "the tick")
    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ("turns=None):", "THE WORKER-TURN SEAM",
                    "lambda: turns(gate)"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("worker-turn seam added, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
