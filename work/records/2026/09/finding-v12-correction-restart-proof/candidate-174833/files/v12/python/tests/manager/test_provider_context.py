"""Selected A: real owner journals and files; deterministic boundary providers.

No production CLI qualification, serving enablement or live engine is claimed.
"""
import copy
import json
import os
import pathlib
import tempfile
import threading
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.job_manager import JobStore, submit
from baton_v12.job_manager import episodes, submission
from baton_v12.worker_manager import (AuthorityPort, ControlStore, accept_offer, activate_assignment, certify_profile, create_line, grant_writer, issue_offer, record_attempt, submit_claim)
from baton_v12.worker_manager import provider_context as context
from baton_v12.worker_manager import context_delivery as delivery
from baton_v12.worker_manager.source_boundary import nominate_source
from baton_v12.worker_manager.workspaces import configure_workspace_storage
from tests.manager import input_roots
from tests.manager.disk_roots import disk_backed_under
from tests.manager.test_offers import FakeSession, NOW, UUID, WORK, WHO, PROFILE, fake_claim_signature
from tests.job_manager.fixtures import job, stage
from tests.job_manager.test_review_driver import Profile


UUID = "0000000a" + "0" * 24


def profile(**changed):
    result = {"schema": context.PROFILE_SCHEMA, "qualification": "deterministic", "evidence_digest": "sha256:" + "e" * 64, "cli_build": "deterministic-claude-layout", "image_digest": "sha256:" + "a" * 64, "adapter_digest": "sha256:" + "d" * 64, "runtime_profile_digest": PROFILE, "model": "deterministic-model", "reported_model": "deterministic-model", "argv_policy_digest": "sha256:" + "3" * 64, "environment_policy_digest": "sha256:" + "4" * 64, "layout_version": "deterministic-layout/1", "cwd": "/output", "state_paths": [".claude/projects/output/session.json"], "max_entries": 64, "max_bytes": 4096, "retention_policy_digest": "sha256:" + "9" * 64}
    result.update(changed)
    return result


