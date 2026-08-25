// W2929 item 4, second slice: opening an agent session.
//
// The pinned rules are all about SEPARATION — two postures that never share
// an epoch or a connection, an assignment that only one of them has, and a
// Baton capability neither of them receives. So most of these cases assert
// what is ABSENT, and the last of them asserts it of the module's own
// signature rather than of its behaviour.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { V12Authority, V12 } from "../src/authority/index.mjs";
import { ContractError, digest } from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { activateAssignment, recordAttempt }
	from "../src/worker_manager/attempts.mjs";
import { certifyAgentSessionProfile }
	from "../src/worker_manager/agent_profile.mjs";
import { agentSessionsOf, closeAgentSession, nextEpoch, openAgentSession }
	from "../src/worker_manager/agent_session.mjs";
import { releaseSlot, requireSlotRecovery }
	from "../src/worker_manager/posture_slots.mjs";

after(removeOwnedRoots);

const UUID = "43c55d4b00ee85c84ae4ed134de36df5";
const WORK = "43c55d4b-W1439";
const WHO = "poc.claude";
const ATTEMPT = "attempt-1";
const NOW = "2026-08-22T12:00:00.000Z";
const ASSIGNMENT = { authorityUuid: UUID, workId: WORK, participant: WHO,
                     generation: 1 };

function open() {
	return new ControlStore(join(ownedTemp("v12-manager-"), "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
}

// The ACP boundary model's own profile, as in the certification suite: its
// per-posture policies are the design's, so what a session pins here is what
// the design pinned rather than what this suite invented.
const ACP_PROFILE = {
	 "session_family": "baton.agent-session",
	 "version": {
	  "major": 1,
	  "minor": 0
	 },
	 "document": "profile",
	 "profile_id": "profile-acp-worker-1",
	 "created_at": "2026-08-21T22:00:00.000Z",
	 "wire_protocol": "acp",
	 "pinned_wire_version": 1,
	 "provider_binding": null,
	 "adapter": {
	  "name": "native-acp-relay",
	  "version": "1.0-design",
	  "build_digest": "sha256:b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1"
	 },
	 "client_capabilities": {
	  "fs": {},
	  "terminal": false
	 },
	 "session_capabilities": [
	  "session.cancel",
	  "session.fresh",
	  "session.mode-pin",
	  "session.permission-refusal",
	  "session.prompt",
	  "session.update-normalization"
	 ],
	 "postures": {
	  "consent": {
	   "policy": {
	    "kind": "acp",
	    "session_mode_id": "plan"
	   },
	   "workspace": false,
	   "declared_output": false
	  },
	  "execution": {
	   "policy": {
	    "kind": "acp",
	    "session_mode_id": "acceptEdits"
	   },
	   "workspace": true,
	   "declared_output": true
	  }
	 },
	 "mcp_servers": [],
	 "limits": {
	  "setup_deadline_ms": 120000,
	  "turn_deadline_ms": 900000,
	  "cancel_drain_deadline_ms": 30000,
	  "max_event_bytes": 16000,
	  "max_queue_events": 1024,
	  "max_queue_bytes": 4194304
	 },
	 "agent_policy_digest": "sha256:c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3",
	 "document_digest": "sha256:3c7b7a50953dd4075533c7c3d90d034920f34bb458b07d799d0f61419bccbe4a"
	};

/** The manager's own authority handle. It answers ONE question — what the
 *  live assignment is — and records that it was asked. */
function api({ assignment = ASSIGNMENT } = {}) {
	const calls = [];
	return { calls, participant: WHO,
	         assignmentOf(workId) { calls.push(workId); return assignment; } };
}

function claimed(store) {
	store.db.prepare(
		"INSERT INTO offers (offer_id, work_id, authority_uuid, participant, "
		+ "runtime_attempt_id, incarnation, input_digest, policy_digest, "
		+ "profile_digest, verifier, verifier_spent, issued_at, expires_at, "
		+ "state, claim_generation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, "
		+ "?, ?, 'claimed', 1)")
		.run("offer-1", WORK, UUID, WHO, ATTEMPT, "manager-1", digest("input"),
		     digest("policy"), digest("profile"), `sha256:${"0".repeat(64)}`,
		     NOW, "2026-08-22T13:00:00.000Z");
}

/** An attempt that names a Work. `activated` additionally fixes the exact
 *  assignment, which only an execution session has. */
function attemptFor(store, { activated = false } = {}) {
	recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
		adapterDigest: digest("adapter"), profileDigest: digest("profile") });
	if (activated) {
		claimed(store);
		activateAssignment(store,
			{ participant: WHO, assignmentOf: () => ASSIGNMENT },
			{ attemptId: ATTEMPT, expect: ASSIGNMENT });
	} else {
		// A consent session exists BEFORE any claim, so the attempt knows its
		// Work and nothing else about an assignment.
		store.db.prepare("UPDATE attempts SET work_id = ?, authority_uuid = ? "
			+ "WHERE runtime_attempt_id = ?").run(WORK, UUID, ATTEMPT);
	}
	return certifyAgentSessionProfile(store, ACP_PROFILE).digest;
}

