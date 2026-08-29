"""W6634 — the sealed result and the collection, on the adapter side.

`work/records/2026/08/finding-v12-sealed-output-credentials/`.

THE ACCEPTANCE, and every case below belongs to one of its lines:

  - output is read only after quiescence, and a replacement race is detected;
  - only DECLARED, bounded, regular files are collected -- missing, undeclared,
    linked, special, over-count and over-byte all refuse without leaving an
    accepted partial artifact;
  - the manifest/count/bytes/digest observation is measured rather than
    declared;
  - what this component produces is what the manager's own receivers accept.

WHAT IS NOT HERE: assignment-scoped credential delivery. `run_vector` composes
no environment and no secret, the sandbox is `--read-only` with one writable
mount, and §13 bars the value from argv, labels, logs, the durable store and
the collected output. The delivery surface has to be CHOSEN and stated in the
record before it is written, not discovered while writing it, and that question
is still open.
"""

import hashlib
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from baton_v12.contracts import ContractRefusal, held_secret
from baton_v12.contracts import digest as contract_digest
from baton_v12.worker_manager import sealing, workspaces
from baton_v12.worker_manager.oci import OciAdapter

NOW = "2026-08-26T00:00:00.000Z"
# HEX AND PREFIXED, because the worker's envelope is now validated against the
# frozen schema and §12's Work-reference rule -- a fixture identity that could
# not exist would be refused before it reached the rule a case aims at.
UUID = "0123456789abcdef0123456789abcdef"
JOB = f"{UUID[:8]}-W1"
WHO = "baton.claude"
DIGEST = "sha256:" + "a" * 64

ASSIGNMENT = {"work_ref": {"authority_uuid": UUID, "work_id": JOB},
              "participant": WHO, "generation": 1}
IDENTITY = {"image_digest": "sha256:" + "b" * 64, "profile_digest": DIGEST,
            "policy_digest": "sha256:" + "c" * 64,
            "adapter_digest": "sha256:" + "d" * 64}


def declaration(name="proposal", path="out", required=True,
                max_entries=100, max_bytes=1_048_576):
    return {"name": name, "type": "directory-result", "path": path,
            "required": required,
            "constraints": {"max_bytes": max_bytes,
                            "max_entries": max_entries,
                            "allowed_media_types": ["text/plain"],
                            "link_policy": "forbid", "validator_digest": None}}


class SealingCase(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="v12-sealing-")
        self.addCleanup(self._release)
        self.inputs = os.path.join(self.root, "inputs")
        self.workspace = os.path.join(self.root, "workspace")
        for place in (self.inputs, self.workspace):
            os.makedirs(place, exist_ok=True)
        self.listed = []
        self.observed = {"state": "quiescent", "why": "nothing is running"}

    def _release(self):
        """Sealing makes trees read-only ON PURPOSE, so cleanup has to undo
        that before it can remove them -- the same duty
        `workspaces.discard_workspace` performs for the manager."""
        for base, directories, files in os.walk(self.root, topdown=False):
            for one in directories:
                os.chmod(os.path.join(base, one), 0o700)
            for one in files:
                full = os.path.join(base, one)
                # NOT THROUGH A LINK. `os.chmod` follows one, and a case that
                # plants a link to `/etc/passwd` would have its CLEANUP try to
                # chmod that -- which is how this fixture first reported a
                # PermissionError as if the module had failed.
                if not os.path.islink(full):
                    os.chmod(full, 0o600)
        os.chmod(self.root, 0o700)

    def found(self, needle):
        """Every regular file under this case's root holding `needle`.

        Cases about material that must not be copied ask the filesystem rather
        than a path they had to be told: an assertion about one location passes
        for a copy that landed in another.
        """
        out = []
        for base, _directories, files in os.walk(self.root):
            for one in sorted(files):
                full = os.path.join(base, one)
                if os.path.islink(full) or not os.path.isfile(full):
                    continue
                with open(full, "rb") as reading:
                    if needle in reading.read():
                        out.append(full)
        return sorted(out)

    def wrote(self, files, into="out"):
        place = os.path.join(self.workspace, into)
        for name, content in files.items():
            full = os.path.join(place, name)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "wb") as handle:
                handle.write(content)
        os.makedirs(place, exist_ok=True)
        return place

    def published(self, declarations=None, disposition="completed",
                  **overrides):
        """The WORKER's `/output/output.json`, as a worker would leave it.

        W6634 sixth review [P1]: this manager now OPENS the worker's envelope,
        owns it with W14251's settled validator, holds it against the
        declarations and recomputes its digest. So every case that drives a
        completed freeze has to have one -- which is the point: a completed
        result with no envelope is a completion nothing signalled, and one case
        below drives exactly that refusal.
        """
        declarations = [declaration()] if declarations is None else declarations
        answers = []
        for one in declarations:
            place = os.path.join(self.workspace, one["path"])
            answers.append({
                "name": one["name"], "type": one["type"], "path": one["path"],
                "status": ("present" if os.path.isdir(place)
                           else "missing-optional"),
                "content_manifest": (self.measured(place)
                                     if os.path.isdir(place) else None),
                "result_metadata": {}})
        body = {"version": {"major": 1, "minor": 0},
                "manifest_id": "completion-1", "created_at": NOW,
                "extensions": {},
                "schema": "baton.worker-manifest/completion",
                "assignment_ref": dict(ASSIGNMENT),
                "disposition": disposition, "outputs": answers}
        body.update(overrides)
        body["manifest_digest"] = contract_digest(body)
        place = os.path.join(self.workspace, "output.json")
        with open(place, "wb") as handle:
            handle.write(json.dumps(body, sort_keys=True).encode("utf-8"))
        return body

    @staticmethod
    def measured(place):
        """The content manifest of one tree, by §3.3's own rules.

        Computed here rather than asserted, because §12 rule 6 refuses a
        manifest whose aggregates do not match its entries -- so a fixture that
        guessed would be refused before it reached the rule a case aims at.
        """
        entries = []
        for base, _directories, files in os.walk(place):
            for one in sorted(files):
                full = os.path.join(base, one)
                with open(full, "rb") as reading:
                    content = reading.read()
                entries.append({
                    "path": os.path.relpath(full, place),
                    "bytes": len(content),
                    "content_digest": "sha256:" + hashlib.sha256(
                        content).hexdigest()})
        entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
        return {"entries": entries, "entry_count": len(entries),
                "total_bytes": sum(one["bytes"] for one in entries),
                "tree_digest": contract_digest(entries)}

    def adapter(self, outputs=None, publish=True, **overrides):
        """One adapter, with the worker's envelope already published.

        W6634 sixth review [P1]: the manager now VALIDATES
        `/output/output.json` before it freezes, so an adapter built for a
        completed freeze needs one -- and publishing it here rather than in
        every case keeps the envelope agreeing with whatever that case
        declared. `publish=False` is how the cases about a MISSING or
        disagreeing envelope drive their own.
        """
        case = self
        declarations = [declaration()] if outputs is None else outputs
        if publish and declarations:
            self.published(declarations)

        class Engine:
            def __call__(self, argv):
                return {"status": 0, "stdout": "[]", "stderr": ""}

        built = OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution",
            outputs=[declaration()] if outputs is None else outputs,
            input_manifest_digest=DIGEST, **overrides)
        built.list = lambda request: case.listed
        built.observe = lambda runtime_id: case.observed
        return built

    def request(self, **overrides):
        # `now` comes from the MANAGER: the adapter has no clock, because
        # `clock` is an injected capability with exactly one crossing -- the
        # control store's -- and a second would give one capability two owners.
        body = {"attempt_id": "attempt-1", "assignment": dict(ASSIGNMENT),
                # W16823: the seal proves quiescence by SELECTING this
                # attempt's runtimes, and the selector is the whole label set.
                "context": {"principal": "principal:org-a",
                            "effective_scope": "scope:deployment"},
                "disposition": "completed", "now": NOW,
                "operation": {"operation_id": "output.freeze:1",
                              "signature_digest": DIGEST}}
        body.update(overrides)
        return body


