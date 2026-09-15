"""W161230 slice1, condition 5: the trusted local placement interface.

WHAT THESE CASES ARE ABOUT. A managed phase runs somewhere else, and what
comes back is a report and a content digest -- untrusted input by
construction, because the thing that produced it is the thing under test.
Publication is the TARGET NODE's act, and every case below drives the real
owners it composes: a real coordinator with a real entry and a real live
lease, a real managed custody record proved against its own journal, a real
Worker Manager attempt whose runtime axis is observed, and the real
integration profile performing the compare-and-swap on a real repository.

THE REFUSALS ARE THE SUBJECT. Each one leaves the target exactly where it was,
and every case asserts that as well as the refusal -- a placement that refused
after moving the reference would be worse than one that did not refuse.
"""
import json
import os
import subprocess
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import (activate_target, enqueue, grant_lease,
                                   managed_execution as managed)
from baton_v12.integration.git_profile import GitIntegrationProfile
from baton_v12.integration import entries_of
from baton_v12.integration.reconciliation import (attach_managed_phase,
                                                  publication_of,
                                                  record_managed_result)
from baton_v12.job_manager import execution_limits
from baton_v12.worker_manager.attempts import observe

from integration_placement import (AUTHORIZATION_SCHEMA, EXCLUSION_SCHEMA,
                                   LocalTargetPlacement, PLACEMENT_SCHEMA,
                                   PUBLISHED_MEMBERS, TARGET_SCHEMA,
                                   publish_collected_integration)

from ..integration import fixtures as coordinator_fixtures
from ..integration.test_managed_storage import (COMMANDS, ORCHESTRATION,
                                                PREPARE)
from ..manager.test_attempts import ATTEMPT, AttemptCase

VCS = "git"
# THE APPLY RUNS AS THE ATTEMPT THIS MANAGER ACTUALLY HOLDS. `AttemptCase`
# claims and activates exactly one, and a placement proves the runtime of the
# execution it is publishing -- so the phase names that attempt rather than a
# string, which is the whole point of the proof.
APPLY = ATTEMPT
COLLECTED = "sha256:" + "c" * 64
SETTLEMENT = {"imported_paths": ["feature.py"],
              "verification": {"status": 0, "detail": "the harness passed"}}


def _run(argv, cwd):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True)


class Materializer:
    """The node's own trusted fetch, recording what it was asked for.

    DETERMINISTIC AND FAKE, AND LABELLED AS SUCH -- but it exercises the real
    checks: what it answers is compared against the target's actual revision,
    and what it is ASKED is asserted to carry a digest and no location.
    """

    def __init__(self, answer=None):
        self.asked = []
        self.answer = answer
        self.before = None

    def materialize(self, operands):
        self.asked.append(dict(operands))
        # A DELIBERATE WINDOW. The real one takes time; this is where a case
        # makes something happen while content resolves.
        if self.before is not None:
            self.before()
        return self.answer


class ExecutionOwner:
    """The executing node's own adapter-backed exclusion, as a fake.

    IT ANSWERS WHAT THE REAL OWNER WOULD and nothing more: the assignment, the
    attempt, the start operation, the runtime identity and the frozen content.
    Every case that varies one of those varies it HERE, because the point of
    the gate is that the placement compares this answer with the manager's own
    durable row rather than believing either alone.
    """

    def __init__(self, **answer):
        self.asked = []
        self.answer = answer
        self.absent = False

    def exclusion_of(self, operands):
        self.asked.append(dict(operands))
        if self.absent:
            return None
        held = {"schema": EXCLUSION_SCHEMA,
                "attempt_id": operands["attempt_id"],
                "assignment": operands["assignment"],
                "content_digest": operands["content_digest"],
                "excluded": True}
        held.update(self.answer)
        return held


class TargetOwner:
    """The target owner that BOTH applies the change and remembers it.

    A DELIBERATELY FAKE BOUNDARY FOR THIS SLICE, and labelled as one. It
    performs the real reference advance through the real profile -- so the
    compare-and-swap under test is the actual one -- and returns a receipt of
    its own. THAT RECEIPT IS NOT GIT PUBLICATION EVIDENCE and nothing here
    claims it is: it stands for the operation-bound receipt a real target-side
    producer would write atomically with its effect, which this slice does not
    build.

    What it does exercise is the real contract: the placement compares every
    operand of the answer, requires a receipt only for `applied`, and keeps
    the uncertainty when this owner says `unknown`.
    """

    def __init__(self, profile, repository, reference):
        self.profile = profile
        self.repository = repository
        self.reference = reference
        self.applied = {}
        self.asked = []
        self.recovered = []
        self.answer = None
        self.recovery_answer = None
        self.before_apply = None

    def _document(self, request, answer, receipt=None):
        return {"schema": TARGET_SCHEMA,
                "publication_id": request["publication_id"],
                "canonical_target_id": request["canonical_target_id"],
                "admitted_old_revision": request["admitted_old_revision"],
                "imported_revision": request["imported_revision"],
                "content_digest": request["content_digest"],
                "derived_proposal_id": request["derived_proposal_id"],
                "answer": answer, "receipt": receipt}

    def apply(self, request):
        self.asked.append(dict(request))
        if self.before_apply is not None:
            self.before_apply()
        if self.answer is not None:
            return self.answer
        placed = self.profile.advance(
            self.repository, reference=self.reference,
            imported=request["imported_revision"],
            reviewed=request["admitted_old_revision"])
        receipt = "receipt-" + request["publication_id"][-12:]
        self.applied[request["publication_id"]] = receipt
        return self._document(dict(request, imported_revision=placed),
                              "applied", receipt)

    def recover(self, request):
        self.recovered.append(dict(request))
        if self.recovery_answer is not None:
            return self.recovery_answer
        receipt = self.applied.get(request["publication_id"])
        if receipt is None:
            return self._document(request, "not-applied")
        return self._document(request, "applied", receipt)


class Authorization:
    """Whether the derived candidate was independently approved, as a fake."""

    def __init__(self, **answer):
        self.asked = []
        self.answer = answer
        self.absent = False

    def authorized(self, operands):
        self.asked.append(dict(operands))
        if self.absent:
            return None
        held = {"schema": AUTHORIZATION_SCHEMA,
                "managed_result_id": operands["managed_result_id"],
                "canonical_target_id": operands["canonical_target_id"],
                "content_digest": operands["content_digest"],
                "derived_proposal_id": "derived-proposal-1",
                "derived_result_id": "derived-result-1",
                "derived_result_digest": "sha256:" + "e" * 64,
                "approved": True}
        held.update(self.answer)
        return held


