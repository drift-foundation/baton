"""W32577 deterministic deadline policy and exact cleanup composition."""
import copy
import json
import os
import threading
import unittest
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (ControlStore, advance_deadline, deadline_of,
    deadline_cleanup_of, observe_deadline, activate_assignment, observe,
    request_runtime_start, runtime_lane)
from baton_v12.worker_manager import attempts, deadlines
from .test_attempts import ATTEMPT, Adapter, Agent, AttemptCase
from .test_offers import NOW, WORK
from .test_oci import Adapting
from .test_intake import IntakeCase, Custodian

LATER = "2026-08-24T00:00:10.000Z"
POLICY = {"policy_digest": "sha256:" + "2" * 64,
          "policy_generation": 1, "duration_seconds": 10, "action": "cancel"}
RETENTION = "sha256:" + "7" * 64


class DeadlineAdapter(Adapter):
    def __init__(self):
        super().__init__()
        self.removed = []
        self.destroy_answer = None
        self.on_destroy = None

    def destroy_deadline(self, command):
        self.removed.append(copy.deepcopy(command))
        if self.on_destroy is not None:
            self.on_destroy()
        return self.destroy_answer or {
            "runtime_id": command["runtime_id"], "state": "absent", "why": "exact identity absent",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "not-delivered"}}


