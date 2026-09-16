"""Verify walk-180078.py against SYNTHETIC trees only.

The real 180078 tree is never touched: the operand root is passed explicitly to
the internal helpers, while the shipped `main` always uses the hard-coded ROOT
and accepts no arguments. Owner180411 forbids inspecting the private tree from
the managed context, and this context's identity is not the operator's anyway.
"""
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import tokenize
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("walk_180078", HERE / "walk-180078.py")
walk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(walk)

GROUP_KEYS = {"type", "uid", "gid", "mode", "readable", "searchable", "count"}
HOME_KEYS = {"home", "state", "errno", "entries", "groups", "errors",
             "links_not_followed", "credential_shaped_skipped", "coverage"}


class Shape(unittest.TestCase):
    def test_the_selected_bounds_are_exact(self):
        self.assertEqual((walk.MAX_ENTRIES, walk.MAX_DEPTH, walk.WALL_SECONDS), (1024, 8, 20))
        self.assertEqual(walk.HOMES, ("use-1/home", "use-2/home"))
        self.assertEqual(walk.ROOT, "/tmp/baton-w177936-qualification-180078")
        self.assertEqual(walk.RUN_IDENTITY, "180078")
        self.assertNotIn("178579", walk.ROOT)

    def test_the_credential_shape_is_the_fixtures_own(self):
        for name in (".credentials.json", "oauth.json", "auth_token", "api-key", "AUTH.TOKEN"):
            self.assertTrue(walk.CREDENTIAL.search(name), name)
        for name in ("solution.py", "projects", "abc.jsonl"):
            self.assertFalse(walk.CREDENTIAL.search(name), name)

    def test_permission_bits_follow_the_kernels_order(self):
        who = {"euid": 1000, "egid": 1000, "groups": [1000, 1001]}
        owner = os.stat_result((stat.S_IFREG | 0o604, 0, 0, 1, 1000, 4000, 0, 0, 0, 0))
        # Owner matches first even though `other` would be more permissive.
        self.assertEqual(walk.permission_bits(owner, who), 6)
        grouped = os.stat_result((stat.S_IFREG | 0o047, 0, 0, 1, 4000, 1001, 0, 0, 0, 0))
        self.assertEqual(walk.permission_bits(grouped, who), 4)
        other = os.stat_result((stat.S_IFREG | 0o004, 0, 0, 1, 4000, 4000, 0, 0, 0, 0))
        self.assertEqual(walk.permission_bits(other, who), 4)

    def test_the_source_cannot_read_follow_or_write(self):
        source = (HERE / "walk-180078.py").read_text()
        code = "".join("" if k == tokenize.COMMENT else t
                       for k, t, _, _, _ in tokenize.generate_tokens(io.StringIO(source).readline))
        body = code.split('"""', 2)[2] if code.count('"""') >= 2 else code
        for banned in ("os.readlink", "os.walk", "os.remove", "os.mkdir", "os.chmod",
                       "os.chown", "os.rename", "os.unlink", "read(", "write(",
                       "import pwd", "import grp", "import shutil", "subprocess",
                       "strerror", ".filename", "follow_symlinks=True"):
            self.assertNotIn(banned, body, banned)
        # os.open is used only for no-follow directory descriptors.
        self.assertEqual(body.count("open("), body.count("os.open("))
        self.assertEqual(body.count("_OPEN_DIR"), 4)
        self.assertIn("O_NOFOLLOW", body)
        self.assertIn("O_DIRECTORY", body)
        self.assertIn("follow_symlinks=False", body)

    def test_main_takes_no_operands_and_uses_the_fixed_root(self):
        import inspect
        with mock.patch.object(sys, "argv", ["walk-180078.py", "/etc"]):
            out = io.StringIO()
            with mock.patch.object(sys, "stdout", out):
                self.assertEqual(walk.main(), 2)
        self.assertEqual(json.loads(out.getvalue())["refused"], "this walk takes no arguments")
        self.assertIn("report(ROOT)", inspect.getsource(walk.main))


