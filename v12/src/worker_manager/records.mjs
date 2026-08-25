// ONE place that answers "is this an INERT JSON DOCUMENT".
//
// This module exists because the answer was written twice. The reconnect
// options envelope and the ACP client-capability envelope are the same
// question — "did the caller hand me data, or a program wearing an object" —
// and each grew its own proof, in `agent_reconnect.mjs` and
// `agent_handshake.mjs` respectively. Both were then found to have the SAME
// defect, independently, one review round apart: a Proxy whose traps answer
// plausibly was accepted as a document.
//
// Two implementations of one rule earned the same finding twice, which is the
// whole argument. W641's second review made the unification a requirement
// rather than a follow-up, and this is it: both boundaries call this, and a
// finding here is fixed once.
//
// WHAT SIX REVIEW ROUNDS ESTABLISHED, in the order they were learned:
//
//  1. A refusal must never SERIALIZE the value it is refusing. `JSON.stringify`
//     throws a raw `TypeError` on a BigInt, so the code that made a refusal
//     read better became a second way for a rejected value to escape the
//     closed error taxonomy at the exact moment the boundary had decided to
//     refuse it.
//
//  2. Nor may it READ the value. A rejected object's prototype may define
//     `constructor` as a throwing getter, and reading an own property runs an
//     own accessor. `hasOwnProperty` is inert and the line after it was not:
//     inert is a property of a specific OPERATION against a specific value,
//     never of a step.
//
//  3. Nor may a catch INTERVIEW what was thrown at it. JavaScript permits
//     throwing any value, so `failure.message` is a property read on an object
//     the caller chose.
//
//  4. "Runs no user code" is not "cannot fail". `Array.isArray` invokes
//     nothing and throws anyway, on a revoked Proxy, because array
//     classification follows a proxy to its target. Every classification is
//     therefore taken in ONE guarded place; `typeof` is the only operation
//     named as exempt, because it is the only one that genuinely cannot throw.
//
//  5. And TRANSLATING A TRAP THAT THROWS DOES NOTHING ABOUT A TRAP THAT
//     ANSWERS. Five rounds of guards all assumed a hostile value MISBEHAVES.
//     A Proxy over `{}` needs no exception at all: it answers the prototype,
//     answers the own keys, answers the descriptors, and is accepted — having
//     run caller code throughout. So the Proxy test is FIRST and NON-OBSERVING.
//     Another try/catch would be one more thing a successful trap walks past.
//
//  6. Looking empty is not BEING the empty document. `Object.keys(new Date(0))`
//     is empty and a Date serializes as a string. The question is never what
//     the object resembles; it is whether it IS the document the contract
//     sends, and the answer to that is its whole shape.
//
// The callers keep their own error taxonomies. This module returns FACTS and
// PROSE, never a `ContractError`: the reconnect envelope refuses as
// `integrity.schema` and the capability envelope as `policy.denied`, and a
// shared primitive that threw one of them would be deciding a policy that
// belongs to its caller.

import { isProxy } from "node:util/types";

/** One value classified ONCE, without running any of its behaviour.
 *
 *  A PROXY IS A PROGRAM WEARING AN OBJECT and is rejected before any
 *  reflection at all. `isProxy` reads an internal slot: it identifies live and
 *  revoked Proxies alike and runs no trap, which is the only kind of proof
 *  that works here (rule 5 above).
 *
 *  Everything after it is reflection, and all of it is translated together —
 *  `Array.isArray`, the prototype read and the own-key read can each throw on
 *  exotic values, and a boundary that has decided to refuse must not then fail
 *  while working out how to say so (rule 4). Failure is a FACT in the answer
 *  rather than an exception. */
export function classify(value) {
	if (isProxy(value)) {
		return { proxy: true, read: false, array: false, prototype: null,
		         names: [] };
	}
	try {
		return { proxy: false, read: true, array: Array.isArray(value),
		         prototype: Object.getPrototypeOf(value),
		         names: [...Object.getOwnPropertyNames(value),
		                 ...Object.getOwnPropertySymbols(value)] };
	} catch {
		return { proxy: false, read: false, array: false, prototype: null,
		         names: [] };
	}
}

/** A REJECTED value, named from inert facts only.
 *
 *  `typeof` runs nothing and cannot fail. `null`, `undefined`, `true` and
 *  `false` are single tokens with no caller content in them at all. Everything
 *  else is named by its SHAPE, from the snapshot.
 *
 *  The result is deliberately coarse. A diagnostic that has to be exactly
 *  right about an untrusted value is a diagnostic that has to touch it. */