class ContextSession(FakeSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discharge_answer["kind"] = "runtime-absent"

    def cancel(self, operands):
        answer = super().cancel(operands)
        self._work = dict(self._work, gate=answer["gate"], phase="block")
        self.live_assignment = None
        return answer


class ContextCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="v12-context-")
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.path = str(self.root / "control.sqlite3")
        self.control = ControlStore.open(self.path, incarnation="context-1", clock=lambda: NOW)
        self.addCleanup(self.control.close)
        self.store = self.control
        self.storage = pathlib.Path(disk_backed_under(self)) / "workspaces"
        self.storage.mkdir(mode=0o700)
        configure_workspace_storage(self.control, str(self.storage))
        input_roots.configured_group(self.control)
        self.source = self.root / "source"
        self.source.mkdir(mode=0o700)
        self.private = self.root / "contexts"
        self.private.mkdir(mode=0o700)
        self.custody = delivery.configure_context_storage(self.control, str(self.private), excluded_roots=[str(self.source), str(self.storage)], runtime_uid=os.getuid())
        self.jobs = JobStore.open(str(self.root / "jobs.sqlite3"), authority_uuid=UUID, incarnation="jobs-1", clock=lambda: NOW)
        self.addCleanup(self.jobs.close)
        submit(self.jobs, {"schema": "baton.v12.job-submission/1", "submission_id": "context-submission", "jobs": [job("context-job", stages=[stage("implementation", WORK), stage("review", WORK)])]})
        self.stage = submission.stages_of(self.jobs, "context-job")[0]
        self.attempt_id = episodes.live_of(self.jobs, self.stage["stage_id"])["attempt_id"]
        self.session = ContextSession()
        self.session._work["authority_uuid"] = UUID
        self.session.live_assignment["work_ref"]["authority_uuid"] = UUID
        self.session.claim_answer["assignment"]["work_ref"]["authority_uuid"] = UUID
        self.port = AuthorityPort(self.session, fake_claim_signature)
        certify_profile(self.control, "runtime", "reference", PROFILE)
        self.profile = Profile()
        self.line = create_line(self.control, source=nominate_source(str(self.source)), declared_base="a" * 40, profile=self.profile, authority_uuid=UUID, work_id=WORK)
        self.profile_digest = context.certify_context_profile(self.control, profile())["profile_digest"]
        from baton_v12.worker_manager import retain_manifest
        given, assignment = input_roots.documents(work_ref={"authority_uuid": UUID, "work_id": WORK}, participant=WHO, generation=1, runtime_attempt_id=self.attempt_id, policy_digest="sha256:" + "2" * 64, profile_digest=PROFILE)
        declaration = copy.deepcopy(given["outputs"][0])
        declaration["name"] = "provider-context-receipt"
        declaration["path"] = "provider-context-receipt"
        declaration["constraints"]["allowed_media_types"] = ["application/json"]
        given["outputs"] = [declaration]
        given.pop("manifest_digest")
        given["manifest_digest"] = digest(given)
        self.given = given
        self.input_digest = retain_manifest(self.control, given, "inputManifest")["digest"]
        self.activate()

    def activate(self, *, generation=1, based=None, review=False):
        attempt = self.attempt_id
        offer = "context-offer-" + attempt
        self.generation = generation
        issue_offer(self.control, self.port, offer_id=offer, work_id=WORK, runtime_attempt_id=attempt, input_digest=self.input_digest, policy_digest="sha256:" + "2" * 64, profile_digest=PROFILE, profile_name="reference", mint_bearer=lambda: "context-bearer")
        accept_offer(self.control, self.port, offer_id=offer, decision="accept", bearer="context-bearer", now=NOW, runtime_attempt_id=attempt, work_ref={"authority_uuid": UUID, "work_id": WORK})
        record_attempt(self.control, attempt_id=attempt, adapter_name="deterministic", adapter_digest="sha256:" + "d" * 64, image_digest=profile()["image_digest"], profile_digest=PROFILE, input_digest=self.input_digest, policy_digest="sha256:" + "2" * 64)
        submit_claim(self.control, self.port, offer_id=offer)
        activate_assignment(self.control, self.port, attempt_id=attempt, expect=self.session.live_assignment)
        if review:
            from baton_v12.worker_manager import attach_review
            self.attachment = attach_review(self.control, checkpoint_id=based, attempt_id=attempt, generation=generation, reviewer_worker_id="independent-reviewer", profile=self.profile)
        else:
            self.writer = grant_writer(self.control, line_id=self.line["line_id"], attempt_id=attempt, generation=generation, worker_id="implementation-worker", profile=self.profile, based_checkpoint_id=based)

    def admit(self, control=None, **changed):
        arguments = dict(attempt_id=self.attempt_id, writer_id=self.writer["writer_id"], profile_digest=self.profile_digest)
        arguments.update(changed)
        return context.admit_context_use(control or self.control, self.jobs, self.port, **arguments)

    def delivered(self):
        self.admit()
        return delivery.materialize_context_use(self.control, self.custody, attempt_id=self.attempt_id)

    def state(self, delivered=None):
        delivered = delivered or self.delivered()
        home = pathlib.Path(delivered.home)
        state = home / profile()["state_paths"][0]
        state.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        # mkdir(parents=True) uses ambient permissions for intermediate dirs.
        (home / ".claude").chmod(0o700)
        (home / ".claude/projects").chmod(0o700)
        state.write_bytes(b'{"private":"remembered"}')
        state.chmod(0o600)
        return delivered, state


    def end_runtime(self, first=None, *, receipt_changes=None, review=False):
        """Ordinary public freeze/intake/retention/fence/cleanup with fake adapters.

        No owner receipts or materialized rows are inserted. The provider output
        is simulated; real owners validate and commit every resulting fact.
        """
        from baton_v12.contracts import canonical_text, digest_of_bytes
        from baton_v12.worker_manager import (request_runtime_start, reconcile_runtime, observe, request_freeze, request_intake, decide_retention, freeze_checkpoint, authorize_cleanup)
        from baton_v12.worker_manager import attempts, output
        from tests.manager.test_attempts import Adapter
        from tests.manager.test_output import Collector, sealed
        from tests.manager.test_intake import Custodian
        attempt = self.attempt_id
        inputs, unused = input_roots.composed(self, str(self.storage), given=self.given, work_ref={"authority_uuid": UUID, "work_id": WORK}, participant=self.session.participant, generation=self.generation, runtime_attempt_id=attempt)
        from baton_v12.job_manager import ending
        self.ending_stage = episodes.attempting(self.stage, episodes.live_of(self.jobs, self.stage["stage_id"]))
        self.ending_assignment = copy.deepcopy(self.session.live_assignment)
        ending.register_ending(self.jobs, self.ending_stage, assignment=self.ending_assignment, disposition="completed", terminal_manifest_digest="sha256:" + "c" * 64, retention_disposition="retain", retention_policy_digest=profile()["retention_policy_digest"])
        self.adapter = Adapter()
        request_runtime_start(self.control, self.adapter, attempt_id=attempt, inputs=inputs)
        reconcile_runtime(self.control, self.adapter, attempt_id=attempt)
        observe(self.control, attempt_id=attempt, axis="execution_runtime", value="quiescent")
        observe(self.control, attempt_id=attempt, axis="worker_disposition", value="completed")
        if not review:
            chain, admitted = context._use(self.control, attempt)
        receipt = {"schema": context.RECEIPT_SCHEMA, "context_id": first.context_id, "use_id": first.use_id, "attempt_id": attempt, "conversation_id": admitted["payload"]["conversation_id"], "profile_digest": self.profile_digest, "invocation_id": context._id("context-invocation", first.use_id), "status": 0, "complete": True, "model": profile()["model"], "observed_model": profile()["reported_model"], "terminal": "success", "cli_build": profile()["cli_build"], "mode": "open", "delivery_digest": first.digest, "input_digest": self.input_digest, "policy_digest": "sha256:" + "2" * 64} if not review else {"finding": "changes-requested"}
        receipt.update(receipt_changes or {})
        self.receipt_body = canonical_text(receipt).encode()
        entries = [{"path": "receipt.json", "bytes": len(self.receipt_body), "content_digest": digest_of_bytes(self.receipt_body)}]
        content = {"entries": entries, "entry_count": 1, "total_bytes": len(self.receipt_body), "tree_digest": digest(entries)}
        artifact = {"artifact_id": "context-artifact-" + attempt, "media_type": "application/json", "bytes": len(self.receipt_body), "content_digest": digest(entries), "locator": "file:///private/context-receipt-artifact"}
        result = sealed({"version": {"major": 1, "minor": 0}, "manifest_id": "context-result", "created_at": NOW, "extensions": {}, "schema": "baton.worker-manifest/result", "result_id": "context-result-" + attempt, "assignment_ref": self.session.live_assignment, "input_manifest_digest": self.input_digest, "policy_digest": "sha256:" + "2" * 64, "disposition": "completed", "outputs": [{"name": "provider-context-receipt", "type": "directory-result", "status": "present", "content_manifest": content, "artifact": artifact, "result_metadata": {}}], "evidence": [], "freeze_operation": dict(output.freeze_operation(attempts._require_attempt(self.control, attempt))), "manager_observed_at": NOW, "completion_manifest_digest": "sha256:" + "c" * 64})
        if review:
            outputs = []
            for name in ("findings", "logs"):
                one = copy.deepcopy(result["outputs"][0])
                one["name"] = name
                one["artifact"]["artifact_id"] = "review-" + name + "-" + attempt
                outputs.append(one)
            result = sealed(dict(result, outputs=outputs))
        request_freeze(self.control, self.port, Collector(result), attempt_id=attempt, disposition="completed")
        artifacts = [one["artifact"] for one in result["outputs"]]
        self.custodian = Custodian({"result_id": "context-result-" + attempt, "artifacts": [{"artifact_id": item["artifact_id"], "content_digest": item["content_digest"], "bytes": item["bytes"], "custody_locator": item["locator"]} for item in artifacts]})
        self.collected = request_intake(self.control, self.port, self.custodian, attempt_id=attempt)
        decide_retention(self.control, self.port, self.custodian, attempt_id=attempt, artifact_ids=[item["artifact_id"] for item in artifacts], disposition="retain", retention_policy_digest=profile()["retention_policy_digest"])
        self.session.fence_answer["assignment"] = dict(self.session.live_assignment)
        self.session.fence_answer["gate"] = "runtime-quiescence:" + str(self.generation)
        if review:
            from baton_v12.worker_manager import record_verdict
            self.verdict = record_verdict(self.control, attachment_id=self.attachment["attachment_id"], disposition="changes-requested", profile=self.profile, port=self.port)
        else:
            self.checkpoint = freeze_checkpoint(self.control, writer_id=self.writer["writer_id"], generation=self.generation, profile=self.profile, port=self.port)
        self.session.live_assignment = None
        self.cleanup = authorize_cleanup(self.control, self.port, self.custodian, attempt_id=attempt, retention_policy_digest=profile()["retention_policy_digest"])
        self.assertEqual(self.cleanup["state"], "absent")

    def finalize(self):
        return context.finalize_context_use(self.control, self.jobs, self.port, attempt_id=self.attempt_id, storage=self.custody, receipt_reader=lambda *args: self.receipt_body, checkpoint_reader=lambda *args: self.checkpoint["checkpoint_id"])


    def settle(self):
        from baton_v12.job_manager import ending
        from baton_v12.worker_manager import discharge_quiescence_gate
        discharge = discharge_quiescence_gate(self.control, self.port, attempt_id=self.attempt_id, retention_policy_digest=profile()["retention_policy_digest"])
        return ending.settle_ending(self.jobs, self.ending_stage, assignment=self.ending_assignment, evidence={"result_id": self.collected["result_id"], "manifest_digest": self.collected["manifest_digest"], "receipt_digest": self.collected["receipt_digest"], "gate_discharge": discharge["gate"]})

    def as_participant(self, participant, generation, principal):
        from tests.manager.test_offers import decision
        self.session = ContextSession(participant=participant)
        self.session._work["authority_uuid"] = UUID
        self.session.live_assignment = {"work_ref": {"authority_uuid": UUID, "work_id": WORK}, "participant": participant, "generation": generation}
        self.session.claim_answer = {"assignment": copy.deepcopy(self.session.live_assignment), "claim_event": generation, "decision": decision(participant=participant, principal=principal)}
        self.port = AuthorityPort(self.session, fake_claim_signature)

    def correction(self, *, finalize=True, next_principal="principal:org-a"):
        first, state = self.state()
        self.end_runtime(first)
        if finalize:
            self.finalize()
        # The first ending is settled by its real public owner and names the
        # actual accepted intake and gate-discharge records, never fake rows.
        self.settle()
        first_attempt = self.attempt_id
        self.first_writer = self.writer
        self.first_checkpoint = self.checkpoint
        self.first_receipt_body = self.receipt_body
        self.stage = submission.stages_of(self.jobs, "context-job")[1]
        self.attempt_id = episodes.live_of(self.jobs, self.stage["stage_id"])["attempt_id"]
        self.as_participant("baton.context-reviewer", 2, "principal:independent-reviewer")
        from baton_v12.worker_manager import retain_manifest
        self.first_given, self.first_input_digest = self.given, self.input_digest
        self.given = copy.deepcopy(self.given)
        self.given["outputs"] = [dict(self.given["outputs"][0], name=name, path=name) for name in ("findings", "logs")]
        self.given.pop("manifest_digest")
        self.given["manifest_digest"] = digest(self.given)
        self.input_digest = retain_manifest(self.control, self.given, "inputManifest")["digest"]
        self.activate(generation=2, based=self.checkpoint["checkpoint_id"], review=True)
        self.end_runtime(review=True)
        self.settle()
        corrected = episodes.advance_correction(self.jobs, self.control, job_id="context-job", line_id=self.line["line_id"], checkpoint_id=self.checkpoint["checkpoint_id"], verdict_id=self.verdict["verdict_id"])
        self.stage = submission.stages_of(self.jobs, "context-job")[0]
        self.attempt_id = corrected["implementation"]["attempt_id"]
        self.as_participant(WHO, 3, next_principal)
        self.given, self.input_digest = self.first_given, self.first_input_digest
        self.activate(generation=3, based=self.checkpoint["checkpoint_id"])
        return first, first_attempt


