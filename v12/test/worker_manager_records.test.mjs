// The shared record proof — `src/worker_manager/records.mjs`.
//
// The reconnect envelope and the ACP capability envelope each assert this
// rule through their OWN error taxonomy. What neither of them can state is the
// primitive's own contract, which is what this file is for: these four
// functions ANSWER, and answering never throws and never runs the value.
//
// That is the property that makes them safe to share. A shared helper that can
// throw is a shared helper that turns one caller's refusal into another
// caller's crash, and this whole module exists because the same rule
// implemented twice earned the same finding twice.

import test from "node:test";
import assert from "node:assert/strict";

import { classify, describe, isPlainRecord, recordFault }
	from "../src/worker_manager/records.mjs";

/** Every trap a Proxy has, so a case cannot pass by naming the two someone
 *  happened to think of. */
const TRAPS = ["apply", "construct", "defineProperty", "deleteProperty", "get",
	"getOwnPropertyDescriptor", "getPrototypeOf", "has", "isExtensible",
	"ownKeys", "preventExtensions", "set", "setPrototypeOf"];

/** Values that RUN something if anything touches them. */
function hostileValues(record) {
	const watched = (target) => new Proxy(target, Object.fromEntries(
		TRAPS.map((trap) => [trap, (...args) => {
			record(`trap:${trap}`);
			return Reflect[trap](...args);
		}])));
	const revoked = () => {
		const pair = Proxy.revocable({}, {});
		pair.revoke();
		return pair.proxy;
	};
	const accessors = () => {
		const value = {};
		for (const member of ["toJSON", "toString", "valueOf", "constructor",
		                      "fs", "terminal", "turnInFlight"]) {
			Object.defineProperty(value, member, {
				get() { record(`get:${member}`); throw new Error(member); },
				enumerable: true, configurable: true });
		}
		return value;
	};
	const throwingPrototype = () => {
		const prototype = {};
		Object.defineProperty(prototype, "constructor", {
			get() { record("get:constructor"); throw new Error("constructor"); },
		});
		return Object.create(prototype);
	};
	return [
		["a Proxy over an empty record", () => watched({})],
		["a Proxy that would answer correctly", () => watched({ fs: {} })],
		["a Proxy over an array", () => watched([])],
		["a Proxy over a null-prototype record",
		 () => watched(Object.create(null))],
		["a revoked Proxy", revoked],
		["a record of throwing accessors", accessors],
		["an object over a throwing prototype", throwingPrototype],
		["a BigInt", () => 1n],
		["a symbol", () => Symbol("x")],
		["a function", () => function named() {}],
	];
}

test("records: answering never throws and never runs the value", () => {
	let ran = [];
	for (const [what, make] of hostileValues((event) => ran.push(event))) {
		for (const [name, call] of [
				["classify", (value) => classify(value)],
				["describe", (value) => describe(value)],
				["isPlainRecord", (value) => isPlainRecord(value)],
				["recordFault/none", (value) => recordFault(value, [])],
				["recordFault/two",
				 (value) => recordFault(value, ["fs", "terminal"])]]) {
			ran = [];
			const value = make();
			assert.doesNotThrow(() => call(value), `${name}: ${what}`);
			assert.deepEqual(ran, [], `${name}: ${what} ran ${ran.join(", ")}`);
		}
	}
});

test("records: a Proxy is refused however plausibly it answers", () => {
	// The sharp end of the rule: this one's answers are all CORRECT. It is
	// refused because of what it IS, not because its answers were wrong.
	const plausible = new Proxy({ fs: {}, terminal: false }, {});
	assert.equal(classify(plausible).proxy, true);
	assert.equal(isPlainRecord(plausible), false);
	assert.equal(describe(plausible), "a Proxy");
	assert.notEqual(recordFault(plausible, ["fs", "terminal"]), null);
	// And it is decided BEFORE reflection, not by reflection failing: a
	// revoked Proxy and a live one reach the same verdict by the same route.
	const pair = Proxy.revocable({}, {});
	pair.revoke();
	assert.equal(classify(pair.proxy).proxy, true);
	assert.equal(classify(pair.proxy).read, false);
});

