"""W39358 — the dogfood operator's composed halves, without a daemon.

`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/
finding-minimal-supervised-operator/`.

WHAT THIS FILE COVERS AND WHAT IT DOES NOT, said at the top because the
distinction is the honest part of this round. It covers the four units the
operator composes FROM: the deployment authority-session facade, the bounded
source staging, the frozen task read on the way in, and the two
manager-authored protocol documents. The composed ARC -- offer through
absence -- is not built yet and therefore is not tested here; `PROGRESS.md`
says so rather than leaving a reader to infer it from an absent class.

NO DAEMON AND NO CREDENTIAL. Everything here is a pure function over
directories and documents, which is what makes it worth running on every
change rather than only where Docker is reachable.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from baton_v12.contracts import (ContractRefusal, digest,     # noqa: E402
                                 live_secret)

from tools import dogfood_operator                            # noqa: E402
from tests.manager import test_intake as intake_fixture       # noqa: E402
from tests.manager import test_output as output_fixture       # noqa: E402
from tools.dogfood_operator import (DeploymentSession, OperatorRefusal,
                                    assignment_manifest, frozen_task,
                                    input_manifest, stage_source)  # noqa: E402

WORK_REF = {"authority_uuid": "43c55d4b1234567890abcdef12345678",
            "work_id": "43c55d4b-W1439"}
NOW = "2026-08-30T00:00:00.000Z"
PROFILE = "sha256:" + "6" * 64
ROLE = "sha256:" + "2" * 64
TOOLCHAIN = "sha256:" + "4" * 64
IMAGE = "sha256:" + "5" * 64
POLICIES = {one: "sha256:" + f"{index}" * 64
            for index, one in enumerate(dogfood_operator.POLICY_DIGESTS,
                                        start=1)}
BINDING = {"root": "baton-repository",
           "path": "work/records/2026/08/finding-v12-first-useful-dogfood-task",
           "finding_digest": "sha256:" + "d" * 64,
           "plan_digest": "sha256:" + "e" * 64}
HUMAN = {"artifact_id": "human-contract-1", "media_type": "text/markdown",
         "bytes": 1200, "content_digest": "sha256:" + "b" * 64,
         "locator": "artifact://contracts/human-contract-1"}

# THE EXACT ASSIGNMENT the arc is about, in the shape the authority names.
EXPECT = {"work_ref": dict(WORK_REF), "participant": "baton.claude",
          "generation": 1}


class TheIndependentDerivationReadsReceiptLocators(unittest.TestCase):
    """A real intake receipt names local custody with a `file://` URI."""

    def test_every_present_proposal_member_is_read_below_the_uri(self):
        home = tempfile.mkdtemp(prefix="v12-derived-uri-")
        self.addCleanup(shutil.rmtree, home, True)
        source = os.path.join(home, "source")
        proposal = os.path.join(home, "proposal")
        candidate = os.path.join(proposal, "candidate")
        os.makedirs(source)
        os.makedirs(candidate)
        for root in (source, candidate):
            with open(os.path.join(root, "harness.py"), "w",
                      encoding="utf-8") as writing:
                writing.write("print('verified')\n")
        for name in ("change.patch", "result.json", "verification.txt"):
            with open(os.path.join(proposal, name), "w",
                      encoding="utf-8") as writing:
                writing.write("fixture\n")

        derived = dogfood_operator._derived(
            "file://" + proposal,
            {"verification": [sys.executable, "harness.py"]}, source)

        self.assertEqual(derived["members_present"],
                         sorted(dogfood_operator.PROPOSAL_MEMBERS))


class PassingSession:
    """A deployment session that records the one act M44657 added.

    Only `pass_work` is exercised: the manager's seven operations reach the
    authority through `AuthorityPort`, which these cases inject separately.
    """

    def __init__(self, route="rview", order=None):
        self.participant = "baton.claude"
        self.passes = []
        self.route = route
        self.answer = None
        self.order = [] if order is None else order

    def pass_work(self, operands):
        # ONE OPERAND DOCUMENT, as a real `Session` takes. This fake accepted
        # keywords for fifteen rounds and taught the deployment a shape no
        # authority has; the real-authority gate is what found it.
        self.order.append("pass")
        self.passes.append(dict(operands))
        if isinstance(self.answer, BaseException):
            raise self.answer
        if self.answer is not None:
            return self.answer
        # THE CLOSED RESULT the authority actually answers with, so a case
        # that means to vary ONE member varies one member.
        return {"route": self.route, "cause": "pass", "phase": "queued",
                "gate": None, "fenced": False,
                "assignment": dict(operands["expect"])}


TASK = {"schema": "baton.dogfood-task/1",
        "task_id": "w39364-ping-pong-coverage",
        "instructions": "Add focused unit coverage for _observed_readable.",
        "verification": ["python3", "harness.py"],
        "source_root": "source"}


class OperatorCase(unittest.TestCase):

    def setUp(self):
        home = tempfile.mkdtemp(prefix="v12-w39358-")
        self.addCleanup(shutil.rmtree, home, True)
        self.home = home
        self.source = os.path.join(home, "source")
        os.makedirs(self.source)
        self.write(os.path.join(self.source, "harness.py"),
                   "print('the staged harness')\n")
        self.write(os.path.join(self.source, "nested", "preflight.py"),
                   "def _observed_readable():\n    return True\n")
        self.inputs = os.path.join(home, "inputs")
        os.makedirs(self.inputs)

    @staticmethod
    def write(place, body):
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write(body)

    def task(self, document=TASK):
        place = os.path.join(self.home, "task.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        return place


class OneSession(unittest.TestCase):
    """The facade, and the one member it deliberately does not carry."""

    class Session:
        participant = "baton.claude"

        def __init__(self):
            self.seen = []

        def __getattr__(self, name):
            # KEYWORDS TOO, since M44657's pass is named-operand shaped where
            # the manager's seven are positional-document shaped.
            def call(*arguments, **operands):
                self.seen.append((name, arguments))
                return {"answered": name}
            return call

    def test_the_six_operations_delegate_to_the_minted_session(self):
        held = self.Session()
        facade = DeploymentSession(held)
        for member in ("project_work", "slot_holder", "claim",
                       "settle_operation", "assignment_of", "cancel"):
            with self.subTest(member=member):
                self.assertEqual(getattr(facade, member)({"a": 1}),
                                 {"answered": member})
        self.assertEqual([one for one, _a in held.seen],
                         ["project_work", "slot_holder", "claim",
                          "settle_operation", "assignment_of", "cancel"])

    def test_the_bound_identity_is_read_from_the_session(self):
        """Read rather than configured: a deployment that named a participant
        of its own would be binding an authorization to an identity the
        authority never minted one for."""
        self.assertEqual(DeploymentSession(self.Session()).participant,
                         "baton.claude")

    def test_publishing_an_answer_is_a_typed_refusal(self):
        """This pilot runs no `inquire`, so a no-op would answer 'published'
        to something nobody published."""
        with self.assertRaises(OperatorRefusal) as caught:
            DeploymentSession(self.Session()).publish_answer({"a": 1})
        self.assertIn("runs no `inquire`", str(caught.exception))

    def test_the_refusal_is_not_a_contract_refusal(self):
        """A deployment saying it does not carry a capability is a different
        fact from the manager judging its own contract, and an operator that
        conflated them would read a composition mistake as a protocol one."""
        self.assertFalse(issubclass(OperatorRefusal, ContractRefusal))

    def test_a_session_missing_an_operation_is_refused_at_construction(self):
        """`AuthorityPort` checks its seven at construction for the reason
        this does: discovering halfway through an offer that the session
        cannot claim is discovering it after durable state depends on it."""
        class Partial:
            participant = "baton.claude"

            def claim(self, *documents):
                return {}

        with self.assertRaises(OperatorRefusal) as caught:
            DeploymentSession(Partial())
        self.assertIn("no callable", str(caught.exception))

    def test_the_review_pass_delegates_like_every_other_member(self):
        """Approver ruling M44657 added an EIGHTH member, and it is not the
        manager's: the port names seven and ignores the rest, so the pass
        lives on this deployment's own facade over its own minted session.

        Delegated rather than composed, because the authority owns what a pass
        means -- it moves the Route and ends the assignment in one act.
        """
        held = self.Session()
        facade = DeploymentSession(held)

        answered = facade.pass_work({"expect": {"generation": 1},
                                     "operation_id": "pass:1",
                                     "to_route": "rview", "comment": "done"})

        self.assertEqual(answered, {"answered": "pass_work"})
        self.assertEqual([one for one, _a in held.seen], ["pass_work"])

    def test_the_facade_refuses_when_the_minted_session_cannot_pass(self):
        """A callable facade method is not an underlying capability.

        The pass is part of this deployment's mandatory success arc. If the
        minted session lacks it, wrapping that session must refuse before the
        facade can pass preflight and discover the missing operation only
        after staging, runtime execution, intake and retention.
        """
        held = self.Session()
        held.pass_work = None

        with self.assertRaises(OperatorRefusal) as caught:
            DeploymentSession(held)

        self.assertIn("pass_work", str(caught.exception))

    def test_the_pass_is_not_one_of_the_operations_the_port_requires(self):
        """It is the deployment's act, not the manager's, and the seven the
        port checks are unchanged by it."""
        self.assertNotIn("pass_work", SESSION_OPERATIONS_UNDER_TEST)

    def test_the_facade_carries_every_operation_the_port_names(self):
        """The port's list is the contract; a facade that fell behind it would
        be refused by the manager rather than by this test, which is later and
        more expensive."""
        facade = DeploymentSession(self.Session())
        for member in SESSION_OPERATIONS_UNDER_TEST:
            with self.subTest(member=member):
                self.assertTrue(callable(getattr(facade, member, None)),
                                member)


SESSION_OPERATIONS_UNDER_TEST = tuple(
    __import__("baton_v12.worker_manager.authority_port", fromlist=["x"])
    .SESSION_OPERATIONS)


class TheArcIsEffectivelyOnceAndAFreshAttemptIsFresh(OperatorCase):
    """The acceptance's third bullet, over REAL manager effectively-once.

    Nothing here mocks the operations that own the property under test.
    `record_attempt`, `submit_claim` and `request_runtime_start` run against a
    real `ControlStore`, because "an exact replay cannot start a second
    runtime" is a claim about the journal and a test that mocked the journal
    would be asserting its own mock.

    What IS supplied is the world outside the manager: an authority session,
    an engine adapter and the worker conversation. Those are other Work's
    boundaries and this case is not about them.
    """

    class Adapter:
        """An engine that counts what it was actually asked to do."""

        def __init__(self, runtime_id="runtime-1"):
            self.runtime_id = runtime_id
            self.started = []
            self.stops = []
            self.abandoned = []
            self.normalized = []
            self.observation = {"state": "running", "why": "up",
                                "mounts": None}

        custodian_image_digest = "sha256:" + "c" * 64

        def normalize_directory(self, store, *, assignment_id, which):
            from baton_v12.worker_manager import custody

            self.normalized.append((assignment_id, which))
            return custody._answered(
                "normalize", 0,
                {"custody": "normalize", "entries": 0, "not_ours": 0,
                 "running_as": [0, 0]}, None)

        def start(self, operands):
            self.started.append(dict(operands))
            return {"runtime_id": self.runtime_id,
                    "labels": operands["labels"]}

        def list(self, operands):
            if not self.started:
                return []
            return [{"runtime_id": self.runtime_id,
                     "labels": self.started[0]["labels"]}]

        def observe(self, runtime_id):
            return dict(self.observation, runtime_id=runtime_id)

        def stop(self, request):
            self.stops.append(dict(request))
            return {"runtime_id": request["runtime_id"], "ordered": True,
                    "state": "quiescent", "why": "stopped"}

        def destroy_abandoned(self, command):
            # W44716's ending, so an unanswered attempt SETTLES and gives its
            # runtime lane back. Without it the manager correctly refuses to
            # start a successor over one assignment's unsettled material --
            # which is the rule, not a fixture inconvenience.
            self.abandoned.append(dict(command))
            return {"runtime_id": command["runtime_id"], "state": "absent",
                    "why": "the abandoned runtime is absent",
                    "credentials": {"lifecycle_state": "not-delivered"},
                    "launch": {"lifecycle_state": "not-delivered"}}

    def store(self, incarnation="operator-1"):
        from baton_v12.worker_manager import ControlStore, certify_profile

        store = ControlStore.open(
            os.path.join(self.home, "control.sqlite3"),
            incarnation=incarnation, clock=lambda: NOW)
        self.addCleanup(store.close)
        certify_profile(store, "runtime", "dogfood", PROFILE)
        # W43975: every ending settles on a directory-custody receipt.
        from baton_v12.worker_manager.workspaces import (
            configure_workspace_storage)
        place = os.path.join(self.home, "storage")
        os.makedirs(place, exist_ok=True)
        configure_workspace_storage(store, place)
        return store

    def authority(self):
        from baton_v12.authority import claim_signature
        from baton_v12.worker_manager import AuthorityPort

        session = ArcSession()
        return session, AuthorityPort(session, claim_signature)

    def attempt(self, store, port, session, adapter, *, attempt_id,
                converse=None, patches, credential_delivery=None,
                adapter_of=None):
        """One whole arc, with only the world outside the manager supplied."""
        from baton_v12.worker_manager import worker_entry

        spoken = converse if converse is not None else {
            "ending": "lost", "why": "the provider was never authorized",
            "answers": []}
        patches.enter_context(mock.patch.object(
            worker_entry, "converse", return_value=spoken))
        patches.enter_context(mock.patch.object(
            dogfood_operator, "_configured_group",
            return_value=self.group(store)))
        from baton_v12.worker_manager import launch

        patches.enter_context(mock.patch.object(
            launch, "materialize", return_value=object()))
        storage = os.path.join(self.home, "storage")
        os.makedirs(storage, exist_ok=True)
        os.makedirs(os.path.join(self.home, "launch"), exist_ok=True)
        return dogfood_operator.run_dogfood_task(
            engine="docker", run=lambda _argv: None,
            open_channel=lambda _argv: None, store=store, port=port,
            session=session, review_route="rview",
            adapter_of=(adapter_of if adapter_of is not None
                        else lambda **_operands: adapter),
            attempt_id=attempt_id, offer_id=f"offer-{attempt_id}",
            source=self.source, task_path=self.task(),
            storage=os.path.join(self.home, "storage"),
            launch_home=os.path.join(self.home, "launch"),
            credential_delivery=(credential_delivery
                                 if credential_delivery is not None
                                 else object()),
            image_digest=IMAGE,
            network="baton-dogfood", work_ref=WORK_REF,
            participant="baton.claude", generation=1, now=NOW,
            policies=POLICIES, record_binding=BINDING,
            assignment_contract="v12-assignment-1", human_contract=HUMAN,
            role_instructions_digest=ROLE, runtime_profile_digest=PROFILE,
            toolchain_digest=TOOLCHAIN, adapter_digest=IMAGE,
            adapter_name="oci", labels={"attempt": attempt_id},
            retention_policy_digest=POLICIES["retention_policy_digest"],
            retention_disposition="discard-after-intake",
            bearer="one-use-bearer")

    def group(self, store):
        """The manager's OWN record of the deployment's configured group.

        Reusing the manager suite's fixture rather than a second spelling: a
        fixture cannot mint a `WorkspaceGroup` any more than a caller can, it
        has to configure one and then read the record back.
        """
        from tests.manager.input_roots import configured_group

        return configured_group(store)

    def test_an_exact_replay_starts_no_second_runtime_or_provider_turn(self):
        """THE ACCEPTANCE, and HOW this deployment actually delivers it.

        The same operands twice. The property required is that a replay start
        no second runtime and open no second provider turn, and this arc keeps
        it by REFUSING BEFORE EITHER: `stage_source` will not stage into an
        input root that already holds a delivery the manager has measured, so
        the second run stops at the delivery half.

        That is a stronger guarantee than the manager's own effectively-once
        would give here and a narrower capability. It is recorded as a
        limitation in the dossier rather than dressed up as resumption: an
        interrupted attempt is not continued by re-running this command, it is
        rerun under a fresh attempt identity.
        """
        store = self.store()
        session, port = self.authority()
        adapter = self.Adapter()
        with ExitStack() as patches:
            first = self.attempt(store, port, session, adapter,
                                 attempt_id="attempt-1", patches=patches)

        with ExitStack() as patches:
            with self.assertRaises(OperatorRefusal) as caught:
                self.attempt(store, port, session, adapter,
                             attempt_id="attempt-1", patches=patches)

        self.assertIn("stages its source once", str(caught.exception))
        self.assertEqual(len(adapter.started), 1,
                         "an exact replay started a second runtime")
        self.assertEqual(len(session.turns()), 1,
                         "an exact replay opened a second provider turn")
        self.assertEqual(first["runtime_id"], "runtime-1")

    def test_a_fresh_attempt_receives_fresh_roots_and_fresh_credentials(self):
        """Acceptance: fresh ROOTS and fresh CREDENTIALS, both observed.

        Review 2026-08-30T12:40:47Z [P1]: the previous case proved distinct
        workspace paths and left the credential half to a coincidence -- the
        helper happened to build a new opaque object per call and nothing
        looked at it. A delivery nobody observes is not a delivery this case
        proved fresh, so each attempt now carries a NAMED one and the adapter
        factory records what it was actually handed.
        """
        store = self.store()
        session, port = self.authority()
        seen = []

        def watching(**operands):
            seen.append(operands["credential_delivery"])
            return operands["adapter"]

        for attempt_id, runtime_id in (("attempt-1", "runtime-1"),
                                       ("attempt-2", "runtime-2")):
            adapter = self.Adapter(runtime_id=runtime_id)
            with ExitStack() as patches:
                self.attempt(store, port, session, adapter,
                             attempt_id=attempt_id, patches=patches,
                             credential_delivery=f"delivery-{attempt_id}",
                             adapter_of=lambda **operands: watching(
                                 adapter=adapter, **operands))

        self.assertEqual(seen, ["delivery-attempt-1", "delivery-attempt-2"],
                         "an attempt was launched with another attempt's "
                         "credential delivery")

    def test_a_fresh_attempt_receives_fresh_roots(self):
        """The other half: a NEW attempt is not a replay of the old one.

        Different attempt identity, different workspace roots -- which is what
        keeps one attempt's candidate tree out of the next one's evidence.
        """
        store = self.store()
        session, port = self.authority()

        with ExitStack() as patches:
            first = self.attempt(store, port, session, self.Adapter(),
                                 attempt_id="attempt-1", patches=patches)
        with ExitStack() as patches:
            second = self.attempt(store, port, session,
                                  self.Adapter(runtime_id="runtime-2"),
                                  attempt_id="attempt-2", patches=patches)

        self.assertNotEqual(first["attempt_id"], second["attempt_id"])
        from baton_v12.worker_manager import workspaces

        roots = [workspaces.assignment_workspace(
                     self.group(store), os.path.join(self.home, "storage"),
                     one)["workspace"]
                 for one in ("attempt-1", "attempt-2")]
        self.assertNotEqual(roots[0], roots[1],
                            "two attempts shared one workspace root")
        for root in roots:
            self.assertTrue(os.path.isdir(root))


class ArcSession:
    """The authority half of the world, recorded rather than journalled.

    The manager's seven operations plus M44657's pass. It answers what a real
    authority answers so the manager's own rules run for real; what it does
    not do is decide anything the manager would.
    """

    def __init__(self, participant="baton.claude"):
        self.participant = participant
        self.calls = []
        self.assignment = {"work_ref": dict(WORK_REF),
                           "participant": participant, "generation": 1}

    # THE AUTHORITY'S OWN VOCABULARY, reused from the manager suite rather
    # than approximated: the claim decision is held to a closed member set and
    # a fixture that invented one would be testing its own invention.
    SCOPE = "scope:deployment"
    ROUTE = "baton.impl"
    PRINCIPAL = "principal:org-a"

    def project_work(self, work_id):
        self.calls.append(("project_work", work_id))
        return {"status": "open", "phase": "queued", "handler": None,
                "gate": None, "authority_uuid": WORK_REF["authority_uuid"],
                "scope": self.SCOPE, "route": self.ROUTE}

    def slot_holder(self, participant):
        self.calls.append(("slot_holder", participant))
        return None

    def assignment_of(self, work_id):
        self.calls.append(("assignment_of", work_id))
        return dict(self.assignment)

    def claim(self, operands):
        self.calls.append(("claim", dict(operands)))
        return {"assignment": dict(self.assignment), "claim_event": 44,
                "decision": {"endpoint": self.participant,
                             "principal": self.PRINCIPAL,
                             "effective_scope": self.SCOPE,
                             "role": self.ROUTE, "grant": "direct",
                             "policy_generation": 1}}

    def settle_operation(self, operands):
        self.calls.append(("settle_operation", dict(operands)))
        return {"kind": "live", "record": None}

    def cancel(self, operands):
        self.calls.append(("cancel", dict(operands)))
        return {"cause": "cancelled", "assignment": dict(self.assignment),
                "phase": "block", "gate": "runtime-quiescence:1",
                "fenced": True}

    def publish_answer(self, operands):
        self.calls.append(("publish_answer", dict(operands)))
        return "baton:M1"

    def turns(self):
        """Every act that opens an assignment's provider turn."""
        return [one for one in self.calls if one[0] == "claim"]

    def pass_work(self, operands):
        self.calls.append(("pass_work", dict(operands["expect"]),
                           operands["to_route"]))
        return {"assignment": dict(operands["expect"]),
                "route": operands["to_route"], "cause": "pass",
                "phase": "queued", "gate": None, "fenced": False}


class TheEvidenceRecordIsHeldBeforeItIsDurable(OperatorCase):
    """The one document that leaves this process and lands on a disk."""

    def record(self, **overrides):
        given = {one: None for one in dogfood_operator.EVIDENCE_MEMBERS}
        given.update({"schema": "baton.dogfood-evidence/1",
                      "attempt_id": "attempt-1", "resolved": True,
                      "intake_receipt": True, "unresolved": []})
        given.update(overrides)
        return given

    def place(self):
        return os.path.join(self.home, "evidence.json")

    def test_a_complete_record_is_written_and_reads_back(self):
        written = dogfood_operator.write_evidence(self.record(), self.place())

        with open(written, "rb") as reading:
            read_back = json.loads(reading.read().decode("utf-8"))
        self.assertEqual(sorted(read_back),
                         sorted(dogfood_operator.EVIDENCE_MEMBERS))
        self.assertEqual(read_back["attempt_id"], "attempt-1")

    def test_a_live_bearer_anywhere_in_the_record_refuses_the_write(self):
        """Section 13, over the WHOLE document at any depth.

        The likeliest carrier is not a member holding a secret on purpose --
        it is a refusal message that interpolated one, which is exactly why
        the sweep is containment-based and why it runs before the shape check.
        """
        from baton_v12.contracts.secrets import held_secret

        with held_secret("one-use-bearer"):
            for spoiled in (
                    self.record(unresolved=["the start failed with "
                                            "one-use-bearer"]),
                    self.record(custody=[{"artifact_id": "one-use-bearer"}]),
                    self.record(conversation={"why": "one-use-bearer"})):
                with self.subTest(where=sorted(spoiled)[0]):
                    with self.assertRaises(OperatorRefusal) as caught:
                        dogfood_operator.write_evidence(spoiled, self.place())
                    self.assertIn("will not be written",
                                  str(caught.exception))
                    self.assertFalse(os.path.exists(self.place()),
                                     "a refused record was written anyway")

    def test_a_live_bearer_in_a_retained_record_refuses_before_retry(self):
        """The read boundary needs the write boundary's whole-document
        secret sweep, not only its member names.

        A retained file is operator-editable.  Letting a registered bearer in
        an allowed member reach the retry would expose it to authority and
        manager refusal/journal surfaces before the final writer got another
        chance to reject it.
        """
        from baton_v12.contracts.secrets import held_secret

        with open(self.place(), "wb") as writing:
            writing.write(json.dumps(self.record(
                unresolved=["retry failed with one-use-bearer"]
            )).encode("utf-8"))

        with held_secret("one-use-bearer"):
            with self.assertRaises(OperatorRefusal) as caught:
                dogfood_operator.read_evidence(self.place())

        self.assertIn("retained evidence", str(caught.exception))

    def test_a_member_nobody_decided_to_keep_is_refused(self):
        """An upstream member added without thought would otherwise ride out
        to a durable file unexamined, which is how raw provider text reached
        `result.json` in W39357."""
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.write_evidence(
                self.record(provider_stderr="..."), self.place())
        self.assertIn("unexpected provider_stderr", str(caught.exception))
        self.assertFalse(os.path.exists(self.place()))

    def test_a_missing_member_is_refused_rather_than_written_partial(self):
        incomplete = self.record()
        del incomplete["runtime_id"]
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.write_evidence(incomplete, self.place())
        self.assertIn("missing runtime_id", str(caught.exception))

    def test_an_unbounded_record_is_refused_before_the_write(self):
        """A durable write driven by a failure path is bounded like every
        other durable thing here."""
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.write_evidence(
                self.record(unresolved=["x" * (
                    dogfood_operator.MAX_EVIDENCE_BYTES + 1)]),
                self.place())
        self.assertIn("at most", str(caught.exception))
        self.assertFalse(os.path.exists(self.place()))

    def test_the_write_replaces_atomically_and_leaves_no_scratch(self):
        """A reader never sees a partial record, and a crash mid-write leaves
        the previous one intact."""
        dogfood_operator.write_evidence(self.record(), self.place())
        dogfood_operator.write_evidence(
            self.record(attempt_id="attempt-2"), self.place())

        with open(self.place(), "rb") as reading:
            self.assertEqual(json.loads(reading.read())["attempt_id"],
                             "attempt-2")
        self.assertEqual(
            [one for one in os.listdir(self.home)
             if one.startswith(".evidence-")], [],
            "a staged scratch file survived the write")

    def test_a_refused_record_leaves_no_scratch_file_either(self):
        with self.assertRaises(OperatorRefusal):
            dogfood_operator.write_evidence({"not": "an evidence record"},
                                            self.place())
        self.assertEqual([one for one in os.listdir(self.home)
                          if one.startswith(".evidence-")], [])


