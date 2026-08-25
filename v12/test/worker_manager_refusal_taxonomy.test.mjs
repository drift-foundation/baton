// W2929 composition revalidation: THE CLOSED TAXONOMY, SWEPT.
//
// Six review rounds on the reconnect primitive established that a refusal must
// never serialize, read, hash or otherwise run the value it is refusing, and
// each round fixed the ONE site the reviewer had found. This file is what I
// should have written after the first of them: the rule stated once, over
// every boundary in the manager, so the next site is covered before someone
// has to find it.
//
// The property is deliberately weak per boundary and strong across them.
// It does not say what any boundary decides — that belongs to the suite that
// owns the boundary. It says that whatever it decides, it says so in the
// closed `category`/`code` pair, for operands chosen to break the two things
// diagnostics are built from: serialization and reflection.
//
// A boundary added later that does not appear here is not covered. The list
// is enumerated rather than discovered on purpose, because a sweep that finds
// its own subjects silently stops finding them when an export is renamed.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { ContractError, nameValue, opaqueIdFault, withinFrozenLength }
	from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import * as axis from "../src/worker_manager/agent_session_axis.mjs";
import * as turn from "../src/worker_manager/agent_turn.mjs";
import * as events from "../src/worker_manager/agent_events.mjs";
import * as slots from "../src/worker_manager/posture_slots.mjs";
import * as shake from "../src/worker_manager/agent_handshake.mjs";
import * as attempts from "../src/worker_manager/attempts.mjs";

after(removeOwnedRoots);

const NOW = "2026-08-22T12:00:00.000Z";

