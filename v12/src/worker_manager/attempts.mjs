// W2929 plan item 3, second slice: ACTIVATION and RUNTIME START.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// The offer slice ended with a recorded claim. This one is what may happen
// next, and the ordering is the whole content:
//
//   1. `assignment.activate` binds this attempt to THIS attempt's own
//      committed claim, through the participant-bound session, and fixes all
//      four parts of the assignment before the first writable adapter call;
//   2. runtime start commits a fully signed `runtime.start` operation and
//      hands its identity to the adapter, so the adapter and a restart
//      settle the same act;
//   3. reconciliation identifies by opaque id PLUS the full four-part
//      assignment labels, attaches once by compare-and-swap, and cancels on
//      mismatch or multiplicity rather than starting another;
//   4. observations move along PER-AXIS transitions, decided and written in
//      one transaction against the expected current state, and journalled so
//      an exact duplicate replays while a conflicting one refuses;
//   5. CANCELLATION fences at the authority FIRST and only afterwards orders
//      the agent cancelled and the runtime stopped, because until the
//      generation is fenced the assignment is still live and the worker is
//      still authorized. Ordering an act is never reported as performing it.
//
// WHAT IS NOT HERE: output freeze, intake and cleanup — the rest of item 3 —
// and all of item 4's agent-session normalization and adapter CONTRACTS. The
// agent and the runtime adapter are injected objects; what a conforming one
// must be, and what certified evidence of runtime ABSENCE looks like, are
// item 4's to pin. Until then absence cannot be proven and the retry path is
// deliberately closed.

import { ContractError, digest, nameValue, opaqueIdFault }
	from "./contracts.mjs";

// THE PER-AXIS TRANSITIONS, not the vocabulary's array order.
//
// Review [P1]: treating the enum's order as a transition order made
// `worker_disposition=completed` advance to `unable` — a different terminal
// ANSWER, not a later stage of the same one. A vocabulary lists what an axis
// may say; only a transition map says what may follow what, and terminal
// ALTERNATIVES must be immutable or a manager can overwrite its own outcome.
//
// `uncertain` is where the two runtime axes are deliberately asymmetric: it
// may return to a positive observation, and it may never become `destroyed`.
// Destruction is a fact about the world, and inferring it from a failure to
// look would report a cleaned-up runtime that is still executing somebody's
// code.
export const TRANSITIONS = Object.freeze({
	consent_runtime: {
		"not-started": ["running", "uncertain", "destroyed"],
		running: ["quiescent", "uncertain", "destroyed"],
		quiescent: ["uncertain", "destroyed"],
		uncertain: ["running", "quiescent"],
		destroyed: [],
	},
	execution_runtime: {
		// A COLD START CAN DISCOVER ANY OF THESE. At restart the local axis
		// is `not-started` while a runtime may already exist, so
		// reconciliation must be able to record what it finds — including
		// positive destruction — without inventing an intermediate state
		// nobody observed.
		// CANCELLATION IS REACHABLE FROM EVERY NONTERMINAL STATE.
		//
		// Review [P1]: `uncertain` had no path to `cancel-requested`, so one
		// ambiguous inspection disabled the safety response to stronger
		// later evidence — a manager that then discovered two runtimes
		// promised a cancellation the axis refused. Mismatch and
		// multiplicity can be discovered from any state in which the
		// manager is still looking, so the INTENT to cancel is reachable
		// from all of them. That is separate from the rule about
		// destruction, which uncertainty still never proves.
		"not-started": ["start-requested", "running", "cancel-requested",
		                "uncertain", "destroyed"],
		"start-requested": ["running", "cancel-requested", "uncertain",
		                    "destroyed"],
		running: ["cancel-requested", "stopping", "quiescent", "uncertain",
		          "destroyed"],
		"cancel-requested": ["stopping", "quiescent", "uncertain", "destroyed"],
		stopping: ["quiescent", "uncertain", "destroyed"],
		quiescent: ["cancel-requested", "uncertain", "destroyed"],
		uncertain: ["running", "cancel-requested", "stopping", "quiescent"],
		destroyed: [],
	},
	output: {
		open: ["freeze-requested", "invalid", "discarded"],
		"freeze-requested": ["frozen", "invalid"],
		frozen: ["sealed", "invalid", "discarded"],
		invalid: ["discarded"],
		sealed: ["discarded"],
		discarded: [],
	},
	// EVERY disposition below is a terminal ALTERNATIVE. One answer is
	// chosen, and the others never follow it.
	worker_disposition: {
		none: ["completed", "unable", "plan-rejected", "cancelled"],
		completed: [], unable: [], "plan-rejected": [], cancelled: [],
	},
	proposal: {
		none: ["publish-requested"],
		"publish-requested": ["published"],
		published: ["superseded"],
		superseded: [],
	},
	verification: {
		none: ["passed", "failed", "unable"],
		passed: [], failed: [], unable: [],
	},
	technical_review: {
		none: ["accepted", "changes-requested", "rejected"],
		accepted: [], "changes-requested": [], rejected: [],
	},
	approval: { none: ["approved", "denied"], approved: [], denied: [] },
	integration: { none: ["integrated", "failed"], integrated: [], failed: [] },
	cleanup: {
		pending: ["blocked-on-intake", "complete", "retained", "failed"],
		"blocked-on-intake": ["complete", "retained", "failed"],
		complete: [], retained: [], failed: [],
	},
});

