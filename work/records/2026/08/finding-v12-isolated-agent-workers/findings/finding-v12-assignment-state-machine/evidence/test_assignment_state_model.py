"""Executable acceptance scenarios for the W151 1-ruled model."""

import unittest

from assignment_state_model import (
	GOLDEN_BEARER, GOLDEN_VERIFIER, V11, V12, Authority, ControlStore,
	Deployment, Manager, Refusal, token_verifier)


class Clock:
	def __init__(self, value=0):
		self.value = value

	def __call__(self):
		return self.value


def accepted(manager, suffix="1", participant="baton.codex", expires=100):
	offer_id = f"offer-{suffix}"
	token = f"secret-{suffix}"
	manager.offer(offer_id, participant, f"attempt-{suffix}", token, expires)
	manager.accept(offer_id, token)
	return offer_id


class AssignmentStateTests(unittest.TestCase):
	def setUp(self):
		self.clock = Clock(10)
		self.deployment = Deployment(certified_contracts={V11, V12})
		self.authority = Authority(
			work_id="full-W1", deployment=self.deployment, contract=V12)
		self.store = ControlStore()
		self.manager = Manager(self.authority, self.store, self.clock)

	def second_work(self, work_id="full-W2", contract=V12):
		"""Another Work in the SAME authority, deployment and control store."""

		authority = Authority(
			work_id=work_id, deployment=self.deployment, contract=contract)
		return authority, Manager(authority, self.store, self.clock)

	# --- offer, token, and settlement boundaries ------------------------

	def test_expired_and_replayed_tokens_never_claim(self):
		self.manager.offer("old", "baton.codex", "attempt-old", "old-token", 11)
		self.clock.value = 11
		with self.assertRaisesRegex(Refusal, "expired"):
			self.manager.accept("old", "old-token")
		self.assertIsNone(self.authority.assignment())

		self.clock.value = 12
		offer_id = accepted(self.manager, "fresh", expires=20)
		with self.assertRaisesRegex(Refusal, "replay"):
			self.manager.accept(offer_id, "secret-fresh")
		self.assertIsNone(self.authority.assignment())

	def test_restart_before_claim_uses_durable_accept_even_after_expiry(self):
		offer_id = accepted(self.manager, expires=20)
		self.clock.value = 25
		restarted = Manager(self.authority, self.store, self.clock)
		assignment = restarted.claim(offer_id)
		self.assertEqual(assignment.generation, 1)
		self.assertEqual(self.authority.work.generation_counter, 1)

	def test_settlement_timeout_never_revives_the_consumed_token(self):
		offer_id = accepted(self.manager, expires=20)
		self.clock.value = self.store.offers[offer_id].settle_by
		self.manager.settlement_timeout(offer_id)
		with self.assertRaisesRegex(Refusal, "replay"):
			self.manager.accept(offer_id, "secret-1")
		with self.assertRaisesRegex(Refusal, "not accepted"):
			self.manager.claim(offer_id)
		self.assertIsNone(self.authority.assignment())

		fresh = accepted(self.manager, "2", expires=200)
		self.assertEqual(self.manager.claim(fresh).generation, 1)

	def test_settlement_timeout_cannot_hide_an_already_committed_claim(self):
		offer_id = accepted(self.manager, expires=20)
		offer = self.store.offers[offer_id]
		committed = self.authority.claim(offer.participant, offer.claim_op_id)

		# The authority committed, but the manager lost the response before it
		# recorded the assignment in its control store. A timeout must reconcile
		# that fixed operation rather than terminally hiding a live assignment.
		self.manager.settlement_timeout(offer_id)
		restarted = Manager(self.authority, self.store, self.clock)
		self.assertEqual(restarted.claim(offer_id), committed)
		self.assertEqual(self.store.offers[offer_id].state, "claimed")

	def test_offer_uniqueness_is_scoped_per_work_in_a_shared_store(self):
		self.manager.offer("offer-1", "baton.codex", "attempt-1", "s1", 100)
		with self.assertRaisesRegex(Refusal, "nonterminal offer exists"):
			self.manager.offer("offer-1b", "baton.claude", "attempt-1b", "s2", 100)

		_, other = self.second_work()
		offer = other.offer("offer-2", "baton.claude", "attempt-2", "s3", 100)
		self.assertEqual(offer.work_ref, ("authority-uuid", "full-W2"))

	def test_offer_and_claim_require_free_participant_capacity(self):
		self.authority.claim("baton.codex", "claim:elsewhere")
		other_authority, other = self.second_work()
		with self.assertRaisesRegex(Refusal, "no free claim capacity"):
			other.offer("offer-2", "baton.codex", "attempt-2", "s2", 100)

		self.authority.end(self.authority.assignment(), "release:first")
		offer_id = accepted(other, "2", expires=200)
		self.authority.claim("baton.codex", "claim:again")
		with self.assertRaisesRegex(Refusal, "ONE active claim"):
			other.claim(offer_id)
		self.assertEqual(self.store.offers[offer_id].state, "claim-refused")
		self.assertIsNone(other_authority.assignment())

	def test_competing_claim_wins_atomically_and_offer_cannot_activate(self):
		offer_id = accepted(self.manager)
		winner = self.authority.claim("baton.claude", "claim:competitor")
		with self.assertRaisesRegex(Refusal, "already claimed"):
			self.manager.claim(offer_id)
		self.assertEqual(winner.generation, 1)
		self.assertEqual(self.store.offers[offer_id].state, "claim-refused")

	# --- W4487: declining without echoing the bearer ---------------------
	#
	# The two frozen contracts contradicted each other — W151 §7 required
	# the exact unspent token to decline, worker-control 1.0 and its schema
	# require `claim_token: null` — and the approver kept the non-secret
	# shape. These pin every property the token requirement was carrying,
	# so the supersession is a change of AUTHORIZATION and not a loss of
	# one.

	def _decline(self, offer_id="offer-1", attempt_id="attempt-1",
	             work_ref=None, reason="the worker has no capacity",
	             op_id="decide-1"):
		return self.manager.decline(
			offer_id, attempt_id,
			self.authority.work_ref() if work_ref is None else work_ref,
			reason, op_id)

	def test_decline_needs_no_bearer_and_kills_the_token(self):
		self.manager.offer("offer-1", "baton.codex", "attempt-1", "secret-1", 100)
		offer = self._decline()
		self.assertEqual(offer.state, "declined")
		self.assertTrue(offer.verifier_spent,
		                "the decline did not consume the offer's verifier")
		self.assertEqual(offer.decline_reason, "the worker has no capacity")
		# No claim, no assignment, no capacity taken: refusing authority is
		# not a quieter way of taking it.
		self.assertIsNone(self.authority.assignment())
		self.assertIsNone(self.authority.work.handler)
		self.assertEqual(self.authority.work.generation_counter, 0)
		self.assertTrue(
			self.deployment.slots.free("baton.codex", self.authority.work.work_id))
		# And the bearer is dead afterwards, exactly as if it had been spent
		# by an acceptance — which is the property W151 §7 was protecting.
		with self.assertRaisesRegex(Refusal, "replay"):
			self.manager.accept("offer-1", "secret-1")
		self.authority.assert_invariants()

	def test_accept_still_requires_the_exact_unspent_bearer(self):
		"""The other half of the ruling, and the one it would be easy to
		lose: acceptance is unchanged."""

		self.manager.offer("offer-1", "baton.codex", "attempt-1", "secret-1", 100)
		with self.assertRaisesRegex(Refusal, "mismatch"):
			self.manager.accept("offer-1", "not-the-secret")
		self.assertIsNone(self.authority.assignment())
		self.manager.accept("offer-1", "secret-1")
		self.assertTrue(self.store.offers["offer-1"].verifier_spent)
		self.assertEqual(self.manager.claim("offer-1").generation, 1)

	def test_a_decline_cannot_terminate_a_differently_bound_offer(self):
		"""The id alone is what a caller NAMES; the binding is what proves
		it is talking about the offer it thinks it is."""

		self.manager.offer("offer-1", "baton.codex", "attempt-1", "secret-1", 100)
		other_authority, other_manager = self.second_work()
		other_manager.offer("offer-2", "baton.codex", "attempt-2", "secret-2", 100)

		# Right offer id, another offer's attempt.
		with self.assertRaisesRegex(Refusal, "binding does not match"):
			self._decline(attempt_id="attempt-2", op_id="decide-wrong-attempt")
		# Right offer id, another Work.
		with self.assertRaisesRegex(Refusal, "binding does not match"):
			self._decline(work_ref=other_authority.work_ref(),
			              op_id="decide-wrong-work")
		# An offer that does not exist at all.
		with self.assertRaisesRegex(Refusal, "no such offer"):
			self._decline(offer_id="offer-absent", op_id="decide-absent")

		for offer_id in ("offer-1", "offer-2"):
			offer = self.store.offers[offer_id]
			self.assertEqual(offer.state, "issued", offer_id)
			self.assertFalse(offer.verifier_spent, offer_id)

	def test_decline_is_effectively_once_and_replays_the_committed_decision(self):
		self.manager.offer("offer-1", "baton.codex", "attempt-1", "secret-1", 100)
		first = self._decline()
		replayed = self._decline()
		self.assertIs(first, replayed,
		              "an exact replay must return the one committed decline")
		self.assertEqual(replayed.declined_at, first.declined_at)
		# A different reason under the same operation id is a COLLISION, not
		# a replay: the prose is a durable operand and rides the signature.
		with self.assertRaisesRegex(Refusal, "different operands"):
			self._decline(reason="a different reason entirely")
		self.assertEqual(self.store.offers["offer-1"].decline_reason,
		                 "the worker has no capacity")

	def test_a_stale_decline_refuses_and_changes_nothing(self):
		offer_id = accepted(self.manager)
		with self.assertRaisesRegex(Refusal, "only an issued offer"):
			self._decline(op_id="decide-after-accept")
		self.assertEqual(self.store.offers[offer_id].state, "accepted")
		# The accepted offer still settles into a claim, untouched.
		self.assertEqual(self.manager.claim(offer_id).generation, 1)

		# And a second decline of an already declined offer refuses under a
		# NEW operation id rather than silently re-terminalizing it.
		other_authority, other_manager = self.second_work()
		other_manager.offer("offer-2", "baton.claude", "attempt-2", "secret-2", 100)
		other_manager.decline("offer-2", "attempt-2", other_authority.work_ref(),
		                      "declined once", "decide-2")
		with self.assertRaisesRegex(Refusal, "offer is declined"):
			other_manager.decline("offer-2", "attempt-2",
			                      other_authority.work_ref(),
			                      "declined twice", "decide-3")

	def test_a_declined_offer_frees_the_Work_for_a_fresh_offer(self):
		"""`declined` is terminal, so the per-Work uniqueness rule lets the
		next offer issue — the point of declining rather than letting the
		offer sit until it expires."""

		self.manager.offer("offer-1", "baton.codex", "attempt-1", "secret-1", 100)
		with self.assertRaisesRegex(Refusal, "another nonterminal offer"):
			self.manager.offer("offer-2", "baton.claude", "attempt-2", "s2", 100)
		self._decline()
		self.manager.offer("offer-2", "baton.claude", "attempt-2", "secret-2", 100)
		self.manager.accept("offer-2", "secret-2")
		self.assertEqual(self.manager.claim("offer-2").generation, 1)

	def test_a_decline_survives_manager_restart(self):
		"""The decline is durable in the control store, not in the process
		that observed it — the same boundary every other manager-owned
		mutation is held to."""

		self.manager.offer("offer-1", "baton.codex", "attempt-1", "secret-1", 100)
		self._decline()
		restarted = Manager(self.authority, self.store, self.clock)
		replayed = restarted.decline("offer-1", "attempt-1",
		                             self.authority.work_ref(),
		                             "the worker has no capacity", "decide-1")
		self.assertEqual(replayed.state, "declined")
		with self.assertRaisesRegex(Refusal, "replay"):
			restarted.accept("offer-1", "secret-1")

	# --- claim, restart, and runtime identity ---------------------------

	def test_restart_after_ambiguous_claim_replays_same_generation(self):
		offer_id = accepted(self.manager)
		offer = self.store.offers[offer_id]
		committed = self.authority.claim(offer.participant, offer.claim_op_id)
		restarted = Manager(self.authority, self.store, self.clock)
		recovered = restarted.claim(offer_id)
		self.assertEqual(recovered, committed)
		self.assertEqual(self.authority.work.generation_counter, 1)

	def test_one_runtime_per_live_assignment_and_exact_reattach(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		first = self.manager.start(offer_id, "runtime-a")
		self.assertEqual(self.manager.start(offer_id, "runtime-a"), first)
		with self.assertRaisesRegex(Refusal, "different runtime"):
			self.manager.start(offer_id, "runtime-b")

	def test_immediate_same_participant_successor_rejects_old_generation(self):
		first_id = accepted(self.manager)
		old = self.manager.claim(first_id)
		self.authority.end(old, "release:first")

		second_manager = Manager(self.authority, self.store, self.clock)
		second_id = accepted(second_manager, "2", expires=200)
		new = second_manager.claim(second_id)
		self.assertEqual(old.participant, new.participant)
		self.assertEqual(new.generation, old.generation + 1)
		with self.assertRaisesRegex(Refusal, "stale"):
			self.authority.end(old, "pass:stale", disposition="pass")
		with self.assertRaisesRegex(Refusal, "stale"):
			self.authority.publish(old, "stale", "digest", "publish:stale")

	# --- cancellation: end the assignment, gate the replacement ---------

	def test_cancellation_ends_the_assignment_and_gates_the_replacement(self):
		offer_id = accepted(self.manager)
		old = self.manager.claim(offer_id)
		self.manager.start(offer_id, "runtime-a")
		self.manager.cancel(offer_id, "operator cancelled the attempt")

		self.assertIsNone(self.authority.assignment())
		self.assertIsNone(self.authority.work.handler)
		self.assertEqual(self.authority.work.phase, "block")
		self.assertEqual(self.authority.work.gate, "runtime-quiescence:1")
		self.assertEqual(self.authority.work.status, "open")
		ended = self.authority.assignment_events[-1]
		self.assertEqual(
			(ended["assignment"], ended["cause"], ended["fenced"]),
			(old, "cancelled", True))

		with self.assertRaisesRegex(Refusal, "fenced"):
			self.authority.publish(old, "late", "digest", "publish:late")
		with self.assertRaisesRegex(Refusal, "fenced"):
			self.authority.activity(old, "late-activity")
		with self.assertRaisesRegex(Refusal, "not claimable"):
			self.authority.claim("baton.claude", "claim:successor")
		self.authority.assert_invariants()

	def test_cancellation_frees_the_participants_one_global_claim_slot(self):
		offer_id = accepted(self.manager)
		old = self.manager.claim(offer_id)
		self.manager.cancel(offer_id, "runtime went unreachable")
		self.manager.observe_quiescence(offer_id, certain=False)

		self.assertNotIn(old.participant, self.deployment.slots.held)
		unrelated, elsewhere = self.second_work()
		other_id = accepted(elsewhere, "2", participant=old.participant, expires=200)
		self.assertEqual(elsewhere.claim(other_id).generation, 1)
		self.assertEqual(self.authority.work.gate, "runtime-quiescence:1")
		unrelated.assert_invariants()

	def test_uncertain_quiescence_requires_a_pinned_certified_policy(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.start(offer_id, "remote-runtime")
		self.manager.cancel(offer_id, "adapter lost the runtime")
		self.manager.force_stop(offer_id)
		self.manager.observe_quiescence(offer_id, certain=False)

		with self.assertRaisesRegex(Refusal, "not permitted"):
			self.manager.satisfy_quiescence(offer_id, policy="clause-3")
		self.deployment.isolation_certified = True
		with self.assertRaisesRegex(Refusal, "not permitted"):
			self.manager.satisfy_quiescence(offer_id)
		self.assertEqual(self.authority.work.gate, "runtime-quiescence:1")

		self.manager.satisfy_quiescence(offer_id, policy="isolation-clause-3")
		self.assertIsNone(self.authority.work.gate)
		self.assertEqual(self.authority.work.phase, "queued")
		self.assertEqual(
			self.authority.gate_evidence[-1]["evidence"]["policy"],
			"isolation-clause-3")

	def test_destroyed_runtime_satisfies_the_gate_and_mints_the_successor(self):
		offer_id = accepted(self.manager)
		old = self.manager.claim(offer_id)
		self.manager.start(offer_id, "runtime-a")
		self.manager.cancel(offer_id, "plan superseded")
		self.manager.force_stop(offer_id)
		self.manager.destroy(offer_id)
		self.manager.satisfy_quiescence(offer_id)
		self.assertEqual(
			self.authority.gate_evidence[-1]["evidence"]["kind"], "runtime-absent")

		successor = accepted(self.manager, "2", expires=200)
		new = self.manager.claim(successor)
		self.assertEqual((old.generation, new.generation), (1, 2))
		self.assertIn(1, self.authority.work.fenced_generations)
		self.authority.assert_invariants()

	def test_exact_cancel_retry_does_not_regress_destroyed_runtime(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.start(offer_id, "runtime-a")
		self.manager.cancel(offer_id, "operator cancelled the attempt")
		self.manager.destroy(offer_id)

		self.manager.cancel(offer_id, "operator cancelled the attempt")
		self.assertEqual(
			self.store.attempts["attempt-1"].runtime, "destroyed",
			"an exact authority replay regressed the manager attempt")

	# --- output retention after cancellation ----------------------------

	def test_cancelled_output_is_sealed_until_an_intake_disposition(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.start(offer_id, "runtime-a")
		self.manager.cancel(offer_id, "approver cancelled the attempt")
		self.manager.destroy(offer_id)
		record = self.manager.collect_output(
			offer_id, "sha256:draft", "approver cancelled the attempt")

		self.assertEqual(
			(record.work_ref, record.generation, record.intake),
			(("authority-uuid", "full-W1"), 1, "pending"))
		self.assertEqual(self.store.attempts["attempt-1"].output, "sealed")
		with self.assertRaisesRegex(Refusal, "awaiting an intake decision"):
			self.manager.cleanup(offer_id)

		self.manager.intake(record.quarantine_id, "preserved")
		# A NEW cleanup decision, with its own operation id: the refusal above
		# wrote `blocked-on-intake`, so the operation that earned it replays it
		# rather than quietly taking a different outcome later.
		self.assertEqual(
			self.manager.cleanup(offer_id, "cleanup:after-intake").cleanup,
			"complete")
		self.assertEqual(self.authority.proposals, {},
		                 "intake inspection never makes worker output canonical")

	def test_discard_on_cancel_requires_a_pinned_disposable_policy(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.cancel(offer_id, "disposable probe")
		self.manager.destroy(offer_id)
		with self.assertRaisesRegex(Refusal, "does not permit discard"):
			self.manager.collect_output(
				offer_id, "sha256:draft", "disposable probe", policy="discard")

		self.deployment.disposable_attempts = True
		self.assertIsNone(self.manager.collect_output(
			offer_id, "sha256:draft", "disposable probe", policy="discard"))
		self.assertEqual(self.store.attempts["attempt-1"].output, "discarded")
		self.assertEqual(self.manager.cleanup(offer_id).cleanup, "complete")

	# --- per-Work contract progression ----------------------------------

	def test_contract_progression_keeps_the_work_and_mints_generation_one(self):
		legacy, manager = self.second_work("full-W3", contract=V11)
		offer_id = accepted(manager, "3", participant="baton.claude", expires=200)
		assignment = manager.claim(offer_id)
		self.assertIsNone(assignment.generation)
		self.assertEqual(legacy.work.generation_counter, 0)
		with self.assertRaisesRegex(Refusal, "v12 assignment contract"):
			legacy.publish(assignment, "p", "digest", "publish:v11")

		legacy.advance_contract(
			assignment, V11, V12, "isolated worker profile is certified",
			"contract:1")
		self.assertEqual(legacy.work.contract, V12)
		self.assertEqual(legacy.work.work_id, "full-W3")
		self.assertIsNone(legacy.work.handler)
		self.assertEqual(legacy.work.phase, "queued")
		self.assertIsNone(legacy.work.gate)

		successor = accepted(manager, "3b", participant="baton.claude", expires=200)
		self.assertEqual(manager.claim(successor).generation, 1)
		legacy.assert_invariants()

	def test_contract_progression_without_a_certified_runtime_blocks(self):
		self.deployment.certified_contracts = {V11}
		legacy, manager = self.second_work("full-W4", contract=V11)
		offer_id = accepted(manager, "4", participant="baton.claude", expires=200)
		assignment = manager.claim(offer_id)
		legacy.advance_contract(
			assignment, V11, V12, "advance ahead of the runtime", "contract:2")

		self.assertEqual(legacy.work.phase, "block")
		self.assertEqual(legacy.work.gate, f"contract-runtime:{V12}")
		with self.assertRaisesRegex(Refusal, "not claimable"):
			legacy.claim("baton.claude", "claim:ungated")
		with self.assertRaisesRegex(Refusal, "no certified runtime profile"):
			legacy.satisfy_gate(
				f"contract-runtime:{V12}", {"kind": "certified-profile"},
				"gate:early")

		self.deployment.certified_contracts = {V11, V12}
		legacy.satisfy_gate(
			f"contract-runtime:{V12}", {"kind": "certified-profile"}, "gate:certified")
		self.assertEqual(legacy.work.phase, "queued")
		later = accepted(manager, "4b", participant="baton.claude", expires=200)
		self.assertEqual(manager.claim(later).generation, 1)

	def test_contract_transition_refuses_stale_or_unpermitted_operands(self):
		legacy, manager = self.second_work("full-W5", contract=V11)
		offer_id = accepted(manager, "5", participant="baton.claude", expires=200)
		assignment = manager.claim(offer_id)
		with self.assertRaisesRegex(Refusal, "contract compare-and-swap is stale"):
			legacy.advance_contract(
				assignment, V12, V12, "wrong expectation", "contract:stale")
		with self.assertRaisesRegex(Refusal, "not permitted by policy"):
			legacy.advance_contract(
				assignment, V11, "v99", "unconfigured target", "contract:unknown")
		stale = assignment.__class__(
			assignment.authority_uuid, assignment.work_id, "baton.codex", None)
		with self.assertRaisesRegex(Refusal, "stale assignment"):
			legacy.advance_contract(
				stale, V11, V12, "not the handler", "contract:not-handler")
		self.assertEqual(legacy.work.contract, V11)

	def test_contract_transition_replay_binds_the_durable_rationale(self):
		legacy, manager = self.second_work("full-W6", contract=V11)
		offer_id = accepted(manager, "6", participant="baton.claude", expires=200)
		assignment = manager.claim(offer_id)
		legacy.advance_contract(
			assignment, V11, V12, "first durable rationale", "contract:1")
		with self.assertRaisesRegex(Refusal, "reused for different operands"):
			legacy.advance_contract(
				assignment, V11, V12, "different rationale", "contract:1")

	# --- result, proposal, and the four workflow receipts ----------------

	def test_plan_rejection_ends_assignment_and_installs_gate_atomically(self):
		offer_id = accepted(self.manager)
		assignment = self.manager.claim(offer_id)
		self.authority.end(
			assignment, "plan-reject:1", phase="block",
			gate="plan-revision:plan-digest-1", disposition="plan-rejected")
		self.assertIsNone(self.authority.assignment())
		self.assertEqual(self.authority.work.phase, "block")
		self.assertEqual(self.authority.work.gate, "plan-revision:plan-digest-1")
		with self.assertRaisesRegex(Refusal, "not claimable"):
			self.authority.claim("baton.codex", "claim:unchanged-plan")

	def test_assignment_end_replay_binds_the_durable_reason(self):
		offer_id = accepted(self.manager)
		assignment = self.manager.claim(offer_id)
		self.authority.end(
			assignment, "release:1", disposition="release", reason="first reason")
		with self.assertRaisesRegex(Refusal, "reused for different operands"):
			self.authority.end(
				assignment, "release:1", disposition="release",
				reason="different reason")

	def test_result_freeze_and_proposal_bind_exact_assignment(self):
		offer_id = accepted(self.manager)
		assignment = self.manager.claim(offer_id)
		self.manager.start(offer_id, "runtime-a")
		self.manager.observe_quiescence(offer_id, certain=True)
		self.manager.freeze(offer_id, "sha256:result")
		self.assertEqual(
			self.manager.publish(offer_id, "proposal-1"),
			("proposal-1", "sha256:result"))
		proposal = self.authority.proposals["proposal-1"]
		self.assertEqual((proposal.assignment, proposal.digest),
		                 (assignment, "sha256:result"))

	def test_frozen_output_cannot_be_rewritten(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.start(offer_id, "runtime-a")
		self.manager.observe_quiescence(offer_id, certain=True)
		self.manager.freeze(offer_id, "sha256:first")
		with self.assertRaisesRegex(Refusal, "immutable|frozen"):
			self.manager.freeze(offer_id, "sha256:replacement")
		self.assertEqual(
			self.store.attempts["attempt-1"].output_digest, "sha256:first")

	def _published(self, digest="candidate-1"):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.start(offer_id, "runtime-a")
		self.manager.observe_quiescence(offer_id, certain=True)
		self.manager.freeze(offer_id, digest)
		self.manager.publish(offer_id, "proposal-1")
		return offer_id

	def test_verify_review_approve_and_integrate_are_distinct_gates(self):
		self._published()
		with self.assertRaisesRegex(Refusal, "explicit approval"):
			self.authority.integrate("proposal-1", "integrate:early")
		self.authority.verify("proposal-1", "passed", "verify:1")
		self.authority.review("proposal-1", "accepted", "review:1")
		self.authority.approve("proposal-1", "approved", "approve:1")
		self.authority.integrate("proposal-1", "integrate:1")
		self.assertEqual(
			self.authority.proposals["proposal-1"].integration, "integrated")
		self.assertEqual(self.authority.target, "candidate-1")
		self.assertIsNotNone(self.authority.assignment(),
		                     "integration does not implicitly close Work")

	def test_workflow_receipts_are_immutable_and_only_replayable(self):
		self._published()
		first = self.authority.verify("proposal-1", "passed", "verify:1")
		self.assertEqual(self.authority.verify("proposal-1", "passed", "verify:1"),
		                 first)
		with self.assertRaisesRegex(Refusal, "reused for different operands"):
			self.authority.verify("proposal-1", "failed", "verify:1")
		with self.assertRaisesRegex(Refusal, "verification receipt is immutable"):
			self.authority.verify("proposal-1", "failed", "verify:2")
		self.assertEqual(
			self.authority.proposals["proposal-1"].verification, "passed")

		self.authority.review("proposal-1", "accepted", "review:1")
		with self.assertRaisesRegex(Refusal, "review receipt is immutable"):
			self.authority.review("proposal-1", "rejected", "review:2")
		self.authority.approve("proposal-1", "approved", "approve:1")
		with self.assertRaisesRegex(Refusal, "approval receipt is immutable"):
			self.authority.approve("proposal-1", "denied", "approve:2")

		committed = self.authority.integrate("proposal-1", "integrate:1")
		self.assertEqual(
			self.authority.integrate("proposal-1", "integrate:1"), committed)
		with self.assertRaisesRegex(Refusal, "integration receipt is immutable"):
			self.authority.integrate("proposal-1", "integrate:2")
		self.assertEqual(
			self.authority.proposals["proposal-1"].integration, "integrated")
		self.assertEqual(self.authority.target, "candidate-1")

	def test_integration_refuses_when_the_reviewed_target_moved(self):
		self._published()
		self.authority.verify("proposal-1", "passed", "verify:1")
		self.authority.review("proposal-1", "accepted", "review:1")
		self.authority.approve("proposal-1", "approved", "approve:1")
		self.authority.target = "other-accepted-change"
		with self.assertRaisesRegex(Refusal, "target moved"):
			self.authority.integrate("proposal-1", "integrate:1")
		self.assertIsNone(
			self.authority.proposals["proposal-1"].integration,
			"a refused attempt writes no receipt")
		self.assertEqual(
			self.authority.integration_attempts[-1],
			("proposal-1", "stale-target", "other-accepted-change"))

	def test_refused_integration_retry_journals_one_attempt(self):
		self._published()
		self.authority.verify("proposal-1", "passed", "verify:1")
		self.authority.review("proposal-1", "accepted", "review:1")
		self.authority.approve("proposal-1", "approved", "approve:1")
		self.authority.target = "other-accepted-change"
		for _ in range(2):
			with self.assertRaisesRegex(Refusal, "target moved"):
				self.authority.integrate("proposal-1", "integrate:1")
		self.assertEqual(
			len(self.authority.integration_attempts), 1,
			"an exact retry repeated a journal mutation")

	# --- terminal close --------------------------------------------------

	def test_close_that_ends_a_live_assignment_needs_the_exact_identity(self):
		offer_id = accepted(self.manager)
		live = self.manager.claim(offer_id)
		with self.assertRaisesRegex(Refusal, "exact assignment identity"):
			self.authority.close("cancelled", "no longer wanted", "close:1")
		participant_only = live.__class__(
			live.authority_uuid, live.work_id, live.participant, None)
		with self.assertRaisesRegex(Refusal, "stale assignment"):
			self.authority.close(
				"cancelled", "no longer wanted", "close:2", expect=participant_only)
		stale = live.__class__(
			live.authority_uuid, live.work_id, live.participant, live.generation + 1)
		with self.assertRaisesRegex(Refusal, "stale assignment"):
			self.authority.close(
				"cancelled", "no longer wanted", "close:3", expect=stale)
		self.assertEqual(self.authority.assignment(), live)

		self.authority.close(
			"cancelled", "approver cancelled the deliverable", "close:4", expect=live)
		self.assertEqual(self.authority.work.status, "closed")
		self.assertIsNone(self.authority.work.phase)
		self.assertIsNone(self.authority.assignment())
		self.assertNotIn(live.participant, self.deployment.slots.held)
		ended = self.authority.assignment_events[-1]
		self.assertEqual((ended["assignment"], ended["cause"], ended["fenced"]),
		                 (live, "close:cancelled", True))
		self.authority.assert_invariants()

	def test_authorized_close_of_unclaimed_work_needs_no_assignment(self):
		self.authority.close("rejected", "superseded by W28", "close:unclaimed")
		self.assertEqual(self.authority.work.status, "closed")
		self.assertEqual(self.authority.assignment_events, [])
		self.authority.assert_invariants()

	def test_close_replay_binds_the_durable_rationale(self):
		offer_id = accepted(self.manager)
		live = self.manager.claim(offer_id)
		self.authority.close(
			"cancelled", "first durable rationale", "close:1", expect=live)
		with self.assertRaisesRegex(Refusal, "reused for different operands"):
			self.authority.close(
				"cancelled", "different rationale", "close:1", expect=live)

	def test_close_after_cancellation_refuses_the_fenced_generation(self):
		offer_id = accepted(self.manager)
		old = self.manager.claim(offer_id)
		self.manager.cancel(offer_id, "operator cancelled the attempt")
		with self.assertRaisesRegex(Refusal, "fenced and ended"):
			self.authority.close("cancelled", "stale identity", "close:stale",
			                     expect=old)
		self.authority.close("cancelled", "abandoning the gated Work", "close:gated")
		self.assertEqual(self.authority.work.status, "closed")

	# --- effectively-once at BOTH boundaries --------------------------------

	def test_settlement_timeout_leaves_an_unanswerable_claim_accepted(self):
		# The other half of the review's P1. "I could not ask the authority"
		# is not "the claim did not commit", so an unanswerable lookup leaves
		# the offer visibly accepted and unsettled rather than terminalizing
		# it on the strength of a row the manager itself may be behind on.
		offer_id = accepted(self.manager, expires=20)
		self.clock.value = self.store.offers[offer_id].settle_by
		self.authority.lookup_available = False
		with self.assertRaisesRegex(Refusal, "lookup is unavailable"):
			self.manager.settlement_timeout(offer_id)
		self.assertEqual(self.store.offers[offer_id].state, "accepted")

		self.authority.lookup_available = True
		self.manager.settlement_timeout(offer_id)
		self.assertEqual(self.store.offers[offer_id].state, "settlement-expired")

	def test_settlement_timeout_cannot_race_a_later_fixed_claim_commit(self):
		# A read-only "no result yet" answer is not proof that the fixed
		# operation can NEVER commit. A concurrent submitter can pass the
		# accepted-offer boundary, then commit immediately after the lookup and
		# before this manager terminalizes the offer. Settlement needs an atomic
		# exclusion/retirement boundary, not merely one point-in-time read.
		offer_id = accepted(self.manager, expires=20)
		offer = self.store.offers[offer_id]
		lookup = self.authority.operation_result

		def lookup_then_commit(op_id):
			self.assertIsNone(lookup(op_id))
			self.authority.claim(offer.participant, op_id)
			return None

		self.authority.operation_result = lookup_then_commit
		self.manager.settlement_timeout(offer_id)
		self.assertIsNotNone(self.authority.assignment())
		self.assertNotEqual(
			offer.state, "settlement-expired",
			"a point-in-time lookup expired an offer whose fixed claim committed")

	def test_a_fixed_claim_refusal_is_terminal_for_that_operation(self):
		# The control row calls a refused claim terminal. The authority must
		# bind the same terminal result too; otherwise a stale submitter can
		# retry the fixed operation after the competing Handler releases and
		# turn the already-refused offer into a live assignment.
		offer_id = accepted(self.manager, participant="baton.codex", expires=20)
		winner = self.authority.claim("baton.claude", "claim:competitor")
		with self.assertRaisesRegex(Refusal, "already claimed"):
			self.manager.claim(offer_id)
		self.assertEqual(self.store.offers[offer_id].state, "claim-refused")

		self.authority.end(winner, "release:competitor")
		with self.assertRaises(Refusal):
			self.authority.claim("baton.codex", f"claim:{offer_id}")
		self.assertIsNone(self.authority.assignment())

	def test_a_destroyed_runtime_observation_never_walks_backwards(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.start(offer_id, "runtime-a")
		self.manager.cancel(offer_id, "operator cancelled the attempt")
		self.manager.destroy(offer_id)
		for label, act in [
			("stop", lambda: self.manager.force_stop(offer_id)),
			("uncertain", lambda: self.manager.observe_quiescence(offer_id, certain=False)),
			("quiescent", lambda: self.manager.observe_quiescence(offer_id, certain=True)),
		]:
			with self.assertRaisesRegex(Refusal, "cannot regress", msg=label):
				act()
		self.assertEqual(self.store.attempts["attempt-1"].runtime, "destroyed")

	def test_an_identical_freeze_replays_and_a_second_digest_refuses(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.start(offer_id, "runtime-a")
		self.manager.observe_quiescence(offer_id, certain=True)
		first = self.manager.freeze(offer_id, "sha256:result")
		self.assertEqual(self.manager.freeze(offer_id, "sha256:result"), first,
		                 "a lost response could not be retried safely")
		with self.assertRaisesRegex(Refusal, "immutable"):
			self.manager.freeze(offer_id, "sha256:other")
		self.assertEqual(
			self.store.attempts["attempt-1"].output_digest, "sha256:result")

	def test_exact_collection_retry_seals_exactly_one_record(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.cancel(offer_id, "approver cancelled the attempt")
		self.manager.destroy(offer_id)
		for _ in range(2):
			record = self.manager.collect_output(
				offer_id, "sha256:draft", "approver cancelled the attempt")
		self.assertEqual(len(self.store.quarantine), 1,
		                 "an exact retry sealed the same output twice")
		self.manager.intake(record.quarantine_id, "preserved")
		# The retry after a disposition must not resurrect a pending record.
		self.manager.collect_output(
			offer_id, "sha256:draft", "approver cancelled the attempt")
		self.assertEqual(
			self.store.quarantine[record.quarantine_id].intake, "preserved")

	def test_exact_intake_retry_returns_the_committed_disposition(self):
		# SPEC section 7 gives intake its own disposition operation identity and
		# says every manager-owned mutation is effectively-once. Losing the
		# first response must replay the committed decision, not turn the same
		# request into an indistinguishable "already recorded" refusal.
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.cancel(offer_id, "approver cancelled the attempt")
		record = self.manager.collect_output(
			offer_id, "sha256:draft", "approver cancelled the attempt")
		first = self.manager.intake(record.quarantine_id, "preserved")
		self.assertEqual(
			self.manager.intake(record.quarantine_id, "preserved"), first)

	def test_cleanup_retry_cannot_change_a_committed_refusal_into_success(self):
		# Cleanup writes `blocked-on-intake` before it refuses. Under section
		# 7 that is a committed manager outcome: retrying the SAME operation
		# after intake moves must replay the refusal, while a NEW cleanup op may
		# re-evaluate and succeed. Without an operation id the model cannot tell
		# those two acts apart and silently takes a different outcome.
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.cancel(offer_id, "approver cancelled the attempt")
		record = self.manager.collect_output(
			offer_id, "sha256:draft", "approver cancelled the attempt")
		with self.assertRaisesRegex(Refusal, "awaiting an intake decision"):
			self.manager.cleanup(offer_id)
		self.assertEqual(
			self.store.attempts["attempt-1"].cleanup, "blocked-on-intake")
		self.manager.intake(record.quarantine_id, "preserved")
		with self.assertRaisesRegex(Refusal, "awaiting an intake decision"):
			self.manager.cleanup(offer_id)

	def test_a_retired_claim_operation_stays_dead_for_every_submitter(self):
		# The other half of settlement. Retiring the fixed operation is what
		# makes the terminal offer row true, so it must outlive the condition
		# that caused it: the Work becoming free again does not reopen it, and
		# a second timeout is a no-op rather than a second outcome.
		offer_id = accepted(self.manager, expires=20)
		offer = self.store.offers[offer_id]
		self.clock.value = offer.settle_by
		self.manager.settlement_timeout(offer_id)
		self.assertEqual(offer.state, "settlement-expired")
		with self.assertRaisesRegex(Refusal, "only an accepted offer"):
			self.manager.settlement_timeout(offer_id)

		self.assertIsNone(self.authority.assignment())
		with self.assertRaisesRegex(Refusal, "deadline"):
			self.authority.claim(offer.participant, offer.claim_op_id)
		self.assertIsNone(self.authority.assignment())

		# A fresh offer with its own operation identity still works.
		fresh = accepted(self.manager, "2", expires=200)
		self.assertEqual(self.manager.claim(fresh).generation, 1)

	def test_settlement_timeout_cannot_fire_immediately_after_acceptance(self):
		# Offer acceptance and claim settlement have deliberately separate
		# deadlines. An accepted offer therefore needs a durable settlement
		# deadline and must remain claimable until that boundary is reached;
		# otherwise the manager can retire the fixed claim operation in the
		# same instant that acceptance commits.
		offer_id = accepted(self.manager, expires=20)
		with self.assertRaisesRegex(Refusal, "settlement.*deadline|deadline.*settlement"):
			self.manager.settlement_timeout(offer_id)
		self.assertEqual(self.store.offers[offer_id].state, "accepted")
		self.assertEqual(self.manager.claim(offer_id).generation, 1)

	def test_settlement_rejects_a_committed_result_with_wrong_claim_operands(self):
		# A lookup by operation id alone cannot prove that the committed result
		# is THIS offer's fixed claim. If another submitter reused the id with
		# different operands, settlement must fail closed on the signature; it
		# must not bind the other participant's assignment to this offer.
		offer_id = accepted(self.manager, participant="baton.codex", expires=20)
		offer = self.store.offers[offer_id]
		other = self.authority.claim("baton.claude", offer.claim_op_id)
		with self.assertRaisesRegex(Refusal, "reused for different operands"):
			self.manager.claim(offer_id)
		self.assertEqual(self.authority.assignment(), other)
		self.assertEqual(offer.state, "accepted")
		self.assertIsNone(offer.assignment)

	def test_a_conflicting_intake_decision_is_refused_either_way(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.cancel(offer_id, "approver cancelled the attempt")
		record = self.manager.collect_output(
			offer_id, "sha256:draft", "approver cancelled the attempt")
		self.manager.intake(record.quarantine_id, "preserved")

		with self.assertRaisesRegex(Refusal, "reused for different operands"):
			self.manager.intake(record.quarantine_id, "discarded")
		with self.assertRaisesRegex(Refusal, "already recorded"):
			self.manager.intake(record.quarantine_id, "discarded", "intake:second")
		self.assertEqual(
			self.store.quarantine[record.quarantine_id].intake, "preserved")

	def test_a_new_cleanup_operation_may_re_evaluate_the_intake_boundary(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.cancel(offer_id, "approver cancelled the attempt")
		record = self.manager.collect_output(
			offer_id, "sha256:draft", "approver cancelled the attempt")
		with self.assertRaisesRegex(Refusal, "awaiting an intake decision"):
			self.manager.cleanup(offer_id, "cleanup:1")
		self.manager.intake(record.quarantine_id, "discarded")

		with self.assertRaisesRegex(Refusal, "awaiting an intake decision"):
			self.manager.cleanup(offer_id, "cleanup:1")
		second = self.manager.cleanup(offer_id, "cleanup:2")
		self.assertEqual(second.cleanup, "complete")
		self.assertEqual(self.manager.cleanup(offer_id, "cleanup:2"), second)

	def test_the_settlement_deadline_is_not_the_token_deadline(self):
		# Ruling 2 keeps them separate, so the model must too. Wall-clock
		# expiry of the bearer token does not open settlement, and reaching
		# the settlement deadline does not depend on the token's.
		offer_id = accepted(self.manager, expires=20)
		offer = self.store.offers[offer_id]
		self.assertGreater(offer.settle_by, offer.expires_at)

		self.clock.value = offer.expires_at + 1
		with self.assertRaisesRegex(Refusal, "settlement.*deadline"):
			self.manager.settlement_timeout(offer_id)
		# Past the TOKEN deadline the fixed claim is still authorized, which
		# is the whole point of the accepted-before-expiry ruling.
		self.assertEqual(self.manager.claim(offer_id).generation, 1)

	def test_a_committed_claim_reconciles_before_its_settlement_deadline(self):
		# Reconciling a claim that already committed is not a termination and
		# needs no settlement authority: making an operator wait for a
		# deadline to LEARN that the claim committed would strand the
		# assignment for exactly as long as the deadline.
		offer_id = accepted(self.manager, expires=20)
		offer = self.store.offers[offer_id]
		committed = self.authority.claim(offer.participant, offer.claim_op_id)
		self.assertLess(self.clock.value, offer.settle_by)
		self.assertEqual(self.manager.settlement_timeout(offer_id), committed)
		self.assertEqual(offer.state, "claimed")

	def test_a_retirement_names_the_operation_it_killed(self):
		# Retiring an unsubmitted identity binds the operands it was settling.
		# A retirement that recorded nothing about WHICH claim died would be
		# indistinguishable from one for a different participant's claim, and
		# the journal is the only place that question can be answered later.
		offer_id = accepted(self.manager, participant="baton.codex", expires=20)
		offer = self.store.offers[offer_id]
		self.clock.value = offer.settle_by
		self.manager.settlement_timeout(offer_id)

		record = self.authority.operation_record(offer.claim_op_id)
		self.assertEqual(record["kind"], "retired")
		self.assertEqual(record["signature"],
		                 self.authority.claim_signature("baton.codex"))
		self.assertIn("settlement", record["detail"]["reason"])
		self.assertEqual(record["detail"]["disposition"], "settlement-expired")
		# Reading the binding does not weaken the rule that every submitter
		# meets the retirement before any operand comparison.
		with self.assertRaisesRegex(Refusal, "settlement"):
			self.authority.claim("baton.claude", offer.claim_op_id)

	def test_retirement_replays_its_terminal_disposition_after_a_crash(self):
		# Authority retirement and the control-store offer CAS are necessarily
		# separate durability boundaries. If the manager crashes between them,
		# the authority record must say not only WHICH operation died but HOW
		# its offer terminalized; otherwise a later claim path can relabel a
		# settlement timeout as claim-refused.
		offer_id = accepted(self.manager, participant="baton.codex", expires=20)
		offer = self.store.offers[offer_id]
		self.clock.value = offer.settle_by
		settle = self.authority.settle_operation

		def settle_then_crash(*args, **kwargs):
			settle(*args, **kwargs)
			raise RuntimeError("manager crashed before the offer CAS")

		self.authority.settle_operation = settle_then_crash
		with self.assertRaisesRegex(RuntimeError, "before the offer CAS"):
			self.manager.settlement_timeout(offer_id)
		self.authority.settle_operation = settle
		self.assertEqual(offer.state, "accepted")

		restarted = Manager(self.authority, self.store, self.clock)
		with self.assertRaises(Refusal):
			restarted.claim(offer_id)
		self.assertEqual(
			offer.state, "settlement-expired",
			"a retry path changed the authority-retired terminal disposition")

	def test_a_colliding_operation_identity_changes_no_record(self):
		# The other half of the signature check. A committed operation under
		# this id with different operands is not this offer's claim, and the
		# collision must leave BOTH records exactly as they were — including
		# after the settlement deadline, where the manager would otherwise
		# have the authority to retire.
		offer_id = accepted(self.manager, participant="baton.codex", expires=20)
		offer = self.store.offers[offer_id]
		other = self.authority.claim("baton.claude", offer.claim_op_id)
		self.clock.value = offer.settle_by
		with self.assertRaisesRegex(Refusal, "reused for different operands"):
			self.manager.settlement_timeout(offer_id)
		self.assertEqual(offer.state, "accepted")
		self.assertIsNone(offer.assignment)
		self.assertEqual(self.authority.assignment(), other)
		self.assertEqual(
			self.authority.operation_result(offer.claim_op_id), other,
			"the colliding operation's committed record was overwritten")

	def test_a_refused_claim_retirement_keeps_its_own_disposition(self):
		# The other direction of the round-4 boundary. A claim positively
		# submitted and refused retires as `claim-refused`, and a later
		# settlement timeout on the same identity must replay THAT, exactly as
		# a timeout retirement survives a later claim path. Neither entry path
		# owns the outcome; the act that retired the identity does.
		offer_id = accepted(self.manager, participant="baton.codex", expires=20)
		offer = self.store.offers[offer_id]
		self.authority.claim("baton.claude", "claim:competitor")
		with self.assertRaisesRegex(Refusal, "already claimed"):
			self.manager.claim(offer_id)
		self.assertEqual(offer.state, "claim-refused")
		self.assertEqual(
			self.authority.operation_record(offer.claim_op_id)["detail"]["disposition"],
			"claim-refused")

		# Reopen the row as a crash would leave it, then time out.
		offer.state = "accepted"
		self.clock.value = offer.settle_by
		self.manager.settlement_timeout(offer_id)
		self.assertEqual(
			offer.state, "claim-refused",
			"the timeout path relabelled a refusal-driven retirement")

	def test_a_replayed_retirement_reports_the_reason_it_died_of(self):
		# The disposition is for the control row; the reason is for whoever
		# has to understand it. A stale submitter meeting the retirement gets
		# the original reason, not a message invented by the path it took.
		offer_id = accepted(self.manager, expires=20)
		offer = self.store.offers[offer_id]
		self.clock.value = offer.settle_by
		self.manager.settlement_timeout(offer_id)
		with self.assertRaisesRegex(Refusal, "deadline for offer-1 passed"):
			self.authority.claim(offer.participant, offer.claim_op_id)
		with self.assertRaisesRegex(Refusal, "deadline for offer-1 passed"):
			self.authority.claim("baton.claude", offer.claim_op_id)

	# --- axis separation ---------------------------------------------------

	def test_work_phase_and_attempt_state_are_not_overloaded(self):
		offer_id = accepted(self.manager)
		self.manager.claim(offer_id)
		self.manager.start(offer_id, "runtime-a")
		self.assertEqual(self.authority.work.phase, "active")
		self.assertEqual(self.store.attempts["attempt-1"].output, "open")

		self.manager.cancel(offer_id, "operator cancelled the attempt")
		self.manager.observe_quiescence(offer_id, certain=False)
		attempt = self.store.attempts["attempt-1"]
		self.assertEqual(self.authority.work.phase, "block")
		self.assertEqual(self.authority.work.gate, "runtime-quiescence:1")
		self.assertEqual(attempt.runtime, "uncertain")
		self.assertEqual(attempt.cleanup, "pending")
		self.authority.assert_invariants()


if __name__ == "__main__":
	unittest.main()


class TokenVerifierTests(unittest.TestCase):
	"""W4487 re-review: this contract owns the offer record, so it owns what
	the verifier IS — and it did not say. Two models derived it two ways and
	both called it the value the manager already stores."""

	def test_the_verifier_is_the_bearer_bytes_in_the_family_digest_form(self):
		# The GOLDEN pair, asserted against a literal rather than against a
		# recomputation of the same expression, which would agree with any
		# derivation including a wrong one.
		self.assertEqual(token_verifier(GOLDEN_BEARER), GOLDEN_VERIFIER)
		self.assertTrue(GOLDEN_VERIFIER.startswith("sha256:"))
		self.assertEqual(len(GOLDEN_VERIFIER), len("sha256:") + 64)

	def test_the_token_bytes_are_hashed_and_not_a_json_encoding_of_them(self):
		"""The exact mistake the re-review found.

		Hashing the JSON encoding brings the quotes and the escaping rules
		into the value, so a peer that escapes a character differently
		computes a different verifier for the same secret."""
		import json
		from hashlib import sha256
		as_json = "sha256:" + sha256(
			json.dumps(GOLDEN_BEARER, separators=(",", ":")).encode()).hexdigest()
		self.assertNotEqual(token_verifier(GOLDEN_BEARER), as_json)
		# And a token whose JSON encoding is NOT its own bytes still verifies
		# by its bytes: the quote would be escaped, the backslash doubled.
		for awkward in ['a"b' + "c" * 29, "a\\b" + "c" * 29, "é" + "c" * 31]:
			self.assertEqual(
				token_verifier(awkward),
				"sha256:" + sha256(awkward.encode("utf-8")).hexdigest(), awkward)

	def test_the_offer_record_stores_exactly_that_verifier(self):
		"""The derivation is not a helper sitting beside the store; it IS
		what the issued record holds, which is what makes the cross-contract
		golden case meaningful."""
		deployment = Deployment(certified_contracts={V11, V12})
		authority = Authority(work_id="golden-W1", deployment=deployment,
		                      contract=V12)
		manager = Manager(authority, ControlStore(), Clock(10))
		offer = manager.offer("golden-offer", "baton.codex", "attempt-golden",
		                      GOLDEN_BEARER, 99)
		self.assertEqual(offer.verifier, GOLDEN_VERIFIER)
		self.assertNotIn(GOLDEN_BEARER, repr(offer),
		                 "the issued record kept the bearer")


if __name__ == "__main__":
	unittest.main()
