"""Claim-250444: the pool/assignment distinction, labelled rather than claimed.

Review 2026-09-23T19:22:24Z: "The main assignment test compares published
values to assignment_of, which validates the reader. It still does not force or
assert a DIFFERENCE between pool and assignment counters as previously
requested. Retain a focused differing-counter case or explicitly label that
claim unproved. Do not overstate it as completed merely because the correct
reader is used."

I am labelling it unproved, and doing it in a way that cannot quietly rot: a
case that READS BOTH AXES FROM THEIR OWN SOURCES and asserts they are equal
under this witness. That is the limitation stated as a check -- if a future
change ever makes them differ here, this fails and the page has to be corrected
rather than silently becoming true.

HOW IT WOULD BE FORCED, so the next claim has a path rather than a restated
gap: `scheduler.reserve` stamps every allocation with the CURRENT POOL
generation, while `attempts.assignment_of` reads the assignment generation the
Authority activated. Activating a second pool generation BEFORE the run's
allocations are made would put the allocations at pool generation 2 with their
assignments still at 1. That is a real forcing path and it is not written here;
writing it badly to close a review point would be worse than saying so.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "test_two_jobs.py"

ANCHOR = ("    def test_an_INTERRUPTION_through_the_command_publishes"
          "_and_still_raises(\n            self):")

ADDED = '''    def test_this_witness_does_NOT_separate_the_pool_and_assignment_axes(
            self):
        """The limitation, asserted so it cannot quietly stop being one.

        `scheduler.reserve` stamps each allocation with the CURRENT POOL
        generation; `attempts.assignment_of` reads the generation the
        Authority activated for that assignment. They are different axes and
        the run above reads the right one -- but this witness activates one
        pool and makes one assignment per stage, so BOTH read 1 and no
        difference between them is demonstrated here.

        Review 2026-09-23T19:22:24Z asked for a forced difference or an
        explicit label. This is the label, written as a check: if the two ever
        diverge in this witness, this case fails and the claim in
        ADOPTION-247941.md has to be corrected rather than silently becoming
        true. Forcing it would mean activating a second pool generation before
        the allocations are made; that is not written here.
        """
        from baton_v12.job_manager import JobStore, scheduler
        from baton_v12.worker_manager import ControlStore
        from baton_v12.worker_manager import attempts as attempt_rows
        _status, published, _captured, into = self.commanded()
        self.assertEqual(published["state"], "settled",
                         published["held_because"])
        jobs = JobStore.open_readonly(
            os.path.join(into, "jobs.sqlite3"),
            authority_uuid=self.config["authority_uuid"],
            incarnation="axis-readback",
            clock=lambda: "1970-01-01T00:00:00.000Z")
        control = ControlStore.open_readonly(
            os.path.join(into, "control.sqlite3"),
            incarnation="axis-readback",
            clock=lambda: "1970-01-01T00:00:00.000Z")
        try:
            pool = scheduler.active_generation(jobs)["generation"]
            assignments = {
                one: attempt_rows.assignment_of(control, one)["generation"]
                for one in published["admitted_attempts"]}
            allocations = {one["generation"]
                           for one in scheduler.allocation_rows(jobs)}
        finally:
            control.close()
            jobs.close()
        self.assertEqual(pool, 1)
        self.assertEqual(allocations, {1},
                         "an allocation was stamped with another pool "
                         "generation; the label below is now wrong")
        self.assertEqual(set(assignments.values()), {1})
        # THE STATEMENT ITSELF: equal, therefore indistinguishable HERE. A
        # reader that took this run as proof that the supervisor reads the
        # assignment axis would be reading a coincidence.
        self.assertEqual(allocations, set(assignments.values()))

'''

OLD_PAGE = '''the REAL assignment generation of every admitted
attempt, read back out of the control store the command left behind and
compared attempt by attempt — the ASSIGNMENT axis, not the pool's; positive'''

NEW_PAGE = '''the REAL assignment generation of every admitted
attempt, read back out of the control store the command left behind and
compared attempt by attempt through `attempts.assignment_of`; positive'''

OLD_LIMITS = '''1. **The worker turn is a seam, not a running container.**'''

NEW_LIMITS = '''1. **The two generation axes are not shown to DIFFER here.** The supervisor
   reads the assignment generation through `attempts.assignment_of` rather
   than the pool generation an allocation carries, and the witness asserts
   that reader attempt by attempt. But this run activates one pool and makes
   one assignment per stage, so both axes read 1 and nothing here separates
   them — a case asserts that equality so the limitation cannot quietly stop
   being one. Forcing a difference would mean activating a second pool
   generation before the allocations are made.
2. **The worker turn is a seam, not a running container.**'''

RENUMBER = (
    ("2. **No live two-Job run has occurred**", "3. **No live two-Job run has occurred**"),
    ("3. **Positive cleanup for two concurrent runtimes is continuity, not a",
     "4. **Positive cleanup for two concurrent runtimes is continuity, not a"),
    ("4. **The operand set is unresolved**", "5. **The operand set is unresolved**"),
)


def swap(place, body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times in {place}, "
            f"not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "does_NOT_separate_the_pool_and_assignment_axes" in body:
        raise SystemExit("REFUSED: the axis label is already present")
    body = swap("test_two_jobs.py", body, ANCHOR, ADDED + ANCHOR,
                "the interruption-case anchor")
    PLACE.write_text(body, encoding="utf-8")
    compile(PLACE.read_text(encoding="utf-8"), str(PLACE), "exec")

    page = HERE / "ADOPTION-247941.md"
    text = page.read_text(encoding="utf-8")
    text = swap(page.name, text, OLD_PAGE, NEW_PAGE, "the witnessed claim")
    text = swap(page.name, text, OLD_LIMITS, NEW_LIMITS, "the limitations head")
    for old, new in RENUMBER:
        text = swap(page.name, text, old, new, f"limitation {old[:2]}")
    page.write_text(text, encoding="utf-8")

    written = page.read_text(encoding="utf-8")
    if "the ASSIGNMENT axis, not the pool's" in written:
        raise SystemExit("REFUSED: the overstated claim survives in the page")
    if "not shown to DIFFER here" not in written:
        raise SystemExit("REFUSED: the label is not in the page")
    print("the axis distinction is labelled unproved, and checked as such")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