class TheDocumentedCommandIsOneGrantsFile(OperatorCase):
    """The acceptance's first bullet: one command, reusable for another task."""

    def grants(self, **overrides):
        given = {one: f"{one}-value" for one in dogfood_operator.GRANT_MEMBERS}
        given.update({"engine": "docker", "generation": 1,
                      "work_ref": dict(WORK_REF), "policies": dict(POLICIES),
                      "record_binding": dict(BINDING),
                      "human_contract": dict(HUMAN), "labels": {"a": "b"},
                      "network": "baton-dogfood", "review_route": "rview",
                      "retention_disposition": "retain",
                      # W51476 review [P1]: `main` now holds every grant it
                      # can judge without a capability BEFORE it builds one,
                      # so these command-level cases carry grants that pass
                      # that boundary. Patching it out instead would be
                      # hiding the act they are meant to run through.
                      "task_path": self.task(),
                      "human_contract": dict(HUMAN),
                      "policies": dict(POLICIES),
                      "record_binding": dict(BINDING),
                      "image_digest": IMAGE,
                      "toolchain_digest": TOOLCHAIN,
                      "runtime_profile_digest": PROFILE,
                      "role_instructions_digest": ROLE})
        given.update(overrides)
        return given

    def written(self, given):
        place = os.path.join(self.home, "grants.json")
        with open(place, "wb") as writing:
            writing.write(json.dumps(given).encode("utf-8"))
        return place

    def test_the_documented_grant_members_are_the_members_this_build_reads(
            self):
        """The prose says the file is the whole of what an operator decides.

        Review 2026-08-30T14:36:46Z [P1]: it then omitted five members the
        launcher requires, so following the documentation exactly produced a
        refusal. Asked of the DOCSTRING rather than restated, because two
        lists that agree today are two lists.
        """
        documented = dogfood_operator.__doc__
        for member in dogfood_operator.GRANT_MEMBERS:
            with self.subTest(member=member):
                self.assertIn(f'"{member}"', documented,
                              "a required grant the command does not name")

    def test_the_launcher_builds_the_seven_capabilities_it_promises(self):
        """The positive launcher-boundary case: the real construction runs.

        Review [P1]: only the missing-grants error had ever executed, so the
        seven-capability build was documented and unexercised. This drives
        `_launched` itself over a real authority store, a real control store
        and a real credential home, and asks what came back.
        """
        from baton_v12.authority import Authority
        from baton_v12.worker_manager import (configure_workspace_group,
                                              credentials)
        from tests.manager.input_roots import deployment_workspace_group

        authority_place = os.path.join(self.home, "authority.sqlite3")
        Authority.create(authority_place,
                         authority_uuid=WORK_REF["authority_uuid"]).dispose()
        storage = os.path.join(self.home, "storage")
        os.makedirs(storage)
        given = self.grants(
            authority_store=authority_place,
            control_store=os.path.join(self.home, "control.sqlite3"),
            incarnation="dogfood-launcher-1",
            credential_home=os.path.join(self.home, "credential-home"),
            credential_slots=["api"],
            credential_profile={"api": {"provider": "vault",
                                        "reference": "kv/one"}},
            participant="baton.claude", storage=storage,
            runtime_profile_digest=PROFILE, adapter_digest=IMAGE)
        os.makedirs(given["credential_home"])
        from baton_v12.worker_manager import ControlStore
        opened = ControlStore.open(given["control_store"],
                                   incarnation=given["incarnation"],
                                   clock=lambda: NOW)
        configure_workspace_group(opened, deployment_workspace_group())
        opened.close()

        built = dogfood_operator._launched(
            given,
            credential_provider=lambda _provider, _reference: "unused")
        # CLOSED, because a case that leaks a store handle is a case that
        # holds a lock on a file the next one opens.
        self.addCleanup(built["open_store"](given["control_store"]).close)

        self.assertEqual(sorted(built),
                         ["adapter_of", "bearer", "closing",
                          "credential_delivery", "open_channel", "open_store",
                          "run", "session"])
        # AND IT SAYS WHAT IT OPENED, so the command can close it: a builder
        # that answered capabilities and kept its handles would leak an
        # authority and a control store on every run.
        self.assertEqual(len(built["closing"]), 2)
        for release in built["closing"]:
            release()
        self.assertTrue(callable(built["adapter_of"]))
        self.assertTrue(callable(built["session"].pass_work),
                        "the facade must carry the eighth member")
        self.assertEqual(built["session"].participant, "baton.claude")
        self.assertNotIn(built["bearer"], json.dumps(given),
                         "the minted bearer reached a durable surface")
        # W55758, approver ruling APPROVE-LAZY (M59057): THIS ASSERTION
        # SUPERSEDES `assertIsInstance(built["credential_delivery"], Delivery)`.
        #
        # Building the bundle used to write the bearer to disk before the arc
        # had recorded, claimed or activated anything, so a process that died
        # in that window left a readable credential with no attempt row and no
        # activated assignment -- and therefore no `label_context` from which
        # a recovery could compose a runtime selector. The ruling moves
        # materialization into `adapter_of`, which the arc calls after
        # activation and before runtime creation, and replaces the shape check
        # with the three TEMPORAL facts that make the window closed:
        #
        #   1. bundle construction leaves no volatile root and no record;
        #   2. the factory materializes exactly once, when it is called; and
        #   3. the adapter receives that delivery and the SAME granted home.
        self.assertIsNone(built["credential_delivery"],
                          "the bundle carried a delivery it had not been "
                          "asked for yet")
        home = credentials.CredentialHome(given["credential_home"])
        self.assertFalse(os.path.lexists(
            home.volatile_root(given["attempt_id"])),
            "building the bundle put a bearer on the host")
        self.assertFalse(os.path.exists(home.state_path(given["attempt_id"])),
                         "building the bundle published a lifecycle record")

    def test_the_launcher_closes_a_partial_build_when_a_later_open_fails(self):
        """Ownership starts when a handle opens, not when the bundle returns.

        Review 2026-08-30T18:34:00Z required every ordinary capability handle
        to close on exception. `main` can close a returned bundle, but a
        `ControlStore.open` failure happens after `_launched` opens Authority
        and before there is a bundle to return. The builder must unwind what
        it already owns on its own refused or faulted construction path.
        """
        from baton_v12.authority import Authority
        from baton_v12.worker_manager import ControlStore

        authority_place = os.path.join(self.home, "partial-authority.sqlite3")
        Authority.create(authority_place,
                         authority_uuid=WORK_REF["authority_uuid"]).dispose()
        opened = Authority.open(authority_place)
        released = mock.Mock(wraps=opened.dispose)
        opened.dispose = released
        self.addCleanup(lambda: opened.dispose()
                        if released.call_count == 0 else None)
        given = self.grants(authority_store=authority_place,
                            control_store=os.path.join(
                                self.home, "never-opened-control.sqlite3"),
                            participant="baton.claude")

        with mock.patch.object(Authority, "open", return_value=opened), \
                mock.patch.object(ControlStore, "open",
                                  side_effect=RuntimeError("open failed")):
            with self.assertRaisesRegex(RuntimeError, "open failed"):
                dogfood_operator._launched(
                    given, credential_provider=lambda _provider, _reference:
                    "unused")

        released.assert_called_once_with()

    def test_a_partial_build_disposes_the_authority_it_already_opened(self):
        """The same property, with the wrapper actually INSTALLED.

        The case above wraps `opened.dispose` in a mock and never assigns it
        onto the instance, so the builder calls the real bound method and the
        wrapper is never reached — no implementation can satisfy it as
        written. This installs the recorder on the object the builder is
        handed, which is what makes the observation possible.
        """
        from baton_v12.authority import Authority
        from baton_v12.worker_manager import ControlStore

        authority_place = os.path.join(self.home, "unwound-authority.sqlite3")
        Authority.create(authority_place,
                         authority_uuid=WORK_REF["authority_uuid"]).dispose()
        opened = Authority.open(authority_place)
        released = mock.Mock(wraps=opened.dispose)
        opened.dispose = released
        self.addCleanup(lambda: released.call_count or opened.dispose())
        given = self.grants(authority_store=authority_place,
                            control_store=os.path.join(
                                self.home, "never-opened.sqlite3"),
                            participant="baton.claude")

        with mock.patch.object(Authority, "open", return_value=opened), \
                mock.patch.object(ControlStore, "open",
                                  side_effect=RuntimeError("open failed")):
            with self.assertRaisesRegex(RuntimeError, "open failed"):
                dogfood_operator._launched(
                    given, credential_provider=lambda _p, _r: "unused")

        released.assert_called_once_with()

    def test_a_complete_grants_file_is_read_back_whole(self):
        given = self.grants()
        self.assertEqual(dogfood_operator.read_grants(self.written(given)),
                         given)

    def test_the_documented_shell_command_reaches_its_grants_boundary(self):
        """The documented invocation must execute, not only define helpers.

        A missing grants path is enough to prove entry: the command must fail
        while opening it. Quiet exit 0 with no evidence means Python merely
        loaded the file and the advertised operator command does not exist.
        """
        missing = os.path.join(self.home, "missing-grants.json")
        evidence = os.path.join(self.home, "evidence.json")

        completed = subprocess.run(
            [sys.executable, dogfood_operator.__file__,
             "--grants", missing, "--evidence", evidence],
            capture_output=True, timeout=30)

        self.assertNotEqual(completed.returncode, 0,
                            "the documented command executed no entrypoint")
        self.assertFalse(os.path.exists(evidence))

    def test_help_names_the_credential_source_the_launcher_requires(self):
        """An explicit input hidden from both the command and its help is
        still an ambient convention, not an operator grant.

        The real launcher consumes ``--credential-file`` before ``main``
        parses the remaining arguments.  The reusable command must expose
        that input to the operator rather than accepting it through an
        undocumented preliminary parser.
        """
        completed = subprocess.run(
            [sys.executable, dogfood_operator.__file__, "--help"],
            capture_output=True, timeout=30)

        self.assertEqual(completed.returncode, 0)
        self.assertIn(b"--credential-file", completed.stdout)

    def test_a_member_this_build_does_not_read_is_refused(self):
        """A member sitting in a file looking like it was honoured is worse
        than a refusal, because an operator believes it."""
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.read_grants(
                self.written(self.grants(bearer="one-use-bearer")))
        self.assertIn("unexpected bearer", str(caught.exception))

    def test_a_missing_grant_is_named_rather_than_defaulted(self):
        given = self.grants()
        del given["review_route"]
        del given["network"]
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.read_grants(self.written(given))
        self.assertIn("missing network, review_route", str(caught.exception))

    def test_a_bearer_pasted_into_the_grants_file_is_refused(self):
        """A grants file is a durable surface an operator edits by hand, and
        the one place a bearer is most likely to be pasted for a moment."""
        from baton_v12.contracts.secrets import held_secret

        with held_secret("one-use-bearer"):
            with self.assertRaises(OperatorRefusal) as caught:
                dogfood_operator.read_grants(
                    self.written(self.grants(attempt_id="one-use-bearer")))
        self.assertIn("will not be used", str(caught.exception))

    def test_a_file_that_is_not_a_json_object_is_refused(self):
        for body in (b"[1, 2]", b"not json at all", b"\xff\xfe"):
            with self.subTest(body=body):
                place = os.path.join(self.home, "grants.json")
                with open(place, "wb") as writing:
                    writing.write(body)
                with self.assertRaises(OperatorRefusal):
                    dogfood_operator.read_grants(place)

    def test_the_command_exits_nonzero_for_an_unresolved_attempt(self):
        """`0` is a resolved attempt and nothing else: an operator scripting
        this reads the status before the file."""
        place = os.path.join(self.home, "evidence.json")
        record = {one: None for one in dogfood_operator.EVIDENCE_MEMBERS}
        record.update({"resolved": False, "intake_receipt": False,
                       "unresolved": ["the runtime was never proved absent"]})
        with mock.patch.object(dogfood_operator, "read_grants",
                               return_value=self.grants()), \
                mock.patch.object(dogfood_operator, "compose",
                                  return_value=record):
            status = dogfood_operator.main(
                ["--grants", "g.json", "--evidence", place],
                capabilities=lambda _given: {})

        self.assertEqual(status, 1)
        with open(place, "rb") as reading:
            self.assertFalse(json.loads(reading.read())["resolved"])

    def test_a_post_start_fault_still_leaves_durable_unresolved_evidence(self):
        """Approver ruling item 8, at the boundary that actually writes.

        An implementation defect is not an attempt outcome, so the fault
        propagates -- but a container that started and an attempt that is now
        unresolved is exactly the case an operator needs the file for. The
        record rides out on the exception, because it is local to the arc and
        a launcher catching the fault has no other way to reach it.
        """
        place = os.path.join(self.home, "evidence.json")
        record = {one: None for one in dogfood_operator.EVIDENCE_MEMBERS}
        record.update({"resolved": False, "intake_receipt": False,
                       "runtime_id": "runtime-1", "attempt_id": "attempt-1",
                       "unresolved": ["the attempt ended on an unexpected "
                                      "KeyError"]})
        broken = KeyError("a defect in this module")
        broken.dogfood_evidence = record

        with mock.patch.object(dogfood_operator, "read_grants",
                               return_value=self.grants()), \
                mock.patch.object(dogfood_operator, "compose",
                                  side_effect=broken):
            with self.assertRaises(KeyError):
                dogfood_operator.main(
                    ["--grants", "g.json", "--evidence", place],
                    capabilities=lambda _given: {})

        with open(place, "rb") as reading:
            written = json.loads(reading.read())
        self.assertFalse(written["resolved"])
        self.assertEqual(written["runtime_id"], "runtime-1",
                         "the record must name the runtime that is still out "
                         "there")

    def test_a_fault_carrying_no_record_propagates_without_a_file(self):
        """A fault BEFORE the arc composed one has nothing to write, and
        inventing an empty record would be reporting an attempt that never
        started."""
        place = os.path.join(self.home, "evidence.json")
        with mock.patch.object(dogfood_operator, "read_grants",
                               return_value=self.grants()), \
                mock.patch.object(dogfood_operator, "compose",
                                  side_effect=RuntimeError("before the arc")):
            with self.assertRaises(RuntimeError):
                dogfood_operator.main(
                    ["--grants", "g.json", "--evidence", place],
                    capabilities=lambda _given: {})

        self.assertFalse(os.path.exists(place))

    def test_the_command_writes_the_record_of_a_resolved_attempt_and_exits_0(
            self):
        place = os.path.join(self.home, "evidence.json")
        record = {one: None for one in dogfood_operator.EVIDENCE_MEMBERS}
        record.update({"resolved": True, "intake_receipt": True,
                       "unresolved": [], "attempt_id": "attempt-1"})
        with mock.patch.object(dogfood_operator, "read_grants",
                               return_value=self.grants()), \
                mock.patch.object(dogfood_operator, "compose",
                                  return_value=record):
            status = dogfood_operator.main(
                ["--grants", "g.json", "--evidence", place],
                capabilities=lambda _given: {})

        self.assertEqual(status, 0)
        with open(place, "rb") as reading:
            self.assertEqual(json.loads(reading.read())["attempt_id"],
                             "attempt-1")


class TheSourceIsStagedBoundedAndOnce(OperatorCase):

    def test_the_exact_subset_lands_under_the_fixed_name(self):
        staged = stage_source(self.source, self.inputs)
        place = os.path.join(self.inputs, dogfood_operator.SOURCE_TARGET)
        self.assertTrue(os.path.isfile(os.path.join(place, "harness.py")))
        self.assertTrue(os.path.isfile(os.path.join(place, "nested",
                                                    "preflight.py")))
        self.assertEqual(staged["entry_count"], 2)
        self.assertIn("tree_digest", staged)

    def test_the_manifest_describes_what_was_copied(self):
        """Answered by the manager's own copier rather than measured again:
        two parties measuring one delivery is how they come to disagree."""
        staged = stage_source(self.source, self.inputs)
        self.assertEqual(sorted(one["path"] for one in staged["entries"]),
                         ["harness.py", os.path.join("nested",
                                                     "preflight.py")])

    def test_a_link_in_the_source_is_refused(self):
        """The bound is the manager's no-follow rule, reached through this
        path rather than restated by it."""
        os.symlink("/etc", os.path.join(self.source, "elsewhere"))
        with self.assertRaises(ContractRefusal):
            stage_source(self.source, self.inputs)

    def test_a_source_past_the_entry_ceiling_is_refused(self):
        with self.assertRaises(ContractRefusal):
            stage_source(self.source, self.inputs, max_entries=1)

    def test_a_source_past_the_byte_ceiling_is_refused(self):
        with self.assertRaises(ContractRefusal):
            stage_source(self.source, self.inputs, max_bytes=4)

    def test_staging_twice_into_one_input_root_is_refused(self):
        """An attempt stages its source once. A second staging would replace
        a delivery the manager has already measured."""
        stage_source(self.source, self.inputs)
        with self.assertRaises(OperatorRefusal) as caught:
            stage_source(self.source, self.inputs)
        self.assertIn("already exists", str(caught.exception))


class TheFrozenTaskIsReadOnTheWayIn(OperatorCase):
    """Read here as well as inside the container, so an operator learns about
    a malformed task before a container starts rather than from a failed
    attempt's evidence."""

    def refuses(self, document, expected):
        with self.assertRaises(OperatorRefusal) as caught:
            frozen_task(self.task(document))
        self.assertIn(expected, str(caught.exception))

    def test_the_operators_own_document_is_answered_whole(self):
        self.assertEqual(frozen_task(self.task()), TASK)

    def test_an_absent_task_is_refused(self):
        with self.assertRaises(OperatorRefusal) as caught:
            frozen_task(os.path.join(self.home, "no-such-task.json"))
        self.assertIn("no readable frozen task", str(caught.exception))

    def test_a_task_from_another_generation_is_refused(self):
        self.refuses(dict(TASK, schema="baton.dogfood-task/2"),
                     "this deployment stages")

    def test_an_extra_member_is_refused(self):
        self.refuses(dict(TASK, alias="a second identity"), "unexpected alias")

    def test_a_missing_member_is_refused(self):
        self.refuses({one: TASK[one] for one in TASK if one != "verification"},
                     "missing verification")

    def test_a_task_that_selects_another_source_root_is_refused(self):
        """The staged name is a constant of this deployment, exactly as it is
        a constant of the adapter that reads it."""
        self.refuses(dict(TASK, source_root="../elsewhere"),
                     "stages exactly")

    def test_every_task_member_is_held_before_the_container_starts(self):
        for member, value in (("task_id", 7), ("instructions", []),
                              ("instructions", ""),
                              ("verification", "python3 harness.py"),
                              ("verification", [])):
            with self.subTest(member=member, value=value):
                with self.assertRaises(OperatorRefusal):
                    frozen_task(self.task(dict(TASK, **{member: value})))

    def test_the_document_is_not_json_is_refused(self):
        place = os.path.join(self.home, "task.json")
        self.write(place, "not a document")
        with self.assertRaises(OperatorRefusal):
            frozen_task(place)


class TheProtocolDocumentsAreComposedHere(OperatorCase):
    """`compose_input_root` takes both as operands, so the party that knows
    what this delivery IS authors them."""

    def given(self, staged):
        return input_manifest(
            work_ref=WORK_REF, staged=staged, created_at=NOW,
            manifest_id="input-w39358",
            assignment_contract="v12-assignment-1", human_contract=HUMAN,
            record_binding=BINDING, role_instructions_digest=ROLE,
            runtime_profile_digest=PROFILE, toolchain_digest=TOOLCHAIN,
            worker_image_digest=IMAGE, policies=POLICIES)

    def composed(self):
        staged = stage_source(self.source, self.inputs)
        given = self.given(staged)
        assignment = assignment_manifest(
            given=given, work_ref=WORK_REF, participant="baton.claude",
            generation=1, attempt_id="attempt-1", offer_id="offer-1",
            claim_receipt_digest="sha256:" + "d" * 64, claim_event_seq=44,
            created_at=NOW, activated_at=NOW,
            assignment_contract="v12-assignment-1",
            manifest_id="assignment-w39358")
        return given, assignment

    def test_the_input_manifest_seals_its_own_digest(self):
        given, _assignment = self.composed()
        held = dict(given)
        held.pop("manifest_digest")
        self.assertEqual(given["manifest_digest"], digest(held))

    def test_the_sources_entry_carries_the_copiers_own_manifest(self):
        """Not a second measurement. A deployment that measured the tree twice
        would be two parties disagreeing about one delivery."""
        staged = stage_source(self.source, self.inputs)
        given = self.given(staged)
        self.assertEqual(given["sources"][0]["content_manifest"], staged)
        self.assertEqual(given["sources"][0]["name"],
                         dogfood_operator.SOURCE_TARGET)

    def test_manifest_paths_are_relative_to_the_two_fixed_roots(self):
        """A source destination is below `/input` and an output path is below
        `/output`; neither spelling carries the retired `workspace/` prefix."""
        given, _assignment = self.composed()
        for role, actual, expected in (
                ("input", given["sources"][0]["destination"], "source"),
                ("output", given["outputs"][0]["path"], "proposal")):
            with self.subTest(role=role):
                self.assertEqual(actual, expected)

    def test_exactly_one_output_is_declared(self):
        """The parent finding's own ruling: the proposal is one directory
        tree, because a second top-level result document would be unmeasured
        auxiliary material."""
        given, _assignment = self.composed()
        self.assertEqual([one["name"] for one in given["outputs"]],
                         ["proposal"])
        self.assertEqual(given["outputs"][0]["type"], "directory-result")
        self.assertEqual(given["outputs"][0]["constraints"]["link_policy"],
                         "forbid")

    def test_the_task_does_not_travel_in_the_protocol_document(self):
        """The schema's ruling, not a preference. A first cut added `task_id`
        and the manager's own composer refused the document; the task is a
        WORKLOAD convention and travels in `/input/task.json`."""
        given, _assignment = self.composed()
        self.assertNotIn("task_id", given)
        self.assertNotIn(TASK["instructions"], json.dumps(given))

    def test_an_incomplete_policy_set_is_refused_before_the_manager_sees_it(
            self):
        """The frozen schema requires all seven, so an operator learns about a
        missing one here rather than from a refused root with the source
        already staged."""
        staged = stage_source(self.source, self.inputs)
        with self.assertRaises(OperatorRefusal) as caught:
            input_manifest(
                work_ref=WORK_REF, staged=staged, created_at=NOW,
                manifest_id="input-w39358",
                assignment_contract="v12-assignment-1", human_contract=HUMAN,
                record_binding=BINDING, role_instructions_digest=ROLE,
                runtime_profile_digest=PROFILE, toolchain_digest=TOOLCHAIN,
                worker_image_digest=IMAGE,
                policies={one: POLICIES[one]
                          for one in list(POLICIES)[:-1]})
        self.assertIn("missing retention_policy_digest", str(caught.exception))

    def test_a_policy_value_that_is_not_a_digest_is_refused_here(self):
        staged = stage_source(self.source, self.inputs)
        malformed = dict(POLICIES, policy_digest="not-a-digest")
        with self.assertRaises(OperatorRefusal):
            input_manifest(
                work_ref=WORK_REF, staged=staged, created_at=NOW,
                manifest_id="input-w39358",
                assignment_contract="v12-assignment-1",
                human_contract=HUMAN, record_binding=BINDING,
                role_instructions_digest=ROLE,
                runtime_profile_digest=PROFILE, toolchain_digest=TOOLCHAIN,
                worker_image_digest=IMAGE, policies=malformed)

    def test_the_assignment_binds_the_input_manifest_it_was_minted_against(
            self):
        given, assignment = self.composed()
        self.assertEqual(assignment["input_manifest_digest"],
                         given["manifest_digest"])
        self.assertEqual(assignment["policy_digest"], given["policy_digest"])
        self.assertEqual(assignment["runtime_profile_digest"],
                         given["runtime_profile_digest"])

    def test_the_assignment_seals_its_own_digest(self):
        _given, assignment = self.composed()
        held = dict(assignment)
        held.pop("manifest_digest")
        self.assertEqual(assignment["manifest_digest"], digest(held))

    def test_the_two_documents_compose_a_real_input_root(self):
        """THE ONE THAT MATTERS: the manager's own composer accepts them.

        A pair of documents this module shaped to look right proves nothing;
        `compose_input_root` is the boundary a real delivery crosses, and it
        holds both against the contract before writing either.
        """
        from baton_v12.worker_manager.workspaces import compose_input_root

        given, assignment = self.composed()
        compose_input_root(self.inputs, given, assignment,
                           assignment=dict(assignment["assignment_ref"]),
                           runtime_attempt_id="attempt-1")
        for name in ("input.json", "assignment.json"):
            self.assertTrue(os.path.isfile(os.path.join(self.inputs, name)),
                            name)
        # AND THE STAGED SOURCE SURVIVED THE COMPOSITION, which is the half a
        # document check cannot establish: the operator stages before the
        # manager composes, so a composer that cleared the root would have
        # taken the delivery with it.
        self.assertTrue(os.path.isfile(os.path.join(
            self.inputs, dogfood_operator.SOURCE_TARGET, "harness.py")))


if __name__ == "__main__":
    unittest.main()


class ThePreflightRunsBeforeAnythingIsStaged(OperatorCase):
    """W39358 review 2026-08-30T05:53:19Z [P1].

    The first round put the policy check inside `input_manifest`, which takes
    the already-produced staged manifest -- so the record claimed a refusal
    happened "while nothing has been staged" and the code could not deliver
    it. `preflight` is that refusal, and these cases hold it where the claim
    is: before `stage_source` writes anything.
    """

    def granted(self, **overrides):
        given = {"task": TASK, "policies": POLICIES,
                 "worker_image_digest": IMAGE, "toolchain_digest": TOOLCHAIN,
                 "runtime_profile_digest": PROFILE,
                 "role_instructions_digest": ROLE, "record_binding": BINDING,
                 "network": "baton-dogfood",
                 "review_route": "rview",
                 "retention_disposition": "retain",
                 "human_contract": dict(HUMAN)}
        given.update(overrides)
        return given

    def refuses(self, expected, **overrides):
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.preflight(**self.granted(**overrides))
        self.assertIn(expected, str(caught.exception))
        # AND NOTHING WAS STAGED, which is the whole point of the ordering.
        self.assertFalse(os.path.exists(
            os.path.join(self.inputs, dogfood_operator.SOURCE_TARGET)))

    def test_a_complete_set_of_grants_passes(self):
        self.assertTrue(dogfood_operator.preflight(**self.granted()))

    def test_a_review_route_that_was_not_named_is_refused(self):
        """Approver ruling M44657 makes the pass part of the arc, so WHERE the
        Work goes next is a grant like any other -- and an operator who did
        not say gets a refusal rather than this module's guess."""
        for wrong in (None, "", "   ", 7, [], {}):
            with self.subTest(route=wrong):
                self.refuses("review route", review_route=wrong)

    def test_a_policy_value_that_is_not_a_digest_is_refused(self):
        """The other half of the finding: the first cut validated the seven
        KEY names, so `policy_digest="not-a-digest"` was accepted here and
        left for the manager to refuse after the delivery existed."""
        self.refuses("policy_digest is not a sha256 digest",
                     policies=dict(POLICIES, policy_digest="not-a-digest"))

    def test_an_incomplete_policy_set_is_refused(self):
        self.refuses("missing retention_policy_digest",
                     policies={one: POLICIES[one]
                               for one in list(POLICIES)[:-1]})

    def test_every_other_digest_operand_is_held_too(self):
        for name in ("worker_image_digest", "toolchain_digest",
                     "runtime_profile_digest", "role_instructions_digest"):
            with self.subTest(operand=name):
                self.refuses(f"{name} is not a sha256 digest",
                             **{name: "latest"})

    def test_a_mutable_image_tag_is_not_a_digest(self):
        """There is no mutable image tag anywhere in this module, and this is
        where an operator finds that out."""
        self.refuses("worker_image_digest is not a sha256 digest",
                     worker_image_digest="baton-dogfood:latest")

    def test_the_record_binding_is_exactly_its_four_members(self):
        self.refuses("the record binding is exactly",
                     record_binding={"root": "baton-repository"})

    def test_an_unnamed_network_is_a_grant_nobody_made(self):
        for wrong in ("", None, 5):
            with self.subTest(network=wrong):
                self.refuses("engine network name", network=wrong)

    def test_a_task_from_another_generation_is_refused_here_too(self):
        self.refuses("this deployment stages",
                     task=dict(TASK, schema="baton.dogfood-task/2"))

    def test_a_held_task_cannot_be_mutated_between_its_two_reads(self):
        """`frozen_task` answers an ordinary writable dict. Preflight must
        re-hold every member before that dict is copied into `/input`, rather
        than checking only the schema and trusting the earlier read."""
        for member, value in (("task_id", 7), ("instructions", ""),
                              ("verification", []),
                              ("source_root", "../elsewhere")):
            with self.subTest(member=member):
                self.refuses("frozen task", task=dict(
                    TASK, **{member: value}))

    def test_record_binding_values_are_held_before_staging(self):
        """Four right key names are not a binding: both digests and both
        locators reach the frozen manifest schema after staging otherwise."""
        for member, value in (("finding_digest", "latest"),
                              ("plan_digest", "sha256:no"),
                              ("root", ""), ("path", "/absolute")):
            with self.subTest(member=member):
                self.refuses("record binding", record_binding=dict(
                    BINDING, **{member: value}))

    def test_record_binding_locators_use_the_frozen_manifest_grammar(self):
        """A looser handwritten locator check only moves part of the frozen
        manifest refusal before staging.  Both the opaque root and relative
        path must hold the schema's length and character rules here too."""
        for member, value in (("root", "has space"),
                              ("root", "r" * 161),
                              ("path", "."),
                              ("path", "record\\binding"),
                              ("path", "record\0binding"),
                              ("path", "r" * 513)):
            with self.subTest(member=member, value=repr(value)):
                self.refuses("record binding", record_binding=dict(
                    BINDING, **{member: value}))

    def test_the_network_is_held_to_the_engine_grammar_before_staging(self):
        """Merely non-empty defers this refusal to `run_vector`, after the
        source and task already exist in the attempt input root."""
        for network in ("--network=host", "../bridge", "two words"):
            with self.subTest(network=network):
                self.refuses("engine network name", network=network)

    def test_a_non_document_policy_set_is_a_typed_preflight_refusal(self):
        """A public boundary reports a composition fault; it does not leak a
        `TypeError` while trying to iterate a value it never held."""
        for policies in (None, [], "policy_digest"):
            with self.subTest(policies=policies):
                self.refuses("policy identities", policies=policies)

    def test_one_refusal_reports_the_whole_preflight(self):
        """Named faults are collected rather than raised one at a time, so an
        operator fixes a launch once instead of discovering its grants in the
        order this module happens to check them."""
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.preflight(**self.granted(
                network="", worker_image_digest="latest",
                record_binding={}))
        message = str(caught.exception)
        for expected in ("worker_image_digest is not a sha256 digest",
                         "the record binding is exactly",
                         "engine network name"):
            self.assertIn(expected, message)


class TheStatedCeilingsAreACeiling(OperatorCase):
    """W39358 review 2026-08-30T05:53:19Z [P1]: the exported helper forwarded
    caller-selected bounds unchanged, so a caller could widen the bound this
    module states -- which makes a stated bound a suggestion."""

    def test_a_caller_may_narrow_its_own_delivery(self):
        staged = stage_source(self.source, self.inputs, max_entries=2,
                              max_bytes=1024)
        self.assertEqual(staged["entry_count"], 2)

    def test_a_caller_may_not_widen_the_operators_ceiling(self):
        for name, value in (
                ("max_entries", dogfood_operator.MAX_SOURCE_ENTRIES + 1),
                ("max_bytes", dogfood_operator.MAX_SOURCE_BYTES + 1)):
            with self.subTest(operand=name):
                with self.assertRaises(OperatorRefusal) as caught:
                    stage_source(self.source, self.inputs, **{name: value})
                self.assertIn("may not widen it", str(caught.exception))

    def test_a_narrower_ceiling_is_a_positive_whole_number(self):
        """Bool, zero and text currently reach comparisons or the copier as
        accidental Python coercions rather than as this operator's bound."""
        for name, value in (("max_entries", True), ("max_entries", 0),
                            ("max_bytes", False), ("max_bytes", "1024")):
            with self.subTest(operand=name, value=value):
                with self.assertRaises(OperatorRefusal):
                    stage_source(self.source, self.inputs, **{name: value})


class TheOperatorAndTheWorkerAgreeOnTheTasksCONSTANTS(unittest.TestCase):
    """WHAT MOST OF THIS COMPARES IS CONSTANTS, and the name says so.

    THE LESSON THAT SURVIVED, and it is the useful one: equal regex TEXT did
    not prove equal PREDICATES. This class once carried a claim that the two
    ends held "one whole contract" while comparing only the member tuple, the
    schema, the source name and the pattern text — and the predicates differed,
    because `claude_agent._task` matched `str(document["task_id"])` while this
    operator required exact text. That gap became W44424.

    **Superseded (W44424, closed satisfying):** the asymmetry itself. The
    receiver holds the identity as text before matching now, so both ends
    refuse a numeric identity and the case below asks the receiver's actual
    predicate rather than its pattern — the constants comparison it used to do
    being the very confusion that found the defect.

    The reason the constants matter at all: the operator's read exists to move
    a refusal earlier, so a copy that drifted from the worker's would move it
    back to the failed provider attempt it was meant to avoid.
    """

    def worker(self):
        import importlib.util
        place = (pathlib_worker() / "claude_agent.py")
        spec = importlib.util.spec_from_file_location("claude_agent", place)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_the_program_execd_is_the_image_s_own_entrypoint(self):
        """The seam the image documents, not the module underneath it.

        DEFECT this closed: the operator named `baton_worker.py`, which runs
        the worker with `agent=None` and falls back to the M2 FIXTURE agent.
        A supervised pilot would have reported a stub's output as the worker's
        work -- and against this image it does not even get that far, because
        W39770 removed `scripted_agent.py` from it.

        Asked of the RECIPE rather than restated here: an ENTRYPOINT and an
        `exec`ed program that drifted apart would be two workers.
        """
        recipe = (pathlib_worker() / "Dockerfile.claude").read_text()
        entry = [one for one in recipe.splitlines()
                 if one.startswith("ENTRYPOINT")]
        self.assertEqual(len(entry), 1, recipe)
        self.assertIn(dogfood_operator.WORKER_PROGRAM[-1], entry[0],
                      "the transport execs a program the image's own "
                      "entrypoint does not name")
        self.assertNotIn("baton_worker.py",
                         dogfood_operator.WORKER_PROGRAM[-1])

    def test_the_closed_member_set_is_one_set(self):
        self.assertEqual(sorted(dogfood_operator._TASK_MEMBERS),
                         sorted(self.worker().TASK_MEMBERS))

    def test_the_schema_is_one_schema(self):
        self.assertEqual(dogfood_operator._TASK_SCHEMA,
                         self.worker().TASK_SCHEMA)

    def test_the_staged_source_name_is_one_name(self):
        """The operator stages it and the adapter reads it by equality; two
        spellings would be a delivery nobody receives."""
        self.assertEqual(dogfood_operator.SOURCE_TARGET,
                         self.worker().SOURCE_ROOT)

    def test_the_task_identity_pattern_text_is_one_pattern(self):
        """The PATTERN, which is not the same claim as the predicate — see
        the case below."""
        self.assertEqual(dogfood_operator._TASK_ID.pattern,
                         self.worker()._TASK_ID.pattern)

    def test_both_ends_refuse_a_numeric_task_id(self):
        """SUPERSEDED AND INVERTED, and it is worth saying why twice over.

        Until W44424 this asserted an ASYMMETRY: the receiver coerced with
        `str()` before matching, so a JSON number was a usable identity to it
        and not to this operator. W44424 closed that — `claude_agent._task`
        requires exact `str` before applying the pattern — so the property
        this case asserted no longer exists.

        AND ITS OLD FORM WAS THE SAME MISTAKE IT WAS ABOUT. It proved "the
        receiver takes it" by applying the receiver's REGEX to `str(7)`
        itself, which is a constants comparison standing in for a predicate —
        exactly the confusion that discovered W44424. Review
        2026-08-30T06:20:54Z [P2] caught it repeating in the case written to
        record it.

        So it asks the receiver's ACTUAL predicate now, through `_task`, over
        a document on disk — the way the receiver is really reached.
        """
        import shutil
        import tempfile

        numeric = dict(TASK, task_id=7)
        with self.assertRaises(OperatorRefusal):
            dogfood_operator.held_task(numeric)

        worker = self.worker()
        home = tempfile.mkdtemp(prefix="v12-w39358-receiver-")
        self.addCleanup(shutil.rmtree, home, True)
        place = os.path.join(home, worker.TASK_DOCUMENT)
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(numeric, handle)
        # THE RECEIVER REFUSES IT TOO. Asked of `_task`, not of the pattern:
        # the pattern is a constant and the refusal is a predicate, and this
        # case exists because those were once confused.
        with self.assertRaises(worker.TaskRefusal):
            worker._task(place)


def pathlib_worker():
    import pathlib
    return pathlib.Path(__file__).resolve().parents[3] / "worker"


