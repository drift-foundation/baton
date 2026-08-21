// Draft `0-spike` JSON envelopes for the W76 proof. These are DISPOSABLE
// prototype contracts, deliberately minimal, and carry no compatibility
// promise: their only job is to make the v12 lifecycle observable end to
// end so W2 can decide what the real IN/OUT contracts must say.
//
// Every envelope names its own kind and version in-band. A consumer that
// cannot name what it just parsed is exactly the failure mode the typed
// contract exists to remove, so validation is structural and fails closed.

export const SPIKE_VERSION = "0-spike";

class EnvelopeError extends Error {}

const SHAPES = {
	// Operator-submitted typed input for one Job.
	"job.in": {
		work: "string", contract: "object", inputs: "array",
	},
	// Read-only pre-claim offer handed to the agent BEFORE any claim.
	// Carries the human contract, input metadata and the claim token —
	// and deliberately no Baton locator the agent could act on.
	offer: {
		work: "string", participant: "string", runtime_attempt: "string",
		contract_human: "string", inputs: "array", token: "object",
		declared_outputs: "array", reply_format: "object",
	},
	// The agent's structured, token-bearing answer to an offer.
	"claim-intent": {
		decision: "string", token: "string", work: "string",
		runtime_attempt: "string", reason: "string",
	},
	// Minted ONLY by a successful canonical claim. Nothing writable
	// starts without one.
	assignment: {
		work: "string", participant: "string", runtime_attempt: "string",
		generation: "number", claim_seq: "number", claimed_at: "string",
	},
	// One agent activity update, captured from the ACP session.
	activity: { ts: "string", channel: "string", text: "string" },
	// The agent's declaration that the named result is complete.
	"job.out": { work: "string", results: "array", summary: "string" },
	// The manager's frozen, validated, digest-bound result.
	result: {
		work: "string", assignment: "object", outputs: "array",
		status: "string",
	},
	// The terminal handoff back through the public Baton boundary.
	return: { work: "string", to: "string", comment: "string", references: "array" },
};

function typeOf(value) {
	if (Array.isArray(value)) return "array";
	if (value === null) return "null";
	return typeof value;
}

export function envelope(kind, body) {
	if (!SHAPES[kind]) throw new EnvelopeError(`unknown envelope kind '${kind}'`);
	return validate({ envelope: kind, version: SPIKE_VERSION, ...body });
}

// Fails closed on an unknown kind, a version this build does not speak,
// and any missing or mistyped required field. Extra fields are allowed:
// a spike contract must be able to carry evidence it has not yet typed.
export function validate(value, expectedKind = null) {
	if (typeOf(value) !== "object") {
		throw new EnvelopeError(`envelope must be a JSON object, got ${typeOf(value)}`);
	}
	const kind = value.envelope;
	const shape = SHAPES[kind];
	if (!shape) throw new EnvelopeError(`unknown envelope kind ${JSON.stringify(kind)}`);
	if (expectedKind && kind !== expectedKind) {
		throw new EnvelopeError(`expected a '${expectedKind}' envelope, got '${kind}'`);
	}
	if (value.version !== SPIKE_VERSION) {
		throw new EnvelopeError(
			`${kind} envelope declares version ${JSON.stringify(value.version)}; `
			+ `this build speaks only '${SPIKE_VERSION}' and refuses rather than guessing`);
	}
	for (const [field, wanted] of Object.entries(shape)) {
		const got = typeOf(value[field]);
		if (got !== wanted) {
			throw new EnvelopeError(
				`${kind}.${field} must be ${wanted}, got ${got}`);
		}
	}
	return value;
}

export { EnvelopeError };
