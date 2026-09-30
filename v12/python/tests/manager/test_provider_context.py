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
from baton_v12.worker_manager import review_cycles
from baton_v12.worker_manager.store import manager_signature
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
        # Production is now a valid document vocabulary, but registering it
        # still requires independently backed certification in the owner store.
        with tempfile.TemporaryDirectory(prefix="context-profile-") as root:
            with ControlStore.open(str(pathlib.Path(root) / "control.sqlite3"), incarnation="profile", clock=lambda: NOW) as control:
                with self.assertRaisesRegex(ContractRefusal, "lacks recorded certification"):
                    context.certify_context_profile(control, profile(qualification="production"))

    def test_closed_profile_rejects_wrong_types_and_unsafe_paths(self):
        for changed in ({"max_entries": True}, {"max_bytes": 2**60}, {"state_paths": [["nested"]]}, {"state_paths": [".claude/../credentials"]}, {"state_paths": [".claude/projects/.credentials.json"]}, {"cwd": "/other"}, {"healthy": True}):
            with self.subTest(changed=changed), self.assertRaises(ContractRefusal):
                context._profile(profile(**changed))


class ConversationStatePaths(ContextCase):
    def test_only_admitted_uuid_expands_the_exact_filename(self):
        template = ".claude/projects/-output/{conversation_id}.jsonl"
        self.profile_digest = context.certify_context_profile(self.control, profile(schema=context.SESSION_PROFILE_SCHEMA, state_paths=[template]))["profile_digest"]
        self.admit()
        chain, admitted = context._use(self.control, self.attempt_id)
        resolved = delivery._state_profile(self.control, admitted)
        conversation = admitted["payload"]["conversation_id"]
        self.assertEqual(resolved["state_paths"], [".claude/projects/-output/" + conversation + ".jsonl"])
        self.assertEqual(context.context_profile_of(self.control, self.profile_digest)["state_paths"], [template])

    def test_historical_profile_keeps_marker_filename_literal(self):
        template = ".claude/projects/-output/{conversation_id}.jsonl"
        self.profile_digest = context.certify_context_profile(self.control, profile(state_paths=[template]))["profile_digest"]
        self.admit()
        chain, admitted = context._use(self.control, self.attempt_id)
        self.assertEqual(delivery._state_profile(self.control, admitted)["state_paths"], [template])

    def test_terminal_reader_refuses_duplicates_partial_nonfinite_and_nonobject(self):
        for raw in (b'{"type":"result","type":"result"}', b'{"model":', b'{"modelUsage":{"tokens":NaN}}', b'{"modelUsage":{"tokens":1e999}}', b'[]'):
            with self.subTest(raw=raw), self.assertRaises(ContractRefusal):
                context._terminal_result(raw)

    def test_templates_do_not_expand_directories_or_arbitrary_placeholders(self):
        for path in (".claude/projects/{conversation_id}/state.json", ".claude/projects/-output/{unknown}.jsonl", ".claude/projects/-output/prefix-{conversation_id}.jsonl", ".claude/projects/{x}/{conversation_id}.jsonl"):
            with self.subTest(path=path), self.assertRaises(ContractRefusal):
                context._profile(profile(schema=context.SESSION_PROFILE_SCHEMA, state_paths=[path]))


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
        discard_execution_roots(str(self.storage), self.attempt_id,
                                control=self.control)
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


