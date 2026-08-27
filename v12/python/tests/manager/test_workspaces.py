"""W6631 — the generic directory measurement and one private workspace per
assignment, as W15232 left them.

The acceptance this file answers to, from the bound records:

  deterministic manifest/digest vectors; symlink, hard-link/special-file,
  traversal, replacement-race and limit refusals that leave NO ACCEPTED
  PARTIAL WORKSPACE; concurrent assignments never share a writable workspace;
  cleanup concerns only what this component created, including the read-only
  trees it made read-only.

WHAT THIS FILE NO LONGER COVERS. W6631 also built source ACQUISITION here -- a
repository port and the operations that delivered a version-controlled or
copied source -- and W15232 removed it under the 2026-08-25 artifact-neutral
ruling: the Worker Manager receives an ALREADY STAGED read-only directory and
does not choose or execute an acquisition operation. Those cases went with the
behaviour, because a test of behaviour that no longer exists asserts nothing.

What stands in their place is `TheCoreManagerDoesNotAcquireSources`, which
asserts the ABSENCE: no acquisition operation on the module or the package, no
acquisition definition named in the module's code or as a string operand, no
acquisition-specific root, and the generic duties still present and callable.

The reasoning that was superseded lives in
`work/records/2026/08/finding-v12-artifact-neutral-source-stager/` and in
W6631's own record; it does not need to survive as this file's contract.
"""

import concurrent.futures
import json
import os
import pathlib
import tempfile
import unittest

# `check_content_manifest` stays in the TEST's imports and left the module's:
# checking a MEASURED manifest against the frozen `contentManifest` shape is a
# generic property of what this manager still produces. What went with the
# acquisition half was the module VALIDATING a claimed one it was handed.
from baton_v12.contracts import (ContractRefusal, check_content_manifest,
                                 digest)
from baton_v12.worker_manager import workspaces
from baton_v12.worker_manager.workspaces import (
    ASSIGNMENT_MANIFEST, INPUT_MANIFEST, MAX_DEPTH, MAX_ENTRIES,
    READ_ONLY_DIR, READ_ONLY_FILE, assignment_workspace, compose_input_root,
    directory_manifest, discard_workspace, read_input_root)

VECTORS = (pathlib.Path(__file__).resolve().parents[4] / "work" / "records"
           / "2026" / "08" / "finding-v12-isolated-agent-workers" / "findings"
           / "finding-v12-worker-contract" / "findings"
           / "finding-worker-control-api-manifests" / "evidence"
           / "vectors.json")



class Workspace(unittest.TestCase):

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-workspaces-")
        self.addCleanup(self._forcibly_remove, root)
        self.root = root.name
        self.storage = os.path.join(self.root, "storage")
        os.makedirs(self.storage)

    def _forcibly_remove(self, root):
        # The component delivers READ-ONLY trees on purpose, so the fixture
        # has to be able to take them away again.
        for current, directories, _ in os.walk(root.name):
            os.chmod(current, 0o700)
            for name in directories:
                os.chmod(os.path.join(current, name), 0o700)
        root.cleanup()

    def origin(self, files, name="origin"):
        place = os.path.join(self.root, name)
        for path, content in files.items():
            full = os.path.join(place, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "wb") as handle:
                handle.write(content)
        os.makedirs(place, exist_ok=True)
        return place

    def staged(self, origin, roots, destination="src"):
        """An ALREADY STAGED read-only input tree, put there by nobody.

        W15232: this used to build a `directorySource` descriptor and hand it
        to `materialize_directory_source`, which is the acquisition duty the
        artifact-neutral ruling moved out of this manager. What the manager
        receives now is the RESULT of that duty -- a read-only directory under
        its inputs root -- so the fixture produces the result directly rather
        than calling an operation that no longer exists.

        Deliberately not a helper that pretends to be a stager: it copies
        nothing this component would have to understand, and the tests using it
        are about cleanup and containment rather than about how bytes arrive.
        """
        into = os.path.join(roots["inputs"], destination)
        os.makedirs(into, exist_ok=True)
        for name in sorted(os.listdir(origin)):
            with open(os.path.join(origin, name), "rb") as handle:
                content = handle.read()
            place = os.path.join(into, name)
            with open(place, "wb") as handle:
                handle.write(content)
            os.chmod(place, READ_ONLY_FILE)
        os.chmod(into, READ_ONLY_DIR)
        return into

    def workspace(self, assignment="assignment-1"):
        return assignment_workspace(self.storage, assignment)

    def open_descriptors_below(self, root):
        """This process's live descriptors into one fixture tree."""
        target = os.path.realpath(root)
        found = 0
        for entry in os.listdir("/proc/self/fd"):
            try:
                opened = os.path.realpath(f"/proc/self/fd/{entry}")
            except OSError:
                continue
            if opened == target or opened.startswith(target + os.sep):
                found += 1
        return found


