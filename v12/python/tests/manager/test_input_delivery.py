"""W33935 — the delivered `/input` pair, read by the identity that has to read
it.

W6's digest-bound capability pass measured, inside the real composed execution
container, that the worker runs as the fixed uid/gid 65532 while both
manager-authored documents were owned by the manager's uid at mode 0400.  BOTH
READS FAILED WITH `EACCES`, so no worker could consume either of the two
documents §7.0 requires it to read, and the sibling launch delivery at 0444 was
readable -- which is what showed the shape rather than merely the symptom.

WHY THIS MODULE EXISTS SEPARATELY FROM `test_workspaces`.  W6631's suite writes
the documents and reads them back AS THE MANAGER, and every case in it passed
throughout: the manager owns those files, so 0400 is readable to it.  A defect
visible only to a different uid inside a container is not reachable from a
suite that never leaves the host, and the correction is only established by a
case that reads them the way a worker does.

WHAT IT PINS, and each is a different way for the delivery to be wrong:

  * both documents are READ by uid 65532 inside the runtime the manager
    composed, and what comes back is the manager's exact bytes;
  * neither is writable, the root is not writable, and the reason for each is
    the one that protects it -- `EROFS` from the read-only bind at the
    directory, and permissions at the files;
  * the mode is ESTABLISHED rather than requested, so a restrictive process
    umask cannot silently author the old unreadable document again;
  * a second incarnation over the same delivery still reads both, because the
    root is composed once and frozen;
  * one assignment's runtime reaches no other assignment's input root.
"""

import concurrent.futures
import json
import os
import tempfile
import subprocess
import threading
import unittest
import uuid
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (credentials, launch, oci,
                                      reconcile_runtime,
                                      request_runtime_start, workspaces)
from baton_v12.worker_manager.workspaces import (READ_ONLY_DIR,
                                                 READ_ONLY_FILE,
                                                 compose_input_root)

from . import test_lifecycle_composition as composition
from .test_lifecycle_composition import MARK, Composition

INPUT_NAMES = (workspaces.INPUT_MANIFEST, workspaces.ASSIGNMENT_MANIFEST)

# The identity the adapter's own `--user` restriction names, written out here
# rather than read from the adapter: a case that asked the adapter which uid it
# uses and then checked for that uid would agree with the adapter whatever
# either of them did.  W6633's recipe and W6632's restriction agree on this
# number because they were written from one decision.
WORKER_UID = 65532


def probe_program(paths):
    """One in-runtime probe: for each path, what it is and whether it reads."""
    return (
        "import json, os\n"
        "out = {'running_as': [os.getuid(), os.getgid()]}\n"
        f"for one in {list(paths)!r}:\n"
        "    answer = {}\n"
        "    try:\n"
        "        held = os.stat(one)\n"
        "        answer['mode'] = oct(held.st_mode & 0o777)\n"
        "        answer['uid'] = held.st_uid\n"
        "    except OSError as error:\n"
        "        out[one] = {'stat': f'{type(error).__name__}'}\n"
        "        continue\n"
        "    try:\n"
        "        with open(one, 'rb') as handle:\n"
        "            answer['read'] = handle.read().decode('utf-8')\n"
        "    except OSError as error:\n"
        "        answer['read'] = None\n"
        "        answer['read_error'] = f'{type(error).__name__}:"
        " {error.errno}'\n"
        "    try:\n"
        "        with open(one, 'ab') as handle:\n"
        "            handle.write(b'x')\n"
        "        answer['wrote'] = True\n"
        "    except OSError as error:\n"
        "        answer['wrote'] = False\n"
        "        answer['write_error'] = f'{type(error).__name__}:"
        " {error.errno}'\n"
        "    out[one] = answer\n"
        "print(json.dumps(out))\n")


def workspace_program(root):
    """W33936: the three acts the acceptance names, from inside the container.

    CREATE, UPDATE and REMOVE, each answered separately, plus what the
    filesystem made of the entries the worker created -- the group they landed
    in and whether a directory carried the setgid bit onward. A case that only
    asked "did a write succeed" would pass on a world-writable root, which is
    the remedy this correction rejected.
    """
    return (
        "import json, os, stat\n"
        f"root = {root!r}\n"
        "out = {'running_as': [os.getuid(), os.getgid()],\n"
        "       'groups': sorted(os.getgroups())}\n"
        "try:\n"
        "    held = os.stat(root)\n"
        "    out['root'] = {'mode': oct(held.st_mode & 0o7777),\n"
        "                   'gid': held.st_gid}\n"
        "except OSError as error:\n"
        "    out['root'] = {'stat': type(error).__name__}\n"
        "made = os.path.join(root, 'worker-made.txt')\n"
        "try:\n"
        "    with open(made, 'wb') as handle:\n"
        "        handle.write(b'one')\n"
        "    out['created'] = True\n"
        "except OSError as error:\n"
        "    out['created'] = False\n"
        "    out['create_error'] = f'{type(error).__name__}:{error.errno}'\n"
        "if out['created']:\n"
        "    try:\n"
        "        with open(made, 'ab') as handle:\n"
        "            handle.write(b'two')\n"
        "        out['updated'] = True\n"
        "    except OSError as error:\n"
        "        out['updated'] = False\n"
        "        out['update_error'] = f'{type(error).__name__}:{error.errno}'\n"
        "    held = os.stat(made)\n"
        "    out['made'] = {'gid': held.st_gid, 'uid': held.st_uid,\n"
        "                   'mode': oct(held.st_mode & 0o7777)}\n"
        "    inner = os.path.join(root, 'worker-made-dir')\n"
        "    try:\n"
        "        os.mkdir(inner)\n"
        # A FILE INSIDE IT, and the distinction is the whole finding: an EMPTY
        # worker directory is removable by the manager, because removing it is
        # a write to the group-writable ROOT. One with content in it is not.
        "        with open(os.path.join(inner, 'nested.txt'), 'wb') as handle:\n"
        "            handle.write(b'nested')\n"
        "        held = os.stat(inner)\n"
        "        out['inner'] = {'gid': held.st_gid,\n"
        "                        'mode': oct(held.st_mode & 0o7777),\n"
        "                        'setgid': bool(held.st_mode & stat.S_ISGID)}\n"
        "    except OSError as error:\n"
        "        out['inner'] = {'error': type(error).__name__}\n"
        "    try:\n"
        "        os.mkdir(os.path.join(root, 'empty-worker-dir'))\n"
        "    except OSError:\n"
        "        pass\n"
        "    keep = os.path.join(root, 'collected.txt')\n"
        "    with open(keep, 'wb') as handle:\n"
        "        handle.write(b'collect me')\n"
        "    shut = os.path.join(root, 'owner-only.txt')\n"
        "    with open(shut, 'wb') as handle:\n"
        "        handle.write(b'mine alone')\n"
        "    os.chmod(shut, 0o600)\n"
        "    try:\n"
        "        os.remove(made)\n"
        "        out['removed'] = not os.path.exists(made)\n"
        "    except OSError as error:\n"
        "        out['removed'] = False\n"
        "        out['remove_error'] = f'{type(error).__name__}:{error.errno}'\n"
        "print(json.dumps(out))\n")


