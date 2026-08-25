// W771: posture occupancy, separated from the observation axis.
//
// `work/records/2026/08/finding-agent-session-close-axis-conflict/`
//
// The ruling's whole content is that two facts stopped being one, so most of
// these cases assert a PAIR: what the provider was observed to do, and
// whether the posture may be used again. The interesting results are the ones
// where those two disagree — `observation: unknown` with `slot: available` is
// coherent and is the normal shape after transport loss.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { ContractError, digest } from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { recordAttempt } from "../src/worker_manager/attempts.mjs";
import { closeAgentSession } from "../src/worker_manager/agent_session.mjs";
import { observeAgentSessionState }
	from "../src/worker_manager/agent_session_axis.mjs";
import { handleTransportLoss }
	from "../src/worker_manager/agent_reconnect.mjs";
import { RECOVERY_EVIDENCE, SLOT_OCCUPANCY, occupySlot, postureSlot,
         releaseSlot, requireSlotRecovery }
	from "../src/worker_manager/posture_slots.mjs";

after(removeOwnedRoots);

const UUID = "43c55d4b00ee85c84ae4ed134de36df5";
const WORK = "43c55d4b-W1439";
const ATTEMPT = "attempt-1";
const NOW = "2026-08-22T12:00:00.000Z";
const CONTAINER = "baton-worker-attempt-1-execution-1";

function open() {
	return new ControlStore(join(ownedTemp("v12-manager-"), "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
}

/** An attempt, one occupied execution slot, and its session row. */
function withSession(store, state = "ready", providerSessionId = null) {
	recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
		adapterDigest: digest("adapter"), profileDigest: digest("profile") });
	// W771 review: `runtime-absent` evidence must name the EXACT runtime the
	// attempt is durably attached to, so the fixture attaches one.
	store.db.prepare("UPDATE attempts SET runtime_id = ? WHERE "
		+ "runtime_attempt_id = ?").run(CONTAINER, ATTEMPT);
	const db = store.db;
	db.exec("BEGIN IMMEDIATE");
	occupySlot(db, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1,
	                 at: NOW });
	db.prepare(
		"INSERT INTO agent_sessions (runtime_attempt_id, posture, "
		+ "session_epoch, profile_digest, pinned_policy, work_id, "
		+ "authority_uuid, provider_session_id, state, opened_at) "
		+ "VALUES (?, 'execution', 1, ?, ?, ?, ?, ?, ?, ?)")
		.run(ATTEMPT, digest("profile"), digest("policy"), WORK, UUID,
		     providerSessionId, state, NOW);
	db.exec("COMMIT");
	return { runtimeAttemptId: ATTEMPT, posture: "execution", sessionEpoch: 1,
	         providerSessionId };
}

function addSession(store, epoch, state = "ready", providerSessionId = null) {
	const db = store.db;
	db.exec("BEGIN IMMEDIATE");
	occupySlot(db, { attemptId: ATTEMPT, posture: "execution",
	                 sessionEpoch: epoch, at: NOW });
	db.prepare(
		"INSERT INTO agent_sessions (runtime_attempt_id, posture, "
		+ "session_epoch, profile_digest, pinned_policy, work_id, "
		+ "authority_uuid, provider_session_id, state, opened_at) "
		+ "VALUES (?, 'execution', ?, ?, ?, ?, ?, ?, ?, ?)")
		.run(ATTEMPT, epoch, digest("profile"), digest("policy"), WORK, UUID,
		     providerSessionId, state, NOW);
	db.exec("COMMIT");
	return { runtimeAttemptId: ATTEMPT, posture: "execution", sessionEpoch: epoch,
	         providerSessionId };
}

function slot(store, posture = "execution") {
	return postureSlot(store, ATTEMPT, posture)?.occupancy ?? null;
}

function observation(store) {
	return store.db.prepare("SELECT state FROM agent_sessions").get().state;
}

// -- the two axes are two --------------------------------------------------