class TheTaskIsHeldEverywhereItIsBelieved(OperatorCase):
    """W39358 review 2026-08-30T06:05:02Z [P1]: checking the schema a second
    time is not the same hold. `held_task` is one pure function applied at the
    first read, at the preflight and immediately before the copy."""

    def granted(self, task):
        return {"task": task, "policies": POLICIES,
                "worker_image_digest": IMAGE, "toolchain_digest": TOOLCHAIN,
                "runtime_profile_digest": PROFILE,
                "role_instructions_digest": ROLE, "record_binding": BINDING,
                "network": "baton-dogfood",
                "review_route": "rview",
                "retention_disposition": "retain",
                "human_contract": dict(HUMAN)}

    def test_a_task_changed_after_its_first_read_does_not_pass_preflight(self):
        for member, value in (("task_id", "../elsewhere"),
                              ("instructions", ""),
                              ("verification", []),
                              ("source_root", "somewhere-else")):
            with self.subTest(member=member):
                held = frozen_task(self.task())
                held[member] = value
                with self.assertRaises(OperatorRefusal):
                    dogfood_operator.preflight(**self.granted(held))

    def test_a_task_changed_after_preflight_is_not_the_task_copied(self):
        """The third application, immediately before the write, is what makes
        the interval between the second and the copy uninteresting."""
        held = frozen_task(self.task())
        dogfood_operator.preflight(**self.granted(held))
        held["verification"] = []
        with self.assertRaises(OperatorRefusal):
            dogfood_operator._copied_task(held, self.inputs)
        self.assertFalse(os.path.exists(os.path.join(self.inputs,
                                                     "task.json")))

    def test_one_function_answers_at_all_three_places(self):
        """A second spelling of the hold is a second chance to disagree."""
        for place in (dogfood_operator.frozen_task,
                      dogfood_operator.preflight,
                      dogfood_operator._copied_task):
            with self.subTest(place=place.__name__):
                self.assertIn("held_task", place.__code__.co_names)


class TheIdentityHoldIsAppliedTwice(OperatorCase):
    """`preflight` is where an operator learns before anything is staged; the
    composer applies the same hold again, which is the second party proving it
    rather than assuming the first did."""

    def test_the_composer_refuses_the_same_malformed_identities(self):
        staged = stage_source(self.source, self.inputs)
        with self.assertRaises(OperatorRefusal) as caught:
            input_manifest(
                work_ref=WORK_REF, staged=staged, created_at=NOW,
                manifest_id="input-w39358",
                assignment_contract="v12-assignment-1", human_contract=HUMAN,
                record_binding=dict(BINDING, path="/absolute/record"),
                role_instructions_digest=ROLE, runtime_profile_digest=PROFILE,
                toolchain_digest=TOOLCHAIN, worker_image_digest=IMAGE,
                policies=POLICIES)
        # THE FROZEN CONTRACT'S OWN NAME FOR THE RULE. Review
        # 2026-08-30T06:13:35Z [P1]: this asserted my handwritten
        # "repository-relative" prose, and the approximation behind it is
        # superseded by `validate_fragment(..., "relativePath")` -- the
        # definition's own owner. This case is mine and changed with the rule
        # it was asserting.
        self.assertIn("relativePath", str(caught.exception))

    def test_a_malformed_policy_container_refuses_at_the_composer_too(self):
        staged = stage_source(self.source, self.inputs)
        with self.assertRaises(OperatorRefusal):
            input_manifest(
                work_ref=WORK_REF, staged=staged, created_at=NOW,
                manifest_id="input-w39358",
                assignment_contract="v12-assignment-1", human_contract=HUMAN,
                record_binding=BINDING, role_instructions_digest=ROLE,
                runtime_profile_digest=PROFILE, toolchain_digest=TOOLCHAIN,
                worker_image_digest=IMAGE, policies=None)


class TheLocatorGrammarHasONEOwner(OperatorCase):
    """W39358 review 2026-08-30T06:13:35Z [P1]. A second approximation
    maintained in this tool is a second grammar with nothing comparing the
    two — the same rule the engine network operand is already under."""

    def test_the_frozen_definitions_are_what_refuses(self):
        """Asserted through the module rather than restated: a case that
        listed the rules itself would be a THIRD copy."""
        from baton_v12.contracts import validate_fragment

        for definition, value in (("opaqueId", "has space"),
                                  ("relativePath", "/absolute")):
            with self.subTest(definition=definition):
                with self.assertRaises(ContractRefusal):
                    validate_fragment(value, definition, what="probe")

    def test_a_root_the_frozen_grammar_refuses_never_reaches_staging(self):
        for wrong in ("has space", "r" * 161, ""):
            with self.subTest(root=wrong):
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.preflight(
                        task=TASK, policies=POLICIES,
                        worker_image_digest=IMAGE,
                        toolchain_digest=TOOLCHAIN,
                        runtime_profile_digest=PROFILE,
                        role_instructions_digest=ROLE,
                        record_binding=dict(BINDING, root=wrong),
                        network="baton-dogfood",
                        review_route="rview",
                retention_disposition="retain",
                human_contract=dict(HUMAN))
                self.assertIn("opaqueId", str(caught.exception))
                self.assertFalse(os.path.exists(os.path.join(
                    self.inputs, dogfood_operator.SOURCE_TARGET)))

    def test_a_path_the_frozen_grammar_refuses_never_reaches_staging(self):
        for wrong in (".", "work\\records", "work/../escape", "p" * 513,
                      "work//records"):
            with self.subTest(path=wrong):
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.preflight(
                        task=TASK, policies=POLICIES,
                        worker_image_digest=IMAGE,
                        toolchain_digest=TOOLCHAIN,
                        runtime_profile_digest=PROFILE,
                        role_instructions_digest=ROLE,
                        record_binding=dict(BINDING, path=wrong),
                        network="baton-dogfood",
                        review_route="rview",
                retention_disposition="retain",
                human_contract=dict(HUMAN))
                self.assertIn("relativePath", str(caught.exception))

    def test_the_refusal_carries_the_contracts_own_sentence(self):
        """A class name would send an operator reading the operator's source
        instead of their own document."""
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.preflight(
                task=TASK, policies=POLICIES, worker_image_digest=IMAGE,
                toolchain_digest=TOOLCHAIN, runtime_profile_digest=PROFILE,
                role_instructions_digest=ROLE,
                record_binding=dict(BINDING, path="/absolute/record"),
                network="baton-dogfood", review_route="rview",
                retention_disposition="retain", human_contract=dict(HUMAN))
        self.assertNotIn("ContractRefusal", str(caught.exception))
        self.assertIn("the record binding's path", str(caught.exception))

    def test_an_owner_defect_is_not_relabelled_as_bad_operator_input(self):
        """Only an owner's typed contract judgement says the supplied grant
        is wrong.  An unexpected failure is a defect at that owner and must
        not become an `OperatorRefusal` telling the human to edit its input."""
        for owner in ("_validate_fragment", "_engine_network"):
            with self.subTest(owner=owner):
                original = getattr(dogfood_operator, owner)

                def broken(*_arguments, **_keywords):
                    raise RuntimeError("the grammar owner failed")

                setattr(dogfood_operator, owner, broken)
                try:
                    with self.assertRaises(RuntimeError):
                        dogfood_operator.preflight(
                            task=TASK, policies=POLICIES,
                            worker_image_digest=IMAGE,
                            toolchain_digest=TOOLCHAIN,
                            runtime_profile_digest=PROFILE,
                            role_instructions_digest=ROLE,
                            record_binding=BINDING,
                            network="baton-dogfood",
                        review_route="rview",
                retention_disposition="retain",
                human_contract=dict(HUMAN))
                finally:
                    setattr(dogfood_operator, owner, original)

    def test_this_tool_keeps_no_second_locator_grammar(self):
        """`posixpath` was imported only to hand-roll the path rule, so the
        module no longer importing it is what makes the deletion deliberate
        rather than drift.

        ASKED OF THE MODULE, not of its text. The superseded rule is described
        in a comment on purpose — this record keeps the history of what was
        replaced — so a source-text search would find the word and report a
        grammar that is no longer there.
        """
        self.assertFalse(hasattr(dogfood_operator, "posixpath"))
        self.assertTrue(hasattr(dogfood_operator, "_validate_fragment"))


class AnOwnerDefectIsNotABadGrant(OperatorCase):
    """W39358 review 2026-08-30T06:20:54Z [P2].

    `OperatorRefusal` says a deployment was asked for something it does not
    do. An implementation defect inside a grammar owner is not that, and
    reporting it as one tells a human to edit a grant that is fine while
    hiding the boundary that actually failed.
    """

    def granted(self, **overrides):
        given = {"task": TASK, "policies": POLICIES,
                 "worker_image_digest": IMAGE, "toolchain_digest": TOOLCHAIN,
                 "runtime_profile_digest": PROFILE,
                 "role_instructions_digest": ROLE, "record_binding": BINDING,
                 "network": "baton-dogfood",
                 "review_route": "rview",
                 "retention_disposition": "retain",
                 "human_contract": dict(HUMAN)}
        given.update(overrides)
        return given

    def broken(self, name):
        """Replace one grammar owner with a defect, for one case."""
        def raising(*arguments, **operands):
            raise RuntimeError("the owner is broken")

        held = getattr(dogfood_operator, name)
        setattr(dogfood_operator, name, raising)
        self.addCleanup(setattr, dogfood_operator, name, held)

    def test_a_network_owner_defect_propagates(self):
        self.broken("_engine_network")
        with self.assertRaises(RuntimeError):
            dogfood_operator.preflight(**self.granted())

    def test_a_locator_owner_defect_propagates(self):
        self.broken("_validate_fragment")
        with self.assertRaises(RuntimeError):
            dogfood_operator.preflight(**self.granted())

    def test_the_typed_outcome_is_still_a_collected_fault(self):
        """The other half: an invalid VALUE is still the operator's to fix."""
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.preflight(**self.granted(network="two words"))
        self.assertIn("engine network name", str(caught.exception))


