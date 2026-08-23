"""Executable 1-ruled model for W151; not Baton application code.

One `Authority` instance models one Work row inside one authority UUID. A
`Deployment` carries the facts that are shared across Works — the
one-live-claim capacity register, the certified contracts and runtime
profiles, and the pinned isolation/retention policy — so scenarios that need
two Works construct two authorities over one deployment and one durable
control store.
"""

from dataclasses import dataclass, field
from hashlib import sha256


# THE CLAIM-TOKEN VERIFIER, AND THIS CONTRACT OWNS IT.
#
# W4487 re-review 2026-08-22
# (`work/records/2026/08/finding-worker-control-decline-token-conflict/
# review-2026-08-22T14-57-26Z.md`).
#
# This contract owns the offer record, so it owns what "the verifier" IS.
# It did not say. This module hashed the token's raw UTF-8 bytes and stored
# bare hexadecimal; worker-control's §4.2 operation-signature payload, added
# by the same Work, hashed the token's JCS JSON encoding — quotes included —
# and serialized it with the family's `sha256:` prefix. Both called the
# result "the verifier the manager already stores". For the bearer `"x" * 43`
# they are
#
#   this module     cc0b1c2c66f3bb9fd1a081c626ba1bef62f6f96441a43be15268523776ac26a1
#   worker-control  sha256:6162a6f0b60f2860a9712724c281a7e83d2a74adf304a9dbaf54d43d5aeceadf
#
# — different hashed byte sequences, not formatting variants. Two conforming
# peers would compute different operation signatures for the same acceptance,
# which is the ambiguity §4.2's clarification existed to remove.
#
# ONE DERIVATION, pinned here and repeated verbatim in worker-control's model,
# with the conformance package asserting the two agree on a golden bearer:
#
#   verifier = "sha256:" + lowercase hex of SHA-256 over the token's own
#              UTF-8 bytes
#
# The token's OWN BYTES, not a JSON encoding of them. A bearer is a secret
# string, not a JSON document: hashing its encoding makes the verifier depend
# on escaping rules, so a peer that escapes a character differently — or at
# all — computes a different verifier for the same secret. The bytes have one
# answer.
#
# The `sha256:` prefix because §3.2 of worker-control is the family's one
# digest representation, it is what the frozen schema's `digest` type accepts,
# and it names the algorithm — so replacing SHA-256 later is a visible change
# rather than a silent reinterpretation of 64 hex characters.
def token_verifier(token):
	"""The single-use offer verifier derived from one bearer token."""
	return "sha256:" + sha256(token.encode("utf-8")).hexdigest()


# The cross-contract golden pair. Pinned as a LITERAL rather than computed,
# so a change to the derivation on either side fails a comparison instead of
# moving both expected values with it.
GOLDEN_BEARER = "x" * 43
GOLDEN_VERIFIER = ("sha256:cc0b1c2c66f3bb9fd1a081c626ba1bef62f6f96441a43be152"
                   "68523776ac26a1")


class Refusal(RuntimeError):
	pass


V11 = "v11"
V12 = "v12-assignment-1"


@dataclass(frozen=True)
class Assignment:
	"""The ruled identity: authority, Work, participant, generation.

	`generation` is None under the `v11` contract, which mints none; a
	positive generation exists only under a v12 assignment contract.
	"""

	authority_uuid: str
	work_id: str
	participant: str
	generation: int | None


class ClaimSlots:
	"""Deployment-wide capacity: a participant holds ONE live claim."""

	def __init__(self):
		self.held = {}

	def free(self, participant, work_id):
		held = self.held.get(participant)
		return held is None or held == work_id

	def take(self, participant, work_id):
		if not self.free(participant, work_id):
			raise Refusal(
				f"{participant} already holds {self.held[participant]}; a "
				f"participant holds ONE active claim at a time")
		self.held[participant] = work_id

	def release(self, participant, work_id):
		if self.held.get(participant) == work_id:
			del self.held[participant]


@dataclass
class Deployment:
	"""Configured facts shared by every Work in one deployment."""

	slots: ClaimSlots = field(default_factory=ClaimSlots)
	certified_contracts: set = field(default_factory=lambda: {V11})
	contract_transitions: set = field(default_factory=lambda: {(V11, V12)})
	isolation_certified: bool = False
	disposable_attempts: bool = False
	# Ruling 2 keeps the bearer-acceptance deadline and the claim-settlement
	# deadline SEPARATE. This is the second one: how long an accepted offer's
	# fixed claim operation stays live before an operator may retire it.
	settlement_window: int = 60


