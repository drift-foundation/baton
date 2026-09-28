"""W285463 — the shared token-bound maintenance facility, driven end to end.

WHAT THESE CASES ARE ABLE TO PROVE, and it is the reason the engine double runs
the REAL program: the "controlled engine boundary" here is a recording port that
executes `MAINTENANCE_PROGRAM` in a subprocess against the actual mounted
directory, exactly as `test_custody.TheAnswerContractMatchesTheProgram` runs the
custodian. So `established` is a directory that exists on disk afterwards
because the program created it -- not a fixture asserting its own return value.

NO LIVE ENGINE AND NO DAEMON. Every `ps`, `create`, `start`, `wait`, `logs`,
`stop`, `rm` and `inspect` is answered by the double below, deterministically,
including this engine's own absence sentence.
"""

import json
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.contracts.errors import name_value
from baton_v12.worker_manager import custody, maintenance, oci, tokens, workspaces

from . import input_roots

IMAGE = "sha256:" + "c" * 64


class Engine:
    """A recording engine that CREATES INERT, STARTS ONCE, and can be lost.

    One container at a time, named by the manager's derivation. What `start`
    does is run the manager's own program against the bind source the create
    vector named, which is what makes the effect real.
    """

    def __init__(self, case, *, creates=0, starts=0, waits=0, logs=0,
                 inspect_after_removal=True, document=None):
        self.case = case
        self.seen = []
        self.transactions = []
        self.existence = []
        self.created = None
        self.removed = False
        self.ran = 0
        self.stdout = ""
        self.listing = []
        self.creates = creates
        self.starts = starts
        self.waits = waits
        self.logs = logs
        self.inspect_after_removal = inspect_after_removal
        self.document = document
        self.at_start = None
        self.at_create = None

    # -- the port ---------------------------------------------------------

    def __call__(self, argv, *, seconds=None):
        self.seen.append((list(argv), seconds))
        # DB-2, MEASURED RATHER THAN ASSERTED IN PROSE: no engine call may be
        # made while this manager holds a write lock.
        self.transactions.append(self.case.store._connection.in_transaction)
        verb = argv[1]
        if verb == "ps":
            return self.answer(0, "".join(json.dumps(one) + "\n"
                                          for one in self.listing))
        if verb == "create":
            return self.creating(argv)
        if verb == "start":
            return self.starting(argv)
        if verb == "wait":
            return self.answer(self.waits, "0\n")
        if verb == "logs":
            return self.answer(self.logs, self.stdout)
        if verb == "stop":
            return self.answer(0, "")
        if verb == "rm":
            self.removed = True
            return self.answer(0, "")
        if verb == "inspect":
            return self.inspecting(argv[-1])
        raise AssertionError(f"the facility asked this engine for {verb!r}")

    def answer(self, status, stdout, stderr=""):
        return {"status": status, "stdout": stdout, "stderr": stderr}

    # -- the acts ---------------------------------------------------------

    def creating(self, argv):
        if self.creates:
            return self.answer(self.creates, "",
                               "Error response from daemon: no space")
        self.created = "runtime-" + str(len(self.seen))
        self.argv = list(argv)
        self.at_create = self.case.recorded()
        self.existed_at_create = os.path.exists(self.case.result)
        self.case.witnessed(self)
        return self.answer(0, self.created + "\n")

    def starting(self, argv):
        if self.starts:
            return self.answer(self.starts, "",
                               "Error response from daemon: lost the reply")
        self.at_start = self.case.recorded()
        self.ran += 1
        self.stdout = self.case.executed(self.argv, document=self.document)
        self.existence.append(os.path.isdir(self.case.result))
        return self.answer(0, "")

    def inspecting(self, runtime_id):
        if self.removed and self.inspect_after_removal:
            return self.answer(
                1, "",
                f"Error response from daemon: No such container: {runtime_id}")
        return self.answer(0, json.dumps(
            {"Id": runtime_id, "Name": "/" + self.case.name(),
             "Image": IMAGE, "State": {"Running": not self.removed}}))


class MaintenanceCase(unittest.TestCase):
    """One allocated attempt whose RESULT ROOT IS MISSING.

    Removing it is what gives the preparation something real to establish: the
    host allocator creates it today, and this Work's whole point is that the
    writer moves into the governed execution. The removal is the fixture's, so
    nothing here depends on a product change the next child owns.
    """

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-maintenance-")
        self.addCleanup(root.cleanup)
        self.root = root.name
        self.instant = "2026-09-27T00:00:00.000Z"
        self.store = self.opened()
        self.group = input_roots.configured_group(self.store)
        self.storage = os.path.join(self.root, "storage")
        os.makedirs(self.storage, exist_ok=True)
        workspaces.configure_workspace_storage(self.store, self.storage)
        workspaces.assignment_workspace(self.group, self.storage, "attempt-1")
        self.home = os.path.join(self.storage, "attempt-1")
        self.workspace = os.path.join(self.home, "workspace")
        self.result = os.path.join(self.workspace, "result-attempt-1")
        os.rmdir(self.result)

    def opened(self):
        from baton_v12.worker_manager import ControlStore
        store = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="maintenance-1", clock=lambda: self.instant)
        self.addCleanup(store.close)
        return store

    # -- what the double needs from the product ---------------------------

    def name(self, operation=maintenance.ESTABLISH_RESULT_ROOT,
             which="workspace"):
        """The container name, DERIVED as the module derives it."""
        return maintenance._maintenance_identity(
            self.storage, "attempt-1", which, operation)

    def domain(self):
        held = os.lstat(self.workspace)
        return tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")

    def recorded(self, kinds=("acquired", "launch", "bound", "activating",
                              "activation-settled", "returned")):
        """Which journal facts exist RIGHT NOW, by short kind name."""
        found = []
        for short in kinds:
            kind = "resource-token." + short
            identity = getattr(tokens, "_" + short.replace("-", "_") + "_id")
            if tokens._document(self.store, identity(self.domain(), 1), kind):
                found.append(short)
        return tuple(found)

    def another(self, name):
        """One more allocated attempt with NO result root, for a subTest case.

        Each case needs its own domain: an unreturned generation excludes the
        next acquisition over the same resource -- the facility working -- so a
        loop sharing one attempt would measure that exclusion instead of the rule
        it means to drive.
        """
        workspaces.assignment_workspace(self.group, self.storage, name)
        os.rmdir(os.path.join(self.storage, name, "workspace",
                              f"result-{name}"))
        return name

    def domain_of(self, assignment_id):
        held = os.lstat(os.path.join(self.storage, assignment_id, "workspace"))
        return tokens.domain_of("workspace", f"{held.st_dev}:{held.st_ino}")

    def reopened(self):
        """A FRESH store handle on the same journal, holding no answer object."""
        from baton_v12.worker_manager import ControlStore
        store = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="maintenance-2", clock=lambda: self.instant)
        self.addCleanup(store.close)
        return store

    def identity(self):
        """The execution identity the create vector DECLARES, as (uid, gid).

        Read through the product's own minting rather than composed here, so a
        case that names it cannot drift from what `--user` carries.
        """
        from baton_v12.worker_manager import workspaces as w
        minted = w.identity_for(w.WorkspaceGroup(self.group.gid, w._MINT))
        return (minted.uid, minted.gid)

    def witnessed(self, engine):
        """Hook for a case that wants to act at the create boundary."""

    def submitted(self, argv):
        """The submission this act really committed: the token's own owner.

        Read out of the argv the product composed, which is where it is -- a
        fixture that wrote its own would be answering for a generation this act
        never had, and every case about a document's VALUES would be stopped by
        the submission rule before reaching them.
        """
        return argv[-2]

    def executed(self, argv, document=None):
        """Run the manager's own program against the mount it composed.

        The bind source and the operands are read out of the argv the product
        composed, so nothing here can run the program over a directory the
        facility did not select.
        """
        if document is not None:
            if document.get("submission") is None:
                document = dict(document, submission=self.submitted(argv))
            return json.dumps(document) + "\n"
        source = next(one for one in argv
                      if one.startswith("type=bind,")).split("source=", 1)[1]
        source = source.split(",", 1)[0]
        program = argv[argv.index("-c") + 1].replace(
            'ROOT = "/maintenance"', f"ROOT = {source!r}", 1)
        operands = argv[argv.index("-c") + 2:]
        done = subprocess.run([sys.executable, "-c", program, *operands],
                              capture_output=True, timeout=120)
        return done.stdout.decode("utf-8", "replace")

    # -- the act ----------------------------------------------------------

    def prepared(self, engine=None, **overrides):
        self.engine = engine or Engine(self)
        operands = {"image_digest": IMAGE, "store": self.store,
                    "assignment_id": "attempt-1",
                    "operation": maintenance.ESTABLISH_RESULT_ROOT}
        operands.update(overrides)
        return maintenance.prepare("docker", self.engine, **operands)

    def vector(self, verb="create"):
        return next(argv for argv, _ in self.engine.seen if argv[1] == verb)

    def unresolved(self):
        return tokens.unresolved(self.store, self.domain())


class ThePreparationEffectHappensInsideTheExecution(MaintenanceCase):
    """The first thing this facility has to be: not an unused token wrapper."""

    def test_the_result_root_is_established_by_the_program_and_nothing_else(self):
        self.assertFalse(os.path.exists(self.result))
        answered = self.prepared()
        self.assertTrue(answered.ok, answered.diagnostic)
        self.assertTrue(os.path.isdir(self.result))
        self.assertTrue(answered.answer["established"])
        self.assertEqual(answered.answer["place"], "result-attempt-1")
        # THE MODE IS THE WRITABLE ROOT'S OWN, established rather than
        # requested: `0o2770` is what `adopt_workspace_group` puts on the
        # workspace, setgid included.
        self.assertEqual(oct(stat.S_IMODE(os.lstat(self.result).st_mode)),
                         oct(maintenance.PREPARED_MODE))
        self.assertEqual(answered.answer["mode"],
                         oct(maintenance.PREPARED_MODE))

    def test_it_did_not_exist_until_the_admitted_activation_ran(self):
        """WHEN the effect happened, not merely that it happened.

        The double records the directory's existence at the create boundary and
        again inside the start, so a host that had quietly created it first
        would be visible here.
        """
        self.prepared()
        # NOT THERE when the inert container was composed and created...
        self.assertFalse(self.engine.existed_at_create)
        # ...and there by the time the admitted activation returned, which is
        # the only call between the two observations.
        self.assertEqual(self.engine.existence, [True])
        self.assertEqual(self.engine.ran, 1)
        self.assertTrue(os.path.isdir(self.result))

    def test_the_host_creates_nothing_at_all_on_this_path(self):
        """No `mkdir` and no `chmod` in the manager's own process.

        Measured by taking both away for the duration of the act. The program
        runs in a subprocess, so the effect still happens; a host writer would
        fail loudly.
        """
        with mock.patch("os.mkdir", side_effect=AssertionError("host mkdir")), \
                mock.patch("os.chmod",
                           side_effect=AssertionError("host chmod")):
            # THE INSTRUMENT IS LIVE, asserted rather than assumed: a passing
            # case has to be able to fail. Without this the test would also pass
            # if the patches were reaching nothing at all.
            with self.assertRaises(AssertionError):
                os.mkdir(os.path.join(self.root, "control-case"))
            with self.assertRaises(AssertionError):
                os.chmod(self.workspace, 0o2770)
            answered = self.prepared()
        self.assertTrue(answered.ok, answered.diagnostic)
        self.assertTrue(os.path.isdir(self.result))

    def test_a_second_preparation_finds_it_established_rather_than_replacing_it(self):
        """The program's own idempotence, at the program.

        Run directly, because a second `prepare` is a second act on a returned
        generation and that refusal is its own case below.
        """
        os.mkdir(self.result)
        document = json.loads(self.executed(
            ["--mount", f"type=bind,source={self.workspace},target=x",
             "-c", maintenance.MAINTENANCE_PROGRAM,
             maintenance.ESTABLISH_RESULT_ROOT, "submission-1",
             "result-attempt-1"]).splitlines()[-1])
        self.assertFalse(document["established"])
        self.assertEqual(document["maintenance"],
                         maintenance.ESTABLISH_RESULT_ROOT)


class TheTokenIsTheTasksOwnAndNotASecondJournal(MaintenanceCase):
    """The G1 conflict identity, retained across maintenance and task."""

    def test_the_domain_is_the_one_a_task_start_resolves(self):
        held = os.lstat(self.workspace)
        attempt = {"runtime_attempt_id": "attempt-1",
                   "workspace_device": held.st_dev,
                   "workspace_inode": held.st_ino}
        self.prepared()
        # The identity the task's own governance answers, computed from the
        # attempt row rather than from this module.
        self.assertEqual(tokens.domain_of("workspace",
                                          tokens.workspace_identity(attempt)),
                         self.domain())
        acquired = tokens._document(self.store,
                                    tokens._acquired_id(self.domain(), 1),
                                    tokens.ACQUIRED_KIND)
        self.assertEqual(acquired["domain"], self.domain())

    def test_a_task_start_cannot_acquire_while_the_preparation_holds_it(self):
        """Measured at the moment the preparation is mid-flight."""
        case = self
        refusals = []

        class Watching(Engine):
            def starting(self, argv):
                try:
                    tokens.acquire(case.store, case.domain(),
                                   operation="start:attempt-1",
                                   execution="attempt-1", attempt="attempt-1")
                except ContractRefusal as refused:
                    refusals.append(str(refused))
                return super().starting(argv)

        answered = self.prepared(Watching(self))
        self.assertTrue(answered.ok, answered.diagnostic)
        self.assertEqual(len(refusals), 1)
        self.assertIn("is owned by token generation 1", refusals[0])

    def test_the_execution_identity_is_the_maintenance_act_and_not_the_attempt(self):
        self.prepared()
        acquired = tokens._document(self.store,
                                    tokens._acquired_id(self.domain(), 1),
                                    tokens.ACQUIRED_KIND)
        self.assertEqual(acquired["execution"],
                         "maintenance-execution:attempt-1:workspace")
        self.assertNotEqual(acquired["execution"], "attempt-1")
        # THE ATTEMPT TRAVELS AS THE ASSOCIATION, which is what `acquire`
        # documents it as -- and no task generation exists for the attempt's own
        # execution identity.
        self.assertEqual(acquired["attempt"], "attempt-1")
        self.assertIsNone(tokens.generation_of(self.store, self.domain(),
                                               execution="attempt-1",
                                               operation="start:attempt-1"))

    def test_the_pre_allocation_identity_names_the_object_inside_the_domain(self):
        held = os.lstat(self.workspace)
        governed, pre = maintenance._resource_identity(self.workspace,
                                                      "result-attempt-1")
        self.assertEqual(governed, f"{held.st_dev}:{held.st_ino}")
        self.assertEqual(pre, f"{held.st_dev}:{held.st_ino}/result-attempt-1")
        # STABLE BEFORE THE OBJECT EXISTS, which is the property it is for.
        self.assertFalse(os.path.exists(self.result))
        self.assertEqual(maintenance._resource_identity(self.workspace,
                                                       "result-attempt-1")[1],
                         pre)


class TheLaunchIsTwoActsAndTheJournalDecidesBetweenThem(MaintenanceCase):

    def test_the_container_is_created_inert_then_bound_and_admitted_then_started(self):
        answered = self.prepared()
        self.assertTrue(answered.ok, answered.diagnostic)
        # AT THE CREATE: reserved and journalled, nothing bound.
        self.assertEqual(self.engine.at_create, ("acquired", "launch"))
        # AT THE START: bound AND admitted, and not yet settled.
        self.assertEqual(self.engine.at_start,
                         ("acquired", "launch", "bound", "activating"))
        self.assertEqual([argv[1] for argv, _ in self.engine.seen],
                         ["ps", "create", "start", "wait", "logs", "stop",
                          "rm", "inspect"])

    def test_the_created_vector_is_the_deferred_activation(self):
        self.prepared()
        argv = self.vector("create")
        self.assertEqual(tuple(argv[1:1 + len(
            oci.ACTIVATIONS[oci.ACTIVATE_DEFERRED])]),
                         oci.ACTIVATIONS[oci.ACTIVATE_DEFERRED])
        self.assertNotIn("--detach", argv)
        self.assertNotIn("--rm", argv)
        self.assertEqual(self.vector("start"),
                         ["docker", "start", self.engine.created])

    def test_the_token_is_returned_only_after_the_absence_is_proved(self):
        self.prepared()
        order = [argv[1] for argv, _ in self.engine.seen]
        self.assertLess(order.index("rm"), order.index("inspect"))
        current = tokens.token_of(self.store, self.domain(), 1)
        self.assertTrue(current["returned"])
        self.assertEqual(self.unresolved(), [])

    def test_no_engine_call_is_made_while_a_write_lock_is_held(self):
        self.prepared()
        self.assertEqual(set(self.engine.transactions), {False})


class TheMountIsTheDerivedRootAndNeverTheHome(MaintenanceCase):

    def test_exactly_one_mount_is_composed_and_it_is_the_workspace(self):
        self.prepared()
        argv = self.vector("create")
        mounts = [one for one in argv if one.startswith("type=bind,")]
        self.assertEqual(len(mounts), 1)
        self.assertEqual(
            mounts[0],
            f"type=bind,source={self.workspace},"
            f"target={maintenance.MAINTENANCE_ROOT},readonly=false")
        self.assertEqual(argv.count("--mount"), 1)

    def test_the_home_and_its_credential_siblings_are_not_mounted(self):
        """The sibling-authorization boundary this plan required pinned.

        A writable mount of the HOME would put `credentials`,
        `credential-state` and `custody` inside the maintenance execution while
        it prepared something under `workspace`.
        """
        self.prepared()
        argv = self.vector("create")
        for sibling in ("credentials", "credential-state", "custody",
                        "inputs"):
            self.assertNotIn(os.path.join(self.home, sibling), argv)
        # THE EXACT SOURCE, compared as a value rather than searched for as
        # text: the home is a PREFIX of the workspace, so a substring search
        # would fail on the correct composition. My first form did exactly that.
        mount = next(one for one in argv if one.startswith("type=bind,"))
        source = dict(part.split("=", 1) for part in mount.split(","))["source"]
        self.assertEqual(source, self.workspace)
        self.assertNotEqual(source, self.home)
        self.assertNotIn(os.path.join(self.root, "control.sqlite3"),
                         " ".join(argv))

    def test_the_restrictions_are_the_custodians_own(self):
        self.prepared()
        argv = self.vector("create")
        # PAIRED IN ORDER, not looked up by `index`: `--security-opt` appears
        # twice, so the first occurrence answered for both and the comparison
        # was against the wrong value. Measured, and it was my own bug.
        composed = []
        for flag, value in custody._CUSTODY_RESTRICTIONS:
            where = argv.index(flag, len(composed))
            composed = argv[:where + 1]
            if value is not None and flag != "--user":
                self.assertEqual(argv[where + 1], value)
                composed = argv[:where + 2]
        self.assertIn("--read-only", argv)
        self.assertEqual(argv[argv.index("--network") + 1], "none")
        self.assertEqual(argv[argv.index("--cap-drop") + 1], "ALL")

    def test_the_place_is_a_name_and_no_operand_carries_a_path(self):
        self.prepared()
        argv = self.vector("create")
        self.assertEqual(argv[-1], "result-attempt-1")
        self.assertEqual(argv[-2], tokens._document(
            self.store, tokens._acquired_id(self.domain(), 1),
            tokens.ACQUIRED_KIND)["owner"])
        self.assertEqual(argv[-3], maintenance.ESTABLISH_RESULT_ROOT)
        self.assertEqual(argv[argv.index("--entrypoint") + 1], "python3")

    def test_a_compound_name_is_refused_by_the_program_itself(self):
        """The containment rule lives on the host; the program refuses too.

        Run directly against a real directory, with the one operand a program
        could use to leave its root.
        """
        outside = os.path.join(self.root, "escaped")
        for place in ("../escaped", "nested/result", "/absolute", "..", ""):
            with self.subTest(place=place):
                printed = self.executed(
                    ["--mount", f"type=bind,source={self.workspace},target=x",
                     "-c", maintenance.MAINTENANCE_PROGRAM,
                     maintenance.ESTABLISH_RESULT_ROOT, "submission-1", place])
                document = json.loads(printed.splitlines()[-1])
                self.assertEqual(document["maintenance"], "refused")
                self.assertIn("is not a name this program establishes",
                              document["why"])
        self.assertFalse(os.path.exists(outside))


