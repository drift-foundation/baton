"""The review supervisor: what it refuses, what it admits, what it reuses.

WHAT IS REAL HERE. `review_supervisor.held_packet` is driven over packets
written to disk; `baseline.AdmissionGate` is the real imported gate, driven
with a recording operations object; and `_verdict_evidence` is driven against a
real `ControlStore` holding a real line, writer, frozen checkpoint and review
attachment, built through the supported `review_cycles` API.

WHAT IS NOT PROVED HERE, said in place rather than left to be assumed: no
container, image, provider, network or credential is involved, and no whole run
is driven end to end through `serve`. The termination, discovery, cancellation
and cleanup machinery this supervisor uses is W239528's, imported unchanged and
bound by digest -- `test_the_imported_baseline_is_the_accepted_bytes` is what
makes that reuse checkable, and W239528's own suite is what proved those parts.
What is new here is the orchestration's review shape, and that is what these
cases cover.
"""

import ast
import json
import os
import pathlib
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from baton_v12.contracts import ContractRefusal, digest_of_bytes
from baton_v12.worker_manager import attach_review

import baseline
import review_supervisor
from test_attachment import REVIEWER, AttachmentCase

SIBLING = os.path.join(os.path.dirname(HERE),
                       "finding-v12-single-implementation-proof")


