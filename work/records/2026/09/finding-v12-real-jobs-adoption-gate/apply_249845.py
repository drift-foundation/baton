"""Claim-249845: record the provenance `verdicts_of` reads, at the launch."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

OLD = '''    __slots__ = ("_job_ids",)

    def __init__(self, operations, *, caps=None, job_ids):
        held = tuple(dict.fromkeys(job_ids))
        if len(held) != 2:
            raise SupervisorRefusal(
                f"this gate serves exactly two Jobs and was given {held!r}; "
                f"one Job named twice is one Job, and a third is a different "
                f"selection with its own capacity question")
        super().__init__(operations, caps=dict(caps or CAPS), job_id=held[0])
        self._job_ids = held

    @property
    def job_ids(self):
        return self._job_ids

    @property
    def generations(self):
        """The assignment generation each launched attempt was admitted at."""
        return getattr(self, "_generations", {})

    def job_of(self, attempt_id):
        """Which bound Job an attempt this gate launched belongs to."""
        return self.stage_jobs.get(self.stage_of.get(attempt_id))

    @property
    def stage_of(self):
        return getattr(self, "_stage_of", {})
'''

NEW = '''    __slots__ = ("_job_ids", "_generations", "_stage_of")

    def __init__(self, operations, *, caps=None, job_ids):
        held = tuple(dict.fromkeys(job_ids))
        if len(held) != 2:
            raise SupervisorRefusal(
                f"this gate serves exactly two Jobs and was given {held!r}; "
                f"one Job named twice is one Job, and a third is a different "
                f"selection with its own capacity question")
        super().__init__(operations, caps=dict(caps or CAPS), job_id=held[0])
        self._job_ids = held
        # THE PROVENANCE `verdicts_of` READS, recorded where it exists.
        # Review 2026-09-23T18:06:35Z: these two were read through `getattr`
        # defaults and NOTHING EVER WROTE THEM, so the public attachment
        # reader was handed `generation=None` and refused, and `job_of`
        # answered None. A reader with a default for a fact nobody records is
        # a reader that always answers "unknown" quietly.
        self._generations = {}
        self._stage_of = {}

    @property
    def job_ids(self):
        return self._job_ids

    @property
    def generations(self):
        """The assignment generation each launched attempt was admitted at."""
        return self._generations

    @property
    def stage_of(self):
        """The stage each launched attempt belongs to."""
        return self._stage_of

    def job_of(self, attempt_id):
        """Which bound Job an attempt this gate launched belongs to."""
        return self.stage_jobs.get(self._stage_of.get(attempt_id))

    def launch(self, attempt, job):
        """The inherited launch, plus the two facts a verdict read needs.

        RECORDED AT THE CALL, before delegating, exactly as the inherited gate
        records the launch itself: an attempt that then faults is still one
        this run must account for, and a fact reconstructed from a projection
        between ticks can be lost.
        """
        if type(attempt) is dict:
            attempt_id = attempt.get("attempt_id")
            if attempt_id is not None:
                stage_id = attempt.get("stage_id")
                if stage_id is not None:
                    self._stage_of[attempt_id] = stage_id
                for name in ("assignment_generation", "generation"):
                    if attempt.get(name) is not None:
                        self._generations[attempt_id] = attempt[name]
                        break
        return super().launch(attempt, job)
'''


def swap(body, old, new, what):
    if old not in body:
        raise SystemExit(f"REFUSED: {what} is not in the file as written")
    return body.replace(old, new, 1)


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")
    body = swap(body, OLD, NEW, "the gate's readers")
    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ('__slots__ = ("_job_ids", "_generations", "_stage_of")',
                    "def launch(self, attempt, job):",
                    "self._generations[attempt_id] = attempt[name]"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    if 'getattr(self, "_generations"' in written:
        raise SystemExit("REFUSED: the defaulted reader survives")
    print("launch provenance recorded, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