@dataclass
class Work:
	work_id: str
	contract: str = V11
	phase: str | None = "queued"
	status: str = "open"
	handler: str | None = None
	generation_counter: int = 0
	live_generation: int | None = None
	gate: str | None = None
	fenced_generations: set = field(default_factory=set)


@dataclass
class Proposal:
	proposal_id: str
	assignment: Assignment
	digest: str
	target: str
	verification: str | None = None
	review: str | None = None
	approval: str | None = None
	integration: str | None = None


class Authority:
	"""Authority-owned Work, contract, generation, assignment, and replay."""

	def __init__(self, authority_uuid="authority-uuid", work_id="full-W1",
	             deployment=None, contract=V11):
		self.authority_uuid = authority_uuid
		self.deployment = deployment or Deployment()
		self.work = Work(work_id, contract=contract)
		self.operations = {}
		self.proposals = {}
		self.activities = []
		self.assignment_events = []
		self.contract_events = []
		self.gate_evidence = []
		self.integration_attempts = []
		self.target = "base-1"
		self.lookup_available = True

	def work_ref(self):
		return (self.authority_uuid, self.work.work_id)

	def assignment(self):
		if self.work.handler is None:
			return None
		return Assignment(self.authority_uuid, self.work.work_id,
		                  self.work.handler, self.work.live_generation)

	def _replay(self, op_id, signature, action, durable_refusal=False):
		"""Effectively-once over the FULL effective operands.

		`durable_refusal` is for an operation that writes something durable
		on its way to refusing — the stale-target integration journals its
		attempt. Such a refusal is itself a committed outcome, so a retry
		replays the same refusal instead of appending a second attempt or,
		if the world moved underneath it, taking a different outcome under
		one operation identity. An ordinary refusal writes nothing and stays
		retryable.
		"""
		prior = self.operations.get(op_id)
		if prior is not None:
			signature_was, kind, value = prior
			# Retirement is a property of the operation IDENTITY, not of one
			# request's operands, so it is answered before the signature.
			if kind == "retired":
				raise Refusal(value["reason"])
			if signature_was != signature:
				raise Refusal("operation id was reused for different operands")
			if kind == "refused":
				raise Refusal(value)
			return value
		try:
			result = action()
		except Refusal as refusal:
			if durable_refusal:
				self.operations[op_id] = (signature, "refused", str(refusal))
			raise
		self.operations[op_id] = (signature, "committed", result)
		return result

	def operation_result(self, op_id):
		"""§8's read-only operation-result lookup, or None if uncommitted.

		Raises when the authority cannot answer, because "I could not ask"
		must never be read as "it did not commit".
		"""
		if not self.lookup_available:
			raise Refusal("the operation-result lookup is unavailable")
		prior = self.operations.get(op_id)
		if prior is None or prior[1] != "committed":
			return None
		return prior[2]

	@staticmethod
	def claim_signature(participant):
		"""The operands a fixed claim operation commits under."""

		return ("claim", participant)

	def operation_record(self, op_id):
		"""What the journal durably says about one operation identity.

		Audit-shaped rather than result-shaped: a retirement's whole job is
		to say WHICH operation died and why, so the record has to be
		readable. `operation_result` deliberately answers only for a
		committed claim.
		"""
		prior = self.operations.get(op_id)
		if prior is None:
			return None
		signature, kind, value = prior
		return {"kind": kind, "signature": signature, "detail": value}

	def settle_operation(self, op_id, signature, reason, disposition,
	                     may_retire=True):
		"""Make one fixed operation durably terminal, atomically.

		A read that says "not committed" proves only its own instant: a
		submitter can already have passed its preconditions and commit right
		after the read. So settlement is not lookup-then-write — it is ONE
		authority act that either finds the committed result or retires the
		identity so nothing can ever commit under it again.

		`signature` is the FIXED operation this caller believes it is
		settling. An operation id is not by itself proof that a committed
		result belongs to this offer: another submitter may have reused the
		identity with different operands. That is a collision, and a
		collision fails closed — it neither adopts the other operation's
		result nor overwrites its record.

		`may_retire` is the caller's settlement authority. Retirement kills a
		live authorization, so a caller with no positive evidence that the
		claim is over — a timeout before its deadline — may only observe.

		`disposition` is how the offer terminalizes because of THIS
		retirement, and it is recorded with it. Authority retirement and the
		control-store row are separate durability boundaries: a manager can
		crash between them, and the next caller to find the retirement
		arrives through whichever entry path it happens to be on. Binding the
		disposition is what stops that caller from relabelling a settlement
		timeout as a refused claim — the outcome was decided by the act that
		retired the identity, not by who noticed afterwards.

		Returns `("committed", result)`, `("refused", message)`,
		`("retired", record)` where the record carries the bound reason and
		disposition, or `("live", None)`; and raises when the authority
		cannot answer at all.
		"""
		self.operation_result(op_id)
		# Re-read INSIDE the settlement. Anything that committed while the
		# lookup was in flight is found here, and after this act the identity
		# is closed to every later and stale submitter alike.
		prior = self.operations.get(op_id)
		if prior is not None:
			signature_was, kind, value = prior
			if kind == "retired":
				return ("retired", value)
			if signature_was != signature:
				raise Refusal("operation id was reused for different operands")
			if kind == "committed":
				return ("committed", value)
			return ("refused", value)
		if not may_retire:
			return ("live", None)
		# The retirement is BOUND to the operands it was settling, so the
		# record says which operation died. `_replay` still answers
		# retirement before any signature comparison, so a stale submitter
		# reading it learns the identity is dead rather than that its
		# operands disagree.
		record = {"reason": reason, "disposition": disposition}
		self.operations[op_id] = (signature, "retired", record)
		return ("retired", record)

	def _expect(self, expected):
		current = self.assignment()
		if current == expected:
			return
		if expected is not None and expected.generation in self.work.fenced_generations:
			raise Refusal("assignment generation was fenced and ended")
		raise Refusal("stale assignment")

	def _proposal(self, proposal_id):
		proposal = self.proposals.get(proposal_id)
		if proposal is None:
			raise Refusal("no such proposal")
		return proposal

	def claim(self, participant, op_id):
		def action():
			if self.work.status != "open" or self.work.phase in {"block", "parked"}:
				raise Refusal("Work is not claimable")
			if self.work.handler is not None:
				raise Refusal("Work is already claimed")
			self.deployment.slots.take(participant, self.work.work_id)
			if self.work.contract != V11:
				self.work.generation_counter += 1
				self.work.live_generation = self.work.generation_counter
			self.work.handler = participant
			self.work.phase = "active"
			return self.assignment()
		return self._replay(op_id, Authority.claim_signature(participant), action)

	def activity(self, expected, key):
		self._expect(expected)
		entry = (expected, key)
		if entry not in self.activities:
			self.activities.append(entry)
		return entry

	def publish(self, expected, proposal_id, digest, op_id, target=None):
		def action():
			self._expect(expected)
			if self.work.contract == V11:
				raise Refusal("publication requires a v12 assignment contract")
			prior = self.proposals.get(proposal_id)
			wanted_target = target or self.target
			if prior is not None and (prior.assignment, prior.digest, prior.target) \
					!= (expected, digest, wanted_target):
				raise Refusal("proposal identity was reused for different bytes")
			self.proposals[proposal_id] = Proposal(
				proposal_id, expected, digest, wanted_target)
			return (proposal_id, digest)
		return self._replay(
			op_id, ("publish", expected, proposal_id, digest, target or self.target), action)

	def verify(self, proposal_id, observation, op_id):
		def action():
			proposal = self._proposal(proposal_id)
			if observation not in {"passed", "failed", "unable"}:
				raise Refusal("invalid verification observation")
			if proposal.verification is not None:
				raise Refusal("verification receipt is immutable")
			proposal.verification = observation
			return ("verification", proposal_id, observation)
		return self._replay(op_id, ("verify", proposal_id, observation), action)

	def review(self, proposal_id, disposition, op_id):
		def action():
			proposal = self._proposal(proposal_id)
			if disposition not in {"accepted", "changes-requested", "rejected"}:
				raise Refusal("invalid review disposition")
			if proposal.review is not None:
				raise Refusal("review receipt is immutable")
			if proposal.verification != "passed":
				raise Refusal("technical review requires passed verification")
			proposal.review = disposition
			return ("review", proposal_id, disposition)
		return self._replay(op_id, ("review", proposal_id, disposition), action)

	def approve(self, proposal_id, disposition, op_id):
		def action():
			proposal = self._proposal(proposal_id)
			if disposition not in {"approved", "denied"}:
				raise Refusal("invalid approval disposition")
			if proposal.approval is not None:
				raise Refusal("approval receipt is immutable")
			if proposal.review != "accepted":
				raise Refusal("approval requires accepted technical review")
			proposal.approval = disposition
			return ("approval", proposal_id, disposition)
		return self._replay(op_id, ("approve", proposal_id, disposition), action)

	def integrate(self, proposal_id, op_id):
		def action():
			proposal = self._proposal(proposal_id)
			if proposal.integration is not None:
				raise Refusal("integration receipt is immutable")
			if proposal.approval != "approved":
				raise Refusal("integration requires explicit approval")
			if self.target != proposal.target:
				# A failed attempt is journalled beside the proposal; it never
				# rewrites a receipt, and there is no receipt to rewrite here.
				self.integration_attempts.append(
					(proposal_id, "stale-target", self.target))
				raise Refusal("canonical target moved")
			self.target = proposal.digest
			proposal.integration = "integrated"
			return ("integration", proposal_id, "integrated")
		return self._replay(op_id, ("integrate", proposal_id), action,
		                    durable_refusal=True)

	def _end(self, expected, phase, gate, disposition, fence, reason):
		self._expect(expected)
		if fence and expected.generation is not None:
			self.work.fenced_generations.add(expected.generation)
		self.deployment.slots.release(self.work.handler, self.work.work_id)
		self.work.handler = None
		self.work.live_generation = None
		self.work.phase = phase
		self.work.gate = gate
		self.assignment_events.append(
			{"assignment": expected, "cause": disposition, "fenced": fence,
			 "reason": reason, "gate": gate})
		return (disposition, expected, phase, gate)

	def end(self, expected, op_id, phase="queued", gate=None,
	        disposition="release", reason=None):
		def action():
			return self._end(expected, phase, gate, disposition, False, reason)
		return self._replay(
			op_id, ("end", expected, phase, gate, disposition, reason), action)

	def cancel(self, expected, op_id, reason):
		"""Fence the exact generation and end the assignment in one act."""

		def action():
			gate = f"runtime-quiescence:{expected.generation}"
			return self._end(expected, "block", gate, "cancelled", True, reason)
		return self._replay(op_id, ("cancel", expected, reason), action)

	def advance_contract(self, expected, expect_contract, target_contract,
	                     rationale, op_id):
		def action():
			self._expect(expected)
			if self.work.contract != expect_contract:
				raise Refusal("contract compare-and-swap is stale")
			if (expect_contract, target_contract) not in \
					self.deployment.contract_transitions:
				raise Refusal("contract transition is not permitted by policy")
			certified = target_contract in self.deployment.certified_contracts
			gate = None if certified else f"contract-runtime:{target_contract}"
			phase = "queued" if certified else "block"
			self.work.contract = target_contract
			self.contract_events.append(
				{"from": expect_contract, "to": target_contract,
				 "assignment": expected, "rationale": rationale})
			self._end(expected, phase, gate, "contract-advanced", False, rationale)
			return (target_contract, phase, gate)
		return self._replay(
			op_id,
			("advance-contract", expected, expect_contract, target_contract,
			 rationale),
			action)

	def satisfy_gate(self, gate, evidence, op_id):
		def action():
			if self.work.gate is None or self.work.gate != gate:
				raise Refusal("that gate is not the one holding this Work")
			kind = evidence.get("kind")
			if gate.startswith("runtime-quiescence:"):
				if kind == "runtime-absent":
					pass
				elif kind == "certified-isolation-policy":
					if not self.deployment.isolation_certified:
						raise Refusal("replacement is not permitted")
					if not evidence.get("policy"):
						raise Refusal("replacement is not permitted")
				else:
					raise Refusal("replacement is not permitted")
			elif gate.startswith("contract-runtime:"):
				if kind != "certified-profile" or \
						self.work.contract not in self.deployment.certified_contracts:
					raise Refusal("no certified runtime profile executes this contract")
			else:
				raise Refusal("unknown gate kind")
			self.gate_evidence.append({"gate": gate, "evidence": evidence})
			self.work.gate = None
			self.work.phase = "queued"
			return (gate, kind)
		return self._replay(op_id, ("satisfy-gate", gate, tuple(sorted(evidence.items()))), action)

	def close(self, outcome, rationale, op_id, expect="omitted"):
		def action():
			if self.work.status != "open":
				raise Refusal("Work is already closed")
			live = self.assignment()
			if live is not None and expect == "omitted":
				raise Refusal(
					"a close that ends a live assignment must supply its "
					"exact assignment identity")
			if expect != "omitted":
				self._expect(expect)
			if live is not None:
				self._end(expect, None, None, f"close:{outcome}", True, rationale)
			self.work.status = "closed"
			self.work.phase = None
			self.work.gate = None
			return (outcome, live)
		return self._replay(
			op_id, ("close", outcome, rationale, expect), action)

	def assert_invariants(self):
		work = self.work
		held = work.handler is not None
		if held:
			assert work.phase == "active"
			assert work.status == "open"
			if work.contract == V11:
				assert work.live_generation is None
			else:
				assert work.live_generation == work.generation_counter
				assert work.live_generation not in work.fenced_generations
			assert self.deployment.slots.held.get(work.handler) == work.work_id
		else:
			assert work.phase != "active"
			assert work.live_generation is None
			assert work.work_id not in self.deployment.slots.held.values()
		assert all(1 <= g <= work.generation_counter for g in work.fenced_generations)
		if work.gate is not None:
			assert work.phase == "block"
		if work.status != "open":
			assert work.phase is None and not held


