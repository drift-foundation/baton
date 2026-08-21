// The claim fence. A pre-claim agent turn is READ-ONLY and holds no
// Baton capability, so its consent has to travel back as something the
// manager can verify: a short-lived, single-use bearer token bound to
// the exact Work, participant and runtime attempt it was minted for.
//
// The fence exists because a plausible-looking answer must not be able
// to start writable execution. A status claim such as "working", a
// confident narrative, or a well-formed ACP response WITHOUT the valid
// token grants nothing — validation is the only thing that mints an
// assignment, and every refusal is terminal for that offer.

import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";

class TokenError extends Error {
	constructor(message, reason) { super(message); this.reason = reason; }
}

const b64 = (buffer) => Buffer.from(buffer).toString("base64url");

export class ClaimTokenIssuer {
	// `secret` is per-manager-run and never leaves the manager. `ttlMs`
	// is deliberately short: the token covers one pre-claim turn, not a
	// session.
	constructor({ secret = randomBytes(32), ttlMs = 120000, now = () => Date.now() } = {}) {
		this.secret = secret;
		this.ttlMs = ttlMs;
		this.now = now;
		// Single-use is enforced by REMEMBERING every jti this issuer
		// ever minted and the state it is in. Forgetting a spent token
		// would make replay succeed after a garbage collection, so
		// entries are retained for the manager's lifetime.
		this.issued = new Map();
	}

	// The token the AGENT sees is a short opaque handle: an id and a tag
	// over that id, and nothing else. The bound payload never leaves the
	// manager.
	//
	// The first version of this carried the signed payload itself, which
	// made the agent-visible token 402 characters. Observed on
	// 2026-08-20: an otherwise correct pre-claim turn transcribed one of
	// those incorrectly and the attempt was refused as "forged". The
	// fence behaved perfectly — nothing was claimed and nothing ran —
	// but refusing honest consent because a model miscopied a long
	// opaque string is a contract defect, not a security result. A ~47
	// character handle carries exactly the same authority with far less
	// to get wrong. See PROGRESS.md.
	mint({ work, participant, runtimeAttempt, offerDigest, ttlMs }) {
		const issuedAt = this.now();
		const payload = {
			jti: randomBytes(9).toString("hex"),
			work, participant,
			runtime_attempt: runtimeAttempt,
			offer_digest: offerDigest,
			issued_at: new Date(issuedAt).toISOString(),
			expires_at: new Date(issuedAt + (ttlMs ?? this.ttlMs)).toISOString(),
		};
		this.issued.set(payload.jti, { state: "issued", payload });
		return { token: this.handle(payload.jti), payload };
	}

	handle(jti) {
		return `${jti}.${b64(createHmac("sha256", this.secret).update(jti).digest()
			.subarray(0, 15))}`;
	}

	// Every refusal names its reason so the negative proof can assert on
	// the exact failure rather than on "it threw". Nothing here mutates
	// Baton, and a refusal never marks a token spent — a token that was
	// never valid cannot be "used up".
	validate(token, expected) {
		if (typeof token !== "string" || !token.includes(".")) {
			throw new TokenError("the claim intent carried no token", "absent");
		}
		// Surrounding whitespace is normalised away. A model that copies
		// the handle correctly but pads it has consented; trimming cannot
		// turn an invalid tag into a valid one, so nothing is weakened.
		const [jti, tag] = token.trim().split(".");
		const record = this.issued.get(jti);
		if (!record) {
			throw new TokenError(
				`claim token ${JSON.stringify(jti).slice(0, 24)} was not minted by this `
				+ `manager run`, "unknown");
		}
		const wanted = Buffer.from(this.handle(jti).split(".")[1], "base64url");
		let got;
		try { got = Buffer.from(tag ?? "", "base64url"); } catch { got = Buffer.alloc(0); }
		if (got.length !== wanted.length || !timingSafeEqual(got, wanted)) {
			throw new TokenError("the claim token signature does not verify", "forged");
		}
		if (record.state === "spent") {
			throw new TokenError(
				`claim token ${jti} was already used for ${record.payload.work}; `
				+ `a replay grants nothing`, "replayed");
		}
		const payload = record.payload;
		// Expiry is checked BEFORE binding so a stale token for the right
		// Work still refuses, and it is checked against the manager's
		// clock and the manager's OWN record of what it minted — never
		// against anything the agent said.
		if (this.now() >= Date.parse(payload.expires_at)) {
			throw new TokenError(
				`claim token ${jti} expired at ${payload.expires_at}`, "expired");
		}
		for (const [field, want] of Object.entries(expected)) {
			if (payload[field] !== want) {
				throw new TokenError(
					`claim token ${jti} is bound to ${field}=${JSON.stringify(payload[field])}, `
					+ `not ${JSON.stringify(want)}`, "misbound");
			}
		}
		return payload;
	}

	// Spending is SEPARATE from validating and happens exactly once, at
	// the moment the manager commits to submitting the canonical claim.
	spend(jti) {
		const record = this.issued.get(jti);
		if (!record) throw new TokenError(`unknown claim token ${jti}`, "unknown");
		if (record.state === "spent") {
			throw new TokenError(`claim token ${jti} was already used`, "replayed");
		}
		record.state = "spent";
		return record.payload;
	}
}

// When a token fails to verify, "the signature does not verify" is true
// and useless: it cannot distinguish a forgery from a transcription
// error, and those want completely different fixes. This describes the
// mismatch STRUCTURALLY — lengths, segment identity, and where the two
// first diverge — without putting either token in the evidence.
export function describeTokenMismatch(received, expected) {
	if (typeof received !== "string" || typeof expected !== "string") {
		return { comparable: false };
	}
	const [gotBody = "", gotMac = ""] = received.split(".");
	const [wantBody = "", wantMac = ""] = expected.split(".");
	let firstDiff = -1;
	for (let index = 0; index < Math.max(received.length, expected.length); index += 1) {
		if (received[index] !== expected[index]) { firstDiff = index; break; }
	}
	return {
		comparable: true,
		received_length: received.length,
		expected_length: expected.length,
		segments_received: received.split(".").length,
		body_matches: gotBody === wantBody,
		mac_matches: gotMac === wantMac,
		body_length_delta: gotBody.length - wantBody.length,
		mac_length_delta: gotMac.length - wantMac.length,
		first_difference_at: firstDiff,
		received_has_whitespace: /\s/.test(received),
	};
}

export { TokenError };
