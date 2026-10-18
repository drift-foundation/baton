"""W321688 — the closed recovery set, and contained evidence resolution.

Review 2026-10-18T08-25-00Z reproduced two defects through the public command
and these are the cases that hold them closed.

P1a: a synthetic manifest naming ONE ordinary file as `authority_store`
returned 0 with `faults: []` and `schema_compatible: true`; provenance was
copied as values nothing validated; sidecar NAMES were recorded without their
bytes; retained inputs, outputs and workspaces were not bound at all; and
without `--flat` the required `--root` was ignored and the original absolute
paths were checked. Every one of those is a separate refusal now.

P1b: a reference the authority accepts as relative, symlinked to a file
OUTSIDE `--root`, could be cited and then verified as intact -- exit 0 twice.
Out-of-root bytes were being certified as this dossier's evidence under this
root.

THE FIXTURES ARE REAL, which is the other half of the correction. The previous
recovery cases used two dummy SQLite headers, cited a synthetic digest with no
matching artifact, and omitted `deployment.json` while expecting a complete
restore to succeed -- so they asserted the defect. Here the authority store is
a REAL one created by the real opener (so its own `meta` answers the identity
and compatibility questions), the provenance is a real document, and the
retained trees hold real files.

No deployment is started, no engine or provider reached, and nothing is copied
out of or into a real instance. Slawomir owns production backup and restore.
"""

import io
import json
import os
import shutil
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from baton_v12.authority import Authority
from baton_v12.job_manager import JobStore
from baton_v12.worker_manager import ControlStore
from baton_v12.authority.schema import SCHEMA_VERSION, STORE_KIND
from tools import dossier_command, stack_command

UUID = "0123456789abcdef0123456789abcdef"
OTHER_UUID = "fedcba9876543210fedcba9876543210"
LOCATOR = "operator-quickstart-7f3a91c2"
REFERENCE = "work/records/2026/10/finding-v12-pilot-dossier-binding/FINDING.md"