@dataclass
class Offer:
	offer_id: str
	work_ref: tuple
	participant: str
	attempt_id: str
	expires_at: int
	verifier: str
	state: str = "issued"
	# W4487: the verifier is a durable single-use fact in its own right,
	# separate from the row's state. Acceptance, decline and expiry all
	# consume it, and once consumed no bearer can ever be validated
	# against this offer again — which is what makes "decline kills the
	# token without echoing it" observable rather than implied by a state
	# name.
	verifier_spent: bool = False
	accepted_at: int | None = None
	# The durable decline record: its exact binding and its prose, so an
	# exact replay returns the one committed decline.
	declined_at: int | None = None
	decline_reason: str | None = None
	# Distinct from `expires_at`: that one is the bearer's deadline to
	# accept, this one is how long the accepted claim stays live afterwards.
	settle_by: int | None = None
	claim_op_id: str | None = None
	assignment: Assignment | None = None


@dataclass
class Attempt:
	attempt_id: str
	assignment: Assignment
	runtime_id: str | None = None
	runtime: str = "not-started"
	output: str = "open"
	output_digest: str | None = None
	cleanup: str = "pending"


@dataclass
class Quarantine:
	quarantine_id: str
	work_ref: tuple
	generation: int | None
	reason: str
	policy: str
	digest: str
	intake: str = "pending"