test("records: the documents the contracts DO send are accepted", () => {
	// A proof that refuses everything satisfies every refusal above and no
	// contract at all.
	for (const [what, value] of [
			["an object literal", {}],
			["a null-prototype record", Object.create(null)],
			["a record with members", { fs: {}, terminal: false }]]) {
		assert.equal(isPlainRecord(value), true, what);
	}
	assert.equal(recordFault({}, []), null);
	assert.equal(recordFault({ fs: {}, terminal: false },
		["terminal", "fs"]), null, "member order is not part of the rule");
	const reversed = Object.create(null);
	reversed.terminal = false;
	reversed.fs = {};
	assert.equal(recordFault(reversed, ["fs", "terminal"]), null);
});

test("records: an array is not a document, wearing any prototype", () => {
	// The prototype rule alone does NOT cover this, and no Proxy is involved:
	// `Object.setPrototypeOf` gives an ordinary array `Object.prototype` or no
	// prototype at all, and it still serializes as `[]`. Array classification
	// is a separate fact and is tested as one.
	for (const [what, value] of [
			["a bare array", []],
			["an array wearing Object.prototype",
			 Object.setPrototypeOf([], Object.prototype)],
			["an array wearing no prototype",
			 Object.setPrototypeOf([], null)]]) {
		assert.equal(isPlainRecord(value), false, what);
		assert.notEqual(recordFault(value, []), null, what);
		assert.equal(describe(value), "an array", what);
	}
});

test("records: the member proof counts what Object.keys hides", () => {
	// A non-enumerable `toJSON` is invisible to `Object.keys` and decides the
	// ENTIRE serialization of the document it hides in. Looking empty is not
	// being the empty document.
	const hiding = {};
	Object.defineProperty(hiding, "toJSON",
		{ value: () => "not a document", enumerable: false });
	assert.notEqual(recordFault(hiding, []), null);
	const symbol = { [Symbol("member")]: 1 };
	assert.notEqual(recordFault(symbol, []), null);
	// And a member that is a PROGRAM is refused without being read.
	let ran = false;
	const accessor = {};
	Object.defineProperty(accessor, "fs",
		{ get() { ran = true; return {}; }, enumerable: true });
	assert.notEqual(recordFault(accessor, ["fs"]), null);
	assert.equal(ran, false);
});

test("records review: an expected JSON member must be enumerable", () => {
	const hidden = {};
	Object.defineProperty(hidden, "fs",
		{ value: {}, enumerable: false });
	assert.equal(JSON.stringify(hidden), "{}",
		"the hidden member is not part of the JSON document");
	assert.notEqual(recordFault(hidden, ["fs"]), null);
});

