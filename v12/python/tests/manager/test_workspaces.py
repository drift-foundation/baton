"""W6631 — exact sources, and one private workspace per assignment.

The acceptance this file answers to, from the bound record:

  deterministic manifest/digest vectors; symlink, hard-link/special-file,
  traversal, replacement-race and limit refusals that leave NO ACCEPTED PARTIAL
  WORKSPACE; pinned revision/ref mismatch and mutable shared Git metadata
  refuse; concurrent assignments never share a writable workspace or Git
  metadata; cleanup concerns only what this component created.

WHY THE GIT HALF USES A FAKE REPOSITORY AND NOT A REAL ONE. Two reasons, and
the second is the one that decides it. The component's own boundary is the
VERIFICATION -- that the pinned object is what is checked out and that an
advertised ref still names it -- and a fake answers those questions exactly as
a real repository does. And the standing role instruction for this deployment
is "never perform mutating Git operations": building fixture repositories would
mean running `git init` and `git commit`, which is that, on the letter of it.
The constraint is reported in the record rather than worked around quietly.
"""

import concurrent.futures
import os
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal, check_content_manifest, digest
from baton_v12.worker_manager import workspaces
from baton_v12.worker_manager.workspaces import (
    MAX_DEPTH, MAX_ENTRIES, READ_ONLY_DIR, READ_ONLY_FILE, GitPort,
    assignment_workspace, directory_manifest, discard_workspace,
    materialize_directory_source, materialize_git_source)

SHA1 = {"algorithm": "sha1", "hex": "a" * 40}
MOVED = {"algorithm": "sha1", "hex": "b" * 40}


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

    def source(self, origin, **overrides):
        source = {"name": "src", "type": "directory",
                  "uri": "file:///origin", "destination": "src",
                  "required": True,
                  "content_manifest": directory_manifest(origin)}
        source.update(overrides)
        return source

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


