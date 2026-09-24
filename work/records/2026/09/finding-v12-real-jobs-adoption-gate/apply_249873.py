"""Claim-249873: the REAL prepared generation, from the allocation itself."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

HELPER = '''

def generations_from(job, operations, gate, uncertainty, caught):
    """Each admitted attempt's ACTUAL assignment generation.

    Review 2026-09-23T18:10:37Z: the projection attempt the manager hands
    `launch` is built from the stage columns plus episode, offer and attempt
    identities -- it carries NO generation, and my launch recorder therefore
    recorded none. The test that seemed to prove otherwise supplied a
    synthetic one.

    THE ALLOCATION IS WHERE IT LIVES. `baton.v12.job-status/4` reports each
    stage's allocation with its `generation`, `worker_id`, participant and
    principal -- the owner's own record of the assignment this attempt was
    prepared under. That is a supported public read, and it is the generation
    `review_for_attempt` fences an attachment to.
    """
    from baton_v12.job_manager import status as projected

    held = {}
    projection = baseline._guarded(
        lambda: projected(job, operations),
        None, what="the status projection the generations are read from",
        uncertainty=uncertainty, interrupted=caught)
    if not projection:
        return held
    for one in projection.get("jobs", ()):
        if one.get("job_id") not in gate.job_ids:
            continue
        for stage in one.get("stages", ()):
            allocation = stage.get("allocation") or {}
            attempt_id = stage.get("attempt_id")
            if attempt_id and allocation.get("generation") is not None:
                held[attempt_id] = allocation["generation"]
    return held
'''


def swap(body, old, new, what):
    if old not in body:
        raise SystemExit(f"REFUSED: {what} is not in the file as written")
    return body.replace(old, new, 1)


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")
    body = swap(body, "\ndef verdicts_of(control, gate, uncertainty, caught):",
                HELPER + "\ndef verdicts_of(control, gate, uncertainty, caught):",
                "the verdicts_of definition")
    # the supervisor records them before deriving verdicts
    body = swap(
        body,
        '''    measured["verdicts"] = verdicts_of(control, gate, uncertainty, caught)''',
        '''    # THE GENERATIONS COME FROM THE ALLOCATIONS, read once here, before any
    # verdict is derived: `review_for_attempt` fences an attachment to one
    # activated generation and refuses `None`.
    gate.generations.update(
        generations_from(job, operations, gate, uncertainty, caught))
    measured["generations"] = dict(gate.generations)
    measured["verdicts"] = verdicts_of(control, gate, uncertainty, caught)''',
        "the verdict derivation")
    # the launch recorder no longer claims a generation it never sees
    body = swap(
        body,
        '''                for name in ("assignment_generation", "generation"):
                    if attempt.get(name) is not None:
                        self._generations[attempt_id] = attempt[name]
                        break''',
        '''                # NO GENERATION IS READ HERE. The projection attempt the
                # manager passes carries none, and recording a default would
                # be inventing the fact `review_for_attempt` fences on.
                # `generations_from` reads it from the allocation instead.
                for name in ("assignment_generation", "generation"):
                    if attempt.get(name) is not None:        # pragma: no cover
                        self._generations[attempt_id] = attempt[name]
                        break''',
        "the launch recorder")
    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ("def generations_from(", 'measured["generations"]',
                    "NO GENERATION IS READ HERE"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("real generations read from the allocations, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