test("W771: occupancy is three states and is not the observation axis", () => {
	assert.deepEqual([...SLOT_OCCUPANCY],
		["available", "occupied", "recovery-required"]);
	// No member of either axis appears in the other. That is the ruling in
	// one assertion: `closed` is evidence and `available` is capacity.
	const sessionStates = ["not-started", "initializing", "ready", "prompting",
		"turn-ended", "cancel-requested", "agent-quiescent", "unknown",
		"closed"];
	assert.deepEqual(
		SLOT_OCCUPANCY.filter((value) => sessionStates.includes(value)), []);
});

test("W771: absence evidence is a closed set, and intent is not in it", () => {
	assert.deepEqual([...RECOVERY_EVIDENCE],
		["provider-session-closed", "runtime-absent"]);
	// The three things that are NOT evidence, named so the omission reads as
	// a decision: a stop REQUEST, an elapsed deadline, and a disconnect.
	for (const wish of ["stop-requested", "deadline-elapsed",
	                    "transport-disconnected"]) {
		assert.equal(RECOVERY_EVIDENCE.includes(wish), false, wish);
	}
});

// -- the required lifecycle cases ------------------------------------------

test("W771: a NORMAL close observes `closed` and returns the slot", () => {
	const store = open();
	try {
		const ref = withSession(store, "ready");
		assert.equal(slot(store), "occupied");
		observeAgentSessionState(store, ref, "prompting");
		observeAgentSessionState(store, ref, "turn-ended");
		// CORRECTED under the review: this used to release BEFORE recording
		// `closed`, which is exactly the defect — the label was accepted
		// while the observation still said `turn-ended`. The product's own
		// close path makes the observation and the release one act, and the
		// release reads the observation that act just made.
		const answer = closeAgentSession(store, { attemptId: ATTEMPT,
			posture: "execution", epoch: 1 });
		assert.equal(answer.closed, true);
		assert.equal(answer.state, "closed");
		assert.equal(answer.slot, "available");
		assert.equal(slot(store), "available");
		assert.equal(observation(store), "closed");
		// And a bare release BEFORE the observation refuses, which is the
		// same rule seen from the other side.
		const other = open();
		try {
			withSession(other, "ready");
			assert.throws(() => releaseSlot(other, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1,
				evidence: "provider-session-closed",
				reason: "asserting a close that was never observed" }),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& error.code === "precondition");
			assert.equal(slot(other), "occupied");
		} finally {
			other.close();
		}
	} finally {
		store.close();
	}
});

test("W771 review: a provider-close label is not the observation", () => {
	const store = open();
	try {
		withSession(store, "ready");
		assert.throws(() => releaseSlot(store, { attemptId: ATTEMPT,
			posture: "execution", sessionEpoch: 1,
			evidence: "provider-session-closed",
			reason: "somebody claimed the provider closed" }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		assert.deepEqual(
			{ observation: observation(store), slot: slot(store) },
			{ observation: "ready", slot: "occupied" });
	} finally {
		store.close();
	}
});

test("W771: a NEVER-SUBMITTED session recovers without inventing an ending",
	() => {
		const store = open();
		try {
			withSession(store, "not-started");
			// This is the case the old code got wrong. It used to write
			// `closed` over `not-started` — an edge §7.3 forbids — because
			// `closed` was the only thing that freed a posture.
			requireSlotRecovery(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1,
				reason: "the session never initialized" });
			assert.equal(slot(store), "recovery-required");
			releaseSlot(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1,
				evidence: "runtime-absent", runtimeIdentity: CONTAINER,
				reason: "the exact assignment container was observed absent" });
			assert.equal(slot(store), "available");
			// AND THE OBSERVATION IS UNTOUCHED. Nothing was ever seen ending,
			// so nothing says it did.
			assert.equal(observation(store), "not-started");
		} finally {
			store.close();
		}
	});