def _write(place, document):
    with open(place, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return place


class PacketCase(unittest.TestCase):
    """A packet on disk whose every pinned artifact really exists."""

    def setUp(self):
        import tempfile

        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = self.temporary.name
        self.criteria_bytes = json.dumps(
            {"schema": "baton.dogfood-task/2", "instructions": "judge it"},
            sort_keys=True).encode("utf-8")
        self.criteria = os.path.join(self.root, "task.json")
        with open(self.criteria, "wb") as handle:
            handle.write(self.criteria_bytes)
        # THE DEPLOYMENT CARRIES THE NO-CORRECTION BOUNDARY. `held_packet`
        # reads this document and refuses without it, which is what keeps the
        # packet non-runnable until the boundary is configured.
        self.deployment = _write(os.path.join(self.root, "deployment.json"),
                                 {"schema": "x",
                                  "correction_policy": "decline"})
        self.submission = _write(os.path.join(self.root, "submission.json"),
                                 {"schema": "y"})
        self.control = os.path.join(self.root, "control.sqlite3")

    def document(self, **overrides):
        held = {
            "schema": review_supervisor.PACKET_SCHEMA,
            "run_id": "independent-review-239533", "work": "W239533",
            "claim": 247159, "note": "the bounded review",
            "subject": {
                "schema": "baton.independent-review-subject/2",
                "line_id": "line-" + "a" * 8,
                "checkpoint_id": "checkpoint-" + "b" * 8,
                "authority_uuid": "c" * 32, "work_id": "cccccccc-W1",
                "declared_base": "1" * 40, "base_object": "1" * 40,
                "head_object": "2" * 40, "tree_object": "3" * 40,
                "checkpoint_digest": "sha256:" + "4" * 64,
                "producer": {"worker_id": "implementation-worker",
                             "participant": "baton.impl",
                             "principal": "principal:baton.impl"}},
            "producer_run_root": self.root,
            "producer_control_store": self.control,
            "worker_image": {"reference": "r", "config_digest": "d",
                             "worker_files": {}},
            "manager_runtime": {"path": self.root, "executable_sha256": "e",
                                "build_commit": "f" * 40},
            "manager_source": {"path": self.root, "packages": [],
                               "file_count": 0, "files": {}},
            "supervisor": {"path": __file__, "sha256": "s"},
            "code_boundary": self.root,
            "deployment": {
                "config_path": self.deployment,
                "config_sha256": baseline._digest_of_file(self.deployment),
                "job_store": os.path.join(self.root, "jobs.sqlite3"),
                "control_store": self.control,
                "authority_store": os.path.join(self.root, "a.sqlite3"),
                "authority_uuid": "c" * 32,
                "state_root": self.root},
            "context": {"storage_path": self.root, "excluded_roots": [],
                        "runtime_uid": os.getuid(), "profile_path": None,
                        "profile_sha256": None, "profile_digest": None,
                        "job_id": "job-independent-review-239533"},
            "submission": {
                "path": self.submission,
                "sha256": baseline._digest_of_file(self.submission),
                "job_id": "job-independent-review-239533"},
            "criteria": {"path": self.criteria,
                         "sha256": baseline._digest_of_file(self.criteria),
                         "content_digest": digest_of_bytes(
                             self.criteria_bytes)},
            "bounds": {"turn_seconds": 180, "total_seconds": 300,
                       "cleanup_seconds": 60, "review_invocations": 1,
                       "retry": False},
            "outcome_path": os.path.join(self.root, "outcome.json")}
        for name, value in overrides.items():
            if isinstance(value, dict) and isinstance(held.get(name), dict):
                held[name] = dict(held[name], **value)
            else:
                held[name] = value
        return held

    def written(self, **overrides):
        return _write(os.path.join(self.root, "PACKET.json"),
                      self.document(**overrides))

    def refusal(self, **overrides):
        with self.assertRaises(review_supervisor.SupervisorRefusal) as caught:
            review_supervisor.held_packet(self.written(**overrides))
        return str(caught.exception)


class ThePacketIsHeldBeforeAnythingOpens(PacketCase):
    def test_a_well_formed_packet_is_accepted(self):
        held = review_supervisor.held_packet(self.written())
        self.assertEqual(held["bounds"]["review_invocations"], 1)

    def test_another_supervisors_packet_is_refused_by_schema(self):
        said = self.refusal(schema="baton.single-implementation-packet/1")
        self.assertIn(review_supervisor.PACKET_SCHEMA, said)

    def test_a_second_review_invocation_is_refused(self):
        said = self.refusal(bounds={"review_invocations": 2})
        self.assertIn("ONE review container", said)

    def test_no_review_invocation_is_refused(self):
        said = self.refusal(bounds={"review_invocations": 0})
        self.assertIn("ONE review container", said)

    def test_retry_is_refused(self):
        said = self.refusal(bounds={"retry": True})
        self.assertIn("never retries", said)

    def test_the_cleanup_reserve_must_be_inside_the_overall_bound(self):
        said = self.refusal(bounds={"cleanup_seconds": 300})
        self.assertIn("beside it", said)

    def test_implementation_bounds_have_no_member_to_land_in(self):
        """`_BOUNDS` is closed, so W239528's own bounds are refused here."""
        said = self.refusal(bounds={"implementer_invocations": 1})
        self.assertIn("bounds", said.lower())

    def test_a_subject_whose_head_is_its_base_has_nothing_to_review(self):
        said = self.refusal(subject={"head_object": "1" * 40})
        self.assertIn("no change to review", said)

    def test_a_declared_base_that_is_not_the_checkpoints_is_refused(self):
        said = self.refusal(subject={"declared_base": "9" * 40})
        self.assertIn("the producer actually froze", said)

    def test_criteria_bytes_that_do_not_hash_to_the_sealed_digest(self):
        with open(self.criteria, "wb") as handle:
            handle.write(b'{"schema": "baton.dogfood-task/2"}')
        said = self.refusal(criteria={
            "sha256": baseline._digest_of_file(self.criteria)})
        self.assertIn("different document from the reviewed one", said)

    def test_a_deployment_that_opens_corrections_is_refused(self):
        """The packet is not runnable until the boundary is configured.

        Owner reroute 247421. Before the selected product change there was no
        way to say this, and claim 247318 reported the round AFTER
        `StageComposition.routed` had opened it -- which review
        2026-09-23T11:56:42Z R4 refused, correctly: "returning held does not
        undo that store effect".
        """
        for policy in (None, "open"):
            with self.subTest(policy=policy):
                self.setUp()
                document = {"schema": "x"}
                if policy is not None:
                    document["correction_policy"] = policy
                _write(self.deployment, document)
                said = self.refusal(deployment={
                    "config_sha256": baseline._digest_of_file(
                        self.deployment)})
                self.assertIn("not runnable until the boundary", said)

    def test_the_required_policy_is_the_products_own_word(self):
        """Mirrored, so the two have to be held together.

        `held_packet` runs BEFORE `verify_imported_sources` has proved which
        `tools` this process resolved, so importing the value from an unproved
        tree to decide whether to trust that tree would be circular. The
        constant is mirrored and this is what stops the mirror drifting.
        """
        from tools import stage_execution

        self.assertEqual(review_supervisor.DECLINE_CORRECTION,
                         stage_execution.DECLINE_CORRECTION)
        self.assertIn(stage_execution.DECLINE_CORRECTION,
                      stage_execution.CORRECTION_POLICIES)

    def test_a_control_store_other_than_the_subjects_is_refused(self):
        """The line being reviewed lives in ONE store."""
        elsewhere = os.path.join(self.root, "other.sqlite3")
        said = self.refusal(deployment={"control_store": elsewhere})
        self.assertIn("cannot reach", said)


class TheImportedMachineryIsBoundAndUnmodified(PacketCase):
    def test_the_imported_baseline_is_the_accepted_bytes(self):
        self.assertEqual(baseline._digest_of_file(baseline.__file__),
                         review_supervisor.BASELINE_SHA256)

    def test_a_drifted_baseline_refuses_before_anything_opens(self):
        """Reuse that cannot say WHICH bytes it reused is a dependency."""
        from unittest import mock

        with mock.patch.object(review_supervisor, "BASELINE_SHA256",
                               "0" * 64):
            said = self.refusal()
        self.assertIn("cannot vouch for machinery it cannot identify", said)

    def test_it_monkeypatches_nothing_in_baseline(self):
        """Asked of the parsed module, not of its prose.

        Review 2026-09-23T05:08:49Z: "Do not monkeypatch baseline globals".
        A specialization that assigned to `baseline.KINDS` would change
        W239528's module for every importer in the process, which is a
        cross-dossier edit performed at runtime rather than in a file.
        """
        tree = ast.parse(pathlib.Path(review_supervisor.__file__).read_text(
            encoding="utf-8"))
        assigned = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                targets = (node.targets if isinstance(node, ast.Assign)
                           else [node.target])
                for one in targets:
                    if isinstance(one, ast.Attribute) and isinstance(
                            one.value, ast.Name) and one.value.id == "baseline":
                        assigned.append(one.attr)
            if isinstance(node, ast.Call) and isinstance(
                    node.func, ast.Name) and node.func.id == "setattr":
                first = node.args[0] if node.args else None
                if isinstance(first, ast.Name) and first.id == "baseline":
                    assigned.append("setattr")
        self.assertEqual(assigned, [])

    def test_its_own_kinds_are_closed_over_review(self):
        self.assertEqual(review_supervisor.KINDS, ("review",))
        # AND W239528'S CONSTANT IS UNTOUCHED.
        self.assertEqual(baseline.KINDS, ("implementation",))


class Recording:
    """An operations object that records the three admitting acts."""

    def __init__(self):
        self.calls = []
        self.canonical = None

    def admit(self, stage, job):
        self.calls.append(("admit", stage.get("kind")))
        return {"admitted": stage.get("stage_id")}

    def claim(self, stage):
        self.calls.append(("claim", stage.get("kind")))
        return {"claimed": stage.get("stage_id")}

    def launch(self, attempt, job):
        self.calls.append(("launch", attempt.get("attempt_id")))
        return {"launched": attempt.get("attempt_id")}


class AdmissionIsBoundedAtTheGate(unittest.TestCase):
    """The REAL imported `AdmissionGate`, given this run's caps.

    Nothing about the gate is specialized; what these cases establish is that
    the caps this supervisor constructs it with produce the review shape.
    """

    JOB = "job-independent-review-239533"

    def gate(self, operations=None):
        return baseline.AdmissionGate(
            operations or Recording(), caps={"review": 1}, job_id=self.JOB)

    def stage(self, kind, stage_id="stage-1", job=None):
        return {"kind": kind, "stage_id": stage_id,
                "job_id": self.JOB if job is None else job}

    def test_one_review_is_admitted_and_the_second_is_refused(self):
        gate = self.gate()
        gate.admit(self.stage("review"), None)
        with self.assertRaises(ContractRefusal):
            gate.admit(self.stage("review", "stage-2"), None)
        self.assertEqual(gate.admissions["review"], 1)
        self.assertEqual(gate.exhausted, ["review"])

    def test_an_implementation_stage_is_refused_by_kind(self):
        gate = self.gate()
        with self.assertRaises(ContractRefusal) as caught:
            gate.admit(self.stage("implementation"), None)
        self.assertIn("review", str(caught.exception))
        self.assertEqual(gate.admissions["review"], 0)

    def test_another_jobs_stage_is_foreign_and_not_a_refusal(self):
        gate = self.gate()
        with self.assertRaises(ContractRefusal):
            gate.admit(self.stage("review", job="job-somebody-else"), None)
        self.assertTrue(gate.foreign)
        self.assertEqual(gate.refusals, [])

    def test_a_closed_gate_admits_claims_and_launches_nothing(self):
        gate = self.gate()
        gate.stop()
        for act, operands in (("admit", (self.stage("review"), None)),
                              ("claim", (self.stage("review"),)),
                              ("launch", ({"attempt_id": "a",
                                           "stage_id": "stage-1"}, None))):
            with self.subTest(act=act):
                with self.assertRaises(ContractRefusal):
                    getattr(gate, act)(*operands)


class TheVerdictEvidenceReadsTheFrozenOutput(AttachmentCase):
    """Driven against a real control store with a real attachment."""

    def packet(self, **overrides):
        held = {
            "bounds": {"review_invocations": 1},
            "subject": {
                "line_id": self.line_id,
                "checkpoint_id": self.checkpoint["checkpoint_id"],
                # `base_object`/`head_object`/`tree_object` ARE WHAT THE ROW
                # CALLS THEM. This read `checkpoint.get("base")` and friends,
                # which are absent, so every comparison below was None-vs-None
                # and proved nothing. Review 2026-09-23T11:30:47Z R2.
                "base_object": self.frozen["base_object"],
                "head_object": self.frozen["head_object"],
                "tree_object": self.frozen["tree_object"],
                "producer": {"worker_id": self.PRODUCER_WORKER,
                             "participant": self.PRODUCER_PARTICIPANT,
                             "principal": self.PRODUCER_PRINCIPAL}}}
        for name, value in overrides.items():
            held[name] = dict(held[name], **value)
        return held

    @property
    def frozen(self):
        from baton_v12.worker_manager import checkpoint_of

        return checkpoint_of(self.store, self.checkpoint["checkpoint_id"])

    def attached(self, generation=7):
        attempt = self.reviewer_attempt(generation)
        attach_review(self.store,
                      checkpoint_id=self.checkpoint["checkpoint_id"],
                      attempt_id=attempt, generation=generation,
                      reviewer_worker_id=REVIEWER["reviewer_worker_id"],
                      profile=self.profile)
        return attempt

    def test_no_review_attempt_at_all_is_a_shortfall(self):
        found = review_supervisor._verdict_evidence(
            self.store, self.packet(), {}, {})
        self.assertTrue(any("declares 1 review invocation" in one
                            for one in found["shortfalls"]), found)

    def test_an_implementation_attempt_here_is_a_shortfall(self):
        found = review_supervisor._verdict_evidence(
            self.store, self.packet(), {"writer-attempt-1": "implementation"},
            {})
        self.assertTrue(any("separate Jobs" in one
                            for one in found["shortfalls"]), found)

    def test_an_attached_review_with_no_frozen_verdict_is_a_shortfall(self):
        """A turn that produced no attributed report is not a result.

        This is the distinction the whole function exists for: the attachment
        is real, the attempt ran, and there is still nothing to report --
        which a supervisor reading a process exit status would have called
        success.
        """
        attempt = self.attached()
        found = review_supervisor._verdict_evidence(
            self.store, self.packet(), {attempt: "review"}, {})
        self.assertEqual(
            [one["attempt_id"] for one in found["attachments"]], [attempt])
        self.assertTrue(
            any("no readable verdict" in one for one in found["shortfalls"])
            or any("did not happen" in one for one in found["shortfalls"]),
            found["shortfalls"])

    def answered(self, **overrides):
        """What `review_verdict_from_result` DOCUMENTS that it returns.

        SUBSTITUTED, AND LABELLED. Reaching a real frozen review output needs
        a provider turn and an Authority receipt, which this deterministic
        suite does not have and must not fabricate. What it can do honestly is
        hold this collector to the PUBLIC RETURN CONTRACT -- the members that
        function's own `return` statement names -- because reading members it
        does not answer is exactly the defect review 2026-09-23T11:30:47Z R2
        found, and no amount of missing-verdict coverage could have caught it.
        """
        held = {"attachment_id": "review-a", "attempt_id": "review-attempt-7",
                "checkpoint_id": self.checkpoint["checkpoint_id"],
                "verdict": "accepted",
                "base": self.frozen["base_object"],
                "head": self.frozen["head_object"],
                "tree": self.frozen["tree_object"],
                "result_id": "result-a",
                "result_digest": "sha256:" + "5" * 64}
        held.update(overrides)
        return held

    def collected(self, answered, attempt):
        from unittest import mock

        from baton_v12.job_manager import review_driver

        with mock.patch.object(review_driver, "review_verdict_from_result",
                               return_value=answered):
            return review_supervisor._verdict_evidence(
                self.store, self.packet(), {attempt: "review"}, {})

    def test_every_supported_verdict_is_a_result_and_not_a_shortfall(self):
        for verdict in review_supervisor.VERDICTS:
            with self.subTest(verdict=verdict):
                self.setUp()
                attempt = self.attached()
                found = self.collected(self.answered(verdict=verdict), attempt)
                self.assertEqual(found["shortfalls"], [], found)
                self.assertEqual(
                    [one["verdict"] for one in found["verdicts"]], [verdict])
                self.assertEqual(found["verdicts"][0]["result_id"],
                                 "result-a")
                self.assertEqual(found["verdicts"][0]["result_digest"],
                                 "sha256:" + "5" * 64)
                self.assertEqual(
                    [one["verdict"] for one in found["dispositions"]],
                    [verdict])

    def test_the_attachment_generation_is_the_one_the_row_records(self):
        attempt = self.attached(generation=7)
        found = self.collected(self.answered(), attempt)
        self.assertEqual(found["attachments"][0]["generation"], 7)
        self.assertEqual(found["attachments"][0]["runtime_attempt_id"],
                         attempt)

    def test_a_verdict_outside_the_contract_is_a_shortfall(self):
        attempt = self.attached()
        found = self.collected(self.answered(verdict="looks-fine"), attempt)
        self.assertTrue(any("which is not one of" in one
                            for one in found["shortfalls"]),
                        found["shortfalls"])

    def test_a_head_other_than_the_checkpoints_is_named(self):
        attempt = self.attached()
        found = self.collected(self.answered(head="9" * 40), attempt)
        self.assertTrue(any("and the reviewed checkpoint records" in one
                            for one in found["shortfalls"]),
                        found["shortfalls"])

    def test_an_attachment_to_another_checkpoint_is_named(self):
        attempt = self.attached()
        found = review_supervisor._verdict_evidence(
            self.store,
            self.packet(subject={"checkpoint_id": "checkpoint-" + "9" * 8}),
            {attempt: "review"}, {})
        self.assertTrue(any("this packet names" in one
                            for one in found["shortfalls"]),
                        found["shortfalls"])


class TheProductBoundaryDeclinesTheRoundItself(unittest.TestCase):
    """`StageDeployment.routed`, driven -- the selected product change.

    THE REAL PRODUCT FUNCTION, unbound and given a stand-in holder, because
    what changed is one condition inside it and constructing a whole
    deployment would test the constructor instead. `open_correction` is
    watched rather than stubbed out: the point is whether it is REACHED.
    """

    def routed(self, policy, answered, *, watcher):
        from unittest import mock

        from tools import stage_execution

        class Holder:
            jobs = None
            control = None

        holder = Holder()
        if policy is not None:
            holder.correction_policy = policy
        with mock.patch.object(stage_execution.review_driver,
                               "open_correction", watcher):
            return stage_execution.StageDeployment.routed(
                holder, {"job_id": "job-independent-review-239533"}, answered)

    def watcher(self):
        seen = []

        def opened(jobs, control, *, job_id, answered):
            seen.append(job_id)
            return {"round": "opened"}

        return seen, opened

    def test_a_declining_deployment_never_reaches_open_correction(self):
        seen, opened = self.watcher()
        answer = self.routed("decline", {"outcome": "correction"},
                             watcher=opened)
        self.assertEqual(seen, [], "the round was opened anyway")
        self.assertIsNone(answer["correction"])
        self.assertEqual(answer["correction_declined"]["policy"], "decline")
        self.assertIn("separately selected Job",
                      answer["correction_declined"]["why"])
        # AND THE VERDICT IS UNTOUCHED. What is declined is the round.
        self.assertEqual(answer["outcome"], "correction")

    def test_every_other_deployment_is_unchanged(self):
        """Absent and `open` both mean exactly what they meant before."""
        for policy in (None, "open"):
            with self.subTest(policy=policy):
                seen, opened = self.watcher()
                answer = self.routed(policy, {"outcome": "correction"},
                                     watcher=opened)
                self.assertEqual(seen, ["job-independent-review-239533"])
                self.assertEqual(answer["correction"], {"round": "opened"})
                self.assertNotIn("correction_declined", answer)

    def test_a_verdict_that_is_not_a_correction_is_returned_as_it_arrived(self):
        for policy in (None, "decline"):
            with self.subTest(policy=policy):
                seen, opened = self.watcher()
                held = {"outcome": "accepted"}
                answer = self.routed(policy, held, watcher=opened)
                self.assertEqual(answer, held)
                self.assertEqual(seen, [])

    def test_a_malformed_policy_is_refused_by_the_validator(self):
        """Owned where every other member is owned, not at `routed`."""
        from tools import stage_execution

        self.assertEqual(stage_execution.CORRECTION_POLICIES,
                         ("open", "decline"))


class Serving:
    """An operations object that serves nothing, and records what it was asked.

    NOT A STUB OF THE COMPOSITION -- a stand-in for the engine side of it, so
    the ORCHESTRATION can be driven. The Job store, the control store, the
    submission, `serve`, `sweep`, `reconcile`, `status` and the real
    `AdmissionGate` are all genuine; what is faked is the part that would
    start a container.

    THE CALL ORDER IS RECORDED, because two of the contract's guarantees are
    about order rather than about values: admission closes BEFORE cancellation
    is asked for, and the cleanup window cannot admit.
    """

    canonical = None

    def __init__(self, *, failing=None, after=0):
        self.calls = []
        self.failing = failing or ()
        self.after = after

    def _note(self, name):
        self.calls.append(name)
        if name in self.failing:
            # `after` exists because the SAME call appears in the owner acts
            # and in the serving loop: `status` reconciles too, so failing at
            # the first `recover` reports a submission failure rather than the
            # serving failure the case is about.
            if self.after > 0:
                self.after -= 1
            else:
                raise RuntimeError(f"the composition failed at {name}")

    def recover(self, *, now):
        self._note("recover")
        return None

    def attach(self, workers):
        self._note("attach")
        return None

    def drain(self, held, quiescent=None):
        self._note("drain")
        return None

    def admit(self, stage, job):
        """Refused the way a busy composition refuses -- as a DEFERRAL.

        `manager._delegate` records a non-durable `ContractRefusal` as a
        deferral, so a tick that cannot admit is a level-triggered condition
        the manager already knows how to report. This fake cannot carry a real
        admit through to a journalled operation, and answering one it cannot
        complete made the NEXT sweep refuse for the fixture's reason rather
        than the run's. Deferring is the honest stand-in, and it leaves the
        loop doing exactly what it does when a runtime cannot start yet.
        """
        self._note("admit")
        raise ContractRefusal("refused", "precondition",
                              "this fixture composition starts no runtime")

    def observe(self, stage):
        """An UNCLAIMED stage, in the projection's own vocabulary.

        Not None: `delegation._bound` owns this document and refuses "a
        canonical observation is one exact document; this is none". A fake
        that answered None made every case report `submission-failed` for a
        reason that had nothing to do with the submission -- which is itself
        a small demonstration of why R3 asked for the orchestration to be
        driven rather than reasoned about.
        """
        self._note("observe")
        return {"claimed_by": None, "runtime": None, "activity": None,
                "output": None, "start_failure": None,
                "preparation_failure": None, "exchange": None}

    def cancel_attempt(self, *, attempt_id, reason, **operands):
        self._note("cancel_attempt")
        return {"attempt_id": attempt_id, "requested": True,
                "why": "the composition was asked and answered",
                "execution_runtime": "destroyed"}

    def __getattr__(self, name):
        def answer(*a, **k):
            self._note(name)
            return None
        return answer


class SupervisionCase(unittest.TestCase):
    """The orchestration itself, driven over real stores.

    Review 2026-09-23T11:30:47Z R3: none of the delivered tests called
    `supervise`, so the 381 lines that ORDER the imported helpers were
    unverified. These drive it.
    """

    AUTHORITY = "0123456789abcdef0123456789abcdef"
    JOB = "job-independent-review-239533"
    NOW = "2026-09-23T00:00:00.000Z"

    def setUp(self):
        import tempfile

        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        from tests.job_manager import fixtures

        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = self.temporary.name
        self.submission_document = {
            "schema": "baton.v12.job-submission/2",
            "submission_id": "review-submission",
            "jobs": [dict(
                fixtures.job(
                    self.JOB, input_digest=fixtures.INPUT_DIGEST,
                    policy_digest=fixtures.POLICY_DIGEST,
                    stages=[fixtures.stage("review", fixtures.WORK_A)]),
                execution_limits={"provider_turn_seconds": 180})]}
        self.submission = os.path.join(self.root, "submission.json")
        with open(self.submission, "w", encoding="utf-8") as handle:
            json.dump(self.submission_document, handle, sort_keys=True)
        self.outcome = os.path.join(self.root, "outcome.json")
        self.job = JobStore.open(
            os.path.join(self.root, "jobs.sqlite3"),
            authority_uuid=self.AUTHORITY, incarnation="review-1",
            clock=lambda: self.NOW)
        self.addCleanup(self.job.close)
        self.control = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="review-1", clock=lambda: self.NOW)
        self.addCleanup(self.control.close)
        self.ticks = [0.0]

    def monotonic(self):
        """A clock this case advances, so a bound is exercised rather than
        waited for."""
        self.ticks[0] += 1.0
        return self.ticks[0]

    def packet(self, **overrides):
        held = {
            "run_id": "independent-review-239533", "work": "W239533",
            "claim": 247318,
            "subject": {"line_id": "line-a", "checkpoint_id": "checkpoint-a",
                        "base_object": "1" * 40, "head_object": "2" * 40,
                        "tree_object": "3" * 40,
                        "producer": {"worker_id": "implementation-worker",
                                     "participant": "baton.impl",
                                     "principal": "principal:baton.impl"}},
            "submission": {"path": self.submission, "job_id": self.JOB},
            "bounds": {"turn_seconds": 180, "total_seconds": 30,
                       "cleanup_seconds": 10, "review_invocations": 1,
                       "retry": False},
            "deployment": {"authority_uuid": self.AUTHORITY},
            "retention": None,
            "outcome_path": self.outcome}
        held.update(overrides)
        return held

    def drive(self, operations=None, *, sleep=None, packet=None):
        operations = Serving() if operations is None else operations
        held = self.packet() if packet is None else packet
        outcome = review_supervisor.supervise(
            self.job, self.control, operations, held,
            clock=lambda: self.NOW,
            sleep=(lambda _s: None) if sleep is None else sleep,
            monotonic=self.monotonic)
        return outcome, operations

    def published(self):
        with open(self.outcome, encoding="utf-8") as handle:
            return json.load(handle)


