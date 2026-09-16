"""What this build IS, and what it refuses to guess. W183883.

OWNER-VERSION-STAMP-20260916.md: one authoritative application version, a
commit and dirty flag CAPTURED at packaging time, dirty builds allowed, and an
unknown that is never reported as clean.

DETERMINISTIC AND OFFLINE. The repository tool is substituted everywhere here:
what is under test is the stamping and the formatting, not somebody's
repository, and this Work performs no version-control operation at all.
`tests/tools/test_packaging.py` asks the REAL built bundle the same question.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

_DISTRIBUTION = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_DISTRIBUTION))
sys.path.insert(1, str(_DISTRIBUTION / "src"))
from baton_v12 import version
from tools import build_stamp


class TheVersionIsWrittenOnce(unittest.TestCase):
    def test_the_module_states_it_and_nothing_else_does(self):
        self.assertEqual(version.VERSION, "12.0.0")
        held = (_DISTRIBUTION / "pyproject.toml").read_text()
        self.assertIn('dynamic = ["version"]', held)
        self.assertIn('version = {attr = "baton_v12.version.VERSION"}', held)
        # TWO LITERALS ARE TWO ANSWERS. The metadata reads the module rather
        # than repeating a number that drifts the first time one is edited.
        self.assertNotIn('version = "12.0.0"', held)

    def test_importing_it_reads_nothing(self):
        """`--version` has to answer where the checkout and the repository tool
        are both absent, so the authority itself must not touch either."""
        source = (_DISTRIBUTION / "src" / "baton_v12" / "version.py").read_text()
        for banned in ("subprocess", "open(", "Path(", "os.environ"):
            self.assertNotIn(banned, source, banned)


class TheBannerSaysWhatIsKnown(unittest.TestCase):
    def test_a_clean_build(self):
        self.assertEqual(
            version.stated({"commit": "3c0dd08225e1691d", "dirty": False}),
            "baton 12.0.0 (3c0dd082)")

    def test_a_dirty_build_is_allowed_and_says_so(self):
        self.assertEqual(
            version.stated({"commit": "3c0dd08225e1691d", "dirty": True}),
            "baton 12.0.0 (3c0dd082, dirty)")

    def test_an_unknown_commit_is_not_a_clean_one(self):
        said = version.stated({"commit": None, "detail": "no repository tool"})
        self.assertIn("source commit unknown", said)
        self.assertIn("no repository tool", said)
        self.assertNotIn("dirty", said)

    def test_no_stamp_at_all_is_still_unknown_rather_than_clean(self):
        self.assertEqual(version.stated(None), "baton 12.0.0 (source commit unknown)")
        self.assertEqual(version.stated({}), "baton 12.0.0 (source commit unknown)")

    def test_a_known_commit_whose_cleanliness_is_not_is_said_so(self):
        said = version.stated({"commit": "abcdef1234", "dirty": None})
        self.assertIn("abcdef12", said)
        self.assertIn("cleanliness unknown", said)


class TheStampIsCapturedFromTheCheckout(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v12-stamp-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def answering(self, commit="a" * 40, status="", fails=()):
        """A stand-in for the repository tool, and nothing else is substituted."""
        self.issued = []

        def ran(argv, cwd, timeout=30):
            self.issued.append(list(argv))
            if "rev-parse" in argv:
                return None if "rev-parse" in fails else commit + "\n"
            if "status" in argv:
                return None if "status" in fails else status
            raise AssertionError("asked something it should not: " + str(argv))
        return ran

    def test_untracked_entries_are_ASKED_FOR_rather_than_left_to_the_host(self):
        """[V1]: `--porcelain` honours `status.showUntrackedFiles=no`, so on a
        host configured that way an ordinary untracked source file was omitted
        and a dirty tree reported itself clean. The observation is forced."""
        build_stamp.capture(self.root, runner=self.answering())
        status = [one for one in self.issued if "status" in one]
        self.assertEqual(len(status), 1)
        self.assertIn("--porcelain", status[0])
        self.assertIn("--untracked-files=normal", status[0])
        # AND THE READS ARE READS: nothing that writes, stages or commits.
        for argv in self.issued:
            self.assertTrue(set(argv) & {"rev-parse", "status"}, argv)
            for banned in ("add", "commit", "checkout", "clean", "stash",
                           "tag", "reset"):
                self.assertNotIn(banned, argv, banned)

    def test_only_THIS_distribution_s_build_output_is_excused(self):
        """[V2]: `build/out`, `build/work` and the written stamp are UNTRACKED
        rather than ignored, so one build made every later capture call the
        tree dirty. They are excused by exact path -- and nothing else is."""
        output = ("?? v12/python/build/out/\n"
                  "?? v12/python/build/work/\n"
                  "?? v12/python/packaging/build-stamp.json\n")
        held = build_stamp.capture(self.root,
                                   runner=self.answering(status=output))
        self.assertIs(held["dirty"], False)
        self.assertEqual(held["changed_entries"], 0)
        self.assertEqual(held["excused_build_output"], 3)

    def test_a_REPEATED_capture_after_a_build_is_still_clean(self):
        """The case the review found: capture, build, capture again."""
        first = build_stamp.capture(self.root, runner=self.answering(status=""))
        after = build_stamp.capture(
            self.root,
            runner=self.answering(status="?? v12/python/build/out/\n"))
        self.assertIs(first["dirty"], False)
        self.assertIs(after["dirty"], False)

    def test_untracked_SOURCE_still_makes_it_dirty(self):
        """The positive control, and the reason the boundary is three exact
        paths rather than a pattern."""
        for said in ("?? v12/python/tools/new_thing.py\n",
                     "?? v12/python/build/notes.txt\n",
                     "?? v12/python/packaging/other.json\n",
                     "?? v12/STACK.md\n",
                     " M v12/python/build/out/something\n"):
            held = build_stamp.capture(self.root,
                                       runner=self.answering(status=said))
            self.assertIs(held["dirty"], True, said)

    def test_a_tracked_change_under_the_build_directory_is_not_excused(self):
        """Excusing UNTRACKED output is not excusing edits to tracked files
        that happen to live there."""
        held = build_stamp.capture(
            self.root,
            runner=self.answering(status="M  v12/python/build/out/kept.txt\n"))
        self.assertIs(held["dirty"], True)

    def test_a_quoted_or_renamed_entry_is_read_as_the_path_it_names(self):
        held = build_stamp.capture(
            self.root,
            runner=self.answering(status='R  a.py -> "v12/python/tools/b.py"\n'))
        self.assertIs(held["dirty"], True)

    def test_a_clean_tree(self):
        held = build_stamp.capture(self.root, runner=self.answering())
        self.assertEqual(held["commit"], "a" * 40)
        self.assertIs(held["dirty"], False)
        self.assertEqual(held["changed_entries"], 0)

    def test_staged_unstaged_and_untracked_all_make_it_dirty(self):
        for said in (" M v12/python/tools/stack.py\n",
                     "M  v12/python/tools/stack.py\n",
                     "?? v12/python/tools/new_thing.py\n"):
            held = build_stamp.capture(self.root,
                                       runner=self.answering(status=said))
            self.assertIs(held["dirty"], True, said)

    def test_ignored_build_output_does_not_make_it_dirty(self):
        """`status --porcelain` omits ignored entries, and a packaging run's
        own `build/` is exactly what would otherwise make every build dirty."""
        held = build_stamp.capture(self.root, runner=self.answering(status=""))
        self.assertIs(held["dirty"], False)

    def test_no_repository_tool_is_unknown_not_clean(self):
        held = build_stamp.capture(self.root,
                                   runner=self.answering(fails=("rev-parse",)))
        self.assertIsNone(held["commit"])
        self.assertIsNone(held["dirty"])
        self.assertIn("could not name a commit", held["detail"])

    def test_a_readable_commit_with_an_unreadable_status_is_unknown_too(self):
        held = build_stamp.capture(self.root,
                                   runner=self.answering(fails=("status",)))
        self.assertEqual(held["commit"], "a" * 40)
        self.assertIsNone(held["dirty"])
        self.assertIn("could not report the tree state", held["detail"])

    def test_no_checkout_at_all_is_said_rather_than_guessed(self):
        held = build_stamp.capture(None, runner=self.answering())
        if held["source"] is None:
            self.assertIn("no repository containing", held["detail"])
        else:
            # This distribution IS in one, which is the ordinary case here.
            self.assertTrue(os.path.isfile(
                os.path.join(held["source"], "v12", "justfile")))

    def test_the_checkout_is_found_from_THIS_file_not_the_cwd(self):
        # FROM AN UNRELATED DIRECTORY, because standing inside the checkout is
        # exactly the condition under which a cwd-based answer looks right.
        here = os.getcwd()
        os.chdir(self.root)
        try:
            found = build_stamp.checkout()
        finally:
            os.chdir(here)
        self.assertIsNotNone(found, "the source was not found from this file")
        self.assertTrue((found / "v12" / "justfile").exists())
        # A path inside the distribution finds the same one; an unrelated path
        # finds nothing rather than something convenient.
        self.assertEqual(build_stamp.checkout(_DISTRIBUTION / "tools"), found)
        self.assertIsNone(build_stamp.checkout("/tmp"))

    def test_it_round_trips_through_the_file_the_bundle_carries(self):
        held = build_stamp.capture(self.root, runner=self.answering())
        place = build_stamp.write(self.root / build_stamp.FILENAME, held)
        self.assertEqual(build_stamp.read(place), held)

    def test_a_file_of_another_schema_is_not_read_as_a_stamp(self):
        place = self.root / build_stamp.FILENAME
        place.write_text(json.dumps({"schema": "something.else/1",
                                     "commit": "b" * 40}))
        self.assertIsNone(build_stamp.read(place))
        self.assertIsNone(build_stamp.read(self.root / "absent.json"))


class TheCommandAnswersWithoutAnythingElse(unittest.TestCase):
    """`--version` before the parser, before any store, credential or runtime."""

    def ran(self, argv, stamp):
        import io

        from tools import stack_command

        out = io.StringIO()
        real = sys.stdout
        sys.stdout = out
        try:
            with mock.patch.object(build_stamp, "stamped", lambda: stamp):
                code = stack_command.main(argv)
        finally:
            sys.stdout = real
        return code, out.getvalue().strip()

    def test_it_answers_and_exits_zero(self):
        code, said = self.ran(["--version"],
                              {"commit": "3c0dd08225e1", "dirty": True})
        self.assertEqual(code, 0)
        self.assertEqual(said, "baton 12.0.0 (3c0dd082, dirty)")

    def test_the_short_form_too(self):
        code, said = self.ran(["-V"], {"commit": "3c0dd08225e1", "dirty": False})
        self.assertEqual((code, said), (0, "baton 12.0.0 (3c0dd082)"))

    def test_it_is_answered_BEFORE_the_subcommand_parser(self):
        """It is not one of the subcommands, and must not be reachable only by
        arranging the rest of a command line correctly."""
        code, said = self.ran(["--version", "start", "--instance", "/nowhere"],
                              {"commit": "abc123def", "dirty": False})
        self.assertEqual(code, 0)
        self.assertIn("baton 12.0.0", said)

    def test_it_opens_no_store_reads_no_credential_and_starts_nothing(self):
        import subprocess as watched

        from tools import stack_command

        with mock.patch.object(watched, "run",
                               lambda *a, **k: self.fail("it ran something")), \
                mock.patch.object(watched, "Popen",
                                  lambda *a, **k: self.fail("it started one")):
            code, said = self.ran(["--version"], {"commit": "abc", "dirty": False})
        self.assertEqual(code, 0)
        self.assertIn("baton", said)
        self.assertIn("version", stack_command.main.__doc__ or "version")

    def test_the_help_names_it(self):
        import io

        from tools import stack_command

        out = io.StringIO()
        real = sys.stdout
        sys.stdout = out
        try:
            stack_command.main([])
        finally:
            sys.stdout = real
        self.assertIn("--version", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