class Delivery(composition.Lifecycle):
    """W6636's composed lifecycle, asked one question it was not asked.

    THE FIXTURE IS REUSED AND ITS CASES ARE NOT.  What a worker sees has to be
    what the production `request_runtime_start` composed, so a second
    hand-written engine fixture would be a different container wearing the same
    name -- but subclassing `Composition` outright would re-collect all
    thirty-two of W6636's cases under this module's class names, which is a
    duplicate test identity in the shared registry and a suite that runs a
    closed Work's cases twice while attributing them here.

    So the engine fixture (`Lifecycle`) is inherited, and the exact helper
    methods this Work depends on are ADOPTED BY NAME below.  The list is the
    honest statement of the coupling: it is what breaks if W6636's fixture
    changes, and it is short enough to read.
    """

    roots = Composition.roots
    adapter = Composition.adapter
    plan = Composition.plan
    launch = Composition.launch
    claimed = Composition.claimed
    activated = Composition.activated
    composed = Composition.composed
    prepared = Composition.prepared
    labels = Composition.labels
    attempt_row = Composition.attempt_row
    carrying = Composition.carrying
    inspected = Composition.inspected

    def started(self):
        """One execution runtime over a real, freshly composed input root."""
        adapter, roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        return adapter, roots, inputs

    def inside(self, paths, argv=None, program=None):
        """Run the probe in the EXACT argv the manager composed.

        Only the entrypoint is replaced.  Every mount, namespace, capability,
        user and network flag is the one `request_runtime_start` produced,
        because they are the same argv -- so what this measures is the delivery
        the manager made and not a container this suite configured.
        """
        argv = list(argv if argv is not None
                    else next(one for one in reversed(self.engine_calls)
                              if "run" in one))
        name = f"{MARK}-w33935-{uuid.uuid4().hex[:10]}"
        argv[argv.index("--name") + 1] = name
        self.made.append(name)
        image = argv[-1]
        argv = argv[:-1]
        # THE ATTEMPT'S RECONCILIATION LABELS ARE DROPPED, and finding out why
        # was worth the round: with them, a probe IS a second container
        # carrying this assignment's labels -- so the engine reports two
        # runtimes for one attempt and the manager's own multiplicity rule
        # would cancel the assignment.  A measuring instrument that changes
        # the state it measures is not one.
        #
        # Everything the delivery is made of stays: the mounts, the user, the
        # namespace, the capability set and the network mode are the argv the
        # manager composed, because they are the same argv.  Only the identity
        # this container claims to be is removed.
        stripped, index = [], 0
        while index < len(argv):
            if argv[index] == "--label":
                index += 2
                continue
            if argv[index] == "--detach":
                index += 1
                continue
            stripped.append(argv[index])
            index += 1
        argv = stripped + ["--label", f"{MARK}-probe=1",
                           "--entrypoint", "python3", image,
                           "-c", program or probe_program(paths)]
        finished = subprocess.run(argv, capture_output=True, timeout=300)
        raw = finished.stdout.decode("utf-8", "replace")
        self.assertTrue(raw.strip(),
                        f"the probe answered nothing; rc={finished.returncode} "
                        f"stderr="
                        f"{finished.stderr.decode('utf-8', 'replace')[:2000]}")
        answered = json.loads(raw.strip().splitlines()[-1])
        # THE PROBE IS THE WORKER'S IDENTITY OR IT MEASURES NOTHING.  A probe
        # that had somehow run as root would read a 0400 file happily and this
        # whole module would pass over the defect it exists to keep out.
        self.assertEqual(answered["running_as"], [WORKER_UID, WORKER_UID],
                         answered)
        return answered

    # -- the positive case ---------------------------------------------------

    def test_the_worker_identity_reads_both_delivered_documents(self):
        """The defect, kept.

        Not "the mode is 0444" -- that is the manager agreeing with itself
        about a number.  This opens both files as uid 65532 inside the runtime
        and compares what comes back against the bytes the manager wrote.
        """
        _adapter, roots, _inputs = self.started()
        targets = [f"/input/{name}" for name in INPUT_NAMES]
        answered = self.inside(targets)
        for name, target in zip(INPUT_NAMES, targets):
            with self.subTest(document=name):
                seen = answered[target]
                self.assertIsNotNone(
                    seen["read"],
                    f"{name} is not readable by the worker: {seen}")
                with open(os.path.join(roots["inputs"], name),
                          encoding="utf-8") as handle:
                    self.assertEqual(seen["read"], handle.read())
                # And it is a real protocol document rather than any readable
                # bytes: a delivery that shipped an empty file would satisfy a
                # length comparison.
                self.assertIn("schema", json.loads(seen["read"]))

    def test_the_launch_document_and_the_input_pair_agree_on_the_mode(self):
        """Two manager-owned read-only deliveries, one rule.

        W26291 corrected this exact shape at the launch document and wrote the
        reason down; the same line here was never revisited, and the two
        components disagreed for two rounds.  Holding them to each other is
        what stops a third.
        """
        self.assertEqual(READ_ONLY_FILE, launch.READ_ONLY_FILE)
        self.assertEqual(READ_ONLY_DIR, launch.READ_ONLY_DIR)

    # -- the negative cases --------------------------------------------------

    def test_neither_document_is_writable_and_neither_is_the_root(self):
        """Readable did not become writable -- asked TWICE, of two different
        things, because one of the two answers cannot see the guard.

        THE ENGINE IS ASKED whether the bind it applied is read-only.  That is
        the guard that actually protects this material and the only one a
        mutation can move: the mutation harness dropped the read-only flag from
        the production run vector and the in-container write STILL failed,
        because the documents are owned by the manager's uid and the container
        is 65532 -- so ownership refuses the write before the bind is reached,
        and a case that asked only the container would have reported the bind
        established while it was gone.

        AND THE CONTAINER IS ASKED anyway, because the engine agreeing to a
        flag and a process actually being denied are two facts and only the
        second one protects anything.
        """
        self.started()
        held = self.inspected(self.attempt_row()["runtime_id"])
        binds = {one["Destination"]: one for one in held["Mounts"]}
        self.assertIn("/input", binds, sorted(binds))
        self.assertFalse(binds["/input"]["RW"], binds["/input"])

        targets = ["/input"] + [f"/input/{name}" for name in INPUT_NAMES]
        answered = self.inside(targets)
        for target in targets:
            with self.subTest(target=target):
                self.assertFalse(answered[target]["wrote"], answered[target])
                self.assertIn("Error", answered[target]["write_error"])

    def test_a_restarted_manager_reuses_a_delivery_that_is_still_readable(
            self):
        """Restart and retry reuse.

        A SECOND `ControlStore` OVER THE SAME FILE is what a restart actually
        is, and it is W6636's own spelling of one.  The new incarnation adopts
        the running runtime rather than composing anything, so the delivery it
        reuses is the frozen one -- and this asks a container over that adopted
        runtime's own argv whether both documents still read.

        A correction applied only where the documents are WRITTEN would pass
        the positive case and fail this one, because nothing here writes them
        again.
        """
        adapter, _roots, inputs = self.started()
        runtime_id = self.attempt_row()["runtime_id"]
        first = self.inside([f"/input/{name}" for name in INPUT_NAMES])

        restarted = self.open_store(incarnation="manager-w33935-restarted")
        reconcile_runtime(restarted, adapter, attempt_id=self.attempt)
        # THE SAME RUNTIME, adopted rather than replaced -- otherwise this
        # would be a fresh delivery and would prove nothing about reuse.
        self.assertEqual(self.attempt_row(restarted)["runtime_id"], runtime_id)
        self.assertEqual(len(self.carrying(self.labels())), 1)

        again = self.inside([f"/input/{name}" for name in INPUT_NAMES])
        for name in INPUT_NAMES:
            with self.subTest(document=name):
                target = f"/input/{name}"
                self.assertIsNotNone(again[target]["read"], again[target])
                self.assertEqual(again[target]["read"], first[target]["read"])

    def test_one_runtime_reaches_no_other_assignments_input_root(self):
        """Sibling isolation.

        A world-readable MODE is only safe because nothing else is mounted.
        This composes a second assignment's root on the same host and asks the
        first assignment's runtime for it by its exact path.
        """
        _adapter, roots, _inputs = self.started()
        stranger = workspaces.assignment_workspace(
            self.group, self.storage, f"{self.attempt}-stranger")
        given, assignment = composition.input_roots.documents(
            work_ref=dict(composition.WORK_REF),
            participant=composition.WHO, generation=1,
            runtime_attempt_id=f"{self.attempt}-stranger", given=None,
            policy_digest=composition.POLICY,
            profile_digest=composition.PROFILE)
        compose_input_root(
            stranger["inputs"], given, assignment,
            assignment=dict(assignment["assignment_ref"]),
            runtime_attempt_id=f"{self.attempt}-stranger")
        self.addCleanup(composition.forcibly_remove, stranger["inputs"])
        neighbour = [os.path.join(stranger["inputs"], name)
                     for name in INPUT_NAMES]
        # THE HOST CAN READ THEM, which is what makes the container's answer
        # mean "not reachable from here" rather than "not there".
        for place in neighbour:
            self.assertTrue(os.path.isfile(place), place)
            with open(place, encoding="utf-8") as handle:
                self.assertIn("schema", json.load(handle))
        answered = self.inside(neighbour)
        for place in neighbour:
            with self.subTest(place=place):
                self.assertEqual(answered[place], {"stat": "FileNotFoundError"},
                                 answered[place])


class DockerDelivery(Delivery, unittest.TestCase):
    engine = "docker"
    required = True


class PodmanDelivery(Delivery, unittest.TestCase):
    engine = "podman"
    required = False


class Configured(unittest.TestCase):
    """A case that holds the deployment's configured workspace group.

    W33936 review [P1] made the group a capability read from this manager's
    own record rather than an integer a caller composes, so every suite that
    allocates a workspace has to configure one and read it back -- which is
    the sequence a deployment performs.
    """

    def setUp(self):
        self._configured = tempfile.TemporaryDirectory(
            prefix="v12-w33936-cfg-")
        self.addCleanup(self._configured.cleanup)
        from baton_v12.worker_manager import ControlStore
        self.store = ControlStore.open(
            os.path.join(self._configured.name, "control.sqlite3"),
            incarnation="configured-1",
            clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.store.close)
        self.group = composition.input_roots.configured_group(self.store)