class EveryPostStartBranchEntersTheEnding(OperatorCase):
    """W39358 review 2026-08-30T06:35:56Z [P0].

    A returned unresolved document is not an ending. Once the manager has
    started a named runtime, transport loss and a worker answer without a
    disposition must enter the same quiescence/cleanup owner as the ordinary
    result rather than return around it.
    """

    class Adapter:

        def __init__(self):
            self.stops = []

        def stop(self, request):
            self.stops.append(dict(request))
            return {"runtime_id": request["runtime_id"], "ordered": True,
                    "state": "quiescent", "why": "stopped for the ending"}

        def observe(self, runtime_id):
            return {"runtime_id": runtime_id, "state": "quiescent",
                    "why": "the ending observed it"}

    def run_until_conversation(self, spoken):
        import baton_v12.worker_manager as manager
        from baton_v12.worker_manager import launch, worker_entry, workspaces

        adapter = self.Adapter()
        roots = {"inputs": self.inputs,
                 "workspace": os.path.join(self.home, "workspace"),
                 "outputs": os.path.join(self.home, "outputs")}
        given = {"manifest_digest": "sha256:" + "a" * 64,
                 "policy_digest": POLICIES["policy_digest"],
                 "outputs": [{"name": "proposal"}]}
        assignment = {"manifest_digest": "sha256:" + "b" * 64,
                      "assignment_ref": {"work_ref": dict(WORK_REF),
                                         "participant": "baton.claude",
                                         "generation": 1}}
        claimed = {"assignment": dict(assignment["assignment_ref"]),
                   "claim_event": 44, "decision": {"grant": "direct"}}
        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                dogfood_operator, "frozen_task", return_value=dict(TASK)))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "preflight", return_value=True))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "_configured_group", return_value=object()))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "stage_source",
                return_value={"tree_digest": "sha256:" + "c" * 64}))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "input_manifest", return_value=given))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "assignment_manifest",
                return_value=assignment))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "_copied_task", return_value="task.json"))
            patches.enter_context(mock.patch.object(
                workspaces, "assignment_workspace",
                return_value=roots))
            patches.enter_context(mock.patch.object(
                workspaces, "compose_input_root", return_value=None))
            patches.enter_context(mock.patch.object(
                launch, "materialize", return_value=object()))
            for name, answer in (
                    ("issue_offer", {}), ("accept_offer", {}),
                    ("record_attempt", {}), ("submit_claim", claimed),
                    ("activate_assignment", {}), ("retain_manifest", {}),
                    ("request_runtime_start", {"runtime_id": "runtime-1"})):
                patches.enter_context(mock.patch.object(
                    manager, name, return_value=answer))
            patches.enter_context(mock.patch.object(
                worker_entry, "converse", return_value=spoken))
            evidence = dogfood_operator.run_dogfood_task(
                engine="docker", run=lambda _argv: None,
                open_channel=lambda _argv: None, store=object(), port=object(),
                session=PassingSession(), review_route="rview",
                adapter_of=lambda **_operands: adapter,
                attempt_id="attempt-1", offer_id="offer-1",
                source=self.source, task_path=self.task(), storage=self.home,
                launch_home=self.home, credential_delivery=object(),
                image_digest=IMAGE, network="baton-dogfood",
                work_ref=WORK_REF, participant="baton.claude", generation=1,
                now=NOW, policies=POLICIES, record_binding=BINDING,
                assignment_contract="v12-assignment-1", human_contract=HUMAN,
                role_instructions_digest=ROLE,
                runtime_profile_digest=PROFILE,
                toolchain_digest=TOOLCHAIN, adapter_digest=IMAGE,
                adapter_name="oci", labels={"attempt": "attempt-1"},
                retention_policy_digest=POLICIES["retention_policy_digest"],
                retention_disposition="discard-after-intake",
                bearer="one-use-bearer")
        return adapter, evidence

    def test_transport_and_disposition_failures_do_not_return_around_ending(
            self):
        """Both receiptless failures enter the ending and report its result.

        Superseded measure, 2026-08-30: this case originally required one
        direct `adapter.stop`. W44716's approved composite now requires the
        authority fence BEFORE runtime control, so a deployment-side stop on
        these receiptless paths would prove the opposite property. The final
        observation and the manager's typed refusal are the evidence that the
        path entered its ending when the narrow fixture lacks the new destroy
        capability.
        """
        # FIXTURE CORRECTED UNDER EXPLICIT AUTHORIZATION, review
        # 2026-08-30T12:27:41Z [P2]: `converse` cannot answer `answered` for a
        # requested describe/work sequence while returning only a `describe`
        # answer. The reachable shape is a complete `work` answer carrying a
        # disposition this deployment cannot use. Assertions unchanged.
        for spoken in (
                {"ending": "lost", "why": "EOF", "answers": []},
                {"ending": "answered", "why": "clean",
                 "answers": [{"operation": "describe", "answer": {}},
                             {"operation": "consider", "answer": {}},
                             {"operation": "work",
                              "answer": {"disposition": None, "outputs": [],
                                         "recap": ""}}]}):
            with self.subTest(ending=spoken["ending"]):
                adapter, evidence = self.run_until_conversation(spoken)
                self.assertFalse(evidence["resolved"])
                self.assertEqual(adapter.stops, [],
                                 "runtime control happened before the fence")
                self.assertIsNotNone(evidence["observed_after"])
                self.assertTrue(any(
                    "abandon" in one for one in evidence["unresolved"]),
                    "the receiptless path returned around abandonment")

    def test_conversation_failures_still_reach_the_abandonment_ending(self):
        """The older case's PROPERTY, under the measure W44716 left it.

        Review 2026-08-30T06:44:13Z [P0] proved a lost conversation returned
        around its ending, and measured the ending as one `adapter.stop`.
        Review 2026-08-30T11:44:55Z [P0] then ruled that this same receiptless
        path must reach `abandon_attempt` with NO prior runtime control, so
        the stop count is no longer the ending's signature -- entering the
        composite is. This case is additive: it holds the original property on
        both original subcases without restating the retired measure.
        """
        import baton_v12.worker_manager as manager

        # THE SECOND SHAPE IS ONE `converse` CAN ACTUALLY RETURN. Review
        # 2026-08-30T06:56:26Z [P2]: a `describe`-only answer set with
        # `ending="answered"` is not a document the real transport produces,
        # because `answered` means every requested operation answered. The
        # reachable defensive case is a `work` answer whose members are all
        # present -- the envelope is closed on NAMES and deliberately does not
        # type the VALUES -- carrying a disposition this deployment cannot use.
        for spoken in (
                {"ending": "lost", "why": "EOF", "answers": []},
                {"ending": "answered", "why": "clean",
                 "answers": [{"operation": "describe", "answer": {}},
                             {"operation": "consider", "answer": {}},
                             {"operation": "work",
                              "answer": {"disposition": None, "outputs": [],
                                         "recap": ""}}]}):
            with self.subTest(ending=spoken["ending"]):
                with mock.patch.object(
                        manager, "abandon_attempt",
                        return_value={
                            "intent": {}, "fenced": {"fenced": True},
                            "cleanup": {"cleanup": "retained",
                                        "state": "absent"}}) as abandon:
                    adapter, evidence = self.run_until_conversation(spoken)
                abandon.assert_called_once()
                self.assertEqual(
                    abandon.call_args.kwargs["attempt_id"], "attempt-1",
                    "the ending must name the attempt that started")
                self.assertEqual(adapter.stops, [],
                                 "no runtime control before the fence")
                self.assertTrue(evidence["abandoned"]["fenced"])
                self.assertIsNotNone(evidence["observed_after"],
                                     "an unsettled ending still reports what "
                                     "remains")

    def test_a_retry_refuses_when_the_launch_delivery_cannot_be_adopted(self):
        """W47225 [P0]: absence is ordinary for the component and
        contradictory here.

        The retained evidence says a runtime started, and a runtime only
        starts after `launch.materialize` completes. Ending with no delivery
        would report `not-delivered` for a root that was really made, which is
        the settlement the child Work exists to stop.
        """
        from baton_v12.worker_manager import launch

        with mock.patch.object(launch, "adopt", return_value=None):
            with self.assertRaises(OperatorRefusal) as caught:
                dogfood_operator._adopted_launch(
                    {"runtime_id": "runtime-1"},
                    {"attempt_id": "attempt-1",
                     "launch_home": self.home,
                     "task_path": self.task()})

        self.assertIn("no launch delivery to adopt", str(caught.exception))

    def test_a_session_that_cannot_pass_is_refused_before_anything_is_staged(
            self):
        """The capability is held with the other grants, not discovered late.

        M44657 makes the pass part of the arc, so a session that cannot
        perform it cannot perform the arc -- and finding that out after a
        container is running would be finding it out once durable state
        depends on it.
        """
        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                dogfood_operator, "frozen_task", return_value=dict(TASK)))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "preflight", return_value=True))
            staged = patches.enter_context(mock.patch.object(
                dogfood_operator, "stage_source"))
            with self.assertRaises(OperatorRefusal) as caught:
                dogfood_operator.run_dogfood_task(
                    engine="docker", run=lambda _argv: None,
                    open_channel=lambda _argv: None, store=object(),
                    port=object(), session=object(), review_route="rview",
                    adapter_of=lambda **_operands: self.Adapter(),
                    attempt_id="attempt-1", offer_id="offer-1",
                    source=self.source, task_path=self.task(),
                    storage=self.home, launch_home=self.home,
                    credential_delivery=object(), image_digest=IMAGE,
                    network="baton-dogfood", work_ref=WORK_REF,
                    participant="baton.claude", generation=1, now=NOW,
                    policies=POLICIES, record_binding=BINDING,
                    assignment_contract="v12-assignment-1",
                    human_contract=HUMAN, role_instructions_digest=ROLE,
                    runtime_profile_digest=PROFILE,
                    toolchain_digest=TOOLCHAIN, adapter_digest=IMAGE,
                    adapter_name="oci", labels={"attempt": "attempt-1"},
                    retention_policy_digest=POLICIES[
                        "retention_policy_digest"],
                    retention_disposition="discard-after-intake",
                    bearer="one-use-bearer")

        self.assertIn("callable pass_work", str(caught.exception))
        staged.assert_not_called()

    def succeeding(self, session, patches, *, receipt=None, retention=None):
        """Everything a successful arc needs mocked, and nothing more.

        Reuses this class's fixture rather than a second one: the case is
        about what happens AFTER retention, so every step before it answers
        the way the real operations do on their success path.
        """
        import baton_v12.worker_manager as manager
        from baton_v12.worker_manager import worker_entry

        spoken = {"ending": "answered", "why": "clean",
                  "answers": [{"operation": "work",
                               "answer": {"disposition": "completed",
                                          "outputs": [], "recap": "done"}}]}
        patches.enter_context(mock.patch.object(
            worker_entry, "converse", return_value=spoken))
        for name, answer in (
                ("reconcile_runtime", {}), ("observe", {}),
                ("request_freeze", {"attempt_id": "attempt-1",
                                    "result_id": "result-attempt-1",
                                    "disposition": "completed",
                                    "manifest_digest": "sha256:" + "a" * 64,
                                    "freeze_operation_id": "freeze:attempt-1",
                                    "frozen_at": NOW, "artifacts": []})):
            patches.enter_context(mock.patch.object(
                manager, name, return_value=answer))
        patches.enter_context(mock.patch.object(
            manager, "request_intake",
            return_value=receipt if receipt is not None else {"receipt_digest": "sha256:" + "b" * 64,
                                  "result_id": "result-attempt-1",
                                  "manifest_digest": "sha256:" + "a" * 64,
                                  "artifacts": [
                                      {"artifact_id": "proposal-1",
                                       "content_digest": "sha256:" + "c" * 64,
                                       "bytes": 12,
                                       "custody_locator": "custody://p-1"}]}))
        patches.enter_context(mock.patch.object(
            dogfood_operator, "_derived",
            return_value={"changed_paths": [], "verification_status": 0,
                          "verification_argv": ["python3", "harness.py"],
                          "members_present": ["candidate"]}))
        patches.enter_context(mock.patch.object(
            manager, "decide_retention",
            return_value=retention if retention is not None else {
                "disposition": "discard-after-intake",
                "retention_policy_digest": POLICIES[
                    "retention_policy_digest"]}))
        # THE MANAGER'S OWN READERS, because the retry asks them rather than
        # believing the retained file.
        patches.enter_context(mock.patch.object(
            manager, "frozen_output_of",
            return_value={"manifest_digest": "sha256:" + "a" * 64,
                          "result_id": "result-attempt-1"}))
        patches.enter_context(mock.patch.object(
            manager, "intake_receipt_of",
            return_value={"receipt_digest": "sha256:" + "b" * 64,
                          "result_id": "result-attempt-1",
                          "manifest_digest": "sha256:" + "a" * 64,
                          "artifacts": [
                              {"artifact_id": "proposal-1",
                               "content_digest": "sha256:" + "c" * 64,
                               "bytes": 12,
                               "custody_locator": "custody://p-1"}]}))
        patches.enter_context(mock.patch.object(
            manager, "retentions_of",
            return_value=({"artifact_id": "proposal-1",
                           "disposition": "discard-after-intake",
                           "retention_policy_digest": POLICIES[
                               "retention_policy_digest"]},)))
        return patches

    def arc(self, session, *, cleanup=None, retention=None, receipt=None,
            disposition="discard-after-intake"):
        """Drive the post-start owner through a successful custody path.

        `retention` and `disposition` are threaded for W51473: retention is
        now an operator grant, so a case has to be able to say both what was
        ASKED for and what the manager COMMITTED, and the two are deliberately
        separable -- the ending is derived from the second.
        """
        import baton_v12.worker_manager as manager

        adapter = self.Adapter()
        evidence = {"conversation": None, "worker_disposition": None,
                    "cleanup": None, "resolved": False, "unresolved": []}
        with ExitStack() as patches:
            self.succeeding(session, patches, retention=retention,
                            receipt=receipt)
            ended = patches.enter_context(mock.patch.object(
                manager, "authorize_cleanup",
                side_effect=lambda *a, **k: (
                    session.order.append("cleanup"),
                    cleanup if cleanup is not None
                    else {"cleanup": "complete", "state": "absent"})[-1]))
            answered = dogfood_operator._after_start(
                object(), object(), session, adapter, evidence,
                engine="docker", open_channel=lambda _argv: None,
                attempt_id="attempt-1", runtime_id="runtime-1",
                roots={}, task=dict(TASK), source=self.source,
                expect=dict(EXPECT), review_route="rview",
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"],
                retention_disposition=disposition, seconds=1)
        return adapter, answered, ended

    def test_a_successful_attempt_is_passed_to_review_before_cleanup(self):
        """Approver ruling M44657, in one case.

        The v11 lifecycle is preserved: the deployment does not close the
        Work, it hands the EXACT assignment generation to a review Route it
        was given. The order matters as much as the act -- the pass both moves
        the Route and ends the assignment, so cleanup afterwards is cleanup of
        an assignment that is over rather than one the authority still
        considers live.
        """
        session = PassingSession()

        _adapter, answered, ended = self.arc(session)

        self.assertEqual(len(session.passes), 1)
        passed = session.passes[0]
        self.assertEqual(passed["expect"], EXPECT,
                         "the EXACT assignment generation, not a fresh one")
        self.assertEqual(passed["to_route"], "rview",
                         "the route the operator named, never a default")
        self.assertEqual(passed["operation_id"], "pass:attempt-1",
                         "derived from the attempt, so a replay does not "
                         "pass a second time")
        self.assertIsNotNone(passed["comment"])
        self.assertEqual(session.order, ["pass", "cleanup"],
                         "cleanup ran before the assignment was passed")
        ended.assert_called_once()
        self.assertEqual(answered["review_pass"]["route"], "rview")
        self.assertTrue(answered["resolved"])

    def test_failed_independent_verification_never_passes_to_review(self):
        """Deriving a status is not the same as requiring it to succeed.

        A candidate whose frozen verification command exited nonzero is not
        the independently verified result the approver authorized for the
        success handoff.  Intake still authorizes a manager settlement
        request, but the exact assignment must remain live and unpassed.
        """
        import baton_v12.worker_manager as manager

        session = PassingSession()
        adapter = self.Adapter()
        evidence = {"conversation": None, "worker_disposition": None,
                    "cleanup": None, "resolved": False, "unresolved": []}
        with ExitStack() as patches:
            self.succeeding(session, patches)
            patches.enter_context(mock.patch.object(
                dogfood_operator, "_derived",
                return_value={"changed_paths": ["harness.py"],
                              "verification_argv": ["false"],
                              "verification_status": 1,
                              "members_present": list(
                                  dogfood_operator.PROPOSAL_MEMBERS)}))
            cleanup = patches.enter_context(mock.patch.object(
                manager, "authorize_cleanup",
                side_effect=ContractRefusal(
                    "refused", "precondition",
                    "the assignment is still the live one")))
            answered = dogfood_operator._after_start(
                object(), object(), session, adapter, evidence,
                engine="docker", open_channel=lambda _argv: None,
                attempt_id="attempt-1", runtime_id="runtime-1",
                roots={}, task=dict(TASK), source=self.source,
                expect=dict(EXPECT), review_route="rview",
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"],
                retention_disposition="discard-after-intake", seconds=1)

        self.assertEqual(session.passes, [],
                         "a candidate that failed verification was passed")
        cleanup.assert_called_once()
        self.assertFalse(answered["resolved"])
        self.assertTrue(any("verification" in one
                            for one in answered["unresolved"]))

    def test_the_route_kept_is_the_one_the_authority_recorded(self):
        """An authority that put the Work somewhere else is not a pass.

        What the evidence carries is the transition that happened, so an
        answer naming another route is a refusal rather than a record of the
        operand this deployment asked for.
        """
        session = PassingSession(route="somewhere-else")

        _adapter, answered, _ended = self.arc(session)

        self.assertFalse(answered["resolved"])
        self.assertTrue(any("somewhere-else" in one
                            for one in answered["unresolved"]),
                        "a pass to another route was reported as success")

    def test_a_pass_answer_for_another_assignment_is_not_adopted(self):
        """The authority answer must prove the exact generation ended.

        Merely echoing the requested Route is not proof that the pass applied
        to this attempt's assignment. The real authority answer carries the
        ended assignment, and an answer naming another generation must not be
        retained as this attempt's successful review pass.
        """
        session = PassingSession()
        session.answer = {
            "route": "rview", "cause": "pass", "phase": "queued",
            "gate": None, "fenced": False,
            "assignment": {**EXPECT, "generation": 2}}

        with self.assertRaises(dogfood_operator._Lost):
            dogfood_operator._passed(
                session, EXPECT, "rview", attempt_id="attempt-1")

    def test_a_pass_answer_that_did_not_queue_ungated_is_not_adopted(self):
        """Every carried ending fact is held, not merely required by name."""
        session = PassingSession()
        session.answer = {
            "route": "rview", "cause": "pass", "phase": "active",
            "gate": "runtime-quiescence:1", "fenced": False,
            "assignment": dict(EXPECT)}

        with self.assertRaises(dogfood_operator._Lost):
            dogfood_operator._passed(
                session, EXPECT, "rview", attempt_id="attempt-1")

    def test_a_refused_pass_is_unresolved_and_still_reaches_the_ending(self):
        """The pass is fallible and it is inside the guarded body.

        A deployment that could not hand the Work on has not finished the arc,
        so `resolved` is false -- and because the receipt is already committed,
        the ending still runs and the manager decides what it can settle.
        """
        session = PassingSession()
        session.answer = ContractRefusal("refused", "precondition",
                                         "the assignment is not live")

        _adapter, answered, ended = self.arc(session)

        self.assertFalse(answered["resolved"])
        self.assertEqual(len(session.passes), 1)
        ended.assert_called_once()
        self.assertTrue(any("assignment is not live" in one
                            for one in answered["unresolved"]))

    @staticmethod
    def committed(patches, **overrides):
        """The three public manager readers a narrow retry now consults.

        Required by review 2026-08-30T15:10:12Z [P0]: the retained record is
        operator-editable, so the retry replay-reads what the manager
        committed rather than believing the file. A case driving the retry has
        to say what the manager holds.
        """
        import baton_v12.worker_manager as manager

        answers = {
            "frozen_output_of": {
                "manifest_digest": "sha256:" + "a" * 64,
                "result_id": "result-attempt-1"},
            "intake_receipt_of": {
                "receipt_digest": "sha256:" + "b" * 64,
                "artifacts": [{"artifact_id": "proposal-1",
                               "content_digest": "sha256:" + "c" * 64,
                               "bytes": 12,
                               "custody_locator":
                                   "file:///custody/proposal"}]},
            "retentions_of": ({"artifact_id": "proposal-1",
                               "disposition": "discard-after-intake",
                               "retention_policy_digest": POLICIES[
                                   "retention_policy_digest"]},)}
        answers.update(overrides)
        for name, answer in answers.items():
            patches.enter_context(mock.patch.object(manager, name,
                                                    return_value=answer))
        return patches

    def trusted(self, **overrides):
        """This deployment's own record of a completed, verified result."""
        given = {one: None for one in dogfood_operator.EVIDENCE_MEMBERS}
        given.update({
            "attempt_id": "attempt-1", "runtime_id": "runtime-1",
            "worker_disposition": "completed",
            "intake_receipt": {"receipt_digest": "sha256:" + "b" * 64},
            "custody": [{"artifact_id": "proposal-1",
                         "content_digest": "sha256:" + "c" * 64,
                         "bytes": 12,
                         "custody_locator": "file:///custody/proposal"}],
            "independent": {"changed_paths": ["harness.py"],
                            "verification_status": 0},
            "retention": {"disposition": "discard-after-intake",
                          "retention_policy_digest": POLICIES[
                              "retention_policy_digest"],
                          "artifact_ids": ["proposal-1"]},
            "output": {"manifest_digest": "sha256:" + "a" * 64,
                       "result_id": "result-attempt-1"},
            "quiescence": {"ordered": True, "state": "quiescent"},
            "resolved": False, "unresolved": ["the review pass refused"]})
        given.update(overrides)
        return given

    def test_a_failed_pass_still_requests_manager_settlement(self):
        """Approver ruling M46497 item 6, and WHY it is safe.

        After a committed intake receipt, settlement is always requested --
        even when the pass refused. It is safe because the manager refuses
        destructive cleanup over a live assignment, so what an uncommitted
        pass produces is an explicit unresolved attempt for retry or W44716
        abandonment, not a torn-down runtime. Successful cleanup stays ordered
        behind a committed pass by the manager's own rule rather than by this
        deployment second-guessing it.
        """
        import baton_v12.worker_manager as manager

        session = PassingSession()
        session.answer = ContractRefusal("refused", "precondition",
                                         "the assignment is still live")
        adapter = self.Adapter()
        with ExitStack() as patches:
            self.succeeding(session, patches)
            asked = patches.enter_context(mock.patch.object(
                manager, "authorize_cleanup",
                side_effect=ContractRefusal(
                    "refused", "precondition",
                    "the assignment is still the live one")))
            answered = dogfood_operator._after_start(
                object(), object(), session, adapter, {
                    "conversation": None, "worker_disposition": None,
                    "cleanup": None, "resolved": False, "unresolved": []},
                engine="docker", open_channel=lambda _argv: None,
                attempt_id="attempt-1", runtime_id="runtime-1",
                roots={}, task=dict(TASK), source=self.source,
                expect=dict(EXPECT), review_route="rview",
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"],
                retention_disposition="discard-after-intake", seconds=1)

        asked.assert_called_once()
        self.assertFalse(answered["resolved"])
        self.assertIsNone(answered.get("review_pass"))

    def test_the_narrow_retry_hands_on_a_trusted_result_and_nothing_else(self):
        """Approver ruling item 7: retry the machinery, not the work.

        A worker that succeeded and whose candidate this operator independently
        rederived is not made untrustworthy by a pass that refused afterwards.
        What the retry must NOT do is the list this case measures: no restage,
        no reassignment, no runtime, no provider turn, no worker run, no
        freeze, no rederivation.
        """
        import baton_v12.worker_manager as manager
        from baton_v12.worker_manager import worker_entry

        session = PassingSession()
        adapter = self.Adapter()
        evidence = self.trusted()
        with ExitStack() as patches:
            self.committed(patches)
            spoke = patches.enter_context(mock.patch.object(
                worker_entry, "converse"))
            staged = patches.enter_context(mock.patch.object(
                dogfood_operator, "stage_source"))
            derived = patches.enter_context(mock.patch.object(
                dogfood_operator, "_derived"))
            for name in ("issue_offer", "accept_offer", "submit_claim",
                         "request_runtime_start", "request_freeze",
                         "request_intake"):
                patches.enter_context(mock.patch.object(
                    manager, name, side_effect=AssertionError(
                        f"the narrow retry called {name}")))
            cleanup = patches.enter_context(mock.patch.object(
                manager, "authorize_cleanup",
                return_value={"cleanup": "complete", "state": "absent"}))
            answered = dogfood_operator.retry_handoff(
                object(), object(), session, adapter, evidence,
                expect=dict(EXPECT), review_route="rview",
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"])

        self.assertEqual(len(session.passes), 1)
        self.assertEqual(answered["review_pass"]["route"], "rview")
        cleanup.assert_called_once()
        spoke.assert_not_called()
        staged.assert_not_called()
        derived.assert_not_called()
        self.assertEqual(adapter.stops, [],
                         "the retry stopped a runtime the arc already quiesced")

    def test_the_narrow_retry_replays_an_already_committed_pass(self):
        """Idempotence is at the AUTHORITY, not at this deployment.

        Superseded measure, review 2026-08-30T15:41:53Z [P0]: this used to
        assert that a recorded pass meant no authority call at all. That made
        an editable file able to suppress the one act that can show the pass
        happened. The pass carries this attempt's own operation identity, so
        replaying it returns the authority's committed answer rather than
        passing twice -- which is what idempotent means here -- and the
        recorded projection is held whole against that answer.
        """
        import baton_v12.worker_manager as manager

        session = PassingSession()
        evidence = self.trusted(review_pass={
            "route": "rview", "cause": "pass", "phase": "queued",
            "gate": None, "fenced": False, "assignment": dict(EXPECT)})
        with ExitStack() as patches:
            self.committed(patches)
            cleanup = patches.enter_context(mock.patch.object(
                manager, "authorize_cleanup",
                return_value={"cleanup": "complete", "state": "absent"}))
            dogfood_operator.retry_handoff(
                object(), object(), session, self.Adapter(), evidence,
                expect=dict(EXPECT), review_route="rview",
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"])

        self.assertEqual(len(session.passes), 1,
                         "an editable record suppressed the authority replay")
        self.assertEqual(session.passes[0]["operation_id"],
                         "pass:attempt-1",
                         "the replay did not carry the attempt's own identity")
        cleanup.assert_called_once()

    def test_the_narrow_retry_converges_after_the_handoff_succeeds(self):
        """Old handoff failures are history, not permanent current gates.

        The retained record necessarily names why the first pass/settlement
        was unresolved.  When the exact retry commits the pass and proves
        cleanup complete with the runtime absent, the command must converge
        to resolved rather than preserve those stale reasons as an eternal
        nonzero exit.
        """
        import baton_v12.worker_manager as manager

        evidence = self.trusted(
            unresolved=["the review pass refused",
                        "the manager declined to end the attempt"])
        with ExitStack() as patches:
            # ADAPTED, NOT CHANGED: review 2026-08-30T15:10:12Z [P0] makes the
            # retry consult the manager's own readers, so a case driving it
            # has to say what the manager holds. Assertions untouched.
            self.committed(patches)
            patches.enter_context(mock.patch.object(
                manager, "authorize_cleanup",
                return_value={"cleanup": "complete", "state": "absent"}))
            answered = dogfood_operator.retry_handoff(
                object(), object(), PassingSession(), self.Adapter(), evidence,
                expect=dict(EXPECT), review_route="rview",
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"])

        self.assertTrue(answered["resolved"],
                        "a successful exact handoff retry still exits nonzero")
        self.assertEqual(answered["unresolved"], [])

    def test_the_narrow_retry_requires_a_committed_retention_decision(self):
        """A verified custody receipt is not yet the retained handoff result.

        The ordinary arc orders ``decide_retention`` before the review pass.
        If that manager act refuses, the evidence still has a completed
        disposition, intake receipt, custody and successful independent
        verification -- the four truthy members the retry currently calls a
        trusted result.  Retrying only pass and cleanup from there skips the
        failed retention step and hands on a result whose required ordering
        never completed.
        """
        evidence = self.trusted(
            output=None,
            unresolved=["a manager contract declined: retention refused"])
        session = PassingSession()

        with self.assertRaises(OperatorRefusal):
            dogfood_operator.retry_handoff(
                object(), object(), session, self.Adapter(), evidence,
                expect=dict(EXPECT), review_route="rview",
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"])

        self.assertEqual(session.passes, [],
                         "retry passed a result with no retention decision")

    def test_editable_evidence_does_not_mint_durable_freeze_and_retention(self):
        """Presence in the retained JSON is not a committed manager fact.

        The evidence file is explicitly operator-editable and therefore
        untrusted on read.  Adding truthy ``output`` and ``retention`` members
        must not create the freeze/retention ordering that licenses a review
        pass when the manager's own durable readers find neither act.
        """
        import baton_v12.worker_manager as manager

        session = PassingSession()
        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                manager, "frozen_output_of", return_value=None))
            patches.enter_context(mock.patch.object(
                manager, "intake_receipt_of", return_value=None))
            patches.enter_context(mock.patch.object(
                manager, "retentions_of", return_value=()))
            patches.enter_context(mock.patch.object(
                manager, "authorize_cleanup",
                return_value={"cleanup": "complete", "state": "absent"}))

            with self.assertRaises(OperatorRefusal):
                dogfood_operator.retry_handoff(
                    object(), object(), session, self.Adapter(),
                    self.trusted(), expect=dict(EXPECT),
                    review_route="rview",
                    retention_policy_digest=POLICIES[
                        "retention_policy_digest"])

        self.assertEqual(session.passes, [],
                         "editable evidence minted a durable handoff result")

    def test_editable_evidence_must_match_every_recorded_manager_fact(self):
        """A partial comparison still lets the file rewrite committed facts.

        The deployment records each of these members because it says the
        manager answered them. A retry that compares only the manifest and
        artifact name accepts a different result, receipt, artifact content or
        retention set while truthfully claiming it replay-read the manager.
        """
        mutations = (
            ("frozen result", {
                "output": {"manifest_digest": "sha256:" + "a" * 64,
                           "result_id": "another-result"}}),
            ("intake receipt", {
                "intake_receipt": {"receipt_digest": "sha256:" + "9" * 64}}),
            ("custody content", {
                "custody": [{"artifact_id": "proposal-1",
                             "content_digest": "sha256:" + "9" * 64,
                             "bytes": 12,
                             "custody_locator":
                                 "file:///custody/proposal"}]}),
            ("retention artifacts", {
                "retention": {
                    "disposition": "discard-after-intake",
                    "retention_policy_digest": POLICIES[
                        "retention_policy_digest"],
                    "artifact_ids": ["another-artifact"]}}))
        for fact, changed in mutations:
            with self.subTest(fact=fact):
                session = PassingSession()
                with ExitStack() as patches:
                    self.committed(patches)
                    with self.assertRaises(OperatorRefusal):
                        dogfood_operator.retry_handoff(
                            object(), object(), session, self.Adapter(),
                            self.trusted(**changed), expect=dict(EXPECT),
                            review_route="rview",
                            retention_policy_digest=POLICIES[
                                "retention_policy_digest"])
                self.assertEqual(
                    session.passes, [],
                    f"editable evidence rewrote the committed {fact}")

    def test_malformed_nested_evidence_is_a_refusal_not_a_python_fault(self):
        """An editable record must be held before its members are consumed.

        ``read_evidence`` proves the top-level member set and secret boundary,
        but those facts do not make an allowed member a document.  A retained
        boolean, string or malformed custody item is untrusted operator input;
        leaking ``AttributeError``/``TypeError``/``KeyError`` from it makes the
        documented retry an unsafe parser rather than a typed boundary.
        """
        malformed = (
            ("independent", {"independent": True}),
            ("output", {"output": True}),
            ("intake receipt", {"intake_receipt": True}),
            ("custody", {"custody": [True]}),
            ("retention", {"retention": "discard-after-intake"}),
            ("unresolved history", {"unresolved": True}))
        for member, changed in malformed:
            with self.subTest(member=member):
                session = PassingSession()
                with ExitStack() as patches:
                    self.committed(patches)
                    with self.assertRaises(OperatorRefusal):
                        dogfood_operator.retry_handoff(
                            object(), object(), session, self.Adapter(),
                            self.trusted(**changed), expect=dict(EXPECT),
                            review_route="rview",
                            retention_policy_digest=POLICIES[
                                "retention_policy_digest"])
                self.assertEqual(
                    session.passes, [],
                    f"malformed {member} reached the authority pass")

    def test_editable_review_pass_cannot_suppress_the_authority_replay(self):
        """The file identifies a pass; the authority proves it committed.

        A narrow retry uses an effectively-once pass identity, so asking the
        authority again safely replays a committed pass. Trusting a non-null
        ``review_pass`` from the editable file instead lets that file skip the
        exact authority act this command promises to finish.
        """
        import baton_v12.worker_manager as manager

        session = PassingSession()
        claimed = {"route": "rview", "cause": "pass", "phase": "queued",
                   "gate": None, "fenced": False,
                   "assignment": dict(EXPECT)}
        with ExitStack() as patches:
            self.committed(patches)
            patches.enter_context(mock.patch.object(
                manager, "authorize_cleanup",
                return_value={"cleanup": "complete", "state": "absent"}))
            dogfood_operator.retry_handoff(
                object(), object(), session, self.Adapter(),
                self.trusted(review_pass=claimed), expect=dict(EXPECT),
                review_route="rview",
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"])

        self.assertEqual(len(session.passes), 1,
                         "editable evidence suppressed authority replay")

    def test_the_retry_binding_covers_every_identity_the_handoff_uses(self):
        """Cross-attempt, cross-work, cross-generation and changed image or
        network are all the same fault: two attempts being spliced.

        The review named the attempt; the pass is composed from more than
        that, so each identity the handoff actually uses is bound. A record
        whose attempt name matched while the work, participant or generation
        did not would still be another attempt's result.
        """
        grants = {"attempt_id": "attempt-1", "work_ref": dict(WORK_REF),
                  "participant": "baton.claude", "generation": 1,
                  "image_digest": IMAGE, "network": "baton-dogfood"}
        for member, wrong in (
                ("attempt_id", "another-attempt"),
                ("work_ref", {"authority_uuid": "0" * 32,
                              "work_id": "0" * 8 + "-W1"}),
                ("participant", "baton.other"),
                ("generation", 2),
                ("worker_image_digest", "sha256:" + "9" * 64),
                ("network", "another-network")):
            with self.subTest(member=member):
                record = self.trusted(
                    work_ref=dict(WORK_REF), participant="baton.claude",
                    generation=1, worker_image_digest=IMAGE,
                    network="baton-dogfood", attempt_id="attempt-1")
                record[member] = wrong

                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator._retried(record, grants, {}, "out.json")

                self.assertIn(member, str(caught.exception))

    def test_a_matching_record_reaches_the_capability_path(self):
        """The binding is a gate and not a wall: an agreeing record proceeds.

        Proved by observing that the retry-capability builder is the FIRST
        outward thing reached, which is also what makes the negative cases
        above meaningful.
        """
        grants = {"attempt_id": "attempt-1", "work_ref": dict(WORK_REF),
                  "participant": "baton.claude", "generation": 1,
                  "image_digest": IMAGE, "network": "baton-dogfood",
                  # W51473: the retry is held to the COMMITTED disposition too,
                  # so an agreeing record needs an agreeing grant.
                  "retention_disposition": "discard-after-intake"}
        record = self.trusted(
            work_ref=dict(WORK_REF), participant="baton.claude",
            generation=1, worker_image_digest=IMAGE,
            network="baton-dogfood", attempt_id="attempt-1")
        reached = []

        with self.assertRaises(RuntimeError):
            dogfood_operator._retried(
                record, grants,
                lambda _e, _g: reached.append(True) or (_ for _ in ()).throw(
                    RuntimeError("the capability path was reached")),
                "out.json")

        self.assertEqual(reached, [True])

    def test_retry_root_proof_refuses_a_symlink_alias(self):
        """Restart lookup keeps allocation's no-alias containment proof.

        ``assignment_workspace`` explicitly refuses a symlink at the attempt
        home or either root.  A retry lookup that uses ``isdir`` follows that
        link and lets a different tree become this attempt's adapter root.
        """
        storage = os.path.join(self.home, "storage")
        attempt = os.path.join(storage, "attempt-1")
        elsewhere = os.path.join(self.home, "elsewhere")
        os.makedirs(attempt)
        os.makedirs(elsewhere)
        os.makedirs(os.path.join(attempt, "workspace"))
        os.symlink(elsewhere, os.path.join(attempt, "inputs"))

        with self.assertRaises(OperatorRefusal):
            dogfood_operator._proved_roots(
                {"storage": storage, "attempt_id": "attempt-1"})

    def test_the_narrow_retry_refuses_an_attempt_with_no_trusted_result(self):
        """Its whole licence is that a result worth preserving exists.

        An attempt with no receipt, no custody or no independent derivation
        did not reach one, and its ending is W44716's abandonment rather than
        a handoff of something nobody has.
        """
        for absent in ("worker_disposition", "intake_receipt", "custody",
                       "independent"):
            with self.subTest(missing=absent):
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.retry_handoff(
                        object(), object(), PassingSession(), self.Adapter(),
                        self.trusted(**{absent: None}),
                        expect=dict(EXPECT), review_route="rview",
                        retention_policy_digest=POLICIES[
                            "retention_policy_digest"])
                self.assertIn(absent, str(caught.exception))

    def test_the_narrow_retry_refuses_evidence_for_another_attempt_first(self):
        """A closed member set does not bind a retained result to grants.

        The evidence attempt is the identity used for the pass operation and
        manager settlement.  It must agree with the durable grant before any
        store, workspace, credential delivery or adapter capability is
        touched; otherwise a valid result record can be paired with another
        assignment's grants.
        """
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator._retried(
                self.trusted(attempt_id="attempt-from-evidence"),
                {"attempt_id": "attempt-from-grants"}, {}, self.task())

        self.assertIn("attempt", str(caught.exception))

    def test_an_empty_intake_receipt_still_authorizes_cleanup(self):
        """A committed receipt is the authorization even when it is empty.

        W39358 review 2026-08-30T06:44:13Z [P0] required every early custody
        ending to reach manager cleanup. Raising instead of returning closes
        the control-flow bypass only if the durable receipt is recorded in the
        operator evidence BEFORE its artifacts are interpreted.
        """
        import baton_v12.worker_manager as manager
        from baton_v12.worker_manager import worker_entry

        adapter = self.Adapter()
        evidence = {"conversation": None, "worker_disposition": None,
                    "cleanup": None, "resolved": False, "unresolved": []}
        spoken = {
            "ending": "answered", "why": "clean",
            "answers": [
                {"operation": "work",
                 "answer": {"disposition": "completed"}}]}
        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                worker_entry, "converse", return_value=spoken))
            for name, answer in (
                    ("reconcile_runtime", {}), ("observe", {}),
                    # ADAPTED: the arc now records the manager's EXACT frozen
                    # answer rather than asserting `frozen=True`, so the
                    # fixture answers with the document `request_freeze`
                    # actually returns. Assertions untouched.
                    ("request_freeze",
                     {"attempt_id": "attempt-1",
                      "result_id": "result-attempt-1",
                      "disposition": "completed",
                      "manifest_digest": "sha256:" + "a" * 64,
                      "freeze_operation_id": "freeze:attempt-1",
                      "frozen_at": NOW, "artifacts": []}),
                    # ADAPTED: the arc now records the receipt's OWN digest
                    # rather than a boolean, so an empty receipt is still a
                    # receipt with an identity. Assertions untouched.
                    ("request_intake",
                     {"receipt_digest": "sha256:" + "b" * 64,
                      "result_id": "result-attempt-1",
                      "manifest_digest": "sha256:" + "a" * 64,
                      "artifacts": []})):
                patches.enter_context(mock.patch.object(
                    manager, name, return_value=answer))
            cleanup = patches.enter_context(mock.patch.object(
                manager, "authorize_cleanup",
                return_value={"cleanup": "complete", "state": "absent"}))
            answered = dogfood_operator._after_start(
                object(), object(), object(), adapter, evidence,
                engine="docker", open_channel=lambda _argv: None,
                attempt_id="attempt-1", runtime_id="runtime-1",
                roots={}, task=dict(TASK), source=self.source,
                expect=dict(EXPECT), review_route="rview",
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"],
                retention_disposition="discard-after-intake", seconds=1)
        cleanup.assert_called_once()
        self.assertEqual(answered["cleanup"],
                         {"cleanup": "complete", "state": "absent"})

    def test_receiptless_abandonment_does_not_stop_before_the_fence(self):
        """The composite manager operation owns fence-before-runtime order."""
        import baton_v12.worker_manager as manager

        adapter = self.Adapter()
        evidence = {"quiescence": None, "intake_receipt": False,
                    "resolved": False,
                    "unresolved": ["the worker conversation was lost"]}
        with mock.patch.object(
                manager, "abandon_attempt",
                return_value={"intent": {}, "fenced": {"fenced": True},
                              "cleanup": {"cleanup": "retained",
                                          "state": "absent"}}) as abandon:
            dogfood_operator._ended_however(
                object(), object(), adapter, evidence,
                attempt_id="attempt-1", runtime_id="runtime-1",
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"])

        abandon.assert_called_once()
        self.assertEqual(adapter.stops, [],
                         "runtime control happened before abandonment fenced")


class TheHumanContractIsHeldBeforeAnySideEffect(OperatorCase):
    """W51476, found by W39364's first live invocation rather than by reading.

    `preflight` held the policies, the record binding, the network, the review
    route and the task. `human_contract` was copied into the frozen manifest
    and validated for the first time by `check_input_pair` -- which
    `compose_input_root` runs AFTER `stage_source` wrote the delivery, after
    `submit_claim`, after `activate_assignment` and after the credential home
    materialized the attempt's slot.

    THE TWO GRAMMARS ARE THE DEFECT. `artifactRef`'s `locator` pattern admits
    `scheme:anything`; `contracts.manifest.check_uri` requires `scheme://` and
    an authority, or the `file:///absolute-path` form that deliberately has no
    host. A locator of `baton:work/records/...` -- the ordinary opaque
    spelling, and exactly what the live invocation carried -- satisfies the
    first and not the second, so the two lifecycle times disagreed and the
    later one owned the real contract.
    """

    def contract(self, **overrides):
        given = dict(HUMAN)
        given.update(overrides)
        return given

    def test_the_incident_locator_is_refused_at_the_preflight(self):
        """The exact value that got through, and where it now stops.

        Named as its own case rather than one row of a table: it is the one
        this Work exists for, and a regression that admitted it again should
        say so by name.
        """
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.held_human_contract(self.contract(
                locator="baton:work/records/2026/08/"
                        "finding-v12-first-useful-dogfood-task/evidence/"
                        "first-task.md"))

        self.assertIn("the frozen input manifest will accept",
                      str(caught.exception))
        # THE OWNER'S OWN SENTENCE, so an operator reads which rule it broke
        # rather than being sent to this file.
        self.assertIn("canonical locator", str(caught.exception))

    def test_the_narrower_manifest_grammar_is_the_one_applied(self):
        """Every form `artifactRef` admits and `check_uri` does not.

        MEASURED RATHER THAN ASSUMED, and the first cut of this case got it
        wrong: it also listed a query and a fragment, which `artifactRef`'s
        own pattern already excludes (`[^?#]*`). Removing `check_uri` left
        those two passing while the ten below failed, so listing them here
        would have credited the narrower owner with refusals the shape check
        was making. Each locator here is one that reached the frozen manifest
        under the old code and was refused halfway through an attempt.
        """
        for locator in ("baton:work/records/one.md",
                        "urn:uuid:0e9b",
                        "mailto:someone@example.com",
                        "https:shorthand",
                        "file:/one-slash/path",
                        "artifact://host/with a space",
                        "artifact://host/with\\a-backslash",
                        "ARTIFACT://host/upper-scheme"):
            with self.subTest(locator=locator):
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.held_human_contract(
                        self.contract(locator=locator))
                self.assertIn("the frozen input manifest will accept",
                              str(caught.exception))

    def test_a_query_or_fragment_is_refused_by_the_shape_owner(self):
        """The two the SCHEMA already owns, kept apart from the case above.

        §12 rule 4 is why: a query is where signed credentials and unstable
        selection parameters ride. Both owners refuse them, and this records
        which one gets there first so a future edit to either is visible.
        """
        for locator in ("artifact://host/with?a=query",
                        "artifact://host/with#a-fragment"):
            with self.subTest(locator=locator):
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.held_human_contract(
                        self.contract(locator=locator))
                self.assertIn("artifact reference", str(caught.exception))

    def test_a_locator_the_manifest_accepts_is_accepted_here(self):
        """The positive half, so the case above is not passing on everything.

        THE SUITE'S OWN FIXTURE IS ONE OF THESE, which is what makes every
        other case in this module evidence about the arc rather than about a
        contract the preflight would now reject.
        """
        for locator in (HUMAN["locator"],
                        "file:///home/one/first-task.md",
                        "artifact://contracts/human-1",
                        "https://example.test/contracts/one.md"):
            with self.subTest(locator=locator):
                held = dogfood_operator.held_human_contract(
                    self.contract(locator=locator))
                self.assertEqual(held["locator"], locator)

    def test_the_shape_comes_from_the_frozen_schema(self):
        """Exactly `artifactRef`'s members, and its value rules.

        Held through `_validate_fragment` rather than a member list kept here,
        so the operator and the manifest cannot disagree about what an
        artifact reference IS either.
        """
        malformed = (
            ("a missing member", {one: HUMAN[one] for one in HUMAN
                                  if one != "content_digest"}),
            ("an unexpected member", dict(HUMAN, extra="not a member")),
            ("a digest that is not one", dict(HUMAN, content_digest="sha256:")),
            ("a negative size", dict(HUMAN, bytes=-1)),
            ("a size that is text", dict(HUMAN, bytes="1200")),
            ("a media type that is not one", dict(HUMAN, media_type="text")),
            ("an identity with a slash", dict(HUMAN, artifact_id="a/b")),
            ("an empty identity", dict(HUMAN, artifact_id="")))
        for what, document in malformed:
            with self.subTest(what=what):
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.held_human_contract(document)
                self.assertIn("artifact reference", str(caught.exception))

    def test_a_contract_that_is_not_a_document_is_refused_by_type(self):
        for one in (None, "", [], "artifact://contracts/one", 12, True):
            with self.subTest(given=one):
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.held_human_contract(one)
                self.assertIn("one JSON object", str(caught.exception))

    def test_an_owner_defect_is_not_reported_as_a_bad_grant(self):
        """Only a typed contract judgement says the operator's grant is wrong.

        `OperatorRefusal` tells a human to edit their document. An
        implementation defect inside `check_uri` is not that, and relabelling
        it would hide the boundary that actually failed -- the same rule
        W39358 established for the network and locator owners.
        """
        import baton_v12.contracts as contracts

        def raising(*arguments, **operands):
            raise RuntimeError("the owner is broken")

        held = contracts.check_uri
        contracts.check_uri = raising
        self.addCleanup(setattr, contracts, "check_uri", held)

        with self.assertRaises(RuntimeError):
            dogfood_operator.held_human_contract(dict(HUMAN))

    def test_the_composer_applies_the_same_hold(self):
        """One function, two call sites, so the two cannot drift.

        A contract read valid at the preflight and changed afterwards is not
        the contract that gets frozen -- `held_task`'s rule, and this grant
        had no equivalent.
        """
        with self.assertRaises(OperatorRefusal):
            dogfood_operator.input_manifest(
                work_ref=dict(WORK_REF),
                staged={"entries": [], "entry_count": 0, "total_bytes": 0,
                        "tree_digest": "sha256:" + "f" * 64},
                created_at=NOW, manifest_id="input-attempt-1",
                assignment_contract="v12-assignment-1",
                human_contract=self.contract(locator="baton:changed/after.md"),
                record_binding=dict(BINDING),
                role_instructions_digest=ROLE,
                runtime_profile_digest=PROFILE, toolchain_digest=TOOLCHAIN,
                worker_image_digest=IMAGE, policies=dict(POLICIES))

    def commandable(self, **overrides):
        """A grants document the documented command can actually be given."""
        given = {one: f"{one}-value"
                 for one in dogfood_operator.GRANT_MEMBERS}
        given.update({
            "engine": "docker", "generation": 1, "work_ref": dict(WORK_REF),
            "policies": dict(POLICIES), "record_binding": dict(BINDING),
            "human_contract": dict(HUMAN), "labels": {"a": "b"},
            "network": "baton-dogfood", "review_route": "rview",
            "retention_disposition": "retain", "task_path": self.task(),
            "image_digest": IMAGE, "toolchain_digest": TOOLCHAIN,
            "runtime_profile_digest": PROFILE,
            "role_instructions_digest": ROLE})
        given.update(overrides)
        place = os.path.join(self.home, "grants.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(given, writing)
        return place

    def test_the_command_refuses_before_it_builds_a_capability(self):
        """W51476 review [P1], and it is the defect one layer further out.

        The shared hold was correct at both places it reached and `main`
        reached it too late: `capabilities(given)` runs BEFORE `compose`, and
        the real builder `_launched` opens the authority, opens the control
        store and calls `CredentialHome.materialize`. So W39364's exact
        malformed contract still materialized the attempt's credential slot
        before anything refused it.

        MY OWN ARC CASE DID NOT COVER THIS and my report said it did. It calls
        `run_dogfood_task` directly with an already-built delivery, so the
        builder is not in it at all; `assignment_workspace` is a workspace
        allocation and is not credential materialization. That claim was
        wrong, and this case is the one that would have caught it.

        THE BUILDER IS THE SPY, so the proof is about the ORDER of the
        documented command rather than about a message.
        """
        from baton_v12.worker_manager import credentials

        grants = self.commandable(human_contract=self.contract(
            locator="baton:work/records/2026/08/"
                    "finding-v12-first-useful-dogfood-task/evidence/"
                    "first-task.md"))
        built = []
        with mock.patch.object(credentials.CredentialHome,
                               "materialize") as delivered:
            with self.assertRaises(OperatorRefusal) as caught:
                dogfood_operator.main(
                    ["--grants", grants,
                     "--evidence", os.path.join(self.home, "out.json")],
                    capabilities=lambda given: built.append(given))

        self.assertIn("will not stage or start anything",
                      str(caught.exception))
        self.assertIn("the frozen input manifest will accept",
                      str(caught.exception))
        self.assertEqual(built, [],
                         "the ordinary capability builder was reached")
        self.assertEqual(delivered.call_count, 0,
                         "a refused human contract still materialized a "
                         "credential")

    def test_a_command_whose_grants_are_sound_still_reaches_the_builder(self):
        """The boundary is a gate and not a wall.

        Without this, the case above would pass just as well if `main` had
        stopped building capabilities altogether.
        """
        grants = self.commandable()
        built = []

        with self.assertRaises(RuntimeError):
            dogfood_operator.main(
                ["--grants", grants,
                 "--evidence", os.path.join(self.home, "out.json")],
                capabilities=lambda given: (
                    built.append(given),
                    (_ for _ in ()).throw(RuntimeError("the builder ran")))[0])

        self.assertEqual(len(built), 1)

    def test_the_command_boundary_holds_every_grant_it_can_judge(self):
        """Not only the human contract: the same owners, in one place.

        `_held_grants` calls `frozen_task` and `preflight`, so every grant
        those own is judged before a capability exists. A boundary that
        happened to catch this Work's operand and nothing else would be a
        boundary somebody has to remember to extend.
        """
        for member, value, expected in (
                ("network", "two words", "engine network name"),
                ("review_route", "", "review route"),
                ("retention_disposition", "keep", "frozen three"),
                ("record_binding", dict(BINDING, path="/absolute"),
                 "record binding"),
                ("human_contract", self.contract(locator="urn:x"),
                 "frozen input manifest")):
            with self.subTest(member=member):
                built = []
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.main(
                        ["--grants", self.commandable(**{member: value}),
                         "--evidence", os.path.join(self.home, "out.json")],
                        capabilities=lambda given: built.append(given))
                self.assertIn(expected, str(caught.exception))
                self.assertEqual(built, [], f"{member} reached the builder")

    def test_the_arc_refuses_before_a_single_side_effect(self):
        """The acceptance, and it is about ORDER rather than about a message.

        W39364's invocation reached the refusal with a staged delivery, a
        submitted claim, an activated assignment and a materialized credential
        slot already in place. This proves none of those happens now: every
        outward act the arc performs before `compose_input_root` is a spy, and
        all of them must be untouched.
        """
        import baton_v12.worker_manager as manager
        from baton_v12.worker_manager import workspaces, worker_entry

        watched = {}
        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                dogfood_operator, "frozen_task", return_value=dict(TASK)))
            for owner, name in ((dogfood_operator, "stage_source"),
                                (dogfood_operator, "_copied_task"),
                                (dogfood_operator, "input_manifest"),
                                (workspaces, "assignment_workspace"),
                                (workspaces, "compose_input_root"),
                                (manager, "issue_offer"),
                                (manager, "accept_offer"),
                                (manager, "submit_claim"),
                                (manager, "record_attempt"),
                                (manager, "activate_assignment"),
                                (manager, "retain_manifest"),
                                (manager, "request_runtime_start"),
                                (worker_entry, "converse")):
                watched[name] = patches.enter_context(
                    mock.patch.object(owner, name))

            with self.assertRaises(OperatorRefusal) as caught:
                dogfood_operator.run_dogfood_task(
                    engine="docker", run=lambda _argv: None,
                    open_channel=lambda _argv: None, store=object(),
                    port=object(), session=PassingSession(),
                    review_route="rview",
                    adapter_of=lambda **_operands: self.Adapter(),
                    attempt_id="attempt-1", offer_id="offer-1",
                    source=self.source, task_path=self.task(),
                    storage=self.home, launch_home=self.home,
                    credential_delivery=object(), image_digest=IMAGE,
                    network="baton-dogfood", work_ref=WORK_REF,
                    participant="baton.claude", generation=1, now=NOW,
                    policies=POLICIES, record_binding=BINDING,
                    assignment_contract="v12-assignment-1",
                    human_contract=self.contract(
                        locator="baton:work/records/one.md"),
                    role_instructions_digest=ROLE,
                    runtime_profile_digest=PROFILE,
                    toolchain_digest=TOOLCHAIN, adapter_digest=IMAGE,
                    adapter_name="oci", labels={"attempt": "attempt-1"},
                    retention_policy_digest=POLICIES[
                        "retention_policy_digest"],
                    retention_disposition="discard-after-intake",
                    bearer="one-use-bearer")

        self.assertIn("will not stage or start anything",
                      str(caught.exception))
        self.assertIn("the frozen input manifest will accept",
                      str(caught.exception))
        for name, spy in watched.items():
            self.assertEqual(
                spy.call_count, 0,
                f"a refused human contract still reached {name}")


class RetentionIsAnOperatorDecision(OperatorCase):
    # THE POST-START FIXTURE'S OWN HELPERS, REUSED BY NAME rather than copied.
    # `succeeding`, `arc`, `trusted` and `Adapter` belong to
    # `EveryPostStartBranchEntersTheEnding`; these cases are about the same
    # post-start owner and a second fixture for them would be a second set of
    # answers about one arc. Named explicitly rather than inherited, because
    # inheriting would re-run that class's cases under this one's name.
    Adapter = EveryPostStartBranchEntersTheEnding.Adapter
    succeeding = EveryPostStartBranchEntersTheEnding.succeeding
    arc = EveryPostStartBranchEntersTheEnding.arc
    trusted = EveryPostStartBranchEntersTheEnding.trusted
    """W51473, and the defect a live attempt found rather than a reading.

    W39364's first supervised attempt drove the whole arc against a real
    provider and then destroyed the thing it existed to produce: `_custody`
    passed the literal `"discard-after-intake"` to `decide_retention`, so the
    `retention_policy_digest` an operator granted named a policy whose
    DISPOSITION nothing read. The manager took custody of an 86,417-byte
    proposal, this operator derived it, and the discard removed the tree --
    taking `result.json`, the worker's own bounded account of its `unable`
    answer, and the candidate the review contract requires a human to inspect.

    AND IT IS NOT FIXED BY SWAPPING THE LITERAL, which is why these cases come
    in pairs. The manager ends cleanup `retained` whenever anything is kept,
    deliberately; this deployment used to call every ending but `complete` a
    failure. A `retain` literal would have preserved the bytes and left the
    documented command unresolved forever.
    """

    def test_the_disposition_is_the_managers_vocabulary_and_not_a_copy(self):
        """One vocabulary, imported -- not a second tuple spelled here.

        A second copy agrees until one of the two is edited, and the one that
        matters is the manager's: it is what `decide_retention` enforces and
        what `_settle` reads to choose the ending.
        """
        from baton_v12.worker_manager import RETENTION_DISPOSITIONS

        for one in RETENTION_DISPOSITIONS:
            with self.subTest(disposition=one):
                self.assertEqual(dogfood_operator.held_disposition(one), one)
        self.assertEqual(sorted(RETENTION_DISPOSITIONS),
                         ["discard-after-intake", "quarantine", "retain"])

    def test_an_absent_or_invented_disposition_is_refused_by_name(self):
        """No default, and no near-miss accepted.

        `""` and `None` are the operator who did not decide; `"discard"` and
        `"keep"` are the operator who decided in some other vocabulary. Both
        are refusals, because retention decides whether a supervised attempt
        leaves anything behind.
        """
        for one in (None, "", "discard", "keep", "RETAIN", True, ["retain"]):
            with self.subTest(disposition=one):
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.held_disposition(one)
                self.assertIn("frozen three", str(caught.exception))

    def test_preflight_refuses_before_anything_is_staged_or_started(self):
        """Beside the network and the review route, and for the same reason."""
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.preflight(
                task=TASK, policies=POLICIES, worker_image_digest=IMAGE,
                toolchain_digest=TOOLCHAIN, runtime_profile_digest=PROFILE,
                role_instructions_digest=ROLE, record_binding=BINDING,
                network="baton-dogfood", review_route="rview",
                retention_disposition="whatever-the-policy-says",
                human_contract=dict(HUMAN))
        self.assertIn("will not stage or start anything",
                      str(caught.exception))
        self.assertIn("frozen three", str(caught.exception))

    def test_the_grant_is_what_reaches_the_manager(self):
        """The operand is USED, not merely validated.

        A grant held at the boundary and dropped on the way to
        `decide_retention` would be the same defect wearing a validator.
        """
        import baton_v12.worker_manager as manager

        for asked in ("retain", "quarantine", "discard-after-intake"):
            with self.subTest(disposition=asked):
                session = PassingSession()
                with ExitStack() as patches:
                    self.succeeding(session, patches, retention={
                        "disposition": asked,
                        "retention_policy_digest": POLICIES[
                            "retention_policy_digest"]})
                    decided = patches.enter_context(mock.patch.object(
                        manager, "decide_retention",
                        return_value={"disposition": asked,
                                      "retention_policy_digest": POLICIES[
                                          "retention_policy_digest"]}))
                    patches.enter_context(mock.patch.object(
                        manager, "authorize_cleanup",
                        return_value={"cleanup": "retained"
                                      if asked != "discard-after-intake"
                                      else "complete", "state": "absent"}))
                    patches.enter_context(mock.patch.object(
                        dogfood_operator, "_kept", lambda _e: None))
                    dogfood_operator._after_start(
                        object(), object(), session, self.Adapter(),
                        {"conversation": None, "worker_disposition": None,
                         "cleanup": None, "resolved": False,
                         "unresolved": []},
                        engine="docker", open_channel=lambda _argv: None,
                        attempt_id="attempt-1", runtime_id="runtime-1",
                        roots={}, task=dict(TASK), source=self.source,
                        expect=dict(EXPECT), review_route="rview",
                        retention_policy_digest=POLICIES[
                            "retention_policy_digest"],
                        retention_disposition=asked, seconds=1)
                self.assertEqual(
                    decided.call_args.kwargs["disposition"], asked,
                    "the granted disposition did not reach the manager")

    def kept(self, disposition, cleanup):
        """One ending, with a committed disposition and a cleanup answer."""
        session = PassingSession()
        _adapter, answered, _ended = self.arc(
            session, cleanup=cleanup, disposition=disposition,
            retention={"disposition": disposition,
                       "retention_policy_digest": POLICIES[
                           "retention_policy_digest"]})
        return answered

    def test_an_intended_keep_ending_retained_is_resolved(self):
        """THE HALF A LITERAL SWAP WOULD HAVE MISSED.

        `retained` is the manager's terminal ending for kept material and it
        is not a failure. Both keeping dispositions are proved, because
        `quarantine` keeps material for a different reason and the deployment
        must not be reading `retain` by name.
        """
        for one in ("retain", "quarantine"):
            with self.subTest(disposition=one):
                with mock.patch.object(dogfood_operator, "_kept",
                                       lambda _e: None):
                    answered = self.kept(
                        one, {"cleanup": "retained", "state": "absent"})
                self.assertEqual(answered["unresolved"], [])
                self.assertTrue(answered["resolved"])
                self.assertEqual(answered["cleanup"],
                                 {"cleanup": "retained", "state": "absent"})

    def test_an_explicit_discard_ending_complete_is_still_resolved(self):
        """The semantics that must not regress."""
        answered = self.kept("discard-after-intake",
                             {"cleanup": "complete", "state": "absent"})
        self.assertEqual(answered["unresolved"], [])
        self.assertTrue(answered["resolved"])

    def test_an_ending_that_does_not_match_the_committed_decision_is_not(self):
        """Both directions, because each is a different lie.

        A keep that ended `complete` says material was cleaned up that policy
        said to keep. A discard that ended `retained` says material survived
        that policy said to remove. Neither is resolved, and the refusal names
        the committed decision so an operator can tell which happened.
        """
        for disposition, cleanup, expected in (
                ("retain", "complete", "'retained'"),
                ("discard-after-intake", "retained", "'complete'")):
            with self.subTest(disposition=disposition, cleanup=cleanup):
                with mock.patch.object(dogfood_operator, "_kept",
                                       lambda _e: None):
                    answered = self.kept(
                        disposition, {"cleanup": cleanup, "state": "absent"})
                self.assertFalse(answered["resolved"])
                self.assertTrue(
                    any(expected in one and repr(disposition) in one
                        for one in answered["unresolved"]),
                    answered["unresolved"])

    def test_a_keep_whose_material_is_gone_is_not_resolved(self):
        """The disk is asked, AFTER the removal, and it decides.

        `_settle` discards the execution roots inside the terminal
        transaction, so this is the first moment "the candidate is still
        there" is a fact. A keep whose locator names nothing is the exact
        outcome W39364 suffered, and reporting it resolved would be the same
        false clean ending in a new place.
        """
        session = PassingSession()
        gone = os.path.join(self.source, "no-such-custody")
        _adapter, answered, _ended = self.arc(
            session, cleanup={"cleanup": "retained", "state": "absent"},
            disposition="retain",
            retention={"disposition": "retain",
                       "retention_policy_digest": POLICIES[
                           "retention_policy_digest"]},
            receipt={"receipt_digest": "sha256:" + "b" * 64,
                     "result_id": "result-attempt-1",
                     "manifest_digest": "sha256:" + "a" * 64,
                     "artifacts": [{"artifact_id": "proposal-1",
                                    "content_digest": "sha256:" + "c" * 64,
                                    "bytes": 12,
                                    "custody_locator": f"file://{gone}"}]})

        self.assertFalse(answered["resolved"])
        self.assertTrue(any("is not a directory this operator can open" in one
                            for one in answered["unresolved"]),
                        answered["unresolved"])

    def test_a_keep_whose_locator_this_operator_cannot_open_is_not_resolved(
            self):
        """A scheme is refused as loudly as an absence.

        Both are "the operator cannot show a reviewer the candidate", which is
        the fact `retained` is supposed to promise. The post-start fixture's
        own receipt names `custody://p-1`, which is exactly such a locator, so
        this case varies nothing and reads what that arc already produces.
        """
        answered = self.kept(
            "retain", {"cleanup": "retained", "state": "absent"})

        self.assertFalse(answered["resolved"])
        self.assertTrue(any("local `file://` locator" in one
                            for one in answered["unresolved"]),
                        answered["unresolved"])

    def proposal(self, name="kept-proposal"):
        """A retained proposal in the shape this operator actually derives.

        W51473 review 2026-08-31T05:33:31Z [P1], second half: the positive
        fixture used to be an EMPTY directory, so the case meant to keep the
        negative ones honest was locking in a false positive -- an empty root
        opens and lists perfectly while the verification rerun has no `cwd`
        and the diff has nothing to compare. A positive fixture has to be a
        thing the acceptance could actually be performed on.
        """
        import os as _os

        root = _os.path.join(self.source, name)
        candidate = _os.path.join(root, "candidate", "v12", "spike")
        _os.makedirs(candidate, exist_ok=True)
        for place, body in (
                (_os.path.join(candidate, "harness.py"), "print('one')\n"),
                (_os.path.join(root, "change.patch"), ""),
                (_os.path.join(root, "result.json"), "{}\n"),
                (_os.path.join(root, "verification.txt"), "ok\n")):
            with open(place, "w", encoding="utf-8") as writing:
                writing.write(body)
        return root

    def inaccessible(self, mode, *, nested=False):
        """A real directory this process cannot use, cleaned up whatever
        happens.

        THE MODE IS RESTORED IN A CLEANUP, because a fixture that left a
        `000` directory behind would be a test making the tree harder to work
        in than it found it.
        """
        import os as _os

        root = _os.path.join(self.source, f"kept-{mode:o}-{int(nested)}")
        _os.makedirs(root, exist_ok=True)
        target = root
        if nested:
            target = _os.path.join(root, "candidate")
            _os.makedirs(target, exist_ok=True)
        self.addCleanup(_os.chmod, target, 0o755)
        _os.chmod(target, mode)
        return root

    def refuses_the_keep(self, root):
        evidence = {"custody": [{"artifact_id": "proposal-1",
                                 "content_digest": "sha256:" + "c" * 64,
                                 "bytes": 12,
                                 "custody_locator": f"file://{root}"}],
                    "unresolved": []}
        dogfood_operator._kept(evidence)
        return evidence["unresolved"]

    def test_a_retained_directory_that_cannot_be_opened_is_not_resolved(self):
        """W51473 review [P1], as its own regression.

        THE FIRST CUT PASSED THIS. Its only positive check was
        `os.path.isdir`, which performs a `stat` -- and a `stat` succeeds on a
        directory nobody may open. So a retained candidate at mode `000` was
        reported `resolved` while `os.listdir` on it raises
        `PermissionError`, and the implementation comment's claim that the
        locator was "PROVED to be openable" was false.

        The reviewer's reproduction, run here rather than described.
        """
        unresolved = self.refuses_the_keep(self.inaccessible(0o000))

        self.assertTrue(any("is not a directory this operator can open" in one
                            and "PermissionError" in one
                            for one in unresolved), unresolved)

    def test_a_retained_directory_that_cannot_be_traversed_is_not_resolved(
            self):
        """The other half of "openable", and the one a read-only mode hides.

        Mode `r--` opens and lists, and the documented uses still cannot act
        on it: the diff opens the files below it and the verification rerun
        executes with the candidate as its `cwd`, and both need SEARCH. The
        descriptor-relative `stat` is the step that needs what this mode
        withholds, so it is the step that refuses.
        """
        root = self.inaccessible(0o444)
        import os as _os
        # An entry to stat, so the traversal has something to reach for.
        self.addCleanup(_os.chmod, root, 0o755)
        _os.chmod(root, 0o755)
        with open(_os.path.join(root, "change.patch"), "w",
                  encoding="utf-8") as writing:
            writing.write("x\n")
        _os.chmod(root, 0o444)

        unresolved = self.refuses_the_keep(root)

        self.assertTrue(any("cannot be read" in one
                            and "PermissionError" in one
                            for one in unresolved), unresolved)

    def test_a_retained_subtree_that_cannot_be_opened_is_not_resolved(self):
        """The walk DESCENDS, because the documented uses do.

        A root that opens over a `candidate/` that does not is exactly the
        shape the review contract cannot act on: `_changed_paths` walks the
        whole tree and the rerun's `cwd` IS that subdirectory.
        """
        unresolved = self.refuses_the_keep(
            self.inaccessible(0o000, nested=True))

        self.assertTrue(any("cannot be read" in one
                            for one in unresolved), unresolved)

    def test_a_locator_naming_a_file_is_not_a_retained_candidate(self):
        """`O_DIRECTORY` is what answers this, in the same act as the open."""
        import os as _os

        place = _os.path.join(self.source, "not-a-directory")
        with open(place, "w", encoding="utf-8") as writing:
            writing.write("x\n")

        unresolved = self.refuses_the_keep(place)

        self.assertTrue(any("is not a directory this operator can open" in one
                            for one in unresolved), unresolved)

    def test_every_retained_artifact_is_asked_about(self):
        """One failure does not stop the others.

        An operator reading this record is deciding what to do about their
        kept material, and "the first one failed" is less use than knowing
        which.
        """
        good = self.proposal("kept-good")
        bad = self.inaccessible(0o000)
        evidence = {"custody": [
            {"artifact_id": "proposal-1", "content_digest": "sha256:" + "c" * 64,
             "bytes": 12, "custody_locator": f"file://{bad}"},
            {"artifact_id": "proposal-2", "content_digest": "sha256:" + "d" * 64,
             "bytes": 12, "custody_locator": f"file://{good}"},
            {"artifact_id": "proposal-3", "content_digest": "sha256:" + "e" * 64,
             "bytes": 12, "custody_locator": "custody://not-a-scheme"}],
            "unresolved": []}

        dogfood_operator._kept(evidence)

        self.assertEqual(len(evidence["unresolved"]), 2,
                         evidence["unresolved"])
        self.assertTrue(any("'proposal-1'" in one
                            for one in evidence["unresolved"]))
        self.assertTrue(any("custody://not-a-scheme" in one
                            for one in evidence["unresolved"]))

    def test_the_proof_changes_nothing_about_the_material(self):
        """A proof that mutated the candidate would be worse than the gap.

        The modes and the entries are compared before and after, because
        `_kept` runs at the terminal boundary over material a reviewer is
        about to read.
        """
        import os as _os

        root = self.proposal("kept-unchanged")

        def seen():
            found = {}
            for base, directories, files in _os.walk(root):
                for name in directories + files:
                    place = _os.path.join(base, name)
                    held = _os.lstat(place)
                    found[place] = (held.st_mode, held.st_size)
            return found

        before = seen()
        self.assertEqual(self.refuses_the_keep(root), [])
        self.assertEqual(seen(), before)

    def test_a_keep_whose_material_is_there_passes_the_same_proof(self):
        """The positive half, so the cases above are not passing on absence.

        A REAL PROPOSAL, not an empty directory: `candidate/` with a file
        below it and the three siblings beside it, which is what `_derived`
        produced and what a reviewer is handed.
        """
        evidence = {"custody": [{"artifact_id": "proposal-1",
                                 "content_digest": "sha256:" + "c" * 64,
                                 "bytes": 12,
                                 "custody_locator":
                                     f"file://{self.proposal()}"}],
                    "unresolved": []}
        dogfood_operator._kept(evidence)
        self.assertEqual(evidence["unresolved"], [])

    def test_a_retained_regular_file_that_cannot_be_read_is_not_resolved(self):
        """W51473 review [P1], as its own regression.

        THE SECOND ROUND PASSED THIS. It opened and traversed DIRECTORIES and
        only `stat`ed everything else -- so a regular file at mode `000`
        inside a perfectly traversable tree passed a proof whose whole purpose
        is that the documented bytewise diff can read it. `filecmp.cmp` opens
        these files; `stat` does not.

        The reviewer's reproduction, run here rather than described.
        """
        import os as _os

        root = self.proposal("kept-unreadable-file")
        place = _os.path.join(root, "candidate", "v12", "spike", "harness.py")
        self.addCleanup(_os.chmod, place, 0o644)
        _os.chmod(place, 0o000)

        unresolved = self.refuses_the_keep(root)

        self.assertTrue(any("cannot be read" in one
                            and "PermissionError" in one
                            for one in unresolved), unresolved)

    def test_a_retained_proposal_with_no_candidate_is_not_resolved(self):
        """The empty-root gap, which the old positive fixture hid.

        An empty or candidate-less root opens and lists perfectly. The
        verification rerun has no working directory and the diff has nothing
        to compare, so neither half of the documented acceptance can be
        performed -- and reporting it resolved says it can.
        """
        import os as _os

        root = self.proposal("kept-no-candidate")
        import shutil as _shutil
        _shutil.rmtree(_os.path.join(root, "candidate"))

        unresolved = self.refuses_the_keep(root)

        self.assertTrue(any("holds no 'candidate' directory" in one
                            for one in unresolved), unresolved)

    def test_a_wholly_empty_retained_root_is_not_resolved(self):
        """The same gap in its barest form, named separately.

        This is exactly what the previous round's positive fixture was.
        """
        import os as _os

        root = _os.path.join(self.source, "kept-empty")
        _os.makedirs(root, exist_ok=True)

        self.assertTrue(any("holds no 'candidate' directory" in one
                            for one in self.refuses_the_keep(root)))

    def test_an_entry_the_diff_cannot_read_is_refused_by_kind(self):
        """Not a regular file and not a directory is not skipped.

        The independent diff reads regular files and walks directories, and
        the manager's own copier refuses links at any depth -- so one of these
        in custody is a tree this operator should not be calling reviewable.
        """
        import os as _os

        root = self.proposal("kept-odd-entry")
        _os.symlink("/etc/hostname",
                    _os.path.join(root, "candidate", "escape.txt"))

        unresolved = self.refuses_the_keep(root)

        self.assertTrue(any("neither a regular file nor a directory" in one
                            for one in unresolved), unresolved)

    def test_a_retry_may_not_redecide_what_happens_to_the_material(self):
        """The record and the grants are held to the COMMITTED decision.

        A retry granted `retain` over an attempt that committed a discard
        would expect an ending the manager will never produce; one granted a
        discard over a committed keep would call a `retained` ending broken.
        Either way it is two attempts being spliced.
        """
        record, grants = self.paired("retain")
        grants["retention_disposition"] = "discard-after-intake"

        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator._bound(record, grants)

        self.assertIn("committed 'retain'", str(caught.exception))
        self.assertIn("does not redecide", str(caught.exception))

    def test_a_retry_that_agrees_with_the_committed_decision_proceeds(self):
        """The gate is a gate and not a wall."""
        record, grants = self.paired("retain")

        self.assertIs(dogfood_operator._bound(record, grants), record)

    def test_a_retry_cannot_quietly_select_a_different_worker_image(self):
        """W55361: the digest is part of the retry binding, executably.

        The approved correction says the artefact is SELECTED by validated
        digest and that a new grants file is not a selection. `_bound` is the
        place that sentence is enforceable rather than documentary — a retry
        whose grants name another image is two attempts being spliced, exactly
        as a redecided disposition is — and this drives it so the operational
        boundary cannot be contradicted by an edit that leaves the prose alone.
        """
        record, grants = self.paired("retain")
        grants["image_digest"] = "sha256:" + "9" * 64

        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator._bound(record, grants)

        self.assertIn("worker_image_digest", str(caught.exception))
        self.assertIn("resumes ONE attempt", str(caught.exception))

    def paired(self, committed):
        """A record and grants that agree on everything but what a case varies.

        Built together so a case about the DISPOSITION is not passing or
        failing on one of the seven flat binding members instead.
        """
        record = self.trusted(
            work_ref=dict(WORK_REF), participant="baton.claude",
            generation=1, worker_image_digest=IMAGE,
            network="baton-dogfood", attempt_id="attempt-1",
            review_route="rview",
            retention_policy_digest=POLICIES["retention_policy_digest"],
            retention={"disposition": committed,
                       "artifact_ids": ["proposal-1"],
                       "retention_policy_digest": POLICIES[
                           "retention_policy_digest"]})
        grants = {"attempt_id": "attempt-1", "work_ref": dict(WORK_REF),
                  "participant": "baton.claude", "generation": 1,
                  "image_digest": IMAGE, "network": "baton-dogfood",
                  "review_route": "rview",
                  "retention_policy_digest": POLICIES[
                      "retention_policy_digest"],
                  "retention_disposition": committed}
        return record, grants


class ThePublicRetryRunsFromRealDurableState(intake_fixture.IntakeCase):
    """W39358's last acceptance gate: the documented retry, for real.

    EVERY OTHER RETRY CASE MOCKS. This one creates durable state the manager
    actually committed -- a real freeze, a real intake receipt, a real
    retention decision -- against a REAL authority, fails the handoff, and
    then crosses the documented `--retry-handoff` command through the real
    capability builder in a fresh construction.

    ONE AUTHORITY SERVES BOTH HALVES, which is what made this writable. A real
    `Session` carries six of the seven operations `AuthorityPort` names, and
    the seventh -- `publish_answer` -- is exactly the one `DeploymentSession`
    supplies as its own typed refusal and does not require of the session it
    wraps. So the manager's own operations and the pass under test go through
    the same authority, and the assignment the retry passes is the one the
    claim really created.
    """

    def setUp(self):
        super().setUp()
        from baton_v12.authority import Authority, claim_signature
        from baton_v12.worker_manager import AuthorityPort
        from baton_v12.worker_manager.workspaces import (
            configure_workspace_storage)

        self.authority_place = os.path.join(self._root.name, "authority.sqlite3")
        authority = Authority.create(self.authority_place,
                                     authority_uuid=intake_fixture.AUTHORITY,
                                     clock=lambda: intake_fixture.NOW)
        self.addCleanup(authority.dispose)
        authority.create_work(intake_fixture.JOB, "baton.impl",
                              contract="v12-assignment-1",
                              operation_id="create-1")
        authority.add_route_handler("baton.impl", "baton.claude")
        authority.add_route_handler("rview", "baton.claude")
        self.facade = dogfood_operator.DeploymentSession(
            authority.session("baton.claude"))
        self.port = AuthorityPort(self.facade, claim_signature)
        # THE STORE THE SHARED FIXTURE ALREADY CONFIGURED. Reconfiguring is
        # refused for a good reason -- every attempt allocated under the first
        # store would become unfindable -- so this uses the one that is there.
        del configure_workspace_storage
        from baton_v12.worker_manager.workspaces import (
            configured_workspace_storage)
        self.storage_place = configured_workspace_storage(self.store).place
        # THE PROFILE NAME THE OPERATOR PROMISES IN ITS OWN OFFER.
        from baton_v12.worker_manager import certify_profile
        certify_profile(self.store, "runtime", "dogfood",
                        output_fixture.PROFILE)
        # THE ROOTS A REAL ATTEMPT WOULD HAVE. The retry adopts them read-only
        # and allocates nothing, so an attempt that never had them is refused
        # -- correctly, and this fixture has to be an attempt that ran.
        from baton_v12.worker_manager.workspaces import assignment_workspace
        from tests.manager.input_roots import configured_group
        assignment_workspace(configured_group(self.store),
                             self.storage_place, intake_fixture.ATTEMPT)

    def ordinary_capabilities(self, given):
        """The ordinary command's capabilities, with a FAILING pass.

        Real authority, real control store, real manager operations. What is
        supplied is the world outside the manager -- engine, channel, adapter
        -- because this case is about the handoff, not about containers; and
        the pass is made to refuse, which is the failure the retry exists to
        recover.
        """
        from baton_v12.worker_manager import ControlStore

        class Refusing:
            """The deployment's facade, with the one act that fails."""

            def __init__(self, facade):
                self._facade = facade
                self.participant = facade.participant

            def __getattr__(self, name):
                return getattr(self._facade, name)

            def pass_work(self, operands):
                raise ContractRefusal(
                    "refused", "precondition",
                    "the review route is not accepting work just now")

        del given
        return {"session": Refusing(self.facade),
                "bearer": "one-use-bearer",
                "credential_delivery": None,
                "open_store": lambda _place: self.store,
                "adapter_of": lambda **operands: self.Adapter(self),
                "run": lambda argv, **_k: {"status": 0, "stdout": "",
                                           "stderr": ""},
                "open_channel": lambda argv, *, seconds: None}

    class Adapter:
        """Everything the ordinary arc asks of an engine, answered."""

        custodian_image_digest = "sha256:" + "c" * 64

        def __init__(self, case):
            self.case = case
            self.started = []
            self.stops = []

        def start(self, operands):
            self.started.append(dict(operands))
            return {"runtime_id": "runtime-1", "labels": operands["labels"]}

        def list(self, operands):
            if not self.started:
                return []
            return [{"runtime_id": "runtime-1",
                     "labels": self.started[0]["labels"]}]

        def observe(self, runtime_id):
            # QUIESCENT ONCE STOPPED, which is the sequence the arc performs:
            # it orders the stop and then reconciles, and a freeze takes a
            # positively quiescent runtime.
            state = "quiescent" if self.stops else "running"
            return {"runtime_id": runtime_id, "state": state,
                    "why": "observed", "mounts": None}

        def stop(self, request):
            self.stops.append(dict(request))
            return {"runtime_id": request["runtime_id"], "ordered": True,
                    "state": "quiescent", "why": "stopped"}

        def normalize_directory(self, store, *, assignment_id, which):
            from baton_v12.worker_manager import custody

            return custody._answered(
                "normalize", 0,
                {"custody": "normalize", "entries": 0, "not_ours": 0,
                 "running_as": [0, 0]}, None)

        # THE OUTPUT CUSTODY HALF, answered from the fixture's own composers
        # over the arc's OWN attempt row -- so the freeze validates a result
        # that names what this run really recorded rather than what a fixture
        # decided in advance.
        def seal(self, request):
            row = self.case.attempt_row()
            self.case.input_digest = row["input_digest"]
            # THE ARC'S OWN POLICY, not the fixture's: this attempt was
            # recorded under the grants file's identities and a sealed result
            # naming another policy is a result about another attempt.
            return self.case.result(policy_digest=row["policy_digest"])

        def collect(self, operands):
            return self.case.collection()

        def retain(self, command):
            return True

        def destroy_abandoned(self, command):
            return self.destroy(command)

        def destroy(self, command):
            return {"runtime_id": command["runtime_id"], "state": "absent",
                    "why": "the exact runtime is absent",
                    "credentials": {"lifecycle_state": "not-delivered"},
                    "launch": {"lifecycle_state": "not-delivered"}}

    def grants(self, task_path):
        from baton_v12.worker_manager import launch

        launch_home = os.path.join(self._root.name, "launch")
        os.makedirs(launch_home, exist_ok=True)
        # NOT MATERIALIZED HERE. The ordinary command creates the delivery
        # and the retry adopts it, which is the real sequence -- pre-making it
        # would have the fixture standing in for the arc.
        del launch
        given = {one: f"{one}-value"
                 for one in dogfood_operator.GRANT_MEMBERS}
        given.update({
            "engine": "docker", "attempt_id": intake_fixture.ATTEMPT,
            "retention_disposition": "discard-after-intake",
            "offer_id": "offer-1", "task_path": task_path,
            "storage": self.storage_place, "launch_home": launch_home,
            "control_store": self.path,
            "authority_store": self.authority_place,
            "incarnation": "retry-1",
            "credential_home": os.path.join(self._root.name, "credential-home"),
            "credential_slots": [], "credential_profile": {},
            "image_digest": IMAGE, "network": "baton-dogfood",
            "review_route": "rview",
            "work_ref": {"authority_uuid": intake_fixture.AUTHORITY,
                         "work_id": intake_fixture.JOB},
            "participant": "baton.claude", "generation": 1,
            "policies": dict(POLICIES), "record_binding": dict(BINDING),
            "human_contract": dict(HUMAN), "labels": {"a": "b"},
            "runtime_profile_digest": output_fixture.PROFILE,
            "role_instructions_digest": ROLE,
            "toolchain_digest": TOOLCHAIN,
            "assignment_contract": "v12-assignment-1",
            "now": intake_fixture.NOW, "human_contract": dict(HUMAN),
            "source": os.path.join(self._root.name, "source"),
            "adapter_digest": "sha256:" + "3" * 64, "adapter_name": "oci",
            "retention_policy_digest": intake_fixture.RETENTION})
        os.makedirs(given["credential_home"], exist_ok=True)
        os.makedirs(given["source"], exist_ok=True)
        with open(os.path.join(given["source"], "harness.py"), "w",
                  encoding="utf-8") as writing:
            writing.write("print('the staged harness')\n")
        return given

    def test_the_documented_retry_recovers_a_handoff_the_command_failed(self):
        """THE ACCEPTANCE, and the failure is produced rather than composed.

        Review 2026-08-30T17:13:10Z [P0]: the previous cut assembled a record
        that LOOKED like a failed handoff, which cannot prove that the real
        failure path produces a retryable one. So the ordinary public command
        runs first, over the real authority and the real manager, with the
        pass made to refuse -- and what the retry is then given is only what
        that command actually wrote: its own grants file and its own evidence.
        """
        from baton_v12.worker_manager import worker_entry

        task_path = os.path.join(self._root.name, "task.json")
        with open(task_path, "w", encoding="utf-8") as writing:
            json.dump(dict(TASK), writing)
        given = self.grants(task_path)
        grants_path = os.path.join(self._root.name, "grants.json")
        with open(grants_path, "wb") as writing:
            writing.write(json.dumps(given).encode("utf-8"))
        evidence_path = os.path.join(self._root.name, "evidence.json")

        # -- the ordinary command, whose handoff fails ----------------------
        spoken = {"ending": "answered", "why": "clean",
                  "answers": [{"operation": "work",
                               "answer": {"disposition": "completed",
                                          "outputs": [], "recap": "done"}}]}
        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                worker_entry, "converse", return_value=spoken))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "_derived",
                return_value={"changed_paths": [], "verification_status": 0,
                              "verification_argv": ["python3", "harness.py"],
                              "members_present": ["candidate"]}))
            ordinary = dogfood_operator.main(
                ["--grants", grants_path, "--evidence", evidence_path],
                capabilities=self.ordinary_capabilities)

        self.assertEqual(ordinary, 1, "the ordinary command reported success")
        with open(evidence_path, "rb") as reading:
            failed = json.loads(reading.read())
        self.assertIsNone(failed["review_pass"],
                          "the pass this case needs to fail did not")
        self.assertTrue(
            any("declined" in one for one in failed["unresolved"]),
            "the ordinary command wrote no reason for its own failure")
        # AND THE MANAGER FACTS ARE REAL, written by the arc rather than here.
        self.assertIsNotNone(failed["output"]["manifest_digest"])
        self.assertIsNotNone(failed["intake_receipt"]["receipt_digest"])
        self.assertEqual(failed["retention"]["disposition"],
                         "discard-after-intake")

        # -- the retry, from those outputs and nothing else ------------------
        with ExitStack() as patches:
            spoke = patches.enter_context(
                mock.patch.object(worker_entry, "converse"))
            staged = patches.enter_context(
                mock.patch.object(dogfood_operator, "stage_source"))
            derived = patches.enter_context(
                mock.patch.object(dogfood_operator, "_derived"))
            dogfood_operator.main(
                ["--grants", grants_path, "--evidence", evidence_path,
                 "--retry-handoff"],
                capabilities=lambda _g: self.fail("the ordinary builder ran"),
                retry_capabilities=dogfood_operator._for_retry)

        # THE PASS REALLY HAPPENED, asked of the authority rather than of the
        # record this deployment wrote.
        self.assertIsNone(self.facade.assignment_of(intake_fixture.JOB),
                          "the assignment was not ended by the pass")
        self.assertEqual(self.facade.project_work(
            intake_fixture.JOB)["route"], "rview",
            "the Work was not passed to its review route")
        with open(evidence_path, "rb") as reading:
            written = json.loads(reading.read())
        self.assertEqual(written["review_pass"]["route"], "rview")
        self.assertEqual(written["review_pass"]["cause"], "pass")

        # AND NOTHING WORKER-SIDE RAN A SECOND TIME.
        spoke.assert_not_called()
        staged.assert_not_called()
        derived.assert_not_called()