class NothingIsSealedWhileSomethingMayStillBeWriting(SealingCase):

    def test_a_running_runtime_for_this_attempt_stops_the_seal(self):
        """The manager proves quiescence from the durable AXIS. This asks the
        engine, because the axis is about observations and this is about a
        filesystem somebody may still be writing into."""
        self.wrote({"report.md": b"done"})
        self.listed = [{"runtime_id": "runtime-1"}]
        self.observed = {"state": "running", "why": "still going"}
        with self.assertRaises(ContractRefusal) as caught:
            self.adapter().seal(self.request())
        self.assertEqual(caught.exception.code, "quiescence-unknown")

    def test_an_uncertain_answer_is_not_a_quiet_one(self):
        """`uncertain` means this component could not read the engine, and a
        tree it cannot prove is quiet is a tree it will not seal."""
        self.wrote({"report.md": b"done"})
        self.listed = [{"runtime_id": "runtime-1"}]
        self.observed = {"state": "uncertain", "why": "the engine refused"}
        with self.assertRaises(ContractRefusal):
            self.adapter().seal(self.request())

    def test_an_absent_or_quiescent_runtime_seals(self):
        self.wrote({"report.md": b"done"})
        for state in ("absent", "quiescent"):
            with self.subTest(state=state):
                self.listed = [{"runtime_id": "runtime-1"}]
                self.observed = {"state": state, "why": "gone"}
                sealed = self.adapter().seal(self.request())
                self.assertEqual(sealed["disposition"], "completed")


class OnlyWhatWasDeclaredIsCollected(SealingCase):

    def test_the_result_answers_every_declaration_and_nothing_else(self):
        self.wrote({"report.md": b"done"})
        # An undeclared tree beside it: written, and never collected.
        self.wrote({"secret.txt": b"nobody asked"}, into="scratch")
        sealed = self.adapter().seal(self.request())
        self.assertEqual([one["name"] for one in sealed["outputs"]],
                         ["proposal"])
        self.assertEqual(sealed["outputs"][0]["status"], "present")

    def test_a_required_output_that_is_not_there_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.adapter().seal(self.request())
        self.assertEqual(caught.exception.code, "precondition")

    def test_an_optional_output_that_is_not_there_is_answered(self):
        """`missing-optional` is an ANSWER, not silence. The declaration was
        made and a receiver that saw nothing would lose the fact that the
        worker was asked."""
        sealed = self.adapter(
            outputs=[declaration(required=False)]).seal(self.request())
        answer = sealed["outputs"][0]
        self.assertEqual(answer["status"], "missing-optional")
        self.assertIsNone(answer["content_manifest"])
        self.assertIsNone(answer["artifact"])

    def test_a_declared_path_leaving_the_writable_root_is_refused(self):
        with self.assertRaises(ContractRefusal):
            self.adapter(outputs=[declaration(path="../escape")]).seal(
                self.request())

    def test_a_link_in_a_declared_output_is_not_a_regular_file(self):
        place = self.wrote({"report.md": b"done"})
        os.symlink("/etc/passwd", os.path.join(place, "elsewhere"))
        with self.assertRaises(ContractRefusal):
            self.adapter().seal(self.request())