class Deadlines(AttemptCase):
    def setUp(self):
        super().setUp()
        self.now = NOW
        self.store._clock = lambda: self.now
        self.adapter = DeadlineAdapter()
        self.agent = Agent()
        self.session.discharge_answer["kind"] = "runtime-absent"
        original = self.session.cancel

        def cancel(command):
            answer = original(command)
            self.session.live_assignment = None
            self.session._work = dict(self.session._work, work_id=WORK, phase="block",
                gate="runtime-quiescence:1", fenced_generations=[
                    {"generation": 1, "cause": "cancelled", "reason": command["reason"]}])
            return answer

        self.session.cancel = cancel

    def activated(self):
        self.claimed()
        activate_assignment(self.store, self.port, attempt_id=ATTEMPT, expect=self.expect())

    def started(self, policy=POLICY):
        self.activated()
        return request_runtime_start(self.store, self.adapter, attempt_id=ATTEMPT, deadline_policy=policy)

    def reached(self):
        self.now = LATER
        return observe_deadline(self.store, self.port, attempt_id=ATTEMPT)

    def advance(self, **changes):
        args = {"attempt_id": ATTEMPT, "retention_policy_digest": RETENTION}
        args.update(changes)
        return advance_deadline(self.store, self.port, self.agent, self.adapter, **args)

    def test_pin_precedes_adapter_and_clock_and_policy_survive_restart(self):
        self.activated()
        original = self.adapter.start
        pins = []

        def start(command):
            pins.append(deadline_of(self.store, attempt_id=ATTEMPT))
            return original(command)

        self.adapter.start = start
        request_runtime_start(self.store, self.adapter, attempt_id=ATTEMPT, deadline_policy=POLICY)
        pin = pins[0]
        self.assertEqual(pin["started_at"], NOW)
        self.assertEqual(pin["deadline_at"], LATER)
        with ControlStore.open(self.path, incarnation="restart", clock=lambda: LATER) as other:
            self.assertEqual(deadline_of(other, attempt_id=ATTEMPT), pin)

    def test_before_boundary_then_exact_reached_is_observation_only(self):
        self.started()
        self.now = "2026-08-24T00:00:09.999Z"
        self.assertIsNone(observe_deadline(self.store, self.port, attempt_id=ATTEMPT))
        before = self.row()
        reached = self.reached()
        self.assertEqual(reached["observed_at"], LATER)
        self.assertEqual(self.row(), before)
        self.assertEqual(self.adapter.stopped, [])
        self.assertEqual(self.adapter.removed, [])

    def test_reached_replay_precedes_clock_rollback_and_stale_authority(self):
        self.started()
        first = self.reached()
        self.now = NOW
        self.session.live_assignment = None
        self.assertEqual(observe_deadline(self.store, self.port, attempt_id=ATTEMPT), first)

    def test_fresh_stale_observation_refuses(self):
        self.started()
        self.session.live_assignment = None
        with self.assertRaisesRegex(ContractRefusal, "stale assignment"):
            self.reached()

    def test_fresh_terminal_observation_refuses(self):
        self.started()
        observe(self.store, attempt_id=ATTEMPT, axis="worker_disposition", value="completed")
        with self.assertRaises(ContractRefusal):
            self.reached()

    def test_report_only_never_uses_destructive_capabilities(self):
        self.started(dict(POLICY, action="report-only"))
        reached = self.reached()
        before = self.row()
        calls = list(self.session.calls)
        answer = advance_deadline(self.store, None, None, None, attempt_id=ATTEMPT,
                                  retention_policy_digest=RETENTION)
        self.assertEqual(answer["observation"], reached)
        self.assertEqual(answer["action"], "report-only")
        self.assertEqual(self.row(), before)
        self.assertEqual(self.session.calls, calls)

    def test_changed_or_omitted_selection_refuses_before_another_start(self):
        self.started()
        for policy in (None, dict(POLICY, policy_generation=2), dict(POLICY, duration_seconds=20),
                       dict(POLICY, action="report-only"), dict(POLICY, policy_digest="other")):
            with self.subTest(policy=policy), self.assertRaises(ContractRefusal):
                request_runtime_start(self.store, self.adapter, attempt_id=ATTEMPT, deadline_policy=policy)
        self.assertEqual(len(self.adapter.started), 1)

    def test_unconfigured_start_pins_explicit_none(self):
        self.started(None)
        pin = deadline_of(self.store, attempt_id=ATTEMPT)
        self.assertIsNone(pin["policy"])
        self.assertIsNone(pin["deadline_at"])
        with self.assertRaises(ContractRefusal):
            self.reached()

    def test_bad_policy_members_and_durations_refuse_before_start(self):
        self.activated()
        invalid = [dict(POLICY, duration_seconds=x) for x in (True, 0, -1, 0.5, float("inf"))]
        invalid += [dict(POLICY, policy_generation=True), dict(POLICY, policy_generation=0),
                    dict(POLICY, action="kill"), dict(POLICY, deadline_at=NOW)]
        for policy in invalid:
            with self.subTest(policy=policy), self.assertRaises(ContractRefusal):
                request_runtime_start(self.store, self.adapter, attempt_id=ATTEMPT, deadline_policy=policy)
        self.assertEqual(self.adapter.started, [])

    def test_interrupted_pin_cannot_gain_a_fresh_cancel_start_window(self):
        self.activated()
        deadlines._pin_start(self.store, attempts._require_attempt(self.store, ATTEMPT), POLICY)
        self.now = LATER
        with self.assertRaisesRegex(ContractRefusal, "already been reached"):
            request_runtime_start(self.store, self.adapter, attempt_id=ATTEMPT, deadline_policy=POLICY)
        self.assertEqual(self.adapter.started, [])
        self.assertEqual(deadline_of(self.store, attempt_id=ATTEMPT)["started_at"], NOW)

    def test_legacy_committed_start_cannot_be_backfilled(self):
        self.started(None)
        row = attempts._require_attempt(self.store, ATTEMPT)
        pin_id = deadlines._id("runtime.deadline-pin", ATTEMPT, self.expect())
        # A bounded old-store fixture: the start predates the new journal kind.
        self.store._connection.execute("DELETE FROM operations WHERE operation_id = ?", (pin_id,))
        self.assertIsNone(deadline_of(self.store, attempt_id=ATTEMPT))
        with self.assertRaisesRegex(ContractRefusal, "legacy"):
            request_runtime_start(self.store, self.adapter, attempt_id=ATTEMPT, deadline_policy=POLICY)
        self.assertIsNone(deadline_of(self.store, attempt_id=ATTEMPT))

    def test_cancel_fences_before_stop_removal_and_discharge(self):
        self.started()
        self.reached()
        original = self.adapter.destroy_deadline

        def destroy(command):
            self.assertTrue(any(name == "cancel" for name, _ in self.session.calls))
            self.assertEqual(self.session._work["gate"], "runtime-quiescence:1")
            self.assertIsNotNone(runtime_lane(self.store, ATTEMPT))
            return original(command)

        self.adapter.destroy_deadline = destroy
        answer = self.advance()
        self.assertEqual(answer["cleanup"]["cleanup"]["cleanup"], "retained")
        self.assertEqual(self.row()["worker_disposition"], "none")
        self.assertEqual(self.row()["output"], "open")
        self.assertIsNone(self.session._work["gate"])
        proof = deadline_cleanup_of(self.store, attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        self.assertEqual(proof, answer["cleanup"])
        count = len(self.adapter.removed)
        self.assertEqual(self.advance(), answer)
        self.assertEqual(len(self.adapter.removed), count)

    def test_authority_refusal_makes_no_destructive_calls(self):
        self.started()
        self.reached()
        self.session.fence_answer = ContractRefusal("refused", "precondition", "fence refused")
        with self.assertRaises(ContractRefusal):
            self.advance()
        self.assertEqual(self.adapter.stopped, [])
        self.assertEqual(self.adapter.removed, [])

    def test_unrelated_cancellation_cannot_be_relabelled(self):
        self.started()
        self.reached()
        attempts.request_cancellation(self.store, self.port, self.agent, self.adapter,
                                      attempt_id=ATTEMPT, reason="another decision")
        with self.assertRaises(ContractRefusal):
            self.advance()
        self.assertEqual(self.adapter.removed, [])

    def test_output_arriving_during_fence_holds_receiptless_cleanup(self):
        self.started()
        self.reached()
        original = self.session.cancel

        def cancel(command):
            answer = original(command)
            observe(self.store, attempt_id=ATTEMPT, axis="worker_disposition", value="completed")
            return answer

        self.session.cancel = cancel
        with self.assertRaisesRegex(ContractRefusal, "output owner"):
            self.advance()
        self.assertEqual(self.adapter.removed, [])
        self.assertEqual(self.row()["worker_disposition"], "completed")
        self.assertEqual(self.row()["cleanup"], "pending")

    def test_provider_unresolved_is_retryable_and_does_not_release_gate(self):
        self.started()
        self.reached()
        self.adapter.destroy_answer = {"runtime_id": "runtime-1", "state": "absent", "why": "gone",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "unresolved", "why": "try again"}}
        answer = self.advance()
        self.assertIsNone(answer["discharge"])
        self.assertEqual(self.row()["cleanup"], "pending")
        self.assertIsNone(deadline_cleanup_of(self.store, attempt_id=ATTEMPT, retention_policy_digest=RETENTION))
        self.adapter.destroy_answer = None
        self.assertEqual(self.advance()["cleanup"]["cleanup"]["cleanup"], "retained")
        self.assertEqual(len(self.adapter.removed), 2)

    def test_engine_uncertainty_keeps_cleanup_retryable(self):
        self.started()
        self.reached()
        self.adapter.destroy_answer = {"runtime_id": "runtime-1", "state": "uncertain", "why": "unavailable",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "not-delivered"}}
        answer = self.advance()
        self.assertIsNone(answer["discharge"])
        self.assertEqual(self.row()["cleanup"], "pending")
        self.adapter.destroy_answer = None
        self.assertEqual(self.advance()["cleanup"]["cleanup"]["cleanup"], "retained")

    def test_no_start_uses_six_fact_proof_not_fabricated_absence(self):
        self.activated()
        deadlines._pin_start(self.store, attempts._require_attempt(self.store, ATTEMPT), POLICY)
        self.reached()
        answer = self.advance()
        self.assertEqual(answer["cleanup"]["state"], "fenced-before-start")
        self.assertIsNone(answer["discharge"])
        self.assertEqual(self.adapter.removed, [])

    def test_corrupt_provider_or_custody_proof_cannot_discharge(self):
        self.started()
        self.reached()
        first = self.advance()
        command = first["cleanup"]["command"]
        operation = deadlines._operation(command)
        record = self.store.operation_record(operation["operation_id"])
        original = json.loads(record["result"])
        for corrupt in ("provider", "custody", "identity"):
            bad = copy.deepcopy(original)
            if corrupt == "provider":
                bad["observed"]["launch"]["lifecycle_state"] = "unresolved"
            elif corrupt == "custody":
                bad["cleanup"]["directory_custody"] = None
            else:
                bad["command"]["runtime_id"] = "sibling"
            self.store._connection.execute("UPDATE operations SET result = ? WHERE operation_id = ?",
                                           (json.dumps(bad), operation["operation_id"]))
            with self.subTest(corrupt=corrupt), self.assertRaises(ContractRefusal):
                deadline_cleanup_of(self.store, attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        self.store._connection.execute("UPDATE operations SET result = ? WHERE operation_id = ?",
                                       (record["result"], operation["operation_id"]))

    def test_two_connections_converge_on_one_observation(self):
        self.started()
        self.now = LATER
        barrier = threading.Barrier(2)
        results, failures = [], []

        def run(number):
            try:
                with ControlStore.open(self.path, incarnation=f"observer-{number}", clock=lambda: LATER) as store:
                    barrier.wait(timeout=5)
                    results.append(observe_deadline(store, self.port, attempt_id=ATTEMPT))
            except BaseException as error:
                failures.append(error)

        threads = [threading.Thread(target=run, args=(number,)) for number in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=8)
        self.assertEqual(failures, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], results[1])

    def test_malformed_public_operands_refuse_without_external_acts(self):
        self.started()
        self.reached()
        from baton_v12.worker_manager import discharge_deadline_quiescence_gate
        operations = (deadline_of, observe_deadline, advance_deadline,
                      deadline_cleanup_of, discharge_deadline_quiescence_gate)
        for operation in operations:
            prefix = (self.store,)
            if operation in (observe_deadline, discharge_deadline_quiescence_gate):
                prefix += (self.port,)
            elif operation is advance_deadline:
                prefix += (self.port, self.agent, self.adapter)
            extra = {} if operation in (deadline_of, observe_deadline) else {"retention_policy_digest": RETENTION}
            with self.subTest(operation=operation.__name__), self.assertRaises(ContractRefusal):
                operation(*prefix, attempt_id=[], **extra)
            if extra:
                with self.subTest(operation=operation.__name__, operand="retention"), self.assertRaises(ContractRefusal):
                    operation(*prefix, attempt_id=ATTEMPT, retention_policy_digest=[])
        self.assertEqual(self.adapter.stopped, [])
        self.assertEqual(self.adapter.removed, [])

    def test_missing_capabilities_refuse_before_cancellation_intent(self):
        self.started()
        self.reached()
        for owner, member in ((self.agent, "cancel"), (self.adapter, "stop"),
                              (self.adapter, "destroy_deadline"), (self.adapter, "normalize_directory"),
                              (self.port, "satisfy_gate")):
            with self.subTest(member=member), mock.patch.object(owner, member, None):
                with self.assertRaises(ContractRefusal):
                    self.advance()
                self.assertIsNone(self.store.operation_record(attempts._cancel_operation_id(
                    attempts._require_attempt(self.store, ATTEMPT))))
        self.assertEqual(self.adapter.stopped, [])
        self.assertEqual(self.adapter.removed, [])

    def test_bad_destroy_answers_cannot_settle_or_discharge(self):
        self.started()
        self.reached()
        valid = self.adapter.destroy_deadline({"runtime_id": "runtime-1"})
        invalid = [[], dict(valid, extra=True), dict(valid, runtime_id="sibling"),
                   dict(valid, state="invented"), dict(valid, why=[])]
        for provider in ("credentials", "launch"):
            invalid += [dict(valid, **{provider: value}) for value in
                        ([], {}, {"lifecycle_state": "unknown"},
                         {"lifecycle_state": [], "why": "bad"},
                         {"lifecycle_state": "torn-down", "extra": True})]
        for bad in invalid:
            self.adapter.destroy_answer = bad
            # Empty lists are deliberately returned too, not replaced by the fake's default.
            with mock.patch.object(self.adapter, "destroy_deadline", return_value=bad):
                with self.subTest(answer=bad), self.assertRaises(ContractRefusal):
                    self.advance()
            self.assertEqual(self.row()["cleanup"], "pending")
            self.assertIsNotNone(runtime_lane(self.store, ATTEMPT))
            self.assertEqual(self.session._work["gate"], "runtime-quiescence:1")
        self.adapter.destroy_answer = None
        self.assertIsNotNone(self.advance()["discharge"])

    def test_crash_after_removal_before_commit_reuses_exact_command(self):
        self.started()
        self.reached()
        from baton_v12.worker_manager import intake
        with mock.patch.object(intake, "_normalized", side_effect=OSError("interrupted custody")):
            with self.assertRaises(OSError):
                self.advance()
        first = self.adapter.removed[0]
        self.assertIsNone(deadline_cleanup_of(self.store, attempt_id=ATTEMPT, retention_policy_digest=RETENTION))
        self.assertIsNotNone(runtime_lane(self.store, ATTEMPT))
        self.assertIsNotNone(self.advance()["discharge"])
        self.assertEqual(self.adapter.removed, [first, first])

    def test_remote_discharge_replays_after_local_receipt_commit_interruption(self):
        self.started()
        self.reached()
        real = self.store.transact

        def transact(operation_id, kind, signature, act):
            if kind == "authority.discharge-quiescence-deadline":
                raise OSError("interrupted receipt commit")
            return real(operation_id, kind, signature, act)

        with mock.patch.object(self.store, "transact", side_effect=transact):
            with self.assertRaises(OSError):
                self.advance()
        self.assertIsNone(self.session._work["gate"])
        self.assertIsNotNone(deadline_cleanup_of(self.store, attempt_id=ATTEMPT, retention_policy_digest=RETENTION))
        count = len(self.adapter.removed)
        self.assertIsNotNone(self.advance()["discharge"])
        self.assertEqual(len(self.adapter.removed), count)

    def test_unknown_committed_start_never_becomes_a_no_start_proof(self):
        self.started()
        self.reached()
        # Interrupted attachment fixture: durable start exists but the runtime id was not adopted.
        self.store._connection.execute("UPDATE attempts SET runtime_id = NULL WHERE runtime_attempt_id = ?", (ATTEMPT,))
        self.adapter.list_answer = []
        with mock.patch.object(self.adapter, "list", return_value=[]):
            with self.assertRaises(ContractRefusal):
                self.advance()
        self.assertEqual(self.adapter.removed, [])
        self.assertIsNotNone(runtime_lane(self.store, ATTEMPT))
        self.assertEqual(self.session._work["gate"], "runtime-quiescence:1")

    def test_missing_authorization_cannot_be_replaced_by_cleanup_axes(self):
        self.started()
        self.reached()
        proof = self.advance()["cleanup"]
        authorization_id = "runtime.deadline-cleanup-authorized:" + deadlines.digest(proof["command"])[len("sha256:"):]
        self.store._connection.execute("DELETE FROM operations WHERE operation_id = ?", (authorization_id,))
        self.assertEqual(self.row()["cleanup"], "retained")
        with self.assertRaisesRegex(ContractRefusal, "committed authorization"):
            deadline_cleanup_of(self.store, attempt_id=ATTEMPT, retention_policy_digest=RETENTION)

    def test_corrupted_pin_and_reached_instants_refuse(self):
        self.started()
        self.reached()
        for kind, members in (("runtime.deadline-pin", ("started_at", "deadline_at")),
                              ("runtime.deadline-reached", ("observed_at",))):
            operation_id = deadlines._id(kind, ATTEMPT, self.expect())
            record = self.store.operation_record(operation_id)
            for member in members:
                for value in ([], "2026-08-23T00:00:00.000Z"):
                    corrupted = json.loads(record["result"])
                    corrupted[member] = value
                    self.store._connection.execute("UPDATE operations SET result = ? WHERE operation_id = ?",
                                                   (json.dumps(corrupted), operation_id))
                    with self.subTest(member=member, value=value), self.assertRaises(ContractRefusal):
                        self.advance()
                    self.store._connection.execute("UPDATE operations SET result = ? WHERE operation_id = ?",
                                                   (record["result"], operation_id))
        self.assertEqual(self.adapter.removed, [])