class ThePublicRecoveryEndsAnInterruptedAttempt(
        ThePublicRetryRunsFromRealDurableState):
    """W55758: the documented `--abandon`, over real durable state.

    `work/records/2026/08/finding-interrupted-dogfood-attempt-strands-runtime-
    credential/`.

    THE INCIDENT. A managed turn was torn down while `attempt-w51487-run7` was
    executing. The control arc stopped at `attempt.attach`, so the container,
    the attempt's volatile credential root with a readable bearer in it, and a
    complete-looking workspace proposal nothing had frozen all outlived the
    process that owned them. `evidence.json` is composed in memory and written
    at the END, so the record naming any of them was never written, and
    `--retry-handoff` refuses -- correctly, because there is no trusted result
    to hand on. The manager had its fourth ending and the deployment had no
    way to invoke it.

    THE FIXTURE INHERITS the real-durable-state rig above and changes ONE
    thing: `credential_slots` names a real slot. The reviewer's research says
    in as many words that the existing case cannot catch this integration
    defect because it configures none -- so an attempt with no credential is
    exactly the shape in which the false `not-delivered` is true.
    """

    CANARY = "not-a-real-credential-" + "z" * 24

    def grants(self, task_path):
        given = super().grants(task_path)
        # A REAL SLOT, and the profile that maps it. Non-secret on purpose:
        # what is under test is that the bytes are never opened, and a real
        # secret in a repository would prove that worse rather than better.
        given["credential_slots"] = ["api"]
        given["credential_profile"] = {"api": {"provider": "fixture",
                                               "reference": "kv/dogfood"}}
        return given

    def written_grants(self):
        task_path = os.path.join(self._root.name, "task.json")
        with open(task_path, "w", encoding="utf-8") as writing:
            json.dump(dict(TASK), writing)
        given = self.grants(task_path)
        grants_path = os.path.join(self._root.name, "grants.json")
        with open(grants_path, "wb") as writing:
            writing.write(json.dumps(given).encode("utf-8"))
        return given, grants_path

    def credential_file(self):
        place = os.path.join(self._root.name, "canary")
        with open(place, "w", encoding="utf-8") as writing:
            writing.write(self.CANARY + "\n")
        return place

    def recovery_capabilities(self, given):
        """The real abandonment builder, with the ENGINE supplied.

        Everything about the recovery is the production path -- the stores,
        the session, the proved roots, the credential owner, the typed orphan
        teardown and the adapter -- and only the process that would speak to
        Docker is this fixture's.
        """
        def run(argv, *, seconds=None):
            del seconds
            if "inspect" in argv:
                # POSITIVE ABSENCE IS ENGINE PROSE THAT NAMES THIS IDENTITY.
                # `_absent_prose` refuses a sentence that names another
                # runtime or none at all, so a stub answering a bare "no such
                # object" would be read as `uncertain` -- correctly, and this
                # case is about the ending that follows absence.
                return {"stdout": "", "status": 1,
                        "stderr": "Error response from daemon: No such "
                                  f"container: {argv[-1]}"}
            return {"stdout": "", "stderr": "", "status": 0}

        built = dogfood_operator._for_abandonment(given, run=run)
        if built.get("disagreement"):
            # THE HOLD REFUSED BEFORE ANY CAPABILITY EXISTED, so there is no
            # adapter to decorate -- which is the property under test in the
            # cases that reach here.
            return built
        # THE DIRECTORY CUSTODY ACT IS THE WORLD OUTSIDE THE MANAGER TOO.
        #
        # W55758 review (2026-09-01T05:54:54Z): the real `OciAdapter` runs a
        # helper container for it, and an engine stub that answered the
        # removal and the inspection but not this left the ending correctly
        # refusing on an act it could not account for. Supplying it is the
        # same thing this suite already does for `start`, `list` and
        # `observe`: the manager's own composition is what is under test.
        from baton_v12.worker_manager import custody

        def normalize_directory(store, *, assignment_id, which):
            del store, assignment_id, which
            return custody._answered(
                "normalize", 0,
                {"custody": "normalize", "entries": 0, "not_ours": 0,
                 "running_as": [0, 0]}, None)

        built["adapter"].normalize_directory = normalize_directory
        return built

    def interrupted(self):
        """One attempt interrupted exactly where run7 was: after attach.

        The credential is materialized through the manager's own home and the
        attempt is recorded and attached through the manager's own operations,
        and then nothing else happens -- which is what an interrupted process
        leaves behind.
        """
        from baton_v12.worker_manager import (credentials, launch,
                                              record_attempt,
                                              activate_assignment)
        from baton_v12.worker_manager import attempts as attempts_module
        from tests.manager.input_roots import configured_group

        given, grants_path = self.written_grants()
        home = credentials.CredentialHome(given["credential_home"])
        with open(self.credential_file(), encoding="utf-8") as reading:
            bearer = reading.read().strip()
        delivery = home.materialize(
            credentials.resolved_delivery(
                given["credential_slots"],
                profile=given["credential_profile"]),
            attempt_id=given["attempt_id"],
            workspace_group=configured_group(self.store),
            credential_provider=lambda one, two: bearer)
        home.written_state(given["attempt_id"],
                           delivery.record(runtime_id="runtime-run7"))
        for value in delivery.bearers().values():
            from baton_v12.contracts import forget_secret
            forget_secret(value)
        launch.materialize(given["launch_home"],
                           **dogfood_operator._launch_operands(
                               given["attempt_id"],
                               dogfood_operator.frozen_task(
                                   given["task_path"])))
        del record_attempt, activate_assignment, attempts_module
        return given, grants_path, home

    # -- the documented retry, over a REAL credential -----------------------

    def test_the_documented_retry_adopts_through_the_granted_owner(self):
        """W55758 review (2026-09-01T10:56:54Z) [P1], PLAN item 65.

        THE GAP THIS CLOSES. The exact-owner assertion existed only around a
        direct `_for_retry` call, and the one public-command retry fixture
        configures no credential at all -- so nothing proved that the
        DOCUMENTED command adopts a real delivery through the granted home and
        hands the adapter that same object. `_for_retry` used to read the
        granted home while `OciAdapter` derived its own from the assignment
        workspace, and the two agreed only when the paths happened to
        coincide.

        THE STATE IS THE ORDINARY COMMAND'S OWN: a real freeze, a real intake
        receipt, a real retention decision and this operator's own independent
        verification, produced by running `main` with its pass made to refuse.
        What this fixture supplies is the half the stubbed engine does not --
        `OciAdapter.start` materializes and publishes the lifecycle record
        after the container is created, and there is no container here.

        AND THE OWNER IS COMPARED BY IDENTITY. A freshly constructed
        `CredentialHome` over the same path satisfies a path comparison and is
        a different owner, which is the assertion gap this campaign has now
        corrected at three builders.
        """
        from baton_v12.contracts import forget_secret, live_secret
        from baton_v12.worker_manager import credentials, worker_entry
        from tests.manager.input_roots import configured_group

        task_path = os.path.join(self._root.name, "task.json")
        with open(task_path, "w", encoding="utf-8") as writing:
            json.dump(dict(TASK), writing)
        given = self.grants(task_path)
        self.assertEqual(given["credential_slots"], ["api"],
                         "a retry over no credential cannot prove adoption")
        grants_path = os.path.join(self._root.name, "grants.json")
        with open(grants_path, "wb") as writing:
            writing.write(json.dumps(given).encode("utf-8"))
        evidence_path = os.path.join(self._root.name, "evidence.json")

        # -- the ordinary command, whose handoff fails ----------------------
        spoken = {"ending": "answered", "why": "clean",
                  "answers": [{"operation": "work",
                               "answer": {"disposition": "completed",
                                          "outputs": [], "recap": "done"}}]}
        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                worker_entry, "converse", return_value=spoken))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "_derived",
                return_value={"changed_paths": [], "verification_status": 0,
                              "verification_argv": ["python3", "harness.py"],
                              "members_present": ["candidate"]}))
            ordinary = dogfood_operator.main(
                ["--grants", grants_path, "--evidence", evidence_path],
                capabilities=self.ordinary_capabilities)
        self.assertEqual(ordinary, 1, "the ordinary command reported success")
        with open(evidence_path, "rb") as reading:
            failed = json.loads(reading.read())
        self.assertIsNone(failed["review_pass"],
                          "the pass this case needs to fail did not")
        # THE MANAGER FACTS ARE REAL, written by the arc rather than here.
        self.assertIsNotNone(failed["output"]["manifest_digest"])
        self.assertIsNotNone(failed["intake_receipt"]["receipt_digest"])
        self.assertEqual(failed["retention"]["disposition"],
                         "discard-after-intake")

        # -- the credential a started runtime would have left behind --------
        home = credentials.CredentialHome(given["credential_home"])
        delivery = home.materialize(
            credentials.resolved_delivery(
                given["credential_slots"],
                profile=given["credential_profile"]),
            attempt_id=given["attempt_id"],
            workspace_group=configured_group(self.store),
            credential_provider=lambda _slot, _reference: self.CANARY)
        home.written_state(given["attempt_id"],
                           delivery.record(
                               runtime_id=failed["runtime_id"]))
        # THE OWNING PROCESS'S REGISTRATION DIES WITH IT, as everywhere else
        # in this suite: what the retry must recover is the durable material.
        for value in delivery.bearers().values():
            forget_secret(value)

        # -- the retry, through the documented command ----------------------
        received = []
        constructed = {}
        held_adopt = credentials.CredentialHome.adopt

        def adopt(owner, *arguments, **operands):
            received.append(owner)
            return held_adopt(owner, *arguments, **operands)

        def retry_capabilities(evidence, operands):
            built = dogfood_operator._for_retry(evidence, operands)
            constructed["adapter"] = built["adapter"]
            return built

        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                credentials.CredentialHome, "adopt", adopt))
            patches.enter_context(mock.patch.object(worker_entry, "converse"))
            patches.enter_context(mock.patch.object(dogfood_operator,
                                                    "stage_source"))
            patches.enter_context(mock.patch.object(dogfood_operator,
                                                    "_derived"))
            dogfood_operator.main(
                ["--grants", grants_path, "--evidence", evidence_path,
                 "--retry-handoff"],
                capabilities=lambda _g: self.fail("the ordinary builder ran"),
                retry_capabilities=retry_capabilities)

        adapter = constructed["adapter"]
        self.assertEqual(len(received), 1,
                         "the command adopted no delivery, or adopted twice")
        self.assertIsInstance(adapter.credential_delivery,
                              credentials.Delivery)
        self.assertEqual(adapter.credential_delivery.attempt_id,
                         given["attempt_id"])
        self.assertIs(adapter.credential_home, received[0],
                      "the command adopted through one home and handed the "
                      "adapter another over the same path")
        self.assertIs(adapter._credential_home(), received[0])
        # AND THE PASS REALLY HAPPENED, asked of the authority rather than of
        # the record this deployment wrote.
        self.assertIsNone(self.facade.assignment_of(intake_fixture.JOB),
                          "the assignment was not ended by the pass")
        self.assertEqual(self.facade.project_work(
            intake_fixture.JOB)["route"], "rview")
        # THE ADOPTION RE-REGISTERED THE BEARER, so this case ends it through
        # the same home rather than leaving it live.
        if live_secret(self.CANARY):
            adapter.credential_home.tear_down(adapter.credential_delivery)
        self.assertFalse(live_secret(self.CANARY))

    # -- the refusals, before anything is opened ----------------------------

    def test_the_declaration_is_required_and_is_the_operators_own(self):
        _given, grants_path = self.written_grants()
        out = os.path.join(self._root.name, "recovery.json")
        for reason in (None, "", "   "):
            argv = ["--grants", grants_path, "--evidence", out, "--abandon"]
            if reason is not None:
                argv += ["--abandon-reason", reason]
            with self.subTest(reason=reason):
                with self.assertRaises(dogfood_operator.OperatorRefusal):
                    dogfood_operator.main(
                        argv, capabilities=lambda _g: self.fail("built"),
                        abandon_capabilities=lambda _g: self.fail("built"))
        self.assertFalse(os.path.exists(out))

    def test_a_recovery_asks_for_no_credential(self):
        """A recovery delivers nothing, and asking for a bearer in order to
        delete one would be the exact read this ending exists to avoid."""
        _given, grants_path = self.written_grants()
        out = os.path.join(self._root.name, "recovery.json")
        with self.assertRaises(dogfood_operator.OperatorRefusal):
            dogfood_operator.main(
                ["--grants", grants_path, "--evidence", out, "--abandon",
                 "--abandon-reason", "the supervising turn was torn down",
                 "--credential-file", self.credential_file()],
                capabilities=lambda _g: self.fail("built"),
                abandon_capabilities=lambda _g: self.fail("built"))

    def test_ending_an_attempt_and_finishing_one_are_not_one_command(self):
        _given, grants_path = self.written_grants()
        out = os.path.join(self._root.name, "recovery.json")
        with self.assertRaises(dogfood_operator.OperatorRefusal):
            dogfood_operator.main(
                ["--grants", grants_path, "--evidence", out, "--abandon",
                 "--abandon-reason", "x", "--retry-handoff"],
                capabilities=lambda _g: self.fail("built"),
                retry_capabilities=lambda *_a: self.fail("built"),
                abandon_capabilities=lambda _g: self.fail("built"))

    def test_a_launcher_with_no_abandonment_path_says_so(self):
        _given, grants_path = self.written_grants()
        out = os.path.join(self._root.name, "recovery.json")
        with self.assertRaises(dogfood_operator.OperatorRefusal):
            dogfood_operator.main(
                ["--grants", grants_path, "--evidence", out, "--abandon",
                 "--abandon-reason", "the supervising turn was torn down"],
                capabilities=lambda _g: self.fail("the ordinary builder ran"))

    # -- the pre-attach branch ----------------------------------------------

    def test_an_unrecorded_orphan_refuses_before_any_act(self):
        """The window this fixture reproduces is CLOSED at the launcher now.

        W55758, approver ruling APPROVE-LAZY (M59057): `_launched` no longer
        materializes when it builds capabilities, so the real deployment can no
        longer reach the state this fixture builds by hand -- a bearer beside
        an attempt that was never activated. The case stays because a HAND-MADE
        or legacy one still can, and it pins what `--abandon` does with it: no
        runtime selector can be composed for an unactivated attempt, so the
        answer is a NON-TERMINAL record naming exactly that, and NOTHING is
        removed on an unproved account.

        Removing here would mean treating raw grants as authority to delete,
        which is the boundary the finding draws. The surviving root is
        therefore the RULED outcome for this input, not an outstanding defect;
        the ordering cases above are what prove the deployment cannot produce
        the input any more.

        W55758 (M60437) SHARPENS THE REFUSAL and moves it earlier. The command
        now holds its grants against the assignment the manager FIXED, before
        either branch and before any external act -- and this fixture's
        attempt was never recorded at all, so there is nothing to hold them
        against. The refusal is the hold's rather than the selector's, and it
        lands before anything is even branched on.
        """
        _given, grants_path, home = self.interrupted()
        out = os.path.join(self._root.name, "recovery.json")
        status = dogfood_operator.main(
            ["--grants", grants_path, "--evidence", out, "--abandon",
             "--abandon-reason", "the supervising turn was torn down"],
            capabilities=lambda _g: self.fail("the ordinary builder ran"),
            abandon_capabilities=self.recovery_capabilities)
        self.assertEqual(status, 1, "an unproved ending reported success")
        with open(out, "rb") as reading:
            written = json.loads(reading.read())
        self.assertEqual(written["schema"], dogfood_operator.RECOVERY_SCHEMA)
        self.assertIsNone(written["branch"],
                          "the hold must land before either branch")
        self.assertFalse(written["resolved"])
        self.assertTrue(any("no attempt" in one
                            for one in written["unresolved"]),
                        written["unresolved"])
        # AND NOTHING WAS REMOVED ON THAT ACCOUNT.
        self.assertTrue(os.path.isdir(
            home.volatile_root(intake_fixture.ATTEMPT)))
        # NOR DID ANY BYTE OF THE CANARY REACH THE RECORD.
        self.assertNotIn(self.CANARY, json.dumps(written))