class Admission(ContextCase):
    def test_admission_is_replayed_after_reopen_without_another_authority_read(self):
        first = self.admit()
        self.session.live_assignment = None
        again = ControlStore.open(self.path, incarnation="context-2", clock=lambda: NOW)
        self.addCleanup(again.close)
        with mock.patch.object(self.port, "assignment_of", side_effect=AssertionError("historical replay made a live call")):
            self.assertEqual(first, self.admit(again))
        self.assertEqual(first["status"], "admitted")

    def test_missing_live_assignment_refuses_before_any_context_transition(self):
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal):
            self.admit()
        self.assertEqual(context._history(self.control), {})

    def test_changed_profile_cannot_reinterpret_an_admitted_use(self):
        self.admit()
        changed = context.certify_context_profile(self.control, profile(model="other-model"))["profile_digest"]
        with self.assertRaises(ContractRefusal):
            self.admit(profile_digest=changed)

    def test_wrong_writer_refuses(self):
        with self.assertRaises(ContractRefusal):
            self.admit(writer_id="other-writer")

    def test_replaced_repository_refuses_before_admission(self):
        from baton_v12.worker_manager import line_of
        line = pathlib.Path(line_of(self.control, self.line["line_id"])["line_path"])
        line.rename(line.with_name(line.name + "-old"))
        line.mkdir(mode=0o700)
        with self.assertRaises(ContractRefusal):
            self.admit()

    def test_two_connections_commit_one_admission(self):
        # SQLite handles are opened in their owning threads. Both requests see
        # the same real Job, assignment and grant; no ready row is fabricated.
        barrier = threading.Barrier(2)
        results = []
        errors = []
        def run(number):
            try:
                with ControlStore.open(self.path, incarnation="racer-" + str(number), clock=lambda: NOW) as control:
                    with JobStore.open(str(self.root / "jobs.sqlite3"), authority_uuid=UUID, incarnation="job-racer-" + str(number), clock=lambda: NOW) as jobs:
                        barrier.wait(timeout=5)
                        result = context.admit_context_use(control, jobs, self.port, attempt_id=self.attempt_id, writer_id=self.writer["writer_id"], profile_digest=self.profile_digest)
                        results.append(result)
            except BaseException as error:
                errors.append(error)
        threads = [threading.Thread(target=run, args=(n,)) for n in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], results[1])
        self.assertEqual(len(context._history(self.control, results[0]["context_id"])), 1)

    def test_observation_is_pure_and_contains_no_private_locator(self):
        use = self.admit()
        before = self.control._connection.total_changes
        observed = context.context_of(self.control, use["context_id"])
        self.assertEqual(self.control._connection.total_changes, before)
        self.assertNotIn(str(self.root), json.dumps(observed))
        self.assertNotIn("conversation_id", observed)

    def test_unknown_use_stays_held(self):
        self.admit()
        first = context.hold_context_use(self.control, attempt_id=self.attempt_id, reason="invocation-unknown", evidence_refs=[])
        self.assertEqual(first, context.hold_context_use(self.control, attempt_id=self.attempt_id, reason="invocation-unknown", evidence_refs=[]))
        with self.assertRaises(ContractRefusal):
            delivery.materialize_context_use(self.control, self.custody, attempt_id=self.attempt_id)

    def test_missing_owner_cleanup_never_reads_the_receipt(self):
        self.delivered()
        with self.assertRaises(ContractRefusal):
            context.finalize_context_use(self.control, self.jobs, self.port, attempt_id=self.attempt_id, storage=self.custody, receipt_reader=lambda *args: self.fail("read before exclusion"), checkpoint_reader=lambda *args: self.fail("checkpoint before exclusion"))