class PlacementCase(AttemptCase):
    """One target node: a repository, a coordinator, a manager, a profile.

    `AttemptCase` is the Worker Manager's own fixture and supplies the real
    ControlStore whose runtime axis the placement reads. The coordinator, the
    repository and the profile are composed beside it, because a placement is
    exactly the node that holds all four at once.
    """

    def setUp(self):
        super().setUp()
        from baton_v12.integration import IntegrationStore
        self.node = tempfile.TemporaryDirectory(prefix="v12-placement-")
        self.addCleanup(self.node.cleanup)
        self.node_root = self.node.name
        self.repository = os.path.join(self.node_root, "target")
        os.makedirs(self.repository)
        for argv in ([VCS, "init", "-q", "-b", "main"],
                     [VCS, "config", "user.email", "t@example.invalid"],
                     [VCS, "config", "user.name", "target"]):
            self.assertEqual(_run(argv, self.repository).returncode, 0)
        self.base = self.write_revision("VALUE = 1\n", "the base")
        self.reference = "refs/heads/main"
        self.candidate = self.write_revision("VALUE = 2\n", "the candidate",
                                             restore=self.base)

        self.coordinator = IntegrationStore.open(
            os.path.join(self.node_root, "coordinator.sqlite3"),
            incarnation="placement-1",
            clock=lambda: coordinator_fixtures.NOW)
        self.addCleanup(self.coordinator.close)
        activate_target(self.coordinator, coordinator_fixtures.target())
        # THE QUEUE'S OWN ACCOUNT OF WHICH SUBMISSION THIS ENTRY IS FOR, and
        # the managed result below is built FROM it. Review
        # 2026-09-14T00:04:25Z: nothing related the two, so content prepared
        # for one submission published and settled an unrelated entry that
        # happened to hold a valid lease.
        self.eligibility = coordinator_fixtures.eligibility(
            expected_target_revision=self.base)
        enqueue(self.coordinator,
                canonical_target_id=coordinator_fixtures.TARGET,
                entry_id="entry-1", eligibility=self.eligibility)
        self.lease = grant_lease(
            self.coordinator,
            canonical_target_id=coordinator_fixtures.TARGET,
            entry_id="entry-1", lease_id="lease-1",
            integrator_participant="baton.integrator",
            attempt_id="attempt-1")
        self.fence = self.lease["lease"]["fence"]
        # THE PROFILE'S ONLY WAY TO REACH A SUBPROCESS, and it answers the
        # closed command-result shape that profile owns -- measured, step 112:
        # handing it a `CompletedProcess` is refused, and rightly.
        def runner(argv):
            answered = subprocess.run(list(argv), cwd=self.repository,
                                      capture_output=True, text=True)
            return {"returncode": answered.returncode,
                    "stdout": answered.stdout, "stderr": answered.stderr}

        self.profile = GitIntegrationProfile(runner)
        self.materializer = Materializer(self.candidate)
        self.execution_owner = ExecutionOwner()
        self.authorization = Authorization()
        self.target_owner = TargetOwner(self.profile, self.repository,
                                        self.reference)
        # THE CLAIM AND THE ACTIVATION, so the manager holds a FIXED
        # assignment for the attempt the apply names. `attempt_runtime_of`
        # answers about an activated attempt, and the placement compares what
        # it answers with the assignment the phase was composed for.
        from baton_v12.worker_manager.attempts import (activate_assignment,
                                                       request_runtime_start)
        from ..manager.test_attempts import Adapter
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT,
                            expect=self.expect())
        # AND THE RUNTIME IS ACTUALLY STARTED AND ATTACHED. Review
        # 2026-09-13T23:50:10Z [P1]: the old fixture observed `destroyed`
        # directly on an attempt that never started, so the positive published
        # with no runtime identity at all -- which proved the missing gate
        # rather than the exclusion it claimed.
        self.adapter = Adapter()
        request_runtime_start(self.store, self.adapter, attempt_id=ATTEMPT)
        self.runtime_id = self.adapter.runtime_id
        self.start_operation_id = self.started_operation()
        self.execution_owner.answer.setdefault("runtime_id", self.runtime_id)
        self.execution_owner.answer.setdefault("start_operation_id",
                                               self.start_operation_id)

    def started_operation(self):
        """The committed `runtime.start` this manager actually journalled."""
        found = self.store._connection.execute(
            "SELECT operation_id FROM operations WHERE kind = 'runtime.start' "
            "AND state = 'committed'").fetchall()
        self.assertEqual(len(found), 1, "one committed start")
        return found[0][0]

    def write_revision(self, content, message, restore=None):
        """One revision on the target, and its object name.

        `restore` puts the reference back afterwards, because a case composes
        a candidate WITHOUT moving the target it is about to publish into.
        """
        with open(os.path.join(self.repository, "feature.py"), "w") as handle:
            handle.write(content)
        self.assertEqual(_run([VCS, "add", "-A"],
                              self.repository).returncode, 0)
        self.assertEqual(_run([VCS, "commit", "-qm", message],
                              self.repository).returncode, 0)
        held = _run([VCS, "rev-parse", "HEAD"],
                    self.repository).stdout.strip()
        if restore is not None:
            self.assertEqual(
                _run([VCS, "reset", "-q", "--hard", restore],
                     self.repository).returncode, 0)
        return held

    # -- the managed custody record -----------------------------------------

    def task(self, **changed):
        held = {"phase": "apply", "orchestration_id": ORCHESTRATION,
                "canonical_target_id": coordinator_fixtures.TARGET,
                "execution_attempt_id": APPLY,
                "assignment": self.expect(),
                "task_digest": "sha256:" + "a" * 64,
                "input_digest": "sha256:" + "b" * 64,
                "harness_digest": "sha256:" + "h" * 64,
                "execution_limits": execution_limits.resolved({}, 1),
                "commands": COMMANDS,
                "parent": {"execution_attempt_id": PREPARE,
                           "collected_digest": COLLECTED}}
        held.update(changed)
        return managed.managed_task(**held)

    def account(self, task=None, *, kind="measured", status=0, completed=None,
                not_run=(), tag=None, collected=True):
        task = task or self.task()
        report = managed.collected_report(
            task, kind=kind,
            completed=[{"name": one, "status": 0} for one in COMMANDS]
            if completed is None else completed,
            not_run=not_run, status=status, tag=tag)
        return {"task": task,
                "result": managed.managed_result(
                    task, report,
                    collected={"result_id": "result-" + APPLY,
                               "manifest_digest": COLLECTED,
                               "disposition": "completed"}
                    if collected else None)}

    def submitted(self, account=None, **changed):
        """The managed result's submission, in the entry's own identities.

        The queue admitted the entry under one submission and reconciliation
        recorded the result under another set of names for the same thing;
        this is that one submission said both ways, so a case that wants them
        to DISAGREE changes exactly one member.
        """
        eligible = account or self.eligibility
        held = {"authority_uuid": eligible["authority_uuid"],
                "work_id": eligible["work_id"], "job_id": "job-1",
                "line_id": eligible["line_id"],
                "source_checkpoint_id": eligible["checkpoint_id"],
                "source_verdict_id": eligible["verdict_id"],
                "source_proposal_id": eligible["proposal_id"],
                "source_result_id": eligible["result_id"],
                "source_result_digest": eligible["result_digest"],
                "source_checkpoint_digest": eligible["checkpoint_digest"],
                "source_base": "a" * 40, "source_candidate": "c" * 40}
        held.update(changed)
        return held

    def custody(self, *, account=None, revision=None, submitted=None):
        """The result, its preparation and its apply, through the real
        owners."""
        record_managed_result(
            self.coordinator, submitted or self.submitted(),
            orchestration_id=ORCHESTRATION,
            canonical_target_id=coordinator_fixtures.TARGET,
            target_revision=revision or self.base)
        preparing = managed.managed_task(
            phase="prepare", orchestration_id=ORCHESTRATION,
            canonical_target_id=coordinator_fixtures.TARGET,
            execution_attempt_id=PREPARE, assignment=self.expect(),
            task_digest="sha256:" + "d" * 64,
            input_digest="sha256:" + "b" * 64,
            harness_digest="sha256:" + "h" * 64,
            execution_limits=execution_limits.resolved({}, 1),
            commands=COMMANDS)
        prepared = managed.collected_report(
            preparing, kind="measured",
            completed=[{"name": one, "status": 0} for one in COMMANDS],
            status=0)
        attach_managed_phase(
            self.coordinator, managed_result_id=ORCHESTRATION,
            task=preparing,
            result=managed.managed_result(
                preparing, prepared,
                collected={"result_id": "result-" + PREPARE,
                           "manifest_digest": COLLECTED,
                           "disposition": "completed"}))
        held = account or self.account()
        attach_managed_phase(self.coordinator,
                             managed_result_id=ORCHESTRATION,
                             task=held["task"], result=held["result"])
        return held

    def stopped(self, attempt_id=APPLY):
        """The manager's own positive observation that the runtime is gone.

        The runtime was really started and attached above, so this is the
        ordinary terminal observation about a runtime that existed -- not a
        terminal axis on an attempt that never ran.
        """
        observe(self.store, attempt_id=attempt_id,
                axis="execution_runtime", value="destroyed")

    def placement(self, **changed):
        held = {"coordinator": self.coordinator, "manager": self.store,
                "profile": self.profile, "materializer": self.materializer,
                "execution_owner": self.execution_owner,
                "authorization": self.authorization,
                "target_owner": self.target_owner,
                "repository": self.repository, "reference": self.reference}
        held.update(changed)
        return LocalTargetPlacement(**held)

    def publish(self, **changed):
        held = {"canonical_target_id": coordinator_fixtures.TARGET,
                "entry_id": "entry-1", "lease_id": "lease-1",
                "fence": self.fence, "admitted_old_revision": self.base,
                "managed_result_id": ORCHESTRATION, "phase": "apply",
                "settlement": SETTLEMENT}
        held.update(changed)
        return publish_collected_integration(self.placement(), **held)

    def standing(self):
        return self.profile.revision(self.repository, self.reference)