test("records correction: acceptance MEANS the JSON document", () => {
	// The finding was that rule 6 has two directions and I implemented one.
	// So this case does not assert the new branch; it asserts the PROPERTY
	// the branch exists for, against the ground truth the proof stands in
	// for — what `JSON.stringify` actually produces.
	//
	//   recordFault(v, expected) === null  =>  the JSON document of v has
	//                                          EXACTLY those members
	//
	// The converse is deliberately NOT claimed. A hidden EXTRA member does
	// not change the wire form either, and the proof refuses it anyway,
	// because a document carrying invisible state is not the document — that
	// is what stops a non-enumerable `toJSON` from deciding the whole
	// serialization. The rule is stricter than the wire, on purpose, and the
	// refusals below say so.
	const hide = (value, members) => {
		for (const [name, member] of Object.entries(members)) {
			Object.defineProperty(value, name,
				{ value: member, enumerable: false, configurable: true });
		}
		return value;
	};
	const nullProto = (members) => Object.assign(Object.create(null), members);
	for (const [what, value, expected] of [
			["the empty document", {}, []],
			["the ACP capability document", { fs: {}, terminal: false },
			 ["fs", "terminal"]],
			["it, written in the other order",
			 { terminal: false, fs: {} }, ["fs", "terminal"]],
			["it, with no prototype",
			 nullProto({ fs: {}, terminal: false }), ["fs", "terminal"]],
			["a document with a false member", { turnInFlight: false },
			 ["turnInFlight"]]]) {
		assert.equal(recordFault(value, expected), null, what);
		// ACCEPTED, so the wire form must be exactly the expected members.
		assert.deepEqual(Object.keys(JSON.parse(JSON.stringify(value))).sort(),
			[...expected].sort(), `${what}: accepted but not the document`);
	}
	for (const [what, value, expected] of [
			["every expected member hidden",
			 hide({}, { fs: {}, terminal: false }), ["fs", "terminal"]],
			["one expected member hidden",
			 hide({ fs: {} }, { terminal: false }), ["fs", "terminal"]],
			["a hidden EXTRA member, which the wire would not show either",
			 hide({ fs: {}, terminal: false }, { note: 1 }),
			 ["fs", "terminal"]],
			["a hidden toJSON, which decides the whole serialization",
			 hide({}, { toJSON: () => ({ fs: {}, terminal: false }) }),
			 ["fs", "terminal"]]]) {
		assert.notEqual(recordFault(value, expected), null, what);
	}
	// The two hidden-member spellings are readable and are not the document,
	// which is the whole distinction.
	const hidden = hide({}, { fs: {}, terminal: false });
	assert.equal(hidden.fs !== undefined && hidden.terminal === false, true);
	assert.equal(JSON.stringify(hidden), "{}");
});

test("records: a rejected value is named by shape and never by content", () => {
	const marker = "zz-caller-content-zz";
	for (const [value, says] of [
			[null, "null"],
			[undefined, "undefined"],
			[true, "true"],
			[false, "false"],
			[marker, "a string value"],
			[1n, "a bigint value"],
			[[], "an array"],
			[{}, "a plain object"],
			[Object.create(null), "a null-prototype object"],
			[new Date(0), "an object with a prototype of its own"],
			[new Proxy({}, {}), "a Proxy"]]) {
		assert.equal(describe(value), says);
	}
	// Nothing a caller chose appears in any answer.
	assert.equal(describe(marker).includes(marker), false);
	assert.equal(recordFault({ [marker]: 1 }, []).includes(marker), true,
		"member NAMES are structure and are reported deliberately");
	assert.equal(recordFault({ fs: marker }, ["fs"]), null,
		"a member VALUE is never inspected once the shape holds");
});

test("W1593 review: a wide record has bounded fault output", () => {
	const wide = {};
	for (let index = 0; index < 20000; index += 1) {
		wide[`member-${index}`] = 1;
	}
	const fault = recordFault(wide, []);
	assert.notEqual(fault, null);
	assert.ok(fault.length < 500, `${fault.length} diagnostic characters`);
});

test("W1593 review: shape prose does not enumerate unreported members", () => {
	const wide = {};
	for (let index = 0; index < 20000; index += 1) {
		wide[`member-${index}`] = 1;
	}
	// Shape prose reports no members, so enumerating all of them is work
	// without evidence. Exact record validation still must enumerate once;
	// this assertion is only about the coarse shape path.
	const ownNames = Object.getOwnPropertyNames;
	const ownSymbols = Object.getOwnPropertySymbols;
	let enumerations = 0;
	try {
		Object.getOwnPropertyNames = (value) => {
			if (value === wide) enumerations += 1;
			return ownNames(value);
		};
		Object.getOwnPropertySymbols = (value) => {
			if (value === wide) enumerations += 1;
			return ownSymbols(value);
		};
		assert.equal(describe(wide), "a plain object");
	} finally {
		Object.getOwnPropertyNames = ownNames;
		Object.getOwnPropertySymbols = ownSymbols;
	}
	assert.equal(enumerations, 0,
		`shape description performed ${enumerations} member enumerations`);
});