export function describe(value, snapshot = null) {
	if (value === null) return "null";
	if (value === undefined) return "undefined";
	if (value === true) return "true";
	if (value === false) return "false";
	const type = typeof value;
	if (type !== "object") return `a ${type} value`;
	const seen = snapshot ?? classify(value);
	// Named for what it IS, not for the reflection that did not happen: this
	// value was never inspected, and saying so is the honest diagnostic.
	if (seen.proxy) return "a Proxy";
	if (!seen.read) return "an object that refused inspection";
	if (seen.array) return "an array";
	if (seen.prototype === null) return "a null-prototype object";
	if (seen.prototype === Object.prototype) return "a plain object";
	return "an object with a prototype of its own";
}

/** Whether this is a DOCUMENT rather than an object with behaviour.
 *
 *  An ordinary object literal or an `Object.create(null)` one. A Date, a Map,
 *  a regular expression and every class instance are objects and none of them
 *  is a document — they carry their own class, and a caller passing one has
 *  not passed a document.
 *
 *  The prototype is the test because it is the only one that GENERALIZES: a
 *  list of the exotic types a contract happens to know today would admit the
 *  next one on the day it appeared, which is a default-open rule wearing a
 *  closed one's clothes.
 *
 *  AN ARRAY IS NOT A DOCUMENT either, and the prototype test alone stops
 *  saying so once a Proxy is involved — a proxy over an array whose
 *  `getPrototypeOf` trap answers `Object.prototype` passes every other check.
 *  The array classification is in the snapshot, so the rule is tested rather
 *  than inferred. */
export function isPlainRecord(value, snapshot = null) {
	if (value === null || typeof value !== "object") return false;
	const seen = snapshot ?? classify(value);
	if (!seen.read) return false;
	if (seen.array) return false;
	return seen.prototype === Object.prototype || seen.prototype === null;
}

/** Why `value` is not the inert JSON record with exactly `expected` members,
 *  as a phrase that completes "<subject> ...", or `null` when it IS one.
 *
 *  Beyond `isPlainRecord`, this proves the MEMBERS:
 *
 *  - exactly the expected own keys, COUNTING THE ONES `Object.keys` HIDES. A
 *    non-enumerable `toJSON` is invisible there and decides the entire
 *    serialization of the document it hides in, so own names and own symbols
 *    are both counted (rule 6).
 *  - and every one of them a DATA member, because a getter is a program: it
 *    may answer one thing to this check and another to the wire, and reading
 *    it runs the caller's code at the boundary that decides the outcome
 *    (rule 2). */
export function recordFault(value, expected) {
	if (value === null || typeof value !== "object") {
		return `is ${describe(value)}`;
	}
	const seen = classify(value);
	if (seen.proxy) {
		return `is a Proxy; a document is data, and a trap that answers is a `
			+ `program authoring the answer`;
	}
	if (!seen.read) return "refused inspection";
	if (seen.array) return "is an array";
	if (!isPlainRecord(value, seen)) {
		return `is ${describe(value, seen)}, whose JSON form is whatever that `
			+ `class serializes to rather than its members`;
	}
	const names = seen.names
		.map((name) => typeof name === "symbol" ? "a symbol member" : name)
		.sort();
	const want = [...expected].sort();
	if (names.length !== want.length
			|| names.some((name, index) => name !== want[index])) {
		return `carries [${names.join(", ")}] and the contract sends `
			+ (want.length === 0 ? `an EMPTY object`
				: `exactly ${want.join(" and ")}`);
	}
	for (const name of want) {
		let descriptor;
		try {
			descriptor = Object.getOwnPropertyDescriptor(value, name);
		} catch {
			return "refused inspection";
		}
		if (!("value" in descriptor)) {
			return `carries ${name} as an accessor; a document carries data, `
				+ `and reading a getter would run the caller's code at the `
				+ `boundary that decides this`;
		}
		// Third review [P1]: AND A MEMBER THAT IS NOT IN THE DOCUMENT IS NOT
		// A MEMBER. Rule 6 counted hidden own keys so an EXTRA one could not
		// smuggle a `toJSON` past the proof — and then proved the EXPECTED
		// ones by property access alone, so an envelope whose `fs` and
		// `terminal` were both non-enumerable passed while
		// `JSON.stringify` of it was `{}`. Both values were readable and
		// neither was on the wire.
		//
		// Rule 6 has one direction in it and I implemented the other. The
		// question is never what the object will ANSWER when asked; it is
		// what it IS as a document, and a non-enumerable member is not part
		// of one. This stays an inert DESCRIPTOR check: the value is still
		// never read.
		if (descriptor.enumerable !== true) {
			return `hides ${name}; a non-enumerable member is readable and is `
				+ `not part of the JSON document, and this proof is about the `
				+ `document`;
		}
	}
	return null;
}
