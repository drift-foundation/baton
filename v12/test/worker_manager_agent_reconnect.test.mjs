// W2929 item 4, seventh slice: reconnect ambiguity.
//
// §8.4's rule is short and its reasoning is specific, so these cases are
// mostly about the two things the boundary REFUSES and the one durable move
// it makes — and about the identity question being asked of this boundary
// explicitly, which is the commitment the session-axis correction ended on.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { ContractError, digest } from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { recordAttempt } from "../src/worker_manager/attempts.mjs";
import { SESSION_STATES, TERMINAL_SESSION_STATES, permitsSessionTransition }
	from "../src/worker_manager/agent_session_axis.mjs";
import { occupySlot, postureSlot }
	from "../src/worker_manager/posture_slots.mjs";
import { TURN_OUTCOMES } from "../src/worker_manager/agent_turn.mjs";
import { handleTransportLoss, repromptAfterTransportLoss,
         transportReachabilityReidentifies }
	from "../src/worker_manager/agent_reconnect.mjs";

after(removeOwnedRoots);

const UUID = "43c55d4b00ee85c84ae4ed134de36df5";
const WORK = "43c55d4b-W1439";
const ATTEMPT = "attempt-1";
const NOW = "2026-08-22T12:00:00.000Z";
const REF = { runtimeAttemptId: ATTEMPT, posture: "execution",
              sessionEpoch: 1, providerSessionId: null };

function open() {
	return new ControlStore(join(ownedTemp("v12-manager-"), "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
}

function withSession(store, state = "prompting", providerSessionId = null) {
	recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
		adapterDigest: digest("adapter"), profileDigest: digest("profile") });
	// W771: a session always holds its posture slot — `openAgentSession`
	// occupies it in the same transaction that writes the row — so a fixture
	// that writes the row alone is describing a state the manager cannot
	// reach. Transport loss moves that slot to `recovery-required`, which is
	// the ruling's own transition, so the slot has to be here.
	store.db.exec("BEGIN IMMEDIATE");
	occupySlot(store.db, { attemptId: ATTEMPT, posture: "execution",
	                       sessionEpoch: 1, at: NOW });
	store.db.exec("COMMIT");
	store.db.prepare(
		"INSERT INTO agent_sessions (runtime_attempt_id, posture, "
		+ "session_epoch, profile_digest, pinned_policy, work_id, "
		+ "authority_uuid, provider_session_id, state, opened_at) "
		+ "VALUES (?, 'execution', 1, ?, ?, ?, ?, ?, ?, ?)")
		.run(ATTEMPT, digest("profile"), digest("policy"), WORK, UUID,
		     providerSessionId, state, NOW);
	return REF;
}

function storedState(store) {
	return store.db.prepare("SELECT state FROM agent_sessions").get().state;
}

test("W2929: a lost transport ends the epoch at `unknown`", () => {
	const store = open();
	try {
		withSession(store, "prompting");
		// EXTENDED under W771's ruling: ambiguity moves the posture slot to
		// `recovery-required`, and transport loss is the ambiguity. The
		// answer says so, and the durable slot agrees — the two used to
		// disagree, which is the gap W771's review found.
		assert.deepEqual(handleTransportLoss(store, REF, { turnInFlight: true }),
			{ agentSessionRef: { ...REF, providerSessionId: null },
			  sessionState: "unknown",
			  slotOccupancy: "recovery-required",
			  resume: false,
			  reprompt: false,
			  nextEpochAllowedWithoutRuntimeReidentification: false,
			  turnOutcome: "transport-lost" });
		assert.equal(storedState(store), "unknown");
		assert.equal(postureSlot(store, ATTEMPT, "execution").occupancy,
			"recovery-required");
		// `unknown` is TERMINAL, which is what makes this an ending rather
		// than a pause: §3.3 keeps it from becoming `closed`, because closed
		// asserts a terminal fact for every turn the epoch started.
		assert.equal(TERMINAL_SESSION_STATES.includes("unknown"), true);
		assert.equal(permitsSessionTransition("unknown", "closed"), false);
	} finally {
		store.close();
	}
});

