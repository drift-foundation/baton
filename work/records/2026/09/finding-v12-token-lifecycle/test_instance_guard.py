"""W275774 — DESIGN HOST-8: one active manager per instance, refused at startup.

Owner 279031 selected the mechanism and this file is its evidence: an EXCLUSIVE
NON-BLOCKING OS FILE LOCK on a descriptor held for the manager's lifetime, a duplicate
start REFUSED before it dispatches work or mutates a managed resource, no standby, no
takeover, and independent instances untouched.

WHAT THE SUPERSEDED EVIDENCE WAS, AND WHAT IT IS NOW. `test_shared_authority.py` proves
that the token journal excludes across two `ControlStore` connections. Review 21:08:45Z
is right that this is SEQUENTIAL same-store evidence and not startup-process exclusion,
and owner 278980/279004 removed the shared-workspace scenario it was written for -- so
its "two managers, one journal" reading is obsolete and is recorded as such in PROGRESS.
The measurements stand as WITHIN-INSTANCE journal safety; the exclusion HOST-8 asks for
is the one below, and it is proved with REAL COMPETING PROCESSES.

AND THE MARKER IS NOT THIS GUARD. `.baton-workspace-authority`, delivered at 279010,
refuses a DIFFERENT control store over one workspace root at configuration time and
permits same-store callers -- which is exactly why it cannot be the HOST-8 guard, as the
review states. Both exist: the marker is a configuration fact written once, the guard is
a live lock. The last case here asserts they do not interfere.

Real disposable stores and roots; the competing manager is a real subprocess. No live
engine, no provider, no container.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, workspaces

NOW = "2026-08-24T00:00:00.000Z"

# The competing manager, as a REAL PROCESS. It takes the guard, reports what happened on
# stdout, and then either exits immediately or waits to be told to -- which is how a case
# chooses between "a live manager holds it" and "a dead manager's guard is gone".
COMPETITOR = """
import json, os, sys
sys.path.insert(0, %(source)r)
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, workspaces

store = ControlStore.open(%(database)r, incarnation="competitor",
                          clock=lambda: %(now)r)
try:
    guard = workspaces.hold_manager_instance(store, %(place)r)
except ContractRefusal as refusal:
    print(json.dumps({"held": False, "category": refusal.category,
                      "code": refusal.code, "message": refusal.message}),
          flush=True)
    raise SystemExit(0)
child = None
if %(fork)r:
    # A CHILD THAT OUTLIVES THIS MANAGER, which is the shape the retention case needs.
    child = os.fork()
    if child == 0:
        while True:
            try:
                os.read(0, 1)
            except OSError:
                pass
            import time
            time.sleep(0.05)
print(json.dumps({"held": True, "path": guard.path, "child": child}), flush=True)
if %(wait)r:
    sys.stdin.readline()