class Profiles(unittest.TestCase):
    def test_production_qualification_cannot_be_asserted_by_a_profile_label(self):
        with self.assertRaises(ContractRefusal):
            context._profile(profile(qualification="production"))

    def test_closed_profile_rejects_wrong_types_and_unsafe_paths(self):
        for changed in ({"max_entries": True}, {"max_bytes": 2**60}, {"state_paths": [["nested"]]}, {"state_paths": [".claude/../credentials"]}, {"state_paths": [".claude/projects/.credentials.json"]}, {"cwd": "/other"}, {"healthy": True}):
            with self.subTest(changed=changed), self.assertRaises(ContractRefusal):
                context._profile(profile(**changed))


class Finalization(ContextCase):
    def test_positive_generation_is_published_and_replayed_after_fence(self):
        first, state = self.state()
        self.end_runtime(first)
        with mock.patch.object(self.port, "assignment_of", side_effect=AssertionError("historical finalize asked for authority")):
            ready = self.finalize()
            self.assertEqual(ready["status"], "ready")
            self.assertEqual(ready, self.finalize())
        self.assertEqual(len(self.adapter.started), 1)
        self.assertEqual(len(list((self.private / first.context_id / "generations").iterdir())), 1)

    def test_wrong_actual_model_receipt_cannot_publish_a_generation(self):
        first, state = self.state()
        self.end_runtime(first, receipt_changes={"model": "other-model"})
        with self.assertRaises(ContractRefusal):
            self.finalize()
        self.assertFalse((self.private / first.context_id / "generations").exists())

    def test_crash_after_publication_before_journal_replays_only_custody(self):
        first, state = self.state()
        self.end_runtime(first)
        original = context._transition
        def cut(*args, **kwargs):
            if kwargs["action"] == "finalize":
                raise RuntimeError("publication cut")
            return original(*args, **kwargs)
        with mock.patch.object(context, "_transition", side_effect=cut), self.assertRaisesRegex(RuntimeError, "publication cut"):
            self.finalize()
        self.assertEqual(context.context_use_of(self.control, self.attempt_id)["status"], "admitted")
        self.assertEqual(self.finalize()["status"], "ready")
        self.assertEqual(len(self.adapter.started), 1)

    def test_crash_during_staging_reuses_only_matching_private_bytes(self):
        first, state = self.state()
        self.end_runtime(first)
        original = delivery._write
        def cut(parent, name, body, **kwargs):
            if name == "manifest":
                raise RuntimeError("staging cut")
            return original(parent, name, body, **kwargs)
        with mock.patch.object(delivery, "_write", side_effect=cut), self.assertRaisesRegex(RuntimeError, "staging cut"):
            self.finalize()
        self.assertEqual(self.finalize()["status"], "ready")
        self.assertEqual(len(self.adapter.started), 1)

    def test_damaged_committed_generation_is_refused(self):
        first, state = self.state()
        self.end_runtime(first)
        self.finalize()
        target = self.private / first.context_id / "generations/1/state" / profile()["state_paths"][0]
        target.chmod(0o600)
        target.write_bytes(b"damaged")
        with self.assertRaises(ContractRefusal):
            self.finalize()

    def test_disposal_preserves_generation_and_invocation_evidence(self):
        first, state = self.state()
        pathlib.Path(first.invocation).write_text("synthetic invocation evidence")
        self.end_runtime(first)
        self.finalize()
        result = delivery.discard_context_use(self.control, self.custody, attempt_id=self.attempt_id)
        self.assertTrue(result["discarded"])
        self.assertEqual(result, delivery.discard_context_use(self.control, self.custody, attempt_id=self.attempt_id))
        self.assertEqual(list(pathlib.Path(first.home).iterdir()), [])
        self.assertTrue(pathlib.Path(first.invocation).exists())
        self.assertEqual(self.finalize()["status"], "ready")


