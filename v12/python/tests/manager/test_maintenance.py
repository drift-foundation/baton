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


if __name__ == "__main__":       # pragma: no cover
    unittest.main()