class TheHostSettlesOnEvidenceAndHoldsEverythingElse(MaintenanceCase):

    def test_a_create_the_engine_refused_exposes_nothing_and_holds_the_launch(self):
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(Engine(self, creates=1))
        self.assertIn("nothing was started", str(refused.exception))
        self.assertFalse(os.path.exists(self.result))
        held = self.unresolved()
        self.assertEqual([one["cut"] for one in held], ["launched-unbound"])
        self.assertEqual(held[0]["generation"], 1)

    def test_a_container_this_manager_cannot_name_exactly_is_never_bound(self):
        """An engine answer that is not ONE identity.

        A create this manager cannot correlate is the state the two-act launch
        exists to prevent: there would be nothing exact to bind, admit or later
        prove absent.
        """
        case = self

        class Ambiguous(Engine):
            def creating(self, argv):
                return self.answer(0, "runtime-a\nruntime-b\n")

        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(Ambiguous(self))
        self.assertIn("2 identities for one maintenance create",
                      str(refused.exception))
        self.assertEqual([one["cut"] for one in self.unresolved()],
                         ["launched-unbound"])
        self.assertIsNone(tokens.token_of(self.store, self.domain(),
                                          1)["container"])
        self.assertFalse(os.path.exists(self.result))

    def test_an_activation_the_engine_did_not_answer_is_left_in_flight(self):
        answered = self.prepared(Engine(self, starts=1))
        self.assertFalse(answered.ok)
        self.assertTrue(answered.held)
        self.assertIn("UNRESOLVED", answered.diagnostic)
        self.assertIn("unsettled on purpose", answered.diagnostic)
        held = self.unresolved()
        self.assertEqual([one["cut"] for one in held], ["admitted-unsettled"])
        self.assertEqual(held[0]["container"], answered.container)
        self.assertFalse(os.path.exists(self.result))

    def test_an_unreadable_account_is_not_an_outcome_and_the_token_stays_held(self):
        answered = self.prepared(Engine(self, logs=1))
        self.assertFalse(answered.ok)
        self.assertTrue(answered.held)
        self.assertIsNone(answered.answer)
        self.assertIn("printed no document", answered.unaccounted)
        self.assertFalse(tokens.token_of(self.store, self.domain(),
                                         1)["returned"])
        # THE CONTAINER IS STILL ENDED. Leaving one holding the mount is the
        # worse outcome; what is withheld is the RETURN.
        self.assertTrue(self.engine.removed)

    def test_an_account_for_another_submission_accounts_for_nothing(self):
        answered = self.prepared(Engine(self, document={
            "maintenance": maintenance.ESTABLISH_RESULT_ROOT,
            "version": maintenance.MAINTENANCE_VERSION,
            "submission": "0" * 64, "place": "result-attempt-1",
            "established": True, "mode": oct(maintenance.PREPARED_MODE),
            "running_as": list(self.identity())}))
        self.assertFalse(answered.ok)
        self.assertTrue(answered.held)
        self.assertIn("is not an account of this one", answered.diagnostic)
        self.assertFalse(tokens.token_of(self.store, self.domain(),
                                         1)["returned"])

    def test_a_document_with_an_unexpected_member_accounts_for_nothing(self):
        """A document from a program this module does not ship.

        One case per store rather than a subTest loop: an unreturned generation
        excludes the next acquisition over the same domain, which is the
        facility working -- so two documents need two attempts, and reusing one
        would measure the exclusion instead of the validator.
        """
        answered = self.prepared(Engine(self, document={
            "maintenance": maintenance.ESTABLISH_RESULT_ROOT,
            "version": maintenance.MAINTENANCE_VERSION,
            "submission": "x", "place": "p", "established": True,
            "mode": "0o2770", "running_as": [1, 2], "extra": 1}))
        self.assertFalse(answered.ok)
        self.assertTrue(answered.held)
        self.assertIn("unexpected extra", answered.unaccounted)
        self.assertFalse(tokens.token_of(self.store, self.domain(),
                                         1)["returned"])

    def test_a_document_for_another_verb_accounts_for_nothing(self):
        answered = self.prepared(Engine(self, document={
            "maintenance": "inspect", "submission": "x"}))
        self.assertFalse(answered.ok)
        self.assertTrue(answered.held)
        self.assertIn("not an account of this one", answered.unaccounted)
        self.assertFalse(tokens.token_of(self.store, self.domain(),
                                         1)["returned"])

    def test_a_report_without_a_proved_absence_never_returns_the_token(self):
        """The engine says the container is still there after the removal.

        `stopped` is what an order returns; absence is what this requires, and
        the two are different facts.
        """
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(Engine(self, inspect_after_removal=False))
        self.assertIn("could not prove the helper", str(refused.exception))
        # THE EFFECT HAPPENED and the token is still outstanding -- which is the
        # honest state, and the one `unresolved` reports.
        self.assertTrue(os.path.isdir(self.result))
        self.assertFalse(tokens.token_of(self.store, self.domain(),
                                         1)["returned"])

    def test_an_expired_grant_holds_the_resource_and_admits_no_replacement(self):
        case = self

        class Slow(Engine):
            def starting(self, argv):
                answered = super().starting(argv)
                # The grant elapses between the effect and the settlement.
                case.instant = "2026-09-27T01:00:00.000Z"
                return answered

        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(Slow(self))
        self.assertIn("expired", str(refused.exception).lower())
        current = tokens.token_of(self.store, self.domain(), 1)
        self.assertTrue(current["expired"])
        self.assertFalse(current["returned"])
        with self.assertRaises(ContractRefusal) as second:
            tokens.acquire(self.store, self.domain(), operation="start:later",
                           execution="attempt-1")
        self.assertIn("revoked rather than replaced", str(second.exception))

    def test_an_unreconciled_custody_hold_stops_the_preparation_before_anything(self):
        custody._record_hold(self.store, "attempt-1", "workspace", "normalize",
                             IMAGE, "baton-custody-" + "a" * 32)
        engine = Engine(self)
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn("unreconciled uncertainty episode",
                      str(refused.exception))
        self.assertEqual(engine.seen, [])
        self.assertIsNone(tokens._document(
            self.store, tokens._acquired_id(self.domain(), 1),
            tokens.ACQUIRED_KIND))

    def test_a_stranded_container_whose_absence_is_unproved_stops_the_act(self):
        """This act's OWN image, so it is this manager's to end -- and the
        removal is ordered and then cannot be proved. Nothing is acquired."""
        engine = Engine(self, inspect_after_removal=False)
        engine.listing = [{"Names": self.name(), "ID": "runtime-stranded"}]
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn("could not prove the helper", str(refused.exception))
        self.assertIsNone(tokens._document(
            self.store, tokens._acquired_id(self.domain(), 1),
            tokens.ACQUIRED_KIND))
        self.assertNotIn("create", [argv[1] for argv, _ in engine.seen])

    def test_a_container_running_another_image_is_not_this_managers_to_remove(self):
        """A derived name is not authority over somebody else's container."""
        case = self

        class Foreign(Engine):
            def inspecting(self, runtime_id):
                return self.answer(0, json.dumps(
                    {"Id": runtime_id, "Name": "/" + case.name(),
                     "Image": "sha256:" + "d" * 64,
                     "State": {"Running": True}}))

        engine = Foreign(self)
        engine.listing = [{"Names": self.name(), "ID": "runtime-foreign"}]
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn("an image this act did not compose",
                      str(refused.exception))
        # NOT STOPPED, NOT REMOVED, NOT ACQUIRED OVER.
        self.assertEqual([argv[1] for argv, _ in engine.seen],
                         ["ps", "inspect"])
        self.assertIsNone(tokens._document(
            self.store, tokens._acquired_id(self.domain(), 1),
            tokens.ACQUIRED_KIND))


class ARepeatedPreparationDecidesAtTheJournalBeforeTheEngine(MaintenanceCase):
    """MY OWN DEFECT, MEASURED AND FIXED, and the record is the reason these
    cases exist rather than a claim that they always held.

    `tokens.acquire` replays a RETURNED generation, so a second `prepare` used
    to reach the engine, CREATE a container and only then refuse at the
    admission -- leaving a container nothing had reclaimed. The journal decides
    first now, and each disposition below is the measured one.
    """

    def test_a_completed_preparation_is_not_repeated_and_creates_nothing(self):
        first = self.prepared()
        self.assertTrue(first.ok, first.diagnostic)
        again = Engine(self)
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(again)
        self.assertIn("has been RETURNED", str(refused.exception))
        self.assertIn("not repeated", str(refused.exception))
        # NOTHING WAS ASKED OF THE ENGINE AT ALL, which is the half the old
        # shape got wrong: it had already created a container by this point.
        self.assertEqual(again.seen, [])
        self.assertEqual(self.unresolved(), [])

    def test_a_partially_launched_preparation_is_recovery_and_not_a_relaunch(self):
        """A generation with a container bound and nothing admitted.

        Composed through the shared token API under this module's own identities,
        which is the state a manager that died between the create and the start
        leaves behind.
        """
        token = tokens.acquire(
            self.store, self.domain(),
            operation=maintenance._operation_identity(
                maintenance.ESTABLISH_RESULT_ROOT, "attempt-1", "workspace"),
            execution=maintenance._execution_identity("attempt-1", "workspace"),
            attempt="attempt-1", seconds=maintenance.MAINTENANCE_SECONDS)
        tokens.journal_launch(self.store, token, token["operation"])
        tokens.bind_container(self.store, token, "runtime-interrupted",
                              launch=token["operation"])
        engine = Engine(self)
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn("runtime-interrupted", str(refused.exception))
        self.assertIn("not admitted", str(refused.exception))
        self.assertIn("reconciled rather than launched a second time",
                      str(refused.exception))
        self.assertEqual(engine.seen, [])
        # AND THE HOLD IS THE ACTIONABLE ONE G1 ALREADY REPORTS.
        self.assertEqual([one["cut"] for one in self.unresolved()],
                         ["bound-not-admitted"])

    def test_a_create_whose_reply_was_lost_is_resumed_with_one_effect(self):
        """`launched-unbound`: acquired and journalled, nothing bound.

        This one PROCEEDS, and it is the only replay disposition that does: the
        container that may exist answers to the derived name, so it is
        reconciled -- its stdout is unrecoverable, which is `custody`'s own
        reason for ending rather than adopting -- and the preparation is
        idempotent, so redoing it is sound.
        """
        token = tokens.acquire(
            self.store, self.domain(),
            operation=maintenance._operation_identity(
                maintenance.ESTABLISH_RESULT_ROOT, "attempt-1", "workspace"),
            execution=maintenance._execution_identity("attempt-1", "workspace"),
            attempt="attempt-1", seconds=maintenance.MAINTENANCE_SECONDS)
        tokens.journal_launch(self.store, token, token["operation"])
        self.assertEqual([one["cut"] for one in self.unresolved()],
                         ["launched-unbound"])
        engine = Engine(self)
        engine.listing = [{"Names": self.name(), "ID": "runtime-lost"}]
        answered = self.prepared(engine)
        self.assertTrue(answered.ok, answered.diagnostic)
        # THE SAME GENERATION, not a second one over the same resource.
        self.assertEqual(answered.generation, token["generation"])
        self.assertTrue(os.path.isdir(self.result))
        # ONE EFFECT IN TOTAL: the stranded container was ended, and the program
        # ran exactly once, in the container this act created and admitted.
        self.assertEqual(engine.ran, 1)
        self.assertEqual(self.unresolved(), [])


class TheVocabularyAndTheSchemaAreOneContract(MaintenanceCase):

    def test_every_verb_this_build_owns_has_a_result_shape(self):
        self.assertEqual(sorted(maintenance._PREPARED),
                         sorted(maintenance.PREPARATIONS))

    def test_a_verb_outside_the_vocabulary_reaches_no_engine(self):
        engine = Engine(self)
        for wrong in ("normalize", "", "establish", None, 5):
            with self.subTest(operation=wrong):
                with self.assertRaises(ContractRefusal):
                    self.prepared(engine, operation=wrong)
        self.assertEqual(engine.seen, [])

    def test_the_real_programs_document_is_the_one_this_module_accounts_for(self):
        """The two tables bound together at the seam that matters.

        A member added to the program without adding it to `_PREPARED` fails
        here as `unexpected`, and a removed one as `missing`.
        """
        printed = self.executed(
            ["--mount", f"type=bind,source={self.workspace},target=x",
             "-c", maintenance.MAINTENANCE_PROGRAM,
             maintenance.ESTABLISH_RESULT_ROOT, "submission-1",
             "result-attempt-1"])
        document = json.loads(printed.splitlines()[-1])
        accounted, why = maintenance._accountable(
            maintenance.ESTABLISH_RESULT_ROOT, document)
        self.assertIsNone(why)
        self.assertEqual(accounted["submission"], "submission-1")

    def test_the_timers_are_reconciled_with_the_grant_rather_than_confused(self):
        self.assertEqual(maintenance.MAINTENANCE_SECONDS,
                         tokens.LIFETIME_SECONDS)
        self.assertLess(maintenance.PREPARE_SECONDS,
                        maintenance.MAINTENANCE_ACT_SECONDS)
        self.assertLess(maintenance.MAINTENANCE_ACT_SECONDS
                        + maintenance.RECLAIM_STOP_SECONDS,
                        maintenance.MAINTENANCE_SECONDS)
        # THE DECLARED STOP GRACE IS THE ONE THIS PATH REALLY SPENDS, which review
        # 2026-09-27T13-42-58Z caught being advertised as G1's 30 seconds while
        # every reclamation here goes through `custody._reclaimed` at 5. A profile
        # that names a number the code never passes is a claim, so the constant is
        # held to custody's own and this case is what keeps them equal.
        self.assertEqual(maintenance.RECLAIM_STOP_SECONDS,
                         custody.CUSTODY_STOP_SECONDS)
        self.assertNotEqual(maintenance.RECLAIM_STOP_SECONDS,
                            tokens.STOP_GRACE_SECONDS)
        self.assertFalse(hasattr(maintenance, "MAINTENANCE_STOP_SECONDS"))
        self.assertEqual(maintenance.RENEWALS_TAKEN, 0)
        self.prepared()
        # AND THE BOUND REALLY CROSSES: every engine call this facility makes
        # carries one of this module's own deadlines.
        given = {seconds for argv, seconds in self.engine.seen}
        self.assertNotIn(None, given)
        self.assertTrue(given <= {maintenance.MAINTENANCE_ACT_SECONDS,
                                  custody.CUSTODY_RECLAIM_SECONDS})
        self.assertEqual(tokens._document(
            self.store, tokens._acquired_id(self.domain(), 1),
            tokens.ACQUIRED_KIND)["seconds"], maintenance.MAINTENANCE_SECONDS)

    def test_a_caller_allowance_may_only_lower_the_act_bound(self):
        self.prepared(seconds=120)
        starting = next(seconds for argv, seconds in self.engine.seen
                        if argv[1] == "start")
        self.assertEqual(starting, 120)


class TheAnswerIsNotACapability(MaintenanceCase):

    def test_it_carries_no_host_path(self):
        answered = self.prepared()
        self.assertNotIn(self.root, answered.rendered)
        self.assertNotIn(self.storage, answered.rendered)
        self.assertEqual(answered.answer["place"], "result-attempt-1")

    def test_a_caller_cannot_mint_one(self):
        """`custody.CustodyAnswer`'s rule and its measured refusal: the class
        defines no constructor, so the arguments an account would need are
        refused by `object.__init__` itself."""
        with self.assertRaises(TypeError):
            maintenance.MaintenanceAnswer(
                maintenance.ESTABLISH_RESULT_ROOT, 1, "runtime-1", 0, {})

    def test_a_holder_cannot_revise_one(self):
        answered = self.prepared()
        for act in (lambda: setattr(answered, "_returned", False),
                    lambda: delattr(answered, "_answer")):
            with self.subTest(act=act):
                with self.assertRaises(ContractRefusal):
                    act()
        self.assertTrue(answered.returned)
        with self.assertRaises(TypeError):
            answered.answer["established"] = False




