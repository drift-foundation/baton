"""W71917 — the source/workspace boundary, from both sides of it.

WHAT THE RULING ASKS FOR, and each clause is a class below:

  one manager-validated nominated source, mounted READ-ONLY at
  `/input/source`, and a separate manager-created, manager-custodied,
  DISK-BACKED workspace mounted writable;
  an ordinary local path that does not walk, copy, snapshot, enumerate, hash
  or Git-process the nominated source;
  a Git-agnostic manager, with the version-control profile owned outside it;
  a declared workspace capacity proved at admission and bounded tmpfs
  scratch, with checkout, build/cache, test artifacts, output and logs not
  relying on scratch;
  restart adopting the EXACT manager-owned workspace, while foreign,
  symlinked or replaced source/workspace paths refuse before runtime start.

WHY THE NO-COPY CASE IS A SABOTAGE RATHER THAN AN INSPECTION. "This code does
not enumerate the source" is the kind of claim a reading proves badly: a walk
three calls down is still a walk, and an assertion about the module's text
would pass the day somebody adds one through a helper. So
`NothingReadsTheNominatedSource` REMOVES the ability to walk -- `os.walk`,
`os.listdir`, `os.scandir`, `directory_manifest` and `copied_manifest` all
raise -- and then drives the whole delivery. A path that enumerates anything
fails; a path that does not, cannot.

AND THE SOURCE IS BOOBY-TRAPPED BESIDES, because a sabotage proves the
manager's own frames and not the interpreter's. The nominated tree carries a
FIFO, an unreadable file and a directory the manager may not enter: a copier
would block on the first, fail on the second and refuse on the third, and a
delivery that stays green over all three is one that did not look.
"""

import os
import subprocess
import tempfile
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.worker_manager import ControlStore, oci, source_boundary
from baton_v12.worker_manager import workspaces
from baton_v12.worker_manager.source_boundary import (
    BACKING, DELIVERY, MEMORY_FILESYSTEMS, MIN_WORKSPACE_BYTES,
    NON_SCRATCH_USES, SCRATCH_BYTES, SOURCE_NAME, SOURCE_TARGET,
    WORKSPACE_TARGET, adopt_source_boundary, boundary_mounts,
    check_disk_backed, compose_source_boundary, declared_profile,
    filesystem_of, nominate_source, source_consumption, workspace_capacity)

from . import disk_roots, input_roots

ATTEMPT = "attempt-w71917-1"
IMAGE = "sha256:" + "e" * 64


# -- the bind-mount capability, probed rather than assumed -------------------
#
# W71917 run7 review [P0] asks for a REAL same-filesystem bind mount "at the
# authorized boundary where the required namespace capability is available",
# and that qualifier is the whole reason this probe exists: establishing one
# needs either privilege or an unprivileged mount namespace, and a managed
# turn has neither on every host.
#
# WHAT IS NOT SKIPPED IS THE BOUNDARY ITSELF. The refusal is proved without any
# capability by the case that reports the mountpoint through the kernel's own
# table, which is the fact the corrected code reads and which fails against the
# device-only implementation. The real bind adds that the kernel agrees with
# the model; it is not the only thing standing between this defect and a
# regression, so a host that cannot create one still runs a discriminating
# test rather than a green blank.

def _bind_argv(source, target):
    return ["unshare", "--mount", "--map-root-user",
            "mount", "--bind", source, target]