class RetentionEnactsTheDispositionOverCustody(SealingCase):
    """W6636 review [P0]: `retain` reported delivery and discarded nothing.

    The first version validated the command and answered
    `{"delivered": True}` for every disposition, which I recorded as an
    unspecified retention semantics. It is not unspecified: the manager's own
    settlement rule says `complete` means nothing was kept, so an arc that
    discarded and then reported `complete` over surviving bytes was a FALSE
    CLEAN ENDING. W6629 decided the boundary already — `output.retain` goes to
    the side holding the material because retention decides what happens to it.
    """

    def collected(self, **overrides):
        body = {"attempt_id": "attempt-1", "assignment": dict(ASSIGNMENT),
                "result_id": "result-attempt-1",
                "output_names": ["proposal"],
                "result_manifest_digest": DIGEST,
                "operation": {"operation_id": "output.collect:1",
                              "signature_digest": DIGEST}}
        body.update(overrides)
        return body

    def held(self, **overrides):
        """One collected artifact, in custody, and the command about it."""
        self.wrote({"a.txt": b"one"})
        built = self.adapter()
        built.seal(self.request())
        collected = built.collect(self.collected())
        body = {"assignment_ref": dict(ASSIGNMENT),
                "runtime_attempt_id": "attempt-1",
                "artifact_ids": [one["artifact_id"]
                                 for one in collected["artifacts"]],
                "disposition": "discard-after-intake",
                "retention_policy_digest": DIGEST,
                "operation": {"operation_id": "output.retain:1",
                              "signature_digest": DIGEST}}
        body.update(overrides)
        return built, body, collected

    @staticmethod
    def place(built, name="proposal", attempt="attempt-1"):
        return os.path.join(built._custody(attempt), name)

    def test_discard_after_intake_removes_the_custody_bytes(self):
        built, command, _collected = self.held()
        self.assertTrue(os.path.isdir(self.place(built)))
        answer = built.retain(command)
        self.assertEqual(answer["discarded"], ["proposal"])
        # ABSENCE IS ESTABLISHED, not ordered: a removal that returned is not
        # evidence that anything is gone, which is the rule every other ending
        # in this adapter is held to.
        self.assertFalse(os.path.exists(self.place(built)))

    def test_retain_and_quarantine_keep_the_bytes(self):
        """`retain` is policy keeping them and `quarantine` is doubt keeping
        them. Both are reasons the material must still be there."""
        for disposition in ("retain", "quarantine"):
            built, command, _collected = self.held(disposition=disposition)
            answer = built.retain(command)
            self.assertEqual(answer["discarded"], [], disposition)
            self.assertTrue(os.path.isdir(self.place(built)), disposition)

    def test_only_the_named_artifacts_are_discarded(self):
        """A subset decision acts on the subset. Retention is per artifact,
        and a discard that took the whole custody home would be deciding about
        material nobody ruled on."""
        self.wrote({"a.txt": b"one"})
        self.wrote({"b.txt": b"two"}, into="second")
        outputs = [declaration(), declaration(name="evidence",
                                              path="second")]
        built = self.adapter(outputs=outputs)
        built.seal(self.request())
        built.collect(self.collected(output_names=["proposal", "evidence"]))
        self.assertTrue(os.path.isdir(self.place(built, "evidence")))

        answer = built.retain({
            "assignment_ref": dict(ASSIGNMENT),
            "runtime_attempt_id": "attempt-1",
            "artifact_ids": ["attempt-1:proposal"],
            "disposition": "discard-after-intake",
            "retention_policy_digest": DIGEST})
        self.assertEqual(answer["discarded"], ["proposal"])
        self.assertFalse(os.path.exists(self.place(built, "proposal")))
        self.assertTrue(os.path.isdir(self.place(built, "evidence")))

    def test_an_exact_retry_is_idempotent(self):
        """The manager delivers this BEFORE its own journal, so a crash
        between the two makes the next authorization repeat it. An
        already-absent tree is the state that was asked for."""
        built, command, _collected = self.held()
        built.retain(command)
        again = built.retain(command)
        self.assertEqual(again["discarded"], ["proposal"])
        self.assertFalse(os.path.exists(self.place(built)))

    def test_another_attempts_artifact_is_refused(self):
        """The identity is `attempt:name` and the tree is DERIVED from it, so
        a cross-attempt identity is refused rather than resolved — otherwise
        one attempt's retention reaches another's material."""
        built, command, _collected = self.held(
            artifact_ids=["attempt-2:proposal"])
        with self.assertRaises(ContractRefusal) as caught:
            built.retain(command)
        self.assertIn("not this attempt's", str(caught.exception))
        self.assertTrue(os.path.isdir(self.place(built)))

    def test_an_undeclared_output_is_refused(self):
        built, command, _collected = self.held(
            artifact_ids=["attempt-1:invented"])
        with self.assertRaises(ContractRefusal) as caught:
            built.retain(command)
        self.assertIn("does not declare", str(caught.exception))
        self.assertTrue(os.path.isdir(self.place(built)))

    def test_an_identity_that_is_a_path_is_refused(self):
        """THE ONE THAT MATTERS. A caller-selected locator is exactly what
        deriving the path from the identity exists to prevent."""
        for invented in ("../../etc", "/etc/passwd", "attempt-1:../secret",
                         "proposal"):
            built, command, _collected = self.held(
                artifact_ids=[invented])
            with self.assertRaises(ContractRefusal):
                built.retain(command)
            self.assertTrue(os.path.isdir(self.place(built)), invented)

    def test_an_unknown_disposition_never_reaches_the_filesystem(self):
        """Re-review [P1]: this branched on membership of the KEEPING pair and
        let everything else fall through to the discard, so a typo or a value
        from a later vocabulary removed the material and reported success.

        An adapter boundary that owns a destructive command may not make
        unknown mean delete. The check runs before the names are resolved, let
        alone before anything is removed.
        """
        for invented in ("not-a-retention-disposition", "discard", "keep",
                         "Retain"):
            built, command, _collected = self.held(disposition=invented)
            with self.assertRaises(ContractRefusal) as caught:
                built.retain(command)
            self.assertIn("is not a retention disposition",
                          str(caught.exception), invented)
            self.assertTrue(os.path.isdir(self.place(built)), invented)

    def test_a_disposition_that_is_not_text_refuses_before_the_vocabulary(
            self):
        """The empty string and a non-string are refused one guard EARLIER, by
        the member's own owner. Named separately rather than folded in, because
        asserting the vocabulary message over them would be asserting a
        refusal that never runs."""
        for invented in ("", 5, None, ["retain"]):
            built, command, _collected = self.held(disposition=invented)
            with self.assertRaises(ContractRefusal) as caught:
                built.retain(command)
            self.assertIn("a retention disposition", str(caught.exception))
            self.assertTrue(os.path.isdir(self.place(built)), invented)

    def test_a_keep_over_absent_custody_refuses(self):
        """Re-review [P0]: the keep branch returned WITHOUT LOOKING.

        Custody that vanished between intake and retention was journalled as
        kept, and cleanup then derived `retained` -- whose whole meaning is
        that the material is still there. That is the keep-side twin of the
        false `complete` the previous review found: an ending reported over
        bytes nobody saw.

        The refusal lands BEFORE the manager journals the decision, which is
        what makes it actionable rather than a second wrong record.
        """
        self.keep_over_absent_custody("retain")

    def test_a_quarantine_over_absent_custody_refuses(self):
        """The other keep disposition, in its OWN case.

        Not a loop: the first pass removes the custody tree, and a second
        `held()` in the same fixture then collects NOTHING -- `collected_result`
        skips a name whose tree is absent -- so the second disposition would
        have been checked with an empty artifact list and passed vacuously.
        Measured: it did, until this was split.
        """
        self.keep_over_absent_custody("quarantine")

    def keep_over_absent_custody(self, disposition):
        built, command, _collected = self.held(disposition=disposition)
        workspaces.discard_tree(self.place(built))
        self.assertFalse(os.path.exists(self.place(built)))
        with self.assertRaises(ContractRefusal) as caught:
            built.retain(command)
        self.assertIn("custody tree is not there", str(caught.exception),
                      disposition)

    def test_a_keep_over_present_custody_still_succeeds(self):
        """The guard is about ABSENCE, not about keeping being hard. The
        ordinary keep is unchanged, which is what stops the new refusal from
        being a regression dressed as a correction."""
        for disposition in ("retain", "quarantine"):
            built, command, _collected = self.held(disposition=disposition)
            answer = built.retain(command)
            self.assertEqual(answer["discarded"], [], disposition)
            self.assertTrue(os.path.isdir(self.place(built)), disposition)

    def test_a_retention_that_cannot_prove_absence_refuses(self):
        """A discard that returned is not a discard. Measured by making the
        removal vacuous: the answer has to come from the filesystem."""
        built, command, _collected = self.held()
        from baton_v12.worker_manager import oci as _oci
        with patch.object(_oci.workspaces, "discard_tree",
                          lambda place: True):
            with self.assertRaises(ContractRefusal) as caught:
                built.retain(command)
        self.assertIn("still present after removal", str(caught.exception))


