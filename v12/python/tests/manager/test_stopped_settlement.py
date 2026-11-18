"""Deterministic owner proof; no engine or provider is executed."""
import copy
import json
import os
import threading
import sqlite3
import unittest
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


class RevokedGenerationReplay(unittest.TestCase):
    """OWNER-REVOKED-REPLAY-20261118.md (W384870 G3; DESIGN DB-7 clarified first).

    After revocation an EXACT same-operation/same-operands retry of a committed
    act answers the committed record and grants nothing; a new act, changed
    operands, a foreign owner, an activation and anything under a settlement
    fence still refuse. Deterministic: one disposable store, no engine.
    """
    EXECUTION, OPERATION, LAUNCH = "attempt-support", "runtime.start:support", "launch:support"

    def setUp(self):
        from .token_support import TokenFixture
        self.fixture = TokenFixture(self)
        self.store = self.fixture.store
        self.domain = self.fixture.domain
        self.held = self.fixture.held(seconds=900)          # 14:00 -> expires 14:15
        self.launch = tokens.journal_launch(self.store, self.held, self.LAUNCH)

    def current(self):
        return tokens.token_of(self.store, self.domain, self.held["generation"])

    def rows(self):
        return self.store._connection.execute(
            "SELECT operation_id, kind, result FROM operations ORDER BY rowid").fetchall()

    def revoked(self, instant="2026-09-26T14:20:00.000Z"):
        """The deadline sweep's first act: the overdue generation is revoked, not replaced."""
        self.fixture.instant = instant
        record = tokens.revoke(self.store, "line-7/workspace", "workspace",
                               execution=self.EXECUTION, operation=self.OPERATION)
        self.assertEqual(record["generation"], self.held["generation"])
        self.assertTrue(self.current()["revoked"])
        return record

    def test_an_exact_launch_replay_after_revocation_answers_the_committed_record_and_changes_nothing(self):
        self.revoked()
        before = [tuple(row) for row in self.rows()]
        state = self.current()
        replay = tokens.journal_launch(self.store, self.held, self.LAUNCH)
        self.assertEqual(replay, self.launch)
        self.assertEqual([tuple(row) for row in self.rows()], before, "a replay writes no row")
        after = self.current()
        self.assertEqual(after, state)
        self.assertTrue(after["revoked"])
        self.assertFalse(after["returned"])
        self.assertEqual((after["generation"], after["expires_at"]), (self.held["generation"], self.held["expires_at"]))
        self.assertIsNone(after["container"])
        self.assertFalse(tokens.effects_permitted(self.store, self.held))
        # and again: a replay of a replay is the same record, still nothing written
        self.assertEqual(tokens.journal_launch(self.store, self.held, self.LAUNCH), self.launch)
        self.assertEqual([tuple(row) for row in self.rows()], before)

    def test_a_new_act_changed_operands_or_a_foreign_owner_still_refuse_after_revocation(self):
        self.revoked()
        before = [tuple(row) for row in self.rows()]
        for name, act, fragment in (
                ("a binding never committed", lambda: tokens.bind_container(self.store, self.held, "container-support", launch=self.LAUNCH), "REVOKED"),
                ("a launch with changed operands", lambda: tokens.journal_launch(self.store, self.held, "launch:another"), "different kind or signature"),
                ("a renewal never committed", lambda: tokens.renew(self.store, self.held, execution=self.EXECUTION, operation=self.OPERATION, expected_revision=0), "REVOKED"),
                ("the committed launch under a foreign owner", lambda: tokens.journal_launch(self.store, dict(self.held, owner="somebody-else"), self.LAUNCH), "different kind or signature"),
                ("the committed launch under another generation", lambda: tokens.journal_launch(self.store, dict(self.held, generation=2), self.LAUNCH), "")):
            with self.subTest(act=name):
                with self.assertRaises(ContractRefusal) as caught:
                    act()
                self.assertIn(fragment, caught.exception.message)
        self.assertEqual([tuple(row) for row in self.rows()], before, "nothing was written by a refused act")
        self.assertFalse(tokens.effects_permitted(self.store, self.held))

    def test_a_committed_renewal_is_not_replayed_after_revocation_and_nothing_extends(self):
        """The smallest correction stops at the acting record. A renewal proves
        ownership in its own PREFLIGHT (`_extended`, before `_acting_record`), so
        an exact renewal retry after revocation refuses there -- the ruling says
        a committed act MAY be answered and selects no renewal change; what it
        requires is that nothing extends, revives or is written, measured here.
        The committed renewal stays readable through `token_of` and verified
        against its decision record (RenewalDecisionRecord)."""
        self.fixture.instant = "2026-09-26T14:10:00.000Z"
        renewed = tokens.renew(self.store, self.held, execution=self.EXECUTION, operation=self.OPERATION, expected_revision=0)
        self.assertEqual((renewed["revision"], renewed["expires_at"]), (1, "2026-09-26T14:25:00.000Z"))
        self.revoked("2026-09-26T14:30:00.000Z")
        before = [tuple(row) for row in self.rows()]
        for revision in (0, 1):
            with self.subTest(expected_revision=revision):
                with self.assertRaises(ContractRefusal) as caught:
                    tokens.renew(self.store, self.held, execution=self.EXECUTION, operation=self.OPERATION, expected_revision=revision)
                self.assertIn("REVOKED", caught.exception.message)
        self.assertEqual([tuple(row) for row in self.rows()], before)
        state = self.current()
        self.assertEqual((state["revision"], state["expires_at"], state["revoked"], state["returned"]),
                         (1, "2026-09-26T14:25:00.000Z", True, False))
        self.assertTrue(state["expired"])
        self.assertFalse(tokens.effects_permitted(self.store, self.held))
        # the committed launch, by contrast, is answered -- the ruled case
        self.assertEqual(tokens.journal_launch(self.store, self.held, self.LAUNCH), self.launch)
        self.assertEqual([tuple(row) for row in self.rows()], before)

    def test_a_revoked_generation_that_was_returned_keeps_every_guard(self):
        """Review 2026-11-18T04:17:54Z [P1], the reviewer's returned-probe as a witness:
        the reclaim revokes first and returns after, so the revocation record outlives
        the return. A RETURNED generation is not the ruled still-held case: its exact
        committed launch and binding refuse as they did, and so does everything else."""
        bound = tokens.bind_container(self.store, self.held, "container-support", launch=self.LAUNCH)
        cessation = {"domain": self.domain, "generation": self.held["generation"], "launch": self.LAUNCH,
                     "container": "container-support", "stopped": True, "helpers": []}
        self.revoked()
        tokens.returned(self.store, self.held, cessation=cessation, reclaiming=True)
        state = self.current()
        self.assertEqual((state["revoked"], state["returned"]), (True, True))
        self.assertIsNone(tokens.settlement_fence_of(self.store, self.domain, self.held["generation"]))
        before = [tuple(row) for row in self.rows()]
        for name, act in (("the committed launch", lambda: tokens.journal_launch(self.store, self.held, self.LAUNCH)),
                          ("the committed binding", lambda: tokens.bind_container(self.store, self.held, "container-support", launch=self.LAUNCH)),
                          ("a renewal", lambda: tokens.renew(self.store, self.held, execution=self.EXECUTION, operation=self.OPERATION, expected_revision=0)),
                          ("an activation", lambda: tokens.admit_activation(self.store, self.held, container="container-support"))):
            with self.subTest(act=name):
                with self.assertRaises(ContractRefusal) as caught:
                    act()
                # `_owning`'s refusal, in its own order: the revocation is read before the
                # return, so the sentence names the withdrawal; what matters is that the
                # branch was not taken and the guard refused
                self.assertEqual(caught.exception.code, "already-terminal")
                self.assertIn("is refused", caught.exception.message)
        self.assertEqual([tuple(row) for row in self.rows()], before)
        self.assertFalse(tokens.effects_permitted(self.store, self.held))
        # and once a REPLACEMENT generation holds the resource, the old one still answers nothing
        newer = self.fixture.held(operation="runtime.start:next", execution="attempt-next", attempt="attempt-next")
        self.assertEqual(newer["generation"], self.held["generation"] + 1)
        for name, act in (("the old committed launch", lambda: tokens.journal_launch(self.store, self.held, self.LAUNCH)),
                          ("the old committed binding", lambda: tokens.bind_container(self.store, self.held, "container-support", launch=self.LAUNCH))):
            with self.subTest(act=name):
                with self.assertRaises(ContractRefusal):
                    act()
        # while the replacement's own acts are untouched by any of this
        launched = tokens.journal_launch(self.store, newer, "launch:next")
        self.assertEqual(launched["generation"], newer["generation"])
        self.assertEqual(tokens.journal_launch(self.store, newer, "launch:next"), launched)
        self.assertTrue(self.current()["revoked"])

    def test_a_revoked_generation_superseded_without_a_return_record_keeps_every_guard(self):
        """The branch's own fourth condition, driven directly: a newer acquisition in
        the domain disqualifies the replay even if the return record were missing."""
        from baton_v12.worker_manager.store import _recorded, manager_signature
        self.revoked()
        self.assertTrue(tokens._revoked_and_still_held(self.store, self.domain, self.held["generation"]))
        self.assertEqual(tokens.journal_launch(self.store, self.held, self.LAUNCH), self.launch)
        # a newer acquisition record alone -- the shape the store holds after a return this test
        # hides from the predicate, so that the fourth condition is what decides
        following = self.held["generation"] + 1
        document = {"domain": self.domain, "generation": following, "owner": "next-owner",
                    "execution": "attempt-next", "operation": "runtime.start:next", "attempt": "attempt-next",
                    "acquired_at": self.fixture.instant, "expires_at": "2026-09-26T15:00:00.000Z", "permission": None}
        self.store._record(tokens._acquired_id(self.domain, following), tokens.ACQUIRED_KIND,
                           manager_signature(tokens.ACQUIRED_KIND, document), "committed", _recorded(document), None)
        with mock.patch.object(tokens, "_returned_id", side_effect=lambda domain, generation: f"hidden:{domain}:{generation}"):
            self.assertFalse(tokens._revoked_and_still_held(self.store, self.domain, self.held["generation"]))
            with self.assertRaises(ContractRefusal) as caught:
                tokens.journal_launch(self.store, self.held, self.LAUNCH)
            self.assertIn("REVOKED", caught.exception.message)

    def test_the_settlement_fence_still_refuses_an_exact_replay(self):
        self.revoked()
        self.store._connection.execute("BEGIN IMMEDIATE")
        tokens._fence_settlement(self.store, self.held, "release")
        self.store._connection.execute("COMMIT")
        self.assertIsNotNone(tokens.settlement_fence_of(self.store, self.domain, self.held["generation"]))
        for name, act in (("the committed launch", lambda: tokens.journal_launch(self.store, self.held, self.LAUNCH)),
                          ("a binding", lambda: tokens.bind_container(self.store, self.held, "container-support", launch=self.LAUNCH)),
                          ("a renewal", lambda: tokens.renew(self.store, self.held, execution=self.EXECUTION, operation=self.OPERATION, expected_revision=0))):
            with self.subTest(act=name):
                with self.assertRaises(ContractRefusal) as caught:
                    act()
                self.assertIn("fenced for stopped-execution settlement", caught.exception.message)

    def test_expiry_of_the_revoked_generation_grants_nothing_and_a_competitor_still_waits(self):
        self.revoked()
        self.fixture.instant = "2026-09-26T16:00:00.000Z"
        self.assertEqual(tokens.journal_launch(self.store, self.held, self.LAUNCH), self.launch)
        state = self.current()
        self.assertTrue(state["expired"] and state["revoked"] and not state["returned"])
        self.assertFalse(tokens.effects_permitted(self.store, self.held))
        with self.assertRaises(ContractRefusal):
            tokens.acquire(self.store, self.domain, operation="competitor", execution="other")
        self.assertEqual(self.current()["generation"], self.held["generation"])

    def test_a_bound_generations_activation_still_refuses_after_revocation(self):
        """Caller inspection, measured: `maintenance` starts through launch -> bind ->
        admit_activation; a replayed launch and a replayed binding answer their records,
        and the activation -- the act that would authorize the engine -- refuses."""
        bound = tokens.bind_container(self.store, self.held, "container-support", launch=self.LAUNCH)
        self.revoked()
        before = [tuple(row) for row in self.rows()]
        self.assertEqual(tokens.journal_launch(self.store, self.held, self.LAUNCH), self.launch)
        self.assertEqual(tokens.bind_container(self.store, self.held, "container-support", launch=self.LAUNCH), bound)
        with self.assertRaises(ContractRefusal) as caught:
            tokens.admit_activation(self.store, self.held, container="container-support")
        self.assertIn("REVOKED", caught.exception.message)
        self.assertEqual([tuple(row) for row in self.rows()], before)
        self.assertFalse(tokens.effects_permitted(self.store, self.held))


