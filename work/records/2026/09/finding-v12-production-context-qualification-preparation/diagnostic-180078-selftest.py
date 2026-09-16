"""Verify diagnostic-180078.py against a SYNTHETIC tree only.

The real 180078 tree is never touched here: the operand root is passed
explicitly to the internal helpers, while the shipped `main` always uses the
hard-coded ROOT and accepts no arguments. Owner180325 forbids inspecting the
private tree from the managed context, and the operator's identity and mount
view are not this one's anyway.
"""
import errno
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
spec = importlib.util.spec_from_file_location("diagnostic_180078", HERE / "diagnostic-180078.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

CLOSED_KEYS = {"operand", "state", "errno", "type", "uid", "gid", "mode", "links"}


class Shape(unittest.TestCase):
    def test_the_eleven_operands_are_exactly_the_reviews(self):
        self.assertEqual(probe.OPERANDS, (
            "", "use-1", "use-1/home", "use-1/home/.claude", "use-1/home/.claude/projects",
            "private-layout.json", "private-layout.json.tmp",
            "use-2", "use-2/home", "use-2/home/.claude", "use-2/home/.claude/projects"))
        self.assertEqual(len(probe.OPERANDS), 11)

    def test_the_root_is_the_consumed_identity_and_not_the_other_one(self):
        self.assertEqual(probe.ROOT, "/tmp/baton-w177936-qualification-180078")
        self.assertEqual(probe.RUN_IDENTITY, "180078")
        self.assertNotIn("178579", probe.ROOT)

    def test_the_errno_enum_is_the_reviews_closed_list(self):
        self.assertEqual(set(probe.CATEGORIES.values()),
                         {"EACCES", "EPERM", "ENOENT", "ENOTDIR", "ELOOP", "ENOSPC", "EDQUOT", "EIO"})
        self.assertEqual(probe.category(errno.EACCES), "EACCES")
        self.assertEqual(probe.category(errno.ENOENT), "ENOENT")
        # Anything outside the enum collapses, rather than exporting a platform name.
        self.assertEqual(probe.category(errno.EEXIST), "other")
        self.assertEqual(probe.category(None), "other")

    def test_identity_is_numbers_and_never_account_names(self):
        value = probe.identity()
        self.assertEqual(set(value), {"uid", "euid", "gid", "egid", "groups"})
        for key in ("uid", "euid", "gid", "egid"):
            self.assertIs(type(value[key]), int)
        self.assertTrue(all(type(g) is int for g in value["groups"]))
        # The name-resolving modules are not even imported.
        self.assertNotIn("pwd", probe.__dict__)
        self.assertNotIn("grp", probe.__dict__)

    def test_the_source_cannot_read_list_or_write(self):
        """Static, over comment-stripped source: the forbidden operations are
        absent from executable text, not merely unused."""
        source = (HERE / "diagnostic-180078.py").read_text()
        code = "".join("" if k == tokenize.COMMENT else t
                       for k, t, _, _, _ in tokenize.generate_tokens(io.StringIO(source).readline))
        body = code.split('"""', 2)[2] if code.count('"""') >= 2 else code
        for banned in ("os.readlink", "os.listdir", "os.scandir", "os.walk", "os.remove",
                       "os.mkdir", "os.chmod", "os.chown", "os.rename", "os.unlink",
                       "read(", "write(", "import pwd", "import grp", "import shutil",
                       "subprocess", "strerror", ".filename"):
            self.assertNotIn(banned, body, banned)
        # `open(` needs care: os.open IS used, for no-follow directory
        # descriptors that cannot read content. Only a BARE open() would.
        self.assertEqual(body.count("open("), body.count("os.open("))
        self.assertEqual(body.count("os.open("), 2)
        # Both carry the no-follow directory flags, and nothing else does.
        self.assertEqual(body.count("_NOFOLLOW_DIR"), 3)
        self.assertIn("O_NOFOLLOW", body)
        self.assertIn("O_DIRECTORY", body)

    def test_main_takes_no_operands(self):
        """A path operand would turn a fixed-path diagnostic into a general
        private-tree reader."""
        with mock.patch.object(sys, "argv", ["diagnostic-180078.py", "/etc"]):
            out = io.StringIO()
            with mock.patch.object(sys, "stdout", out):
                self.assertEqual(probe.main(), 2)
        self.assertEqual(json.loads(out.getvalue())["refused"],
                         "this diagnostic takes no arguments")

    def test_main_uses_the_fixed_root(self):
        import inspect
        self.assertIn("report(ROOT)", inspect.getsource(probe.main))


class SyntheticTree(unittest.TestCase):
    """A stand-in with one of every state the operator's tree could show."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="w177936-diagnostic-selftest-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "run"
        (self.root / "use-1/home/.claude/projects").mkdir(parents=True)
        (self.root / "private-layout.json").write_bytes(b"{}")
        os.chmod(self.root / "use-1/home/.claude", 0o2770)

    def rows(self):
        return {r["operand"]: r for r in
                [probe.row(str(self.root), relative) for relative in probe.OPERANDS]}

    def test_present_absent_and_the_closed_field_set(self):
        rows = self.rows()
        self.assertEqual(len(rows), 11)
        for row in rows.values():
            self.assertEqual(set(row), CLOSED_KEYS)
        self.assertEqual(rows["<root>"]["state"], "present")
        self.assertEqual(rows["<root>"]["type"], "directory")
        self.assertEqual(rows["use-1/home/.claude"]["mode"], "0o2770")
        self.assertEqual(rows["private-layout.json"]["type"], "regular")
        self.assertEqual(rows["private-layout.json"]["links"], 1)
        # The absent half of the operand list, which is the interesting half:
        # a stopped attempt should not have reached use-2 at all.
        for missing in ("private-layout.json.tmp", "use-2", "use-2/home",
                        "use-2/home/.claude", "use-2/home/.claude/projects"):
            self.assertEqual(rows[missing]["state"], "absent", missing)
            self.assertEqual(rows[missing]["errno"], "ENOENT", missing)
            self.assertIsNone(rows[missing]["uid"], missing)

    def test_a_symlinked_intermediate_is_refused_not_resolved(self):
        """THE CASE PLAIN LSTAT GETS WRONG. `use-2/home` is a symlink to a real
        directory; lstat of `use-2/home/.claude` would describe the target and
        look like a clean answer.

        The refusal errno is NOT pinned to ELOOP. Linux reports ENOTDIR when
        O_DIRECTORY accompanies O_NOFOLLOW on a symlink, and this test failed
        the first time for exactly that reason -- the guard worked and the
        assertion named the wrong code. Both codes are inside the review's
        closed enum, so either way the operator sees a refusal rather than a
        wrong location."""
        (self.root / "use-2").mkdir()
        (self.root / "elsewhere/.claude").mkdir(parents=True)
        (self.root / "use-2/home").symlink_to(self.root / "elsewhere")
        rows = self.rows()
        self.assertEqual(rows["use-2/home"]["type"], "symlink")
        self.assertEqual(rows["use-2/home/.claude"]["state"], "error")
        self.assertIn(rows["use-2/home/.claude"]["errno"], ("ELOOP", "ENOTDIR"))
        self.assertIn(rows["use-2/home/.claude"]["errno"], set(probe.CATEGORIES.values()))
        self.assertIsNone(rows["use-2/home/.claude"]["uid"])
        # And the plain-lstat answer it avoided: the target really is there,
        # so a following implementation would have reported a clean directory.
        self.assertTrue(os.path.isdir(str(self.root / "use-2/home/.claude")))

    def test_an_unsearchable_directory_reports_eacces(self):
        os.chmod(self.root / "use-1/home", 0o000)
        self.addCleanup(os.chmod, self.root / "use-1/home", 0o755)
        rows = self.rows()
        self.assertEqual(rows["use-1/home"]["state"], "present")
        self.assertEqual(rows["use-1/home"]["mode"], "0o0")
        self.assertEqual(rows["use-1/home/.claude"]["state"], "error")
        self.assertEqual(rows["use-1/home/.claude"]["errno"], "EACCES")

    def test_a_non_directory_component_reports_enotdir(self):
        (self.root / "use-2").write_bytes(b"not a directory")
        rows = self.rows()
        self.assertEqual(rows["use-2"]["type"], "regular")
        self.assertEqual(rows["use-2/home"]["errno"], "ENOTDIR")

    def test_no_private_name_content_or_message_reaches_the_export(self):
        """Canaries at every shape the tree could hold."""
        (self.root / "use-1/home/.claude/projects/CANARY-PROJECT").mkdir()
        (self.root / "use-1/home/CANARY-FILE.jsonl").write_bytes(b"CANARY-CONTENT")
        (self.root / "use-1/home/.claude/.credentials.json").symlink_to("/CANARY-TARGET")
        exported = json.dumps(probe.report(str(self.root)), sort_keys=True)
        for canary in ("CANARY-PROJECT", "CANARY-FILE", "CANARY-CONTENT", "CANARY-TARGET"):
            self.assertNotIn(canary, exported, canary)
        # Not even as a digest.
        self.assertNotIn("sha256", exported)

    def test_the_report_is_closed_and_json_safe(self):
        value = probe.report(str(self.root))
        self.assertEqual(set(value), {"schema", "work", "run_identity", "root",
                                      "operator", "paths", "method", "limits"})
        self.assertEqual(json.loads(json.dumps(value)), value)
        self.assertEqual(value["run_identity"], "180078")

    def test_the_tree_is_not_modified_by_looking_at_it(self):
        def snapshot():
            seen = {}
            for base, directories, files in os.walk(self.root):
                for name in list(directories) + list(files):
                    place = Path(base) / name
                    info = place.lstat()
                    seen[str(place)] = (info.st_mode, info.st_uid, info.st_gid, info.st_size)
            return seen

        before = snapshot()
        probe.report(str(self.root))
        self.assertEqual(snapshot(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