class StagingRecovery(ContextCase):
    def cut_write(self, target, count):
        original = delivery._write
        write = os.write
        def selected(parent, name, body, **kwargs):
            if name != target:
                return original(parent, name, body, **kwargs)
            def cut(fd, remaining):
                if count:
                    write(fd, remaining[:count])
                raise RuntimeError("interrupted staged write")
            with mock.patch.object(os, "write", side_effect=cut):
                return original(parent, name, body, **kwargs)
        with mock.patch.object(delivery, "_write", side_effect=selected), self.assertRaisesRegex(RuntimeError, "interrupted staged write"):
            self.finalize()

    def check_recovery(self, target, count):
        first, state = self.state()
        source = state.read_bytes()
        pathlib.Path(first.invocation).write_bytes(b"original invocation witness")
        self.end_runtime(first)
        receipt = self.receipt_body
        self.cut_write(target, count)
        self.assertEqual(context.context_use_of(self.control, self.attempt_id)["status"], "admitted")
        staged = next((self.private / first.context_id / "staging").iterdir())
        partial = staged / ("state/" + profile()["state_paths"][0] if target == "session.json" else target)
        self.assertEqual(partial.stat().st_size, count)
        staged_inode = staged.stat().st_ino
        self.control.close()
        self.control = ControlStore.open(self.path, incarnation="recover-staging", clock=lambda: NOW)
        self.addCleanup(self.control.close)
        with mock.patch.object(self.port, "assignment_of", side_effect=AssertionError("recovery asked for a fresh assignment")):
            ready = self.finalize()
            changes = self.control._connection.total_changes
            self.assertEqual(self.finalize(), ready)
            self.assertEqual(self.control._connection.total_changes, changes)
        self.assertEqual(ready["status"], "ready")
        published = self.private / first.context_id / "generations/1"
        self.assertEqual(published.stat().st_ino, staged_inode)
        self.assertEqual((published / "state" / profile()["state_paths"][0]).read_bytes(), source)
        self.assertEqual(state.read_bytes(), source)
        self.assertEqual(self.receipt_body, receipt)
        self.assertEqual(pathlib.Path(first.invocation).read_bytes(), b"original invocation witness")
        self.assertEqual(len(self.adapter.started), 1)
        self.assertEqual(len([one for one in context._history(self.control, first.context_id) if one["action"] == "finalize"]), 1)

    def test_zero_state_write_recovers(self):
        self.check_recovery("session.json", 0)

    def test_partial_state_write_recovers(self):
        self.check_recovery("session.json", 3)

    def test_zero_identity_write_recovers(self):
        self.check_recovery("identity", 0)

    def test_partial_identity_write_recovers(self):
        self.check_recovery("identity", 3)

    def test_zero_manifest_write_recovers(self):
        self.check_recovery("manifest", 0)

    def test_partial_manifest_write_recovers(self):
        self.check_recovery("manifest", 3)

    def test_mismatching_staging_bytes_are_preserved_and_refused(self):
        first, state = self.state()
        self.end_runtime(first)
        self.cut_write("identity", 3)
        staged = next((self.private / first.context_id / "staging").iterdir())
        identity = staged / "identity"
        identity.write_bytes(b"foreign")
        with self.assertRaisesRegex(ContractRefusal, "existing custody file differs"):
            self.finalize()
        self.assertEqual(identity.read_bytes(), b"foreign")
        self.assertEqual(len(self.adapter.started), 1)

    def test_replaced_staging_objects_are_refused(self):
        first, state = self.state()
        self.end_runtime(first)
        self.cut_write("identity", 0)
        staged = next((self.private / first.context_id / "staging").iterdir())
        staged.rename(staged.with_name("original-staging"))
        staged.mkdir(mode=0o700)
        with self.assertRaisesRegex(ContractRefusal, "staging objects were replaced"):
            self.finalize()
        self.assertEqual(len(self.adapter.started), 1)

    def test_source_changes_after_interruption_are_refused(self):
        first, state = self.state()
        self.end_runtime(first)
        self.cut_write("manifest", 3)
        state.write_bytes(b"different excluded source")
        with self.assertRaisesRegex(ContractRefusal, "staging owner facts changed"):
            self.finalize()
        self.assertEqual(len(self.adapter.started), 1)

    def test_complete_write_before_freeze_recovers(self):
        first, state = self.state()
        self.end_runtime(first)
        original = os.fchmod
        def cut(fd, mode):
            if mode == 0o400:
                raise RuntimeError("before file freeze")
            return original(fd, mode)
        with mock.patch.object(os, "fchmod", side_effect=cut), self.assertRaisesRegex(RuntimeError, "before file freeze"):
            self.finalize()
        self.assertEqual(self.finalize()["status"], "ready")
        self.assertEqual(len(self.adapter.started), 1)

    def cut_staging_registration(self):
        original = self.control.transact
        def cut(operation, kind, *args, **kwargs):
            if kind == "provider-context.staging":
                raise RuntimeError("before staging registration")
            return original(operation, kind, *args, **kwargs)
        with mock.patch.object(self.control, "transact", side_effect=cut), self.assertRaisesRegex(RuntimeError, "before staging registration"):
            self.finalize()

    def test_empty_staging_before_registration_can_recover(self):
        first, state = self.state()
        self.end_runtime(first)
        self.cut_staging_registration()
        self.assertEqual(self.finalize()["status"], "ready")
        self.assertEqual(len(self.adapter.started), 1)

    def test_unregistered_nonempty_staging_is_preserved_and_refused(self):
        first, state = self.state()
        self.end_runtime(first)
        self.cut_staging_registration()
        staged = next((self.private / first.context_id / "staging").iterdir())
        identity = staged / "identity"
        identity.write_bytes(b"foreign staging")
        with self.assertRaisesRegex(ContractRefusal, "unowned staging is not empty"):
            self.finalize()
        self.assertEqual(identity.read_bytes(), b"foreign staging")
        self.assertEqual(len(self.adapter.started), 1)