class RenewalDecisionRecord(unittest.TestCase):
    """Owner selection 2026-11-17 (RENEWAL-DECISION.md option A), review 2026-10-31T03:05:05Z P1.

    The renewal REQUEST keeps its identity, signed operands and lost-reply replay; the
    decided instants are a self-signed DECISION record written in the same transaction.
    Every reader and every replay verifies the request against its decision.
    """
    EXECUTION, OPERATION = "attempt-support", "runtime.start:support"

    def setUp(self):
        from .token_support import TokenFixture
        self.fixture = TokenFixture(self)
        self.store = self.fixture.store
        self.held = self.fixture.held(seconds=900)
        self.fixture.instant = "2026-09-26T14:10:00.000Z"

    def renew(self, revision=0):
        return tokens.renew(self.store, self.held, execution=self.EXECUTION, operation=self.OPERATION,
                            expected_revision=revision)

    def current(self):
        return tokens.token_of(self.store, self.fixture.domain, self.held["generation"])

    def rows(self, kind):
        return self.store._connection.execute(
            "SELECT operation_id, signature, result FROM operations WHERE kind = ? ORDER BY rowid", (kind,)).fetchall()

    def rewrite(self, kind, **changes):
        row = self.rows(kind)[0]
        document = json.loads(row["result"])
        document.update(changes)
        self.store._connection.execute("UPDATE operations SET result = ? WHERE operation_id = ?",
                                       (json.dumps(document, sort_keys=True), row["operation_id"]))

    def every_reader_refuses(self, fragment):
        """token_of, the direct renew retry (replay) and an owner-gated act all refuse with `fragment`."""
        for name, act in (("token_of", self.current), ("renew retry", lambda: self.renew(0)),
                          ("journal_launch through _owning", lambda: tokens.journal_launch(self.store, self.held, "launch:probe"))):
            with self.subTest(reader=name):
                with self.assertRaises(ContractRefusal) as caught:
                    act()
                self.assertIn(fragment, caught.exception.message)

    def test_an_honest_renewal_writes_request_and_decision_together_and_reads_through_both(self):
        first = self.renew(0)
        requests, decisions = self.rows(tokens.RENEWED_KIND), self.rows(tokens.RENEWAL_DECIDED_KIND)
        self.assertEqual((len(requests), len(decisions)), (1, 1))
        decision = json.loads(decisions[0]["result"])
        self.assertEqual(decision, json.loads(decisions[0]["signature"])["operands"], "the decision IS its signed operands")
        self.assertEqual(decision, {"version": tokens.TOKEN_VERSION, "domain": self.fixture.domain, "generation": 1,
                                    "revision": 1, "renewed_at": "2026-09-26T14:10:00.000Z",
                                    "expires_at": "2026-09-26T14:25:00.000Z"})
        self.assertNotIn("renewed_at", json.loads(requests[0]["signature"])["operands"], "the request signs the request, not the clock")
        self.assertEqual((first["expires_at"], first["renewed_at"]), (decision["expires_at"], decision["renewed_at"]))
        answer = self.current()
        self.assertEqual((answer["revision"], answer["expires_at"], answer["renewed_at"], answer["expired"]),
                         (1, decision["expires_at"], decision["renewed_at"], False))
        self.fixture.instant = "2026-09-26T14:25:00.000Z"
        self.assertTrue(self.current()["expired"])

    def test_a_lost_reply_replays_the_same_renewal_under_another_clock_without_a_second_decision(self):
        first = self.renew(0)
        self.fixture.instant = "2026-09-26T14:13:00.000Z"
        self.assertEqual(self.renew(0), first)
        self.assertEqual((len(self.rows(tokens.RENEWED_KIND)), len(self.rows(tokens.RENEWAL_DECIDED_KIND))), (1, 1))
        self.assertEqual(self.current()["revision"], 1)
        with self.assertRaises(ContractRefusal):
            self.renew(5)  # a revision ahead of the state is refused, not decided

    def test_a_rewritten_request_deadline_refuses_at_every_reader_and_replay(self):
        self.renew(0)
        self.fixture.instant = "2030-01-01T00:00:00.000Z"
        self.assertTrue(self.current()["expired"], "honest: expired")
        self.rewrite(tokens.RENEWED_KIND, expires_at="2099-01-01T00:00:00.000Z")
        self.every_reader_refuses("changed after the renewal was decided")

    def test_a_rewritten_request_renewed_at_refuses_too(self):
        self.renew(0)
        self.rewrite(tokens.RENEWED_KIND, renewed_at="2026-09-26T14:11:00.000Z")
        self.every_reader_refuses("changed after the renewal was decided")

    def test_a_corrupted_decision_refuses(self):
        self.renew(0)
        self.rewrite(tokens.RENEWAL_DECIDED_KIND, expires_at="2099-01-01T00:00:00.000Z")
        self.every_reader_refuses("signed operands")

    def test_a_renewal_without_a_decision_record_is_refused_not_adopted(self):
        """Every renewal committed before this correction looks like this: fail closed, no adoption."""
        self.renew(0)
        self.store._connection.execute("DELETE FROM operations WHERE kind = ?", (tokens.RENEWAL_DECIDED_KIND,))
        self.every_reader_refuses("no committed decision record")
        self.assertEqual(len(self.rows(tokens.RENEWAL_DECIDED_KIND)), 0, "nothing wrote a decision from the old bytes")

    def test_a_decision_about_another_renewal_does_not_verify_this_one(self):
        from baton_v12.worker_manager.store import _recorded, manager_signature
        self.renew(0)
        identity = tokens._renewal_decision_id(self.fixture.domain, 1, 1)
        self.store._connection.execute("DELETE FROM operations WHERE operation_id = ?", (identity,))
        for member, value in (("revision", 2), ("generation", 2), ("domain", "workspace:line-8/workspace")):
            with self.subTest(member=member):
                other = {"version": tokens.TOKEN_VERSION, "domain": self.fixture.domain, "generation": 1, "revision": 1,
                         "renewed_at": "2026-09-26T14:10:00.000Z", "expires_at": "2026-09-26T14:25:00.000Z", member: value}
                self.store._record(identity, tokens.RENEWAL_DECIDED_KIND, manager_signature(tokens.RENEWAL_DECIDED_KIND, other),
                                   "committed", _recorded(other), None)
                self.every_reader_refuses("a decision about another renewal")
                self.store._connection.execute("DELETE FROM operations WHERE operation_id = ?", (identity,))

    def test_a_fault_after_the_decision_rolls_both_halves_back(self):
        original = ControlStore._record

        def failing(self_store, operation_id, kind, *rest):
            if kind == tokens.RENEWED_KIND:
                raise RuntimeError("the request row could not be written")
            return original(self_store, operation_id, kind, *rest)
        with mock.patch.object(ControlStore, "_record", failing):
            with self.assertRaises(RuntimeError):
                self.renew(0)
        self.assertEqual((len(self.rows(tokens.RENEWED_KIND)), len(self.rows(tokens.RENEWAL_DECIDED_KIND))), (0, 0),
                         "neither half survives the rolled-back transaction")
        self.assertEqual(self.current()["revision"], 0)
        self.assertEqual(self.renew(0)["revision"], 1, "the next honest renewal is the first")
        self.assertEqual((len(self.rows(tokens.RENEWED_KIND)), len(self.rows(tokens.RENEWAL_DECIDED_KIND))), (1, 1))

    def test_the_expiry_judgement_reads_the_verified_renewal(self):
        """`_judge_expired` correlates against the renewed deadline; a corrupted renewal cannot feed it."""
        self.renew(0)
        self.rewrite(tokens.RENEWED_KIND, expires_at="2099-01-01T00:00:00.000Z")
        self.fixture.instant = "2030-01-01T00:00:00.000Z"
        with self.assertRaises(ContractRefusal) as caught:
            self.renew(1)
        self.assertIn("changed after the renewal was decided", caught.exception.message)
        self.assertEqual(self.rows(tokens.EXPIRED_KIND), [], "no expiry judgement was written from an unverifiable deadline")