export const AXES = Object.freeze(Object.fromEntries(
	Object.entries(TRANSITIONS).map(([axis, moves]) =>
		[axis, Object.freeze(Object.keys(moves))])));

/** W2929 composition revalidation, 2026-08-23. THE IDENTIFIER IS PROVED
 *  BEFORE IT REACHES THE STATEMENT. Measured: an unproved id went straight
 *  into the prepared statement, so a caller handing this boundary an object
 *  got SQLite's own binding error — "Unknown named parameter 'toJSON'" — or,
 *  through a trapping Proxy, an arbitrary Error of the caller's choosing.
 *  Either way the closed pair was lost at a read that never validated its one
 *  operand.
 *
 *  An absent attempt still answers null, and that is the point of separating
 *  the two: a well-formed id naming nothing is an ABSENCE, and an id that is
 *  not an id is a REFUSAL. Conflating them tells a caller "no such attempt"
 *  about a question that was never asked. */
function attemptRow(store, attemptId) {
	const fault = opaqueIdFault(attemptId);
	if (fault !== null) {
		throw new ContractError("integrity", "schema",
			`a runtime attempt id ${fault}; an operand is proved before it `
			+ `reaches the store, and a malformed identity is not an absence`);
	}
	return store.db.prepare(
		"SELECT * FROM attempts WHERE runtime_attempt_id = ?")
		.get(attemptId) ?? null;
}

function requireAttempt(store, attemptId) {
	const row = attemptRow(store, attemptId);
	if (row === null) {
		throw new ContractError("refused", "precondition",
			`no runtime attempt ${attemptId}`);
	}
	return row;
}