class ALimitIsARefusalRatherThanATruncation(SealingCase):

    def test_more_entries_than_the_declaration_allows_refuses(self):
        self.wrote({f"file-{index:03d}.txt": b"x" for index in range(4)})
        with self.assertRaises(ContractRefusal) as caught:
            self.adapter(outputs=[declaration(max_entries=3)]).seal(
                self.request())
        self.assertEqual(caught.exception.code, "limit")

    def test_more_bytes_than_the_declaration_allows_refuses(self):
        self.wrote({"big.bin": b"x" * 64})
        with self.assertRaises(ContractRefusal) as caught:
            self.adapter(outputs=[declaration(max_bytes=16)]).seal(
                self.request())
        self.assertEqual(caught.exception.code, "limit")

    def test_nothing_partial_is_accepted_when_a_limit_refuses(self):
        """A refusal is not a smaller result. The whole seal fails, so no
        receiver ever sees an artifact this component decided to trim."""
        self.wrote({"big.bin": b"x" * 64})
        with self.assertRaises(ContractRefusal):
            self.adapter(outputs=[declaration(max_bytes=16)]).seal(
                self.request())


class TheObservationIsMeasuredRatherThanDeclared(SealingCase):

    def test_the_manifest_counts_and_digests_what_is_actually_there(self):
        self.wrote({"a.txt": b"one", "b.txt": b"two!"})
        sealed = self.adapter().seal(self.request())
        manifest = sealed["outputs"][0]["content_manifest"]
        self.assertEqual(manifest["entry_count"], 2)
        self.assertEqual(manifest["total_bytes"], 7)
        self.assertEqual(sorted(one["path"] for one in manifest["entries"]),
                         ["a.txt", "b.txt"])
        self.assertEqual(sealed["outputs"][0]["artifact"]["content_digest"],
                         manifest["tree_digest"])

    def test_the_custody_copy_is_read_only_afterwards(self):
        """W6634 review [P1]: what is frozen is the manager's COPY, not the
        worker's tree. Freezing the workspace in place left the observation
        over a path the worker still owns -- and the live tree is deliberately
        left alone now, because custody is what the result describes."""
        self.wrote({"a.txt": b"one"})
        sealed = self.adapter().seal(self.request())
        held = sealed["outputs"][0]["artifact"]["locator"][len("file://"):]
        self.assertFalse(os.access(os.path.join(held, "a.txt"), os.W_OK))
        self.assertNotEqual(held, os.path.join(self.workspace, "out"))

    def test_a_tree_that_moves_during_the_pass_cannot_reach_custody(self):
        """REPLACED BY W26283, and the replacement asserts something stronger.

        This case used to drive a change BETWEEN two measurements and assert a
        `collection` refusal. That window no longer exists: staging measures
        and copies in ONE no-follow pass, so the bytes written are the bytes
        read from the descriptor that produced them and there is nothing to
        change in between. Asserting a refusal for an unreachable window would
        be asserting something false.

        What the old case was protecting -- custody never describes a tree that
        moved -- is now true by construction, so it is asserted directly: a
        worker that rewrites a file the instant after it is read does not get
        those bytes into custody, and does not get them into the sealed
        manifest either.

        The change is driven from the `admits` hook, which is the one moment
        the pass has content in hand, so it lands strictly after the read of
        `a.txt` and strictly before its write.
        """
        place = self.wrote({"a.txt": b"one"})
        built = self.adapter()
        original = sealing.workspaces.copied_manifest

        def racing(root, into, *, max_entries=None, max_bytes=None,
                   admits=None):
            def moving(relative, content):
                if admits is not None:
                    admits(relative, content)
                with open(os.path.join(place, relative), "wb") as handle:
                    handle.write(b"CHANGED-AFTER-THE-READ")
            return original(root, into, max_entries=max_entries,
                            max_bytes=max_bytes, admits=moving)

        sealing.workspaces.copied_manifest = racing
        try:
            sealed = built.seal(self.request())
        finally:
            sealing.workspaces.copied_manifest = original

        held = sealed["outputs"][0]["artifact"]["locator"][len("file://"):]
        with open(os.path.join(held, "a.txt"), "rb") as reading:
            self.assertEqual(reading.read(), b"one")
        manifest = sealed["outputs"][0]["content_manifest"]
        self.assertEqual(manifest["total_bytes"], 3)
        # The live tree really did move, or this proves nothing.
        with open(os.path.join(place, "a.txt"), "rb") as reading:
            self.assertEqual(reading.read(), b"CHANGED-AFTER-THE-READ")

    def test_a_live_secret_in_an_output_never_reaches_custody(self):
        """W26283: the acceptance says live-secret BYTES fail closed, and
        nothing established it.

        The scan was here in the provisional code and no case drove it -- the
        mutation pass found that by replacing it with a no-op and watching
        every suite still pass. A guard nothing observes is not established,
        whatever the comment beside it says.

        A worker that writes its own bearer into the output it produces puts
        that value somewhere no walk of a manager-composed DOCUMENT has ever
        looked, which is why the rule is over the artifact's own content.
        """
        bearer = "live-bearer-value-nobody-may-publish"
        place = self.wrote({"a.txt": b"harmless"})
        built = self.adapter()
        with open(os.path.join(place, "leaked.txt"), "wb") as handle:
            handle.write(f"token={bearer}\n".encode("utf-8"))
        with held_secret(bearer):
            with self.assertRaises(ContractRefusal) as caught:
                built.seal(self.request())
        # `integrity/secret` is §13's own pairing, which the contracts layer
        # owns; asserted exactly rather than as "some refusal", so a later
        # change that refused for an unrelated reason would not pass here.
        self.assertEqual(caught.exception.category, "integrity")
        self.assertEqual(caught.exception.code, "secret-leak")
        # AND THE BYTES ARE NOT IN CUSTODY. Refusing after copying would be
        # objecting to material this manager had already taken.
        self.assertEqual(self.found(bearer.encode("utf-8")),
                         [os.path.join(place, "leaked.txt")])

    def test_the_same_bytes_seal_once_the_secret_is_no_longer_live(self):
        """The rule is about a LIVE registration, not about the characters.

        Without this the refusal above would be satisfied by a component that
        refused the string forever -- which would make a retired bearer's
        text permanently unpublishable and the registry pointless.
        """
        retired = "retired-bearer-value"
        place = self.wrote({"a.txt": b"harmless"})
        built = self.adapter()
        with open(os.path.join(place, "mentions.txt"), "wb") as handle:
            handle.write(f"token={retired}\n".encode("utf-8"))
        with held_secret(retired):
            with self.assertRaises(ContractRefusal):
                built.seal(self.request())
        # The registration is released; the same bytes now seal.
        rebuilt = self.adapter()
        sealed = rebuilt.seal(self.request())
        self.assertEqual(sealed["disposition"], "completed")

    def test_custody_that_disagrees_with_the_copy_refuses(self):
        """The write is VERIFIED, and the collaborator is what is faked.

        After the single-pass redesign nothing a worker does can make the
        copy's manifest disagree with custody -- which is the point. What the
        check still defends against is the copy being WRONG ABOUT ITSELF: a
        short write, a full device, a truncated file. That is a fault in
        `copied_manifest`, not in the tree, so the honest way to drive it is
        to make `copied_manifest` return a manifest that does not describe
        what it wrote. Faking the boundary this layer does not own is not the
        same as faking the code under test.
        """
        self.wrote({"a.txt": b"one"})
        built = self.adapter()
        original = sealing.workspaces.copied_manifest

        def lying(root, into, **rest):
            answer = original(root, into, **rest)
            return {**answer, "tree_digest": "sha256:" + "0" * 64}

        sealing.workspaces.copied_manifest = lying
        try:
            with self.assertRaises(ContractRefusal) as caught:
                built.seal(self.request())
        finally:
            sealing.workspaces.copied_manifest = original
        self.assertEqual(caught.exception.code, "digest")


    def test_a_path_replaced_after_it_was_listed_never_reaches_custody(self):
        """W26283 [P1], driven rather than argued.

        Staging used to reopen every measured path with a plain `open`, which
        resolves the whole path string a second time. A measured subdirectory
        replaced by a symbolic link therefore put material from OUTSIDE the
        workspace into manager custody. The single no-follow pass refuses the
        link where it finds it, and custody stays empty.
        """
        place = self.wrote({"deep/a.txt": b"legitimate"})
        # THE ADAPTER IS BUILT FIRST, and that is the honest order rather than
        # a fixture convenience: the worker completes and publishes its
        # envelope over a legitimate tree, and only then does the tree change.
        # Tampering first would make the FIXTURE refuse while measuring, and
        # the case would prove nothing about the freeze.
        built = self.adapter()
        outside = os.path.join(self.root, "elsewhere")
        os.makedirs(outside)
        with open(os.path.join(outside, "a.txt"), "wb") as handle:
            handle.write(b"HOST MATERIAL")
        os.rename(os.path.join(place, "deep"),
                  os.path.join(self.root, "deep-real"))
        os.symlink(outside, os.path.join(place, "deep"))

        with self.assertRaises(ContractRefusal) as caught:
            built.seal(self.request())
        self.assertIn("symbolic link", str(caught.exception))
        # ASKED OF THE FILESYSTEM, not of the custody path this case would
        # otherwise have to know: nowhere outside the directory that legitimately
        # holds it does the host material exist. A path assertion would pass for
        # a copy that landed somewhere else.
        self.assertEqual(self.found(b"HOST MATERIAL"),
                         [os.path.join(outside, "a.txt")])

    def test_a_named_pipe_where_a_file_was_does_not_hang_the_manager(self):
        """W26283 [P1]: the other half of the same defect.

        A plain `open` on a FIFO blocks until somebody writes, so one `mkfifo`
        stalled the freeze indefinitely -- the failure `_read_without_following`
        added `O_NONBLOCK` to prevent for `output.json`, reintroduced one
        function away. The walk refuses a non-regular file where it lists it,
        so the open never happens.

        Bounded by the suite rather than by hope: an unbounded hang would show
        as this case never finishing, so the assertion is that it returns at
        all AND refuses for the right reason.
        """
        place = self.wrote({"a.txt": b"one"})
        # BUILT BEFORE THE PIPE EXISTS. `published` measures the tree to
        # compose the worker's envelope, so creating the FIFO first hangs the
        # FIXTURE -- which is the same defect one layer out, and worth naming:
        # a plain read of a worker-owned tree blocks wherever it happens.
        built = self.adapter()
        os.unlink(os.path.join(place, "a.txt"))
        os.mkfifo(os.path.join(place, "a.txt"))
        with self.assertRaises(ContractRefusal) as caught:
            built.seal(self.request())
        self.assertIn("neither a regular file nor a directory",
                      str(caught.exception))