test("W2929: with no turn in flight there is no turn outcome to report", () => {
	const store = open();
	try {
		withSession(store, "ready");
		const answer = handleTransportLoss(store, REF, { turnInFlight: false });
		// SELECTED, NEVER INFERRED — the same rule the turn slice carries. A
		// transport that died with nothing running ended an epoch and not a
		// turn, and naming an outcome anyway would be inventing one.
		assert.equal(answer.turnOutcome, null);
		assert.equal(answer.sessionState, "unknown");
		// And the default is the honest one: a caller that says nothing has
		// not told this boundary a turn was running.
		assert.equal(handleTransportLoss(store, REF).turnOutcome, null);
	} finally {
		store.close();
	}
});

test("W2929: `transport-lost` is one of the closed eight", () => {
	// The outcome this boundary names has to be an outcome the turn
	// vocabulary already has; minting a ninth here would put two closed sets
	// in one manager.
	assert.equal(TURN_OUTCOMES.includes("transport-lost"), true);
});

test("W2929: whether a turn was in flight is stated, not inferred", () => {
	const store = open();
	try {
		withSession(store, "prompting");
		for (const value of ["true", 1, null, {}]) {
			assert.throws(
				() => handleTransportLoss(store, REF, { turnInFlight: value }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", String(value));
			assert.equal(storedState(store), "prompting");
		}
	} finally {
		store.close();
	}
});

test("W2929 correction: an absent operand defaults, a wrong one refuses", () => {
	// The distinction the two P1s share, held on its own. A default is for an
	// ARGUMENT NOBODY GAVE; using it for an argument somebody gave wrongly is
	// how a malformed call commits an epoch to `unknown` on operands nobody
	// proved. Driven at both levels: the envelope and the member.
	const store = open();
	try {
		withSession(store, "prompting");
		// Absent, at both levels: the honest default and no refusal.
		assert.equal(handleTransportLoss(store, REF).turnOutcome, null);
		assert.equal(storedState(store), "unknown");
	} finally {
		store.close();
	}
	for (const [what, options] of [["an explicit null member",
	                                { turnInFlight: null }],
	                               ["an undefined member",
	                                { turnInFlight: undefined }],
	                               ["an empty-string member",
	                                { turnInFlight: "" }],
	                               ["a zero member", { turnInFlight: 0 }]]) {
		const store = open();
		try {
			withSession(store, "prompting");
			assert.throws(() => handleTransportLoss(store, REF, options),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", what);
			assert.equal(storedState(store), "prompting", what);
		} finally {
			store.close();
		}
	}
});

test("W2929 correction: the reported reference is read once and is closed", () => {
	// The other half of the snapshot rule: the answer carries EXACTLY the
	// four §3.1 members, so a caller cannot use this boundary to launder an
	// extra field into something that looks like a session reference.
	const store = open();
	try {
		withSession(store, "prompting");
		const answer = handleTransportLoss(store,
			{ ...REF, untrustedExtra: "not part of the reference" });
		assert.deepEqual(Object.keys(answer.agentSessionRef).sort(),
			["posture", "providerSessionId", "runtimeAttemptId",
			 "sessionEpoch"]);
		// And it is a fresh object: editing the answer must not reach
		// whatever the caller still holds.
		answer.agentSessionRef.posture = "consent";
		assert.equal(handleTransportLoss(store, REF).agentSessionRef.posture,
			"execution");
	} finally {
		store.close();
	}
});

test("W2929 correction: a null-prototype document is a record, and behaviour "
	+ "is not", () => {
		// The prototype test in both directions. `Object.create(null)` is a
		// document — it carries no class and no behaviour — so refusing it
		// would have been a list of known-good shapes rather than a rule.
		const store = open();
		try {
			withSession(store, "prompting");
			const record = Object.create(null);
			record.turnInFlight = true;
			assert.equal(handleTransportLoss(store, REF, record).turnOutcome,
				"transport-lost");
			assert.equal(storedState(store), "unknown");
		} finally {
			store.close();
		}
		// And a shape this contract has never seen refuses for the same
		// reason a Date does, rather than because somebody listed it.
		class Options { constructor() { this.turnInFlight = true; } }
		for (const [what, options] of [["a class instance", new Options()],
		                              ["a promise", Promise.resolve()],
		                              ["a typed array", new Uint8Array(1)],
		                              ["a boxed string",
		                               new String("in-flight")]]) {
			const store = open();
			try {
				withSession(store, "prompting");
				assert.throws(() => handleTransportLoss(store, REF, options),
					(error) => error instanceof ContractError
						&& error.category === "integrity"
						&& error.code === "schema", what);
				assert.equal(storedState(store), "prompting", what);
			} finally {
				store.close();
			}
		}
	});

test("W2929 correction: the member must be the caller's OWN", () => {
	// A document created over another object is refused by the PROTOTYPE
	// rule before ownership is even asked — its prototype is neither
	// `Object.prototype` nor null. The reviewer's own case drives that.
	//
	// The own-member rule is load-bearing at the one input the prototype rule
	// admits: a plain record whose `turnInFlight` lives on `Object.prototype`
	// itself. That is prototype pollution, and `in` would read it.
	const polluted = Object.prototype;
	polluted.turnInFlight = true;
	try {
		const store = open();
		try {
			withSession(store, "prompting");
			// An EMPTY document. The caller said nothing about a turn, so the
			// honest answer is the absent default — reading a member somebody
			// else put on the prototype would be reading what this caller
			// never passed.
			assert.equal(handleTransportLoss(store, REF, {}).turnOutcome, null);
			assert.equal(storedState(store), "unknown");
		} finally {
			store.close();
		}
		// And an OWN member still decides, so the rule is about ownership
		// rather than about ignoring the member.
		const store2 = open();
		try {
			withSession(store2, "prompting");
			assert.equal(handleTransportLoss(store2, REF,
				{ turnInFlight: true }).turnOutcome, "transport-lost");
		} finally {
			store2.close();
		}
	} finally {
		delete polluted.turnInFlight;
	}
});

test("W2929: transport loss reaches `unknown` from every live state", () => {
	// EXHAUSTIVE over the vocabulary. A transport can die at any point the
	// epoch is still live, so the states that refuse are exactly the ones
	// that already ended — and `agent-quiescent` is among them, because a
	// terminal turn fact WAS observed there and `unknown` would be a
	// regression in knowledge rather than the honest absence of it.
	const refused = [];
	for (const state of SESSION_STATES) {
		const store = open();
		try {
			withSession(store, state);
			if (state === "unknown") {
				// Already there: reporting the same loss twice answers.
				assert.equal(
					handleTransportLoss(store, REF).sessionState, "unknown");
				continue;
			}
			try {
				handleTransportLoss(store, REF);
				assert.equal(storedState(store), "unknown", state);
			} catch (failure) {
				assert.equal(failure instanceof ContractError, true, state);
				assert.equal(failure.code, "state-regression", state);
				assert.equal(storedState(store), state, state);
				refused.push(state);
			}
		} finally {
			store.close();
		}
	}
	assert.deepEqual(refused, ["agent-quiescent", "closed"]);
});

test("W2929: the identity question is asked of THIS boundary too", () => {
	// The commitment the session-axis correction ended on: every boundary
	// taking a session reference gets the identity question asked of it
	// explicitly, rather than inferred from whether its own subject-matter
	// cases pass. That correction was needed three times because the missing
	// component never breaks a happy path.
	const store = open();
	try {
		withSession(store, "prompting", "provider-session-a");
		for (const providerSessionId of ["provider-session-b", null]) {
			assert.throws(() => handleTransportLoss(store,
				{ ...REF, providerSessionId }, { turnInFlight: true }),
				(error) => error instanceof ContractError
					&& error.category === "runtime-observation"
					&& error.code === "identity-mismatch",
				String(providerSessionId));
			assert.equal(storedState(store), "prompting");
		}
		for (const [what, ref] of [["absent", null],
		                          ["empty attempt", { ...REF,
		                           runtimeAttemptId: "" }],
		                          ["foreign posture", { ...REF,
		                           posture: "review" }],
		                          ["zero epoch", { ...REF, sessionEpoch: 0 }]]) {
			assert.throws(() => handleTransportLoss(store, ref),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", what);
			assert.equal(storedState(store), "prompting", what);
		}
		// And the agreeing reference ends the epoch, so the refusals above
		// are about the label rather than about the boundary being closed.
		assert.equal(handleTransportLoss(store,
			{ ...REF, providerSessionId: "provider-session-a" },
			{ turnInFlight: true }).sessionState, "unknown");
	} finally {
		store.close();
	}
});

test("W2929 review: the answer carries the one session reference it bound",
	() => {
		const store = open();
		try {
			withSession(store, "prompting", "provider-session-a");
			let reads = 0;
			const shifting = {
				runtimeAttemptId: ATTEMPT,
				posture: "execution",
				sessionEpoch: 1,
				get providerSessionId() {
					reads += 1;
					return reads === 1
						? "provider-session-a" : "provider-session-b";
				},
				untrustedExtra: "does not belong to an agent-session reference",
			};
			const answer = handleTransportLoss(store, shifting,
				{ turnInFlight: true });
			assert.equal(storedState(store), "unknown");
			// The axis bound provider A. Re-reading and spreading the caller's
			// object after that commit can label the answer as provider B and
			// can copy members the closed reference shape does not have.
			assert.deepEqual(answer.agentSessionRef,
				{ ...REF, providerSessionId: "provider-session-a" });
			assert.equal(reads, 1,
				"the reference was read again after its durable observation");
		} finally {
			store.close();
		}
	});

test("W2929 review: malformed transport-loss options move no axis", () => {
	const observed = [];
	for (const [what, options] of [["null", null], ["boolean", true],
	                              ["text", "in-flight"], ["array", []]]) {
		const store = open();
		try {
			withSession(store, "prompting");
			let failure = null;
			try { handleTransportLoss(store, REF, options); }
			catch (caught) { failure = caught; }
			observed.push({ what, refusal: failure instanceof ContractError
				? `${failure.category}.${failure.code}`
				: failure?.constructor?.name ?? null,
				state: storedState(store) });
		} finally {
			store.close();
		}
	}
	assert.deepEqual(observed, ["null", "boolean", "text", "array"]
		.map((what) => ({ what, refusal: "integrity.schema",
		                   state: "prompting" })));
});

test("W2929 re-review: an options document is a plain record", () => {
	class OptionsInstance {}
	const inherited = Object.create({ turnInFlight: true });
	const observed = [];
	for (const [what, options] of [["date", new Date(0)],
	                              ["map", new Map()],
	                              ["regular expression", /in-flight/],
	                              ["class instance", new OptionsInstance()],
	                              ["inherited member", inherited]]) {
		const store = open();
		try {
			withSession(store, "prompting");
			let failure = null;
			try { handleTransportLoss(store, REF, options); }
			catch (caught) { failure = caught; }
			observed.push({ what, refusal: failure instanceof ContractError
				? `${failure.category}.${failure.code}`
				: failure?.constructor?.name ?? null,
				state: storedState(store) });
		} finally {
			store.close();
		}
	}
	assert.deepEqual(observed, ["date", "map", "regular expression",
	                           "class instance", "inherited member"]
		.map((what) => ({ what, refusal: "integrity.schema",
		                   state: "prompting" })));
});

test("W2929 third review: a non-boolean member refuses without serializing it",
	() => {
		const store = open();
		try {
			withSession(store, "prompting");
			assert.throws(() => handleTransportLoss(store, REF,
				{ turnInFlight: 1n }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema");
			assert.equal(storedState(store), "prompting");
		} finally {
			store.close();
		}
	});

test("W2929 third review: refusing a non-record does not run its prototype",
	() => {
		const prototype = Object.create(null);
		Object.defineProperty(prototype, "constructor", {
			get() { throw new Error("untrusted constructor getter ran"); },
		});
		const store = open();
		try {
			withSession(store, "prompting");
			assert.throws(() => handleTransportLoss(store, REF,
				Object.create(prototype)),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema");
			assert.equal(storedState(store), "prompting");
		} finally {
			store.close();
		}
	});

test("W2929 correction: a refusal never runs the value it is refusing", () => {
	// The general rule the two review cases are instances of. Every one of
	// these is hostile in a DIFFERENT way, and none of them may reach the
	// caller as anything but the closed pair — the refusal has already
	// decided; touching the value afterwards can only lose that decision.
	const throwingToJSON = { toJSON() { throw new Error("toJSON ran"); } };
	const throwingValueOf = { valueOf() { throw new Error("valueOf ran"); } };
	const hostileProto = Object.create(null);
	Object.defineProperty(hostileProto, "constructor", {
		get() { throw new Error("constructor ran"); } });
	const cases = [
		["a BigInt member", { turnInFlight: 1n }],
		["a symbol member", { turnInFlight: Symbol("yes") }],
		["a throwing toJSON member", { turnInFlight: throwingToJSON }],
		["a throwing valueOf member", { turnInFlight: throwingValueOf }],
		["a hostile-prototype envelope", Object.create(hostileProto)],
		["a BigInt envelope", 1n],
		["a symbol envelope", Symbol("options")],
	];
	for (const [what, options] of cases) {
		const store = open();
		try {
			withSession(store, "prompting");
			assert.throws(() => handleTransportLoss(store, REF, options),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", what);
			assert.equal(storedState(store), "prompting", what);
		} finally {
			store.close();
		}
	}
});

test("W2929 fourth review: prototype reflection failure uses the closed pair",
	() => {
		const options = new Proxy({}, {
			getPrototypeOf() { throw new Error("prototype trap ran"); },
		});
		const store = open();
		try {
			withSession(store, "prompting");
			assert.throws(() => handleTransportLoss(store, REF, options),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema");
			assert.equal(storedState(store), "prompting");
		} finally {
			store.close();
		}
	});

test("W2929 fourth review: an options member is data, not behaviour", () => {
	let ran = false;
	const options = {};
	Object.defineProperty(options, "turnInFlight", {
		get() { ran = true; throw new Error("member getter ran"); },
	});
	const store = open();
	try {
		withSession(store, "prompting");
		assert.throws(() => handleTransportLoss(store, REF, options),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema");
		assert.equal(ran, false, "the boundary executed an options accessor");
		assert.equal(storedState(store), "prompting");
	} finally {
		store.close();
	}
});

test("W2929 correction: an ACCEPTED document is not touched either", () => {
	// A plain record carrying a hostile `Symbol.toStringTag` is a legitimate
	// document — its prototype is `Object.prototype` and it has no own
	// `turnInFlight`, so the honest answer is the absent default. The
	// property worth asserting is that getting there ran nothing: my first
	// version of this case expected a REFUSAL and was wrong about which rule
	// applied, which is its own small lesson about asserting the rule rather
	// than the outcome you assumed.
	let ran = false;
	const document = {};
	Object.defineProperty(document, Symbol.toStringTag, {
		get() { ran = true; return "Options"; } });
	const store = open();
	try {
		withSession(store, "prompting");
		assert.equal(handleTransportLoss(store, REF, document).turnOutcome,
			null);
		assert.equal(storedState(store), "unknown");
		assert.equal(ran, false, "the boundary read the document's tag");
	} finally {
		store.close();
	}
});

test("W2929 correction: the refusal still says something useful", () => {
	// Coarse is not useless. A diagnostic that has to be exactly right about
	// an untrusted value is one that has to touch it, so these are the facts
	// that cost nothing: what kind of thing it was, and roughly what shape.
	const store = open();
	try {
		withSession(store, "prompting");
		for (const [options, expected] of [
				[1n, /a bigint value/],
				["in-flight", /a string value/],
				[new Date(0), /an object with a prototype of its own/],
				[[], /an array/],
				[null, /null/],
				[{ turnInFlight: 7 }, /a number value/]]) {
			assert.throws(() => handleTransportLoss(store, REF, options),
				(error) => expected.test(error.message),
				`${String(options)} -> ${expected}`);
		}
	} finally {
		store.close();
	}
});

test("W2929 correction: reflection is translated at EVERY site, not the last",
	() => {
		// The rule I stated last round and applied at one of two sites. A
		// Proxy traps `getPrototypeOf`, and the record test reflected before
		// the description did — so the guard I wrote was downstream of the
		// leak it was for.
		const store = open();
		try {
			withSession(store, "prompting");
			for (const [what, options] of [
					["a trapping prototype", new Proxy({}, {
						getPrototypeOf() { throw new Error("trap ran"); } })],
					["a trapping ownKeys", new Proxy({}, {
						getOwnPropertyDescriptor() {
							throw new Error("descriptor trap ran"); } })]]) {
				assert.throws(() => handleTransportLoss(store, REF, options),
					(error) => error instanceof ContractError
						&& error.category === "integrity"
						&& error.code === "schema", what);
				assert.equal(storedState(store), "prompting", what);
			}
		} finally {
			store.close();
		}
	});

test("W2929 correction: an operand is DATA, and a getter is a program", () => {
	// `hasOwnProperty` runs nothing, but the property read that followed it
	// executed an own accessor — so an ACCEPTED plain record could still run
	// behaviour at a boundary whose whole rule is that it does not.
	let ran = false;
	const withGetter = {};
	Object.defineProperty(withGetter, "turnInFlight", {
		enumerable: true, get() { ran = true; return true; } });
	const store = open();
	try {
		withSession(store, "prompting");
		assert.throws(() => handleTransportLoss(store, REF, withGetter),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema");
		assert.equal(ran, false, "the boundary ran the caller's getter");
		assert.equal(storedState(store), "prompting");
	} finally {
		store.close();
	}
	// A data member of the same name still decides, so the rule is about the
	// KIND of member rather than about ignoring it.
	const other = open();
	try {
		withSession(other, "prompting");
		assert.equal(handleTransportLoss(other, REF,
			{ turnInFlight: true }).turnOutcome, "transport-lost");
	} finally {
		other.close();
	}
});

test("W2929 fifth review: revoked proxies keep reflection in the closed pair",
	() => {
		const revoked = () => {
			const pair = Proxy.revocable({}, {});
			pair.revoke();
			return pair.proxy;
		};
		for (const [what, options] of [
			["a revoked options envelope", revoked()],
			["a revoked member value", { turnInFlight: revoked() }],
		]) {
			const store = open();
			try {
				withSession(store, "prompting");
				assert.throws(() => handleTransportLoss(store, REF, options),
					(error) => error instanceof ContractError
						&& error.category === "integrity"
						&& error.code === "schema", what);
				assert.equal(storedState(store), "prompting", what);
			} finally {
				store.close();
			}
		}
	});

test("W2929 fifth review: refusing descriptor failure runs no thrown value",
	() => {
		let ran = false;
		const failure = {};
		Object.defineProperty(failure, "message", {
			get() { ran = true; throw new Error("failure message getter ran"); },
		});
		const options = new Proxy({}, {
			getOwnPropertyDescriptor() { throw failure; },
		});
		const store = open();
		try {
			withSession(store, "prompting");
			assert.throws(() => handleTransportLoss(store, REF, options),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema");
			assert.equal(ran, false,
				"the boundary inspected the value thrown by a reflection trap");
			assert.equal(storedState(store), "prompting");
		} finally {
			store.close();
		}
	});

test("W2929 correction: no refusal interviews the value that was thrown",
	() => {
		// The review found this at ONE catch. The rule is about every catch
		// that establishes a refusal, so this drives all three reflection
		// traps this boundary can hit and asserts the same thing of each:
		// the thrown value is never touched.
		const hostile = () => {
			const thrown = {};
			for (const member of ["message", "name", "stack", "code",
			                      "toString", "valueOf"]) {
				Object.defineProperty(thrown, member, {
					get() { ran = true; throw new Error(`${member} was read`); },
				});
			}
			return thrown;
		};
		let ran = false;
		for (const [what, options] of [
			["a getPrototypeOf trap on the envelope",
			 new Proxy({}, { getPrototypeOf() { throw hostile(); } })],
			["a getOwnPropertyDescriptor trap on the envelope",
			 new Proxy({}, { getOwnPropertyDescriptor() { throw hostile(); } })],
			["a getPrototypeOf trap on the member value",
			 { turnInFlight: new Proxy({},
				{ getPrototypeOf() { throw hostile(); } }) }],
		]) {
			ran = false;
			const store = open();
			try {
				withSession(store, "prompting");
				assert.throws(() => handleTransportLoss(store, REF, options),
					(error) => error instanceof ContractError
						&& error.category === "integrity"
						&& error.code === "schema", what);
				assert.equal(ran, false, what);
				assert.equal(storedState(store), "prompting", what);
			} finally {
				store.close();
			}
		}
	});

test("W2929 correction: an array is not a document however it is dressed",
	() => {
		// The prototype test alone stops saying so once a Proxy is involved:
		// array classification follows a proxy to its target, but a
		// getPrototypeOf trap answers whatever it likes.
		const dressed = () => new Proxy([], {
			getPrototypeOf() { return Object.prototype; },
		});
		// SUPERSEDED DIAGNOSTIC, on the sixth review's P1, and marked where
		// it stood: the two dressed entries used to assert "an array" too.
		// A Proxy is now refused BEFORE any reflection, so a dressed array
		// never reaches array classification and is named for what it is.
		// The refusal itself — the rule this case owns — is unchanged, and
		// it is now reached earlier and without running a trap.
		for (const [what, options, says] of [
			["a bare array envelope", [], /an array/],
			["an array envelope wearing Object.prototype", dressed(), /a Proxy/],
			["an array member", { turnInFlight: [] }, /an array/],
			["a member array wearing Object.prototype",
			 { turnInFlight: dressed() }, /a Proxy/],
		]) {
			const store = open();
			try {
				withSession(store, "prompting");
				assert.throws(() => handleTransportLoss(store, REF, options),
					(error) => error instanceof ContractError
						&& error.category === "integrity"
						&& error.code === "schema"
						&& says.test(error.message), what);
				assert.equal(storedState(store), "prompting", what);
			} finally {
				store.close();
			}
		}
	});

test("W2929 sixth review: a Proxy envelope is not a plain record", () => {
	// The envelope rule admits ordinary object literals and null-prototype
	// records. A Proxy over one is neither: even traps that return plausible
	// answers are caller programs. Accepting their answers both runs behaviour
	// and lets a non-document commit the epoch.
	let ran = false;
	const proxy = new Proxy({}, {
		getPrototypeOf() { ran = true; return Object.prototype; },
		getOwnPropertyDescriptor() { ran = true; return undefined; },
	});
	const store = open();
	try {
		withSession(store, "prompting");
		assert.throws(() => handleTransportLoss(store, REF, proxy),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema");
		assert.equal(ran, false, "the accepted envelope ran a Proxy trap");
		assert.equal(storedState(store), "prompting");
	} finally {
		store.close();
	}
});

test("W2929 sixth review: refusing a Proxy member runs no trap", () => {
	let ran = false;
	const proxy = new Proxy({}, {
		getPrototypeOf() { ran = true; return Object.prototype; },
	});
	const store = open();
	try {
		withSession(store, "prompting");
		assert.throws(() => handleTransportLoss(store, REF,
			{ turnInFlight: proxy }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema");
		assert.equal(ran, false, "the refusal ran a member Proxy trap");
		assert.equal(storedState(store), "prompting");
	} finally {
		store.close();
	}
});

test("W2929 correction: an options value never runs, accepted or refused",
	() => {
		// Five rounds went into making reflection FAIL safely and the whole
		// time the ordinary case was the hole: a trap that ANSWERS needs no
		// exception at all. So this case does not name the two traps the
		// review used — it instruments EVERY trap a Proxy has and asserts
		// that none of them runs, whatever the boundary decides.
		const TRAPS = ["apply", "construct", "defineProperty",
			"deleteProperty", "get", "getOwnPropertyDescriptor",
			"getPrototypeOf", "has", "isExtensible", "ownKeys",
			"preventExtensions", "set", "setPrototypeOf"];
		let ran = [];
		const watched = (target) => new Proxy(target, Object.fromEntries(
			TRAPS.map((trap) => [trap, (...args) => {
				ran.push(trap);
				return Reflect[trap](...args);
			}])));
		const revoked = () => {
			const pair = Proxy.revocable({}, {});
			pair.revoke();
			return pair.proxy;
		};
		for (const [what, make] of [
			["an empty document", () => watched({})],
			// THE SHARP END: this one would answer correctly. It is refused
			// anyway, because the rule is about what the value IS and not
			// about whether its answers happen to be right this time.
			["a document that would answer correctly",
			 () => watched({ turnInFlight: true })],
			["a revoked one", revoked],
			["a document over a null-prototype record",
			 () => watched(Object.create(null))],
			["a member", () => ({ turnInFlight: watched({}) })],
			["a revoked member", () => ({ turnInFlight: revoked() })],
		]) {
			ran = [];
			const store = open();
			try {
				withSession(store, "prompting");
				assert.throws(() => handleTransportLoss(store, REF, make()),
					(error) => error instanceof ContractError
						&& error.category === "integrity"
						&& error.code === "schema", what);
				assert.deepEqual(ran, [], `${what}: ran ${ran.join(", ")}`);
				assert.equal(storedState(store), "prompting", what);
			} finally {
				store.close();
			}
		}
		// AND THE GUARD DOES NOT SIMPLY REFUSE EVERYTHING. A refusal that
		// refuses ordinary data would pass every case above and none of the
		// contract: the plain records this boundary exists to accept still
		// commit the epoch.
		for (const options of [undefined, {}, { turnInFlight: true },
		                       Object.create(null)]) {
			const store = open();
			try {
				withSession(store, "prompting");
				assert.equal(handleTransportLoss(store, REF, options)
					.sessionState, "unknown");
			} finally {
				store.close();
			}
		}
	});

test("W2929: an epoch belongs to a session", () => {
	const store = open();
	try {
		recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
			adapterDigest: digest("adapter"),
			profileDigest: digest("profile") });
		assert.throws(() => handleTransportLoss(store, REF),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
	} finally {
		store.close();
	}
});

test("W2929: re-prompting after transport loss is refused, whatever is sent",
	() => {
		// `ambiguous.operation` and not `refused.precondition`: the manager is
		// not saying the request is malformed or out of order, it is saying it
		// CANNOT KNOW what the first attempt did. The prompt is ignored on
		// purpose — the refusal is about the epoch, not about what is re-sent.
		for (const prompt of [undefined, null, "the original prompt",
		                      [{ type: "text", text: "again" }], {}]) {
			assert.throws(() => repromptAfterTransportLoss(prompt),
				(error) => error instanceof ContractError
					&& error.category === "ambiguous"
					&& error.code === "operation", String(prompt));
		}
	});

test("W2929: transport reachability is NEVER re-identification", () => {
	// The mirror of §7.4's quiescence gate: a fact about a socket is not a
	// fact about the process that held the generation. W151 §9 answers this
	// and is not built here, so this says so rather than letting a later
	// caller assume reachability was enough.
	for (const evidence of [undefined, null, true, "reconnected",
	                        { socket: "open", pid: 4242 }]) {
		assert.equal(transportReachabilityReidentifies(evidence), false,
			String(evidence));
	}
});