class TheAttachedRecoveryEndsThroughTheRuledAbandonment(unittest.TestCase):
    """W55758: `recover_abandoned`'s attached branch, over a real ending.

    THE MEASURED SHAPE, which is run7's: the runtime attached and nothing
    after it did. The manager's own W44716 ending is what runs -- declaration,
    authority fence, exact force-removal, positive absence, both provider
    endings, cleanup `retained`, lane released -- and this composition adds
    the credential owner that ending was missing, plus the record an operator
    reads afterwards.
    """

    def setUp(self):
        from tests.manager import test_attempts as A

        self.rig = A.ExplicitAbandonmentFencesBeforeItRemoves(
            "test_the_public_ending_fences_then_removes_and_retains")
        self.rig.setUp()
        self.addCleanup(self.rig.doCleanups)
        self.A = A
        self._home = tempfile.TemporaryDirectory(prefix="v12-w55758-")
        self.addCleanup(self._home.cleanup)

    CANARY = "not-a-real-credential-" + "q" * 24

    def credential_home(self, name="granted"):
        from baton_v12.worker_manager import credentials

        place = os.path.join(self._home.name, name)
        os.makedirs(place, exist_ok=True)
        return credentials.CredentialHome(place)

    def materialized(self, home):
        """A real delivery whose owning object is then let go -- the shape an
        interrupted process leaves behind."""
        from baton_v12.contracts import forget_secret
        from baton_v12.worker_manager import credentials
        from tests.manager.input_roots import configured_group

        delivery = home.materialize(
            credentials.resolved_delivery(
                ["api"], profile={"api": {"provider": "fixture",
                                          "reference": "kv/one"}}),
            attempt_id=self.A.ATTEMPT,
            workspace_group=configured_group(self.rig.store),
            credential_provider=lambda one, two: self.CANARY)
        home.written_state(self.A.ATTEMPT,
                           delivery.record(runtime_id="runtime-1"))
        for value in delivery.bearers().values():
            forget_secret(value)
        return home

    def attached(self, orphan=None):
        """A real attached attempt, whose destroy runs the REAL credential
        ending rather than a fixture's opinion of one.

        The rig's custodian answers a fixed `not-delivered`, which is exactly
        the word under test -- so this one delegates to the orphan capability
        the way `OciAdapter._torn_down` does, on the same precondition:
        positive absence first.
        """
        from baton_v12.worker_manager import (activate_assignment,
                                              request_runtime_start)

        class Ending(self.rig.Custodian):

            def destroy_abandoned(self, command):
                answer = super().destroy_abandoned(command)
                if orphan is not None and answer["state"] == "absent":
                    answer["credentials"] = orphan.tear_down()
                return answer

        self.rig.claimed()
        activate_assignment(self.rig.store, self.rig.port,
                            attempt_id=self.A.ATTEMPT,
                            expect=self.rig.expect())
        adapter = Ending([])
        request_runtime_start(self.rig.store, adapter,
                              attempt_id=self.A.ATTEMPT)
        return adapter

    def given(self):
        """Grants that name the assignment THIS MANAGER FIXED.

        W55758 (M60437): the recovery holds its grants against the attempt's
        fixed assignment before any act, so a fixture composing an identity of
        its own would be testing the refusal rather than the ending. The
        identity is read out of the same projection the command reads.
        """
        from baton_v12.worker_manager import attempt_runtime_of

        found = attempt_runtime_of(self.rig.store, self.A.ATTEMPT) or {}
        fixed = found.get("assignment") or {}
        return {"attempt_id": self.A.ATTEMPT,
                "work_ref": dict(fixed.get("work_ref") or {}),
                "participant": fixed.get("participant"),
                "generation": fixed.get("generation"),
                "retention_policy_digest": "sha256:" + "7" * 64,
                "task_path": None, "launch_home": None}

    def recovered(self, adapter, orphan, reason="the supervising turn died"):
        return dogfood_operator.recover_abandoned(
            self.rig.store, self.rig.port, adapter, self.given(),
            reason=reason, orphan=orphan)

    # -- the acceptance ------------------------------------------------------

    def test_the_public_read_is_what_the_branch_turns_on(self):
        """`attempt_runtime_of`, and a branch that does not read prose."""
        from baton_v12.worker_manager import attempt_runtime_of

        self.assertIsNone(attempt_runtime_of(self.rig.store, "attempt-none"))
        self.attached()
        found = attempt_runtime_of(self.rig.store, self.A.ATTEMPT)
        self.assertEqual(found["runtime_id"], "runtime-1")
        self.assertEqual(found["cleanup"], "pending")

    def test_an_attached_attempt_ends_and_its_credential_is_torn_down(self):
        """THE WHOLE POINT: `torn-down`, never `not-delivered`."""
        home = self.materialized(self.credential_home())
        orphan = self.orphan(home)
        adapter = self.attached(orphan)
        record = self.recovered(adapter, orphan)

        self.assertEqual(record["branch"], "abandonment")
        self.assertTrue(record["authority_fence"]["fenced"])
        self.assertEqual(record["cleanup"], "retained")
        self.assertEqual(record["runtime"]["state"], "absent")
        self.assertEqual(record["credentials"]["lifecycle_state"], "torn-down")
        self.assertNotEqual(record["credentials"]["lifecycle_state"],
                            "not-delivered")
        self.assertTrue(record["resolved"], record["unresolved"])
        # THE HOST IS CLEAN, asked of the filesystem rather than of the word.
        self.assertFalse(os.path.lexists(home.volatile_root(self.A.ATTEMPT)))
        self.assertFalse(os.path.exists(home.state_path(self.A.ATTEMPT)))
        # AND NOTHING THE WORKER WROTE WAS PROMOTED.
        row = self.rig.row()
        self.assertEqual(row["output"], "open")
        self.assertEqual(row["worker_disposition"], "none")
        self.assertEqual(row["cleanup"], "retained")

    def orphan(self, *homes):
        from baton_v12.worker_manager import credentials

        return credentials.OrphanTeardown(self.A.ATTEMPT, homes=list(homes))

    def test_an_attempt_that_delivered_nothing_still_says_not_delivered(self):
        """The old word is true exactly when nothing was ever delivered."""
        adapter = self.attached()
        record = self.recovered(adapter, None)
        self.assertEqual(record["credentials"],
                         {"lifecycle_state": "not-delivered"})
        self.assertTrue(record["resolved"], record["unresolved"])

    def test_a_record_written_by_this_recovery_carries_no_bearer(self):
        home = self.materialized(self.credential_home())
        orphan = self.orphan(home)
        adapter = self.attached(orphan)
        record = self.recovered(adapter, orphan)
        place = os.path.join(self._home.name, "recovery.json")
        dogfood_operator.write_recovery(record, place)
        with open(place, encoding="utf-8") as reading:
            body = reading.read()
        self.assertNotIn(self.CANARY, body)
        self.assertIn('"lifecycle_state": "torn-down"', body)

    def test_an_ending_reporting_no_credential_teardown_is_unresolved(self):
        """The gap said out loud rather than papered over: this recovery holds
        credential material and the ending did not settle it."""
        adapter = self.attached()          # no orphan reaches the destroy
        home = self.materialized(self.credential_home())
        record = self.recovered(adapter, self.orphan(home))
        self.assertEqual(record["credentials"]["lifecycle_state"],
                         "unresolved")
        self.assertFalse(record["resolved"])

    def test_the_exported_operation_takes_no_projection_from_a_caller(self):
        """W55758 review (2026-09-01T10:56:54Z) [P1]: the door built to close
        the hole must not be the hole, and a Python class is not a lock.

        The carried observation was first a plain `state` operand and then a
        nominal `_HeldProjection`. Both let a DIRECT caller of the exported
        operation supply a forged projection -- a generation-2 document beside
        generation-2 grants ended the real generation-1 attempt and published
        generation 2 as the identity the ending used -- because the nominal
        type was an ordinary module attribute with a public constructor.

        SO THERE IS NOTHING LEFT TO FORGE. The operand is gone from the
        exported surface, which reads and holds the manager's own row itself.
        """
        import inspect

        self.assertNotIn(
            "state",
            inspect.signature(dogfood_operator.recover_abandoned).parameters,
            "the exported recovery accepts a caller-supplied projection "
            "again, which is the forgery this row exists to refuse")
        self.assertFalse(
            [one for one in vars(dogfood_operator)
             if one.endswith("HeldProjection")],
            "the nominal capability is back, and an importable class with a "
            "public constructor is not one")

        home = self.materialized(self.credential_home())
        orphan = self.orphan(home)
        adapter = self.attached(orphan)
        forged = dict(self.given())
        forged["generation"] = 2
        state = {"attempt_id": self.A.ATTEMPT, "runtime_id": "runtime-1",
                 "execution_runtime": "running", "cleanup": "pending",
                 "assignment": {"work_ref": dict(forged["work_ref"]),
                                "participant": forged["participant"],
                                "generation": 2}}

        with self.assertRaises(TypeError):
            dogfood_operator.recover_abandoned(
                self.rig.store, self.rig.port, adapter, forged,
                reason="a forged projection", orphan=orphan, state=state)

        # AND THE OPERATION'S OWN READ REFUSES THE SAME GRANTS, which is what
        # makes the missing operand a closure rather than a hole moved.
        record = dogfood_operator.recover_abandoned(
            self.rig.store, self.rig.port, adapter, forged,
            reason="a forged projection", orphan=orphan)
        self.assertFalse(record["resolved"])
        self.assertIsNone(record["branch"],
                          "the hold must land before either branch")
        self.assertTrue(any("disagree on" in one
                            for one in record["unresolved"]),
                        record["unresolved"])
        self.assertEqual(record["generation"], 2,
                         "a refusal accounts for the identity that was ASKED "
                         "for, and this ending never ran")

        # NOTHING HAPPENED: no removal, and the material is where it was.
        self.assertEqual(adapter.abandoned, [])
        self.assertTrue(os.path.lexists(home.volatile_root(self.A.ATTEMPT)))
        self.assertEqual(self.rig.row()["cleanup"], "pending")

    def test_a_refused_ending_is_recorded_rather_than_raised(self):
        """An attempt whose worker answered cannot be abandoned, and the
        recovery says so instead of failing the command."""
        from baton_v12.worker_manager import observe

        adapter = self.attached()
        observe(self.rig.store, attempt_id=self.A.ATTEMPT,
                axis="worker_disposition", value="completed")
        record = self.recovered(adapter, None)
        self.assertFalse(record["resolved"])
        self.assertTrue(any("declined to abandon" in one
                            for one in record["unresolved"]))


class ARecoveryThatBeganAlwaysLeavesAnAccount(unittest.TestCase):
    """W55758 review (2026-09-01T04:57:06Z) [P1]: the record survives a fault.

    THE MEASURED DEFECT. `_abandoned` wrote the recovery document only after
    `recover_abandoned` returned, and the pre-attach path performs real
    external acts -- a teardown per credential home, then the launch root --
    without turning a later failure into the record's own account. A real
    multi-home ending can remove the FIRST home and then refuse on the second,
    after an external mutation and before anything durable has been written.

    `main`'s ordinary branch already holds the opposite rule in as many words:
    a post-start fault still leaves a file. One rule is right for both.
    """

    def setUp(self):
        self._home = tempfile.TemporaryDirectory(prefix="v12-w55758-fault-")
        self.addCleanup(self._home.cleanup)
        self.place = os.path.join(self._home.name, "recovery.json")

    def given(self):
        return {"attempt_id": "attempt-1",
                "work_ref": {"authority_uuid": "a" * 32, "work_id": "w-1"},
                "participant": "baton.claude", "generation": 1,
                "retention_policy_digest": "sha256:" + "5" * 64}

    def session(self):
        """Enough of a session for `AuthorityPort` to accept it: this case is
        about what happens AFTER the port exists."""
        from baton_v12.worker_manager.authority_port import SESSION_OPERATIONS

        made = mock.Mock(participant="baton.claude")
        for member in SESSION_OPERATIONS:
            setattr(made, member, lambda *a, **k: None)
        return made

    def capabilities(self, closing=()):
        def build(_given):
            # `state` IS PART OF THE BUILDER'S CONTRACT, because M60437's
            # hold is the builder's own act; this stand-in takes the place of
            # a builder that took one, and `_recovering` is patched out below.
            return {"store": object(), "session": self.session(),
                    "adapter": object(), "orphan": None, "state": None,
                    "launch_home": None, "closing": closing}

        return build

    def test_an_unexpected_fault_still_writes_a_bounded_record(self):
        released = []
        faulted = RuntimeError("the second home would not release")

        def recovering(_record, *_a, **_k):
            raise faulted

        with mock.patch.object(dogfood_operator, "_recovering", recovering):
            with self.assertRaises(RuntimeError):
                dogfood_operator._abandoned(
                    self.given(), "the supervising turn died",
                    self.capabilities((lambda: released.append(1),)),
                    self.place)
        self.assertEqual(released, [1], "the capabilities were not closed")
        self.assertTrue(os.path.exists(self.place),
                        "a recovery that began left no durable account")
        with open(self.place, encoding="utf-8") as reading:
            written = json.load(reading)
        self.assertEqual(sorted(written),
                         sorted(dogfood_operator.RECOVERY_MEMBERS))
        self.assertFalse(written["resolved"])
        self.assertTrue(any("faulted after it began" in one
                            for one in written["unresolved"]))
        # ONLY THE TYPE, never the message: a fault's text is untrusted prose
        # and this is the most durable surface this command has.
        body = json.dumps(written)
        self.assertIn("RuntimeError", body)
        self.assertNotIn("would not release", body)

    def test_a_cleanup_refusal_becomes_a_named_unresolved_fact(self):
        """An EXPECTED cleanup refusal is an account, not a fault: the record
        is composed, writable, and says which ending did not settle."""
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import credentials

        record = {one: None for one in dogfood_operator.RECOVERY_MEMBERS}
        record.update({"schema": dogfood_operator.RECOVERY_SCHEMA,
                       "attempt_id": "attempt-1", "resolved": False,
                       "unresolved": []})

        class Refusing:
            attempt_id = "attempt-1"

            def tear_down(self):
                raise ContractRefusal(
                    "policy", "credential-lifetime",
                    "a credential root is still present after teardown "
                    "removed it")

            def evidence(self):
                return [{"home": "/state", "volatile_root": True,
                         "lifecycle_record": False}]

        class Adapter:
            def recover_credentials(self, _request):
                return {"lifecycle_state": "absent", "orphans": {}}

        del credentials
        with mock.patch.object(dogfood_operator, "_launch_after",
                               return_value={"lifecycle_state": "torn-down"}), \
                mock.patch("baton_v12.worker_manager.label_context",
                           return_value={"principal": "principal:p",
                                         "effective_scope": "scope:s"}):
            answered = dogfood_operator._pre_attach_recovered(
                record, object(), Adapter(), self.given(),
                orphan=Refusing(), launch_home=None)
        self.assertEqual(answered["credentials"]["lifecycle_state"],
                         "unresolved")
        self.assertFalse(answered["resolved"])
        self.assertTrue(any("credential teardown did not settle" in one
                            for one in answered["unresolved"]))
        # AND THE MATERIAL IT COULD NOT REMOVE IS NAMED.
        self.assertTrue(any("still present under /state" in one
                            for one in answered["unresolved"]))
        # THE RECORD IS STILL WRITABLE, which is the whole point.
        dogfood_operator.write_recovery(answered, self.place)
        self.assertTrue(os.path.exists(self.place))