class Fixture(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-recovery-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name

    def write(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def record(self, *operands):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = stack_command.main(["record", *operands])
        return code, out.getvalue(), err.getvalue()


class ContainedEvidence(Fixture):
    """P1b. The root means something or the relative grammar promises nothing."""

    def setUp(self):
        super().setUp()
        self.store = os.path.join(self.root, "authority.sqlite3")
        self.work = UUID[:8] + "-W1"
        authority = Authority.create(self.store, authority_uuid=UUID)
        authority.create_work(self.work, "impl", operation_id="op-create")
        authority.bind_dossier(self.work, LOCATOR, operation_id="op-bind")
        authority.dispose()
        self.repo = os.path.join(self.root, "repo")
        self.inside = self.write(os.path.join(self.repo, REFERENCE), "real\n")
        self.outside = self.write(os.path.join(self.root, "outside.md"),
                                  "not under the root\n")

    def base(self):
        return ["--authority-store", self.store, "--authority-uuid", UUID]

    def cite(self, reference, operation_id="op-ev"):
        return self.record("cite", *self.base(), "--work", self.work,
                           "--root", self.repo, "--reference", reference,
                           "--operation-id", operation_id)

    def verify(self):
        return self.record("verify", *self.base(), "--work", self.work,
                           "--root", self.repo)

    def test_a_contained_regular_file_cites_and_verifies(self):
        code, _out, err = self.cite(REFERENCE)
        self.assertEqual(code, 0, err)
        code, out, err = self.verify()
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["evidence"][0]["state"],
                         dossier_command.EVIDENCE_PRESENT)

    def test_a_SYMLINK_to_a_file_outside_the_root_cannot_be_CITED(self):
        """The exact reproduction: exit 0 twice, before."""
        os.symlink(self.outside, os.path.join(self.repo, "escape"))
        code, _out, err = self.cite("escape")
        self.assertEqual(code, 2, err)
        self.assertIn(dossier_command.EVIDENCE_ESCAPES, err)
        self.assertIn("not under this root", err)

    def test_an_INTERMEDIATE_symlink_is_refused_at_its_own_depth(self):
        """`a -> /tmp` makes `a/b` out of root as surely as a final link does,
        and a check that only looked at the leaf would miss it."""
        elsewhere = os.path.join(self.root, "elsewhere")
        self.write(os.path.join(elsewhere, "target.md"), "outside\n")
        os.symlink(elsewhere, os.path.join(self.repo, "through"))
        code, _out, err = self.cite("through/target.md")
        self.assertEqual(code, 2, err)
        self.assertIn(dossier_command.EVIDENCE_ESCAPES, err)

    def test_a_symlink_that_happens_to_point_INSIDE_is_still_refused(self):
        """A link's target can be replaced after the answer, so a contained
        resolution cannot depend on where one pointed at check time."""
        os.symlink(self.inside, os.path.join(self.repo, "inward"))
        self.assertEqual(self.cite("inward")[0], 2)

    def test_evidence_REPLACED_BY_A_SYMLINK_verifies_as_an_escape(self):
        """And the citation already recorded stays honest afterwards."""
        self.assertEqual(self.cite(REFERENCE)[0], 0)
        os.remove(self.inside)
        os.symlink(self.outside, self.inside)
        code, out, err = self.verify()
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["evidence"][0]["state"],
                         dossier_command.EVIDENCE_ESCAPES)
        self.assertIn("did not resolve intact", err)

    def test_the_GRAMMAR_is_checked_before_any_filesystem_access(self):
        """P1b's second half: malformed escape operands were read before the
        authority was asked whether they were citable at all."""
        for reference in ("/etc/passwd", "a/../../etc/passwd", "~/secret",
                          "./a", "a//b"):
            with self.subTest(reference=reference):
                code, _out, err = self.cite(reference, operation_id="op-bad")
                self.assertEqual(code, 2)
                self.assertNotIn(dossier_command.EVIDENCE_PRESENT, err)

    def test_absent_and_unreadable_stay_DIFFERENT_answers(self):
        self.assertEqual(self.cite(REFERENCE)[0], 0)
        os.remove(self.inside)
        self.assertEqual(json.loads(self.verify()[1])["evidence"][0]["state"],
                         dossier_command.EVIDENCE_ABSENT)
        self.write(self.inside, "real\n")
        if os.getuid() != 0:
            os.chmod(self.inside, 0)
            self.addCleanup(os.chmod, self.inside, stat.S_IRUSR | stat.S_IWUSR)
            self.assertEqual(
                json.loads(self.verify()[1])["evidence"][0]["state"],
                dossier_command.EVIDENCE_UNREADABLE)

    def test_a_DIRECTORY_at_the_reference_is_not_a_regular_file(self):
        os.makedirs(os.path.join(self.repo, "adir"))
        code, _out, err = self.cite("adir")
        self.assertEqual(code, 2)
        self.assertIn(dossier_command.EVIDENCE_NOT_REGULAR, err)


