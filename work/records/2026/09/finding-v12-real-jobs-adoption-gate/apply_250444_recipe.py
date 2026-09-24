"""Claim-250444: the recipe's printed operands, checked against the commands.

Review 2026-09-23T19:22:24Z: "ADOPTION step4 opens `<run root>/jobs.sqlite3`
and `<run root>/control.sqlite3`, while step6 watches
`<run root>/db/jobs.sqlite3` and `<run root>/db/control.sqlite3`. Correct the
recipe to inspect the stores actually opened. The internal status test cannot
catch this discrepancy because it reads the live objects directly. Verify the
printed inspect operands as part of the recipe check."

Both stores are corrected. This adds the check that would have caught it: the
page's own text, parsed, with the store paths held equal across the steps and
every printed flag held against the command's own `--help`. An operator reads
the page, not the objects, so the page is what has to agree.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "test_two_jobs.py"

ANCHOR = "def baseline_interrupted():"

ADDED = '''class TheOPERATORRecipePrintsOperandsThatAGREE(unittest.TestCase):
    """The page an operator types from, read as an operator would.

    Review 2026-09-23T19:22:24Z found step 6 inspecting `<run root>/db/...`
    while step 4 opened `<run root>/...`. Nothing here could catch it: every
    other check reaches the live objects, and the objects were right. What was
    wrong was the text, so this reads the text.
    """

    PAGE = os.path.join(HERE, "ADOPTION-247941.md")

    def page(self):
        with open(self.PAGE, encoding="utf-8") as handle:
            return handle.read()

    def operands(self, page, flag):
        """Every value the page gives to one long flag."""
        import re
        return re.findall(rf'{re.escape(flag)}\\s+"([^"]+)"', page)

    def test_the_inspect_step_names_the_stores_the_run_step_OPENS(self):
        """One store per axis across the whole page, or this fails."""
        page = self.page()
        jobs = set(self.operands(page, "--job-store")
                   + self.operands(page, "--store"))
        control = set(self.operands(page, "--control-store")
                      + self.operands(page, "--control"))
        self.assertEqual(jobs, {"<run root>/jobs.sqlite3"})
        self.assertEqual(control, {"<run root>/control.sqlite3"})
        # AND THE EXACT SHAPE THAT WAS WRONG, named so a reintroduction is a
        # failure with the reviewer's own words on it.
        self.assertNotIn("/db/jobs.sqlite3", page)
        self.assertNotIn("/db/control.sqlite3", page)

    def test_every_flag_the_run_step_prints_is_one_the_COMMAND_accepts(self):
        """Against the command's own `--help`, not against a list here.

        A second list of flags kept in a test is a second thing to drift.
        This asks the program.
        """
        import re
        import subprocess
        answer = subprocess.run(
            [sys.executable, "-B",
             os.path.join(HERE, "two_job_supervisor.py"), "--help"],
            capture_output=True, text=True, timeout=120, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=os.pathsep.join([SNAPSHOT, HERE])))
        self.assertEqual(answer.returncode, 0, answer.stderr)
        page = self.page()
        start = page.index("## Step 4 — serve the bounded run")
        block = page[start:page.index("```", page.index("```sh", start) + 5)]
        printed = sorted(set(re.findall(r"(--[a-z][a-z-]+)", block)))
        self.assertIn("--job-store", printed)
        for flag in printed:
            with self.subTest(flag=flag):
                self.assertIn(flag, answer.stdout)

    def test_every_flag_the_inspect_step_prints_is_one_the_TOOL_accepts(self):
        """The same question of `tools.job_manager status`.

        This is the step whose operands were wrong, and asking the tool is how
        the next wrong one gets caught.
        """
        import re
        import subprocess
        answer = subprocess.run(
            [sys.executable, "-B", "-m", "tools.job_manager", "--store", "x",
             "--incarnation", "x", "--authority-uuid", "0" * 32,
             "status", "--help"],
            capture_output=True, text=True, timeout=120, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=SNAPSHOT))
        self.assertEqual(answer.returncode, 0, answer.stderr)
        page = self.page()
        start = page.index("## Step 6 — watch, read-only")
        block = page[start:page.index("```", page.index("```sh", start) + 5)]
        printed = sorted(set(re.findall(r"(--[a-z][a-z-]+)", block)))
        self.assertIn("--control", printed)
        # `--store`, `--incarnation` and `--authority-uuid` are the TOOL's
        # operands rather than the subcommand's, so they are held against the
        # tool's own help instead.
        outer = subprocess.run(
            [sys.executable, "-B", "-m", "tools.job_manager", "--help"],
            capture_output=True, text=True, timeout=120, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=SNAPSHOT))
        self.assertEqual(outer.returncode, 0, outer.stderr)
        for flag in printed:
            with self.subTest(flag=flag):
                self.assertTrue(flag in answer.stdout or flag in outer.stdout,
                                f"{flag} is in neither help text")


'''

IMPORT_OLD = '''from tests.tools.test_stage_execution import (                # noqa: E402
    SECOND_WORK, TwoBoundJobsTraverseServingAndCorrection)'''

IMPORT_NEW = '''# THE PINNED SNAPSHOT, for the subprocess checks that ask a command what
# operands it accepts. They must ask the selected product, not the checkout.
SNAPSHOT = "/home/sl/baton-runs/independent-review-247947/manager-source"

from tests.tools.test_stage_execution import (                # noqa: E402
    SECOND_WORK, TwoBoundJobsTraverseServingAndCorrection)'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "TheOPERATORRecipePrintsOperandsThatAGREE" in body:
        raise SystemExit("REFUSED: the recipe checks are already present")
    body = swap(body, IMPORT_OLD, IMPORT_NEW, "the import block")
    body = swap(body, ANCHOR, ADDED + ANCHOR, "the module-function anchor")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for present in ("TheOPERATORRecipePrintsOperandsThatAGREE",
                    "test_the_inspect_step_names_the_stores_the_run_step_OPENS",
                    "test_every_flag_the_run_step_prints_is_one_the_COMMAND",
                    "test_every_flag_the_inspect_step_prints_is_one_the_TOOL"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("recipe operand checks added, parsed and verified on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