class TheModeIsEstablishedRatherThanRequested(Configured):
    """The mechanism, daemon-free.

    A creation mode is filtered by the process umask, so `os.open(..., 0o444)`
    authors 0444 under umask 022 and 0400 under the ordinary service umask 077
    -- the unreadable document arriving silently and only on some hosts.  That
    is how this defect reached a reviewed component in the first place, and a
    case that only compared the constant would pass with the old line restored
    on the machine it happened to run on.
    """

    def setUp(self):
        super().setUp()
        import tempfile

        self._root = tempfile.TemporaryDirectory(prefix="v12-w33935-")
        self.addCleanup(self._root.cleanup)
        self.storage = os.path.join(self._root.name, "storage")
        os.makedirs(self.storage)

    def compose_under(self, umask):
        roots = workspaces.assignment_workspace(self.group, self.storage, "assignment-1")
        self.addCleanup(composition.forcibly_remove, roots["inputs"])
        given, assignment = composition.input_roots.documents(
            work_ref=dict(composition.WORK_REF),
            participant=composition.WHO, generation=1,
            runtime_attempt_id="attempt-1", given=None,
            policy_digest=composition.POLICY,
            profile_digest=composition.PROFILE)
        previous = os.umask(umask)
        try:
            return compose_input_root(
                roots["inputs"], given, assignment,
                assignment=dict(assignment["assignment_ref"]),
                runtime_attempt_id="attempt-1")
        finally:
            os.umask(previous)

    def test_a_restrictive_umask_cannot_author_an_unreadable_document(self):
        for umask in (0o022, 0o077, 0o777):
            with self.subTest(umask=oct(umask)):
                self.setUp()
                for place in self.compose_under(umask):
                    self.assertEqual(
                        os.stat(place).st_mode & 0o777, READ_ONLY_FILE,
                        f"{os.path.basename(place)} under umask {oct(umask)}")

    def test_the_delivered_mode_grants_read_and_no_write_to_anybody(self):
        """The claim the mode itself makes, stated as bits.

        Every class may read; no class may write.  Written as an assertion
        about the VALUE rather than about the number, so a future edit that
        added a write bit to make some other case convenient has to fail here.
        """
        self.assertEqual(READ_ONLY_FILE & 0o222, 0, oct(READ_ONLY_FILE))
        for shift in (0, 3, 6):
            self.assertTrue(READ_ONLY_FILE & (0o4 << shift),
                            oct(READ_ONLY_FILE))
        self.assertEqual(READ_ONLY_DIR & 0o222, 0, oct(READ_ONLY_DIR))
        for shift in (0, 3, 6):
            self.assertTrue(READ_ONLY_DIR & (0o5 << shift) == (0o5 << shift),
                            oct(READ_ONLY_DIR))


class TheInputRootIsFrozenAndNotOnlyItsFiles(Configured):
    """W33935 review [P0], kept.

    `READ_ONLY_DIR` existed, was exported, and NOTHING applied it: both
    documents were written at 0444 and the root was left at 0775.  A 0444 file
    inside a writable directory is not protected -- unlink and rename are
    permissions of the DIRECTORY -- so the manager's own uid, or anything
    sharing its group, could remove either document and put a different one at
    the same name underneath a worker that had already mounted it.  The
    read-only bind stops the container writing; it does not stop the host
    replacing a bound file.

    EVERY CASE HERE ACTS ON THE HOST as the manager's own identity, because
    that is the party the freeze is against.  The container half is the class
    above, and both are needed: a root the host cannot rewrite and the worker
    cannot read would be no use either.
    """

    def setUp(self):
        super().setUp()
        # A CASE THAT CANNOT BE DENIED MEASURES NOTHING.  Running as root
        # bypasses every directory permission below, so this refuses rather
        # than passing green on a machine where it proves nothing.
        if os.geteuid() == 0:
            raise AssertionError(
                "these cases establish that ordinary permissions DENY a write, "
                "and root is not denied by them; run them unprivileged")
        import tempfile

        self._root = tempfile.TemporaryDirectory(prefix="v12-w33935-freeze-")
        self.addCleanup(self._root.cleanup)
        self.storage = os.path.join(self._root.name, "storage")
        os.makedirs(self.storage)

    def composed(self, assignment="assignment-1", umask=None):
        roots = workspaces.assignment_workspace(self.group, self.storage, assignment)
        self.addCleanup(composition.forcibly_remove, roots["inputs"])
        given, assignment_manifest = composition.input_roots.documents(
            work_ref=dict(composition.WORK_REF),
            participant=composition.WHO, generation=1,
            runtime_attempt_id=f"attempt-{assignment}", given=None,
            policy_digest=composition.POLICY,
            profile_digest=composition.PROFILE)
        previous = None if umask is None else os.umask(umask)
        try:
            compose_input_root(
                roots["inputs"], given, assignment_manifest,
                assignment=dict(assignment_manifest["assignment_ref"]),
                runtime_attempt_id=f"attempt-{assignment}")
        finally:
            if previous is not None:
                os.umask(previous)
        return roots

    def test_the_root_is_frozen_to_the_declared_mode(self):
        for umask in (None, 0o022, 0o077, 0o777):
            with self.subTest(umask=umask if umask is None else oct(umask)):
                self.setUp()
                roots = self.composed(umask=umask)
                self.assertEqual(
                    os.stat(roots["inputs"]).st_mode & 0o777, READ_ONLY_DIR)

    def test_the_frozen_root_denies_create_unlink_rename_and_replacement(self):
        """The four ways a directory's write bit lets somebody change what a
        mounted document IS, each attempted and each required to be denied.

        Named separately rather than as "no write": a case that only tried to
        CREATE would pass while unlink and rename -- the two that actually
        replace a bound file -- stayed open.
        """
        roots = self.composed()
        root = roots["inputs"]
        existing = os.path.join(root, workspaces.INPUT_MANIFEST)
        other = os.path.join(self._root.name, "impostor.json")
        with open(other, "w", encoding="utf-8") as handle:
            handle.write("{}")

        attempts = {
            "create": lambda: open(os.path.join(root, "new.json"), "w"),
            "unlink": lambda: os.unlink(existing),
            "rename": lambda: os.rename(existing,
                                        os.path.join(root, "moved.json")),
            "replace": lambda: os.replace(other, existing),
            "replace-in-place": lambda: open(existing, "w"),
        }
        for what, attempt in attempts.items():
            with self.subTest(what=what):
                with self.assertRaises(PermissionError) as caught:
                    attempt()
                self.assertEqual(caught.exception.errno, 13, what)

        # AND NOTHING MOVED.  A denial that had already unlinked would be a
        # denial of the second half of the act.
        self.assertEqual(sorted(os.listdir(root)), sorted(INPUT_NAMES))
        with open(existing, encoding="utf-8") as handle:
            self.assertIn("schema", json.load(handle))

    def test_the_manager_can_still_read_and_traverse_what_it_froze(self):
        """0555 and not 0500: the container's fixed uid is not this manager's,
        and a root nobody but the owner may traverse is a root whose readable
        documents the worker cannot reach."""
        roots = self.composed()
        self.assertTrue(READ_ONLY_DIR & 0o111 == 0o111, oct(READ_ONLY_DIR))
        self.assertEqual(sorted(os.listdir(roots["inputs"])),
                         sorted(INPUT_NAMES))
        for name in INPUT_NAMES:
            with open(os.path.join(roots["inputs"], name),
                      encoding="utf-8") as handle:
                self.assertIn("schema", json.load(handle))

    def test_cleanup_removes_a_frozen_root_and_thaws_nothing_else(self):
        """Retry and cleanup still work, and reach exactly one tree.

        A freeze that the manager's own cleanup could not undo would trade one
        defect for a worse one; a cleanup that thawed more than the tree it
        removes would give the freeze away.
        """
        kept = self.composed("assignment-kept")
        going = self.composed("assignment-going")
        self.assertEqual(os.stat(going["inputs"]).st_mode & 0o777,
                         READ_ONLY_DIR)

        self.assertTrue(
            workspaces.discard_workspace(self.storage, "assignment-going"))
        self.assertFalse(os.path.exists(going["inputs"]))
        # THE SIBLING IS UNTOUCHED, mode included.
        self.assertEqual(os.stat(kept["inputs"]).st_mode & 0o777,
                         READ_ONLY_DIR)
        self.assertEqual(sorted(os.listdir(kept["inputs"])),
                         sorted(INPUT_NAMES))

    def test_recomposition_is_still_refused_rather_than_forced(self):
        """The freeze is not what makes a second composition impossible, and
        the rule that does is unchanged."""
        roots = self.composed()
        given, assignment_manifest = composition.input_roots.documents(
            work_ref=dict(composition.WORK_REF),
            participant=composition.WHO, generation=1,
            runtime_attempt_id="attempt-assignment-1", given=None,
            policy_digest=composition.POLICY,
            profile_digest=composition.PROFILE)
        with self.assertRaises(Exception) as caught:
            compose_input_root(
                roots["inputs"], given, assignment_manifest,
                assignment=dict(assignment_manifest["assignment_ref"]),
                runtime_attempt_id="attempt-assignment-1")
        self.assertIn("composed once and then frozen", str(caught.exception))