class ADeliveredSourceIsExactAndReadOnly(Workspace):

    def test_the_second_read_closes_every_ancestor_descriptor(self):
        """Publication reopens each component and must own those handles."""
        origin = self.origin({"deep/deeper/a.txt": b"one"}, "descriptor-copy")
        source = self.source(origin)
        before = self.open_descriptors_below(origin)
        roots = self.workspace("assignment-descriptor-copy")
        materialize_directory_source(source, origin=origin,
                                     inputs=roots["inputs"])
        self.assertEqual(self.open_descriptors_below(origin), before)

    def test_a_source_descriptor_is_the_frozen_closed_shape(self):
        """Materialization consumes a sourceDescriptor, not a loose subset."""
        origin = self.origin({"a.txt": b"one"})
        source = self.source(origin)
        malformed = {
            "missing uri": {name: value for name, value in source.items()
                            if name != "uri"},
            "missing required": {name: value for name, value in source.items()
                                 if name != "required"},
            "extra member": dict(source, surprise=True),
        }
        for index, (what, candidate) in enumerate(malformed.items()):
            with self.subTest(what=what):
                roots = self.workspace(f"assignment-shape-{index}")
                with self.assertRaises(ContractRefusal):
                    materialize_directory_source(
                        candidate, origin=origin, inputs=roots["inputs"])
                self.assertEqual(os.listdir(roots["inputs"]), [])

    def test_a_matching_source_is_delivered_read_only(self):
        origin = self.origin({"a.txt": b"one", "d/b.txt": b"two"})
        roots = self.workspace()
        answer = materialize_directory_source(
            self.source(origin), origin=origin, inputs=roots["inputs"])
        self.assertEqual(answer["entry_count"], 2)
        delivered = answer["destination"]
        with open(os.path.join(delivered, "d/b.txt"), "rb") as handle:
            self.assertEqual(handle.read(), b"two")
        self.assertEqual(
            os.stat(os.path.join(delivered, "a.txt")).st_mode & 0o777,
            READ_ONLY_FILE)
        self.assertEqual(os.stat(delivered).st_mode & 0o777, READ_ONLY_DIR)
        # And the delivered tree measures back to the manifest that was
        # declared for it, which is the property the whole component exists for.
        os.chmod(delivered, 0o700)
        self.assertEqual(directory_manifest(delivered)["tree_digest"],
                         answer["tree_digest"])

    def test_a_short_write_cannot_publish_a_truncated_source(self):
        """One os.write call is not a promise that every byte was written."""
        content = b"more than one byte"
        origin = self.origin({"a.txt": content}, "short-write")
        roots = self.workspace("assignment-short-write")
        original = os.write

        def short(descriptor, data):
            return original(descriptor, data[:1])

        os.write = short
        try:
            answer = materialize_directory_source(
                self.source(origin), origin=origin, inputs=roots["inputs"])
        finally:
            os.write = original
        with open(os.path.join(answer["destination"], "a.txt"), "rb") as handle:
            self.assertEqual(handle.read(), content)

    def test_a_stale_staging_symlink_is_not_cleanup_authority(self):
        """Recovery may remove only a staging directory this component owns."""
        origin = self.origin({"a.txt": b"one"}, "staging-origin")
        roots = self.workspace("assignment-staging-link")
        target = os.path.join(self.root, "not-staging")
        os.makedirs(target, mode=0o755)
        staging = os.path.join(roots["inputs"], "src.materializing")
        os.symlink(target, staging)
        with self.assertRaises(ContractRefusal):
            materialize_directory_source(
                self.source(origin), origin=origin, inputs=roots["inputs"])
        self.assertEqual(os.stat(target).st_mode & 0o777, 0o755)

    def test_a_source_whose_digest_disagrees_is_not_delivered(self):
        origin = self.origin({"a.txt": b"one"})
        source = self.source(origin)
        source["content_manifest"] = dict(
            source["content_manifest"],
            tree_digest="sha256:" + "0" * 64)
        roots = self.workspace()
        with self.assertRaises(ContractRefusal) as caught:
            materialize_directory_source(source, origin=origin,
                                         inputs=roots["inputs"])
        self.assertEqual(caught.exception.code, "digest")
        self.assertEqual(sorted(os.listdir(roots["inputs"])), [],
                         "a refused source left something behind")

    def test_a_count_or_byte_disagreement_is_named_before_the_digest(self):
        """A manifest that is INTERNALLY CONSISTENT and describes another tree.

        Editing one aggregate would be caught by the frozen §12 rule before
        this component measured anything, which proves the contracts layer
        rather than this one. So the declared manifest is a real manifest --
        of a DIFFERENT directory -- and only measuring the origin can tell.

        The digests would differ too. The count and the byte total are compared
        first and named because a reader of this refusal is trying to find out
        what is on disk that should not be, and two long hex strings do not say.
        """
        origin = self.origin({"a.txt": b"one"}, "small")
        other = self.origin({"a.txt": b"one", "b.txt": b"twotwo"}, "larger")
        source = self.source(origin,
                             content_manifest=directory_manifest(other))
        self.assertEqual(check_content_manifest(source["content_manifest"]),
                         source["content_manifest"])
        roots = self.workspace("assignment-aggregates")
        with self.assertRaises(ContractRefusal) as caught:
            materialize_directory_source(source, origin=origin,
                                         inputs=roots["inputs"])
        self.assertEqual(caught.exception.code, "digest")
        self.assertIn("entry_count", caught.exception.message)
        self.assertEqual(os.listdir(roots["inputs"]), [])

        thinner = self.origin({"a.txt": b"ONE!"}, "same-count")
        source = self.source(origin,
                             content_manifest=directory_manifest(thinner))
        roots = self.workspace("assignment-bytes")
        with self.assertRaises(ContractRefusal) as caught:
            materialize_directory_source(source, origin=origin,
                                         inputs=roots["inputs"])
        self.assertIn("total_bytes", caught.exception.message)

    def test_a_destination_leaving_the_inputs_root_is_refused(self):
        """The frozen `relativePath` type catches these BEFORE this component
        looks at them, which is the right place: the schema owns the path's
        shape and this owns where the shape may land.

        The containment check remains and is not redundant -- it answers a
        question the schema cannot, which is whether a well-formed relative
        path resolves inside THIS assignment's inputs root once symbolic links
        are followed.
        """
        origin = self.origin({"a.txt": b"one"})
        roots = self.workspace()
        for destination in ("../escape", "a/../../escape", "/absolute"):
            with self.subTest(destination=destination):
                with self.assertRaises(ContractRefusal) as caught:
                    materialize_directory_source(
                        self.source(origin, destination=destination),
                        origin=origin, inputs=roots["inputs"])
                self.assertEqual(caught.exception.category, "integrity")
        self.assertEqual(os.listdir(roots["inputs"]), [])

    def test_the_frozen_fragment_owns_the_source_before_anything_is_read(self):
        """Review [P1]: a hand-written member list is a SECOND contract for a
        shape the frozen schema already states exactly.

        `directorySource` closes its member set, types every member and
        carries the content manifest's own rules -- so a malformed source is
        refused before a member is read or the filesystem is touched, rather
        than reaching a `realpath` call with nothing having established it was
        a source at all.
        """
        origin = self.origin({"a.txt": b"one"})
        roots = self.workspace()
        for what, source in [
                ("a member the schema does not name",
                 {**self.source(origin), "unexpected": 1}),
                ("a missing member",
                 {name: value for name, value in self.source(origin).items()
                  if name != "required"}),
                ("the wrong type", self.source(origin, type="git")),
                ("a name that is not an opaque id",
                 self.source(origin, name="")),
                ("required that is not a boolean",
                 self.source(origin, required="yes"))]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    materialize_directory_source(source, origin=origin,
                                                 inputs=roots["inputs"])
                self.assertEqual(caught.exception.category, "integrity")
        self.assertEqual(os.listdir(roots["inputs"]), [])

    def test_something_already_at_the_staging_name_is_never_taken_over(self):
        """Review [P1]: this used to REMOVE whatever it found.

        A symbolic link planted at the staging name would have been followed by
        that removal, deleting somebody else's tree; and even a leftover
        directory is material this operation did not create. `lstat` asks about
        the NAME rather than what it points at, so a link is seen as a link and
        neither followed nor unlinked.
        """
        origin = self.origin({"a.txt": b"one"})
        roots = self.workspace()
        elsewhere = self.origin({"precious.txt": b"do not delete"}, "elsewhere")
        staging = os.path.join(roots["inputs"], "src.materializing")
        for what, plant in [
                ("a symbolic link to somebody else's tree",
                 lambda: os.symlink(elsewhere, staging)),
                ("a leftover directory", lambda: os.makedirs(staging)),
                ("an ordinary file",
                 lambda: open(staging, "wb").close())]:
            with self.subTest(what=what):
                plant()
                try:
                    with self.assertRaises(ContractRefusal) as caught:
                        materialize_directory_source(
                            self.source(origin), origin=origin,
                            inputs=roots["inputs"])
                    self.assertIn("did not create", caught.exception.message)
                    # AND THE PLANTED THING IS STILL THERE, unfollowed.
                    self.assertTrue(os.path.lexists(staging))
                    self.assertTrue(os.path.exists(
                        os.path.join(elsewhere, "precious.txt")))
                finally:
                    if os.path.islink(staging) or os.path.isfile(staging):
                        os.unlink(staging)
                    elif os.path.isdir(staging):
                        os.rmdir(staging)

    def test_a_short_write_is_not_a_written_file(self):
        """Review [P1]: `os.write` may write fewer bytes than it was given.

        A truncated delivery would otherwise be published under the digest of
        the whole file -- the seal describing the wrong tree, by another route.
        Driven deterministically by making every write move one byte.
        """
        origin = self.origin({"a.txt": b"one", "d/b.txt": b"a longer body"})
        roots = self.workspace()
        real = os.write
        self.addCleanup(setattr, os, "write", real)
        os.write = lambda descriptor, payload: real(descriptor, payload[:1])
        answer = materialize_directory_source(
            self.source(origin), origin=origin, inputs=roots["inputs"])
        os.write = real
        # THE PUBLISHED TREE IS THE MEASURED TREE, proved by measuring it
        # again rather than by trusting the copy.
        delivered = answer["destination"]
        os.chmod(delivered, 0o700)
        for current, directories, _ in os.walk(delivered):
            for name in directories:
                os.chmod(os.path.join(current, name), 0o700)
        self.assertEqual(directory_manifest(delivered)["tree_digest"],
                         answer["tree_digest"])

    def test_an_ancestor_directory_swapped_for_a_link_is_refused(self):
        """Review [P1]: a no-follow open of the FINAL file does not stop a
        raced ANCESTOR from becoming a symbolic link.

        The walk descends by opened directory identity -- each directory is
        opened `O_NOFOLLOW|O_DIRECTORY` and read through that descriptor -- so
        a component replaced after it was listed is a directory this walk never
        entered, rather than a door out of the tree that every later path
        string goes through.
        """
        origin = self.origin({"deep/a.txt": b"one"}, "raced")
        elsewhere = self.origin({"secret.txt": b"not yours"}, "outside")
        inner = os.path.join(origin, "deep")
        os.rename(inner, inner + "-gone")
        os.symlink(elsewhere, inner)
        with self.assertRaises(ContractRefusal) as caught:
            directory_manifest(origin)
        self.assertIn("symbolic link", caught.exception.message)

    def test_a_directory_swapped_after_listing_is_not_followed(self):
        """The queued child name must not become traversal authority.

        Swap the child only after the root listing has produced its entries,
        but before `_walk` descends into the queued name. A pathname-based
        descent follows the replacement link and measures somebody else's
        tree; descriptor-bound descent refuses or stays on the directory that
        was actually listed.
        """
        origin = self.origin({"deep/a.txt": b"one"}, "raced-after-listing")
        elsewhere = self.origin({"secret.txt": b"not yours"},
                                "outside-after-listing")
        child = os.path.join(origin, "deep")
        moved = child + "-gone"
        original = os.scandir
        swapped = False

        class Listing:
            def __init__(self, path):
                self.path = path
                self.inner = original(path)
                self.iterator = None

            def __enter__(self):
                self.iterator = iter(self.inner.__enter__())
                return self

            def __exit__(self, *args):
                return self.inner.__exit__(*args)

            def __iter__(self):
                return self

            def __next__(self):
                nonlocal swapped
                try:
                    return next(self.iterator)
                except StopIteration:
                    # TRIGGER ADJUSTED, INTENT UNCHANGED. This matched on the
                    # scandir PATH being the origin -- which a descriptor-bound
                    # walk never passes, because it lists an opened directory
                    # rather than a name. The first listing IS the root's, so
                    # this fires at exactly the moment the case describes:
                    # after the root's entries are produced and before the
                    # queued child name is descended into.
                    if not swapped:
                        os.rename(child, moved)
                        os.symlink(elsewhere, child)
                        swapped = True
                    raise

        self.addCleanup(setattr, os, "scandir", original)
        os.scandir = Listing
        with self.assertRaises(ContractRefusal):
            directory_manifest(origin)

    def test_a_source_is_materialized_once(self):
        origin = self.origin({"a.txt": b"one"})
        roots = self.workspace()
        materialize_directory_source(self.source(origin), origin=origin,
                                     inputs=roots["inputs"])
        with self.assertRaises(ContractRefusal) as caught:
            materialize_directory_source(self.source(origin), origin=origin,
                                         inputs=roots["inputs"])
        self.assertIn("already delivered", caught.exception.message)

    def test_a_tree_that_changed_before_delivery_is_refused(self):
        """The swap that happens before the measurement: caught by measuring.

        This is the ordinary case and the outer guard. The one BETWEEN the
        measurement and the copy is the next case.
        """
        origin = self.origin({"a.txt": b"one", "b.txt": b"two"})
        source = self.source(origin)
        roots = self.workspace()
        with open(os.path.join(origin, "b.txt"), "wb") as handle:
            handle.write(b"SWAPPED")
        with self.assertRaises(ContractRefusal) as caught:
            materialize_directory_source(source, origin=origin,
                                         inputs=roots["inputs"])
        self.assertEqual(caught.exception.code, "digest")
        self.assertEqual(sorted(os.listdir(roots["inputs"])), [],
                         "a refused source left a partial workspace")

    def test_a_file_replaced_between_measuring_and_copying_is_caught(self):
        """THE RACE THIS COMPONENT READS EVERY FILE TWICE FOR.

        The window is between the measurement and the copy, so it cannot be
        reached through the public operation without a scheduler that
        cooperates -- and a test that raced a real writer would pass or fail
        depending on the machine. So the two halves are driven directly, with
        the swap in the window: this reaches for a private on purpose, because
        the window exists only between the two public steps and a witness that
        cannot see it proves nothing.

        Without the second read, `b.txt` would be delivered under the digest of
        the version that is gone -- the seal describing the wrong tree, which is
        the failure the whole component exists to prevent.
        """
        origin = self.origin({"a.txt": b"one", "b.txt": b"two"})
        roots = self.workspace()
        measured = directory_manifest(origin)
        with open(os.path.join(origin, "b.txt"), "wb") as handle:
            handle.write(b"SWAPPED")
        destination = os.path.join(roots["inputs"], "src")
        with self.assertRaises(ContractRefusal) as caught:
            workspaces._publish(origin, destination, measured, "a source")
        self.assertIn("changed while it was being delivered",
                      caught.exception.message)
        self.assertEqual(caught.exception.code, "digest")
        self.assertEqual(sorted(os.listdir(roots["inputs"])), [],
                         "a lost race left a staging tree behind")

    def test_no_refusal_leaves_a_staging_tree_behind(self):
        """Every refusal on the delivery path, and the same assertion each
        time: nothing under the inputs root that a caller could read."""
        origin = self.origin({"a.txt": b"one"})
        cases = {
            "the wrong type": self.source(origin, type="git"),
            "a missing member": {member: value
                                 for member, value in self.source(origin).items()
                                 if member != "destination"},
            "an escaping destination": self.source(origin,
                                                   destination="../out"),
        }
        for what, source in cases.items():
            with self.subTest(what=what):
                roots = self.workspace(f"assignment-{abs(hash(what))}")
                with self.assertRaises(ContractRefusal):
                    materialize_directory_source(source, origin=origin,
                                                 inputs=roots["inputs"])
                self.assertEqual(os.listdir(roots["inputs"]), [])