def _can_bind_mount():
    try:
        answer = subprocess.run(
            ["unshare", "--mount", "--map-root-user", "true"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False
    return answer.returncode == 0


def _bind(source, target):
    subprocess.run(_bind_argv(source, target), check=True, timeout=60)


def _unbind(target):
    subprocess.run(["unshare", "--mount", "--map-root-user",
                    "umount", target],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=60)


class BoundaryCase(unittest.TestCase):
    """One manager-owned storage root on real disk, and one nominated tree.

    THE STORAGE IS DISK-BACKED DELIBERATELY AND THE NOMINATION IS NOT
    NECESSARILY, which is the asymmetry the ruling creates: the workspace is
    this manager's and must be storage, while the nominated source is somebody
    else's directory and this manager takes no view of what it is on.
    """

    def setUp(self):
        self.root = disk_roots.disk_backed_under(self)
        self.storage = os.path.join(self.root, "storage")
        os.makedirs(self.storage)
        self.store = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="source-boundary-1",
            clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.store.close)
        self.group = input_roots.configured_group(self.store)
        self.source = os.path.join(self.root, "nominated")
        os.makedirs(os.path.join(self.source, "pkg"))
        with open(os.path.join(self.source, "pkg", "one.py"), "w",
                  encoding="utf-8") as writing:
            writing.write("# a file no manager reads\n")

    def roots(self, attempt=ATTEMPT):
        return workspaces.assignment_workspace(self.group, self.storage,
                                               attempt)

    def capacity(self):
        return workspace_capacity(MIN_WORKSPACE_BYTES + 1)

    def composed(self, attempt=ATTEMPT):
        roots = self.roots(attempt)
        return roots, compose_source_boundary(nominate_source(self.source),
                                              roots, self.capacity())


class TheRuntimeReceivesOneMountedSourceAndOneWritableWorkspace(BoundaryCase):
    """The positive path, end to end, down to the argv the engine receives."""

    def test_the_boundary_names_the_two_roots_and_the_mountpoint(self):
        roots, boundary = self.composed()
        self.assertEqual(boundary.source.place, self.source)
        self.assertEqual(boundary.workspace,
                         os.path.realpath(roots["workspace"]))
        self.assertEqual(boundary.mountpoint,
                         os.path.join(os.path.realpath(roots["inputs"]),
                                      SOURCE_NAME))
        self.assertTrue(os.path.isdir(boundary.mountpoint))

    def test_the_mountpoint_is_established_empty_and_nothing_is_copied(self):
        """The whole difference from the retired bootstrap, on disk.

        The copied bootstrap wrote the nominated tree into this directory. The
        replacement establishes it and leaves it alone, so what the manifest
        declares at that destination -- the empty tree -- is what is actually
        there.
        """
        _roots, boundary = self.composed()
        self.assertEqual(os.listdir(boundary.mountpoint), [])
        self.assertEqual(
            workspaces.directory_manifest(boundary.mountpoint),
            {"entries": [], "entry_count": 0, "total_bytes": 0,
             "tree_digest": digest([])})

    def test_the_two_binds_are_read_only_source_and_writable_workspace(self):
        _roots, boundary = self.composed()
        self.assertEqual(
            boundary_mounts(boundary),
            ((self.source, SOURCE_TARGET, False),
             (boundary.workspace, WORKSPACE_TARGET, True)))

    def test_the_start_vector_carries_the_read_only_source_bind(self):
        roots, boundary = self.composed()
        argv = oci.run_vector(
            "docker", image_digest=IMAGE, labels=_labels(),
            assignment_roots=roots, posture="execution",
            mounts=[{"source": roots["inputs"], "target": "/input",
                     "writable": False},
                    {"source": roots["workspace"], "target": "/output",
                     "writable": True}],
            source_delivered=boundary, name="runtime-1",
            workspace_group=self.group)
        self.assertIn(
            f"type=bind,source={self.source},target={SOURCE_TARGET},"
            f"readonly=true", argv)
        # AND THE WORKSPACE IS THE ONE WRITABLE BIND. A vector in which the
        # source were writable, or the workspace were not, would be the
        # boundary inverted rather than composed.
        writable = [one for one in argv
                    if one.startswith("type=bind,") and "readonly=false" in one]
        self.assertEqual(
            writable,
            [f"type=bind,source={os.path.realpath(roots['workspace'])},"
             f"target=/output,readonly=false"])

    def test_an_assignment_mount_at_the_source_target_is_refused(self):
        """Two binds on one path: the second hides the first, and neither this
        manager nor the engine says which the worker reads."""
        roots, boundary = self.composed()
        with self.assertRaises(ContractRefusal) as caught:
            oci.run_vector(
                "docker", image_digest=IMAGE, labels=_labels(),
                assignment_roots=roots, posture="execution",
                mounts=[{"source": roots["inputs"], "target": SOURCE_TARGET,
                         "writable": False}],
                source_delivered=boundary, name="runtime-collision",
                workspace_group=self.group)
        self.assertEqual(caught.exception.category, "policy")
        self.assertIn("already mounts", caught.exception.message)

    def test_a_source_landing_under_no_read_only_mount_is_refused(self):
        """A bind onto the image filesystem, or under something the worker may
        write, is not a delivery this adapter composes."""
        roots, boundary = self.composed()
        with self.assertRaises(ContractRefusal) as caught:
            oci.run_vector(
                "docker", image_digest=IMAGE, labels=_labels(),
                assignment_roots=roots, posture="execution",
                mounts=[{"source": roots["workspace"], "target": "/output",
                         "writable": True}],
                source_delivered=boundary, name="runtime-bare",
                workspace_group=self.group)
        self.assertEqual(caught.exception.category, "policy")
        self.assertIn("read-only mount", caught.exception.message)

    def test_a_boundary_from_another_assignment_is_refused(self):
        """W71917 second review [P1]: the cross-wire, and it is a real one.

        Every rule this family had passed while the read-only claim was false.
        Attempt A's boundary is composed GENUINELY, over a source that happens
        to be attempt B's workspace -- which is nothing to A, because B's roots
        are not A's and containment is asked about A's own. That boundary is
        then handed to a start carrying B's own genuinely allocated roots, so
        the same host directory reaches the container writable at `/output`
        and read-only at `/input/source`, and the worker can rewrite the Work
        it was given through the other name.

        The target rules cannot see this: the target is the constant, it is
        inside a read-only assignment mount, and the capability is one this
        manager minted. What was missing is the only question that separates
        them -- whose assignment it was proved over.
        """
        other = self.roots("attempt-w71917-cross")
        alias = os.path.realpath(other["workspace"])
        mine = self.roots(ATTEMPT)
        crossed = compose_source_boundary(nominate_source(alias), mine,
                                          self.capacity())
        with self.assertRaises(ContractRefusal) as caught:
            oci.run_vector(
                "docker", image_digest=IMAGE, labels=_labels(),
                assignment_roots=other, posture="execution",
                mounts=[{"source": other["inputs"], "target": "/input",
                         "writable": False},
                        {"source": other["workspace"], "target": "/output",
                         "writable": True}],
                source_delivered=crossed, name="runtime-crosswire",
                workspace_group=self.group)
        self.assertEqual(caught.exception.category, "policy")
        self.assertIn("proved over the workspace", caught.exception.message)

    def test_a_boundary_proved_over_another_input_root_is_refused(self):
        """The mountpoint half of the same question.

        A boundary whose workspace matched but whose mountpoint was
        established inside a different assignment's input root would bind over
        a directory this start never created.
        """
        roots, boundary = self.composed()
        other = self.roots("attempt-w71917-other-inputs")
        with self.assertRaises(ContractRefusal) as caught:
            oci.run_vector(
                "docker", image_digest=IMAGE, labels=_labels(),
                assignment_roots={"workspace": roots["workspace"],
                                  "inputs": other["inputs"]},
                posture="execution",
                mounts=[{"source": other["inputs"], "target": "/input",
                         "writable": False},
                        {"source": roots["workspace"], "target": "/output",
                         "writable": True}],
                source_delivered=boundary, name="runtime-other-inputs",
                workspace_group=self.group)
        self.assertEqual(caught.exception.category, "policy")
        self.assertIn("input root establishes", caught.exception.message)

    def test_a_source_replaced_after_adoption_never_reaches_the_argv(self):
        """W71917 second review [P1]: adoption proved an object and the argv
        was composed from a NAME.

        The directory is unlinked and recreated after the boundary is adopted,
        which is the substitution `nominate_source` cannot see by spelling and
        `adopt_source_boundary` has already run past. The last comparison this
        manager can make is where the binds are derived, so it is made there.
        """
        roots, boundary = self.composed()
        adopted = adopt_source_boundary(boundary, roots)
        replacement = os.path.join(self.root, "replacement")
        os.makedirs(replacement, exist_ok=True)
        os.rename(self.source, os.path.join(self.root, "displaced"))
        os.rename(replacement, self.source)
        self.assertNotEqual(os.lstat(self.source).st_ino, adopted.inode)
        with self.assertRaises(ContractRefusal) as caught:
            boundary_mounts(adopted)
        self.assertEqual(caught.exception.category, "integrity")
        self.assertIn("re-pointed", caught.exception.message)

    def test_a_start_composes_no_source_bind_without_a_boundary(self):
        """The pre-W71917 shape is an addition rather than a migration."""
        roots = self.roots()
        argv = oci.run_vector(
            "docker", image_digest=IMAGE, labels=_labels(),
            assignment_roots=roots, posture="execution",
            mounts=[{"source": roots["inputs"], "target": "/input",
                     "writable": False}],
            name="runtime-2", workspace_group=self.group)
        self.assertEqual([one for one in argv if SOURCE_TARGET in one], [])


class NothingReadsTheNominatedSource(BoundaryCase):
    """The no-copy, no-enumeration rule, proved by taking the ability away."""

    WALKERS = ("walk", "listdir", "scandir")

    def setUp(self):
        super().setUp()
        # A TREE THAT PUNISHES A COPIER, beside the sabotage. Each entry
        # defeats a different half of the retired bootstrap: an unreadable
        # file fails an `open`, a directory with no execute bit fails a
        # descent, and a FIFO makes a blocking `open` hang forever -- which is
        # the failure a test cannot even report, so it is the one most worth
        # making impossible.
        os.mkfifo(os.path.join(self.source, "pipe"))
        unreadable = os.path.join(self.source, "unreadable.txt")
        with open(unreadable, "w", encoding="utf-8") as writing:
            writing.write("nobody reads this\n")
        os.chmod(unreadable, 0o000)
        closed = os.path.join(self.source, "closed")
        os.makedirs(closed)
        os.chmod(closed, 0o000)
        self.addCleanup(os.chmod, closed, 0o700)

    def sabotaged(self):
        """Every way to enumerate a tree, replaced with a refusal.

        THE PATCHES LAND ON `os` AND ON THE MANAGER'S OWN COPIERS, which are
        two different escapes: a direct `os.walk` in this module, and a call
        into `workspaces` that walks on its behalf. Patching only the first
        would leave "the manager did not walk, its helper did", which is the
        distinction with no difference this Work exists to close.
        """
        patches = [mock.patch.object(os, name, side_effect=_walked)
                   for name in self.WALKERS]
        patches += [
            mock.patch.object(workspaces, "directory_manifest",
                              side_effect=_measured),
            mock.patch.object(workspaces, "copied_manifest",
                              side_effect=_measured)]
        for one in patches:
            one.start()
            self.addCleanup(one.stop)

    def test_the_whole_delivery_composes_with_no_walker_available(self):
        roots = self.roots()
        capacity = self.capacity()
        self.sabotaged()
        boundary = compose_source_boundary(nominate_source(self.source),
                                           roots, capacity)
        adopted = adopt_source_boundary(boundary, roots)
        self.assertEqual(boundary_mounts(adopted)[0],
                         (self.source, SOURCE_TARGET, False))

    def test_the_start_vector_composes_with_no_walker_available(self):
        roots, boundary = self.composed()
        self.sabotaged()
        argv = oci.run_vector(
            "docker", image_digest=IMAGE, labels=_labels(),
            assignment_roots=roots, posture="execution",
            mounts=[{"source": roots["inputs"], "target": "/input",
                     "writable": False},
                    {"source": roots["workspace"], "target": "/output",
                     "writable": True}],
            source_delivered=boundary, name="runtime-3",
            workspace_group=self.group)
        self.assertIn(
            f"type=bind,source={self.source},target={SOURCE_TARGET},"
            f"readonly=true", argv)

    def test_the_sabotage_can_actually_fail(self):
        """A walker that is not really disabled passes the cases above for the
        wrong reason, which is the failure mode of every check like this."""
        self.sabotaged()
        with self.assertRaises(AssertionError):
            os.listdir(self.source)
        with self.assertRaises(AssertionError):
            workspaces.directory_manifest(self.source)

    def test_the_cost_does_not_depend_on_what_is_in_the_tree(self):
        """One `lstat` and one `fstat`, whatever is behind the mount.

        Counting the syscalls a nomination makes is how "this is O(1) in the
        size of the source" becomes a measured fact rather than a claim about
        the code's shape.
        """
        for name in ("small", "large"):
            place = os.path.join(self.root, name)
            os.makedirs(place)
            for index in range(1 if name == "small" else 200):
                with open(os.path.join(place, f"{index}.txt"), "w",
                          encoding="utf-8") as writing:
                    writing.write("x" * 64)
        counted = {}
        for name in ("small", "large"):
            place = os.path.join(self.root, name)
            with mock.patch.object(os, "lstat",
                                   side_effect=os.lstat) as watching:
                nominate_source(place)
            counted[name] = watching.call_count
        self.assertEqual(counted["small"], counted["large"])


class TheManagerTakesNoViewOfVersionControl(BoundaryCase):
    """Git-agnostic, and the boundary is structural rather than a promise."""

    def test_a_tree_carrying_version_control_metadata_is_treated_the_same(
            self):
        """The one case a Git-aware manager would behave differently on."""
        plain = self.composed("attempt-plain")[1]
        os.makedirs(os.path.join(self.source, ".git", "objects"))
        with open(os.path.join(self.source, ".git", "HEAD"), "w",
                  encoding="utf-8") as writing:
            writing.write("ref: refs/heads/main\n")
        versioned = self.composed("attempt-versioned")[1]
        self.assertEqual(boundary_mounts(plain)[0],
                         boundary_mounts(versioned)[0])

    # `checkout` IS DELIBERATELY NOT ON THIS LIST, and the omission is the
    # distinction the whole class is about. It appears in `NON_SCRATCH_USES`
    # as the ruling's own name for one of the five things that must not rely
    # on scratch -- a property of a workspace, stated by a manager that has no
    # idea how a checkout is produced. The words below are version-control
    # ACTS and OBJECTS; naming one would be an inference, and naming a use is
    # not.
    VOCABULARY = ("git", "clone", "rev-parse", "refs", "hardlink", "worktree",
                  "submodule", "fetch")

    def test_the_boundary_module_names_no_version_control_vocabulary(self):
        """Read off the module, and off the RUNTIME pieces of it.

        SCANNED WITH `ast`, NOT AS TEXT, for the reason
        `tests/authority/test_boundary` gives about its own reach scan: this
        module's prose says, correctly, that the manager is Git-agnostic and
        that a Git-aware profile is somebody else's, and a checker that cannot
        tell a claim from a reach is a checker that punishes documentation. So
        what is scanned is every identifier and every string literal that is
        NOT a docstring -- the pieces the running code can actually use.

        WORD BOUNDARIES, because `isdigit` contains `git` and is not version
        control. The three-letter substring is exactly the kind of match that
        makes a word list untrustworthy, and untrustworthy is worse than
        absent.

        SCOPED TO THIS MODULE rather than the package, and the scope is the
        claim. W71917 is what introduced a nominated source, so this module is
        where a version-control inference would have been added; the manager's
        pre-existing vocabulary elsewhere -- a declared OUTPUT TYPE an
        assignment may name, for one -- is not this Work's to relitigate. The
        package-wide half of the same claim is
        `TheProfilesAreOwnedOutsideTheManager`, which proves the manager
        cannot reach the code where these words mean something.
        """
        import ast
        import pathlib
        import re
        place = pathlib.Path(source_boundary.__file__)
        tree = ast.parse(place.read_text(encoding="utf-8"), str(place))
        for piece in _runtime_pieces(tree):
            for word in self.VOCABULARY:
                with self.subTest(word=word, piece=piece[:60]):
                    self.assertIsNone(
                        re.search(rf"\b{word}\b", piece, re.IGNORECASE),
                        f"{place.name} names {word!r} in running code; the "
                        f"manager carries the profile as opaque text and "
                        f"reads nothing into it")

    def test_the_vocabulary_sweep_is_not_vacuous(self):
        """A sweep that resolves nothing passes the case above for the wrong
        reason -- and the words really are found where they DO belong."""
        import ast
        import pathlib
        import re
        from baton_v12.source_profiles import checkout
        place = pathlib.Path(checkout.__file__)
        pieces = list(_runtime_pieces(
            ast.parse(place.read_text(encoding="utf-8"), str(place))))
        self.assertGreater(len(pieces), 20)
        found = {word for word in self.VOCABULARY for piece in pieces
                 if re.search(rf"\b{word}\b", piece, re.IGNORECASE)}
        self.assertIn("git", found)
        self.assertIn("clone", found)

    def test_the_profile_word_crosses_without_being_interpreted(self):
        for profile in ("git", "generic", "svn", "something-nobody-wrote-yet"):
            with self.subTest(profile=profile):
                declared = source_consumption(profile)
                self.assertEqual(
                    declared[source_boundary.CONSUMPTION_KEY],
                    {"delivery": DELIVERY, "workspace": BACKING,
                     "profile": profile})
                self.assertEqual(
                    declared_profile({"consumption": declared}), profile)

    def test_a_descriptor_that_declares_no_boundary_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            declared_profile({"consumption": {"baton.directory/1": {}}})
        self.assertEqual(caught.exception.code, "schema")

    def test_a_declaration_naming_another_delivery_is_refused(self):
        for member, value in (("delivery", "staged-copy"),
                              ("workspace", "tmpfs")):
            with self.subTest(member=member):
                declared = source_consumption("generic")
                declared[source_boundary.CONSUMPTION_KEY][member] = value
                with self.assertRaises(ContractRefusal) as caught:
                    declared_profile({"consumption": declared})
                self.assertEqual((caught.exception.category,
                                  caught.exception.code),
                                 ("policy", "denied"))


class TheProfilesAreOwnedOutsideTheManager(unittest.TestCase):
    """The Git-aware and non-Git profiles, and the separation between them.

    IMPORTED HERE AND NOWHERE IN THE MANAGER, which is the property under
    test as much as anything either profile does.
    """

    def test_the_manager_does_not_import_the_profile_package(self):
        import ast
        import pathlib
        import baton_v12.worker_manager as package
        root = pathlib.Path(package.__file__).resolve().parent
        for place in sorted(root.rglob("*.py")):
            tree = ast.parse(place.read_text(encoding="utf-8"), str(place))
            for node in ast.walk(tree):
                named = []
                if isinstance(node, ast.Import):
                    named = [one.name for one in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    named = [node.module or ""]
                for one in named:
                    with self.subTest(source=place.name, module=one):
                        self.assertNotIn("source_profiles", one)

    def test_a_git_profile_clones_copy_safely_and_verifies_the_base(self):
        from baton_v12 import source_profiles
        base = "b" * 40
        plan = source_profiles.checkout_plan(
            SOURCE_TARGET, WORKSPACE_TARGET,
            profile=source_profiles.GIT_PROFILE, declared=base)
        clone, detach, verify = (one["argv"] for one in plan["steps"])
        # COPY-SAFE. Without these the clone hardlinks its objects to the
        # read-only mount's inodes, so the workspace and the nominated source
        # become two names for one object -- the aliasing the read-only bind
        # exists to prevent.
        self.assertIn("--no-hardlinks", clone)
        self.assertIn("--no-local", clone)
        # INSIDE THE WRITABLE WORKSPACE, never beside the mount.
        self.assertTrue(clone[-1].startswith(WORKSPACE_TARGET + "/"))
        self.assertEqual(clone[-2], SOURCE_TARGET)
        self.assertEqual(plan["source_root"], clone[-1])
        # THE WORKTREE IS PUT AT THE DECLARED COMMIT. W71917 run7 review [P1]:
        # cloning takes the source's CURRENT HEAD, so without this step the
        # worker edits whatever the mount happened to be on.
        self.assertEqual(detach[:2], ("git", "-C"))
        self.assertEqual(detach[2], clone[-1])
        self.assertEqual(detach[3:5], ("checkout", "--detach"))
        self.assertEqual(detach[-1], f"{base}^{{commit}}")
        # AND THE ACTIVE HEAD IS WHAT IS THEN CONFIRMED, against the declared
        # base. Asking whether the base EXISTS is what the superseded plan did,
        # and a repository can answer that yes while its worktree is elsewhere.
        self.assertEqual(verify[:2], ("git", "-C"))
        self.assertEqual(verify[2], clone[-1])
        self.assertEqual(verify[-3:], ("rev-parse", "--verify", "HEAD"))
        self.assertEqual([one["expect_stdout"] for one in plan["steps"]],
                         [None, None, base])

    def test_the_plan_lands_on_the_declared_base_when_source_head_moved_on(
            self):
        """W71917 run7 review [P1], against a REAL repository.

        The argv-shape case above cannot see this defect: clone-then-`rev-parse`
        composes perfectly well and both commands succeed. What distinguishes
        the plans is what the worktree ends up being, so this builds a source
        whose HEAD is a SECOND commit while the assignment declares the first,
        runs the plan's steps for real, and requires the checkout to be at the
        declared base with the declared base's content.

        Against the superseded plan the clone lands on the newer commit, both
        steps still exit zero, and this fails on the content assertion -- which
        is the worker editing the wrong revision.
        """
        import shutil
        import subprocess as run

        if shutil.which("git") is None:                  # pragma: no cover
            self.skipTest("this run has no git, so the real-repository "
                          "checkout cannot be exercised")
        from baton_v12 import source_profiles

        root = disk_roots.disk_backed_under(self)
        source = os.path.join(root, "source")
        os.makedirs(source)

        def git(*argv, where=source):
            answer = run.run(["git", "-C", where, *argv], check=True,
                             capture_output=True, text=True, timeout=120)
            return answer.stdout.strip()

        git("init", "--quiet", "-b", "main")
        git("config", "user.email", "w71917@example.invalid")
        git("config", "user.name", "W71917")
        with open(os.path.join(source, "file.txt"), "w",
                  encoding="utf-8") as writing:
            writing.write("the declared base\n")
        git("add", "file.txt")
        git("commit", "--quiet", "-m", "declared base")
        declared = git("rev-parse", "HEAD")
        # THE SOURCE MOVES ON, which is the whole point: it still CONTAINS the
        # declared commit, so an existence check is satisfied by it.
        with open(os.path.join(source, "file.txt"), "w",
                  encoding="utf-8") as writing:
            writing.write("somebody else's later work\n")
        git("commit", "--quiet", "-am", "later work")
        self.assertNotEqual(git("rev-parse", "HEAD"), declared)

        workspace = os.path.join(root, "workspace")
        os.makedirs(workspace)
        plan = source_profiles.checkout_plan(
            source, workspace, profile=source_profiles.GIT_PROFILE,
            declared=declared)
        for step in plan["steps"]:
            answer = run.run(list(step["argv"]), capture_output=True,
                             text=True, timeout=300)
            self.assertEqual(answer.returncode, 0,
                             f"{step['argv']} failed: {answer.stderr}")
            if step["expect_stdout"] is not None:
                self.assertEqual(answer.stdout.strip(), step["expect_stdout"],
                                 "the checkout is not at the declared base")
        # THE WORKTREE IS THE DECLARED COMMIT, by its content and not only by
        # a ref: a plan that resolved the ref while leaving the tree alone
        # would pass the step above and fail here.
        with open(os.path.join(plan["source_root"], "file.txt"),
                  encoding="utf-8") as reading:
            self.assertEqual(reading.read(), "the declared base\n")
        # AND THE MOUNT IS UNTOUCHED, still on its own later commit.
        self.assertNotEqual(git("rev-parse", "HEAD"), declared)

    def test_a_generic_profile_uses_the_same_boundary_with_no_inference(self):
        from baton_v12 import source_profiles
        plan = source_profiles.checkout_plan(
            SOURCE_TARGET, WORKSPACE_TARGET,
            profile=source_profiles.GENERIC_PROFILE)
        # NO STEPS AT ALL, and the mount IS the source root: the generic
        # profile is not a degraded Git one, it is the same delivery with no
        # version-control act in it.
        self.assertEqual(plan["steps"], ())
        self.assertEqual(plan["source_root"], SOURCE_TARGET)
        self.assertEqual(plan["workspace"], WORKSPACE_TARGET)
        self.assertNotIn("base", plan)

    def test_a_generic_profile_carrying_a_base_is_refused(self):
        from baton_v12 import source_profiles
        with self.assertRaises(source_profiles.ProfileRefusal):
            source_profiles.checkout_plan(
                SOURCE_TARGET, WORKSPACE_TARGET,
                profile=source_profiles.GENERIC_PROFILE, declared="c" * 40)

    def test_a_git_profile_without_a_base_is_refused(self):
        from baton_v12 import source_profiles
        with self.assertRaises(source_profiles.ProfileRefusal):
            source_profiles.checkout_plan(
                SOURCE_TARGET, WORKSPACE_TARGET,
                profile=source_profiles.GIT_PROFILE)

    def test_an_abbreviated_base_is_refused_rather_than_resolved(self):
        """Expanding one would make this composer ask the mount a question,
        and the answer would decide which object gets verified."""
        from baton_v12 import source_profiles
        for declared in ("b" * 7, "b" * 39, "B" * 40, "z" * 40, ""):
            with self.subTest(declared=declared):
                with self.assertRaises(source_profiles.ProfileRefusal):
                    source_profiles.check_declared_base(declared)

    def test_both_object_widths_are_accepted_and_never_converted(self):
        from baton_v12 import source_profiles
        for width, kind in source_profiles.BASE_KINDS.items():
            with self.subTest(width=width):
                base = "a" * width
                plan = source_profiles.checkout_plan(
                    SOURCE_TARGET, WORKSPACE_TARGET,
                    profile=source_profiles.GIT_PROFILE, declared=base)
                self.assertEqual(plan["base"], base)
                self.assertEqual(plan["base_kind"], kind)


class TheWorkspaceIsStorageAndScratchIsBounded(BoundaryCase):
    """Kernel-bounded scratch, a DECLARED capacity, and the rule that
    separates them.

    W71917's approved ruling: scratch is bounded and the workspace is not. The
    two used to be described as one thing, and the cases below hold each to
    what it actually does -- the tmpfs mounts carry a size the kernel applies,
    and the workspace declaration is proved once at admission and applied to
    nothing afterwards.
    """

    def test_the_runtime_gets_exactly_the_declared_bounded_scratch(self):
        composed = [value for flag, value in oci.RESTRICTIONS
                    if flag == "--tmpfs"]
        self.assertEqual(
            composed,
            [f"{target}:rw,noexec,nosuid,nodev,size={one >> 20}m"
             for target, one in source_boundary.SCRATCH_MOUNTS])
        # AND IT IS SMALL, PRIVATE AND NON-EXECUTABLE, which is what makes it
        # scratch rather than a workspace.
        for value in composed:
            self.assertIn("noexec", value)
            self.assertIn("nosuid", value)
            self.assertIn("nodev", value)

    def test_a_workspace_on_a_memory_filesystem_is_refused(self):
        """The ruled uses do not rely on scratch, and this is where that is
        enforced rather than documented."""
        memory = _memory_backed_directory(self)
        with self.assertRaises(ContractRefusal) as caught:
            check_disk_backed(memory)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        for use in NON_SCRATCH_USES:
            self.assertIn(use, caught.exception.message)

    def test_the_composed_workspace_is_proved_to_be_storage(self):
        roots = self.roots()
        capacity = self.capacity()
        with mock.patch.object(source_boundary, "filesystem_of",
                               return_value="tmpfs"):
            with self.assertRaises(ContractRefusal) as caught:
                compose_source_boundary(nominate_source(self.source), roots,
                                        capacity)
        self.assertEqual(caught.exception.category, "policy")

    def test_a_capacity_no_larger_than_the_scratch_bound_is_refused(self):
        """THE DETERMINISTIC >64 MiB PROOF, as a rule rather than a run.

        A workspace declared no larger than the private scratch beside it is a
        workspace whose entire contents would have fitted in that scratch --
        so a checkout, a build cache, test artifacts, the output and the logs
        could all have lived in memory and nothing about the delivery would
        say otherwise. The floor is the whole scratch bound and the comparison
        is strict, so the smallest admissible workspace is already one byte
        more than every memory filesystem the runtime has.
        """
        self.assertGreater(MIN_WORKSPACE_BYTES, SCRATCH_BYTES)
        for value in (1, SCRATCH_BYTES, MIN_WORKSPACE_BYTES):
            with self.subTest(max_bytes=value):
                with self.assertRaises(ContractRefusal) as caught:
                    workspace_capacity(value)
                self.assertEqual(caught.exception.category, "policy")
        self.assertEqual(workspace_capacity(MIN_WORKSPACE_BYTES + 1).max_bytes,
                         MIN_WORKSPACE_BYTES + 1)

    def test_a_declared_capacity_is_one_positive_whole_number(self):
        for max_bytes in (None, True, -1, 0, "many", 1.5):
            with self.subTest(max_bytes=max_bytes):
                with self.assertRaises(ContractRefusal):
                    workspace_capacity(max_bytes)

    def test_a_declared_capacity_carries_no_entry_ceiling(self):
        """The [P1] the run7 review found, as a rule rather than a docstring.

        `max_entries` was declared beside `max_bytes`, validated against this
        build's own bound, carried into the composed boundary -- and then
        reached no mount, no runtime and no sweep. A number nothing applies is
        a limit's name over no mechanism, which is the one shape the ruling
        does not permit, so the member is GONE rather than documented as
        inert. This fails against an implementation that keeps it.
        """
        declared = self.capacity()
        self.assertEqual(source_boundary.WorkspaceCapacity.__slots__,
                         ("max_bytes",))
        self.assertFalse(hasattr(declared, "max_entries"))
        with self.assertRaises(TypeError):
            workspace_capacity(MIN_WORKSPACE_BYTES + 1, 2000)
        # AND IT DOES NOT REAPPEAR ONE LAYER ALONG. The composed boundary is
        # what every later component reads, and the runtime binds are what the
        # engine receives; neither may carry a ceiling the delivery cannot
        # apply.
        _roots, boundary = self.composed()
        self.assertEqual(boundary.capacity, declared)
        self.assertFalse(hasattr(boundary.capacity, "max_entries"))
        workspace = [one for one in boundary_mounts(boundary) if one[2]]
        self.assertEqual(workspace, [(boundary.workspace, WORKSPACE_TARGET,
                                      True)])

    def test_the_declared_capacity_is_proved_and_not_reserved(self):
        """Admission evidence about an INSTANT, which is what the ruling says
        it is.

        A reservation would make the second assignment's proof answer against
        what the first one took. Nothing is taken, so the filesystem reports
        the same free bytes to both and both are admitted -- which is the
        deployment exposure `DEPLOYMENT.md` states out loud rather than the
        bound the old name implied. An implementation that deducted an
        admitted declaration from a pool would refuse the second here.

        The filesystem's answer is FIXED for the duration rather than read for
        real, because a host with room to spare would admit both whatever this
        component did and the case would prove nothing.
        """
        declared = self.capacity()
        allocated = [self.roots("attempt-w71917-capacity-a"),
                     self.roots("attempt-w71917-capacity-b")]

        class Exactly:
            f_bavail = declared.max_bytes
            f_frsize = 1

        with mock.patch.object(os, "statvfs", return_value=Exactly()):
            for roots in allocated:
                with self.subTest(workspace=roots["workspace"]):
                    boundary = compose_source_boundary(
                        nominate_source(self.source), roots, declared)
                    self.assertEqual(boundary.capacity, declared)

    def test_a_capacity_the_storage_cannot_meet_is_refused_before_the_start(
            self):
        roots = self.roots()
        capacity = self.capacity()

        class Full:
            f_bavail = 1
            f_frsize = 512

        with mock.patch.object(os, "statvfs", return_value=Full()):
            with self.assertRaises(ContractRefusal) as caught:
                compose_source_boundary(nominate_source(self.source), roots,
                                        capacity)
        self.assertEqual(caught.exception.code, "limit")

    @unittest.skipUnless(
        os.environ.get("BATON_V12_LARGE_WORKSPACE_PROOF") == "1",
        "the >64 MiB disk-workspace proof writes more than the bootstrap "
        "container's whole 64 MiB tmpfs; set "
        "BATON_V12_LARGE_WORKSPACE_PROOF=1 on a host with room to run it")
    def test_more_than_the_scratch_bound_really_fits_in_the_workspace(self):
        """The rule above, executed rather than argued.

        DELIBERATELY GATED. This writes `MIN_WORKSPACE_BYTES + 1` bytes -- more
        than the runtime's entire private scratch -- which is the point of it
        and also why it must not run inside a bootstrap container whose own
        `/tmp` is that size. The rule it demonstrates is checked
        unconditionally by the case above; this is the demonstration that the
        rule is about real bytes on real storage.

        WHAT IT PROVES THAT THE RULE CANNOT. That the workspace the boundary
        composed actually accepts the declared volume, and that writing it
        touches no memory filesystem: the scratch directories are measured
        before and after and must not have moved.
        """
        _roots, boundary = self.composed()
        scratch = tempfile.gettempdir()
        before = os.statvfs(scratch).f_bavail
        place = os.path.join(boundary.workspace, "large-proof.bin")
        block = b"\0" * (1024 * 1024)
        written = 0
        with open(place, "wb") as writing:
            while written <= MIN_WORKSPACE_BYTES:
                writing.write(block)
                written += len(block)
        self.addCleanup(os.unlink, place)
        self.assertGreater(os.stat(place).st_size, MIN_WORKSPACE_BYTES)
        self.assertGreater(os.stat(place).st_size, SCRATCH_BYTES)
        self.assertNotIn(filesystem_of(place), MEMORY_FILESYSTEMS)
        if filesystem_of(scratch) in MEMORY_FILESYSTEMS:
            # A MEMORY SCRATCH THAT DID NOT SHRINK is the evidence that none of
            # this went through it. Compared with slack, because an unrelated
            # process on the host may also be using `/tmp`.
            self.assertGreater(os.statvfs(scratch).f_bavail,
                               before - (SCRATCH_BYTES // 4096))


class ForeignSymlinkedOrReplacedPathsRefuseBeforeTheStart(BoundaryCase):
    """The negative half, and every case refuses with no runtime started."""

    def test_a_symlinked_nominated_source_is_refused(self):
        linked = os.path.join(self.root, "linked")
        os.symlink(self.source, linked)
        with self.assertRaises(ContractRefusal) as caught:
            nominate_source(linked)
        self.assertEqual(caught.exception.code, "path")
        self.assertIn("link", caught.exception.message)

    def test_a_nominated_source_with_a_linked_ancestor_is_refused(self):
        """The escape that looks perfectly ordinary until it is followed."""
        os.makedirs(os.path.join(self.root, "real", "tree"))
        os.symlink(os.path.join(self.root, "real"),
                   os.path.join(self.root, "alias"))
        with self.assertRaises(ContractRefusal) as caught:
            nominate_source(os.path.join(self.root, "alias", "tree"))
        self.assertEqual(caught.exception.code, "path")

    def test_a_nominated_source_that_is_not_a_directory_is_refused(self):
        place = os.path.join(self.root, "a-file")
        with open(place, "w", encoding="utf-8") as writing:
            writing.write("not a tree\n")
        with self.assertRaises(ContractRefusal) as caught:
            nominate_source(place)
        self.assertEqual(caught.exception.code, "file-type")

    def test_a_relative_traversing_or_colon_bearing_path_is_refused(self):
        for place in ("relative/source", "/srv/../etc", "/srv/a:b",
                      "/srv/source/", "/srv//source"):
            with self.subTest(place=place):
                with self.assertRaises(ContractRefusal):
                    nominate_source(place)

    def test_a_source_replaced_after_the_proof_refuses_at_adoption(self):
        """A path re-pointed at another tree resolves to the same characters
        and a different inode, which is what the pinned identity is for."""
        roots, boundary = self.composed()
        replacement = os.path.join(self.root, "replacement")
        os.makedirs(replacement)
        os.rename(self.source, os.path.join(self.root, "moved-aside"))
        os.rename(replacement, self.source)
        with self.assertRaises(ContractRefusal) as caught:
            adopt_source_boundary(boundary, roots)
        self.assertEqual(caught.exception.code, "path")
        self.assertIn("another tree", caught.exception.message)

    def test_a_source_that_became_a_link_refuses_at_adoption(self):
        roots, boundary = self.composed()
        os.rename(self.source, os.path.join(self.root, "moved"))
        os.symlink(os.path.join(self.root, "moved"), self.source)
        with self.assertRaises(ContractRefusal):
            adopt_source_boundary(boundary, roots)

    def test_a_source_that_vanished_refuses_at_adoption(self):
        roots, boundary = self.composed()
        os.rename(self.source, os.path.join(self.root, "gone"))
        with self.assertRaises(ContractRefusal):
            adopt_source_boundary(boundary, roots)

    def test_a_source_inside_the_manager_s_own_roots_is_refused(self):
        """Two names for one directory with two writabilities."""
        roots = self.roots()
        capacity = self.capacity()
        for name in ("workspace", "inputs"):
            with self.subTest(root=name):
                inside = os.path.join(os.path.realpath(roots[name]), "nested")
                os.makedirs(inside, exist_ok=True)
                with self.assertRaises(ContractRefusal) as caught:
                    compose_source_boundary(nominate_source(inside), roots,
                                            capacity)
                self.assertEqual(caught.exception.category, "policy")

    def test_a_source_containing_the_manager_s_own_roots_is_refused(self):
        roots = self.roots()
        with self.assertRaises(ContractRefusal) as caught:
            compose_source_boundary(nominate_source(self.storage), roots,
                                    self.capacity())
        self.assertEqual(caught.exception.category, "policy")

    def test_roots_a_caller_composed_are_refused(self):
        """`AllocatedRoots` is what makes the workspace manager-created; a
        plain mapping would let a caller name any two directories."""
        roots = self.roots()
        with self.assertRaises(ContractRefusal) as caught:
            compose_source_boundary(nominate_source(self.source),
                                    dict(roots), self.capacity())
        self.assertEqual(caught.exception.category, "policy")

    def test_a_nomination_a_caller_minted_is_refused(self):
        roots = self.roots()
        with self.assertRaises(ContractRefusal):
            source_boundary.NominatedSource(self.source, 1, 1)
        with self.assertRaises(ContractRefusal) as caught:
            compose_source_boundary(self.source, roots, self.capacity())
        self.assertEqual(caught.exception.category, "policy")

    def test_a_boundary_a_caller_minted_is_refused(self):
        with self.assertRaises(ContractRefusal):
            source_boundary.SourceBoundary(None, "/w", "/m", None, 1, 1,
                                           2, 2)
        with self.assertRaises(ContractRefusal):
            source_boundary.WorkspaceCapacity(1 << 30)

    def test_a_composed_boundary_cannot_be_retargeted(self):
        _roots, boundary = self.composed()
        for name, value in (("source", None), ("workspace", "/elsewhere"),
                            ("mountpoint", "/elsewhere")):
            with self.subTest(member=name):
                with self.assertRaises(ContractRefusal):
                    setattr(boundary, name, value)

    def test_a_workspace_replaced_by_a_link_refuses_at_adoption(self):
        """A workspace that moved between composition and start is not the one
        this manager holds custody of."""
        roots, boundary = self.composed()
        elsewhere = os.path.join(self.root, "elsewhere")
        os.makedirs(elsewhere)
        os.rename(roots["workspace"], os.path.join(self.root, "moved-away"))
        os.symlink(elsewhere, roots["workspace"])
        with self.assertRaises(ContractRefusal) as caught:
            adopt_source_boundary(boundary, roots)
        self.assertEqual(caught.exception.code, "path")
        self.assertIn("custody", caught.exception.message)

    def test_a_workspace_that_vanished_refuses_at_adoption(self):
        roots, boundary = self.composed()
        os.rename(roots["workspace"], os.path.join(self.root, "gone-away"))
        with self.assertRaises(ContractRefusal) as caught:
            adopt_source_boundary(boundary, roots)
        self.assertEqual(caught.exception.code, "path")

    def test_a_mountpoint_replaced_by_a_link_refuses_at_adoption(self):
        roots, boundary = self.composed()
        elsewhere = os.path.join(self.root, "somewhere-else")
        os.makedirs(elsewhere)
        os.chmod(os.path.realpath(roots["inputs"]), 0o700)
        os.rmdir(boundary.mountpoint)
        os.symlink(elsewhere, boundary.mountpoint)
        with self.assertRaises(ContractRefusal) as caught:
            adopt_source_boundary(boundary, roots)
        self.assertEqual(caught.exception.code, "path")

    def test_a_link_at_the_mountpoint_name_is_never_established_over(self):
        roots = self.roots()
        inputs = os.path.realpath(roots["inputs"])
        os.symlink(self.source, os.path.join(inputs, SOURCE_NAME))
        with self.assertRaises(ContractRefusal) as caught:
            compose_source_boundary(nominate_source(self.source), roots,
                                    self.capacity())
        self.assertEqual(caught.exception.code, "path")


class ARestartAdoptsTheExactManagerOwnedWorkspace(BoundaryCase):
    """Reopening an attempt is not reusing an identity."""

    def test_a_second_incarnation_adopts_the_same_roots_and_mountpoint(self):
        first_roots, first = self.composed()
        # A FRESH INCARNATION: the store is reopened and the roots are ADOPTED
        # rather than allocated, which is what a restarted manager does.
        adopted_roots = workspaces.adopted_assignment_workspace(self.storage,
                                                               ATTEMPT)
        second = compose_source_boundary(nominate_source(self.source),
                                         adopted_roots, self.capacity())
        self.assertEqual(second.workspace, first.workspace)
        self.assertEqual(second.mountpoint, first.mountpoint)
        self.assertEqual((second.device, second.inode),
                         (first.device, first.inode))
        again = adopt_source_boundary(second, adopted_roots)
        self.assertEqual(again.workspace, first.workspace)

    def test_a_source_replaced_while_the_manager_was_down_is_refused(self):
        """W71917 run7 review [P1], and it is the case the class was missing.

        The case above nominates the SAME unchanged directory in both
        incarnations, so it cannot see this: a second incarnation recomposes
        its boundary from configuration, and comparing that fresh reading with
        itself always agrees. What catches a replacement is the identity an
        EARLIER incarnation durably recorded.

        Here the nominated directory is genuinely replaced between the two
        incarnations -- unlinked and recreated at the same path, which is what
        a checkout being re-made looks like -- so every question about its
        spelling still passes and the object is different. Without the pinned
        pair this passes and a runtime starts over material nobody nominated.
        """
        _first_roots, first = self.composed()
        # BOTH PAIRS, SOURCE FIRST. W71917 third review [P1] made the pinned
        # evidence cover both roots; this case is still about the source half
        # and passes the workspace's real identity beside it so that the half
        # under test is the only thing that can refuse.
        pinned = ((first.device, first.inode),
                  (first.workspace_device, first.workspace_inode))
        replaced = self.source + "-replacement"
        os.rename(self.source, replaced)
        os.makedirs(self.source)
        with open(os.path.join(self.source, "somebody-elses.txt"), "w",
                  encoding="utf-8") as writing:
            writing.write("a different tree at the same path\n")
        adopted_roots = workspaces.adopted_assignment_workspace(self.storage,
                                                                ATTEMPT)
        second = compose_source_boundary(nominate_source(self.source),
                                         adopted_roots, self.capacity())
        # THE RECOMPOSED BOUNDARY AGREES WITH ITSELF, which is the whole point:
        # the in-memory gate cannot tell that anything happened.
        self.assertNotEqual((second.device, second.inode), pinned[0])
        adopt_source_boundary(second, adopted_roots)
        # AND THE PINNED PAIR REFUSES IT.
        with self.assertRaises(ContractRefusal) as caught:
            adopt_source_boundary(second, adopted_roots, pinned=pinned)
        # THE SAME CATEGORY AND CODE THE NEIGHBOURING SOURCE-REPLACEMENT
        # REFUSAL CARRIES, because it is the same fact arriving by the other
        # route: the path names an object this manager did not prove.
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "path"))
        self.assertIn("earlier incarnation", caught.exception.message)

    def test_a_real_directory_replacing_the_workspace_is_refused(self):
        """W71917 third review [P1]: the writable half had only a PATHNAME.

        The source carried a proved object and the workspace carried its
        spelling, so a real directory created at the workspace's path after
        composition passed every question adoption asked -- it resolves to the
        same characters, it is a directory of its own, and it is on real
        storage. The only existing replacement case substitutes a SYMLINK,
        which the spelling checks already catch; a real directory is the shape
        that distinguishes path identity from object identity.

        This is the half an assignment's answer is collected out of, so a
        runtime started over it would write into material this manager never
        took custody of.
        """
        roots, boundary = self.composed()
        held = os.path.realpath(roots["workspace"])
        os.rename(held, held + "-displaced")
        os.makedirs(held)
        self.assertNotEqual(os.lstat(held).st_ino, boundary.workspace_inode)
        with self.assertRaises(ContractRefusal) as caught:
            adopt_source_boundary(boundary, roots)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "path"))
        self.assertIn("names another directory", caught.exception.message)

    def test_a_workspace_replaced_while_the_manager_was_down_is_refused(self):
        """The restart half of the same question, and the one the in-memory
        gate cannot answer.

        A second incarnation recomposes its boundary from the roots it
        allocates, so it proves whatever directory is there and agrees with
        itself. What catches the replacement is the object an EARLIER
        incarnation durably recorded -- the same argument the source pair is
        under, now applied to the root the acceptance clause names beside it.
        """
        _roots, first = self.composed()
        pinned = ((first.device, first.inode),
                  (first.workspace_device, first.workspace_inode))
        held = os.path.realpath(first.workspace)
        os.rename(held, held + "-displaced")
        os.makedirs(held)
        adopted_roots = workspaces.adopted_assignment_workspace(self.storage,
                                                                ATTEMPT)
        second = compose_source_boundary(nominate_source(self.source),
                                         adopted_roots, self.capacity())
        # THE RECOMPOSED BOUNDARY AGREES WITH ITSELF, which is the point.
        self.assertNotEqual(
            (second.workspace_device, second.workspace_inode), pinned[1])
        adopt_source_boundary(second, adopted_roots)
        # AND THE PINNED PAIR REFUSES IT.
        with self.assertRaises(ContractRefusal) as caught:
            adopt_source_boundary(second, adopted_roots, pinned=pinned)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "path"))
        self.assertIn("earlier incarnation", caught.exception.message)

    def test_a_workspace_replaced_after_adoption_never_reaches_the_argv(self):
        """The last manager-owned boundary, for the writable root.

        `boundary_mounts` re-proves the source object there because adoption
        is not the last moment anything can change. The workspace is bound by
        the same argv and is subject to the same interval, so it is proved in
        the same place.
        """
        roots, boundary = self.composed()
        adopted = adopt_source_boundary(boundary, roots)
        held = os.path.realpath(adopted.workspace)
        os.rename(held, held + "-displaced")
        os.makedirs(held)
        with self.assertRaises(ContractRefusal) as caught:
            boundary_mounts(adopted)
        self.assertEqual(caught.exception.category, "integrity")
        self.assertIn("re-pointed", caught.exception.message)

    def test_an_unchanged_source_still_adopts_against_its_pinned_identity(
            self):
        """The ordinary restart, which must not be made to refuse by the gate
        that catches the replacement."""
        _roots, first = self.composed()
        adopted_roots = workspaces.adopted_assignment_workspace(self.storage,
                                                                ATTEMPT)
        second = compose_source_boundary(nominate_source(self.source),
                                         adopted_roots, self.capacity())
        again = adopt_source_boundary(
            second, adopted_roots,
            pinned=((first.device, first.inode),
                    (first.workspace_device, first.workspace_inode)))
        self.assertEqual((again.device, again.inode),
                         (first.device, first.inode))
        self.assertEqual((again.workspace_device, again.workspace_inode),
                         (first.workspace_device, first.workspace_inode))

    def test_a_same_incarnation_substitution_refuses_before_the_start(self):
        """The window between composition and start, in one process.

        The in-memory pair catches this one, and the case exists because the
        review named the window explicitly: everything between composition and
        the runtime start -- the input root, the retained manifest, the launch
        document, the credential delivery -- takes time a host is free to
        change things in.
        """
        roots, boundary = self.composed()
        replaced = self.source + "-substituted"
        os.rename(self.source, replaced)
        os.makedirs(self.source)
        with open(os.path.join(self.source, "substituted.txt"), "w",
                  encoding="utf-8") as writing:
            writing.write("swapped in after composition\n")
        with self.assertRaises(ContractRefusal) as caught:
            adopt_source_boundary(boundary, roots)
        self.assertIn("not the directory this manager proved",
                      caught.exception.message)

    def test_the_mountpoint_is_adopted_rather_than_created_twice(self):
        _roots, first = self.composed()
        marker = os.path.join(os.path.dirname(first.mountpoint), "marker")
        with open(marker, "w", encoding="utf-8") as writing:
            writing.write("still the same root\n")
        adopted_roots = workspaces.adopted_assignment_workspace(self.storage,
                                                               ATTEMPT)
        second = compose_source_boundary(nominate_source(self.source),
                                         adopted_roots, self.capacity())
        self.assertEqual(second.mountpoint, first.mountpoint)
        self.assertTrue(os.path.exists(marker))

    def test_another_attempt_never_receives_this_attempt_s_workspace(self):
        _roots, mine = self.composed("attempt-mine")
        _other_roots, theirs = self.composed("attempt-theirs")
        self.assertNotEqual(mine.workspace, theirs.workspace)
        self.assertNotEqual(mine.mountpoint, theirs.mountpoint)

    def test_a_foreign_workspace_root_is_refused_rather_than_adopted(self):
        """A home whose entry is a link to another attempt's root is still
        contained by manager storage, and is still not this attempt's."""
        self.composed("attempt-first")
        home = os.path.join(self.storage, "attempt-second")
        os.makedirs(home)
        os.symlink(os.path.join(self.storage, "attempt-first", "workspace"),
                   os.path.join(home, "workspace"))
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.adopted_assignment_workspace(self.storage,
                                                    "attempt-second")
        # `policy/denied`, which is the pair this manager already answers a
        # foreign root with. The code is read off the behaviour rather than
        # asserted from this file's expectation of it: what matters here is
        # that adoption REFUSES, and which closed pair it uses is
        # `workspaces`' own long-standing decision.
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))