function open() {
	return new ControlStore(join(ownedTemp("v12-manager-"), "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
}

/** Operands that break the two things a diagnostic is built from.
 *
 *  A BigInt and a circular object defeat SERIALIZATION. A throwing `toJSON`
 *  and a trapping Proxy defeat it by RUNNING, and the Proxy defeats
 *  reflection too. Between them they cover every way `JSON.stringify` has
 *  actually escaped a refusal in this manager. */
function hostileOperands() {
	const circular = () => {
		const value = {};
		value.self = value;
		return value;
	};
	return [
		["a BigInt", () => 1n],
		["a circular object", circular],
		["a throwing toJSON", () => ({ toJSON() { throw new Error("ran"); } })],
		["a trapping Proxy",
		 () => new Proxy({}, { ownKeys() { throw new Error("trap"); },
		                       getPrototypeOf() { throw new Error("trap"); } })],
		["a symbol", () => Symbol("operand")],
		["a function", () => function operand() {}],
	];
}

/** Every boundary that takes a caller operand, named rather than discovered. */
function boundaries(store) {
	const ref = { runtimeAttemptId: "attempt-1", posture: "execution",
	              sessionEpoch: 1, providerSessionId: "provider-1" };
	return [
		["normalizeAgentSessionRef", (v) => axis.normalizeAgentSessionRef(v)],
		["permitsSessionTransition", (v) => axis.permitsSessionTransition(v, v)],
		["satisfiesRuntimeQuiescenceGate",
		 (v) => axis.satisfiesRuntimeQuiescenceGate(v)],
		["observeAgentSessionState", (v) => axis.observeAgentSessionState(
			store, ref, v)],
		["normalizeAcpUpdate/envelope", (v) => events.normalizeAcpUpdate(v)],
		["normalizeAcpUpdate/sourceKind",
		 (v) => events.normalizeAcpUpdate({ sessionUpdate: v })],
		["normalizeAcpUpdate/status", (v) => events.normalizeAcpUpdate(
			{ sessionUpdate: "tool_call", toolCallId: "c", status: v })],
		["normalizeAcpUpdate/toolKind", (v) => events.normalizeAcpUpdate(
			{ sessionUpdate: "tool_call", toolCallId: "c",
			  status: "completed", kind: v })],
		["sealEvent/kind", (v) => events.sealEvent(
			{ kind: v, sourceKind: "x" })],
		["eventRecordOf/ref", (v) => events.eventRecordOf(store, v, 1)],
		["eventRecordOf/seq", (v) => events.eventRecordOf(store, ref, v)],
		["turnToken", (v) => turn.turnToken(v, 1)],
		["selectTurnOutcome", (v) => turn.selectTurnOutcome(v)],
		["fromTerminalFact", (v) => turn.fromTerminalFact(v)],
		["allocateTurn", (v) => turn.allocateTurn(store, v)],
		["recordTurn", (v) => turn.recordTurn(store,
			{ sessionRef: v, turnToken: v })],
		["turnRecordOf", (v) => turn.turnRecordOf(store, v)],
		["permitsDisposition", (v) => turn.permitsDisposition(store, v, v)],
		["postureSlot", (v) => slots.postureSlot(store, v, v)],
		["occupySlot", (v) => slots.occupySlot(store,
			{ attemptId: v, posture: v, sessionEpoch: v })],
		["requireSlotRecovery", (v) => slots.requireSlotRecovery(store,
			{ attemptId: v, posture: v, sessionEpoch: v, reason: v })],
		["releaseSlot", (v) => slots.releaseSlot(store,
			{ attemptId: v, posture: v, sessionEpoch: v, evidence: v })],
		["validateClientCapabilities",
		 (v) => shake.validateClientCapabilities(v)],
		["checkOutboundMethod", (v) => shake.checkOutboundMethod(v)],
		["serveClientMethod", (v) => shake.serveClientMethod(v)],
		["routeAgentOriginCall", (v) => shake.routeAgentOriginCall(v)],
		["activateAssignment", (v) => attempts.activateAssignment(store,
			{ participant: "p", assignmentOf: () => null },
			{ attemptId: v, expect: v })],
	];
}

test("W2929 composition: every boundary refuses inside the closed taxonomy",
	() => {
		const store = open();
		try {
			const operands = hostileOperands();
			let checked = 0;
			for (const [where, call] of boundaries(store)) {
				for (const [what, make] of operands) {
					checked += 1;
					try {
						call(make());
					} catch (failure) {
						assert.equal(failure instanceof ContractError, true,
							`${where} answered ${what} with `
							+ `${failure?.constructor?.name}: `
							+ `${String(failure?.message).slice(0, 80)}`);
						assert.equal(typeof failure.category, "string", where);
						assert.equal(typeof failure.code, "string", where);
					}
				}
			}
			// The sweep is only worth what it covers, so the count is stated:
			// a boundary quietly dropped from the list would otherwise make
			// this case pass MORE easily.
			assert.equal(checked, 27 * 6);
		} finally {
			store.close();
		}
	});

test("W2929 review: every hostile taxonomy cell actually refuses", () => {
	// The composition case verifies the taxonomy IF a boundary throws. This
	// closes the other half: every enumerated hostile operand must reach a
	// refusal rather than being silently accepted and therefore never entering
	// that catch block at all.
	const store = open();
	try {
		let checked = 0;
		for (const [where, call] of boundaries(store)) {
			for (const [what, make] of hostileOperands()) {
				checked += 1;
				assert.throws(() => call(make()),
					(error) => error instanceof ContractError
						&& typeof error.category === "string"
						&& typeof error.code === "string",
					`${where}: ${what}`);
			}
		}
		assert.equal(checked, 27 * 6);
	} finally {
		store.close();
	}
});

test("W2929 review: every caller-controlled primitive name is bounded", () => {
	// A Symbol description and a BigInt have caller-controlled, unbounded
	// string forms too. Being safe to convert does not make the resulting
	// diagnostic safe to retain.
	for (const [what, value] of [
		["a string", "x".repeat(1000)],
		["a symbol", Symbol("x".repeat(1000))],
		["a bigint", BigInt("9".repeat(1000))],
	]) {
		assert.ok(nameValue(value).length < 200, what);
	}
});

test("W2929 composition: absence and refusal are different answers", () => {
	// Proving an identifier before it reaches the store must not turn "no such
	// thing" into a refusal. A well-formed id naming nothing is an ABSENCE;
	// an id that is not an id was never a question.
	const store = open();
	try {
		assert.equal(turn.turnRecordOf(store, "turn:nothing-here"), null);
		assert.equal(events.eventRecordOf(store,
			{ runtimeAttemptId: "attempt-1", posture: "execution",
			  sessionEpoch: 1, providerSessionId: null }, 1), null);
		for (const [where, call] of [
				["turnRecordOf", (v) => turn.turnRecordOf(store, v)],
				["eventRecordOf", (v) => events.eventRecordOf(store, v, 1)]]) {
			for (const bad of [null, undefined, "", 7, {}, []]) {
				assert.throws(() => call(bad),
					(error) => error instanceof ContractError
						&& error.category === "integrity"
						&& error.code === "schema",
					`${where}: ${String(bad)}`);
			}
		}
	} finally {
		store.close();
	}
});

test("W2929 review: only a frozen opaque id can be absent", () => {
	// `turnRecordOf` and the private attempt lookup now distinguish malformed
	// input from absence, but nonempty is only one third of the frozen opaqueId
	// rule. A malformed string still was not a question merely because SQLite
	// can bind it.
	const store = open();
	try {
		for (const bad of ["contains a space", "x".repeat(161)]) {
			assert.throws(() => turn.turnRecordOf(store, bad),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", `turn: ${bad.length}`);
			assert.throws(() => attempts.activateAssignment(store,
				{ participant: "p", assignmentOf: () => null },
				{ attemptId: bad, expect: null }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", `attempt: ${bad.length}`);
		}
	} finally {
		store.close();
	}
});

test("W2929 correction: one verdict per opaque id, at every boundary", () => {
	// The review found "nonempty is one third of the rule" at two boundaries.
	// The rule underneath is that ONE STRING GETS ONE VERDICT: five boundaries
	// type an identifier as the frozen `opaqueId`, and the way they came to
	// disagree before was that each asked its own version of the question.
	//
	// So this does not check that each boundary refuses a space. It checks
	// that they all AGREE, which is the property that survives someone
	// editing one of them.
	const store = open();
	try {
		const ref = (attemptId) => ({ runtimeAttemptId: attemptId,
			posture: "execution", sessionEpoch: 1, providerSessionId: null });
		const sites = [
			["turnRecordOf", (id) => turn.turnRecordOf(store, id)],
			["activateAssignment", (id) => attempts.activateAssignment(store,
				{ participant: "p", assignmentOf: () => null },
				{ attemptId: id, expect: null })],
			["normalizeAgentSessionRef",
			 (id) => axis.normalizeAgentSessionRef(ref(id))],
			["eventRecordOf", (id) => events.eventRecordOf(store, ref(id), 1)],
			["postureSlot", (id) => slots.postureSlot(store, id, "execution")],
		];
		for (const [what, id, wellFormed] of [
				["an ordinary id", "attempt-1", true],
				["a turn token", `turn:${"a1b2c3d4".repeat(8)}`, true],
				["a UUID", "550e8400-e29b-41d4-a716-446655440000", true],
				["one dotted and colonned", "baton.v12:attempt.1", true],
				["exactly 160 characters", "a".repeat(160), true],
				["161 characters", "a".repeat(161), false],
				["one containing a space", "has a space", false],
				["one starting with a dash", "-leading", false],
				["one with a slash", "a/b", false],
				["an empty one", "", false]]) {
			for (const [where, call] of sites) {
				const label = `${where}: ${what}`;
				let schemaRefusal = false;
				try {
					call(id);
				} catch (failure) {
					assert.equal(failure instanceof ContractError, true, label);
					schemaRefusal = failure.category === "integrity"
						&& failure.code === "schema";
				}
				// A well-formed id may still be refused for its OWN reasons
				// past the identity — no such attempt, no live assignment —
				// and that is not a schema refusal. Only the identity verdict
				// is compared.
				assert.equal(schemaRefusal, !wellFormed, label);
			}
		}
	} finally {
		store.close();
	}
});

test("W2929 correction: one ruler, and it is the frozen contract's", () => {
	// The finding was not "512 was compared wrongly". It was that a
	// hand-written proof of a frozen bound MEASURED IN A DIFFERENT UNIT than
	// the contract it exists to be faithful to — `.length` counts UTF-16 code
	// units, `maxLength` counts characters — so the two agree until a string
	// leaves the BMP and then silently do not.
	//
	// So this case is about the RULER, at every place one is used.
	const astral = "😀";
	assert.equal(astral.length, 2, "the two units differ on this character");

	// 1. The frozen opaqueId limit. Its grammar admits only ASCII, so no
	//    astral string is ACCEPTED either way — but the count must still be
	//    the contract's, and a 161-character ASCII id must refuse for LENGTH
	//    while an 80-character astral one refuses for GRAMMAR.
	assert.equal(opaqueIdFault("a".repeat(160)), null);
	assert.match(opaqueIdFault("a".repeat(161)), /longer than the frozen/);
	assert.match(opaqueIdFault(astral.repeat(80)), /grammar/);

	// 2. The shared ruler itself, at the exact boundary.
	for (const [what, limit, value, within] of [
			["ASCII at the limit", 512, "p".repeat(512), true],
			["ASCII one over", 512, "p".repeat(513), false],
			["astral at the limit", 512, astral.repeat(512), true],
			["astral one over", 512, astral.repeat(513), false],
			["two lone high surrogates", 2, "\uD83D\uD83D", true],
			// AND THE UNIT IS CODE POINTS, NOT GRAPHEMES. `e` + a combining
			// acute renders as one glyph and is TWO characters to JSON
			// Schema, so this is three and does not fit in two. Asserted
			// because my first draft of this row assumed graphemes — the
			// contract's unit is the one that decides, not the one that
			// looks right.
			["a combining sequence", 2, "e\u0301x", false],
			["that same sequence in three", 3, "e\u0301x", true]]) {
		assert.equal(withinFrozenLength(value, limit), within,
			`${what}: ${value.length} code units`);
	}
	assert.equal(withinFrozenLength(7, 512), false, "a non-string is not one");

	// 3. And the diagnostic ruler, which decides no verdict and can still
	//    produce a MALFORMED string: slicing by code unit cuts a surrogate
	//    pair in half. The bounded name must be well-formed text.
	const named = nameValue(astral.repeat(1000));
	assert.equal(named.includes("\uFFFD"), false, "the name was mangled");
	assert.equal([...named].some((character) => {
		const code = character.codePointAt(0);
		return code >= 0xD800 && code <= 0xDFFF;
	}), false, "the name carries a lone surrogate");
	assert.ok([...named].length <= 80, `${[...named].length} characters`);
});

test("W2929 review: a bounded diagnostic does not walk its discarded tail",
	() => {
		// The corrected output keeps 60 characters. Materializing `[...text]`
		// first still walks and allocates the entire caller-sized tail. Wrap the
		// standard iterator only to count work: the answer must need at most one
		// short bound probe and one short prefix pass, not all 1,000 characters.
		const original = String.prototype[Symbol.iterator];
		let yielded = 0;
		let named;
		try {
			String.prototype[Symbol.iterator] = function countedIterator() {
				const source = original.call(this);
				return {
					next() {
						const step = source.next();
						if (!step.done) yielded += 1;
						return step;
					},
					[Symbol.iterator]() { return this; },
				};
			};
			named = nameValue("😀".repeat(1000));
		} finally {
			String.prototype[Symbol.iterator] = original;
		}
		assert.ok([...named].length <= 80);
		assert.ok(yielded <= 130, `${yielded} characters traversed`);
});

test("W2929 correction: a refusal is bounded by the RULE, not by the operand",
	() => {
		// The review found this in one helper: a bounded OUTPUT is not a
		// bounded operation, and a refusal path should not do work — or write
		// a message — proportional to the value it is rejecting. That is a
		// property of every refusal, so it is asserted as one.
		const wide = {};
		for (let index = 0; index < 20000; index += 1) {
			wide[`member-${index}`] = 1;
		}
		const long = "m/".repeat(20000);
		const store = open();
		try {
			for (const [what, call] of [
					["a capability envelope with 20,000 members",
					 () => shake.validateClientCapabilities(wide)],
					["a capability fs record with 20,000 members",
					 () => shake.validateClientCapabilities(
						{ fs: wide, terminal: false })],
					["a reference with 20,000 members",
					 () => axis.normalizeAgentSessionRef(wide)],
					["an update with 20,000 members",
					 () => events.normalizeAcpUpdate({ ...wide,
						sessionUpdate: "tool_call", toolCallId: "c",
						status: "nope" })],
					["a 40,000-character method",
					 () => shake.serveClientMethod(long)],
					["a 40,000-character turn token",
					 () => turn.turnRecordOf(store, long)],
					["a 40,000-character attempt id",
					 () => slots.postureSlot(store, long, "execution")]]) {
				assert.throws(call, (error) => {
					assert.equal(error instanceof ContractError, true, what);
					assert.ok(error.message.length < 500,
						`${what}: ${error.message.length} characters`);
					return true;
				}, what);
			}
		} finally {
			store.close();
		}
		// AND THE ORDINARY CASE COSTS NOTHING. The cheap code-unit test in
		// front of the counting pass is exact for short values — a code point
		// is never more than one code unit — so a name that already fits is
		// never iterated at all. Measured the same way the review measured
		// the long case, because an optimisation nothing observes is an
		// optimisation nothing protects.
		const original = String.prototype[Symbol.iterator];
		let yielded = 0;
		try {
			String.prototype[Symbol.iterator] = function counted() {
				const source = original.call(this);
				return { next() {
					const step = source.next();
					if (!step.done) yielded += 1;
					return step;
				}, [Symbol.iterator]() { return this; } };
			};
			nameValue("session/prompt");
		} finally {
			String.prototype[Symbol.iterator] = original;
		}
		assert.equal(yielded, 0, `a short name was iterated ${yielded} times`);
		// W1593 owns the shared `recordFault` follow-up. Its two capability rows
		// live beside W4's five consumers so one property guards both the local
		// boundary and the shared primitive.
	});

test("W2929 correction: the bound belongs to the renderer, not to strings",
	() => {
		// The review found the bound applied to the branch I had thought about.
		// Every branch renders something a caller controls except the shape
		// branch, which renders manager text — so the property is about the
		// FUNCTION, not about one of its cases.
		const long = 1000;
		for (const [what, value] of [
				["a string", "x".repeat(long)],
				["a symbol description", Symbol("x".repeat(long))],
				["a bigint", BigInt("9".repeat(long))],
				["a negative bigint", -BigInt("9".repeat(long))],
				["a number", Number.MAX_VALUE],
				["a record with a huge member name",
				 { [`k${"y".repeat(long)}`]: 1 }],
				["a huge array", new Array(long).fill(0)]]) {
			const named = nameValue(value);
			assert.equal(typeof named, "string", what);
			assert.ok(named.length <= 80, `${what}: ${named.length}`);
		}
		// And the bound does not eat SHORT values, which is the other half:
		// a diagnostic nobody can read is not safer, it is just useless.
		assert.equal(nameValue("session/prompt"), "\"session/prompt\"");
		assert.equal(nameValue(7n), "7");
		assert.equal(nameValue(Symbol("mode")), "Symbol(mode)");
	});

test("W2929 composition: one §3.1 reference, not two that disagree", () => {
	// MEASURED, not suspected. `turnSessionRef` and `normalizeAgentSessionRef`
	// are two copies of §3.1, and they had DIVERGED rather than merely
	// duplicated: the turn copy accepted an empty `providerSessionId` that the
	// axis refused, so the same reference was valid at one boundary and
	// invalid at the other. The frozen schema decides it without a ruling —
	// `$defs.providerSessionId` is `minLength: 1`.
	//
	// This case drives BOTH copies through one table, because the defect was
	// not either check on its own; it was that nothing compared them.
	const base = { runtimeAttemptId: "attempt-1", posture: "execution",
	               sessionEpoch: 1, providerSessionId: "provider-1" };
	const store = open();
	try {
		for (const [what, ref, accepted] of [
				["a full reference", base, true],
				["no provider id", { ...base, providerSessionId: null }, true],
				["an EMPTY provider id",
				 { ...base, providerSessionId: "" }, false],
				["a numeric provider id",
				 { ...base, providerSessionId: 7 }, false],
				// The frozen `$defs.providerSessionId` is
				// `{minLength: 1, maxLength: 512}`, and the upper bound was
				// as unenforced as the opaque-id one until this correction.
				["a provider id of exactly 512",
				 { ...base, providerSessionId: "p".repeat(512) }, true],
				["a provider id of 513",
				 { ...base, providerSessionId: "p".repeat(513) }, false],
				// JSON Schema maxLength counts Unicode code points, not UTF-16
				// code units. Keep the hand-written member proof faithful to the
				// frozen schema at the boundary where those measures differ.
				["a provider id of exactly 512 Unicode characters",
				 { ...base, providerSessionId: "😀".repeat(512) }, true],
				["a provider id of 513 Unicode characters",
				 { ...base, providerSessionId: "😀".repeat(513) }, false],
				["an empty attempt", { ...base, runtimeAttemptId: "" }, false],
				["a foreign posture", { ...base, posture: "review" }, false],
				["a zero epoch", { ...base, sessionEpoch: 0 }, false],
				["a fractional epoch", { ...base, sessionEpoch: 1.5 }, false]]) {
			for (const [where, call] of [
					["axis", () => axis.normalizeAgentSessionRef(ref)],
					["turn", () => turn.allocateTurn(store, ref)]]) {
				const label = `${where}: ${what}`;
				if (accepted) {
					// The turn boundary refuses for its OWN reasons past the
					// reference — no such session — and that is not a
					// reference refusal. Only the schema pair is compared.
					try {
						call();
					} catch (failure) {
						assert.equal(failure instanceof ContractError, true,
							label);
						assert.notEqual(
							`${failure.category}/${failure.code}`,
							"integrity/schema", label);
					}
				} else {
					assert.throws(call,
						(error) => error instanceof ContractError
							&& error.category === "integrity"
							&& error.code === "schema", label);
				}
			}
		}
	} finally {
		store.close();
	}
});

test("W2929 composition: a refusal names a value without running it", () => {
	// The diagnostic is still worth reading. A method name is a string and a
	// string interpolates without running anything, so it is SHOWN — "the
	// agent called session/prompt" is the whole diagnostic, and losing it to
	// "a string value" would be paying for safety twice.
	assert.throws(() => shake.serveClientMethod("fs/read_text_file"),
		(error) => error instanceof ContractError
			&& error.message.includes("fs/read_text_file"));
	// And a value with behaviour is named by SHAPE, with none of it run.
	let ran = false;
	const hostile = { toJSON() { ran = true; throw new Error("ran"); } };
	assert.throws(() => shake.serveClientMethod(hostile),
		(error) => error instanceof ContractError
			&& error.message.includes("a plain object"));
	assert.equal(ran, false);
	// A long caller string is bounded rather than copied whole into a message
	// that may end up in a durable record.
	const long = "m/".repeat(500);
	assert.throws(() => shake.serveClientMethod(long),
		(error) => error instanceof ContractError
			&& error.message.length < 400);
});