/** Record the attempt an accepted offer named. */
export function recordAttempt(store, { attemptId, adapterName, adapterDigest,
                                       profileDigest, inputDigest = null,
                                       policyDigest = null,
                                       imageDigest = null,
                                       toolchainDigest = null }) {
	// EVERY DURABLE OPERAND. Review [P1]: this signed three of eight, so a
	// changed adapter name or input digest replayed instead of colliding.
	// An operation identity that ignores operands is not an identity.
	const signature = digest({ kind: "attempt.record", operands: {
		attemptId, adapterName, adapterDigest, profileDigest, inputDigest,
		policyDigest, imageDigest, toolchainDigest } });
	return store.transact(`attempt.record:${attemptId}`, "attempt.record",
		signature, (db) => {
			db.prepare(
				"INSERT INTO attempts (runtime_attempt_id, adapter_name, "
				+ "adapter_digest, profile_digest, input_digest, "
				+ "policy_digest, image_digest, toolchain_digest, created_at) "
				+ "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
				.run(attemptId, adapterName, adapterDigest, profileDigest,
				     inputDigest, policyDigest, imageDigest, toolchainDigest,
				     store.clock());
			return { attemptId, adapterName, profileDigest };
		});
}

/** THIS attempt's own committed claim, or null.
 *
 *  Review [P1]: activation accepted any free-standing attempt beside any
 *  currently live assignment. A live assignment somewhere in the authority
 *  is not evidence that this attempt's accepted offer claimed it — and
 *  without that link a foreign session could activate somebody else's
 *  attempt onto its own Work. */
function claimOf(store, attemptId) {
	// EXACTLY ONE, and the count is asked for rather than assumed. The
	// unique index makes two impossible going forward; this fails closed
	// against a store written before it, because "which of these two is
	// this attempt's claim" has no answer a manager may guess at.
	const rows = store.db.prepare(
		"SELECT * FROM offers WHERE runtime_attempt_id = ? AND state = 'claimed'")
		.all(attemptId);
	if (rows.length > 1) {
		throw new ContractError("integrity", "schema",
			`attempt ${attemptId} has ${rows.length} claimed offers; one `
			+ `attempt belongs to one offer, and choosing between them by row `
			+ `order would be inventing an answer`);
	}
	return rows[0] ?? null;
}

const ASSIGNMENT_FIELDS = ["authorityUuid", "workId", "participant",
                           "generation"];

function sameAssignment(left, right) {
	return ASSIGNMENT_FIELDS.every((field) => left?.[field] === right?.[field]);
}

function fixedAssignment(attempt) {
	if (attempt.assignment_generation === null) return null;
	return { authorityUuid: attempt.authority_uuid, workId: attempt.work_id,
	         participant: attempt.assignment_participant,
	         generation: attempt.assignment_generation };
}

/** Step 1: bind the attempt to its own claim, through its own session.
 *
 *  Three separate things must agree before anything writable runs: the
 *  session's binding, this attempt's committed claim, and the authority's
 *  live assignment. Any two agreeing is not enough — that is exactly how a
 *  foreign session or a replayed activation gets in. */
export function activateAssignment(store, session, { attemptId, expect }) {
	const attempt = requireAttempt(store, attemptId);
	if (session?.participant === undefined || session.participant === null) {
		throw new ContractError("integrity", "schema",
			"activation runs through a participant-bound session; this one "
			+ "names no participant");
	}
	if (expect?.participant !== session.participant) {
		throw new ContractError("refused", "precondition",
			`this session acts for ${session.participant} and the activation `
			+ `names ${expect?.participant}; an assignment is activated by `
			+ `the identity that holds it`);
	}
	const claim = claimOf(store, attemptId);
	if (claim === null) {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} has no committed claim; a live assignment `
			+ `elsewhere in the authority is not evidence that this attempt's `
			+ `offer claimed it`);
	}
	const claimed = { authorityUuid: claim.authority_uuid,
	                  workId: claim.work_id, participant: claim.participant,
	                  generation: claim.claim_generation };
	if (!sameAssignment(claimed, expect)) {
		throw new ContractError("stale-assignment", "generation",
			`attempt ${attemptId} claimed `
			+ `${nameValue(claimed)} and this activation names `
			+ `${nameValue(expect)}`);
	}
	const already = fixedAssignment(attempt);
	if (already !== null) {
		// FIXED ONCE, and compared on ALL FOUR parts. Comparing Work and
		// generation alone let a later activation replay under another
		// participant or authority.
		if (!sameAssignment(already, expect)) {
			throw new ContractError("stale-assignment", "generation",
				`attempt ${attemptId} is fixed to ${nameValue(already)}`);
		}
		return { attemptId, assignment: already, alreadyFixed: true };
	}
	const live = session.assignmentOf(expect.workId);
	if (live === null) {
		throw new ContractError("stale-assignment", "ended",
			`${expect.workId} holds no live assignment; nothing writable may `
			+ `run against an assignment that has ended`);
	}
	if (!sameAssignment(live, expect)) {
		throw new ContractError("stale-assignment", "generation",
			`the live assignment is ${nameValue(live)} and this `
			+ `activation expects ${nameValue(expect)}`);
	}
	const signature = digest({ kind: "assignment.activate",
	                           operands: { attemptId, expect } });
	return store.transact(`assignment.activate:${attemptId}`,
		"assignment.activate", signature, (db) => {
			const changed = db.prepare(
				"UPDATE attempts SET work_id=?, authority_uuid=?, "
				+ "assignment_generation=?, assignment_participant=? "
				+ "WHERE runtime_attempt_id=? AND assignment_generation IS NULL")
				.run(expect.workId, expect.authorityUuid, expect.generation,
				     expect.participant, attemptId).changes;
			if (changed !== 1) {
				throw new ContractError("refused", "precondition",
					`attempt ${attemptId} was activated by another act`);
			}
			return { attemptId, assignment: expect, alreadyFixed: false };
		});
}

/** The labels every runtime this manager starts must carry.
 *
 *  ALL FOUR parts of the assignment. Review [P1]: they omitted the
 *  participant, so two participants' runtimes on one Work and generation
 *  were indistinguishable by label. */
export function runtimeLabels(attempt) {
	return {
		runtimeAttemptId: attempt.runtime_attempt_id,
		authorityUuid: attempt.authority_uuid,
		workId: attempt.work_id,
		participant: attempt.assignment_participant,
		generation: attempt.assignment_generation,
		profileDigest: attempt.profile_digest,
		adapterDigest: attempt.adapter_digest,
	};
}

function sameLabels(left, right) {
	return digest(left) === digest(right);
}

/** The ONE fixed start operation for an attempt.
 *
 *  Derived, so a restart and the adapter can both name the act this manager
 *  performed without having watched it. */
export function startOperationId(attempt) {
	return `runtime.start:${digest({
		attemptId: attempt.runtime_attempt_id,
		assignment: fixedAssignment(attempt),
		profileDigest: attempt.profile_digest,
	}).slice("sha256:".length)}`;
}

/** Step 2: commit a signed start operation, then call the adapter with it.
 *
 *  Review [P1]: an axis label is not an effectively-once act. A journalled
 *  operation is what a restart replays and what the adapter can be asked
 *  about; a state column records only that somebody once intended to start.
 *  The adapter receives the operation identity so both sides settle the same
 *  act rather than two acts that happen to be adjacent. */
