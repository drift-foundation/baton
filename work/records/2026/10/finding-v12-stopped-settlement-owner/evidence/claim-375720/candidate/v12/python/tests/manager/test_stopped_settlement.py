"""Deterministic owner proof; no engine or provider is executed."""
import copy
import os
import threading
import sqlite3
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import attempts, tokens, workspaces
from baton_v12.worker_manager import stopped_settlement as settlement
from baton_v12.worker_manager.store import ControlStore
from .test_attempts import AttemptCase, Adapter, Agent, ATTEMPT
from .test_exchange import Home


class GovernedAdapter(Adapter):
    def start(self, operands, *, bind):
        bind(self.runtime_id)()
        return super().start(operands)


class StoppedSettlement(AttemptCase, Home):
    def setUp(self):
        AttemptCase.setUp(self)
        self.ATTEMPT = ATTEMPT
        self.control = self.store
        self.launch_home = os.path.join(self._root.name, "launch")
        os.mkdir(self.launch_home)
        self.claimed()
        attempts.activate_assignment(self.store, self.port, attempt_id=ATTEMPT, expect=self.expect())
        self.roots = workspaces.assignment_workspace(self.group, self.storage, ATTEMPT)
        workspaces.record_preparation(self.store, ATTEMPT, self.roots, ["input.json", "assignment.json"])
        self.workspace_identity = workspaces.preparation_completed(self.store, ATTEMPT)["workspace"]
        self.govern = tokens.Governance("workspace", lambda attempt: self.workspace_identity)
        self.adapter = GovernedAdapter()
        attempts.request_runtime_start(self.store, self.adapter, attempt_id=ATTEMPT, govern=self.govern)
        self.adapter.observation = {"state": "quiescent", "why": "deterministic stopped runtime"}
        self.delivery, command = self.commanded()
        self.chain(self.delivery, command, answered=[], ending="faulted", stopped="describe", disposition=None, manifest_digest=None, fault_code="agent")
        attempt = attempts._require_attempt(self.store, ATTEMPT)
        self.start = attempts._start_operation_id(attempt)
        self.domain = tokens.domain_of("workspace", self.workspace_identity)
        self.token = tokens.token_of(self.store, self.domain, 1)
        self.request = {"schema": settlement.SCHEMA, "operation_id": "settle-test", "attempt_id": ATTEMPT, "runtime_id": self.adapter.runtime_id, "start_operation_id": self.start, "assignment": self.expect(), "token": {key: self.token[key] for key in ("domain", "generation", "owner", "launch")}, "failure_digest": settlement.failure_digest(self.delivery)}

    def settle(self, **overrides):
        return settlement.settle_stopped(self.store, self.port, self.adapter, self.govern, request=overrides.get("request", self.request), delivery=self.delivery)

    def test_stopped_failure_preserves_axes_and_replays_without_observation(self):
        before = attempts.attempt_runtime_of(self.store, ATTEMPT)
        assignment = copy.deepcopy(self.session.live_assignment)
        output = os.path.join(self.roots["workspace"], "partial")
        with open(output, "w") as writing:
            writing.write("retained partial output")
        answer = self.settle()
        self.assertEqual(answer["state"], "settled")
        self.assertEqual(answer["outcome"]["execution_outcome"], "failed-stopped")
        self.assertEqual(before, attempts.attempt_runtime_of(self.store, ATTEMPT))
        self.assertEqual(assignment, self.session.live_assignment)
        self.assertEqual(self.adapter.stopped, [])
        self.assertEqual(self.adapter.normalized, [])
        self.assertTrue(os.path.exists(output))
        with mock.patch.object(self.adapter, "observe", side_effect=AssertionError("replayed observation")), mock.patch.object(self.port, "assignment_of", side_effect=AssertionError("replayed authority")):
            self.assertEqual(self.settle(), answer)

    def test_running_initial_observation_does_not_select_or_fence(self):
        self.adapter.observation["state"] = "running"
        self.assertEqual(self.settle()["state"], "held")
        self.assertIsNone(tokens.settlement_fence_of(self.store, self.domain, 1))
        self.assertEqual(settlement.status(self.store, self.request)["state"], "not-selected")

    def test_post_fence_observation_holds_and_all_acting_paths_refuse(self):
        observations = [{"state": "quiescent", "why": "first"}, {"state": "running", "why": "second"}]
        with mock.patch.object(self.adapter, "observe", side_effect=observations):
            self.assertEqual(self.settle()["state"], "held")
        self.assertFalse(tokens.effects_permitted(self.store, self.token))
        for action in (lambda: tokens.journal_launch(self.store, self.token, self.start), lambda: tokens.bind_container(self.store, self.token, self.adapter.runtime_id, launch=self.start), lambda: tokens.admit_activation(self.store, self.token, container=self.adapter.runtime_id), lambda: tokens.renew(self.store, self.token, execution=ATTEMPT, operation=self.start, expected_revision=0)):
            with self.assertRaises(ContractRefusal):
                action()
        self.session.live_assignment = None
        self.assertEqual(self.settle()["state"], "settled")

    def test_crash_at_each_durable_cut_resumes_same_selection(self):
        # Each subcase uses a newly built disposable fixture and the real journal.
        for cut in (settlement.INTENT, settlement.OUTCOME, tokens.RETURNED_KIND, settlement.RECEIPT):
            with self.subTest(cut=cut):
                case = StoppedSettlement("test_running_initial_observation_does_not_select_or_fence")
                case.setUp()
                try:
                    transact = case.store.transact
                    def interrupted(operation, kind, signature, action):
                        answer = transact(operation, kind, signature, action)
                        if kind == cut:
                            raise RuntimeError("simulated lost reply")
                        return answer
                    with mock.patch.object(case.store, "transact", side_effect=interrupted):
                        with self.assertRaises(RuntimeError):
                            case.settle()
                    state = settlement.status(case.store, case.request)["state"]
                    self.assertEqual(state, {settlement.INTENT: "held", settlement.OUTCOME: "release-pending", tokens.RETURNED_KIND: "returned-receipt-pending", settlement.RECEIPT: "settled"}[cut])
                    if cut in (tokens.RETURNED_KIND, settlement.RECEIPT):
                        with mock.patch.object(case.adapter, "observe", side_effect=AssertionError("new observation")):
                            self.assertEqual(case.settle()["state"], "settled")
                    else:
                        self.assertEqual(case.settle()["state"], "settled")
                finally:
                    case.doCleanups()

    def test_intent_failure_rolls_back_fence_and_selection(self):
        record = self.store._record
        def interrupted(operation, kind, *args):
            if kind == settlement.INTENT:
                raise RuntimeError("journal unavailable")
            return record(operation, kind, *args)
        with mock.patch.object(self.store, "_record", side_effect=interrupted):
            with self.assertRaises(RuntimeError):
                self.settle()
        self.assertIsNone(tokens.settlement_fence_of(self.store, self.domain, 1))
        self.assertEqual(settlement.status(self.store, self.request)["state"], "not-selected")
        self.assertEqual(self.settle()["state"], "settled")

    def test_collision_stale_assignment_and_foreign_runtime_refuse(self):
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal):
            self.settle()
        self.session.live_assignment = self.expect()
        changed = dict(self.request, runtime_id="foreign-runtime")
        with self.assertRaises(ContractRefusal):
            self.settle(request=changed)
        self.settle()
        for changed in (dict(self.request, operation_id="second-selection"), dict(self.request, failure_digest="sha256:" + "a" * 64)):
            with self.assertRaises(ContractRefusal):
                self.settle(request=changed)

    def test_old_receipt_never_returns_a_successor_generation(self):
        self.settle()
        later = tokens.acquire(self.store, self.domain, execution="later", operation="later-start")
        self.settle()
        self.assertFalse(tokens.token_of(self.store, self.domain, later["generation"])["returned"])

    def test_callbacks_are_outside_transactions_and_status_has_no_writes(self):
        observe = self.adapter.observe
        def observed(runtime):
            self.assertFalse(self.store._connection.in_transaction)
            return observe(runtime)
        with mock.patch.object(self.adapter, "observe", side_effect=observed):
            self.settle()
        before = self.store._connection.total_changes
        settlement.status(self.store, self.request)
        settlement.status(self.store, self.request)
        self.assertEqual(before, self.store._connection.total_changes)

    def test_surviving_or_unknown_writer_holds(self):
        for answer in (None, [{"helper_identity": "late-helper", "why": "pending"}]):
            with mock.patch.object(self.adapter, "surviving_helpers", return_value=answer):
                self.assertEqual(self.settle()["state"], "held")
        self.assertFalse(tokens.token_of(self.store, self.domain, 1)["returned"])

    def test_unknown_activation_and_missing_preparation_refuse_before_fence(self):
        for owner, name in ((tokens, "settle_activation"), (workspaces, "record_preparation")):
            with self.subTest(cut=name):
                case = StoppedSettlement()
                if name == "record_preparation":
                    # A missing owner read cannot become a positive cessation claim.
                    with mock.patch.object(workspaces, "preparation_completed", return_value=None):
                        with self.assertRaises(ContractRefusal):
                            self.settle()
                    self.assertIsNone(tokens.settlement_fence_of(self.store, self.domain, 1))
                    continue
                try:
                    with mock.patch.object(owner, name, return_value=None):
                        case.setUp()
                    with self.assertRaises(ContractRefusal):
                        case.settle()
                    self.assertIsNone(tokens.settlement_fence_of(case.store, case.domain, 1))
                    self.assertFalse(tokens.token_of(case.store, case.domain, 1)["returned"])
                finally:
                    case.doCleanups()

    def test_fenced_token_still_allows_expiry_revocation_and_manager_cessation(self):
        with mock.patch.object(self.adapter, "observe", side_effect=[{"state": "quiescent", "why": "first"}, {"state": "running", "why": "second"}]):
            self.settle()
        with mock.patch.object(self.store, "_now", return_value="2026-10-28T00:00:00.000Z"):
            self.govern.revoke(self.store, attempts._require_attempt(self.store, ATTEMPT), operation=self.start)
            self.assertTrue(tokens.token_of(self.store, self.domain, 1)["revoked"])
            self.assertEqual(self.settle()["state"], "settled")

    def test_two_real_connections_replay_one_selection(self):
        barrier = threading.Barrier(2)
        results = []
        failures = []
        def run():
            store = None
            try:
                store = ControlStore.open(self.path, incarnation="settlement-concurrent", clock=self.store._now)
                class Observer:
                    calls = 0
                    def observe(inner, runtime):
                        self.assertFalse(store._connection.in_transaction)
                        inner.calls += 1
                        if inner.calls == 1:
                            barrier.wait(timeout=5)
                        return {"state": "quiescent", "why": "deterministic observer"}
                results.append(settlement.settle_stopped(store, self.port, Observer(), self.govern, request=self.request, delivery=self.delivery))
            except BaseException as failure:
                failures.append(failure)
            finally:
                if store is not None:
                    store.close()
        threads = [threading.Thread(target=run) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual([result["state"] for result in results], ["settled", "settled"])
        self.assertEqual(results[0]["intent"], results[1]["intent"])
        self.assertEqual(results[0]["receipt"], results[1]["receipt"])

    def test_cancellation_can_still_stop_after_settlement_fence(self):
        with mock.patch.object(self.adapter, "observe", side_effect=[{"state": "quiescent", "why": "first"}, {"state": "running", "why": "second"}]):
            self.settle()
        attempts.request_cancellation(self.store, self.port, Agent(), self.adapter, attempt_id=ATTEMPT)
        self.assertEqual(len(self.adapter.stopped), 1)
        self.assertEqual(self.settle()["state"], "settled")

    def test_fence_wins_over_preflighted_renewal_replay(self):
        tokens.renew(self.store, self.token, execution=ATTEMPT, operation=self.start, expected_revision=0)
        acting = tokens._acting_record
        def interleaved(*args, **kwargs):
            with mock.patch.object(self.adapter, "observe", side_effect=[{"state": "quiescent", "why": "first"}, {"state": "running", "why": "second"}]):
                self.settle()
            return acting(*args, **kwargs)
        with mock.patch.object(tokens, "_acting_record", side_effect=interleaved):
            with self.assertRaises(ContractRefusal):
                tokens.renew(self.store, self.token, execution=ATTEMPT, operation=self.start, expected_revision=0)
        self.assertEqual(tokens.token_of(self.store, self.domain, 1)["revision"], 1)
        self.assertFalse(tokens.effects_permitted(self.store, self.token))

    def test_request_members_and_nominal_capabilities_refuse(self):
        for path in (("operation_id",), ("attempt_id",), ("runtime_id",), ("start_operation_id",), ("schema",), ("failure_digest",), ("assignment",), ("assignment", "work_ref"), ("assignment", "participant"), ("assignment", "generation"), ("assignment", "work_ref", "authority_uuid"), ("assignment", "work_ref", "work_id"), ("token",), ("token", "domain"), ("token", "generation"), ("token", "owner"), ("token", "launch")):
            changed = copy.deepcopy(self.request)
            target = changed
            for member in path[:-1]:
                target = target[member]
            target[path[-1]] = None
            for function in (lambda: self.settle(request=changed), lambda: settlement.status(self.store, changed)):
                with self.subTest(path=path), self.assertRaises(ContractRefusal):
                    function()
        with self.assertRaises(ContractRefusal):
            settlement.failure_digest(object())
        for malformed in (None, True, 0, "1"):
            with self.assertRaises(ContractRefusal):
                tokens.settlement_fence_of(self.store, self.domain, malformed)
        with self.assertRaises(ContractRefusal):
            workspaces.settlement_preparation(self.store, None)
        self.assertEqual(settlement.status(self.store, self.request)["state"], "not-selected")

    def test_inaccessible_output_is_preserved_and_not_inspected(self):
        with mock.patch.object(self.adapter, "observe", side_effect=[{"state": "quiescent", "why": "first"}, {"state": "running", "why": "second"}]):
            self.settle()
        os.chmod(self.roots["workspace"], 0)
        try:
            with mock.patch("os.scandir", side_effect=AssertionError("output inspection")):
                self.assertEqual(self.settle()["state"], "settled")
        finally:
            os.chmod(self.roots["workspace"], 0o700)
        self.assertEqual(self.adapter.normalized, [])

    def test_existing_readonly_store_reports_without_repair(self):
        self.settle()
        reader = ControlStore.open_readonly(self.path, incarnation="settlement-reader", clock=self.store._now)
        try:
            self.assertEqual(settlement.status(reader, self.request)["state"], "settled")
        finally:
            reader.close()

    def test_local_request_and_capability_rules(self):
        for field, value in (("schema", "baton.v12.stopped-settlement-request/999"), ("failure_digest", "sha256:" + "A" * 64), ("failure_digest", "sha256:abc"), ("failure_digest", "md5:" + "a" * 64), ("operation_id", "x" * 513)):
            changed = dict(self.request, **{field: value})
            for call in (lambda: self.settle(request=changed), lambda: settlement.status(self.store, changed)):
                with self.subTest(field=field, value=value), self.assertRaises(ContractRefusal):
                    call()
        with self.assertRaises(ContractRefusal):
            settlement.settle_stopped(self.store, self.port, self.adapter, self.govern, request=self.request, delivery=object())
        with mock.patch.object(self.delivery, "attempt_id", "another-attempt"):
            with self.assertRaises(ContractRefusal):
                self.settle()
        result = settlement.settle_stopped(self.store, self.port, object(), self.govern, request=self.request, delivery=self.delivery)
        self.assertEqual(result["state"], "held")
        self.assertFalse(result["selected"])
        self.assertIsNone(tokens.settlement_fence_of(self.store, self.domain, 1))
        self.store._connection.close()
        for call in (lambda: tokens.settlement_fence_of(self.store, self.domain, 1), lambda: workspaces.settlement_preparation(self.store, ATTEMPT)):
            with self.assertRaises(sqlite3.ProgrammingError):
                call()
