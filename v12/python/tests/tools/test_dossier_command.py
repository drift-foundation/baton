"""W321688 — the installed record command, and the recovery set it checks.

The pilot assessment found `stack_command.COMMANDS` had no record verb at all,
so these drive the SUBCOMMAND an operator actually reaches rather than the API
underneath it: `python3 -m tools.stack_command record ...` and
`<distro>/baton-v12-stack record ...` are the same code.

TWO THINGS THESE PROVE THAT THE AUTHORITY CASES CANNOT. The authority stores
references and never opens a file, so the honest refusal when cited evidence is
absent, unreadable or CHANGED is this layer's behaviour. And the retained-instance
recovery contract is filesystem work by definition: a complete set, every digest,
and a refusal to call a restore admissible while an earlier writer cannot be ruled
out.

Every store, instance and root is this fixture's own temporary directory. No
deployment is started, no engine or provider is reached, and nothing is copied
out of or into a real instance.
"""

import hashlib
import io
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from baton_v12.authority import Authority
from baton_v12.authority.schema import SCHEMA_VERSION
from tools import stack_command

UUID = "0123456789abcdef0123456789abcdef"
LOCATOR = "operator-quickstart-7f3a91c2"
REFERENCE = "work/records/2026/10/finding-v12-pilot-dossier-binding/FINDING.md"


class CommandCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-record-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.store = os.path.join(self.root, "authority.sqlite3")
        self.work = UUID[:8] + "-W1"
        authority = Authority.create(self.store, authority_uuid=UUID)
        authority.create_work(self.work, "impl", operation_id="op-create")
        authority.dispose()
        self.repo = os.path.join(self.root, "repo")
        os.makedirs(os.path.dirname(os.path.join(self.repo, REFERENCE)))
        self.evidence = os.path.join(self.repo, REFERENCE)
        self.write(self.evidence, "the finding\n")

    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def record(self, *operands):
        """The installed subcommand, with its streams captured.

        Reached through `stack_command.main` rather than the module directly,
        because the gap the assessment recorded was that the DEPLOYED command
        had no such verb -- so the dispatch table is part of what is proved.
        """
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = stack_command.main(["record", *operands])
        return code, out.getvalue(), err.getvalue()

    def said(self, out):
        return json.loads(out)

    def base(self):
        return ["--authority-store", self.store, "--authority-uuid", UUID]

    def bind(self, locator=LOCATOR, operation_id="op-bind"):
        code, out, err = self.record("bind", *self.base(), "--work", self.work,
                                     "--locator", locator,
                                     "--operation-id", operation_id)
        self.assertEqual(code, 0, err)
        return self.said(out)

    def cite(self, reference=REFERENCE, operation_id="op-ev"):
        code, out, err = self.record("cite", *self.base(), "--work", self.work,
                                     "--root", self.repo,
                                     "--reference", reference,
                                     "--operation-id", operation_id)
        return code, out, err


class TheRecordVerbIsPartOfTheInstalledCommand(CommandCase):

    def test_record_is_a_subcommand_of_the_deployed_command(self):
        """The finding was that it was not."""
        self.assertIn("record", stack_command.COMMANDS)

    def test_it_is_reachable_the_same_way_from_a_frozen_build(self):
        """`bundled_argv` is how the supervisor starts a child in either form;
        a verb it cannot name is a verb a deployment cannot run."""
        argv = stack_command.bundled_argv("record", ["read"])
        self.assertIn("record", argv)

    def test_the_help_lists_it(self):
        out = io.StringIO()
        with redirect_stdout(out):
            stack_command.main([])
        self.assertIn("record", out.getvalue())


class ItBindsAndReadsThroughTheCommand(CommandCase):

    def test_bind_then_read_resolves_authority_and_work_to_one_dossier(self):
        self.bind()
        code, out, err = self.record("read", *self.base(), "--work", self.work)
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertEqual(said["authority_uuid"], UUID)
        self.assertEqual(said["dossier"]["locator"], LOCATOR)
        self.assertEqual(said["evidence"], [])

    def test_read_resolves_a_LOCATOR_back_to_its_work(self):
        self.bind()
        code, out, err = self.record("read", *self.base(),
                                     "--locator", LOCATOR)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.said(out)["dossier"]["work_id"], self.work)

    def test_read_of_an_unbound_work_answers_null_rather_than_failing(self):
        code, out, err = self.record("read", *self.base(), "--work", self.work)
        self.assertEqual(code, 0, err)
        self.assertIsNone(self.said(out)["dossier"])

    def test_read_names_EXACTLY_ONE_selector(self):
        for operands in ([], ["--work", self.work, "--locator", LOCATOR]):
            with self.subTest(operands=operands):
                code, _out, err = self.record("read", *self.base(), *operands)
                self.assertEqual(code, 2)
                self.assertIn("exactly one", err)

    def test_an_AUTHORITY_REFUSAL_arrives_as_its_own_sentence(self):
        """Not a traceback: every refusal reachable here is a contract answer
        an operator is meant to read."""
        self.bind()
        code, _out, err = self.record(
            "bind", *self.base(), "--work", self.work,
            "--locator", "operator-quickstart-0b1c2d3e",
            "--operation-id", "op-bind-2")
        self.assertEqual(code, 2)
        self.assertIn("refused:", err)
        self.assertIn("keeps one address", err)

    def test_a_MALFORMED_locator_refuses_through_the_command_too(self):
        code, _out, err = self.record(
            "bind", *self.base(), "--work", self.work,
            "--locator", "nested/record-7f3a91c2", "--operation-id", "op-x")
        self.assertEqual(code, 2)
        self.assertIn("ONE FLAT SEGMENT", err)