export function requestRuntimeStart(store, adapter, { attemptId }) {
	const attempt = requireAttempt(store, attemptId);
	if (attempt.assignment_generation === null) {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} is not activated; the assignment manifest `
			+ `is fixed before the first writable adapter call`);
	}
	if (attempt.execution_runtime !== "not-started") {
		throw new ContractError("refused", "already-terminal",
			`attempt ${attemptId} execution is ${attempt.execution_runtime}`);
	}
	const labels = runtimeLabels(attempt);
	const operationId = startOperationId(attempt);
	const signature = digest({ kind: "runtime.start",
	                           operands: { attemptId, labels, operationId } });
	store.transact(operationId, "runtime.start", signature, () => {
		observe(store, { attemptId, axis: "execution_runtime",
		                 value: "start-requested" });
		return { attemptId, operationId };
	});
	const started = adapter.start({ labels, operationId });
	return reconcileRuntime(store, adapter, {
		attemptId, minted: started?.runtimeId ?? null,
		mintedLabels: started?.labels ?? null });
}

/** Step 3: decide what exists, by identity AND by the full labels.
 *
 *  ZERO WAITS. "The adapter reports nothing" and "nothing exists" are
 *  different facts, and starting a second runtime for one assignment is the
 *  failure this whole ordering exists to prevent.
 *
 *  Review [P1]: the previous version took `absenceProven` as a caller
 *  boolean — the rejected `schemaProven: true` shape again, where a proof a
 *  caller can write is not a proof. Positive absence needs validated
 *  certified-adapter evidence, which is item 4's to define, so until then
 *  THE RETRY PATH IS CLOSED and says so.
 *
 *  MISMATCH OR MULTIPLICITY CANCELS, including a minted runtime whose labels
 *  are wrong: that is a mismatch this call caused, not an absence. */
export function reconcileRuntime(store, adapter, { attemptId, minted = null,
                                                   mintedLabels = null }) {
	const attempt = requireAttempt(store, attemptId);
	const labels = runtimeLabels(attempt);
	const listed = adapter.list({ labels }) ?? [];
	// THE MINTED RUNTIME IS CHECKED BEFORE THE FILTER.
	//
	// Review [P1]: a runtime this call started, carrying labels for a
	// different assignment, was filtered out and reported as uncertainty —
	// but it is not absent, it is WRONG, and this call caused it. That is
	// the pinned mismatch cancellation, and dropping it would leave a
	// mislabelled runtime running with the manager waiting for news.
	if (minted !== null) {
		const own = listed.find((runtime) => runtime.runtimeId === minted);
		const ownLabels = mintedLabels ?? own?.labels ?? null;
		if (ownLabels !== null && !sameLabels(ownLabels, labels)) {
			return cancel(store, attemptId,
				`the runtime this call started (${minted}) carries labels for `
				+ `a different assignment`);
		}
	}
	const found = listed.filter(
		(runtime) => sameLabels(runtime.labels ?? {}, labels));
	if (found.length > 1) {
		return cancel(store, attemptId,
			`${found.length} runtimes carry this assignment's labels; `
			+ `starting another would compound it`,
			found.map((runtime) => runtime.runtimeId));
	}
	if (found.length === 1) {
		const runtime = found[0];
		if (minted !== null && runtime.runtimeId !== minted) {
			return cancel(store, attemptId,
				`this call started ${minted} and the adapter holds `
				+ `${runtime.runtimeId} for these labels`);
		}
		return attach(store, attempt, runtime.runtimeId);
	}
	if (minted !== null) {
		// This call started something the adapter now cannot see. That is
		// not absence either — it is a runtime whose fate is unknown.
		observe(store, { attemptId, axis: "execution_runtime",
		                 value: "uncertain" });
		return { attemptId, decision: "uncertain",
		         why: `this call started ${minted} and the adapter does not `
		              + `list it; a second start could leave two runtimes` };
	}
	observe(store, { attemptId, axis: "execution_runtime",
	                 value: "uncertain" });
	return { attemptId, decision: "uncertain",
	         why: "the adapter reports no runtime, and positive absence needs "
	              + "certified adapter evidence this slice does not yet have; "
	              + "a second start would risk two runtimes for one assignment" };
}

// THE STATES IN WHICH A STOP IS ALREADY IN FLIGHT.
//
// Review [P1]: `stopping` was the one nonterminal state with no cancellation
// response, so a later inspection that found two runtimes was refused by the
// very axis the safety response writes to. But the answer is not to declare
// `stopping -> cancel-requested`: that would move the axis BACKWARDS to
// re-announce an intent the runtime is already carrying out. The DECISION is
// what a caller acts on; the axis records where the runtime actually is, and
// re-requesting a cancellation already under way changes nothing about it.
//
// `destroyed` is deliberately not here. It is terminal, and an adapter still
// listing runtimes for a destroyed attempt is a contradiction — not a
// cancellation this manager can carry out — so it keeps refusing rather than
// being quietly reported as a cancellation that never happens.
const CANCELLATION_IN_FLIGHT = Object.freeze(["cancel-requested", "stopping"]);

function cancel(store, attemptId, why, runtimes = undefined) {
	const attempt = requireAttempt(store, attemptId);
	if (!CANCELLATION_IN_FLIGHT.includes(attempt.execution_runtime)) {
		observe(store, { attemptId, axis: "execution_runtime",
		                 value: "cancel-requested" });
	}
	return { attemptId, decision: "cancel", why,
	         ...(runtimes === undefined ? {} : { runtimes }) };
}