class CooperativeDeadlineFailures(Deadlines):
    # Only this class's additive cases are selected below; the parent owns the
    # original matrix and supplies the same real manager/store fixture.

    def failure_records(self):
        return [json.loads(row[0]) for row in self.store._connection.execute(
            "SELECT result FROM operations WHERE kind = 'runtime.deadline-cooperative-failure' ORDER BY operation_id")]

    def test_recurring_agent_fault_restarts_through_provider_hold_and_preserves_sibling(self):
        self.started()
        self.reached()
        live = {"runtime-1", "runtime-sibling"}
        self.adapter.on_destroy = lambda: live.discard("runtime-1")
        sibling = os.path.join(os.path.dirname(self.path), "sibling-output")
        with open(sibling, "wb") as handle:
            handle.write(b"sibling evidence")
        self.adapter.destroy_answer = {"runtime_id": "runtime-1", "state": "absent", "why": "removed",
            "credentials": {"lifecycle_state": "not-delivered"},
            "launch": {"lifecycle_state": "unresolved", "why": "provider temporarily unavailable"}}
        with mock.patch.object(self.agent, "cancel", side_effect=OSError("agent unreachable")) as cancel:
            first = self.advance()
            self.assertIsNone(first["discharge"])
            self.assertIsNotNone(runtime_lane(self.store, ATTEMPT))
            self.assertEqual(self.session._work["gate"], "runtime-quiescence:1")
            self.adapter.destroy_answer = None
            with ControlStore.open(self.path, incarnation="deadline-recovery", clock=lambda: LATER) as restarted:
                final = advance_deadline(restarted, self.port, self.agent, self.adapter,
                    attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
            self.assertEqual(cancel.call_count, 1)
            self.assertIsNotNone(final["discharge"])
            self.assertEqual(self.advance(), final)
            self.assertEqual(cancel.call_count, 1)
        self.assertEqual(len(self.adapter.stopped), 1)
        self.assertEqual(self.adapter.removed[0], self.adapter.removed[1])
        records = self.failure_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["stage"], "agent.cancel")
        self.assertEqual(records[0]["failure"]["message"], "agent unreachable")
        self.assertEqual(records[0]["runtime_id"], "runtime-1")
        self.assertEqual(live, {"runtime-sibling"})
        with open(sibling, "rb") as handle:
            self.assertEqual(handle.read(), b"sibling evidence")

    def test_both_cooperative_faults_survive_removal_interruption_and_restart(self):
        self.started()
        self.reached()
        with mock.patch.object(self.agent, "cancel", side_effect=OSError("agent gone")), \
                mock.patch.object(self.adapter, "stop", side_effect=OSError("stop unavailable")):
            with mock.patch.object(self.adapter, "destroy_deadline", side_effect=OSError("remove interrupted")):
                with self.assertRaisesRegex(OSError, "remove interrupted"):
                    self.advance()
            self.assertEqual(self.row()["cleanup"], "pending")
            self.assertIsNotNone(runtime_lane(self.store, ATTEMPT))
            with ControlStore.open(self.path, incarnation="deadline-both-recovery", clock=lambda: LATER) as restarted:
                result = advance_deadline(restarted, self.port, self.agent, self.adapter,
                    attempt_id=ATTEMPT, retention_policy_digest=RETENTION)
        self.assertIsNotNone(result["discharge"])
        self.assertEqual({one["stage"] for one in self.failure_records()}, {"agent.cancel", "adapter.stop"})
        self.assertEqual(len(self.failure_records()), 2)
        self.assertEqual(self.row()["worker_disposition"], "none")

    def test_stop_fault_alone_still_reaches_exact_removal(self):
        self.started()
        self.reached()
        with mock.patch.object(self.adapter, "stop", side_effect=OSError("stop unavailable")):
            result = self.advance()
        self.assertIsNotNone(result["discharge"])
        self.assertEqual([one["stage"] for one in self.failure_records()], ["adapter.stop"])
        self.assertEqual(len(self.adapter.removed), 1)

    def test_authority_failure_is_not_an_advisory_failure(self):
        self.started()
        self.reached()
        self.session.fence_answer = ContractRefusal("refused", "precondition", "fence refused")
        with mock.patch.object(self.agent, "cancel", side_effect=OSError("agent gone")) as agent, \
                mock.patch.object(self.adapter, "stop", side_effect=OSError("stop failed")) as stop:
            with self.assertRaisesRegex(ContractRefusal, "fence refused"):
                self.advance()
        agent.assert_not_called()
        stop.assert_not_called()
        self.assertEqual(self.adapter.removed, [])
        self.assertEqual(self.failure_records(), [])

    def test_recovery_must_resolve_the_exact_authority_fence(self):
        self.started()
        self.reached()
        original = self.session.cancel
        calls = []

        def cancel(command):
            calls.append(copy.deepcopy(command))
            if len(calls) == 2:
                raise ContractRefusal("refused", "precondition", "fence replay unavailable")
            return original(command)

        self.session.cancel = cancel
        with mock.patch.object(self.agent, "cancel", side_effect=OSError("agent gone")):
            with self.assertRaisesRegex(ContractRefusal, "fence replay unavailable"):
                self.advance()
        self.assertEqual(calls[0], calls[1])
        self.assertEqual(len(self.failure_records()), 1)
        self.assertEqual(self.adapter.removed, [])
        self.assertIsNotNone(runtime_lane(self.store, ATTEMPT))

    def test_changed_runtime_during_advisory_failure_holds_before_recovery(self):
        self.started()
        self.reached()

        def cancelled(command):
            self.store._connection.execute("UPDATE attempts SET runtime_id = 'runtime-sibling' WHERE runtime_attempt_id = ?", (ATTEMPT,))
            raise OSError("agent gone")

        with mock.patch.object(self.agent, "cancel", side_effect=cancelled):
            with self.assertRaisesRegex(ContractRefusal, "changed assignment or runtime"):
                self.advance()
        self.assertEqual(self.adapter.removed, [])

    def test_changed_runtime_during_fence_replay_holds_before_removal(self):
        self.started()
        self.reached()
        original = self.session.cancel
        calls = []

        def cancel(command):
            answer = original(command)
            calls.append(command)
            if len(calls) == 2:
                self.store._connection.execute("UPDATE attempts SET runtime_id = 'runtime-sibling' WHERE runtime_attempt_id = ?", (ATTEMPT,))
            return answer

        self.session.cancel = cancel
        with mock.patch.object(self.agent, "cancel", side_effect=OSError("agent gone")):
            with self.assertRaisesRegex(ContractRefusal, "assignment or runtime changed"):
                self.advance()
        self.assertEqual(self.adapter.removed, [])

    def test_output_arriving_with_advisory_fault_keeps_its_owner(self):
        self.started()
        self.reached()

        def cancelled(command):
            observe(self.store, attempt_id=ATTEMPT, axis="worker_disposition", value="completed")
            raise OSError("agent disconnected after answer")

        with mock.patch.object(self.agent, "cancel", side_effect=cancelled):
            with self.assertRaisesRegex(ContractRefusal, "output owner"):
                self.advance()
        self.assertEqual(self.adapter.removed, [])
        self.assertEqual(self.row()["worker_disposition"], "completed")
        self.assertIsNotNone(runtime_lane(self.store, ATTEMPT))

    def test_advisory_fault_diagnostic_cannot_persist_a_held_credential(self):
        from baton_v12.contracts import held_secret
        self.started()
        self.reached()
        value = "credential-should-stay-out-of-evidence"
        with held_secret(value), mock.patch.object(self.agent, "cancel", side_effect=OSError(value)):
            self.assertIsNotNone(self.advance()["discharge"])
        self.assertNotIn(value, json.dumps(self.failure_records()))
        self.assertEqual(self.failure_records()[0]["failure"]["fault"], "unrecordable-diagnostic")

    def test_diagnostic_truncation_cannot_persist_a_credential_prefix(self):
        from baton_v12.contracts import held_secret
        self.started()
        self.reached()
        value = "credential-crossing-the-diagnostic-bound"
        with held_secret(value), mock.patch.object(self.agent, "cancel", side_effect=OSError("x" * 1990 + value)):
            self.assertIsNotNone(self.advance()["discharge"])
        self.assertEqual(self.failure_records()[0]["failure"]["fault"], "unrecordable-diagnostic")

    def test_ordinary_cancellation_still_reports_the_agent_failure(self):
        self.started()
        with mock.patch.object(self.agent, "cancel", side_effect=OSError("ordinary agent failure")):
            with self.assertRaisesRegex(OSError, "ordinary agent failure"):
                attempts.request_cancellation(self.store, self.port, self.agent, self.adapter,
                    attempt_id=ATTEMPT, reason="ordinary cancellation")
        self.assertEqual(len(self.adapter.stopped), 1)
        self.assertEqual(self.adapter.removed, [])
        self.assertEqual(self.failure_records(), [])

    def test_manager_fault_without_cooperative_provenance_propagates(self):
        self.started()
        self.reached()
        with mock.patch.object(attempts, "request_cancellation", side_effect=OSError("manager journal unavailable")):
            with self.assertRaisesRegex(OSError, "manager journal unavailable"):
                self.advance()
        self.assertEqual(self.adapter.removed, [])
        self.assertEqual(self.failure_records(), [])

    def test_forwarder_preserves_the_settlement_and_original_exception(self):
        self.started()
        self.reached()
        original = attempts.request_cancellation
        fault = OSError("same fault instance")
        seen = []

        def cancellation(*args, **kwargs):
            try:
                return original(*args, **kwargs)
            except OSError as caught:
                seen.append(caught)
                raise

        with mock.patch.object(attempts, "request_cancellation", side_effect=cancellation), \
                mock.patch.object(self.agent, "cancel", side_effect=fault):
            self.assertIsNotNone(self.advance()["discharge"])
        self.assertEqual(len(seen), 1)
        self.assertIs(seen[0], fault)

    def test_forwarder_returns_unmodified_successful_settlements(self):
        self.started()
        self.reached()
        original = attempts.request_cancellation
        replies = []
        agent_answer = {"boundary": "agent", "value": [1, 2]}
        stop_answer = {"boundary": "runtime", "value": [3, 4]}

        def cancellation(*args, **kwargs):
            answer = original(*args, **kwargs)
            replies.append(answer)
            return answer

        with mock.patch.object(attempts, "request_cancellation", side_effect=cancellation), \
                mock.patch.object(self.agent, "cancel", return_value=agent_answer), \
                mock.patch.object(self.adapter, "stop", return_value=stop_answer):
            self.assertIsNotNone(self.advance()["discharge"])
        self.assertEqual(replies[0]["quiescence"]["agent_settlement"], agent_answer)
        self.assertEqual(replies[0]["quiescence"]["runtime_settlement"], stop_answer)

    def test_replayed_fence_for_another_generation_cannot_authorize_cleanup(self):
        self.started()
        self.reached()
        original = self.session.cancel
        calls = []

        def cancel(command):
            answer = copy.deepcopy(original(command))
            calls.append(command)
            if len(calls) == 2:
                answer["assignment"]["generation"] = 2
            return answer

        self.session.cancel = cancel
        with mock.patch.object(self.agent, "cancel", side_effect=OSError("agent gone")):
            with self.assertRaises(ContractRefusal):
                self.advance()
        self.assertEqual(self.adapter.removed, [])
        self.assertIsNotNone(runtime_lane(self.store, ATTEMPT))