class TheWholeDeliveryIsFrozenAndNotOnlyTheRoot(Configured):
    """W39358, measured inside the real composed runtime.

    The class above proves the ROOT's own mode and the two documents'. This
    proves the third thing under `/input` and the one nothing had ever read:
    the staged source TREE. `copied_manifest` creates every file it copies at
    `0o600` and makes its directories with a plain `os.makedirs`, and
    `compose_input_root` chmodded exactly one directory -- so the delivery was
    owner-only beside two `0o444` documents, and the container's fixed uid
    65532 got `EACCES` opening the very source the assignment tells it to work
    from. The dogfood operator's first real worker turn failed exactly there.

    THIS ASKS THE MODE RATHER THAN A CONTAINER, deliberately: the engine half
    is `TheConfiguredWorkspaceGroup` and the real-engine dogfood gate, and a
    mode case that needs a daemon is one that cannot run everywhere the rule
    applies.
    """

    def setUp(self):
        super().setUp()
        if os.geteuid() == 0:
            raise AssertionError(
                "these cases establish that ordinary permissions DENY a read, "
                "and root is not denied by them; run them unprivileged")
        import tempfile

        self._root = tempfile.TemporaryDirectory(prefix="v12-w39358-freeze-")
        self.addCleanup(self._root.cleanup)
        self.storage = os.path.join(self._root.name, "storage")
        os.makedirs(self.storage)

    def staged(self, assignment="assignment-1", umask=None):
        """A source tree delivered the way the operator delivers one."""
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                assignment)
        self.addCleanup(composition.forcibly_remove, roots["inputs"])
        source = os.path.join(self._root.name, "source")
        os.makedirs(os.path.join(source, "below", "deeper"))
        for relative in ("harness.py", "below/one.py", "below/deeper/two.py"):
            with open(os.path.join(source, relative), "w",
                      encoding="utf-8") as writing:
                writing.write(f"# {relative}\n")
        given, assignment_manifest = composition.input_roots.documents(
            work_ref=dict(composition.WORK_REF),
            participant=composition.WHO, generation=1,
            runtime_attempt_id=f"attempt-{assignment}", given=None,
            policy_digest=composition.POLICY,
            profile_digest=composition.PROFILE)
        previous = None if umask is None else os.umask(umask)
        try:
            workspaces.copied_manifest(source,
                                       os.path.join(roots["inputs"], "source"))
            compose_input_root(
                roots["inputs"], given, assignment_manifest,
                assignment=dict(assignment_manifest["assignment_ref"]),
                runtime_attempt_id=f"attempt-{assignment}")
        finally:
            if previous is not None:
                os.umask(previous)
        return roots

    def test_every_staged_file_and_directory_carries_the_declared_mode(self):
        """Whatever the umask was when the copier ran.

        NOT `0o777`, which the sibling class above does use. A total umask is
        exact against the ROOT's freeze, because `os.chmod` on an existing
        directory was never umask-filtered -- but `copied_manifest` MAKES its
        own subdirectories, so under `0o777` it creates one at mode zero and
        then refuses `EACCES` writing into it. That is the copier's own
        question and it fails closed and loudly; this case is about what the
        freeze leaves behind, and a delivery that never happened has nothing
        to freeze.
        """
        for umask in (None, 0o022, 0o077):
            with self.subTest(umask=umask if umask is None else oct(umask)):
                self.setUp()
                roots = self.staged(umask=umask)
                seen = 0
                for base, directories, files in os.walk(roots["inputs"]):
                    for one in directories:
                        seen += 1
                        self.assertEqual(
                            os.stat(os.path.join(base, one)).st_mode & 0o777,
                            READ_ONLY_DIR,
                            f"{one} is not frozen to the declared directory "
                            f"mode")
                    for one in files:
                        seen += 1
                        self.assertEqual(
                            os.stat(os.path.join(base, one)).st_mode & 0o777,
                            READ_ONLY_FILE,
                            f"{one} is not frozen to the declared file mode")
                # THE WALK REALLY SAW THE TREE. A case that measured an empty
                # delivery would pass while proving nothing at all.
                self.assertEqual(seen, 8, "the staged delivery was not walked")

    def test_a_party_that_is_neither_owner_nor_group_can_still_read_it(self):
        """WHICH IS THE POINT, and the half that was missing.

        The container's fixed uid is not this manager's and holds the
        workspace group, not the manager's own -- so `other` is the bit that
        decides whether a worker can open the source it was given. This asks
        the mode for exactly that rather than running a container to find out.
        """
        roots = self.staged()
        for relative in ("source", "source/below", "source/below/deeper"):
            mode = os.stat(os.path.join(roots["inputs"],
                                        relative)).st_mode & 0o777
            self.assertEqual(mode & 0o5, 0o5,
                             f"{relative} is not traversable by a worker")
        for relative in ("source/harness.py", "source/below/one.py",
                         "source/below/deeper/two.py"):
            mode = os.stat(os.path.join(roots["inputs"],
                                        relative)).st_mode & 0o777
            self.assertEqual(mode & 0o4, 0o4,
                             f"{relative} is not readable by a worker")
            self.assertEqual(mode & 0o222, 0,
                             f"{relative} is writable by somebody")


class TheRootsOwnENTRYIsFrozenToo(Configured):
    """W33935 re-review [P0], kept.

    `0555` on `inputs` governs create, unlink and rename INSIDE it.  Renaming
    or replacing `inputs` ITSELF is a write to its parent, and the assignment
    home was left at the process default -- so the whole frozen root could be
    moved aside and a writable one put at the same canonical path with
    different bytes in it.  A worker that had already resolved that path would
    then be reading somebody else's documents through a mount the manager
    still believed it had frozen.

    A directory entry can only be protected through its parent.  There is no
    other mechanism, which is why the correction is at the home.
    """

    def setUp(self):
        super().setUp()
        if os.geteuid() == 0:
            raise AssertionError(
                "these cases establish that ordinary permissions DENY a write, "
                "and root is not denied by them; run them unprivileged")
        import tempfile

        self._root = tempfile.TemporaryDirectory(prefix="v12-w33935-parent-")
        self.addCleanup(self._root.cleanup)
        self.storage = os.path.join(self._root.name, "storage")
        os.makedirs(self.storage)

    def composed(self, assignment="assignment-1"):
        roots = workspaces.assignment_workspace(self.group, self.storage, assignment)
        self.addCleanup(self._forcibly_remove_home, assignment)
        given, manifest = composition.input_roots.documents(
            work_ref=dict(composition.WORK_REF),
            participant=composition.WHO, generation=1,
            runtime_attempt_id=f"attempt-{assignment}", given=None,
            policy_digest=composition.POLICY,
            profile_digest=composition.PROFILE)
        compose_input_root(
            roots["inputs"], given, manifest,
            assignment=dict(manifest["assignment_ref"]),
            runtime_attempt_id=f"attempt-{assignment}")
        return roots

    def _forcibly_remove_home(self, assignment):
        home = os.path.join(self.storage, assignment)
        if os.path.isdir(home):
            os.chmod(home, 0o700)
            composition.forcibly_remove(home)

    def home_of(self, roots):
        return os.path.dirname(roots["inputs"].rstrip("/"))

    def test_the_home_is_frozen_once_its_entries_exist(self):
        roots = self.composed()
        self.assertEqual(os.stat(self.home_of(roots)).st_mode & 0o777,
                         READ_ONLY_DIR)

    def test_the_root_entry_itself_cannot_be_renamed_or_replaced(self):
        """The reviewer's reproduction, as a permanent case.

        Each of the three moves is attempted separately: renaming the root
        aside, creating a new directory at the canonical path, and renaming
        something else onto it.  A case that only tried the first would leave
        the other two open, and it is the SECOND that actually swaps a mounted
        root's contents.
        """
        roots = self.composed()
        home = self.home_of(roots)
        original = roots["inputs"]
        with open(os.path.join(original, workspaces.INPUT_MANIFEST),
                  encoding="utf-8") as handle:
            before = handle.read()
        decoy = os.path.join(self._root.name, "decoy")
        os.makedirs(decoy)

        attempts = {
            "rename the root aside":
                lambda: os.rename(original, original + ".displaced"),
            "make a new root at the canonical path":
                lambda: os.mkdir(original + ".x") or os.rename(
                    original + ".x", original),
            "rename another directory onto it":
                lambda: os.rename(decoy, original),
            "remove the root":
                lambda: os.rmdir(original),
            "add a sibling entry to the home":
                lambda: os.mkdir(os.path.join(home, "extra")),
        }
        for what, attempt in attempts.items():
            with self.subTest(what=what):
                with self.assertRaises(PermissionError) as caught:
                    attempt()
                self.assertEqual(caught.exception.errno, 13, what)

        # THE CANONICAL PATH AND THE EXACT DOCUMENTS DID NOT MOVE.
        self.assertTrue(os.path.isdir(original))
        self.assertEqual(sorted(os.listdir(original)), sorted(INPUT_NAMES))
        with open(os.path.join(original, workspaces.INPUT_MANIFEST),
                  encoding="utf-8") as handle:
            self.assertEqual(handle.read(), before)
        self.assertEqual(sorted(os.listdir(home)),
                         sorted(workspaces.HOME_ENTRIES))

    def test_what_the_frozen_home_still_permits(self):
        """The home's mode governs its ENTRIES and nothing deeper.

        Custody trees, volatile credential roots and durable credential records
        are all created after the freeze, INSIDE entries this function
        provisioned -- so the freeze has to leave that possible or it breaks
        the arc it is protecting.
        """
        roots = self.composed()
        home = self.home_of(roots)
        for entry in ("custody", "credentials", "credential-state"):
            with self.subTest(entry=entry):
                place = os.path.join(home, entry, "attempt-1")
                os.makedirs(place)
                with open(os.path.join(place, "record.json"), "w",
                          encoding="utf-8") as handle:
                    handle.write("{}")
        # ...and the writable root is still writable, which is what the worker
        # and the freeze both depend on.
        with open(os.path.join(roots["workspace"], "output"), "w",
                  encoding="utf-8") as handle:
            handle.write("x")

    def test_cleanup_reaches_exactly_one_frozen_home(self):
        kept = self.composed("assignment-kept")
        going = self.composed("assignment-going")
        self.assertTrue(
            workspaces.discard_workspace(self.storage, "assignment-going"))
        self.assertFalse(os.path.exists(self.home_of(going)))
        self.assertEqual(os.stat(self.home_of(kept)).st_mode & 0o777,
                         READ_ONLY_DIR)
        self.assertEqual(os.stat(kept["inputs"]).st_mode & 0o777,
                         READ_ONLY_DIR)
        self.assertEqual(sorted(os.listdir(kept["inputs"])),
                         sorted(INPUT_NAMES))