test("W771: TRANSPORT LOSS leaves unknown observed and the slot recoverable",
	() => {
		const store = open();
		try {
			const ref = withSession(store, "prompting");
			handleTransportLoss(store, ref, { turnInFlight: true });
			requireSlotRecovery(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1,
				reason: "the transport died and nothing observed the ending" });
			// The coherent durable shape the ruling describes, before
			// recovery and after it.
			assert.equal(observation(store), "unknown");
			assert.equal(slot(store), "recovery-required");
			releaseSlot(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1,
				evidence: "runtime-absent", runtimeIdentity: CONTAINER,
				reason: "the exact assignment container was observed stopped" });
			assert.deepEqual(
				{ observation: observation(store), slot: slot(store) },
				{ observation: "unknown", slot: "available" });
			// `unknown` STAYS. Recovering capacity never promotes it.
			assert.throws(() => observeAgentSessionState(store, ref, "closed"),
				(error) => error instanceof ContractError
					&& error.code === "state-regression");
		} finally {
			store.close();
		}
	});

test("W771 review: transport loss itself enters slot recovery", () => {
	const store = open();
	try {
		const ref = withSession(store, "prompting");
		handleTransportLoss(store, ref, { turnInFlight: true });
		assert.deepEqual(
			{ observation: observation(store),
			  occupancy: postureSlot(store, ATTEMPT, "execution").occupancy,
			  sessionEpoch: postureSlot(store, ATTEMPT, "execution").sessionEpoch },
			{ observation: "unknown", occupancy: "recovery-required",
			  sessionEpoch: 1 });
	} finally {
		store.close();
	}
});

test("W771: a stop REQUEST recovers nothing; the observation does", () => {
	const store = open();
	try {
		withSession(store, "prompting");
		requireSlotRecovery(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1,
			reason: "cancellation was ordered and nothing answered" });
		for (const [what, operands] of [
				["a stop request", { evidence: "stop-requested" }],
				["an elapsed deadline", { evidence: "deadline-elapsed" }],
				["a disconnect", { evidence: "transport-disconnected" }],
				["no evidence at all", {}],
				["absence naming no runtime", { evidence: "runtime-absent" }],
				["absence naming an empty runtime",
				 { evidence: "runtime-absent", runtimeIdentity: "" }]]) {
			assert.throws(() => releaseSlot(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1, reason: "wanted the posture back",
				...operands }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", what);
			assert.equal(slot(store), "recovery-required", what);
		}
		// The exact container, observed. That is the difference.
		releaseSlot(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1,
			evidence: "runtime-absent", runtimeIdentity: CONTAINER,
			reason: "the exact assignment container was observed stopped" });
		assert.equal(slot(store), "available");
	} finally {
		store.close();
	}
});

test("W771 review: runtime absence binds the attached runtime identity", () => {
	const store = open();
	try {
		withSession(store, "prompting");
		store.db.prepare("UPDATE attempts SET runtime_id = ? WHERE "
			+ "runtime_attempt_id = ?").run(CONTAINER, ATTEMPT);
		requireSlotRecovery(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1, reason: "the transport died" });
		assert.throws(() => releaseSlot(store, { attemptId: ATTEMPT,
			posture: "execution", sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: "stale-container",
			reason: "a different container was absent" }),
			(error) => error instanceof ContractError
				&& error.category === "runtime-observation"
				&& error.code === "identity-mismatch");
		assert.equal(slot(store), "recovery-required");
		releaseSlot(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: CONTAINER,
			reason: "the attached runtime was observed absent" });
		assert.equal(slot(store), "available");
	} finally {
		store.close();
	}
});

test("W771 review: delayed slot evidence cannot move a newer epoch", () => {
	const store = open();
	try {
		withSession(store, "ready");
		requireSlotRecovery(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1, reason: "epoch one became ambiguous" });
		releaseSlot(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: CONTAINER, reason: "epoch one was absent" });
		addSession(store, 2, "ready");
		for (const act of [
			() => requireSlotRecovery(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1,
				reason: "a late epoch-one disconnect" }),
			() => releaseSlot(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1,
				evidence: "runtime-absent", runtimeIdentity: CONTAINER,
				reason: "late epoch-one absence" }),
		]) {
			assert.throws(act, (error) => error instanceof ContractError
				&& error.category === "runtime-observation"
				&& error.code === "identity-mismatch");
			assert.deepEqual(postureSlot(store, ATTEMPT, "execution"),
				{ attemptId: ATTEMPT, posture: "execution",
				  occupancy: "occupied", sessionEpoch: 2, reason: null,
				  changedAt: NOW });
		}
	} finally {
		store.close();
	}
});