class AManifestIsMeasuredRatherThanDeclared(Workspace):

    def test_measuring_nested_directories_closes_every_descriptor(self):
        """Opened-directory identity is authority only while the walk runs."""
        origin = self.origin({"deep/deeper/a.txt": b"one"}, "descriptor-walk")
        before = self.open_descriptors_below(origin)
        directory_manifest(origin)
        self.assertEqual(self.open_descriptors_below(origin), before)

    def test_the_manifest_is_the_frozen_contracts_own_shape(self):
        origin = self.origin({"b.txt": b"two", "a/c.txt": b"three"})
        manifest = directory_manifest(origin)
        # It is not merely shaped like one: the exported §12 rule accepts it,
        # which is the same check every consumer of a manifest applies.
        self.assertEqual(check_content_manifest(manifest), manifest)
        self.assertEqual([entry["path"] for entry in manifest["entries"]],
                         ["a/c.txt", "b.txt"])
        self.assertEqual(manifest["entry_count"], 2)
        self.assertEqual(manifest["total_bytes"], 8)
        self.assertEqual(manifest["tree_digest"], digest(manifest["entries"]))

    def test_the_same_tree_measures_the_same_digest_twice_over(self):
        """DETERMINISTIC, and not merely stable within one process.

        The entries are sorted BYTEWISE rather than by whatever `sorted` does
        to text, because a manifest that recomputes differently under another
        collation is a manifest two conforming readers disagree about.
        """
        files = {"z.txt": b"z", "A.txt": b"A", "a/b.txt": b"b",
                 "é.txt": "e".encode("utf-8")}
        first = directory_manifest(self.origin(files, "one"))
        second = directory_manifest(self.origin(files, "two"))
        self.assertEqual(first, second)
        self.assertEqual([entry["path"] for entry in first["entries"]],
                         sorted((entry["path"] for entry in first["entries"]),
                                key=lambda path: path.encode("utf-8")))

    def test_an_empty_tree_is_a_manifest_and_not_a_refusal(self):
        manifest = directory_manifest(self.origin({}, "empty"))
        self.assertEqual(manifest["entry_count"], 0)
        self.assertEqual(manifest["total_bytes"], 0)
        self.assertEqual(check_content_manifest(manifest), manifest)


class NothingButRegularFilesIsDelivered(Workspace):

    def test_a_symbolic_link_is_refused_wherever_it_sits(self):
        """The lesson the frozen host's own module opens with.

        A link inside a source materializes as ORDINARY FILES in the worker's
        snapshot, and every downstream digest then faithfully describes content
        the assignment was never given.
        """
        for what, target in [("a file link", "b.txt"),
                             ("an absolute link outside", "/etc/hostname"),
                             ("a relative link outside", "../../elsewhere"),
                             ("a directory link", ".")]:
            with self.subTest(what=what):
                origin = self.origin({"b.txt": b"two"}, f"link-{hash(what)}")
                os.symlink(target, os.path.join(origin, "linked"))
                with self.assertRaises(ContractRefusal) as caught:
                    directory_manifest(origin)
                self.assertIn("symbolic link", caught.exception.message)

    def test_a_hard_link_is_refused_although_nothing_shows_on_the_entry(self):
        """The same disclosure as a symlink, with no link to see.

        `st_nlink` is a property of the inode, so this is asked of the
        DESCRIPTOR rather than of the directory entry -- there is nothing in
        the listing that distinguishes a second name for one inode from a file.
        """
        origin = self.origin({"a.txt": b"one"}, "hard")
        os.link(os.path.join(origin, "a.txt"), os.path.join(origin, "b.txt"))
        with self.assertRaises(ContractRefusal) as caught:
            directory_manifest(origin)
        self.assertIn("hard link", caught.exception.message)

    def test_a_special_file_is_neither_a_regular_file_nor_a_directory(self):
        origin = self.origin({}, "special")
        os.mkfifo(os.path.join(origin, "pipe"))
        with self.assertRaises(ContractRefusal) as caught:
            directory_manifest(origin)
        self.assertIn("neither a regular file nor a directory",
                      caught.exception.message)

    def test_a_root_that_is_itself_a_link_is_resolved_before_it_is_walked(self):
        """Lexical containment is not containment.

        The root is canonicalized, so a link standing in for the root is
        followed once, deliberately, and everything under it is then measured
        against the real place rather than the name.
        """
        real = self.origin({"a.txt": b"one"}, "real")
        linked = os.path.join(self.root, "linked-root")
        os.symlink(real, linked)
        self.assertEqual(directory_manifest(linked), directory_manifest(real))