"""


class TheGuardIsHeldByOneProcess(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="v12-instance-guard-")
        self.addCleanup(self._remove, self.root)
        self.place = os.path.join(self.root, "storage")
        os.makedirs(self.place)
        self.path = os.path.join(self.root, "control.sqlite3")
        self.store = ControlStore.open(self.path, incarnation="manager-1",
                                       clock=lambda: NOW)
        self.addCleanup(self.store.close)

    @staticmethod
    def _remove(place):
        import shutil
        shutil.rmtree(place, ignore_errors=True)

    def competitor(self, *, database=None, place=None, wait=False, fork=False):
        """A REAL second manager process, and what its own startup answered."""
        source = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(workspaces.__file__))))
        program = COMPETITOR % {"source": source,
                                "database": database or self.path,
                                "place": place or self.place,
                                "now": NOW, "wait": wait, "fork": fork}
        running = subprocess.Popen(
            [sys.executable, "-c", program], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, text=True)
        self.addCleanup(self._reap, running)
        answered = json.loads(running.stdout.readline())
        return running, answered

    @staticmethod
    def _reap(running):
        """Kill if still alive, wait, and CLOSE THIS TEST'S OWN HANDLES.

        Review 21:26:24Z asked for the hygiene: a case that leaves a pipe open reports a
        ResourceWarning that has nothing to do with what it measured.
        """
        if running.poll() is None:
            running.kill()
        running.wait(timeout=10)
        for handle in (running.stdin, running.stdout, running.stderr):
            if handle is not None and not handle.closed:
                handle.close()

    # -- the exclusion, between real processes ---------------------------------

    def test_a_DUPLICATE_START_is_refused_while_another_process_holds_it(self):
        """HOST-8's own sentence, measured: the second manager refuses startup.

        The first manager is a real process holding the guard and still alive. The
        second start is refused `policy/denied`, names the workspace and the holder's
        control store, and says what to do -- and it is not standby: the call returns by
        raising, having waited for nothing.
        """
        living, held = self.competitor(wait=True)
        self.assertTrue(held["held"], held)
        self.assertEqual(living.poll(), None, "the first manager must still be alive")
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.hold_manager_instance(self.store, self.place)
        self.assertEqual(caught.exception.category, "policy")
        self.assertEqual(caught.exception.code, "denied")
        self.assertIn("another manager is already active", caught.exception.message)
        self.assertIn(self.path, caught.exception.message,
                      "the refusal names the holder's own control store")
        self.assertIn("configuration error", caught.exception.message)

    def test_THIS_process_holds_it_and_the_next_process_is_refused(self):
        """The same exclusion in the other direction, so neither side is privileged."""
        guard = workspaces.hold_manager_instance(self.store, self.place)
        self.addCleanup(guard.release)
        _running, answered = self.competitor()
        self.assertFalse(answered["held"], answered)
        self.assertEqual(answered["code"], "denied")
        self.assertIn("another manager is already active", answered["message"])

    def test_A_DEAD_MANAGERS_GUARD_IS_GONE(self):
        """EXIT IS THE RELEASE, which is why the descriptor is the guard.

        The first process takes the guard and exits. No cleanup ran, nothing was
        unlinked, and the next manager starts -- because the lock lived exactly as long
        as that process did.
        """
        running, held = self.competitor()
        self.assertTrue(held["held"], held)
        self.assertEqual(running.wait(timeout=10), 0)
        guard = workspaces.hold_manager_instance(self.store, self.place)
        self.addCleanup(guard.release)
        self.assertTrue(os.path.exists(guard.path),
                        "the file stays; the LOCK is what was released")

    def test_A_KILLED_MANAGERS_GUARD_IS_GONE_TOO(self):
        """A manager that died without running any code still releases it, which is the
        property a lease would have to approximate with a clock and this does not."""
        running, held = self.competitor(wait=True)
        self.assertTrue(held["held"], held)
        running.kill()
        running.wait(timeout=10)
        guard = workspaces.hold_manager_instance(self.store, self.place)
        self.addCleanup(guard.release)
        self.assertEqual(guard.holder, self.path)

    def test_AN_INDEPENDENT_INSTANCE_IS_UNTOUCHED(self):
        """Many managers per machine, each with its own database and workspace.

        HOST-8 allows this explicitly and it is not an afterthought: a guard that
        excluded independent instances would be the machine-wide singleton the owner
        ruled out.
        """
        guard = workspaces.hold_manager_instance(self.store, self.place)
        self.addCleanup(guard.release)
        beside = os.path.join(self.root, "beside-storage")
        os.makedirs(beside)
        other = ControlStore.open(os.path.join(self.root, "beside.sqlite3"),
                                  incarnation="manager-beside",
                                  clock=lambda: NOW)
        self.addCleanup(other.close)
        _running, answered = self.competitor(
            database=os.path.join(self.root, "beside.sqlite3"), place=beside)
        self.assertTrue(answered["held"], answered)

    # -- and the three ways a duplicate might try to get around it -------------

    def test_AN_ALIAS_OF_THE_ROOT_IS_ONE_GUARD_AND_NOT_TWO(self):
        """A symlinked root, a `..` and a trailing slash are one directory, so they are
        one guard -- resolved before the path is composed, not compared as text."""
        guard = workspaces.hold_manager_instance(self.store, self.place)
        self.addCleanup(guard.release)
        alias = os.path.join(self.root, "alias")
        os.symlink(self.place, alias)
        for spelling in (alias, self.place + "/", os.path.join(
                self.place, "..", os.path.basename(self.place))):
            with self.subTest(spelling=spelling):
                _running, answered = self.competitor(place=spelling)
                self.assertFalse(answered["held"],
                                 f"{spelling} took a second guard")

    def test_A_REFUSED_START_REPLACES_NOTHING(self):
        """NO REPLACEMENT OF A HELD GUARD, from this implementation's own side.

        A duplicate start opens the guard without `O_TRUNC`, never unlinks it and never
        rewrites it: the file another manager holds is byte-for-byte and object-for-object
        what it was. That is the half of the owner's requirement this code owns.
        """
        _living, held = self.competitor(wait=True)
        before = os.stat(held["path"])
        body = open(held["path"], "rb").read()
        with self.assertRaises(ContractRefusal):
            workspaces.hold_manager_instance(self.store, self.place)
        after = os.stat(held["path"])
        self.assertEqual((before.st_dev, before.st_ino),
                         (after.st_dev, after.st_ino))
        self.assertEqual(open(held["path"], "rb").read(), body,
                         "a refused start rewrote the holder's own record")

    def test_A_GUARD_THAT_IS_NOT_THE_FILE_AT_ITS_PATH_IS_REFUSED(self):
        """THE IDENTITY CHECK, driven at the one window it exists for.

        Between opening the guard and holding it, the file at that path can be replaced
        by something outside this manager -- and a lock on an object the path no longer
        names excludes nobody. The replacement is injected with a targeted patch on this
        module's own `os.stat`, because no production path performs it; what is asserted
        is the refusal, not how the bytes moved.

        AND THE HONEST LIMIT, recorded rather than implied: an advisory lock cannot
        survive its own NAME being removed. A process that unlinks a held guard does
        destroy the exclusion, and nothing in this manager unlinks it -- which is why the
        case above measures that this implementation replaces nothing, and this one
        measures that a path/descriptor disagreement fails closed.
        """
        from unittest import mock

        class Elsewhere:
            st_dev = 987654321
            st_ino = 123456789

        with mock.patch.object(workspaces.os, "stat",
                               return_value=Elsewhere()):
            with self.assertRaises(ContractRefusal) as caught:
                workspaces.hold_manager_instance(self.store, self.place)
        self.assertEqual(caught.exception.code, "denied")
        self.assertIn("was replaced while being taken", caught.exception.message)
        # AND THE GUARD IS STILL TAKEABLE afterwards: the refusal closed its descriptor
        # rather than leaving a lock nobody can account for.
        guard = workspaces.hold_manager_instance(self.store, self.place)
        self.addCleanup(guard.release)

    def test_THE_GUARD_IS_NOT_INHERITED_BY_A_CHILD(self):
        """NO CHILD RETENTION: the descriptor is close-on-exec, so nothing this manager
        execs can hold the guard open after the manager is gone."""
        import fcntl as posix_fcntl

        guard = workspaces.hold_manager_instance(self.store, self.place)
        self.addCleanup(guard.release)
        flags = posix_fcntl.fcntl(guard._descriptor, posix_fcntl.F_GETFD)
        self.assertTrue(flags & posix_fcntl.FD_CLOEXEC,
                        "an inherited guard would outlive its manager")

    # -- fork, which `O_CLOEXEC` says nothing about ----------------------------

    def test_a_FORK_CHILD_INHERITS_NO_OWNERSHIP(self):
        """THE P1 REVIEW 21:26:24Z REPRODUCED, as my own case.

        `O_CLOEXEC` covers `exec` and a fork child never execs: it held the live
        descriptor AND the process cache, so it could outlive its parent still holding
        the lock, or answer "I am the manager" without acquiring anything. Observed
        `(True, True)` where `(False, False)` is required.

        THREE FACTS, CHECKED IN THE CHILD ITSELF: the inherited descriptor is closed, the
        cache is empty, and asking for the guard REFUSES -- because the parent still holds
        it and a child must acquire like anybody else.
        """
        guard = workspaces.hold_manager_instance(self.store, self.place)
        self.addCleanup(guard.release)
        reading, writing = os.pipe()
        child = os.fork()
        if child == 0:                                     # pragma: no cover - the child
            os.close(reading)
            answer = {}
            try:
                try:
                    os.fstat(guard._descriptor)
                    answer["descriptor"] = "inherited"
                except (OSError, TypeError):
                    answer["descriptor"] = "closed"
                answer["cached"] = self.place in workspaces._HELD_GUARDS
                try:
                    workspaces.hold_manager_instance(self.store, self.place)
                    answer["asked"] = "held"
                except ContractRefusal as refusal:
                    answer["asked"] = refusal.code
                os.write(writing, json.dumps(answer).encode())
            finally:
                os._exit(0)
        os.close(writing)
        try:
            answered = json.loads(os.read(reading, 4096).decode())
        finally:
            os.close(reading)
        self.assertEqual(os.waitpid(child, 0)[1], 0)
        self.assertEqual(answered["descriptor"], "closed",
                         "a forked child retained the manager's descriptor")
        self.assertFalse(answered["cached"],
                         "a forked child inherited the ownership cache")
        self.assertEqual(answered["asked"], "denied",
                         "a forked child was allowed to act as the manager")

    def test_THE_PARENTS_EXCLUSION_SURVIVES_THE_FORK(self):
        """CLOSED, NOT UNLOCKED -- and this is the case that tells them apart.

        `flock` holds its lock on the open file description that fork SHARES, so a child
        that called `LOCK_UN` would release its parent's exclusion. The child closes its
        own descriptor instead, and the proof is that a separate PROCESS is still refused
        afterwards.
        """
        guard = workspaces.hold_manager_instance(self.store, self.place)
        self.addCleanup(guard.release)
        child = os.fork()
        if child == 0:                                     # pragma: no cover - the child
            os._exit(0)
        self.assertEqual(os.waitpid(child, 0)[1], 0)
        _running, answered = self.competitor()
        self.assertFalse(answered["held"],
                         "the fork released the parent's own exclusion")
        self.assertEqual(answered["code"], "denied")

    def test_a_SURVIVING_FORK_CHILD_CANNOT_RETAIN_THE_LOCK(self):
        """AND THE OUTLIVING CASE, with real processes on both sides.

        A manager takes the guard, forks a child that outlives it, and exits. If the
        child had kept the inherited descriptor the guard would still be held by a
        process that never acquired it and never will release it deliberately -- so the
        measurement is that the NEXT manager starts.
        """
        running, held = self.competitor(wait=True, fork=True)
        self.assertTrue(held["held"], held)
        surviving = held["child"]
        running.stdin.write("go\n")
        running.stdin.flush()
        self.assertEqual(running.wait(timeout=10), 0)
        self.assertTrue(self._alive(surviving),
                        "the case needs the child to actually outlive its parent")
        try:
            guard = workspaces.hold_manager_instance(self.store, self.place)
            self.addCleanup(guard.release)
            self.assertEqual(guard.holder, self.path)
        finally:
            os.kill(surviving, 9)

    @staticmethod
    def _alive(pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    # -- what the guard is NOT -------------------------------------------------

    def test_RELEASING_THE_GUARD_FREES_NO_WORKER_TOKEN(self):
        """The review's own boundary, asserted: guard release is not a cessation.

        A resource held by a token is still held after the manager that guarded the
        instance has gone. Anything else would turn a process exit into evidence about a
        container nobody observed.
        """
        from baton_v12.worker_manager import tokens

        guard = workspaces.hold_manager_instance(self.store, self.place)
        token = tokens.acquire(self.store, "workspace:1:2",
                               operation="runtime.start:1",
                               execution="attempt-1", attempt="attempt-1")
        self.assertEqual(token["generation"], 1)
        guard.release()
        held = tokens.outstanding(self.store, "workspace:1:2")
        self.assertEqual([one["generation"] for one in held], [1],
                         "a released guard must not return anybody's resource")

    def test_THE_MARKER_AND_THE_GUARD_DO_NOT_INTERFERE(self):
        """They answer different questions and both survive the other.

        `.baton-workspace-authority` is the configuration fact written once;
        `.baton-manager-instance` is the live lock. The marker permits same-store
        callers -- which is why the review is right that it is not this guard -- and the
        guard refuses a second ACTIVE manager whatever the marker says.
        """
        workspaces.configure_workspace_storage(self.store, self.place)
        self.assertEqual(workspaces.claimed_workspace_authority(self.place),
                         self.store.database)
        guard = workspaces.hold_manager_instance(self.store, self.place)
        self.addCleanup(guard.release)
        _running, answered = self.competitor()
        self.assertFalse(answered["held"],
                         "the same store is permitted by the marker and refused by "
                         "the guard, which is the whole difference")
        self.assertEqual(workspaces.claimed_workspace_authority(self.place),
                         self.store.database, "and the marker is unchanged")


class TheREALSTARTUPSEAMRefusesBeforeAnything(unittest.TestCase):
    """THE DUPLICATE REFUSED AT THE PRODUCTION STARTUP, and before it writes.

    Review 21:26:24Z asked for this and named the defect it found on the way: the guard
    was taken AFTER `worker_preflight`'s two configuring acts, so a duplicate manager
    committed configuration into the database the ACTIVE manager owns before being
    refused. HOST-8 wants the refusal before work is dispatched or a managed resource is
    mutated, and another manager's store is such a resource. The guard is now the first
    thing that seam does.
    """

    def setUp(self):
        from tests.tools.test_single_worker import SingleWorkerCase

        self.case = SingleWorkerCase()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def holder(self):
        """A REAL other manager, holding the guard for this deployment's own root."""
        guarding = TheGuardIsHeldByOneProcess()
        guarding.place = self.case.config["workspace_storage"]
        guarding.path = self.case.control_path
        guarding.addCleanup = self.addCleanup
        return guarding.competitor(database=self.case.control_path,
                                   place=self.case.config["workspace_storage"],
                                   wait=True)

    def test_a_DUPLICATE_STARTUP_refuses_and_CONFIGURES_NOTHING(self):
        from tests.tools.test_single_worker import Engine
        from baton_v12.worker_manager import workspaces as owner

        _running, held = self.holder()
        self.assertTrue(held["held"], held)
        job, control = self.case.stores("duplicate-startup")
        engine = Engine()
        with self.assertRaises(ContractRefusal) as caught:
            self.case.operations(job, control, engine)
        self.assertEqual(caught.exception.code, "denied")
        self.assertIn("another manager is already active", caught.exception.message)
        # NOTHING WAS DISPATCHED: the engine was never asked for anything.
        self.assertEqual(engine.vectors, [])
        # AND NOTHING WAS WRITTEN: no configuration, in the projection or the journal.
        self.assertIsNone(owner._configured_storage(control, physical=False),
                          "a refused duplicate wrote its configuration anyway")
        self.assertIsNone(owner._committed_workspace_storage(control,
                                                            physical=False))

    def test_AND_THE_SAME_STARTUP_SUCCEEDS_once_the_holder_is_gone(self):
        """The control, so the refusal above is the guard and not a broken fixture."""
        from tests.tools.test_single_worker import Engine

        running, held = self.holder()
        self.assertTrue(held["held"], held)
        running.stdin.write("go\n")
        running.stdin.flush()
        self.assertEqual(running.wait(timeout=10), 0)
        job, control = self.case.stores("after-the-holder")
        operations = self.case.operations(job, control, Engine())
        self.addCleanup(operations.close)


if __name__ == "__main__":
    unittest.main()