test("W771 review: a delayed close cannot release a newer epoch", () => {
	const store = open();
	try {
		withSession(store, "ready");
		requireSlotRecovery(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1, reason: "epoch one became ambiguous" });
		releaseSlot(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: CONTAINER, reason: "epoch one was absent" });
		addSession(store, 2, "ready");
		try {
			closeAgentSession(store, { attemptId: ATTEMPT,
				posture: "execution", epoch: 1 });
		} catch (failure) {
			assert.equal(failure instanceof ContractError, true);
			assert.equal(failure.code, "identity-mismatch");
		}
		assert.deepEqual(postureSlot(store, ATTEMPT, "execution"),
			{ attemptId: ATTEMPT, posture: "execution", occupancy: "occupied",
			  sessionEpoch: 2, reason: null, changedAt: NOW });
		assert.deepEqual(store.db.prepare("SELECT session_epoch, state FROM "
			+ "agent_sessions ORDER BY session_epoch").all()
			.map((row) => ({ session_epoch: row.session_epoch,
			                 state: row.state })),
			[{ session_epoch: 1, state: "closed" },
			 { session_epoch: 2, state: "ready" }]);
	} finally {
		store.close();
	}
});

test("W771 second review: a transport-loss retry survives later recovery", () => {
	const store = open();
	try {
		const ref = withSession(store, "prompting");
		handleTransportLoss(store, ref, { turnInFlight: true });
		releaseSlot(store, { attemptId: ATTEMPT, posture: "execution",
			sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: CONTAINER, reason: "epoch one was absent" });
		// The first report committed before its response was lost; another
		// manager then recovered the slot. Replaying the report must neither
		// refuse nor put an available posture back into recovery. The observation
		// and the recovery are both durable facts, and neither supersedes the
		// other.
		assert.doesNotThrow(() => handleTransportLoss(store, ref,
			{ turnInFlight: true }));
		assert.deepEqual(
			{ observation: observation(store), slot: slot(store) },
			{ observation: "unknown", slot: "available" });
	} finally {
		store.close();
	}
});

test("W771 second review: delayed transport loss cannot hide its observation "
	+ "or move a newer epoch", () => {
	const store = open();
	try {
		const first = withSession(store, "ready");
		requireSlotRecovery(store, { attemptId: ATTEMPT, posture: "execution",
			sessionEpoch: 1, reason: "epoch one became ambiguous" });
		releaseSlot(store, { attemptId: ATTEMPT, posture: "execution",
			sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: CONTAINER, reason: "epoch one was absent" });
		addSession(store, 2, "ready");
		// As with a delayed normal close, this is two independent facts. The old
		// epoch really lost transport, so its observation lands; the slot now
		// belongs to epoch two, so it does not move.
		assert.doesNotThrow(() => handleTransportLoss(store, first,
			{ turnInFlight: false }));
		assert.deepEqual(postureSlot(store, ATTEMPT, "execution"),
			{ attemptId: ATTEMPT, posture: "execution", occupancy: "occupied",
			  sessionEpoch: 2, reason: null, changedAt: NOW });
		assert.deepEqual(store.db.prepare("SELECT session_epoch, state FROM "
			+ "agent_sessions ORDER BY session_epoch").all()
			.map((row) => ({ session_epoch: row.session_epoch, state: row.state })),
			[{ session_epoch: 1, state: "unknown" },
			 { session_epoch: 2, state: "ready" }]);
	} finally {
		store.close();
	}
});

