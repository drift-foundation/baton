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

    def witnessed(self, engine):
        """Hook for a case that wants to act at the create boundary."""

    def executed(self, argv, document=None):
        """Run the manager's own program against the mount it composed.

        The bind source and the operands are read out of the argv the product
        composed, so nothing here can run the program over a directory the
        facility did not select.
        """
        if document is not None:
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
            "submission": "0" * 64, "place": "result-attempt-1",
            "established": True, "mode": "0o2770", "running_as": [65532, 1000]}))
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
                        + maintenance.MAINTENANCE_STOP_SECONDS,
                        maintenance.MAINTENANCE_SECONDS)
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


if __name__ == "__main__":       # pragma: no cover
    unittest.main()