# Runtime observations only ever move FORWARD. `destroyed` is positive
# proof of absence and terminal: nothing may turn it back into a runtime
# that might still be executing, which would also un-satisfy a quiescence
# gate that was settled on it.
RUNTIME_ORDER = {
	"not-started": 0, "start-requested": 1, "running": 2,
	"cancel-requested": 3, "stopping": 4,
	"quiescent": 5, "uncertain": 5,
	"destroyed": 6,
}


@dataclass
class ControlStore:
	offers: dict = field(default_factory=dict)
	attempts: dict = field(default_factory=dict)
	quarantine: dict = field(default_factory=dict)
	operations: dict = field(default_factory=dict)

	def replay(self, op_id, signature, action, durable_refusal=False):
		"""The manager's own effectively-once journal.

		The authority's replay protects authority state; it says nothing
		about the control store. Without this, an exact retry of a
		manager-owned act replays the authority result and then re-runs the
		manager's own mutation on top of newer observations.

		`durable_refusal` carries the same meaning it has in the authority:
		a refusal that WROTE something — cleanup recording
		`blocked-on-intake` — is a committed outcome of that operation, so
		the same operation replays it. A NEW operation is free to evaluate
		the world as it now stands.
		"""
		prior = self.operations.get(op_id)
		if prior is not None:
			signature_was, kind, value = prior
			if signature_was != signature:
				raise Refusal("operation id was reused for different operands")
			if kind == "refused":
				raise Refusal(value)
			return value
		try:
			result = action()
		except Refusal as refusal:
			if durable_refusal:
				self.operations[op_id] = (signature, "refused", str(refusal))
			raise
		self.operations[op_id] = (signature, "committed", result)
		return result