class GenerationIdentity(ContextCase):
    def check_damage(self, damage, *, before_commit=False):
        first, state = self.state()
        self.end_runtime(first)
        if before_commit:
            original = context._transition
            def cut(*args, **kwargs):
                if kwargs["action"] == "finalize":
                    raise RuntimeError("published before journal")
                return original(*args, **kwargs)
            with mock.patch.object(context, "_transition", side_effect=cut), self.assertRaisesRegex(RuntimeError, "published before journal"):
                self.finalize()
        else:
            self.finalize()
        generation = self.private / first.context_id / "generations/1"
        identity = generation / "identity"
        original_bytes = identity.read_bytes()
        if damage == "wrong":
            identity.chmod(0o600)
            value = json.loads(original_bytes)
            value["use_id"] = "foreign-use"
            identity.write_text(json.dumps(value))
            identity.chmod(0o400)
        elif damage == "exclusion":
            identity.chmod(0o600)
            value = json.loads(original_bytes)
            value["exclusion_digest"] = "sha256:" + "0" * 64
            identity.write_text(json.dumps(value))
            identity.chmod(0o400)
        elif damage == "mode":
            identity.chmod(0o600)
        elif damage in ("missing", "symlink", "directory"):
            generation.chmod(0o700)
            identity.unlink()
            if damage == "symlink":
                identity.symlink_to(state)
            elif damage == "directory":
                identity.mkdir(mode=0o400)
            generation.chmod(0o500)
        elif damage == "hardlink":
            os.link(identity, self.root / "foreign-identity-link")
        elif damage == "oversized":
            identity.chmod(0o600)
            identity.write_bytes(b"x" * 1025)
            identity.chmod(0o400)
        else:
            self.fail("unknown damage")
        before = self.control._connection.total_changes
        observed = context.context_of(self.control, first.context_id)
        self.assertEqual(self.control._connection.total_changes, before)
        self.assertEqual(observed["status"], "admitted" if before_commit else "held")
        with self.assertRaises(ContractRefusal):
            self.finalize()
        self.assertEqual(context.context_of(self.control, first.context_id)["status"], "held")
        self.assertEqual(len(self.adapter.started), 1)
        self.assertEqual(len([one for one in context._history(self.control, first.context_id) if one["action"] == "finalize"]), 0 if before_commit else 1)

    def test_wrong_use_is_not_ready(self):
        self.check_damage("wrong")

    def test_wrong_exclusion_is_not_ready(self):
        self.check_damage("exclusion")

    def test_missing_identity_is_not_ready(self):
        self.check_damage("missing")

    def test_writable_identity_is_not_ready(self):
        self.check_damage("mode")

    def test_symlink_identity_is_not_ready(self):
        self.check_damage("symlink")

    def test_directory_identity_is_not_ready(self):
        self.check_damage("directory")

    def test_hardlink_identity_is_not_ready(self):
        self.check_damage("hardlink")

    def test_oversized_identity_is_not_ready(self):
        self.check_damage("oversized")

    def test_publication_replay_refuses_wrong_identity(self):
        self.check_damage("wrong", before_commit=True)

    def test_publication_replay_refuses_wrong_exclusion(self):
        self.check_damage("exclusion", before_commit=True)

    def test_publication_replay_refuses_missing_identity(self):
        self.check_damage("missing", before_commit=True)

    def test_publication_replay_refuses_writable_identity(self):
        self.check_damage("mode", before_commit=True)

    def test_restore_admission_refuses_damaged_prior_identity(self):
        first, first_attempt = self.correction()
        identity = self.private / first.context_id / "generations/1/identity"
        identity.chmod(0o600)
        identity.write_bytes(b"foreign")
        identity.chmod(0o400)
        with self.assertRaises(ContractRefusal):
            self.admit()

    def test_publication_replay_preserves_mismatching_state(self):
        first, state = self.state()
        self.end_runtime(first)
        original = context._transition
        def cut(*args, **kwargs):
            if kwargs["action"] == "finalize":
                raise RuntimeError("published before journal")
            return original(*args, **kwargs)
        with mock.patch.object(context, "_transition", side_effect=cut), self.assertRaisesRegex(RuntimeError, "published before journal"):
            self.finalize()
        target = self.private / first.context_id / "generations/1/state" / profile()["state_paths"][0]
        target.chmod(0o600)
        target.write_bytes(b"mismatching published state")
        target.chmod(0o400)
        with self.assertRaisesRegex(ContractRefusal, "generation is damaged"):
            self.finalize()
        self.assertEqual(target.read_bytes(), b"mismatching published state")
        self.assertEqual(len(self.adapter.started), 1)

    def test_restore_materialization_rechecks_original_generation_identity(self):
        first, first_attempt = self.correction()
        self.admit()
        identity = self.private / first.context_id / "generations/1/identity"
        identity.chmod(0o600)
        identity.write_bytes(b"foreign")
        identity.chmod(0o400)
        with self.assertRaisesRegex(ContractRefusal, "generation identity"):
            delivery.materialize_context_use(self.control, self.custody, attempt_id=self.attempt_id)


