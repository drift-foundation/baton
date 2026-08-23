// The durable identity shapes of `SPEC.md` §4, and the canonical form
// every operation signature is compared in.
//
// Two rules from the contract are enforced HERE rather than at each call
// site, because §4 says an identity is never a substitute for the
// operands and §7 says every durable operand rides the replay signature:
//
//   1. An `assignment_ref` is exactly (authority UUID, full Work ID,
//      participant, generation) — never a participant alone, never a
//      local selector. `assignmentKey` refuses anything else, so a
//      caller cannot accidentally compare three quarters of an identity.
//   2. A signature is a CANONICAL serialization of every effective
//      operand including the prose. Sorting keys is what makes
//      `{a, b}` and `{b, a}` one signature rather than two, and
//      including reasons and rationales is what makes reusing one
//      operation id with different durable text a refusal instead of a
//      silent replay of somebody else's result.

import { Refusal } from "./errors.mjs";

export const V11 = "v11";
export const V12 = "v12-assignment-1";

// `null` and `undefined` are DIFFERENT operands to a caller and the same
// thing to JSON, so the canonical form spells the absent one out. A
// transition that means "no gate" and one that forgot to pass a gate must
// not share a signature.
function canonical(value) {
	if (value === undefined) return { $undefined: true };
	if (value === null) return null;
	if (Array.isArray(value)) return value.map(canonical);
	if (value instanceof Date) return { $date: value.toISOString() };
	if (typeof value === "object") {
		const out = {};
		for (const key of Object.keys(value).sort()) out[key] = canonical(value[key]);
		return out;
	}
	return value;
}

// The stable string an operation's operands are compared as.
export function signatureOf(kind, operands) {
	return JSON.stringify(canonical({ kind, operands }));
}

export function isAssignmentRef(value) {
	return Boolean(value) && typeof value === "object"
		&& typeof value.authorityUuid === "string"
		&& typeof value.workId === "string"
		&& typeof value.participant === "string"
		&& (value.generation === null || Number.isInteger(value.generation));
}

// The comparable form of one assignment identity.
//
// A missing field is refused rather than defaulted. §8 exists because
// participant equality is insufficient — the same participant may release
// generation 7 and immediately claim generation 8 — so an identity that
// silently completed itself from current state would defeat the one check
// the contract is built on.
export function assignmentKey(assignment, { what = "assignment" } = {}) {
	if (assignment === null) return null;
	if (!isAssignmentRef(assignment)) {
		throw new Refusal(
			`${what} must be the full four-part identity (authority UUID, Work ID, `
			+ `participant, generation); a participant alone is not an assignment`);
	}
	return JSON.stringify([assignment.authorityUuid, assignment.workId,
	                       assignment.participant, assignment.generation]);
}

export function assignmentRef({ authorityUuid, workId, participant, generation }) {
	return Object.freeze({ authorityUuid, workId, participant, generation });
}

// Take ONE snapshot of a caller-owned operand and never look at the
// original again.
//
// Re-review 2026-08-22 [P1]: the session validated
// `operands.expect.participant` and then handed the SAME object to the
// core, which read it again. A getter that answered `poc.claude` for the
// first two reads and `poc.gemini` afterwards passed the binding check and
// then ended Gemini's live assignment. Validating one view and executing
// another is the whole defect, and no amount of checking fixes it while the
// object can still change its answer.
//
// So every value crossing a boundary is copied into plain frozen data
// first: own enumerable properties only, each read exactly once. Anything
// that is not plain data is not an operand this authority takes.
export function snapshot(value, depth = 0) {
	if (depth > 8) throw new Refusal("operand is nested too deeply to snapshot");
	if (value === null || typeof value !== "object") {
		if (typeof value === "function" || typeof value === "symbol") {
			throw new Refusal(`an operand may not be a ${typeof value}`);
		}
		return value;
	}
	if (Array.isArray(value)) {
		return Object.freeze(value.map((entry) => snapshot(entry, depth + 1)));
	}
	const out = {};
	// `Object.keys` walks own enumerable names once; each property is then
	// read exactly once, into `out`.
	for (const key of Object.keys(value)) out[key] = snapshot(value[key], depth + 1);
	return Object.freeze(out);
}

// The snapshot of one assignment identity, validated as the full four-part
// shape. `null`/`undefined` pass through, so a caller that legitimately has
// no assignment — an unclaimed close, an unclaimed gate arrival — is not
// forced to invent one.
export function normalizeAssignment(value, { what = "assignment" } = {}) {
	if (value === null || value === undefined) return value;
	const taken = snapshot(value);
	assignmentKey(taken, { what });
	return taken;
}

export function sameAssignment(left, right) {
	if (left === null || right === null) return left === right;
	return assignmentKey(left) === assignmentKey(right);
}

export function isV12Contract(contract) {
	return contract !== V11;
}

// Gate tokens are TYPED (§4). The type is what a satisfier checks, so it
// is parsed here once rather than by string-matching at three call sites.
export const GATE_QUIESCENCE = "runtime-quiescence";
export const GATE_CONTRACT_RUNTIME = "contract-runtime";
export const GATE_PLAN_REVISION = "plan-revision";

export function gateToken(kind, detail) {
	return `${kind}:${detail}`;
}

export function parseGate(gate) {
	if (typeof gate !== "string") return null;
	const at = gate.indexOf(":");
	if (at < 1) return null;
	return { kind: gate.slice(0, at), detail: gate.slice(at + 1) };
}