class TheHomeLayoutIsDeclaredWhereItIsFrozen(unittest.TestCase):
    """A parent can only be closed once nothing more needs creating in it.

    `HOME_ENTRIES` is therefore a claim about the OTHER two components: the
    adapter's custody tree and the credential home's two places are siblings
    under this home, and if either grew a third the freeze would break it at
    run time on somebody else's machine.  This holds them to the list rather
    than trusting the comment beside it.
    """

    def test_every_home_entry_the_other_components_name_is_declared(self):
        import ast
        import pathlib

        declared = set(workspaces.HOME_ENTRIES)
        self.assertEqual(set(workspaces.ROOT_NAMES) - declared, set())
        found = set()
        for module in (oci, credentials):
            source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
            for node in ast.walk(ast.parse(source)):
                # `os.path.join(<something that is the home>, "<name>", ...)`
                # is how both of them name a sibling; the literal immediately
                # after the home expression is the entry.
                if not (isinstance(node, ast.Call)
                        and getattr(node.func, "attr", "") == "join"
                        and len(node.args) >= 2):
                    continue
                first = ast.unparse(node.args[0])
                if "_home()" not in first and "self.place" not in first:
                    continue
                if isinstance(node.args[1], ast.Constant) \
                        and isinstance(node.args[1].value, str):
                    found.add(node.args[1].value)
        self.assertTrue(found, "the walker found no sibling names to check")
        self.assertEqual(found - declared, set(),
                         f"named under the assignment home but not declared "
                         f"in HOME_ENTRIES: {sorted(found - declared)}")


