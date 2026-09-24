"""Claim-249919: the ASSIGNMENT generation, not the pool's."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

OLD_START = "def generations_from(job, operations, gate, uncertainty, caught, *,\n                     observed_at):"

NEW = '''def generations_from(control, gate, uncertainty, caught):
    """Each admitted attempt's ASSIGNMENT generation, from the control store.

    Review 2026-09-23T18:16:47Z: the previous version read
    `allocation.generation` out of the status projection, and that is the POOL
    generation -- `projection._stage_status` gets it from
    `scheduler.allocation_of`, which joins `pool_generations`. The schema
    distinguishes the two axes on purpose, and my "it is not None" check could
    not tell coincident counters apart. Two axes that happen to both be 1 is
    the easiest possible false pass.

    `attempts.assignment_of` is the supported reader for the DURABLE
    assignment identity fixed to an attempt -- the accepted `baseline` uses it
    for exactly this -- and it REFUSES an attempt that has not activated one.
    That refusal is honest absence: it lands in `uncertainty` and the verdict
    for that attempt is simply not derived.
    """
    from baton_v12.worker_manager import attempts as attempt_rows

    held = {}
    for attempt_id in sorted(gate.launched):
        assignment = baseline._guarded(
            lambda one=attempt_id: attempt_rows.assignment_of(control, one),
            None, what=f"the fixed assignment of {attempt_id}",
            uncertainty=uncertainty, interrupted=caught)
        if assignment and assignment.get("generation") is not None:
            held[attempt_id] = assignment["generation"]
    return held'''


def swap(body, old, new, what):
    if old not in body:
        raise SystemExit(f"REFUSED: {what} is not in the file as written")
    return body.replace(old, new, 1)


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")
    start = body.index(OLD_START)
    end = body.index("\ndef verdicts_of(control, gate, uncertainty, caught):")
    body = body[:start] + NEW + "\n\n" + body[end:]
    body = swap(
        body,
        '''        gate.generations.update(
            generations_from(job, operations, gate, uncertainty, caught,
                             observed_at=clock()))
        if gate.refusals:''',
        '''        gate.generations.update(
            generations_from(control, gate, uncertainty, caught))
        if gate.refusals:''',
        "the per-tick capture")
    body = swap(
        body,
        '''    gate.generations.update(
        generations_from(job, operations, gate, uncertainty, caught,
                         observed_at=clock()))''',
        '''    gate.generations.update(
        generations_from(control, gate, uncertainty, caught))''',
        "the stop-time capture")
    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ("attempt_rows.assignment_of(control, one)",
                    "def generations_from(control, gate, uncertainty, caught)"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    if "allocation.get(\"generation\")" in written:
        raise SystemExit("REFUSED: the pool-generation read survives")
    print("assignment generation read through the supported reader, verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
