"""The connected deterministic checks for the SELECTED useful-task path. W247941 claim 305675.

Review 2026-09-29T12-34-10Z asked for tests on that path specifically, beside the 85 that guard the
greeting fixture. These drive the real builder, the real delivery and the real checker -- no store, no
engine, no provider, no Git -- and each one holds a property the packet claims.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:                                # pragma: no cover
    sys.path.insert(0, str(HERE))

import check_useful_tasks                                    # noqa: E402
import useful_tasks                                          # noqa: E402


class TheSelectedTasksAreOneContract(unittest.TestCase):
    """The builder and the checker read ONE table, so they cannot drift."""

    def test_the_builder_and_the_checker_share_the_table(self):
        self.assertIs(useful_tasks.TASKS, check_useful_tasks.TASKS)

    def test_the_two_paths_are_disjoint_and_documented(self):
        paths = {job_id: held["path"] for job_id, held in useful_tasks.TASKS.items()}
        self.assertEqual(len(set(paths.values())), 2, paths)
        contract = (HERE / useful_tasks.CONTRACT).read_text(encoding="utf-8")
        for job_id, path in paths.items():
            self.assertIn(path, contract, f"{job_id}'s path is not in the contract")

    def test_every_required_heading_reaches_the_brief(self):
        for job_id, held in useful_tasks.TASKS.items():
            brief = useful_tasks.task_document(
                job_id, run_id="probe", base="0" * 40)["instructions"]
            for heading in held["headings"]:
                self.assertIn(heading, brief, f"{job_id} omits {heading!r}")
            self.assertIn(f"UNDER {held['line_bound_exclusive']} lines", brief)

    def test_the_document_is_the_shape_the_preparation_binds(self):
        import prepare_two_jobs

        mine = useful_tasks.task_document("job-a", run_id="probe", base="0" * 40)
        theirs = prepare_two_jobs.task_document("job-a", run_id="probe", base="0" * 40)
        self.assertEqual(sorted(mine), sorted(theirs))
        self.assertEqual(mine["schema"], theirs["schema"])

    def test_the_brief_and_the_verification_name_paths_INSIDE_the_checkout(self):
        """W247941 owner ruling 2026-09-29 and review 13:08:19Z, measured.

        The previous brief pointed at `/input/excerpts/` and the verification at
        `/input/checker/check_useful_tasks.py` -- a mount this packet never arranged, so the frozen
        context reached no worker and the emitted verification could not have started. Both now name
        repo-relative paths in the Job's own checkout, which is the ACCEPTED single-Job mechanism.
        """
        for job_id in sorted(useful_tasks.TASKS):
            brief = useful_tasks.task_document(
                job_id, run_id="probe", base="0" * 40)["instructions"]
            self.assertNotIn("/input/", brief)
            self.assertIn(useful_tasks.SOURCE_INPUTS, brief)
            for name in useful_tasks.EXCERPTS:
                self.assertIn(useful_tasks.relative(name, "excerpts"), brief)
            self.assertIn(useful_tasks.relative(useful_tasks.CONTRACT, "contract"), brief)
            argv = useful_tasks.verification(job_id)
            self.assertNotIn("/input/checker/check_useful_tasks.py", argv)
            self.assertIn(useful_tasks.relative("check_useful_tasks.py", "checker"), argv)

    def test_the_verification_names_this_jobs_own_path_only(self):
        for job_id, held in useful_tasks.TASKS.items():
            argv = useful_tasks.verification(job_id)
            self.assertEqual(argv[-1], held["path"])
            self.assertIn(job_id, argv)
            other = [one["path"] for name, one in useful_tasks.TASKS.items()
                     if name != job_id]
            for path in other:
                self.assertNotIn(path, argv)


class TheEXCERPTSAreDeliveredAndPROVED(unittest.TestCase):
    """Delivery is not pinning: the COPY a Job reads is what gets hashed."""

    def test_every_excerpt_lands_with_its_pinned_digest(self):
        with tempfile.TemporaryDirectory() as root:
            delivered = useful_tasks.deliver(root)
            for name, held in useful_tasks.EXCERPTS.items():
                self.assertIn(name, delivered)
                self.assertEqual(delivered[name]["sha256"], held["sha256"])
                place = pathlib.Path(delivered[name]["place"])
                self.assertTrue(place.is_file())
                self.assertEqual(place.read_bytes(),
                                 (useful_tasks.CHECKOUT / held["source"]).read_bytes())

    def test_the_checker_is_delivered_beside_them(self):
        with tempfile.TemporaryDirectory() as root:
            delivered = useful_tasks.deliver(root)
            place = pathlib.Path(delivered["check_useful_tasks.py"]["place"])
            self.assertTrue(place.is_file())
            self.assertEqual(place.read_bytes(),
                             (HERE / "check_useful_tasks.py").read_bytes())

    def test_the_CONTRACT_travels_too(self):
        """W247941 review 2026-09-29T12-42-29Z: the contract was NAMED in the brief and never
        delivered, so a reviewer asked to judge against it had no copy of it."""
        with tempfile.TemporaryDirectory() as root:
            delivered = useful_tasks.deliver(root)
            for name, _into in useful_tasks.CARRIED:
                self.assertIn(name, delivered, f"{name} was not delivered")
                place = pathlib.Path(delivered[name]["place"])
                self.assertEqual(place.read_bytes(), (HERE / name).read_bytes())

    def test_an_EXISTING_target_with_other_bytes_refuses_before_writing(self):
        """The gate ORDER is the property: a refusal leaves no partial delivery behind."""
        with tempfile.TemporaryDirectory() as root:
            first = useful_tasks.deliver(root)
            pathlib.Path(first["check_useful_tasks.py"]["place"]).write_bytes(b"tampered\n")
            # THE WHOLE RELEVANT TREE, not one directory. W247941 review 2026-09-29T12-57-17Z:
            # comparing only `excerpts/` would miss a refusal that touched the contract or the
            # checker, which are the other two things a Job reads.
            tree = pathlib.Path(root) / useful_tasks.SOURCE_INPUTS

            def walked():
                return {str(one.relative_to(tree)): one.read_bytes()
                        for one in sorted(tree.rglob("*")) if one.is_file()}

            before = walked()
            with self.assertRaises(ValueError) as caught:
                useful_tasks.deliver(root)
            self.assertIn("does not overwrite a mounted input", str(caught.exception))
            self.assertEqual(before, walked(), "the refusal changed the delivery")

    def test_an_EXACT_repeat_is_a_replay_rather_than_a_refusal(self):
        with tempfile.TemporaryDirectory() as root:
            first = useful_tasks.deliver(root)
            again = useful_tasks.deliver(root)
            self.assertEqual({name: one["sha256"] for name, one in first.items()},
                             {name: one["sha256"] for name, one in again.items()})

    def test_a_MOVED_excerpt_is_refused_rather_than_delivered(self):
        """The pin is the point: a source whose bytes changed stops the delivery."""
        with tempfile.TemporaryDirectory() as fake:
            root = pathlib.Path(fake) / "checkout"
            for held in useful_tasks.EXCERPTS.values():
                place = root / held["source"]
                place.parent.mkdir(parents=True, exist_ok=True)
                place.write_bytes(b"these are not the frozen bytes\n")
            with tempfile.TemporaryDirectory() as into:
                with self.assertRaises(ValueError) as caught:
                    useful_tasks.deliver(into, checkout=root)
                self.assertIn("the frozen input moved", str(caught.exception))

    def test_an_ABSENT_excerpt_is_refused_by_name(self):
        with tempfile.TemporaryDirectory() as fake:
            with tempfile.TemporaryDirectory() as into:
                with self.assertRaises(FileNotFoundError) as caught:
                    useful_tasks.deliver(into, checkout=fake)
                self.assertIn("is absent", str(caught.exception))


class ThePREPARATIONPROVESTheSourceCarriesThemWithoutWriting(unittest.TestCase):
    """`present` is the preparation's gate, and it is a gate BECAUSE it writes nothing.

    W247941 owner ruling 2026-09-29: the writes-before-refusal defect was structural -- a copy step
    inside a function that can still refuse. A read cannot have that defect, so these hold that
    `present` reads, refuses by name, and leaves the tree exactly as it found it.
    """

    def seeded(self, root):
        return useful_tasks.deliver(root)

    def test_a_SEEDED_source_is_proved_member_by_member(self):
        with tempfile.TemporaryDirectory() as root:
            seeded = self.seeded(root)
            proven = useful_tasks.present(root)
            self.assertEqual(sorted(proven), sorted(seeded))
            for name, held in proven.items():
                self.assertEqual(held["sha256"], seeded[name]["sha256"])
                self.assertEqual(held["relative"], seeded[name]["relative"])
                self.assertTrue(held["relative"].startswith(useful_tasks.SOURCE_INPUTS + "/"))

    def test_an_UNSEEDED_source_is_refused_by_the_path_it_lacks(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(FileNotFoundError) as caught:
                useful_tasks.present(root)
            self.assertIn("does not carry", str(caught.exception))
            self.assertIn(useful_tasks.SOURCE_INPUTS, str(caught.exception))

    def test_a_TAMPERED_member_is_refused_and_NOTHING_is_written(self):
        with tempfile.TemporaryDirectory() as root:
            seeded = self.seeded(root)
            tampered = pathlib.Path(seeded["check_useful_tasks.py"]["place"])
            tampered.write_bytes(b"not the checker\n")
            tree = pathlib.Path(root)

            def walked():
                return {str(one.relative_to(tree)): one.read_bytes()
                        for one in sorted(tree.rglob("*")) if one.is_file()}

            before = walked()
            with self.assertRaises(ValueError) as caught:
                useful_tasks.present(root)
            self.assertIn("the Jobs would read bytes no digest here names",
                          str(caught.exception))
            self.assertEqual(before, walked(), "a proof wrote to the tree")


class TheDELIVEREDCheckerDecidesTheStructure(unittest.TestCase):
    """The checker a Job actually runs is the delivered copy, driven as the task names it."""

    def _candidate(self, root, job_id, lines=None):
        held = useful_tasks.TASKS[job_id]
        place = pathlib.Path(root) / held["path"]
        place.parent.mkdir(parents=True, exist_ok=True)
        body = list(held["headings"]) + list(lines or ["body"])
        place.write_text("\n".join(body) + "\n", encoding="utf-8")
        return held["path"]

    def _run(self, checker, job_id, root, changed):
        argv = [sys.executable, "-B", str(checker), "--job", job_id,
                "--root", str(root)]
        for one in changed:
            argv += ["--changed", one]
        return subprocess.run(argv, capture_output=True, text=True, timeout=120)

    def test_both_jobs_pass_through_the_delivered_copy(self):
        with tempfile.TemporaryDirectory() as run_root:
            delivered = useful_tasks.deliver(run_root)
            checker = delivered["check_useful_tasks.py"]["place"]
            with tempfile.TemporaryDirectory() as candidate:
                for job_id in sorted(useful_tasks.TASKS):
                    path = self._candidate(candidate, job_id)
                    answer = self._run(checker, job_id, candidate, [path])
                    self.assertEqual(answer.returncode, 0, answer.stdout + answer.stderr)
                    held = json.loads(answer.stdout)
                    self.assertEqual(held["structural"], "pass")
                    self.assertEqual(held["path"], path)

    def test_the_other_jobs_file_in_the_changed_set_is_refused(self):
        with tempfile.TemporaryDirectory() as run_root:
            checker = useful_tasks.deliver(run_root)["check_useful_tasks.py"]["place"]
            with tempfile.TemporaryDirectory() as candidate:
                mine = self._candidate(candidate, "job-a")
                theirs = useful_tasks.TASKS["job-b"]["path"]
                answer = self._run(checker, "job-a", candidate, [mine, theirs])
                self.assertEqual(answer.returncode, 1)
                self.assertIn("may change exactly", answer.stdout)

    def test_the_line_bound_is_exclusive_through_the_delivered_copy(self):
        with tempfile.TemporaryDirectory() as run_root:
            checker = useful_tasks.deliver(run_root)["check_useful_tasks.py"]["place"]
            held = useful_tasks.TASKS["job-a"]
            bound = held["line_bound_exclusive"]
            filler = ["body"] * (bound - 1 - len(held["headings"]))
            with tempfile.TemporaryDirectory() as candidate:
                path = self._candidate(candidate, "job-a", lines=filler)
                self.assertEqual(
                    self._run(checker, "job-a", candidate, [path]).returncode, 0)
            with tempfile.TemporaryDirectory() as candidate:
                path = self._candidate(candidate, "job-a", lines=filler + ["one more"])
                answer = self._run(checker, "job-a", candidate, [path])
                self.assertEqual(answer.returncode, 1)
                self.assertIn(f"UNDER {bound}", answer.stdout)


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main(verbosity=2)