class OneAssignmentOneWorkspace(Workspace):

    def test_the_three_roots_are_siblings_and_never_nested(self):
        """A worker that could write into its own inputs would make the seal
        over them describe a tree that has since changed."""
        roots = self.workspace()
        self.assertEqual(sorted(roots), ["git", "inputs", "workspace"])
        for name, place in roots.items():
            for other, elsewhere in roots.items():
                if name == other:
                    continue
                with self.subTest(name=name, other=other):
                    self.assertFalse(place.startswith(elsewhere + os.sep))

    def test_two_assignments_share_nothing(self):
        first = self.workspace("assignment-a")
        second = self.workspace("assignment-b")
        for name in ("inputs", "workspace", "git"):
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
        for name in ("inputs", "workspace", "git"):
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
        materialize_directory_source(self.source(origin), origin=origin,
                                     inputs=roots["inputs"])
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


class FakeRepository:
    """A repository that answers the two questions and records both."""

    def __init__(self, refs=None, tree=None):
        self.refs = refs or {}
        self.tree = tree if tree is not None else {"README": b"hello"}
        self.calls = []

    def resolve(self, *, uri, ref):
        self.calls.append(("resolve", uri, ref))
        return self.refs.get(ref)

    def checkout(self, *, uri, revision, into, git_dir):
        self.calls.append(("checkout", uri, revision["hex"], into, git_dir))
        for path, content in self.tree.items():
            full = os.path.join(into, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "wb") as handle:
                handle.write(content)