class DeadlineDocuments(unittest.TestCase):
    def test_closed_constructor_members(self):
        from baton_v12.worker_manager import documents
        constructors = {"pin": documents.deadline_pin, "reached": documents.deadline_reached,
                        "destroy": documents.deadline_destroy_command, "cleanup": documents.deadline_cleanup,
                        "advanced": documents.deadline_advanced, "discharge": documents.deadline_discharge}
        for kind, constructor in constructors.items():
            required, optional = documents.CONTRACTS["deadline." + kind]
            valid = {member: "owned-value" for member in required}
            with self.subTest(kind=kind):
                self.assertEqual(constructor(**valid), valid)
                with self.assertRaises(ContractRefusal):
                    constructor(**dict(valid, unowned=True))
                for member in required:
                    with self.subTest(missing=member), self.assertRaises(ContractRefusal):
                        constructor(**{key: value for key, value in valid.items() if key != member})


class DeadlineAdapterBoundary(Adapting):
    def test_exact_removal_preserves_sibling_runtime_launch_and_output(self):
        live = {"runtime-1", "runtime-sibling"}

        def answer(argv):
            if "rm" in argv:
                self.assertEqual(argv[-1], "runtime-1")
                live.remove(argv[-1])
                return {"status": 0, "stdout": "", "stderr": ""}
            self.assertIn("inspect", argv)
            self.assertEqual(argv[-1], "runtime-1")
            return {"status": 1, "stdout": "", "stderr": "Error: No such object: runtime-1"}

        sibling_launch = self.launched("attempt-sibling")
        adapter = self.adapter(answering=answer)
        sentinel = os.path.join(self.live_roots["workspace"], "untrusted-output.txt")
        with open(sentinel, "wb") as handle:
            handle.write(b"partial output remains")
        command = {"runtime_attempt_id": "attempt-1", "assignment_ref": {"fixed": "manager-owned"},
                   "runtime_id": "runtime-1", "deadline_operation_id": "reached-1", "deadline_digest": "digest",
                   "cancel_operation_id": "cancel-1", "authority_operation_id": "fence-1",
                   "retention_policy_digest": RETENTION}
        with self.assertRaises(ContractRefusal):
            adapter.destroy_deadline(dict(command, caller_timeout=True))
        self.assertEqual(self.engine.vectors, [])
        observed = adapter.destroy_deadline(command)
        self.assertEqual(observed["state"], "absent")
        self.assertEqual(observed["launch"]["lifecycle_state"], "torn-down")
        self.assertEqual(live, {"runtime-sibling"})
        self.assertTrue(os.path.exists(sibling_launch.root))
        with open(sentinel, "rb") as handle:
            self.assertEqual(handle.read(), b"partial output remains")