class ALimitIsARefusalRatherThanAWalk(Workspace):

    def test_a_tree_deeper_than_the_limit_is_refused(self):
        origin = self.origin({"/".join(["d"] * (MAX_DEPTH + 2)) + "/a.txt":
                              b"deep"}, "deep")
        with self.assertRaises(ContractRefusal) as caught:
            directory_manifest(origin)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        self.assertIn("nests deeper", caught.exception.message)

    def test_the_entry_and_byte_limits_are_the_frozen_contracts_own(self):
        """Stated rather than probed with a hundred thousand files.

        Building a tree at the limit would measure the machine rather than the
        rule. What matters is that the numbers this component enforces are the
        ones a `contentManifest` can hold -- so a manifest it produces is never
        one the frozen schema would then refuse.
        """
        self.assertEqual(MAX_ENTRIES, 100_000)
        self.assertLessEqual(MAX_ENTRIES, 100_000)
        self.assertLess(workspaces.MAX_BYTES, 9007199254740991)


class OneAssignmentOneWorkspace(Workspace):

    def test_the_two_roots_are_siblings_and_never_nested(self):
        """A worker that could write into its own inputs would make the seal
        over them describe a tree that has since changed.

        W15232 review [P1]: there were three. The acquisition-specific one is
        gone with the operations that consumed it."""
        roots = self.workspace()
        self.assertEqual(sorted(roots), ["inputs", "workspace"])
        for name, place in roots.items():
            for other, elsewhere in roots.items():
                if name == other:
                    continue
                with self.subTest(name=name, other=other):
                    self.assertFalse(place.startswith(elsewhere + os.sep))

    def test_two_assignments_share_nothing(self):
        first = self.workspace("assignment-a")
        second = self.workspace("assignment-b")
        for name in ("inputs", "workspace"):
            with self.subTest(name=name):
                self.assertNotEqual(first[name], second[name])
                self.assertFalse(first[name].startswith(second[name] + os.sep))
                self.assertFalse(second[name].startswith(first[name] + os.sep))

    def test_concurrent_assignments_never_share_a_root(self):
        """CONCURRENCY, measured rather than reasoned about.

        The roots are created with `makedirs(exist_ok=True)`, so two callers
        racing on the same parent is the ordinary case rather than the
        exceptional one; what must never happen is two ASSIGNMENTS answering
        with one root.
        """
        names = [f"assignment-{index}" for index in range(24)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            answers = list(pool.map(self.workspace, names))
        for name in ("inputs", "workspace"):
            places = [answer[name] for answer in answers]
            with self.subTest(name=name):
                self.assertEqual(len(set(places)), len(names))

    def test_the_same_assignment_asked_twice_gets_the_same_roots(self):
        """Recoverable rather than exclusive: a manager that crashed after
        creating the roots must be able to ask again."""
        self.assertEqual(self.workspace("assignment-r"),
                         self.workspace("assignment-r"))

    def test_storage_this_manager_does_not_own_is_refused(self):
        for what, storage in [("a relative path", "storage"),
                              ("a file", __file__),
                              ("a path that does not exist",
                               os.path.join(self.root, "absent"))]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    assignment_workspace(storage, "assignment-x")


class CleanupTouchesOnlyWhatWasCreated(Workspace):

    def test_a_workspace_is_removed_including_its_read_only_trees(self):
        origin = self.origin({"a.txt": b"one"})
        roots = self.workspace()
        self.staged(origin, roots)
        self.assertTrue(discard_workspace(self.storage, "assignment-1"))
        self.assertFalse(os.path.exists(os.path.dirname(roots["inputs"])))
        # And the ORIGIN is untouched: cleanup concerns only what this
        # component created.
        self.assertTrue(os.path.exists(os.path.join(origin, "a.txt")))

    def test_removing_what_is_already_gone_is_an_answer_not_a_fault(self):
        self.assertFalse(discard_workspace(self.storage, "never-created"))

    def test_cleanup_never_reaches_outside_its_storage(self):
        with self.assertRaises(ContractRefusal):
            discard_workspace(self.storage, "../..")


class TheInputRootIsComposedOnceAndThenFrozen(Workspace):
    """W19784, approved 2026-08-26.

    THE DEFECT. `completionManifest` requires the exact full `assignment_ref`
    including the authority generation; `inputManifest` is minted before any
    claim exists and carries none; nothing else inside the execution container
    carried one. So a worker obeying the input contract could not obey the
    output contract, and this manager had no step that put the missing
    document where the worker could read it.

    THE LIFECYCLE IS THE RULE, not a convenience. `input.json` is pre-claim
    evidence whose bytes never change; `assignment.json` is materialized after
    the claim commits; no container observes the root in between; and only
    then is the whole surface exposed read-only.
    """

    def documents(self, **spoiled):
        published = json.loads(VECTORS.read_text(encoding="utf-8"))
        by_schema = {one["document"].get("schema"): one["document"]
                     for one in published["valid"]}
        given = by_schema["baton.worker-manifest/input"]
        assignment = dict(by_schema["baton.worker-manifest/assignment"])
        assignment.update(spoiled)
        assignment.pop("manifest_digest", None)
        assignment["manifest_digest"] = digest(assignment)
        return given, assignment

    def inputs(self):
        return assignment_workspace(self.storage, "assignment-1")["inputs"]

    def owned(self, assignment):
        """The manager's own copy of the identity it is composing for.

        A SEPARATE VALUE rather than a reference into the document under test:
        `compose_input_root` compares the delivered manifest with what the
        manager holds, and a fixture that handed it the same object would be
        comparing a thing with itself.
        """
        return dict(assignment["assignment_ref"])

    def compose(self, inputs, given, delivered, **override):
        # `delivered` rather than `assignment`: the keyword operand under test
        # IS called `assignment`, and a helper whose positional shared the name
        # could not express "compose this document for a DIFFERENT identity",
        # which is the whole point of the override.
        operands = {"assignment": self.owned(delivered),
                    "runtime_attempt_id": delivered["runtime_attempt_id"]}
        operands.update(override)
        return compose_input_root(inputs, given, delivered, **operands)

    def bytes_under(self, root):
        found = {}
        for name in os.listdir(root):
            with open(os.path.join(root, name), "rb") as one:
                found[name] = one.read()
        return found

    def test_both_documents_land_at_their_fixed_names(self):
        inputs = self.inputs()
        given, assignment = self.documents()
        written = self.compose(inputs, given, assignment)
        self.assertEqual(
            [os.path.basename(one) for one in written],
            [INPUT_MANIFEST, ASSIGNMENT_MANIFEST])
        self.assertEqual(sorted(os.listdir(inputs)),
                         sorted([INPUT_MANIFEST, ASSIGNMENT_MANIFEST]))
        for place in written:
            with open(place, encoding="utf-8") as one:
                self.assertIn("schema", json.load(one))

    def test_a_composed_document_is_evidence_rather_than_scratch(self):
        """The mode says on disk what the contract says in prose. A read-only
        bind protects the CONTAINER's view; it does not protect the host copy
        from this manager's own later mistake."""
        inputs = self.inputs()
        for place in self.compose(inputs, *self.documents()):
            with self.subTest(place=os.path.basename(place)):
                self.assertEqual(os.stat(place).st_mode & 0o777,
                                 READ_ONLY_FILE)

    def test_a_mis_composed_pair_writes_NOTHING(self):
        """Two documents that are not one delivery must never exist together on
        disk. A mount is not the last chance to notice -- it is the first
        moment it is too late, because a worker may already have read them."""
        inputs = self.inputs()
        other = "sha256:" + "f" * 64
        for what, spoiled in (
                ("another Work",
                 {"assignment_ref": {
                     "work_ref": {"authority_uuid": "f" * 32,
                                  "work_id": "ffffffff-W9"},
                     "participant": "baton.claude", "generation": 3}}),
                ("another input manifest", {"input_manifest_digest": other}),
                ("another policy", {"policy_digest": other}),
                ("another runtime profile",
                 {"runtime_profile_digest": other})):
            with self.subTest(what=what):
                given, assignment = self.documents(**spoiled)
                with self.assertRaises(ContractRefusal):
                    self.compose(inputs, given, assignment)
                self.assertEqual(os.listdir(inputs), [],
                                 "a refused composition left a document "
                                 "behind")

    def test_the_root_is_composed_once(self):
        """Rewriting `input.json` after a claim was made against it would
        change the evidence the result is measured by; replacing
        `assignment.json` would move an identity a running worker may already
        have copied into a durable envelope."""
        inputs = self.inputs()
        given, assignment = self.documents()
        self.compose(inputs, given, assignment)
        before = self.bytes_under(inputs)
        with self.assertRaises(ContractRefusal) as caught:
            self.compose(inputs, given, assignment)
        self.assertEqual(caught.exception.code, "path")
        after = self.bytes_under(inputs)
        self.assertEqual(before, after)

    def test_a_half_composed_root_is_refused_rather_than_completed(self):
        """The interrupted case, and it is NOT repaired here. A manager that
        finished somebody else's half-composition would be asserting that the
        document already on disk is the one this pair belongs to, which is
        exactly the question `check_input_pair` exists to answer."""
        inputs = self.inputs()
        given, assignment = self.documents()
        with open(os.path.join(inputs, INPUT_MANIFEST), "w") as handle:
            handle.write("{}")
        with self.assertRaises(ContractRefusal):
            self.compose(inputs, given, assignment)
        self.assertEqual(os.listdir(inputs), [INPUT_MANIFEST])

    def test_no_partial_document_survives_under_a_final_name(self):
        """Publication is atomic: a half-written protocol document under its
        final name is indistinguishable from a complete one, and this root is
        handed to a container that reads exactly these two names."""
        inputs = self.inputs()
        for place in self.compose(inputs, *self.documents()):
            with open(place, "rb") as one:
                json.loads(one.read().decode("utf-8"))
        self.assertFalse([name for name in os.listdir(inputs)
                          if name.endswith(".composing")])

    def test_an_interrupted_write_publishes_no_protocol_document(self):
        """A half-written protocol document under its final name is
        indistinguishable from a complete one, and this root is about to be
        handed to a container that reads exactly these two names. So the bytes
        become visible under the final name only once they are all there."""
        inputs = self.inputs()
        real = workspaces.os.write

        def stops(handle, payload):
            real(handle, payload[:1])
            raise OSError(28, "no space left on device")

        workspaces.os.write = stops
        self.addCleanup(setattr, workspaces.os, "write", real)
        with self.assertRaises(OSError):
            self.compose(inputs, *self.documents())
        self.assertEqual(
            [name for name in os.listdir(inputs)
             if not name.endswith(".composing")], [],
            "an interrupted write left a document under its final name")

    def test_a_root_this_manager_did_not_allocate_is_refused(self):
        """A refusal rather than an `OSError` out of `os.open`. This boundary's
        contract is to refuse what it cannot do; a caller that received a raw
        errno would be reading this manager's implementation."""
        for what, place in (
                ("a root that does not exist",
                 os.path.join(self.storage, "never-allocated", "inputs")),
                ("a root that is a file", self.a_file())):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    self.compose(place, *self.documents())
                self.assertEqual(caught.exception.category, "integrity")

    def a_file(self):
        place = os.path.join(self.storage, "not-a-directory")
        with open(place, "w") as handle:
            handle.write("x")
        return place

    def test_a_self_consistent_pair_for_another_delivery_writes_NOTHING(self):
        """W19784 review [P0]. THE PAIR RULE IS NOT AN AUTHORIZATION.

        Every document below is internally valid and the two agree with each
        other perfectly -- `check_input_pair` accepts them. What they are not
        is the delivery THIS manager is composing a root for. A superseded
        generation, another participant, another Work, another runtime
        attempt: each agrees with itself, and each would have been written,
        mounted, and caught only at the freeze, after the agent had already
        run against material nothing authorized.
        """
        inputs = self.inputs()
        given, assignment = self.documents()
        mine = self.owned(assignment)
        for what, override in (
                ("a superseded generation",
                 {"assignment": dict(mine, generation=mine["generation"] + 1)}),
                ("another participant",
                 {"assignment": dict(mine, participant="baton.someone")}),
                ("another Work",
                 {"assignment": dict(mine, work_ref={
                     "authority_uuid": "f" * 32, "work_id": "ffffffff-W9"})}),
                ("another runtime attempt",
                 {"runtime_attempt_id": "attempt-99"})):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    self.compose(inputs, given, assignment, **override)
                self.assertIn(caught.exception.category,
                              ("stale-assignment", "runtime-observation"))
                self.assertEqual(os.listdir(inputs), [],
                                 "an unauthorized pair reached the disk")

    def test_the_composed_root_reads_back_as_the_pair_that_was_written(self):
        """The launch path proves the root off DISK, because what a runtime
        mounts is the disk rather than a value threaded down from whoever
        composed it."""
        inputs = self.inputs()
        given, assignment = self.documents()
        self.compose(inputs, given, assignment)
        back_input, back_assignment = read_input_root(inputs)
        self.assertEqual(back_input["manifest_digest"],
                         given["manifest_digest"])
        self.assertEqual(back_assignment["assignment_ref"],
                         assignment["assignment_ref"])

    def test_a_root_edited_after_composition_does_not_read_back_clean(self):
        """WHY THE READ REVALIDATES. Composition proved the pair; the disk is
        not the composition. A root whose assignment document was replaced
        after the fact -- same identity, minted against a DIFFERENT input
        manifest -- is a delivery no longer describing the material beside it,
        and the launch path reads the disk rather than a value threaded down
        from whoever composed it."""
        inputs = self.inputs()
        given, assignment = self.documents()
        self.compose(inputs, given, assignment)
        replaced = dict(assignment,
                        input_manifest_digest="sha256:" + "e" * 64)
        replaced.pop("manifest_digest", None)
        replaced["manifest_digest"] = digest(replaced)
        place = os.path.join(inputs, ASSIGNMENT_MANIFEST)
        os.chmod(place, 0o600)
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(replaced, handle)
        with self.assertRaises(ContractRefusal) as caught:
            read_input_root(inputs)
        self.assertEqual(caught.exception.code, "digest")

    def test_a_root_that_is_not_a_composed_pair_cannot_be_read_back(self):
        inputs = self.inputs()
        given, assignment = self.documents()
        def wrote(**named):
            # Closed handles. The review flagged three leaking here: a
            # `ResourceWarning` in a suite about filesystem boundaries is
            # noise in exactly the place a real handle leak would show.
            for name, payload in named.items():
                with open(os.path.join(inputs, name), "w",
                          encoding="utf-8") as handle:
                    handle.write(payload)

        for what, prepare in (
                ("nothing composed yet", lambda: None),
                ("only the input side",
                 lambda: wrote(**{INPUT_MANIFEST: json.dumps(given)})),
                ("a document that is not a document",
                 lambda: wrote(**{INPUT_MANIFEST: "{oops",
                                  ASSIGNMENT_MANIFEST: "{oops"}))):
            with self.subTest(what=what):
                for name in os.listdir(inputs):
                    os.chmod(os.path.join(inputs, name), 0o600)
                    os.unlink(os.path.join(inputs, name))
                prepare()
                with self.assertRaises(ContractRefusal):
                    read_input_root(inputs)

    def test_the_generation_reaches_the_root_and_the_input_side_has_none(self):
        """The member the whole Work is about, observed where it lands."""
        inputs = self.inputs()
        self.compose(inputs, *self.documents())
        with open(os.path.join(inputs, ASSIGNMENT_MANIFEST)) as one:
            delivered = json.load(one)
        with open(os.path.join(inputs, INPUT_MANIFEST)) as one:
            staged = json.load(one)
        self.assertIn("generation", delivered["assignment_ref"])
        self.assertNotIn("assignment_ref", staged)




class TheCopyIsTheMeasurement(Workspace):
    """W26283: `copied_manifest` measures and copies in ONE no-follow pass.

    The defect this exists for was real and was driven before it was fixed:
    W6634's staging measured with `directory_manifest` -- which descends by
    opened directory identity and refuses links -- and then copied by
    REOPENING each path with a plain `open`, resolving every component a second
    time. That put material from outside the tree into manager custody, and one
    `mkfifo` blocked the copy forever.
    """

    def into(self, name="custody"):
        return os.path.join(self.root, name)

    def test_the_copy_answers_what_a_fresh_measurement_of_it_answers(self):
        """The one pass and the two passes agree, or the manifest describes
        something other than what was written."""
        place = self.origin({"a.txt": b"one", "deep/b.txt": b"two"})
        into = self.into()
        written = workspaces.copied_manifest(place, into)
        self.assertEqual(written, workspaces.directory_manifest(into))
        self.assertEqual(written["entry_count"], 2)
        self.assertEqual(written["total_bytes"], 6)
        with open(os.path.join(into, "deep", "b.txt"), "rb") as reading:
            self.assertEqual(reading.read(), b"two")

    def test_a_symbolic_link_is_refused_where_it_is_found(self):
        place = self.origin({"a.txt": b"one"})
        os.symlink("/etc/hostname", os.path.join(place, "link"))
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.copied_manifest(place, self.into())
        self.assertIn("symbolic link", str(caught.exception))

    def test_a_directory_replaced_by_a_link_after_listing_is_not_entered(self):
        """THE HARM, at this boundary. A path-based copy resolves the whole
        string again, so an ancestor that became a link is a door out of the
        tree; this descends through the descriptor it opened."""
        place = self.origin({"deep/a.txt": b"legitimate"})
        outside = os.path.join(self.root, "elsewhere")
        os.makedirs(outside)
        with open(os.path.join(outside, "a.txt"), "wb") as handle:
            handle.write(b"HOST MATERIAL")
        os.rename(os.path.join(place, "deep"),
                  os.path.join(self.root, "deep-real"))
        os.symlink(outside, os.path.join(place, "deep"))
        into = self.into()
        with self.assertRaises(ContractRefusal):
            workspaces.copied_manifest(place, into)
        self.assertFalse(os.path.exists(os.path.join(into, "deep", "a.txt")))

    def test_a_named_pipe_is_refused_rather_than_opened(self):
        """A plain `open` on a FIFO blocks until somebody writes. The walk
        refuses a non-regular file where it lists it, so the open never
        happens -- and this case returning at all is half of what it
        asserts."""
        place = self.origin({"a.txt": b"one"})
        os.mkfifo(os.path.join(place, "pipe"))
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.copied_manifest(place, self.into())
        self.assertIn("neither a regular file nor a directory",
                      str(caught.exception))

    def test_a_destination_that_is_a_link_is_not_written_through(self):
        """The copy makes bytes the caller's OWN, so a link left at a
        destination name must not become the thing written to."""
        place = self.origin({"a.txt": b"one"})
        target = os.path.join(self.root, "elsewhere.txt")
        with open(target, "wb") as handle:
            handle.write(b"UNTOUCHED")
        into = self.into()
        os.makedirs(into)
        os.symlink(target, os.path.join(into, "a.txt"))
        with self.assertRaises(OSError):
            workspaces.copied_manifest(place, into)
        with open(target, "rb") as reading:
            self.assertEqual(reading.read(), b"UNTOUCHED")

    def test_a_declared_ceiling_refuses_as_a_limit_not_as_a_denial(self):
        """TWO CEILINGS, TWO REFUSALS. This module's own MAX_* are policy --
        what this build will handle at all. A caller's ceiling is part of a
        delivery's declared contract, and exceeding it is an integrity failure
        of that delivery. Callers already depend on which one they get."""
        place = self.origin({"a.txt": b"one", "b.txt": b"two"})
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.copied_manifest(place, self.into(), max_entries=1)
        self.assertEqual(caught.exception.category, "integrity")
        self.assertEqual(caught.exception.code, "limit")
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.copied_manifest(place, self.into("c2"), max_bytes=3)
        self.assertEqual(caught.exception.code, "limit")

    def test_a_ceiling_stops_the_pass_rather_than_the_whole_tree(self):
        """Enforced AS THE WALK RUNS. A tree copied whole and refused
        afterwards has already written every byte it was refused for."""
        place = self.origin({f"{index:03d}.txt": b"x" * 10
                             for index in range(20)})
        into = self.into()
        with self.assertRaises(ContractRefusal):
            workspaces.copied_manifest(place, into, max_entries=5)
        written = sum(len(files) for _b, _d, files in os.walk(into))
        self.assertLessEqual(written, 5)
        self.assertLess(written, 20)

    def test_the_caller_rule_runs_before_the_write_and_refusing_writes_none(
            self):
        """`admits` exists so a caller's own content rule runs at the one
        moment the content is in hand -- and refusing means the bytes never
        became the caller's, rather than being taken and then objected to."""
        place = self.origin({"a.txt": b"harmless", "b.txt": b"FORBIDDEN"})
        into = self.into()
        seen = []

        def admits(relative, content):
            seen.append(relative)
            if b"FORBIDDEN" in content:
                raise ContractRefusal("policy", "denied", "not this one")

        with self.assertRaises(ContractRefusal):
            workspaces.copied_manifest(place, into, admits=admits)
        self.assertIn("b.txt", seen)
        self.assertFalse(os.path.exists(os.path.join(into, "b.txt")))

    def test_a_hard_link_is_refused(self):
        """A second name for one inode delivers content the caller was never
        given, with nothing on the directory entry to see."""
        place = self.origin({"a.txt": b"one"})
        outside = os.path.join(self.root, "outside.txt")
        with open(outside, "wb") as handle:
            handle.write(b"HOST MATERIAL")
        os.link(outside, os.path.join(place, "linked.txt"))
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.copied_manifest(place, self.into())
        self.assertIn("hard link", str(caught.exception))

    def test_an_entry_already_at_the_destination_refuses(self):
        """`O_EXCL`, and the reason is ownership rather than tidiness.

        This pass is what makes bytes the caller's own, so every entry it
        writes must be one it CREATED. A destination file already there is
        somebody else's -- an interrupted attempt's prefix, or another writer
        -- and overwriting it would publish a tree assembled from two passes.
        Callers clear custody first; this refuses if that did not happen.
        """
        place = self.origin({"a.txt": b"one"})
        into = self.into()
        os.makedirs(into)
        with open(os.path.join(into, "a.txt"), "wb") as handle:
            handle.write(b"SOMEBODY ELSE'S")
        with self.assertRaises(OSError):
            workspaces.copied_manifest(place, into)
        with open(os.path.join(into, "a.txt"), "rb") as reading:
            self.assertEqual(reading.read(), b"SOMEBODY ELSE'S")

    def test_this_builds_own_ceilings_refuse_as_policy(self):
        """The OTHER half of the two-ceilings rule.

        `MAX_ENTRIES` and `MAX_BYTES` are what this build will handle at all,
        whoever asked, and they refuse as `policy/denied` rather than as a
        delivery's integrity failure. Driven by lowering the module's own
        constants, because a case that wrote a hundred thousand files would
        be a case nobody runs.
        """
        place = self.origin({"a.txt": b"one", "b.txt": b"two"})
        original_entries = workspaces.MAX_ENTRIES
        original_bytes = workspaces.MAX_BYTES
        try:
            workspaces.MAX_ENTRIES = 1
            with self.assertRaises(ContractRefusal) as caught:
                workspaces.copied_manifest(place, self.into())
            self.assertEqual(caught.exception.category, "policy")
            self.assertEqual(caught.exception.code, "denied")
            workspaces.MAX_ENTRIES = original_entries
            workspaces.MAX_BYTES = 3
            with self.assertRaises(ContractRefusal) as caught:
                workspaces.copied_manifest(place, self.into("c2"))
            self.assertEqual(caught.exception.category, "policy")
        finally:
            workspaces.MAX_ENTRIES = original_entries
            workspaces.MAX_BYTES = original_bytes

    def test_an_empty_tree_copies_to_an_empty_manifest(self):
        place = self.origin({})
        into = self.into()
        written = workspaces.copied_manifest(place, into)
        self.assertEqual(written["entry_count"], 0)
        self.assertEqual(written["total_bytes"], 0)
        self.assertTrue(os.path.isdir(into))




class TheComponentIsOnThePublicSurface(Workspace):

    def test_every_operation_this_cut_adds_is_exported(self):
        for name in workspaces.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(workspaces, name))