class TheCollectionAnswersTheFreezeRatherThanReMeasuringIt(SealingCase):

    def collected(self, **overrides):
        body = {"attempt_id": "attempt-1", "assignment": dict(ASSIGNMENT),
                "result_id": "result-attempt-1",
                "output_names": ["proposal"],
                "result_manifest_digest": DIGEST,
                "operation": {"operation_id": "output.collect:1",
                              "signature_digest": DIGEST}}
        body.update(overrides)
        return body

    def test_the_collection_names_what_the_freeze_recorded(self):
        self.wrote({"a.txt": b"one"})
        built = self.adapter()
        sealed = built.seal(self.request())
        answer = built.collect(self.collected())
        self.assertEqual(answer["result_id"], "result-attempt-1")
        self.assertEqual(len(answer["artifacts"]), 1)
        artifact = answer["artifacts"][0]
        frozen = sealed["outputs"][0]["artifact"]
        # The three members intake COMPARES against the freeze.
        self.assertEqual(artifact["artifact_id"], frozen["artifact_id"])
        self.assertEqual(artifact["content_digest"], frozen["content_digest"])
        self.assertEqual(artifact["bytes"], frozen["bytes"])
        # And the one it adopts.
        self.assertIn("custody_locator", artifact)

    def test_collection_uses_immutable_custody_not_the_live_workspace(self):
        place = self.wrote({"a.txt": b"one"})
        built = self.adapter()
        sealed = built.seal(self.request())
        frozen = sealed["outputs"][0]["artifact"]

        # Sealing has to copy the bytes into manager-owned immutable custody.
        # A later writer with host authority over the assignment workspace
        # must not be able to change what collection returns.
        os.chmod(place, 0o700)
        target = os.path.join(place, "a.txt")
        os.chmod(target, 0o600)
        with open(target, "wb") as handle:
            handle.write(b"CHANGED")

        artifact = built.collect(self.collected())["artifacts"][0]
        self.assertEqual(artifact["content_digest"],
                         frozen["content_digest"])
        self.assertEqual(artifact["bytes"], frozen["bytes"])
        self.assertNotEqual(artifact["custody_locator"], f"file://{place}")

    def test_an_exact_seal_retry_replays_custody_without_the_workspace(self):
        """W6634 accepts restart/retry by manager operation and artifact
        identity. Once the first seal has immutable custody, an exact retry is
        a fact about that settled identity and must not depend on worker-owned
        bytes still existing today."""
        place = self.wrote({"a.txt": b"one"})
        built = self.adapter()
        first = built.seal(self.request())

        os.remove(os.path.join(place, "a.txt"))
        os.rmdir(place)

        replay = built.seal(self.request())
        self.assertEqual(replay, first)

    def test_an_exact_retry_does_not_need_the_worker_envelope_again(self):
        """The manager receipt already binds the validated envelope digest.

        Worker-owned `/output/output.json` may be removed with the writable
        assignment root after settlement. Exact replay must consult the
        committed receipt before requiring that transient completion signal
        again; otherwise immutable custody is not actually restartable.
        """
        self.wrote({"a.txt": b"one"})
        built = self.adapter()
        first = built.seal(self.request())

        os.remove(os.path.join(self.workspace, "output.json"))

        replay = built.seal(self.request())
        self.assertEqual(replay, first)

    def test_a_partial_custody_directory_is_not_a_settled_replay(self):
        """Directory existence is not proof that staging committed.

        A process can stop after creating custody and copying only part of the
        measured tree. Restart must not publish that prefix as though the
        operation had settled; it must either finish from the complete live
        output or refuse the ambiguous custody.
        """
        self.wrote({"a.txt": b"one", "b.txt": b"two"})
        built = self.adapter()
        partial = os.path.join(built._custody("attempt-1"), "proposal")
        os.makedirs(partial)
        with open(os.path.join(partial, "a.txt"), "wb") as handle:
            handle.write(b"one")

        sealed = built.seal(self.request())
        manifest = sealed["outputs"][0]["content_manifest"]
        self.assertEqual(manifest["entry_count"], 2)
        self.assertEqual([one["path"] for one in manifest["entries"]],
                         ["a.txt", "b.txt"])

    def test_a_frozen_custody_without_its_record_is_re_staged(self):
        """The window between freezing custody and publishing the record.

        Staging freezes each output as it completes and the settled record is
        published LAST, so a process can stop with custody complete and frozen
        and no record naming it. Restart has no committed answer to replay, so
        it stages again -- into a tree that is now read-only.

        Measured: without the reopen in `_staged` this raises `PermissionError`
        rather than sealing. It is the one path that reaches that code, and it
        was written before any case drove it.
        """
        self.wrote({"a.txt": b"one"})
        built = self.adapter()
        first = built.seal(self.request())
        # Exactly the interrupted state: custody frozen, record gone.
        os.remove(os.path.join(built._custody("attempt-1"), "sealed.json"))
        again = built.seal(self.request())
        self.assertEqual(again["outputs"][0]["content_manifest"],
                         first["outputs"][0]["content_manifest"])

    def test_an_exact_retry_preserves_a_missing_optional_answer(self):
        """A missing output is a settled answer even though it has no tree.

        Custody keyed only by artifact directories has no marker for that
        answer, so consulting today's workspace can silently turn the same
        operation from missing into present.
        """
        built = self.adapter(outputs=[declaration(required=False)])
        first = built.seal(self.request())
        self.assertEqual(first["outputs"][0]["status"], "missing-optional")

        self.wrote({"late.txt": b"too late"})

        replay = built.seal(self.request())
        self.assertEqual(replay, first)

    def test_an_incomplete_committed_record_is_not_replay_evidence(self):
        """Publication is not atomic merely because it happens last.

        Opening the final record truncates or creates it before the bytes are
        complete. A stopped writer can therefore leave an existing empty or
        partial file, and restart must fail closed with a contract refusal or
        restage from the complete live output rather than leaking a decoder
        fault or adopting partial prose as a settled answer.
        """
        self.wrote({"a.txt": b"one"})
        built = self.adapter()
        custody = built._custody("attempt-1")
        os.makedirs(custody)
        with open(os.path.join(custody, "sealed.json"), "wb"):
            pass

        try:
            sealed = built.seal(self.request())
        except ContractRefusal:
            return
        self.assertEqual(sealed["outputs"][0]["content_manifest"]
                         ["entry_count"], 1)

    def test_the_receipt_binds_the_envelope_this_manager_validated(self):
        """W6634 sixth review [P1]. The digest is a MEASUREMENT this manager
        made over the bytes it read, not a caller's claim that a validation
        happened -- the adapter no longer takes one at all."""
        self.wrote({"a.txt": b"one"})
        envelope = self.published()
        sealed = self.adapter(publish=False).seal(self.request())
        self.assertEqual(sealed["completion_manifest_digest"],
                         envelope["manifest_digest"])
        self.assertEqual(sealed["schema"], "baton.worker-manifest/result")

    def test_a_completed_freeze_without_an_envelope_refuses(self):
        """The envelope IS the completion signal, so a completed result
        without one is a completion nothing signalled."""
        self.wrote({"a.txt": b"one"})
        with self.assertRaises(ContractRefusal) as caught:
            self.adapter(publish=False).seal(self.request())
        self.assertIn("output.json", caught.exception.message)

    def test_the_completion_signal_is_a_regular_file_in_the_output_root(self):
        """A worker-controlled link must not become a host-side read.

        The manager opens the container's fixed completion path from its host
        workspace. Following a symlink there lets the worker choose a path
        outside the writable root and substitute another assignment's valid
        envelope, even though declared payloads correctly forbid links.
        """
        self.wrote({"a.txt": b"one"})
        self.published()
        planted = os.path.join(self.inputs, "planted-completion.json")
        os.replace(os.path.join(self.workspace, "output.json"), planted)
        os.symlink(planted, os.path.join(self.workspace, "output.json"))

        with self.assertRaises(ContractRefusal):
            self.adapter(publish=False).seal(self.request())

    def test_an_unfinished_ending_needs_no_envelope(self):
        """A worker that died before publishing published nothing to validate,
        and the manager still owes a receipt for what it froze."""
        self.wrote({"a.txt": b"one"})
        sealed = self.adapter(publish=False).seal(
            self.request(disposition="unable"))
        self.assertNotIn("completion_manifest_digest", sealed)

    def test_the_completion_signal_is_not_a_directory_or_a_special_file(self):
        """`O_NOFOLLOW` refuses a link; it does not refuse everything else a
        worker can put at that name.

        A directory opens read-only quite happily and a FIFO opens and then
        blocks, so the mode is proved on the OPENED DESCRIPTOR -- which is also
        why the check is there rather than on the path: nothing can be swapped
        between a check and a read that share one descriptor.
        """
        self.wrote({"a.txt": b"one"})
        place = os.path.join(self.workspace, "output.json")
        for what, make in (("a directory", lambda: os.mkdir(place)),
                           ("a named pipe", lambda: os.mkfifo(place))):
            with self.subTest(what=what):
                if os.path.exists(place):
                    (os.rmdir if os.path.isdir(place) else os.remove)(place)
                make()
                with self.assertRaises(ContractRefusal) as caught:
                    self.adapter(publish=False).seal(self.request())
                self.assertEqual(caught.exception.code, "file-type")

    def test_a_changed_envelope_is_not_an_operand_of_a_settled_freeze(self):
        """REVISED under the seventh review's explicit authority, because the
        rule it pinned was mine and it was wrong.

        I asserted that a receipt settled over one worker document refuses to
        replay under another. That reads well and it inverts the ordering this
        module has been corrected on three times: replay sits above every state
        read, and `/output/output.json` is worker state. An operation settled
        at the moment it was settled -- the receipt records WHICH envelope this
        manager validated, and the request that replays it does not carry one.
        A file that changed afterwards is not an operand of a committed
        operation, and treating it as one made an exact retry depend on a tree
        cleanup is entitled to remove.
        """
        self.wrote({"a.txt": b"one"})
        built = self.adapter(publish=False)
        first = self.published()
        settled = built.seal(self.request())
        self.assertEqual(settled["completion_manifest_digest"],
                         first["manifest_digest"])

        self.published(manifest_id="completion-2")
        self.assertEqual(built.seal(self.request()), settled)

    def test_the_envelope_is_held_against_the_exact_declarations(self):
        """§12 rule 15, which needs two documents and so cannot live in the
        validator that owns the envelope alone. Each of these is a document
        that is internally perfect and answers a different assignment."""
        self.wrote({"a.txt": b"one"})
        whole = declaration()
        answer = {"name": "proposal", "type": "directory-result",
                  "path": "out", "status": "present",
                  "content_manifest": self.measured(
                      os.path.join(self.workspace, "out")),
                  "result_metadata": {}}
        for what, outputs in (
                ("an undeclared answer",
                 [answer, dict(answer, name="invented", path="other")]),
                ("no answer at all", []),
                ("a differing type", [dict(answer, type="record-output")]),
                ("a differing path", [dict(answer, path="elsewhere")])):
            with self.subTest(what=what):
                self.published([whole], outputs=outputs)
                with self.assertRaises(ContractRefusal) as caught:
                    self.adapter(publish=False).seal(self.request())
                self.assertIn("§12 rule 15", caught.exception.message)

    def test_the_envelope_answers_this_exact_assignment(self):
        """A structurally valid completion for another generation is not the
        envelope for the input manifest and freeze request being settled."""
        self.wrote({"a.txt": b"one"})
        stale = {**ASSIGNMENT, "generation": 2}
        self.published(assignment_ref=stale)

        with self.assertRaises(ContractRefusal):
            self.adapter(publish=False).seal(self.request())

    def test_a_required_declaration_cannot_be_answered_missing(self):
        """Whether an output was required is this manager's declaration, and a
        worker that could answer it away would be settling its own attempt."""
        self.wrote({"a.txt": b"one"})
        self.published([declaration()], outputs=[
            {"name": "proposal", "type": "directory-result", "path": "out",
             "status": "missing-optional", "content_manifest": None,
             "result_metadata": {}}])
        with self.assertRaises(ContractRefusal) as caught:
            self.adapter(publish=False).seal(self.request())
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))

    def test_a_committed_record_whose_bytes_moved_is_not_evidence(self):
        """The record carries the digest of its own body, and replay re-derives
        it. Measured: the review's zero-byte case reaches the decoder guard and
        the non-exact operation reaches the binding, but NEITHER reaches this
        one -- a record that decodes, binds correctly and describes something
        other than what it says it describes is a third state, and it is the
        one that says whether the stored bytes are the published ones."""
        self.wrote({"a.txt": b"one"})
        built = self.adapter()
        settled = built.seal(self.request())
        record = os.path.join(built._custody("attempt-1"), "sealed.json")
        moved = dict(settled)
        moved["outputs"] = [dict(moved["outputs"][0], status="missing-optional")]
        with open(record, "wb") as handle:
            handle.write(json.dumps(moved, sort_keys=True).encode("utf-8"))

        with self.assertRaises(ContractRefusal):
            built.seal(self.request())

    def test_the_final_record_never_exists_before_its_bytes_do(self):
        """Publication is a RENAME, which is why an interrupted publish leaves
        no record rather than an empty one.

        This stops the process at the last possible instant -- the bytes are
        written and forced, and the act that makes them the answer does not
        happen. The final name must be absent afterwards, so restart sees no
        settled answer at all rather than one it cannot read.
        """
        self.wrote({"a.txt": b"one"})
        built = self.adapter()
        custody = built._custody("attempt-1")
        stopped = os.replace

        def stop(source, target):
            raise KeyboardInterrupt("stopped between the write and the rename")

        os.replace = stop
        try:
            with self.assertRaises(KeyboardInterrupt):
                built.seal(self.request())
        finally:
            os.replace = stopped
        self.assertFalse(os.path.exists(os.path.join(custody, "sealed.json")))

        # And the next attempt settles normally over the same custody.
        self.assertEqual(
            built.seal(self.request())["outputs"][0]["status"], "present")

    def test_replay_requires_the_same_freeze_operation(self):
        """A record under one attempt is not every operation's answer."""
        self.wrote({"a.txt": b"one"})
        built = self.adapter()
        built.seal(self.request())
        different = self.request(
            operation={"operation_id": "output.freeze:different",
                       "signature_digest": "sha256:" + "e" * 64})
        with self.assertRaises(ContractRefusal):
            built.seal(different)

    def test_an_undeclared_output_name_is_refused(self):
        self.wrote({"a.txt": b"one"})
        built = self.adapter()
        built.seal(self.request())
        with self.assertRaises(ContractRefusal):
            built.collect(self.collected(output_names=["invented"]))


