"""W101493: interrupted integration is inspectable and operator-held."""

import json
import os
from unittest import mock

from baton_v12.integration import block_target, lease_of, recovery, runtime

from .test_execution import ExecutionCase, IMPORTED, Model, profile


class RecoveryCase(ExecutionCase):

    def interrupted(self, *, state="quiescent", model=None):
        self.recorded(self, "integration-attempt", state)
        granted = self.grant("integration-attempt")
        assignment = runtime.compose_assignment(
            self.coordinator, self.manager, profile=profile(),
            canonical_target_id=self.target_id, entry_id=granted["entry"]["entry_id"],
            lease_id="integration-lease", fence=granted["lease"]["fence"],
            attempt_id="integration-attempt")
        delivery = runtime.materialize_delivery(
            self.launch, attempt_id="integration-attempt",
            workspace_group=self.group)
        runtime.publish_assignment(delivery, assignment)
        if model is not None:
            model.run(delivery, assignment)
        return delivery, assignment

    @property
    def target_id(self):
        from .fixtures import TARGET
        return TARGET

    def grant(self, attempt_id):
        from baton_v12.integration import grant_lease
        return grant_lease(
            self.coordinator, canonical_target_id=self.target_id,
            entry_id="entry-1",
            lease_id="integration-lease", integrator_participant="baton.merge",
            attempt_id=attempt_id)


class RestartAlwaysHolds(RecoveryCase):

    def test_untouched_target_is_held_without_an_automatic_action(self):
        before = self.target_state()
        delivery, assignment = self.interrupted()
        status = recovery.hold_interrupted(
            self.coordinator, self.manager, delivery, assignment)
        self.assertEqual(status["state"], "operator-held")
        self.assertEqual(status["target_state"], "blocked")
        self.assertEqual(status["reason"], "runtime-interrupted")
        self.assertEqual(status["lease_state"], "live")
        self.assertEqual(status["evidence"]["delivery_state"], "waiting")
        self.assertEqual(self.target_state(), before)

    def test_interruption_before_delivery_is_still_a_durable_hold(self):
        self.recorded(self, "integration-attempt")
        granted = self.grant("integration-attempt")
        assignment = runtime.compose_assignment(
            self.coordinator, self.manager, profile=profile(),
            canonical_target_id=self.target_id,
            entry_id=granted["entry"]["entry_id"],
            lease_id="integration-lease", fence=granted["lease"]["fence"],
            attempt_id="integration-attempt")
        status = recovery.hold_interrupted(
            self.coordinator, self.manager, None, assignment)
        self.assertEqual(status["reason"], "runtime-ambiguous")
        self.assertEqual(status["evidence"]["delivery_state"], "not-assigned")
        self.assertIsNone(status["locators"]["result_document"])
        self.assertEqual(status["lease_state"], "live")

    def test_a_completed_looking_result_is_evidence_not_acceptance(self):
        delivery, assignment = self.interrupted(
            model=Model(target=self.target, runs=False))
        status = recovery.hold_interrupted(
            self.coordinator, self.manager, delivery, assignment)
        self.assertEqual(status["evidence"]["result_outcome"], "integrated")
        self.assertEqual(status["entry_state"], "held")
        self.assertEqual(status["lease_state"], "live")
        self.assertEqual(self.states()[0][1], "held")
        self.assertTrue(os.path.exists(os.path.join(self.target, IMPORTED)))

    def test_mixed_or_untrusted_material_is_retained_behind_the_hold(self):
        delivery, assignment = self.interrupted()
        result = os.path.join(delivery.result_root, runtime.RESULT_DOCUMENT)
        with open(result, "wb") as writing:
            writing.write(b"{not-json")
        status = recovery.hold_interrupted(
            self.coordinator, self.manager, delivery, assignment)
        self.assertEqual(status["reason"], "result-unreadable")
        self.assertEqual(status["evidence"]["delivery_state"], "held")
        with open(result, "rb") as reading:
            self.assertEqual(reading.read(), b"{not-json")

    def test_unknown_runtime_is_held_and_cannot_be_recovered(self):
        delivery, assignment = self.interrupted(state="uncertain")
        status = recovery.hold_interrupted(
            self.coordinator, self.manager, delivery, assignment)
        self.assertEqual(status["reason"], "runtime-ambiguous")
        caught = self.refusal(recovery.abandon_held_lease,
                              self.coordinator, self.manager,
                              delivery, assignment)
        self.assertEqual(caught.category, "policy")
        self.assertEqual(status["lease_state"], "live")