class CleanupNeverRemovesMaterialThisManagerDidNotCreate(BoundaryCase):
    """The hazard the mountpoint introduces, and the guard that closes it."""

    def test_a_foreign_mount_under_a_root_refuses_before_anything_is_removed(
            self):
        """A mountpoint is not a symbolic link, so `followlinks=False` does
        not stop a removal walk descending through one."""
        _roots, boundary = self.composed()
        inputs = os.path.dirname(boundary.mountpoint)
        os.chmod(inputs, 0o700)
        kept = os.path.join(boundary.mountpoint, "somebody-elses-file")
        with open(kept, "w", encoding="utf-8") as writing:
            writing.write("material this manager did not create\n")
        # THE DEVICE IS WHAT A MOUNT CHANGES, so a foreign mount is simulated
        # by making the mountpoint answer another one. Actually mounting would
        # need privilege this test does not have and should not want.
        real = os.lstat

        def elsewhere(place, *rest, **named):
            held = real(place, *rest, **named)
            if str(place) == boundary.mountpoint:
                return os.stat_result(
                    tuple(held)[:2] + (held.st_dev + 1,) + tuple(held)[3:])
            return held

        with mock.patch.object(os, "lstat", side_effect=elsewhere):
            with self.assertRaises(ContractRefusal) as caught:
                workspaces.discard_workspace(self.storage, ATTEMPT)
        self.assertEqual(caught.exception.category, "policy")
        self.assertTrue(os.path.exists(kept),
                        "the removal touched material behind the mountpoint")

    def test_a_same_filesystem_mount_is_refused_though_its_device_matches(
            self):
        """W71917 run7 review [P0]: the device number cannot see a bind mount.

        The case above simulates a mount by changing `st_dev`, which is what a
        CROSS-DEVICE mount changes. A bind mount from the same filesystem keeps
        the bound directory's device number, so the tree it exposes has exactly
        the device the removal walk is comparing against -- and the old check
        walked straight into it.

        Here the device is left alone and the KERNEL'S TABLE is what names the
        mountpoint, which is the fact the corrected boundary reads. This case
        fails against the device-only implementation: it would find nothing
        wrong and unlink the file below.
        """
        _roots, boundary = self.composed()
        inputs = os.path.dirname(boundary.mountpoint)
        os.chmod(inputs, 0o700)
        kept = os.path.join(boundary.mountpoint, "somebody-elses-file")
        with open(kept, "w", encoding="utf-8") as writing:
            writing.write("material this manager did not create\n")
        # THE DEVICE IS DELIBERATELY UNTOUCHED. Anything that made it differ
        # would be re-testing the case above.
        self.assertEqual(os.lstat(boundary.mountpoint).st_dev,
                         os.lstat(self.storage).st_dev)
        held = workspaces.mount_table

        def also_mounted(**named):
            return list(held(**named)) + [(boundary.mountpoint, "ext4")]

        with mock.patch.object(workspaces, "mount_table",
                               side_effect=also_mounted):
            with self.assertRaises(ContractRefusal) as caught:
                workspaces.discard_workspace(self.storage, ATTEMPT)
        self.assertEqual(caught.exception.category, "policy")
        self.assertIn("mount point", caught.exception.message)
        self.assertTrue(os.path.exists(kept),
                        "the removal walked into a same-filesystem mount")

    def test_a_mount_holding_a_nested_directory_loses_nothing(self):
        """W71917 second review [P0]: the refusal arrived after the deletion.

        The two cases above put their file DIRECTLY at the mount root, and
        that shape is the one a bottom-up walk happens to get right: `os.walk`
        yields the mount itself before that file is unlinked. A mount holding
        a SUBDIRECTORY is the shape it gets wrong -- the subdirectory is
        yielded first, its files go, and only then does the walk reach the
        mount root it was going to refuse.

        So the boundary is asked about the tree a real source actually has.
        Everything under the mount must survive, and the refusal must arrive
        with the whole of it still there rather than with the deepest of it
        already gone.
        """
        _roots, boundary = self.composed()
        os.chmod(os.path.dirname(boundary.mountpoint), 0o700)
        nested = os.path.join(boundary.mountpoint, "pkg", "deeper")
        os.makedirs(nested)
        kept = [os.path.join(boundary.mountpoint, "at-the-root"),
                os.path.join(boundary.mountpoint, "pkg", "one-level-down"),
                os.path.join(nested, "two-levels-down")]
        for place in kept:
            with open(place, "w", encoding="utf-8") as writing:
                writing.write("material this manager did not create\n")
        # THE DEVICE IS DELIBERATELY UNTOUCHED, as in the case above: this is
        # the same-filesystem bind the kernel's table is the only witness to.
        held = workspaces.mount_table

        def also_mounted(**named):
            return list(held(**named)) + [(boundary.mountpoint, "ext4")]

        with mock.patch.object(workspaces, "mount_table",
                               side_effect=also_mounted):
            with self.assertRaises(ContractRefusal) as caught:
                workspaces.discard_workspace(self.storage, ATTEMPT)
        self.assertEqual(caught.exception.category, "policy")
        for place in kept:
            self.assertTrue(os.path.exists(place),
                            f"the removal reached {place} behind the mount")
        self.assertTrue(os.path.isdir(nested))

    def test_nothing_is_removed_anywhere_when_a_mount_is_found(self):
        """The refusal precedes EVERY unlink, not merely the ones under the
        mount.

        A guard that refuses on reaching the mount still leaves whatever the
        walk had already passed through deleted, and a cleanup that half-ran
        is a cleanup an operator cannot reason about. The admitted directories
        are therefore collected before anything is removed, so a mount
        anywhere in the tree leaves the whole tree alone.
        """
        _roots, boundary = self.composed()
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                ATTEMPT)
        elsewhere = os.path.join(os.path.realpath(roots["workspace"]),
                                 "ours", "own")
        os.makedirs(elsewhere)
        mine = os.path.join(elsewhere, "this-manager-made-it")
        with open(mine, "w", encoding="utf-8") as writing:
            writing.write("the manager's own material\n")
        os.chmod(os.path.dirname(boundary.mountpoint), 0o700)
        held = workspaces.mount_table

        def also_mounted(**named):
            return list(held(**named)) + [(boundary.mountpoint, "ext4")]

        with mock.patch.object(workspaces, "mount_table",
                               side_effect=also_mounted):
            with self.assertRaises(ContractRefusal):
                workspaces.discard_workspace(self.storage, ATTEMPT)
        self.assertTrue(os.path.exists(mine),
                        "a refused cleanup removed material in another "
                        "subtree before it reached the mount")

    def test_an_unreadable_mount_table_refuses_before_anything_is_removed(
            self):
        """A build that cannot ask the kernel does not guess.

        An empty table read as "no mounts here" is exactly the reading that
        restores the defect, so the refusal is proved rather than assumed --
        and it is proved to happen BEFORE the walk removes anything.
        """
        _roots, boundary = self.composed()
        inside = os.path.join(boundary.mountpoint, "kept-by-the-refusal")
        os.chmod(os.path.dirname(boundary.mountpoint), 0o700)
        with open(inside, "w", encoding="utf-8") as writing:
            writing.write("still here\n")
        with mock.patch.object(workspaces, "MOUNTINFO",
                               "/proc/self/there-is-no-such-file"):
            with self.assertRaises(ContractRefusal) as caught:
                workspaces.discard_workspace(self.storage, ATTEMPT)
        self.assertEqual(caught.exception.category, "integrity")
        self.assertTrue(os.path.exists(inside),
                        "the removal ran before it could read the table")

    @unittest.skipUnless(_can_bind_mount(),
                         "this run cannot create a mount namespace, so the "
                         "REAL same-filesystem bind mount is not exercised "
                         "here; test_a_same_filesystem_mount_is_refused_"
                         "though_its_device_matches proves the same boundary "
                         "from the kernel's table without the capability")
    def test_a_real_same_filesystem_bind_mount_is_refused(self):
        """The same proof with an actual bind, where the capability exists.

        Everything the simulated case models is real here: the bind is
        established from the same filesystem, the device number is identical by
        construction, and the entry behind it must still be there afterwards.
        """
        _roots, boundary = self.composed()
        inputs = os.path.dirname(boundary.mountpoint)
        os.chmod(inputs, 0o700)
        foreign = os.path.join(self.root, "foreign")
        os.makedirs(foreign, exist_ok=True)
        kept = os.path.join(foreign, "somebody-elses-file")
        with open(kept, "w", encoding="utf-8") as writing:
            writing.write("material this manager did not create\n")
        _bind(foreign, boundary.mountpoint)
        self.addCleanup(_unbind, boundary.mountpoint)
        self.assertEqual(os.lstat(boundary.mountpoint).st_dev,
                         os.lstat(foreign).st_dev)
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.discard_workspace(self.storage, ATTEMPT)
        self.assertEqual(caught.exception.category, "policy")
        self.assertTrue(os.path.exists(kept),
                        "the removal walked into a real bind mount")

    def test_an_ordinary_empty_mountpoint_is_removed_with_the_root(self):
        """The ordinary arc: the bind lives in the container's own namespace,
        so what cleanup finds on the host is an empty directory."""
        _roots, boundary = self.composed()
        self.assertTrue(workspaces.discard_workspace(self.storage, ATTEMPT))
        self.assertFalse(os.path.exists(boundary.mountpoint))
        # AND THE NOMINATED SOURCE IS UNTOUCHED, which is the whole point of
        # it never having been this manager's material.
        self.assertTrue(os.path.isdir(os.path.join(self.source, "pkg")))