class TheRuledTrustModel(unittest.TestCase):
    """Approver ruling M34768, as six measurements.

    The trust model is now explicit: the Worker Manager, its host uid, its
    private state root and the Docker daemon are TRUSTED.  This suite therefore
    stops defending the delivery against a malicious same-uid host process --
    the regress that took three rounds and had no name-based end, because one
    unprivileged uid can always replace a path it can create.

    What is defended instead is what the ruling names: the untrusted worker in
    its container, and ACCIDENTAL manager corruption.  The six properties below
    are that defence, and each is measured rather than asserted.
    """

    def setUp(self):
        import tempfile

        self._root = tempfile.TemporaryDirectory(prefix="v12-w33935-trust-")
        self.addCleanup(self._root.cleanup)
        self.storage = os.path.join(self._root.name, "storage")
        os.makedirs(self.storage)
        # W33936 review [P1]: allocation consumes the deployment's frozen
        # answer, so this suite configures one and reads it back.
        from baton_v12.worker_manager import ControlStore
        self.store = ControlStore.open(
            os.path.join(self._root.name, "control.sqlite3"),
            incarnation="trust-1",
            clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.store.close)
        self.group = composition.input_roots.configured_group(self.store)

    def documents(self, attempt):
        return composition.input_roots.documents(
            work_ref=dict(composition.WORK_REF),
            participant=composition.WHO, generation=1,
            runtime_attempt_id=attempt, given=None,
            policy_digest=composition.POLICY,
            profile_digest=composition.PROFILE)

    def composed(self, attempt="attempt-1"):
        roots = workspaces.assignment_workspace(self.group, self.storage, attempt)
        self.addCleanup(self._thaw_and_remove, attempt)
        given, manifest = self.documents(attempt)
        compose_input_root(roots["inputs"], given, manifest,
                           assignment=dict(manifest["assignment_ref"]),
                           runtime_attempt_id=attempt)
        return roots

    def _thaw_and_remove(self, attempt):
        home = os.path.join(self.storage, attempt)
        if os.path.isdir(home):
            os.chmod(home, 0o700)
            composition.forcibly_remove(home)

    # -- 1 and 2: unique per-attempt roots, and collision refused ------------

    def test_two_attempts_receive_two_private_roots(self):
        first = self.composed("attempt-1")
        second = self.composed("attempt-2")
        self.assertNotEqual(first["inputs"], second["inputs"])
        for one in ("inputs", "workspace"):
            self.assertFalse(
                os.path.realpath(first[one]).startswith(
                    os.path.realpath(second[one]) + os.sep))

    def test_a_colliding_home_cannot_alias_another_attempts_root(self):
        """Exclusive allocation refuses stale names rather than adopting them.

        A root resolved through a sibling symlink is still contained by the
        manager's storage, but it is not private to this attempt.  This is the
        collision/isolation case the clean-allocation comparison does not
        exercise.
        """
        first = workspaces.assignment_workspace(self.group, self.storage, "attempt-1")
        self.addCleanup(self._thaw_and_remove, "attempt-1")
        collision = os.path.join(self.storage, "attempt-collision")
        os.makedirs(collision)
        os.symlink(first["inputs"], os.path.join(collision, "inputs"))
        self.addCleanup(self._thaw_and_remove, "attempt-collision")
        with self.assertRaises(Exception):
            workspaces.assignment_workspace(self.group, self.storage,
                                            "attempt-collision")

    def test_a_colliding_home_cannot_alias_another_attempts_home(self):
        """The attempt home itself is part of the exclusive boundary.

        Checking only its children against the resolved home accepts a home
        symlink, because every child then resolves exactly beneath the wrong
        attempt used as that comparison's anchor.
        """
        first = workspaces.assignment_workspace(self.group, self.storage, "attempt-1")
        self.addCleanup(self._thaw_and_remove, "attempt-1")
        collision = os.path.join(self.storage, "attempt-home-collision")
        os.symlink(os.path.dirname(first["inputs"]), collision,
                   target_is_directory=True)
        self.addCleanup(os.unlink, collision)
        with self.assertRaises(Exception):
            workspaces.assignment_workspace(self.group, self.storage,
                                            "attempt-home-collision")

    def test_first_allocation_race_answers_or_refuses_in_contract(self):
        """An exclusive mkdir collision is a refusal, not a raw OS fault."""
        attempt = "attempt-allocation-race"
        home = os.path.join(self.storage, attempt)
        rendezvous = threading.Barrier(2)
        real_lexists = os.path.lexists

        def simultaneous_absence(place):
            found = real_lexists(place)
            if place == home:
                rendezvous.wait(timeout=2)
            return found

        def allocate():
            try:
                return "answer", workspaces.assignment_workspace(
                    self.group, self.storage, attempt)
            except ContractRefusal as refusal:
                return "refusal", refusal
            except Exception as error:
                return "leak", error

        with mock.patch.object(workspaces.os.path, "lexists",
                               side_effect=simultaneous_absence):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: allocate(), range(2)))
        self.addCleanup(self._thaw_and_remove, attempt)
        self.assertNotIn("leak", [kind for kind, _ in results], results)
        answers = [value for kind, value in results if kind == "answer"]
        self.assertTrue(answers, results)
        for answer in answers[1:]:
            self.assertEqual(answer, answers[0])

    def test_a_second_attempt_cannot_publish_over_a_published_delivery(self):
        """The collision refusal, at the boundary where a collision is
        distinguishable from a repetition.

        I first put this in `assignment_workspace`, and the suite refuted it:
        a RESTART asks for the same attempt's roots again, which is the
        ordinary adoption path and not a reused identity. A rule that cannot
        tell those apart using only a directory named after the attempt
        refuses the first to catch the second.

        Publication CAN tell them apart, because a delivery is composed once.
        """
        roots = self.composed("attempt-1")
        given, manifest = self.documents("attempt-1")
        with self.assertRaises(Exception) as caught:
            compose_input_root(roots["inputs"], given, manifest,
                               assignment=dict(manifest["assignment_ref"]),
                               runtime_attempt_id="attempt-1")
        self.assertIn("composed once and then frozen", str(caught.exception))

    def test_provisioning_is_idempotent_because_a_restart_needs_it(self):
        """Asking twice is not reusing an identity.

        Every caller reaches for its roots more than once on the way to a
        start, and a restarted manager reaches for them again across
        incarnations -- which is what `test_ended_runtime_adoption` drives.
        """
        first = workspaces.assignment_workspace(self.group, self.storage, "attempt-3")
        again = workspaces.assignment_workspace(self.group, self.storage, "attempt-3")
        self.addCleanup(self._thaw_and_remove, "attempt-3")
        self.assertEqual(first, again)
        # ...and after publication too, which is the restart case exactly.
        published = self.composed("attempt-7")
        self.assertEqual(
            workspaces.assignment_workspace(self.group, self.storage, "attempt-7"),
            published)

    # -- 3 and 4: complete before publication, immutable after --------------

    def test_a_partial_pair_is_never_published(self):
        """Both documents or neither: §7.0's order, and the rule that a mount
        is not the last chance to notice."""
        roots = workspaces.assignment_workspace(self.group, self.storage, "attempt-4")
        self.addCleanup(self._thaw_and_remove, "attempt-4")
        given, manifest = self.documents("attempt-4")
        # A PAIR THE MANAGER'S OWN LIVE IDENTITY DOES NOT MATCH. The pair
        # agrees with itself; what it does not agree with is the generation
        # this manager is composing for, which is the check §12 rule 16 puts
        # BEFORE anything is written.
        stale = dict(manifest["assignment_ref"], generation=2)
        with self.assertRaises(Exception) as caught:
            compose_input_root(roots["inputs"], given, manifest,
                               assignment=stale,
                               runtime_attempt_id="attempt-4")
        self.assertIn("is not thereby the delivery that was authorized",
                      str(caught.exception))
        # NOTHING WAS WRITTEN. Two documents that are not one delivery must
        # never exist on disk together, and half of one must never exist at
        # all.
        self.assertEqual(os.listdir(roots["inputs"]), [])

    def test_a_published_delivery_is_not_recomposed(self):
        roots = self.composed("attempt-5")
        given, manifest = self.documents("attempt-5")
        with self.assertRaises(Exception) as caught:
            compose_input_root(roots["inputs"], given, manifest,
                               assignment=dict(manifest["assignment_ref"]),
                               runtime_attempt_id="attempt-5")
        self.assertIn("composed once and then frozen", str(caught.exception))

    def test_the_published_documents_carry_no_write_bit_for_anybody(self):
        roots = self.composed("attempt-6")
        for name in INPUT_NAMES:
            mode = os.stat(os.path.join(roots["inputs"], name)).st_mode & 0o777
            with self.subTest(name=name):
                self.assertEqual(mode, READ_ONLY_FILE)
                self.assertEqual(mode & 0o222, 0)
        self.assertEqual(
            os.stat(roots["inputs"]).st_mode & 0o777, READ_ONLY_DIR)

    # -- 6: exact-attempt cleanup, retry and sibling isolation --------------

    def test_cleanup_reaches_one_attempt_and_retries_cleanly(self):
        kept = self.composed("attempt-kept")
        self.composed("attempt-going")
        self.assertTrue(
            workspaces.discard_workspace(self.storage, "attempt-going"))
        # A RETRY IS THE STATE ASKED FOR, not a refusal.
        self.assertFalse(
            workspaces.discard_workspace(self.storage, "attempt-going"))
        self.assertFalse(
            os.path.exists(os.path.join(self.storage, "attempt-going")))
        # AND THE SIBLING IS UNTOUCHED, contents and modes.
        self.assertEqual(sorted(os.listdir(kept["inputs"])),
                         sorted(INPUT_NAMES))
        self.assertEqual(os.stat(kept["inputs"]).st_mode & 0o777,
                         READ_ONLY_DIR)

    def test_cleanup_never_reaches_outside_the_storage_root(self):
        outside = os.path.join(self._root.name, "not-storage")
        os.makedirs(outside)
        with self.assertRaises(Exception):
            workspaces.discard_workspace(self.storage, "../not-storage")
        self.assertTrue(os.path.isdir(outside))

    def test_a_stale_entry_of_any_other_kind_is_refused_too(self):
        """The alias is one shape of stale state; these are the others.

        A regular file, a dangling link and a link to somewhere outside
        manager storage all resolve to something that is not this attempt's
        own directory, and each fails closed for the same reason rather than
        being adopted because it happened to pass containment.
        """
        outside = os.path.join(self._root.name, "elsewhere")
        os.makedirs(outside)
        cases = {
            "a regular file": lambda place: open(place, "w").close(),
            "a dangling link": lambda place: os.symlink(
                os.path.join(self._root.name, "gone"), place),
            "a link out of storage": lambda place: os.symlink(outside, place),
        }
        for index, (what, make) in enumerate(cases.items()):
            attempt = f"attempt-stale-{index}"
            with self.subTest(what=what):
                home = os.path.join(self.storage, attempt)
                os.makedirs(home)
                self.addCleanup(self._thaw_and_remove, attempt)
                make(os.path.join(home, "inputs"))
                with self.assertRaises(Exception) as caught:
                    workspaces.assignment_workspace(self.group, self.storage, attempt)
                self.assertIn("is not this attempt's own inputs root",
                              str(caught.exception))

    def test_an_aliased_home_is_refused_by_every_shape_it_can_take(self):
        """The reviewer's whole-home case, and its siblings.

        The first cut of this proof checked only `os.path.isdir(home)`, which
        FOLLOWS SYMLINKS -- so a home that was itself a link passed, and the
        child proofs then anchored on the wrong sibling and compared equal on
        both sides. A structural proof applied to the children and not to the
        thing they are measured against is not applied.
        """
        first = workspaces.assignment_workspace(self.group, self.storage, "attempt-anchor")
        self.addCleanup(self._thaw_and_remove, "attempt-anchor")
        outside = os.path.join(self._root.name, "elsewhere-home")
        os.makedirs(outside)
        homes = {
            "a link to another attempt's home":
                os.path.join(self.storage, "attempt-anchor"),
            "a link out of manager storage": outside,
            "a dangling link": os.path.join(self._root.name, "gone"),
        }
        for index, (what, target) in enumerate(homes.items()):
            attempt = f"attempt-aliased-{index}"
            with self.subTest(what=what):
                os.symlink(target, os.path.join(self.storage, attempt))
                with self.assertRaises(Exception) as caught:
                    workspaces.assignment_workspace(self.group, self.storage, attempt)
                self.assertIn("is not this attempt's own assignment home",
                              str(caught.exception))
        # AND THE FIRST ATTEMPT IS UNTOUCHED by any of it.
        self.assertEqual(
            workspaces.assignment_workspace(self.group, self.storage, "attempt-anchor"),
            first)

    def test_a_home_that_is_not_a_directory_is_refused(self):
        place = os.path.join(self.storage, "attempt-file")
        with open(place, "w", encoding="utf-8") as handle:
            handle.write("not a home")
        with self.assertRaises(Exception) as caught:
            workspaces.assignment_workspace(self.group, self.storage, "attempt-file")
        self.assertIn("is not this attempt's own assignment home",
                      str(caught.exception))

    def test_the_restart_lookup_still_answers_the_same_roots(self):
        """The path the previous cut broke, kept green beside the new guard.

        Reopening an attempt is not reusing an identity: its entries are real
        directories at their own paths, so the guard answers rather than
        refusing -- before publication and after it.
        """
        first = workspaces.assignment_workspace(self.group, self.storage, "attempt-reopen")
        self.addCleanup(self._thaw_and_remove, "attempt-reopen")
        self.assertEqual(
            workspaces.assignment_workspace(self.group, self.storage, "attempt-reopen"),
            first)
        published = self.composed("attempt-reopen-2")
        self.assertEqual(
            workspaces.assignment_workspace(self.group, self.storage, "attempt-reopen-2"),
            published)

    def _race_on(self, target, attempt):
        """Two allocations of one attempt, held together at `os.mkdir`.

        THE RENDEZVOUS MOVED WITH THE SEAM.  The reviewer's case holds both
        callers at `os.path.lexists`, which the correction removed -- create
        and prove are now one operation, so there is no separate observation
        of absence to synchronise on.  Left alone that case would pass while
        racing nothing, so this one holds them at the create ITSELF, which is
        where the collision now happens.
        """
        real_mkdir = os.mkdir
        rendezvous = threading.Barrier(2)

        def simultaneous_create(place, *rest, **named):
            if place == target:
                rendezvous.wait(timeout=5)
            return real_mkdir(place, *rest, **named)

        def allocate(_):
            try:
                return "answer", workspaces.assignment_workspace(
                    self.group, self.storage, attempt)
            except ContractRefusal as refusal:
                return "refusal", str(refusal)
            except Exception as error:                     # noqa: BLE001
                return "leak", f"{type(error).__name__}: {error}"

        with mock.patch.object(workspaces.os, "mkdir",
                               side_effect=simultaneous_create):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                return list(pool.map(allocate, range(2)))

    def test_the_home_create_race_answers_or_refuses_in_contract(self):
        attempt = "attempt-home-race"
        results = self._race_on(os.path.join(self.storage, attempt), attempt)
        self.addCleanup(self._thaw_and_remove, attempt)
        self.assertNotIn("leak", [kind for kind, _ in results], results)
        answers = [value for kind, value in results if kind == "answer"]
        self.assertTrue(answers, results)
        for answer in answers[1:]:
            self.assertEqual(answer, answers[0])

    def test_the_child_create_race_answers_or_refuses_in_contract(self):
        """The same contract one level down, which the review asks for by name.

        The loser of a child create falls through to exactly the proof a
        pre-existing entry gets, so it reopens the real directory rather than
        faulting -- the same question asked once, whether the directory has
        been there for a week or for a microsecond.
        """
        attempt = "attempt-child-race"
        results = self._race_on(
            os.path.join(self.storage, attempt, "inputs"), attempt)
        self.addCleanup(self._thaw_and_remove, attempt)
        self.assertNotIn("leak", [kind for kind, _ in results], results)
        answers = [value for kind, value in results if kind == "answer"]
        self.assertTrue(answers, results)
        for answer in answers[1:]:
            self.assertEqual(answer, answers[0])

    def test_the_loser_of_a_create_race_reopens_rather_than_refusing(self):
        """Both callers get roots, because both are the same attempt.

        A refusal would also satisfy the contract, and this pins the stronger
        outcome the design actually reaches: the loser proves the directory is
        this attempt's own and answers with it.
        """
        attempt = "attempt-race-reopen"
        results = self._race_on(os.path.join(self.storage, attempt), attempt)
        self.addCleanup(self._thaw_and_remove, attempt)
        self.assertEqual([kind for kind, _ in results], ["answer", "answer"],
                         results)