class TheOrchestrationIsDrivenEndToEnd(SupervisionCase):
    def test_a_run_that_starts_nothing_stops_at_its_serving_bound(self):
        """And `no-progress` deliberately does NOT fire here.

        The detector requires something accountable: "a stage that cannot
        advance while every runtime it started is already positively
        excluded". This fixture composition starts no runtime, so there is
        nothing positively excluded and the honest stop is the backstop. The
        no-progress rule needs an admitted runtime to be exercised, which
        needs a composition that completes an admit through to a journalled
        operation -- stated here rather than faked, because a fake that
        answered an admit it could not finish made the NEXT sweep refuse for
        the fixture's reason instead of the run's.
        """
        outcome, operations = self.drive()
        self.assertEqual(outcome["stopped"], "overall-bound-exceeded")
        self.assertEqual(outcome["stalled_ticks"], 0)
        self.assertEqual(outcome["state"], "held")
        # A RUN THAT ADMITTED NOTHING SAYS SO rather than calling itself done.
        self.assertTrue(any("answered nothing about the reviewer" in one
                            for one in outcome["held_because"]),
                        outcome["held_because"])
        self.assertEqual(self.published()["stopped"],
                         "overall-bound-exceeded")

    def test_exactly_one_review_is_admitted_over_a_whole_drive(self):
        """The cap, measured over the real serving loop rather than the gate.

        `AdmissionIsBoundedAtTheGate` asks the imported gate directly. This
        asks the question the packet actually makes: over a whole run, with
        the loop sweeping until it stops, how many times was the composition
        asked to admit? Once -- and the outcome's own count agrees with the
        calls the composition recorded.
        """
        outcome, operations = self.drive()
        # THE GATE LET THE REVIEW THROUGH TO THE COMPOSITION. The gate refuses
        # by kind and by cap before delegating, so reaching the composition at
        # all is the measurement that a `review` stage is this packet's own.
        self.assertGreaterEqual(operations.calls.count("admit"), 1,
                                operations.calls)
        # AND THE GATE ITSELF REFUSED NOTHING: no cap was spent, because the
        # fixture composition defers rather than starting a runtime, and a
        # refused admission is not an invocation.
        self.assertEqual(outcome["gate_refusals"], [])
        self.assertEqual(outcome["admissions"], {"review": 0})
        # NOTHING OF ANOTHER KIND. An implementation admission here would be
        # W239528's or W236087's workload arriving in this run.
        self.assertEqual(outcome["foreign_admissions"], [])
        self.assertEqual(outcome["admitted_attempts"], [])

    def test_the_cleanup_reserve_stays_inside_the_overall_bound(self):
        """300 total with 60 reserved must not spend 360.

        The injected monotonic advances one second per read, so the elapsed
        figures below are tick counts and the arithmetic is exact.
        """
        outcome, _ = self.drive()
        bounds = self.packet()["bounds"]
        self.assertEqual(outcome["serving_bound_seconds"],
                         bounds["total_seconds"] - bounds["cleanup_seconds"])
        self.assertLessEqual(outcome["served_seconds"],
                             bounds["total_seconds"])
        self.assertLess(self.ticks[0],
                        bounds["total_seconds"] + bounds["cleanup_seconds"])

    def test_a_serving_failure_still_publishes_an_outcome(self):
        outcome, _ = self.drive(Serving(failing=("attach",)))
        self.assertEqual(outcome["stopped"], "serving-failed")
        self.assertIn("RuntimeError", outcome["serving_failure"])
        self.assertTrue(any("did not end cleanly" in one
                            for one in outcome["held_because"]))
        self.assertEqual(self.published()["stopped"], "serving-failed")

    def test_a_submission_that_refuses_still_publishes_an_outcome(self):
        """The path R3 named: the owner acts sat outside the publishing region.

        A colliding Job identity is the real shape of it -- `submit` refuses,
        "one Job identity names one pipeline" -- and before this fix the
        function escaped with nothing on disk.
        """
        from baton_v12.job_manager import read_submission, submit

        # A DIFFERENT SUBMISSION NAMING THE SAME JOB. Re-submitting the same
        # document REPLAYS -- which is the contract -- so the collision has to
        # be a second submission identity over one Job identity, which is what
        # "one Job identity names one pipeline" refuses.
        with open(self.submission, encoding="utf-8") as handle:
            held = json.loads(handle.read())
        submit(self.job, read_submission(json.dumps(
            dict(held, submission_id="somebody-elses-submission"),
            sort_keys=True)))
        outcome, _ = self.drive()
        self.assertEqual(outcome["stopped"], "submission-failed")
        self.assertIsNotNone(outcome["submission_failure"])
        self.assertTrue(any("the submission did not complete" in one
                            for one in outcome["held_because"]),
                        outcome["held_because"])
        self.assertTrue(os.path.exists(self.outcome))

    def test_an_interrupt_during_the_first_owner_act_still_publishes(self):
        """R3a, reproduced the way the reviewer reproduced it.

        The real public `submit` is wrapped, allowed to COMMIT, and then the
        interrupt is injected. Before the fix the submission guard caught
        `Exception` only, so a `KeyboardInterrupt` -- which the installed
        handler raises and which is not an `Exception` -- escaped through
        `supervise`'s `finally`, which only restores handlers. One stage
        stayed committed and no outcome reached disk.
        """
        from unittest import mock

        from baton_v12.job_manager import submit as real_submit
        import baton_v12.job_manager as job_manager

        committed = []

        def submitting(store, document):
            answer = real_submit(store, document)
            committed.append(answer["submission_id"])
            raise KeyboardInterrupt("operator stopped the run")

        with mock.patch.object(job_manager, "submit", submitting):
            with self.assertRaises(
                    review_supervisor.SupervisorInterrupted) as got:
                self.drive()
        # THE STAGE REALLY DID COMMIT, so this is the window that mattered.
        self.assertEqual(committed, ["review-submission"])
        outcome = got.exception.outcome
        self.assertEqual(outcome["stopped"], "interrupted")
        self.assertIn("KeyboardInterrupt", outcome["interrupted"])
        self.assertIn("KeyboardInterrupt", outcome["submission_failure"])
        self.assertTrue(os.path.exists(self.outcome),
                        "the outcome was lost with a committed stage behind it")
        self.assertEqual(self.published()["stopped"], "interrupted")
        # AND THE ACCOUNTING STILL RAN, rather than being skipped with the
        # interrupt. `final_canonical_read` is the precondition of a truthful
        # answer about what was left behind.
        self.assertIn("final_canonical_read", outcome)

    def test_an_interruption_publishes_the_outcome_and_still_raises(self):
        def interrupting(_seconds):
            raise KeyboardInterrupt("operator stopped the run")

        with self.assertRaises(review_supervisor.SupervisorInterrupted) as got:
            self.drive(sleep=interrupting)
        # THE OUTCOME TRAVELS ON `.outcome`, not in `args`.
        # `SupervisorInterrupted.__init__` passes only the reason to
        # `BaseException` and keeps the retained outcome as an attribute --
        # "the retained outcome travels on `.outcome` so a caller that does
        # want to read what the run left behind can, without the interrupt
        # being swallowed". Reading `args[1]` was this case assuming a shape
        # instead of reading the one the class documents.
        outcome = got.exception.outcome
        self.assertEqual(outcome["stopped"], "interrupted")
        self.assertIn("KeyboardInterrupt", outcome["interrupted"])
        self.assertEqual(outcome["state"], "held")
        published = self.published()
        self.assertEqual(published["interrupted"], outcome["interrupted"])

    def test_an_outcome_is_published_on_every_path(self):
        """The one invariant that holds across all of the above."""
        for name, operands in (
                ("quiet", {}),
                ("serving", {"operations": Serving(
                    failing=("attach",))})):
            with self.subTest(path=name):
                self.setUp()
                self.drive(**operands)
                self.assertTrue(os.path.exists(self.outcome))
                self.assertIn("held_because", self.published())