class DeadlineReceiptedOutput(IntakeCase):
    def test_output_after_interrupted_cancel_intent_uses_ordinary_receipt_cleanup(self):
        from . import test_intake
        real_start = request_runtime_start
        runtime = DeadlineAdapter()

        def start(store, adapter, **operands):
            answer = real_start(store, adapter, **operands, deadline_policy=POLICY)
            store._clock = lambda: LATER
            reached = observe_deadline(store, self.port, attempt_id=ATTEMPT)
            reached_id = deadlines._id("runtime.deadline-reached", ATTEMPT, reached["assignment"])
            with mock.patch.object(self.session, "cancel", side_effect=OSError("interrupted before fence")):
                with self.assertRaises((OSError, ContractRefusal)):
                    attempts.request_cancellation(store, self.port, Agent(), runtime, attempt_id=ATTEMPT,
                        reason="runtime deadline reached: " + reached_id)
            return answer

        with mock.patch.object(test_intake, "request_runtime_start", side_effect=start):
            receipt = self.retained_ready()
        self.assertEqual(receipt["custody"], "accepted")
        self.session.fence_answer["assignment"] = copy.deepcopy(self.session.live_assignment)
        original = self.session.cancel

        def cancel(command):
            answer = original(command)
            self.session.live_assignment = None
            self.session._work = dict(self.session._work, phase="block", gate="runtime-quiescence:1")
            return answer

        self.session.cancel = cancel
        self.session.discharge_answer["kind"] = "runtime-absent"
        adapter = Custodian()
        adapter.stop = runtime.stop
        adapter.destroy_deadline = mock.Mock(side_effect=AssertionError("receiptless destruction"))
        answer = advance_deadline(self.store, self.port, Agent(), adapter, attempt_id=ATTEMPT,
                                  retention_policy_digest=RETENTION)
        self.assertEqual(answer["cleanup"]["cleanup"], "complete")
        self.assertEqual(len(adapter.destroyed_with), 1)
        adapter.destroy_deadline.assert_not_called()
        self.assertEqual(self.attempt_axis("worker_disposition"), "completed")
        self.assertEqual(self.attempt_axis("output"), "sealed")
        self.assertIsNotNone(answer["discharge"])
        self.assertEqual(advance_deadline(self.store, self.port, Agent(), adapter, attempt_id=ATTEMPT,
                                         retention_policy_digest=RETENTION), answer)
        self.assertEqual(len(adapter.destroyed_with), 1)


def load_tests(loader, tests, pattern):
    """Run each authored case once; inherited fixtures supply no duplicate matrix."""
    selected = unittest.TestSuite()
    for cls in (Deadlines, CooperativeDeadlineFailures, DeadlineDocuments,
                DeadlineAdapterBoundary, DeadlineReceiptedOutput):
        for name in sorted(cls.__dict__):
            if name.startswith("test_"):
                selected.addTest(cls(name))
    return selected