class TheCredentialIsMaterializedAfterActivationAndNotBefore(
        ThePublicRecoveryEndsAnInterruptedAttempt):
    """W55758, approver ruling APPROVE-LAZY (M59057): the window is CLOSED.

    THE DEFECT IT REPLACES. `_launched` wrote the bearer to disk while it was
    building capabilities -- before `run_dogfood_task` had recorded, claimed
    or activated anything -- so a process that died in that window left a
    readable credential with no attempt row, no activated assignment, and
    therefore no `label_context` from which a recovery could compose a runtime
    selector. `--abandon` could prove nothing and clean nothing.

    THE ORDER IS THE CORRECTION and the arc already had it: `adapter_of` runs
    after `record_attempt`, the claim and `activate_assignment`, and before
    `request_runtime_start`. A crash before activation now leaves no bearer at
    all; a crash after it leaves one the manager can name.
    """

    def test_nothing_is_on_the_host_until_the_factory_is_called(self):
        given, _grants_path = self.written_grants()
        built = dogfood_operator._launched(
            given, credential_provider=lambda _p, _r: self.CANARY)
        for release in built["closing"]:
            release()
        from baton_v12.worker_manager import credentials

        home = credentials.CredentialHome(given["credential_home"])
        self.assertIsNone(built["credential_delivery"])
        self.assertFalse(os.path.lexists(
            home.volatile_root(given["attempt_id"])))
        self.assertFalse(os.path.exists(home.state_path(given["attempt_id"])))

    def test_the_factory_materializes_exactly_once_through_the_owned_home(
            self):
        """And the adapter receives THAT delivery and the SAME granted home --
        one owner from the first act of the attempt."""
        from baton_v12.worker_manager import credentials, launch
        from baton_v12.worker_manager.workspaces import (
            adopted_assignment_workspace)

        given, _grants_path = self.written_grants()
        built = dogfood_operator._launched(
            given, credential_provider=lambda _p, _r: self.CANARY)
        self.addCleanup(lambda: [release() for release in built["closing"]])
        home = credentials.CredentialHome(given["credential_home"])
        roots = adopted_assignment_workspace(given["storage"],
                                             given["attempt_id"])
        made = launch.materialize(
            given["launch_home"],
            **dogfood_operator._launch_operands(
                given["attempt_id"],
                dogfood_operator.frozen_task(given["task_path"])))
        adapter = built["adapter_of"](
            engine=given["engine"], run=lambda *a, **k: None,
            image_digest=given["image_digest"], network=given["network"],
            labels={}, roots=roots, declared=[], launch=made,
            credential_delivery=None, input_manifest_digest=None)
        self.addCleanup(home.tear_down, adapter.credential_delivery)
        self.assertIsInstance(adapter.credential_delivery,
                              credentials.Delivery)
        self.assertEqual(adapter.credential_delivery.attempt_id,
                         given["attempt_id"])
        self.assertEqual(adapter.credential_home.place,
                         given["credential_home"])
        self.assertIs(adapter._credential_home(), adapter.credential_home)
        # EXACTLY ONCE. A second factory call for the same attempt would
        # refuse against its own root, and answering the first one again would
        # hide the caller that asked twice.
        with self.assertRaises(dogfood_operator.OperatorRefusal):
            built["adapter_of"](
                engine=given["engine"], run=lambda *a, **k: None,
                image_digest=given["image_digest"],
                network=given["network"], labels={}, roots=roots,
                declared=[], launch=made, credential_delivery=None,
                input_manifest_digest=None)


class TheArcMaterializesBetweenActivationAndRuntimeCreation(
        ThePublicRecoveryEndsAnInterruptedAttempt):
    """W55758 review (2026-09-01T05:40:30Z) [P1]: the ORDER, proved by the ARC.

    THE GAP THIS CLOSES. The launcher cases drive `_launched` and then call
    `adapter_of` themselves, so they prove the factory's own behaviour and
    nothing about WHEN the arc calls it. A change moving that call before
    `activate_assignment` would reopen the exact bearer-without-selector window
    M59057 was issued to close, and every one of those cases would still pass.

    SO THE MARKS ARE TAKEN FROM THE REAL OPERATIONS. `run_dogfood_task`
    imports them from the package inside its own body, so wrapping the package
    attributes observes the arc rather than a copy of it.

    AND THE HOME IS COMPARED BY IDENTITY, not by path. A freshly constructed
    `CredentialHome` over the same string satisfies a path comparison and is a
    different owner; what M59057 approved is that the adapter receives the
    exact object whose `materialize` produced the delivery.
    """

    def test_the_factory_runs_after_activation_and_before_runtime_start(self):
        from baton_v12.contracts import ContractRefusal, live_secret
        from baton_v12.worker_manager import credentials
        from baton_v12 import worker_manager

        _given, grants_path = self.written_grants()
        evidence_path = os.path.join(self._root.name, "arc-evidence.json")
        order = []
        received = []
        built = []
        held_materialize = credentials.CredentialHome.materialize

        def materialize(home, *arguments, **operands):
            order.append("materialize")
            received.append(home)
            return held_materialize(home, *arguments, **operands)

        held_activate = worker_manager.activate_assignment
        held_start = worker_manager.request_runtime_start

        def activate(*arguments, **operands):
            order.append("activate")
            return held_activate(*arguments, **operands)

        def start(*arguments, **operands):
            order.append("start")
            # THE ENGINE IS NEVER REACHED. What is under test is the ORDER of
            # the two edges around materialization, and a real runtime start
            # would need a daemon this case has no business requiring.
            raise ContractRefusal("unavailable", "transport",
                                  "this case stops before the engine")

        def capabilities(given):
            bundle = dogfood_operator._launched(
                given, credential_provider=lambda _p, _r: self.CANARY)
            factory = bundle["adapter_of"]

            def watched(**operands):
                made = factory(**operands)
                built.append(made)
                return made

            bundle["adapter_of"] = watched
            return bundle

        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                credentials.CredentialHome, "materialize", materialize))
            patches.enter_context(mock.patch.object(
                worker_manager, "activate_assignment", activate))
            patches.enter_context(mock.patch.object(
                worker_manager, "request_runtime_start", start))
            with self.assertRaises(ContractRefusal):
                dogfood_operator.main(
                    ["--grants", grants_path, "--evidence", evidence_path,
                     "--credential-file", self.credential_file()],
                    capabilities=capabilities)

        # THE DELIVERY THIS CASE REALLY MADE IS REALLY ENDED, and through its
        # OWNING HOME rather than by deleting a directory.
        #
        # W55758 review (2026-09-01T05:46:47Z) [P1]: `materialize` is the real
        # one here, so it registered the canary live -- and
        # `TemporaryDirectory.cleanup` removes a tree without calling any
        # ending, so the registration outlived the case and armed every later
        # module's leak walk against a string this one invented. The component
        # owns root absence and registry release TOGETHER, which is why this
        # is a teardown and not a `forget_secret`.
        if built:
            built[0].credential_home.tear_down(built[0].credential_delivery)
            self.assertFalse(live_secret(self.CANARY),
                             "this case left a credential registered live")
        # THE TWO EDGES, in the one order that closes the window.
        self.assertEqual(order, ["activate", "materialize", "start"],
                         "the credential was materialized outside the window "
                         "assignment activation and runtime creation define")
        # AND THE ADAPTER OWNS THE EXACT HOME THAT MADE THE DELIVERY.
        self.assertEqual(len(received), 1, "the delivery was made more than "
                                           "once, or not through the arc")
        self.assertEqual(len(built), 1)
        self.assertIs(built[0].credential_home, received[0],
                      "the adapter was handed a different home object over "
                      "the same path")
        self.assertIs(built[0]._credential_home(), received[0])
        # AND THE BEARER IS NOWHERE IN WHAT THE COMMAND WROTE.
        if os.path.exists(evidence_path):
            with open(evidence_path, encoding="utf-8") as reading:
                self.assertNotIn(self.CANARY, reading.read())


class TheRecoveryIsRetryableAndRefusesAConflictingDeclaration(
        TheAttachedRecoveryEndsThroughTheRuledAbandonment):
    """W55758 matrix: exact retry, a conflicting declaration, and an
    uncertain runtime, through the recovery composition.

    THESE ARE COMPOSITION CASES ON PURPOSE. `abandon_attempt` owns replay,
    declaration collision and the uncertain-runtime refusal, and its own suite
    proves each; what is untested until here is what the RECOVERY COMMAND
    makes of them -- which is where this Work has already found a false
    credential ending, a cross-attempt deletion and a lost partial record.
    """

    def test_an_exact_retry_replays_without_a_second_external_act(self):
        home = self.materialized(self.credential_home())
        orphan = self.orphan(home)
        adapter = self.attached(orphan)
        first = self.recovered(adapter, orphan)
        self.assertTrue(first["resolved"], first["unresolved"])
        removals = len(adapter.abandoned)

        second = self.recovered(adapter, orphan)

        self.assertEqual(second["cleanup"], "retained")
        self.assertEqual(second["runtime"]["state"], "absent")
        self.assertEqual(len(adapter.abandoned), removals,
                         "an exact retry performed the removal again")
        # THE CREDENTIAL ENDING IS NOT RE-CLAIMED EITHER. The first call tore
        # it down; the replayed composite carries no new teardown, so the
        # record says `unresolved` rather than asserting a second ending.
        self.assertIn(second["credentials"]["lifecycle_state"],
                      ("torn-down", "unresolved"))
        self.assertFalse(os.path.lexists(home.volatile_root(self.A.ATTEMPT)))

    def test_a_conflicting_declaration_is_recorded_not_forced(self):
        """Calling the command IS the declaration, so a second one naming a
        different reason is a different declaration for one attempt."""
        home = self.materialized(self.credential_home())
        orphan = self.orphan(home)
        adapter = self.attached(orphan)
        self.recovered(adapter, orphan, reason="the supervising turn died")

        conflicting = self.recovered(adapter, orphan,
                                     reason="a completely different account")

        self.assertFalse(conflicting["resolved"])
        self.assertTrue(any("declined to abandon" in one
                            for one in conflicting["unresolved"]),
                        conflicting["unresolved"])

    def test_an_uncertain_runtime_settles_nothing_and_keeps_the_bearer(self):
        """`unresolved` is an answer, and it is the one that matters most: a
        container this manager cannot say is gone may still be reading the
        mount, so the credential stays exactly where it is."""
        home = self.materialized(self.credential_home())
        orphan = self.orphan(home)

        class Uncertain(self.rig.Custodian):
            def destroy_abandoned(self, command):
                answer = super().destroy_abandoned(command)
                answer["state"] = "uncertain"
                answer["why"] = "the engine did not answer about it"
                return answer

        from baton_v12.worker_manager import (activate_assignment,
                                              request_runtime_start)
        self.rig.claimed()
        activate_assignment(self.rig.store, self.rig.port,
                            attempt_id=self.A.ATTEMPT,
                            expect=self.rig.expect())
        adapter = Uncertain([])
        request_runtime_start(self.rig.store, adapter,
                              attempt_id=self.A.ATTEMPT)

        record = self.recovered(adapter, orphan)

        self.assertFalse(record["resolved"])
        self.assertNotEqual(record["cleanup"], "retained")
        # THE MATERIAL IS UNTOUCHED, which is the whole point of the refusal.
        self.assertTrue(os.path.lexists(home.volatile_root(self.A.ATTEMPT)))
        self.assertTrue(os.path.exists(home.state_path(self.A.ATTEMPT)))
        self.assertNotEqual(record["credentials"]["lifecycle_state"],
                            "torn-down")


class TheDocumentedRecoveryEndsRealAttachedState(
        ThePublicRecoveryEndsAnInterruptedAttempt):
    """W55758 plan item 7: ONE reusable fixture for durable ATTACHED state.

    THE MISSING PIECE THE LAST TWO ROUNDS NAMED. Every remaining matrix row is
    about the documented command over an attempt that really attached, and
    every earlier attempt to cover them borrowed the `test_attempts` rig --
    which proves the manager's own composition and says nothing about the
    OPERATOR's grants, stores and command wrapper. This builds that state the
    only honest way: by running the ordinary command's own arc and cutting it
    off exactly where an interrupted process is cut off.

    WHAT IS REAL HERE. The authority, the control store, the offer, the claim,
    the activation, the launch delivery, the credential materialized through
    the granted `CredentialHome` in the arc's own order, and the attach. What
    is the fixture's is the world outside the manager: the engine and the
    channel.

    WHAT IS CUT. `_ended_however` never runs -- that is the ending the killed
    process never reached, and neutering it is the interruption rather than a
    convenience.
    """

    def interrupted_attached(self, publish=True, activate=True):
        """Run the ordinary command and stop it where run7 stopped.

        `publish=False` is the other interruption the matrix names: the
        runtime was created and the lifecycle record was not yet written.
        """
        from baton_v12.contracts import forget_secret, live_secret
        from baton_v12.worker_manager import worker_entry

        given, grants_path = self.written_grants()
        evidence_path = os.path.join(self._root.name, "interrupted.json")
        stub = self.Adapter(self)
        deliveries = []

        def capabilities(operands):
            built = dogfood_operator._launched(
                operands, credential_provider=lambda _p, _r: self.CANARY)
            factory = built["adapter_of"]

            def adapter_of(**inner):
                # THE CREDENTIAL IS REALLY MATERIALIZED, through the granted
                # home and in the arc's own order; only the ENGINE is the
                # fixture's, so what lands on disk is what a real attempt
                # leaves behind.
                made = factory(**inner)
                deliveries.append(made.credential_delivery)
                # THE HALF THE STUBBED ENGINE DOES NOT DO. `OciAdapter.start`
                # publishes the lifecycle record after the container is
                # created, and this fixture's adapter is not that one -- so
                # the record is published here, through the SAME granted home
                # the delivery was made under, rather than left absent and
                # quietly changing the shape under test.
                if publish:
                    made.credential_home.written_state(
                        made.credential_delivery.attempt_id,
                        made.credential_delivery.record(
                            runtime_id="runtime-1"))
                return stub

            built["adapter_of"] = adapter_of
            built["session"] = self.facade
            built["open_store"] = lambda _place: self.store
            built["open_channel"] = lambda argv, *, seconds: None
            return built

        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                worker_entry, "converse",
                side_effect=RuntimeError(
                    "the supervising turn was torn down")))
            if not activate:
                # RECORDED AND NEVER ACTIVATED: the attempt exists and no
                # assignment was ever fixed for it.
                from baton_v12 import worker_manager

                patches.enter_context(mock.patch.object(
                    worker_manager, "activate_assignment",
                    side_effect=ContractRefusal(
                        "unavailable", "authority",
                        "the authority went away before activation")))
            # THE ENDING THE KILLED PROCESS NEVER REACHED.
            patches.enter_context(mock.patch.object(
                dogfood_operator, "_ended_however", lambda *a, **k: None))
            try:
                dogfood_operator.main(
                    ["--grants", grants_path, "--evidence", evidence_path,
                     "--credential-file", self.credential_file()],
                    capabilities=capabilities)
            except BaseException:                          # noqa: BLE001
                pass
        # THE OWNING PROCESS'S REGISTRATIONS DIE WITH IT, and this is the one
        # thing this fixture has to model rather than perform.
        #
        # W55758 review (2026-09-01T05:54:54Z) [P1]: the delivery is REAL, so
        # `materialize` registered its bearer live -- and the process that
        # owned it is exactly what this fixture is pretending died. Keeping
        # the registration would arm every later module's leak walk against a
        # string this case invented, which is contamination rather than
        # fidelity.
        #
        # THE ROOT STAYS. Releasing the in-memory registration is modelling
        # the process boundary; removing the files would model a cleanup that
        # never happened and would delete the very thing recovery recovers.
        for made in deliveries:
            for value in made.bearers().values():
                forget_secret(value)
        self.assertFalse(live_secret(self.CANARY),
                         "the interrupted process's registration outlived it")
        return given, grants_path, deliveries

    def interrupted_before_attach(self):
        """The OTHER interruption the matrix names, cut one step earlier.

        The attempt is recorded, claimed and activated and its credential is
        materialized through the granted home in the arc's own order -- and
        the manager never records a runtime, which is the state
        `attempt_runtime_of` answers with a null `runtime_id` and the state
        the pre-attach branch exists for. The lifecycle record the fixture's
        `adapter_of` publishes is the half a real `OciAdapter.start` performs
        after the engine has created something, so what is left behind is
        exactly a bearer whose runtime this manager cannot name.
        """
        from baton_v12 import worker_manager

        with mock.patch.object(
                worker_manager, "request_runtime_start",
                side_effect=ContractRefusal(
                    "refused", "precondition",
                    "the supervising turn was torn down before the runtime "
                    "was requested")):
            given, grants_path, made = self.interrupted_attached()
        found = self.state(given)
        self.assertIsNotNone(found, "no attempt was recorded at all")
        self.assertIsNone(found["runtime_id"],
                          "a runtime attached, so this is not the pre-attach "
                          "branch and this fixture proves nothing")
        return given, grants_path, made

    def state(self, given):
        from baton_v12.worker_manager import attempt_runtime_of

        return attempt_runtime_of(self.store, given["attempt_id"])

    def home(self, given):
        from baton_v12.worker_manager import credentials

        return credentials.CredentialHome(given["credential_home"])

    def test_the_fixture_really_leaves_an_attached_interrupted_attempt(self):
        """The premise, proved before anything is built on it."""
        given, _grants, deliveries = self.interrupted_attached()
        found = self.state(given)
        self.assertIsNotNone(found, "no attempt was recorded at all")
        self.assertIsNotNone(found["runtime_id"], "no runtime attached")
        self.assertEqual(found["cleanup"], "pending",
                         "the arc's own ending ran after all")
        self.assertEqual(len(deliveries), 1)
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])),
            "the interrupted attempt left no bearer, so there is nothing to "
            "recover and this fixture proves nothing")
        self.assertTrue(os.path.exists(home.state_path(given["attempt_id"])))

    # -- the documented command over durable attached state -----------------

    def test_the_documented_command_ends_real_attached_state(self):
        """PLAN ITEM 7's centre: `main --abandon`, end to end, over an attempt
        that really attached through the operator's own grants and stores."""
        given, grants_path, _made = self.interrupted_attached()
        out = os.path.join(self._root.name, "recovery.json")

        status = dogfood_operator.main(
            ["--grants", grants_path, "--evidence", out, "--abandon",
             "--abandon-reason", "the supervising turn was torn down"],
            capabilities=lambda _g: self.fail("the ordinary builder ran"),
            abandon_capabilities=self.recovery_capabilities)

        with open(out, encoding="utf-8") as reading:
            written = json.load(reading)
        self.assertEqual(status, 0, written["unresolved"])
        self.assertEqual(written["branch"], "abandonment")
        self.assertTrue(written["authority_fence"]["fenced"])
        self.assertEqual(written["cleanup"], "retained")
        self.assertEqual(written["runtime"]["state"], "absent")
        self.assertEqual(written["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertTrue(written["resolved"])
        # THE HOST IS CLEAN, asked of the filesystem rather than of the word.
        home = self.home(given)
        self.assertFalse(os.path.lexists(
            home.volatile_root(given["attempt_id"])))
        self.assertFalse(os.path.exists(home.state_path(given["attempt_id"])))
        # NOT ONE BYTE OF THE CANARY, and no registration left behind.
        self.assertNotIn(self.CANARY, json.dumps(written))
        self.assertFalse(live_secret(self.CANARY))
        # AND THE WORKER'S OUTPUT IS NOT PROMOTED: the ending is `retained`,
        # which is the frozen axis's word for material kept on purpose.
        found = self.state(given)
        self.assertEqual(found["cleanup"], "retained")

    def test_an_exact_retry_of_the_command_replays_the_same_ending(self):
        _given, grants_path, _made = self.interrupted_attached()
        out = os.path.join(self._root.name, "recovery.json")
        argv = ["--grants", grants_path, "--evidence", out, "--abandon",
                "--abandon-reason", "the supervising turn was torn down"]
        self.assertEqual(dogfood_operator.main(
            argv, capabilities=lambda _g: self.fail("built"),
            abandon_capabilities=self.recovery_capabilities), 0)

        self.assertEqual(dogfood_operator.main(
            argv, capabilities=lambda _g: self.fail("built"),
            abandon_capabilities=self.recovery_capabilities), 0)

        with open(out, encoding="utf-8") as reading:
            written = json.load(reading)
        self.assertEqual(written["cleanup"], "retained")
        self.assertEqual(written["runtime"]["state"], "absent")

    def test_a_conflicting_declaration_through_the_command_is_refused(self):
        """Calling the command IS the declaration, so a second one naming a
        different reason is a different declaration for one attempt."""
        _given, grants_path, _made = self.interrupted_attached()
        out = os.path.join(self._root.name, "recovery.json")
        dogfood_operator.main(
            ["--grants", grants_path, "--evidence", out, "--abandon",
             "--abandon-reason", "the supervising turn was torn down"],
            capabilities=lambda _g: self.fail("built"),
            abandon_capabilities=self.recovery_capabilities)

        status = dogfood_operator.main(
            ["--grants", grants_path, "--evidence", out, "--abandon",
             "--abandon-reason", "a completely different account"],
            capabilities=lambda _g: self.fail("built"),
            abandon_capabilities=self.recovery_capabilities)

        self.assertEqual(status, 1)
        with open(out, encoding="utf-8") as reading:
            written = json.load(reading)
        self.assertFalse(written["resolved"])
        self.assertTrue(any("declined to abandon" in one
                            for one in written["unresolved"]),
                        written["unresolved"])

    def test_a_terminal_refusal_still_reports_what_already_happened(self):
        """W55758 review (2026-09-01T05:54:54Z) [P1]: the PARTIAL ACCOUNT.

        `abandon_attempt` refuses at its terminal settlement long after it has
        declared, fenced the authority, removed the runtime and proved it
        absent. The record used to keep only the credential fact, so an
        operator could not tell whether the container was gone, whether the
        fence landed, or which step refused.

        The custody act is made to refuse HERE, which is the shape that
        produces the partial ending in the first place.
        """
        given, grants_path, _made = self.interrupted_attached()
        out = os.path.join(self._root.name, "recovery.json")

        def refusing(operands):
            built = self.recovery_capabilities(operands)

            def normalize_directory(store, *, assignment_id, which):
                del store, assignment_id, which
                raise ContractRefusal(
                    "runtime-observation", "quiescence-unknown",
                    "the custody helper did not answer")

            built["adapter"].normalize_directory = normalize_directory
            return built

        status = dogfood_operator.main(
            ["--grants", grants_path, "--evidence", out, "--abandon",
             "--abandon-reason", "the supervising turn was torn down"],
            capabilities=lambda _g: self.fail("built"),
            abandon_capabilities=refusing)

        self.assertEqual(status, 1)
        with open(out, encoding="utf-8") as reading:
            written = json.load(reading)
        self.assertFalse(written["resolved"])
        # EVERY MEMBER THAT BECAME KNOWN BEFORE THE REFUSAL.
        self.assertTrue(written["authority_fence"]["fenced"],
                        "the record cannot say whether the fence landed")
        self.assertEqual(written["runtime"]["state"], "absent",
                         "the record cannot say whether the runtime is gone")
        self.assertIsNotNone(written["observed_after"])
        self.assertEqual(written["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertIsNotNone(written["attempt_state"])
        # AND THE ACT THAT DID NOT HAPPEN STAYS UNSET.
        self.assertIsNone(written["custody"])
        self.assertNotEqual(written["cleanup"], "retained")
        self.assertNotIn(self.CANARY, json.dumps(written))
        # THE HOST IS CLEAN EVEN SO, because the credential teardown follows
        # positive runtime absence and precedes the terminal settlement.
        home = self.home(given)
        self.assertFalse(os.path.lexists(
            home.volatile_root(given["attempt_id"])))

    def test_an_engine_that_cannot_be_asked_settles_nothing(self):
        """`unresolved` is an answer. A runtime this manager cannot say is
        gone may still be reading the mount, so nothing is removed."""
        given, grants_path, _made = self.interrupted_attached()
        out = os.path.join(self._root.name, "recovery.json")

        def unreachable(operands):
            def run(argv, *, seconds=None):
                del seconds
                if "inspect" in argv:
                    return {"stdout": "", "status": 1,
                            "stderr": "Cannot connect to the daemon"}
                return {"stdout": "", "stderr": "", "status": 0}

            return dogfood_operator._for_abandonment(operands, run=run)

        status = dogfood_operator.main(
            ["--grants", grants_path, "--evidence", out, "--abandon",
             "--abandon-reason", "the supervising turn was torn down"],
            capabilities=lambda _g: self.fail("built"),
            abandon_capabilities=unreachable)

        self.assertEqual(status, 1)
        with open(out, encoding="utf-8") as reading:
            written = json.load(reading)
        self.assertFalse(written["resolved"])
        self.assertNotEqual(written["cleanup"], "retained")
        self.assertNotEqual(written["credentials"]["lifecycle_state"],
                            "torn-down")
        # THE BEARER IS EXACTLY WHERE THE INTERRUPTED ATTEMPT LEFT IT.
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))
        self.assertTrue(os.path.exists(home.state_path(given["attempt_id"])))

    def test_a_runtime_created_before_its_record_is_still_ended(self):
        """The matrix row between runtime creation and lifecycle publication.

        `OciAdapter.start` publishes the record AFTER the container exists, so
        a process killed in between leaves a bearer with no record at all.
        The teardown computes both locations from the home rather than from
        the record, so it ends exactly that: the root goes, and the absent
        record is proved absent rather than looked for.
        """
        given, grants_path, _made = self.interrupted_attached(publish=False)
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))
        self.assertFalse(os.path.exists(home.state_path(given["attempt_id"])),
                         "this row needs a root with no record")
        out = os.path.join(self._root.name, "recovery.json")

        status = dogfood_operator.main(
            ["--grants", grants_path, "--evidence", out, "--abandon",
             "--abandon-reason", "the supervising turn was torn down"],
            capabilities=lambda _g: self.fail("built"),
            abandon_capabilities=self.recovery_capabilities)

        with open(out, encoding="utf-8") as reading:
            written = json.load(reading)
        self.assertEqual(status, 0, written["unresolved"])
        self.assertEqual(written["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertFalse(os.path.lexists(
            home.volatile_root(given["attempt_id"])))
        self.assertFalse(live_secret(self.CANARY))