class TransactionBoundaryRegression(ContextCase):
    """W236087: NO EXTERNAL READ inside a ControlStore transaction. DESIGN DB-1/2/4.

    `PREPARATION-307667.md` and `RESEARCH-307667.json` localised the defect: the
    admission's `check` and the invocation's `commit` called `_facts`, which reads the
    Job store, asks the Authority and walks two filesystem ancestries with
    `context_delivery._open_absolute` -- all while `store.transact` held
    `BEGIN IMMEDIATE`. These observe the boundary rather than describe it.

    WHAT IS NOT FORBIDDEN, and these hold that too: a read of the CONTROL store inside
    its own transaction is the compare-and-swap DB-3/5 asks for, so the qualification
    grant and the transition chain are still read there.

    THE SERVING INVOCATION IS COVERED ELSEWHERE, deliberately. `bind_context_invocation`
    needs a submitted manifest and task bytes, which this disposable fixture does not
    build and which no unit test here drives; the same boundary over the whole connected
    scenario -- admission, binding and launch revalidation -- is
    `tests/tools/test_correction_restart.py`
    `TransactionBoundaryThroughTheConnectedPath`. A case asserting nothing because its
    subject never ran would be worse than no case.
    """

    def observed(self):
        """Wrap the transaction and the external readers, and record the nesting."""
        import contextlib
        from baton_v12.worker_manager import attempts, context_delivery, store

        seen = {"external": [], "depth": [0]}

        def watching(name, original):
            def wrapper(*arguments, **keywords):
                if seen["depth"][0]:
                    seen["external"].append(name)
                return original(*arguments, **keywords)
            return wrapper

        stack = contextlib.ExitStack()
        original_transact = store.ControlStore.transact

        def transact(this, operation_id, kind, signature, action):
            def counted(connection):
                seen["depth"][0] += 1
                try:
                    return action(connection)
                finally:
                    seen["depth"][0] -= 1
            return original_transact(this, operation_id, kind, signature, counted)

        stack.enter_context(mock.patch.object(store.ControlStore, "transact",
                                             transact))
        stack.enter_context(mock.patch.object(
            context_delivery, "_open_absolute",
            watching("_open_absolute", context_delivery._open_absolute)))
        stack.enter_context(mock.patch.object(
            context, "_job_attempt", watching("_job_attempt",
                                              context._job_attempt)))
        stack.enter_context(mock.patch.object(
            attempts, "assignment_of", watching("attempts.assignment_of",
                                                attempts.assignment_of)))
        stack.enter_context(mock.patch.object(
            self.port, "assignment_of",
            watching("authority.assignment_of", self.port.assignment_of)))
        self.addCleanup(stack.close)
        return seen

    def test_a_public_admission_reaches_nothing_external_under_the_lock(self):
        seen = self.observed()
        self.admit()
        self.assertEqual(seen["external"], [], seen["external"])
        # AND THE ADMISSION REALLY HAPPENED, so this is not an empty observation.
        self.assertEqual(context.context_use_of(self.control,
                                                self.attempt_id)["status"],
                         "admitted")

    def test_a_CANDIDATE_qualification_admission_holds_the_boundary(self):
        """The case my first boundary test MISSED, and the reviewer found.

        W236087 review 2026-09-29T19-50-38Z R1: a deterministic profile returns from
        `_qualified` before it reaches `qualification_deployment`, so a successful
        deterministic admission never exercised the two filesystem ancestry walks that
        function performs. A candidate profile does reach them, and the reviewer observed
        both under BEGIN IMMEDIATE. This drives that profile.

        THE PRODUCTION BRANCH IS NOT DRIVEN HERE, and saying so is better than a case
        that pretends to: it reaches the SAME `qualification_deployment(...)` call, now
        fed by the same operand, and certifying a production profile needs a full accepted
        continuity report with a retained provider result -- which this disposable fixture
        does not build. The split is one call site and the candidate path proves it; a
        production case belongs with the connected work, where a real report exists.
        """
        self.profile_digest = context.certify_context_profile(
            self.control, profile(qualification="candidate"))["profile_digest"]
        context.authorize_qualification_run(
            self.control, run_id="boundary-candidate",
            profile_digest=self.profile_digest, storage_path=str(self.private),
            authority_uuid=UUID, job_id="context-job", note="boundary regression")
        seen = self.observed()
        self.admit()
        self.assertEqual(seen["external"], [], seen["external"])
        # AND THE GRANT REALLY WAS CONSUMED, so this is a qualified admission.
        chain = context._history(self.control)
        consumed = [one for chain_held in chain.values() for one in chain_held
                    if one["action"] == "admit"]
        self.assertEqual([one["payload"]["qualification_run"] for one in consumed],
                         ["boundary-candidate"])

    def test_the_DEPLOYMENT_COMPARISON_survives_becoming_an_operand(self):
        """Moving the resolution out must not lose the comparison it feeds.

        TWO ATTEMPTS AT THIS FAILED FIRST, and both failed because the system is tighter
        than I assumed. Reconfiguring the workspace store is refused outright -- "a changed
        store is a fresh store rather than a reconfiguration" -- and authorizing a grant
        against a foreign storage path is refused at authorization: "qualification storage
        differs from configured deployment". So no legitimate route from this fixture can
        present `_qualified` with a deployment that disagrees.

        WHAT IS ACTUALLY AT RISK is therefore the operand itself: a later change that drops
        it would silently skip the comparison. This drives `_qualified` with a deployment
        that disagrees and requires the refusal, which is the assertion that protects the
        split.
        """
        self.profile_digest = context.certify_context_profile(
            self.control, profile(qualification="candidate"))["profile_digest"]
        context.authorize_qualification_run(
            self.control, run_id="boundary-operand",
            profile_digest=self.profile_digest, storage_path=str(self.private),
            authority_uuid=UUID, job_id="context-job", note="boundary regression")
        facts = context._facts(self.control, self.jobs, self.port, self.attempt_id,
                               self.writer["writer_id"], self.profile_digest,
                               live=True)
        resolved = context.qualification_deployment(self.control, UUID)
        held = context.context_profile_of(self.control, self.profile_digest)
        owner = context._id("context", facts["identity"])
        # THE HONEST OPERAND SELECTS THE GRANT.
        self.assertEqual(context._qualified(self.control, self.jobs, facts, held, 0,
                                            owner, resolved),
                         "boundary-operand")
        # A DISAGREEING ONE REFUSES, so the comparison is still made.
        with self.assertRaises(ContractRefusal):
            context._qualified(self.control, self.jobs, facts, held, 0, owner,
                               dict(resolved, workspace_path="/somewhere/else"))

    def test_a_REFUSING_admission_also_holds_the_boundary(self):
        """The exception path, because that is where a lock is held longest."""
        seen = self.observed()
        with self.assertRaises(ContractRefusal):
            self.admit(writer_id="writer-nobody-owns")
        self.assertEqual(seen["external"], [], seen["external"])

    def test_a_FINALIZED_use_is_judged_from_the_JOURNAL_without_the_filesystem(self):
        """Review R2, at the split it created.

        `context_use_of` is not a journal read: on a FINALIZED head it calls
        `validate_generation`, which opens the private generation files. The binding's
        commit used it for eligibility, so a finalized use seen at commit performed
        filesystem validation under BEGIN IMMEDIATE before refusing -- the reviewer
        observed exactly that with an isolated finalized probe.

        `_journal_use` is the half the commit may ask. This holds both sides: the journal
        answer is `ready` and touches nothing, and `context_use_of` still validates, so the
        check was split rather than dropped.
        """
        from baton_v12.worker_manager import context_delivery

        # THE RUNTIME MUST BE EXCLUDED BEFORE A GENERATION CAN FINALIZE -- "old runtime
        # exclusion is unproved" is what my first version got, and `correction` is the
        # existing helper that ends the runtime before finalizing. Reusing it is also how
        # this case reaches a genuinely finalized use rather than a contrived one.
        first, _state = self.state()
        self.end_runtime(first)
        self.finalize()

        opened = []
        original = context_delivery._open_absolute

        def watching(*arguments, **keywords):
            opened.append(arguments[0] if arguments else None)
            return original(*arguments, **keywords)

        with mock.patch.object(context_delivery, "_open_absolute", watching):
            journal, _admitted, _owned = context._journal_use(self.control,
                                                              self.attempt_id)
        self.assertEqual(journal["status"], "ready")
        self.assertEqual(opened, [], opened)

        # AND THE VALIDATION IS STILL PERFORMED by the reader that always did it.
        with mock.patch.object(context_delivery, "_open_absolute", watching):
            self.assertEqual(context.context_use_of(self.control,
                                                    self.attempt_id)["status"],
                             "ready")
        self.assertNotEqual(opened, [])

    # THE LAUNCH FENCE IS NOT COVERED FROM HERE, and the case I wrote for it was
    # VACUOUS. W236087 review 2026-09-29T20-10-41Z: it called
    # `revalidate_context_start` without binding an invocation, so the refusal came
    # from "serving use cannot start" -- binding `null`, ZERO `_facts` calls -- and it
    # would have passed with an unchanged repository too. Removed rather than
    # patched over.
    #
    # THE REAL PRELAUNCH FENCE EVIDENCE is
    # `tests/manager/test_claude_context.py` `ServingBinding`, which has an actually
    # bound invocation:
    # `test_current_authority_change_between_preparation_and_start_refuses` changes the
    # Authority assignment between preparation and start and observes the refusal with
    # zero provider calls and zero engine starts, and
    # `test_private_repository_change_between_preparation_and_start_refuses` does the
    # same for the repository object this split moved out of the transaction.

    def test_a_PRODUCTION_profile_without_certification_refuses_at_the_JOURNAL(self):
        """The production branch's FIRST refusal, and nothing further. Named exactly.

        Review 2026-09-29T20-10-41Z is right about what this does and does not reach: it
        refuses at the certification journal, which is BEFORE the deployment comparison, and
        it is driven OUTSIDE a transaction. So it covers the journal refusal and the operand
        being accepted by that branch's signature -- NOT the production deployment
        comparison, and not that branch under the lock.

        THAT REMAINS AN HONEST LIMIT: reaching the comparison needs a recorded certification,
        which needs a full accepted continuity report with a retained provider result, and
        this disposable fixture builds none. It belongs with the connected work, where a real
        report exists.
        """
        facts = context._facts(self.control, self.jobs, self.port, self.attempt_id,
                               self.writer["writer_id"], self.profile_digest,
                               live=True)
        resolved = context.qualification_deployment(self.control, UUID)
        held = dict(context.context_profile_of(self.control, self.profile_digest),
                    qualification="production")
        owner = context._id("context", facts["identity"])
        with self.assertRaisesRegex(ContractRefusal, "lacks recorded certification"):
            context._qualified(self.control, self.jobs, facts, held, 0, owner,
                               resolved)

    def test_a_REPEATED_admission_REPLAYS_onto_the_same_use(self):
        """Replay is unchanged by the split: the durable reservation still decides.

        NAMED FOR WHAT IT DRIVES. Review 2026-09-29T20-10-41Z: I called this an INTERRUPTED
        request and it is a COMPLETED one replayed, which is a different property. The
        interrupted-request path -- a crash between the journalled request and the
        transition -- is covered by
        `QualificationAdmissionRegression.test_grant_is_rechecked_inside_commit_and_request_restart`,
        which refuses inside the commit and then reopens the store to replay the request,
        and by `test_historical_admission_survives_restart_without_rewriting`.

        What THIS holds is that a second admission of the same attempt answers the SAME use
        rather than minting another, and writes no second admit operation.
        """
        first = self.admit()
        operations = self.control._connection.execute(
            "SELECT COUNT(*) AS held FROM operations WHERE kind = ?",
            (context.TRANSITION_KIND,)).fetchone()["held"]
        again = self.admit()
        self.assertEqual(again, first)
        self.assertEqual(
            self.control._connection.execute(
                "SELECT COUNT(*) AS held FROM operations WHERE kind = ?",
                (context.TRANSITION_KIND,)).fetchone()["held"],
            operations)

    def test_UNRELATED_DB_PROGRESS_happens_WHILE_the_external_validation_runs(self):
        """The point of moving the external reads out, proved CONCURRENTLY.

        MY FIRST VERSION PROVED NOTHING. Review 2026-09-29T20-10-41Z: it used the SAME
        connection after a wrong-writer refusal that happens BEFORE any transaction, so
        there was never a lock to be blocked by.

        THIS BLOCKS INSIDE THE REAL EXTERNAL VALIDATION -- `_facts`, the reading that used
        to run under `BEGIN IMMEDIATE` -- and requires a SECOND ControlStore connection to
        commit its own operation while that validation is pending. Under the old placement
        this window was inside the write lock and the second connection could not commit.
        Bounded by a timeout, so a regression fails rather than hanging.

        AND IT IS NOT READ AS A GENERAL CLAIM. Review 2026-09-29T20-19-13Z: a positive
        progress probe at ONE point does not prove where every later read sits. The
        placement of the readings themselves is what the NESTING cases above measure --
        `test_a_public_admission_reaches_nothing_external_under_the_lock`, the candidate
        one, the refusing one and the connected
        `TransactionBoundaryThroughTheConnectedPath`. This adds that the window it opens is
        genuinely outside the lock, and no more.
        """
        import threading

        holding = threading.Event()
        release = threading.Event()
        committed = []
        original = context._facts

        def blocking(*arguments, **keywords):
            held = original(*arguments, **keywords)
            holding.set()
            # BOUNDED: a regression that never lets the other connection commit fails
            # here rather than hanging the suite.
            release.wait(timeout=10)
            return held

        def unrelated():
            if not holding.wait(timeout=10):
                return
            other = ControlStore.open(self.path, incarnation="unrelated-progress",
                                      clock=lambda: NOW)
            try:
                committed.append(other.transact(
                    "operation-unrelated-progress",
                    "provider-context.regression-probe",
                    manager_signature("provider-context.regression-probe",
                                      {"held": 1}),
                    lambda connection: {"held": 1}))
            finally:
                other.close()
                release.set()

        worker = threading.Thread(target=unrelated)
        worker.start()
        try:
            # THE BLOCKING READER IS ACTUALLY INSTALLED -- my first run defined it and
            # never patched it in, so the admission never paused and the other
            # connection had nothing to race.
            with mock.patch.object(context, "_facts", blocking):
                self.admit()
        finally:
            release.set()
            worker.join(timeout=15)
        self.assertFalse(worker.is_alive(), "the unrelated writer did not finish")
        self.assertEqual(committed, [{"held": 1}],
                         "an unrelated connection could not commit while the external "
                         "validation was pending")
        self.assertEqual(context.context_use_of(self.control,
                                                self.attempt_id)["status"],
                         "admitted")

    def test_the_UNRELATED_PROGRESS_PROBE_can_detect_a_held_lock(self):
        """The counter-check for the case above: the probe has teeth.

        A concurrency case that would pass under the OLD placement proves nothing. This
        blocks inside `control.transact`'s action -- where the external reading used to run
        -- and requires that a second connection CANNOT commit while it is held. So the
        previous case's success is evidence about the placement rather than about the probe.
        """
        import threading

        from baton_v12.worker_manager import store

        holding = threading.Event()
        release = threading.Event()
        blocked = []

        def unrelated():
            if not holding.wait(timeout=10):
                return
            other = ControlStore.open(self.path, incarnation="probe-teeth",
                                      clock=lambda: NOW)
            try:
                other._connection.execute("BEGIN IMMEDIATE")
                other._connection.rollback()
                blocked.append(False)
            except Exception:                                # noqa: BLE001
                # ANY failure to begin, not a specific error class. Review
                # 2026-09-29T20-19-13Z: describing this as a sqlite busy condition would
                # claim more than the probe observes.
                blocked.append(True)
            finally:
                other.close()
                release.set()

        worker = threading.Thread(target=unrelated)
        worker.start()
        original = store.ControlStore.transact

        def holding_transact(this, operation_id, kind, signature, action):
            def held(connection):
                answer = action(connection)
                holding.set()
                release.wait(timeout=10)
                return answer
            return original(this, operation_id, kind, signature, held)

        try:
            with mock.patch.object(store.ControlStore, "transact", holding_transact):
                self.admit()
        finally:
            release.set()
            worker.join(timeout=15)
        self.assertFalse(worker.is_alive())
        self.assertEqual(blocked, [True],
                         "a second connection committed while this store held "
                         "BEGIN IMMEDIATE, so the probe above cannot detect the "
                         "old placement")

    def test_a_FAILED_FIRST_SAVE_claims_nothing_at_all(self):
        """INITIAL-SAVE VISIBILITY, which is what this actually drives.

        W236087 review 2026-09-29T20-25-55Z R2: I offered this as "preserve generation 0 on
        failed save" and it fails the FIRST-EVER save, so there is no saved generation 0 to
        preserve -- it holds that a failed opening save claims nothing, which is worth
        having and is not the same property. The real one is
        `test_a_SAVED_generation_0_SURVIVES_a_later_failed_save` below.
        """
        first, _state = self.state()
        self.end_runtime(first)
        with mock.patch.object(delivery, "seal_generation",
                              side_effect=RuntimeError("injected save failure")):
            with self.assertRaises(RuntimeError):
                self.finalize()
        held = context.context_use_of(self.control, self.attempt_id)
        # NOT READY, and still the OPENING generation: a failed save is not reuse.
        self.assertNotEqual(held["status"], "ready")
        self.assertEqual(held["generation"], 0)
        # AND NO FINALIZE TRANSITION WAS JOURNALLED.
        chain = context._history(self.control, held["context_id"])
        self.assertEqual([one["action"] for one in chain
                          if one["action"] == "finalize"], [])

    def test_a_SAVED_generation_0_SURVIVES_a_later_failed_save(self):
        """The property item 2 names, on the fixture the review pointed at.

        THE FIXTURE BLOCKER WAS RESOLVED BY THE REVIEWER, and it is worth recording what it
        was: `ContextCase.end_runtime` hardcodes `mode: open` in the receipt it rebuilds, so
        finalizing a RESTORED use refused at `_receipt` -- "receipt does not prove this
        healthy invocation". The restored use needs
        `end_runtime(first, receipt_changes={"mode": "restore"})`.

        Generation 0 is SAVED and its identity and bytes captured; a fresh restored use then
        fails its own save; and the saved generation 0 must still be there, unchanged and
        valid, with NO successful new generation.
        """
        from baton_v12.worker_manager import context_delivery as custody

        # THE OPENING GENERATION IS SAVED, through the existing correction helper.
        self.correction()
        opening = [one for chain in context._history(self.control).values()
                   for one in chain if one["action"] == "finalize"]
        self.assertEqual(len(opening), 1, "the opening generation was not saved")
        saved, context_id = opening[0]["payload"], opening[0]["context_id"]
        storage = custody.configured_context_storage(self.control)
        # ITS IDENTITY AND ITS BYTES, captured before anything else happens.
        custody.validate_generation(self.control, storage, context_id, saved)
        # THE BYTES WHERE THEY ACTUALLY ARE. My first version guessed
        # `<storage>/<context>/<generation>` and found an empty directory; the generation's
        # own state lives under the profile's state path inside it, so this walks the whole
        # context subtree rather than one level of it.
        owner = pathlib.Path(storage.path) / context_id
        before = {str(one.relative_to(owner)): one.read_bytes()
                  for one in sorted(owner.rglob("*")) if one.is_file()}
        self.assertTrue(before, owner)

        # THE RESTORED USE'S OWN SAVE FAILS.
        restored, _state = self.state()
        self.end_runtime(restored, receipt_changes={"mode": "restore"})
        with mock.patch.object(delivery, "seal_generation",
                              side_effect=RuntimeError("injected later save failure")):
            with self.assertRaises(RuntimeError):
                self.finalize()

        # NO NEW SUCCESSFUL GENERATION, and the saved one is byte-for-byte intact.
        after = [one for chain in context._history(self.control).values()
                 for one in chain if one["action"] == "finalize"]
        self.assertEqual([one["payload"] for one in after], [saved])
        custody.validate_generation(self.control, storage, context_id, saved)
        now = {str(one.relative_to(owner)): one.read_bytes()
               for one in sorted(owner.rglob("*")) if one.is_file()}
        # THE SAVED GENERATION'S OWN BYTES ARE UNCHANGED, member for member.
        self.assertEqual({name: now.get(name) for name in before}, before)
        # THE FAILED USE'S OWN MATERIAL MAY STAND BESIDE IT, and does: the restored use's
        # `uses/...` state is still there. That is the preservation policy rather than a
        # regression -- a failed save deletes nothing -- and it is NOT a new generation,
        # which the journal assertion above is what rules out.
        appeared = sorted(set(now) - set(before))
        self.assertTrue(all(one.startswith("uses/") for one in appeared), appeared)

    def test_the_SAME_STORE_comparison_is_still_made_inside(self):
        """`_qualified` and the transition chain are this store's own rows.

        Moving them out would lose the compare-and-swap, so this asserts they are
        still read under the lock -- the opposite of the assertion above, on purpose.
        """
        import contextlib
        from baton_v12.worker_manager import store

        inside = {"qualified": 0, "history": 0, "depth": [0]}
        original_transact = store.ControlStore.transact

        def transact(this, operation_id, kind, signature, action):
            def counted(connection):
                inside["depth"][0] += 1
                try:
                    return action(connection)
                finally:
                    inside["depth"][0] -= 1
            return original_transact(this, operation_id, kind, signature, counted)

        def watching(name, original):
            def wrapper(*arguments, **keywords):
                if inside["depth"][0]:
                    inside[name] += 1
                return original(*arguments, **keywords)
            return wrapper

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(store.ControlStore, "transact",
                                                  transact))
            stack.enter_context(mock.patch.object(
                context, "_qualified", watching("qualified",
                                                context._qualified)))
            stack.enter_context(mock.patch.object(
                context, "_history", watching("history", context._history)))
            self.admit()
        self.assertGreaterEqual(inside["qualified"], 1)
        self.assertGreaterEqual(inside["history"], 1)