class SyntheticTree(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="w177936-walk-selftest-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "run"
        self.home = self.root / "use-1/home"
        (self.home / ".claude/projects/a-project").mkdir(parents=True)
        (self.home / ".claude/projects/a-project/session.jsonl").write_bytes(b"PRIVATE")
        (self.home / ".claude.json").write_bytes(b"PRIVATE")
        (self.home / ".claude/.credentials.json").symlink_to("/run/baton/credentials/claude")
        self.who = walk.identity()

    def homes(self, root=None):
        return {h["home"]: h for h in walk.report(str(root or self.root))["homes"]}

    def test_absent_home_is_absent_not_an_error(self):
        homes = self.homes()
        self.assertEqual(homes["use-2/home"]["state"], "absent")
        self.assertEqual(homes["use-2/home"]["errno"], "ENOENT")
        self.assertEqual(homes["use-2/home"]["entries"], 0)
        self.assertEqual(set(homes["use-2/home"]), HOME_KEYS)

    def test_aggregates_only_and_the_closed_group_shape(self):
        home = self.homes()["use-1/home"]
        self.assertEqual(home["state"], "present")
        self.assertTrue(home["groups"])
        for group in home["groups"]:
            self.assertEqual(set(group), GROUP_KEYS)
            self.assertIs(type(group["count"]), int)
            self.assertIs(type(group["readable"]), bool)
            self.assertIs(type(group["searchable"]), bool)
        self.assertEqual(sum(g["count"] for g in home["groups"]), home["entries"])

    def test_no_name_content_or_link_target_reaches_the_export(self):
        (self.home / "CANARY-DIR").mkdir()
        (self.home / "CANARY-FILE.jsonl").write_bytes(b"CANARY-CONTENT")
        (self.home / "CANARY-LINK").symlink_to("/CANARY-TARGET")
        exported = json.dumps(walk.report(str(self.root)), sort_keys=True)
        for canary in ("CANARY-DIR", "CANARY-FILE", "CANARY-CONTENT", "CANARY-TARGET",
                       "a-project", "session.jsonl", "PRIVATE"):
            self.assertNotIn(canary, exported, canary)
        self.assertNotIn("sha256", exported)

    def test_a_symlinked_home_component_is_refused_not_walked(self):
        """The probe that put this here passed at first: only the static source
        check noticed O_NOFOLLOW, so nothing PROVED it mattered. It matters on
        the home's own path -- if `use-1/home` were a link, a following open
        would walk the target and report it as the home."""
        other = Path(self.temp.name) / "decoy"
        (other / "deep").mkdir(parents=True)
        (other / "deep/DECOY-FILE").write_bytes(b"x")
        linked = Path(self.temp.name) / "linked"
        (linked / "use-1").mkdir(parents=True)
        (linked / "use-1/home").symlink_to(other)
        home = self.homes(root=linked)["use-1/home"]
        self.assertEqual(home["state"], "error")
        self.assertIn(home["errno"], ("ELOOP", "ENOTDIR"))
        self.assertEqual(home["entries"], 0)
        self.assertFalse(home["coverage"]["complete"])
        self.assertNotIn("DECOY", json.dumps(home))
        # And the target really was walkable, so a following open would have
        # produced a clean-looking answer for the wrong directory.
        self.assertTrue((other / "deep/DECOY-FILE").exists())

    def test_links_are_counted_and_never_followed(self):
        (self.home / "outside").symlink_to(self.temp.name + "/elsewhere")
        (Path(self.temp.name) / "elsewhere/deep").mkdir(parents=True)
        (Path(self.temp.name) / "elsewhere/deep/SECRET").write_bytes(b"x")
        home = self.homes()["use-1/home"]
        self.assertGreaterEqual(home["links_not_followed"], 1)
        self.assertNotIn("SECRET", json.dumps(home))
        self.assertTrue(any(g["type"] == "symlink" for g in home["groups"]))

    def test_credential_shaped_entries_are_skipped_not_opened(self):
        (self.home / ".claude/oauth-state").mkdir()
        (self.home / ".claude/oauth-state/INSIDE").write_bytes(b"x")
        home = self.homes()["use-1/home"]
        self.assertGreaterEqual(home["credential_shaped_skipped"], 1)
        self.assertNotIn("INSIDE", json.dumps(home))

    def test_an_unreadable_nested_file_is_classified_not_opened(self):
        """THE HYPOTHESIS THIS WALK EXISTS TO TEST: a provider-created file the
        collector cannot read."""
        target = self.home / ".claude/projects/a-project/session.jsonl"
        os.chmod(target, 0o000)
        self.addCleanup(os.chmod, target, 0o644)
        home = self.homes()["use-1/home"]
        denied = [g for g in home["groups"] if g["type"] == "regular" and not g["readable"]]
        self.assertTrue(denied, home["groups"])
        self.assertEqual(sum(g["count"] for g in denied), 1)

    def test_an_unsearchable_directory_reports_a_stat_error(self):
        """Mode 0600 on a directory: readable, so it OPENS and SCANDIRS fine,
        but not searchable, so stat of each child fails. A probe taught me this
        lands on the stat handler, not the opendir one -- I had assumed opendir
        and the test was passing for the other reason."""
        os.chmod(self.home / ".claude/projects", 0o600)
        self.addCleanup(os.chmod, self.home / ".claude/projects", 0o755)
        home = self.homes()["use-1/home"]
        self.assertTrue(home["errors"], home)
        self.assertIn("stat:EACCES", home["errors"])
        self.assertFalse(home["coverage"]["complete"])

    def test_an_unopenable_directory_reports_an_opendir_error(self):
        """Mode 0000: the open itself fails, which is the other handler."""
        os.chmod(self.home / ".claude/projects", 0o000)
        self.addCleanup(os.chmod, self.home / ".claude/projects", 0o755)
        home = self.homes()["use-1/home"]
        self.assertIn("opendir:EACCES", home["errors"])
        self.assertFalse(home["coverage"]["complete"])
        # The directory itself is still counted and classified; only its
        # contents are unreachable.
        self.assertTrue(any(g["type"] == "directory" and not g["readable"]
                            for g in home["groups"]), home["groups"])

    def test_the_entry_cap_truncates_and_says_so(self):
        with mock.patch.object(walk, "MAX_ENTRIES", 3):
            home = self.homes()["use-1/home"]
        self.assertEqual(home["entries"], 3)
        self.assertTrue(home["coverage"]["truncated"])
        self.assertFalse(home["coverage"]["complete"])

    def test_the_depth_cap_stops_and_says_so(self):
        deep = self.home
        for level in range(6):
            deep = deep / ("level-%d" % level)
        deep.mkdir(parents=True)
        with mock.patch.object(walk, "MAX_DEPTH", 2):
            home = self.homes()["use-1/home"]
        self.assertTrue(home["coverage"]["depth_limited"])
        self.assertLessEqual(home["coverage"]["max_depth_reached"], 2)
        self.assertFalse(home["coverage"]["complete"])

    def test_the_wall_bound_stops_and_says_so(self):
        with mock.patch.object(walk, "WALL_SECONDS", -1):
            home = self.homes()["use-1/home"]
        self.assertTrue(home["coverage"]["timed_out"])
        self.assertFalse(home["coverage"]["complete"])
        self.assertEqual(home["entries"], 0)

    def test_a_clean_tree_reports_complete(self):
        home = self.homes()["use-1/home"]
        self.assertTrue(home["coverage"]["complete"], home)
        self.assertEqual(home["errors"], {})

    def test_the_walk_does_not_modify_the_tree(self):
        def snapshot():
            seen = {}
            for base, directories, files in os.walk(self.root):
                for name in list(directories) + list(files):
                    place = Path(base) / name
                    info = place.lstat()
                    seen[str(place)] = (info.st_mode, info.st_uid, info.st_gid, info.st_size)
            return seen

        before = snapshot()
        walk.report(str(self.root))
        self.assertEqual(snapshot(), before)

    def test_no_descriptor_is_leaked(self):
        before = len(os.listdir("/proc/self/fd"))
        for _ in range(5):
            walk.report(str(self.root))
        self.assertLessEqual(len(os.listdir("/proc/self/fd")), before + 1)

    def test_the_report_is_closed_and_json_safe(self):
        value = walk.report(str(self.root))
        self.assertEqual(set(value), {"schema", "work", "run_identity", "root", "operator",
                                      "bounds", "homes", "method", "limits"})
        self.assertEqual(json.loads(json.dumps(value)), value)
        self.assertEqual(value["bounds"],
                         {"max_entries_per_home": 1024, "max_depth": 8, "wall_seconds": 20})


if __name__ == "__main__":
    unittest.main(verbosity=2)