class StatusAndExplicitRecovery(RecoveryCase):

    def test_status_exposes_identities_and_locators_but_not_payload_detail(self):
        delivery, assignment = self.interrupted()
        secret = "credential-shaped-private-material"
        result = os.path.join(delivery.result_root, runtime.RESULT_DOCUMENT)
        answer = {"schema": runtime.RESULT_SCHEMA,
                  "attempt_id": assignment["attempt_id"],
                  "lease_id": assignment["lease_id"],
                  "canonical_target_id": assignment["canonical_target_id"],
                  "entry_id": assignment["entry_id"],
                  "fence": assignment["fence"], "outcome": "held",
                  "detail": {"reason": "mixed", "private": secret}}
        with open(result, "w", encoding="utf-8") as writing:
            json.dump(answer, writing)
        status = recovery.hold_interrupted(
            self.coordinator, self.manager, delivery, assignment)
        rendered = json.dumps(status, sort_keys=True)
        self.assertNotIn(secret, rendered)
        self.assertEqual(status["attempt_id"], "integration-attempt")
        self.assertEqual(status["lease_id"], "integration-lease")
        self.assertEqual(status["fence"], assignment["fence"])
        self.assertEqual(status["locators"]["result_document"], result)

    def test_an_existing_untrusted_block_reason_is_not_projected(self):
        delivery, assignment = self.interrupted()
        secret = "credential-shaped-private-material"
        block_target(self.coordinator,
                     canonical_target_id=assignment["canonical_target_id"],
                     entry_id=assignment["entry_id"],
                     lease_id=assignment["lease_id"],
                     fence=assignment["fence"], reason=secret,
                     detail={"private": secret})
        status = recovery.held_status(
            self.coordinator, self.manager, delivery, assignment)
        self.assertEqual(status["reason"], "integration-held")
        self.assertNotIn(secret, json.dumps(status, sort_keys=True))

    def test_explicit_abandonment_requires_quiescence_and_keeps_the_hold(self):
        delivery, assignment = self.interrupted()
        recovery.hold_interrupted(
            self.coordinator, self.manager, delivery, assignment)
        status = recovery.abandon_held_lease(
            self.coordinator, self.manager, delivery, assignment)
        self.assertEqual(status["state"], "operator-held")
        self.assertEqual(status["entry_state"], "held")
        self.assertEqual(status["lease_state"], "abandoned")

    def test_status_preflight_precedes_the_last_runtime_observation(self):
        delivery, assignment = self.interrupted()
        recovery.hold_interrupted(
            self.coordinator, self.manager, delivery, assignment)
        actual = recovery.lease_of

        def manager_moves_during_status(*operands, **named):
            self.started("integration-attempt", "uncertain")
            return actual(*operands, **named)

        with mock.patch.object(recovery, "lease_of",
                               side_effect=manager_moves_during_status):
            caught = self.refusal(recovery.abandon_held_lease,
                                  self.coordinator, self.manager,
                                  delivery, assignment)
        self.assertEqual(caught.category, "policy")
        self.assertEqual(lease_of(
            self.coordinator, assignment["lease_id"])["state"], "live")

    def test_an_invalid_delivery_refuses_before_abandonment(self):
        delivery, assignment = self.interrupted()
        recovery.hold_interrupted(
            self.coordinator, self.manager, delivery, assignment)
        caught = self.refusal(recovery.abandon_held_lease,
                              self.coordinator, self.manager,
                              object(), assignment)
        self.assertEqual(caught.category, "policy")
        self.assertEqual(lease_of(
            self.coordinator, assignment["lease_id"])["state"], "live")

    def test_successful_abandonment_replays_after_the_runtime_advances(self):
        delivery, assignment = self.interrupted()
        recovery.hold_interrupted(
            self.coordinator, self.manager, delivery, assignment)
        first = recovery.abandon_held_lease(
            self.coordinator, self.manager, delivery, assignment)
        self.started("integration-attempt", "destroyed")
        second = recovery.abandon_held_lease(
            self.coordinator, self.manager, delivery, assignment)
        self.assertEqual(first["lease_state"], "abandoned")
        self.assertEqual(second["lease_state"], "abandoned")

    def test_status_is_read_only(self):
        delivery, assignment = self.interrupted()
        recovery.hold_interrupted(
            self.coordinator, self.manager, delivery, assignment)
        first = recovery.held_status(
            self.coordinator, self.manager, delivery, assignment)
        second = recovery.held_status(
            self.coordinator, self.manager, delivery, assignment)
        self.assertEqual(first, second)
        self.assertEqual(second["lease_state"], "live")