class ThePublicationIsTheTargetNodesAct(PlacementCase):

    def test_a_collected_apply_reaches_the_target(self):
        """THE POSITIVE, and it names everything it rested on."""
        self.custody()
        self.stopped()
        answer = self.publish()
        self.assertEqual(sorted(answer), sorted(PUBLISHED_MEMBERS))
        self.assertEqual(answer["schema"], PLACEMENT_SCHEMA)
        self.assertEqual(answer["imported_revision"], self.candidate)
        self.assertEqual(answer["admitted_old_revision"], self.base)
        self.assertEqual(answer["content_digest"], COLLECTED)
        # THE TARGET ACTUALLY MOVED, and to the materialized content.
        self.assertEqual(self.standing(), self.candidate)
        # AND THE MATERIALIZER WAS ASKED BY DIGEST, never by location.
        self.assertEqual(len(self.materializer.asked), 1)
        asked = self.materializer.asked[0]
        self.assertEqual(asked["content_digest"], COLLECTED)
        for absent in ("path", "workspace", "locator", "host", "repository"):
            self.assertNotIn(absent, asked)

    def test_the_swap_is_against_the_admitted_revision(self):
        """NOT against whatever the reference says now. Those are the same
        value in the ordinary case and different exactly when something moved
        the target underneath this integration -- which is the case the swap
        exists for."""
        self.custody()
        self.stopped()
        moved = self.write_revision("VALUE = 99\n", "somebody else")
        self.assertEqual(self.standing(), moved)
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("something else moved the target",
                      str(caught.exception))
        self.assertIn("this publication was admitted against",
                      str(caught.exception))
        self.assertEqual(self.standing(), moved)

    def test_a_result_reconciled_against_another_revision_is_refused(self):
        self.custody(revision=self.candidate)
        self.stopped()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("was reconciled against", str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_a_result_for_another_target_is_refused(self):
        self.custody()
        self.stopped()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish(canonical_target_id="target:elsewhere")
        self.assertEqual(caught.exception.category, "policy")
        self.assertEqual(self.standing(), self.base)


class NothingPublishesBehindARunningExecution(PlacementCase):
    """A worker's own stop report, a stop order somebody sent and an elapsed
    timeout can all be true while the execution is still writing. None of them
    reaches this proof, which is the manager's own durable observation."""

    def test_an_unobserved_runtime_refuses(self):
        self.custody()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("positively observed", str(caught.exception))
        self.assertEqual(self.standing(), self.base)
        self.assertEqual(self.materializer.asked, [])

    def test_a_quiescent_runtime_is_not_a_stopped_one(self):
        """A runtime that stopped EXECUTING still exists."""
        self.custody()
        observe(self.store, attempt_id=APPLY, axis="execution_runtime",
                value="running")
        observe(self.store, attempt_id=APPLY, axis="execution_runtime",
                value="quiescent")
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("quiescent", str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_an_attempt_this_manager_never_recorded_refuses(self):
        """Absence of a record is not absence of a runtime."""
        self.custody(account=self.account(
            self.task(execution_attempt_id="apply-attempt-elsewhere")))
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        # THE EXCLUSION'S OWN BINDING FAILS FIRST, and that is the stronger
        # refusal: the start this manager committed names another attempt, so
        # the owner's answer is about something else before anything asks what
        # this manager holds for it.
        self.assertIn("was signed over attempt", str(caught.exception))
        self.assertEqual(self.standing(), self.base)


class OnlyAMeasuredSuccessAuthorizesAPublication(PlacementCase):
    """The three report answers, and only one of them may publish."""

    def test_a_report_collected_without_a_status_cannot_publish(self):
        self.custody(account=self.account(
            kind="collected-without-status", status=None,
            completed=[{"name": COMMANDS[0], "status": 0}],
            not_run=list(COMMANDS[1:]),
            tag="the runtime was destroyed before the harness reported"))
        self.stopped()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("neither authorizes a publication",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_no_collected_report_cannot_publish(self):
        self.custody(account=self.account(
            kind="not-collected", status=None, completed=[],
            not_run=list(COMMANDS), collected=False))
        self.stopped()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("neither authorizes a publication",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_a_measured_failure_cannot_publish(self):
        self.custody(account=self.account(
            status=2,
            completed=[{"name": COMMANDS[0], "status": 0},
                       {"name": COMMANDS[1], "status": 0},
                       {"name": COMMANDS[2], "status": 2}]))
        self.stopped()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("whose own harness succeeded", str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_a_sequence_that_stopped_partway_cannot_publish(self):
        """A completed prefix with a zero status is not a passing run: the
        not-run suffix is exactly what a shorter successful sequence would
        have hidden."""
        self.custody(account=self.account(
            completed=[{"name": COMMANDS[0], "status": 0}],
            not_run=list(COMMANDS[1:])))
        self.stopped()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("is not a shorter sequence that passed",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)


class TheGrantAndTheContentAreProvedBeforeAnyWrite(PlacementCase):

    def test_a_stale_fence_refuses_before_the_swap(self):
        self.custody()
        self.stopped()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish(fence=self.fence + 1)
        self.assertEqual(self.standing(), self.base)
        self.assertIsInstance(caught.exception, ContractRefusal)
        # THE CONTENT WAS RESOLVED FIRST AND ON PURPOSE. The grant is proved
        # at the MUTATION boundary now, so the one step that takes time
        # happens outside the window that must hold at the moment of the swap
        # -- and resolving content mutates nothing.
        self.assertEqual(len(self.materializer.asked), 1)

    def test_a_lease_this_node_does_not_hold_refuses(self):
        self.custody()
        self.stopped()
        with self.assertRaises(ContractRefusal):
            self.publish(lease_id="lease-somebody-elses")
        self.assertEqual(self.standing(), self.base)

    def test_content_this_node_does_not_hold_refuses(self):
        """A publication imports bytes this node actually has. The grant has
        been proved by now, and nothing has been written."""
        self.custody()
        self.stopped()
        self.materializer.answer = None
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("holds no collected content", str(caught.exception))
        self.assertEqual(self.standing(), self.base)
        self.assertEqual(len(self.materializer.asked), 1)

    def test_a_node_with_no_target_repository_refuses(self):
        self.custody()
        self.stopped()
        placement = self.placement(
            repository=os.path.join(self.node_root, "absent"))
        with self.assertRaises(ContractRefusal) as caught:
            publish_collected_integration(
                placement,
                canonical_target_id=coordinator_fixtures.TARGET,
                entry_id="entry-1", lease_id="lease-1", fence=self.fence,
                admitted_old_revision=self.base,
                managed_result_id=ORCHESTRATION, settlement=SETTLEMENT)
        self.assertIn("publishes into the target it was configured with",
                      str(caught.exception))

    def test_a_placement_without_a_materializer_is_refused_at_composition(self):
        """A location operand would be the worker choosing where the bytes
        come from, so the node's fetch is a CAPABILITY and its absence is a
        refusal before anything is asked of it."""
        with self.assertRaises(ContractRefusal) as caught:
            self.placement(materializer=object())
        self.assertIn("materializer", str(caught.exception))

    def test_a_phase_this_result_does_not_retain_refuses(self):
        self.custody()
        self.stopped()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish(phase="prepare", settlement=SETTLEMENT)
        # The preparation IS retained, so this one refuses further along: its
        # own runtime was never observed stopped.
        # THE EXCLUSION'S OWN BINDING FAILS FIRST, and that is the stronger
        # refusal: the start this manager committed names another attempt, so
        # the owner's answer is about something else before anything asks what
        # this manager holds for it.
        self.assertIn("was signed over attempt", str(caught.exception))
        self.assertEqual(self.standing(), self.base)


class TheTrustedOwnersAreBothRequired(PlacementCase):
    """[P1] Gate 4: a locally composed execution-owner capability obtaining
    POSITIVE EXCLUSION from the adapter on the node that ran the phase, and an
    independently approved derived candidate.

    The first version had neither. Its positive published while the runtime
    identity was `None` and the managed result carried no derived proposal at
    all -- which proved the missing gate rather than the exclusion the test
    claimed. The fakes below are deterministic and fake, and they exercise the
    real checks: what they answer is compared against this manager's own
    durable row and against the phase's own content.
    """

    def ready(self):
        self.custody()
        self.stopped()

    def test_the_positive_binds_every_required_fact(self):
        self.ready()
        answer = self.publish()
        self.assertEqual(answer["outcome"], "published")
        self.assertEqual(answer["derived_proposal_id"], "derived-proposal-1")
        asked = self.execution_owner.asked[0]
        self.assertEqual(asked["attempt_id"], APPLY)
        self.assertEqual(asked["assignment"], self.expect())
        self.assertEqual(asked["content_digest"], COLLECTED)
        # AND THE RUNTIME REALLY EXISTED: started, attached, then destroyed.
        self.assertEqual(self.execution_owner.answer["runtime_id"],
                         self.runtime_id)
        self.assertIsNotNone(self.start_operation_id)
        self.assertEqual(self.standing(), self.candidate)

    def test_an_unavailable_execution_owner_refuses(self):
        self.ready()
        self.execution_owner.absent = True
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("answered nothing", str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_a_negative_exclusion_refuses(self):
        """A forged stopped report is not an exclusion: the owner says so."""
        self.ready()
        self.execution_owner.answer["excluded"] = False
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("only a positive exclusion publishes",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_a_foreign_runtime_identity_refuses(self):
        """The owner's answer and this manager's row must name ONE runtime."""
        self.ready()
        self.execution_owner.answer["runtime_id"] = "runtime-somewhere-else"
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("and this manager records", str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_a_start_operation_this_manager_never_committed_refuses(self):
        """A runtime identity with no start behind it is a runtime nobody in
        this deployment is recorded as having launched."""
        self.ready()
        self.execution_owner.answer["start_operation_id"] = "runtime.start:x"
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("holds no committed runtime start there",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_an_exclusion_about_another_phase_refuses(self):
        for member, wrong in (("attempt_id", "apply-attempt-elsewhere"),
                              ("assignment", {"work_ref": {
                                  "authority_uuid": "0" * 31 + "a",
                                  "work_id": "00000000-W9"},
                                  "participant": "baton.other",
                                  "generation": 1}),
                              ("content_digest", "sha256:" + "9" * 64)):
            with self.subTest(member=member):
                case = type(self)(self._testMethodName)
                case.setUp()
                case.ready()
                case.execution_owner.answer[member] = wrong
                with self.assertRaises(ContractRefusal) as caught:
                    case.publish()
                self.assertIn("is not an answer about this",
                              str(caught.exception))
                self.assertEqual(case.standing(), case.base)
                case.doCleanups()

    def test_an_attempt_with_no_attached_runtime_refuses(self):
        """The shape a publication follows is a runtime that EXISTED. An
        attempt that never attached one has nothing to be excluded from."""
        self.custody(account=self.account(
            self.task(execution_attempt_id="apply-attempt-elsewhere")))
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        # THE EXCLUSION'S OWN BINDING FAILS FIRST, and that is the stronger
        # refusal: the start this manager committed names another attempt, so
        # the owner's answer is about something else before anything asks what
        # this manager holds for it.
        self.assertIn("was signed over attempt", str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_an_unavailable_authorization_owner_refuses(self):
        self.ready()
        self.authorization.absent = True
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("no authorization owner answered", str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_an_unapproved_candidate_refuses(self):
        """A measured worker report says the harness passed. It does not say
        anybody approved publishing the bytes."""
        self.ready()
        self.authorization.answer["approved"] = False
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("somebody independently authorized",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_an_authorization_for_other_content_refuses(self):
        self.ready()
        self.authorization.answer["content_digest"] = "sha256:" + "9" * 64
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("the authorization names content_digest",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_an_authorization_for_another_result_refuses(self):
        self.ready()
        self.authorization.answer["managed_result_id"] = "somebody-elses"
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("the authorization names managed_result_id",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_a_placement_missing_either_owner_is_refused_at_composition(self):
        for member in ("execution_owner", "authorization", "materializer"):
            with self.subTest(capability=member):
                with self.assertRaises(ContractRefusal) as caught:
                    self.placement(**{member: object()})
                self.assertIsInstance(caught.exception, ContractRefusal)


class TheGrantIsProvedAtTheMutationBoundary(PlacementCase):
    """[P1] The pre-mutation check used to precede an intervening capability.

    `live_grant` ran before `materialize`, and the materializer is the one step
    that takes time. A grant released while content resolved let the target
    advance under a lease already known to be over, and only the settlement
    refused -- after the reference had moved.
    """

    def test_a_grant_lost_while_content_resolves_stops_the_swap(self):
        from baton_v12.integration import refuse_entry
        self.custody()
        self.stopped()

        def ending():
            refuse_entry(self.coordinator, lease_id="lease-1",
                         canonical_target_id=coordinator_fixtures.TARGET,
                         entry_id="entry-1", fence=self.fence,
                         settlement={"reason": "policy",
                                     "detail": {"why": "withdrawn"}})

        self.materializer.before = ending
        with self.assertRaises(ContractRefusal):
            self.publish()
        # THE TARGET DID NOT MOVE. That is the whole finding: the swap is
        # behind the grant check now, not in front of it.
        self.assertEqual(self.standing(), self.base)
        self.assertEqual(len(self.materializer.asked), 1)


class TheWholeRequestIsOwnedBeforeAnyEffect(PlacementCase):
    """[P1] A malformed settlement moved the reference and then refused.

    It was passed untouched to `settle_integrated` AFTER the swap, so
    deterministic validation of caller input produced a partial canonical
    effect. The settlement is owned through the queue's own rule before
    anything happens -- one lock, both doors.
    """

    def test_an_empty_settlement_refuses_with_the_target_unchanged(self):
        self.custody()
        self.stopped()
        with self.assertRaises(ContractRefusal):
            self.publish(settlement={})
        self.assertEqual(self.standing(), self.base)
        self.assertEqual(self.materializer.asked, [])

    def test_a_settlement_of_the_wrong_variant_refuses(self):
        self.custody()
        self.stopped()
        with self.assertRaises(ContractRefusal):
            self.publish(settlement={"reason": "policy", "detail": {}})
        self.assertEqual(self.standing(), self.base)

    def test_a_settlement_whose_members_are_wrong_refuses(self):
        self.custody()
        self.stopped()
        with self.assertRaises(ContractRefusal):
            self.publish(settlement={"imported_paths": "feature.py",
                                     "verification": {"status": 0}})
        self.assertEqual(self.standing(), self.base)


class APublicationReplaysAndResumesItsOwnEffects(PlacementCase):
    """[P2] An exact retry mistook its own CAS for foreign movement.

    The only comparison was against the admitted revision, so after a
    successful publication the target no longer matched and the retry refused.
    What distinguishes "our own swap" from "somebody else's" is that the
    revision is resolved from THIS phase's content digest through this node's
    own materializer -- a bound value, not a coincidence.
    """

    def published(self):
        self.custody()
        self.stopped()
        return self.publish()

    def test_an_exact_retry_replays_without_materializing_or_swapping(self):
        first = self.published()
        self.assertEqual(first["outcome"], "published")
        asked = len(self.materializer.asked)
        again = self.publish()
        self.assertEqual(again["outcome"], "replayed")
        self.assertEqual(again["imported_revision"], self.candidate)
        self.assertEqual(again["settlement"], first["settlement"])
        # NOTHING WAS RESOLVED AND NOTHING WAS SWAPPED.
        self.assertEqual(len(self.materializer.asked), asked)
        self.assertEqual(self.standing(), self.candidate)

    def test_a_retry_under_a_different_settlement_refuses(self):
        self.published()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish(settlement={"imported_paths": ["other.py"],
                                     "verification": {"status": 0,
                                                      "detail": "different"}})
        self.assertIn("not a second account of it", str(caught.exception))

    def test_an_interrupted_publication_resumes_without_swapping_twice(self):
        """The swap committed and the settlement did not. A resume finishes
        what is missing; it does not swap again, because a compare-and-swap
        that committed cannot be undone by this interface."""
        self.custody()
        self.stopped()
        from baton_v12.integration import queue as queue_owner
        real = queue_owner.settle_integrated

        def interrupted(*argv, **named):
            raise RuntimeError("the process died before settling")

        try:
            import integration_placement as placement_module
            placement_module.settle_integrated = interrupted
            with self.assertRaises(RuntimeError):
                self.publish()
        finally:
            placement_module.settle_integrated = real
        # THE TARGET MOVED AND NOTHING SETTLED: the interrupted state.
        self.assertEqual(self.standing(), self.candidate)
        resumed = self.publish()
        self.assertEqual(resumed["outcome"], "resumed")
        self.assertEqual(resumed["imported_revision"], self.candidate)
        self.assertEqual(self.standing(), self.candidate)

    def test_a_foreign_revision_is_never_adopted_as_our_own(self):
        """Merely finding the target somewhere other than the admitted
        revision is not a resume. It is somebody else's mutation until the
        revision is the one THIS content resolves to."""
        self.custody()
        self.stopped()
        foreign = self.write_revision("VALUE = 77\n", "somebody else")
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("something else moved the target", str(caught.exception))
        self.assertEqual(self.standing(), foreign)


class TheEntryThisSettlesIsThisSubmissionsOwn(PlacementCase):
    """[P1] Review 2026-09-14T00:04:25Z: nothing related the two.

    Content prepared for one submission published and SETTLED an unrelated
    entry that happened to hold a valid lease. A grant says this node may
    write the target; it does not say which queued work the bytes answer.
    """

    def unrelated(self):
        """A second entry, for a different submission, with its own lease."""
        from baton_v12.integration import refuse_entry
        refuse_entry(self.coordinator, lease_id="lease-1",
                     canonical_target_id=coordinator_fixtures.TARGET,
                     entry_id="entry-1", fence=self.fence,
                     settlement={"reason": "policy",
                                 "detail": {"why": "stand down"}})
        # A DIFFERENT CANDIDATE, not merely a different proposal id: one
        # checkpoint holds one place in a target's queue, and a second entry
        # for the same candidate is refused by the queue itself (measured,
        # step 125) -- which is its rule and not this case's subject.
        other = coordinator_fixtures.eligibility(
            checkpoint_id="checkpoint-somebody-else",
            verdict_id="verdict-somebody-else",
            proposal_id="proposal-somebody-else",
            result_id="result-somebody-else",
            expected_target_revision=self.base)
        enqueue(self.coordinator,
                canonical_target_id=coordinator_fixtures.TARGET,
                entry_id="entry-2", eligibility=other)
        held = grant_lease(self.coordinator,
                           canonical_target_id=coordinator_fixtures.TARGET,
                           entry_id="entry-2", lease_id="lease-2",
                           integrator_participant="baton.integrator",
                           attempt_id="attempt-2")
        return held["lease"]["fence"]

    def test_content_for_one_submission_cannot_settle_another_entry(self):
        self.custody()
        self.stopped()
        fence = self.unrelated()
        with self.assertRaises(ContractRefusal) as caught:
            self.publish(entry_id="entry-2", lease_id="lease-2", fence=fence)
        self.assertIn("not which queued work these bytes answer",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)
        # AND NOTHING SETTLED: the unrelated entry is where it was.
        self.assertEqual(
            [one["state"] for one in
             entries_of(self.coordinator, coordinator_fixtures.TARGET)
             if one["entry_id"] == "entry-2"], ["leased"])

    def test_each_admitted_identity_is_compared_by_name(self):
        """One member at a time, so none hides behind another's failure."""
        for member, wrong in (("authority_uuid", "0" * 31 + "b"),
                              ("work_id", "0000000a-W9"),
                              ("line_id", "line-somebody-else"),
                              ("source_checkpoint_id", "checkpoint-9"),
                              ("source_verdict_id", "verdict-9"),
                              ("source_proposal_id", "proposal-9"),
                              ("source_result_id", "result-9"),
                              ("source_result_digest", "sha256:" + "9" * 64),
                              ("source_checkpoint_digest",
                               "sha256:" + "8" * 64)):
            with self.subTest(member=member):
                case = type(self)(self._testMethodName)
                case.setUp()
                case.custody(submitted=case.submitted(**{member: wrong}))
                case.stopped()
                with self.assertRaises(ContractRefusal) as caught:
                    case.publish()
                self.assertIn("is queued for", str(caught.exception))
                self.assertEqual(case.standing(), case.base)
                case.doCleanups()

    def test_a_tampered_entry_is_refused_by_the_queues_own_proof(self):
        """AND THE QUEUE GETS THERE FIRST, which is the right owner.

        Measured, step 126: editing an entry's `expected_target_revision`
        directly is caught by the queue's own chain proof -- it compares the
        column with what the enqueue act recorded -- before this placement's
        comparison is reached. The placement keeps its own check for the case
        that proof cannot see: an entry legitimately enqueued against a
        different snapshot, which within one target requires a later
        re-enqueue after this one settles. I am not asserting a refusal I
        reached by a route the queue closes, and I am not claiming coverage of
        the path I did not reach.
        """
        self.custody()
        self.stopped()
        self.coordinator._connection.execute(
            "UPDATE entries SET expected_target_revision = ? "
            "WHERE entry_id = ?", ("f" * 40, "entry-1"))
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("recorded expected_target_revision",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)


class APublicationKeepsItsOwnDurableAccount(PlacementCase):
    """[P1/P2] A materializer mapping proves what content IS. It cannot say
    who moved a reference.

    The restart decision used to compare the target's current revision with
    the revision this content materializes to, so a FOREIGN move onto the same
    revision was adopted as an owned swap, a completed retry accepted an
    unrelated lease and a fence 99 higher, and a retry after later movement
    reported that foreign revision as its own imported outcome. The
    publication now records what it is about and what it did, before it does
    it.
    """

    def published(self):
        self.custody()
        self.stopped()
        return self.publish()

    def test_a_foreign_move_to_our_own_revision_is_not_our_swap(self):
        """THE CASE THE PREVIOUS FORM COULD NOT DISTINGUISH. Nothing of ours
        has run; somebody else moved the target to the very revision we would
        have imported. Without a record of our own there is nothing that makes
        it ours."""
        self.custody()
        self.stopped()
        self.profile.advance(self.repository, reference=self.reference,
                             imported=self.candidate, reviewed=self.base)
        self.assertEqual(self.standing(), self.candidate)
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("something else moved the target", str(caught.exception))
        self.assertIsNone(publication_of(self.coordinator, ORCHESTRATION,
                                         "apply"))

    def test_a_completed_retry_refuses_an_unrelated_lease_or_fence(self):
        self.published()
        for member, wrong in (("lease_id", "lease-somebody-elses"),
                              ("fence", self.fence + 99),
                              ("entry_id", "entry-2")):
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal) as caught:
                    self.publish(**{member: wrong})
                self.assertIsInstance(caught.exception, ContractRefusal)

    def test_a_retry_after_later_movement_returns_its_own_revision(self):
        """NOT the foreign one standing there now."""
        first = self.published()
        moved = self.write_revision("VALUE = 500\n", "somebody later",
                                    restore=None)
        self.assertEqual(self.standing(), moved)
        again = self.publish()
        self.assertEqual(again["outcome"], "replayed")
        self.assertEqual(again["imported_revision"], self.candidate)
        self.assertEqual(again["imported_revision"],
                         first["imported_revision"])
        self.assertNotEqual(again["imported_revision"], moved)

    def test_the_record_names_what_it_was_about(self):
        self.published()
        held = publication_of(self.coordinator, ORCHESTRATION, "apply")
        self.assertEqual(held["state"], "settled")
        self.assertEqual(held["entry_id"], "entry-1")
        self.assertEqual(held["lease_id"], "lease-1")
        self.assertEqual(held["fence"], self.fence)
        self.assertEqual(held["admitted_old_revision"], self.base)
        self.assertEqual(held["imported_revision"], self.candidate)
        self.assertEqual(held["content_digest"], COLLECTED)
        self.assertEqual(held["derived_proposal_id"], "derived-proposal-1")

    def interrupt_after_effect(self):
        """Run a publication whose effect lands and whose marker does not."""
        import integration_placement as placement_module
        real = placement_module.record_publication_effect

        def interrupted(store, publication_id, state):
            if state == "swapped":
                raise RuntimeError("the process died after the effect")
            return real(store, publication_id, state)

        try:
            placement_module.record_publication_effect = interrupted
            with self.assertRaises(RuntimeError):
                self.publish()
        finally:
            placement_module.record_publication_effect = real

    def test_an_interrupted_effect_is_resolved_by_its_receipt(self):
        """A crash between the effect and its marker is answerable BECAUSE the
        owner that applied the change is the owner that remembers it.

        Review 2026-09-14T00:26:30Z: the reference cannot tell a delayed
        effect from an absent one, so the recovery is asked instead -- and
        `applied` comes back with the receipt that act wrote.
        """
        self.custody()
        self.stopped()
        self.interrupt_after_effect()
        self.assertEqual(
            publication_of(self.coordinator, ORCHESTRATION,
                           "apply")["state"], "intended")
        self.assertEqual(self.standing(), self.candidate)
        resumed = self.publish()
        self.assertEqual(resumed["outcome"], "resumed")
        self.assertEqual(resumed["imported_revision"], self.candidate)
        # THE RECOVERY WAS ASKED and nothing was applied a second time.
        self.assertEqual(len(self.target_owner.recovered), 1)
        self.assertEqual(len(self.target_owner.asked), 1)
        self.assertEqual(
            publication_of(self.coordinator, ORCHESTRATION,
                           "apply")["state"], "settled")

    def test_an_owner_that_cannot_say_leaves_it_uncertain(self):
        """`unknown` is one of the three answers, and this interface keeps it
        rather than issuing a second compare-and-swap on the strength of the
        current reference."""
        self.custody()
        self.stopped()
        self.interrupt_after_effect()
        held = publication_of(self.coordinator, ORCHESTRATION, "apply")
        self.target_owner.recovery_answer = {
            "schema": TARGET_SCHEMA,
            "publication_id": held["publication_id"],
            "canonical_target_id": coordinator_fixtures.TARGET,
            "admitted_old_revision": self.base,
            "imported_revision": self.candidate,
            "content_digest": COLLECTED,
            "derived_proposal_id": "derived-proposal-1",
            "answer": "unknown", "receipt": None}
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("cannot say whether publication", str(caught.exception))
        # AND IT DOES NOT CLAIM NOTHING CHANGED. The recovery has already been
        # called, and an effect-capable owner may have done something this
        # interface did not observe; asserting otherwise would be the
        # unfounded certainty this branch exists to avoid.
        self.assertNotIn("Nothing was changed", str(caught.exception))
        self.assertEqual(len(self.target_owner.asked), 1)
        self.assertEqual(
            publication_of(self.coordinator, ORCHESTRATION,
                           "apply")["state"], "intended")

    def test_an_unavailable_target_owner_leaves_it_uncertain(self):
        self.custody()
        self.stopped()
        self.interrupt_after_effect()
        self.target_owner.recover = lambda request: None
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("answered nothing", str(caught.exception))
        self.assertNotIn("Nothing was changed", str(caught.exception))
        self.assertEqual(
            publication_of(self.coordinator, ORCHESTRATION,
                           "apply")["state"], "intended")

    def test_an_answer_about_another_publication_is_refused(self):
        self.custody()
        self.stopped()
        self.interrupt_after_effect()
        self.target_owner.recovery_answer = {
            "schema": TARGET_SCHEMA,
            "publication_id": "publication:somebody-elses",
            "canonical_target_id": coordinator_fixtures.TARGET,
            "admitted_old_revision": self.base,
            "imported_revision": self.candidate,
            "content_digest": COLLECTED,
            "derived_proposal_id": "derived-proposal-1",
            "answer": "applied", "receipt": "receipt-elsewhere"}
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("is not an answer about this", str(caught.exception))

    def test_an_applied_answer_without_a_receipt_is_refused(self):
        """A receipt accounts for an effect that happened, and it is the only
        answer that claims one."""
        self.custody()
        self.stopped()
        self.interrupt_after_effect()
        held = publication_of(self.coordinator, ORCHESTRATION, "apply")
        self.target_owner.recovery_answer = {
            "schema": TARGET_SCHEMA,
            "publication_id": held["publication_id"],
            "canonical_target_id": coordinator_fixtures.TARGET,
            "admitted_old_revision": self.base,
            "imported_revision": self.candidate,
            "content_digest": COLLECTED,
            "derived_proposal_id": "derived-proposal-1",
            "answer": "applied", "receipt": None}
        with self.assertRaises(ContractRefusal):
            self.publish()

    def test_a_positive_exclusion_still_meets_the_targets_real_state(self):
        """`not-applied` is a POSITIVE exclusion of a delayed effect, which is
        the only thing that makes a second attempt safe -- and the attempt
        still meets the target's actual state, so a reference somebody else
        moved refuses at the swap rather than being overwritten."""
        from baton_v12.integration.reconciliation import (
            record_publication_intent)
        self.custody()
        self.stopped()
        record_publication_intent(self.coordinator, {
            "managed_result_id": ORCHESTRATION, "phase": "apply",
            "canonical_target_id": coordinator_fixtures.TARGET,
            "entry_id": "entry-1", "lease_id": "lease-1", "fence": self.fence,
            "admitted_old_revision": self.base,
            "imported_revision": self.candidate,
            "content_digest": COLLECTED,
            "derived_proposal_id": "derived-proposal-1",
            "settlement": SETTLEMENT})
        # OUR EFFECT NEVER RAN, and somebody else moved the target onto the
        # very revision we would have imported.
        self.profile.advance(self.repository, reference=self.reference,
                             imported=self.candidate, reviewed=self.base)
        with self.assertRaises(Exception) as caught:
            self.publish()
        self.assertNotIsInstance(caught.exception, RuntimeError)
        self.assertEqual(self.target_owner.recovered[-1]["publication_id"],
                         publication_of(self.coordinator, ORCHESTRATION,
                                        "apply")["publication_id"])
        self.assertEqual(
            publication_of(self.coordinator, ORCHESTRATION,
                           "apply")["state"], "intended")

    def test_a_recorded_swap_is_never_performed_twice(self):
        """Interrupted after the swap was RECORDED and before the settlement,
        with the target moved back to the base afterwards. A recorded swap is
        never performed a second time, and settling over a target that no
        longer holds what we published is refused rather than papered over."""
        self.custody()
        self.stopped()
        import integration_placement as placement_module
        real = placement_module.settle_integrated

        def interrupted(*argv, **named):
            raise RuntimeError("the process died before settling")

        try:
            placement_module.settle_integrated = interrupted
            with self.assertRaises(RuntimeError):
                self.publish()
        finally:
            placement_module.settle_integrated = real
        self.assertEqual(
            publication_of(self.coordinator, ORCHESTRATION,
                           "apply")["state"], "swapped")
        # SOMEBODY MOVES THE TARGET BACK.
        self.profile.advance(self.repository, reference=self.reference,
                             imported=self.base, reviewed=self.candidate)
        self.assertEqual(self.standing(), self.base)
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("is recorded and the target now stands at",
                      str(caught.exception))
        self.assertIn("never performed a second time", str(caught.exception))
        self.assertEqual(self.standing(), self.base)


class ThePublicationRowIsNotAnAccountWithoutItsActs(PlacementCase):
    """[P1] Review 2026-09-14T00:17:42Z: the row derived its own identity and
    nothing else was checked.

    The identity deliberately excludes `state`, because the state changes
    while the publication stays the same one -- so editing `intended` to
    `settled` was accepted by the reader AND by the placement's replay, and
    deleting the creating intent act left the row reading normally. A row is
    not an account of an act until the act is there.
    """

    def published(self):
        self.custody()
        self.stopped()
        return self.publish()

    def test_a_state_nobody_journalled_is_refused_on_read_and_on_replay(self):
        self.custody()
        self.stopped()
        from baton_v12.integration.reconciliation import (
            record_publication_intent)
        record_publication_intent(self.coordinator, {
            "managed_result_id": ORCHESTRATION, "phase": "apply",
            "canonical_target_id": coordinator_fixtures.TARGET,
            "entry_id": "entry-1", "lease_id": "lease-1", "fence": self.fence,
            "admitted_old_revision": self.base,
            "imported_revision": self.candidate,
            "content_digest": COLLECTED,
            "derived_proposal_id": "derived-proposal-1",
            "settlement": SETTLEMENT})
        self.coordinator._connection.execute(
            "UPDATE managed_publications SET state = 'settled' "
            "WHERE managed_result_id = ?", (ORCHESTRATION,))
        with self.assertRaises(ContractRefusal) as caught:
            publication_of(self.coordinator, ORCHESTRATION, "apply")
        self.assertIn("this store holds no act", str(caught.exception))
        # AND THE PLACEMENT REFUSES THROUGH THE SAME OWNER, with the target
        # still at the base: no swap was inferred from a state nobody
        # journalled.
        with self.assertRaises(ContractRefusal):
            self.publish()
        self.assertEqual(self.standing(), self.base)

    def test_a_row_whose_state_is_behind_its_journal_is_refused(self):
        self.published()
        self.coordinator._connection.execute(
            "UPDATE managed_publications SET state = 'intended' "
            "WHERE managed_result_id = ?", (ORCHESTRATION,))
        with self.assertRaises(ContractRefusal) as caught:
            publication_of(self.coordinator, ORCHESTRATION, "apply")
        self.assertIn("is behind its own journal", str(caught.exception))

    def test_a_deleted_intent_act_refuses(self):
        held = self.published()
        self.assertEqual(held["outcome"], "published")
        row = self.coordinator._connection.execute(
            "SELECT publication_id FROM managed_publications").fetchone()[0]
        self.coordinator._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            ("result.managed:" + row,))
        with self.assertRaises(ContractRefusal) as caught:
            publication_of(self.coordinator, ORCHESTRATION, "apply")
        self.assertIn("nobody is recorded as having written",
                      str(caught.exception))

    def test_a_deleted_effect_act_refuses(self):
        self.published()
        row = self.coordinator._connection.execute(
            "SELECT publication_id FROM managed_publications").fetchone()[0]
        self.coordinator._connection.execute(
            "DELETE FROM operations WHERE operation_id = ?",
            ("result.managed:" + row + "/settled",))
        with self.assertRaises(ContractRefusal) as caught:
            publication_of(self.coordinator, ORCHESTRATION, "apply")
        self.assertIn("nobody is recorded as having written",
                      str(caught.exception))

    def test_an_edited_operand_no_longer_names_its_own_act(self):
        self.published()
        self.coordinator._connection.execute(
            "UPDATE managed_publications SET lease_id = ? "
            "WHERE managed_result_id = ?", ("lease-elsewhere", ORCHESTRATION))
        with self.assertRaises(ContractRefusal) as caught:
            publication_of(self.coordinator, ORCHESTRATION, "apply")
        self.assertIn("does not derive its own identity",
                      str(caught.exception))


class ARecoveryIsNotACompletionCheck(PlacementCase):
    """[P1] Review 2026-09-14T00:35:44Z: a receipt proves a PAST effect.

    The target was read before the recovery, so a reference moved back to the
    admitted revision in between was settled as `integrated` while holding
    none of this publication's content. A receipt says what once happened; it
    does not say what the target holds now.

    AND A RECOVERY IS AN EFFECT-CAPABLE CALL on another owner. The grant is
    proved after it, immediately before the apply -- your own probe released
    this lease from inside a `recover`, and the placement applied anyway.
    """

    def interrupt_after_effect(self):
        import integration_placement as placement_module
        real = placement_module.record_publication_effect

        def interrupted(store, publication_id, state):
            if state == "swapped":
                raise RuntimeError("the process died after the effect")
            return real(store, publication_id, state)

        try:
            placement_module.record_publication_effect = interrupted
            with self.assertRaises(RuntimeError):
                self.publish()
        finally:
            placement_module.record_publication_effect = real

    def test_a_receipt_for_content_the_target_no_longer_holds_refuses(self):
        self.custody()
        self.stopped()
        self.interrupt_after_effect()
        # SOMEBODY MOVES IT BACK before the retry.
        self.profile.advance(self.repository, reference=self.reference,
                             imported=self.base, reviewed=self.candidate)
        self.assertEqual(self.standing(), self.base)
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("a receipt proves what once happened",
                      str(caught.exception))
        # NOTHING SETTLED AND NOTHING WAS APPLIED AGAIN.
        self.assertEqual(self.standing(), self.base)
        self.assertEqual(len(self.target_owner.asked), 1)
        self.assertEqual(
            [one["state"] for one in
             entries_of(self.coordinator, coordinator_fixtures.TARGET)
             if one["entry_id"] == "entry-1"], ["leased"])

    def test_the_target_moving_during_recovery_is_caught(self):
        """The same window, with the movement happening inside the recovery
        call itself rather than before it."""
        self.custody()
        self.stopped()
        self.interrupt_after_effect()
        moved = []

        def moving(request):
            if not moved:
                moved.append(True)
                self.profile.advance(self.repository,
                                     reference=self.reference,
                                     imported=self.base,
                                     reviewed=self.candidate)
            return TargetOwner.recover(self.target_owner, request)

        self.target_owner.recover = moving
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("a receipt proves what once happened",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)

    def test_a_grant_lost_during_recovery_stops_the_apply(self):
        """[P1] A `recover` can change the world. The grant is proved after
        it, immediately before the apply."""
        from baton_v12.integration import refuse_entry
        from baton_v12.integration.reconciliation import (
            record_publication_intent)
        self.custody()
        self.stopped()
        record_publication_intent(self.coordinator, {
            "managed_result_id": ORCHESTRATION, "phase": "apply",
            "canonical_target_id": coordinator_fixtures.TARGET,
            "entry_id": "entry-1", "lease_id": "lease-1", "fence": self.fence,
            "admitted_old_revision": self.base,
            "imported_revision": self.candidate,
            "content_digest": COLLECTED,
            "derived_proposal_id": "derived-proposal-1",
            "settlement": SETTLEMENT})

        def ending(request):
            refuse_entry(self.coordinator, lease_id="lease-1",
                         canonical_target_id=coordinator_fixtures.TARGET,
                         entry_id="entry-1", fence=self.fence,
                         settlement={"reason": "policy",
                                     "detail": {"why": "withdrawn"}})
            return TargetOwner.recover(self.target_owner, request)

        self.target_owner.recover = ending
        with self.assertRaises(ContractRefusal):
            self.publish()
        # THE APPLY WAS NEVER REACHED and the target never moved.
        self.assertEqual(self.target_owner.asked, [])
        self.assertEqual(self.standing(), self.base)

    def test_a_grant_lost_before_a_fresh_apply_stops_it_too(self):
        from baton_v12.integration import refuse_entry
        self.custody()
        self.stopped()

        def ending():
            refuse_entry(self.coordinator, lease_id="lease-1",
                         canonical_target_id=coordinator_fixtures.TARGET,
                         entry_id="entry-1", fence=self.fence,
                         settlement={"reason": "policy",
                                     "detail": {"why": "withdrawn"}})

        self.materializer.before = ending
        with self.assertRaises(ContractRefusal):
            self.publish()
        self.assertEqual(self.target_owner.asked, [])
        self.assertEqual(self.standing(), self.base)


class WhateverIsCheckedLastIsWhatIsTrue(PlacementCase):
    """[P1] Review 2026-09-14T00:41:55Z: two more windows, both from ordering.

    Reading the reference is itself a call that takes time, so a grant proved
    BEFORE that read was already stale when the apply ran. And an owner's
    `applied` answer can be TRUTHFUL while the target has moved between its
    effect and its reply -- the answer accounts for what that owner did, not
    for what happened afterwards.
    """

    def test_a_grant_released_during_the_final_target_read_stops_it(self):
        from baton_v12.integration import refuse_entry
        self.custody()
        self.stopped()
        released = []
        real = self.profile.revision

        def reading(repository, reference):
            answer = real(repository, reference)
            if not released:
                released.append(True)
                refuse_entry(self.coordinator, lease_id="lease-1",
                             canonical_target_id=coordinator_fixtures.TARGET,
                             entry_id="entry-1", fence=self.fence,
                             settlement={"reason": "policy",
                                         "detail": {"why": "withdrawn"}})
            return answer

        self.profile.revision = reading
        with self.assertRaises(ContractRefusal):
            self.publish()
        # THE APPLY WAS NEVER REACHED: the grant is proved after the read.
        self.assertEqual(self.target_owner.asked, [])
        self.assertEqual(real(self.repository, self.reference), self.base)

    def test_a_truthful_applied_reply_after_foreign_movement_refuses(self):
        """The owner really did apply, and by the time it answered somebody
        else had moved the target. The effect is retained and never repeated,
        and the entry is not settled over content the target does not hold."""
        self.custody()
        self.stopped()

        def moving(request):
            answer = TargetOwner.apply(self.target_owner, request)
            # AFTER the real advance and before the reply reaches us.
            self.profile.advance(self.repository, reference=self.reference,
                                 imported=self.base,
                                 reviewed=request["imported_revision"])
            return answer

        self.target_owner.apply = moving
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("is recorded and is never repeated",
                      str(caught.exception))
        self.assertEqual(self.standing(), self.base)
        # THE EFFECT IS RETAINED: the publication records its swap, so a later
        # attempt resumes rather than applying a second time.
        self.assertEqual(
            publication_of(self.coordinator, ORCHESTRATION,
                           "apply")["state"], "swapped")
        self.assertEqual(
            [one["state"] for one in
             entries_of(self.coordinator, coordinator_fixtures.TARGET)
             if one["entry_id"] == "entry-1"], ["leased"])

    def test_the_completion_check_covers_the_recorded_swap_path_too(self):
        """One check, after every owner call and all effect bookkeeping,
        shared by the fresh, recovered and already-recorded paths."""
        self.custody()
        self.stopped()
        import integration_placement as placement_module
        real = placement_module.settle_integrated

        def interrupted(*argv, **named):
            raise RuntimeError("the process died before settling")

        try:
            placement_module.settle_integrated = interrupted
            with self.assertRaises(RuntimeError):
                self.publish()
        finally:
            placement_module.settle_integrated = real
        self.assertEqual(
            publication_of(self.coordinator, ORCHESTRATION,
                           "apply")["state"], "swapped")
        self.profile.advance(self.repository, reference=self.reference,
                             imported=self.base, reviewed=self.candidate)
        with self.assertRaises(ContractRefusal) as caught:
            self.publish()
        self.assertIn("never performed a second time", str(caught.exception))
        self.assertEqual(self.standing(), self.base)


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