test("W2929: a CONSENT session has no assignment, workspace or output", () => {
	const store = open();
	try {
		const profileDigest = attemptFor(store);
		const opened = openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "consent", profileDigest });
		assert.equal(opened.assignment, null);
		assert.equal(opened.workspace, false);
		assert.equal(opened.declaredOutput, false);
		assert.deepEqual(opened.workRef, { authorityUuid: UUID, workId: WORK });
		assert.equal(opened.pinnedPolicy,
			digest(ACP_PROFILE.postures.consent.policy));
		const [row] = agentSessionsOf(store, ATTEMPT);
		assert.equal(row.participant, null);
		assert.equal(row.generation, null);
	} finally {
		store.close();
	}
});

test("W2929: an EXECUTION session has the exact assignment", () => {
	const store = open();
	try {
		const profileDigest = attemptFor(store, { activated: true });
		const opened = openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "execution", profileDigest });
		assert.deepEqual(opened.assignment,
			{ participant: WHO, generation: 1 });
		assert.equal(opened.workspace, true);
		assert.equal(opened.declaredOutput, true);
		// The cross-field rule the frozen schema's own description says it
		// cannot express: this assignment's Work is the session's Work.
		assert.deepEqual(opened.workRef, { authorityUuid: UUID, workId: WORK });
		assert.equal(opened.pinnedPolicy,
			digest(ACP_PROFILE.postures.execution.policy));
	} finally {
		store.close();
	}
});

test("W2929: the two postures pin DIFFERENT policies", () => {
	const store = open();
	try {
		const profileDigest = attemptFor(store, { activated: true });
		const consent = openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "consent", profileDigest });
		const execution = openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "execution", profileDigest });
		assert.notEqual(consent.pinnedPolicy, execution.pinnedPolicy,
			"the separation certification enforces was lost when opening");
	} finally {
		store.close();
	}
});

test("W2929: an EXECUTION session needs an activated attempt", () => {
	const store = open();
	try {
		const profileDigest = attemptFor(store);
		assert.throws(() => openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "execution", profileDigest }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		assert.equal(agentSessionsOf(store, ATTEMPT).length, 0);
	} finally {
		store.close();
	}
});

