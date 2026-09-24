"""Claim-249799: success from RESULTS, a final cleanup read, and the seams."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

OLD_SUCCESS = '''    held_because = []
    # A RUN THAT ADMITTED NOTHING HAS NOT SUCCEEDED. Review
    # 2026-09-23T17:44:56Z: an empty serve published `settled` with zero
    # admissions and no verdicts, because "settled" was defined as "nothing to
    # complain about". Success is what the run PRODUCED: four admissions, and
    # a positive cleanup for every runtime it started.
    expected = sum(dict(gate._caps).values())                 # noqa: SLF001
    if sum(measured["admissions"].values()) != expected:
        held_because.append(
            f"this run admitted {sum(measured['admissions'].values())} of the "
            f"{expected} stages it is configured for: "
            f"{measured['admissions']}. A run that admitted less than its "
            f"workload did not serve it")
    if not measured["admitted_attempts"]:
        held_because.append(
            "no runtime was ever launched, so there is nothing this run can "
            "claim to have stopped or cleaned up")
'''

NEW_SUCCESS = '''    # THE FINAL CLEANUP READ, after the last sweep rather than before it.
    # Review 2026-09-23T18:00:25Z. A cleanup that settled on the last sweep
    # would otherwise be reported as outstanding by a read taken before it.
    settled = baseline._guarded(
        lambda: baseline._cleanups(
            control, {"deployment": {"config_path": deployment_path}},
            dict(gate.launched)),
        settled, what="the final cleanup journal read",
        uncertainty=uncertainty, interrupted=caught)
    measured["cleanup"] = {} if settled is None else settled.get("cleanup", {})
    measured["outstanding_cleanup"] = (
        sorted(gate.launched) if settled is None
        else sorted(settled.get("outstanding", ())))

    # AND THE VERDICTS, DERIVED FROM EACH JOB'S OWN FROZEN RESULT. Review
    # 2026-09-23T18:00:25Z: "success must require results not admission
    # counts". An admission is a run starting something; a verdict is the
    # thing a review Job exists to produce.
    measured["verdicts"] = verdicts_of(control, gate, uncertainty, caught)

    held_because = []
    for one in gate.job_ids:
        if one not in measured["verdicts"]:
            held_because.append(
                f"Job {one} produced no attributed verdict; a two-Job review "
                f"run that collected fewer than two has not done its work")
    if not measured["admitted_attempts"]:
        held_because.append(
            "no runtime was ever launched, so there is nothing this run can "
            "claim to have stopped or cleaned up")
'''

VERDICTS = '''

def verdicts_of(control, gate, uncertainty, caught):
    """Each bound Job's verdict, DERIVED from its own frozen result.

    `review_verdict_from_result` is the manager's own deriver: it refuses
    unless the frozen result belongs to that attachment's attempt, its
    retained manifest names the same result and the same assignment at the
    same generation, and the base, head and tree the reviewer reports are the
    ones the checkpoint's evidence records. Nothing here reads a disposition
    off a status row.

    A read that does not complete is UNCERTAINTY, not an absent verdict: this
    answers what it could derive and the caller holds the run for the rest.
    """
    from baton_v12.job_manager import review_driver
    from baton_v12.worker_manager import review_cycles

    held = {}
    for attempt_id, kind in sorted(gate.launched.items()):
        if kind != "review":
            continue
        attachment = baseline._guarded(
            lambda one=attempt_id: review_cycles.review_for_attempt(
                control, attempt_id=one,
                generation=gate.generations.get(one)),
            None, what=f"the review attachment for {attempt_id}",
            uncertainty=uncertainty, interrupted=caught)
        if not attachment:
            continue
        verdict = baseline._guarded(
            lambda one=attachment: review_driver.review_verdict_from_result(
                control, attachment_id=one["attachment_id"]),
            None, what=f"the verdict derived for {attempt_id}",
            uncertainty=uncertainty, interrupted=caught)
        if verdict:
            held[gate.stage_jobs.get(
                attachment.get("stage_id"), gate.job_of(attempt_id))] = verdict
    return held
'''


def swap(body, old, new, what):
    if old not in body:
        raise SystemExit(f"REFUSED: {what} is not in the file as written")
    return body.replace(old, new, 1)


def main():
    place = HERE / "two_job_supervisor.py"
    body = place.read_text(encoding="utf-8")
    body = swap(body, OLD_SUCCESS, NEW_SUCCESS, "the success predicate")
    body = swap(body, "\ndef supervise(job, control, operations, *,",
                VERDICTS + "\ndef supervise(job, control, operations, *,",
                "the supervise definition")
    # the gate must be able to say which Job an attempt belongs to
    body = swap(
        body,
        '''    @property
    def job_ids(self):
        return self._job_ids''',
        '''    @property
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
        return getattr(self, "_stage_of", {})''',
        "the gate's readers")
    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    for present in ("def verdicts_of(", 'measured["verdicts"]',
                    "the final cleanup journal read", "def job_of("):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("result-based success and the final cleanup read added, verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