class ItCitesEvidenceByDigestingIt(CommandCase):

    def setUp(self):
        super().setUp()
        self.bind()

    def test_cite_digests_the_real_file_and_records_that_digest(self):
        code, out, err = self.cite()
        self.assertEqual(code, 0, err)
        with open(self.evidence, "rb") as handle:
            expected = "sha256:" + hashlib.sha256(handle.read()).hexdigest()
        self.assertEqual(self.said(out)["digest"], expected)

    def test_citing_a_file_that_is_not_there_is_refused(self):
        code, _out, err = self.cite(reference="work/records/absent.md")
        self.assertEqual(code, 2)
        self.assertIn("nothing", err)

    def test_an_exact_recitation_replays_through_the_command(self):
        self.cite()
        code, out, err = self.cite()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.said(out)["act_id"], "op-ev")


class VerifyResolvesCitationsHonestly(CommandCase):
    """The acceptance's "absent or inaccessible evidence is honest refusal",
    and the four outcomes are deliberately not one outcome."""

    def setUp(self):
        super().setUp()
        self.bind()
        code, _out, err = self.cite()
        self.assertEqual(code, 0, err)

    def verify(self):
        return self.record("verify", *self.base(), "--work", self.work,
                           "--root", self.repo)

    def test_intact_evidence_verifies(self):
        code, out, err = self.verify()
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertEqual(said["cited"], 1)
        self.assertEqual(said["intact"], 1)
        self.assertEqual(said["evidence"][0]["state"], "present")
        self.assertEqual(said["authority_uuid"], UUID)

    def test_ABSENT_evidence_is_refused_and_named_as_absent(self):
        os.remove(self.evidence)
        code, out, err = self.verify()
        self.assertEqual(code, 2)
        self.assertEqual(self.said(out)["evidence"][0]["state"], "absent")
        self.assertIn("did not resolve intact", err)
        self.assertIn("nothing was changed", err)

    def test_CHANGED_evidence_is_refused_and_distinguished_from_absent(self):
        """A citation whose bytes moved underneath it is a different fact from
        one whose file is gone, and only a recorded digest can tell them
        apart."""
        self.write(self.evidence, "rewritten\n")
        code, out, err = self.verify()
        self.assertEqual(code, 2)
        held = self.said(out)["evidence"][0]
        self.assertEqual(held["state"], "changed")
        self.assertNotEqual(held["actual"], held["cited_digest"])
        self.assertIn("did not resolve intact", err)

    @unittest.skipIf(os.getuid() == 0, "root bypasses the mode bits")
    def test_UNREADABLE_evidence_is_NOT_reported_as_absent(self):
        """Reporting a permission problem as a missing file would send an
        operator to restore something that was never lost."""
        os.chmod(self.evidence, 0)
        self.addCleanup(os.chmod, self.evidence, stat.S_IRUSR | stat.S_IWUSR)
        code, out, err = self.verify()
        self.assertEqual(code, 2)
        self.assertEqual(self.said(out)["evidence"][0]["state"], "unreadable")
        self.assertIn("did not resolve intact", err)

    def test_a_DIRECTORY_at_the_reference_is_its_own_state(self):
        os.remove(self.evidence)
        os.makedirs(self.evidence)
        code, out, _err = self.verify()
        self.assertEqual(code, 2)
        self.assertEqual(self.said(out)["evidence"][0]["state"],
                         "not-a-regular-file")

    def test_a_dossier_citing_NOTHING_is_refused_rather_than_called_intact(self):
        other = UUID[:8] + "-W2"
        authority = Authority.open(self.store, expected_authority_uuid=UUID)
        authority.create_work(other, "impl", operation_id="op-create-2")
        authority.bind_dossier(other, "second-record-0b1c2d3e",
                               operation_id="op-bind-second")
        authority.dispose()
        code, out, err = self.record("verify", *self.base(), "--work", other,
                                     "--root", self.repo)
        self.assertEqual(code, 2)
        self.assertEqual(self.said(out)["cited"], 0)
        self.assertIn("cites no evidence", err)

    def test_verifying_an_UNBOUND_work_is_refused(self):
        other = UUID[:8] + "-W3"
        authority = Authority.open(self.store, expected_authority_uuid=UUID)
        authority.create_work(other, "impl", operation_id="op-create-3")
        authority.dispose()
        code, _out, err = self.record("verify", *self.base(), "--work", other,
                                      "--root", self.repo)
        self.assertEqual(code, 2)
        self.assertIn("no canonical dossier", err)


# W321688 review 2026-10-18T08-25-00Z P1: THE RECOVERY CASES MOVED, and their
# expectations were wrong rather than merely thin. They built two dummy SQLite
# headers, cited a synthetic digest with no matching artifact, omitted
# deployment.json, and expected a COMPLETE restore to succeed -- so they
# asserted the defect. They are replaced by `test_dossier_recovery.py`, which
# builds a real authority store, real provenance and real retained trees, and
# drives the closed set the owner accepted.


if __name__ == "__main__":
    unittest.main()