test("W2929: every epoch is FRESH, ACROSS LEGITIMATE CLOSURES", () => {
	const store = open();
	try {
		// Review [P1]: the first version of this case opened three consent
		// epochs AT ONCE and called that freshness. Freshness and concurrency
		// are two rules; this one drives the terminal transition between
		// same-posture epochs, and the concurrency rule has its own case.
		const profileDigest = attemptFor(store, { activated: true });
		const epochs = [];
		for (const posture of ["consent", "consent", "execution", "consent"]) {
			const opened = openAgentSession(store, api(),
				{ attemptId: ATTEMPT, posture, profileDigest });
			const epoch = opened.agentSessionRef.sessionEpoch;
			epochs.push([posture, epoch]);
			// MIGRATED under W771's ruling. This case is about EPOCH
			// FRESHNESS, and it used to get the posture back by writing
			// `closed` over a `not-started` row — an edge §7.3 forbids, taken
			// because `closed` was also the only thing that freed a posture.
			// A session that never initialized ended AMBIGUOUSLY, so the
			// honest path is the one the ruling added: the slot needs
			// recovery, and positive absence evidence returns it. The
			// observation stays `not-started`, because that is what was seen.
			// W771 review: evidence names the EPOCH it is about and the
			// EXACT runtime the attempt is attached to, so this attaches one
			// before observing it absent.
			store.db.prepare("UPDATE attempts SET runtime_id = ? WHERE "
				+ "runtime_attempt_id = ?")
				.run(`container-${posture}-${epoch}`, ATTEMPT);
			requireSlotRecovery(store, { attemptId: ATTEMPT, posture,
				sessionEpoch: epoch,
				reason: "the session never initialized" });
			releaseSlot(store, { attemptId: ATTEMPT, posture,
				sessionEpoch: epoch, evidence: "runtime-absent",
				runtimeIdentity: `container-${posture}-${epoch}`,
				reason: "the exact assignment container was observed absent" });
		}
		assert.deepEqual(epochs, [["consent", 1], ["consent", 2],
		                          ["execution", 1], ["consent", 3]],
			"an epoch was reused, or the two postures shared a counter");
		// A finished epoch is never reopened: the next one is always the next.
		assert.equal(nextEpoch(store, ATTEMPT, "consent"), 4);
		assert.equal(nextEpoch(store, ATTEMPT, "execution"), 2);
		// AND RECOVERY REWROTE NO HISTORY. Every epoch's observation is still
		// exactly what the provider was seen to do, which is the whole of
		// W771's separation.
		assert.deepEqual(agentSessionsOf(store, ATTEMPT)
			.map((row) => row.state),
			["not-started", "not-started", "not-started", "not-started"]);
	} finally {
		store.close();
	}
});

test("W771: positive absence evidence recovers the posture", () => {
	// RENAMED on the review's case-specific authority. The old title, "only
	// CLOSING frees the posture", became false the moment the ruling
	// separated the two axes — closing is now ONE kind of positive evidence
	// and runtime absence is another. Every assertion below is retained and
	// strengthened.
	const store = open();
	try {
		const profileDigest = attemptFor(store);
		const first = openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "consent", profileDigest });
		// `unknown` is transport ambiguity — where a second session is most
		// tempting and least safe — and it does NOT free the posture.
		//
		// MIGRATED under W771's ruling, and the property is UNCHANGED: what
		// used to free the slot was writing `closed` over that `unknown`,
		// which §3.3 names as recording knowledge nobody acquired. Positive
		// absence evidence frees it now, and the `unknown` observation
		// SURVIVES — the durable result is exactly the coherent shape the
		// ruling describes.
		store.db.prepare("UPDATE agent_sessions SET state = 'unknown' "
			+ "WHERE runtime_attempt_id = ?").run(ATTEMPT);
		store.db.prepare("UPDATE attempts SET runtime_id = ? WHERE "
			+ "runtime_attempt_id = ?").run("container-consent-1", ATTEMPT);
		requireSlotRecovery(store, { attemptId: ATTEMPT, posture: "consent",
			sessionEpoch: 1,
			reason: "the transport died and nothing observed the ending" });
		assert.throws(() => openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "consent", profileDigest }),
			(error) => error instanceof ContractError
				&& error.code === "duplicate-runtime");
		// And a stop REQUEST is not the observation, so it recovers nothing:
		// only evidence from the closed set moves the slot.
		for (const [what, operands] of [
				["no evidence", { }],
				["a stop request", { evidence: "stop-requested" }],
				["absence without an identity",
				 { evidence: "runtime-absent" }]]) {
			assert.throws(() => releaseSlot(store, { attemptId: ATTEMPT,
				posture: "consent", sessionEpoch: 1,
				reason: "wanted the posture back", ...operands }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", what);
		}
		releaseSlot(store, { attemptId: ATTEMPT, posture: "consent",
			sessionEpoch: 1, evidence: "runtime-absent",
			runtimeIdentity: "container-consent-1",
			reason: "the exact assignment container was observed absent" });
		assert.equal(openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "consent", profileDigest })
			.agentSessionRef.sessionEpoch, 2);
		// The first epoch's observation is untouched: recovery recovers
		// CAPACITY and never relabels evidence.
		assert.equal(agentSessionsOf(store, ATTEMPT)
			.find((row) => row.session_epoch === 1).state, "unknown");
		assert.equal(first.agentSessionRef.sessionEpoch, 1);
	} finally {
		store.close();
	}
});