test("W771: a RETRIED recovery answers, and a re-reported ambiguity keeps the "
	+ "first reason", () => {
		const store = open();
		try {
			withSession(store, "prompting");
			const first = requireSlotRecovery(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1, reason: "the transport died" });
			assert.equal(first.moved, true);
			const again = requireSlotRecovery(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1, reason: "somebody looked again" });
			// The later report observed nothing new, so it changes nothing —
			// including the reason a reader will find.
			assert.equal(again.moved, false);
			assert.equal(postureSlot(store, ATTEMPT, "execution").reason,
				"the transport died");
			const released = releaseSlot(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1,
				evidence: "runtime-absent",
				runtimeIdentity: CONTAINER, reason: "observed absent" });
			assert.equal(released.moved, true);
			assert.equal(releaseSlot(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1,
				evidence: "runtime-absent",
				runtimeIdentity: CONTAINER, reason: "observed absent" }).moved,
				false);
			assert.equal(slot(store), "available");
		} finally {
			store.close();
		}
	});

test("W771: a slot survives restart, and silence never recovers it", () => {
	const path = join(ownedTemp("v12-manager-"), "control.sqlite3");
	const first = new ControlStore(path,
		{ incarnation: "manager-1", clock: () => NOW });
	try {
		withSession(first, "prompting");
		requireSlotRecovery(first, { attemptId: ATTEMPT, posture: "execution",
			sessionEpoch: 1, reason: "the manager crashed mid-turn" });
	} finally {
		first.close();
	}
	// A NEW manager incarnation, later. Elapsed time and a fresh process are
	// not evidence: the slot is exactly where the last observation left it.
	const restarted = new ControlStore(path,
		{ incarnation: "manager-2", clock: () => "2026-08-22T18:00:00.000Z" });
	try {
		assert.equal(slot(restarted), "recovery-required");
		assert.equal(observation(restarted), "prompting");
		assert.equal(postureSlot(restarted, ATTEMPT, "execution").reason,
			"the manager crashed mid-turn");
		releaseSlot(restarted, { attemptId: ATTEMPT, posture: "execution",
			sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: CONTAINER,
			reason: "the exact assignment container was observed absent" });
		assert.equal(slot(restarted), "available");
	} finally {
		restarted.close();
	}
});

test("W771: recovering the slot decides nothing about retained output", () => {
	const store = open();
	try {
		const ref = withSession(store, "prompting");
		handleTransportLoss(store, ref, { turnInFlight: true });
		requireSlotRecovery(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1,
			reason: "the transport died" });
		releaseSlot(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1,
			evidence: "runtime-absent", runtimeIdentity: CONTAINER,
			reason: "observed stopped" });
		// Stopping the container recovers EXECUTION CAPACITY. It does not
		// discard a filesystem, accept an output or choose salvage — those
		// are independent disposition decisions, and this module writes
		// nothing about any of them.
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM outputs").get().n, 0);
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM intake").get().n, 0);
		assert.deepEqual(
			{ observation: observation(store), slot: slot(store) },
			{ observation: "unknown", slot: "available" });
	} finally {
		store.close();
	}
});

// -- occupancy itself ------------------------------------------------------

test("W771: the two postures hold separate slots", () => {
	const store = open();
	try {
		withSession(store, "ready");
		const db = store.db;
		db.exec("BEGIN IMMEDIATE");
		occupySlot(db, { attemptId: ATTEMPT, posture: "consent", sessionEpoch: 1,
		                 at: NOW });
		db.exec("COMMIT");
		assert.equal(slot(store, "execution"), "occupied");
		assert.equal(slot(store, "consent"), "occupied");
		// Runtime evidence, because a provider-close release now READS the
		// session's own observation and this consent slot has no session —
		// which is itself the rule working.
		releaseSlot(store, { attemptId: ATTEMPT, posture: "consent",
			sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: CONTAINER,
			reason: "the exact assignment container was observed absent" });
		assert.equal(slot(store, "consent"), "available");
		assert.equal(slot(store, "execution"), "occupied",
			"the two postures shared a slot");
	} finally {
		store.close();
	}
});