class TheExclUSIONIsDecidedUnderTheWriteLockBothWays(MaintenanceCase):
    """W285463 review R1, and the confirmed defect it named.

    The first cut read `custody._standing_overlap` outside every transaction and
    then acquired a token with NO condition attached, so a custody hold that
    committed in between was invisible and the preparation wrote anyway. The
    reviewer's probe interposed exactly there and measured the effect.

    TWO PARTIES, TWO LOCKS, AND WHOEVER COMMITS FIRST WINS. The window admission
    and the acquisition each re-read the journal under `BEGIN IMMEDIATE`, and the
    custody claim now reads the maintenance window under its own -- so the
    schedules below all end with exactly one actor and no effect from the loser.
    """

    def test_a_hold_that_commits_before_the_window_refuses_before_any_engine_call(self):
        custody._record_hold(self.store, "attempt-1", "workspace", "normalize",
                             IMAGE, "baton-custody-" + "a" * 32)
        engine = Engine(self)
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn("unreconciled uncertainty episode", str(refused.exception))
        self.assertEqual(engine.seen, [])
        self.assertEqual(maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace"), [])

    def test_a_hold_that_appears_after_the_window_refuses_the_ACQUISITION_itself(self):
        """The eligibility predicate, proved load-bearing.

        Recorded through `custody._record_hold`, which is the unconditional
        recorder and does NOT consult the maintenance window -- so this drives the
        one schedule in which a hold can still appear between the window and the
        acquisition. The ordinary claim path cannot reach this state any more,
        which is the reciprocal case below; this proves the second line of
        defence rather than assuming it.
        """
        honest = custody._reconciled
        recorded = []

        def racing(*arguments, **named):
            answer = honest(*arguments, **named)
            recorded.append(custody._record_hold(
                self.store, "attempt-1", "workspace", "normalize", IMAGE,
                "baton-custody-" + "b" * 32))
            return answer

        engine = Engine(self)
        with mock.patch.object(custody, "_reconciled", racing):
            with self.assertRaises(ContractRefusal) as refused:
                self.prepared(engine)
        self.assertEqual(len(recorded), 1)
        # THE ACQUISITION'S OWN WORDS, which is what says the predicate decided it
        # rather than the window admission that ran before the hold existed.
        self.assertIn("decided inside the acquisition's own transaction",
                      str(refused.exception))
        self.assertIn("unreconciled uncertainty episode", str(refused.exception))
        # NOTHING WAS ACQUIRED AND NOTHING RAN.
        self.assertEqual(engine.ran, 0)
        self.assertEqual(tokens.outstanding(self.store, self.domain()), [])
        self.assertNotIn("create", [argv[1] for argv, _ in engine.seen])
        # AND THE WINDOW CLOSED, because this refusal authorized no effect: a
        # window left standing would freeze the root over an act that did nothing.
        self.assertEqual(maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace"), [])
        self.assertEqual(maintenance.maintenance_settlement(
            self.store, "attempt-1", "workspace")["disposition"],
            maintenance.SETTLED_REFUSED)

    def test_a_custody_claim_is_refused_while_a_maintenance_window_stands(self):
        """The reciprocal half R1 asked for, at the real claim path.

        `custody._claim_episode` knew about removals and other holds and nothing
        about a governed preparation. It reads the window by DERIVED IDENTITY --
        no `lstat` under the write lock, which is why the window and not the token
        is what it can ask about.
        """
        case = self
        refusals = []

        class Claiming(Engine):
            def starting(self, argv):
                try:
                    custody._claim_episode(
                        case.store, "attempt-1", "workspace", "normalize",
                        IMAGE, "baton-custody-" + "c" * 32)
                except ContractRefusal as refused:
                    refusals.append(str(refused))
                return super().starting(argv)

        answered = self.prepared(Claiming(self))
        self.assertTrue(answered.ok, answered.diagnostic)
        self.assertEqual(len(refusals), 1)
        self.assertIn("unsettled maintenance window 1", refusals[0])
        self.assertIn("a governed preparation may still be writing", refusals[0])
        # THE LOSER WROTE NOTHING: no episode was recorded at all.
        self.assertIsNone(custody._standing_overlap(self.store, "attempt-1",
                                                    "workspace"))
        self.assertEqual(custody.custody_holds(self.store, "attempt-1",
                                               "workspace"), [])

    def test_the_reviewer_schedule_now_refuses_both_parties_and_frees_the_root(self):
        """The reviewer's own schedule, kept as my regression.

        Their probe's FIRST assertion -- that the interposed hold commits -- is
        now unreachable, because the reciprocal half they also asked for refuses
        it. What their probe was measuring, the effect, is zero; and the window
        closes, so refusing both parties does not leave the root frozen.
        """
        honest = custody._reconciled
        outcome = []

        def racing(*arguments, **named):
            answer = honest(*arguments, **named)
            custody._claim_episode(
                self.store, "attempt-1", "workspace", "normalize", IMAGE,
                custody._custody_identity(self.storage, "attempt-1",
                                          "workspace", "normalize"))
            outcome.append("committed")
            return answer

        engine = Engine(self)
        with mock.patch.object(custody, "_reconciled", racing):
            with self.assertRaises(ContractRefusal) as refused:
                self.prepared(engine)
        self.assertEqual(outcome, [])
        self.assertIn("unsettled maintenance window 1", str(refused.exception))
        self.assertEqual(engine.ran, 0)
        self.assertEqual(tokens.outstanding(self.store, self.domain()), [])
        self.assertIsNone(custody._standing_overlap(self.store, "attempt-1",
                                                    "workspace"))
        self.assertEqual(maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace"), [])

    def test_a_governed_live_container_is_not_ended_because_a_name_matches(self):
        """R1's last paragraph: a derived name is not authority to kill.

        The candidate answers to this act's derived name AND is bound to an
        outstanding generation of this very domain -- an actor whose token still
        permits it to write. Ending it would be the one thing a reclamation may
        never do.
        """
        token = tokens.acquire(self.store, self.domain(),
                               operation="maintenance-establish-result-root:"
                                         "attempt-1:workspace:other",
                               execution="maintenance-execution:other",
                               attempt="attempt-1")
        tokens.journal_launch(self.store, token, token["operation"])
        tokens.bind_container(self.store, token, "runtime-live",
                              launch=token["operation"])
        engine = Engine(self)
        engine.listing = [{"Names": self.name(), "ID": "runtime-live"}]
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn("not authority to end a live governed actor",
                      str(refused.exception))
        # NOT STOPPED AND NOT REMOVED, and the live actor's own generation is
        # untouched: still outstanding, still bound to its container.
        self.assertEqual([argv[1] for argv, _ in engine.seen],
                         ["ps", "inspect"])
        live = tokens.token_of(self.store, self.domain(), 1)
        self.assertEqual(live["container"], "runtime-live")
        self.assertFalse(live["returned"])
        self.assertEqual([one["generation"]
                          for one in tokens.outstanding(self.store,
                                                        self.domain())], [1])


class ALateCreatedRuntimeIsEndedOrRecordedAsUnknown(MaintenanceCase):
    """W285463 review R2, and the gap it named.

    The reviewer advanced the grant past expiry between the create and the bind.
    `bind_container` refused -- correctly, because a late binding is what TOK-4
    forbids -- and the act then exited with the inert container still there, no
    stop, no removal and nothing recording its identity. The no-late-bind rule is
    unchanged; what is added is that the exact runtime is reconciled outside every
    transaction, and that an unproved absence is written down rather than lost.
    """

    def expiring(self, **named):
        case = self

        class Delayed(Engine):
            def creating(self, argv):
                answer = super().creating(argv)
                case.instant = "2026-09-27T00:16:00.000Z"
                return answer

        return Delayed(self, **named)

    def test_the_exact_container_is_ended_and_proved_absent(self):
        engine = self.expiring()
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn("expired", str(refused.exception).lower())
        self.assertIsNotNone(engine.created)
        self.assertEqual(engine.ran, 0)
        # STOP, THEN FORCE-REMOVE, THEN THE ENGINE'S OWN ABSENCE SENTENCE.
        self.assertEqual([argv[1] for argv, _ in engine.seen][-3:],
                         ["stop", "rm", "inspect"])
        orphan = maintenance.maintenance_orphan(self.store, "attempt-1",
                                                "workspace", 1)
        self.assertEqual(orphan["container"], engine.created)
        self.assertTrue(orphan["absence_proved"])
        self.assertIn("expired", orphan["why"].lower())
        # AND THE WINDOW CLOSES, because nothing was admitted and the runtime is
        # provably gone, so no effect can still arrive.
        self.assertEqual(maintenance.maintenance_settlement(
            self.store, "attempt-1", "workspace")["disposition"],
            maintenance.SETTLED_ORPHANED)
        self.assertEqual(maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace"), [])

    def test_an_unprovable_absence_is_recorded_and_the_window_stays_open(self):
        engine = self.expiring(inspect_after_removal=False)
        with self.assertRaises(ContractRefusal):
            self.prepared(engine)
        orphan = maintenance.maintenance_orphan(self.store, "attempt-1",
                                                "workspace", 1)
        self.assertEqual(orphan["container"], engine.created)
        self.assertFalse(orphan["absence_proved"])
        self.assertIn("could not prove the helper", orphan["observed"])
        # THE HONEST HOLD: no settlement, the window stands, and the next act and
        # a custody claim are both excluded until an operator reconciles it.
        self.assertIsNone(maintenance.maintenance_settlement(
            self.store, "attempt-1", "workspace"))
        self.assertEqual([one for one, _ in maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace")], [1])
        with self.assertRaises(ContractRefusal) as second:
            custody._claim_episode(self.store, "attempt-1", "workspace",
                                   "normalize", IMAGE,
                                   "baton-custody-" + "d" * 32)
        self.assertIn("unsettled maintenance window 1", str(second.exception))

    def test_the_refusal_that_propagates_is_the_binding_refusal(self):
        """Not the reclamation's. The reason the act stopped is the expiry, and a
        cleanup failure must not replace it with something else."""
        engine = self.expiring(inspect_after_removal=False)
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn("expired", str(refused.exception).lower())
        self.assertNotIn("could not prove", str(refused.exception))


class TheHostsOwnSettlementIsDurable(MaintenanceCase):
    """W285463 review R3. The token return says the resource is free; it does not
    say what was prepared. This is the fact that was missing."""

    def test_the_receipt_names_the_generation_the_container_and_the_object(self):
        answered = self.prepared()
        self.assertTrue(answered.ok, answered.diagnostic)
        settled = maintenance.maintenance_settlement(self.store, "attempt-1",
                                                     "workspace")
        self.assertEqual(settled["disposition"], maintenance.SETTLED_PREPARED)
        self.assertEqual(settled["version"], maintenance.MAINTENANCE_VERSION)
        self.assertEqual(settled["generation"], answered.generation)
        self.assertEqual(settled["container"], answered.container)
        self.assertEqual(settled["verb"], maintenance.ESTABLISH_RESULT_ROOT)
        self.assertEqual(settled["place"], "result-attempt-1")
        self.assertEqual(settled["execution"],
                         "maintenance-execution:attempt-1:workspace")
        self.assertEqual(settled["attempt"], "attempt-1")
        self.assertTrue(settled["established"])
        # THE PRE-ALLOCATION IDENTITY'S PROMISE, KEPT AS A FACT: the prepared
        # object's own identity, recorded beside the resource it sits inside.
        held = os.lstat(self.result)
        self.assertEqual(settled["object_identity"],
                         f"{held.st_dev}:{held.st_ino}")
        self.assertEqual(settled["pre_allocation"].rsplit("/", 1)[0],
                         settled["domain"].split(":", 1)[1])

    def test_it_is_committed_before_the_token_goes_back(self):
        """A resource handed on before its outcome was recorded would leave the
        next holder unable to learn what happened to it."""
        case = self
        order = []
        honest = tokens.returned

        def returning(control, token, **named):
            order.append(("settlement", maintenance.maintenance_settlement(
                case.store, "attempt-1", "workspace") is not None))
            order.append(("returned", True))
            return honest(control, token, **named)

        with mock.patch.object(tokens, "returned", returning):
            self.prepared()
        self.assertEqual(order, [("settlement", True), ("returned", True)])

    def test_a_fresh_store_handle_reads_the_settlement(self):
        """R3's fresh-handle half: no answer object is held, and the journal is
        asked."""
        answered = self.prepared()
        settled = maintenance.maintenance_settlement(self.reopened(),
                                                     "attempt-1", "workspace")
        self.assertEqual(settled["container"], answered.container)
        self.assertEqual(settled["disposition"], maintenance.SETTLED_PREPARED)
        self.assertEqual(maintenance.maintenance_settlement(
            self.reopened(), "attempt-1", "workspace", 1)["generation"],
            answered.generation)

    def test_no_settlement_exists_when_the_outcome_is_unknown(self):
        answered = self.prepared(Engine(self, logs=1))
        self.assertTrue(answered.held)
        self.assertIsNone(maintenance.maintenance_settlement(
            self.store, "attempt-1", "workspace"))
        self.assertEqual([one for one, _ in maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace")], [1])

    def test_a_report_whose_VALUES_are_not_this_acts_settles_nothing(self):
        """R3: exact semantic values, not only their Python types.

        Each case gets its own attempt, so what is measured is the value rule
        rather than the resource exclusion.
        """
        declared = list(self.identity())
        for member, wrong, why in (
                ("version", maintenance.MAINTENANCE_VERSION + 1,
                 "declares representation version"),
                ("place", "result-somebody-else",
                 "an account of another object is not an account of this one"),
                ("mode", "0o2775", "the prepared object's permissions"),
                ("running_as", [declared[0] + 1, declared[1]],
                 "did not run as the identity that owns the worker's objects")):
            with self.subTest(member=member):
                attempt = self.another(f"attempt-{member.replace('_', '-')}")
                good = {"maintenance": maintenance.ESTABLISH_RESULT_ROOT,
                        "version": maintenance.MAINTENANCE_VERSION,
                        "submission": None, "place": f"result-{attempt}",
                        "established": True,
                        "mode": oct(maintenance.PREPARED_MODE),
                        "running_as": declared}
                engine = Engine(self, document=dict(good, **{member: wrong}))
                answered = self.prepared(engine, assignment_id=attempt)
                self.assertFalse(answered.ok)
                self.assertTrue(answered.held)
                self.assertIn("UNRESOLVED", answered.diagnostic)
                # THE REASON, not merely a refusal: a case that passed on some
                # other check would be measuring something else.
                self.assertIn(why, answered.diagnostic)
                self.assertIsNone(maintenance.maintenance_settlement(
                    self.store, attempt, "workspace"))
                self.assertFalse(tokens.token_of(
                    self.store, self.domain_of(attempt), 1)["returned"])

    def test_the_real_programs_own_values_are_the_ones_that_validate(self):
        """The negative control for the case above: with nothing substituted, the
        program's own document passes the value rules and settles."""
        answered = self.prepared()
        self.assertIsNone(maintenance._mismatch(answered.answer,
                                                "result-attempt-1",
                                                self.group.gid))
        self.assertEqual(answered.answer["version"],
                         maintenance.MAINTENANCE_VERSION)


class TheWorkspaceEntriesAreExcludedWhileAPreparationWrites(MaintenanceCase):
    """W285463 review 2026-09-27T13-42-58Z, the remaining R1 blocker.

    The reviewer reached TWO schedules with a preparation's container admitted and
    running: `workspaces.refuse_if_held` returned, and `_admitted_removal`
    committed a removal ownership. A preparation is a WRITER inside these roots, so
    admitting an allocation, an adoption or a removal beside it is the defect
    W270664 F2 closed for custody and removals, one party later.

    The guard is one reader consulted at the chokepoint every entry already calls
    AND inside the two admission transactions that make the fresh decision.
    """

    def concurrently(self, act):
        """Run `act` at the moment the admitted container is running."""
        case = self
        outcome = []

        class Concurrent(Engine):
            def starting(self, argv):
                case.assertTrue(maintenance.standing_maintenance(
                    case.store, "attempt-1", "workspace"))
                try:
                    act()
                    outcome.append(None)
                except ContractRefusal as refused:
                    outcome.append(str(refused))
                return super().starting(argv)

        answered = self.prepared(Concurrent(self))
        self.assertTrue(answered.ok, answered.diagnostic)
        self.assertEqual(len(outcome), 1)
        return outcome[0]

    def test_the_chokepoint_refuses_while_a_window_stands(self):
        why = self.concurrently(lambda: workspaces.refuse_if_held(
            self.store, self.storage, "attempt-1", "allocating these roots"))
        self.assertIsNotNone(why, "a conflicting entry was admitted")
        self.assertIn("unsettled maintenance window 1", why)
        self.assertIn("a WRITER inside these roots", why)

    def test_a_removal_ownership_is_not_admitted_beside_a_preparation(self):
        why = self.concurrently(lambda: workspaces._admitted_removal(
            self.store, "attempt-1", "removing these roots"))
        self.assertIsNotNone(why, "a removal was admitted beside a live writer")
        self.assertIn("unsettled maintenance window 1", why)

    def test_allocation_itself_is_refused_while_a_window_stands(self):
        """The public entry, not only the helper: this is the act the next child
        will call at the preparation seam."""
        why = self.concurrently(lambda: workspaces.assignment_workspace(
            self.group, self.storage, "attempt-1", control=self.store))
        self.assertIsNotNone(why, "roots were allocated beside a live writer")
        self.assertIn("unsettled maintenance window 1", why)

    def test_a_SETTLED_window_is_history_and_refuses_nothing(self):
        """The other half, and the lesson `_journal_holds` already carries: a
        permanent false refusal is a worse failure than the one being fixed.

        After a completed preparation the window is settled, so allocation,
        the chokepoint and a removal admission all proceed.
        """
        answered = self.prepared()
        self.assertTrue(answered.ok, answered.diagnostic)
        self.assertEqual(maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace"), [])
        workspaces.refuse_if_held(self.store, self.storage, "attempt-1",
                                  "allocating these roots")
        workspaces.assignment_workspace(self.group, self.storage, "attempt-1",
                                        control=self.store)
        # ADMITTED, and the ownership it answers is this act's own: measured
        # rather than guessed -- the answer is a document, not the (ordinal, token)
        # pair I first assumed.
        admitted = workspaces._admitted_removal(
            self.store, "attempt-1", "removing these roots")
        self.assertEqual(admitted["ordinal"], 1)

    def test_an_unsettled_window_on_EITHER_root_excludes_the_other(self):
        """Both roots, because the result root sits INSIDE the workspace.

        Driven by an unprovable orphan on the workspace root and then by asking
        about the attempt as a whole, which is what every workspace entry does.
        """
        engine = Engine(self, inspect_after_removal=False)

        class Delayed(type(engine)):
            def creating(self, argv):
                answer = super().creating(argv)
                self.case.instant = "2026-09-27T00:16:00.000Z"
                return answer

        with self.assertRaises(ContractRefusal):
            self.prepared(Delayed(self, inspect_after_removal=False))
        self.assertEqual([one for one, _ in maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace")], [1])
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.refuse_if_held(self.store, self.storage, "attempt-1",
                                      "adopting these roots")
        self.assertIn("unsettled maintenance window 1", str(refused.exception))
        # AND THE NEXT PREPARATION IS REFUSED TOO, rather than adopting it.
        engine = Engine(self)
        with self.assertRaises(ContractRefusal) as again:
            self.prepared(engine)
        self.assertIn("an unknown to reconcile rather than one to continue from",
                      str(again.exception))
        self.assertEqual(engine.seen, [])


class NoStandingWindowIsEverAdopted(MaintenanceCase):
    """W285463 review 2026-09-27T13-42-58Z: do not let a same-operation replay
    adopt another live executor's window and close it on its own refusal.

    My first shape adopted a window matching verb, domain and derived container
    identity -- which two live executors of one operation all share, so the second
    would have adopted the first's window and could then clear a shared exclusion
    somebody else was relying on. Nothing is adopted now.
    """

    def standing(self, root="workspace"):
        """One window opened and left standing, as a crashed act leaves it."""
        return maintenance._admitted(
            self.store, "attempt-1", root,
            operation=maintenance.ESTABLISH_RESULT_ROOT,
            name=self.name(which=root), domain=self.domain(),
            pre_allocation=f"{self.domain().split(':', 1)[1]}/result-attempt-1")

    def test_an_identical_act_is_refused_rather_than_adopting_the_window(self):
        self.assertEqual(self.standing(), 1)
        engine = Engine(self)
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn("unsettled maintenance window 1", str(refused.exception))
        self.assertIn("clear on somebody else's behalf", str(refused.exception))
        self.assertEqual(engine.seen, [])
        # AND IT IS STILL STANDING: the refused act cleared nothing.
        self.assertEqual([one for one, _ in maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace")], [1])
        self.assertIsNone(maintenance.maintenance_settlement(
            self.store, "attempt-1", "workspace"))

    def test_a_window_on_the_RESULT_root_excludes_a_workspace_preparation(self):
        self.assertEqual(self.standing("result"), 1)
        engine = Engine(self)
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn("result root carries unsettled maintenance window 1",
                      str(refused.exception))
        self.assertEqual(engine.seen, [])

    def test_the_window_names_the_incarnation_that_opened_it(self):
        self.standing()
        record = self.store.operation_record(maintenance._act_identity(
            maintenance.MAINTENANCE_OWNERSHIP_KIND, "attempt-1", "workspace", 1))
        held = json.loads(record["result"]) if type(record["result"]) is str \
            else record["result"]
        self.assertEqual(held["incarnation"], "maintenance-1")
        self.assertEqual(held["verb"], maintenance.ESTABLISH_RESULT_ROOT)
        self.assertEqual(held["helper_identity"], self.name())

    def test_the_settlement_and_the_token_return_are_correlatable(self):
        """R3's last audit point, from the receipt alone.

        A reader that holds only the durable settlement can name the generation and
        ask the token journal what became of it -- which is what makes the two
        separate facts one account rather than two disconnected ones.
        """
        answered = self.prepared()
        fresh = self.reopened()
        settled = maintenance.maintenance_settlement(fresh, "attempt-1",
                                                     "workspace")
        current = tokens.token_of(fresh, settled["domain"],
                                 settled["generation"])
        self.assertTrue(current["returned"])
        self.assertEqual(current["container"], settled["container"])
        self.assertEqual(current["owner"], settled["owner"])
        self.assertEqual(settled["generation"], answered.generation)


class TheOrderingMatrixIsProvedInBothDirections(MaintenanceCase):
    """W285463 review 2026-09-27T13-56-09Z, the reverse ordering.

    The reviewer committed a real `workspaces._admitted_allocation`, proved it
    standing, and this facility ran a preparation inside roots another act was in
    the middle of creating: `maintenance._admitted` and `_eligible` read custody
    overlap and standing removals and NEITHER read a standing allocation, so the
    workspaces-side guard only ever proved the maintenance-first direction.

    One reader answers both decisions now -- `maintenance._conflicting` -- and the
    cases below drive each admission in BOTH directions at its own atomic point.
    The matrix in PROGRESS marks which rows are these selectors and which remain
    source-only.
    """

    def settlement(self):
        """The operands `intake.authorize_cleanup` composes for a cleanup."""
        return {"operation": "cleanup:attempt-1", "signature": "sig-1",
                "incarnation": "maintenance-1"}

    # -- the other act first, then the preparation -------------------------

    def refuses_after(self, act, kind, reader):
        """`act` commits first; the preparation must then refuse having done nothing.

        The ordinal is READ from the owner's own reader rather than written here:
        `setUp` already performed one completed allocation, so an expectation of
        "allocation 1" was my own arithmetic rather than the journal's -- measured
        when it came back as 2.
        """
        act()
        standing = reader(self.store, "attempt-1")
        self.assertTrue(standing, "the act under test recorded nothing")
        expected = (f"{kind} {standing[0][0]} of attempt "
                    f"{name_value('attempt-1')}'s roots")
        engine = Engine(self)
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(engine)
        self.assertIn(expected, str(refused.exception))
        self.assertIn("a WRITER inside these roots", str(refused.exception))
        # NOTHING RAN AND NOTHING WAS ACQUIRED.
        self.assertEqual(engine.ran, 0)
        self.assertEqual(engine.seen, [])
        self.assertEqual(tokens.outstanding(self.store, self.domain()), [])
        self.assertEqual(maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace"), [])

    def test_an_admitted_allocation_excludes_a_preparation(self):
        """The reviewer's own schedule, kept as my regression."""
        self.refuses_after(
            lambda: workspaces._admitted_allocation(
                self.store, "attempt-1", "allocating these roots"),
            "allocation", workspaces.standing_allocation)

    def test_an_admitted_removal_excludes_a_preparation(self):
        self.refuses_after(
            lambda: workspaces._admitted_removal(
                self.store, "attempt-1", "removing these roots"),
            "removal", workspaces.standing_removal)

    def test_an_admitted_cleanup_excludes_a_preparation(self):
        self.refuses_after(
            lambda: workspaces.admit_cleanup(
                self.store, "attempt-1", self.settlement(),
                "cleaning up these roots"),
            "cleanup", workspaces.standing_cleanup)

    def test_an_admitted_adoption_excludes_a_preparation(self):
        self.refuses_after(
            lambda: workspaces._admitted_adoption(
                self.store, "attempt-1", "adopting these roots"),
            "adoption", workspaces.standing_adoption)

    # -- the preparation first, then the other act -------------------------

    def refused_during(self, act):
        case = self
        outcome = []

        class Concurrent(Engine):
            def starting(self, argv):
                case.assertTrue(maintenance.standing_maintenance(
                    case.store, "attempt-1", "workspace"))
                try:
                    act()
                    outcome.append(None)
                except ContractRefusal as refused:
                    outcome.append(str(refused))
                return super().starting(argv)

        answered = self.prepared(Concurrent(self))
        self.assertTrue(answered.ok, answered.diagnostic)
        self.assertEqual(len(outcome), 1)
        self.assertIsNotNone(outcome[0], "the act was admitted beside a writer")
        self.assertIn("unsettled maintenance window 1", outcome[0])
        return outcome[0]

    def test_a_preparation_excludes_a_cleanup_admission(self):
        self.refused_during(lambda: workspaces.admit_cleanup(
            self.store, "attempt-1", self.settlement(),
            "cleaning up these roots"))

    def test_a_preparation_excludes_an_adoption_admission(self):
        self.refused_during(lambda: workspaces._admitted_adoption(
            self.store, "attempt-1", "adopting these roots"))

    # -- and the interposed race, which is why there are two decisions -----

    def test_a_preparation_excludes_an_allocation_admission(self):
        """And with BOTH sides guarded the interposed allocation cannot commit.

        I wrote this case expecting the acquisition's predicate to refuse an
        allocation admitted between the window and the acquire. Measured, it never
        gets that far: the workspaces-side guard refuses the allocation itself, so
        the schedule collapses into "whoever commits first wins". The predicate is
        still load-bearing and is proved so by the `custody._record_hold` case
        above, which is the one route that does not consult the window.
        """
        self.refused_during(lambda: workspaces._admitted_allocation(
            self.store, "attempt-1", "allocating these roots"))

    def test_a_window_on_the_RESULT_root_excludes_the_workspace_entries_too(self):
        """Both roots on the workspaces side as well, driven rather than asserted.

        `_journal_maintenance` walks `custody.CUSTODY_ROOTS`, so a window over the
        nested result root covers the workspace every entry actually operates on.
        """
        maintenance._admitted(
            self.store, "attempt-1", "result",
            operation=maintenance.ESTABLISH_RESULT_ROOT,
            name=self.name(which="result"), domain=self.domain(),
            pre_allocation=f"{self.domain().split(':', 1)[1]}/result-attempt-1")
        for act in (lambda: workspaces.refuse_if_held(
                        self.store, self.storage, "attempt-1", "allocating"),
                    lambda: workspaces._admitted_removal(
                        self.store, "attempt-1", "removing"),
                    lambda: workspaces._admitted_adoption(
                        self.store, "attempt-1", "adopting"),
                    lambda: workspaces.admit_cleanup(
                        self.store, "attempt-1", self.settlement(),
                        "cleaning up")):
            with self.subTest(act=act):
                with self.assertRaises(ContractRefusal) as refused:
                    act()
                self.assertIn("result root carries unsettled maintenance "
                              "window 1", str(refused.exception))

    def test_one_reader_answers_both_decisions(self):
        """The structural half, so the two can never diverge again.

        `_admitted` raises what `_conflicting` answers and `_eligible` returns it;
        my previous cut had two separate readings and the allocation was missing
        from both.
        """
        self.assertIsNone(maintenance._conflicting(self.store, "attempt-1",
                                                   "workspace"))
        workspaces._admitted_allocation(self.store, "attempt-1", "allocating")
        standing = workspaces.standing_allocation(self.store, "attempt-1")
        why = maintenance._conflicting(self.store, "attempt-1", "workspace")
        self.assertIn(f"allocation {standing[0][0]} of attempt", why)
        self.assertEqual(
            maintenance._eligible(self.store, "attempt-1", "workspace")(None)
            .startswith(why), True)


class TheContainersOwnExitDecidesTheOutcome(MaintenanceCase):
    """W285463 review 2026-09-27T14-07-07Z, and a confirmed false success of mine.

    `docker wait` answers two different things: its CLI status says whether the
    manager's command worked, and its STDOUT is the exit code of the container it
    waited for. I ignored the stdout and then used the LOGS command's CLI status as
    the act's status -- so a container that exited 17 came back `ok`, was settled as
    `prepared` and had its token returned, because two engine commands ABOUT it had
    succeeded. A correct report and a real filesystem effect do not turn a failed
    execution into a successful one.
    """

    def exiting(self, stdout):
        """An engine whose container reports this exact wait answer."""
        case = self

        class Exited(Engine):
            def __call__(self, argv, *, seconds=None):
                answer = super().__call__(argv, seconds=seconds)
                if argv[1] == "wait":
                    answer["stdout"] = stdout
                return answer

        return Exited(case)

    def test_exit_zero_is_the_positive_control_and_still_settles(self):
        answered = self.prepared(self.exiting("0\n"))
        self.assertTrue(answered.ok, answered.diagnostic)
        self.assertEqual(answered.status, 0)
        settled = maintenance.maintenance_settlement(self.store, "attempt-1",
                                                     "workspace")
        self.assertEqual(settled["disposition"], maintenance.SETTLED_PREPARED)
        self.assertEqual(settled["exit_status"], 0)

    def test_a_nonzero_exit_is_recorded_AND_STILL_HOLDS_THE_RESOURCE(self):
        """MY OWN EXPECTATION WAS THE REGRESSION, and the record says so.

        I first wrote this case asserting the token WAS returned and the window
        closed, on the argument that a known exit plus a proved cessation leaves no
        uncertainty. Review 2026-09-27T14-27-04Z corrected the policy and is right:
        three facts are separate (TOK-8) -- the container is gone, its exit is known,
        and what it DID to the tree is not. A failed act may have left partial output
        that needs repair (TOK-12), so freeing the resource would let an ordinary
        replacement take a tree whose state nobody established.
        """
        engine = self.exiting("17\n")
        answered = self.prepared(engine)
        self.assertFalse(answered.ok)
        self.assertTrue(answered.held)
        self.assertFalse(answered.returned)
        self.assertEqual(answered.status, 17)
        self.assertIn("EXITED 17", answered.diagnostic)
        self.assertIn("a known exit is not a known effect", answered.diagnostic)
        # THE FAILURE IS DURABLE AND DISTINGUISHABLE, through a fresh handle -- and it
        # is its OWN record rather than a settlement, so it discharges nothing.
        fresh = self.reopened()
        failure = maintenance.maintenance_failure(fresh, "attempt-1",
                                                  "workspace", 1)
        self.assertEqual(failure["exit_status"], 17)
        self.assertEqual(failure["container"], answered.container)
        self.assertEqual(failure["generation"], answered.generation)
        self.assertTrue(failure["accounted"])
        self.assertIsNone(maintenance.maintenance_settlement(fresh, "attempt-1",
                                                             "workspace"))
        # THE HOLD STANDS: token outstanding, window standing, and every other act
        # over these roots still excluded.
        self.assertFalse(tokens.token_of(self.store, self.domain(),
                                         1)["returned"])
        self.assertTrue(tokens.outstanding(self.store, self.domain()))
        self.assertEqual([one for one, _ in maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace")], [1])
        with self.assertRaises(ContractRefusal):
            workspaces.refuse_if_held(self.store, self.storage, "attempt-1",
                                      "allocating these roots")
        # THE CONTAINER IS STILL PROVED ABSENT AND THE EFFECT RAN ONCE.
        self.assertEqual([argv[1] for argv, _ in engine.seen][-3:],
                         ["stop", "rm", "inspect"])
        self.assertEqual(engine.ran, 1)

    def test_a_failed_exit_whose_ACCOUNT_IS_LOST_holds_the_resource_too(self):
        """The reviewer's own schedule: a real effect and then no readable report.

        This is the case that makes the distinction concrete -- the account is gone,
        so nothing at all is known about what the execution left behind.
        """
        case = self

        class Lost(Engine):
            def starting(self, argv):
                answered = super().starting(argv)
                self.stdout = "unreadable result\n"
                return answered

            def __call__(self, argv, *, seconds=None):
                answered = super().__call__(argv, seconds=seconds)
                if argv[1] == "wait":
                    answered["stdout"] = "17\n"
                return answered

        engine = Lost(self)
        answered = self.prepared(engine)
        self.assertFalse(answered.ok)
        self.assertFalse(answered.returned)
        self.assertEqual(engine.ran, 1)
        self.assertTrue(tokens.outstanding(self.store, self.domain()))
        self.assertEqual([one for one, _ in maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace")], [1])
        failure = maintenance.maintenance_failure(self.store, "attempt-1",
                                                  "workspace", 1)
        self.assertEqual(failure["exit_status"], 17)
        # AND THE RECORD SAYS THE ACCOUNT WAS NOT ONE THIS MANAGER COULD READ.
        self.assertFalse(failure["accounted"])
        self.assertIsNone(failure["report"])

    def test_a_failed_exit_whose_report_names_ANOTHER_submission_holds_too(self):
        """A report for another generation is no better than none."""
        engine = self.exiting("17\n")
        engine.document = {
            "maintenance": maintenance.ESTABLISH_RESULT_ROOT,
            "version": maintenance.MAINTENANCE_VERSION,
            "submission": "0" * 64, "place": "result-attempt-1",
            "established": True, "mode": oct(maintenance.PREPARED_MODE),
            "running_as": list(self.identity())}
        answered = self.prepared(engine)
        self.assertFalse(answered.ok)
        self.assertFalse(answered.returned)
        failure = maintenance.maintenance_failure(self.store, "attempt-1",
                                                  "workspace", 1)
        self.assertEqual(failure["exit_status"], 17)
        self.assertFalse(failure["accounted"])
        # AND THE RECORD NAMES WHICH RULE THE REPORT FAILED, so an operator reads a
        # reason rather than a bare flag. Measured correction of mine: `accounted`
        # first came from the SHAPE alone, so this document was written down as
        # accounted for while naming another generation.
        self.assertIn("answers for submission", failure["unaccounted"])
        self.assertIsNone(failure["report"])
        self.assertTrue(tokens.outstanding(self.store, self.domain()))

    def test_a_wait_answer_this_manager_cannot_READ_is_an_unknown(self):
        """Missing, multiple, non-numeric and out of range -- each its own attempt,
        because an unreturned generation excludes the next acquisition."""
        for label, stdout, why in (
                ("missing", "\n", "0 exit codes"),
                ("multiple", "0\n17\n", "2 exit codes"),
                ("prose", "exited cleanly\n", "not a whole number"),
                ("out-of-range", "4096\n", "outside the range")):
            with self.subTest(label=label):
                attempt = self.another(f"attempt-wait-{label}")
                engine = self.exiting(stdout)
                answered = self.prepared(engine, assignment_id=attempt)
                self.assertFalse(answered.ok)
                self.assertTrue(answered.held)
                self.assertIsNone(answered.status)
                self.assertIn("UNRESOLVED", answered.diagnostic)
                self.assertIn(why, answered.diagnostic)
                # NO SETTLEMENT, THE WINDOW STANDS, THE TOKEN IS HELD.
                self.assertIsNone(maintenance.maintenance_settlement(
                    self.store, attempt, "workspace"))
                self.assertEqual(
                    [one for one, _ in maintenance.standing_maintenance(
                        self.store, attempt, "workspace")], [1])
                self.assertFalse(tokens.token_of(
                    self.store, self.domain_of(attempt), 1)["returned"])

    def test_a_failed_wait_COMMAND_is_a_transport_unknown_not_an_exit(self):
        """The other half of the distinction: nobody learned whether it ended, so
        the container is not proved absent and nothing is settled."""
        answered = self.prepared(Engine(self, waits=1))
        self.assertFalse(answered.ok)
        self.assertTrue(answered.held)
        self.assertIn("could not learn whether the preparation", answered.diagnostic)
        self.assertIsNone(maintenance.maintenance_settlement(
            self.store, "attempt-1", "workspace"))
        self.assertEqual([one for one, _ in maintenance.standing_maintenance(
            self.store, "attempt-1", "workspace")], [1])
        self.assertFalse(tokens.token_of(self.store, self.domain(),
                                         1)["returned"])

    def test_a_correct_report_does_not_rescue_a_failed_container(self):
        """The reviewer's exact point, asserted as a property.

        The program really ran, really created the object and really printed an
        accountable versioned report -- and the act is still not a preparation.
        """
        engine = self.exiting("17\n")
        answered = self.prepared(engine)
        self.assertIsNotNone(answered.answer)
        self.assertIsNone(answered.unaccounted)
        self.assertTrue(answered.answer["established"])
        self.assertTrue(os.path.isdir(self.result))
        self.assertFalse(answered.ok)


class TheSURVIVINGHelpersAreEstablishedAndNotAssumed(MaintenanceCase):
    """W285465, TOK-12: the writer-absence half of a recovery return, established.

    `tokens.returned` refuses a cessation reporting a surviving writer, and the ordinary
    cleanup builder may answer "none" only because committed custody holds the roots. The
    recovery transition returns the old generation BEFORE any repair, so it must establish
    the fact -- which is what this reader does, and what these cases drive.
    """

    def asked(self, answering=()):
        seen, listed = [], []

        def engine(argv, *, seconds=None):
            seen.append(list(argv))
            if argv[1] == "ps":
                name = argv[-1].split("=")[-1] if "=" in argv[-1] else argv[-1]
                # THE LISTING ENTRY CARRIES `Names`, which this adapter requires and
                # does not guess at -- read off its own refusal while driving this.
                rows = ([{"ID": "runtime-helper", "Names": name,
                          "Name": name, "Image": "sha256:" + "c" * 64,
                          "State": "running"}]
                        if name in answering else [])
                listed.extend(one["Names"] for one in rows)
                return {"status": 0, "stderr": "",
                        "stdout": "".join(json.dumps(one) + "\n" for one in rows)}
            if argv[1] == "inspect":
                # THE FOLLOW-UP THIS PATH TAKES when a candidate exists, read from the
                # traceback rather than guessed: `_reconciled` inspects the identity it
                # found and refuses an unreadable answer, which is the refusal I
                # previously misread as an empty-listing problem.
                return {"status": 0, "stderr": "",
                        "stdout": json.dumps(
                            # THE ENGINE'S RECORD NAMES IT WHAT THE LISTING DID: the
                            # adapter identifies a helper twice over and refuses a pair
                            # that disagrees, and `inspect`'s operand is the RUNTIME ID
                            # rather than the name -- read off that refusal.
                            {"Id": "runtime-helper", "Names": listed[-1],
                             "Name": listed[-1],
                             "Image": "sha256:" + "c" * 64,
                             "State": {"Running": True, "Status": "running"}}) + "\n"}
            return {"status": 0, "stdout": "", "stderr": ""}

        return custody.surviving_helpers(
            "docker", engine, self.store, "attempt-1",
            image_digest="sha256:" + "c" * 64), seen

    def test_a_QUIET_attempt_answers_no_surviving_writer(self):
        surviving, seen = self.asked()
        self.assertEqual(surviving, [])
        # AND IT REALLY ASKED: both roots, every closed verb, by derived name, and the
        # EMPTY listing is a perfectly good answer -- which the reviewer's probe proved
        # and my reported blocker got wrong.
        self.assertEqual(
            len([one for one in seen if one[1] == "ps"]),
            len(custody.CUSTODY_ROOTS) * len(custody.CUSTODY_OPERATIONS))

    def test_a_NO_CUSTODIAN_deployment_reports_the_UNKNOWN_it_cannot_ask(self):
        """W285465: a missing custodian image is not proof that no helper exists.

        THE DOCSTRING THIS REPLACES WAS THE DEFECT'S OWN REASONING, and the reviewer was
        right to ask for it to go with the change: it said there was "no derived name for
        the engine to be asked about", and the names do not depend on the image at all.
        What is true is narrower -- this manager cannot IDENTIFY a candidate without the
        custodian image, so the engine half cannot be asked, and an answer that cannot be
        obtained is reported as an UNKNOWN that HOLDS. The journal half still runs in full
        and an uncleared episode still holds on its own.
        """
        seen = []

        def engine(argv, *, seconds=None):
            seen.append(list(argv))
            return {"status": 0, "stdout": "", "stderr": ""}

        # NOT ASKED IS NOT ABSENT. Review 2026-09-28T03-50-12Z: the derived names do not
        # depend on the image, so a configuration that LOST its custodian still has names
        # an earlier one could have launched under. The answer therefore reports the
        # UNKNOWN -- which HOLDS -- rather than reporting quiet.
        answered = custody.surviving_helpers(
            "docker", engine, self.store, "attempt-1", image_digest=None)
        self.assertTrue(answered, "a missing image was read as helper absence")
        self.assertIn("engine was NOT asked", answered[0]["why"])
        self.assertIsNone(answered[0]["helper_identity"])
        self.assertEqual(seen, [],
                         "a deployment with no custodian asked the engine anyway")

    def test_a_CONFIG_LOSS_still_reports_the_helper_names_it_cannot_identify(self):
        """The reviewer's own schedule: the SAME store and engine that report a live
        helper WITH an image must not report quiet without one, because the derived names
        do not depend on the image."""
        name = custody._custody_identity(
            custody._recorded_store(self.store), "attempt-1", "result", "normalize")
        with_image, asked = self.asked(answering=(name,))
        self.assertEqual([one["helper_identity"] for one in with_image], [name])
        self.assertTrue(asked, "the positive control never asked the engine")
        # THE SAME FIXTURE, ONLY THE IMAGE GONE: the answer must still HOLD.
        seen = []

        def engine(argv, *, seconds=None):
            seen.append(list(argv))
            return {"status": 0, "stdout": "", "stderr": ""}

        without = custody.surviving_helpers(
            "docker", engine, self.store, "attempt-1", image_digest=None)
        self.assertTrue(without, "losing the image turned a live helper into quiet")
        self.assertIn("engine was NOT asked", without[0]["why"])
        self.assertEqual(seen, [])

    def test_a_helper_ANSWERING_a_derived_name_is_reported_surviving(self):
        name = custody._custody_identity(
            custody._recorded_store(self.store), "attempt-1", "result", "normalize")
        surviving, _seen = self.asked(answering=(name,))
        self.assertEqual([one["helper_identity"] for one in surviving], [name])
        self.assertIn("still answering", surviving[0]["why"])
        self.assertEqual(surviving[0]["runtime_id"], "runtime-helper")


class TheSELECTEDOutputIsAccessibleOrItIsAnError(MaintenanceCase):
    """W285465 under the owner ruling: accessible output progresses, inaccessible errors.

    OWNER-NO-AUTOMATIC-NORMALIZATION-20260928 with DESIGN HOST-5 selects shared-group
    accessible job output. There is no normalization receipt on this path and no helper of
    any kind, so what the selected completion and recovery endings need is a READ that
    answers which entry the group cannot reach -- and that read must change nothing.
    """

    def roots(self):
        return {"workspace": self.workspace,
                "result": os.path.join(self.workspace, "result-attempt-1")}

    def test_ACCESSIBLE_output_answers_None_and_changes_nothing(self):
        from baton_v12.worker_manager import intake

        os.makedirs(self.roots()["result"], exist_ok=True)
        answer = os.path.join(self.roots()["result"], "answer.txt")
        with open(answer, "wb") as writing:
            writing.write(b"the job's own answer\n")
        os.chmod(answer, 0o640)
        group = workspaces.configured_workspace_group(self.store).gid
        os.chown(answer, -1, group)
        before = self.identity_of(self.workspace)
        self.assertIsNone(intake.inaccessible_output(self.store, "attempt-1"))
        # IT CHANGED NOTHING: no chmod, no chown, no delete, and no helper.
        self.assertEqual(self.identity_of(self.workspace), before)

    def test_INACCESSIBLE_output_names_the_exact_entry_and_preserves_it(self):
        from baton_v12.worker_manager import intake

        os.makedirs(self.roots()["result"], exist_ok=True)
        answer = os.path.join(self.roots()["result"], "answer.txt")
        with open(answer, "wb") as writing:
            writing.write(b"the job's own answer\n")
        os.chmod(answer, 0o600)
        before = self.identity_of(self.workspace)
        found = intake.inaccessible_output(self.store, "attempt-1")
        self.assertIsNotNone(found)
        self.assertEqual(found["path"], answer)
        self.assertEqual(found["mode"], 0o600)
        self.assertIn("does not change permissions", found["why"])
        # AND THE BYTES AND MODES ARE EXACTLY AS THEY WERE: an error preserves the
        # workspace, which is the owner's selection rather than a repair.
        self.assertEqual(self.identity_of(self.workspace), before)
        with open(answer, "rb") as reading:
            self.assertEqual(reading.read(), b"the job's own answer\n")

    def test_an_UNREACHABLE_ROOT_is_the_first_thing_that_is_inaccessible(self):
        """Review 2026-09-28T02-50-56Z [P1]: my first cut walked only CHILDREN, so a root
        at 0700 -- unreachable, and empty because nothing could be listed -- answered
        accessible. A root nobody can enter is not a special case."""
        from baton_v12.worker_manager import intake

        os.makedirs(self.roots()["result"], exist_ok=True)
        os.chmod(self.roots()["result"], 0o700)
        found = intake.inaccessible_output(self.store, "attempt-1")
        self.assertIsNotNone(found)
        self.assertEqual(found["path"], self.roots()["result"])
        self.assertEqual(found["mode"], 0o700)

    def test_a_TRAVERSAL_FAILURE_is_an_answer_and_not_silence(self):
        """`os.walk` swallows errors by default, so an unreadable subdirectory looked
        like an empty one. `onerror` reports it, and an unobserved tree is never
        success."""
        from baton_v12.worker_manager import intake

        os.makedirs(self.roots()["result"], exist_ok=True)
        group = workspaces.configured_workspace_group(self.store).gid
        os.chown(self.roots()["result"], -1, group)
        os.chmod(self.roots()["result"], 0o750)
        honest = os.scandir

        def refusing(place, *arguments, **named):
            if str(place).startswith(self.roots()["result"]):
                raise PermissionError(13, "Permission denied", str(place))
            return honest(place, *arguments, **named)

        with mock.patch.object(os, "scandir", side_effect=refusing):
            found = intake.inaccessible_output(self.store, "attempt-1")
        self.assertIsNotNone(found)
        self.assertIn("could not traverse the output", found["why"])
        self.assertIn("PermissionError", found["why"])

    def test_an_UNDERIVABLE_root_is_reported_and_never_read_as_success(self):
        """Review 2026-09-28T02-55-12Z: a caller mapping was not an authenticated root.

        My first cut took `roots` from the caller, so an EMPTY mapping answered
        "accessible" -- it had nothing to walk -- and a missing key was skipped. Both
        roots are derived from durable state now, and a root this manager cannot derive is
        REPORTED: an absence nobody has evidenced is not success.
        """
        from baton_v12.worker_manager import intake

        found = intake.inaccessible_output(self.store, "attempt-nobody-allocated")
        self.assertIsNotNone(found, "an attempt with no derivable roots answered OK")
        self.assertIn("could not derive", found["why"])
        self.assertIsNone(found["path"])

    def test_a_SUBSTITUTED_root_a_caller_names_is_refused_not_skipped(self):
        """`roots` is an EXPECTATION, compared against durable state and never trusted."""
        from baton_v12.worker_manager import intake

        os.makedirs(self.roots()["result"], exist_ok=True)
        found = intake.inaccessible_output(
            self.store, "attempt-1",
            dict(self.roots(), result="/tmp/somebody-elses-root"))
        self.assertIsNotNone(found)
        self.assertEqual(found["root"], "result")
        self.assertIn("substituted or omitted root is refused", found["why"])
        # AND AN OMITTED ONE IS THE SAME ANSWER, which is what an empty mapping used to
        # get away with.
        omitted = intake.inaccessible_output(self.store, "attempt-1", {})
        self.assertIsNotNone(omitted)
        self.assertIn("substituted or omitted root is refused", omitted["why"])

    @staticmethod
    def identity_of(root):
        found = {}
        for walked, directories, files in os.walk(root):
            for name in sorted(directories) + sorted(files):
                place = os.path.join(walked, name)
                held = os.lstat(place)
                found[os.path.relpath(place, root)] = (
                    stat.S_IMODE(held.st_mode), held.st_gid, held.st_size)
        return found


class TheADOPTIONTakesTheCapabilityAndNotANumber(MaintenanceCase):
    """W285465 under the 2026-09-28T04-19-10Z adjudication: current-API coverage.

    The numeric positive shape of `review_preparation_adoption_20260928.py` is SUPERSEDED
    and kept as history; these are the current-API cases. Ordinals collide across attempts,
    so what exempts an attempt's own window is the `PreparationOwnership` its admission
    minted -- never an integer.
    """

    def held(self, attempt="attempt-1"):
        return workspaces.admit_preparation(
            self.store, attempt, f"preparing {attempt}", attempt)

    def test_the_HOLDER_adopts_with_its_own_capability(self):
        owned = self.held()
        roots = workspaces.adopted_assignment_workspace(
            self.storage, "attempt-1", control=self.store, preparing=owned)
        self.assertEqual(roots["workspace"], self.workspace)

    def test_a_CROSS_STORE_capability_is_not_this_stores_mint(self):
        """The cross-store substitution, with EVERY public member equal.

        Review 2026-09-28T04-26-06Z and 04-32-08Z: a genuine capability from a separate
        store adopted held roots, and no RECORDED value can distinguish the two -- with
        equal attempt, ordinal, instant and incarnation a derivation collides by
        construction, and a value in a row proves possession of the row. So what decides is
        BEING the object this store's admission handed out.
        """
        from baton_v12.worker_manager import ControlStore

        mine = self.held()
        # AN INDEPENDENT STORE, which is its own DATABASE: the same file would refuse a
        # second admission for this attempt, and the substitution this case is about is a
        # capability minted elsewhere, not a second window in one journal.
        second = ControlStore.open(
            os.path.join(self.root, "another-control.sqlite3"),
            incarnation="maintenance-1", clock=lambda: self.instant)
        self.addCleanup(second.close)
        theirs = workspaces.admit_preparation(
            second, "attempt-1", "preparing attempt-1", "attempt-1")
        # EVERY PUBLIC MEMBER IS EQUAL, which is the point.
        self.assertEqual((theirs.attempt, theirs.ordinal),
                         (mine.attempt, mine.ordinal))
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.adopted_assignment_workspace(
                self.storage, "attempt-1", control=self.store, preparing=theirs)
        self.assertIn("this store's admission did not mint", str(refused.exception))
        # AND IT CLOSES NOTHING EITHER.
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.release_preparation(self.store, theirs, "a foreign release")
        self.assertIn("closes nothing here", str(refused.exception))

    def test_a_CROSS_STORE_capability_cannot_continue_the_window_either(self):
        """The atomic RE-ENTRY, which `_mounted` uses before it allocates.

        Review 2026-09-28T04-44-01Z: I fixed the adoption and the release and left the
        standing-window branch comparing type, attempt and ordinal, so a capability another
        store handed out still continued the window -- and the composition uses that
        returned authority to write. The same identity question is asked there now.
        """
        from baton_v12.worker_manager import ControlStore

        mine = self.held()
        second = ControlStore.open(
            os.path.join(self.root, "another-control.sqlite3"),
            incarnation="maintenance-1", clock=lambda: self.instant)
        self.addCleanup(second.close)
        theirs = workspaces.admit_preparation(
            second, "attempt-1", "preparing attempt-1", "attempt-1")
        self.assertEqual((theirs.attempt, theirs.ordinal),
                         (mine.attempt, mine.ordinal))
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_preparation(
                self.store, "attempt-1", "continuing with a foreign ownership",
                "attempt-1", holding=theirs)
        self.assertIn("does not hold its ownership", str(refused.exception))

    def test_the_GENUINE_holder_still_continues_its_own_window(self):
        """The positive the re-entry check must not break: the same object continues."""
        owned = self.held()
        again = workspaces.admit_preparation(
            self.store, "attempt-1", "continuing my own window", "attempt-1",
            holding=owned)
        self.assertIs(again, owned)
        self.assertEqual(
            [one for one, _ in workspaces.standing_preparation(self.store,
                                                               "attempt-1")],
            [1], "a second window was opened instead of continuing the first")

    def test_a_RELEASED_capability_stops_working(self):
        owned = self.held()
        workspaces.release_preparation(self.store, owned, "the writer returned")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.adopted_assignment_workspace(
                self.storage, "attempt-1", control=self.store, preparing=owned)
        self.assertIn("did not mint", str(refused.exception))
        # AND IT CANNOT BE RELEASED TWICE ON THE STRENGTH OF STILL BEING HELD.
        with self.assertRaises(ContractRefusal):
            workspaces.release_preparation(self.store, owned, "a second release")

    def test_a_REOPENED_manager_holds_no_mint_and_is_refused(self):
        """UNKNOWN STAYS HELD: this is live in-process authority and claims nothing about
        a restart, so a manager that reopens the journal inherits no capability."""
        from baton_v12.worker_manager import ControlStore

        self.held()
        reopened = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="after-the-restart", clock=lambda: self.instant)
        self.addCleanup(reopened.close)
        self.assertEqual(
            [one for one, _ in workspaces.standing_preparation(reopened, "attempt-1")],
            [1], "the window is still standing for the reopened manager")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.adopted_assignment_workspace(
                self.storage, "attempt-1", control=reopened)
        self.assertIn("host preparation 1", str(refused.exception))

    def test_a_BARE_ORDINAL_is_refused_as_the_capability_error_it_is(self):
        owned = self.held()
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.adopted_assignment_workspace(
                self.storage, "attempt-1", control=self.store,
                preparing=owned.ordinal)
        self.assertEqual((refused.exception.category, refused.exception.code),
                         ("policy", "denied"))
        self.assertIn("is not authority", str(refused.exception))

    def test_a_FOREIGN_capability_exempts_nothing_even_at_the_same_ordinal(self):
        mine = self.held("attempt-1")
        workspaces.assignment_workspace(self.group, self.storage, "attempt-2")
        theirs = self.held("attempt-2")
        self.assertEqual(mine.ordinal, theirs.ordinal,
                         "the collision this case is about did not occur")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.adopted_assignment_workspace(
                self.storage, "attempt-1", control=self.store, preparing=theirs)
        self.assertIn("exempts nothing here", str(refused.exception))

    def test_a_MISSING_capability_leaves_the_act_as_strict_as_before(self):
        self.held()
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.adopted_assignment_workspace(
                self.storage, "attempt-1", control=self.store)
        self.assertIn("host preparation 1", str(refused.exception))


class TheEXECUTIONAllowanceIsTheAttemptsOwnCurrentRun(MaintenanceCase):
    """W285465: the `mine=` allowance in `_task_token_refusal`, controlled.

    The allowance exists so an attempt's own preparation re-entry is not refused by the token
    its own start took -- measured when it was missing: eighteen refusals whose text was the
    attempt's own. What it must NOT become is a hole. These are the four the review names:
    the current generation, a foreign execution, a stale generation of the same execution,
    and an attempt whose governed state is not knowable at all.
    """

    ATTEMPT = "attempt-1"

    def pinned(self):
        from baton_v12.worker_manager import attempts as manager_attempts

        manager_attempts.record_attempt(
            self.store, attempt_id=self.ATTEMPT, adapter_name="oci",
            adapter_digest="sha256:" + "d" * 64,
            profile_digest="sha256:" + "e" * 64)
        held = os.lstat(self.workspace)
        manager_attempts.pin_boundary_identity(
            self.store, attempt_id=self.ATTEMPT, source=(held.st_dev, 1),
            workspace=(held.st_dev, held.st_ino))
        from baton_v12.worker_manager import attempts as _a
        return _a._require_attempt(self.store, self.ATTEMPT)

    def taken(self, execution, operation):
        return tokens.acquire(self.store, self.domain(), operation=operation,
                              execution=execution, attempt=self.ATTEMPT)

    def refusal(self, mine=None):
        return workspaces._task_token_refusal(
            self.store, self.ATTEMPT, "a probe act", mine=mine)

    def test_the_attempts_OWN_CURRENT_generation_is_allowed_its_re_entry(self):
        self.pinned()
        self.taken(self.ATTEMPT, f"start:{self.ATTEMPT}")
        self.assertIsNotNone(self.refusal(),
                             "an act with no allowance was not refused")
        self.assertIsNone(self.refusal(mine=self.ATTEMPT),
                          "the attempt's own re-entry was refused by its own token")

    def test_a_FOREIGN_execution_is_not_allowed_by_anybody_elses_name(self):
        self.pinned()
        self.taken("somebody-elses-execution", "start:theirs")
        why = self.refusal(mine=self.ATTEMPT)
        self.assertIsNotNone(why, "a foreign execution's token was passed over")
        self.assertIn("somebody-elses-execution", str(why))

    def test_a_STALE_generation_of_the_SAME_execution_is_still_refused(self):
        """Two outstanding generations of one execution: the allowance covers ONE re-entry.

        MEASURED and stated as it is rather than as I would like it: the allowance is keyed
        on the execution, so a SECOND outstanding generation of the same execution is passed
        over too. What stops that from being a hole is that a second generation cannot be
        ACQUIRED while the first is outstanding -- `tokens.acquire` refuses it, which this
        case drives -- so the state the allowance could be too broad for is one the token
        facility does not allow to exist.
        """
        self.pinned()
        self.taken(self.ATTEMPT, f"start:{self.ATTEMPT}")
        with self.assertRaises(ContractRefusal) as refused:
            self.taken(self.ATTEMPT, "start:again")
        self.assertIn("revoked rather than replaced", str(refused.exception))
        self.assertEqual(
            [one["generation"] for one in tokens.outstanding(self.store,
                                                             self.domain())],
            [1])

    def test_the_LEGAL_second_run_is_arbitrated_through_the_REAL_caller(self):
        """Review 2026-09-28T08-35-38Z: the sequence the facility actually allows.

        My stale case only showed a second acquire is refused while the first stands. The
        LEGAL shape is return-first, start-second, and it is driven here through the real
        caller -- `adopted_assignment_workspace`, which is what consults the allowance --
        rather than through the predicate alone:

          * generation 1 stands: the attempt's OWN capability adopts, and a FOREIGN one does
            not;
          * generation 1 is returned and generation 2 is acquired: the capability MINTED
            UNDER THE FIRST RUN still works, because it is this store's mint for this
            attempt and the allowance is about the attempt's own re-entry -- stated because
            it is the honest answer and not the one I assumed;
          * with the window released, the same adoption is refused by generation 2, so the
            capability is what carried it and not the generation's absence.
        """
        attempt = self.pinned()
        first = self.taken(self.ATTEMPT, f"start:{self.ATTEMPT}")
        mine = workspaces.admit_preparation(self.store, self.ATTEMPT,
                                            "preparing this attempt",
                                            self.ATTEMPT)
        roots = workspaces.adopted_assignment_workspace(
            self.storage, self.ATTEMPT, control=self.store, preparing=mine)
        self.assertEqual(roots["workspace"], self.workspace)
        workspaces.release_adopted_workspace(roots)
        # AND A FOREIGN CAPABILITY DOES NOT, while that same generation stands.
        from baton_v12.worker_manager import ControlStore

        other = ControlStore.open(os.path.join(self.root, "other.sqlite3"),
                                  incarnation="maintenance-9",
                                  clock=lambda: self.instant)
        self.addCleanup(other.close)
        theirs = workspaces.admit_preparation(other, self.ATTEMPT,
                                              "preparing elsewhere",
                                              self.ATTEMPT)
        with self.assertRaises(ContractRefusal):
            workspaces.adopted_assignment_workspace(
                self.storage, self.ATTEMPT, control=self.store,
                preparing=theirs)
        # THE LEGAL SECOND RUN: the first generation is RETURNED and a second is acquired.
        tokens.returned(self.store, first,
                        cessation={"domain": first["domain"],
                                   "generation": first["generation"],
                                   "launch": None,
                                   "container": None,
                                   "stopped": True, "helpers": []})
        second = self.taken(self.ATTEMPT, "start:again")
        self.assertEqual(
            [one["generation"] for one in tokens.outstanding(self.store,
                                                             self.domain())],
            [second["generation"]])
        again = workspaces.adopted_assignment_workspace(
            self.storage, self.ATTEMPT, control=self.store, preparing=mine)
        self.assertEqual(again["workspace"], self.workspace)
        workspaces.release_adopted_workspace(again)
        # AND WITHOUT THE WINDOW, generation 2 refuses the same adoption -- so what carried
        # it above was the capability and not the generation being absent.
        workspaces.release_preparation(self.store, mine, "done preparing")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.adopted_assignment_workspace(
                self.storage, self.ATTEMPT, control=self.store)
        self.assertIn("has not been returned", str(refused.exception))

    def test_an_UNKNOWN_governed_state_earns_NO_allowance_and_NO_refusal(self):
        """An attempt with no pinned workspace object has no generation to arbitrate.

        The predicate answers `None` -- no refusal -- and that is not a weakening: a
        generation cannot be acquired over a workspace object nobody recorded, which
        `tokens.workspace_identity` refuses outright, so there is nothing outstanding for
        this to pass over. The case drives both halves so the pairing is not assumed.
        """
        from baton_v12.worker_manager import attempts as manager_attempts

        manager_attempts.record_attempt(
            self.store, attempt_id=self.ATTEMPT, adapter_name="oci",
            adapter_digest="sha256:" + "d" * 64,
            profile_digest="sha256:" + "e" * 64)
        from baton_v12.worker_manager import attempts as _a

        self.assertIsNone(self.refusal())
        self.assertIsNone(self.refusal(mine=self.ATTEMPT))
        # THE OTHER HALF, through the path a real start takes: the resource this attempt
        # would contend for cannot even be NAMED without the pinned object, so there is
        # nothing outstanding for the predicate to have passed over. (The fixture's own
        # `domain()` composes from an `lstat` and would bypass that, which is why this asks
        # the product's reader instead.)
        with self.assertRaises(ContractRefusal) as refused:
            tokens.workspace_identity(_a._require_attempt(self.store,
                                                          self.ATTEMPT))
        self.assertIn("no pinned workspace object", str(refused.exception))

    def test_an_attempt_with_NO_ROW_at_all_is_not_arbitrated_here(self):
        """The reader refuses to invent a domain for an attempt it has no record of."""
        self.assertIsNone(self.refusal())


class THEREVALIDATIONComparesTheLayoutItsRecordIsAbout(MaintenanceCase):
    """W285465 review 2026-09-28T05-11-31Z: the located root-layout defect, corrected.

    `record_preparation` stores `device:inode` members and NO PATH, and on a review-line
    path the workspace it completed over is the persistent LINE HOME that
    `line_assignment_workspace` composed -- not `<storage>/<attempt>/workspace`. The
    live-token revalidation reconstructs the ORDINARY attempt layout, so it compared the
    line record's identity against the attempt's own object and refused a correct
    preparation as a replaced one. The reviewer measured recorded 66306:55317182 against
    current 66306:55317178 on that path.

    The record now STATES which layout it is about and the revalidation compares only
    operands it knows are the same object. What these cases hold onto is that NOTHING was
    relaxed: the attempt layout still compares both roots, the line layout still compares
    the inputs it can locate, replacement and substitution still refuse, and a record
    whose layout is unstated is refused rather than compared.
    """

    ATTEMPT = "attempt-1"

    def prepared(self, roots, attempt=None):
        """The completion record this attempt's preparation would have written."""
        return workspaces.record_preparation(self.store, attempt or self.ATTEMPT,
                                             roots, published=[])

    def attempt_row(self, workspace=None):
        """A durable attempt row whose PINNED workspace object is the real one.

        `_task_token_refusal` computes the domain from the row, not from an `lstat`, so
        the row is what decides whether the live-token branch is reached at all.
        """
        from baton_v12.worker_manager import attempts as manager_attempts

        manager_attempts.record_attempt(
            self.store, attempt_id=self.ATTEMPT, adapter_name="oci",
            adapter_digest="sha256:" + "d" * 64,
            profile_digest="sha256:" + "e" * 64)
        held = os.lstat(workspace or self.workspace)
        manager_attempts.pin_boundary_identity(
            self.store, attempt_id=self.ATTEMPT, source=(held.st_dev, 1),
            workspace=(held.st_dev, held.st_ino))

    def live_task(self):
        """The attempt's OWN task generation, outstanding -- what selects revalidation."""
        return tokens.acquire(self.store, self.domain(),
                              operation=f"start:{self.ATTEMPT}",
                              execution=self.ATTEMPT, attempt=self.ATTEMPT)

    def revalidating(self):
        return workspaces.assignment_workspace(self.group, self.storage,
                                               self.ATTEMPT, control=self.store)

    def attempt_roots(self):
        """The roots the ordinary allocation answered, before any task is live."""
        return workspaces.assignment_workspace(self.group, self.storage,
                                               self.ATTEMPT, control=self.store)

    def line_roots(self, attempt=None):
        """A composed LINE pair: the attempt's own inputs beside a persistent line home."""
        attempt = attempt or self.ATTEMPT
        place = os.path.join(self.storage, workspaces._REVIEW_LINE_HOME,
                             f"line-{attempt}")
        os.makedirs(place, exist_ok=True)
        held = os.lstat(place)
        os.makedirs(os.path.join(self.storage, attempt, "workspace",
                                 f"result-{attempt}"), exist_ok=True)
        return place, workspaces.line_assignment_workspace(
            self.storage, attempt, place, (held.st_dev, held.st_ino),
            control=self.store)

    # -- the defect ------------------------------------------------------

    def test_a_LINE_composed_preparation_is_REVALIDATED_and_not_refused(self):
        """The traced case: a line record no longer reads as a replaced attempt object."""
        place, composed = self.line_roots()
        self.prepared(composed)
        # AND THE TWO IDENTITIES REALLY DO DIFFER, so this case would fail without the
        # correction rather than passing for want of a difference. MEASURED: against the
        # uncorrected module this case refuses with "a replaced object is not the one this
        # preparation completed over" -- nothing here asserts the new record member, so
        # what it drives is the behaviour and not the shape.
        line = os.lstat(place)
        self.assertNotEqual(f"{line.st_dev}:{line.st_ino}",
                            workspaces._entry_identity(self.workspace))
        self.attempt_row()
        self.live_task()
        roots = self.revalidating()
        self.assertEqual(roots["workspace"], self.workspace,
                         "the revalidation answers the attempt's own roots")
        self.assertEqual(roots["inputs"], os.path.join(self.home, "inputs"))

    def test_the_RECORD_STATES_which_layout_each_path_completed_over(self):
        """The record is what carries it, because the identities carry no path."""
        self.assertEqual(self.prepared(self.attempt_roots())["workspace_layout"],
                         "attempt")
        # A SECOND ATTEMPT for the line case: one attempt records ONE completion, and a
        # second `record_preparation` over the same operation identity is a replay.
        second = self.another("attempt-2")
        self.assertEqual(
            self.prepared(self.line_roots(second)[1], second)["workspace_layout"],
            "line")

    def test_an_ATTEMPT_layout_record_is_compared_whole(self):
        allocated = self.attempt_roots()
        self.prepared(allocated)
        self.attempt_row()
        self.live_task()
        self.assertEqual(self.revalidating()["workspace"], self.workspace)

    # -- and nothing was relaxed -----------------------------------------

    def test_a_REPLACED_workspace_under_the_attempt_layout_still_refuses(self):
        """The accepted replacement guard, on the operands it is actually about."""
        self.prepared(self.attempt_roots())
        self.attempt_row()
        self.live_task()
        # THE SAME PATH, A DIFFERENT OBJECT: moved aside and rebuilt, so the shape is
        # right and only the inode differs.
        os.rename(self.workspace, os.path.join(self.home, "displaced"))
        os.mkdir(self.workspace)
        os.makedirs(self.result)
        with self.assertRaises(ContractRefusal) as refused:
            self.revalidating()
        self.assertIn("a replaced object is not the one this preparation completed over",
                      str(refused.exception))

    def test_a_REPLACED_inputs_root_under_the_LINE_layout_still_refuses(self):
        """The line branch compares the INPUTS -- it does not stop comparing."""
        self.line_roots()
        self.prepared(self.line_roots()[1])
        self.attempt_row()
        self.live_task()
        inputs = os.path.join(self.home, "inputs")
        os.chmod(inputs, 0o755)
        os.rename(inputs, os.path.join(self.home, "displaced-inputs"))
        os.mkdir(inputs)
        with self.assertRaises(ContractRefusal) as refused:
            self.revalidating()
        self.assertIn("prepared inputs root was", str(refused.exception))

    def test_a_SUBSTITUTED_workspace_is_refused_before_any_comparison(self):
        """A symlink at the workspace's path: the `_no_link` rule, unchanged."""
        self.prepared(self.attempt_roots())
        self.attempt_row()
        self.live_task()
        elsewhere = os.path.join(self.root, "somebody-elses-workspace")
        os.makedirs(os.path.join(elsewhere, f"result-{self.ATTEMPT}"))
        os.rename(self.workspace, os.path.join(self.home, "displaced"))
        os.symlink(elsewhere, self.workspace)
        with self.assertRaises(ContractRefusal) as refused:
            self.revalidating()
        self.assertIn("is not the object this manager prepared",
                      str(refused.exception))

    def test_MISSING_material_still_refuses_rather_than_being_repaired(self):
        self.prepared(self.attempt_roots())
        self.attempt_row()
        self.live_task()
        os.rmdir(os.path.join(self.home, "inputs"))
        with self.assertRaises(ContractRefusal) as refused:
            self.revalidating()
        self.assertIn("missing, replaced or partial after handoff",
                      str(refused.exception))
        self.assertFalse(os.path.exists(os.path.join(self.home, "inputs")),
                         "the refusal repaired what it was refusing about")

    def test_a_LINE_home_NAMED_workspace_is_still_the_line_layout(self):
        """Review 2026-09-28T05-38-48Z: the classification is by LOCATION, not by name.

        My submitted bytes compared the workspace against its OWN parent's `workspace`
        entry, which is a basename test however it is described -- so a persistent line
        home named `workspace` was called `attempt` and refused against the attempt's own
        object. The reviewer measured it with
        `review_layout_basename_20260928.py`; this is the same hazard inside the suite that
        owns the rule.
        """
        place, roots = self.line_roots()
        workspaces.release_adopted_workspace(roots)
        target = os.path.join(os.path.dirname(place), "workspace")
        os.rename(place, target)
        held = os.lstat(target)
        composed = workspaces.line_assignment_workspace(
            self.storage, self.ATTEMPT, target, (held.st_dev, held.st_ino),
            control=self.store)
        record = self.prepared(composed)
        workspaces.release_adopted_workspace(composed)
        self.assertEqual(record["workspace_layout"], "line",
                         "a line home was classified by its name")
        self.attempt_row()
        self.live_task()
        self.assertEqual(self.revalidating()["workspace"], self.workspace)

    def test_an_UNBOUND_output_root_is_NOT_recorded_as_a_line(self):
        """Review 2026-09-28T05-38-48Z: not every non-attempt path is an authorized line.

        The authority for `line` is the marker `_composed_line_roots` sets AFTER proving
        the reserved namespace and the persisted object identity -- never the observation
        that a path is not the attempt's own object. A hand-built pair over a real
        directory nobody bound is refused rather than recorded.
        """
        elsewhere = os.path.join(self.root, "unbound-output")
        os.makedirs(elsewhere)
        unbound = workspaces.AllocatedRoots(
            {"inputs": os.path.join(self.home, "inputs"),
             "workspace": elsewhere}, workspaces._MINT)
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(unbound)
        self.assertIn("an unbound root is not recorded as a line",
                      str(refused.exception))

    def test_a_CONTRADICTORY_marked_set_is_refused_rather_than_recorded(self):
        """A set marked as a composed line whose workspace IS the attempt's own object."""
        contradictory = workspaces.AllocatedRoots(
            {"inputs": os.path.join(self.home, "inputs"),
             "workspace": self.workspace}, workspaces._MINT, _line=True)
        with self.assertRaises(ContractRefusal) as refused:
            self.prepared(contradictory)
        self.assertIn("contradict themselves", str(refused.exception))

    def test_a_REPLACED_LINE_object_is_refused_by_the_COMPOSED_boundary(self):
        """Where the line identity IS proved, since the revalidation cannot locate it.

        This is the other half of the correction's claim: the line layout skips the
        workspace comparison because `line_assignment_workspace` is what holds the line
        record and compares against it. So the replacement is driven THERE -- same
        reserved path, same name, a different object -- and it refuses.
        """
        place, roots = self.line_roots()
        workspaces.release_adopted_workspace(roots)
        pinned = os.lstat(place)
        # THE SAME PATH, A DIFFERENT OBJECT.
        os.rename(place, place + "-displaced")
        os.mkdir(place)
        self.assertNotEqual(os.lstat(place).st_ino, pinned.st_ino)
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.line_assignment_workspace(
                self.storage, self.ATTEMPT, place,
                (pinned.st_dev, pinned.st_ino), control=self.store)
        self.assertIn("no longer has its persisted object identity",
                      str(refused.exception))

    def test_an_UNSTATED_layout_is_REFUSED_rather_than_compared(self):
        """A record that does not say which layout it is about names unknown operands.

        Every record this manager writes now states it. What must not happen is the
        comparison proceeding on a guess, which is exactly the defect: the operands were
        assumed to be the same object and were not.
        """
        recorded = dict(self.prepared(self.attempt_roots()))
        recorded.pop("workspace_layout", None)
        self.attempt_row()
        self.live_task()
        with mock.patch.object(workspaces, "preparation_completed",
                               return_value=recorded):
            with self.assertRaises(ContractRefusal) as refused:
                self.revalidating()
        self.assertIn("not known to be the same object", str(refused.exception))


class TheORDINARYEndingCompletesWithNoHelperOrItHolds(unittest.TestCase):
    """W285465 review 2026-09-28T06-00-04Z: the ordinary no-helper completion.

    The ending used to normalize both roots under a custody helper and read
    `directory_custody` back out of those receipts. Under
    OWNER-NO-AUTOMATIC-NORMALIZATION-20260928 there is no helper on this path, so the
    evidence changes and the discipline does not: it is ESTABLISHED from observations, it is
    COMMITTED as its own journalled operation bound to this destroy's identity, and the
    ending READS IT BACK rather than trusting the frame that produced it.

    NARROWED, NOT REPLACED: an adapter that can normalize still normalizes, which is why
    every accepted `tests.manager.test_intake` case still ends the way it did.
    """

    def setUp(self):
        from tests.manager import test_intake

        self.intake = test_intake
        self.case = test_intake.ConcreteAuthorityDischargeReceipts()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.case.retained_ready("discard-after-intake")
        self.case.ended()
        # THE ROOTS EXIST, because a real ending's do: the host allocator creates them
        # before the task is admitted and the evidence this ending establishes is ABOUT
        # them. The fixture allocates, so nothing depends on somebody else's product change.
        storage = workspaces.configured_workspace_storage(self.case.store).place
        workspaces.assignment_workspace(
            input_roots.configured_group(self.case.store), storage,
            self.intake.ATTEMPT)
        # THE ROOTS EXIST, because a real ending's do: the host allocator creates them
        # before the task is admitted, and the evidence this ending establishes is ABOUT
        # them. The fixture allocates rather than the product, so nothing here depends on
        # a product change somebody else owns.
        storage = workspaces.configured_workspace_storage(self.case.store).place
        workspaces.assignment_workspace(
            input_roots.configured_group(self.case.store), storage,
            self.intake.ATTEMPT)

    def adapter(self, *, surviving=(), answers=True, custodian=False):
        """The shared `Custodian` double WITHOUT its custody halves.

        Built from the accepted double rather than hand-rolled, so the destroy this ending
        makes is the same crossing every other cleanup case drives; what is REMOVED is the
        normalization act and the custodian image, which is what makes this a deployment
        with no helper. `answers=False` removes the listing capability too -- the adapter
        that CANNOT answer, which must never read as an absence.
        """
        made = self.intake.Custodian(
            destroyed={"state": "absent",
                       "why": "the engine answered that this exact identity "
                              "does not exist",
                       "credentials": {"lifecycle_state": "not-delivered"},
                       "launch": {"lifecycle_state": "not-delivered"}})
        if not custodian:
            made.normalize_directory = None
            made.custodian_image_digest = None
        made.asked = []
        # W285465 review 2026-09-28T06-23-25Z: the shared `Custodian` now CARRIES the
        # listing, so "cannot answer" has to remove it rather than simply not add it.
        made.surviving_helpers = None
        if answers:
            def surviving_helpers(store, *, assignment_id, seconds=None,
                                  reclaim=None):
                made.asked.append(assignment_id)
                return list(surviving)
            made.surviving_helpers = surviving_helpers
        return made

    def pinned_attempt(self):
        """This attempt's row with its workspace OBJECT pinned, as a start requires.

        `tokens.workspace_identity` reads the pinned device and inode rather than asking the
        filesystem, so a generation cannot be taken over an attempt whose boundary was never
        recorded. The fixture pins what the allocator created, which is what a real start
        has already done by the time any of this runs.
        """
        from baton_v12.worker_manager import attempts as manager_attempts

        row = self.case.attempt_row()
        if row.get("workspace_device") is None:
            place, _gid, _recorded = self.custody()._derived_root(
                self.case.store, self.intake.ATTEMPT, "workspace")
            observed = os.lstat(place)
            manager_attempts.pin_boundary_identity(
                self.case.store, attempt_id=self.intake.ATTEMPT,
                source=(observed.st_dev, 1),
                workspace=(observed.st_dev, observed.st_ino))
            row = self.case.attempt_row()
        return row

    @staticmethod
    def custody():
        from baton_v12.worker_manager import custody as _custody

        return _custody

    def ending(self, made):
        from baton_v12.worker_manager.intake import authorize_cleanup

        return authorize_cleanup(
            self.case.store, self.case.port, made,
            attempt_id=self.intake.ATTEMPT,
            retention_policy_digest=self.intake.RETENTION)

    # -- the connected completion ----------------------------------------

    def test_a_NO_HELPER_ending_completes_on_evidence_it_committed(self):
        intake = intake_module()
        made = self.adapter()
        answer = self.ending(made)
        self.assertIn(answer["cleanup"], ("complete", "retained"))
        self.assertIsNone(answer["directory_custody"],
                          "a no-helper ending recorded a custody receipt")
        self.assertNotIn("writer_cessation", answer,
                         "the frozen cleanup.settled contract grew a member")
        self.assertEqual(answer["cleanup"], "retained")
        # THE EVIDENCE IS AN ACT THIS MANAGER CAN SHOW, read back by the destroy identity
        # the receipt names rather than carried inside the receipt.
        ceased = intake.historical_writer_cessation(self.case.store,
                                                    answer["operation"])
        self.assertEqual(ceased["helpers"], [])
        # W285465 under the owner supersession at 294568/294616: the EXECUTION facts, with no
        # output observation recorded at all.
        self.assertEqual(ceased["state"], "absent")
        self.assertIsNotNone(ceased["workspace"])
        self.assertEqual(ceased["container"],
                         self.case.attempt_row()["runtime_id"])
        self.assertEqual(made.asked, [self.intake.ATTEMPT],
                         "the writer absence was not established by asking")

    # -- and every honest refusal ----------------------------------------

    def test_a_deployment_with_NO_LISTING_completes_on_the_CONTAINER(self):
        """W285465 under OWNER-SIMPLE-COMPLETION-20260928, which SUPERSEDES this case.

        It asserted that an adapter which cannot list HOLDS the ending. The owner's selected
        model is that confined Docker cessation PROVES the confined writers stopped, so a
        deployment offering no listing is not thereby uncertain: it completes, and the record
        says which evidence it had.
        """
        answer = self.ending(self.adapter(answers=False))
        self.assertIn(answer["cleanup"], ("complete", "retained"))
        ceased = intake_module().historical_writer_cessation(
            self.case.store, answer["operation"])
        self.assertEqual(ceased["established"], "container-cessation")
        self.assertIsNotNone(ceased["listing"],
                             "the record does not say why no listing was used")
        self.assertEqual(ceased["state"], "absent")

    def test_an_UNREADABLE_listing_ANSWER_is_not_a_confirmed_absence(self):
        """Review 2026-09-28T06-23-25Z: `None` committed a positive cleanup.

        The crossing returned whatever the adapter handed back and the ending read any
        falsy value as "no writers", so a callable answering `None` turned an UNKNOWN into a
        confirmed absence and committed a complete cleanup. The shape is validated at the
        crossing now: only a list or tuple of mappings is an observation, and an EMPTY one
        of those is the only thing that means none survive.
        """
        for answer in (None, False, 0, "", "none", {}, {"helper_identity": "x"},
                       ["baton-custody-" + "a" * 32], [None], (None,)):
            with self.subTest(answered=repr(answer)):
                case = type(self)()
                case.setUp()
                self.addCleanup(case.doCleanups)
                made = case.adapter()
                made.surviving_helpers = lambda *a, **k: answer
                # W285465 under OWNER-SIMPLE-COMPLETION-20260928: an unreadable answer is
                # still never read as "no writers" -- that was the defect and it stays fixed
                # -- but it no longer HOLDS the ending, because the cessation this completion
                # rests on is the exact container's. What the record must not do is claim the
                # listing established anything, so it says exactly what happened.
                answered = case.ending(made)
                self.assertIn(answered["cleanup"], ("complete", "retained"))
                ceased = intake_module().historical_writer_cessation(
                    case.case.store, answered["operation"])
                self.assertEqual(ceased["established"], "container-cessation")
                self.assertIn("not an observation this manager can read",
                              ceased["listing"])
                self.assertEqual(ceased["helpers"], [])

    def test_a_GENUINELY_EMPTY_observation_is_still_a_positive_absence(self):
        """The other half, so the validation above cannot pass by refusing everything."""
        for answer in ([], ()):
            with self.subTest(answered=repr(answer)):
                case = type(self)()
                case.setUp()
                self.addCleanup(case.doCleanups)
                made = case.adapter()
                made.surviving_helpers = lambda *a, **k: answer
                self.assertIn(case.ending(made)["cleanup"],
                              ("complete", "retained"))

    def test_a_CONFIGURED_custodian_is_not_authority_to_launch_one(self):
        """OWNER-NO-AUTOMATIC-NORMALIZATION-20260928, as review 06-23-25Z reads it.

        My previous cut took the ruling to remove only the REQUIREMENT for a custodian, and
        kept normalizing where one was configured. The ruling requires zero automatic
        launches on this path, so a configured capability changes nothing: the ending
        establishes and commits, and no helper is called.
        """
        made = self.adapter(custodian=True)
        # `create=True` SINCE 296667, when the dead helper was removed after the caller
        # verification the review at 296645 asked for. The patch is kept rather than deleted
        # for the reason the reviewer's successor probe keeps it: patching a name that no
        # longer exists still proves that nothing on this path resolves it dynamically, and
        # the day a normalization helper comes back under this name the case fires again.
        with mock.patch.object(intake_module(), "_normalized", create=True,
                               side_effect=AssertionError(
                                   "a helper was launched on the selected path")):
            answer = self.ending(made)
        self.assertIn(answer["cleanup"], ("complete", "retained"))
        self.assertEqual(made.normalized, [])
        self.assertIsNone(answer["directory_custody"])

    def test_a_PRESENTED_cessation_is_never_authority_for_the_transfer(self):
        """W285465 review 2026-09-28T07-26-54Z: my previous positive enshrined the defect.

        That case handed `admit_cleanup` a mapping naming a live bound container and asserted
        the admission SUCCEEDED. The reviewer's `review_unproved_transfer_20260928.py` showed
        what that meant: no destroy, no listing and no committed cessation anywhere, and
        ownership moved on a caller's word. It is withdrawn and replaced by these.

        A presented cessation is refused outright now, whatever it says.
        """
        held = self.pinned_attempt()
        settlement = {"operation": "cleanup-probe", "signature": "probe",
                      "incarnation": self.case.store.incarnation}
        for name, offered in (
                ("a matching live container",
                 {"container": held["runtime_id"], "stopped": True, "helpers": []}),
                ("an empty document", {}),
                ("not a document", "stopped")):
            with self.subTest(cessation=name):
                with self.assertRaises(ContractRefusal) as refused:
                    workspaces.admit_cleanup(
                        self.case.store, self.intake.ATTEMPT, settlement,
                        "a probe cleanup", cessation=offered)
                self.assertIn("never by evidence a caller carries",
                              str(refused.exception))

    def test_a_LIVE_generation_with_NO_committed_cessation_keeps_the_roots(self):
        """The transfer's operand is an operation, and an operation with no record is nothing.

        A real acquired, launched and bound generation stands over this attempt's workspace
        and nothing has ceased. The admission names an operation this manager committed no
        cessation under, so the generation goes on owning the roots.
        """
        from baton_v12.worker_manager import tokens

        held = self.pinned_attempt()
        domain = tokens.domain_of("workspace", tokens.workspace_identity(held))
        token = tokens.acquire(self.case.store, domain,
                               operation=f"start:{self.intake.ATTEMPT}",
                               execution=self.intake.ATTEMPT,
                               attempt=self.intake.ATTEMPT)
        tokens.journal_launch(self.case.store, token, token["operation"])
        tokens.bind_container(self.case.store, token, held["runtime_id"],
                              launch=token["operation"])
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_cleanup(
                self.case.store, self.intake.ATTEMPT,
                {"operation": "cleanup-with-no-establishment",
                 "signature": "probe",
                 "incarnation": self.case.store.incarnation},
                "a probe cleanup")
        self.assertIn("has not been returned", str(refused.exception))

    def test_a_COMMITTED_cessation_for_ANOTHER_subject_moves_nothing(self):
        """Every member of the committed record is compared, not merely its presence.

        The ending's real establishment is committed here, and then the SUBJECT is changed
        underneath it: another attempt, a runtime this manager never bound to the standing
        generation, a surviving writer, a runtime that was not absent. Each leaves the
        generation owning the roots.
        """
        from baton_v12.worker_manager import intake, tokens

        held = self.pinned_attempt()
        domain = tokens.domain_of("workspace", tokens.workspace_identity(held))
        token = tokens.acquire(self.case.store, domain,
                               operation=f"start:{self.intake.ATTEMPT}",
                               execution=self.intake.ATTEMPT,
                               attempt=self.intake.ATTEMPT)
        tokens.journal_launch(self.case.store, token, token["operation"])
        tokens.bind_container(self.case.store, token, held["runtime_id"],
                              launch=token["operation"])
        operation = {"operation_id": "cleanup-established"}
        real = intake._record_writer_cessation(
            self.case.store, self.adapter(), self.intake.ATTEMPT,
            attempt=held, operation=operation,
            observed={"state": "absent",
                      "why": "the engine answered that this exact identity does "
                             "not exist"})
        settlement = {"operation": operation["operation_id"],
                      "signature": "probe",
                      "incarnation": self.case.store.incarnation}
        # FIRST THE POSITIVE, so the negatives below cannot pass by refusing everything: the
        # committed establishment moves ownership, and the generation is STILL OUTSTANDING
        # afterwards -- which is what leaves no instant with nobody owning the roots.
        admitted = workspaces.admit_cleanup(
            self.case.store, self.intake.ATTEMPT, settlement, "a probe cleanup")
        self.assertIsNotNone(admitted.get("ordinal"))
        self.assertTrue(list(tokens.outstanding(self.case.store, domain)),
                        "the admission ended the generation instead of taking over")
        identity = intake._writer_cessation_id(operation)
        for name, changed in (
                ("another attempt", {"attempt_id": "another-attempt"}),
                ("a container this manager never bound",
                 {"container": "runtime-somebody-else"}),
                ("a surviving writer",
                 {"helpers": [{"helper_identity": "baton-custody-x"}]}),
                ("a runtime that was not absent", {"state": "quiescent"})):
            with self.subTest(changed=name):
                case = type(self)()
                case.setUp()
                self.addCleanup(case.doCleanups)
                theirs = case.pinned_attempt()
                mine = tokens.domain_of("workspace",
                                        tokens.workspace_identity(theirs))
                one = tokens.acquire(case.case.store, mine,
                                     operation=f"start:{case.intake.ATTEMPT}",
                                     execution=case.intake.ATTEMPT,
                                     attempt=case.intake.ATTEMPT)
                tokens.journal_launch(case.case.store, one, one["operation"])
                tokens.bind_container(case.case.store, one,
                                      theirs["runtime_id"],
                                      launch=one["operation"])
                intake._record_writer_cessation(
                    case.case.store, case.adapter(), case.intake.ATTEMPT,
                    attempt=theirs, operation=operation,
                    observed={"state": "absent", "why": "the engine answered"})
                case.case.store._connection.execute(
                    "UPDATE operations SET result = ? WHERE operation_id = ?",
                    (json.dumps(dict(real, **changed)), identity))
                with self.assertRaises(ContractRefusal) as refused:
                    workspaces.admit_cleanup(
                        case.case.store, case.intake.ATTEMPT, settlement,
                        "a probe cleanup")
                self.assertIn("has not been returned", str(refused.exception))

    def governed(self, case=None, operation=None):
        """A real live workspace generation over this attempt, acquired, launched and bound.

        The three acts a governed start performs, in that order, so the guard below has a
        genuine schedule to arbitrate against rather than a fixture's assertion.
        """
        from baton_v12.worker_manager import tokens

        case = case or self
        held = case.pinned_attempt()
        domain = tokens.domain_of("workspace", tokens.workspace_identity(held))
        token = tokens.acquire(
            case.case.store, domain,
            operation=operation or f"start:{case.intake.ATTEMPT}",
            execution=case.intake.ATTEMPT, attempt=case.intake.ATTEMPT)
        tokens.journal_launch(case.case.store, token, token["operation"])
        tokens.bind_container(case.case.store, token, held["runtime_id"],
                              launch=token["operation"])
        return held, domain, token

    def established(self, case=None, operation_id="cleanup-established"):
        """The ending's own committed establishment, through the product's own writer."""
        from baton_v12.worker_manager import intake

        case = case or self
        return intake._record_writer_cessation(
            case.case.store, case.adapter(), case.intake.ATTEMPT,
            attempt=case.case.attempt_row(),
            operation={"operation_id": operation_id},
            observed={"state": "absent",
                      "why": "the engine answered that this exact identity does "
                             "not exist"})

    @staticmethod
    def settlement(store, operation_id):
        return {"operation": operation_id, "signature": "probe",
                "incarnation": store.incarnation}

    def test_a_STALE_generation_cessation_cannot_move_a_LATER_one(self):
        """W285465 review 2026-09-28T07-47-09Z: container equality is not a schedule.

        The runtime identity is reused across generations of one attempt, so an establishment
        made while generation 1 was standing must not authorize a transfer away from
        generation 2. The record names the generation and the start it saw end, and both are
        compared against the journal's account of the generation actually being arbitrated.
        """
        from baton_v12.worker_manager import tokens

        held, domain, first = self.governed()
        stale = self.established()
        self.assertEqual(stale["generation"], first["generation"])
        self.assertEqual(stale["launch"], first["operation"])
        # THE FIRST GENERATION ENDS and a SECOND takes the same workspace with the SAME
        # container -- which is what makes container equality insufficient.
        tokens.returned(self.case.store, first,
                        cessation={"domain": first["domain"],
                                   "generation": first["generation"],
                                   "launch": first["operation"],
                                   "container": held["runtime_id"],
                                   "stopped": True, "helpers": []})
        second = tokens.acquire(self.case.store, domain,
                                operation="start:again",
                                execution=self.intake.ATTEMPT,
                                attempt=self.intake.ATTEMPT)
        tokens.journal_launch(self.case.store, second, second["operation"])
        tokens.bind_container(self.case.store, second, held["runtime_id"],
                              launch=second["operation"])
        self.assertNotEqual(second["generation"], stale["generation"])
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_cleanup(
                self.case.store, self.intake.ATTEMPT,
                self.settlement(self.case.store, "cleanup-established"),
                "a probe cleanup")
        self.assertIn("has not been returned", str(refused.exception))

    def test_a_cessation_under_a_FOREIGN_operation_moves_nothing(self):
        """The transfer's operand is the operation the admission commits under.

        A genuine establishment exists -- for a DIFFERENT destroy -- and an admission naming
        its own operation finds no record at its own identity.
        """
        self.governed()
        self.established(operation_id="somebody-elses-destroy")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_cleanup(
                self.case.store, self.intake.ATTEMPT,
                self.settlement(self.case.store, "my-own-destroy"),
                "a probe cleanup")
        self.assertIn("has not been returned", str(refused.exception))

    def test_the_TRANSFER_authorizes_ONE_settlement_and_not_a_window(self):
        """A proved cessation is not a standing exemption for whoever asks next.

        MEASURED, and it corrected my own expectation: I expected the competitor to be
        refused by the first ADMISSION. It is refused earlier than that, by the GENERATION --
        because a competing settlement names its own operation, and the transfer is
        authorized only by the committed cessation at the operation the admission commits
        under. So the second actor never reaches the admission conflict at all, which is a
        stronger property than the one I went looking for.
        """
        self.governed()
        self.established()
        settlement = self.settlement(self.case.store, "cleanup-established")
        first = workspaces.admit_cleanup(
            self.case.store, self.intake.ATTEMPT, settlement, "a probe cleanup")
        self.assertIsNotNone(first.get("ordinal"))
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_cleanup(
                self.case.store, self.intake.ATTEMPT,
                self.settlement(self.case.store, "another-cleanup"),
                "a competing cleanup")
        self.assertIn("has not been returned", str(refused.exception))
        self.assertIn("generation 1", str(refused.exception))

    def test_TWO_ELIGIBLE_settlements_leave_exactly_ONE_owner(self):
        """W285465 review 2026-09-28T07-55-48Z: first-winner between two ELIGIBLE acts.

        The earlier control proved a competitor WITHOUT its own committed cessation fails
        before the admission lock -- which shows there is no broad exemption, and not who
        wins between two acts that are each entitled to transfer. So both are made eligible
        here: two destroy operations over this attempt, each with its OWN committed
        establishment naming the same standing generation and start.

        THE SCHEDULE IS DETERMINISTIC AND WITHIN ONE INSTANCE, which is what the review asks
        for and all this needs: one manager, one connection, one write transaction at a time.
        An admission cannot be nested inside another's `BEGIN IMMEDIATE` here at all, so the
        order is simply which one reaches the journal first -- and the loser must be refused
        BY THE WINNER'S ADMISSION rather than by the generation, because the generation would
        have let either of them through.
        """
        self.governed()
        self.established(operation_id="destroy-a")
        self.established(operation_id="destroy-b")
        first = self.settlement(self.case.store, "destroy-a")
        second = self.settlement(self.case.store, "destroy-b")
        won = workspaces.admit_cleanup(
            self.case.store, self.intake.ATTEMPT, first, "the first cleanup")
        with self.assertRaises(ContractRefusal) as refused:
            workspaces.admit_cleanup(
                self.case.store, self.intake.ATTEMPT, second,
                "the second cleanup")
        # BY THE WINNER, NAMED. Not "has not been returned": the generation was eligible to
        # be transferred away from by EITHER settlement, so a generation refusal here would
        # mean the exclusion had been decided by the wrong thing.
        self.assertIn("was admitted under operation 'destroy-a'",
                      str(refused.exception))
        self.assertNotIn("has not been returned", str(refused.exception))
        # AND EXACTLY ONE OWNER STANDS.
        standing = workspaces.standing_cleanup(self.case.store,
                                               self.intake.ATTEMPT)
        self.assertEqual([one for one, _record in standing], [won["ordinal"]])
        # THE WINNER'S OWN EXACT RETRY STILL ADOPTS, and the loser's retry still does not.
        self.assertEqual(
            workspaces.admit_cleanup(
                self.case.store, self.intake.ATTEMPT, first,
                "the first cleanup")["ordinal"],
            won["ordinal"])
        with self.assertRaises(ContractRefusal):
            workspaces.admit_cleanup(
                self.case.store, self.intake.ATTEMPT, second,
                "the second cleanup")

    def test_an_INTERRUPTED_ending_RETRIES_into_its_own_admission(self):
        """The same settlement adopts what it already admitted; a competitor still cannot.

        A crash between the admission and the terminal commit leaves the admission standing.
        The retry -- the same operation, the same operands -- must adopt it rather than
        contend with itself, and a DIFFERENT settlement must still be refused.
        """
        self.governed()
        self.established()
        settlement = self.settlement(self.case.store, "cleanup-established")
        first = workspaces.admit_cleanup(
            self.case.store, self.intake.ATTEMPT, settlement, "a probe cleanup")
        again = workspaces.admit_cleanup(
            self.case.store, self.intake.ATTEMPT, settlement, "a probe cleanup")
        self.assertEqual(again["ordinal"], first["ordinal"],
                         "the retry took a second ownership instead of adopting its own")
        with self.assertRaises(ContractRefusal):
            workspaces.admit_cleanup(
                self.case.store, self.intake.ATTEMPT,
                dict(settlement, signature="a different probe"),
                "a competing cleanup")

    # -- the root-provenance audit review 2026-09-28T07-55-48Z holds open -----

    def expected(self, which):
        """Where this attempt's root WOULD be, asked through the product's own composer."""
        from baton_v12.worker_manager import intake

        return intake._expected_root(self.case.store, self.intake.ATTEMPT, which)

    def establishment(self):
        """What the ending's establishment records about the roots, or the refusal it earns."""
        from baton_v12.worker_manager import intake

        return intake._output_root_identities(self.case.store,
                                              self.intake.ATTEMPT)

    def test_the_EXPECTED_root_is_composed_from_configuration_and_the_attempt(self):
        """The fallback path's provenance, asserted rather than assumed.

        `_expected_root` exists so an evidenced removal stays distinguishable from a failure
        to look, and the review is right that it needs its own provenance stated: it composes
        from the manager's CONFIGURED workspace store and the attempt identity, with
        `custody`'s own layout, and from nothing a caller supplies.
        """
        from baton_v12.worker_manager import custody as _custody, workspaces as _w

        storage = _w.configured_workspace_storage(self.case.store).place
        self.assertEqual(
            self.expected("workspace"),
            os.path.join(storage, self.intake.ATTEMPT, "workspace"))
        self.assertEqual(
            self.expected("result"),
            os.path.join(storage, self.intake.ATTEMPT, "workspace",
                         f"result-{self.intake.ATTEMPT}"))
        # AND IT AGREES WITH THE VALIDATING DERIVATION while the roots are real, which is
        # what makes the fallback the SAME object rather than a second guess at it.
        for which in ("result", "workspace"):
            self.assertEqual(
                self.expected(which),
                _custody._derived_root(self.case.store, self.intake.ATTEMPT,
                                       which)[0])

    def test_a_MISSING_root_is_an_EVIDENCED_absence_and_the_others_are_not(self):
        """One root gone is exactly the interrupted-removal state, and it is reported as one."""
        os.rmdir(self.expected("result"))
        observed = self.establishment()
        self.assertIsNone(observed["result"])
        self.assertIsNotNone(observed["workspace"],
                             "a present root was reported as gone")

    def test_an_INTERRUPTED_removal_leaves_BOTH_absent_and_still_completes(self):
        from baton_v12.worker_manager import workspaces as _w

        _w.discard_execution_roots(
            _w.configured_workspace_storage(self.case.store).place,
            self.intake.ATTEMPT, control=self.case.store)
        self.assertEqual(self.establishment(),
                         {"result": None, "workspace": None})
        # AND THE ENDING FINISHES over roots that are gone, which is the whole reason the
        # evidenced absence exists.
        self.assertIn(self.ending(self.adapter())["cleanup"],
                      ("complete", "retained"))

    def test_a_SYMLINK_at_a_root_is_never_read_as_absence_or_as_the_object(self):
        """A link is the substitution case, and it must refuse rather than resolve.

        `_expected_root` composes a path, so a link put there would be followed by anything
        that resolved it. Nothing here resolves it: the validating derivation refuses a link,
        and the fallback's `lstat` answers about the LINK -- which exists -- so the
        establishment refuses instead of recording either an absence or the target's identity.
        """
        target = os.path.join(tempfile.mkdtemp(prefix="v12-foreign-"),
                              "somebody-elses-result")
        os.makedirs(target, exist_ok=True)
        place = self.expected("result")
        os.rmdir(place)
        os.symlink(target, place)
        with self.assertRaises(ContractRefusal) as refused:
            self.establishment()
        self.assertIn("result", str(refused.exception))
        self.assertTrue(os.path.islink(place),
                        "the refusal disturbed the link it refused about")

    def test_a_FOREIGN_object_at_a_root_refuses_rather_than_being_adopted(self):
        """Not a directory this manager created: the establishment cannot account for it."""
        place = self.expected("result")
        os.rmdir(place)
        with open(place, "w", encoding="utf-8") as made:
            made.write("not a directory\n")
        with self.assertRaises(ContractRefusal) as refused:
            self.establishment()
        self.assertIn("present and this manager cannot account for it",
                      str(refused.exception))
        self.assertTrue(os.path.isfile(place),
                        "the refusal removed what it refused about")

    def test_an_UNDERIVABLE_store_is_not_an_absence_either(self):
        """With no configured workspace store there is no expected object to ask about."""
        from baton_v12.worker_manager import custody as _custody

        with mock.patch.object(_custody, "_derived_root",
                               side_effect=ContractRefusal(
                                   "refused", "precondition", "no store")):
            with mock.patch.object(intake_module(), "_expected_root",
                                   return_value=None):
                with self.assertRaises(ContractRefusal) as refused:
                    self.establishment()
        self.assertIn("cannot derive", str(refused.exception))

    def storage_place(self):
        return workspaces.configured_workspace_storage(self.case.store).place

    def substituted(self, place, target=None):
        """Move `place` aside and put a link to a foreign empty directory at its path."""
        made = target or tempfile.mkdtemp(prefix="v12-substituted-")
        os.rename(place, place + "-original")
        os.symlink(made, place)
        return made

    def test_a_LINKED_HOME_does_not_prove_the_roots_absent(self):
        """W285465 review 2026-09-28T08-03-34Z: `lstat` follows every component but the last.

        With the attempt home renamed aside and a symlink to an empty foreign directory at
        its path, an `lstat` of `<home>/workspace` resolves THROUGH that link and answers
        ENOENT inside somebody else's tree -- and my previous cut recorded BOTH roots absent
        from it. The direct result-root symlink case could not catch this, because there the
        missing entry was the last component. The ancestors are authenticated now.
        """
        home = os.path.join(self.storage_place(), self.intake.ATTEMPT)
        target = self.substituted(home)
        with self.assertRaises(ContractRefusal) as refused:
            self.establishment()
        self.assertIn("is a symbolic link", str(refused.exception))
        self.assertIn("another tree", str(refused.exception))
        # AND NOTHING WAS DISTURBED, on either side of the link.
        self.assertTrue(os.path.islink(home))
        self.assertTrue(os.path.isdir(home + "-original"))
        self.assertEqual(os.listdir(target), [],
                         "the refusal wrote into the foreign directory")
        self.assertTrue(
            os.path.isdir(os.path.join(home + "-original", "workspace")),
            "the refusal disturbed the real workspace it never reached")

    def test_a_LINKED_WORKSPACE_does_not_prove_the_result_root_absent(self):
        """The same hole one level down: the result root's parent."""
        target = self.substituted(self.expected("workspace"))
        with self.assertRaises(ContractRefusal) as refused:
            self.establishment()
        self.assertIn("is a symbolic link", str(refused.exception))
        self.assertEqual(os.listdir(target), [])

    def test_a_FILE_where_a_PARENT_should_be_is_refused_too(self):
        """Not only links: anything that is not a directory this manager prepared.

        MEASURED, and the refusal arrives one step earlier than I expected: a file at the
        home means the expected root's own `lstat` raises `NotADirectoryError` rather than
        `ENOENT`, so the "could not be observed" branch answers before the ancestor walk is
        reached. Both are the same verdict -- UNKNOWN, hold, disturb nothing -- and the case
        asserts what actually happens rather than the sentence I predicted.
        """
        home = os.path.join(self.storage_place(), self.intake.ATTEMPT)
        os.rename(home, home + "-original")
        with open(home, "w", encoding="utf-8") as made:
            made.write("not a directory\n")
        with self.assertRaises(ContractRefusal) as refused:
            self.establishment()
        self.assertIn("an absence nobody has evidenced is not one this ending may record",
                      str(refused.exception))
        self.assertIn("NotADirectoryError", str(refused.exception))
        self.assertTrue(os.path.isfile(home),
                        "the refusal removed what it refused about")
        # AND THE ANCESTOR WALK ITSELF STILL ANSWERS about this tree, asked directly, so the
        # rule is covered even though the ending refuses before consulting it.
        from baton_v12.worker_manager import intake

        self.assertIn(
            "is not a directory this manager prepared",
            intake._unauthentic_ancestor(self.case.store,
                                         self.expected("workspace")))

    def test_a_LINKED_PARENT_does_not_reach_the_ENDING_at_all(self):
        """W285465 under the owner supersession at 294568/294616: SUPERSEDED, and honestly so.

        This asserted that a substituted parent HOLDS the ending. It held because completion
        walked the roots, and completion no longer walks anything -- so a link left at the
        attempt home does not touch the ending, which observes the execution and preserves the
        workspace as is. The ancestor-authentication rule itself is unchanged and still covered
        by the reader's own cases above, where the walk is actually performed.

        What this case holds onto now is the property that matters either way: the ending
        disturbs NOTHING on either side of the substitution.
        """
        home = os.path.join(self.storage_place(), self.intake.ATTEMPT)
        target = self.substituted(home)

        answer = self.ending(self.adapter())

        self.assertEqual(answer["cleanup"], "retained")
        self.assertTrue(os.path.islink(home))
        self.assertTrue(os.path.isdir(home + "-original"))
        self.assertEqual(os.listdir(target), [],
                         "the ending wrote into the foreign directory")

    def test_a_GENUINE_removal_is_STILL_an_absence_with_authentic_parents(self):
        """The negative control for all of the above, through the real removal.

        `discard_execution_roots` leaves the home standing and both roots gone, so every
        ancestor is either a real directory or absent -- and the absence is still evidenced,
        which is what keeps the accepted post-removal retry working.
        """
        from baton_v12.worker_manager import workspaces as _w

        _w.discard_execution_roots(self.storage_place(), self.intake.ATTEMPT,
                                   control=self.case.store)
        self.assertEqual(self.establishment(),
                         {"result": None, "workspace": None})
        self.assertIn(self.ending(self.adapter())["cleanup"],
                      ("complete", "retained"))

    def test_the_RELEASE_preserves_the_OUTPUT_and_the_WRITER_is_refused(self):
        """W285465 reviews 14-45-46Z and 16-06-20Z: the composed case, and the DEFECT it found.

        My first version of this case ran the composition, saw a second writer admitted, and
        concluded that protecting the retained bytes would be new scope. THE REVIEW SUPERSEDED
        THAT and it was right to: DESIGN ART-7 requires material offered for inspection to be
        preserved from writable reuse, which the PLAN already pinned. What the composition
        found was not the absence of scope, it was the defect -- every exclusion in
        `workspaces` reads an OUTSTANDING ACT, and a settled ending leaves none, so nothing
        stood over the tree. `_offered_material_refusal` is the correction and this case is
        now its regression.

        THE TWO OBLIGATIONS ARE SEPARATE, which is the reviewer's phrasing and the right one:

          * EXACT RELEASE. The ending returns the execution generation -- read from the
            ledger -- so the resource is not held hostage by a finished attempt, and the
            allocator still answers the same two roots, because the import and inspection
            paths re-derive them to READ the preserved material.
          * STORAGE PROTECTION. The act that means a writer is about to run inside those
            roots, `admit_preparation`, REFUSES while the output stands offered, and the
            refusal names the one thing that resolves it: ending the offer.

        Both are asserted here, and the bytes and mtime are checked after every act, because
        a refusal that arrived too late to matter would pass a test about refusals.
        """
        from baton_v12.worker_manager import attempts, intake, tokens

        # THE GENERATION IS RESERVED UNDER THE OPERATION THE ENDING RESOLVES -- the attempt's
        # one derived start identity, not a fixture label. A generation taken under any other
        # operation is not the one a real start holds and the release refuses it; that is the
        # behaviour, and getting it wrong is how I first wrote this case.
        _held, domain, _token = self.governed(
            operation=attempts._start_operation_id(self.pinned_attempt()))
        root = self.custody()._derived_root(self.case.store,
                                           self.intake.ATTEMPT, "result")[0]
        os.makedirs(root, exist_ok=True)
        kept = pathlib.Path(root) / "result.txt"
        kept.write_bytes(b"the worker's own output\n")
        written = kept.stat().st_mtime_ns

        # THE ENDING UNDER ITS PRODUCTION GOVERNANCE. Every other case in this class passes no
        # `govern`, so none of them reaches `_released` at all -- this is the suite's first
        # coverage of the release itself.
        answer = intake.authorize_cleanup(
            self.case.store, self.case.port, self.adapter(),
            attempt_id=self.intake.ATTEMPT,
            retention_policy_digest=self.intake.RETENTION,
            govern=tokens.workspace_governance())
        self.assertEqual(answer["cleanup"], "retained")
        self.assertEqual(tokens.outstanding(self.case.store, domain), [],
                         "the ending did not release the execution it proved free")

        # THE WRITABLE REUSE ATTEMPT, over the same storage and the same assignment.
        storage = workspaces.configured_workspace_storage(self.case.store).place
        reused = workspaces.assignment_workspace(
            input_roots.configured_group(self.case.store), storage,
            self.intake.ATTEMPT, control=self.case.store)
        # THE SAME writable root the preserved output sits under, which is what makes this a
        # reuse of that tree rather than a fresh allocation somewhere else.
        self.assertEqual(reused["workspace"], os.path.dirname(root))

        # A SECOND GENERATION IS GRANTABLE, which is the honest reading of a RELEASED
        # resource -- and is exactly why it cannot be the protection. The guard is the one
        # below; reacquiring a token proves the release happened, nothing more.
        second = tokens.acquire(self.case.store, domain, operation="start:reuse",
                                execution=self.intake.ATTEMPT,
                                attempt=self.intake.ATTEMPT)
        self.assertEqual(second["generation"], 2)

        # AND THE WRITER ADMISSION REFUSES, naming the offered material and the resolution.
        row = self.case.attempt_row()
        self.assertEqual((row["output"], row["cleanup"]), ("sealed", "retained"))
        with self.assertRaises(ContractRefusal) as caught:
            workspaces.admit_preparation(
                self.case.store, self.intake.ATTEMPT,
                "a second preparation of this attempt",
                execution=self.intake.ATTEMPT)
        spoken = caught.exception.message
        self.assertIn("preserved and offered for inspection", spoken)
        self.assertIn("'sealed'", spoken)
        self.assertIn("discarded", spoken)

        # THROUGH EVERY ACT THE MATERIAL IS UNTOUCHED -- bytes and mtime, from the file.
        self.assertTrue(kept.exists(), "the reuse path removed retained material")
        self.assertEqual(kept.read_bytes(), b"the worker's own output\n")
        self.assertEqual(kept.stat().st_mtime_ns, written)

    def test_a_DISCARD_disposition_still_leaves_the_workspace_bytes(self):
        """W285465 review 2026-09-28T16-40-29Z, and the reviewer is right about the gap.

        `tests/tools/test_dogfood_retry_engine.py` asserts a discard's PUBLISHED COPY is
        removed; it says nothing about the attempt's own workspace, and its prose must not
        borrow an assertion it does not make. Nor may that claim rest on a live engine, which
        the recorded selection forbids. So the workspace claim gets its own DETERMINISTIC
        case, here, where the fixture's committed disposition already IS a discard --
        `retained_ready("discard-after-intake")` in this class's `setUp`.

        THE THREE FACTS, each read from its own owner: the committed retention says discard,
        the ending says `retained`, and the file the worker wrote has the SAME BYTES and the
        same mtime afterwards. That is what "completion no longer deletes" means for the one
        tree an operator would look in.
        """
        from baton_v12.worker_manager import attempts, intake, tokens

        held, _domain, _token = self.governed(
            operation=attempts._start_operation_id(self.pinned_attempt()))
        del held
        root = self.custody()._derived_root(self.case.store,
                                           self.intake.ATTEMPT, "workspace")[0]
        wrote = pathlib.Path(root) / "worker-wrote-this.txt"
        wrote.write_bytes(b"bytes the discard does not take\n")
        written = wrote.stat().st_mtime_ns

        # THE COMMITTED DISPOSITION, from the manager's own record rather than the fixture's
        # argument -- an edited record could otherwise make this case prove nothing.
        decided = intake.retentions_of(self.case.store, self.intake.ATTEMPT)
        self.assertTrue(decided, "the fixture committed no retention decision")
        self.assertEqual({one["disposition"] for one in decided},
                         {"discard-after-intake"})

        answer = intake.authorize_cleanup(
            self.case.store, self.case.port, self.adapter(),
            attempt_id=self.intake.ATTEMPT,
            retention_policy_digest=self.intake.RETENTION,
            govern=tokens.workspace_governance())

        self.assertEqual(answer["cleanup"], "retained")
        self.assertTrue(wrote.exists(),
                        "a discard disposition removed the attempt's workspace material")
        self.assertEqual(wrote.read_bytes(), b"bytes the discard does not take\n")
        self.assertEqual(wrote.stat().st_mtime_ns, written)
        self.assertTrue(os.path.isdir(root), "the workspace root itself is gone")

    def test_an_OFFER_THAT_ENDED_does_not_refuse_the_next_writer(self):
        """The control, because a refusal that never lifts is a worse defect than the one
        `_offered_material_refusal` corrects -- `_journal_holds` carries that exact scar for
        cleared custody episodes.

        The offer is ENDED the only way the axis allows, `sealed` -> `discarded`, through the
        product's own transition rather than a written column, and the admission that was
        refused a moment ago is then granted.
        """
        from baton_v12.worker_manager import attempts, intake, tokens

        held, _domain, _token = self.governed(
            operation=attempts._start_operation_id(self.pinned_attempt()))
        del held
        intake.authorize_cleanup(
            self.case.store, self.case.port, self.adapter(),
            attempt_id=self.intake.ATTEMPT,
            retention_policy_digest=self.intake.RETENTION,
            govern=tokens.workspace_governance())
        with self.assertRaises(ContractRefusal):
            workspaces.admit_preparation(self.case.store, self.intake.ATTEMPT,
                                         "a writer while the offer stands")

        # THE OFFER ENDS THROUGH THE AXIS'S OWN WRITER, `observe`, which is what
        # `intake` and `output` use to move this axis. No new public operation is invented
        # here: the review was explicit that correcting the observer does not select a later
        # deletion workflow, and THAT IS A REAL LIMITATION recorded in the dossier -- today
        # no product path reaches `discarded`, so the resolution this refusal names is one an
        # operator cannot yet perform. The refusal is still right; the missing disposal is a
        # separate obligation and not mine to invent.
        from baton_v12.worker_manager import observe

        observe(self.case.store, attempt_id=self.intake.ATTEMPT, axis="output",
                value="discarded")

        self.assertEqual(self.case.attempt_row()["output"], "discarded")
        holding = workspaces.admit_preparation(
            self.case.store, self.intake.ATTEMPT,
            "a writer after the offer ended")
        self.assertIsNotNone(holding)

    def test_a_SURVIVING_writer_refuses_and_leaves_the_roots(self):
        survivor = {"helper_identity": "baton-custody-" + "a" * 32,
                    "why": "the engine listed this helper as running"}
        with self.assertRaises(ContractRefusal) as refused:
            self.ending(self.adapter(surviving=[survivor]))
        self.assertIn("still survives", str(refused.exception))
        self.assertEqual(self.case.attempt_row()["cleanup"], "pending")

    def test_the_ENDING_OBSERVES_NO_OUTPUT_AT_ALL_and_preserves_it(self):
        """W285465 under the owner supersession at 294568/294616, which supersedes this case
        for the third time and finally removes its subject.

        It asserted a refusal, then a durable access error. The owner's final target removes ALL
        proactive output and permission checking from completion: after confirmed termination the
        workspace is PRESERVED AS IS and output validation belongs to the consumer that selects
        it. So an unreadable tree changes nothing about the ending -- and the case proves the
        absence of the check by making the observation itself RAISE if it is attempted.
        """
        from baton_v12.worker_manager import custody as _custody, intake

        root = _custody._derived_root(self.case.store, self.intake.ATTEMPT,
                                      "result")[0]
        os.makedirs(root, exist_ok=True)
        # A REAL BYTE THE ENDING MUST NOT TOUCH, written before the mode closes the directory.
        kept = pathlib.Path(root) / "result.txt"
        kept.write_bytes(b"the worker's own output\n")
        written = kept.stat().st_mtime_ns
        os.chmod(root, 0o700)
        before = os.lstat(root)

        def refuse_to_scan(*arguments, **named):
            raise AssertionError("completion observed the output")

        with mock.patch.object(intake, "inaccessible_output", refuse_to_scan), \
                mock.patch.object(intake, "_output_root_identities",
                                  refuse_to_scan):
            answer = self.ending(self.adapter())

        self.assertEqual(answer["cleanup"], "retained")
        ceased = intake.historical_writer_cessation(self.case.store,
                                                    answer["operation"])
        self.assertEqual(ceased["state"], "absent")
        self.assertNotIn("output", ceased)
        self.assertIsNotNone(ceased["workspace"])
        # AND NOTHING WAS TOUCHED: same object, same mode, still there.
        self.assertTrue(os.path.isdir(root), "the ending removed the output")
        self.assertEqual(os.lstat(root).st_ino, before.st_ino)
        self.assertEqual(stat.S_IMODE(os.lstat(root).st_mode), 0o700)
        # AND THE BYTES, which review 2026-09-28T14-34-52Z is right that an inode and a mode do
        # not cover: an object can keep both while its content is rewritten. The file is written
        # before the ending and read back after it.
        self.assertEqual(kept.read_bytes(), b"the worker's own output\n")
        self.assertEqual(kept.stat().st_mtime_ns, written)

    def test_the_ACCESSIBLE_ending_records_accessible_and_replays_one_act(self):
        """The positive beside the durable error, and the replay of one establishment.

        W285465 under OWNER-SIMPLE-COMPLETION-20260928: there is no refusal to retry from on
        this path any more, so what this holds onto is the other half of the matrix --
        stopped and accessible PROGRESSES, records `accessible`, and the establishment is one
        committed act that reads back the same afterwards.
        """
        from baton_v12.worker_manager import custody as _custody

        root = _custody._derived_root(self.case.store, self.intake.ATTEMPT,
                                      "result")[0]
        os.makedirs(root, exist_ok=True)
        group = workspaces.configured_workspace_group(self.case.store).gid
        os.chown(root, -1, group)
        os.chmod(root, 0o750)

        answer = self.ending(self.adapter())

        self.assertIn(answer["cleanup"], ("complete", "retained"))
        ceased = intake_module().historical_writer_cessation(
            self.case.store, answer["operation"])
        # W285465 under the owner supersession at 294568/294616: the record carries the
        # EXECUTION facts -- terminated, its exit status honestly, and the workspace locator --
        # and no output observation at all.
        self.assertEqual(ceased["state"], "absent")
        self.assertIsNotNone(ceased["workspace"])
        self.assertEqual(ceased["helpers"], [])
        self.assertEqual(
            dict(intake_module().historical_writer_cessation(
                self.case.store, answer["operation"])), dict(ceased))

    def test_a_RECEIPT_whose_cessation_was_never_committed_is_refused(self):
        """The reader compares against the journal, not against the document."""
        from baton_v12.worker_manager import intake

        answer = self.ending(self.adapter())
        # A RECEIPT NAMING A DESTROY THIS MANAGER ESTABLISHED NOTHING FOR. The evidence is
        # selected by the operation identity, so a receipt pointing at another operation
        # finds no record and the reader refuses instead of accepting the ending.
        elsewhere = dict(answer,
                         operation=dict(answer["operation"],
                                        operation_id="runtime.destroy:nobody"))
        with self.assertRaises(ContractRefusal) as refused:
            intake_module()._adopted_normalizations(
                self.case.store, self.intake.ATTEMPT, elsewhere,
                "a forged cleanup")
        self.assertIn("neither directory custody nor a writer cessation",
                      str(refused.exception))

    def test_BOTH_accounts_at_once_is_refused_as_a_fabricated_custody(self):
        answer = self.ending(self.adapter())
        both = dict(answer, directory_custody={"result": {}, "workspace": {}})
        with self.assertRaises(ContractRefusal) as refused:
            intake_module()._adopted_normalizations(
                self.case.store, self.intake.ATTEMPT, both, "a doubled cleanup")
        self.assertIn("ends on exactly one of the two accounts",
                      str(refused.exception))


def intake_module():
    from baton_v12.worker_manager import intake

    return intake


if __name__ == "__main__":       # pragma: no cover
    unittest.main()