class TheDeclarationsAreOwnedAtConstruction(SealingCase):

    def test_an_unreadable_declaration_refuses_before_any_freeze(self):
        """A declaration this adapter cannot read is a LAUNCH mistake. By
        freeze time a worker has already done the work against limits nobody
        could state, and refusing then would be refusing the wrong party."""
        for spoiled in ({"name": "x"},
                        declaration(max_entries="lots"),
                        declaration(required="yes")):
            with self.subTest(spoiled=spoiled):
                with self.assertRaises(ContractRefusal):
                    sealing.declared_outputs([spoiled])

    def test_one_name_is_declared_once(self):
        with self.assertRaises(ContractRefusal):
            sealing.declared_outputs([declaration(), declaration()])

    def test_two_names_cannot_alias_or_nest_the_same_output_tree(self):
        for second in ("out", "out/nested"):
            with self.subTest(second=second):
                with self.assertRaises(ContractRefusal):
                    sealing.declared_outputs([
                        declaration(name="first", path="out"),
                        declaration(name="second", path=second),
                    ])

    def test_output_paths_are_validated_at_construction(self):
        """A declaration is a launch-time boundary. Absolute, escaping and
        non-canonical paths refuse there rather than after a worker has already
        run or after sealing has begun mutating custody."""
        for path in ("../escape", "/absolute", "out/../other",
                     "out//nested", "out/./nested"):
            with self.subTest(path=path):
                with self.assertRaises(ContractRefusal):
                    sealing.declared_outputs([declaration(path=path)])

    def test_an_assignment_declaring_nothing_is_refused(self):
        with self.assertRaises(ContractRefusal):
            sealing.declared_outputs([])


if __name__ == "__main__":
    unittest.main()