class TheConfiguredWorkspaceGroup(Delivery):
    """W33936, approver rulings M34630 and M34916, and the review that followed.

    The deployment provisions ONE dedicated non-authority group and grants this
    manager permission to use it.  This Work owns the configuration, the
    validation, the allocation-time adoption, the pre-launch proof and the
    engine wiring -- and never creates or modifies a host group.

    THE PREVIOUS CUT OF THIS CLASS WAS A NEGATIVE ENVIRONMENT PROBE, and the
    review said so correctly: it attempted an adoption it knew would fail and
    then required the worker's write to be DENIED, which is the original defect
    dressed as an assertion.  Every case below proves the corrected behaviour
    instead.

    WHICH GROUP THIS PROOF CONFIGURES, and what that does and does not show.
    No dedicated `baton-workspace` group is provisioned on this host and this
    manager may not create one, so the fixture configures the group it can
    actually `chgrp` to -- `os.getgid()`.  That makes every step REAL: the
    allocation adopts the group, the daemon applies it, and the worker writes.
    What it does NOT show is that a manager's own primary group is an
    acceptable production configuration; M34630 requires a dedicated
    non-authority group, and that is a property of a deployment which no code
    here can measure.  What `check_workspace_group` CAN refuse it does, and the
    first case drives every one of those refusals.
    """

    @property
    def PROOF_GROUP(self):
        """The deployment's CONFIGURED group, as the capability it now is.

        W33936 review [P1]: the group stopped being an integer a caller
        composes. This suite therefore configures one and reads the manager's
        own record back, which is the sequence a deployment performs -- and
        the negative below proves that a second group this manager also holds
        refuses despite being perfectly usable by the process.
        """
        return composition.input_roots.configured_group(self.store)

    def allocated(self):
        """One assignment's roots, allocated through the CANONICAL boundary.

        Not a hand-built directory: `assignment_workspace` is where the review
        required the grant to be wired, so a case that adopted the group beside
        it would prove a helper rather than the path a manager takes.
        """
        given, assignment = self.activated()
        roots = workspaces.assignment_workspace(
            self.group, self.storage, self.attempt)
        inputs = self.composed(roots, given, assignment)
        return roots, inputs

    def executing(self, roots):
        adapter = self.adapter(roots=roots, mounts=self.plan(roots))
        adapter.workspace_group = self.PROOF_GROUP
        return adapter

    def test_the_group_is_validated_and_never_inferred(self):
        for bad, why in ((0, "root"), (-1, "negative"), (True, "a bool"),
                         ("1000", "text"), (99998, "not held")):
            with self.subTest(why=why):
                with self.assertRaises(ContractRefusal):
                    workspaces.check_workspace_group(bad)
        self.assertEqual(
            workspaces.check_workspace_group(self.PROOF_GROUP.gid),
            self.PROOF_GROUP.gid)

    def test_allocation_puts_the_workspace_in_the_configured_group(self):
        """The wiring the review found missing, at the canonical boundary."""
        roots, _inputs = self.allocated()
        held = os.lstat(roots["workspace"])
        self.assertEqual(held.st_gid, self.PROOF_GROUP.gid)
        self.assertEqual(held.st_mode & 0o7777, 0o2770)
        # AND THE INPUT ROOT IS UNCHANGED by any of it: the grant is over the
        # writable tree and nothing else.
        self.assertNotEqual(os.lstat(roots["inputs"]).st_mode & 0o7777, 0o2770)

    def test_an_allocation_takes_only_the_deployments_own_answer(self):
        """Review [P1], and this is the case it asked for.

        The defect was that every layer took the same raw integer from its
        caller and every layer agreed. So a group is no longer a number: it is
        a capability, and the only thing that mints one is a read of this
        manager's own record of what the deployment configured.
        """
        with self.assertRaises(TypeError):
            workspaces.assignment_workspace(self.storage, "no-group")
        for bad in (0, -1, "1000", 99998, os.getgid()):
            with self.subTest(bad=bad):
                with self.assertRaises(ContractRefusal) as caught:
                    workspaces.assignment_workspace(
                        bad, self.storage, f"bad-{bad}")
                self.assertIn("configured group", caught.exception.message)
        # AND THE CAPABILITY CANNOT BE MINTED EITHER. A type a caller can
        # construct would leave the hole exactly where it was.
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.WorkspaceGroup(os.getgid())
        self.assertIn("is not constructed", caught.exception.message)

    def test_a_second_held_group_refuses_despite_being_usable(self):
        """THE REVIEW'S NAMED NEGATIVE.

        The manager holds configured group A and an unrelated group B -- here
        `nogroup`, which this process really is a member of. B is perfectly
        usable: it is a non-zero gid in `os.getgroups()`, so every check the
        old code had would have passed it. It refuses now, because what
        authorizes a group is the deployment's record and not the manager's
        membership.
        """
        held = set(os.getgroups()) | {os.getgid()}
        other = next((one for one in sorted(held)
                      if one not in (0, self.PROOF_GROUP.gid)), None)
        if other is None:
            self.skipTest("this process holds only its configured group, so "
                          "there is no second usable group to refuse")
        # B IS USABLE, which is what makes the refusal meaningful.
        self.assertEqual(workspaces.check_workspace_group(other), other)
        # ...AND IS STILL REFUSED at allocation and at the vector, because
        # neither takes an integer any more.
        with self.assertRaises(ContractRefusal):
            workspaces.assignment_workspace(other, self.storage, "group-b")
        with self.assertRaises(ContractRefusal):
            oci.run_vector(self.engine, image_digest=self.image_digest,
                           labels=self.labels(),
                           assignment_roots=dict(self.roots()),
                           posture="execution", workspace_group=other,
                           name="baton-w33936-b")
        # AND THE DEPLOYMENT'S OWN RECORD STILL ANSWERS A, not B.
        self.assertNotEqual(self.PROOF_GROUP.gid, other)

    def test_the_worker_creates_updates_and_removes_in_its_workspace(self):
        """THE ACCEPTANCE, positive, in the exact composed container.

        The three acts the finding names, each answered separately, in the
        argv `request_runtime_start` produced.
        """
        roots, inputs = self.allocated()
        request_runtime_start(self.store, self.executing(roots),
                              attempt_id=self.attempt, inputs=inputs)
        answered = self.inside(["/workspace"],
                               program=workspace_program("/workspace"))
        self.assertEqual(answered["running_as"], [WORKER_UID, WORKER_UID])
        self.assertIn(self.PROOF_GROUP.gid, answered["groups"])
        self.assertEqual(answered["root"]["mode"], "0o2770")
        self.assertTrue(answered["created"], answered)
        self.assertTrue(answered["updated"], answered)
        self.assertTrue(answered["removed"], answered)

    def test_what_the_worker_creates_inherits_the_workspace_group(self):
        """The ruling's own required proof, and the reason for the setgid bit.

        A file owned by the worker's primary gid would be one the manager --
        which is not that gid and not in that group -- could not collect. The
        setgid directory is what makes the worker's output the manager's to
        read without widening anything.
        """
        roots, inputs = self.allocated()
        request_runtime_start(self.store, self.executing(roots),
                              attempt_id=self.attempt, inputs=inputs)
        answered = self.inside(["/workspace"],
                               program=workspace_program("/workspace"))
        self.assertEqual(answered["made"]["gid"], self.PROOF_GROUP.gid,
                         answered)
        self.assertNotEqual(answered["made"]["uid"], os.getuid())
        self.assertEqual(answered["inner"]["gid"], self.PROOF_GROUP.gid,
                         answered)
        self.assertTrue(answered["inner"]["setgid"], answered)
        # ...AND THE MANAGER READS IT, on the host, as itself.
        collected = os.path.join(roots["workspace"], "collected.txt")
        with open(collected, "rb") as handle:
            self.assertEqual(handle.read(), b"collect me")

    def test_an_owner_only_output_fails_closed_rather_than_widening(self):
        """The ruling's negative half.

        A worker file at 0600 is the worker's alone: the manager shares the
        group and the group has no bits. The right answer is that the manager
        cannot read it and does not chmod it -- widening permission to collect
        an output would make the grant unbounded whenever a worker asked.
        """
        roots, inputs = self.allocated()
        request_runtime_start(self.store, self.executing(roots),
                              attempt_id=self.attempt, inputs=inputs)
        self.inside(["/workspace"], program=workspace_program("/workspace"))
        shut = os.path.join(roots["workspace"], "owner-only.txt")
        before = os.lstat(shut).st_mode & 0o7777
        self.assertEqual(before, 0o600)
        with self.assertRaises(PermissionError):
            open(shut, "rb").close()
        # NOTHING WIDENED IT.  The mode after the failed read is the mode the
        # worker set, which is what "fails closed" has to mean if it means
        # anything.
        self.assertEqual(os.lstat(shut).st_mode & 0o7777, before)

    def test_the_applied_group_is_asked_of_the_engine_and_the_process(self):
        """`--group-add` composed is one fact; applied is the one that counts.

        And the pinned identity is untouched, which is the whole difference
        from the rejected `--user 65532:<gid>` design.
        """
        roots, inputs = self.allocated()
        request_runtime_start(self.store, self.executing(roots),
                              attempt_id=self.attempt, inputs=inputs)
        argv = next(one for one in reversed(self.engine_calls) if "run" in one)
        self.assertEqual(argv[argv.index("--group-add") + 1],
                         str(self.PROOF_GROUP.gid))
        self.assertEqual(argv[argv.index("--user") + 1], "65532:65532")
        held = self.inspected(self.attempt_row()["runtime_id"])
        self.assertIn(str(self.PROOF_GROUP.gid),
                      [str(one) for one in
                       (held["HostConfig"].get("GroupAdd") or [])],
                      held["HostConfig"].get("GroupAdd"))
        self.assertEqual(held["Config"]["User"], "65532:65532")

    def test_the_grant_reaches_no_surface_but_the_workspace(self):
        """Correction boundary: the group grants write HERE and nowhere else.

        Every other place the container can reach is asked in the same
        container, under the same argv, holding the same group.
        """
        roots, inputs = self.allocated()
        request_runtime_start(self.store, self.executing(roots),
                              attempt_id=self.attempt, inputs=inputs)
        answered = self.inside(["/input", "/input/input-manifest.json",
                                "/run/baton/launch.json"])
        self.assertEqual(answered["running_as"], [WORKER_UID, WORKER_UID])
        for place in ("/input", "/input/input-manifest.json",
                      "/run/baton/launch.json"):
            with self.subTest(place=place):
                # NOT REACHED AT ALL, or reached and not writable -- both are
                # the answer. The read-only bind makes the probe's append fail
                # before it opens, so `wrote` is absent rather than False, and
                # a case that demanded the member would pass only on the
                # weaker of the two outcomes.
                self.assertFalse(answered[place].get("wrote", False),
                                 answered[place])
        # AND THE MANAGER'S OWN SIBLINGS ARE NOT EVEN MOUNTED, which is a
        # stronger statement than "not writable" and the one the topology
        # actually makes.
        argv = next(one for one in reversed(self.engine_calls) if "run" in one)
        home = os.path.dirname(roots["workspace"].rstrip("/"))
        for sibling in ("custody", "credentials", "credential-state"):
            with self.subTest(sibling=sibling):
                self.assertNotIn(os.path.join(home, sibling), " ".join(argv))

    def test_a_consent_runtime_is_given_no_supplementary_group(self):
        roots = self.roots()
        with self.assertRaises(ContractRefusal) as caught:
            oci.run_vector(self.engine, image_digest=self.image_digest,
                           labels=self.labels(), assignment_roots=dict(roots),
                           posture="consent", name="baton-w33936-consent",
                           workspace_group=self.PROOF_GROUP)
        self.assertIn("no supplementary group", str(caught.exception))

    def test_an_unconfigured_execution_refuses_before_the_engine(self):
        """Review [P0], and my last cut had this exactly backwards.

        I argued that composing no group left an unconfigured deployment
        "unchanged". Unchanged IS the defect: a start with no group
        deterministically produces the container this Work exists to correct.
        There is no legacy execution posture, and the refusal happens before
        the engine is invoked -- proved by counting the engine's `run` calls
        across the attempt.
        """
        roots, inputs = self.allocated()
        adapter = self.adapter(roots=roots, mounts=self.plan(roots))
        adapter.workspace_group = None
        before = len([one for one in self.engine_calls if "run" in one])
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt, inputs=inputs)
        self.assertIn("configured workspace group", str(caught.exception))
        self.assertEqual(
            len([one for one in self.engine_calls if "run" in one]), before,
            "the engine was invoked for a start that had to refuse")

    def test_a_root_that_left_the_group_refuses_before_the_engine(self):
        """The pre-launch proof, driven by the thing it exists to catch.

        A grant established at allocation is not a grant at LAUNCH. The root is
        moved out of the configured mode between the two -- which a restart
        under a changed configuration, or an operator, can do -- and the start
        refuses with nothing created.
        """
        roots, inputs = self.allocated()
        os.chmod(roots["workspace"], 0o700)
        before = len([one for one in self.engine_calls if "run" in one])
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, self.executing(roots),
                                  attempt_id=self.attempt, inputs=inputs)
        self.assertIn("0o700", str(caught.exception))
        self.assertEqual(
            len([one for one in self.engine_calls if "run" in one]), before,
            "the engine was invoked for a start that had to refuse")

    def test_manager_cleanup_of_worker_content_is_measured_not_assumed(self):
        """The cleanup half of the acceptance, and it does NOT come out clean.

        MEASURED, on a real daemon, with the corrected mechanism in place:

          * a FILE the worker created at the workspace root is removable by the
            manager -- the root is group-writable and unlinking is a write to
            the ROOT;
          * an EMPTY directory the worker created is also removable, for the
            same reason -- `rmdir` is a write to the parent;
          * a directory the worker created WITH CONTENT IN IT is not. Its mode
            comes from the worker's umask (`drwxr-sr-x` here), so the group has
            no write, and the manager owns neither the directory nor a way to
            `chmod` it. `os.chmod` is EPERM and unlinking inside it is EACCES.

        So a worker that creates a populated subdirectory -- which is what any
        real worker does -- leaves a tree this manager cannot remove. That is a CONSEQUENCE of the approved mechanism rather
        than a defect in it, and it is not this Work's to decide: making the
        root `02777` widens what the ruling narrowed, and running cleanup as
        the worker identity is a new mechanism. It is raised for a ruling and
        recorded here as the measurement that raised it.

        What this cut DOES own is the failure's shape: it fails closed, and it
        names which party owns the thing in the way instead of surfacing a raw
        errno from inside a walk.
        """
        roots, inputs = self.allocated()
        request_runtime_start(self.store, self.executing(roots),
                              attempt_id=self.attempt, inputs=inputs)
        self.inside(["/workspace"], program=workspace_program("/workspace"))
        place = roots["workspace"]
        # THE FILE HALF, and it works.
        collected = os.path.join(place, "collected.txt")
        self.assertTrue(os.path.exists(collected))
        os.unlink(collected)
        self.assertFalse(os.path.exists(collected))
        # AND AN EMPTY WORKER DIRECTORY IS REMOVABLE TOO, because removing it
        # is a write to the group-writable ROOT rather than to the directory.
        empty = os.path.join(place, "empty-worker-dir")
        os.rmdir(empty) if os.path.isdir(empty) else None
        # THE DIRECTORY-WITH-CONTENT HALF, and it is not.
        inner = os.path.join(place, "worker-made-dir")
        held = os.lstat(inner)
        self.assertNotEqual(held.st_uid, os.getuid(),
                            "the worker did not create this; the case proves "
                            "nothing about ownership it does not have")
        with self.assertRaises(PermissionError):
            os.chmod(inner, 0o700)
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.discard_workspace(self.storage, self.attempt)
        self.assertIn("owned by uid", str(caught.exception))
        self.assertIn("fails closed", str(caught.exception))
        # AND NOTHING WAS WIDENED on the way to that refusal.
        self.assertEqual(os.lstat(inner).st_mode & 0o7777,
                         held.st_mode & 0o7777)

    def test_one_assignment_workspace_reaches_no_other(self):
        """Sibling isolation, with both roots in the SAME configured group.

        The group is deployment-wide, so this is the case that says the group
        is not what separates two assignments -- the mount plan is. A second
        assignment's workspace is adopted into the same group and is still
        absent from this container.
        """
        roots, inputs = self.allocated()
        stranger = workspaces.assignment_workspace(
            self.group, self.storage, "another-assignment")["workspace"]
        self.assertEqual(os.lstat(stranger).st_gid, self.PROOF_GROUP.gid)
        request_runtime_start(self.store, self.executing(roots),
                              attempt_id=self.attempt, inputs=inputs)
        argv = next(one for one in reversed(self.engine_calls) if "run" in one)
        self.assertNotIn(stranger, " ".join(argv))
        answered = self.inside([stranger])
        self.assertIn("stat", answered[stranger], answered[stranger])


class DockerConfiguredGroup(TheConfiguredWorkspaceGroup, unittest.TestCase):
    engine = "docker"
    required = True


class PodmanConfiguredGroup(TheConfiguredWorkspaceGroup, unittest.TestCase):
    engine = "podman"
    required = False