class QualificationAdmissionRegression(ContextCase):
    def candidate(self):
        self.profile_digest = context.certify_context_profile(self.control, profile(qualification="candidate"))["profile_digest"]
        context.authorize_qualification_run(self.control, run_id="qualification-regression", profile_digest=self.profile_digest, storage_path=str(self.private), authority_uuid=UUID, job_id="context-job", note="deterministic regression")

    def test_historical_admission_survives_restart_without_rewriting(self):
        facts = context._facts(self.control, self.jobs, self.port, self.attempt_id, self.writer["writer_id"], self.profile_digest, live=True)
        owner = context._id("context", facts["identity"])
        import uuid
        payload = dict(facts, generation=0, mode="open", predecessor=None, conversation_id=str(uuid.uuid5(uuid.NAMESPACE_OID, owner)))
        use = context._id("context-use", [owner, self.attempt_id, 0])
        context._transition(self.control, action="admit", context_id=owner, use_id=use, expected_revision=0, payload=payload)
        operation = context._operation("admit", owner, use, 0)
        before = self.control.operation_record(operation)
        reopened = ControlStore.open(self.path, incarnation="historical-reopen", clock=lambda: NOW)
        self.addCleanup(reopened.close)
        self.assertEqual(self.admit(reopened)["use_id"], use)
        self.assertEqual(reopened.operation_record(operation), before)
        self.assertNotIn("qualification_run", context._history(reopened, owner)[0]["payload"])
        delivery.materialize_context_use(reopened, self.custody, attempt_id=self.attempt_id)

    def test_grant_is_rechecked_inside_commit_and_request_restart(self):
        self.candidate()
        original = context._qualified
        seen = []
        # `deployment` IS NOW AN OPERAND. W236087 review 2026-09-29T19-50-38Z R1:
        # `_qualified` reached `qualification_deployment`, which walks two filesystem
        # ancestries, from inside the transaction. The caller resolves it outside and
        # passes it; this stub takes it and forwards it unchanged.
        def consumed(control, jobs, facts, held, generation, owner, deployment=None):
            seen.append(control._connection.in_transaction)
            if control._connection.in_transaction:
                context._refuse("candidate profile has no live qualification grant for this deployment and Job")
            return original(control, jobs, facts, held, generation, owner, deployment)
        with mock.patch.object(context, "_qualified", side_effect=consumed):
            with self.assertRaisesRegex(ContractRefusal, "no live qualification grant"):
                self.admit()
        self.assertEqual(seen, [False, True])
        self.assertIsNone(context._grant_consumer(self.control, "qualification-regression"))
        reopened = ControlStore.open(self.path, incarnation="request-reopen", clock=lambda: NOW)
        self.addCleanup(reopened.close)
        with mock.patch.object(context, "_qualified", side_effect=consumed):
            with self.assertRaisesRegex(ContractRefusal, "no live qualification grant"):
                self.admit(reopened)
        self.assertTrue(seen[-1])
        self.assertIsNone(context._grant_consumer(reopened, "qualification-regression"))
        # A transient precommit fault did not consume or poison the request.
        self.assertEqual(self.admit(reopened)["status"], "admitted")
        self.assertIsNotNone(context._grant_consumer(reopened, "qualification-regression"))

    def test_authority_and_workspace_object_are_bound(self):
        self.candidate()
        grant = context.qualification_grant_of(self.control, "qualification-regression")
        self.assertEqual(grant["deployment"]["authority_uuid"], UUID)
        self.assertEqual(grant["deployment"]["workspace_path"], str(self.storage))
        facts = context._facts(self.control, self.jobs, self.port, self.attempt_id, self.writer["writer_id"], self.profile_digest, live=True)
        moved = self.storage.with_name("original-workspaces")
        self.storage.rename(moved)
        self.storage.mkdir(mode=0o700)
        with self.assertRaisesRegex(ContractRefusal, "no live qualification grant"):
            context._qualified(self.control, self.jobs, facts, context.context_profile_of(self.control, self.profile_digest), 0, context._id("context", facts["identity"]))

    def test_wrong_authority_grant_cannot_be_spent(self):
        self.profile_digest = context.certify_context_profile(self.control, profile(qualification="candidate"))["profile_digest"]
        context.authorize_qualification_run(self.control, run_id="wrong-authority", profile_digest=self.profile_digest, storage_path=str(self.private), authority_uuid="another-authority", job_id="context-job", note="deterministic negative")
        with self.assertRaisesRegex(ContractRefusal, "no live qualification grant"):
            self.admit()

    def test_competing_context_consumes_between_selection_and_commit(self):
        self.candidate()
        facts = context._facts(self.control, self.jobs, self.port, self.attempt_id, self.writer["writer_id"], self.profile_digest, live=True)
        other = copy.deepcopy(facts)
        other["identity"]["line_id"] = "independent-second-line"
        other["attempt_id"] = other["assignment"]["runtime_attempt_id"] = "independent-second-attempt"
        other["writer_id"] = "independent-second-writer"
        owner = context._id("context", other["identity"])
        import uuid
        payload = dict(other, generation=0, mode="open", predecessor=None, conversation_id=str(uuid.uuid5(uuid.NAMESPACE_OID, owner)), qualification_run="qualification-regression")
        use = context._id("context-use", [owner, other["attempt_id"], 0])
        original_transition, original_facts = context._transition, context._facts
        def facts_at_boundary(control, jobs, authority, attempt, writer, profile_digest, *, live):
            # Two independently valid assignment snapshots are supplied at the
            # assignment boundary; grant selection and both commits are real.
            return other if attempt == other["attempt_id"] else original_facts(control, jobs, authority, attempt, writer, profile_digest, live=live)
        raced = []
        def interleaved(control, **arguments):
            if arguments["action"] == "admit" and not raced:
                raced.append(True)
                original_transition(control, action="admit", context_id=owner, use_id=use, expected_revision=0, payload=payload, check=lambda: context._check_admission(control, self.jobs, self.port, owner, payload))
            return original_transition(control, **arguments)
        with mock.patch.object(context, "_facts", side_effect=facts_at_boundary), mock.patch.object(context, "_transition", side_effect=interleaved):
            with self.assertRaisesRegex(ContractRefusal, "no live qualification grant"):
                self.admit()
        self.assertEqual(context._grant_consumer(self.control, "qualification-regression"), owner)
        self.assertEqual(len(context._history(self.control)), 1)
        reopened = ControlStore.open(self.path, incarnation="race-reopen", clock=lambda: NOW)
        self.addCleanup(reopened.close)
        with self.assertRaisesRegex(ContractRefusal, "no live qualification grant"):
            self.admit(reopened)
        self.assertEqual(len(context._history(reopened)), 1)