/** The FIRST positive attachment fixes the runtime identity.
 *
 *  Review [P1]: this overwrote `runtime_id` unconditionally, so a later
 *  inspection silently replaced the fixed runtime. The CAS admits null or
 *  the identical id; a different one is a mismatch, and a mismatch cancels
 *  rather than rewriting what is already recorded. */
function attach(store, attempt, runtimeId) {
	const attemptId = attempt.runtime_attempt_id;
	if (attempt.runtime_id !== null && attempt.runtime_id !== runtimeId) {
		return cancel(store, attemptId,
			`attempt ${attemptId} is attached to ${attempt.runtime_id} and `
			+ `the adapter now holds ${runtimeId}`);
	}
	// ONE OPERATION PER RUNTIME, not one per attempt.
	//
	// Review [P1]: with the identity keyed on the attempt alone, a stale
	// manager that lost the race reached the journal under the SAME
	// operation id with a DIFFERENT signature — so it surfaced
	// `refused.operation-collision` instead of the pinned mismatch
	// cancellation. Attaching runtime A and attaching runtime B are two
	// acts, and giving them one identity made the second read as a botched
	// retry of the first.
	let attached = false;
	try {
		store.transact(`attempt.attach:${attemptId}:${runtimeId}`,
			"attempt.attach",
			digest({ kind: "attempt.attach",
			         operands: { attemptId, runtimeId } }),
			(db) => {
				const changed = db.prepare(
					"UPDATE attempts SET runtime_id=? WHERE runtime_attempt_id=? "
					+ "AND (runtime_id IS NULL OR runtime_id = ?)")
					.run(runtimeId, attemptId, runtimeId).changes;
				if (changed !== 1) {
					throw new ContractError("refused", "precondition",
						`attempt ${attemptId} is attached to another runtime`);
				}
				attached = true;
				return { attemptId, runtimeId };
			});
	} catch (failure) {
		if (!(failure instanceof ContractError)) throw failure;
	}
	if (!attached) {
		// LOST. The fixed identity is re-read and PRESERVED — whoever
		// attached first decided it — and the runtime this call saw becomes
		// a mismatch to cancel rather than a second write.
		const now = requireAttempt(store, attemptId);
		if (now.runtime_id === runtimeId) {
			return { attemptId, decision: "attached", runtimeId };
		}
		return cancel(store, attemptId,
			`attempt ${attemptId} is attached to ${now.runtime_id} and this `
			+ `inspection found ${runtimeId}`);
	}
	observe(store, { attemptId, axis: "execution_runtime", value: "running" });
	return { attemptId, decision: "attached", runtimeId };
}

/** The ONE fixed cancellation operation for an attempt's exact generation.
 *
 *  Derived from the attempt and its assignment, so a manager that restarts
 *  mid-cancellation names the act it already performed instead of starting a
 *  second one. */
export function cancelOperationId(attempt) {
	return `attempt.cancel:${digest({
		attemptId: attempt.runtime_attempt_id,
		assignment: fixedAssignment(attempt),
	}).slice("sha256:".length)}`;
}

/** The AUTHORITY's identity for the same cancellation.
 *
 *  Derived from the same operands and DELIBERATELY DIFFERENT from the
 *  manager's. §4.2: success at one boundary does not imply success at the
 *  other, and reconciliation queries both exact records — one shared string
 *  would invite reading either journal's row as evidence of the other's. */
export function authorityCancelOperationId(attempt) {
	return `authority.${cancelOperationId(attempt)}`;
}

/** Cancellation, in the ONE order that is safe.
 *
 *  `session.cancel` FIRST. The authority atomically fences the exact
 *  generation, ends the assignment and installs the typed quiescence gate —
 *  and until that has happened the assignment is still live, so a runtime
 *  stopped first would be a worker torn out from under an assignment that
 *  the authority still believes is executing. Fence, then stop.
 *
 *  The manager's own intent is journalled BEFORE the authority is asked, for
 *  the same reason runtime start journals before the adapter call: a crash
 *  between the two boundaries must be answerable, and a state column records
 *  only that somebody once intended to cancel.
 *
 *  WHAT THIS DOES NOT DO: it does not satisfy the quiescence gate the
 *  authority installs. That gate takes positive absence naming the exact
 *  runtime, which is the same certified-adapter evidence the retry path is
 *  closed for until item 4 defines it. Agent-side quiescence is not that
 *  evidence and never becomes it. */