class Manager:
	"""Restartable manager over a durable control store and authority."""

	def __init__(self, authority, store, now=lambda: 0, deployment=None):
		self.authority = authority
		self.store = store
		self.now = now
		self.deployment = deployment or authority.deployment

	@staticmethod
	def _digest(token):
		return token_verifier(token)

	def _attempt(self, offer_id):
		return self.store.attempts[self.store.offers[offer_id].attempt_id]

	@staticmethod
	def _observe(attempt, state):
		"""Record a runtime observation that does not walk backwards."""

		if RUNTIME_ORDER[state] < RUNTIME_ORDER[attempt.runtime]:
			raise Refusal(
				f"a {attempt.runtime} runtime observation cannot regress to "
				f"{state}")
		attempt.runtime = state
		return attempt

	def _record_claim(self, offer, assignment):
		offer.assignment = assignment
		offer.state = "claimed"
		self.store.attempts.setdefault(
			offer.attempt_id, Attempt(offer.attempt_id, assignment))
		return assignment

	def offer(self, offer_id, participant, attempt_id, token, expires_at):
		work_ref = self.authority.work_ref()
		if any(o.state in {"issued", "accepted"} and o.work_ref == work_ref
		       for o in self.store.offers.values()):
			raise Refusal("another nonterminal offer exists for this Work")
		work = self.authority.work
		if work.status != "open" or work.phase in {"block", "parked"} \
				or work.handler is not None:
			raise Refusal("Work is not offerable")
		if work.contract not in self.deployment.certified_contracts:
			raise Refusal("no certified runtime profile executes this contract")
		if not self.deployment.slots.free(participant, work.work_id):
			raise Refusal("participant has no free claim capacity")
		offer = Offer(offer_id, work_ref, participant, attempt_id, expires_at,
		              self._digest(token))
		self.store.offers[offer_id] = offer
		return offer

	def accept(self, offer_id, token):
		"""ACCEPTANCE STILL REQUIRES THE BEARER, and W4487 does not touch it.

		The ruling separates the two decisions on purpose: taking authority
		presents the exact unspent, unexpired bearer and succeeds only
		through the canonical claim transaction, while REFUSING authority
		needs no secret at all. Weakening this half would have been the
		obvious wrong reading of "decline carries no token".
		"""

		offer = self.store.offers[offer_id]
		if offer.state != "issued" or offer.verifier_spent:
			raise Refusal("token replay")
		if self.now() >= offer.expires_at:
			offer.state = "expired"
			offer.verifier_spent = True
			raise Refusal("token expired")
		if self._digest(token) != offer.verifier:
			raise Refusal("token mismatch")
		offer.verifier_spent = True
		offer.state = "accepted"
		offer.accepted_at = self.now()
		offer.settle_by = offer.accepted_at + self.deployment.settlement_window
		offer.claim_op_id = f"claim:{offer.offer_id}"
		return offer

	def decline(self, offer_id, attempt_id, work_ref, reason, op_id):
		"""W4487: refuse an issued offer WITHOUT echoing the bearer.

		Ruled 2026-08-22 and recorded in
		`work/records/2026/08/finding-worker-control-decline-token-conflict/`.
		The frozen contracts contradicted each other: W151 §7 required the
		exact unspent token, while worker-control 1.0 §6.1 and its schema
		require `claim_token: null` when `decision=decline`. A manager could
		not satisfy both, and the approver kept worker-control's non-secret
		shape — so W151's token requirement for DECLINE is superseded.

		What replaces it is not "less authorization", it is DIFFERENT
		authorization. The integrity-protected `offer.decide` operation is
		bound to the exact issued offer, runtime attempt, Work, decision and
		reason; the manager validates that whole binding and only then
		consumes the verifier. A worker declining an offer is refusing
		authority rather than taking it, and transmitting a secret in order
		to refuse is a leak with nothing bought by it.

		Every property acceptance had, this keeps except the bearer:

		- bound to the EXACT issued offer, so it cannot terminate another;
		- effectively once, through the manager's own operation journal;
		- consumes the verifier, so the token is dead afterwards;
		- mints no claim and touches no authority state at all.
		"""

		def action():
			offer = self.store.offers.get(offer_id)
			if offer is None:
				raise Refusal("no such offer")
			# THE WHOLE BINDING, not the id alone. The id is what a caller
			# names; the binding is what proves the caller is talking about
			# the offer it thinks it is. A decline naming one offer while
			# carrying another's attempt or Work terminates neither.
			if (offer.attempt_id, offer.work_ref) != (attempt_id, work_ref):
				raise Refusal(
					"decline binding does not match the issued offer")
			if offer.state != "issued" or offer.verifier_spent:
				raise Refusal(
					f"offer is {offer.state}; only an issued offer with an "
					f"unspent verifier can be declined")
			offer.verifier_spent = True
			offer.state = "declined"
			offer.declined_at = self.now()
			offer.decline_reason = reason
			return offer
		# The prose rides the signature, exactly as §7 requires of every
		# durable operand: reusing one operation id with a different reason
		# is a collision, not a replay of the first one.
		return self.store.replay(
			op_id, ("decline", offer_id, attempt_id, work_ref, "decline", reason),
			action)

	def _terminalize(self, offer, state, reason, may_retire=True):
		"""Close the fixed claim operation FIRST, then the offer row.

		No terminal control row may coexist with a claim operation that can
		still commit later. Settling the operation is what makes that true;
		the row only records it. If the settlement finds a committed claim
		instead, that claim wins and is recorded, however late — reconciling
		a claim that already committed is not a termination and needs no
		settlement authority.

		A collision refusal propagates untouched and the offer row is left
		exactly as it was: an identity this manager cannot prove is its own
		is not one it may declare over.

		`state` is what this caller's path would terminalize as; it is a
		PROPOSAL. A retirement that already exists carries the disposition
		decided when the identity died, and that one wins — otherwise a
		manager crashing between the authority retirement and this row would
		let whichever entry path noticed next choose the outcome.
		"""
		kind, result = self.authority.settle_operation(
			offer.claim_op_id, Authority.claim_signature(offer.participant),
			reason, disposition=state, may_retire=may_retire)
		if kind == "committed":
			return self._record_claim(offer, result)
		if kind == "live":
			raise Refusal(
				"the claim-settlement deadline for this accepted offer has "
				"not passed; its fixed claim is still live")
		if kind == "retired":
			offer.state = result["disposition"]
			return offer
		offer.state = state
		return offer

	def settlement_timeout(self, offer_id):
		"""An accepted offer whose claim never settled; the token stays spent.

		The offer row is NOT the settlement. §8 settles an ambiguous claim
		through its fixed operation, and this is exactly that ambiguity: the
		authority may have committed the claim and the manager lost the
		result before writing `claimed`. Terminalizing on the row alone
		strands a live assignment with no recoverable attempt — it holds the
		participant's one slot while every later claim refuses "offer was not
		accepted".

		So a committed claim WINS and is recorded; only a claim the authority
		positively reports as uncommitted may expire. If the authority cannot
		answer, the offer stays visibly accepted and unsettled.
		"""
		offer = self.store.offers[offer_id]
		if offer.state != "accepted":
			raise Refusal("only an accepted offer can time out its settlement")
		return self._terminalize(
			offer, "settlement-expired",
			f"the claim-settlement deadline for {offer.offer_id} passed with "
			f"no committed claim",
			# The deadline is what separates "this claim never settled" from
			# "this claim has not settled YET". Before it, the timeout may
			# observe and reconcile but not retire.
			may_retire=self.now() >= offer.settle_by)

	def claim(self, offer_id):
		offer = self.store.offers[offer_id]
		if offer.state not in {"accepted", "claimed"}:
			raise Refusal("offer was not accepted")
		try:
			assignment = self.authority.claim(offer.participant, offer.claim_op_id)
		except Refusal:
			# The authority refusing is not by itself terminal — an ordinary
			# refusal writes nothing and stays retryable, which is right for
			# the operation and WRONG for the offer. Calling the offer
			# `claim-refused` while its fixed operation could still commit
			# after the competitor releases would mint an assignment for an
			# offer the control store already retired.
			if offer.state == "accepted":
				self._terminalize(
					offer, "claim-refused",
					f"the claim for {offer.offer_id} was refused and its offer "
					f"is terminal")
			raise
		return self._record_claim(offer, assignment)

	def start(self, offer_id, runtime_id):
		offer = self.store.offers[offer_id]
		attempt = self.store.attempts[offer.attempt_id]
		if self.authority.assignment() != attempt.assignment:
			raise Refusal("assignment is not current")
		if attempt.runtime_id is not None and attempt.runtime_id != runtime_id:
			raise Refusal("a different runtime already owns this assignment")
		if attempt.runtime_id == runtime_id and attempt.runtime != "not-started":
			return attempt
		attempt.runtime_id = runtime_id
		return Manager._observe(attempt, "running")

	def cancel(self, offer_id, reason):
		"""Authority first: fence the generation and end the assignment."""

		def action():
			attempt = self._attempt(offer_id)
			self.authority.cancel(attempt.assignment, f"cancel:{offer_id}", reason)
			return Manager._observe(attempt, "cancel-requested")
		# Manager-owned replay as well as the authority's: an exact retry of
		# a cancellation must not walk a later `destroyed` observation back
		# to `cancel-requested` on top of an authority result that simply
		# replayed.
		return self.store.replay(f"cancel:{offer_id}", ("cancel", offer_id, reason),
		                         action)

	def force_stop(self, offer_id):
		return Manager._observe(self._attempt(offer_id), "stopping")

	def observe_quiescence(self, offer_id, certain):
		return Manager._observe(self._attempt(offer_id),
		                        "quiescent" if certain else "uncertain")

	def destroy(self, offer_id):
		"""Positive proof that this assignment's exact runtime is gone."""

		return Manager._observe(self._attempt(offer_id), "destroyed")

	def collect_output(self, offer_id, digest, reason, policy="retain"):
		"""Seal recoverable output; discard only where policy permits it."""

		def action():
			attempt = self._attempt(offer_id)
			if policy == "discard":
				if not self.deployment.disposable_attempts:
					raise Refusal("retention policy does not permit discard")
				attempt.output = "discarded"
				return None
			record = Quarantine(
				f"quarantine:{offer_id}", self.authority.work_ref(),
				attempt.assignment.generation, reason, policy, digest)
			self.store.quarantine[record.quarantine_id] = record
			attempt.output = "sealed"
			return record
		return self.store.replay(
			f"collect:{offer_id}", ("collect", offer_id, digest, reason, policy),
			action)

	def intake(self, quarantine_id, disposition, op_id=None):
		"""Trusted intake judges sealed material; it never makes it canonical.

		The disposition rides the operation signature, so an exact retry of
		one decision replays it while a DIFFERENT decision is refused as the
		second decision it is.
		"""
		def action():
			record = self.store.quarantine[quarantine_id]
			if record.intake != "pending":
				raise Refusal("intake disposition is already recorded")
			if disposition not in {"preserved", "revised", "submitted", "discarded"}:
				raise Refusal("invalid intake disposition")
			record.intake = disposition
			return record
		return self.store.replay(
			op_id or f"intake:{quarantine_id}",
			("intake", quarantine_id, disposition), action)

	def satisfy_quiescence(self, offer_id, policy=None):
		attempt = self._attempt(offer_id)
		gate = f"runtime-quiescence:{attempt.assignment.generation}"
		if attempt.runtime == "destroyed":
			evidence = {"kind": "runtime-absent", "runtime": attempt.runtime_id or ""}
		else:
			evidence = {"kind": "certified-isolation-policy",
			            "policy": policy or "", "runtime": attempt.runtime}
		return self.authority.satisfy_gate(gate, evidence, f"gate:{offer_id}")

	def cleanup(self, offer_id, op_id=None):
		"""Delete the private checkout, once the retention boundary allows it.

		The refusal WRITES `blocked-on-intake`, so it is a committed outcome
		of this operation and the same operation replays it. Re-evaluating
		after intake moves is a new decision and takes a new operation id.
		"""
		def action():
			attempt = self._attempt(offer_id)
			pending = [q for q in self.store.quarantine.values()
			           if q.work_ref == self.authority.work_ref()
			           and q.generation == attempt.assignment.generation
			           and q.intake == "pending"]
			if pending:
				attempt.cleanup = "blocked-on-intake"
				raise Refusal("sealed output is still awaiting an intake decision")
			attempt.cleanup = "complete"
			return attempt
		return self.store.replay(
			op_id or f"cleanup:{offer_id}", ("cleanup", offer_id), action,
			durable_refusal=True)

	def freeze(self, offer_id, digest):
		"""Freeze the declared output ONCE.

		"Frozen" is what makes a proposal's content digest mean anything. A
		second freeze that replaces the digest would rewrite the bytes a
		published proposal is bound to, so the second call is either the
		same digest — idempotent, and the honest answer to a lost response —
		or a refusal.
		"""
		attempt = self._attempt(offer_id)
		if attempt.output == "frozen":
			if attempt.output_digest == digest:
				return attempt
			raise Refusal("frozen output is immutable")
		if attempt.runtime != "quiescent":
			raise Refusal("runtime is not quiescent")
		def action():
			attempt.output = "frozen"
			attempt.output_digest = digest
			return attempt
		return self.store.replay(
			f"freeze:{offer_id}", ("freeze", offer_id, digest), action)

	def publish(self, offer_id, proposal_id):
		attempt = self._attempt(offer_id)
		if attempt.output != "frozen":
			raise Refusal("output is not frozen")
		return self.authority.publish(
			attempt.assignment, proposal_id, attempt.output_digest,
			f"publish:{proposal_id}")