test("W2929: the DATABASE refuses the second open session", () => {
	const path = join(ownedTemp("v12-manager-"), "control.sqlite3");
	const first = new ControlStore(path, { incarnation: "manager-1",
		clock: () => NOW });
	const second = new ControlStore(path, { incarnation: "manager-2",
		clock: () => NOW });
	try {
		const profileDigest = attemptFor(first);
		openAgentSession(first, api(),
			{ attemptId: ATTEMPT, posture: "consent", profileDigest });
		// A read of MAX followed by a separate insert is not an atomic
		// allocator, so the guard that decides is the partial unique index —
		// driven from a SECOND connection, which no read-then-write check
		// could refuse.
		assert.throws(() => openAgentSession(second, api(),
			{ attemptId: ATTEMPT, posture: "consent", profileDigest }),
			(error) => error instanceof ContractError
				&& error.category === "runtime-observation"
				&& error.code === "duplicate-runtime");
		assert.equal(agentSessionsOf(first, ATTEMPT).length, 1);
	} finally {
		first.close();
		second.close();
	}
});

test("W2929 review: one posture cannot have two concurrent sessions", () => {
	const store = open();
	try {
		const profileDigest = attemptFor(store);
		openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "consent", profileDigest });
		assert.throws(() => openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "consent", profileDigest }),
			(error) => error instanceof ContractError
				&& error.category === "runtime-observation"
				&& error.code === "duplicate-runtime");
		assert.equal(agentSessionsOf(store, ATTEMPT).length, 1,
			"the refused concurrent session still opened another epoch");
	} finally {
		store.close();
	}
});

test("W2929 review: execution cannot open after its assignment ended", () => {
	const root = ownedTemp("v12-manager-");
	const authority = V12Authority.create(join(root, "authority.sqlite3"),
		{ authorityUuid: UUID });
	const store = new ControlStore(join(root, "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
	try {
		authority.certifyContract(V12);
		authority.addRouteHandler("impl", WHO);
		authority.createWork({ workId: WORK, route: "impl", contract: V12 });
		const api = authority.session(WHO);
		const assignment = api.claim({ workId: WORK,
			operationId: "claim:session-review" });
		recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
			adapterDigest: digest("adapter"), profileDigest: digest("profile") });
		claimed(store);
		activateAssignment(store, api,
			{ attemptId: ATTEMPT, expect: assignment });
		const profileDigest =
			certifyAgentSessionProfile(store, ACP_PROFILE).digest;
		api.cancel({ expect: assignment, operationId: "cancel:session-review",
			reason: "assignment ended before the agent session opened" });
		// The call shape moved to carry the manager's OWN authority handle,
		// which is the boundary this same finding asked for. Every assertion
		// below is the reviewer's, unchanged.
		assert.throws(() => openAgentSession(store, api,
			{ attemptId: ATTEMPT, posture: "execution", profileDigest }),
			(error) => error instanceof ContractError
				&& error.category === "stale-assignment"
				&& error.code === "ended");
		assert.equal(agentSessionsOf(store, ATTEMPT).length, 0);
	} finally {
		store.close();
	}
});