export function requestCancellation(store, session, agent, adapter,
                                    { attemptId, reason = null }) {
	// THE PARAMETER ORDER IS THE ACT ORDER: fence, then the agent, then the
	// runtime. Two adjacent injected objects are easy to swap, so the shapes
	// are checked — a swap refuses here instead of quietly cancelling the
	// wrong boundary first.
	requireBoundary(agent, "cancel", "the agent");
	requireBoundary(adapter, "stop", "the runtime adapter");
	const attempt = requireAttempt(store, attemptId);
	const expect = fixedAssignment(attempt);
	if (expect === null) {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} has no fixed assignment; cancellation fences `
			+ `an exact generation and there is none to fence`);
	}
	// The session is the BINDING. A session for somebody else could
	// otherwise end this participant's assignment through this manager,
	// which is the authorization the activation slice already refuses.
	if (session.participant !== expect.participant) {
		throw new ContractError("refused", "capability",
			`this session acts for ${session.participant} and attempt `
			+ `${attemptId} is assigned to ${expect.participant}`);
	}
	// NO LIVENESS PRE-CHECK. Whether this assignment is still the live one
	// is the AUTHORITY's decision, made inside its own transaction against
	// its own state; asking first and acting on the answer would be a
	// read-then-write race wearing a guard's clothes.
	const managerOperationId = cancelOperationId(attempt);
	const authorityOperationId = authorityCancelOperationId(attempt);
	const signature = digest({ kind: "attempt.cancel", operands: {
		attemptId, expect, authorityOperationId, reason } });
	const intent = store.transact(managerOperationId, "attempt.cancel",
		signature, () => ({ attemptId, assignment: expect,
		                    authorityOperationId, reason }));
	const fenced = session.cancel({ expect, operationId: authorityOperationId,
	                                reason });
	// ONLY NOW. Everything below this line runs after the generation is
	// fenced and the assignment is ended.
	return { ...intent, fenced, ...orderQuiescence(store, agent, adapter,
	                                               attemptId, expect,
	                                               managerOperationId) };
}

function requireBoundary(given, method, what) {
	if (typeof given?.[method] !== "function") {
		throw new ContractError("integrity", "schema",
			`${what} must supply ${method}(); cancellation orders the agent `
			+ `before the runtime and cannot silently skip either`);
	}
}

/** Order the AGENT cancelled and then the runtime stopped — and never claim
 *  either of them happened.
 *
 *  Review [P1]: this discarded `adapter.stop`'s answer and reported
 *  `stopped: true` whenever the call RETURNED. Reaching a boundary is not
 *  evidence of its effect: an adapter answering `{ stopped: false }` left the
 *  manager announcing a stopped runtime while its own axis still said only
 *  `cancel-requested`. That is exactly the confusion the quiescence gate
 *  exists to prevent, so the manager reports what it KNOWS — that it ordered
 *  the acts — and passes each settlement through uninterpreted. Positive
 *  quiescence arrives as an OBSERVATION or not at all.
 *
 *  Review [P1]: the pinned order is "agent cancellation AND runtime stop",
 *  and only the runtime half was here. `session.cancel` is the
 *  assignment-authority fence; it is not the provider agent's cancellation.
 *  The agent is an injected boundary for the same reason the runtime adapter
 *  is — item 4 owns what a conforming one must BE — but its PLACE in the
 *  order is item 3's and is pinned here.
 *
 *  The axis is announced only when the transition map declares
 *  `cancel-requested` from where the runtime actually is. That is the round-3
 *  rule: a runtime already `stopping` is carrying the intent out and a
 *  `destroyed` one has nothing left to carry out, so neither is re-announced.
 *  The stop ORDER is still re-issued in flight, under the same operation
 *  identity — an order that may have been lost must be repeatable, and the
 *  identity is what keeps the repeat one act rather than two.
 *
 *  This is a different act from `cancel`'s DECISION above. That one reports
 *  what an inspection found, and a destroyed attempt contradicts it. This one
 *  performs a cancellation at the authority, and a destroyed runtime merely
 *  leaves nothing to stop. */
function orderQuiescence(store, agent, adapter, attemptId, assignment,
                         operationId) {
	const attempt = requireAttempt(store, attemptId);
	const current = attempt.execution_runtime;
	if (TRANSITIONS.execution_runtime[current].includes("cancel-requested")) {
		observe(store, { attemptId, axis: "execution_runtime",
		                 value: "cancel-requested" });
	}
	if (attempt.runtime_id === null) {
		return { ordered: false,
		         why: `no runtime is attached to attempt ${attemptId}, so `
		              + `there is no agent inside one and nothing to stop` };
	}
	if (current === "destroyed") {
		return { ordered: false,
		         why: `attempt ${attemptId} observed ${attempt.runtime_id} `
		              + `destroyed; there is nothing left to cancel or stop` };
	}
	// THE AGENT FIRST, then the runtime. An agent told to stop after its
	// runtime is already going away never hears the order, and the whole
	// point of asking it is the cooperative shutdown a kill does not give.
	//
	// Both receive the MANAGER's operation identity, so each side settles
	// the same act rather than two acts that happen to be adjacent.
	//
	// A FAILED COOPERATIVE REQUEST DOES NOT VETO THE STOP.
	//
	// Review [P1]: a throwing agent left the function before `adapter.stop`
	// was reached, and the authority had ALREADY fenced and ended the
	// assignment — so an unreachable provider left a fenced runtime running
	// indefinitely. Persistent agent unreachability is a REASON to stop the
	// runtime, not a reason to leave it alone. The failure is captured, the
	// stop is ordered anyway, and only then is the failure re-thrown
	// unchanged: it is the caller's to classify, not this boundary's.
	//
	// PRESENCE IS ITS OWN FACT. Review [P2]: `agentFailure = null` meant
	// BOTH "nothing was thrown" and "`null` was thrown", and JavaScript lets
	// a boundary throw either. An agent that threw `null` had its failure
	// silently dropped — the stop was ordered, but the caller got an
	// ordinary answer and a simultaneous runtime failure lost its partner.
	// This is the same defect the journal's `replay` already carries a note
	// about: a value that also means absence cannot carry presence.
	//
	// The settlements are passed through VERBATIM — no `?? null`. Normalizing
	// them would collapse "the boundary returned nothing" into "the boundary
	// returned null", which is a smaller version of the same mistake and
	// contradicts what the comment below claims this does.
	let agentSettlement;
	let agentFailed = false;
	let agentFailure;
	try {
		agentSettlement = agent.cancel({
			attemptId, assignment, runtimeId: attempt.runtime_id,
			operationId });
	} catch (failure) {
		agentFailed = true;
		agentFailure = failure;
	}
	let runtimeSettlement;
	try {
		runtimeSettlement = adapter.stop({
			runtimeId: attempt.runtime_id, operationId });
	} catch (failure) {
		// Both boundaries failed. Neither is allowed to hide the other, and
		// choosing between them would be this boundary deciding which
		// failure the caller is entitled to see.
		if (agentFailed) {
			throw new AggregateError([agentFailure, failure],
				`neither the agent nor the runtime accepted cancellation for `
				+ `attempt ${attemptId}`);
		}
		throw failure;
	}
	if (agentFailed) throw agentFailure;
	// ORDERED, not done. Each settlement is passed through as the boundary
	// gave it, un-summarized: the manager has no basis for turning either
	// into a fact about the world.
	return { ordered: true, runtimeId: attempt.runtime_id,
	         agentSettlement, runtimeSettlement };
}

/** Step 4: one observation, decided and written atomically.
 *
 *  Review [P1]: this read the current value, checked it in JavaScript, and
 *  wrote unconditionally outside any transaction — so a stale observer could
 *  overwrite a newer value between the two. The transition is decided INSIDE
 *  the write, against the exact value the update compares.
 *
 *  It is also journalled. An exact duplicate — same adapter incarnation,
 *  same source sequence, same observed digest — replays; a conflicting one
 *  refuses, which is what makes "the same observation again" answerable at
 *  all. */
export function observe(store, { attemptId, axis, value, source = null }) {
	const moves = TRANSITIONS[axis];
	if (moves === undefined) {
		throw new ContractError("integrity", "schema",
			`${axis} is not one of the frozen runtime-attempt axes`);
	}
	if (!Object.hasOwn(moves, value)) {
		throw new ContractError("integrity", "schema",
			`${value} is not a value of ${axis}; the axes are frozen by the `
			+ `runtime-attempt manifest`);
	}
	const incarnation = source?.incarnation ?? store.incarnation;
	const observed = digest({ attemptId, axis, value });
	// A SAVEPOINT rather than a transaction, because `observe` is also
	// called from inside a `store.transact` action — the runtime-start
	// operation records `start-requested` within its own journalled
	// transaction, and a nested BEGIN would refuse. A savepoint gives the
	// same all-or-nothing boundary at either depth.
	const mark = `observe_${Math.abs(hashOf(attemptId + axis))}`;
	store.db.exec(`SAVEPOINT ${mark}`);
	try {
		const answer = decide();
		store.db.exec(`RELEASE ${mark}`);
		return answer;
	} catch (failure) {
		try { store.db.exec(`ROLLBACK TO ${mark}`); } catch { /* gone */ }
		try { store.db.exec(`RELEASE ${mark}`); } catch { /* gone */ }
		if (failure instanceof ContractError) throw failure;
		// ONLY CONTENTION IS TRANSLATED.
		//
		// Review [P2]: every non-contract failure was rewritten as another
		// writer's newer observation — so a disk error, a constraint
		// violation or a corrupt page would have carried a portable meaning
		// and a retry policy that belong to a completely different fact. A
		// wrong diagnosis is worse than a raw one, because a caller can see
		// that a raw error is unclassified.
		if (!isContention(failure)) throw failure;
		// A LOCKED DATABASE is a fact about the file, but at this boundary
		// it means exactly one thing: another writer is deciding this
		// attempt, so this observation did not land and the value it would
		// have overwritten is somebody else's newer one.
		throw new ContractError("runtime-observation", "state-regression",
			`${axis} is being decided by another writer; this observation `
			+ `did not land (${failure?.message ?? failure})`);
	}

	function decide() {
		const attempt = requireAttempt(store, attemptId);
		// THE DURABLE IDENTITY IS RESOLVED FIRST, before today's axis is
		// consulted at all.
		//
		// Review [P1]: the current-value shortcut and the transition check
		// ran ahead of it, so an EXACT old observation was refused once the
		// axis had advanced, while a DIFFERENT observation reusing the same
		// source identity slipped through whenever its axis already held the
		// requested value. Both invert the pinned rule. What a source
		// identity already said is a fact about that identity, and today's
		// axis has no bearing on it.
		const sourceSeq = source?.seq
			?? (store.db.prepare(
				"SELECT COALESCE(MAX(source_seq), 0) + 1 AS next FROM "
				+ "observations WHERE runtime_attempt_id = ? AND incarnation = ?")
				.get(attemptId, incarnation).next);
		const prior = store.db.prepare(
			"SELECT observation_digest FROM observations WHERE "
			+ "runtime_attempt_id=? AND incarnation=? AND source_seq=?")
			.get(attemptId, incarnation, sourceSeq);
		if (prior !== undefined) {
			if (prior.observation_digest !== observed) {
				throw new ContractError("runtime-observation",
					"state-regression",
					`incarnation ${incarnation} already reported a different `
					+ `observation at source sequence ${sourceSeq}`);
			}
			// An exact replay returns the recorded answer and changes
			// nothing — never a regression of whatever came after it.
			return { attemptId, axis, value, changed: false, replayed: true };
		}
		const current = attempt[axis];
		// AN ACCEPTED OBSERVATION CONSUMES ITS SOURCE IDENTITY, whether or
		// not it moved an axis.
		//
		// Review [P1]: an inert sourced observation returned success without
		// writing a row, so its `(attempt, incarnation, source_seq)` stayed
		// reusable and a DIFFERENT observation could commit under it. The
		// conflict rule only bit when the first observation happened to
		// change state — which makes the identity's meaning depend on where
		// the axis already was, and the whole point of the identity is that
		// it does not.
		//
		// A manager-internal repeat is left inert: it mints a fresh sequence
		// at every call, so there is no identity for anyone else to reuse
		// and a row would record nothing that could be asked about.
		if (current === value && source === null) {
			return { attemptId, axis, value, changed: false };
		}
		if (current !== value) {
			if (!moves[current].includes(value)) {
				throw new ContractError("runtime-observation",
					"state-regression",
					`${axis} is ${current}; ${value} does not follow it`);
			}
			const changed = store.db.prepare(
				`UPDATE attempts SET ${axis} = ?, `
				+ `observation_seq = observation_seq + 1, `
				+ `observed_at = ? WHERE runtime_attempt_id = ? AND ${axis} = ?`)
				.run(value, store.clock(), attemptId, current).changes;
			if (changed !== 1) {
				throw new ContractError("runtime-observation",
					"state-regression",
					`${axis} moved while this observation was being decided`);
			}
		}
		const managerSeq = store.db.prepare(
			"SELECT COALESCE(MAX(manager_seq), 0) + 1 AS next FROM "
			+ "observations WHERE runtime_attempt_id = ?").get(attemptId).next;
		store.db.prepare(
			"INSERT INTO observations (runtime_attempt_id, incarnation, "
			+ "source_seq, runtime_id, observation_digest, manager_seq, "
			+ "observed_at) VALUES (?, ?, ?, ?, ?, ?, ?)")
			.run(attemptId, incarnation, sourceSeq, attempt.runtime_id,
			     observed, managerSeq, store.clock());
		return { attemptId, axis, value, changed: current !== value,
		         managerSeq };
	}
}

/** Whether a storage failure is CONTENTION and nothing else.
 *
 *  SQLite reports a busy or locked database as its own condition, and only
 *  that one carries the meaning this boundary translates. Everything else —
 *  a constraint, a trigger's abort, a disk or schema fault — keeps its own
 *  identity, because giving it a portable meaning it does not have would
 *  hand a caller the wrong retry policy with full confidence. */
function isContention(failure) {
	// Review [P2]: this matched a substring of the free-form message, and a
	// trigger raising `busy provider invariant` was consequently handed a
	// database lock's meaning and retry policy. The message is
	// APPLICATION-CONTROLLED prose; the result code is SQLite's own answer.
	// `node:sqlite` carries it on `errcode`, where the low byte is the
	// primary code and the high bits are the extended reason — a trigger
	// abort arrives as 1811, whose primary code is SQLITE_CONSTRAINT.
	const errcode = failure?.errcode;
	if (typeof errcode !== "number") return false;
	const primary = errcode & 0xff;
	return primary === SQLITE_BUSY || primary === SQLITE_LOCKED;
}

const SQLITE_BUSY = 5;
const SQLITE_LOCKED = 6;

/** A stable, SQL-identifier-safe name for one savepoint. Savepoint names
 *  cannot be bound as parameters, so they are derived rather than
 *  interpolated from caller text. */
function hashOf(text) {
	let value = 0;
	for (const character of text) {
		value = (value * 31 + character.codePointAt(0)) | 0;
	}
	return value;
}