class ThePARENTReplacementRaceIsClosed(Fixture):
    """Review 2026-10-18T08-48-00Z P1, reproduced by the reviewer and now shut.

    The previous resolution checked every component with `lstat` and then
    opened the WHOLE PATHNAME, so `O_NOFOLLOW` guarded only the final
    component. Rename `root/a` and put a symlink to an outside directory in its
    place between its `lstat` and the final open, and the open resolved through
    the new link and returned OUTSIDE BYTES as `present`.

    Descriptor anchoring closes it: each component is opened relative to the
    previous one's descriptor, so a replacement after a component has been
    opened cannot change what that descriptor refers to. The check and the use
    are the same act.
    """

    def setUp(self):
        super().setUp()
        self.repo = os.path.join(self.root, "repo")
        self.inside = self.write(os.path.join(self.repo, "a", "f"), "inside\n")
        self.outside = os.path.join(self.root, "outside")
        self.write(os.path.join(self.outside, "f"), "OUTSIDE BYTES\n")

    def swap_parent(self):
        """Replace `repo/a` with a link to the outside directory, once."""
        os.rename(os.path.join(self.repo, "a"),
                  os.path.join(self.root, "moved"))
        os.symlink(self.outside, os.path.join(self.repo, "a"))

    def test_a_parent_replaced_MID_RESOLUTION_cannot_be_read_through(self):
        """The interleaving: the swap happens at the moment the old code was
        between its last check and its open."""
        import hashlib

        held = []
        real = dossier_command._digest_fd

        def hooked(descriptor):
            held.append(True)
            return real(descriptor)

        # The hook fires only once the final descriptor is already open, so
        # swapping here is strictly LATER than the window the old code had --
        # and the stricter test is below.
        dossier_command._digest_fd = hooked
        self.addCleanup(setattr, dossier_command, "_digest_fd", real)
        self.swap_parent()
        state, digest, _bytes = dossier_command._contained_read(self.repo,
                                                                "a/f")
        # The parent IS a symlink now, so resolution refuses rather than
        # reading the outside file.
        self.assertEqual(state, dossier_command.EVIDENCE_ESCAPES)
        self.assertIsNone(digest)
        outside = hashlib.sha256(b"OUTSIDE BYTES\n").hexdigest()
        self.assertNotIn(outside, json.dumps(state))

    def test_the_descriptor_ANCHOR_survives_a_rename_after_it_is_open(self):
        """Once `repo/a` is open, renaming it away cannot redirect the read:
        the descriptor still refers to the directory that was checked."""
        state, digest, _bytes = dossier_command._contained_read(self.repo,
                                                                "a/f")
        self.assertEqual(state, dossier_command.EVIDENCE_PRESENT)
        intact = digest
        self.swap_parent()
        # A fresh resolution now refuses, and the earlier answer was never the
        # outside file.
        again, _digest, _held = dossier_command._contained_read(self.repo,
                                                               "a/f")
        self.assertEqual(again, dossier_command.EVIDENCE_ESCAPES)
        self.assertTrue(intact.startswith("sha256:"))

    def test_a_FIFO_does_not_block_the_check(self):
        """Opening a FIFO for reading waits for a writer unless `O_NONBLOCK`
        is set, so a check that hung on a named pipe somebody left in a tree
        would be a denial of service dressed as a verification."""
        os.mkfifo(os.path.join(self.repo, "pipe"))
        state, digest, _bytes = dossier_command._contained_read(self.repo,
                                                                "pipe")
        self.assertEqual(state, dossier_command.EVIDENCE_NOT_REGULAR)
        self.assertIsNone(digest)

    def test_an_empty_reference_is_not_the_root_itself(self):
        self.assertEqual(
            dossier_command._contained_read(self.repo, "")[0],
            dossier_command.EVIDENCE_NOT_REGULAR)

    def test_a_root_that_is_itself_a_symlink_is_refused(self):
        linked = os.path.join(self.root, "linked-root")
        os.symlink(self.repo, linked)
        self.assertEqual(
            dossier_command._contained_read(linked, "a/f")[0],
            dossier_command.EVIDENCE_ESCAPES)