test("W2929 review: execution uses the assignment participant's session", () => {
	const root = ownedTemp("v12-manager-");
	const authority = V12Authority.create(join(root, "authority.sqlite3"),
		{ authorityUuid: UUID });
	const store = new ControlStore(join(root, "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
	try {
		authority.certifyContract(V12);
		authority.addRouteHandler("impl", WHO);
		authority.createWork({ workId: WORK, route: "impl", contract: V12 });
		const claimant = authority.session(WHO);
		const assignment = claimant.claim({ workId: WORK,
			operationId: "claim:participant-session-review" });
		recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
			adapterDigest: digest("adapter"), profileDigest: digest("profile") });
		claimed(store);
		activateAssignment(store, claimant,
			{ attemptId: ATTEMPT, expect: assignment });
		const profileDigest =
			certifyAgentSessionProfile(store, ACP_PROFILE).digest;
		const foreign = authority.session("poc.gemini");
		assert.throws(() => openAgentSession(store, foreign,
			{ attemptId: ATTEMPT, posture: "execution", profileDigest }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		assert.equal(agentSessionsOf(store, ATTEMPT).length, 0);
	} finally {
		store.close();
	}
});

test("W2929: an UNCERTIFIED profile opens nothing", () => {
	const store = open();
	try {
		attemptFor(store, { activated: true });
		assert.throws(() => openAgentSession(store, api(), { attemptId: ATTEMPT,
			posture: "consent", profileDigest: digest("not certified") }),
			(error) => error instanceof ContractError
				&& error.category === "policy"
				&& error.code === "profile-uncertified");
		assert.equal(agentSessionsOf(store, ATTEMPT).length, 0);
	} finally {
		store.close();
	}
});

test("W2929: a WITHDRAWN profile opens nothing", () => {
	const store = open();
	try {
		const profileDigest = attemptFor(store, { activated: true });
		store.db.prepare("UPDATE profiles SET withdrawn_at = ? WHERE digest = ?")
			.run(NOW, profileDigest);
		assert.throws(() => openAgentSession(store, api(),
			{ attemptId: ATTEMPT, posture: "consent", profileDigest }),
			(error) => error instanceof ContractError
				&& error.code === "profile-uncertified");
	} finally {
		store.close();
	}
});

test("W2929: only the two pinned postures exist", () => {
	const store = open();
	try {
		const profileDigest = attemptFor(store, { activated: true });
		for (const posture of ["admin", "consent-ish", "", "CONSENT"]) {
			assert.throws(() => openAgentSession(store, api(),
				{ attemptId: ATTEMPT, posture, profileDigest }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", posture);
		}
	} finally {
		store.close();
	}
});

test("W2929: a retained profile edited after certification opens nothing",
	() => {
		const store = open();
		try {
			const profileDigest = attemptFor(store, { activated: true });
			// A guard on the way IN cannot see an edit made afterwards, so the
			// loader re-binds the bytes to the key they are filed under.
			store.db.prepare("UPDATE profiles SET body = ? WHERE digest = ?")
				.run(JSON.stringify({ ...ACP_PROFILE, profile_id: "other" }),
				     profileDigest);
			assert.throws(() => openAgentSession(store, api(),
				{ attemptId: ATTEMPT, posture: "consent", profileDigest }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "digest");
		} finally {
			store.close();
		}
	});

test("W2929 review: retained profile must declare the digest it is filed under",
	() => {
		const store = open();
		try {
			const profileDigest = attemptFor(store, { activated: true });
			const tampered = { ...ACP_PROFILE,
				document_digest: `sha256:${"0".repeat(64)}` };
			store.db.prepare("UPDATE profiles SET body = ? WHERE digest = ?")
				.run(JSON.stringify(tampered), profileDigest);
			assert.throws(() => openAgentSession(store, api(),
				{ attemptId: ATTEMPT, posture: "consent", profileDigest }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "digest");
			assert.equal(agentSessionsOf(store, ATTEMPT).length, 0);
		} finally {
			store.close();
		}
	});

test("W2929: the AUTHORITY HANDLE reaches no answer and no durable row", () => {
	const store = open();
	try {
		// Review [P1]: my first version of this case forbade the manager from
		// HAVING a handle, and that conflated two roles. The trusted Worker
		// Manager IS the one Baton authority client and must reproject the
		// assignment; the untrusted agent endpoint and relay are what must
		// never receive a capability. So the rule is about where the handle
		// GOES, not about whether the manager has one.
		const profileDigest = attemptFor(store, { activated: true });
		const handle = api();
		const opened = openAgentSession(store, handle,
			{ attemptId: ATTEMPT, posture: "execution", profileDigest });
		// It was USED — the liveness read is the whole reason it is here.
		assert.deepEqual(handle.calls, [WORK]);
		// And it appears in nothing the caller is handed...
		const answer = JSON.stringify(opened);
		// NAMES A HANDLE ACTUALLY TRAVELS UNDER, and nothing wider. I made
		// this list too blunt one round ago — forbidding "authority" and
		// failing on `authority_uuid` — and then did it again here with
		// `participant`, which is the assignment's own identity and not a
		// capability at all. Twice is a habit, so the list is now only what a
		// session object exposes.
		for (const forbidden of ["assignmentOf", "calls"]) {
			assert.equal(answer.includes(forbidden), false,
				`the opened session carries ${forbidden}`);
		}
		assert.equal(Object.values(opened).some((v) => typeof v === "function"),
			false, "the opened session carries a callable");
		// ...nor in any column of the durable row.
		const [row] = agentSessionsOf(store, ATTEMPT);
		for (const value of Object.values(row)) {
			assert.notEqual(typeof value, "function");
			assert.equal(String(value).includes("assignmentOf"), false);
		}
	} finally {
		store.close();
	}
});

test("W2929: a MUTATING participant getter cannot pass the binding", () => {
	const store = open();
	try {
		const profileDigest = attemptFor(store, { activated: true });
		// A getter that answers correctly once and differently afterwards
		// does not get past — and what lands in the row is the ATTEMPT's
		// participant, never the handle's. Measured: the local snapshot is
		// EQUIVALENT to reading the getter inline, because the value is used
		// exactly once; what this case pins is the single read and the
		// source of the stored value, not the variable.
		let answered = 0;
		const shifty = {
			get participant() {
				answered += 1;
				return answered === 1 ? WHO : "poc.gemini";
			},
			assignmentOf: () => ASSIGNMENT,
		};
		const opened = openAgentSession(store, shifty,
			{ attemptId: ATTEMPT, posture: "execution", profileDigest });
		assert.equal(answered, 1,
			"the participant binding was read more than once");
		assert.deepEqual(opened.assignment, { participant: WHO, generation: 1 });
		// And what landed is the ATTEMPT's participant, never the handle's.
		assert.equal(agentSessionsOf(store, ATTEMPT)[0].participant, WHO);
	} finally {
		store.close();
	}
});

test("W2929: a CONSENT session needs no authority handle at all", () => {
	const store = open();
	try {
		// The binding rule is about the assignment an EXECUTION session
		// claims. A consent session exists before any claim, so requiring a
		// handle for it would be requiring proof of something that does not
		// exist yet.
		const profileDigest = attemptFor(store);
		const opened = openAgentSession(store, null,
			{ attemptId: ATTEMPT, posture: "consent", profileDigest });
		assert.equal(opened.assignment, null);
		assert.equal(agentSessionsOf(store, ATTEMPT).length, 1);
	} finally {
		store.close();
	}
});