class Restoration(ContextCase):
    def test_actual_correction_admits_a_fresh_copy_with_the_same_conversation(self):
        first, first_attempt = self.correction()
        second = self.admit()
        self.assertNotEqual(first.use_id, second["use_id"])
        delivered = delivery.materialize_context_use(self.control, self.custody, attempt_id=self.attempt_id)
        source = self.private / first.context_id / "generations/1/state" / profile()["state_paths"][0]
        target = pathlib.Path(delivered.home) / profile()["state_paths"][0]
        self.assertEqual(source.read_bytes(), target.read_bytes())
        self.assertNotEqual(source.stat().st_ino, target.stat().st_ino)
        self.assertFalse(pathlib.Path(delivered.invocation).exists())
        target.write_bytes(b"corrected private context")
        self.assertNotEqual(source.read_bytes(), target.read_bytes())
        self.assertEqual(context._use(self.control, first_attempt)[1]["payload"]["conversation_id"], context._use(self.control, self.attempt_id)[1]["payload"]["conversation_id"])

    def test_competing_restore_refusal_does_not_consume_incumbent_finalization(self):
        first, first_attempt = self.correction(finalize=False)
        with self.assertRaises(ContractRefusal):
            self.admit()
        refused_attempt, refused_writer = self.attempt_id, self.writer
        self.attempt_id = first_attempt
        self.receipt_body = self.first_receipt_body
        self.writer = self.first_writer
        self.assertEqual(self.finalize()["status"], "ready")
        # The exact refused request stays refused; it is never silently admitted
        # by changing its operation id after its predecessor has advanced.
        self.attempt_id, self.writer = refused_attempt, refused_writer
        with self.assertRaises(ContractRefusal) as replay:
            self.admit()

        self.assertTrue(replay.exception.durable)