class TheClosedRecoverySet(Fixture):
    """P1a. A REAL instance, and the whole set or nothing."""

    def setUp(self):
        super().setUp()
        # THE REAL INSTANCE PRODUCER AND THE REAL LAYOUT. Review
        # 2026-10-18T09-04-00Z P1: the previous fixture handcrafted a selector
        # carrying an `authority_store` member that `tools.instance.emit` does
        # not emit, so it proved the consumer agreed with a double rather than
        # with the contract. Everything below comes from `instance.layout` and
        # `instance.emit`, and `instance.malformed` accepts the result.
        from tools import instance as contract

        self.contract = contract
        self.destination = os.path.join(self.root, "instance")
        self.places = contract.layout(self.destination)
        os.makedirs(self.places["stores"])
        self.store = self.places["authority_store"]
        # REAL STORES, through their own supported openers, so the identity and
        # compatibility questions are answered by real metadata rather than by
        # two dummy SQLite headers.
        authority = Authority.create(self.store, authority_uuid=UUID)
        work = UUID[:8] + "-W1"
        authority.create_work(work, "impl", operation_id="op-create")
        authority.bind_dossier(work, LOCATOR, operation_id="op-bind")
        authority.dispose()
        clock = (lambda: "2026-10-18T09:00:00.000Z")
        JobStore.open(self.places["job_store"], authority_uuid=UUID,
                      incarnation="jobs-1", clock=clock).close()
        ControlStore.open(self.places["control_store"],
                          incarnation="manager-1", clock=clock).close()
        self.deployment = self.write(self.places["deployment"],
                                     json.dumps({"schema":
                                                 "baton.v12.deployment/1"}))
        for name in ("state", "logs", "repository"):
            self.write(os.path.join(self.places[name], "kept.txt"),
                       f"retained {name}\n")
        # The command the selector names must exist for the real validator.
        self.write(self.places["command"], "#!/bin/sh\nexit 0\n")
        self.described = contract.emit(
            self.destination, authority_uuid=UUID,
            identity={"version": "12.0.0", "command": "baton-v12-stack"},
            runtime={"files": 81, "digest": "c1ef3d23"},
            now="2026-10-18T09:00:00.000Z")
        self.assertIsNone(
            contract.malformed(self.described, self.places["instance"]),
            "the fixture must be a selector the REAL validator accepts")
        self.instance = self.places["instance"]
        self.rewrite()
        self.manifest = os.path.join(self.root, "recovery-set.json")
        self.restored = os.path.join(self.root, "restored")

    def under(self, name):
        """Where the real layout puts `name`, relative to the destination.

        DERIVED, never spelled: the contract's own directory names are its
        business -- `stores` is `db` and `repository` is `repo` -- and a test
        that hard-coded either would be asserting against a guess.
        """
        return os.path.relpath(self.places[name], self.destination)

    def restored_at(self, name):
        return os.path.join(self.restored, self.under(name))

    def rewrite(self):
        self.write(self.instance, json.dumps(self.described))

    def manifested(self, *, expect=0):
        code, out, err = self.record("recovery-manifest",
                                     "--instance", self.instance)
        self.assertEqual(code, expect, err)
        if out.strip():
            self.write(self.manifest, out)
        return (json.loads(out) if out.strip() else None), err

    def restore(self):
        """The whole destination, as recorded, under a new root."""
        shutil.copytree(self.destination, self.restored, symlinks=True)

    def checked(self, *extra):
        return self.record("recovery-check", "--manifest", self.manifest,
                           "--root", self.restored, *extra)

    def tamper(self, relative, text="tampered\n"):
        self.write(os.path.join(self.restored, relative), text)

    # -- the manifest ------------------------------------------------------

    def test_the_manifest_binds_the_WHOLE_set_with_real_provenance(self):
        said, _err = self.manifested()
        self.assertEqual(sorted(said["members"]), sorted(
            dossier_command.STORES))
        self.assertEqual(sorted(said["provenance"]), sorted(
            dossier_command.PROVENANCE))
        self.assertEqual(said["missing_members"], [])
        self.assertEqual(said["authority_uuid"], UUID)
        # THE STORE'S OWN METADATA, read from the file rather than assumed.
        self.assertEqual(said["stored_identity"]["store_kind"], STORE_KIND)
        self.assertEqual(said["stored_identity"]["schema_version"],
                         str(SCHEMA_VERSION))
        # SIDECAR BYTES, not names.
        for held in said["members"].values():
            self.assertIsInstance(held["sidecars"], dict)
        # AND THE RETAINED TREES, bound by content manifest.
        for name in dossier_command.RETAINED:
            self.assertEqual(said["retained"][name]["state"], "present")
            self.assertEqual(said["retained"][name]["files"], 1)
            self.assertTrue(
                said["retained"][name]["content_digest"].startswith("sha256:"))

    def test_a_document_the_REAL_VALIDATOR_rejects_is_refused(self):
        """And it is refused in the validator's own words, so the consumer and
        the producer cannot disagree about what a selector is."""
        for drop in ("command", "state", "logs", "repository", "job_store",
                     "destination"):
            with self.subTest(drop=drop):
                held = dict(self.described)
                held.pop(drop)
                self.write(self.instance, json.dumps(held))
                _said, err = self.manifested(expect=2)
                self.assertIn("not a supported instance selector", err)
        self.rewrite()

    def test_a_selector_DISAGREEING_WITH_ITS_OWN_DESTINATION_is_refused(self):
        """Every path an instance owns is derived from its destination."""
        held = dict(self.described, job_store=os.path.join(self.root,
                                                           "elsewhere.sqlite3"))
        self.write(self.instance, json.dumps(held))
        _said, err = self.manifested(expect=2)
        self.assertIn("different deployment than its own destination", err)
        self.rewrite()

    def test_the_REQUIRED_retained_roots_cannot_be_declared_unconfigured(self):
        """Review P1: `not-configured` was a bypass. The contract requires
        state, logs and repository, so a manifest claiming one was never
        configured describes a selector the real validator rejects."""
        said, _err = self.manifested()
        said["retained"]["logs"] = {"state": "not-configured"}
        self.write(self.manifest, json.dumps(said))
        self.restore()
        shutil.rmtree(self.destination)
        shutil.rmtree(self.restored_at("logs"))
        code, out, err = self.checked()
        self.assertEqual(code, 2)
        held = json.loads(out)
        self.assertEqual(held["retained"]["logs"]["state"],
                         "not-configured-but-required")
        self.assertIn("retained:logs", held["faults"])

    def test_a_MISSING_PROVENANCE_member_refuses(self):
        os.remove(self.deployment)
        said, err = self.manifested(expect=2)
        self.assertIn("deployment", said["missing_members"])
        self.assertIn("partial set", err)

    def test_a_MISSING_STORE_refuses(self):
        os.remove(self.places["control_store"])
        said, err = self.manifested(expect=2)
        self.assertEqual(said["missing_members"], ["control_store"])
        self.assertIn("partial set", err)

    def test_a_store_that_is_NOT_THIS_INSTANCES_refuses(self):
        other = os.path.join(self.root, "other.sqlite3")
        Authority.create(other, authority_uuid=OTHER_UUID).dispose()
        # The layout owns where the authority store lives, so a store that is
        # not this instance's is reached by REPLACING it at that path.
        shutil.copyfile(other, self.store)
        _said, err = self.manifested(expect=2)
        self.assertIn("not its recovery set", err)

    # -- the check ---------------------------------------------------------

    def test_a_COMPLETE_restore_passes_and_still_admits_NOTHING(self):
        self.manifested()
        self.restore()
        code, out, err = self.checked()
        self.assertEqual(code, 2, err)
        # The ORIGINAL destination still exists in this fixture, so writer
        # uncertainty is correctly reported. Removing it is NOT the accounting.
        said = json.loads(out)
        self.assertEqual(said["faults"], [])
        self.assertTrue(said["schema_compatible"])
        self.assertTrue(said["writer_uncertainty"])
        self.assertTrue(said["operator_must_account_for_writers"])

    def test_a_clean_report_NEVER_claims_the_old_runtime_STOPPED(self):
        """Review P1: a destination directory disappearing is not proof that
        an old runtime stopped, and the first cut treated it as exactly that."""
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        code, out, err = self.checked()
        self.assertEqual(code, 0, err)
        said = json.loads(out)
        self.assertEqual(said["faults"], [])
        self.assertEqual(said["writer_uncertainty"], [])
        self.assertTrue(said["operator_must_account_for_writers"])
        self.assertEqual(said["writable_admission"][:11], "these check")
        self.assertIn("do NOT", said["writable_admission"])
        self.assertIn("no absence of a directory proves that",
                      said["writable_admission"])

    def test_a_SYNTHETIC_one_member_manifest_is_refused(self):
        """The reviewer's `one_member_recovery` reproduction, which returned 0
        with faults=[] and schema_compatible=true."""
        self.write(self.manifest, json.dumps({
            "schema": dossier_command.RECOVERY_SCHEMA,
            "destination": self.destination, "authority_uuid": UUID,
            "members": {"authority_store": {
                "path": self.store, "digest": "sha256:" + "0" * 64,
                "bytes": 1, "sidecars": {}}}}))
        os.makedirs(self.restored, exist_ok=True)
        code, out, err = self.checked()
        self.assertEqual(code, 2)
        said = json.loads(out)
        self.assertIn("job_store", said["faults"])
        self.assertIn("control_store", said["faults"])
        self.assertIn("provenance:deployment", said["faults"])
        self.assertFalse(said["schema_compatible"])
        self.assertEqual(said["writable_admission"], "refused")

    def test_a_manifest_that_RECORDED_MISSING_MEMBERS_is_refused_for_that(self):
        os.remove(self.deployment)
        said, _err = self.manifested(expect=2)
        self.write(self.manifest, json.dumps(said))
        self.restore()
        code, out, err = self.checked()
        self.assertEqual(code, 2)
        self.assertIn("never described a complete deployment", "".join(
            one for one in json.loads(out)["faults"]))

    def test_the_ROOT_is_honoured_WITHOUT_flat(self):
        """Before, `--root` was ignored unless `--flat` was given, so the
        ORIGINAL absolute paths were checked and a restore was never examined."""
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        code, out, err = self.checked()
        self.assertEqual(code, 0, err)
        said = json.loads(out)
        self.assertEqual(said["layout"], "as-recorded")
        for held in said["members"].values():
            self.assertTrue(held["path"].startswith(self.restored), held)

    def test_a_CHANGED_store_is_refused(self):
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        self.tamper(os.path.join(self.under("stores"), "jobs.sqlite3"))
        code, out, _err = self.checked()
        self.assertEqual(code, 2)
        self.assertIn("job_store", json.loads(out)["faults"])

    def test_a_CHANGED_PROVENANCE_document_is_refused(self):
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        self.tamper(self.under("deployment"),
                    '{"schema":"something.else/1"}')
        code, out, _err = self.checked()
        self.assertEqual(code, 2)
        self.assertIn("provenance:deployment", json.loads(out)["faults"])

    def test_CHANGED_RETAINED_evidence_is_refused(self):
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        self.tamper(os.path.join(self.under("logs"), "kept.txt"),
                    "rewritten\n")
        code, out, _err = self.checked()
        self.assertEqual(code, 2)
        self.assertIn("retained:logs", json.loads(out)["faults"])

    def test_REMOVED_RETAINED_evidence_is_refused(self):
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        shutil.rmtree(self.restored_at("state"))
        code, out, _err = self.checked()
        self.assertEqual(code, 2)
        self.assertIn("retained:state", json.loads(out)["faults"])

    def test_a_CHANGED_SIDECAR_is_refused(self):
        with open(self.store + "-wal", "wb") as handle:
            handle.write(b"\0" * 32)
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        self.tamper(self.under("authority_store") + "-wal", "different\n")
        code, out, _err = self.checked()
        self.assertEqual(code, 2)
        self.assertIn("authority_store", json.loads(out)["faults"])

    def test_a_sidecar_that_APPEARED_is_writer_uncertainty(self):
        """`-journal` rather than `-wal`: the manifest legitimately records a
        `-shm`/`-wal` that its own read-only identity read created, so the
        suffix that proves "something opened this since the cut" has to be one
        nothing in the manifest path touches."""
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        self.tamper(self.under("authority_store") + "-journal", "appeared\n")
        code, out, err = self.checked()
        self.assertEqual(code, 2)
        said = json.loads(out)
        # BOTH FACTS, and both are true of this restore. The journal is a
        # writer signal, AND a hot journal beside a WAL store is one SQLite
        # will not read -- so the identity cannot be established either.
        # Asserting only the first would have been a tidier case about a
        # store this program can no longer vouch for.
        self.assertTrue(any("-journal" in one
                            for one in said["writer_uncertainty"]))
        self.assertIn("stored-identity", said["faults"])
        self.assertIn("cannot be ruled out", err)
        self.assertEqual(said["writable_admission"], "refused")

    def test_a_restored_store_of_ANOTHER_AUTHORITY_is_refused(self):
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        other = os.path.join(self.root, "other.sqlite3")
        Authority.create(other, authority_uuid=OTHER_UUID).dispose()
        shutil.copyfile(other, os.path.join(self.restored,
                                            "db/authority.sqlite3"))
        code, out, _err = self.checked()
        self.assertEqual(code, 2)
        said = json.loads(out)
        self.assertIn("authority_store", said["faults"])
        self.assertIn("stored-identity", said["faults"])

    def test_COMPATIBILITY_is_the_STORED_version_not_this_builds_constant(self):
        """The correction review named: before, the manifest's recorded number
        was compared against the emitting build's own constant, so nothing
        ever looked inside the restored file."""
        import sqlite3

        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        place = self.restored_at("authority_store")
        connection = sqlite3.connect(place)
        connection.execute("UPDATE meta SET value = '5' "
                           "WHERE key = 'schema_version'")
        connection.commit()
        connection.close()
        code, out, err = self.checked()
        self.assertEqual(code, 2)
        said = json.loads(out)
        self.assertFalse(said["schema_compatible"])
        self.assertEqual(said["stored_identity"]["schema_version"], "5")
        self.assertEqual(said["build_speaks_schema_version"], SCHEMA_VERSION)
        self.assertIn("does not migrate", err)

    def test_a_document_that_is_not_a_recovery_set_is_refused(self):
        self.write(self.manifest, json.dumps({"schema": "something.else/1"}))
        os.makedirs(self.restored, exist_ok=True)
        code, _out, err = self.checked()
        self.assertEqual(code, 2)
        self.assertIn(dossier_command.RECOVERY_SCHEMA, err)

    def test_an_OMITTED_retained_axis_is_refused_not_believed(self):
        """Review P1's second reproduction: deleting `retained` from a /2
        manifest and every restored tree with it returned 0 with faults=[],
        retained={} and a clean-set report."""
        said, _err = self.manifested()
        said.pop("retained", None)
        said.pop("required_retained", None)
        self.write(self.manifest, json.dumps(said))
        self.restore()
        shutil.rmtree(self.destination)
        for name in dossier_command.RETAINED:
            shutil.rmtree(self.restored_at(name))
        code, out, err = self.checked()
        self.assertEqual(code, 2)
        held = json.loads(out)
        for name in dossier_command.RETAINED:
            self.assertIn(f"retained:{name}", held["faults"])
        self.assertIn("required retained roots", " ".join(held["faults"]))
        self.assertEqual(held["writable_admission"], "refused")

    def test_a_manifest_CREATED_over_a_missing_retained_root_refuses(self):
        """And the refusal starts at manifest creation: an absent configured
        directory is not proof that nothing was retained."""
        shutil.rmtree(self.places["logs"])
        said, err = self.manifested(expect=2)
        self.assertIn("retained:logs", said["missing_members"])
        self.assertIn("partial set", err)

    @unittest.skipIf(os.getuid() == 0, "root bypasses the mode bits")
    def test_an_UNREADABLE_retained_subtree_is_not_a_complete_tree(self):
        """`os.walk` without an error handler silently skips what it cannot
        read, so an unreadable subtree used to shrink the manifest and still
        be called complete."""
        closed = os.path.join(self.places["state"], "closed")
        self.write(os.path.join(closed, "kept.txt"), "deep\n")
        os.chmod(closed, 0)
        self.addCleanup(os.chmod, closed, stat.S_IRWXU)
        said, err = self.manifested(expect=2)
        self.assertEqual(said["retained"]["state"]["state"], "unreadable")
        self.assertTrue(said["retained"]["state"]["unreadable"])
        self.assertIn("retained:state", said["missing_members"])

    def test_a_DIRECTORY_SYMLINK_in_a_retained_tree_is_bound(self):
        """It appears in `directories`, never in `names`, so the previous walk
        did not record it at all despite claiming to."""
        os.symlink(self.root, os.path.join(self.places["logs"], "away"))
        said, _err = self.manifested()
        self.assertIn("away", said["retained"]["logs"]["symlinks"])

    def test_the_restored_set_is_RE_READ_after_the_identity_probe(self):
        """Review P1: the probe ran after the digests were reported, so a check
        could modify the set it had just certified. The probe reads a COPY and
        this proves the originals are untouched."""
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        before = {name: os.path.getmtime(
            os.path.join(self.restored, self.under("stores"), name))
            for name in ("authority.sqlite3", "jobs.sqlite3")}
        code, out, err = self.checked()
        self.assertEqual(code, 0, err)
        held = json.loads(out)["unchanged_after_observation"]
        for name in dossier_command.STORES:
            self.assertTrue(held[name]["digest_unchanged"], held[name])
            self.assertEqual(held[name]["sidecars_now"],
                             held[name]["sidecars_at_cut"])
        for name, when in before.items():
            self.assertEqual(os.path.getmtime(
                os.path.join(self.restored, self.under("stores"), name)), when)

    def test_the_identity_probe_uses_the_SUPPORTED_authority_surface(self):
        """Not raw SQL: `Authority.stored_identity` is the authority's own
        read-only probe, the one `open` itself uses before it decides."""
        self.assertEqual(
            Authority.stored_identity(self.store)["store_kind"], STORE_KIND)
        self.assertIsNone(Authority.stored_identity(
            self.write(os.path.join(self.root, "prose.txt"), "not a store\n")))

    def test_the_RESTORED_authority_still_answers_record_and_history(self):
        """Readback is acceptance."""
        self.manifested()
        self.restore()
        shutil.rmtree(self.destination)
        self.assertEqual(self.checked()[0], 0)
        authority = Authority.open(
            self.restored_at("authority_store"),
            expected_authority_uuid=UUID)
        self.addCleanup(authority.dispose)
        work = UUID[:8] + "-W1"
        self.assertEqual(authority.dossier_of(work)["locator"], LOCATOR)
        self.assertEqual(authority.work_creation(work)["operation_id"],
                         "op-create")
        self.assertIsNotNone(authority.operation_record("op-bind"))


if __name__ == "__main__":
    unittest.main()