class TheCoreManagerDoesNotAcquireSources(Workspace):
    """W15232, and the whole point of this Work.

    The 2026-08-25 ruling removed source ACQUISITION from the core Worker
    Manager: it receives an already staged read-only directory and its generic
    integrity envelope, and it does not understand where the bytes came from or
    choose an operation to fetch them.

    W6631's `GitPort`, `materialize_git_source` and
    `materialize_directory_source` performed exactly that duty here. They are
    gone rather than re-homed, because the assignment permits re-homing only
    behind an ALREADY PINNED stager or driver owner and there is none -- the
    ledger has no such Work and the records name no such boundary. Inventing
    one to keep the code would have been the second acquisition contract this
    Work exists to avoid.

    The cases they had are gone with them: a test of behaviour that no longer
    exists asserts nothing. What replaces them is this -- the ABSENCE, stated
    so that re-adding an acquisition operation to this manager has to fail
    here first.
    """

    def test_no_acquisition_operation_survives_on_the_manager(self):
        import baton_v12.worker_manager as manager
        for name in ("GitPort", "materialize_git_source",
                     "materialize_directory_source"):
            with self.subTest(name=name):
                self.assertNotIn(name, workspaces.__all__)
                self.assertFalse(hasattr(workspaces, name),
                                 f"{name} is still on the workspace module")
                self.assertNotIn(name, manager.__all__)
                self.assertFalse(hasattr(manager, name),
                                 f"{name} is still on the manager package")

    def test_no_acquisition_descriptor_is_interpreted_here(self):
        """The other half, and the one a re-added helper would trip.

        An operation could be spelled differently and still READ a `gitSource`
        or `directorySource` -- which is the coupling that made W14251's
        neutral schema refuse every request through this module. The module
        names neither definition now, and nothing in it reaches the fragment
        validator that would.
        """
        import ast
        import inspect
        # THE CODE, NOT THE PROSE. My first version read the raw source and
        # failed on the module's own comment explaining why these names are
        # gone -- a case that cannot tell an explanation from a use is a case
        # that punishes writing the explanation down.
        tree = ast.parse(inspect.getsource(workspaces))
        reached = {node.id for node in ast.walk(tree)
                   if isinstance(node, ast.Name)}
        reached |= {node.attr for node in ast.walk(tree)
                    if isinstance(node, ast.Attribute)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and type(node.value) is str:
                # A definition NAME reaching the fragment validator is a
                # string operand, so string literals count -- except the ones
                # that are documentation, which `ast` hands back as the body's
                # first statement rather than as an expression operand.
                continue
        for named in ("gitSource", "directorySource", "validate_fragment",
                      "check_content_manifest"):
            with self.subTest(named=named):
                self.assertNotIn(named, reached)
        # And no string operand names a removed definition either.
        literals = {node.value for node in ast.walk(tree)
                    if isinstance(node, ast.Constant)
                    and type(node.value) is str}
        self.assertEqual(
            sorted(literals & {"gitSource", "directorySource"}), [],
            "an acquisition definition is still named as an operand")

    def test_no_surface_still_describes_the_acquisition_specific_root(self):
        """W15232 review [P2], and the second time this campaign that I
        corrected code and left the prose beside it describing what was
        removed. A reader -- and a generated test description -- sees the old
        ownership after the executable boundary was corrected.

        Checked as a STRING OPERAND rather than as a word, which is the
        distinction that matters: a root name is a literal these modules act
        on, while an explanation of why that root is gone is prose which
        should be free to say so. An earlier attempt at this kind of case
        failed on the module's own comment, punishing the explanation it
        wanted written down.
        """
        import ast
        import inspect
        from baton_v12.worker_manager import oci
        removed = "git"
        for named, module in (("workspaces", workspaces), ("oci", oci)):
            tree = ast.parse(inspect.getsource(module))
            literals = {node.value for node in ast.walk(tree)
                        if isinstance(node, ast.Constant)
                        and type(node.value) is str}
            with self.subTest(module=named):
                self.assertNotIn(
                    removed, literals,
                    f"{named} still names the acquisition-specific root as an "
                    f"operand")
        self.assertEqual(oci.ROOT_NAMES, ("inputs", "workspace"))

    def test_the_generic_duties_this_manager_keeps_are_still_here(self):
        """Removal, not amputation. Assignment-private paths, the measured
        manifest over an already staged tree, and cleanup are the manager's
        own and say nothing about where bytes came from."""
        for name in ("assignment_workspace", "compose_input_root",
                     "directory_manifest", "discard_workspace"):
            with self.subTest(name=name):
                self.assertIn(name, workspaces.__all__)
                self.assertTrue(callable(getattr(workspaces, name)))

    def test_no_git_metadata_root_survives_the_acquisition_cut(self):
        """A retained helper cannot keep provisioning an acquisition-specific
        root after the core manager has stopped understanding Git."""
        roots = self.workspace("artifact-neutral")
        self.assertEqual(sorted(roots), ["inputs", "workspace"])
        self.assertFalse(os.path.exists(os.path.join(
            self.storage, "artifact-neutral", "git")))


if __name__ == "__main__":
    unittest.main()