class TheRecoveryMatrixOverDurableAttachedState(
        TheDocumentedRecoveryEndsRealAttachedState):
    """W55758 plan item 7's remaining rows, through the one fixture.

    EVERY CASE HERE IS A COMPOSITION CASE. `abandon_attempt` owns replay, the
    fence, the removal order and the terminal settlement, and its own suite
    proves each; what these ask is what the DOCUMENTED COMMAND makes of them
    over state the operator's own arc really produced.
    """

    def attempt_labels(self, given):
        """The whole frozen label set that selects THIS attempt's runtimes.

        Composed exactly as `OciAdapter._attempt_labels` composes it -- the
        activated context plus the grants' assignment plus the three resolved
        digests -- because a listing the adapter cannot reconcile on is not
        evidence about this attempt at all.
        """
        from baton_v12.worker_manager import documents, label_context
        from baton_v12.worker_manager.oci import LABEL_PREFIX

        context = label_context(self.store, given["attempt_id"])
        labels = documents.runtime_labels(
            runtime_attempt_id=given["attempt_id"],
            authority_uuid=given["work_ref"]["authority_uuid"],
            work_id=given["work_ref"]["work_id"],
            participant=given["participant"],
            generation=given["generation"],
            principal=context["principal"],
            effective_scope=context["effective_scope"],
            profile_digest=given["runtime_profile_digest"],
            policy_digest=given["policies"]["policy_digest"],
            adapter_digest=given["adapter_digest"])
        return {f"{LABEL_PREFIX}{name}": str(labels[name])
                for name in documents.RUNTIME_LABELS}

    def engine(self, *, inspect, listed=()):
        """A recovery capability set whose engine answers `inspect` so.

        `listed` is what the engine says carries this attempt's whole label
        set. That is the question the PRE-ATTACH branch asks before it removes
        anything, and until this fixture could answer it that branch had no
        command-level coverage of M60437's untouched-runtime rule.

        EVERY ARGV IS RECORDED, because the rule is about what this recovery
        did NOT do: a `stop` issued for a runtime it could not identify
        exactly is the defect, and only the vectors can show its absence.
        """
        self.commands = []

        def capabilities(operands):
            def run(argv, *, seconds=None):
                del seconds
                self.commands.append(list(argv))
                if "inspect" in argv:
                    return inspect(argv[-1])
                if "ps" in argv:
                    rows = [json.dumps(
                        {"ID": one, "Image": operands["image_digest"],
                         "Labels": self.attempt_labels(operands)})
                        for one in listed]
                    return {"status": 0, "stderr": "",
                            "stdout": "\n".join(rows)}
                return {"stdout": "", "stderr": "", "status": 0}

            built = dogfood_operator._for_abandonment(operands, run=run)
            if built.get("disagreement"):
                return built
            from baton_v12.worker_manager import custody

            built["adapter"].normalize_directory = (
                lambda store, *, assignment_id, which: custody._answered(
                    "normalize", 0,
                    {"custody": "normalize", "entries": 0, "not_ours": 0,
                     "running_as": [0, 0]}, None))
            return built

        return capabilities

    def abandoned(self, grants_path, capabilities, out=None,
                  reason="the supervising turn was torn down"):
        place = out or os.path.join(self._root.name, "recovery.json")
        status = dogfood_operator.main(
            ["--grants", grants_path, "--evidence", place, "--abandon",
             "--abandon-reason", reason],
            capabilities=lambda _g: self.fail("the ordinary builder ran"),
            abandon_capabilities=capabilities)
        with open(place, encoding="utf-8") as reading:
            return status, json.load(reading)

    # -- runtime outcomes ----------------------------------------------------

    def test_a_runtime_the_engine_still_reports_running_settles_nothing(self):
        """The removal was ordered and the engine says the container is UP.

        A container this manager cannot say is gone may still be reading the
        mount, so nothing is torn down and nothing is called an ending.
        """
        given, grants_path, _made = self.interrupted_attached()

        def running(runtime):
            return {"status": 0, "stderr": "", "stdout": json.dumps(
                [{"Id": runtime, "State": {"Running": True}, "Mounts": []}])}

        status, written = self.abandoned(grants_path, self.engine(
            inspect=running))

        self.assertEqual(status, 1)
        self.assertFalse(written["resolved"])
        self.assertEqual(written["runtime"]["state"], "running")
        self.assertNotEqual(written["cleanup"], "retained")
        self.assertNotEqual(written["credentials"]["lifecycle_state"],
                            "torn-down")
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])),
            "a bearer was removed under a container reported running")

    def test_an_engine_answering_about_another_runtime_is_not_evidence(self):
        """The wrong-label shape at the identity that matters: an inspection
        naming a different runtime says nothing about this one."""
        given, grants_path, _made = self.interrupted_attached()

        def elsewhere(_runtime):
            return {"status": 0, "stderr": "", "stdout": json.dumps(
                [{"Id": "some-other-runtime", "State": {"Running": False},
                  "Mounts": []}])}

        status, written = self.abandoned(grants_path,
                                         self.engine(inspect=elsewhere))

        self.assertEqual(status, 1)
        self.assertEqual(written["runtime"]["state"], "uncertain")
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))

    def test_an_inspection_naming_two_runtimes_is_not_evidence_either(self):
        """The duplicate shape. One exact identity has one answer."""
        given, grants_path, _made = self.interrupted_attached()

        def duplicated(runtime):
            return {"status": 0, "stderr": "", "stdout": json.dumps(
                [{"Id": runtime, "State": {"Running": False}, "Mounts": []},
                 {"Id": runtime, "State": {"Running": False}, "Mounts": []}])}

        status, written = self.abandoned(grants_path,
                                         self.engine(inspect=duplicated))

        self.assertEqual(status, 1)
        self.assertEqual(written["runtime"]["state"], "uncertain")
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))

    # -- restart through the command ----------------------------------------

    def faulting(self, where):
        """A recovery capability set that faults at ONE named boundary."""
        def capabilities(operands):
            built = self.recovery_capabilities(operands)
            if built.get("disagreement"):
                return built
            adapter = built["adapter"]
            if where == "fence":
                session = built["session"]

                def cancel(*arguments, **operands_):
                    del arguments, operands_
                    raise RuntimeError("the authority went away mid-fence")

                session.cancel = cancel
            elif where == "removal":
                def destroy_abandoned(_command):
                    raise RuntimeError("the engine went away mid-removal")

                adapter.destroy_abandoned = destroy_abandoned
            elif where == "custody":
                def normalize_directory(store, *, assignment_id, which):
                    del store, assignment_id, which
                    raise RuntimeError("the custody helper went away")

                adapter.normalize_directory = normalize_directory
            else:
                raise AssertionError(f"unknown boundary {where}")
            return built

        return capabilities

    def test_a_restart_after_a_fault_at_any_boundary_converges(self):
        """RESTART IS THE POINT, and every one of these is a fresh process's
        worth of state: the command is invoked again from the same grants,
        with nothing carried in memory from the run that faulted.

        THE FAULTING RUN STILL LEAVES A RECORD, which is the rule `main`
        already holds for a post-start fault, and the SECOND run converges to
        the same terminal ending with the host clean.
        """
        for where in ("fence", "removal", "custody"):
            with self.subTest(boundary=where):
                self.setUp()
                given, grants_path, _made = self.interrupted_attached()
                place = os.path.join(self._root.name, f"{where}.json")
                with self.assertRaises(RuntimeError):
                    dogfood_operator.main(
                        ["--grants", grants_path, "--evidence", place,
                         "--abandon", "--abandon-reason",
                         "the supervising turn was torn down"],
                        capabilities=lambda _g: self.fail("built"),
                        abandon_capabilities=self.faulting(where))
                # THE FAULT LEFT AN ACCOUNT.
                self.assertTrue(os.path.exists(place),
                                f"a fault at {where} wrote no record")
                with open(place, encoding="utf-8") as reading:
                    faulted = json.load(reading)
                self.assertFalse(faulted["resolved"])
                self.assertTrue(any("faulted after it began" in one
                                    for one in faulted["unresolved"]))

                # AND THE RESTART CONVERGES.
                status, written = self.abandoned(
                    grants_path, self.recovery_capabilities, out=place)
                self.assertEqual(status, 0, written["unresolved"])
                self.assertEqual(written["cleanup"], "retained")
                self.assertEqual(written["credentials"]["lifecycle_state"],
                                 "torn-down")
                home = self.home(given)
                self.assertFalse(os.path.lexists(
                    home.volatile_root(given["attempt_id"])))
                self.assertFalse(live_secret(self.CANARY))

    # -- the narrow retry adopts through the same owner ---------------------

    def test_the_narrow_retry_adopts_through_the_granted_credential_owner(
            self):
        """W55758's option (a), at the OTHER builder.

        `_for_retry` used to read the granted home while `OciAdapter` derived
        its own from the assignment workspace, so adoption refused and the
        ending would have misreported a delivered credential. This proves the
        retry builder now adopts through the granted home AND hands the
        adapter that same owner.
        """
        from baton_v12.worker_manager import credentials

        given, _grants_path, made = self.interrupted_attached()
        evidence = {one: given.get(one)
                    for one in dogfood_operator.EVIDENCE_MEMBERS
                    if one in given}
        evidence.update({"runtime_id": "runtime-1",
                         "worker_image_digest": given["image_digest"]})
        # W55758 review (2026-09-01T06:09:21Z) [P1]: BY IDENTITY, NOT BY PATH.
        # A freshly constructed same-path `CredentialHome` satisfies a path
        # comparison and is a different owner, which is the same assertion gap
        # caught earlier at `_launched`. So the RECEIVER of the `adopt` call
        # is captured and the adapter is required to own that exact object.
        received = []
        held_adopt = credentials.CredentialHome.adopt

        def adopt(home, *arguments, **operands):
            received.append(home)
            return held_adopt(home, *arguments, **operands)

        with mock.patch.object(credentials.CredentialHome, "adopt", adopt):
            built = dogfood_operator._for_retry(evidence, given)
        self.addCleanup(lambda: [close() for close in built["closing"]])
        adapter = built["adapter"]

        self.assertEqual(len(received), 1,
                         "the retry adopted no delivery, or adopted twice")
        self.assertIsInstance(adapter.credential_delivery,
                              credentials.Delivery)
        self.assertEqual(adapter.credential_delivery.attempt_id,
                         given["attempt_id"])
        self.assertIs(adapter.credential_home, received[0],
                      "the retry adopted through one home and handed the "
                      "adapter another over the same path")
        self.assertIs(adapter._credential_home(), received[0])
        # THE ADOPTION RE-REGISTERED THE BEARER, so this case owns it and
        # ends it through the same home rather than leaving it live.
        adapter.credential_home.tear_down(adapter.credential_delivery)
        self.assertFalse(live_secret(self.CANARY))
        del made


class TheGrantsAreHeldAgainstTheFixedAssignment(
        TheRecoveryMatrixOverDurableAttachedState):
    """W55758, approver ruling APPROVE-EXTEND (M60437).

    THE MEASURED DEFECT. A grants file is an editable durable surface and
    nothing compared it with what activation FIXED: `abandon_attempt` takes
    its assignment from the attempt ROW, so a recovery granted generation 2
    ended the generation-1 attempt anyway and wrote its own generation into
    the record as though it were the identity the ending used.

    THE HOLD IS BEFORE EITHER BRANCH AND BEFORE ANY EXTERNAL ACT, which is
    what each of these asserts: no authority act, no engine act, no credential
    or launch teardown, no custody, and the branch itself unset.
    """

    def watched(self):
        """Recovery capabilities that RECORD every external seam they touch.

        W55758 review (2026-09-01T10:21:35Z) [P1]. Asserting that no member of
        the record was filled proves nothing happened AFTER the builder ran;
        the ruling is about what happens INSIDE it. So the seams the builder
        would exercise are watched, and the assertion is that none was.
        """
        from baton_v12.authority import Authority
        from baton_v12.worker_manager import credentials, launch

        self.exercised = []
        held = {"authority": Authority.open, "roots": dogfood_operator._proved_roots,
                "orphan": credentials.OrphanTeardown,
                "launch": launch.adopt}

        def capabilities(operands):
            with ExitStack() as watching:
                for name, original in held.items():
                    watching.enter_context(self.watching(name, original))
                return self.recovery_capabilities(operands)

        return capabilities

    def watching(self, name, original):
        from baton_v12.authority import Authority
        from baton_v12.worker_manager import credentials, launch

        def noted(*arguments, **operands):
            self.exercised.append(name)
            return original(*arguments, **operands)

        targets = {"authority": (Authority, "open"),
                   "roots": (dogfood_operator, "_proved_roots"),
                   "orphan": (credentials, "OrphanTeardown"),
                   "launch": (launch, "adopt")}
        owner, member = targets[name]
        return mock.patch.object(owner, member, noted)

    def edited(self, grants_path, **overrides):
        with open(grants_path, encoding="utf-8") as reading:
            given = json.load(reading)
        for name, value in overrides.items():
            if name == "work_ref":
                given["work_ref"] = dict(given["work_ref"], **value)
            else:
                given[name] = value
        place = os.path.join(self._root.name, "edited-grants.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(given, writing)
        return place

    def test_every_assignment_member_refuses_with_nothing_touched(self):
        for name, overrides in (
                ("generation", {"generation": 2}),
                ("authority_uuid",
                 {"work_ref": {"authority_uuid": "f" * 32}}),
                ("work_id", {"work_ref": {"work_id": "2bdb4a5d-W99999"}}),
                ("participant", {"participant": "baton.someone"})):
            with self.subTest(member=name):
                self.setUp()
                given, grants_path, _made = self.interrupted_attached()
                edited = self.edited(grants_path, **overrides)
                home = self.home(given)
                before = self.state(given)

                status, written = self.abandoned(edited, self.watched())

                self.assertEqual(status, 1)
                self.assertFalse(written["resolved"])
                self.assertIsNone(written["branch"],
                                  "the hold must land before either branch")
                self.assertTrue(any("disagree on" in one
                                    for one in written["unresolved"]),
                                written["unresolved"])
                # NO CAPABILITY WAS EVER BUILT, which is the ruled boundary
                # rather than merely "nothing mutated afterwards": the builder
                # opens the authority, selects a session, proves roots,
                # constructs the credential owners and adopts the launch
                # delivery, and none of that may happen behind a grants file
                # that is not this attempt's.
                self.assertEqual(self.exercised, [],
                                 f"capabilities were built: {self.exercised}")
                # NOTHING WAS TOUCHED: no authority act, no engine act, no
                # credential or launch teardown, no custody.
                for member in ("authority_fence", "runtime", "credentials",
                               "launch", "custody", "cleanup"):
                    self.assertIsNone(written[member], member)
                self.assertEqual(self.state(given), before,
                                 "the manager's own axes moved")
                self.assertTrue(os.path.lexists(
                    home.volatile_root(given["attempt_id"])),
                    "a bearer was removed under mismatched grants")
                self.assertTrue(os.path.exists(
                    home.state_path(given["attempt_id"])))

    def test_matching_grants_still_end_the_attempt(self):
        """The positive half, so the refusals above are not passing because
        nothing works."""
        _given, grants_path, _made = self.interrupted_attached()
        status, written = self.abandoned(grants_path,
                                         self.recovery_capabilities)
        self.assertEqual(status, 0, written["unresolved"])
        self.assertEqual(written["cleanup"], "retained")

    def test_grants_naming_another_attempt_never_reach_an_act(self):
        """A grants file naming an attempt this manager never recorded.

        It used to refuse at `_proved_roots`, INSIDE the capability builder --
        after the authority was open and a participant session selected. The
        hold now lands before any of that, so the refusal is the hold's and
        the command still writes the account an operator reads.
        """
        given, grants_path, _made = self.interrupted_attached()
        edited = self.edited(grants_path, attempt_id="attempt-never-recorded")
        home = self.home(given)
        before = self.state(given)

        status, written = self.abandoned(edited, self.recovery_capabilities)

        self.assertEqual(status, 1)
        self.assertIsNone(written["branch"])
        self.assertTrue(any("no attempt" in one
                            for one in written["unresolved"]),
                        written["unresolved"])
        self.assertEqual(self.state(given), before)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))


class TheCredentialToLaunchBoundaryConverges(
        TheRecoveryMatrixOverDurableAttachedState):
    """W55758 review (2026-09-01T06:09:21Z) [P1]: the boundary INSIDE the
    composite answer, reached at a PUBLIC act.

    `_removed` settles the credential and then the launch root on one absence
    observation, and a process can die between those two acts even though the
    adapter answers once. The injection point is `launch.discard`, which is a
    public manager act -- no private seam is touched.
    """

    def test_a_fault_between_the_two_teardowns_leaves_an_account(self):
        from baton_v12.worker_manager import launch

        given, grants_path, _made = self.interrupted_attached()
        place = os.path.join(self._root.name, "recovery.json")
        home = self.home(given)

        with mock.patch.object(
                launch, "discard",
                side_effect=RuntimeError("the launch root would not go")):
            with self.assertRaises(RuntimeError):
                dogfood_operator.main(
                    ["--grants", grants_path, "--evidence", place,
                     "--abandon", "--abandon-reason",
                     "the supervising turn was torn down"],
                    capabilities=lambda _g: self.fail("built"),
                    abandon_capabilities=self.recovery_capabilities)

        with open(place, encoding="utf-8") as reading:
            faulted = json.load(reading)
        self.assertFalse(faulted["resolved"])
        # THE CREDENTIAL HALF REALLY HAPPENED, and the record says so.
        self.assertEqual(faulted["runtime"]["state"], "absent")
        self.assertEqual(faulted["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertFalse(os.path.lexists(
            home.volatile_root(given["attempt_id"])))
        # AND THE LAUNCH HALF DID NOT.
        self.assertNotEqual((faulted["launch"] or {}).get("lifecycle_state"),
                            "torn-down")
        self.assertTrue(any("faulted after it began" in one
                            for one in faulted["unresolved"]))

        # THE RESTART CONVERGES.
        status, written = self.abandoned(grants_path,
                                         self.recovery_capabilities,
                                         out=place)
        self.assertEqual(status, 0, written["unresolved"])
        self.assertEqual(written["cleanup"], "retained")
        self.assertEqual(written["launch"]["lifecycle_state"], "torn-down")
        self.assertFalse(live_secret(self.CANARY))

    def test_an_attempt_with_no_fixed_assignment_refuses_before_any_act(self):
        """Activation is what fixes an assignment, and a grants file cannot be
        held against something that was never decided.

        The attempt EXISTS here -- it was recorded -- so this is the hold's
        second branch rather than its first.
        """
        given, grants_path, _made = self.interrupted_attached(activate=False)
        status, written = None, None
        found = self.state(given)
        self.assertIsNotNone(found, "this row needs a recorded attempt")
        self.assertIsNone(found["assignment"],
                          "this row needs an attempt with no fixed assignment")

        status, written = self.abandoned(grants_path,
                                         self.recovery_capabilities)

        home = self.home(given)
        before = self.state(given)
        self.assertEqual(status, 1)
        self.assertIsNone(written["branch"],
                          "the hold must land before either branch")
        self.assertTrue(any("no fixed assignment" in one
                            for one in written["unresolved"]),
                        written["unresolved"])
        for member in ("authority_fence", "runtime", "credentials", "launch",
                       "custody", "cleanup"):
            self.assertIsNone(written[member], member)
        self.assertEqual(self.state(given), before)
        # AND THERE IS NO BEARER HERE AT ALL, which is the lazy-materialization
        # ruling showing through: activation is what admits the credential, so
        # an attempt that never activated never had one. The row is about the
        # HOLD refusing before any act, not about material it could protect.
        self.assertFalse(os.path.lexists(
            home.volatile_root(given["attempt_id"])))


class TheRecoveryNeverAdoptsAnOlderIncarnationsRuntime(
        TheGrantsAreHeldAgainstTheFixedAssignment):
    """W55758, approver ruling M60437.

    V12 does not adopt or resume a runtime from an older Worker Manager
    incarnation. An EXACTLY IDENTIFIED one may be stopped, its credential
    settled and its attempt marked interrupted, with its output preserved as
    untrusted evidence. Unknown, ambiguous and MISMATCHED runtimes stay
    untouched and are reported as zombies; automatic reconciliation of those
    is deliberately out of scope, so the report IS the deliverable.
    """

    def test_a_fresh_incarnation_ends_the_exactly_identified_old_runtime(self):
        """The attempt was attached under one incarnation and the recovery
        runs under another. Nothing is adopted or resumed: the exact runtime
        is removed, its credential settled and its attempt left `retained`
        with the worker's output untouched."""
        from baton_v12.worker_manager import (frozen_output_of,
                                              intake_receipt_of)

        given, grants_path, _made = self.interrupted_attached()
        fresh = self.edited(grants_path,
                            incarnation="w55758-a-later-manager")
        with open(fresh, encoding="utf-8") as reading:
            self.assertNotEqual(json.load(reading)["incarnation"],
                                given["incarnation"])
        # W55758 review (2026-09-01T10:56:54Z) [P1]: REAL BYTES, WRITTEN WHERE
        # A WORKER WRITES THEM. `cleanup: retained` is the manager's word for
        # material kept on purpose and says nothing about file content, so
        # this case asserted the axis and proved nothing about the output the
        # ruling requires preserved.
        marker = os.path.join(
            dogfood_operator._proved_roots(given)["workspace"],
            "proposal", "candidate", "the-worker-wrote-this.txt")
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        body = b"an interrupted worker's untrusted output\n"
        with open(marker, "wb") as writing:
            writing.write(body)

        status, written = self.abandoned(fresh, self.recovery_capabilities)

        self.assertEqual(status, 0, written["unresolved"])
        self.assertEqual(written["cleanup"], "retained")
        self.assertEqual(written["runtime"]["state"], "absent")
        self.assertEqual(written["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertIsNone(written["zombies"],
                          "an exactly identified runtime is not a zombie")
        home = self.home(given)
        self.assertFalse(os.path.lexists(
            home.volatile_root(given["attempt_id"])))
        # THE WORKER'S OWN OUTPUT IS PRESERVED, untrusted and in place: the
        # ending is `retained`, which is the frozen axis's word for material
        # kept on purpose.
        self.assertEqual(self.state(given)["cleanup"], "retained")
        # AND THE BYTES ARE STILL THERE, unmoved and unchanged.
        self.assertTrue(os.path.exists(marker),
                        "the worker's output was removed by an ending that "
                        "reports it retained")
        with open(marker, "rb") as reading:
            self.assertEqual(reading.read(), body)
        # UNTRUSTED, which means NOTHING PROMOTED IT. A recovery runs no
        # freeze and no intake, so the manager's own two readers must still
        # answer that this attempt reached neither.
        self.assertIsNone(frozen_output_of(self.store, given["attempt_id"]),
                          "a recovery froze the worker's output")
        self.assertIsNone(intake_receipt_of(self.store, given["attempt_id"]),
                          "a recovery took the worker's output into custody")
        self.assertEqual(
            sorted({one["verb"] for one in written["custody"].values()}),
            ["normalize"],
            "the only custody act an ending performs is normalization; a "
            "promotion verb here would be a proposal this recovery trusted")

    def test_an_unidentifiable_runtime_is_reported_and_left_alone(self):
        """The other half. An engine answering about another id cannot
        identify this attempt's runtime, so nothing is stopped and the
        recovery's one obligation is to name what it left."""
        given, grants_path, _made = self.interrupted_attached()

        def elsewhere(_runtime):
            return {"status": 0, "stderr": "", "stdout": json.dumps(
                [{"Id": "some-other-runtime", "State": {"Running": True},
                  "Mounts": []}])}

        status, written = self.abandoned(grants_path,
                                         self.engine(inspect=elsewhere))

        self.assertEqual(status, 1)
        self.assertFalse(written["resolved"])
        self.assertIsNotNone(written["zombies"],
                             "a runtime this recovery could not identify was "
                             "left running and never reported")
        named = {one["runtime_id"]: one for one in written["zombies"]}
        # THE IDENTITY THE ENGINE ACTUALLY REPORTED IS NAMED, which the first
        # cut of this report could not do: it reconstructed the list from the
        # EXPECTED target while the engine had answered about another.
        self.assertIn("some-other-runtime", named)
        self.assertFalse(named["some-other-runtime"]["targeted"])
        self.assertIn("left untouched", named["some-other-runtime"]["action"])
        # W55758 review (2026-09-01T10:56:54Z) [P1]: ITS OWN STATE AND ITS OWN
        # REASON. This candidate's inspection says `Running: true`, and the
        # report wrote the literal `unidentified` for it and copied the
        # target's diagnostic as its explanation.
        self.assertEqual(named["some-other-runtime"]["state"], "running")
        self.assertEqual(named["some-other-runtime"]["why"],
                         "the engine reports it running")
        # AND THE TARGET IS NAMED TRUTHFULLY: a removal really was issued for
        # it, so calling it untouched would be false.
        target = self.state(given)["runtime_id"]
        self.assertIn(target, named)
        self.assertTrue(named[target]["targeted"])
        self.assertIn("removal was issued", named[target]["action"])
        self.assertNotIn("left untouched", named[target]["action"])
        # AND NOTHING WAS TOUCHED.
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))
        self.assertNotEqual(written["cleanup"], "retained")

    def test_a_running_runtime_is_reported_rather_than_resumed(self):
        given, grants_path, _made = self.interrupted_attached()

        def running(runtime):
            return {"status": 0, "stderr": "", "stdout": json.dumps(
                [{"Id": runtime, "State": {"Running": True}, "Mounts": []}])}

        status, written = self.abandoned(grants_path,
                                         self.engine(inspect=running))

        self.assertEqual(status, 1)
        [zombie] = written["zombies"]
        self.assertEqual(zombie["state"], "running")
        self.assertEqual(zombie["runtime_id"],
                         self.state(given)["runtime_id"])
        self.assertTrue(zombie["targeted"])
        self.assertIn("removal was issued", zombie["action"])
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))

    def test_an_ambiguous_answer_reports_every_candidate_it_named(self):
        """The duplicate shape, which the first report omitted entirely: the
        engine answered about two runtimes and the report named neither."""
        given, grants_path, _made = self.interrupted_attached()

        def duplicated(_runtime):
            return {"status": 0, "stderr": "", "stdout": json.dumps(
                [{"Id": "runtime-a", "State": {"Running": True},
                  "Mounts": []},
                 {"Id": "runtime-b", "State": {"Running": True},
                  "Mounts": []}])}

        status, written = self.abandoned(grants_path,
                                         self.engine(inspect=duplicated))

        self.assertEqual(status, 1)
        named = {one["runtime_id"]: one for one in written["zombies"]}
        for candidate in ("runtime-a", "runtime-b"):
            self.assertIn(candidate, named,
                          f"the engine named {candidate} and the report "
                          f"omitted it")
            self.assertFalse(named[candidate]["targeted"])
            self.assertIn("left untouched", named[candidate]["action"])
            # EACH ONE'S OWN OBSERVED STATE, not the target's and not a
            # placeholder: both of these inspections say `Running: true`.
            self.assertEqual(named[candidate]["state"], "running")
            self.assertEqual(named[candidate]["why"],
                             "the engine reports it running")
        target = self.state(given)["runtime_id"]
        self.assertIn(target, named)
        self.assertIn("removal was issued", named[target]["action"])
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))

    def test_one_identity_answered_twice_in_conflict_is_one_zombie_row(self):
        """W55758 review (2026-09-01T11:38:25Z) [P1], PLAN item 68.

        The engine named `runtime-1` TWICE for one exact identity, once
        `Running: false` and once `Running: true`. The runtime itself was
        reported `uncertain`, which is the truth; the durable record then
        carried both documents as independent rows -- one `quiescent`, one
        `running`, both targeted -- and an operator reading it had two
        mutually exclusive facts about one locator and no way to choose.
        """
        given, grants_path, _made = self.interrupted_attached()

        def conflicting(runtime):
            return {"status": 0, "stderr": "", "stdout": json.dumps(
                [{"Id": runtime, "State": {"Running": False}, "Mounts": []},
                 {"Id": runtime, "State": {"Running": True}, "Mounts": []}])}

        status, written = self.abandoned(grants_path,
                                         self.engine(inspect=conflicting))

        self.assertEqual(status, 1)
        self.assertFalse(written["resolved"])
        self.assertEqual(written["runtime"]["state"], "uncertain")
        # EXACTLY ONE ROW for the one identity the engine talked about.
        [zombie] = written["zombies"]
        self.assertEqual(zombie["runtime_id"], self.state(given)["runtime_id"])
        self.assertEqual(zombie["state"], "uncertain")
        # AND ITS REASON NAMES THE CONFLICT ITSELF, with both of the engine's
        # accounts, rather than the one that happened to be read first.
        self.assertIn("disagree", zombie["why"])
        self.assertIn("the engine reports it not running", zombie["why"])
        self.assertIn("the engine reports it running", zombie["why"])
        # THE PER-RUNTIME ACT IS UNCHANGED AND STILL TRUE: a removal really
        # was issued for this exact identity, so it is not untouched.
        self.assertTrue(zombie["targeted"])
        self.assertIn("removal was issued", zombie["action"])
        self.assertNotIn("left untouched", zombie["action"])
        # AND NOTHING RODE ON AN UNPROVED ABSENCE.
        self.assertNotEqual(written["cleanup"], "retained")
        self.assertNotEqual(written["credentials"]["lifecycle_state"],
                            "torn-down")
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))

    def test_two_uncertain_accounts_for_one_identity_keep_both(self):
        """W55758 review (2026-09-01T11:53:38Z) [P1], PLAN item 70.

        Agreement was decided on the coarse `state` alone, and `uncertain` is
        the state whose REASON is the whole of the evidence. One document
        carrying no state record and another carrying `Running: "yes"` are two
        different engine accounts that both map to `uncertain`; collapsing
        them published the first reason and dropped the second without a word,
        which is the same silent loss this canonicalization exists to end.
        """
        given, grants_path, _made = self.interrupted_attached()

        def two_uncertainties(runtime):
            return {"status": 0, "stderr": "", "stdout": json.dumps(
                [{"Id": runtime, "Mounts": []},
                 {"Id": runtime, "State": {"Running": "yes"},
                  "Mounts": []}])}

        status, written = self.abandoned(
            grants_path, self.engine(inspect=two_uncertainties))

        self.assertEqual(status, 1)
        self.assertFalse(written["resolved"])
        [zombie] = written["zombies"]
        self.assertEqual(zombie["runtime_id"], self.state(given)["runtime_id"])
        self.assertEqual(zombie["state"], "uncertain")
        # BOTH ACCOUNTS, because neither is the other's summary.
        self.assertIn("carries no state record", zombie["why"])
        self.assertIn("Running as 'yes'", zombie["why"])
        self.assertTrue(zombie["targeted"])
        self.assertIn("removal was issued", zombie["action"])
        self.assertNotEqual(written["cleanup"], "retained")
        self.assertNotEqual(written["credentials"]["lifecycle_state"],
                            "torn-down")
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))

    def test_one_identity_answered_twice_in_agreement_is_one_zombie_row(self):
        """The other half of the same rule: an engine repeating itself is one
        observation seen twice, and collapsing it must not invent an
        `uncertain` the engine never reported."""
        given, grants_path, _made = self.interrupted_attached()

        def repeated(runtime):
            return {"status": 0, "stderr": "", "stdout": json.dumps(
                [{"Id": runtime, "State": {"Running": True}, "Mounts": []},
                 {"Id": runtime, "State": {"Running": True}, "Mounts": []}])}

        status, written = self.abandoned(grants_path,
                                         self.engine(inspect=repeated))

        self.assertEqual(status, 1)
        [zombie] = written["zombies"]
        self.assertEqual(zombie["runtime_id"], self.state(given)["runtime_id"])
        self.assertEqual(zombie["state"], "running")
        self.assertEqual(zombie["why"], "the engine reports it running")
        self.assertTrue(zombie["targeted"])
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))

    # -- the PRE-ATTACH branch, under the same rule --------------------------

    def running_elsewhere(self, runtime):
        """The engine's answer about whichever runtime it was asked about."""
        return {"status": 0, "stderr": "", "stdout": json.dumps(
            [{"Id": runtime, "State": {"Running": True}, "Mounts": []}])}

    def assertNothingWasStopped(self):
        acted = [one for one in self.commands
                 if "stop" in one or "kill" in one or "rm" in one]
        self.assertEqual(acted, [],
                         "M60437 leaves an unidentified runtime untouched and "
                         "this recovery acted on one")

    def test_ambiguous_pre_attach_candidates_are_reported_not_stopped(self):
        """W55758 review (2026-09-01T10:56:54Z) [P1], PLAN item 63.

        `OciAdapter._recovery_failed` stopped EVERY candidate it had listed,
        including the ambiguous ones, and reduced the whole answer to prose
        with no zombie member at all. W32385's signed-off contract and M60437
        both say multiplicity fails closed WITHOUT removing unrelated
        candidates, and that the survivors are reported.
        """
        given, grants_path, _made = self.interrupted_before_attach()

        status, written = self.abandoned(
            grants_path,
            self.engine(inspect=self.running_elsewhere,
                        listed=("runtime-a", "runtime-b")))

        self.assertEqual(status, 1)
        self.assertFalse(written["resolved"])
        self.assertEqual(written["branch"], "pre-attach")
        self.assertNothingWasStopped()
        named = {one["runtime_id"]: one for one in written["zombies"]}
        self.assertEqual(sorted(named), ["runtime-a", "runtime-b"])
        for candidate in ("runtime-a", "runtime-b"):
            self.assertFalse(named[candidate]["targeted"])
            self.assertIn("left untouched", named[candidate]["action"])
            self.assertEqual(named[candidate]["state"], "running")
            self.assertEqual(named[candidate]["why"],
                             "the engine reports it running")
        # AND NOTHING OF THIS ATTEMPT'S WAS REMOVED on that account.
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))

    def test_a_pre_attach_identity_listed_twice_is_one_zombie_row(self):
        """The same canonicalization, through the OTHER composer's branch.

        The engine listed one identity twice under this attempt's whole label
        set and then answered differently about it on each observation. One
        composer serves both endings, so a contradiction has to arrive as one
        `uncertain` row here too -- and the runtime is still untouched,
        because nothing about it was ever identified exactly.
        """
        given, grants_path, _made = self.interrupted_before_attach()
        answers = ["Running: false", "Running: true"]

        def alternating(runtime):
            running = answers.pop(0) == "Running: true" if answers else True
            return {"status": 0, "stderr": "", "stdout": json.dumps(
                [{"Id": runtime, "State": {"Running": running},
                  "Mounts": []}])}

        status, written = self.abandoned(
            grants_path,
            self.engine(inspect=alternating,
                        listed=("runtime-a", "runtime-a")))

        self.assertEqual(status, 1)
        self.assertFalse(written["resolved"])
        self.assertEqual(written["branch"], "pre-attach")
        self.assertNothingWasStopped()
        [zombie] = written["zombies"]
        self.assertEqual(zombie["runtime_id"], "runtime-a")
        self.assertEqual(zombie["state"], "uncertain")
        self.assertIn("disagree", zombie["why"])
        self.assertIn("the engine reports it not running", zombie["why"])
        self.assertIn("the engine reports it running", zombie["why"])
        self.assertFalse(zombie["targeted"])
        self.assertIn("left untouched", zombie["action"])
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))

    def test_a_mismatched_pre_attach_candidate_is_reported_not_stopped(self):
        """The other half: one runtime carries this attempt's labels and the
        lifecycle record names a different one, so nothing is exactly
        identified and nothing is acted on."""
        given, grants_path, _made = self.interrupted_before_attach()

        status, written = self.abandoned(
            grants_path,
            self.engine(inspect=self.running_elsewhere,
                        listed=("runtime-somebody-elses",)))

        self.assertEqual(status, 1)
        self.assertFalse(written["resolved"])
        self.assertEqual(written["branch"], "pre-attach")
        self.assertNothingWasStopped()
        [zombie] = written["zombies"]
        self.assertEqual(zombie["runtime_id"], "runtime-somebody-elses")
        self.assertFalse(zombie["targeted"])
        self.assertEqual(zombie["state"], "running")
        self.assertIn("left untouched", zombie["action"])
        home = self.home(given)
        self.assertTrue(os.path.lexists(
            home.volatile_root(given["attempt_id"])))