class RemainingBoundaries(ContextCase):
    def test_actual_principal_change_cannot_inherit_the_existing_context(self):
        self.correction(next_principal="principal:replacement")
        with self.assertRaisesRegex(ContractRefusal, "context owner"):
            self.admit()

    def test_another_jobs_store_cannot_supply_this_episode(self):
        other = JobStore.open(str(self.root / "other-jobs.sqlite3"), authority_uuid=UUID, incarnation="other", clock=lambda: NOW)
        self.addCleanup(other.close)
        submit(other, {"schema": "baton.v12.job-submission/1", "submission_id": "other-submission", "jobs": [job("other-job", stages=[stage("implementation", WORK)])]})
        with self.assertRaises(ContractRefusal):
            context.admit_context_use(self.control, other, self.port, attempt_id=self.attempt_id, writer_id=self.writer["writer_id"], profile_digest=self.profile_digest)

    def test_a_foreign_live_actor_is_refused(self):
        self.session.live_assignment["participant"] = "baton.someone-else"
        with self.assertRaises(ContractRefusal):
            self.admit()

    def test_original_context_survives_removal_of_generic_execution_roots(self):
        from baton_v12.worker_manager.workspaces import discard_execution_roots
        first, state = self.state()
        self.end_runtime(first)
        discard_execution_roots(str(self.storage), self.attempt_id)
        self.assertTrue(state.is_file())
        with mock.patch.object(self.port, "assignment_of", side_effect=AssertionError("ending attempted admission")):
            self.assertEqual(self.finalize()["status"], "ready")

    def test_damage_is_observed_as_a_hold_without_mutating_the_store(self):
        first, state = self.state()
        self.end_runtime(first)
        self.finalize()
        path = self.private / first.context_id / "generations/1/state" / profile()["state_paths"][0]
        path.chmod(0o600)
        path.write_bytes(b"damaged")
        before = self.control._connection.total_changes
        observed = context.context_of(self.control, first.context_id)
        self.assertEqual(observed["status"], "held")
        self.assertEqual(observed["reason"], "generation-damaged")
        self.assertEqual(self.control._connection.total_changes, before)

    def test_unknown_file_in_staging_cannot_enter_a_generation(self):
        first, state = self.state()
        self.end_runtime(first)
        original = delivery._copy
        def extra(parent, entries, **kwargs):
            original(parent, entries, **kwargs)
            fd = os.open("unexpected", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent)
            os.close(fd)
        with mock.patch.object(delivery, "_copy", side_effect=extra), self.assertRaises(ContractRefusal):
            self.finalize()
        self.assertEqual(context.context_of(self.control, first.context_id)["status"], "held")

    def test_a_replaced_generation_with_identical_bytes_is_still_not_the_original(self):
        import shutil
        first, state = self.state()
        self.end_runtime(first)
        self.finalize()
        path = self.private / first.context_id / "generations/1"
        path.rename(path.with_name("old-generation"))
        shutil.copytree(path.with_name("old-generation"), path)
        with self.assertRaises(ContractRefusal):
            self.finalize()

    def test_retirement_cannot_release_an_unknown_writer(self):
        use = self.admit()
        context.hold_context_use(self.control, attempt_id=self.attempt_id, reason="invocation-unknown", evidence_refs=[])
        with self.assertRaises(ContractRefusal):
            context.retire_context(self.control, use["context_id"])

    def test_unproven_receipt_bytes_cannot_replace_a_frozen_healthy_receipt(self):
        first, state = self.state()
        self.end_runtime(first)
        self.receipt_body = b"{}"
        with self.assertRaises(ContractRefusal):
            self.finalize()
        self.assertEqual(context.context_of(self.control, first.context_id)["reason"], "receipt-invalid")


    def test_actual_image_drift_refuses_before_admission(self):
        changed = context.certify_context_profile(self.control, profile(image_digest="sha256:" + "f" * 64))["profile_digest"]
        with self.assertRaisesRegex(ContractRefusal, "runtime profile or adapter"):
            self.admit(profile_digest=changed)