class TheRevisionIsTheContractAndTheRefIsEvidence(Workspace):

    def git_source(self, **overrides):
        source = {"name": "repo", "type": "git",
                  "uri": "https://example.test/repo",
                  "destination": "repo", "required": True,
                  "repository_id": "repo-1", "object_format": "sha1",
                  "base_revision": dict(SHA1),
                  "source_ref": None, "integration_ref": None,
                  "acquisition_policy_digest": "sha256:" + "c" * 64}
        source.update(overrides)
        return source

    def deliver(self, repository, **overrides):
        roots = self.workspace(overrides.pop("assignment", "assignment-1"))
        return materialize_git_source(
            self.git_source(**overrides), git=GitPort(repository),
            inputs=roots["inputs"], git_metadata=roots["git"]), roots

    def test_the_pinned_revision_is_what_is_checked_out(self):
        repository = FakeRepository()
        answer, _ = self.deliver(repository)
        self.assertEqual(answer["base_revision"], SHA1)
        self.assertIn(("checkout", "https://example.test/repo", SHA1["hex"],
                       answer["destination"] + ".materializing",
                       answer["git_dir"]),
                      repository.calls)

    def test_an_advertised_ref_that_still_names_the_revision_is_accepted(self):
        repository = FakeRepository(refs={"refs/heads/main": dict(SHA1)})
        answer, _ = self.deliver(repository, source_ref="refs/heads/main")
        self.assertEqual(answer["base_revision"], SHA1)

    def test_a_ref_that_moved_refuses_rather_than_being_followed(self):
        """A source delivered from where the branch is NOW is not the source
        the assignment was made against."""
        repository = FakeRepository(refs={"refs/heads/main": dict(MOVED)})
        for member in ("source_ref", "integration_ref"):
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal) as caught:
                    self.deliver(repository,
                                 assignment=f"assignment-{member}",
                                 **{member: "refs/heads/main"})
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("policy", "denied"))
                self.assertIn("a ref that moved is evidence that it moved",
                              caught.exception.message)

    def test_a_ref_the_repository_does_not_carry_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.deliver(FakeRepository(), source_ref="refs/heads/gone")
        self.assertIn("does not carry", caught.exception.message)

    def test_a_revision_algorithm_that_is_not_the_object_format_refuses(self):
        """§12 rule 7: a sha1 revision under a sha256 repository is a different
        object namespace, not a shorter digest."""
        with self.assertRaises(ContractRefusal) as caught:
            self.deliver(FakeRepository(), object_format="sha256")
        self.assertIn("§12 rule 7", caught.exception.message)

    def test_each_source_gets_git_metadata_of_its_own(self):
        repository = FakeRepository()
        first, roots = self.deliver(repository)
        second = materialize_git_source(
            self.git_source(name="other", destination="other"),
            git=GitPort(repository), inputs=roots["inputs"],
            git_metadata=roots["git"])
        self.assertNotEqual(first["git_dir"], second["git_dir"])
        self.assertTrue(os.path.isdir(first["git_dir"]))

    def test_metadata_is_created_once_and_never_reused(self):
        """Shared Git metadata is one assignment able to move another's refs,
        prune another's objects, and decide what another's revision
        resolves to."""
        repository = FakeRepository()
        _, roots = self.deliver(repository)
        with self.assertRaises(ContractRefusal) as caught:
            materialize_git_source(
                self.git_source(destination="again"),
                git=GitPort(repository), inputs=roots["inputs"],
                git_metadata=roots["git"])
        self.assertIn("already exists", caught.exception.message)

    def test_what_the_checkout_wrote_is_measured_like_any_other_tree(self):
        """A checkout is somebody else's process writing into a directory this
        component owns, so its answer is evidence and the tree is the fact."""
        repository = FakeRepository(tree={"a.txt": b"one", "d/b.txt": b"two"})
        answer, _ = self.deliver(repository)
        self.assertEqual(answer["entry_count"], 2)
        self.assertEqual(answer["total_bytes"], 6)

    def test_a_checkout_that_writes_a_link_is_refused_and_leaves_nothing(self):
        class Linking(FakeRepository):
            def checkout(self, *, uri, revision, into, git_dir):
                super().checkout(uri=uri, revision=revision, into=into,
                                 git_dir=git_dir)
                os.symlink("/etc/hostname", os.path.join(into, "leak"))

        with self.assertRaises(ContractRefusal) as caught:
            answer, roots = self.deliver(Linking())
        self.assertIn("symbolic link", caught.exception.message)
        roots = assignment_workspace(self.storage, "assignment-1")
        self.assertEqual(os.listdir(roots["inputs"]), [])

    def test_a_repository_that_cannot_answer_is_refused_at_construction(self):
        class Partial:
            def resolve(self, **operands):
                return None

        for what, repository in [("no operations at all", object()),
                                 ("one operation missing", Partial())]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    GitPort(repository)


class TheComponentIsOnThePublicSurface(Workspace):

    def test_every_operation_this_cut_adds_is_exported(self):
        for name in workspaces.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(workspaces, name))


if __name__ == "__main__":
    unittest.main()
