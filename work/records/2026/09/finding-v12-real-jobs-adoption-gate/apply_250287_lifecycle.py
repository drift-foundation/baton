"""Claim-250287: two corrections to what I just added, from running it.

  * `pathlib` was used by the structural check and never imported.
  * The lifecycle case asserted `stopped == "interrupted"`, and that is not
    what the accepted machinery does with an interruption arriving INSIDE a
    turn. `baseline._guarded` catches `BaseException` deliberately -- "an
    interruption arriving inside a read is recorded so `supervise` can
    re-raise it once the outcome is on disk" -- so the run finishes its
    shutdown, records the interruption, publishes, and raises. `stopped`
    names how SERVING ended, which is still the bound. I asserted the shape I
    expected rather than the shape the accepted machinery documents; the case
    now asserts the guarantee that actually matters, which is that the
    outcome is on disk and the interruption is neither lost nor swallowed.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "test_two_jobs.py"

OLD_ASSERT = '''        self.assertEqual(published["stopped"], "interrupted")
        self.assertEqual(published["state"], "held")
        self.assertTrue(published["interruptions"])
'''

NEW_ASSERT = '''        # `stopped` NAMES HOW SERVING ENDED, and serving ended at its bound.
        # `baseline._guarded` catches `BaseException` on purpose so that an
        # interruption arriving inside a turn is RECORDED rather than allowed
        # to abandon the shutdown -- cancellation, cleanup and publication
        # still run, and `supervise` re-raises once the document is on disk.
        # That is the protection being asserted here, so this asserts the
        # record rather than the loop's exit reason.
        self.assertEqual(published["state"], "held")
        self.assertTrue(any("KeyboardInterrupt" in one
                            for one in published["interruptions"]),
                        published["interruptions"])
        self.assertTrue(any("KeyboardInterrupt" in one
                            for one in published["held_because"]),
                        published["held_because"])
        # AND THE SHUTDOWN STILL RAN TO THE END rather than being abandoned.
        self.assertIs(published["admission_closed_before_cancellation"], True)
        self.assertIn("cleanup_sweeps", published)
        self.assertEqual(published["verdicts"], {})
'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    body = swap(body, OLD_ASSERT, NEW_ASSERT, "the lifecycle assertions")
    if "\nimport pathlib\n" not in body:
        body = swap(body, "\nimport os\n", "\nimport os\nimport pathlib\n",
                    "the import block")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    if 'published["stopped"], "interrupted"' in written:
        raise SystemExit("REFUSED: the wrong assertion survives in the file")
    for present in ("import pathlib", 'admission_closed_before_cancellation'):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("lifecycle assertions and the pathlib import corrected on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