test("W771: an occupied slot refuses a second occupant", () => {
	const store = open();
	try {
		withSession(store, "ready");
		const db = store.db;
		db.exec("BEGIN IMMEDIATE");
		assert.throws(() => occupySlot(db, { attemptId: ATTEMPT,
			posture: "execution", sessionEpoch: 2, at: NOW }),
			(error) => error instanceof ContractError
				&& error.category === "runtime-observation"
				&& error.code === "duplicate-runtime");
		db.exec("ROLLBACK");
		// And a slot needing recovery refuses one too: that is the whole
		// point of the middle state.
		requireSlotRecovery(store, { attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1,
			reason: "the transport died" });
		db.exec("BEGIN IMMEDIATE");
		assert.throws(() => occupySlot(db, { attemptId: ATTEMPT,
			posture: "execution", sessionEpoch: 2, at: NOW }),
			(error) => error instanceof ContractError
				&& error.code === "duplicate-runtime");
		db.exec("ROLLBACK");
	} finally {
		store.close();
	}
});

test("W771 correction: an unattached attempt has no absence to observe", () => {
	// The refusal is `refused.precondition`, not `identity-mismatch`: there
	// is no attached identity for a claim to disagree WITH. Driven because
	// the comparison alone would refuse this too, with a pair that says the
	// caller named the wrong runtime when the truth is that this attempt
	// names none.
	const store = open();
	try {
		withSession(store, "prompting");
		store.db.prepare("UPDATE attempts SET runtime_id = NULL WHERE "
			+ "runtime_attempt_id = ?").run(ATTEMPT);
		requireSlotRecovery(store, { attemptId: ATTEMPT, posture: "execution",
			sessionEpoch: 1, reason: "the transport died" });
		assert.throws(() => releaseSlot(store, { attemptId: ATTEMPT,
			posture: "execution", sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: CONTAINER, reason: "observed absent" }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		assert.equal(slot(store), "recovery-required");
	} finally {
		store.close();
	}
});

test("W771 correction: the two endings share one asymmetry", () => {
	// The rule the reviewer taught me for `closeAgentSession` and I did not
	// carry to transport loss: the OBSERVATION is about the epoch and always
	// lands; the SLOT movement is about the posture and only applies to its
	// own occupant. Held once, over both endings, so the next ending has a
	// property to satisfy rather than a precedent to notice.
	for (const [what, end] of [
			["transport loss", (store) => handleTransportLoss(store,
				{ runtimeAttemptId: ATTEMPT, posture: "execution",
				  sessionEpoch: 1, providerSessionId: null })],
			["a normal close", (store) => closeAgentSession(store,
				{ attemptId: ATTEMPT, posture: "execution", epoch: 1 })]]) {
		const store = open();
		try {
			withSession(store, what === "a normal close" ? "ready"
				: "prompting");
			// Epoch 1's slot is recovered on positive evidence, then epoch 2
			// takes the posture — so epoch 1's ending is late twice over.
			requireSlotRecovery(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1,
				reason: "epoch one became ambiguous" });
			releaseSlot(store, { attemptId: ATTEMPT, posture: "execution",
				sessionEpoch: 1, evidence: "runtime-absent",
				runtimeIdentity: CONTAINER, reason: "epoch one was absent" });
			addSession(store, 2, "ready");
			const answer = end(store);
			// THE ANSWER REPORTS THE OCCUPANCY THAT ACTUALLY HOLDS, not the
			// one this ending would have produced on its own — a caller that
			// is told `recovery-required` while the posture is occupied by a
			// later epoch has been told something false about the posture.
			assert.equal(what === "a normal close" ? answer.slot
				: answer.slotOccupancy, "occupied", what);
			// The observation LANDED for epoch 1...
			const rows = store.db.prepare("SELECT session_epoch, state FROM "
				+ "agent_sessions ORDER BY session_epoch").all();
			assert.equal(rows[0].state,
				what === "a normal close" ? "closed" : "unknown", what);
			// ...and epoch 2's posture is exactly as it was.
			assert.equal(rows[1].state, "ready", what);
			assert.deepEqual(postureSlot(store, ATTEMPT, "execution"),
				{ attemptId: ATTEMPT, posture: "execution",
				  occupancy: "occupied", sessionEpoch: 2, reason: null,
				  changedAt: NOW }, what);
		} finally {
			store.close();
		}
	}
});

test("W771: a slot that was never occupied recovers nothing", () => {
	const store = open();
	try {
		recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
			adapterDigest: digest("adapter"),
			profileDigest: digest("profile") });
		assert.equal(postureSlot(store, ATTEMPT, "execution"), null);
		for (const act of [
				() => requireSlotRecovery(store, { attemptId: ATTEMPT,
					posture: "execution", sessionEpoch: 1, reason: "wishful" }),
				() => releaseSlot(store, { attemptId: ATTEMPT,
					posture: "execution", sessionEpoch: 1,
					evidence: "provider-session-closed", reason: "wishful" })]) {
			assert.throws(act, (error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		}
	} finally {
		store.close();
	}
});

test("W771: an available slot cannot become ambiguous", () => {
	const store = open();
	try {
		withSession(store, "ready");
		releaseSlot(store, { attemptId: ATTEMPT, posture: "execution",
			sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: CONTAINER, reason: "observed absent" });
		// Ambiguity is about an epoch that MIGHT still act. A slot nothing
		// holds has nothing to be ambiguous about.
		assert.throws(() => requireSlotRecovery(store, { attemptId: ATTEMPT,
			posture: "execution", sessionEpoch: 1, reason: "second thoughts" }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		assert.equal(slot(store), "available");
	} finally {
		store.close();
	}
});

test("W771: every slot movement carries a reason a reader can use", () => {
	const store = open();
	try {
		withSession(store, "ready");
		for (const reason of [undefined, null, "", "   ", 7]) {
			assert.throws(() => requireSlotRecovery(store,
				{ attemptId: ATTEMPT, posture: "execution", sessionEpoch: 1, reason }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", String(reason));
			assert.throws(() => releaseSlot(store, { attemptId: ATTEMPT,
				posture: "execution", sessionEpoch: 1,
				evidence: "provider-session-closed", reason }),
				(error) => error instanceof ContractError
					&& error.code === "schema", String(reason));
		}
		assert.equal(slot(store), "occupied");
	} finally {
		store.close();
	}
});

test("W771: a malformed slot reference is refused before any lookup", () => {
	const store = open();
	try {
		withSession(store, "ready");
		for (const [what, operands] of [
				["no attempt", { attemptId: "", posture: "execution" }],
				["a foreign posture", { attemptId: ATTEMPT,
				                        posture: "review" }],
				["no posture", { attemptId: ATTEMPT, posture: null }]]) {
			assert.throws(() => postureSlot(store, operands.attemptId,
				operands.posture),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", what);
			assert.throws(() => requireSlotRecovery(store,
				{ ...operands, sessionEpoch: 1, reason: "why" }),
				(error) => error instanceof ContractError
					&& error.code === "schema", what);
		}
	} finally {
		store.close();
	}
});

test("W771: the DATABASE refuses an invented occupancy", () => {
	const store = open();
	try {
		withSession(store, "ready");
		// The real enforcement, and it is stronger than a read-side check: a
		// store written by some other process cannot hold a value outside the
		// three, because the column will not take one.
		assert.throws(
			() => store.db.prepare(
				"UPDATE posture_slots SET occupancy = 'borrowed'").run(),
			(failure) => /CHECK constraint/i.test(String(failure?.message)));
		assert.equal(slot(store), "occupied");
		// `postureSlot`'s own vocabulary check is therefore MEASURED AS
		// UNREACHABLE through SQL and is kept as defence against a store
		// built some other way. It is not counted as a guard, and this case
		// asserts the constraint that actually holds rather than the line
		// that cannot fire.
	} finally {
		store.close();
	}
});