def _runtime_pieces(tree):
    """Every identifier and every NON-DOCSTRING string literal in one module.

    `tests/authority/test_boundary._runtime_strings`' distinction, widened to
    identifiers: a docstring is documentation ABOUT a boundary and only the
    other kind can be a use of one.
    """
    import ast
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) \
                    and isinstance(first.value, ast.Constant) \
                    and isinstance(first.value.value, str):
                docstrings.add(id(first.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docstrings:
            yield node.value
        elif isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            yield node.name


def _walked(*args, **named):
    raise AssertionError(
        "the W71917 delivery enumerated a directory; the ordinary local path "
        "does not walk, copy, snapshot, enumerate or hash the nominated "
        "source")


def _measured(*args, **named):
    raise AssertionError(
        "the W71917 delivery measured a tree through the manager's own "
        "copier; the retired bootstrap is what did that")


def _labels():
    """The full runtime label set, borrowed from `test_oci`'s own fixture.

    A second hand-built label set here would be a second account of the
    contract's own vocabulary, and this file's subject is the mount rather
    than the labels.
    """
    from .test_oci import LABELS
    return dict(LABELS)


def _memory_backed_directory(case):
    """A directory that really is on a memory filesystem, or a skip.

    NOT A MOCK. The refusal under test is about what the kernel says a path is
    stored on, and a stubbed `filesystem_of` would prove this file's own
    stubbing. `/dev/shm` is a tmpfs on every host this runs on that has one;
    where there is none, there is nothing to prove and the case says so rather
    than passing.
    """
    for place in ("/dev/shm", tempfile.gettempdir()):
        try:
            if filesystem_of(place) in MEMORY_FILESYSTEMS:
                return place
        except ContractRefusal:
            continue
    raise unittest.SkipTest(
        "no memory-backed directory is available to prove the refusal "
        "against; this host has neither a tmpfs /dev/shm nor a tmpfs "
        "temporary directory")