class TheRunReportsWhatItCouldNotPrevent(SupervisionCase):
    """R4, at the width the product actually supports.

    A correction round opened by `StageComposition.routed` is not something a
    supervisor can decline -- `review_supervisor.CORRECTION_LIMITATION` states
    exactly why -- so the run HOLDS rather than redefining its scope.
    """

    def test_an_implementation_stage_in_this_job_holds_the_run(self):
        from baton_v12.job_manager import read_submission, submit
        from tests.job_manager import fixtures

        document = dict(
            self.submission_document,
            jobs=[dict(
                fixtures.job(
                    self.JOB, input_digest=fixtures.INPUT_DIGEST,
                    policy_digest=fixtures.POLICY_DIGEST,
                    stages=[fixtures.stage("review", fixtures.WORK_A),
                            fixtures.stage("implementation",
                                           fixtures.WORK_A)]),
                execution_limits={"provider_turn_seconds": 180})])
        with open(self.submission, "w", encoding="utf-8") as handle:
            json.dump(document, handle, sort_keys=True)
        outcome, _ = self.drive()
        self.assertTrue(outcome["correction_rounds_opened"],
                        "the Job's own stage records were not read")
        self.assertTrue(
            any("a correction round was opened" in one
                for one in outcome["held_because"]), outcome["held_because"])
        self.assertIn("open_correction", outcome["correction_limitation"])

    def test_the_limitation_names_the_boundary_that_now_closes_it(self):
        """The limitation text moved when the product change closed it.

        It used to say the round could not be prevented and that the fix
        belonged to the owning implementation scope. Owner selection 247421
        made that change, so the text now names the boundary instead -- and a
        round appearing ANYWAY is a fault worth holding on rather than a state
        to accommodate.
        """
        said = review_supervisor.CORRECTION_LIMITATION
        self.assertIn("StageComposition.routed", said)
        self.assertIn("open_correction", said)
        self.assertIn("correction_policy", said)
        self.assertIn("did not hold", said)


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if isinstance(value, type) and issubclass(value, unittest.TestCase) \
                and value.__module__ == __name__ \
                and name not in ("PacketCase", "SupervisionCase"):
            suite.addTests(loader.loadTestsFromTestCase(value))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
